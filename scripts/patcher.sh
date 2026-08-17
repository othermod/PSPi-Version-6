#!/usr/bin/env bash
set -euo pipefail

[[ $EUID -ne 0 ]] && echo "ERROR: This script must be run as root (use sudo)" && exit 1

# Usage:
#   ./scripts/patcher.sh --distro <name> [--version X.Y.Z] [--driver-binaries PATH] [--target TARGET]
#
# ---------------------------------------------------------------------------
# Distro config contract
# ---------------------------------------------------------------------------
# Configs live in scripts/distros/<name>.sh. Anything matching that glob is
# treated as a distro by the release workflow, so shared code belongs in this
# file, not there.
#
# Required:
#   PATCH_METHOD                 - "squashfs" or "copy"
#   DRIVERS_BASE                 - runtime path where drivers/boot.sh live on the device
#   INIT_SYSTEM                  - systemd or sysv
#   ALL_TARGETS                  - bash array of target names
#   TARGET_URL[<target>]         - download URL; compression detected from file extension
#   TARGET_SHA256[<target>]      - SHA256 of the download. Empty skips verification;
#                                  a cached file is then trusted as-is (delete it to
#                                  force a re-download).
#   TARGET_PSPI_PREFIX[<target>] - output filename prefix; -v<version>.img.xz appended automatically
#   TARGET_BIN[<target>]         - 32 or 64
#
# Required for PATCH_METHOD=squashfs:
#   SQUASHFS_PATH                - path to squashfs within the mounted boot partition
#   SQUASHFS_COMP_ARGS           - extra args passed to mksquashfs (e.g. "-comp zstd"), can be empty
#
# Optional:
#   BOOT_OVERLAYS_DIR            - where .dtbo files are written, relative to the boot
#                                  partition root. Default "overlays". Set this for A/B
#                                  layouts where the firmware reads from elsewhere.
#
# Optional hooks. Argument lists below are exact; every config implementing
# distro_post_patch uses the same slot meanings.
#   distro_pre_patch  <img_path> <work_dir> <BIN> <label>
#       After decompression, before any partition is mounted. Use to expand or
#       repartition the image.
#   distro_post_patch <rootfs_target> <mnt_boot> <work_dir> <BIN> <label>
#       After the generic boot-partition and init-system setup. rootfs_target is
#       the overlay mount (squashfs) or the mounted rootfs (copy). A hook may
#       replace files the generic layer installed, not only add to them --
#       firmware.sh replaces boot.sh wholesale.
#   distro_post_write <mnt_boot> <BIN> <label>
#       After the squashfs repack and swap. Use for checksums and marker files.
#
# Available to configs, all defined in this file:
#   die <msg>                     - print to stderr and exit
#   PROJECT_DIR                   - repository root
#   CONFIG_DIR                    - scripts/config
#   DRIVER_BINARIES_DIR           - --driver-binaries path, empty when building locally
#   detect_partition <img> <n>    - prints "<offset_bytes> <size_bytes>"
#   attach_partition <img> <n>    - prints a bounded loop device path
#   set_input_mouse <mnt_boot>
#   build_battery_module_from_headers <hdr> <kver> <rootfs> <work_dir> <BIN>
#   enable_battery_module_at_boot <rootfs>

die() { echo "ERROR: $*" >&2; exit 1; }

DISTRO=""
VERSION=""
DRIVER_BINARIES_DIR=""
TARGET=""
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG_DIR="$SCRIPT_DIR/config"
# Local builds are frozen to /home/user so cache and output never vary with
# the invoking user's $HOME. Override the local root with PSPI_LOCAL_ROOT.
# GitHub Actions (GITHUB_WORKSPACE set) overrides both paths.
LOCAL_ROOT="${PSPI_LOCAL_ROOT:-/home/user}"
OUTPUT_DIR="${GITHUB_WORKSPACE:-$LOCAL_ROOT}/pspi/patched_images"
CACHE_DIR="${GITHUB_WORKSPACE:-$LOCAL_ROOT}/pspi/stock_images"
DOWNLOAD_ATTEMPTS=5
# Where per-image work directories are created. Override with PSPI_WORK_DIR when
# the default is unsuitable -- notably inside a container whose /tmp is on
# overlayfs, which cannot host the nested overlay mount the squashfs method uses.
WORK_ROOT="${PSPI_WORK_DIR:-/tmp}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --distro)          DISTRO="$2";              shift 2 ;;
        --version)         VERSION="$2";             shift 2 ;;
        --driver-binaries) DRIVER_BINARIES_DIR="$2"; shift 2 ;;
        --target)          TARGET="$2";              shift 2 ;;
        --help|-h)         sed -n '/^# Usage:/,/^$/p' "$0"; exit 0 ;;
        *)                 die "Unknown argument: $1 (use --help)" ;;
    esac
done

[[ -z "$DISTRO" ]] && die "No distro specified. Use --distro <name>"
DISTRO_FILE="$SCRIPT_DIR/distros/${DISTRO}.sh"
[[ -f "$DISTRO_FILE" ]] || die "Distro config not found: $DISTRO_FILE"
# shellcheck source=/dev/null
source "$DISTRO_FILE"

# Validate required distro vars
: "${PATCH_METHOD:?$DISTRO_FILE must set PATCH_METHOD (squashfs or copy)}"
: "${DRIVERS_BASE:?$DISTRO_FILE must set DRIVERS_BASE}"
: "${INIT_SYSTEM:?$DISTRO_FILE must set INIT_SYSTEM (systemd or sysv)}"
: "${ALL_TARGETS:?$DISTRO_FILE must set ALL_TARGETS}"
[[ "$PATCH_METHOD" == "squashfs" || "$PATCH_METHOD" == "copy" ]] \
    || die "PATCH_METHOD must be 'squashfs' or 'copy'"
if [[ "$PATCH_METHOD" == "squashfs" ]]; then
    : "${SQUASHFS_PATH:?$DISTRO_FILE must set SQUASHFS_PATH for squashfs method}"
    SQUASHFS_COMP_ARGS="${SQUASHFS_COMP_ARGS:-}"
fi

if [[ -z "$VERSION" ]]; then
    LAST_TAG="$(git -C "$PROJECT_DIR" describe --tags --abbrev=0 2>/dev/null || true)"
    VERSION="${LAST_TAG#v}"
    [[ -z "$VERSION" ]] && VERSION="0.0.0"
fi

# Idempotent: run at startup to clear anything a previous run stranded, and
# again on exit so an aborted build doesn't leave mounts or loop devices behind.
# Only touches this script's own work directories.
cleanup() {
    local mp
    # Overlays first, then their squashfs sources, then everything else in
    # reverse mount order so nested mounts (the RetroPie chroot's proc/sys/dev)
    # come down before their parents.
    awk -v root="$WORK_ROOT/pspi-build-" '$3=="overlay" && index($2,root)==1 {print $2}' /proc/mounts | while read -r mp; do
        umount "$mp" 2>/dev/null || umount -l "$mp" 2>/dev/null || true
    done
    awk -v root="$WORK_ROOT/pspi-build-" '$3=="squashfs" && index($2,root)==1 {print $2}' /proc/mounts | while read -r mp; do
        umount "$mp" 2>/dev/null || umount -l "$mp" 2>/dev/null || true
    done
    awk -v root="$WORK_ROOT/pspi-build-" 'index($2,root)==1 {print $2}' /proc/mounts | tac | while read -r mp; do
        umount "$mp" 2>/dev/null || umount -l "$mp" 2>/dev/null || true
    done
    # Only detach loop devices backed by pspi build images.
    # Guarded with `if` so a no-match grep (exit 1) doesn't trip `set -e`.
    if losetup -a 2>/dev/null | grep -qF "$WORK_ROOT/pspi-build-"; then
        losetup -a 2>/dev/null | grep -F "$WORK_ROOT/pspi-build-" | cut -d: -f1 | while read -r dev; do
            losetup -d "$dev" 2>/dev/null || true
        done
    fi
    rm -rf "$WORK_ROOT"/pspi-build-*
}

build_drivers() {
    # Drop back to the invoking user so builds use their toolchain/PATH.
    # -H sets HOME to that user as well, which the ATmega makefile needs: it
    # locates the Arduino AVR core under $HOME/.arduino15, and the README has
    # you install that core as your normal user.
    local -a as_user=()
    if [[ -n "${SUDO_USER:-}" ]]; then
        as_user=(sudo -u "$SUDO_USER" -H)
    else
        # Running as root directly, so there is no user to drop to and the
        # Arduino core is looked up under root's home.
        echo "NOTE: SUDO_USER is unset, so drivers build as root and the Arduino" \
             "AVR core is read from ${HOME:-/root}/.arduino15." \
             "Run via sudo from your normal user, or install the core for root."
    fi

    echo "Building gamepad..."
    ( cd "$PROJECT_DIR/rpi/gamepad" && "${as_user[@]}" make 32 && "${as_user[@]}" make 64 )

    echo "Building battery monitor..."
    ( cd "$PROJECT_DIR/rpi/battery" && "${as_user[@]}" make 32 && "${as_user[@]}" make 64 )

    echo "Building rtc..."
    ( cd "$PROJECT_DIR/rpi/rtc" && "${as_user[@]}" make 32 && "${as_user[@]}" make 64 )

    echo "Building firmware updater..."
    ( cd "$PROJECT_DIR/rpi/firmware" && "${as_user[@]}" make 32 && "${as_user[@]}" make 64 )

    echo "Building atmega firmware..."
    ( cd "$PROJECT_DIR/atmega/firmware" && "${as_user[@]}" make all )

    echo "Building wifi monitor..."
    ( cd "$PROJECT_DIR/rpi/wifi" && "${as_user[@]}" make 32 && "${as_user[@]}" make 64 )

    for overlay in audio lcd pcie; do
        echo "Building $overlay overlay..."
        ( cd "$PROJECT_DIR/rpi/$overlay" && "${as_user[@]}" make clean && "${as_user[@]}" make all )
    done
}

download_image() {
    local url="$1" sha256="$2" compressed="$3"
    local cached="$CACHE_DIR/$compressed"
    mkdir -p "$CACHE_DIR"

    if [[ -f "$cached" ]]; then
        if [[ -n "$sha256" ]]; then
            local actual_sha
            actual_sha="$(sha256sum "$cached" | awk '{print $1}')"
            if [[ "$actual_sha" == "$sha256" ]]; then
                echo "  Cached: $compressed"
                return 0
            fi
            echo "  Checksum mismatch. Redownloading..."
            rm -f "$cached"
        else
            # No checksum configured, so there is nothing to revalidate against
            # -- treat the cached file as the source of truth and use it as-is.
            # Never re-download based on age; refresh only happens when a
            # configured SHA256 does not match.
            echo "  Cached (no SHA256 set): $compressed"
            return 0
        fi
    fi

    echo "  Downloading $compressed..."
    local attempt reason actual_sha delay
    for ((attempt = 1; attempt <= DOWNLOAD_ATTEMPTS; attempt++)); do
        reason=""
        # Retries are handled by the outer loop only; wget does a single attempt
        # so a failure is not multiplied across two backoff layers.
        if wget -nv --timeout=30 --tries=1 -O "$cached" "$url"; then
            if [[ -z "$sha256" ]]; then
                echo "  WARNING: downloaded $compressed ($(du -h "$cached" | cut -f1))" \
                     "UNVERIFIED -- no SHA256 set for this target"
                return 0
            fi
            actual_sha="$(sha256sum "$cached" | awk '{print $1}')"
            if [[ "$actual_sha" == "$sha256" ]]; then
                echo "  Downloaded: $compressed ($(du -h "$cached" | cut -f1)), SHA256 OK"
                return 0
            fi
            reason="checksum mismatch: expected $sha256, got $actual_sha"
        else
            reason="wget failed"
        fi

        rm -f "$cached"
        if ((attempt < DOWNLOAD_ATTEMPTS)); then
            delay=$((attempt * 15))
            echo "  Attempt $attempt/$DOWNLOAD_ATTEMPTS failed ($reason). Retrying in ${delay}s..."
            sleep "$delay"
        fi
    done
    die "Failed to download $url after $DOWNLOAD_ATTEMPTS attempts ($reason)"
}

# Print "<offset_bytes> <size_bytes>" for MBR partition <n> (1-based).
# Validates the boot signature so a truncated or non-image file fails loudly
# instead of yielding a nonsense offset.
detect_partition() {
    local img_path="$1" part_num="$2"
    python3 - "$img_path" "$part_num" <<'EOF'
import struct, sys
path, num = sys.argv[1], int(sys.argv[2])
with open(path, 'rb') as f:
    mbr = f.read(512)
if len(mbr) < 512 or mbr[510:512] != b'\x55\xAA':
    sys.exit(f"No MBR boot signature in {path}")
# A GPT disk's protective MBR also passes the 0x55AA check; its first entry
# is type 0xEE and spans the whole disk, which would yield a garbage offset.
# The type byte is at entry-start+4, i.e. offset 450 for entry 1.
if mbr[450] == 0xEE:
    sys.exit(f"GPT disk detected in {path}; detect_partition only supports MBR")
entry = mbr[446 + (num - 1) * 16:446 + num * 16]
lba, sectors = struct.unpack_from('<II', entry, 8)
if lba == 0 or sectors == 0:
    sys.exit(f"Partition {num} is empty in {path}")
print(lba * 512, sectors * 512)
EOF
}

# Attach a partition to a free loop device, bounded to the partition's own
# length so anything that resizes to the device size cannot overrun it.
attach_partition() {
    local img_path="$1" part_num="$2"
    local offset size
    read -r offset size < <(detect_partition "$img_path" "$part_num") \
        || die "Failed to read partition $part_num from $img_path"
    losetup --find --show --offset "$offset" --sizelimit "$size" "$img_path" \
        || die "Failed to attach partition $part_num of $img_path"
}

# --- Helpers available to distro configs ---

# Switch the shipped runtime config from gamepad to mouse input. Desktop
# images use this so the stick drives the cursor.
set_input_mouse() {
    local mnt_boot="$1"
    grep -q '^input_type=' "$mnt_boot/pspi.conf" \
        || die "pspi.conf has no input_type line to switch"
    sed -i 's/^input_type=.*$/input_type=mouse/' "$mnt_boot/pspi.conf"
    echo "  Set input_type=mouse in pspi.conf"
}

# Cross-compile pspi_battery.ko against an already-extracted kernel header
# tree and install it into the image.
#
#   build_battery_module_from_headers <hdr_dir> <kver> <rootfs> <work_dir> <arch>
#
# <arch> is 32 or 64. Callers differ only in how they obtain <hdr_dir>: Kali
# uses the trees the image already ships, Ubuntu fetches them from the archive.
build_battery_module_from_headers() {
    local hdr="$1" kver="$2" rootfs="$3" work_dir="$4" bin="$5"
    local karch cross build_dir log

    if [[ "$bin" == "64" ]]; then
        karch="arm64"; cross="aarch64-linux-gnu-"
        export QEMU_LD_PREFIX="/usr/aarch64-linux-gnu"
    else
        karch="arm";   cross="arm-linux-gnueabihf-"
        export QEMU_LD_PREFIX="/usr/arm-linux-gnueabihf"
    fi

    build_dir="$work_dir/pspi_battery"
    log="$work_dir/pspi_battery-${kver}.log"
    mkdir -p "$build_dir"
    cp "$PROJECT_DIR/rpi/battery/module/pspi_battery.c" "$build_dir/"
    echo "obj-m += pspi_battery.o" > "$build_dir/Makefile"

    echo "  Building pspi_battery for $kver..."
    if ! make -C "$hdr" M="$build_dir" ARCH="$karch" CROSS_COMPILE="$cross" \
            modules > "$log" 2>&1; then
        echo "--- last 30 lines of $log ---" >&2
        tail -30 "$log" >&2
        die "pspi_battery build failed for $kver (full log: $log)"
    fi
    [[ -f "$build_dir/pspi_battery.ko" ]] \
        || die "pspi_battery.ko was not produced for $kver"

    mkdir -p "$rootfs/lib/modules/$kver/extra"
    cp "$build_dir/pspi_battery.ko" "$rootfs/lib/modules/$kver/extra/"
    depmod -b "$rootfs" "$kver" || die "depmod failed for $kver"
    make -C "$hdr" M="$build_dir" ARCH="$karch" CROSS_COMPILE="$cross" \
        clean > /dev/null 2>&1 || true
}

# Load the module at boot, before battery_monitor picks its output path.
# boot.sh also attempts the modprobe itself; this covers the case where
# something else on the image reads the battery before boot.sh runs.
# Refuse to promise a module we never installed: a lone modules-load.d entry
# would just fail silently at boot, leaving the battery invisible with no signal.
enable_battery_module_at_boot() {
    local rootfs="$1"
    ls "$rootfs"/lib/modules/*/extra/pspi_battery.ko >/dev/null 2>&1 \
        || die "pspi_battery.ko not installed under $rootfs/lib/modules"
    mkdir -p "$rootfs/etc/modules-load.d"
    echo "pspi_battery" > "$rootfs/etc/modules-load.d/pspi_battery.conf"
}

patch_image() {
    local img_path="$1" work_dir="$2" BIN="$3" label="$4"

    local boot_offset boot_size
    read -r boot_offset boot_size < <(detect_partition "$img_path" 1) \
        || die "Failed to read boot partition from $img_path"
    echo "  Boot partition: offset $(( boot_offset / 1024 / 1024 )) MiB," \
         "size $(( boot_size / 1024 / 1024 )) MiB"

    local stale_dev
    while IFS= read -r stale_dev; do
        echo "  Detaching stale loop device: $stale_dev"
        losetup -d "$stale_dev" 2>/dev/null || true
    done < <(losetup --associated "$img_path" --output NAME --noheadings 2>/dev/null)

    local device_path
    device_path=$(attach_partition "$img_path" 1)

    local mnt_boot="$work_dir/mnt-boot"
    mkdir -p "$mnt_boot"
    mount "$device_path" "$mnt_boot" || die "Failed to mount boot partition"

    # Append PSPi hardware config (conditional filter tags handle per-board settings)
    cat "$CONFIG_DIR/config.txt" >> "$mnt_boot/config.txt"

    # Copy PSPi runtime config and boot script
    cp "$CONFIG_DIR/pspi.conf" "$mnt_boot/pspi.conf"
    cp "$CONFIG_DIR/boot.sh"   "$mnt_boot/boot.sh"
    chmod +x "$mnt_boot/boot.sh"

    local base="${DRIVER_BINARIES_DIR:-$PROJECT_DIR/rpi}"

    # Copy device tree overlays. A missing overlay yields an image with a dead
    # LCD or no audio, so an empty source directory is fatal, not skipped.
    # BOOT_OVERLAYS_DIR lets a distro point this at a non-standard location
    # (eg. an A/B layout where os_prefix sends the firmware to current/).
    local overlays_rel="${BOOT_OVERLAYS_DIR:-overlays}"
    local overlays_dir="$mnt_boot/$overlays_rel"
    [[ -d "$(dirname "$overlays_dir")" ]] \
        || die "Overlay destination parent missing: $overlays_rel (check BOOT_OVERLAYS_DIR)"
    mkdir -p "$overlays_dir"
    local -a dtbos
    local dtbo_count=0
    for overlay in audio lcd pcie; do
        dtbos=("${base}/${overlay}/"*.dtbo)
        [[ -e "${dtbos[0]}" ]] || die "No .dtbo files found in ${base}/${overlay}"
        cp "${dtbos[@]}" "$overlays_dir/" || die "Failed to copy $overlay overlays"
        dtbo_count=$(( dtbo_count + ${#dtbos[@]} ))
    done
    echo "  Installed $dtbo_count overlays into $overlays_rel/"

    # Copy driver binaries
    mkdir -p "$mnt_boot/drivers"
    cp "${base}/gamepad/${BIN}/gamepad"           "$mnt_boot/drivers/gamepad"
    cp "${base}/battery/${BIN}/battery_monitor"   "$mnt_boot/drivers/battery_monitor"
    cp "${base}/rtc/${BIN}/rtc"                   "$mnt_boot/drivers/rtc"
    cp "${base}/wifi/${BIN}/wifi_monitor"   "$mnt_boot/drivers/wifi_monitor"

    # Method-specific: set up the editable rootfs and register the cleanup trap
    local rootfs_target
    if [[ "$PATCH_METHOD" == "copy" ]]; then
        local rootfs_dev
        rootfs_dev=$(attach_partition "$img_path" 2)
        local mnt_rootfs="$work_dir/mnt-rootfs"
        mkdir -p "$mnt_rootfs"
        mount "$rootfs_dev" "$mnt_rootfs" || die "Failed to mount rootfs partition"
        rootfs_target="$mnt_rootfs"
        trap "(umount '$mnt_rootfs' 2>/dev/null || true; \
               umount '$mnt_boot' 2>/dev/null || true; \
               losetup -d $rootfs_dev 2>/dev/null || true; \
               losetup -d $device_path 2>/dev/null || true)" RETURN
    else
        local mnt_squashfs="$work_dir/mnt-squashfs"
        local overlay_upper="$work_dir/overlay-upper"
        local overlay_work="$work_dir/overlay-work"
        local overlay_target="$work_dir/overlay-target"
        mkdir -p "$mnt_squashfs" "$overlay_upper" "$overlay_work" "$overlay_target"
        # Attach the squashfs to a loop device explicitly rather than via the
        # mount -o loop shorthand. The implicit device is torn down
        # asynchronously after unmount, which leaves the parent mount busy and
        # the backing file still in use; detaching by hand is synchronous.
        local sq_dev
        sq_dev=$(losetup --find --show --read-only "$mnt_boot/$SQUASHFS_PATH") \
            || die "Failed to attach $SQUASHFS_PATH to a loop device"
        mount --type squashfs --options ro \
            --source "$sq_dev" --target "$mnt_squashfs"
        mount --type overlay \
            --options "lowerdir=$mnt_squashfs,upperdir=$overlay_upper,workdir=$overlay_work" \
            --source overlay --target "$overlay_target"
        rootfs_target="$overlay_target"
        trap "(umount '$overlay_target' 2>/dev/null || true; \
               umount '$mnt_squashfs' 2>/dev/null || true; \
               losetup -d $sq_dev 2>/dev/null || true; \
               umount '$mnt_boot' 2>/dev/null || true; \
               losetup -d $device_path 2>/dev/null || true)" RETURN
    fi

    # Install startup entries based on the distro's init system
    # Templates in config/ use __DRIVERS_BASE__ as a placeholder, substituted here
    case "$INIT_SYSTEM" in
        systemd)
            mkdir -p "$rootfs_target/usr/lib/systemd/system" \
                     "$rootfs_target/usr/lib/systemd/system/multi-user.target.wants"

            local unit
            for unit in pspi.service pspi-wifi.service; do
                sed "s|__DRIVERS_BASE__|$DRIVERS_BASE|g" \
                    "$CONFIG_DIR/$unit" \
                    > "$rootfs_target/usr/lib/systemd/system/$unit"
                ln -sf "../$unit" \
                    "$rootfs_target/usr/lib/systemd/system/multi-user.target.wants/$unit"
            done
            ;;
        sysv)
            mkdir -p "$rootfs_target/etc/init.d"
            sed "s|__DRIVERS_BASE__|$DRIVERS_BASE|g" \
                "$CONFIG_DIR/S99pspi-daemons" \
                > "$rootfs_target/etc/init.d/S99pspi-daemons"
            chmod +x "$rootfs_target/etc/init.d/S99pspi-daemons"
            ;;
        *)
            die "Unknown INIT_SYSTEM: $INIT_SYSTEM (expected systemd or sysv)"
            ;;
    esac

    # Distro-specific rootfs edits (retroarch config, extra init scripts, etc.)
    if declare -f distro_post_patch > /dev/null; then
        distro_post_patch "$rootfs_target" "$mnt_boot" "$work_dir" "$BIN" "$label"
    fi

    # Method-specific: repack squashfs and swap it back into the image
    if [[ "$PATCH_METHOD" == "squashfs" ]]; then
        echo "  Repacking squashfs..."
        local temp_squashfs="$work_dir/filesystem.squashfs"
        # shellcheck disable=SC2086
        mksquashfs "$overlay_target" "$temp_squashfs" -noappend -quiet $SQUASHFS_COMP_ARGS \
            || die "Failed to repack rootfs"

        echo "  Unmounting overlay and squashfs..."
        umount "$overlay_target"
        umount "$mnt_squashfs"
        # Release the backing file before it is replaced below
        losetup -d "$sq_dev" || die "Failed to detach $sq_dev"

        echo "  Swapping squashfs in boot partition..."
        rm "$mnt_boot/$SQUASHFS_PATH"
        cp "$temp_squashfs" "$mnt_boot/$SQUASHFS_PATH"
    fi

    # Distro-specific post-write steps (checksums, board marker files, etc.)
    if declare -f distro_post_write > /dev/null; then
        distro_post_write "$mnt_boot" "$BIN" "$label"
    fi
}

build_image() {
    local label="$1"

    [[ -n "${TARGET_URL[$label]+x}" ]] || die "Unknown target: $label (check ALL_TARGETS in $DISTRO_FILE)"
    local T_URL="${TARGET_URL[$label]}"
    local T_SHA256="${TARGET_SHA256[$label]}"
    local T_PSPI_NAME="${TARGET_PSPI_PREFIX[$label]}-v${VERSION}.img.xz"
    local T_BIN="${TARGET_BIN[$label]}"
    local T_COMPRESSED="${T_URL##*/}"

    echo "Building $label..."
    local work_dir
    work_dir="$(mktemp -d "$WORK_ROOT/pspi-build-XXXXXX")"
    mkdir -p "$OUTPUT_DIR"

    download_image "$T_URL" "$T_SHA256" "$T_COMPRESSED"

    local ext="${T_COMPRESSED##*.}"
    local img_path="$work_dir/${T_COMPRESSED%.$ext}"
    case "$ext" in
        gz)  gunzip -c "$CACHE_DIR/$T_COMPRESSED" > "$img_path" ;;
        xz)  xz -dc   "$CACHE_DIR/$T_COMPRESSED" > "$img_path" ;;
        *)   die "Unknown compression extension: $ext (expected gz or xz)" ;;
    esac
    echo "  Decompressed: $(du -h "$img_path" | cut -f1)"

    # Optional pre-patch hook (eg. expand image, resize partitions)
    if declare -f distro_pre_patch > /dev/null; then
        distro_pre_patch "$img_path" "$work_dir" "$T_BIN" "$label"
    fi

    patch_image "$img_path" "$work_dir" "$T_BIN" "$label"

    # The mounts are already down and the loop devices detached by this point,
    # both of which flush. This is cheap insurance against anything a distro
    # hook wrote directly to the image file after that.
    sync

    if [[ "$PATCH_METHOD" == "squashfs" ]]; then
        echo "  Zeroing free space in boot partition..."
        local boot_offset boot_size
        read -r boot_offset boot_size < <(detect_partition "$img_path" 1) \
            || die "Failed to read boot partition from $img_path"
        python3 "$SCRIPT_DIR/zero_fat32.py" "$img_path" "$boot_offset" \
            || die "Boot-partition zeroing failed (see above)"
    else
        # Deleted files leave their contents as ordinary bytes that compress
        # no better than the originals (RetroPie clears a large apt cache here).
        # zerofree needs a block device, so reattach the now-unmounted rootfs.
        command -v zerofree >/dev/null 2>&1 \
            || die "zerofree not installed; required to zero rootfs free space"
        echo "  Zeroing free space in rootfs partition..."
        local zf_dev
        zf_dev=$(attach_partition "$img_path" 2)
        if ! zerofree "$zf_dev"; then
            losetup -d "$zf_dev"
            die "zerofree failed on the rootfs partition"
        fi
        losetup -d "$zf_dev"
    fi

    xz -9 -T0 "$img_path"
    mv "${img_path}.xz" "$OUTPUT_DIR/$T_PSPI_NAME"
    echo "  Compressed: $T_PSPI_NAME ($(du -h "$OUTPUT_DIR/$T_PSPI_NAME" | cut -f1))"

    # Best-effort cleanup
    rm -rf "$work_dir" 2>/dev/null || \
        echo "  Warning: could not fully remove build dir $work_dir"
}

# --- Main ---

cleanup
trap cleanup EXIT

# The squashfs method stacks an overlay on top of the mounted squashfs, and
# overlayfs refuses an upperdir that is itself on overlayfs. Containers whose
# root is overlayfs hit this, and the kernel's error names neither cause nor
# cure, so check up front.
if [[ "$PATCH_METHOD" == "squashfs" ]]; then
    mkdir -p "$WORK_ROOT"
    work_fs="$(stat -f -c %T "$WORK_ROOT" 2>/dev/null || echo unknown)"
    if [[ "$work_fs" == "overlayfs" ]]; then
        die "Work directory $WORK_ROOT is on overlayfs, which cannot host the
       overlay mount the squashfs method needs. Either set PSPI_WORK_DIR to a
       path on a real filesystem, or give the container a volume for /tmp
       (docker run -v /tmp ...). GitHub runners are unaffected."
    fi
fi

echo "PSPi Version 6 | distro=$DISTRO method=$PATCH_METHOD version=$VERSION output=$OUTPUT_DIR"

if [[ -z "$DRIVER_BINARIES_DIR" ]]; then
    build_drivers
fi

if [[ -z "$TARGET" ]]; then
    for t in "${ALL_TARGETS[@]}"; do
        build_image "$t"
    done
else
    build_image "$TARGET"
fi

echo "Done. Artifacts in: $OUTPUT_DIR"

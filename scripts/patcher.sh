#!/usr/bin/env bash
set -euo pipefail

[[ $EUID -ne 0 ]] && echo "ERROR: This script must be run as root (use sudo)" && exit 1

# Usage:
#   ./scripts/buildroot.sh --distro <name> [--version X.Y.Z] [--driver-binaries PATH] [--target TARGET]
#
# Distro configs live in scripts/distros/<name>.sh and must define:
#   PATCH_METHOD                 - "squashfs" or "copy"
#   DRIVERS_BASE                 - runtime path where drivers/boot.sh live on the device
#   INIT_SYSTEM                  - systemd or sysv
#   ALL_TARGETS                  - bash array of target names
#   TARGET_URL[<target>]         - download URL; compression detected from file extension
#   TARGET_SHA256[<target>]      - SHA256 of the download, or empty to skip verification
#   TARGET_PSPI_PREFIX[<target>] - output filename prefix; -v<version>.img.gz appended automatically
#   TARGET_BIN[<target>]         - 32 or 64
#
# For PATCH_METHOD=squashfs, also define:
#   SQUASHFS_PATH                - path to squashfs within the mounted boot partition
#   SQUASHFS_COMP_ARGS           - extra args passed to mksquashfs (e.g. "-comp zstd"), can be empty
#
# Optional hooks (define in distro config if needed):
#   distro_post_patch() - called with (rootfs_target, mnt_boot, work_dir, BIN)
#                         rootfs_target is overlay_target (squashfs) or mnt_rootfs (copy)
#   distro_post_write() - called with (mnt_boot, BIN) after write is complete;
#                         use for checksums, board marker files, etc.

die() { echo "ERROR: $*" >&2; exit 1; }

DISTRO=""
VERSION=""
DRIVER_BINARIES_DIR=""
TARGET=""
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG_DIR="$SCRIPT_DIR/config"
OUTPUT_DIR="$HOME/pspi/patched_images"
CACHE_DIR="$HOME/pspi/stock_images"

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

cleanup() {
    awk '$3=="overlay" && $2~/pspi/ {print $2}' /proc/mounts | while read -r mp; do
        umount "$mp" 2>/dev/null || true
    done
    awk '$3=="squashfs" && $2~/pspi/ {print $2}' /proc/mounts | while read -r mp; do
        umount "$mp" 2>/dev/null || true
    done
    awk '$2~/pspi/ {print $2}' /proc/mounts | while read -r mp; do
        umount "$mp" 2>/dev/null || true
    done
    for dev in /dev/loop{0..7}; do
        losetup -d "$dev" 2>/dev/null || true
    done
    rm -rf /tmp/pspi-build-*
}

build_drivers() {
    # Drop back to the invoking user so builds use their toolchain/PATH.
    # Falls back to running as-is if SUDO_USER is unset (e.g. root running directly).
    local -a as_user=()
    [[ -n "${SUDO_USER:-}" ]] && as_user=(sudo -u "$SUDO_USER")

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
        if [[ -z "$sha256" ]]; then
            echo "  Cached: $compressed (checksum skipped)"
            return 0
        fi
        local actual_sha
        actual_sha="$(sha256sum "$cached" | awk '{print $1}')"
        if [[ "$actual_sha" == "$sha256" ]]; then
            echo "  Cached: $compressed"
            return 0
        fi
        echo "  Checksum mismatch. Redownloading..."
        rm -f "$cached"
    fi

    echo "  Downloading $compressed..."
    wget -nv -O "$cached" "$url" || die "Failed to download $url"
    if [[ -n "$sha256" ]]; then
        local actual_sha
        actual_sha="$(sha256sum "$cached" | awk '{print $1}')"
        [[ "$actual_sha" != "$sha256" ]] && die "Checksum mismatch: expected $sha256, got $actual_sha"
        echo "  Downloaded: $compressed ($(du -h "$cached" | cut -f1)), SHA256 OK"
    else
        echo "  Downloaded: $compressed ($(du -h "$cached" | cut -f1))"
    fi
}

detect_boot_offset() {
    local img_path="$1"
    python3 - "$img_path" <<'EOF'
import struct, sys
with open(sys.argv[1], 'rb') as f:
    f.seek(446)          # first partition entry in MBR
    lba_start, = struct.unpack_from('<I', f.read(16), 8)
print(lba_start * 512)
EOF
}

detect_rootfs_offset() {
    local img_path="$1"
    python3 - "$img_path" <<'EOF'
import struct, sys
with open(sys.argv[1], 'rb') as f:
    f.seek(446 + 16)     # second partition entry in MBR
    lba_start, = struct.unpack_from('<I', f.read(16), 8)
print(lba_start * 512)
EOF
}

patch_image() {
    local img_path="$1" work_dir="$2" BIN="$3"

    local boot_offset
    boot_offset=$(detect_boot_offset "$img_path")
    echo "  Boot partition offset: $boot_offset bytes ($(( boot_offset / 1024 / 1024 )) MiB)"

    local stale_dev
    while IFS= read -r stale_dev; do
        echo "  Detaching stale loop device: $stale_dev"
        losetup -d "$stale_dev" 2>/dev/null || true
    done < <(losetup --associated "$img_path" --output NAME --noheadings 2>/dev/null)

    local device_path=""
    for dev in /dev/loop{0..7}; do
        if losetup -o "$boot_offset" "$dev" "$img_path" 2>/dev/null; then
            device_path="$dev"
            break
        fi
    done
    [[ -z "$device_path" ]] && die "No available loop device"

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

    # Copy device tree overlays
    mkdir -p "$mnt_boot/overlays"
    for overlay in audio lcd pcie; do
        cp "${base}/${overlay}/"*.dtbo "$mnt_boot/overlays/" 2>/dev/null || true
    done

    # Copy driver binaries
    mkdir -p "$mnt_boot/drivers"
    cp "${base}/gamepad/${BIN}/gamepad"           "$mnt_boot/drivers/gamepad"
    cp "${base}/battery/${BIN}/battery_monitor"   "$mnt_boot/drivers/battery_monitor"
    cp "${base}/rtc/${BIN}/rtc"                   "$mnt_boot/drivers/rtc"
    cp "${base}/wifi/${BIN}/wifi_monitor"   "$mnt_boot/drivers/wifi_monitor"

    # Method-specific: set up the editable rootfs and register the cleanup trap
    local rootfs_target
    if [[ "$PATCH_METHOD" == "copy" ]]; then
        local rootfs_offset rootfs_dev=""
        rootfs_offset=$(detect_rootfs_offset "$img_path")
        for dev in /dev/loop{0..7}; do
            if [[ "$dev" == "$device_path" ]]; then continue; fi
            if losetup -o "$rootfs_offset" "$dev" "$img_path" 2>/dev/null; then
                rootfs_dev="$dev"
                break
            fi
        done
        [[ -z "$rootfs_dev" ]] && die "No available loop device for rootfs"
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
        mount --type squashfs --options loop \
            --source "$mnt_boot/$SQUASHFS_PATH" --target "$mnt_squashfs"
        mount --type overlay \
            --options "lowerdir=$mnt_squashfs,upperdir=$overlay_upper,workdir=$overlay_work" \
            --source overlay --target "$overlay_target"
        rootfs_target="$overlay_target"
        trap "(umount '$overlay_target' 2>/dev/null || true; \
               umount '$mnt_squashfs' 2>/dev/null || true; \
               umount '$mnt_boot' 2>/dev/null || true; \
               losetup -d $device_path 2>/dev/null || true)" RETURN
    fi

    # Install startup entries based on the distro's init system
    # Templates in config/ use __DRIVERS_BASE__ as a placeholder, substituted here
    case "$INIT_SYSTEM" in
        systemd)
            mkdir -p "$rootfs_target/usr/lib/systemd/system" \
                     "$rootfs_target/usr/lib/systemd/system/multi-user.target.wants"

            sed "s|__DRIVERS_BASE__|$DRIVERS_BASE|g" \
                "$CONFIG_DIR/pspi.service" \
                > "$rootfs_target/usr/lib/systemd/system/pspi.service"
            ln -sf ../pspi.service \
                "$rootfs_target/usr/lib/systemd/system/multi-user.target.wants/pspi.service"
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
        distro_post_patch "$rootfs_target" "$mnt_boot" "$work_dir" "$BIN"
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

        echo "  Swapping squashfs in boot partition..."
        rm "$mnt_boot/$SQUASHFS_PATH"
        cp "$temp_squashfs" "$mnt_boot/$SQUASHFS_PATH"
    fi

    # Distro-specific post-write steps (checksums, board marker files, etc.)
    if declare -f distro_post_write > /dev/null; then
        distro_post_write "$mnt_boot" "$BIN"
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
    work_dir="$(mktemp -d /tmp/pspi-build-XXXXXX)"
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

    patch_image "$img_path" "$work_dir" "$T_BIN"

    if [[ "$PATCH_METHOD" == "squashfs" ]]; then
        echo "  Zeroing free space in boot partition..."
        local boot_offset
        boot_offset=$(detect_boot_offset "$img_path")
        python3 "$SCRIPT_DIR/zero_fat32.py" "$img_path" "$boot_offset"
    fi

    xz -9 -T0 "$img_path"
    mv "${img_path}.xz" "$OUTPUT_DIR/$T_PSPI_NAME"
    echo "  Compressed: $T_PSPI_NAME ($(du -h "$OUTPUT_DIR/$T_PSPI_NAME" | cut -f1))"

    ls -lh "$OUTPUT_DIR"/*.img.gz "$OUTPUT_DIR"/*.7z.* 2>/dev/null || true
    rm -rf "$work_dir"
}

# --- Main ---

cleanup
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

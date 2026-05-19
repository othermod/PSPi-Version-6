#!/usr/bin/env bash
set -euo pipefail

[[ $EUID -ne 0 ]] && echo "ERROR: This script must be run as root (use sudo)" && exit 1

# Usage:
#   ./scripts/build-batocera.sh [--version X.Y.Z] [--driver-binaries PATH] [--target cm4|cm5|zero2|zero]

die() { echo "ERROR: $*" >&2; exit 1; }

VERSION=""
DRIVER_BINARIES_DIR=""
TARGET=""
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG_DIR="$SCRIPT_DIR/config"
OUTPUT_DIR="$PROJECT_DIR/completed_images"
CACHE_DIR="$PROJECT_DIR/cache"
DRIVERS_BIN_DIR=""  # set via mktemp in main before use

# Batocera v43 stable release (May 1, 2026)
BATOCERA_CM4_URL="https://updates.batocera.org/bcm2711/stable/last/batocera-bcm2711-43-20260501.img.gz"
BATOCERA_CM4_SHA256=""
BATOCERA_CM5_URL="https://updates.batocera.org/bcm2712/stable/last/batocera-bcm2712-43-20260430.img.gz"
BATOCERA_CM5_SHA256=""
BATOCERA_ZERO2_URL="https://updates.batocera.org/bcm2837/stable/last/batocera-bcm2837-43-20260508.img.gz"
BATOCERA_ZERO2_SHA256=""
BATOCERA_ZERO_URL="https://updates.batocera.org/bcm2835/stable/last/batocera-bcm2835-43-20260507.img.gz"
BATOCERA_ZERO_SHA256=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --version)         VERSION="$2";             shift 2 ;;
        --driver-binaries) DRIVER_BINARIES_DIR="$2"; shift 2 ;;
        --target)          TARGET="$2";              shift 2 ;;
        --help|-h)         sed -n '/^# Usage:/,/^$/p' "$0"; exit 0 ;;
        *)                 die "Unknown argument: $1 (use --help)" ;;
    esac
done

if [[ -z "$VERSION" ]]; then
    LAST_TAG="$(git -C "$PROJECT_DIR" describe --tags --abbrev=0 2>/dev/null || true)"
    VERSION="${LAST_TAG#v}"
    [[ -z "$VERSION" ]] && VERSION="0.0.0"
fi

cleanup() {
    awk '$3=="overlay" && $2~/pspi/ {print $2}' /proc/mounts | while read -r mp; do
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
    mkdir -p "$DRIVERS_BIN_DIR"

    echo "Building gamepad..."
    ( cd "$PROJECT_DIR/rpi/gamepad" && make 32 && make 64 )
    cp "$PROJECT_DIR/rpi/gamepad/bin/32bit/gamepad"         "$DRIVERS_BIN_DIR/gamepad_32"
    cp "$PROJECT_DIR/rpi/gamepad/bin/64bit/gamepad"         "$DRIVERS_BIN_DIR/gamepad_64"

    echo "Building battery monitor..."
    ( cd "$PROJECT_DIR/rpi/battery" && make 32 && make 64 )
    cp "$PROJECT_DIR/rpi/battery/bin/32bit/battery_monitor" "$DRIVERS_BIN_DIR/battery_monitor_32"
    cp "$PROJECT_DIR/rpi/battery/bin/64bit/battery_monitor" "$DRIVERS_BIN_DIR/battery_monitor_64"

    echo "Building rtc..."
    ( cd "$PROJECT_DIR/rpi/rtc" && make 32 && make 64 )
    cp "$PROJECT_DIR/rpi/rtc/bin/32bit/rtc"                 "$DRIVERS_BIN_DIR/rtc_32"
    cp "$PROJECT_DIR/rpi/rtc/bin/64bit/rtc"                 "$DRIVERS_BIN_DIR/rtc_64"

    for overlay in audio lcd pcie; do
        echo "Building $overlay overlay..."
        ( cd "$PROJECT_DIR/rpi/$overlay" && make clean && make all )
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

patch_batocera_image() {
    local img_path="$1" work_dir="$2" device_type="$3"

    local stale_dev
    while IFS= read -r stale_dev; do
        echo "  Detaching stale loop device: $stale_dev"
        losetup -d "$stale_dev" 2>/dev/null || true
    done < <(losetup --associated "$img_path" --output NAME --noheadings 2>/dev/null)

    local device_path=""
    for dev in /dev/loop{0..7}; do
        if losetup -o 1048576 "$dev" "$img_path" 2>/dev/null; then
            device_path="$dev"
            break
        fi
    done
    [[ -z "$device_path" ]] && die "No available loop device"

    local mnt_boot="$work_dir/mnt-boot"
    local mnt_squashfs="$work_dir/mnt-squashfs"
    local overlay_upper="$work_dir/overlay-upper"
    local overlay_work="$work_dir/overlay-work"
    local overlay_target="$work_dir/overlay-target"
    mkdir -p "$mnt_boot" "$mnt_squashfs" "$overlay_upper" "$overlay_work" "$overlay_target"

    trap "(umount '$overlay_target' 2>/dev/null || true; umount '$mnt_squashfs' 2>/dev/null || true; umount '$mnt_boot' 2>/dev/null || true; losetup -d $device_path 2>/dev/null || true; rm -rf '$work_dir/rootfs' '$work_dir/overlay-upper' '$work_dir/overlay-work' '$work_dir/overlay-target' '$work_dir/mnt-squashfs')" RETURN

    mount "$device_path" "$mnt_boot" || die "Failed to mount boot partition"

    local device_config
    case "$device_type" in
        batocera_cm4)   device_config="cm4"   ;;
        batocera_cm5)   device_config="cm5"   ;;
        batocera_zero2) device_config="zero2" ;;
        batocera_zero)  device_config="zero1" ;;
    esac
    local config_file="$CONFIG_DIR/${device_config}.txt"
    [[ -f "$config_file" ]] || die "Device config file not found: $config_file"
    cat "$config_file" >> "$mnt_boot/config.txt"

    # vc4-kms-v3d line is optional on Batocera (no distroconfig.txt on all builds)
    if [[ -f "$mnt_boot/distroconfig.txt" ]]; then
        local vc4_line
        vc4_line=$(grep "dtoverlay=vc4-kms-v3d" "$mnt_boot/distroconfig.txt" | head -1)
        [[ -n "$vc4_line" ]] && echo "$vc4_line,noaudio" >> "$mnt_boot/config.txt"
    fi

    cp "$CONFIG_DIR/pspi.conf" "$mnt_boot/pspi.conf"
    cp "$CONFIG_DIR/boot.sh"   "$mnt_boot/boot.sh"
    chmod +x "$mnt_boot/boot.sh"

    mkdir -p "$mnt_boot/overlays"
    if [[ -n "$DRIVER_BINARIES_DIR" ]]; then
        for overlay in audio lcd pcie; do
            cp "$DRIVER_BINARIES_DIR/${overlay}_overlays/"*.dtbo "$mnt_boot/overlays/" 2>/dev/null || true
        done
    else
        for overlay in audio lcd pcie; do
            cp "$PROJECT_DIR/rpi/$overlay/"*.dtbo "$mnt_boot/overlays/" 2>/dev/null || true
        done
    fi

    local BIN
    case "$device_type" in
        batocera_cm4|batocera_cm5|batocera_zero2) BIN=64 ;;
        batocera_zero)                            BIN=32 ;;
    esac

    local bin_src="${DRIVER_BINARIES_DIR:-$DRIVERS_BIN_DIR}"
    mkdir -p "$mnt_boot/drivers"
    cp "$bin_src/gamepad_${BIN}"         "$mnt_boot/drivers/gamepad"
    cp "$bin_src/battery_monitor_${BIN}" "$mnt_boot/drivers/battery_monitor"
    cp "$bin_src/rtc_${BIN}"             "$mnt_boot/drivers/rtc"

    local batocera_squashfs="$mnt_boot/boot/batocera"

    mount --type squashfs --options loop \
        --source "$batocera_squashfs" --target "$mnt_squashfs"
    mount --type overlay \
        --options "lowerdir=$mnt_squashfs,upperdir=$overlay_upper,workdir=$overlay_work" \
        --source overlay --target "$overlay_target"

    cat << 'SVCEOF' > "$overlay_target/usr/lib/systemd/system/pspi-rtc.service"
[Unit]
Description=PSPi RTC daemon (PCF8563)
After=dev-i2c-1.device
Conflicts=shutdown.target

[Service]
Type=simple
WorkingDirectory=/boot
ExecStart=/boot/drivers/rtc
Restart=always
RestartSec=5

[Install]
WantedBy=sysinit.target
SVCEOF
    mkdir -p "$overlay_target/usr/lib/systemd/system/sysinit.target.wants"
    ln -sf ../system/pspi-rtc.service \
        "$overlay_target/usr/lib/systemd/system/sysinit.target.wants/pspi-rtc.service"

    cat << 'SVCEOF' > "$overlay_target/usr/lib/systemd/system/pspi.service"
[Unit]
Description=PSPi gamepad and battery monitor
After=sys-subsystem-net-devices-wlan0.device
Wants=sys-subsystem-net-devices-wlan0.device

[Service]
Type=simple
WorkingDirectory=/boot
ExecStart=/boot/boot.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
SVCEOF
    mkdir -p "$overlay_target/usr/lib/systemd/system/multi-user.target.wants"
    ln -sf ../system/pspi.service \
        "$overlay_target/usr/lib/systemd/system/multi-user.target.wants/pspi.service"

    cat << 'EOF' > "$overlay_target/etc/init.d/S99pspi-daemons"
#!/bin/sh
case "$1" in
    start) cd /boot && ./boot.sh ;;
esac
EOF
    chmod +x "$overlay_target/etc/init.d/S99pspi-daemons"

    echo "  Repacking squashfs..."
    local temp_squashfs="$work_dir/filesystem.squashfs"
    mksquashfs "$overlay_target" "$temp_squashfs" -noappend -quiet -comp zstd || die "Failed to repack rootfs"

    # Unmount overlay and squashfs before zeroing to prevent corruption
    echo "  Unmounting overlay and squashfs..."
    umount "$overlay_target"
    umount "$mnt_squashfs"

    # Zero out free space in the boot partition
    echo "  Zeroing out free space in boot partition..."
    dd if=/dev/zero of="$mnt_boot/boot/batocera" bs=1M status=progress || true
    sync
    rm "$mnt_boot/boot/batocera"

    # Copy the repacked squashfs back to the image
    echo "  Copying repacked squashfs back to image..."
    cp "$temp_squashfs" "$mnt_boot/boot/batocera"
    echo "batocera-${BIN}" > "$mnt_boot/batocera.board"
}

build_image() {
    local label="$1" url sha256 compressed pspi_name work_dir

    case "$label" in
        batocera_cm4)   url="$BATOCERA_CM4_URL"   sha256="$BATOCERA_CM4_SHA256"
                        compressed="batocera-bcm2711-43-20260501.img.gz"
                        pspi_name="Batocera43-CM4-PSPi6-v${VERSION}.img.gz"   ;;
        batocera_cm5)   url="$BATOCERA_CM5_URL"   sha256="$BATOCERA_CM5_SHA256"
                        compressed="batocera-bcm2712-43-20260430.img.gz"
                        pspi_name="Batocera43-CM5-PSPi6-v${VERSION}.img.gz"   ;;
        batocera_zero2) url="$BATOCERA_ZERO2_URL" sha256="$BATOCERA_ZERO2_SHA256"
                        compressed="batocera-bcm2837-43-20260508.img.gz"
                        pspi_name="Batocera43-Zero2-PSPi6-v${VERSION}.img.gz" ;;
        batocera_zero)  url="$BATOCERA_ZERO_URL"  sha256="$BATOCERA_ZERO_SHA256"
                        compressed="batocera-bcm2835-43-20260507.img.gz"
                        pspi_name="Batocera43-Zero-PSPi6-v${VERSION}.img.gz"  ;;
    esac

    echo "Building $label..."
    work_dir="$(mktemp -d /tmp/pspi-build-XXXXXX)"
    mkdir -p "$OUTPUT_DIR"

    download_image "$url" "$sha256" "$compressed"

    local img_path="$work_dir/${compressed%.gz}"
    gunzip -c "$CACHE_DIR/$compressed" > "$img_path"
    echo "  Decompressed: $(du -h "$img_path" | cut -f1)"

    patch_batocera_image "$img_path" "$work_dir" "$label"

    gzip -9c "$img_path" > "$OUTPUT_DIR/$pspi_name"
    echo "  Compressed: $pspi_name ($(du -h "$OUTPUT_DIR/$pspi_name" | cut -f1))"


    ls -lh "$OUTPUT_DIR"/*.img.gz "$OUTPUT_DIR"/*.7z.* 2>/dev/null || true
    rm -rf "$work_dir"
}

cleanup
echo "PSPi Version 6 | version=$VERSION output=$OUTPUT_DIR"

if [[ -z "$DRIVER_BINARIES_DIR" ]]; then
    DRIVERS_BIN_DIR="$(mktemp -d /tmp/pspi-drivers-XXXXXX)"
    build_drivers
fi

if [[ -z "$TARGET" ]]; then
    build_image batocera_cm4
    build_image batocera_cm5
    build_image batocera_zero2
    build_image batocera_zero
else
    case "$TARGET" in
        cm4)   build_image batocera_cm4   ;;
        cm5)   build_image batocera_cm5   ;;
        zero2) build_image batocera_zero2 ;;
        zero)  build_image batocera_zero  ;;
        *)     die "Unknown target: $TARGET (use cm4, cm5, zero2, or zero)" ;;
    esac
fi

[[ -n "$DRIVERS_BIN_DIR" ]] && rm -rf "$DRIVERS_BIN_DIR"
echo "Done. Artifacts in: $OUTPUT_DIR"

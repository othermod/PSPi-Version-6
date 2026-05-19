#!/usr/bin/env bash
set -euo pipefail

[[ $EUID -ne 0 ]] && echo "ERROR: This script must be run as root (use sudo)" && exit 1

# Usage:
#   ./scripts/build-lakka.sh [--version X.Y.Z] [--driver-binaries PATH] [--target cm4|cm5|zero|arm]

die() { echo "ERROR: $*" >&2; exit 1; }

VERSION=""
DRIVER_BINARIES_DIR=""
TARGET=""
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_DIR="$SCRIPT_DIR/config"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT_DIR="$PROJECT_DIR/completed_images"
CACHE_DIR="$PROJECT_DIR/cache"
DRIVERS_BIN_DIR=""  # set via mktemp in main before use

# Lakka 6.1 stable release (Feb 21, 2026)
LAKKA_CM4_URL="https://github.com/libretro/Lakka-LibreELEC/releases/download/v6.1/Lakka-RPi4.aarch64-6.1.img.gz"
LAKKA_CM4_SHA256="9e541bd8d092c63a65c5b7c66295ff9d3c3fc073d6bb6229560526c1c505ca11"
LAKKA_CM5_URL="https://github.com/libretro/Lakka-LibreELEC/releases/download/v6.1/Lakka-RPi5.aarch64-6.1.img.gz"
LAKKA_CM5_SHA256="b2fd310742c612b6f7f221540518f03845a75f8e5d0b55c0c2abeb81da8c5bb3"
LAKKA_ZERO_URL="https://github.com/libretro/Lakka-LibreELEC/releases/download/v6.1/Lakka-RPi3.aarch64-6.1.img.gz"
LAKKA_ZERO_SHA256="e72cf352cbaaf0366fc7f46650b0e5335786b6119cdcaf086a0ecee2355ac742"
LAKKA_ARM_URL="https://github.com/libretro/Lakka-LibreELEC/releases/download/v6.1/Lakka-RPi.arm-6.1.img.gz"
LAKKA_ARM_SHA256="c331c30d4dc52fbae168d16b844c18833a1e7e790039ceb5f2d2acc6c9b09414"

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
    local actual_sha
    actual_sha="$(sha256sum "$cached" | awk '{print $1}')"
    [[ "$actual_sha" != "$sha256" ]] && die "Checksum mismatch: expected $sha256, got $actual_sha"
    echo "  Downloaded: $compressed ($(du -h "$cached" | cut -f1)), SHA256 OK"
}

patch_lakka_image() {
    local img_path="$1" work_dir="$2" device_type="$3"

    local stale_dev
    while IFS= read -r stale_dev; do
        echo "  Detaching stale loop device: $stale_dev"
        losetup -d "$stale_dev" 2>/dev/null || true
    done < <(losetup --associated "$img_path" --output NAME --noheadings 2>/dev/null)

    local device_path=""
    for dev in /dev/loop{0..7}; do
        if losetup -o 4194304 "$dev" "$img_path" 2>/dev/null; then
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

    trap "(umount --type overlay '$overlay_target' 2>/dev/null || true; umount --type squashfs '$mnt_squashfs' 2>/dev/null || true; umount '$mnt_boot' 2>/dev/null || true; losetup -d $device_path 2>/dev/null || true)" RETURN

    mkdir -p "$mnt_boot" "$mnt_squashfs" "$overlay_upper" "$overlay_work" "$overlay_target"
    mount "$device_path" "$mnt_boot" || die "Failed to mount boot partition"

    local device_config
    case "$device_type" in
        lakka_cm4)  device_config="cm4"   ;;
        lakka_cm5)  device_config="cm5"   ;;
        lakka_zero) device_config="zero2" ;;
        lakka_arm)  device_config="zero1" ;;
    esac
    local config_file="$CONFIG_DIR/${device_config}.txt"
    [[ -f "$config_file" ]] || die "Device config file not found: $config_file"
    cat "$config_file" >> "$mnt_boot/config.txt"

    local vc4_line
    vc4_line=$(grep "dtoverlay=vc4-kms-v3d" "$mnt_boot/distroconfig.txt" | head -1)
    [[ -z "$vc4_line" ]] && die "vc4-kms-v3d line not found in distroconfig.txt"
    echo "$vc4_line,noaudio" >> "$mnt_boot/config.txt"

    cp "$CONFIG_DIR/pspi.conf" "$mnt_boot/pspi.conf"
    cp "$CONFIG_DIR/boot.sh"   "$mnt_boot/boot.sh"
    chmod +x "$mnt_boot/boot.sh"

    mkdir -p "$mnt_boot/overlays"
    local bin_src="${DRIVER_BINARIES_DIR:-$DRIVERS_BIN_DIR}"
    if [[ -n "$DRIVER_BINARIES_DIR" ]]; then
        cp "$DRIVER_BINARIES_DIR/audio_overlays/"*.dtbo "$mnt_boot/overlays/" 2>/dev/null || true
        cp "$DRIVER_BINARIES_DIR/lcd_overlays/"*.dtbo  "$mnt_boot/overlays/" 2>/dev/null || true
        cp "$DRIVER_BINARIES_DIR/pcie_overlays/"*.dtbo "$mnt_boot/overlays/" 2>/dev/null || true
    else
        cp "$PROJECT_DIR/rpi/audio/"*.dtbo "$mnt_boot/overlays/" 2>/dev/null || true
        cp "$PROJECT_DIR/rpi/lcd/"*.dtbo   "$mnt_boot/overlays/" 2>/dev/null || true
        cp "$PROJECT_DIR/rpi/pcie/"*.dtbo  "$mnt_boot/overlays/" 2>/dev/null || true
    fi

    local BIN
    case "$device_type" in
        lakka_cm4|lakka_cm5|lakka_zero) BIN=64 ;;
        lakka_arm)                      BIN=32 ;;
    esac

    mkdir -p "$mnt_boot/drivers"
    cp "$bin_src/gamepad_${BIN}"         "$mnt_boot/drivers/gamepad"
    cp "$bin_src/battery_monitor_${BIN}" "$mnt_boot/drivers/battery_monitor"
    cp "$bin_src/rtc_${BIN}"             "$mnt_boot/drivers/rtc"

    mount --type squashfs --options loop \
        --source "$mnt_boot/SYSTEM" --target "$mnt_squashfs"
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
WorkingDirectory=/flash
ExecStart=/flash/drivers/rtc
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
WorkingDirectory=/flash
ExecStart=/flash/boot.sh
RemainAfterExit=yes
[Install]
WantedBy=multi-user.target
SVCEOF
    mkdir -p "$overlay_target/usr/lib/systemd/system/multi-user.target.wants"
    ln -sf ../system/pspi.service \
        "$overlay_target/usr/lib/systemd/system/multi-user.target.wants/pspi.service"

    sed -i \
        's/menu_swap_ok_cancel_buttons = "false"/menu_swap_ok_cancel_buttons = "true"/' \
        "$overlay_target/etc/retroarch.cfg"
    sed -i 's/xmb_layout = "0"/xmb_layout = "2"/'                           "$overlay_target/etc/retroarch.cfg"
    sed -i 's/xmb_menu_color_theme = .*/xmb_menu_color_theme = "2"/'        "$overlay_target/etc/retroarch.cfg"
    sed -i 's/menu_shader_pipeline = .*/menu_shader_pipeline = "0"/'         "$overlay_target/etc/retroarch.cfg"
    sed -i 's/input_volume_up = "add"/input_volume_up = "volumeup"/'         "$overlay_target/etc/retroarch.cfg"
    sed -i 's/input_volume_down = "subtract"/input_volume_down = "volumedown"/' "$overlay_target/etc/retroarch.cfg"

    echo "  Repacking squashfs..."
    mksquashfs "$overlay_target" "$work_dir/filesystem.squashfs" -noappend -quiet
    cp "$work_dir/filesystem.squashfs" "$mnt_boot/SYSTEM"
    md5sum "$mnt_boot/SYSTEM" > "$mnt_boot/SYSTEM.md5"
}

build_image() {
    local label="$1" url sha256 compressed pspi_name work_dir

    case "$label" in
        lakka_cm4)  url="$LAKKA_CM4_URL"  sha256="$LAKKA_CM4_SHA256"
                    compressed="Lakka-RPi4.aarch64-6.1.img.gz"
                    pspi_name="Lakka6.1-CM4-PSPi6-v${VERSION}.img.gz"   ;;
        lakka_cm5)  url="$LAKKA_CM5_URL"  sha256="$LAKKA_CM5_SHA256"
                    compressed="Lakka-RPi5.aarch64-6.1.img.gz"
                    pspi_name="Lakka6.1-CM5-PSPi6-v${VERSION}.img.gz"   ;;
        lakka_zero) url="$LAKKA_ZERO_URL" sha256="$LAKKA_ZERO_SHA256"
                    compressed="Lakka-RPi3.aarch64-6.1.img.gz"
                    pspi_name="Lakka6.1-Zero2-PSPi6-v${VERSION}.img.gz" ;;
        lakka_arm)  url="$LAKKA_ARM_URL"  sha256="$LAKKA_ARM_SHA256"
                    compressed="Lakka-RPi.arm-6.1.img.gz"
                    pspi_name="Lakka6.1-Zero1-PSPi6-v${VERSION}.img.gz" ;;
    esac

    echo "Building $label..."
    work_dir="$(mktemp -d /tmp/pspi-build-XXXXXX)"
    mkdir -p "$OUTPUT_DIR"

    download_image "$url" "$sha256" "$compressed"

    local img_path="$work_dir/${compressed%.gz}"
    gunzip -c "$CACHE_DIR/$compressed" > "$img_path"
    echo "  Decompressed: $(du -h "$img_path" | cut -f1)"

    patch_lakka_image "$img_path" "$work_dir" "$label"

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
    build_image lakka_cm4
    build_image lakka_cm5
    build_image lakka_zero
    build_image lakka_arm
else
    case "$TARGET" in
        cm4)  build_image lakka_cm4  ;;
        cm5)  build_image lakka_cm5  ;;
        zero) build_image lakka_zero ;;
        arm)  build_image lakka_arm  ;;
        *)    die "Unknown target: $TARGET (use cm4, cm5, zero, or arm)" ;;
    esac
fi

[[ -n "$DRIVERS_BIN_DIR" ]] && rm -rf "$DRIVERS_BIN_DIR"
echo "Done. Artifacts in: $OUTPUT_DIR"

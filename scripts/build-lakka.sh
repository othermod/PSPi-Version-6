#!/usr/bin/env bash
set -euo pipefail


[[ $EUID -ne 0 ]] && echo "ERROR: This script must be run as root (use sudo)" && exit 1
###############################################################################
# build-images.sh
# Builds patched Lakka images for PSPi hardware (CM4 and Zero2).
#
# Usage:
#   ./scripts/build-images.sh [--version X.Y.Z] [--driver-binaries PATH]
###############################################################################

die() { echo "ERROR: $*" >&2; exit 1; }

VERSION=""
DRIVER_BINARIES_DIR=""
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT_DIR="$PROJECT_DIR/completed_images"
CACHE_DIR="$PROJECT_DIR/cache"
DRIVERS_BIN_DIR="$PROJECT_DIR/.drivers-bin"  # staging dir for built binaries

# Lakka 6.1 stable release (Feb 21, 2026)
LAKKA_CM4_URL="https://github.com/libretro/Lakka-LibreELEC/releases/download/v6.1/Lakka-RPi4.aarch64-6.1.img.gz"
LAKKA_ZERO_URL="https://github.com/libretro/Lakka-LibreELEC/releases/download/v6.1/Lakka-RPi3.aarch64-6.1.img.gz"
LAKKA_CM4_SHA256="9e541bd8d092c63a65c5b7c66295ff9d3c3fc073d6bb6229560526c1c505ca11"
LAKKA_ZERO_SHA256="e72cf352cbaaf0366fc7f46650b0e5335786b6119cdcaf086a0ecee2355ac742"
	LAKKA_ARM_URL="https://github.com/libretro/Lakka-LibreELEC/releases/download/v6.1/Lakka-RPi.arm-6.1.img.gz"
	LAKKA_ARM_SHA256="c331c30d4dc52fbae168d16b844c18833a1e7e790039ceb5f2d2acc6c9b09414"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --version) VERSION="$2"; shift 2 ;;
        --driver-binaries) DRIVER_BINARIES_DIR="$2"; shift 2 ;;
        --help|-h) sed -n '/^# Usage:/,/^#$/p' "$0" | head -8; exit 0 ;;
        *) echo "Unknown argument: $1"; exit 1 ;;
    esac
done

if [[ -z "$VERSION" ]]; then
    LAST_TAG="$(git -C "$PROJECT_DIR" describe --tags --abbrev=0 2>/dev/null || true)"
    VERSION="${LAST_TAG#v}"
    [[ -z "$VERSION" ]] && VERSION="0.0.0"
fi
echo "Version: $VERSION"

###############################################################################
# Cleanup stale mounts and loop devices
###############################################################################
cleanup() {
    echo "Cleaning up..."
    umount --type overlay /tmp/pspi-target 2>/dev/null || true
    umount --type squashfs /mnt/pspi-squashfs 2>/dev/null || true
    umount /mnt/pspi-boot 2>/dev/null || true
    for dev in /dev/loop{0..7}; do
        losetup -d "$dev" 2>/dev/null || true
    done
    rm -rf /tmp/pspi-upper /tmp/pspi-work /tmp/pspi-target
}

###############################################################################
# Build driver binaries and overlays
###############################################################################
build_drivers() {
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo " Building driver binaries and overlays"
    echo "═══════════════════════════════════════════════════════"

    mkdir -p "$DRIVERS_BIN_DIR"

    # Build gamepad binary (32-bit + 64-bit)
    echo "[1/5] Building gamepad binary..."
    local gamepad_dir="$PROJECT_DIR/rpi/gamepad"
    if [[ ! -d "$gamepad_dir" ]]; then
        die "Gamepad source not found at $gamepad_dir"
    fi
    (
        cd "$gamepad_dir"
        make 32 || die "Failed to build 32-bit gamepad"
        make 64 || die "Failed to build 64-bit gamepad"
    )
    cp "$gamepad_dir/bin/32bit/gamepad" "$DRIVERS_BIN_DIR/gamepad_32"
    cp "$gamepad_dir/bin/64bit/gamepad" "$DRIVERS_BIN_DIR/gamepad_64"
    echo "  Gamepad: 32-bit and 64-bit built."

    # Build battery monitor binary (32-bit + 64-bit)
    echo "[2/5] Building battery monitor..."
    local battery_dir="$PROJECT_DIR/rpi/battery"
    if [[ ! -d "$battery_dir" ]]; then
        die "Battery monitor source not found at $battery_dir"
    fi
    (
        cd "$battery_dir"
        make 32 || die "Failed to build 32-bit battery monitor"
        make 64 || die "Failed to build 64-bit battery monitor"
    )
    cp "$battery_dir/bin/32bit/battery_monitor" "$DRIVERS_BIN_DIR/battery_monitor_32"
    cp "$battery_dir/bin/64bit/battery_monitor" "$DRIVERS_BIN_DIR/battery_monitor_64"
    echo "  Battery monitor: 32-bit and 64-bit built."

    # Build audio overlays
    echo "[3/5] Building audio overlays..."
    local audio_dir="$PROJECT_DIR/rpi/audio"
    if [[ ! -d "$audio_dir" ]]; then
        die "Audio overlay source not found at $audio_dir"
    fi
    (
        cd "$audio_dir"
        make clean || true
        make all || die "Failed to build audio overlays"
    )
    mkdir -p "$OUTPUT_DIR/audio_overlays"
    cp "$audio_dir"/*.dtbo "$OUTPUT_DIR/audio_overlays/" 2>/dev/null || true
    echo "  Audio overlays built."

    # Build LCD overlays
    echo "[4/5] Building LCD overlays..."
    local lcd_dir="$PROJECT_DIR/rpi/lcd"
    if [[ ! -d "$lcd_dir" ]]; then
        die "LCD overlay source not found at $lcd_dir"
    fi
    (
        cd "$lcd_dir"
        make clean || true
        make all || die "Failed to build LCD overlays"
    )
    mkdir -p "$OUTPUT_DIR/lcd_overlays"
    cp "$lcd_dir"/*.dtbo "$OUTPUT_DIR/lcd_overlays/" 2>/dev/null || true
    echo "  LCD overlays built."

    # Build PCIe overlay
    echo "[5/5] Building PCIe overlay..."
    local pcie_dir="$PROJECT_DIR/rpi/pcie"
    if [[ ! -d "$pcie_dir" ]]; then
        die "PCIe overlay source not found at $pcie_dir"
    fi
    (
        cd "$pcie_dir"
        make clean || true
        make all || die "Failed to build PCIe overlay"
    )
    mkdir -p "$OUTPUT_DIR/pcie_overlays"
    cp "$pcie_dir"/*.dtbo "$OUTPUT_DIR/pcie_overlays/" 2>/dev/null || true
    echo "  PCIe overlay built."

    echo "Driver binaries and overlays ready."
}

###############################################################################
# Download and verify image
###############################################################################
download_image() {
    local label="$1" url="$2" sha256="$3" compressed="$4"
    mkdir -p "$CACHE_DIR"
    local cached="$CACHE_DIR/$compressed"

    if [[ -f "$cached" ]]; then
        local actual_sha
        actual_sha="$(sha256sum "$cached" | awk '{print $1}')"
        if [[ "$actual_sha" == "$sha256" ]]; then
            echo "  Checksum matches. Skipping download."
            return 0
        fi
        echo "  Checksum mismatch ($actual_sha != $sha256). Redownloading..."
        rm -f "$cached"
    fi

    echo "  Downloading $compressed..."
    cd "$CACHE_DIR"
    wget -nv -O "$compressed" "$url" || die "Failed to download $url"
    local actual_sha
    actual_sha="$(sha256sum "$cached" | awk '{print $1}')"
    [[ "$actual_sha" != "$sha256" ]] && die "Checksum mismatch: expected $sha256, got $actual_sha"
    echo "  Downloaded: $compressed ($(du -h "$cached" | cut -f1))"
    echo "  SHA256 OK"
}

###############################################################################
# Patch a Lakka image
###############################################################################
patch_lakka_image() {
    local img_path="$1" work_dir="$2" device_type="$3"

    # Detach any loop devices already associated with this image from a previous
    # incomplete run so we don't hit "overlapping loop device" errors.
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

    trap "(umount --type overlay /tmp/pspi-target 2>/dev/null || true; umount --type squashfs /mnt/pspi-squashfs 2>/dev/null || true; umount /mnt/pspi-boot 2>/dev/null || true; losetup -d $device_path 2>/dev/null || true)" RETURN

    mkdir -p /mnt/pspi-boot /mnt/pspi-squashfs /tmp/pspi-upper /tmp/pspi-work /tmp/pspi-target

    echo "    Mounting boot partition (offset 4194304)..."
    mount "$device_path" /mnt/pspi-boot || die "Failed to mount boot partition"

    echo "    Appending device-specific config to /boot/config.txt..."
    case "$device_type" in
        lakka_cm4)
            cat >> /mnt/pspi-boot/config.txt << 'EOF'
# Disable HDMI audio
hdmi_ignore_edid_audio=1

# Set framebuffer width and height for the LCD display
framebuffer_width=800
framebuffer_height=480

# Power off the Raspberry Pi when GPIO pin 44 is triggered
dtoverlay=gpio-poweroff,gpiopin=44,active_low=yes

# Enable the PCF8563 Real Time Clock module
dtoverlay=i2c-rtc,pcf8563

# Enable USB
dtoverlay=dwc2,dr_mode=host

# Disables pci-e link to prevent warning at boot
dtoverlay=disable-pcie

# Enable antenna
dtparam=ant2

# Set up CM4 audio pin
dtoverlay=pspi-audio-cm4-kernel6+

# Set minimum ARM frequency to 300
arm_freq_min=300

# Set minimum core frequency to 200
core_freq_min=200

dtoverlay=pspi-lcd-compute
EOF
            ;;
        lakka_zero|lakka_arm)
            cat >> /mnt/pspi-boot/config.txt << 'EOF'
# Disable HDMI audio
hdmi_ignore_edid_audio=1

# Set framebuffer width and height for the LCD display
framebuffer_width=800
framebuffer_height=480

# Power off the Raspberry Pi when GPIO pin 4 is triggered
dtoverlay=gpio-poweroff,gpiopin=4,active_low=yes

# Enable the PCF8563 Real Time Clock module
dtoverlay=i2c-rtc,pcf8563

# Set activity LED GPIO pin to 20
dtparam=act_led_gpio=20

# Enable audio
dtoverlay=pspi-audio-zero-kernel6+

# Controls the behavior of the activity LED on the Raspberry Pi Zero.
dtparam=act_led_activelow=no

# Set minimum ARM frequency to 500 MHz
arm_freq_min=500

# Set minimum core frequency to 200 MHz
core_freq_min=200

dtoverlay=pspi-lcd-zero
EOF
            ;;
    esac
    echo "    Creating pspi.conf..."
    cat << 'EOF' > /mnt/pspi-boot/pspi.conf
# Enable dimming after <seconds>, between 1 and 3600
enable_dim=true
dim_seconds=300
# Enable fast mode (double input polling rate on atmega)
fast_mode=false
# Disable CRC checks
disable_crc=false
# Enable the gamepad or mouse
input_type=gamepad
# Set number of joysticks, where <num> is between 0 and 2
joysticks=1

EOF

    echo "    Creating boot.sh..."
    cat << 'BOOTEOF' > /mnt/pspi-boot/boot.sh
#!/usr/bin/env bash
CONF="/flash/pspi.conf"

enable_dim=false
dim_seconds=120
fast_mode=false
disable_crc=false
input_type=gamepad
joysticks=1
while IFS="=" read -r key value; do
    [[ "$key" =~ ^#.*$ || -z "$key" ]] && continue
    key=$(echo "$key" | xargs)
    value=$(echo "$value" | xargs)
    case "$key" in
        enable_dim) enable_dim="$value" ;;
        dim_seconds) dim_seconds="$value" ;;
        fast_mode) fast_mode="$value" ;;
        disable_crc) disable_crc="$value" ;;
        input_type) input_type="$value" ;;
        joysticks) joysticks="$value" ;;
    esac
done < "$CONF"

GAMEPAD_ARGS=""
[[ "$enable_dim" == "true" ]] && GAMEPAD_ARGS="$GAMEPAD_ARGS --dim $dim_seconds"
[[ "$disable_crc" == "true" ]] && GAMEPAD_ARGS="$GAMEPAD_ARGS --nocrc"
[[ "$fast_mode" == "true" ]] && GAMEPAD_ARGS="$GAMEPAD_ARGS --fast"
[[ "$input_type" != "gamepad" ]] && GAMEPAD_ARGS="$GAMEPAD_ARGS --input $input_type"
[[ "$joysticks" != "1" ]] && GAMEPAD_ARGS="$GAMEPAD_ARGS --joysticks $joysticks"


# Auto-detect architecture for correct binaries
case $(uname -m) in
    aarch64) BIN=64 ;;
    *)       BIN=32 ;;
esac

/flash/drivers/bin/gamepad_$BIN $GAMEPAD_ARGS &
/flash/drivers/bin/battery_monitor_$BIN &
wait
BOOTEOF
    chmod +x /mnt/pspi-boot/boot.sh

    echo "    Copying overlays..."
    mkdir -p /mnt/pspi-boot/overlays
    cp "$PROJECT_DIR/rpi/audio/"*.dtbo /mnt/pspi-boot/overlays/ 2>/dev/null || true
    cp "$PROJECT_DIR/rpi/lcd/"*.dtbo /mnt/pspi-boot/overlays/ 2>/dev/null || true
    cp "$PROJECT_DIR/rpi/pcie/"*.dtbo /mnt/pspi-boot/overlays/ 2>/dev/null || true

    echo "    Copying driver binaries..."
    mkdir -p /mnt/pspi-boot/drivers/bin
    if [[ -n "$DRIVER_BINARIES_DIR" ]]; then
        cp "$DRIVER_BINARIES_DIR"/* /mnt/pspi-boot/drivers/bin/
    else
        cp "$DRIVERS_BIN_DIR"/* /mnt/pspi-boot/drivers/bin/
    fi

    echo "    Mounting SYSTEM squashfs..."
    mount --type squashfs --options loop --source /mnt/pspi-boot/SYSTEM --target /mnt/pspi-squashfs

    echo "    Mounting overlay..."
    mount --type overlay --options "lowerdir=/mnt/pspi-squashfs,upperdir=/tmp/pspi-upper,workdir=/tmp/pspi-work" --source overlay --target /tmp/pspi-target

    echo "    Creating pspi service..."
    cat << 'SVCEOF' > /tmp/pspi-target/usr/lib/systemd/system/pspi.service
[Unit]
Description=PSPi gamepad and battery monitor
After=sys-subsystem-net-devices-wlan0.device
Wants=sys-subsystem-net-devices-wlan0.device
[Service]
Type=simple
ExecStart=/flash/boot.sh
RemainAfterExit=yes
[Install]
WantedBy=multi-user.target
SVCEOF
    mkdir -p /tmp/pspi-target/usr/lib/systemd/system/multi-user.target.wants
    ln -sf ../system/pspi.service /tmp/pspi-target/usr/lib/systemd/system/multi-user.target.wants/pspi.service

    echo "    Patching retroarch.cfg..."
    sed -i 's/menu_swap_ok_cancel_buttons = "false"/menu_swap_ok_cancel_buttons = "true"/' /tmp/pspi-target/etc/retroarch.cfg
    sed -i '2927s/.*/menu_scale_factor = "1.200000"/' /tmp/pspi-target/etc/retroarch.cfg
    echo "    Repacking squashfs..."
    mksquashfs /tmp/pspi-target "$work_dir/filesystem.squashfs" -noappend -quiet

    echo "    Copying new squashfs back..."
    cp "$work_dir/filesystem.squashfs" /mnt/pspi-boot/SYSTEM
    md5sum /mnt/pspi-boot/SYSTEM > /mnt/pspi-boot/SYSTEM.md5

}

###############################################################################
# Build a full image
###############################################################################
build_image() {
    local label="$1" url sha256 compressed pspi_name work_dir

    case "$label" in
        lakka_cm4)
            url="$LAKKA_CM4_URL" sha256="$LAKKA_CM4_SHA256"
            compressed="Lakka-RPi4.aarch64-6.1.img.gz"
            pspi_name="Lakka6.1-CM4-PSPi6-v${VERSION}.img.gz" ;;
        lakka_zero)
            url="$LAKKA_ZERO_URL" sha256="$LAKKA_ZERO_SHA256"
            compressed="Lakka-RPi3.aarch64-6.1.img.gz"
            pspi_name="Lakka6.1-Zero2-PSPi6-v${VERSION}.img.gz" ;;
        lakka_arm)
            url="$LAKKA_ARM_URL" sha256="$LAKKA_ARM_SHA256"
            compressed="Lakka-RPi.arm-6.1.img.gz"
            pspi_name="Lakka6.1-PiZero1-PSPi6-v${VERSION}.img.gz" ;;
    esac

    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo " Building: $label"
    echo "═══════════════════════════════════════════════════════"

    work_dir="$(mktemp -d /tmp/pspi-build-XXXXXX)"
    mkdir -p "$OUTPUT_DIR"

    download_image "$label" "$url" "$sha256" "$compressed"

    echo "[2/5] Decompressing..."
    cd "$CACHE_DIR"
    local img_file="${compressed%.gz}"
    echo "  Removing stale .img if present..."
    rm -f "$img_file"
    if [[ -f "$compressed" ]]; then
        gunzip -c "$compressed" > "$img_file"
    else
        die "$compressed not found in cache"
    fi
    echo "  Uncompressed: $img_file ($(du -h "$img_file" | cut -f1))"

    echo "[3/5] Patching image..."
    patch_lakka_image "$CACHE_DIR/$img_file" "$work_dir" "$label"
    cp -f "$CACHE_DIR/$img_file" "$OUTPUT_DIR/${pspi_name%.gz}"
    echo "  Patched: $pspi_name"

    echo "  Raw image size: $(du -m "$OUTPUT_DIR/${pspi_name%.gz}" | cut -f1)M"
    echo "[4/5] Compressing..."
    cd "$OUTPUT_DIR"
    gzip -9f "${pspi_name%.gz}"
    echo "  Compressed: $pspi_name ($(du -h "$pspi_name" | cut -f1))"

    local file_size
    file_size="$(stat -c%s "$OUTPUT_DIR/$pspi_name")"
    if [[ $file_size -gt $((2 * 1024 * 1024 * 1024)) ]]; then
        echo "  Image > 2GB, splitting with 7z..."
        7z a "${pspi_name}.7z" "$pspi_name" -v1500M 2>/dev/null || true
        rm -f "$OUTPUT_DIR/$pspi_name"
    fi

    echo "[5/5] Generating SHA256..."
    shopt -s nullglob
    for f in "$OUTPUT_DIR"/*.img.gz "$OUTPUT_DIR"/*.7z.*; do
        sha256sum "$f" | awk '{print $1}' > "${f}.sha256"
    done
    shopt -u nullglob
    echo "  Output:"
    ls -lh "$OUTPUT_DIR"/*.img.gz "$OUTPUT_DIR"/*.sha256 "$OUTPUT_DIR"/*.7z.* 2>/dev/null || true

    cd /
    rm -rf "$work_dir"
}

###############################################################################
# Main
###############################################################################
cleanup
echo ""
echo "PSPi Version 6 — Local Image Builder"
echo "Version: $VERSION"
echo "Output:  $OUTPUT_DIR"
echo "Drivers: $DRIVERS_BIN_DIR"
echo "Cache:   $CACHE_DIR"
echo ""

# Build driver binaries and overlays (unless pre-built binaries provided)
if [[ -z "$DRIVER_BINARIES_DIR" ]]; then
    build_drivers
fi

build_image lakka_cm4
build_image lakka_zero
build_image lakka_arm


# Clean up staging dir
rm -rf "$DRIVERS_BIN_DIR"


echo ""
echo "Done. Artifacts in: $OUTPUT_DIR"


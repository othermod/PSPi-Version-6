# Raspbian Buster Lite (standard ext4 rootfs, no squashfs)
PATCH_METHOD="copy"
DRIVERS_BASE="/boot/firmware"
INIT_SYSTEM="systemd"

ALL_TARGETS=(all)

declare -A TARGET_URL TARGET_SHA256 TARGET_PSPI_PREFIX TARGET_BIN

TARGET_URL[all]="https://downloads.raspberrypi.com/raspios_oldstable_lite_armhf/images/raspios_oldstable_lite_armhf-2026-04-14/2026-04-13-raspios-bookworm-armhf-lite.img.xz"
TARGET_SHA256[all]=""
TARGET_PSPI_PREFIX[all]="Update-Firmware-PSPi6"
TARGET_BIN[all]=32

# Resolve project root from this file's location (scripts/distros/firmware.sh)
_DISTRO_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$_DISTRO_DIR/.."

distro_post_patch() {
    local rootfs_target="$1"
    local mnt_boot="$2"
    local work_dir="$3"
    local BIN="$4"

    mkdir -p "$mnt_boot/update_firmware"

    # Overwrite boot.sh with the firmware updater script
    cat > "$mnt_boot/boot.sh" << 'BOOT'
#!/usr/bin/env bash

modprobe i2c-dev

# Update the firmware.
if /boot/firmware/update_firmware/update_firmware /boot/firmware/update_firmware/firmware.hex; then
    echo "Firmware update succeeded"
    sleep 5
    /sbin/poweroff
else
    echo "Firmware update failed"
fi
BOOT
    chmod +x "$mnt_boot/boot.sh"

    # Append I2C GPIO overlay for the bootloader bus
    echo "dtoverlay=i2c-gpio,i2c_gpio_sda=2,i2c_gpio_scl=3,bus=1" >> "$mnt_boot/config.txt"

    echo "  [firmware] Copying update_firmware and firmware.hex to boot partition..."
    cp "$PROJECT_ROOT/rpi/firmware/${BIN}/update_firmware" "$mnt_boot/update_firmware/update_firmware"
    cp "$PROJECT_ROOT/atmega/firmware/firmware.hex" "$mnt_boot/update_firmware/firmware.hex"
    echo "  [firmware] Copy complete"
}

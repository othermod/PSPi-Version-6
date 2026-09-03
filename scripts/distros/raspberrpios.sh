# Raspberry Pi OS Trixie (standard ext4 rootfs, no squashfs)
PATCH_METHOD="copy"
DRIVERS_BASE="/boot/firmware"
INIT_SYSTEM="systemd"

# Raspberry Pi OS ships one image per architecture, and config.txt selects the
# correct board section at boot, so targets are split by architecture only.
#   armhf: boots on CM4, CM5, Zero 2 W, and Zero 1
#   arm64: boots on CM4, CM5, and Zero 2 W (Zero 1 is armv6 and cannot run it)
ALL_TARGETS=(arm64 armhf)

declare -A TARGET_URL TARGET_SHA256 TARGET_PSPI_PREFIX TARGET_BIN

TARGET_URL[arm64]="https://downloads.raspberrypi.com/raspios_arm64/images/raspios_arm64-2026-06-19/2026-06-18-raspios-trixie-arm64.img.xz"
TARGET_URL[armhf]="https://downloads.raspberrypi.com/raspios_armhf/images/raspios_armhf-2026-06-19/2026-06-18-raspios-trixie-armhf.img.xz"

TARGET_SHA256[arm64]="123287c05f27b0eebd8f65456f6369b8f6635fa50a3d440a4f9f6223bf58c8e2"
TARGET_SHA256[armhf]="676b4a58a75dbbe753d0af64cc97927fdba3cd7750327c6f5fccdb52b0ecc600"

TARGET_PSPI_PREFIX[arm64]="PiOS-Trixie-64bit-Zero2-CM4-CM5-PSPi6"
TARGET_PSPI_PREFIX[armhf]="PiOS-Trixie-32bit-Zero1-Zero2-CM4-CM5-PSPi6"

TARGET_BIN[arm64]=64
TARGET_BIN[armhf]=32

distro_post_patch() {
    local mnt_root="$1"
    local mnt_boot="$2"
    set_input_mouse "$mnt_boot"
    # Always launch Squeekboard at login (stock image only starts it with a touchscreen)
    if [ -f "$mnt_root/etc/xdg/autostart/squeekboard.desktop" ]; then
        sed -i 's|^Exec=/usr/bin/sbtest|Exec=/usr/bin/squeekboard|' "$mnt_root/etc/xdg/autostart/squeekboard.desktop"
    fi
}

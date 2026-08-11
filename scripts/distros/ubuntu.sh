# Ubuntu 26.04 LTS "Resolute Raccoon" — preinstalled desktop arm64 for Raspberry Pi.
#
# Standard ext4 rootfs (no squashfs), systemd init. Runtime layout:
#   boot partition -> /boot/firmware  (LABEL=system-boot, vfat)
#   rootfs         -> /               (LABEL=writable,   ext4)
#
# Two Raspberry-Pi-specific quirks of this image are handled in
# distro_post_patch below:
#
#   1. A/B "piboot-try" boot layout. config.txt sets os_prefix=current/, so the
#      bootloader resolves kernel, DTB and *device-tree overlays* from the
#      current/ directory rather than the boot root. The generic patcher places
#      the PSPi .dtbo files in overlays/ (the RaspiOS convention). We copy them
#      into current/overlays/ so the firmware can actually load them.
#
#   2. It is a desktop (GNOME on Wayland, PipeWire audio), so the gamepad is
#      configured as a mouse by default so the joystick can drive the desktop
#      cursor.
#
# This arm64 desktop image only boots on Pi 4 and Pi 5 (CM4 and CM5).
# Zero boards (armv6/armv7) cannot run it, so only those two are targets.

PATCH_METHOD="copy"
DRIVERS_BASE="/boot/firmware"
INIT_SYSTEM="systemd"

ALL_TARGETS=(all)

declare -A TARGET_URL TARGET_SHA256 TARGET_PSPI_PREFIX TARGET_BIN

TARGET_URL[all]="https://cdimage.ubuntu.com/ubuntu/releases/26.04/release/ubuntu-26.04-preinstalled-desktop-arm64+raspi.img.xz"

TARGET_SHA256[all]="c8b5d454baf26c6ed3f2a211cdd80183671aed8b67a92817cf5750e02da7f6a6"

TARGET_PSPI_PREFIX[all]="Ubuntu26.04-Desktop-CM4-CM5-PSPi6"

TARGET_BIN[all]=64

distro_post_patch() {
    local rootfs_target="$1"
    local mnt_boot="$2"
    local work_dir="$3"
    local BIN="$4"

    # Desktop default: PSPi joystick/buttons act as a mouse so they can drive
    # the GNOME/Wayland cursor (mirrors Pi OS and Kali desktop configs).
    sed -i 's/^input_type=gamepad$/input_type=mouse/' "$mnt_boot/pspi.conf"
    echo "  [ubuntu] Set input_type=mouse in pspi.conf"

    # Comment out stock Ubuntu config.txt entries that conflict with the PSPi.
    # config.txt cannot un-set a dtoverlay/dtparam from a later section, so the
    # stock lines must be edited in place. NOTE: vc4-kms-v3d and
    # disable_fw_kms_setup=1 are deliberately KEPT -- the PSPi LCD is a DPI
    # panel driven by the vc4 KMS driver, so removing them would kill the LCD.
    local cfg="$mnt_boot/config.txt"
    for entry in 'dtparam=spi=on' 'dtparam=audio=on' 'display_auto_detect=1'; do
        if grep -qE "^${entry}$" "$cfg"; then
            # shellcheck disable=SC2001
            sed -i "s|^${entry}$|# PSPi: disabled (conflicts with PSPi LCD/audio) -- was: ${entry}|" "$cfg"
            echo "  [ubuntu] Disabled stock config.txt entry: ${entry}"
        fi
    done

    # A/B boot layout: the bootloader resolves every dtoverlay= entry (PSPi
    # audio, LCD, disable-pcie) from current/overlays/ (os_prefix=current/ in
    # config.txt). The generic patcher dropped the PSPi .dtbo files in
    # overlays/; copy them over so the firmware actually loads them.
    if [[ -d "$mnt_boot/current/overlays" ]]; then
        cp -f "$mnt_boot"/overlays/*.dtbo "$mnt_boot/current/overlays/" 2>/dev/null || true
        echo "  [ubuntu] Installed PSPi overlays into current/overlays/"
    else
        echo "  [ubuntu] WARNING: current/overlays not found, PSPi overlays left in overlays/"
    fi
}

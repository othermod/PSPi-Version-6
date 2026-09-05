# Raspberry Pi OS Lite + firmware flasher (headless display — 32-bit armhf).
#
# Same base image, layout, and process as raspioslite.sh (Trixie Lite, copy
# method, systemd, /boot/firmware), with ONE difference: instead of running
# the gamepad driver, the image runs rpi/firmware/firmware — the interactive
# firmware flasher for the ATmega8 controller board. It renders a status
# screen over KMS/DRM: what bootloader/firmware is installed and its verify
# state, the candidate firmware.hex bundled on the boot partition (version,
# version match, checksum match), and a "hold display to flash" action. The
# gamepad driver is never run and the ATmega is expected in bootloader mode
# (power on with DISPLAY held), so no virtual input devices are created.
#
# I2C: the ATmega bootloader sits on the bit-banged i2c-gpio bus (GPIO2/3,
# bus 1), NOT the hardware controller — the BCM2835 core doesn't honor the
# ATmega's clock stretching. Two config.txt changes in distro_post_patch:
#   - comment out dtoverlay=i2c-rtc,pcf8563 (appended from config/config.txt
#     by the generic patcher): it claims GPIO2/3 with the hardware I2C
#     controller, and the i2c-gpio overlay then fails with EBUSY
#   - append dtoverlay=i2c-gpio,i2c_gpio_sda=2,i2c_gpio_scl=3,bus=1
#
# 32-bit: the firmware binary is cross-built for armv6 (armv6+vfp2, the same
# baseline Raspberry Pi OS armhf itself uses), so this distro ships a single
# armhf target that boots CM4, CM5, Zero 2 W, and the original Zero.
#
# Everything else is carried over from raspioslite.sh, including the headless
# first-boot login fix: Trixie Lite locks the pi user (password AND shell
# /usr/sbin/nologin) with SSH off and no first-boot dialog, so the patcher
# drops the stock image's own markers on the boot partition —
#   userconf  -> userconfig.service sets pi's shell + password on first boot
#   ssh       -> sshswitch.service enables sshd on first boot
# Resulting login: user pi, password othermod, over SSH (see raspioslite.sh
# and the Raspberry Pi OS docs for how to change the hash).

PATCH_METHOD="copy"
DRIVERS_BASE="/boot/firmware"
INIT_SYSTEM="systemd"

ALL_TARGETS=(armhf)

declare -A TARGET_URL TARGET_SHA256 TARGET_PSPI_PREFIX TARGET_BIN

# Same 2026-06-19 Trixie Lite armhf image as raspioslite.sh.
TARGET_URL[armhf]="https://downloads.raspberrypi.com/raspios_lite_armhf/images/raspios_lite_armhf-2026-06-19/2026-06-18-raspios-trixie-armhf-lite.img.xz"

TARGET_SHA256[armhf]="ea4e84c501d6dd4f4b1d04eb84df133a03f90a05ee2e8ab849185c17c2b0707b"

TARGET_PSPI_PREFIX[armhf]="Firmware-Flasher-32bit-Zero1-Zero2-CM4-CM5-PSPi6"

TARGET_BIN[armhf]=32

distro_post_patch() {
    local mnt_root="$1"
    local mnt_boot="$2"
    local work_dir="$3"
    local BIN="$4"
    # label="$5" -- not needed here

    # --- Headless first-boot login, same as raspioslite.sh: both marker
    # files are consumed and removed by the stock image's own first-boot
    # services (see write_headless_login in patcher.sh).
    write_headless_login "$mnt_boot"

    # --- Replace boot.sh. Runs the flasher in full screen. The flasher
    # powers the system off itself when the user holds the power key, so
    # the poweroff below is only reached if the flasher exits without one
    # (i.e. something went wrong). No restart loop: if the flasher died,
    # restarting it into the same broken state just obscures the cause.
    cat > "$mnt_boot/boot.sh" <<'BOOT'
#!/bin/sh

modprobe i2c-dev

cd /boot/firmware/firmware
./firmware firmware.hex

# Only reached when the flasher exited without powering off.
/sbin/poweroff
BOOT
    chmod +x "$mnt_boot/boot.sh"
    echo "  [firmware] boot.sh rewritten (flasher instead of gamepad)"

    # --- I2C: swap the hardware controller for the bit-banged bus.
    # The RTC overlay line is appended by the generic patcher (from
    # config/config.txt); commenting it out frees GPIO2/3 for i2c-gpio.
    sed -i 's|^dtoverlay=i2c-rtc,pcf8563|# dtoverlay=i2c-rtc,pcf8563 (disabled: hardware I2C conflicts with the bit-banged bus used by the flasher)|' \
        "$mnt_boot/config.txt"
    grep -q '^dtoverlay=i2c-gpio' "$mnt_boot/config.txt" || \
        echo "dtoverlay=i2c-gpio,i2c_gpio_sda=2,i2c_gpio_scl=3,bus=1" >> "$mnt_boot/config.txt"
    echo "  [firmware] config.txt: i2c-rtc disabled, i2c-gpio bit-banged bus enabled"

    # --- Copy the flasher binary and the candidate firmware image it flashes
    mkdir -p "$mnt_boot/firmware"
    if [[ -n "${DRIVER_BINARIES_DIR:-}" ]]; then
        cp "$DRIVER_BINARIES_DIR/firmware/${BIN}/firmware"      "$mnt_boot/firmware/firmware"
        cp "$DRIVER_BINARIES_DIR/atmega-firmware/firmware.hex"  "$mnt_boot/firmware/firmware.hex"
    else
        cp "$PROJECT_DIR/rpi/firmware/${BIN}/firmware"     "$mnt_boot/firmware/firmware"
        cp "$PROJECT_DIR/atmega/firmware/firmware.hex"     "$mnt_boot/firmware/firmware.hex"
    fi
    echo "  [firmware] Copying firmware flasher and firmware.hex to boot partition..."

    # --- Service adjustments. The generic pspi.service has Restart=on-failure;
    # a dead flasher shouldn't be relaunched into the same broken state, so it
    # becomes a one-shot. pspi-wifi.service is disabled entirely: wifi_monitor
    # polls the ATmega over the same (bit-banged) bus and would race the
    # flasher; the battery/wifi monitors have nothing to monitor here anyway
    # (bootloader mode, no gamepad app running).
    cat > "$mnt_root/usr/lib/systemd/system/pspi.service" <<'UNIT'
[Unit]
Description=PSPi firmware flasher

[Service]
Type=simple
WorkingDirectory=/boot/firmware/firmware
ExecStart=/boot/firmware/boot.sh
Restart=no

[Install]
WantedBy=multi-user.target
UNIT
    rm -f "$mnt_root/usr/lib/systemd/system/multi-user.target.wants/pspi-wifi.service"
    echo "  [firmware] pspi.service made one-shot; pspi-wifi.service disabled"

    # --- This image runs nothing but the flasher. The generic patcher copied
    # every driver binary (gamepad, battery_monitor, rtc, wifi_monitor,
    # troubleshooter) into drivers/; remove them so nothing can be started by
    # mistake. The battery module from the stock boot.sh is not loaded either
    # (boot.sh above replaces it wholesale).
    rm -rf "$mnt_boot/drivers"
    echo "  [firmware] Removed stock driver binaries (flasher-only image)"
}

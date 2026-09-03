# Raspberry Pi OS Lite + troubleshooter (headless display — 32-bit armhf).
#
# Same base image, layout, and process as raspioslite.sh (Trixie Lite, copy
# method, systemd, /boot/firmware), with ONE difference: instead of running
# the gamepad driver, the image runs rpi/troubleshooter. That binary reads the
# controller board directly over I2C (0x10, CRC-16-CCITT packets — same
# protocol as the gamepad driver) and renders the live pad state on the PSPi
# LCD via KMS/DRM: pressing buttons, stick deflection with deadzone, and a
# power-key popup (500 ms hold = poweroff). The gamepad driver is never run,
# so it creates no virtual input devices and gamepad input is not exposed to
# the OS — this is a controller-display image, not an input device.
#
# 32-bit: the troubleshooter binary is cross-built for armv6 (armv6+vfp2, the
# same baseline Raspberry Pi OS armhf itself uses), so this distro ships a
# single armhf target that boots CM4, CM5, Zero 2 W, and the original Zero.
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

TARGET_PSPI_PREFIX[armhf]="Troubleshooter-32bit-Zero1-Zero2-CM4-CM5-PSPi6"

TARGET_BIN[armhf]=32

distro_post_patch() {
    local mnt_root="$1"
    local mnt_boot="$2"
    # work_dir="$3", BIN="$4" -- not needed here

    # --- Headless first-boot login, same as raspioslite.sh: both marker
    # files are consumed and removed by the stock image's own first-boot
    # services (see write_headless_login in patcher.sh).
    write_headless_login "$mnt_boot"

    # --- Replace boot.sh. The generic patcher already installed the stock
    # boot.sh, which runs the gamepad driver; this image runs the
    # troubleshooter instead (copied into drivers/ by the generic patcher
    # like every other driver). The gamepad binary stays on the image but is
    # never executed, so it creates no virtual input devices and gamepad
    # input is not exposed to the OS. Same flow otherwise (battery_monitor,
    # wifi_monitor via pspi-wifi.service, restart-on-crash). No pspi.conf
    # parsing: troubleshooter takes no config args — it reads the controller
    # board directly and draws until the power key is held 500 ms (its
    # built-in shutdown) or the system is powered off via the gpio-poweroff
    # overlay in config.txt.
    cat > "$mnt_boot/boot.sh" <<'BOOT'
#!/bin/sh

modprobe i2c-dev

# Load the power_supply module where one exists (udev/UPower); silent otherwise.
modprobe pspi_battery 2>/dev/null

# Start the battery monitor early so the OS sees the battery
./drivers/battery_monitor &

# Wait for the I2C bus before starting anything that depends on it
until [ -e /dev/i2c-1 ]; do sleep 1; done

# Restart troubleshooter on crash: same backoff pattern the stock boot.sh uses
# for the gamepad. troubleshooter exits 1 before touching the display when no
# CRC-valid packet arrives, so this also covers "controller not powered yet".
# pkill before relaunch: if the visualizer died mid audio test, the tone is
# orphaned (setsid'd) and would keep playing.
(
    delay=2
    while true; do
        ./drivers/troubleshooter
        rc=$?
        echo "troubleshooter exited ($rc); restarting in ${delay}s" >&2
        pkill -x speaker-test 2>/dev/null || true
        sleep "$delay"
        if [ "$delay" -lt 60 ]; then
            delay=$(( delay * 2 ))
        else
            delay=60
        fi
    done
) &

# On systemd, pspi-wifi.service owns wifi_monitor instead.
if [ "${PSPI_WIFI_MANAGED:-}" != "1" ]; then
    ./drivers/wifi_monitor &
fi

wait
BOOT
    chmod +x "$mnt_boot/boot.sh"
    echo "  [troubleshooter] boot.sh rewritten (troubleshooter instead of gamepad)"
}
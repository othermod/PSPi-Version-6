# Raspberry Pi OS Lite + gamepad_view (headless display — 64-bit only).
#
# Same base image, layout, and process as raspioslite.sh (Trixie Lite, copy
# method, systemd, /boot/firmware), with ONE difference: instead of running
# the gamepad driver, the image runs rpi/gamepad_view. That binary reads the
# controller board directly over I2C (0x10, CRC-16-CCITT packets — same
# protocol as the gamepad driver) and renders the live pad state on the PSPi
# LCD via KMS/DRM: pressing buttons, stick deflection with deadzone, and a
# power-key popup (500 ms hold = poweroff). No USB HID gamepad is presented
# and there is no desktop cursor, so gamepad input is not exposed to the OS —
# this is a controller-display image, not an input device.
#
# 64-bit only: gamepad_view is an aarch64 build (libdrm, via the top-level
# rpi/Makefile's BUILD64 set), so this distro ships a single arm64 target
# (CM4, CM5, Zero 2 W — Zero 1 is armv6 and cannot run it).
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

ALL_TARGETS=(arm64)

declare -A TARGET_URL TARGET_SHA256 TARGET_PSPI_PREFIX TARGET_BIN

# Same 2026-06-19 Trixie Lite arm64 image as raspioslite.sh.
TARGET_URL[arm64]="https://downloads.raspberrypi.com/raspios_lite_arm64/images/raspios_lite_arm64-2026-06-19/2026-06-18-raspios-trixie-arm64-lite.img.xz"

TARGET_SHA256[arm64]="acff736ca7945e3b305f07cda4abdb870910e12634991da69783611756e381b3"

TARGET_PSPI_PREFIX[arm64]="GamepadView-64bit-CM4-CM5-Zero2-PSPi6"

TARGET_BIN[arm64]=64

distro_post_patch() {
    local mnt_root="$1"
    local mnt_boot="$2"
    # work_dir="$3", BIN="$4" -- not needed here

    # --- Headless first-boot login, same as raspioslite.sh: both marker
    # files are consumed and removed by the stock image's own first-boot
    # services (see write_headless_login in patcher.sh).
    write_headless_login "$mnt_boot"

    # --- Swap the gamepad driver for gamepad_view. The generic patcher has
    # already copied /boot/firmware/drivers/gamepad and boot.sh; both are
    # replaced here so only gamepad_view ever runs.
    rm -f "$mnt_boot/drivers/gamepad"

    # Resolve the gamepad_view binary: CI supplies it via --driver-binaries
    # (artifact "gamepad-view"), local builds produce it under the repo
    # (patcher.sh build_drivers runs `make -C rpi/gamepad_view 64`). Try both
    # artifact layouts: upload-artifact organizes a single-directory path
    # differently by version (64/gamepad_view vs gamepad_view at the root).
    local gv_src="" cand
    if [[ -n "${DRIVER_BINARIES_DIR:-}" ]]; then
        for cand in \
            "$DRIVER_BINARIES_DIR/gamepad-view/64/gamepad_view" \
            "$DRIVER_BINARIES_DIR/gamepad-view/gamepad_view"; do
            [[ -f "$cand" ]] && gv_src="$cand" && break
        done
    else
        gv_src="$PROJECT_DIR/rpi/gamepad_view/64/gamepad_view"
    fi
    [[ -n "$gv_src" && -f "$gv_src" ]] \
        || die "[gamepadview] gamepad_view binary not found under drivers-bin or the repo (run: make -C rpi/gamepad_view 64)"
    cp "$gv_src" "$mnt_boot/drivers/gamepad_view"
    chmod +x "$mnt_boot/drivers/gamepad_view"

    # boot.sh: same flow as the stock one (battery_monitor, wifi_monitor via
    # pspi-wifi.service, restart-on-crash) but gamepad_view instead of the
    # gamepad. No pspi.conf parsing: gamepad_view takes no config args — it
    # reads the controller board directly and draws until the power key is
    # held 500 ms (its built-in shutdown) or the system is powered off via
    # the gpio-poweroff overlay in config.txt.
    cat > "$mnt_boot/boot.sh" <<'BOOT'
#!/bin/sh

modprobe i2c-dev

# Load the power_supply module where one exists (udev/UPower); silent otherwise.
modprobe pspi_battery 2>/dev/null

# Start the battery monitor early so the OS sees the battery
./drivers/battery_monitor &

# Wait for the I2C bus before starting anything that depends on it
until [ -e /dev/i2c-1 ]; do sleep 1; done

# Restart gamepad_view on crash: same backoff pattern the stock boot.sh uses
# for the gamepad. gamepad_view exits 1 before touching the display when no
# CRC-valid packet arrives, so this also covers "controller not powered yet".
(
    delay=2
    while true; do
        ./drivers/gamepad_view
        rc=$?
        echo "gamepad_view exited ($rc); restarting in ${delay}s" >&2
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
    echo "  [gamepadview] Swapped gamepad -> drivers/gamepad_view; boot.sh rewritten"
}
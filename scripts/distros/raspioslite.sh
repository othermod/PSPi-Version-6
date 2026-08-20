# Raspberry Pi OS Lite (headless) — Trixie, standard ext4 rootfs, no squashfs.
#
# Same base image family as raspberrpios.sh (the desktop build) but the Lite
# variant: no desktop, no X11/Wayland, no compositor. Boot partition layout,
# config.txt handling, drivers, and systemd units are identical, so this
# config uses the generic copy-method patcher exactly as the desktop does.
# The only differences are the first-boot login story, which is broken on a
# stock Lite image and is fixed in distro_post_patch:
#
#   1. Trixie Lite ships the pi user with a LOCKED password AND shell
#      /usr/sbin/nologin, sshd disabled, and no first-boot dialog
#      (userconfig's INTERACTIVE path only runs on desktop images). A stock
#      image therefore cannot be logged into at all — deliberate on
#      Raspberry Pi's side: they expect you to pre-seed credentials with
#      rpi-imager at write time. A PSPi has no keyboard for that, so the
#      patcher must do it here.
#
#   2. distro_post_patch writes two small marker files onto the boot
#      partition, using only mechanisms the stock image itself ships:
#        - userconf -> consumed by userconfig.service on first boot, which
#          calls /usr/lib/userconf-pi/userconf pi <hash>: sets pi's shell to
#          /bin/bash, applies the SHA-512 crypt password, cancels the rename
#          nag, then deletes the file. Non-interactive when booting to the
#          console (INTERACTIVE=False); this is the same path rpi-imager's
#          credential pre-seeding uses.
#        - ssh      -> consumed by sshswitch.service on first boot, which
#          enables sshd and removes the marker. Same mechanism as "Enable
#          SSH" in rpi-imager.
#      Resulting login: user pi, password othermod, over SSH via the PSPi's
#      WiFi (stock wpa/networkd brings WiFi up at first boot). To change the
#      password, regenerate the hash and replace it below:
#          printf 'pi:<new-password>\n' | openssl passwd -6 -stdin
#      To keep SSH disabled, drop the ssh-marker creation line.
#
#   3. The gamepad stays input_type=gamepad (pspi.conf default): headless
#      means there is no desktop cursor to drive, so --input mouse would only
#      waste the buttons. Everything else boots like the desktop Trixie image.

PATCH_METHOD="copy"
DRIVERS_BASE="/boot/firmware"
INIT_SYSTEM="systemd"

# Same target split as the desktop: one image per architecture, and config.txt
# selects the board at boot. armhf boots CM4, CM5, Zero 2 W, and Zero 1;
# arm64 boots CM4, CM5, and Zero 2 W (Zero 1 is armv6 and cannot run it).
ALL_TARGETS=(arm64 armhf)

declare -A TARGET_URL TARGET_SHA256 TARGET_PSPI_PREFIX TARGET_BIN

# 2026-06-19 release (Trixie), same date as the desktop images.
TARGET_URL[arm64]="https://downloads.raspberrypi.com/raspios_lite_arm64/images/raspios_lite_arm64-2026-06-19/2026-06-18-raspios-trixie-arm64-lite.img.xz"
TARGET_URL[armhf]="https://downloads.raspberrypi.com/raspios_lite_armhf/images/raspios_lite_armhf-2026-06-19/2026-06-18-raspios-trixie-armhf-lite.img.xz"

TARGET_SHA256[arm64]="acff736ca7945e3b305f07cda4abdb870910e12634991da69783611756e381b3"
TARGET_SHA256[armhf]="ea4e84c501d6dd4f4b1d04eb84df133a03f90a05ee2e8ab849185c17c2b0707b"

TARGET_PSPI_PREFIX[arm64]="PiOS-Trixie-Lite-64bit-CM4-CM5-Zero2-PSPi6"
TARGET_PSPI_PREFIX[armhf]="PiOS-Trixie-Lite-32bit-AllBoards-PSPi6"

TARGET_BIN[arm64]=64
TARGET_BIN[armhf]=32

distro_post_patch() {
    local mnt_root="$1"
    local mnt_boot="$2"
    # work_dir="$3", BIN="$4" -- not needed here

    # Headless first-boot login, see header comment: both marker files are
    # consumed and removed by the stock image's own first-boot services so
    # nothing extra runs on the device and repeated boots are unaffected.
    write_headless_login "$mnt_boot"
}
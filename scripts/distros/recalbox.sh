PATCH_METHOD="squashfs"
SQUASHFS_PATH="boot/recalbox"
DRIVERS_BASE="/boot"
INIT_SYSTEM=sysv
SQUASHFS_COMP_ARGS="-comp xz"

ALL_TARGETS=(cm4 cm5 zero2 zero1)

declare -A TARGET_URL TARGET_SHA256 TARGET_PSPI_PREFIX TARGET_BIN

TARGET_URL[cm4]="https://upgrade.recalbox.com/latest/rpi4_64/recalbox-rpi4_64.img.xz"
TARGET_URL[cm5]="https://upgrade.recalbox.com/latest/rpi5_64/recalbox-rpi5_64.img.xz"
TARGET_URL[zero2]="https://upgrade.recalbox.com/latest/rpizero2/recalbox-rpizero2.img.xz"
TARGET_URL[zero1]="https://upgrade.recalbox.com/latest/rpi1/recalbox-rpi1.img.xz"

TARGET_SHA256[cm4]=""
TARGET_SHA256[cm5]=""
TARGET_SHA256[zero2]=""
TARGET_SHA256[zero1]=""

TARGET_PSPI_PREFIX[cm4]="Recalbox10.0.0.5-Recalbox-CM4"
TARGET_PSPI_PREFIX[cm5]="Recalbox10.0.0.5-Recalbox-CM5"
TARGET_PSPI_PREFIX[zero2]="Recalbox10.0.0.5-Recalbox-Zero2"
TARGET_PSPI_PREFIX[zero1]="Recalbox9.2.3-Recalbox-Zero1"

TARGET_BIN[cm4]=64
TARGET_BIN[cm5]=64
TARGET_BIN[zero2]=32
TARGET_BIN[zero1]=32

distro_post_patch() {
    local overlay_target="$1"
    local mnt_boot="$2"

    # Remove the gamepad proxy overlay entirely - PSPi has its own gamepad driver
    rm -f "$mnt_boot/overlays/recalbox-gamepad-proxy.dtbo"

    # Stub out all recalbox hardware detection and addon init scripts.
    # PSPi has its own drivers for everything; these scripts probe GPIOs (e.g.
    # DetectGPiCase2 claims GPIO18 via RPi.GPIO during hardware detection),
    # load conflicting overlays, and start addon daemons that are not needed.
    for script in \
        S02earlyhardware \
        S03recalbox-official-harware-detector \
        S04rrgbjamma \
        S05hardware \
        S13hardware \
        S13crt \
        S92switch
    do
        printf '#!/bin/sh\nexit 0\n' > "$overlay_target/etc/init.d/$script"
    done
}

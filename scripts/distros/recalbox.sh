SQUASHFS_PATH="boot/recalbox"
DRIVERS_BASE="/boot"
VC4_REQUIRED=false
INIT_SYSTEM=sysv
SQUASHFS_COMP_ARGS=""

ALL_TARGETS=(cm4)

declare -A TARGET_URL TARGET_SHA256 TARGET_PSPI_PREFIX TARGET_BIN

TARGET_URL[cm4]="https://upgrade.recalbox.com/latest/download-wizard/rpi4_64/recalbox-rpi4_64.img.xz"
TARGET_SHA256[cm4]=""
TARGET_PSPI_PREFIX[cm4]="Recalbox10.0.0.5-PSPi6"
TARGET_BIN[cm4]=64

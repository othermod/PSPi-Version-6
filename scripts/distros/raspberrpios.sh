# Raspberry Pi OS Trixie (standard ext4 rootfs, no squashfs)
PATCH_METHOD="copy"
DRIVERS_BASE="/boot/firmware"
INIT_SYSTEM="systemd"

ALL_TARGETS=(cm4 cm5 zero2 zero1)

declare -A TARGET_URL TARGET_SHA256 TARGET_PSPI_PREFIX TARGET_BIN

TARGET_URL[cm4]="https://downloads.raspberrypi.com/raspios_arm64/images/raspios_arm64-2026-06-19/2026-06-18-raspios-trixie-arm64.img.xz"
TARGET_URL[cm5]="https://downloads.raspberrypi.com/raspios_arm64/images/raspios_arm64-2026-06-19/2026-06-18-raspios-trixie-arm64.img.xz"
TARGET_URL[zero2]="https://downloads.raspberrypi.com/raspios_arm64/images/raspios_arm64-2026-06-19/2026-06-18-raspios-trixie-arm64.img.xz"
TARGET_URL[zero1]="https://downloads.raspberrypi.com/raspios_armhf/images/raspios_armhf-2026-06-19/2026-06-18-raspios-trixie-armhf.img.xz"

TARGET_SHA256[cm4]=""
TARGET_SHA256[cm5]=""
TARGET_SHA256[zero2]=""
TARGET_SHA256[zero1]=""

TARGET_PSPI_PREFIX[cm4]="RasPiOS-Trixie-CM4-PSPi6"
TARGET_PSPI_PREFIX[cm5]="RasPiOS-Trixie-CM5-PSPi6"
TARGET_PSPI_PREFIX[zero2]="RasPiOS-Trixie-Zero2-PSPi6"
TARGET_PSPI_PREFIX[zero1]="RasPiOS-Trixie-Zero1-PSPi6"

TARGET_BIN[cm4]=64
TARGET_BIN[cm5]=64
TARGET_BIN[zero2]=64
TARGET_BIN[zero1]=32

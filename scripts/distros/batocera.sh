# Batocera distro config for buildroot.sh
# Sourced by buildroot.sh; not run directly.
#
# To build all targets:   sudo ./scripts/buildroot.sh --distro batocera
# To build one target:    sudo ./scripts/buildroot.sh --distro batocera --target cm4

# --- Partition and filesystem layout ---

SQUASHFS_PATH="boot/batocera"  # path to squashfs within the mounted boot partition
DRIVERS_BASE="/boot"           # runtime path where drivers/ and boot.sh live on the device
VC4_REQUIRED=false             # distroconfig.txt may not exist on all Batocera builds
INIT_SYSTEM=sysv
SQUASHFS_COMP_ARGS="-comp zstd"

# --- Targets ---

ALL_TARGETS=(cm4 cm5 zero2 zero1)

declare -A TARGET_URL TARGET_SHA256 TARGET_PSPI_PREFIX TARGET_BIN

# SHA256s not yet populated upstream; skipped during download verification
TARGET_URL[cm4]="https://updates.batocera.org/bcm2711/stable/last/batocera-bcm2711-43-20260501.img.gz"
TARGET_URL[cm5]="https://updates.batocera.org/bcm2712/stable/last/batocera-bcm2712-43-20260430.img.gz"
TARGET_URL[zero2]="https://updates.batocera.org/bcm2837/stable/last/batocera-bcm2837-43-20260508.img.gz"
TARGET_URL[zero1]="https://updates.batocera.org/bcm2835/stable/last/batocera-bcm2835-43-20260507.img.gz"

TARGET_SHA256[cm4]=""
TARGET_SHA256[cm5]=""
TARGET_SHA256[zero2]=""
TARGET_SHA256[zero1]=""

TARGET_PSPI_PREFIX[cm4]="Batocera43-CM4-PSPi6"
TARGET_PSPI_PREFIX[cm5]="Batocera43-CM5-PSPi6"
TARGET_PSPI_PREFIX[zero2]="Batocera43-Zero2-PSPi6"
TARGET_PSPI_PREFIX[zero1]="Batocera43-Zero1-PSPi6"

TARGET_BIN[cm4]=64
TARGET_BIN[cm5]=64
TARGET_BIN[zero2]=64
TARGET_BIN[zero1]=32

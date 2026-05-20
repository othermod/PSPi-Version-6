# Recalbox distro config for buildroot.sh
# Sourced by buildroot.sh; not run directly.
#
# To build all targets:   sudo ./scripts/buildroot.sh --distro recalbox
# To build one target:    sudo ./scripts/buildroot.sh --distro recalbox --target cm4

# --- Partition and filesystem layout ---

SQUASHFS_PATH="boot/recalbox"  # path to squashfs within the mounted boot partition
DRIVERS_BASE="/boot"           # runtime path where drivers/ and boot.sh live on the device
VC4_REQUIRED=false             # distroconfig.txt may not exist on all Recalbox builds
INIT_SYSTEM=sysv
SQUASHFS_COMP_ARGS=""

# --- Targets ---

ALL_TARGETS=(cm4)

declare -A TARGET_URL TARGET_SHA256 TARGET_PSPI_PREFIX TARGET_BIN

TARGET_URL[cm4]="https://upgrade.recalbox.com/latest/download-wizard/rpi4_64/recalbox-rpi4_64.img.xz"
TARGET_SHA256[cm4]=""
TARGET_PSPI_PREFIX[cm4]="Recalbox10.0.0.5-PSPi6"
TARGET_BIN[cm4]=64

# Kali Linux (standard ext4 rootfs, no squashfs)
PATCH_METHOD="copy"
DRIVERS_BASE="/boot/firmware"
INIT_SYSTEM="systemd"

# Kali ships armhf and arm64 Raspberry Pi images per release.
# armhf zero2 image: boots on Zero 2 W, Zero 1, and CM4
# arm64 pi image: boots on Pi 4, Pi 400, and CM4
ALL_TARGETS=(zero2 cm4)

declare -A TARGET_URL TARGET_SHA256 TARGET_PSPI_PREFIX TARGET_BIN

TARGET_URL[zero2]="https://kali.download/arm-images/kali-2026.2/kali-linux-2026.2-raspberry-pi-zero-2-w-armhf.img.xz"
TARGET_URL[cm4]="https://kali.download/arm-images/kali-2026.2/kali-linux-2026.2-raspberry-pi-arm64.img.xz"

TARGET_SHA256[zero2]="c16ab9511353db77d9e324ba804525b047f7984025672a6ee636fd720e7a29b8"
TARGET_SHA256[cm4]="795495b65b31e567613304cdfcccf67e0e1e5d018a006fdee00a5b5d2d49d72c"

TARGET_PSPI_PREFIX[zero2]="Kali2026.2-Zero2-PSPi6"
TARGET_PSPI_PREFIX[cm4]="Kali2026.2-CM4-PSPi6"

TARGET_BIN[zero2]=32
TARGET_BIN[cm4]=64

distro_post_patch() {
    local mnt_boot="$2"
    sed -i 's/^input_type=gamepad$/input_type=mouse/' "$mnt_boot/pspi.conf"
}

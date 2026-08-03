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

# Kali's desktop reads the battery through UPower, which enumerates via udev
# and so cannot see battery_monitor's tmpfs. Build a real power_supply driver
# against the header trees the image already ships, one per installed kernel.
build_battery_module() {
    local rootfs="$1" work_dir="$2" bin="$3"
    local arch cross build_dir kver kdir

    if [[ "$bin" == "64" ]]; then
        arch="arm64"; cross="aarch64-linux-gnu-"
    else
        arch="arm";   cross="arm-linux-gnueabihf-"
    fi

    build_dir="$work_dir/pspi_battery"
    mkdir -p "$build_dir"
    cp "$PROJECT_DIR/rpi/battery/module/pspi_battery.c" "$build_dir/"
    echo "obj-m += pspi_battery.o" > "$build_dir/Makefile"

    # The arch-specific header trees include the common tree by absolute path
    # (/usr/src/linux-headers-*-common-rpi), so expose the image's trees at
    # that path on the build host for the duration of the build.
    local -a linked=()
    for tree in "$rootfs"/usr/src/linux-headers-*; do
        local name="/usr/src/$(basename "$tree")"
        # Only replace links we own; a dangling one from a failed run reads as
        # absent to -e, so test -L as well.
        if [[ -L "$name" ]]; then
            rm -f "$name"
        elif [[ -e "$name" ]]; then
            continue
        fi
        ln -s "$tree" "$name"
        linked+=("$name")
    done

    for kdir in "$rootfs"/lib/modules/*/; do
        kver="$(basename "$kdir")"
        if [[ ! -d "/usr/src/linux-headers-$kver" ]]; then
            echo "  No header tree for $kver, skipping"
            continue
        fi

        echo "  Building pspi_battery for $kver..."
        make -C "/usr/src/linux-headers-$kver" \
             M="$build_dir" ARCH="$arch" CROSS_COMPILE="$cross" modules \
             > /dev/null || die "Module build failed for $kver"

        mkdir -p "$kdir/extra"
        cp "$build_dir/pspi_battery.ko" "$kdir/extra/"
        depmod -b "$rootfs" "$kver" || die "depmod failed for $kver"
        make -C "/usr/src/linux-headers-$kver" \
             M="$build_dir" ARCH="$arch" CROSS_COMPILE="$cross" clean > /dev/null
    done

    # Stale links from an aborted run are removed on the next pass above,
    # so this only needs to handle the success path.
    if [[ ${#linked[@]} -gt 0 ]]; then
        rm -f "${linked[@]}"
    fi

    # Load at boot, before battery_monitor starts
    mkdir -p "$rootfs/etc/modules-load.d"
    echo "pspi_battery" > "$rootfs/etc/modules-load.d/pspi_battery.conf"
}

distro_post_patch() {
    local rootfs="$1" mnt_boot="$2" work_dir="$3" bin="$4"

    sed -i 's/^input_type=gamepad$/input_type=mouse/' "$mnt_boot/pspi.conf"

    build_battery_module "$rootfs" "$work_dir" "$bin"

    # Belt and braces: modules-load.d handles it, but make sure the module is
    # up before battery_monitor picks its output path.
    sed -i 's|^\./drivers/battery_monitor &$|modprobe pspi_battery 2>/dev/null\n./drivers/battery_monitor \&|' \
        "$mnt_boot/boot.sh"
}

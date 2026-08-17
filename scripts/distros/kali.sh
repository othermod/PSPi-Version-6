# Kali Linux (standard ext4 rootfs, no squashfs)
PATCH_METHOD="copy"
DRIVERS_BASE="/boot/firmware"
INIT_SYSTEM="systemd"

# Kali ships armhf and arm64 Raspberry Pi images per release.
# armhf zero2 image: boots on Zero 2 W, Zero 1, and CM4
# arm64 pi image: boots on Pi 4, Pi 400, CM4, and CM5
ALL_TARGETS=(zero2 cm4)

declare -A TARGET_URL TARGET_SHA256 TARGET_PSPI_PREFIX TARGET_BIN

TARGET_URL[zero2]="https://kali.download/arm-images/kali-2026.2/kali-linux-2026.2-raspberry-pi-zero-2-w-armhf.img.xz"
TARGET_URL[cm4]="https://kali.download/arm-images/kali-2026.2/kali-linux-2026.2-raspberry-pi-arm64.img.xz"

TARGET_SHA256[zero2]="c16ab9511353db77d9e324ba804525b047f7984025672a6ee636fd720e7a29b8"
TARGET_SHA256[cm4]="795495b65b31e567613304cdfcccf67e0e1e5d018a006fdee00a5b5d2d49d72c"

TARGET_PSPI_PREFIX[zero2]="Kali2026.2-Zero2-PSPi6"
TARGET_PSPI_PREFIX[cm4]="Kali2026.2-CM4-CM5-PSPi6"

TARGET_BIN[zero2]=32
TARGET_BIN[cm4]=64

# Kali's desktop reads the battery through UPower, which enumerates via udev
# and so cannot see battery_monitor's tmpfs. Build a real power_supply driver
# against the header trees the image already ships, one per installed kernel.
build_battery_module() {
    local rootfs="$1" work_dir="$2" bin="$3"
    local kdir kver

    # The arch-specific header trees include the common tree by absolute path
    # (/usr/src/linux-headers-*-common-rpi), so expose them there for the build.
    # Bind-mount (not symlink) so nothing is left on the host and concurrent
    # builds don't collide.
    local -a bound=()
    local tree name
    shopt -s nullglob   # no header trees must not yield a literal 'linux-headers-*'
    for tree in "$rootfs"/usr/src/linux-headers-*; do
        name="/usr/src/$(basename "$tree")"
        if [[ -e "$name" ]]; then
            echo "  Not bind-mounting $name: path already exists on host"
            continue
        fi
        mkdir -p "$name"
        mount --bind "$tree" "$name" || die "Failed to bind-mount $name"
        bound+=("$name")
    done
    shopt -u nullglob

    _kali_unbind_headers() {
        local m
        for m in "${bound[@]}"; do
            umount "$m" 2>/dev/null || umount -l "$m" 2>/dev/null || true
            rmdir "$m" 2>/dev/null || true
        done
        bound=()
    }
    # RETURN covers the normal path; EXIT covers die(). These mounts are
    # outside the patcher's work dir, so chain onto both. Idempotent.
    trap _kali_unbind_headers RETURN
    trap '_kali_unbind_headers; cleanup' EXIT

    for kdir in "$rootfs"/lib/modules/*/; do
        kver="$(basename "$kdir")"
        if [[ ! -d "/usr/src/linux-headers-$kver" ]]; then
            echo "  No header tree for $kver, skipping"
            continue
        fi
        build_battery_module_from_headers \
            "/usr/src/linux-headers-$kver" "$kver" "$rootfs" "$work_dir" "$bin"
    done

    _kali_unbind_headers
    trap cleanup EXIT

    enable_battery_module_at_boot "$rootfs"
}

distro_post_patch() {
    local rootfs="$1" mnt_boot="$2" work_dir="$3" bin="$4"

    set_input_mouse "$mnt_boot"

    # Kali's cloud-init generator sometimes fails to pull cloud-init.target
    # into the boot transaction, so the first-boot rootfs resize never runs.
    # Enable it statically; the units self-disable via ConditionPathExists
    # once the first run completes.
    mkdir -p "$rootfs/etc/systemd/system/multi-user.target.wants"
    ln -sf /lib/systemd/system/cloud-init.target \
        "$rootfs/etc/systemd/system/multi-user.target.wants/cloud-init.target"

    build_battery_module "$rootfs" "$work_dir" "$bin"
}

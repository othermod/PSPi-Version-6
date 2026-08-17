# Ubuntu 26.04 LTS "Resolute Raccoon" — preinstalled desktop arm64 for Raspberry Pi.
#
# Standard ext4 rootfs (no squashfs), systemd init. Runtime layout:
#   boot partition -> /boot/firmware  (LABEL=system-boot, vfat)
#   rootfs         -> /               (LABEL=writable,   ext4)
#
# Two Raspberry-Pi-specific quirks of this image are handled in
# distro_post_patch below:
#
#   1. A/B "piboot-try" boot layout. config.txt sets os_prefix=current/, so the
#      bootloader resolves kernel, DTB and *device-tree overlays* from the
#      current/ directory rather than the boot root. BOOT_OVERLAYS_DIR below
#      points the generic patcher straight at current/overlays/, so the PSPi
#      .dtbo files are written to the directory the firmware actually reads.
#
#   2. It is a desktop (GNOME on Wayland, PipeWire audio), so the gamepad is
#      configured as a mouse by default so the joystick can drive the desktop
#      cursor.
#
# This arm64 desktop image only boots on Pi 4 and Pi 5 (CM4 and CM5).
# Zero boards (armv6/armv7) cannot run it, so only those two are targets.

PATCH_METHOD="copy"
DRIVERS_BASE="/boot/firmware"
INIT_SYSTEM="systemd"

# A/B "piboot-try" layout: config.txt sets os_prefix=current/, so the firmware
# resolves every dtoverlay= entry from current/overlays rather than the boot
# root. Declaring it here means the generic patcher writes the .dtbo files
# straight to the location the firmware reads, and fails if it is absent.
BOOT_OVERLAYS_DIR="current/overlays"

ALL_TARGETS=(all)

declare -A TARGET_URL TARGET_SHA256 TARGET_PSPI_PREFIX TARGET_BIN

TARGET_URL[all]="https://cdimage.ubuntu.com/ubuntu/releases/26.04/release/ubuntu-26.04-preinstalled-desktop-arm64+raspi.img.xz"

TARGET_SHA256[all]="c8b5d454baf26c6ed3f2a211cdd80183671aed8b67a92817cf5750e02da7f6a6"

TARGET_PSPI_PREFIX[all]="Ubuntu26.04-Desktop-CM4-CM5-PSPi6"

TARGET_BIN[all]=64

# Build pspi_battery.ko on the host. Ubuntu's preinstalled image ships no
# kernel headers, so fetch the matching linux-headers debs from the arm64
# archive and cross-compile against them. The raspi headers ship prebuilt
# arm64 build tools (modpost) that run under QEMU via libc6-arm64-cross's
# loader (QEMU_LD_PREFIX) -- same trick Kali uses.
# Host deps: gcc-14/15-aarch64-linux-gnu (>=14 for -fmin-function-alignment),
#            libc6-arm64-cross, kmod (depmod), qemu-user-static, binfmt-support
build_battery_module() {
    local rootfs="$1" work_dir="$2"

    # Resolve the installed kernel version from the image's own module dir
    local kver=""
    for kd in "$rootfs"/lib/modules/*/; do
        [[ -d "$kd" ]] && kver="$(basename "$kd")" && break
    done
    [[ -z "$kver" ]] && die "[ubuntu] No kernel module dir found in $rootfs/lib/modules"
    local front="${kver%-raspi}"   # e.g. 7.0.0-1009
    echo "  [ubuntu] Building battery module for kernel $kver"

    # A recent-enough aarch64 cross gcc (>= 14 for -fmin-function-alignment).
    local cc="" c
    for c in aarch64-linux-gnu-gcc-15 aarch64-linux-gnu-gcc-14; do
        if command -v "$c" >/dev/null 2>&1; then cc="$c"; break; fi
    done
    [[ -n "$cc" ]] || die "[ubuntu] No aarch64 gcc >=14 found. Install gcc-14-aarch64-linux-gnu"
    local tccbin="$work_dir/tccbin"; mkdir -p "$tccbin"
    ln -sf "$(command -v "$cc")" "$tccbin/aarch64-linux-gnu-gcc"

    [[ -d /usr/aarch64-linux-gnu ]] \
        || die "[ubuntu] libc6-arm64-cross not installed (QEMU loader). Run: apt install libc6-arm64-cross"

    # Resolve from the archive package index (not an HTML listing) so a
    # format change or newer ABI can't silently misselect.
    local pool="http://ports.ubuntu.com/ubuntu-ports/pool/main/l/linux-raspi"
    local index arch_deb common_deb
    index="$(curl -fsS "$pool/" 2>/dev/null || true)"
    [[ -n "$index" ]] || die "[ubuntu] Could not reach $pool (network?)"

    # Match the exact kernel version; take the highest build of it.
    arch_deb="$(printf '%s\n' "$index" \
        | grep -oE "linux-headers-${kver}_[0-9][^\"<> ]*_arm64\.deb" | sort -Vu | tail -1)"
    common_deb="$(printf '%s\n' "$index" \
        | grep -oE "linux-raspi-headers-${front}_[0-9][^\"<> ]*_arm64\.deb" | sort -Vu | tail -1)"
    [[ -n "$arch_deb" ]] \
        || die "[ubuntu] No linux-headers package for kernel $kver in the archive"
    [[ -n "$common_deb" ]] \
        || die "[ubuntu] No linux-raspi-headers package for $front in the archive"
    echo "  [ubuntu] Using $arch_deb and $common_deb"

    local hdr_root="$work_dir/hdr" HDR
    mkdir -p "$hdr_root"
    wget -q "$pool/$arch_deb"   -O "$hdr_root/$arch_deb"   || die "[ubuntu] failed to download $arch_deb"
    wget -q "$pool/$common_deb" -O "$hdr_root/$common_deb" || die "[ubuntu] failed to download $common_deb"
    dpkg-deb -x "$hdr_root/$arch_deb"   "$hdr_root/root"
    dpkg-deb -x "$hdr_root/$common_deb" "$hdr_root/root"
    HDR="$hdr_root/root/usr/src/linux-headers-${kver}"
    [[ -d "$HDR" ]]              || die "[ubuntu] Extracted header tree not found at $HDR"
    [[ -f "$HDR/.config" ]]      || die "[ubuntu] Header tree missing .config: $HDR"

    # Build and install (modpost runs under QEMU via the cross-gcc PATH + loader)
    PATH="$tccbin:$PATH" \
        build_battery_module_from_headers "$HDR" "$kver" "$rootfs" "$work_dir" 64

    enable_battery_module_at_boot "$rootfs"
    echo "  [ubuntu] Installed pspi_battery.ko for $kver + modules-load.d entry"
}

distro_post_patch() {
    local rootfs_target="$1"
    local mnt_boot="$2"
    local work_dir="$3"
    local BIN="$4"

    # Desktop default: PSPi joystick/buttons act as a mouse so they can drive
    # the GNOME/Wayland cursor (mirrors Pi OS and Kali desktop configs).
    set_input_mouse "$mnt_boot"

    # Comment out stock Ubuntu config.txt entries that conflict with the PSPi.
    # config.txt can't un-set a dtoverlay/dtparam later, so edit in place.
    # vc4-kms-v3d and disable_fw_kms_setup=1 are KEPT -- the PSPi LCD is a DPI
    # panel driven by the vc4 KMS driver.
    local cfg="$mnt_boot/config.txt"
    for entry in 'dtparam=spi=on' 'dtparam=audio=on' 'display_auto_detect=1'; do
        if grep -qE "^${entry}$" "$cfg"; then
            # shellcheck disable=SC2001
            sed -i "s|^${entry}$|# PSPi: disabled (conflicts with PSPi LCD/audio) -- was: ${entry}|" "$cfg"
            echo "  [ubuntu] Disabled stock config.txt entry: ${entry}"
        fi
    done

    # GNOME/UPower reads the battery via udev, so build the real power_supply
    # module (battery_monitor auto-switches to it).
    build_battery_module "$rootfs_target" "$work_dir"

    # GNOME's built-in on-screen keyboard shows only when the a11y setting
    # screen-keyboard-enabled is true. Enable it system-wide via a locked dconf
    # override so every user (including first-boot wizard accounts) gets it.
    mkdir -p "$rootfs_target/etc/dconf/profile" \
             "$rootfs_target/etc/dconf/db/local.d/locks"
    cat > "$rootfs_target/etc/dconf/profile/user" <<'PROFILE'
user-db:user
system-db:local
PROFILE
    cat > "$rootfs_target/etc/dconf/db/local.d/00-pspi-osk" <<'OSKDB'
[org/gnome/desktop/a11y/applications]
screen-keyboard-enabled=true
OSKDB
    cat > "$rootfs_target/etc/dconf/db/local.d/locks/00-pspi-osk" <<'OSKLOCK'
/org/gnome/desktop/a11y/applications/screen-keyboard-enabled
OSKLOCK
    # Keep the desktop from auto-locking/suspending on idle (would land on the
    # GDM login screen, awkward with the OSK on the small LCD). Dimming stays
    # enabled; lock+sleep turned off but NOT locked so the user can re-enable.
    mkdir -p "$rootfs_target/etc/dconf/db/local.d"
    cat > "$rootfs_target/etc/dconf/db/local.d/01-pspi-idle" <<'IDLE'
[org/gnome/desktop/screensaver]
lock-enabled=false

[org/gnome/settings-daemon/plugins/power]
sleep-inactive-ac-type='nothing'
sleep-inactive-battery-type='nothing'
IDLE
    echo "  [ubuntu] Forced on-screen keyboard (dconf override + lock); disabled idle lock/suspend"

    # Default account (ubuntu/othermod) so the first-boot wizard isn't required.
    # Stock user-data has `users: []`, which forces the interactive
    # gnome-initial-setup wizard. Replace it so cloud-init creates the user, and
    # disable the wizard in GDM.
    local ud="$mnt_boot/user-data"
    if [[ -f "$ud" ]]; then
        python3 - "$ud" <<'PY'
import re, sys
p = sys.argv[1]
s = open(p).read()
block = (
"users:\n"
"  - name: ubuntu\n"
"    gecos: Ubuntu\n"
"    groups: [adm, audio, cdrom, dialout, dip, floppy, netdev, plugdev, sudo, video]\n"
"    sudo: ALL=(ALL) NOPASSWD:ALL\n"
"    shell: /bin/bash\n"
"    lock_passwd: false\n"
"    plain_text_passwd: othermod\n")
if re.search(r'^\s*name:\s*ubuntu\s*$', s, re.M):
    print("  [ubuntu] user already defined in user-data, skipping")
else:
    s2 = re.sub(r'^users:\s*\[\s*\]\s*$', block, s, count=1, flags=re.M)
    if s2 == s:
        print("  [ubuntu] WARNING: could not find 'users: []' in user-data, skipping")
    else:
        open(p, 'w').write(s2)
        print("  [ubuntu] cloud-init will create ubuntu/othermod on first boot")
PY
    fi
    local gdmc="$rootfs_target/etc/gdm3/custom.conf"
    if [[ -f "$gdmc" ]]; then
        # Auto-login ubuntu and disable the first-boot wizard. Each entry is
        # inserted after [daemon] if not already present.
        grep -q '^AutomaticLoginEnable' "$gdmc" \
            || sed -i '/^\[daemon\]/a AutomaticLoginEnable=true' "$gdmc"
        grep -q '^AutomaticLogin=' "$gdmc" \
            || sed -i '/^\[daemon\]/a AutomaticLogin=ubuntu' "$gdmc"
        grep -q '^InitialSetupEnable' "$gdmc" \
            || sed -i '/^\[daemon\]/a InitialSetupEnable=false' "$gdmc"
        echo "  [ubuntu] GDM: autologin=ubuntu, first-boot wizard disabled"
    fi
}

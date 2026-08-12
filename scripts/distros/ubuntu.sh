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
#      current/ directory rather than the boot root. The generic patcher places
#      the PSPi .dtbo files in overlays/ (the RaspiOS convention). We copy them
#      into current/overlays/ so the firmware can actually load them.
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

ALL_TARGETS=(all)

declare -A TARGET_URL TARGET_SHA256 TARGET_PSPI_PREFIX TARGET_BIN

TARGET_URL[all]="https://cdimage.ubuntu.com/ubuntu/releases/26.04/release/ubuntu-26.04-preinstalled-desktop-arm64+raspi.img.xz"

TARGET_SHA256[all]="c8b5d454baf26c6ed3f2a211cdd80183671aed8b67a92817cf5750e02da7f6a6"

TARGET_PSPI_PREFIX[all]="Ubuntu26.04-Desktop-CM4-CM5-PSPi6"

TARGET_BIN[all]=64

# Build the pspi_battery kernel module for the image's specific kernel by
# cross-compiling on the host (Option B). The preinstalled Ubuntu image ships
# NO kernel headers (unlike Kali), so we fetch the matching linux-headers
# packages from the Ubuntu arm64 archive, extract them into a scratch tree,
# and build against them with an aarch64 cross gcc.
#
# The raspi headers ship PREBUILT arm64 build tools (scripts/mod/modpost), which
# run on this x86_64 host under QEMU -- so qemu-user-static/binfmt plus
# libc6-arm64-cross (the loader at /usr/aarch64-linux-gnu) are required, wired
# up via QEMU_LD_PREFIX (the same trick Kali uses).
#
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

    # A recent-enough aarch64 cross gcc (gcc >= 14 understands the kernel's
    # -fmin-function-alignment flag)
    local cc="" c
    for c in aarch64-linux-gnu-gcc-15 aarch64-linux-gnu-gcc-14; do
        if command -v "$c" >/dev/null 2>&1; then cc="$c"; break; fi
    done
    [[ -n "$cc" ]] || die "[ubuntu] No aarch64 gcc >=14 found. Install gcc-14-aarch64-linux-gnu"
    local tccbin="$work_dir/tccbin"; mkdir -p "$tccbin"
    ln -sf "$(command -v "$cc")" "$tccbin/aarch64-linux-gnu-gcc"

    [[ -d /usr/aarch64-linux-gnu ]] \
        || die "[ubuntu] libc6-arm64-cross not installed (QEMU loader). Run: apt install libc6-arm64-cross"

    # Fetch the matching header packages from the Ubuntu arm64 archive
    local pool="http://ports.ubuntu.com/ubuntu-ports/pool/main/l/linux-raspi"
    local listing arch_deb common_deb
    listing="$(curl -fsS "$pool/" 2>/dev/null || true)"
    [[ -n "$listing" ]] || die "[ubuntu] Could not list $pool (network?)"
    arch_deb="$(printf '%s\n' "$listing" | grep -oE "linux-headers-${kver}_[^\"<> ]+_arm64\.deb" | sort -Vu | tail -1)"
    common_deb="$(printf '%s\n' "$listing" | grep -oE "linux-raspi-headers-${front}_[^\"<> ]+_arm64\.deb" | sort -Vu | tail -1)"
    [[ -n "$arch_deb" && -n "$common_deb" ]] \
        || die "[ubuntu] Could not find header packages for $kver in Ubuntu archive"

    local hdr_root="$work_dir/hdr" HDR
    mkdir -p "$hdr_root"
    wget -q "$pool/$arch_deb"   -O "$hdr_root/$arch_deb"   || die "[ubuntu] failed to download $arch_deb"
    wget -q "$pool/$common_deb" -O "$hdr_root/$common_deb" || die "[ubuntu] failed to download $common_deb"
    dpkg-deb -x "$hdr_root/$arch_deb"   "$hdr_root/root"
    dpkg-deb -x "$hdr_root/$common_deb" "$hdr_root/root"
    HDR="$hdr_root/root/usr/src/linux-headers-${kver}"
    [[ -d "$HDR" ]]              || die "[ubuntu] Extracted header tree not found at $HDR"
    [[ -f "$HDR/.config" ]]      || die "[ubuntu] Header tree missing .config: $HDR"

    # Build the module (modpost runs under QEMU via the cross-gcc PATH + loader)
    local bdir="$work_dir/pspi_battery"
    mkdir -p "$bdir"
    cp "$PROJECT_DIR/rpi/battery/module/pspi_battery.c" "$bdir/"
    echo 'obj-m += pspi_battery.o' > "$bdir/Makefile"
    PATH="$tccbin:$PATH" QEMU_LD_PREFIX=/usr/aarch64-linux-gnu \
        make -C "$HDR" M="$bdir" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- modules \
        >/dev/null 2>&1 || die "[ubuntu] pspi_battery module build failed"
    [[ -f "$bdir/pspi_battery.ko" ]] || die "[ubuntu] pspi_battery.ko was not produced"

    # Install into the image and refresh module metadata
    local kdir="$rootfs/lib/modules/$kver"
    mkdir -p "$kdir/extra"
    cp "$bdir/pspi_battery.ko" "$kdir/extra/"
    depmod -b "$rootfs" "$kver" || die "[ubuntu] depmod failed for $kver"

    # Load early (before battery_monitor starts, which auto-detects the module)
    mkdir -p "$rootfs/etc/modules-load.d"
    echo "pspi_battery" > "$rootfs/etc/modules-load.d/pspi_battery.conf"
    echo "  [ubuntu] Installed pspi_battery.ko for $kver + modules-load.d entry"
}

distro_post_patch() {
    local rootfs_target="$1"
    local mnt_boot="$2"
    local work_dir="$3"
    local BIN="$4"

    # Desktop default: PSPi joystick/buttons act as a mouse so they can drive
    # the GNOME/Wayland cursor (mirrors Pi OS and Kali desktop configs).
    sed -i 's/^input_type=gamepad$/input_type=mouse/' "$mnt_boot/pspi.conf"
    echo "  [ubuntu] Set input_type=mouse in pspi.conf"

    # Comment out stock Ubuntu config.txt entries that conflict with the PSPi.
    # config.txt cannot un-set a dtoverlay/dtparam from a later section, so the
    # stock lines must be edited in place. NOTE: vc4-kms-v3d and
    # disable_fw_kms_setup=1 are deliberately KEPT -- the PSPi LCD is a DPI
    # panel driven by the vc4 KMS driver, so removing them would kill the LCD.
    local cfg="$mnt_boot/config.txt"
    for entry in 'dtparam=spi=on' 'dtparam=audio=on' 'display_auto_detect=1'; do
        if grep -qE "^${entry}$" "$cfg"; then
            # shellcheck disable=SC2001
            sed -i "s|^${entry}$|# PSPi: disabled (conflicts with PSPi LCD/audio) -- was: ${entry}|" "$cfg"
            echo "  [ubuntu] Disabled stock config.txt entry: ${entry}"
        fi
    done

    # A/B boot layout: the bootloader resolves every dtoverlay= entry (PSPi
    # audio, LCD, disable-pcie) from current/overlays/ (os_prefix=current/ in
    # config.txt). The generic patcher dropped the PSPi .dtbo files in
    # overlays/; copy them over so the firmware actually loads them.
    if [[ -d "$mnt_boot/current/overlays" ]]; then
        cp -f "$mnt_boot"/overlays/*.dtbo "$mnt_boot/current/overlays/" 2>/dev/null || true
        echo "  [ubuntu] Installed PSPi overlays into current/overlays/"
    else
        echo "  [ubuntu] WARNING: current/overlays not found, PSPi overlays left in overlays/"
    fi

    # GNOME/UPower reads the battery via udev, so the tmpfs fallback is
    # invisible on this desktop. Build + install the real power_supply kernel
    # module for the image's kernel (battery_monitor auto-switches to it).
    build_battery_module "$rootfs_target" "$work_dir"

    # Belt-and-braces: make sure the module is up before battery_monitor picks
    # its output path (modules-load.d already handles it).
    sed -i 's|^\./drivers/battery_monitor &$|modprobe pspi_battery 2>/dev/null\n./drivers/battery_monitor \&|' \
        "$mnt_boot/boot.sh"

    # On-screen keyboard: GNOME Shell ships a built-in keyboard (no separate
    # Squeekboard like Raspberry Pi OS) shown only when the accessibility
    # setting org.gnome.desktop.a11y.applications screen-keyboard-enabled is
    # true. Enable it system-wide and lock it so every user (including one
    # created by the first-boot wizard) gets it, regardless of touchscreen --
    # the canonical GNOME dconf-override mechanism.
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
    # Keep the desktop from auto-locking / suspending on idle, which would land
    # on the GDM login screen (awkward with the on-screen keyboard on the small
    # LCD). Screen dimming/blanking is left enabled -- only the lock, and the
    # whole-system suspension on idle, are turned off. Deliberately NOT locked
    # so the end user can still enable locking/suspend in Settings if desired.
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
    # Ubuntu's preinstalled desktop ships NoCloud user-data with `users: []`,
    # which tells cloud-init to create NO user and instead forces the interactive
    # gnome-initial-setup wizard (which builds the account on screen). We:
    #   1. replace `users: []` so cloud-init creates the `ubuntu` user with
    #      password `othermod` on first boot (keeps the swap config intact), and
    #   2. set GDM InitialSetupEnable=false so the wizard never runs.
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
        # Auto-login the ubuntu user so it boots straight to the desktop, and
        # disable the first-boot setup wizard. Each entry is inserted after the
        # [daemon] header if not already present (no duplicate lines).
        grep -q '^AutomaticLoginEnable' "$gdmc" \
            || sed -i '/^\[daemon\]/a AutomaticLoginEnable=true' "$gdmc"
        grep -q '^AutomaticLogin=' "$gdmc" \
            || sed -i '/^\[daemon\]/a AutomaticLogin=ubuntu' "$gdmc"
        grep -q '^InitialSetupEnable' "$gdmc" \
            || sed -i '/^\[daemon\]/a InitialSetupEnable=false' "$gdmc"
        echo "  [ubuntu] GDM: autologin=ubuntu, first-boot wizard disabled"
    fi
}

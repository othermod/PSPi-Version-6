# RetroPie (built from Raspberry Pi OS Lite via QEMU chroot)
#
# This distro config downloads stock Pi OS Lite, expands the image,
# installs RetroPie inside a QEMU chroot, then applies PSPi6 patches.
#
# Prerequisites (host):
#   apt install qemu-user-static binfmt-support e2fsprogs
#
# Build:
#   sudo ./scripts/patcher.sh --distro retropie [--target <zero1|zero2|cm4|cm5>]

PATCH_METHOD="copy"
DRIVERS_BASE="/boot/firmware"
INIT_SYSTEM="systemd"

ALL_TARGETS=(zero1 zero2 cm4 cm5)

declare -A TARGET_URL TARGET_SHA256 TARGET_PSPI_PREFIX TARGET_BIN TARGET_RP_PLATFORM

# zero1 (armv6) uses the 32-bit armhf image; zero2/cm4/cm5 share the 64-bit arm64 image.
TARGET_URL[zero1]="https://downloads.raspberrypi.com/raspios_oldstable_lite_armhf/images/raspios_oldstable_lite_armhf-2026-04-14/2026-04-13-raspios-bookworm-armhf-lite.img.xz"
TARGET_URL[zero2]="https://downloads.raspberrypi.com/raspios_oldstable_lite_arm64/images/raspios_oldstable_lite_arm64-2026-04-14/2026-04-13-raspios-bookworm-arm64-lite.img.xz"
TARGET_URL[cm4]="https://downloads.raspberrypi.com/raspios_oldstable_lite_arm64/images/raspios_oldstable_lite_arm64-2026-04-14/2026-04-13-raspios-bookworm-arm64-lite.img.xz"
TARGET_URL[cm5]="https://downloads.raspberrypi.com/raspios_oldstable_lite_arm64/images/raspios_oldstable_lite_arm64-2026-04-14/2026-04-13-raspios-bookworm-arm64-lite.img.xz"

TARGET_SHA256[zero1]=""
TARGET_SHA256[zero2]=""
TARGET_SHA256[cm4]=""
TARGET_SHA256[cm5]=""

TARGET_PSPI_PREFIX[zero1]="RetroPie-Bookworm-32bit-Zero1-PSPi6"
TARGET_PSPI_PREFIX[zero2]="RetroPie-Bookworm-64bit-Zero2-PSPi6"
TARGET_PSPI_PREFIX[cm4]="RetroPie-Bookworm-64bit-CM4-PSPi6"
TARGET_PSPI_PREFIX[cm5]="RetroPie-Bookworm-64bit-CM5-PSPi6"

TARGET_BIN[zero1]=32
TARGET_BIN[zero2]=64
TARGET_BIN[cm4]=64
TARGET_BIN[cm5]=64

# RetroPie __platform per board (controls which prebuilt cores get installed)
TARGET_RP_PLATFORM[zero1]="rpi1"
TARGET_RP_PLATFORM[zero2]="rpi3"
TARGET_RP_PLATFORM[cm4]="rpi4"
TARGET_RP_PLATFORM[cm5]="rpi5"

# --- QEMU chroot helpers ---

_retropie_setup_binfmt() {
    local arch="$1"
    local qemu_bin

    if [[ "$arch" == "64" ]]; then
        qemu_bin="qemu-aarch64-static"
    else
        qemu_bin="qemu-arm-static"
    fi

    # Native arch -- no emulation needed
    local host_arch
    host_arch="$(uname -m)"
    if [[ "$host_arch" == "aarch64" && "$arch" == "64" ]]; then
        echo ""
        return
    elif [[ "$host_arch" == armv7* && "$arch" == "32" ]]; then
        echo ""
        return
    fi

    command -v "$qemu_bin" >/dev/null 2>&1 \
        || die "$qemu_bin not found. Install qemu-user-static."

    # Mount binfmt_misc if needed
    if [[ ! -d /proc/sys/fs/binfmt_misc/register ]]; then
        mount -t binfmt_misc binfmt_misc /proc/sys/fs/binfmt_misc 2>/dev/null || true
    fi

    # Register the handler if not already present
    if [[ ! -f "/proc/sys/fs/binfmt_misc/$qemu_bin" ]]; then
        if [[ "$arch" == "64" ]]; then
            printf '%s' ':qemu-aarch64:M::\x7fELF\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\xb7\x00:\xff\xff\xff\xff\xff\xff\xff\x00\xff\xff\xff\xff\xff\xff\xff\xff\xfe\xff\xff\xff:/usr/bin/qemu-aarch64-static:F' \
                > /proc/sys/fs/binfmt_misc/register
        else
            printf '%s' ':qemu-arm:M::\x7fELF\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x28\x00:\xff\xff\xff\xff\xff\xff\xff\x00\xff\xff\xff\xff\xff\xff\xff\xff\xfe\xff\xff\xff:/usr/bin/qemu-arm-static:F' \
                > /proc/sys/fs/binfmt_misc/register
        fi
    fi

    echo "$qemu_bin"
}

_retropie_enter_chroot() {
    local rootfs="$1" qemu_bin="$2"

    [[ -n "$qemu_bin" ]] && cp "$(command -v "$qemu_bin")" "$rootfs/usr/bin/"
    # Prevent mount propagation from leaking to the host (critical in Docker)
    mount --make-rprivate "$rootfs"
    mount -t proc proc "$rootfs/proc"
    mount -t sysfs sysfs "$rootfs/sys"
    # Use tmpfs instead of devtmpfs to avoid sharing the host's /dev.
    # devtmpfs is a single kernel-wide instance -- rm -rf during cleanup
    # would delete real device nodes from the host.
    mount -t tmpfs -o mode=755 tmpfs "$rootfs/dev"
    mknod -m 666 "$rootfs/dev/null"    c 1 3
    mknod -m 666 "$rootfs/dev/zero"    c 1 5
    mknod -m 666 "$rootfs/dev/full"    c 1 7
    mknod -m 444 "$rootfs/dev/random"  c 1 8
    mknod -m 444 "$rootfs/dev/urandom" c 1 9
    mknod -m 666 "$rootfs/dev/tty"     c 5 0
    mknod -m 600 "$rootfs/dev/console" c 5 1
    mkdir -p "$rootfs/dev/pts" "$rootfs/dev/shm"
    mount -t devpts devpts "$rootfs/dev/pts"
    ln -s /proc/self/fd "$rootfs/dev/fd"
    ln -s pts/ptmx "$rootfs/dev/ptmx"
    cp /etc/resolv.conf "$rootfs/etc/resolv.conf"
    export HOME=/root
}

_retropie_exit_chroot() {
    local rootfs="$1" qemu_bin="$2"

    # Detach nested mounts (dev/pts, devtmpfs/tmpfs, sys, proc) first so the
    # rootfs can be cleanly unmounted and its buffers flushed on loop detach.
    umount -l "$rootfs/dev/pts" 2>/dev/null || true
    umount -l "$rootfs/dev/shm" 2>/dev/null || true
    umount -l "$rootfs/dev" 2>/dev/null || true
    umount -l "$rootfs/sys" 2>/dev/null || true
    umount -l "$rootfs/proc" 2>/dev/null || true
    sync
    [[ -n "$qemu_bin" ]] && rm -f "$rootfs/usr/bin/$qemu_bin"
}

# --- Hooks ---

distro_pre_patch() {
    local img_path="$1"

    echo "  [retropie] Expanding image by 4GB for RetroPie install..."
    truncate -s +4G "$img_path"

    # Get rootfs partition start sector
    local root_start
    root_start=$(python3 - "$img_path" <<'PY'
import struct, sys
with open(sys.argv[1], 'rb') as f:
    f.seek(446 + 16)
    lba = struct.unpack_from('<I', f.read(16), 8)[0]
print(lba)
PY
    )

    # Recreate partition 2 to fill available space
    echo -e "d\n2\nn\np\n2\n${root_start}\n\nw" | fdisk "$img_path" >/dev/null 2>&1 || true

    # Resize the filesystem (mount briefly just for resize2fs)
    local resize_dev=""
    for dev in /dev/loop{0..7}; do
        if losetup -o $((root_start * 512)) "$dev" "$img_path" 2>/dev/null; then
            resize_dev="$dev"
            break
        fi
    done
    [[ -z "$resize_dev" ]] && die "No available loop device for resize"

    e2fsck -fy "$resize_dev" >/dev/null 2>&1 || true
    resize2fs "$resize_dev" >/dev/null 2>&1
    losetup -d "$resize_dev"

    echo "  [retropie] Image expanded"
}

distro_post_patch() {
    local rootfs="$1"
    local mnt_boot="$2"
    local work_dir="$3"
    local BIN="$4"
    local LABEL="$5"

    local qemu_bin
    qemu_bin=$(_retropie_setup_binfmt "$BIN")

    # RetroPie platform mapping (per-board: controls which prebuilt cores get installed)
    local rp_platform="${TARGET_RP_PLATFORM[$LABEL]:-rpi4}"

    _retropie_enter_chroot "$rootfs" "$qemu_bin"

    # Create the pi user if missing (base image usually already has one, but
    # locked, awaiting the first-boot wizard)
    if ! chroot "$rootfs" id pi >/dev/null 2>&1; then
        echo "  [retropie] Creating user 'pi'..."
        chroot "$rootfs" useradd -m -G sudo,video,input,audio,dialout,plugdev,netdev -s /bin/bash pi
    fi

    # Set the password unconditionally, whether pi already existed (locked)
    # or was just created above. Written directly into /etc/shadow instead
    # of chpasswd inside the chroot, since that depends on QEMU emulation
    # working correctly and can fail silently.
    echo "  [retropie] Setting pi password..."
    local pw_hash
    pw_hash=$(openssl passwd -6 othermod)
    sed -i "s#^pi:[^:]*:#pi:${pw_hash}:#" "$rootfs/etc/shadow"

    # Disable the first-boot wizard (mask services via symlink, not systemctl,
    # since systemctl in a chroot talks to the host's systemd)
    echo "  [retropie] Disabling first-boot wizard..."
    ln -sf /dev/null "$rootfs/etc/systemd/system/userconfig.service"
    ln -sf /dev/null "$rootfs/etc/systemd/system/piwiz.service"
    rm -f "$rootfs/etc/xdg/autostart/piwiz.desktop"

    # userconfig.service is normally what enables getty@tty1 on first boot.
    # Since we mask it above, enable getty@tty1 directly or the console never
    # gets a login prompt.
    mkdir -p "$rootfs/etc/systemd/system/getty.target.wants"
    ln -sf /lib/systemd/system/getty@.service \
        "$rootfs/etc/systemd/system/getty.target.wants/getty@tty1.service"

    # Set US keyboard layout
    cat > "$rootfs/etc/default/keyboard" <<'KEYBOARD'
XKBMODEL="pc105"
XKBLAYOUT="us"
XKBVARIANT=""
XKBOPTIONS=""
BACKSPACE="guess"
KEYBOARD

    # Install RetroPie-Setup dependencies
    echo "  [retropie] Installing dependencies..."
    chroot "$rootfs" apt-get update -qq
    chroot "$rootfs" apt-get install -y --no-install-recommends \
        git dialog xmlstarlet python3-pyudev lsb-release

    # Clone RetroPie-Setup
    if [[ ! -d "$rootfs/home/pi/RetroPie-Setup" ]]; then
        echo "  [retropie] Cloning RetroPie-Setup..."
        git clone --depth 1 https://github.com/RetroPie/RetroPie-Setup.git \
            "$rootfs/home/pi/RetroPie-Setup"
        chroot "$rootfs" chown -R pi:pi /home/pi/RetroPie-Setup
    fi

    # Run the basic install
    echo "  [retropie] Running basic_install (this will take a long time under QEMU)..."
    chroot "$rootfs" /bin/bash -c \
        "__platform=$rp_platform __user=pi /home/pi/RetroPie-Setup/retropie_packages.sh setup basic_install"

    # Install the USB ROM Service (usbromservice): the stock image's tool for
    # adding ROMs/BIOS by plugging in a USB drive. It's an opt-section module,
    # so basic_install doesn't pull it in either. No args = full depends/build/
    # install/configure cycle (it builds RetroPie's usbmount .deb from source).
    echo "  [retropie] Installing USB ROM Service..."
    chroot "$rootfs" /bin/bash -c \
        "__platform=$rp_platform __user=pi /home/pi/RetroPie-Setup/retropie_packages.sh usbromservice"

    # Install and enable RetroPie's Samba ROM shares. basic_install only covers
    # the core/main section packages, so samba (a config-section module) is not
    # pulled in by it -- but it is part of the stock RetroPie image and lets
    # users drop ROMs/BIOS onto the device over the network out of the box.
    echo "  [retropie] Installing and enabling Samba ROM shares..."
    # Run while still in the chroot so getDepends/aptInstall see /proc and /dev.
    chroot "$rootfs" /bin/bash -c \
        "__platform=$rp_platform __user=pi /home/pi/RetroPie-Setup/retropie_packages.sh samba depends"
    chroot "$rootfs" /bin/bash -c \
        "__platform=$rp_platform __user=pi /home/pi/RetroPie-Setup/retropie_packages.sh samba install_shares"

    # Enable EmulationStation autostart (done manually since raspi-config/systemctl
    # don't work in a chroot)
    echo "  [retropie] Configuring auto-login and EmulationStation autostart..."

    # Auto-login pi on tty1
    mkdir -p "$rootfs/etc/systemd/system/getty@tty1.service.d"
    cat > "$rootfs/etc/systemd/system/getty@tty1.service.d/autologin.conf" <<'AUTOLOGIN'
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin pi --noclear %I $TERM
AUTOLOGIN

    # Profile script that launches autostart.sh on tty1
    cat > "$rootfs/etc/profile.d/10-retropie.sh" <<'PROFILE'
if [ "`tty`" = "/dev/tty1" ] && [ -z "$DISPLAY" ] && [ "$USER" = "pi" ]; then
    bash "/opt/retropie/configs/all/autostart.sh"
fi
PROFILE

    # Autostart script that launches EmulationStation
    mkdir -p "$rootfs/opt/retropie/configs/all"
    cat > "$rootfs/opt/retropie/configs/all/autostart.sh" <<'AUTOSTART'
emulationstation #auto
AUTOSTART

    # Default EmulationStation's audio to the PCM/analog output instead of
    # HDMI. RetroPie's ES sets AudioDevice="HDMI" by default on RPi, which
    # spams the console with HDMI audio errors when no HDMI is attached. PCM
    # routes sound to the PSPi's on-board analog/PCM DAC (the bcm2835 card).
    es_dir="$rootfs/opt/retropie/configs/all/emulationstation"
    mkdir -p "$es_dir"
    if [[ -f "$es_dir/es_settings.cfg" ]]; then
        sed -i 's|<string name="AudioCard" value="[^"]*"|<string name="AudioCard" value="default"|' "$es_dir/es_settings.cfg"
        sed -i 's|<string name="AudioDevice" value="[^"]*"|<string name="AudioDevice" value="PCM"|' "$es_dir/es_settings.cfg"
        grep -q 'name="AudioCard"' "$es_dir/es_settings.cfg" || echo '<string name="AudioCard" value="default" />' >> "$es_dir/es_settings.cfg"
        grep -q 'name="AudioDevice"' "$es_dir/es_settings.cfg" || echo '<string name="AudioDevice" value="PCM" />' >> "$es_dir/es_settings.cfg"
    else
        cat > "$es_dir/es_settings.cfg" <<'ESCFG'
<string name="AudioCard" value="default" />
<string name="AudioDevice" value="PCM" />
ESCFG
    fi
    chroot "$rootfs" chown -R pi:pi /opt/retropie/configs/all/emulationstation
    echo "  [retropie] Set EmulationStation audio to PCM"

    # Clean up apt cache to save space
    chroot "$rootfs" apt-get clean

    _retropie_exit_chroot "$rootfs" "$qemu_bin"

    # RetroArch PSPi tweaks
    local ra_cfg="$rootfs/opt/retropie/configs/all/retroarch.cfg"
    if [[ -f "$ra_cfg" ]]; then
        sed -i 's/^#\?\s*menu_swap_ok_cancel_buttons\s*=.*/menu_swap_ok_cancel_buttons = "true"/' "$ra_cfg"
        sed -i 's/^#\?\s*input_volume_up\s*=.*/input_volume_up = "volumeup"/'     "$ra_cfg"
        sed -i 's/^#\?\s*input_volume_down\s*=.*/input_volume_down = "volumedown"/' "$ra_cfg"
        echo "  [retropie] Updated retroarch.cfg"
    else
        echo "  [retropie] WARNING: retroarch.cfg not found"
    fi
    # Enable RetroPie Setup's "Swap A/B Buttons in ES" (Emulation Station -> Swap A/B).
    # Mirrors exactly what toggling that option to "Swapped" does in RetroPie Setup:
    #   setAutoConf "es_swap_a_b" "1"  (writes es_swap_a_b = "1" to autoconf.cfg)
    # and the corresponding menu_swap_ok_cancel_buttons = "true" change above.
    local ac_cfg="$rootfs/opt/retropie/configs/all/autoconf.cfg"
    if [[ -f "$ac_cfg" ]]; then
        sed -i 's/^#\?\s*es_swap_a_b\s*=.*/es_swap_a_b = "1"/' "$ac_cfg"
        if ! grep -q '^es_swap_a_b' "$ac_cfg"; then
            echo 'es_swap_a_b = "1"' >> "$ac_cfg"
        fi
        chown 1000:1000 "$ac_cfg"
        echo "  [retropie] Swapped A/B buttons in ES (es_swap_a_b=1)"
    else
        echo "  [retropie] WARNING: autoconf.cfg not found"
    fi
}

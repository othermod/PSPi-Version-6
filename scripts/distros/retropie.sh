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

# EmulationStation fork (adds a battery level indicator for handheld use).
# The emulationstation scriptmodule is repointed at this repo before
# basic_install, and ES is rebuilt from source afterward to override any
# prebuilt binary that basic_install installed.
ES_FORK_URL="https://github.com/othermod/EmulationStation.git"
ES_FORK_BRANCH="master"

ALL_TARGETS=(zero1 zero2 cm4 cm5)

declare -A TARGET_URL TARGET_SHA256 TARGET_PSPI_PREFIX TARGET_BIN TARGET_RP_PLATFORM

# zero1 (armv6) uses the 32-bit armhf image; zero2/cm4/cm5 share the 64-bit arm64 image.
TARGET_URL[zero1]="https://downloads.raspberrypi.com/raspios_oldstable_lite_armhf/images/raspios_oldstable_lite_armhf-2026-04-14/2026-04-13-raspios-bookworm-armhf-lite.img.xz"
TARGET_URL[zero2]="https://downloads.raspberrypi.com/raspios_oldstable_lite_arm64/images/raspios_oldstable_lite_arm64-2026-04-14/2026-04-13-raspios-bookworm-arm64-lite.img.xz"
TARGET_URL[cm4]="https://downloads.raspberrypi.com/raspios_oldstable_lite_arm64/images/raspios_oldstable_lite_arm64-2026-04-14/2026-04-13-raspios-bookworm-arm64-lite.img.xz"
TARGET_URL[cm5]="https://downloads.raspberrypi.com/raspios_oldstable_lite_arm64/images/raspios_oldstable_lite_arm64-2026-04-14/2026-04-13-raspios-bookworm-arm64-lite.img.xz"

TARGET_SHA256[zero1]="265dfcd2a032ef01c224e8f9fc03b5fd0e31d3a5038f7e578cc5f01e22bc74a9"
TARGET_SHA256[zero2]="9bba9c625dd4dd4e1b326dd2551e37a2029db9090bf19ea300649b78c054de6f"
TARGET_SHA256[cm4]="9bba9c625dd4dd4e1b326dd2551e37a2029db9090bf19ea300649b78c054de6f"
TARGET_SHA256[cm5]="9bba9c625dd4dd4e1b326dd2551e37a2029db9090bf19ea300649b78c054de6f"

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
        echo "none 0"
        return
    elif [[ "$host_arch" == armv7* && "$arch" == "32" ]]; then
        echo "none 0"
        return
    fi

    command -v "$qemu_bin" >/dev/null 2>&1 \
        || die "$qemu_bin not found. Install qemu-user-static."

    # Mount binfmt_misc if needed (register is a file, not a dir).
    if [[ ! -e /proc/sys/fs/binfmt_misc/register ]]; then
        mount -t binfmt_misc binfmt_misc /proc/sys/fs/binfmt_misc 2>/dev/null || true
    fi

    # Handlers register under the interpreter name (qemu-aarch64), not the
    # binary filename (qemu-aarch64-static).
    local handler
    if [[ "$arch" == "64" ]]; then handler="qemu-aarch64"; else handler="qemu-arm"; fi

    # Register only if missing; record it so _retropie_exit_chroot can remove it.
    if [[ ! -e "/proc/sys/fs/binfmt_misc/$handler" ]]; then
        if [[ "$arch" == "64" ]]; then
            printf '%s' ':qemu-aarch64:M::\x7fELF\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\xb7\x00:\xff\xff\xff\xff\xff\xff\xff\x00\xff\xff\xff\xff\xff\xff\xff\xff\xfe\xff\xff\xff:/usr/bin/qemu-aarch64-static:F' \
                > /proc/sys/fs/binfmt_misc/register \
                || die "Failed to register binfmt handler $handler"
        else
            printf '%s' ':qemu-arm:M::\x7fELF\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x28\x00:\xff\xff\xff\xff\xff\xff\xff\x00\xff\xff\xff\xff\xff\xff\xff\xff\xfe\xff\xff\xff:/usr/bin/qemu-arm-static:F' \
                > /proc/sys/fs/binfmt_misc/register \
                || die "Failed to register binfmt handler $handler"
        fi
        _RETROPIE_DID_REGISTER=1
    fi

    # Called via command substitution, so variables die with the subshell;
    # print both values for the caller to split.
    echo "$qemu_bin ${_RETROPIE_DID_REGISTER:-0}"
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

    # Working DNS without baking the host resolver into the image: bind-mount
    # over the image's resolv.conf (unmounted on exit). If none exists, create
    # an empty file to mount over and track it for removal.
    _RETROPIE_TEMP_RESOLV=""
    if [[ ! -e "$rootfs/etc/resolv.conf" ]]; then
        # A symlink writes through to its target; keep it, don't track it.
        : > "$rootfs/etc/resolv.conf"
        [[ -L "$rootfs/etc/resolv.conf" ]] || _RETROPIE_TEMP_RESOLV="$rootfs/etc/resolv.conf"
    fi
    mount --bind /etc/resolv.conf "$rootfs/etc/resolv.conf" \
        || die "Failed to bind-mount resolv.conf into the chroot"

    export HOME=/root
}

_retropie_exit_chroot() {
    local rootfs="$1" qemu_bin="$2"

    # Detach nested mounts first so the rootfs unmounts cleanly on loop detach.
    umount "$rootfs/etc/resolv.conf" 2>/dev/null \
        || umount -l "$rootfs/etc/resolv.conf" 2>/dev/null || true
    [[ -n "${_RETROPIE_TEMP_RESOLV:-}" ]] && rm -f "$_RETROPIE_TEMP_RESOLV"
    umount -l "$rootfs/dev/pts" 2>/dev/null || true
    umount -l "$rootfs/dev/shm" 2>/dev/null || true
    umount -l "$rootfs/dev" 2>/dev/null || true
    umount -l "$rootfs/sys" 2>/dev/null || true
    umount -l "$rootfs/proc" 2>/dev/null || true
    sync
    [[ -n "$qemu_bin" ]] && rm -f "$rootfs/usr/bin/$qemu_bin"

    # Remove only a handler this build registered.
    if [[ -n "${_RETROPIE_REGISTERED_BINFMT:-}" ]]; then
        echo -1 > "/proc/sys/fs/binfmt_misc/$_RETROPIE_REGISTERED_BINFMT" 2>/dev/null || true
        _RETROPIE_REGISTERED_BINFMT=""
    fi
    return 0
}

# --- Hooks ---

distro_pre_patch() {
    local img_path="$1"

    echo "  [retropie] Expanding image by 4GB for RetroPie install..."
    truncate -s +4G "$img_path"

    # Get rootfs partition start sector
    local root_offset root_size root_start
    read -r root_offset root_size < <(detect_partition "$img_path" 2) \
        || die "[retropie] Failed to read rootfs partition"
    root_start=$(( root_offset / 512 ))

    # Recreate partition 2 to fill available space
    echo -e "d\n2\nn\np\n2\n${root_start}\n\nw" | fdisk "$img_path" >/dev/null \
        || die "[retropie] Failed to recreate the rootfs partition"

    # resize2fs grows to the bounded loop device, not end-of-image.
    local resize_dev
    resize_dev=$(attach_partition "$img_path" 2)

    # e2fsck returns 1 on successful repair; only >= 4 is a real failure.
    e2fsck -fy "$resize_dev" >/dev/null 2>&1 || [[ $? -lt 4 ]] \
        || die "[retropie] e2fsck failed on the rootfs partition"
    resize2fs "$resize_dev" >/dev/null 2>&1 \
        || die "[retropie] resize2fs failed on the rootfs partition"

    # Confirm the filesystem actually grew into the partition.
    local block_size block_count fs_bytes new_size
    read -r new_size < <(detect_partition "$img_path" 2 | cut -d' ' -f2)
    block_size=$(dumpe2fs -h "$resize_dev" 2>/dev/null | awk -F': *' '/^Block size/{print $2}')
    block_count=$(dumpe2fs -h "$resize_dev" 2>/dev/null | awk -F': *' '/^Block count/{print $2}')
    losetup -d "$resize_dev"

    fs_bytes=$(( block_size * block_count ))
    (( fs_bytes > new_size - 16 * 1024 * 1024 )) \
        || die "[retropie] Resize did not fill the partition ($fs_bytes of $new_size bytes)"

    echo "  [retropie] Image expanded ($(( fs_bytes / 1024 / 1024 )) MiB rootfs)"
}

distro_post_patch() {
    local rootfs="$1"
    local mnt_boot="$2"
    local work_dir="$3"
    local BIN="$4"
    local LABEL="$5"

    # Purge any rfkill state baked into the base image. systemd-rfkill
    # restores these files verbatim at every boot, so a stale "blocked" entry
    # for the board's Bluetooth UART leaves hci0 soft-blocked and powered off
    # -- bluetoothctl scans then report "No devices were found".
    echo "  [retropie] Clearing stale rfkill state..."
    rm -rf "$rootfs/var/lib/systemd/rfkill"

    # raspberrypi-sys-mods ships /etc/modprobe.d/rfkill_default.conf with
    # "options rfkill default_state=0", registering every radio soft-blocked
    # at creation. Upstream assumes the first-boot wizard unblocks radios once
    # the user picks a wireless country; piwiz is masked here, so nothing ever
    # does and hci0 stays blocked. Re-enable the kernel default (radios come
    # up unblocked); the filename must sort after rfkill_default.conf since
    # the last matching modprobe.d entry wins. A user can still disable a
    # radio with rfkill block -- that choice persists via systemd-rfkill.
    cat > "$rootfs/etc/modprobe.d/zz-pspi-rfkill.conf" <<'MODPROBE'
options rfkill default_state=1
MODPROBE

    local qemu_bin registered
    # "none" means the host runs this arch natively and no emulation is needed.
    read -r qemu_bin registered < <(_retropie_setup_binfmt "$BIN")
    [[ "$qemu_bin" == "none" ]] && qemu_bin=""
    _RETROPIE_REGISTERED_BINFMT=""
    if [[ "$registered" == "1" ]]; then
        _RETROPIE_REGISTERED_BINFMT=$([[ "$BIN" == "64" ]] && echo qemu-aarch64 || echo qemu-arm)
    fi

    # RetroPie platform mapping (per-board: controls which prebuilt cores get installed)
    local rp_platform="${TARGET_RP_PLATFORM[$LABEL]:-rpi4}"

    _retropie_enter_chroot "$rootfs" "$qemu_bin"

    # If die() fires inside the chroot, _retropie_exit_chroot would never run
    # (die exits), leaking the chroot mounts, resolv.conf bind, and binfmt
    # handler. Chain it onto EXIT with values baked in; restore the patcher's
    # trap on the success path below. Idempotent, so double-call is harmless.
    trap "_retropie_exit_chroot '$rootfs' '$qemu_bin' 2>/dev/null; cleanup" EXIT

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

    # Quiet console boot: append `quiet` to kernel cmdline.txt (append-only,
    # never reorder or remove existing kernel args).
    echo "  [retropie] Appending quiet to cmdline.txt..."
    grep -q ' quiet' "$mnt_boot/cmdline.txt" \
        || sed -i 's/$/ quiet/' "$mnt_boot/cmdline.txt"

    # Disable RetroPie's splash screen. It plays the boot logo via vlc, which
    # needs X11/HDMI output: run as User=pi in a system service it dies with
    # "XDG_RUNTIME_DIR is invalid or not set", and run as root it refuses
    # ("VLC is not supposed to be run as root"). A PSPi has a DPI LCD, no
    # HDMI and no display server, so it can never show anything -- mask the
    # unit (systemctl is unusable in a chroot; a /dev/null symlink is the
    # standard mask).
    echo "  [retropie] Disabling splash screen..."
    ln -sf /dev/null "$rootfs/etc/systemd/system/asplashscreen.service"

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

    # Make RetroPie's downloads resilient to transient CDN timeouts.
    # download() in helpers.sh hardcodes "--connect-timeout 10" with no --retry,
    # so a single SSL/connection timeout to files.retropie.org.uk aborts the
    # whole build. Add retries and a longer connect timeout so transient
    # failures are retried instead of failing the build.
    local helpers="$rootfs/home/pi/RetroPie-Setup/scriptmodules/helpers.sh"
    if [[ -f "$helpers" ]] && ! grep -q 'RP_RETRY_DOWNLOADS' "$helpers"; then
        sed -i 's/--connect-timeout 10 --speed-limit 1 --speed-time 60 --fail/--connect-timeout 30 --retry 5 --retry-delay 2 --speed-limit 1 --speed-time 60 --fail/' "$helpers"
        echo "  [retropie] Patched RetroPie download() with --retry 5 (resilient CDN downloads)"
    fi

    # Point the emulationstation scriptmodule at the PSPi6 fork. Done after
    # cloning RetroPie-Setup and before basic_install. Hardcoding the branch
    # (instead of the module's _get_branch function) keeps every target on the
    # same tested code regardless of OS version.
    local es_module="$rootfs/home/pi/RetroPie-Setup/scriptmodules/supplementary/emulationstation.sh"
    if [[ -f "$es_module" ]]; then
        sed -i "s|^rp_module_repo=.*|rp_module_repo=\"git ${ES_FORK_URL} ${ES_FORK_BRANCH}\"|" "$es_module"
        echo "  [retropie] Repointed emulationstation module at othermod/EmulationStation (${ES_FORK_BRANCH})"
    else
        echo "  [retropie] WARNING: emulationstation.sh module not found - using stock ES"
    fi

    # Run the basic install
    echo "  [retropie] Running basic_install (this will take a long time under QEMU)..."
    chroot "$rootfs" /bin/bash -c \
        "__platform=$rp_platform __user=pi /home/pi/RetroPie-Setup/retropie_packages.sh setup basic_install"

    # Rebuild EmulationStation from the fork. basic_install installs prebuilt
    # binaries for rpi3/rpi4/rpi5 (and builds from source for rpi1), so this
    # explicit source build guarantees the fork's code (battery indicator)
    # ends up in the image on every target. _source_ runs the full chain:
    # depends sources build install configure.
    echo "  [retropie] Rebuilding EmulationStation from the PSPi6 fork (slow, especially under QEMU)..."
    chroot "$rootfs" /bin/bash -c \
        "__platform=$rp_platform __user=pi /home/pi/RetroPie-Setup/retropie_packages.sh emulationstation _source_"

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

    # Install the experimental Steam Link port (streams games from a networked PC)
    # and apply the first-launch black-screen fix.
    # The scriptmodule is a bin module (depends -> aptInstall the Valve "steamlink"
    # deb -> configure creates ~/.local/share/SteamLink and the "Steam Link" port).
    # It is flagged "!all rpi3 rpi4 rpi5", so it only applies to zero2 (rpi3) /
    # cm4 (rpi4) / cm5 (rpi5). On zero1 (rpi1) rp_callModule prints "not available
    # for your system" and returns 3 (graceful skip, not a hard failure), but we
    # gate it explicitly so zero1 doesn't run the udev pre-seed either.
    # retropie_packages.sh with no mode arg runs the full install cycle
    # (depends + install_bin + configure).
    case "$rp_platform" in
        rpi3|rpi4|rpi5)
            # Workaround: the chroot has MODULES=dep in initramfs.conf, so
            # mkinitramfs tries to autodetect the root block device, which fails
            # inside the chroot ("failed to determine device for /"). Any apt
            # transaction that triggers the initramfs-tools postinst then returns
            # non-zero, and RetroPie's aptInstall treats that as fatal -> the
            # Steam Link install aborts the whole build even though the deb
            # itself installed. Temporarily switch to MODULES=most (the
            # documented workaround, skips root-device probing) for the
            # duration of the Steam Link install, clear any half-installed
            # initramfs-tools state left by earlier failed triggers, then
            # restore MODULES=dep afterward to keep the stock image behavior.
            local irconf="$rootfs/etc/initramfs-tools/initramfs.conf"
            if [[ -f "$irconf" ]]; then
                sed -i 's/^MODULES=dep$/MODULES=most/' "$irconf"
                echo "  [retropie] Temporarily set initramfs MODULES=most for the Steam Link install"
            fi
            chroot "$rootfs" /usr/bin/dpkg --configure -a || true

            echo "  [retropie] Installing Steam Link port..."
            chroot "$rootfs" /bin/bash -c \
                "__platform=$rp_platform __user=pi /home/pi/RetroPie-Setup/retropie_packages.sh steamlink"

            # Restore the stock MODULES=dep so the final image regenerates the
            # initrd the same way Raspberry Pi OS does (dep works on the real
            # device where / is a real block device).
            if [[ -f "$irconf" ]] && grep -q '^MODULES=most$' "$irconf"; then
                sed -i 's/^MODULES=most$/MODULES=dep/' "$irconf"
                echo "  [retropie] Restored initramfs MODULES=dep"
            fi

            # Fix: Steam Link's first-launch setup (steamlink.sh) runs a one-time
            # udev block that ends in an interactive "Press return to continue:
            # read". Under RetroPie runcommand there is no tty input, so that read
            # blocks forever and the app never starts -> permanent black screen.
            # The whole block is guarded by "if [ ! -f /lib/udev/rules.d/56-steamlink.rules ]",
            # so pre-creating that rule file (and the uinput module-load entry) in
            # the image makes first launch skip the blocker and reach the app GUI.
            echo "  [retropie] Pre-seeding Steam Link udev rules (skip first-run black screen)..."
            mkdir -p "$rootfs/lib/udev/rules.d" "$rootfs/etc/modules-load.d"
            cat > "$rootfs/lib/udev/rules.d/56-steamlink.rules" <<'STEAMLINKRULES'
# USB devices
SUBSYSTEM=="usb", GROUP="plugdev"

# HID devices
KERNEL=="hidraw*", GROUP="input", MODE:="0660"

# Creating virtual devices
KERNEL=="uinput", GROUP="input", MODE:="0660"
STEAMLINKRULES
            echo 'uinput' > "$rootfs/etc/modules-load.d/uinput.conf"
            ;;
        *)
            echo "  [retropie] Skipping Steam Link (not supported on $rp_platform)"
            ;;
    esac

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
    local es_dir="$rootfs/opt/retropie/configs/all/emulationstation"
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

    # Replay EmulationStation's first-boot controller wizard for the PSPi pad.
    # On a stock image the wizard's onfinish action (inputconfiguration.sh)
    # converts the newly-configured pad into per-app inputs: the retroarch
    # joypad autoconfig (which joy2key reads to navigate RetroPie-Setup,
    # raspi-config and runcommand dialogs), the SDL mapper and the per-emulator
    # keymaps (mupen64plus, flycast/reicast). We preinstall es_input.cfg so the
    # wizard never runs on the device, so replay it here from the temp config
    # ES would have written for that session. The layout mirrors
    # scripts/config/es_input.cfg; leftshoulder/rightshoulder are the L1/R1
    # buttons (also pageup/pagedown in ES), and no hotkeyenable is assigned so
    # the wizard's onend rule makes select the retroarch hotkey.
    local tmp_cfg="/opt/retropie/configs/all/emulationstation/es_temporaryinput.cfg"
    cat > "$rootfs$tmp_cfg" <<'ESCFG'
<?xml version="1.0"?>
<inputList>
  <inputConfig type="joystick" deviceName="PS3 Controller" vendorId="1356" productId="616" deviceGUID="03007a2e4c0500006802000011810000">
    <input name="a" type="button" id="0" value="1"/>
    <input name="b" type="button" id="1" value="1"/>
    <input name="x" type="button" id="2" value="1"/>
    <input name="y" type="button" id="3" value="1"/>
    <input name="leftshoulder" type="button" id="4" value="1"/>
    <input name="rightshoulder" type="button" id="5" value="1"/>
    <input name="select" type="button" id="8" value="1"/>
    <input name="start" type="button" id="9" value="1"/>
    <input name="up" type="button" id="13" value="1"/>
    <input name="down" type="button" id="14" value="1"/>
    <input name="left" type="button" id="15" value="1"/>
    <input name="right" type="button" id="16" value="1"/>
    <input name="leftanalogup" type="axis" id="1" value="-1"/>
    <input name="leftanalogdown" type="axis" id="1" value="1"/>
    <input name="leftanalogleft" type="axis" id="0" value="-1"/>
    <input name="leftanalogright" type="axis" id="0" value="1"/>
  </inputConfig>
</inputList>
ESCFG
    chroot "$rootfs" chown pi:pi "$tmp_cfg"
    local ic_script="/opt/retropie/supplementary/emulationstation/scripts/inputconfiguration.sh"
    [[ -f "$rootfs$ic_script" ]] \
        || die "[retropie] $ic_script missing (emulationstation install incomplete)"
    chroot "$rootfs" /bin/su -s /bin/bash pi -c "$ic_script" \
        || die "[retropie] inputconfiguration.sh failed"
    # Clear the wizard's scratch files (it also rewrites es_input.cfg from the
    # temp config; the curated copy below restores the tested layout instead).
    rm -f "$rootfs/tmp/sdl2temp.txt" "$rootfs/tmp/guid_check.py" \
          "$rootfs/tmp/openMSXtemp.cfg" "$rootfs/tmp/mp64tempconfig.cfg" \
          "$rootfs/tmp/flycast-input-"*.ini "$rootfs$tmp_cfg"

    # Skip the ES input wizard on first boot.
    rm -f "$es_dir/es_input.cfg.bak"
    cp "$CONFIG_DIR/es_input.cfg" "$es_dir/es_input.cfg" \
        || die "[retropie] Failed to install es_input.cfg"

    chroot "$rootfs" chown -R pi:pi /opt/retropie/configs/all/emulationstation
    echo "  [retropie] Set EmulationStation audio to PCM, installed es_input.cfg"

    # Clean up apt cache to save space
    chroot "$rootfs" apt-get clean

    _retropie_exit_chroot "$rootfs" "$qemu_bin"
    # Restore the patcher's own EXIT trap.
    trap cleanup EXIT

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
    # Mirrors RetroPie Setup's "Swap A/B Buttons in ES" toggle
    # (setAutoConf es_swap_a_b 1) + the retroarch.cfg change above.
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

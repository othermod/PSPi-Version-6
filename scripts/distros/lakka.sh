PATCH_METHOD="squashfs"
SQUASHFS_PATH="SYSTEM"
DRIVERS_BASE="/flash"
INIT_SYSTEM=systemd
SQUASHFS_COMP_ARGS=""

# --- Targets ---

ALL_TARGETS=(cm4 cm5 zero2 zero1)

declare -A TARGET_URL TARGET_SHA256 TARGET_PSPI_PREFIX TARGET_BIN

TARGET_URL[cm4]="https://github.com/libretro/Lakka-LibreELEC/releases/download/v6.1/Lakka-RPi4.aarch64-6.1.img.gz"
TARGET_URL[cm5]="https://github.com/libretro/Lakka-LibreELEC/releases/download/v6.1/Lakka-RPi5.aarch64-6.1.img.gz"
TARGET_URL[zero2]="https://github.com/libretro/Lakka-LibreELEC/releases/download/v6.1/Lakka-RPi3.aarch64-6.1.img.gz"
TARGET_URL[zero1]="https://github.com/libretro/Lakka-LibreELEC/releases/download/v6.1/Lakka-RPi.arm-6.1.img.gz"

TARGET_SHA256[cm4]="9e541bd8d092c63a65c5b7c66295ff9d3c3fc073d6bb6229560526c1c505ca11"
TARGET_SHA256[cm5]="b2fd310742c612b6f7f221540518f03845a75f8e5d0b55c0c2abeb81da8c5bb3"
TARGET_SHA256[zero2]="e72cf352cbaaf0366fc7f46650b0e5335786b6119cdcaf086a0ecee2355ac742"
TARGET_SHA256[zero1]="c331c30d4dc52fbae168d16b844c18833a1e7e790039ceb5f2d2acc6c9b09414"

TARGET_PSPI_PREFIX[cm4]="Lakka6.1-CM4-PSPi6"
TARGET_PSPI_PREFIX[cm5]="Lakka6.1-CM5-PSPi6"
TARGET_PSPI_PREFIX[zero2]="Lakka6.1-Zero2-PSPi6"
TARGET_PSPI_PREFIX[zero1]="Lakka6.1-Zero1-PSPi6"

TARGET_BIN[cm4]=64
TARGET_BIN[cm5]=64
TARGET_BIN[zero2]=64
TARGET_BIN[zero1]=32

# --- Mono downmix audio module (prebuilt, PSPi-6-Audio-Modules releases) ---
# The PSPi amp is wired to one audio pin per board, so stereo content needs
# the patched snd-bcm2835 (cm4/zero2/zero1) or rp1_aout (cm5) driver, built
# by the PSPi-6-Audio-Modules repo against each image's exact kernel. The
# asset is fetched and verified by fetch_audio_module (patcher.sh) and
# replaces the stock module in place inside the SYSTEM squashfs: same module
# name and dependencies, so the shipped modules.dep/modules.alias stay valid
# and no depmod is needed.
#
# One artifact per target -- the RPi3 kernel (zero2) is a different build
# (preempt, modversions) and zero1 is ARMv6, so none are interchangeable.
# Vermagic is the only ABI gate here (no modversions, no signing), so a
# wrong-artifact download must fail the build, not boot.
declare -A MODULE_ASSET MODULE_VERMAGIC

MODULE_ASSET[cm4]="Lakka-RPi4.aarch64-6.1-snd-bcm2835-mono.ko"
MODULE_ASSET[cm5]="Lakka-RPi5.aarch64-6.1-rp1-aout-mono.ko"
MODULE_ASSET[zero2]="Lakka-RPi3.aarch64-6.1-snd-bcm2835-mono.ko"
MODULE_ASSET[zero1]="Lakka-RPi.arm-6.1-snd-bcm2835-mono.ko"

MODULE_VERMAGIC[cm4]="6.12.66 SMP mod_unload aarch64"
MODULE_VERMAGIC[cm5]="6.12.66 SMP mod_unload aarch64"
MODULE_VERMAGIC[zero2]="6.12.66 SMP preempt mod_unload modversions aarch64"
MODULE_VERMAGIC[zero1]="6.12.66 mod_unload ARMv6 p2v8"

install_audio_module() {
    local rootfs="$1" mnt_boot="$2" label="$3"
    local ko
    ko="$(fetch_audio_module "$label")"

    # Locate the stock module; its parent tree fixes the kernel version.
    local modbase="$rootfs/usr/lib/kernel-overlays/base/lib/modules"
    local -a kvers=()
    local kd
    for kd in "$modbase"/*/; do
        [[ -d "$kd" ]] && kvers+=("$(basename "$kd")")
    done
    [[ ${#kvers[@]} -eq 1 ]] \
        || die "[lakka] expected exactly one kernel in $modbase, found: ${kvers[*]:-none}"
    local kver="${kvers[0]}"

    local dest_rel
    case "$label" in
        cm5) dest_rel="kernel/sound/soc/raspberrypi/rp1_aout.ko" ;;
        *)   dest_rel="kernel/drivers/staging/vc04_services/bcm2835-audio/snd-bcm2835.ko" ;;
    esac
    local stock="$modbase/$kver/$dest_rel"
    [[ -f "$stock" ]] \
        || die "[lakka] stock module missing at $stock (kernel or overlay layout drift)"
    cp "$ko" "$stock" \
        || die "[lakka] failed to install $(basename "$ko") over $stock"

    if [[ "$label" == "cm5" ]]; then
        # rp1_aout has no module parameters: the downmix is gated by the DT
        # property the cm5 overlay sets via this config.txt override, read
        # once at probe. The stock module ignores the unread property, so
        # the line stays valid either way.
        sed -i 's|^dtoverlay=pspi-audio-cm5-kernel6+$|dtoverlay=pspi-audio-cm5-kernel6+,mono_mix|' \
            "$mnt_boot/config.txt"
        grep -q '^dtoverlay=pspi-audio-cm5-kernel6+,mono_mix$' "$mnt_boot/config.txt" \
            || die "[lakka] failed to enable mono_mix on the cm5 audio overlay line"
        echo "  [lakka] Installed rp1-aout-mono for $kver; mono_mix enabled in config.txt"
    else
        # snd_bcm2835 auto-loads via udev (vchiq alias), so a modprobe.d
        # option applies wherever the module loads from. The overlay's
        # chosen/bootargs is NOT a reliable channel on Lakka (the firmware's
        # cmdline.txt clobbers it). Note /etc/modprobe.d in Lakka is a
        # symlink into the writable /storage partition -- unusable at build
        # time -- so the option goes to /usr/lib/modprobe.d, which kmod reads
        # directly on every load.
        [[ -d "$rootfs/usr/lib/modprobe.d" ]] \
            || die "[lakka] $rootfs/usr/lib/modprobe.d missing"
        cat > "$rootfs/usr/lib/modprobe.d/pspi-audio.conf" <<'CONF'
# PSPi 6: one PWM pin feeds the speaker; patched snd-bcm2835 (from
# PSPi-6-Audio-Modules) downmixes (L+R)/2 so that pin carries the full
# stereo image.
options snd_bcm2835 enable_headphones=Y mono_mix=Y
CONF
        echo "  [lakka] Installed snd-bcm2835-mono for $kver; mono_mix set via modprobe.d"
    fi
}

distro_post_patch() {
    local overlay_target="$1"
    local mnt_boot="$2"

    # Append vc4-kms-v3d with noaudio -- required for Lakka's display pipeline
    local vc4_line
    vc4_line=$(grep "dtoverlay=vc4-kms-v3d" "$mnt_boot/distroconfig.txt" | head -1)
    [[ -z "$vc4_line" ]] && die "vc4-kms-v3d line not found in distroconfig.txt"
    echo "$vc4_line,noaudio" >> "$mnt_boot/config.txt"

    local cfg="$overlay_target/etc/retroarch.cfg"
    sed -i 's/menu_swap_ok_cancel_buttons = "false"/menu_swap_ok_cancel_buttons = "true"/'  "$cfg"
    sed -i 's/xmb_layout = "0"/xmb_layout = "2"/'                                          "$cfg"
    sed -i 's/xmb_menu_color_theme = .*/xmb_menu_color_theme = "7"/'                       "$cfg"
    sed -i 's/menu_shader_pipeline = .*/menu_shader_pipeline = "1"/'                        "$cfg"
    sed -i 's/input_volume_up = "add"/input_volume_up = "volumeup"/'                        "$cfg"
    sed -i 's/input_volume_down = "subtract"/input_volume_down = "volumedown"/'             "$cfg"
    sed -i 's/input_audio_mute = "f9"/input_audio_mute = "mute"/'                           "$cfg"
    sed -i 's/input_player1_analog_dpad_mode = "0"/input_player1_analog_dpad_mode = "1"/'   "$cfg"

    # Patched mono-downmix audio module, fetched from PSPi-6-Audio-Modules
    # and installed over the stock driver inside the squashfs.
    install_audio_module "$overlay_target" "$mnt_boot" "$5"
}

distro_post_write() {
    local mnt_boot="$1"
    # BIN="$2" -- not needed here

    md5sum "$mnt_boot/SYSTEM" > "$mnt_boot/SYSTEM.md5"
}

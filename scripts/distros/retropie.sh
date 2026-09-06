# RetroPie (prebuilt base image from RetroPie-Image-Builder)
#
# The RetroPie-Image-Builder repo (github.com/othermod/RetroPie-Image-Builder)
# downloads stock Pi OS Lite, installs RetroPie inside a QEMU/native chroot,
# and publishes ready-to-patch images as release assets. That includes the
# RetroPie basic_install, the EmulationStation fork (battery indicator),
# Steam Link, Samba shares, USB ROM Service, the pi user, autologin, and the
# ES autostart setup.
#
# This config consumes those images and applies only PSPi-specific file
# edits: rfkill state, controller layout, input autoconfig/keymaps (joy2key,
# RetroArch, flycast, mupen64plus), and analog audio routing. No QEMU,
# no chroot, no package installation.
#
# Target mapping (board -> builder image):
#   zero1 -> rpi1 image (32-bit)      zero2 -> rpi3 image (64-bit)
#   cm4   -> rpi4 image (64-bit)      cm5   -> rpi5 image (64-bit)
#
# The released images are pre-expanded (+4GB), so no distro_pre_patch.

PATCH_METHOD="copy"
DRIVERS_BASE="/boot/firmware"
INIT_SYSTEM="systemd"

ALL_TARGETS=(zero1 zero2 cm4 cm5)

declare -A TARGET_URL TARGET_SHA256 TARGET_PSPI_PREFIX TARGET_BIN

# Latest published release of the builder repo. Its CI uploads an unversioned
# alias asset per target alongside the date-versioned ones, so "latest" always
# resolves to the newest published release regardless of date.
#
# TARGET_SHA256 is left empty: the patcher then trusts the cached download
# (see download_image in patcher.sh). For reproducible release builds, pin
# each URL to a date-versioned asset and set its checksum from the
# release's SHA256SUMS file.
RP_RELEASE="https://github.com/othermod/RetroPie-Image-Builder/releases/latest/download"

TARGET_URL[zero1]="$RP_RELEASE/RetroPie-Bookworm-32bit-rpi1.img.xz"
TARGET_URL[zero2]="$RP_RELEASE/RetroPie-Bookworm-64bit-rpi3.img.xz"
TARGET_URL[cm4]="$RP_RELEASE/RetroPie-Bookworm-64bit-rpi4.img.xz"
TARGET_URL[cm5]="$RP_RELEASE/RetroPie-Bookworm-64bit-rpi5.img.xz"

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

# --- Mono downmix audio module (prebuilt, PSPi-6-Audio-Modules releases) ---
# The base image is Raspberry Pi OS Bookworm Lite 2026-04-13, which carries
# MULTIPLE kernel trees; only one boots per board (zero1 -> v6, zero2/cm4 ->
# v8, cm5 -> 2712), so the module is installed into just that tree. Stock
# modules are XZ-COMPRESSED (.ko.xz): the fetched .ko is recompressed to
# replace the stock file in place -- same module name and dependencies, so
# the shipped modules.dep/modules.alias stay valid and no depmod is needed.
# All these kernels have CONFIG_MODVERSIONS on; the release builds carry
# CRCs harvested from the image's own Module.symvers.
#
# Activation: the pspi-audio overlay's bootargs (snd_bcm2835.mono_mix=1)
# land on the kernel command line, and an /etc/modprobe.d option (a real
# directory on Pi OS) is the deterministic second channel. cm5 uses the
# overlay's mono_mix DT property instead -- rp1_aout has no parameters.
declare -A MODULE_ASSET MODULE_VERMAGIC

MODULE_ASSET[zero1]="2026-04-13-raspios-bookworm-armhf-lite-v6-snd-bcm2835-mono.ko"
MODULE_ASSET[zero2]="2026-04-13-raspios-bookworm-arm64-lite-snd-bcm2835-mono.ko"
MODULE_ASSET[cm4]="2026-04-13-raspios-bookworm-arm64-lite-snd-bcm2835-mono.ko"
MODULE_ASSET[cm5]="2026-04-13-raspios-bookworm-arm64-lite-2712-rp1-aout-mono.ko"

MODULE_VERMAGIC[zero1]="6.12.75+rpt-rpi-v6 mod_unload modversions ARMv6 p2v8"
MODULE_VERMAGIC[zero2]="6.12.75+rpt-rpi-v8 SMP preempt mod_unload modversions aarch64"
MODULE_VERMAGIC[cm4]="6.12.75+rpt-rpi-v8 SMP preempt mod_unload modversions aarch64"
MODULE_VERMAGIC[cm5]="6.12.75+rpt-rpi-2712 SMP preempt mod_unload modversions aarch64"

# The kernel tree each target's board actually boots.
boot_kver_glob() {
    case "$1" in
        zero1)          echo '*-rpi-v6' ;;
        zero2|cm4)      echo '*-rpi-v8' ;;
        cm5)            echo '*-rpi-2712' ;;
        *)              die "[retropie] no kernel tree mapping for target: $1" ;;
    esac
}

install_audio_module() {
    local rootfs="$1" mnt_boot="$2" label="$3"
    local ko
    ko="$(fetch_audio_module "$label")"

    local modbase="$rootfs/lib/modules"
    local kvers=()
    readarray -t kvers < <(find "$modbase" -maxdepth 1 -type d \
        -name "$(boot_kver_glob "$label")" -printf '%f\n' | sort)
    [[ ${#kvers[@]} -eq 1 ]] \
        || die "[retropie] expected exactly one booting kernel tree matching" \
               " '$(boot_kver_glob "$label")' in $modbase, found: ${kvers[*]:-none}"
    local kver="${kvers[0]}"

    local dest_rel
    case "$label" in
        cm5) dest_rel="kernel/sound/soc/raspberrypi/rp1_aout.ko" ;;
        *)   dest_rel="kernel/drivers/staging/vc04_services/bcm2835-audio/snd-bcm2835.ko" ;;
    esac
    # Pi OS trees store modules compressed (snd-bcm2835.ko.xz); locate the
    # stock file by prefix so the format switch below drives off its real
    # extension.
    local stock_dir="$modbase/$kver/$(dirname "$dest_rel")"
    local base_name
    base_name="$(basename "$dest_rel")"
    local -a stocks=()
    readarray -t stocks < <(find "$stock_dir" -maxdepth 1 -type f -name "${base_name}*" | sort)
    [[ ${#stocks[@]} -eq 1 ]] \
        || die "[retropie] expected exactly one stock module '${base_name}*' in" \
               " $stock_dir, found: ${stocks[*]:-none}"
    local stock="${stocks[0]}"

    # Recompress the verified module to the tree's on-disk format and swap it
    # in place (write to a temp name first: a failed xz must not truncate the
    # stock file).
    case "$stock" in
        *.ko.xz)
            command -v xz >/dev/null 2>&1 || die "[retropie] xz not found; needed to match the tree's compressed module format"
            xz -T0 -c "$ko" > "$stock.tmp" || die "[retropie] failed to compress $(basename "$ko")"
            mv "$stock.tmp" "$stock"
            ;;
        *.ko)
            cp "$ko" "$stock" || die "[retropie] failed to install $(basename "$ko")"
            ;;
        *)
            die "[retropie] unsupported stock module format: $stock"
            ;;
    esac

    if [[ "$label" == "cm5" ]]; then
        # rp1_aout has no module parameters: the downmix is gated by the DT
        # property the cm5 overlay sets via this config.txt override, read
        # once at probe. The stock module ignores the unread property, so
        # the line stays valid either way.
        sed -i 's|^dtoverlay=pspi-audio-cm5-kernel6+$|dtoverlay=pspi-audio-cm5-kernel6+,mono_mix|' \
            "$mnt_boot/config.txt"
        grep -q '^dtoverlay=pspi-audio-cm5-kernel6+,mono_mix$' "$mnt_boot/config.txt" \
            || die "[retropie] failed to enable mono_mix on the cm5 audio overlay line"
        echo "  [retropie] Installed rp1-aout-mono into $kver; mono_mix enabled in config.txt"
    else
        # snd_bcm2835 auto-loads via udev (vchiq alias), so a modprobe.d
        # option applies wherever the module loads from. /etc/modprobe.d is a
        # real directory on Pi OS (unlike Lakka's /storage symlink).
        [[ -d "$rootfs/etc/modprobe.d" ]] \
            || die "[retropie] $rootfs/etc/modprobe.d missing"
        cat > "$rootfs/etc/modprobe.d/pspi-audio.conf" <<'CONF'
# PSPi 6: one PWM pin feeds the speaker; patched snd-bcm2835 (from
# PSPi-6-Audio-Modules) downmixes (L+R)/2 so that pin carries the full
# stereo image.
options snd_bcm2835 enable_headphones=Y mono_mix=Y
CONF
        echo "  [retropie] Installed snd-bcm2835-mono into $kver; mono_mix set via modprobe.d"
    fi
}

distro_post_patch() {
    local rootfs="$1"
    local mnt_boot="$2"

    # Purge any rfkill state baked into the base image. systemd-rfkill
    # restores these files verbatim at every boot, so a stale "blocked" entry
    # for the board's Bluetooth UART leaves hci0 soft-blocked and powered off
    # -- bluetoothctl scans then report "No devices were found".
    echo "  [retropie] Clearing stale rfkill state..."
    rm -rf "$rootfs/var/lib/systemd/rfkill"

    # raspberrypi-sys-mods ships /etc/modprobe.d/rfkill_default.conf with
    # "options rfkill default_state=0", registering every radio soft-blocked
    # at creation. Upstream assumes the first-boot wizard unblocks radios once
    # the user picks a wireless country; the builder image masks the wizard,
    # so nothing ever does and hci0 stays blocked. Re-enable the kernel
    # default (radios come up unblocked); the filename must sort after
    # rfkill_default.conf since the last matching modprobe.d entry wins. A
    # user can still disable a radio with rfkill block -- that choice
    # persists via systemd-rfkill.
    cat > "$rootfs/etc/modprobe.d/zz-pspi-rfkill.conf" <<'MODPROBE'
options rfkill default_state=1
MODPROBE

    # PSPi controller layout (validated on-device with both the PSPi pad and a
    # real DualSense). The pad is captured Nintendo-style - east pressed for
    # "A" - so RetroPie's own swap mechanisms align every consumer:
    #   es_swap_a_b=1                -> ES config module writes es_input.cfg
    #                                   inverted, giving X(enter)/O(back) in ES
    #   menu_swap_ok_cancel_buttons  -> joy2key swaps Enter/Space in console
    #                                   dialogs so Enter lands on south/X
    #                                   (inert upstream until a comparison bug
    #                                   in joy2key_sdl.py is fixed; harmless)
    # RetroArch games read the autoconfig directly: A=east, B=south, and
    # Start+Home exits a game (hotkey = Home/PS button).
    local ra_cfg="$rootfs/opt/retropie/configs/all/retroarch.cfg"
    if [[ -f "$ra_cfg" ]]; then
        sed -i 's/^#\?\s*menu_swap_ok_cancel_buttons\s*=.*/menu_swap_ok_cancel_buttons = "true"/' "$ra_cfg"
        sed -i 's/^#\?\s*input_volume_up\s*=.*/input_volume_up = "volumeup"/'     "$ra_cfg"
        sed -i 's/^#\?\s*input_volume_down\s*=.*/input_volume_down = "volumedown"/' "$ra_cfg"
        echo "  [retropie] Updated retroarch.cfg"
    else
        echo "  [retropie] WARNING: retroarch.cfg not found"
    fi
    local ac_cfg="$rootfs/opt/retropie/configs/all/autoconf.cfg"
    if [[ -f "$ac_cfg" ]]; then
        sed -i 's/^#\?\s*es_swap_a_b\s*=.*/es_swap_a_b = "1"/' "$ac_cfg"
        if ! grep -q '^es_swap_a_b' "$ac_cfg"; then
            echo 'es_swap_a_b = "1"' >> "$ac_cfg"
        fi
        chown 1000:1000 "$ac_cfg"
        echo "  [retropie] Set es_swap_a_b=1"
    else
        echo "  [retropie] WARNING: autoconf.cfg not found"
    fi

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

    # Skip the ES input wizard on first boot by installing the curated
    # es_input.cfg (a = button 0/X/south = enter, b = button 1/O/east = back;
    # hotkey on Home/PS). It matches what a swap-enabled wizard re-run
    # produces, keeping the first-boot layout deterministic.
    rm -f "$es_dir/es_input.cfg.bak"
    cp "$CONFIG_DIR/es_input.cfg" "$es_dir/es_input.cfg" \
        || die "[retropie] Failed to install es_input.cfg"
    # uid/gid of the pi user in Raspberry Pi OS (numeric: the host may have
    # no pi user to resolve the name against).
    chown -R 1000:1000 "$es_dir"
    echo "  [retropie] Set ES audio to PCM, installed es_input.cfg"

    # Seed the input autoconfig/keymaps that the ES controller wizard's
    # onfinish hook (inputconfiguration.sh) generates from es_temporaryinput.cfg.
    # A fresh builder image ships with an EMPTY retroarch-joypads/, so
    # joy2key_sdl.py falls back to its built-in generic mapping (4 buttons +
    # hat D-pad) and the PSPi pad's button D-pad / shoulder buttons / analog
    # sticks do nothing in RetroPie-Setup and runcommand dialogs. These files
    # are the exact outputs captured from a device after running the ES
    # controller config with the PSPi pad (reports as "PS3 Controller",
    # vendor 1356, product 616, GUID 03007a2e...11810000).
    local joy2k_dir="$rootfs/opt/retropie/configs/all/retroarch-joypads"
    local ra_auto_dir="$rootfs/opt/retropie/configs/all/retroarch/autoconfig"
    # retroarch-joypads may be a symlink to retroarch/autoconfig (the stock
    # RetroPie layout in the base image); an absolute symlink target does not
    # resolve on the build host, so mkdir -p on it errors. Write through the
    # real target dir instead, and only copy into retroarch-joypads directly
    # when it is a real directory (as on a device after the wizard ran).
    mkdir -p "$ra_auto_dir"
    cp "$CONFIG_DIR/retropie/retroarch-joypads/PS3 Controller.cfg" \
        "$ra_auto_dir/PS3 Controller.cfg" \
        || die "[retropie] Failed to install retroarch autoconfig"
    if [[ -L "$joy2k_dir" ]]; then
        :  # symlink -> file is already visible through retroarch/autoconfig
    elif [[ -d "$joy2k_dir" ]]; then
        cp "$CONFIG_DIR/retropie/retroarch-joypads/PS3 Controller.cfg" \
            "$joy2k_dir/PS3 Controller.cfg" \
            || die "[retropie] Failed to install retroarch-joypads autoconfig"
    else
        mkdir -p "$joy2k_dir"
        cp "$CONFIG_DIR/retropie/retroarch-joypads/PS3 Controller.cfg" \
            "$joy2k_dir/PS3 Controller.cfg" \
            || die "[retropie] Failed to install retroarch-joypads autoconfig"
    fi

    # flycast/reicast per-controller mapping (also generated by the wizard).
    local dc_maps="$rootfs/opt/retropie/configs/dreamcast/mappings"
    mkdir -p "$dc_maps"
    cp "$CONFIG_DIR/retropie/dreamcast/SDL_PS3 Controller.cfg" \
        "$dc_maps/SDL_PS3 Controller.cfg" \
        || die "[retropie] Failed to install flycast SDL mapping"
    cp "$CONFIG_DIR/retropie/dreamcast/evdev_PS3 Controller.cfg" \
        "$dc_maps/evdev_PS3 Controller.cfg" \
        || die "[retropie] Failed to install flycast evdev mapping"

    # mupen64plus: append the wizard-generated [PS3 Controller] section to the
    # stock InputAutoCfg.ini (which ships with a [Keyboard] section). If the
    # stock file is missing, install the full captured file instead.
    local iaf="$rootfs/opt/retropie/configs/n64/InputAutoCfg.ini"
    mkdir -p "$(dirname "$iaf")"
    if [[ -f "$iaf" ]] && grep -q '^\[Keyboard\]' "$iaf"; then
        if ! grep -q '^\[PS3 Controller\]' "$iaf"; then
            printf '\n' >> "$iaf"
            cat "$CONFIG_DIR/retropie/n64/InputAutoCfg.ps3controller.ini" >> "$iaf"
        fi
    else
        cp "$CONFIG_DIR/retropie/n64/InputAutoCfg.ini" "$iaf" \
            || die "[retropie] Failed to install n64 InputAutoCfg.ini"
    fi

    # chown the seeded paths to the pi user. retroarch-joypads may be a symlink
    # (then skip it; its real target autoconfig is chowned below).
    chown -R 1000:1000 "$ra_auto_dir" "$dc_maps" "$rootfs/opt/retropie/configs/n64"
    [[ -L "$joy2k_dir" ]] || chown -R 1000:1000 "$joy2k_dir"
    echo "  [retropie] Seeded joy2key autoconfig + emulator keymaps (retroarch, flycast, mupen64plus)"

    # Mono downmix audio module (see the block comment at the maps above).
    install_audio_module "$rootfs" "$mnt_boot" "$5"
}

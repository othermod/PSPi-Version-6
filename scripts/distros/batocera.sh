# Batocera variant carrying ONLY the stereo mono-downmix kernel module --
# batocera-noaudio.sh (stock PipeWire/ALSA/RetroArch userspace, no pactl
# wrapper, no asound.conf) with the prebuilt module from PSPi-6-Audio-Modules
# added back. The PSPi feeds one audio pin per board, so the patched
# snd-bcm2835 / rp1_aout downmixes (L+R)/2 and that pin carries the full
# stereo image; everything else stays exactly as Batocera ships it. Compare
# with batocera.sh, which additionally rewrites the userspace audio stack
# (pipewire off, ALSA defaults, retroarch/SDL drivers, pactl wrapper).
PATCH_METHOD="squashfs"
SQUASHFS_PATH="boot/batocera"
DRIVERS_BASE="/boot"
INIT_SYSTEM=sysv
SQUASHFS_COMP_ARGS="-comp zstd"

ALL_TARGETS=(cm4 cm5 zero2 zero1)

declare -A TARGET_URL TARGET_SHA256 TARGET_PSPI_PREFIX TARGET_BIN

TARGET_URL[cm4]="https://updates.batocera.org/bcm2711/stable/last/batocera-bcm2711-43.1-20260530.img.gz"
TARGET_URL[cm5]="https://updates.batocera.org/bcm2712/stable/last/batocera-bcm2712-43.1-20260529.img.gz"
TARGET_URL[zero2]="https://updates.batocera.org/bcm2837/stable/last/batocera-bcm2837-43.1-20260530.img.gz"
TARGET_URL[zero1]="https://updates.batocera.org/bcm2835/stable/last/batocera-bcm2835-43-20260507.img.gz"

TARGET_SHA256[cm4]="0cd09f3f6d37f5c64523d4a7e2f9f3658b1fbaf36bc440d32fcc1940898c2a13"
TARGET_SHA256[cm5]="17274ab36b452a26d4be8cfbba871b068da9b2c16bf962ae412a8468fed225c4"
TARGET_SHA256[zero2]="e12208735bcfa9013577557bd28a43e4f9320608e8c9dc30fdb6fa1ab5d51fe1"
TARGET_SHA256[zero1]="0c5a82a76e1db6613de5e6bfb6d271d73b7fbff46cd0aa18d9d9af42d1072afb"

TARGET_PSPI_PREFIX[cm4]="Batocera43.1-CM4-PSPi6"
TARGET_PSPI_PREFIX[cm5]="Batocera43.1-CM5-PSPi6"
TARGET_PSPI_PREFIX[zero2]="Batocera43.1-Zero2-PSPi6"
TARGET_PSPI_PREFIX[zero1]="Batocera43-Zero1-PSPi6"

TARGET_BIN[cm4]=64
TARGET_BIN[cm5]=64
TARGET_BIN[zero2]=64
TARGET_BIN[zero1]=32

# --- Stock-image torrent fallback ---
# updates.batocera.org redirects to mirrors.o2switch.fr, whose TLS certificate
# expired 2026-09-05; when direct download fails, the patcher falls back to
# these torrents (scripts/torrents/, committed to the repo). The bcm2711 and
# bcm2712 torrents are Batocera's official ones with the mirror injected as a
# web seed -- url-list lives outside the info dict, so the infohash (and thus
# Batocera's swarm) is preserved. bcm2837/bcm2835 have no official torrent;
# theirs were created with mktorrent. The web seed is deliberately plain
# http: torrent pieces are hash-verified by the client as they arrive, and
# the patcher's TARGET_SHA256 gate still applies to the assembled file.
declare -A TARGET_TORRENT

TARGET_TORRENT[cm4]="scripts/torrents/batocera-bcm2711-43.1-20260530.img.gz.torrent"
TARGET_TORRENT[cm5]="scripts/torrents/batocera-bcm2712-43.1-20260529.img.gz.torrent"
TARGET_TORRENT[zero2]="scripts/torrents/batocera-bcm2837-43.1-20260530.img.gz.torrent"
TARGET_TORRENT[zero1]="scripts/torrents/batocera-bcm2835-43-20260507.img.gz.torrent"

# --- Mono downmix audio module (prebuilt, PSPi-6-Audio-Modules releases) ---
# One audio pin per board, patched snd-bcm2835 / rp1_aout per target, fetched
# and verified by fetch_audio_module (patcher.sh). All four Batocera kernels
# have CONFIG_MODVERSIONS on; the release builds carry CRCs harvested from
# each image's stock module, so the swap is ABI-safe.
#
# cm4/zero2/zero1: the stock snd-bcm2835.ko sits at the standard vc04_services
# path (uncompressed on the 64-bit images, gzip-compressed .ko.gz on the 32-bit
# bcm2835 image), so the release build replaces it in place, matching the
# compression it found -- same module name and deps, shipped metadata stays
# valid, no depmod. Activation: the pspi-audio overlay's bootargs
# (snd_bcm2835.mono_mix=1) land on the kernel command line, and an
# /etc/modprobe.d option (a real directory here, unlike Lakka's /storage
# symlink) is the deterministic second channel.
#
# cm5: Batocera's bcm2712 kernel has NO rp1_audio_out driver at all
# (# CONFIG_SND_RP1_AUDIO_OUT is not set), so analog audio never worked on
# this image. The module is therefore NEW, not a replacement: it goes into
# /lib/modules/<kver>/updates/ and depmod regenerates the metadata so the
# of: alias for the DT node the cm5 overlay enables resolves to it. The
# same overlay's mono_mix override gates the downmix at probe.
declare -A MODULE_ASSET MODULE_VERMAGIC

MODULE_ASSET[cm4]="batocera-bcm2711-43.1-20260530-snd-bcm2835-mono.ko"
MODULE_ASSET[cm5]="batocera-bcm2712-43.1-20260529-rp1-aout-mono.ko"
MODULE_ASSET[zero2]="batocera-bcm2837-43.1-20260530-snd-bcm2835-mono.ko"
MODULE_ASSET[zero1]="batocera-bcm2835-43-20260507-snd-bcm2835-mono.ko"

MODULE_VERMAGIC[cm4]="6.12.62-v8 SMP preempt mod_unload modversions aarch64"
MODULE_VERMAGIC[cm5]="6.12.62 SMP preempt mod_unload modversions aarch64"
MODULE_VERMAGIC[zero2]="6.12.62-v8 SMP preempt mod_unload modversions aarch64"
MODULE_VERMAGIC[zero1]="6.12.62 mod_unload modversions ARMv6 p2v8"

install_audio_module() {
    local rootfs="$1" mnt_boot="$2" label="$3"
    local ko
    ko="$(fetch_audio_module "$label")"

    local modbase="$rootfs/lib/modules"
    local -a kvers=()
    local kd
    for kd in "$modbase"/*/; do
        [[ -d "$kd" ]] && kvers+=("$(basename "$kd")")
    done
    [[ ${#kvers[@]} -eq 1 ]] \
        || die "[batocera] expected exactly one kernel in $modbase, found: ${kvers[*]:-none}"
    local kver="${kvers[0]}"

    if [[ "$label" == "cm5" ]]; then
        # New driver, not a replacement -- see the block comment above.
        mkdir -p "$modbase/$kver/updates"
        cp "$ko" "$modbase/$kver/updates/rp1_aout.ko" \
            || die "[batocera] failed to install rp1_aout.ko into updates/"
        command -v depmod >/dev/null 2>&1 \
            || die "[batocera] depmod not found (kmod); needed to index the new rp1_aout module"
        depmod -b "$rootfs" "$kver" || die "[batocera] depmod failed for $kver"

        # Enable the DT property the patched rp1_aout reads at probe (the
        # generic patcher appended the bare overlay line under [cm5]).
        sed -i 's|^dtoverlay=pspi-audio-cm5-kernel6+$|dtoverlay=pspi-audio-cm5-kernel6+,mono_mix|' \
            "$mnt_boot/config.txt"
        grep -q '^dtoverlay=pspi-audio-cm5-kernel6+,mono_mix$' "$mnt_boot/config.txt" \
            || die "[batocera] failed to enable mono_mix on the cm5 audio overlay line"
        echo "  [batocera] Installed rp1-aout-mono into updates/ for $kver (depmod'd); mono_mix enabled in config.txt"
    else
        # The module dir is stable, but its compression isn't: the 64-bit
        # images ship snd-bcm2835.ko uncompressed while the 32-bit image
        # (bcm2835) ships every module gzip-compressed. Match whichever form
        # is present and install the replacement in the same form -- kmod's
        # modules.dep entries carry the suffix, and the kernel decompresses
        # at load, so the swap stays ABI- and metadata-neutral.
        local moddir="$modbase/$kver/kernel/drivers/staging/vc04_services/bcm2835-audio"
        local stock="" ext
        for ext in "" ".gz" ".xz" ".zst"; do
            [[ -f "$moddir/snd-bcm2835.ko$ext" ]] && stock="$moddir/snd-bcm2835.ko$ext" && break
        done
        [[ -n "$stock" ]] \
            || die "[batocera] stock module missing in $moddir (kernel or overlay layout drift)"
        case "$stock" in
            *.gz)  gzip -c "$ko" > "$stock"  || die "[batocera] failed to gzip $(basename "$ko") over $stock" ;;
            *.xz)  xz -c   "$ko" > "$stock"  || die "[batocera] failed to xz $(basename "$ko") over $stock" ;;
            *.zst) zstd -q -c "$ko" > "$stock" || die "[batocera] failed to zstd $(basename "$ko") over $stock" ;;
            *)     cp "$ko" "$stock"         || die "[batocera] failed to install $(basename "$ko") over $stock" ;;
        esac

        [[ -d "$rootfs/etc/modprobe.d" ]] \
            || die "[batocera] $rootfs/etc/modprobe.d missing"
        cat > "$rootfs/etc/modprobe.d/pspi-audio.conf" <<'CONF'
# PSPi 6: one PWM pin feeds the speaker; patched snd-bcm2835 (from
# PSPi-6-Audio-Modules) downmixes (L+R)/2 so that pin carries the full
# stereo image.
options snd_bcm2835 enable_headphones=Y mono_mix=Y
CONF
        echo "  [batocera] Installed snd-bcm2835-mono as $(basename "$stock") for $kver; mono_mix set via modprobe.d"
    fi
}

distro_post_patch() {
    local overlay_target="$1"
    local mnt_boot="$2"

    # Size optimization: firmware for wireless/graphics hardware the PSPi
    # cannot have. Also removes some USB WiFi adapter firmware -- if one stops
    # working, restore the matching directory.
    echo "  [batocera] Removing firmware for hardware the PSPi cannot have..."
    rm -rf "${overlay_target}/lib/firmware/intel" \
           "${overlay_target}/lib/firmware/ath11k" \
           "${overlay_target}/lib/firmware/mediatek" \
           "${overlay_target}/lib/firmware/ath12k" \
           "${overlay_target}/lib/firmware/rtw89"
    echo "  [batocera] Removed unused firmware"

    # Seed a Moonlight launcher so the system appears in EmulationStation on
    # first boot without needing a terminal. EmulationStation only lists a
    # system when it has at least one ROM, so this single .moonlight file is
    # what makes the Moonlight system show up. On first launch (no host yet)
    # it opens the moonlight-qt client GUI for host discovery and PIN pairing.
    local ml_seed="${overlay_target}/usr/share/batocera/datainit/roms/moonlight"
    if [[ -d "$ml_seed" ]]; then
        if [[ ! -e "$ml_seed/Moonlight.moonlight" ]]; then
            : > "$ml_seed/Moonlight.moonlight"
            echo "  [batocera] Seeded Moonlight launcher (Moonlight.moonlight)"
        else
            echo "  [batocera] Moonlight launcher already present"
        fi
    else
        echo "  [batocera] WARNING: datainit roms/moonlight not found, skipping Moonlight"
    fi

    # Mono downmix stereo module -- the only audio modification in this
    # variant (see the block comment at the maps above).
    install_audio_module "$overlay_target" "$mnt_boot" "$5"
}

PATCH_METHOD="squashfs"
SQUASHFS_PATH="boot/batocera"
DRIVERS_BASE="/boot"
INIT_SYSTEM=sysv
SQUASHFS_COMP_ARGS="-comp zstd"

ALL_TARGETS=(cm4 cm5 zero2 zero1)

declare -A TARGET_URL TARGET_SHA256 TARGET_PSPI_PREFIX TARGET_BIN

TARGET_URL[cm4]="https://updates.batocera.org/bcm2711/stable/last/batocera-bcm2711-43-20260501.img.gz"
TARGET_URL[cm5]="https://updates.batocera.org/bcm2712/stable/last/batocera-bcm2712-43-20260430.img.gz"
TARGET_URL[zero2]="https://updates.batocera.org/bcm2837/stable/last/batocera-bcm2837-43-20260508.img.gz"
TARGET_URL[zero1]="https://updates.batocera.org/bcm2835/stable/last/batocera-bcm2835-43-20260507.img.gz"

TARGET_SHA256[cm4]=""
TARGET_SHA256[cm5]=""
TARGET_SHA256[zero2]=""
TARGET_SHA256[zero1]=""

TARGET_PSPI_PREFIX[cm4]="Batocera43-CM4-PSPi6"
TARGET_PSPI_PREFIX[cm5]="Batocera43-CM5-PSPi6"
TARGET_PSPI_PREFIX[zero2]="Batocera43-Zero2-PSPi6"
TARGET_PSPI_PREFIX[zero1]="Batocera43-Zero1-PSPi6"

TARGET_BIN[cm4]=64
TARGET_BIN[cm5]=64
TARGET_BIN[zero2]=64
TARGET_BIN[zero1]=32

distro_post_patch() {
    local overlay_target="$1"
    local mnt_boot="$2"

    echo "  [batocera] Removing boot partition files..."
    rm -f "$mnt_boot/boot/rufomaculata"
    echo "  [batocera] Removed boot partition files"

    echo "  [batocera] Applying bcm2835 audio fix..."

    rm -rf "${overlay_target}/lib/firmware/intel" \
           "${overlay_target}/lib/firmware/ath11k" \
           "${overlay_target}/lib/firmware/mediatek" \
           "${overlay_target}/lib/firmware/ath12k" \
           "${overlay_target}/lib/firmware/rtw89"
    echo "  [batocera] Removed unused firmware"

    local s06audio="${overlay_target}/etc/init.d/S06audio"
    if [[ -f "$s06audio" ]]; then
        sed -i 's/^\([[:space:]]*\)start_pipewire[[:space:]]*$/\1# start_pipewire/' "$s06audio"
        echo "  [batocera] Disabled Pipewire in S06audio"
    else
        echo "  [batocera] WARNING: S06audio not found, skipping"
    fi

    mkdir -p "${overlay_target}/usr/share/alsa/alsa.conf.d"
    cat > "${overlay_target}/usr/share/alsa/alsa.conf.d/99-pspi-default.conf" << 'EOF'
defaults.pcm.card 0
defaults.ctl.card 0
EOF
    echo "  [batocera] Set ALSA default to card 0"

    local s31es="${overlay_target}/etc/init.d/S31emulationstation"
    if [[ -f "$s31es" ]]; then
        if ! grep -q "SDL_AUDIODRIVER" "$s31es"; then
            sed -i '/\. \/etc\/profile\.d\/dbus\.sh/a export SDL_AUDIODRIVER=alsa' "$s31es"
            echo "  [batocera] Set SDL_AUDIODRIVER=alsa in S31emulationstation"
        fi
    else
        echo "  [batocera] WARNING: S31emulationstation not found, skipping"
    fi

    local retroarch_cfg="${overlay_target}/etc/retroarch.cfg"
    if [[ -f "$retroarch_cfg" ]]; then
        sed -i 's/^#\?\s*audio_driver\s*=.*/audio_driver = alsathread/' "$retroarch_cfg"
        echo "  [batocera] Set audio_driver in retroarch.cfg"
    else
        echo "  [batocera] WARNING: retroarch.cfg not found, skipping"
    fi

    local seed="${overlay_target}/usr/share/batocera/datainit/system/batocera.conf"
    if [[ -f "$seed" ]]; then
        if grep -q "global.retroarch.audio_driver" "$seed"; then
            sed -i 's/global\.retroarch\.audio_driver=.*/global.retroarch.audio_driver=alsathread/' "$seed"
        else
            echo "global.retroarch.audio_driver=alsathread" >> "$seed"
        fi
        echo "  [batocera] Set RetroArch audio driver in datainit seed"
    else
        echo "  [batocera] WARNING: datainit batocera.conf not found, skipping"
    fi

    local pactl_bin="${overlay_target}/usr/bin/pactl"
    if [[ -f "$pactl_bin" ]]; then
        mv "$pactl_bin" "${pactl_bin}.real"
    fi
    cat > "$pactl_bin" << 'PACTL_EOF'
#!/bin/bash
# pactl -> amixer wrapper for bcm2835 PWM audio (PSPi)
# Translates Pipewire/PulseAudio volume commands to amixer.
# Unknown commands are forwarded to the real pactl binary.

CARD=0
CONTROL="PCM"
SINK_NAME="alsa_output.bcm2835"

get_volume() {
    amixer -c $CARD get "$CONTROL" 2>/dev/null | grep -o '[0-9]*%' | head -1 | tr -d '%'
}

get_mute() {
    amixer -c $CARD get "$CONTROL" 2>/dev/null | grep -o '\[on\]\|\[off\]' | head -1
}

case "$1" in
    info)
        echo "Default Sink: ${SINK_NAME}"
        ;;
    list)
        case "$2" in
            sinks-raw)
                VOL=$(get_volume)
                MUTE=$(get_mute)
                [ "$MUTE" = "[off]" ] && MUTE_VAL=1 || MUTE_VAL=0
                echo "sink=\"0\" name=\"${SINK_NAME}\" description=\"bcm2835 Headphones\" volume=\"${VOL}\" mute=\"${MUTE_VAL}\""
                ;;
            short)
                [ "$3" = "sinks" ] && echo "0	${SINK_NAME}	ALSA	s16le 2ch 44100Hz	RUNNING"
                ;;
            cards-profiles-raw)
                ;;
        esac
        ;;
    get-default-sink)
        echo "${SINK_NAME}"
        ;;
    set-default-sink|set-card-profile)
        ;;
    set-sink-volume)
        VOL="${3//%/}"
        amixer -c $CARD set "$CONTROL" "${VOL}%" -q 2>/dev/null
        ;;
    set-sink-mute)
        case "$3" in
            toggle) amixer -c $CARD set "$CONTROL" toggle -q 2>/dev/null ;;
            1)      amixer -c $CARD set "$CONTROL" mute -q 2>/dev/null ;;
            0)      amixer -c $CARD set "$CONTROL" unmute -q 2>/dev/null ;;
        esac
        ;;
    get-sink-mute)
        MUTE=$(get_mute)
        [ "$MUTE" = "[off]" ] && echo "Mute: yes" || echo "Mute: no"
        ;;
    *)
        exec /usr/bin/pactl.real "$@"
        ;;
esac
PACTL_EOF
    chmod +x "$pactl_bin"
    echo "  [batocera] Installed pactl amixer wrapper"

    echo "  [batocera] Audio fix complete"
}

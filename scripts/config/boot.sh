#!/usr/bin/env bash
CONF="./pspi.conf"

enable_dim=false
dim_seconds=120
fast_mode=false
disable_crc=false
input_type=gamepad
joysticks=1
deadzone=20
autocenter=false
verbose=false
extrabuttons=disabled
update_firmware=false
while IFS="=" read -r key value; do
    [[ "$key" =~ ^#.*$ || -z "$key" ]] && continue
    key=$(echo "$key" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    value=$(echo "$value" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    case "$key" in
        enable_dim) enable_dim="$value" ;;
        dim_seconds) dim_seconds="$value" ;;
        fast_mode) fast_mode="$value" ;;
        disable_crc) disable_crc="$value" ;;
        input_type) input_type="$value" ;;
        joysticks) joysticks="$value" ;;
        deadzone) deadzone="$value" ;;
        autocenter) autocenter="$value" ;;
        verbose) verbose="$value" ;;
        extrabuttons) extrabuttons="$value" ;;
        update_firmware) update_firmware="$value" ;;
    esac
done < "$CONF"

if [[ "$update_firmware" == "true" ]]; then
    ./drivers/update_firmware ./drivers/firmware.hex
    case $? in
        1) poweroff ;;
        2) echo "Firmware update failed, continuing boot." ;;
    esac
fi

GAMEPAD_ARGS=""
[[ "$enable_dim" == "true" ]] && GAMEPAD_ARGS="$GAMEPAD_ARGS --dim $dim_seconds"
[[ "$disable_crc" == "true" ]] && GAMEPAD_ARGS="$GAMEPAD_ARGS --nocrc"
[[ "$fast_mode" == "true" ]] && GAMEPAD_ARGS="$GAMEPAD_ARGS --fast"
[[ "$input_type" != "gamepad" ]] && GAMEPAD_ARGS="$GAMEPAD_ARGS --input $input_type"
[[ "$joysticks" != "1" ]] && GAMEPAD_ARGS="$GAMEPAD_ARGS --joysticks $joysticks"
[[ "$deadzone" != "20" ]] && GAMEPAD_ARGS="$GAMEPAD_ARGS --deadzone $deadzone"
[[ "$autocenter" == "true" ]] && GAMEPAD_ARGS="$GAMEPAD_ARGS --autocenter"
[[ "$verbose" == "true" ]] && GAMEPAD_ARGS="$GAMEPAD_ARGS --verbose"
[[ "$extrabuttons" != "disabled" ]] && GAMEPAD_ARGS="$GAMEPAD_ARGS --extrabuttons $extrabuttons"

./drivers/gamepad $GAMEPAD_ARGS &
./drivers/battery_monitor &
wait

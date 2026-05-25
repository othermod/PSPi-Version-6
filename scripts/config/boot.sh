#!/usr/bin/env bash
CONF="./pspi.conf"

modprobe i2c-dev

./drivers/battery_monitor &

# Wait for the I2C bus before starting anything that depends on it
until [ -e /dev/i2c-1 ]; do sleep 1; done

# Start the RTC daemon
./drivers/rtc &

# If firmware update binaries are present, schedule the update in the background.
# The rest of the system starts normally; the device powers off when the update
# completes, matching the original one-shot service behaviour.
if [[ -f ./drivers/update_firmware && -f ./drivers/firmware.hex ]]; then
    ( sleep 20 && ./drivers/update_firmware ./drivers/firmware.hex && /sbin/poweroff ) &
fi

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
while IFS="=" read -r key value; do
    [[ "$key" =~ ^#.*$ || -z "$key" ]] && continue
    key=$(echo "$key" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    value=$(echo "$value" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    case "$key" in
        enable_dim)   enable_dim="$value"   ;;
        dim_seconds)  dim_seconds="$value"  ;;
        fast_mode)    fast_mode="$value"    ;;
        disable_crc)  disable_crc="$value"  ;;
        input_type)   input_type="$value"   ;;
        joysticks)    joysticks="$value"    ;;
        deadzone)     deadzone="$value"     ;;
        autocenter)   autocenter="$value"   ;;
        verbose)      verbose="$value"      ;;
        extrabuttons) extrabuttons="$value" ;;
    esac
done < "$CONF"

GAMEPAD_ARGS=""
[[ "$enable_dim"    == "true" ]]     && GAMEPAD_ARGS="$GAMEPAD_ARGS --dim $dim_seconds"
[[ "$disable_crc"   == "true" ]]     && GAMEPAD_ARGS="$GAMEPAD_ARGS --nocrc"
[[ "$fast_mode"     == "true" ]]     && GAMEPAD_ARGS="$GAMEPAD_ARGS --fast"
[[ "$input_type"    != "gamepad" ]]  && GAMEPAD_ARGS="$GAMEPAD_ARGS --input $input_type"
[[ "$joysticks"     != "1" ]]        && GAMEPAD_ARGS="$GAMEPAD_ARGS --joysticks $joysticks"
[[ "$deadzone"      != "20" ]]       && GAMEPAD_ARGS="$GAMEPAD_ARGS --deadzone $deadzone"
[[ "$autocenter"    == "true" ]]     && GAMEPAD_ARGS="$GAMEPAD_ARGS --autocenter"
[[ "$verbose"       == "true" ]]     && GAMEPAD_ARGS="$GAMEPAD_ARGS --verbose"
[[ "$extrabuttons"  != "disabled" ]] && GAMEPAD_ARGS="$GAMEPAD_ARGS --extrabuttons $extrabuttons"

./drivers/gamepad $GAMEPAD_ARGS &
wait

#!/bin/sh
CONF="./pspi.conf"

modprobe i2c-dev

# Load the power_supply module where one exists (udev/UPower); silent otherwise.
modprobe pspi_battery 2>/dev/null

# Start the battery monitor early so the OS sees the battery
./drivers/battery_monitor &

# Wait for the I2C bus before starting anything that depends on it
until [ -e /dev/i2c-1 ]; do sleep 1; done

# The PCF8563 is driven by the i2c-rtc kernel overlay; userspace daemon unused.
#./drivers/rtc &

# Absent/empty keys fall through to the gamepad's compiled-in defaults, so
# pspi.conf is the single source of truth. Deliberately plain POSIX sh:
# Lakka/Batocera/Recalbox run this under busybox ash or dash (no real bash),
# so bash-only features would abort the script before the gamepad starts.
while IFS="=" read -r key value; do
    key=$(printf '%s' "$key" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    case "$key" in ''|\#*) continue ;; esac
    value=$(printf '%s' "$value" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    [ -n "$value" ] || continue
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

# --input must precede --joysticks/--extrabuttons (parser requires it).
GAMEPAD_ARGS=""
if [ "$enable_dim" = "true" ]; then
    # Bare --dim uses the gamepad's own default timeout
    GAMEPAD_ARGS="$GAMEPAD_ARGS --dim"
    [ -n "$dim_seconds" ] && GAMEPAD_ARGS="$GAMEPAD_ARGS $dim_seconds"
fi
[ "$disable_crc" = "true" ] && GAMEPAD_ARGS="$GAMEPAD_ARGS --nocrc"
[ "$fast_mode"   = "true" ] && GAMEPAD_ARGS="$GAMEPAD_ARGS --fast"
[ -n "$input_type" ]        && GAMEPAD_ARGS="$GAMEPAD_ARGS --input $input_type"
# --joysticks/--extrabuttons are gamepad-only: in mouse mode the binary skips
# the flag but consumes the value, then exits on the unknown argument.
if [ "$input_type" = "gamepad" ]; then
    [ -n "$joysticks" ] && GAMEPAD_ARGS="$GAMEPAD_ARGS --joysticks $joysticks"
fi
[ -n "$deadzone" ]         && GAMEPAD_ARGS="$GAMEPAD_ARGS --deadzone $deadzone"
[ "$autocenter" = "true" ] && GAMEPAD_ARGS="$GAMEPAD_ARGS --autocenter"
[ "$verbose"    = "true" ] && GAMEPAD_ARGS="$GAMEPAD_ARGS --verbose"
if [ "$input_type" = "gamepad" ]; then
    [ -n "$extrabuttons" ] && GAMEPAD_ARGS="$GAMEPAD_ARGS --extrabuttons $extrabuttons"
fi

# Restart the gamepad on crash: neither init system restarts boot.sh's
# children. Backoff handles both transient crashes and unsatisfiable configs
# (gamepad.c exits 1 for arg errors before the main loop and never exits 0).
(
    delay=2
    while true; do
        ./drivers/gamepad $GAMEPAD_ARGS
        rc=$?
        echo "gamepad exited ($rc); restarting in ${delay}s" >&2
        sleep "$delay"
        if [ "$delay" -lt 60 ]; then
            delay=$(( delay * 2 ))
        else
            delay=60
        fi
    done
) &

# On systemd, pspi-wifi.service owns wifi_monitor instead.
if [ "${PSPI_WIFI_MANAGED:-}" != "1" ]; then
    ./drivers/wifi_monitor &
fi

wait

#!/usr/bin/env bash
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
# pspi.conf is the single source of truth.
declare -A conf
while IFS="=" read -r key value; do
    key="${key//[[:space:]]/}"
    [[ -z "$key" || "$key" == \#* ]] && continue
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    [[ -n "$value" ]] && conf["$key"]="$value"
done < "$CONF"

set_flag() {   # set_flag <key> <flag>: pass the flag when the key is "true"
    [[ "${conf[$1]:-}" == "true" ]] && GAMEPAD_ARGS+=("$2")
}

set_value() {  # set_value <key> <flag>: pass the flag and its value when set
    [[ -n "${conf[$1]:-}" ]] && GAMEPAD_ARGS+=("$2" "${conf[$1]}")
}

# --input must precede --joysticks/--extrabuttons (parser requires it).
GAMEPAD_ARGS=()
if [[ "${conf[enable_dim]:-}" == "true" ]]; then
    # Bare --dim uses the gamepad's own default timeout
    GAMEPAD_ARGS+=(--dim)
    [[ -n "${conf[dim_seconds]:-}" ]] && GAMEPAD_ARGS+=("${conf[dim_seconds]}")
fi
set_flag  disable_crc  --nocrc
set_flag  fast_mode    --fast
set_value input_type   --input
# --joysticks/--extrabuttons are gamepad-only: in mouse mode the binary skips
# the flag but consumes the value, then exits on the unknown argument.
if [[ "${conf[input_type]:-gamepad}" == "gamepad" ]]; then
    set_value joysticks    --joysticks
fi
set_value deadzone     --deadzone
set_flag  autocenter   --autocenter
set_flag  verbose      --verbose
if [[ "${conf[input_type]:-gamepad}" == "gamepad" ]]; then
    set_value extrabuttons --extrabuttons
fi

# Restart the gamepad on crash: neither init system restarts boot.sh's
# children. Backoff handles both transient crashes and unsatisfiable configs
# (gamepad.c exits 1 for arg errors before the main loop and never exits 0).
(
    delay=2
    while true; do
        ./drivers/gamepad "${GAMEPAD_ARGS[@]}"
        rc=$?
        echo "gamepad exited ($rc); restarting in ${delay}s" >&2
        sleep "$delay"
        (( delay < 60 )) && delay=$(( delay * 2 )) || delay=60
    done
) &

# On systemd, pspi-wifi.service owns wifi_monitor instead.
if [[ "${PSPI_WIFI_MANAGED:-}" != "1" ]]; then
    ./drivers/wifi_monitor &
fi

wait

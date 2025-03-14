#!/bin/bash

. /boot/pspi.conf
modprobe i2c-dev

echo "enable_dim: $enable_dim"
echo "dim_seconds: $dim_seconds"
echo "fast_mode: $fast_mode"
echo "disable_crc: $disable_crc"
echo "disable_gamepad: $disable_gamepad"
echo "joysticks: $joysticks"
echo "disable_osd: $disable_osd"

params=""

# Set additional parameters based on configuration variables
if [ "$enable_dim" = "true" ]; then
    params="$params --dim $dim_seconds  "
fi

if [ "$fast_mode" = "true" ]; then
    params="$params --fast "
fi

if [ "$disable_crc" = "true" ]; then
    params="$params --nocrc "
fi

if [ "$disable_gamepad" = "true" ]; then
    params="$params --nogamepad "
fi

echo "Starting PSPi with parameters: $params"

/boot/drivers/main $params &

if [ "$disable_osd" = "false" ]; then
    sleep 1
    /boot/drivers/osd &
fi

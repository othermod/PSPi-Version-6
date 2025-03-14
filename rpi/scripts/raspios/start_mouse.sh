#!/bin/bash

. /boot/firmware/pspi.conf
modprobe i2c-dev

echo "enable_mouse: $enable_mouse"

echo "Starting PSPi with parameters: $params"

if [ "$enable_mouse" = "true" ]; then
    /usr/bin/mouse
fi
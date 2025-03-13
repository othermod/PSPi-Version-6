#!/bin/bash

if [ "$(uname -m)" = "armv7l" ]; then
    . /boot/pspi.conf
else
    . /boot/firmware/pspi.conf
fi

echo "disable_osd: $disable_osd"

if [ "$disable_osd" = "false" ]; then
    /usr/bin/osd
fi
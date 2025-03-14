#!/bin/bash

. /boot/pspi.conf

echo "disable_osd: $disable_osd"

if [ "$disable_osd" = "false" ]; then
    /usr/bin/osd
fi

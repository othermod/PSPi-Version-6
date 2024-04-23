#!/bin/sh

modprobe i2c-dev
sleep 1
/boot/drivers/main_64 &
sleep 1
/boot/drivers/osd_64

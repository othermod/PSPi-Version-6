modprobe i2c-dev
cp -v /boot/lib/* /usr/lib/
sleep 1
/boot/drivers/bin/main_64 &
sleep 1
/boot/drivers/bin/gamepad_64 &
/boot/drivers/bin/osd_64 &
bash /userdata/system/resize.sh

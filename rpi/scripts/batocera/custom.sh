modprobe i2c-dev
cp -v /boot/lib/* /usr/lib/
sleep 1
/boot/drivers/main_64 &
sleep 1
/boot/drivers/gamepad_64 &
/boot/drivers/osd_64 &
bash /userdata/system/resize.sh

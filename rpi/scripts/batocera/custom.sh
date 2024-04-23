modprobe i2c-dev
cp -v /boot/libraries/* /usr/lib/
sleep 1
/boot/drivers/main_64 --dim &
sleep 1
/boot/drivers/osd_64 &
bash /userdata/system/resize.sh

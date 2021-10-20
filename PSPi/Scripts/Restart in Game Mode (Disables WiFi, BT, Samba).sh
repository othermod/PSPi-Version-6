#!/bin/bash
echo "Checking status in config.txt"
grep '#dtoverlay=pi3-disable-wifi' /boot/config.txt >/dev/null
if [ $? -eq 0 ]; then
	echo "Disabling WiFi and BT in config.txt"
	sudo sed -i 's/#dtoverlay=pi3-disable-wifi/dtoverlay=pi3-disable-wifi/' /boot/config.txt
	sudo sed -i 's/#dtoverlay=pi3-disable-bt/dtoverlay=pi3-disable-bt/' /boot/config.txt
	echo "Disabling services"
	sudo update-rc.d nmbd disable 2> /dev/null
	echo "-smbd"
	sudo systemctl stop smbd 2> /dev/null
	sudo systemctl disable smbd 2> /dev/null
	echo "Rebooting"
	sleep 1
	sudo reboot
else
	echo "WiFi and BT appear to already be disabled"
	sleep 1
fi
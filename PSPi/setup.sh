#!/bin/bash
# https://www.othermod.com
if [ $(id -u) -ne 0 ]; then
	echo "Installer must be run as root."
	echo "Try 'sudo bash $0'"
	exit 1
fi

#killall emulationstatio 2>/dev/null
killall pspi-controller 2>/dev/null
killall pngview 2>/dev/null
sleep 1
echo "Copying files"


# Make directory for driver and other files
rm -r /home/pi/PSPi 2>/dev/null
mkdir /home/pi/PSPi

# Startup image
cp -f /boot/PSPi/Theme/pspi.png /home/pi/RetroPie/splashscreens/pspi.png
cp -f /boot/PSPi/Theme/splashscreen.list /etc/splashscreen.list

# Controller Software
mkdir /home/pi/PSPi/Driver
cp -r /boot/PSPi/Driver/. /home/pi/PSPi/Driver

# Controller Configs
cp -f /boot/PSPi/Configs/es_input.cfg /opt/retropie/configs/all/emulationstation/es_input.cfg
cp -f /boot/PSPi/Configs/es_settings.cfg /opt/retropie/configs/all/emulationstation/es_settings.cfg
cp -f /boot/PSPi/Configs/retroarch.cfg /opt/retropie/configs/all/retroarch.cfg
cp -f "/boot/PSPi/Configs/PSPi Controller.cfg" "/opt/retropie/configs/all/retroarch-joypads/PSPi Controller.cfg"

# Console Scripts
cp -f /boot/PSPi/Theme/es_systems.cfg /etc/emulationstation/es_systems.cfg
mkdir /home/pi/PSPi/Scripts >/dev/null
cp -r /boot/PSPi/Scripts/. /home/pi/PSPi/Scripts

# Theme
cp -r /boot/PSPi/Console/. /etc/emulationstation/themes/carbon/PSPi/
cp -f /boot/pspi/Theme/background.png /etc/emulationstation/themes/carbon/art/carbon_fiber.png
cp -f /boot/PSPi/Theme/carbon.xml /etc/emulationstation/themes/carbon/carbon.xml

# Remove verbose startup/shutdown to shave time off startup
grep fastboot /boot/cmdline.txt >/dev/null
if [ $? -eq 0 ]; then
        echo "fastboot is already in cmdline.txt"
else
        echo "adding fastboot to cmdline.txt"
        sed -i ' 1 s/.*/& fastboot/' /boot/cmdline.txt >/dev/null
fi
grep quiet /boot/cmdline.txt >/dev/null
if [ $? -eq 0 ]; then
        echo "quiet is already in cmdline.txt"
else
        echo "adding quiet to cmdline.txt"
        sed -i ' 1 s/.*/& quiet/' /boot/cmdline.txt >/dev/null
fi

# remove DHCP wait, for faster bootup
rm -f /etc/systemd/system/dhcpcd.service.d/wait.conf 2>/dev/null
sleep 1
echo "Enabling I2C"

INTERACTIVE=False
BLACKLIST=/etc/modprobe.d/raspi-blacklist.conf
CONFIG=/boot/config.txt

do_i2c() {
    SETTING=on
    STATUS=enabled

#  set_config_var dtparam=i2c_arm $SETTING $CONFIG &&
  if ! [ -e $BLACKLIST ]; then
    touch $BLACKLIST
  fi
  sed $BLACKLIST -i -e "s/^\(blacklist[[:space:]]*i2c[-_]bcm2708\)/#\1/"
  sed /etc/modules -i -e "s/^#[[:space:]]*\(i2c[-_]dev\)/\1/"
  if ! grep -q "^i2c[-_]dev" /etc/modules; then
    printf "i2c-dev\n" >> /etc/modules
  fi
  dtparam i2c_arm=$SETTING
  modprobe i2c-dev
}

do_i2c

# create services
systemctl stop disablehdmi 2>/dev/null
systemctl stop pspi_controller 2>/dev/null
systemctl disable disablehdmi 2>/dev/null
systemctl disable pspi_controller 2>/dev/null
cp -f /boot/PSPi/Configs/pspi_controller.service /etc/systemd/system/pspi_controller.service
systemctl enable pspi_controller 2>/dev/null

# fix file permissions
chmod 0755 /home/pi/PSPi/Driver/pspi-controller
chmod 0755 /home/pi/PSPi/Driver/pngview

echo "Rebooting"
sleep 1
reboot

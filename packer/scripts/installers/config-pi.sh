#!/bin/bash -e
################################################################################
##  File:  configure-apt.sh
##  Desc:  Configure apt, install jq and apt-fast packages.
################################################################################
set -x

CONFIG=/boot/config.txt
cat /etc/hostname
cat /etc/hosts

locale=en_US.UTF-8
layout=us
raspi-config nonint do_change_locale $locale
raspi-config nonint do_configure_keyboard $layout
raspi-config nonint do_hostname pspi6
# raspi-config nonint do_boot_splash 0
raspi-config nonint do_i2c 1
sed -i "s/dtoverlay=vc4-kms-v3d/dtoverlay=vc4-fkms-v3d/g" $CONFIG
sed -i "s/camera_auto_detect=1/#camera_auto_detect=1/g" $CONFIG
sed -i "s/display_auto_detect=1/#display_auto_detect=1/g" $CONFIG
sed -i "s/max_framebuffers=2/max_framebuffers=1/g" $CONFIG
sed -i "s/dtoverlay=dwc2/dtoverlay=dwc2,dr_mode=host/g" $CONFIG
cat <<EOF >> $CONFIG
# Enable audio (loads snd_bcm2835)
dtparam=audio=on

# Reduce I2C speed to avoid clock bug in Raspberry Pi I2C
dtparam=i2c_baudrate=25000

#disable HDMI audio
hdmi_ignore_edid_audio=1

#Configure DPI signal
framebuffer_width=800
framebuffer_height=480
enable_dpi_lcd=1
display_default_lcd=1
dpi_group=2
dpi_mode=87
dpi_output_format=503863

over_voltage=-2
EOF
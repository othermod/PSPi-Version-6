#!/bin/bash -e
################################################################################
##  File:  configure-apt.sh
##  Desc:  Configure apt, install jq and apt-fast packages.
################################################################################
set -x

CONFIG=/boot/config.txt
locale=en_US.UTF-8
layout=us

# Workaround: Temp hardcode nameserver to 8.8.8.8
mv /etc/resolv.conf /etc/resolv.conf.bak
echo 'nameserver 8.8.8.8' > /etc/resolv.conf

raspi-config nonint do_change_locale $locale
raspi-config nonint do_configure_keyboard $layout
raspi-config nonint do_hostname pspi6
raspi-config nonint do_expand_rootfs 
raspi-config nonint do_change_timezone UTC
cat <<EOF >> $CONFIG
# Don't show splash screen
disable_splash=1

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
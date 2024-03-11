#!/bin/bash -e
################################################################################
##  File:  config-pi.sh
##  Desc:  Configure raspberry pi
################################################################################

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
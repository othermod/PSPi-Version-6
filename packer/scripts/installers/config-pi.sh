#!/bin/bash -e
################################################################################
##  File:  configure-apt.sh
##  Desc:  Configure apt, install jq and apt-fast packages.
################################################################################
set -x

cat /etc/hostname
cat /etc/hosts

locale=en_US.UTF-8
layout=us
raspi-config nonint do_change_locale $locale
raspi-config nonint do_configure_keyboard $layout
raspi-config nonint do_hostname pspi6
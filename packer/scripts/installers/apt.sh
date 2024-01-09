#!/bin/bash -e
################################################################################
##  File:  configure-apt.sh
##  Desc:  Configure apt, install jq and apt-fast packages.
################################################################################

apt update
apt full-upgrade -y

# Install & enable i2c
apt install i2c-tools -y
raspi-config nonint do_i2c 1
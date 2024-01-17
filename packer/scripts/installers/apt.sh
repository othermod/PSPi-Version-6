#!/bin/bash -e
################################################################################
##  File:  configure-apt.sh
##  Desc:  Configure apt, install jq and apt-fast packages.
################################################################################

df -h

apt-get update
apt full-upgrade -y

# Install & enable i2c
apt-get install i2c-tools -y
raspi-config nonint do_i2c 1
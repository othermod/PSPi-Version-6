#!/bin/bash -e
################################################################################
##  File:  apt.sh
##  Desc:  Update OS & Install any required packages for PSPi
################################################################################

df -h

apt-get update

# Ensure the system clock is synchronized
sudo apt install -y ntpdate
sudo ntpdate pool.ntp.org

# Install & enable i2c
set +e
apt-get install i2c-tools -y
raspi-config nonint do_i2c 1
set -e
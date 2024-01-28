#!/bin/bash -e
################################################################################
##  File:  build-drivers.sh
##  Desc:  Installs required dependencies for PSPi6 drivers & builds them
################################################################################

# Install Dependencies
apt-get update
apt-get install make libraspberrypi-dev raspberrypi-kernel-headers libpng-dev libasound2-dev -y

cd /packer/drivers
make clean
make all

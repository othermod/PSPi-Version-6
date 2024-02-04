#!/bin/bash -e
################################################################################
##  File:  build-drivers.sh
##  Desc:  Installs required dependencies for PSPi6 drivers & builds them
################################################################################
set -x

# Install Dependencies
apt-get update
apt-get install make libraspberrypi-dev raspberrypi-kernel-headers libpng-dev libasound2-dev git -y

cd /packer/drivers
make clean
make all

# Build patchelf
git clone https://github.com/NixOS/patchelf.git
cd patchelf
./bootstrap.sh
./configure
make
make check
make install

# Patch OSD Driver
patchelf --replace-needed libbcm_host.so.0 libbcm_host.so ../osd
#!/bin/bash -e
################################################################################
##  File:  build-drivers.sh
##  Desc:  Update OS & Install any required packages for PSPi
################################################################################

# Install Dependencies
apt-get update
apt-get install make libraspberrypi-dev raspberrypi-kernel-headers -y

cd /packer/drivers
make
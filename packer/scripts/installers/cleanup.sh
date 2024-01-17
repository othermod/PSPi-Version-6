#!/bin/bash -e
################################################################################
##  File:  cleanup.sh
##  Desc:  This script is responsible for performing cleanup tasks after the installation process. It removes temporary files, cleans up the system, and ensures that the environment is left in a clean state.
################################################################################

rm -rf /etc/resolv.conf
mv /etc/resolv.conf.bak /etc/resolv.con
rm -rf /packer
#!/bin/bash -e
################################################################################
##  File:  configure-apt.sh
##  Desc:  Configure apt, install jq and apt-fast packages.
################################################################################

rm -rf /etc/resolv.conf
mv /etc/resolv.conf.bak /etc/resolv.con
rm -rf /packer
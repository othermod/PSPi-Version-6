#!/bin/bash -x -e
################################################################################
##  File:  configure-apt.sh
##  Desc:  Configure apt, install jq and apt-fast packages.
################################################################################

systemctl stop userconfig
systemctl disable userconfig
systemctl mask userconfig
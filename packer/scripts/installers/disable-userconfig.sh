#!/bin/bash -e
################################################################################
##  File:  configure-apt.sh
##  Desc:  Configure apt, install jq and apt-fast packages.
################################################################################
set -x

systemctl stop userconfig
systemctl disable userconfig
systemctl mask userconfig
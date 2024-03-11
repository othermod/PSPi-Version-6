#!/bin/bash -e
################################################################################
##  File:  disable-userconfig.sh
##  Desc:  Stop & disable userconfig service
################################################################################

systemctl stop userconfig
systemctl disable userconfig
systemctl mask userconfig
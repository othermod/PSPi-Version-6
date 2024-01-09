#!/bin/bash
set -e

apt-get install cloud-init -y

touch /boot/meta-data
touch /boot/user-data

# Disable dhcpcd - it has a conflict with cloud-init network config
systemctl mask dhcpcd
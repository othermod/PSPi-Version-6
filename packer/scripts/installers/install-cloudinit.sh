#!/bin/bash
set -x -e

apt install cloud-init -y

touch /boot/meta-data
touch /boot/user-data

# Disable dhcpcd - it has a conflict with cloud-init network config
systemctl mask dhcpcd

cat <<EOF >/etc/cloud/cloud.cfg.d/99_datasource.cfg
datasource_list: [ NoCloud, None ]
datasource:
  NoCloud:
    fs_label: boot
EOF

cat <<EOF >/etc/cloud/cloud.cfg.d/99_user.cfg
users:
  - default

system_info:
    default_user:
    name: pi
    lock_passwd: false
    gecos: Raspbian
    groups: [pi adm dialout cdrom sudo audio video plugdev games users input netdev spi i2c gpio]
    sudo: ["ALL=(ALL) NOPASSWD: ALL"]
    shell: /bin/bash
    package_mirrors:
    - arches: [default]
    failsafe:
    primary: http://raspbian.raspberrypi.org/raspbian
    security: http://raspbian.raspberrypi.org/raspbian
EOF
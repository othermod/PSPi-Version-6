#!/bin/bash -e
################################################################################
##  File:  install-pspi6.sh
##  Desc: This script is used to install Retropie onto a PiOS arch64 image. It contains the necessary installation steps and dependencies required for the installation process.
##  https://retropie.org.uk/docs/Manual-Installation/
##  https://www.youtube.com/watch?v=PAePvz6YSWo
################################################################################
set -x

apt update
apt upgrade -y
apt install git lsb-release -y

# Install RetroPie
cd /opt
git clone --depth=1 https://github.com/RetroPie/RetroPie-Setup.git
cd RetroPie-Setup
chmod +x /opt/RetroPie-Setup/retropie_packages.sh

/opt/RetroPie-Setup/retropie_packages.sh setup basic_install
/opt/RetroPie-Setup/retropie_packages.sh samba depends
/opt/RetroPie-Setup/retropie_packages.sh samba install_shares
/opt/RetroPie-Setup/retropie_packages.sh splashscreen default
/opt/RetroPie-Setup/retropie_packages.sh splashscreen enable
/opt/RetroPie-Setup/retropie_packages.sh bashwelcometweak
/opt/RetroPie-Setup/retropie_packages.sh autostart enable
#!/bin/bash -e
################################################################################
##  File:  install-pspi6.sh
##  Desc: This script is used to install Retropie onto a PiOS arch64 image. It contains the necessary installation steps and dependencies required for the installation process.
##  https://retropie.org.uk/docs/Manual-Installation/
##  https://www.youtube.com/watch?v=PAePvz6YSWo
################################################################################
set -x

sudo apt update
sudo apt upgrade -y
sudo apt install git lsb-release -y

# Install RetroPie
sudo cd /opt
sudo git clone --depth=1 https://github.com/RetroPie/RetroPie-Setup.git
sudo cd RetroPie-Setup
sudo chmod +x /opt/RetroPie-Setup/retropie_packages.sh

sudo /opt/RetroPie-Setup/retropie_packages.sh setup basic_install
sudo /opt/RetroPie-Setup/retropie_packages.sh samba depends
sudo /opt/RetroPie-Setup/retropie_packages.sh samba install_shares
sudo /opt/RetroPie-Setup/retropie_packages.sh splashscreen default
sudo /opt/RetroPie-Setup/retropie_packages.sh splashscreen enable
sudo /opt/RetroPie-Setup/retropie_packages.sh bashwelcometweak
sudo /opt/RetroPie-Setup/retropie_packages.sh autostart enable
#!/bin/bash -e
################################################################################
##  File:  install-pspi6.sh
##  Desc: This script is used to install PSPi Version 6. It contains the necessary installation steps and dependencies required for the installation process.
################################################################################
set -x

detect_os_and_setup_services() {
    echo "Operating System Detected: $OS"
    case "$OS" in
    Debian | Raspios | Kali | ubuntu)
        default_setup
        ;;
    RetroPie)
        retropie_setup
        ;;
    *)
        unknown_setup
        ;;
    esac
}

unknown_setup() {
    echo "Unknown or unsupported OS. Manual setup may be required."
}

default_setup() {
    echo "Configuring RaspiOS..."

    enable_i2c
    set_binary_permissions
    add_services "main osd mouse"
}

retropie_setup() {
    echo "Configuring RetroPie..."

    enable_i2c
    set_binary_permissions
    add_services "main osd"
}

set_binary_permissions() {
    echo "Setting permissions on binaries..."
    chmod +x /usr/bin/main_64
    chmod +x /usr/bin/mouse_64
    chmod +x /usr/bin/osd_64
    chmod +x /usr/local/bin/start_main.sh
    chmod +x /usr/local/bin/start_osd.sh
    chmod +x /usr/local/bin/start_mouse.sh
}

enable_i2c() {
    echo "Enabling I2C..."
    BLACKLIST=/etc/modprobe.d/raspi-blacklist.conf

    # Handle the blacklist file for I2C
    if [ -e $BLACKLIST ]; then
        sed -i "s/^\(blacklist[[:space:]]*i2c[-_]bcm2708\)/#\1/" $BLACKLIST
    fi

    # Ensure i2c-dev is in /etc/modules
    if ! grep -q "^i2c[-_]dev" /etc/modules; then
        echo "i2c-dev" >>/etc/modules
    fi

    # Enable the I2C device
    set +e
    modprobe i2c-dev
    set -e
}

add_services() {
    echo "Installing and enabling services..."
    systemctl daemon-reload

    # Enable services
    for service in $1; do
        systemctl enable ${service}.service
    done

    echo "Services added."
}

detect_os_and_setup_services

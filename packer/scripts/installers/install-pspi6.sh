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
    RetroPie_32)
        retropie_32_setup
        ;;
    RetroPie_64)
        retropie_64_setup
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
    set_binary_permissions "/usr/bin/mouse_64 /usr/bin/main_64 /usr/bin/osd_64 /usr/local/bin/start_mouse.sh /usr/local/bin/start_main.sh /usr/local/bin/start_osd.sh"
    add_services "main osd mouse"
}

retropie_32_setup() {
    echo "Configuring RetroPie..."

    enable_i2c
    set_binary_permissions "/usr/bin/main /usr/bin/osd /usr/local/bin/start_main.sh /usr/local/bin/start_osd.sh"
    add_services "main osd"
}

retropie_64_setup() {
    echo "Configuring RetroPie..."

    enable_i2c
    set_binary_permissions "/usr/bin/main_64 /usr/bin/osd_64 /usr/local/bin/start_main.sh /usr/local/bin/start_osd.sh"
    add_services "main osd"
    echo "Adding user 'pi' to passwordless sudo..."
    cat <<EOF | sudo tee /etc/sudoers.d/pi
pi ALL=(ALL) NOPASSWD:ALL
EOF
    sudo chmod 440 /etc/sudoers.d/pi
}

set_binary_permissions() {
    echo "Setting permissions on binaries..."
    for binary in $1; do
        chmod +x $binary
    done
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

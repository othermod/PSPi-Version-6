#!/bin/bash -e
################################################################################
##  File:  install-pspi6.sh
##  Desc: This script is used to install PSPi Version 6. It contains the necessary installation steps and dependencies required for the installation process.
################################################################################
set -x

detect_architecture() {
    local arch
    arch=$(uname -m)
    case "$arch" in
    x86_64 | aarch64)
        echo "64-bit OS detected"
        ARCH_SUFFIX="_64"
        ;;
    *)
        echo "32-bit OS detected"
        ARCH_SUFFIX="_32"
        ;;
    esac
}

detect_os_and_setup_services() {
    echo "Operating System Detected: $OS"
    case "$OS" in
    Debian | Raspios | RetroPie)
        raspios_setup
        ;;
    Ubuntu)
        ubuntu_setup
        ;;
    Lakka)
        lakka_setup
        ;;
    *)
        unknown_setup
        ;;
    esac
}

unknown_setup() {
    echo "Unknown or unsupported OS. Manual setup may be required."
}

raspios_setup() {
    enable_i2c
    set_binary_permissions
    add_services
}

ubuntu_setup() {
    set_binary_permissions
    add_services
}

lakka_setup() {
    echo "Configuring Lakka..."

    # Make autostart executable
    chmod +x /storage/.config/autostart.sh

    # Modify a line in retroarch.cfg
    sed -i '/input_quit_gamepad_combo/c\input_quit_gamepad_combo = "4"' /storage/.config/retroarch/retroarch.cfg
    echo "Modified input_quit_gamepad_combo in retroarch.cfg."
}

set_binary_permissions() {
    echo "Setting permissions on binaries..."
    case "$ARCH_SUFFIX" in
    _64)
        chmod +x /usr/bin/gamepad_64
        chmod +x /usr/bin/main_64
        chmod +x /usr/bin/mouse_64
        chmod +x /usr/bin/osd_64
        ;;
    _32)
        chmod +x /usr/bin/gamepad_32
        chmod +x /usr/bin/main_32
        chmod +x /usr/bin/mouse_32
        chmod +x /usr/bin/osd_32
        ;;
    *)
        echo "Unknown or unsupported architecture."
        ;;
    esac
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
    for service in main osd mouse gamepad; do
        systemctl enable ${service}${ARCH_SUFFIX}.service
    done

    echo "Services added."
}

detect_architecture
detect_os_and_setup_services

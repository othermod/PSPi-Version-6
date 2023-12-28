#!/bin/bash

detect_architecture() {
    local arch
    arch=$(uname -m)
    case "$arch" in
        x86_64|aarch64)
            echo "64-bit OS detected"
            ARCH_SUFFIX="_64"
            ;;
        *)
            echo "32-bit OS detected"
            ARCH_SUFFIX="_32"
            ;;
    esac
}

lakka_setup() {
    echo "Lakka OS detected. Setting up autostart script..."

    if [ -f "/storage/.config/autostart.sh" ]; then
        mv "/storage/.config/autostart.sh" "/storage/.config/autostart.old"
        echo "Renamed existing autostart.sh to autostart.old"
    fi

    cat << EOF > /storage/.config/autostart.sh
#!/bin/bash
/flash/drivers/bin/./main$ARCH_SUFFIX &
sleep 1
/flash/drivers/bin/./gamepad$ARCH_SUFFIX &
/flash/drivers/bin/./osd$ARCH_SUFFIX &
EOF

    chmod +x /storage/.config/autostart.sh
    echo "New autostart.sh for Lakka created and configured."
}

batocera_setup() {
    echo "batocera"
}

raspbian_setup() {
    enable_i2c
    remove_services
    copy_binaries
    add_services
}

ubuntu_setup() {
    remove_services
    copy_binaries
    add_services
}

remove_services() {
    echo "Disabling and removing existing services..."
    # Stop and disable existing services
    for service in main osd mouse gamepad; do
        sudo systemctl stop ${service}${ARCH_SUFFIX}.service 2>/dev/null || true
        sudo systemctl disable ${service}${ARCH_SUFFIX}.service 2>/dev/null || true
    done
    echo "Existing services removed."
}

enable_i2c() {
    echo "Enabling I2C..."
    SETTING=on
    CONFIG=/boot/config.txt
    BLACKLIST=/etc/modprobe.d/raspi-blacklist.conf

    # Check if the dtparam=i2c_arm line exists and is not commented out
    if grep -q "^dtparam=i2c_arm=.*" $CONFIG; then
        # dtparam line exists, ensure it is set to 'on'
        sed -i "s/^dtparam=i2c_arm=.*/dtparam=i2c_arm=$SETTING/" $CONFIG
    elif grep -q "^#dtparam=i2c_arm=.*" $CONFIG; then
        # dtparam line is commented, uncomment and set to 'on'
        sed -i "s/^#dtparam=i2c_arm=.*/dtparam=i2c_arm=$SETTING/" $CONFIG
    else
        # dtparam line does not exist, add it
        echo "dtparam=i2c_arm=$SETTING" >> $CONFIG
    fi

    # Handle the blacklist file for I2C
    if [ -e $BLACKLIST ]; then
        sed -i "s/^\(blacklist[[:space:]]*i2c[-_]bcm2708\)/#\1/" $BLACKLIST
    fi

    # Ensure i2c-dev is in /etc/modules
    if ! grep -q "^i2c[-_]dev" /etc/modules; then
        echo "i2c-dev" >> /etc/modules
    fi

    # Enable the I2C device
    modprobe i2c-dev
}

copy_binaries() {
    echo "Copying binaries from /boot/drivers/bin/ to /usr/share/bin/..."
    # Copy all files from the source directory to the target directory
    sudo cp -r /boot/drivers/bin/* /usr/bin/
}

add_services() {
    echo "Installing and enabling services..."
    # Copy new service files
    sudo cp /boot/services/* /etc/systemd/system/
    sudo systemctl daemon-reload

    # Always enable and start main and osd services
    for service in main osd; do
        sudo systemctl enable ${service}${ARCH_SUFFIX}.service
        sudo systemctl start ${service}${ARCH_SUFFIX}.service
    done

    # User choice for mouse and gamepad services
    for service in mouse gamepad; do
        read -p "Enable and start the ${service} service? [y/N]: " enable_service
        if [ "$enable_service" = "y" ]; then
            sudo systemctl enable ${service}${ARCH_SUFFIX}.service
            sudo systemctl start ${service}${ARCH_SUFFIX}.service
        else
            echo "Skipping ${service}${ARCH_SUFFIX} service"
        fi
    done

    echo "Services added and started."
}

unknown_setup() {
    echo "Unknown or unsupported OS. Manual setup may be required."
}

detect_os_and_setup_services() {
    OS=$(grep '^ID=' /etc/os-release | cut -d= -f2 | tr -d '"')
    echo "Operating System Detected: $OS"
    case "$OS" in
        batocera)
            batocera_setup
            ;;
        debian)
            raspbian_setup
            ;;
        lakka)
            lakka_setup
            ;;
        raspbian)
            raspbian_setup
            ;;
        retropie)
            raspbian_setup
            ;;
        ubuntu)
            raspbian_setup
            ;;
        *)
            echo "Operating System Detection: Unknown or Unsupported"
            unknown_setup
            ;;
    esac
}

detect_architecture
detect_os_and_setup_services

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
    # Check for PSPi-Controller.cfg and rename if it exists
    if [ -f "/storage/joypads/udev/PSPi-Controller.cfg" ]; then
        mv "/storage/joypads/udev/PSPi-Controller.cfg" "/storage/joypads/udev/PSPi-Controller.old"
        echo "Renamed existing PSPi-Controller.cfg to PSPi-Controller.old"
    fi

    # Create new PSPi-Controller.cfg with specific contents
    cat << EOF > /storage/joypads/udev/PSPi-Controller.cfg
input_driver = "udev"
input_device = "PSPi-Controller"
input_vendor_id = "4660"
input_product_id = "22136"
input_b_btn = "3"
input_y_btn = "4"
input_select_btn = "1"
input_start_btn = "2"
input_up_btn = "10"
input_down_btn = "11"
input_left_btn = "9"
input_right_btn = "12"
input_a_btn = "6"
input_x_btn = "5"
input_l_btn = "8"
input_r_btn = "7"
input_l_x_plus_axis = "+0"
input_l_x_minus_axis = "-0"
input_l_y_plus_axis = "+1"
input_l_y_minus_axis = "-1"
input_gun_trigger_mbtn = "1"
EOF

    echo "New PSPi-Controller.cfg for Lakka created and configured."

    # Modify a line in retroarch.cfg
    sed -i '/input_quit_gamepad_combo/c\input_quit_gamepad_combo = "4"' /storage/.config/retroarch/retroarch.cfg
    echo "Modified input_quit_gamepad_combo in retroarch.cfg."

    # Prompt for reboot
    read -p "Configuration complete. Would you like to reboot now? (yes/no) " answer
    case $answer in
        [Yy]* ) reboot;;
        [Nn]* ) echo "Reboot skipped. Please reboot manually for changes to take effect.";;
        * ) echo "Invalid response. Please reboot manually for changes to take effect.";;
    esac
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

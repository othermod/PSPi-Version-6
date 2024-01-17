#!/bin/bash -e
################################################################################
##  File:  configure-apt.sh
##  Desc:  Configure apt, install jq and apt-fast packages.
################################################################################

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

lakka_setup() {
    echo "Lakka OS detected. Setting up autostart script..."

    echo "Copying overlays"
    cp -r /packer/temp/overlays/* /storage/overlays/

    if [ -f "/storage/.config/autostart.sh" ]; then
        mv "/storage/.config/autostart.sh" "/storage/.config/autostart.old"
        echo "Renamed existing autostart.sh to autostart.old"
    fi

    cat <<EOF >/storage/.config/autostart.sh
#!/bin/bash
/packer/temp/drivers/bin/./main$ARCH_SUFFIX &
sleep 1
/packer/temp/drivers/bin/./gamepad$ARCH_SUFFIX &
/packer/temp/drivers/bin/./osd$ARCH_SUFFIX &
EOF

    chmod +x /storage/.config/autostart.sh
    echo "New autostart.sh for Lakka created and configured."
    # Check for PSPi-Controller.cfg and rename if it exists
    if [ -f "/storage/joypads/udev/PSPi-Controller.cfg" ]; then
        mv "/storage/joypads/udev/PSPi-Controller.cfg" "/storage/joypads/udev/PSPi-Controller.old"
        echo "Renamed existing PSPi-Controller.cfg to PSPi-Controller.old"
    fi

    # Create new PSPi-Controller.cfg with specific contents
    cat <<EOF >/storage/joypads/udev/PSPi-Controller.cfg
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
}

batocera_setup() {
    echo "batocera"
}

raspbian_setup() {
    enable_i2c
    copy_config
    copy_binaries
    add_services
}

ubuntu_setup() {
    copy_binaries
    add_services
}

copy_config() {
    echo "Copying config.txt from /packer/temp/config/ to /boot/..."
    # Copy all files from the source directory to the target directory
    cp -r /packer/temp/config/* /boot/

    cat <<EOF >> /boot/config.txt
[board-type=0x14]
# This applies to CM4 only
include cm4.txt

[pi0]
include pi0.txt
EOF
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
        echo "dtparam=i2c_arm=$SETTING" >>$CONFIG
    fi

    # Handle the blacklist file for I2C
    if [ -e $BLACKLIST ]; then
        sed -i "s/^\(blacklist[[:space:]]*i2c[-_]bcm2708\)/#\1/" $BLACKLIST
    fi

    # Ensure i2c-dev is in /etc/modules
    if ! grep -q "^i2c[-_]dev" /etc/modules; then
        echo "i2c-dev" >>/etc/modules
    fi

    # Enable the I2C device
    modprobe i2c-dev
}

copy_binaries() {
    echo "Copying binaries from /packer/temp/drivers/bin/ to /usr/bin/..."
    # Copy all files from the source directory to the target directory
    cp -r /packer/temp/drivers/bin/* /usr/bin/
}

add_services() {
    echo "Installing and enabling services..."
    # Copy new service files
    cp /packer/temp/services/* /etc/systemd/system/
    systemctl daemon-reload

    # Always enable and start main and osd services
    for service in main osd; do
        systemctl enable ${service}${ARCH_SUFFIX}.service
    done

    # User choice for mouse and gamepad services
    for service in mouse gamepad; do
        systemctl enable ${service}${ARCH_SUFFIX}.service
    done

    echo "Services added."
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

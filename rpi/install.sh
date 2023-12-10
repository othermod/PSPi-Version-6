#!/bin/bash

setup_binaries() {
    echo "Removing old binaries from /usr/local/bin..."
    rm -f /usr/local/bin/{main,osd,mouse,gamepad}

    echo "Setting up new binaries..."
    chmod +x rpi/drivers/bin/{main,osd,mouse,gamepad}
    cp drivers/bin/{main,osd,mouse,gamepad} /usr/local/bin/
    echo "New binaries are set up and copied to /usr/local/bin."
}

lakka_setup() {
    setup_binaries
    # Lakka-specific commands here
}

batocera_setup() {
    setup_binaries
    # Batocera-specific commands here
}

raspbian_setup() {
    remove_services
    add_services
}

retropie_setup() {
    remove_services
    add_services
}

remove_services() {
    echo "Disabling and removing existing services..."
    # Stop and disable existing services
    for service in main osd mouse gamepad; do
        sudo systemctl stop $service.service 2>/dev/null || true
        sudo systemctl disable $service.service 2>/dev/null || true
    done
    echo "Existing services removed."
}

add_services() {
    echo "Installing and enabling services..."
    # Copy new service files
    sudo cp services/*.service /etc/systemd/system/
    sudo systemctl daemon-reload

    # Always enable and start main and osd services
    for service in main osd; do
        sudo systemctl enable $service.service
        sudo systemctl start $service.service
    done

    # User choice for mouse and gamepad services
    for service in mouse gamepad; do
        read -p "Enable and start the $service service? [y/N]: " enable_service
        if [ "$enable_service" = "y" ]; then
            sudo systemctl enable $service.service
            sudo systemctl start $service.service
        else
            echo "Skipping $service service"
        fi
    done

    echo "Services added and started."
}


unknown_setup() {
    echo "Unknown or unsupported OS. Manual service setup may be required."
}

detect_os_and_setup_services() {
    OS=$(grep '^ID=' /etc/os-release | cut -d= -f2 | tr -d '"')
    echo "Operating System Detected: $OS"
    case "$OS" in
        lakka)
            lakka_setup
            ;;
        batocera)
            batocera_setup
            ;;
        retropie)
            retropie_setup
            ;;
        raspbian)
            raspbian_setup
            ;;
        *)
            echo "Operating System Detection: Unknown or Unsupported"
            unknown_setup
            ;;
    esac
}

detect_os_and_setup_services

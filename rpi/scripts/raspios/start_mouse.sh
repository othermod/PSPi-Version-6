#!/bin/bash

. /boot/firmware/pspi.conf
modprobe i2c-dev

echo "enable_mouse: $enable_mouse"

# Function to detect the architecture of the operating system
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
detect_architecture

echo "Starting PSPi with parameters: $params"

if [ "$enable_mouse" = "true" ]; then
    /usr/bin/mouse$ARCH_SUFFIX
fi
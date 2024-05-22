#!/bin/bash

. /boot/pspi.conf

echo "disable_osd: $disable_osd"

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

if [ "$disable_osd" = "false" ]; then
    /usr/bin/osd$ARCH_SUFFIX
fi
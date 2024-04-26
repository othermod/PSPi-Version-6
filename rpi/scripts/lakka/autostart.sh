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

detect_architecture

/flash/drivers/main$ARCH_SUFFIX --dim &
sleep 1
/flash/drivers/osd$ARCH_SUFFIX &

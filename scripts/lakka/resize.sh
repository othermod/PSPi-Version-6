#!/bin/bash

# Function to safely execute parted commands with error handling
run_parted() {
    local cmd=$1
    local output
    output=$(printf 'Yes\nIgnore\n' | parted ---pretend-input-tty /dev/mmcblk0 $cmd 2>&1)
    local status=$?

    if [[ $status -ne 0 ]]; then
        echo "Error running parted command '$cmd': $output"
        exit $status
    fi
}

# Get the starting sector of the second partition
start_sector=$(parted /dev/mmcblk0 -ms unit s print | grep "^2:" | cut -d: -f2 | sed 's/s//')

# Check if the start sector was successfully obtained
if [ -z "$start_sector" ]; then
    echo "Error: Unable to determine the start sector of the partition."
    exit 1
fi

# Remove the second partition
run_parted "rm 2"

# Recreate the partition with the correct start sector
run_parted "unit s mkpart primary ${start_sector} 100%"

# Resize the filesystem
resize2fs /dev/mmcblk0p2

# Remove the script call from autostart.sh
sed -i '/\/resize\.sh/d' /storage/.config/autostart.sh

# Reboot the system
echo "Rebooting the system..."
reboot

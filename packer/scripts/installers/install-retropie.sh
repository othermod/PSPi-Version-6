#!/bin/bash -e
################################################################################
##  File:  install-pspi6.sh
##  Desc: This script is used to install Retropie onto a PiOS Aarch64 image. It contains the necessary installation steps and dependencies required for the installation process.
##  https://retropie.org.uk/docs/Manual-Installation/
##  https://www.youtube.com/watch?v=PAePvz6YSWo
################################################################################
set -x

# Generate a unique log file name using the current timestamp
LOG_FILE="/var/log/install-retropie-$(date +%Y%m%d%H%M%S).log"

# Redirect all output (stdout and stderr) to the log file
exec > >(tee -a "$LOG_FILE") 2>&1

# Add a file to track installation progress
PROGRESS_FILE="/opt/retropie_installation_progress"

# Function to check if a step is complete
is_step_complete() {
    grep -q "$1" "$PROGRESS_FILE" 2>/dev/null
}

# Function to mark a step as complete
mark_step_complete() {
    echo "$1" >> "$PROGRESS_FILE"
}

# Function to handle step failure
handle_failure() {
    echo "Step failed: $1. Rebooting..."
    sleep 60
    reboot
}

# Ensure the progress file exists
touch "$PROGRESS_FILE"
chmod 666 "$PROGRESS_FILE"

# Variable to track if any changes were made
CHANGES_MADE=false

# Update and upgrade system
if ! is_step_complete "update_upgrade"; then
    apt update || handle_failure "update"
    apt upgrade -y || handle_failure "upgrade"
    mark_step_complete "update_upgrade"
    CHANGES_MADE=true
fi

# Install dependencies
if ! is_step_complete "install_dependencies"; then
    apt install git lsb-release -y || handle_failure "install_dependencies"
    mark_step_complete "install_dependencies"
    CHANGES_MADE=true
fi

# Install RetroPie
if ! is_step_complete "clone_retropie"; then
    cd /opt || handle_failure "change_directory"
    if [ ! -d "/opt/RetroPie-Setup" ]; then
        git clone --depth=1 https://github.com/RetroPie/RetroPie-Setup.git || handle_failure "clone_retropie"
    fi
    mark_step_complete "clone_retropie"
    CHANGES_MADE=true
fi

if ! is_step_complete "setup_retropie"; then
    cd /opt/RetroPie-Setup || handle_failure "change_directory_retropie"
    chmod +x /opt/RetroPie-Setup/retropie_packages.sh || handle_failure "chmod_retropie_packages"

    # Break down each retropie_packages.sh command into its own step
    if ! is_step_complete "install_retroarch"; then
        /opt/RetroPie-Setup/retropie_packages.sh retroarch || handle_failure "install_retroarch"
        mark_step_complete "install_retroarch"
        CHANGES_MADE=true
    fi

    if ! is_step_complete "install_emulationstation"; then
        /opt/RetroPie-Setup/retropie_packages.sh emulationstation || handle_failure "install_emulationstation"
        mark_step_complete "install_emulationstation"
        CHANGES_MADE=true
    fi

    if ! is_step_complete "install_retropiemenu"; then
        /opt/RetroPie-Setup/retropie_packages.sh retropiemenu || handle_failure "install_retropiemenu"
        mark_step_complete "install_retropiemenu"
        CHANGES_MADE=true
    fi

    if ! is_step_complete "install_runcommand"; then
        /opt/RetroPie-Setup/retropie_packages.sh runcommand || handle_failure "install_runcommand"
        mark_step_complete "install_runcommand"
        CHANGES_MADE=true
    fi

    if ! is_step_complete "install_samba_depends"; then
        /opt/RetroPie-Setup/retropie_packages.sh samba depends || handle_failure "install_samba_depends"
        mark_step_complete "install_samba_depends"
        CHANGES_MADE=true
    fi

    if ! is_step_complete "install_samba_shares"; then
        /opt/RetroPie-Setup/retropie_packages.sh samba install_shares || handle_failure "install_samba_shares"
        mark_step_complete "install_samba_shares"
        CHANGES_MADE=true
    fi

    if ! is_step_complete "install_splashscreen_default"; then
        /opt/RetroPie-Setup/retropie_packages.sh splashscreen default || handle_failure "install_splashscreen_default"
        mark_step_complete "install_splashscreen_default"
        CHANGES_MADE=true
    fi

    if ! is_step_complete "enable_splashscreen"; then
        /opt/RetroPie-Setup/retropie_packages.sh splashscreen enable || handle_failure "enable_splashscreen"
        mark_step_complete "enable_splashscreen"
        CHANGES_MADE=true
    fi

    if ! is_step_complete "install_bashwelcometweak"; then
        /opt/RetroPie-Setup/retropie_packages.sh bashwelcometweak || handle_failure "install_bashwelcometweak"
        mark_step_complete "install_bashwelcometweak"
        CHANGES_MADE=true
    fi

    # Enable autostart for EmulationStation
    if ! is_step_complete "enable_autostart"; then
        /opt/RetroPie-Setup/retropie_packages.sh autostart enable || handle_failure "enable_autostart"

        # Update the autostart.sh script to wait for all processes running /usr/local/bin/install-retropie.sh to end
        sed -i '3i\    sleep 3\n    while pgrep -f "/usr/local/bin/install-retropie.sh" > /dev/null; do\n      sleep 5\n    done' /etc/profile.d/10-retropie.sh

        mark_step_complete "enable_autostart"
        reboot
    fi

    mark_step_complete "setup_retropie"
    CHANGES_MADE=true
fi

# Install RetroPie cores
# Load cores from configuration file
CORES=$(grep -oP '^\s*"[^"]+"(?=\s*#|$)' /boot/firmware/retropie.conf | tr -d '"')

for CORE in $CORES; do
    if ! is_step_complete "install_$CORE"; then
        /opt/RetroPie-Setup/retropie_packages.sh "$CORE" || handle_failure "install_$CORE"
        mark_step_complete "install_$CORE"
        CHANGES_MADE=true
    fi
done

# Reboot only if changes were made
if [ "$CHANGES_MADE" = true ]; then
    reboot
fi
# Installation Instructions

## General Setup (Applies to All Operating Systems)

Before beginning the setup process, ensure you have flashed your desired operating system onto the SD card. Once the operating system is flashed, the SD card will appear as a folder on your computer. Follow these steps to prepare your SD card:

1. Insert the flashed SD card into your computer.
2. Open the SD card folder that appears on your computer.
3. Copy the `drivers` and `overlays` folders to the root directory of the SD card. There should already be an 'overlays' folder, and you should allow them to merge.
4. Copy the `install.sh` script to the root directory of the SD card.
5. Safely eject the SD card from your computer and insert it into your device.

## Configuring the `config.txt` File - add separate instruction for each os and things to consider

*Instructions for configuring the `config.txt` file to ensure proper booting and video output.*

- Placeholder of explanation of necessary configuration changes...
- Placeholder of step-by-step guide on what to add or modify in the `config.txt` file...
- ...

## Retropie

To set up on Retropie, follow these instructions:

1. Boot up your device with the Retropie SD card.
2. When Retropie starts, press F4 to enter the command prompt.
3. Connect a keyboard to the device.
4. Run the command `sudo bash /boot/install.sh` to set the drivers to load at bootup.

## Raspberry Pi OS

To set up on Raspberry Pi OS, follow these instructions:

1. Boot up your device with the Raspberry Pi OS SD card.
2. Once started, open the Terminal application.
3. Connect a keyboard to the device.
4. Run the command `sudo bash /boot/install.sh` to set the drivers to load at bootup.

## Lakka

To set up on Lakka, follow these instructions:

1. Boot up your device with the Lakka SD card. Allow Lakka to resize the partition on its first boot.
2. Connect a keyboard to the device.
3. Connect to your Wi-Fi network through the keyboard.
4. Enable SSH in Lakka's settings.
5. Using an SSH client on your computer, SSH into the device using `root` as both the username and password.
6. Run the command `bash /boot/install.sh`. This will set the drivers to load at bootup.

## Batocera

*Instructions for setting up on Batocera.*

- Step 1: ...
- Step 2: ...
- ...

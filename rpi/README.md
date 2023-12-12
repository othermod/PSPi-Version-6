# Installation Instructions

***

## Copy Necessary Files (Applies to All Operating Systems)

Before beginning the setup process, ensure you have flashed your desired operating system onto the SD card. Once the operating system is flashed, the SD card will appear as a folder on your computer. Follow these steps to prepare your SD card:

1. Insert the flashed SD card into your computer.
2. Open the SD card folder that appears on your computer.
3. Copy the `drivers`, `overlays`, and `services` folders to the root directory of the SD card. There should already be an 'overlays' folder, and you should allow them to merge.
4. Copy the `install.sh` script to the root directory of the SD card.

## Setting up the `config.txt` File

This section provides instructions on how to configure the `config.txt` file to get an image on the LCD.

### General Configuration for All Raspberry Pi Models and Operating Systems

**Perform the following checks:**
- Look for any entry in the `config.txt` that includes `dtoverlay=vc4-kms-v3d`, and replace it with `dtoverlay=vc4-fkms-v3d`
- Look for any entry that includes `dtoverlay=dwc2`, and replace it with `dtoverlay=dwc2,dr_mode=host`
- Look for any entry that includes `camera_auto_detect=1` or `display_auto_detect=1` and comment them out (by adding a `#` before them)
- Look for any entry that includes `max_framebuffers=2`, and replace it with `max_framebuffers=1`

Not every check is required, but some combinations of entries will make the video output only to HDMI instead of the LCD.

**Next. add these General Configuration lines to the bottom of your `config.txt` file:**

```
# Don't show splash screen
disable_splash=1

# Enable I2C
dtparam=i2c_arm=on

# Enable audio (loads snd_bcm2835)
dtparam=audio=on

# Reduce I2C speed to avoid clock bug in Raspberry Pi I2C
dtparam=i2c_baudrate=25000

# Disable HDMI audio
hdmi_ignore_edid_audio=1

# Configure DPI signal
framebuffer_width=800
framebuffer_height=480
enable_dpi_lcd=1
display_default_lcd=1
dpi_group=2
dpi_mode=87
dpi_output_format=503863

over_voltage=-2
```
Next, you should add the additional configuration lines for the Raspberry Pi you are using.

### Additional Configuration for Raspberry Pi Compute Module 4 (CM4)

**For systems running on a Raspberry Pi Compute Module 4 (CM4), include these additional lines just below the General Configuration lines:**

```
# Enable DRM VC4 V3D driver
dtoverlay=vc4-fkms-v3d
max_framebuffers=1

# Set GPIO pins for 24-Bit DPI Mode 7
gpio=0=a2,np
gpio=1=a2,np
gpio=2=a0,np
gpio=3=a0,np
gpio=4-27=a2,np

dpi_timings=800 0 8 4 8 480 0 8 4 8 0 0 0 60 0 25000000 6

# Enable USB
dtoverlay=dwc2,dr_mode=host

# Disable WiFi and Bluetooth (Optional)
#dtoverlay=pi3-disable-wifi
#dtoverlay=pi3-disable-bt

# Disables PCI-E link to prevent warning at boot
dtoverlay=disable-pcie

# Enable external PSP antenna
dtparam=ant2

# Set up CM4 audio pin
dtoverlay=audiocm4

arm_freq_min=300
core_freq_min=200
```

### Configuration for 40-pin Raspberry Pi Boards (Pi Zero, Zero 2, Pi 3, and Pi 4)

**For Raspberry Pi Zero, Zero 2, and other Pi boards with the 40-pin header, include these additional lines just below the General Configuration lines:**

```
gpu_mem_256=128
gpu_mem_512=256
gpu_mem_1024=256

# Set GPIO pins for 21-Bit DPI
gpio=0=a2,np
gpio=1=a2,np
gpio=2=a0,np
gpio=3=a0,np
gpio=5-11=a2,np
gpio=13-19=a2,np
gpio=21-27=a2,np

dpi_timings=800 0 8 4 8 480 0 8 4 8 0 0 0 60 0 32000000 6

# Zero-specific settings
dtparam=act_led_gpio=20
dtoverlay=audiozero
dtoverlay=gpio-poweroff,gpiopin=4,active_low=yes
dtparam=act_led_activelow=no

arm_freq_min=500
core_freq_min=200
```
***
## Driver Installation

### Retropie

To set up on Retropie, follow these instructions:

1. Boot up your device with the Retropie SD card.
2. When Retropie starts, press F4 to enter the command prompt.
3. Connect a keyboard to the device.
4. Run the command `sudo bash /boot/install.sh` to set the drivers to load at bootup.

### Raspberry Pi OS

To set up on Raspberry Pi OS, follow these instructions:

1. Boot up your device with the Raspberry Pi OS SD card.
2. Once started, open the Terminal application.
3. Connect a keyboard to the device.
4. Run the command `sudo bash /boot/install.sh` to set the drivers to load at bootup.

### Lakka

To set up on Lakka, follow these instructions:

1. Boot up your device with the Lakka SD card. Allow Lakka to resize the partition on its first boot.
2. Connect a keyboard to the device.
3. Connect to your Wi-Fi network through the keyboard.
4. Enable SSH in Lakka's settings.
5. Using an SSH client on your computer, SSH into the device using `root` as both the username and password.
6. Run the command `bash /boot/install.sh`. This will set the drivers to load at bootup.

### Batocera

*Instructions for setting up on Batocera.*

- Step 1: ...
- Step 2: ...
- ...

# PSPi Version 6
![PSPi Zero](https://othermod.com/wp-content/uploads/IMG_8727.jpg)

### Option 1 - Installation Instructions Using Image

Download the ready-to-use image from [Google Drive](https) or [Torrent](https)

Extract the image and use imaging software (such as Win32DiskImager, Etcher, or Raspberry Pi Imager) to image your SD card

### Option 2 - Manual Offline Installation Instructions

Download repository, extract and copy the PSPi folder and config.txt file to the BOOT partition of a fresh RetroPie microSD (v4.7.1 currently). You must overwrite the original config.txt file from the RetroPie image.

Next, copy the appropriate lcd.txt file (from the 480x272 or 800x480 folder depending on which LCD you are using) to the BOOT partition. This goes into the same BOOT folder as the config.txt file

Boot the PSPi with the SD card inserted, with a USB keyboard attached.

After Emulation Station loads, press F4 on the keyboard to exit to the command line.

Type the following command to install everything:
```
sudo bash /boot/PSPi/setup.sh
```
The system will reboot after installation completes.

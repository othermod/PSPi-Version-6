# PSPi Version 6 ATmega8A Firmware Guide

This guide provides step-by-step instructions for flashing the necessary firmware and fuses to the ATmega8A microcontroller on the PSPi 6 board, using either a Raspberry Pi or an Arduino.

**Note:** If you order a board from othermod.com, you don't have to flash firmware. I flash the firmware on every board before shipping. This is only required if you are manufacturing your own board or are updating the firmware.

## Table of Contents
1. [Connection](#connection)
2. [Firmware and Fuses](#firmware-and-fuses)
3. [Flashing with Raspberry Pi](#flashing-with-raspberry-pi)
   - [Wiring](#wiring)
   - [Configuring avrdude](#configuring-avrdude)
   - [Flashing](#flashing)


## Connection

Before flashing the firmware, you need to wire a connection with the ATmega8A chip on your PSPi board. You can either solder wires directly to the board or use a pogo pin rig for a non-permanent connection.

**Note:** The image shows 6 connection points, including a dedicated ground point. However, this ground point was only added in PCB version 1.2. If you have an earlier board version, you'll need to use one of the ground pins on the 40-pin header instead of the dedicated ground point shown in the diagram.

![SPI Attachment Points](/atmega/images/spi.jpg)

Regardless of your chosen method, you'll need to connect to these points on the PSPi board (colors will stay consistent throughout the guide):
- 🔴 VCC
- ⚫ GND (use a ground pin on the 40-pin header if you have a PCB version earlier than 1.2)
- 🟡 Clock
- 🟢 Reset
- 🔵 MOSI
- 🟠 MISO

## Firmware and Fuses

You can flash firmware using either a Raspberry Pi or an Arduino. Each method is described below.

## Flashing with Raspberry Pi

### Wiring

Before you begin the flashing process, you need to connect the PSPi board to your Raspberry Pi. Here's how to make the connections:

![Raspberry Pi GPIO Pinout](/atmega/images/pi.jpg)

- 🔴 Connect VCC to Raspberry Pi 3.3V (Pin 1 or 17)
- ⚫ Connect GND to any Raspberry Pi GND pin (e.g., Pin 6)
- 🟡 Connect Clock to Raspberry Pi GPIO3 (Pin 5)
- 🟢 Connect Reset to Raspberry Pi GPIO2 (Pin 3)
- 🔵 Connect MOSI to Raspberry Pi GPIO5 (Pin 29)
- 🟠 Connect MISO to Raspberry Pi GPIO6 (Pin 31)

Ensure all connections are secure and not bridged before proceeding with the flashing process.

### Configuring avrdude

1. Install avrdude if you haven't already:
   ```
   sudo apt-get update
   sudo apt-get install avrdude
   ```

2. Edit the avrdude configuration file:
   ```
   sudo nano /etc/avrdude.conf
   ```

3. Find the `linuxgpio` entry (use Ctrl+W to search) and modify it to:
   ```
   programmer
     id    = "linuxgpio";
     desc  = "Use the Linux sysfs interface to bitbang GPIO lines";
     type  = "linuxgpio";
     reset = 2;
     sck   = 3;
     mosi  = 5;
     miso  = 6;
   ;
   ```
   The entry may be commented out by default, so remove the # from the beginning of each line.

### Flashing
1. Copy the [firmware file](https://github.com/othermod/PSPi-Version-6/tree/main/atmega/atmega.ino.arduino_standard.hex) to your Raspberry Pi.

2. Flash the fuses:
   ```
   sudo avrdude -p m8 -c linuxgpio -U lfuse:w:0xE4:m -U hfuse:w:0xDC:m
   ```

3. Flash the firmware:
   ```
   sudo avrdude -p m8 -c linuxgpio -e -U flash:w:atmega.ino.arduino_standard.hex
   ```

After successful flashing, disconnect the wires from your Raspberry Pi. The PSPi board is ready to use.


## Future Updates

I use a custom pogo pin jig for flashing firmware on boards I sell, and I'll post the PCB files shortly. Stay tuned for updates!

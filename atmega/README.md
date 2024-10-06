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
4. [Flashing with Arduino](#flashing-with-arduino)
   - [Connecting to the Arduino](#connecting-to-the-arduino)
   - [Modifying boards.txt configuration](#modifying-boardstxt-configuration)
   - [Setting Up Arduino as ISP](#setting-up-arduino-as-isp)
   - [Flashing](#flashing-1)
5. [Creating Custom Firmware](#creating-custom-firmware)
6. [Troubleshooting](#troubleshooting)
7. [Future Updates](#future-updates)

## Connection

Before flashing the firmware, you need to wire a connection with the ATmega8A chip on your PSPi board. You can either solder wires directly to the board or use a pogo pin rig for a non-permanent connection.

**Note:** The image shows 6 connection points, including a dedicated ground point. However, this ground point was only added in PCB version 1.2. If you have an earlier board version, you'll need to use one of the ground pins on the 40-pin header instead of the dedicated ground point shown in the diagram.

![SPI Attachment Points](/atmega/images/spi.jpg)

Regardless of your chosen method, you'll need to connect to these points on the PSPi board (colors will stay consistent throughout the guide):
- 🔴 VCC
- ⚫ GND (use a ground pin on the 40-pin header if you have a PCB version earlier than 1.2)
- 🟢 Clock
- 🟠 MISO
- 🔵 MOSI
- 🟡 Reset

## Firmware and Fuses

You can flash firmware using either a Raspberry Pi or an Arduino. Each method is described below.

## Flashing with Raspberry Pi

### Wiring

Before you begin the flashing process, you need to connect the PSPi board to your Raspberry Pi. Here's how to make the connections:

![Raspberry Pi GPIO Pinout](/atmega/images/pi.jpg)

- 🔴 Connect VCC to Raspberry Pi 3.3V (Pin 1 or 17)
- ⚫ Connect GND to any Raspberry Pi GND pin (e.g., Pin 6)
- 🟢 Connect Clock to Raspberry Pi GPIO3
- 🟠 Connect MISO to Raspberry Pi GPIO6
- 🔵 Connect MOSI to Raspberry Pi GPIO5
- 🟡 Connect Reset to Raspberry Pi GPIO2

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

## Flashing with Arduino

The process for flashing with Arduino is similar to the Raspberry Pi method, but with a few key differences. Most importantly, we'll be using a level shifter to protect the PSPi board from voltage damage.

### Connecting to the Arduino

Before beginning the flashing process, you need to connect the PSPi board to your Arduino using a level shifter. This is crucial to protect the voltage regulator on the PSPi board from damage, as the ATmega operates at 5V but the PSPi board requires 3.0-3.3V.

![Arduino to PSPi Connections](/atmega/images/arduino.jpg)

![Level Shifter Connections](/atmega/images/level-shifter.jpg)

Here's how to make the connections:

1. Arduino to Level Shifter connections:
   - 🔴 Connect Arduino 5V to the level shifter's HV (high voltage) side
   - 🟣 Connect Arduino 3.3V to the level shifter's LV (low voltage) side
   - ⚫ Connect Arduino GND to both GND pins on the level shifter
   - 🟢 Connect Arduino Pin 13 (Clock) to the level shifter's HV4
   - 🟠 Connect Arduino Pin 12 (MISO) to the level shifter's HV3
   - 🔵 Connect Arduino Pin 11 (MOSI) to the level shifter's HV2
   - 🟡 Connect Arduino Pin 10 (Reset) to the level shifter's HV1


2. Level Shifter to PSPi connections:
   - 🔴 Connect the level shifter's LV to PSPi VCC
   - ⚫ Connect the level shifter's GND to PSPi GND
   - 🟢 Connect the level shifter's LV4 to PSPi Clock
   - 🟠 Connect the level shifter's LV3 to PSPi MISO
   - 🔵 Connect the level shifter's LV2 to PSPi MOSI
   - 🟡 Connect the level shifter's LV1 to PSPi Reset


### Modifying boards.txt configuration

Before flashing the firmware using Arduino, you need to modify the boards.txt file to add support for the ATmega8A:

1. Locate your Arduino IDE installation directory.
2. Navigate to the `C:\Program Files (x86)\Arduino\hardware\arduino\avr` directory.
3. Open the `boards.txt` file in a text editor.
4. Add the following lines at the end of the file:

```
atmega8a_nb.name=ATmega8A (8MHz Internal, No bootloader)
atmega8a_nb.upload.tool=avrdude
atmega8a_nb.upload.protocol=arduino
atmega8a_nb.upload.maximum_size=8192
atmega8a_nb.upload.maximum_data_size=1024
atmega8a_nb.bootloader.tool=avrdude
atmega8a_nb.bootloader.low_fuses=0xE4
atmega8a_nb.bootloader.high_fuses=0xDC
atmega8a_nb.bootloader.unlock_bits=0x3F
atmega8a_nb.bootloader.lock_bits=0x0F
atmega8a_nb.bootloader.file=empty.hex
atmega8a_nb.build.mcu=atmega8a
atmega8a_nb.build.f_cpu=8000000L
atmega8a_nb.build.core=arduino:arduino
atmega8a_nb.build.variant=arduino:standard
atmega8a_nb.build.board=atmega8a
atmega8a_nb.recipe.size.regex=^(?:\.text|\.data|\.bootloader)\s+([0-9]+).*
atmega8a_nb.recipe.size.regex.data=^(?:\.data|\.bss)\s+([0-9]+).*
atmega8a_nb.recipe.size.regex.eeprom=^\.eeprom\s+([0-9]+).*
```

5. Save the file and restart the Arduino IDE.

### Setting Up Arduino as ISP

This configures the Arduino as a connection point between the PC and the microcontroller on the PSPi.

1. In Arduino IDE, go to File > Examples > 11.ArduinoISP > ArduinoISP.
2. Select Tools > Board > Arduino Uno.
3. Select Tools > Programmer > AVRISP MKII.
4. Upload the sketch to your Arduino.

### Flashing

1. Select Tools > Board > ATmega8A (8MHz Internal, No bootloader).
2. Select Tools > Programmer > Arduino as ISP.
3. To flash the fuses:
   - Go to Tools > Burn Bootloader.
4. To flash the firmware:
   - Go to Sketch > Upload Using Programmer.

**Note:** You will see an error regarding a missing empty.hex file when flashing the fuses. It doesn't affect the process, but if you want to eliminate the error, copy [empty.hex](https://github.com/othermod/PSPi-Version-6/tree/main/atmega/empty.hex) to `C:\Program Files (x86)\Arduino\hardware\arduino\avr\bootloaders`.

After successful flashing, disconnect all wires from the Arduino and level shifter. The PSPi board is now ready to use.

## Creating Custom Firmware

If you want to create your own custom firmware for the ATmega8A, you'll need to follow the same steps for modifying the boards.txt file as described in the [Modifying boards.txt configuration](#modifying-boardstxt-configuration) section above. After configuring the Arduino IDE, you can develop your custom firmware, compile it, and then flash it to the ATmega8A using the same steps outlined in the [Flashing with Arduino](#flashing-with-arduino) section.

## Troubleshooting

- If you encounter errors during flashing, double-check all connections.
- For the pogo pin setup, ensure all pins are making good contact with the board.
- If using direct soldering, verify that there are no solder bridges or cold joints.
- Ensure you're using the correct GPIO numbers (for Raspberry Pi) or pin numbers (for Arduino).
- Verify that the ATmega8A firmware file is in the correct location.

## Future Updates

I use a custom pogo pin jig for flashing firmware on boards I sell, and I'll post the PCB files shortly. Stay tuned for updates!

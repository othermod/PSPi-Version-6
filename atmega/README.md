Of course, I'll integrate that section back into the README for clarity.

---

# ATmega8 Setup for PSPi Version 6

This repository contains the necessary files and instructions for setting up the ATmega8 microcontroller on your PSPi Version 6 board. Please follow the steps below to get it up and running.

## Pre-requisites

- A PSPi Version 6 board.
- Raspberry Pi (with Raspbian OS installed).
- Soldering iron, solder, and jumper wires.
- avrdude installed on your Raspberry Pi.

## Setup Instructions

### 1. Soldering Wires to the PSPi Board

Before you can flash the ATmega8, you'll need to solder wires to the specified connections on your PSPi Version 6 board.

**Instructions:**

![SPI Attachment Points](/atmega/images/spi.jpg)

- Power off your Raspberry Pi and PSPi board.
- Using your soldering iron, carefully solder jumper wires to the PSPi board's SPI attachment points:
  - Solder a wire from the Raspberry Pi's 3.3V (Pin 1) to the PSPi's 3.3V.
  - Solder a wire from the Raspberry Pi's GND (Pin 6, 9, 14, 20, or 25) to the PSPi's GND.
  - Solder a wire from a free Raspberry Pi GPIO to the PSPi's MOSI.
  - Solder a wire from another free Raspberry Pi GPIO to the PSPi's MISO.
  - Solder a wire from another free Raspberry Pi GPIO to the PSPi's Clock.
  - Solder a wire from another free Raspberry Pi GPIO to the PSPi's Reset.

Please note the GPIO pin numbers you use as you will need them in the next steps.

### 2. Configure avrdude

Before flashing the ATmega8, you need to ensure avrdude is configured to use the GPIO pins.

- Edit the AVRDUDE configuration file:
  ```bash
  sudo nano /etc/avrdude.conf
  ```
- Search for the `linuxgpio` entry in the configuration. (Press `CTRL + W` and type "linuxgpio").
- Uncomment and modify the `linuxgpio` entry to reflect your GPIO pin connections:

  ```
  programmer
     id    = "linuxgpio";
     desc  = "Use the Linux sysfs interface to bitbang GPIO lines";
     type  = "linuxgpio";
     reset = ?;  # Replace ? with the GPIO number connected to the pspi's Reset.
     sck   = ?;  # Replace ? with the GPIO number connected to the pspi's Clock.
     mosi  = ?;  # Replace ? with the GPIO number connected to the pspi's MOSI.
     miso  = ?;  # Replace ? with the GPIO number connected to the pspi's MISO.
  ;
  ```

### 3. Flashing Fuses

With the wires soldered, the next step is to flash the fuses to the ATmega8 microcontroller. Execute the following command:

```bash
sudo avrdude -p m8 -c linuxgpio -U lfuse:w:0xE4:m -U hfuse:w:0xDC:m
```

### 4. Flashing Firmware

Now, it's time to flash the firmware to the ATmega8. Execute the command below:

```bash
sudo avrdude -p m8 -c linuxgpio -e -U flash:w:atmega.ino.arduino_standard.hex
```

This command will flash the provided firmware file `atmega.ino.arduino_standard.hex` to the ATmega8 microcontroller.

Your PSPi Version 6 board should now be set up and ready to use with the ATmega8 microcontroller. If you encounter any issues or need further assistance, please raise an issue in this repository.

## Upcoming Interface

Stay tuned for an upcoming interface that will eliminate the need for soldering wires to the PSPi board. This new interface will simplify the setup process, making it easier and quicker to get your PSPi Version 6 board up and running with the ATmega8 microcontroller.

---

I've added the configuration section back into the README for a clearer guide.

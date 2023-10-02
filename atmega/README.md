
# ATmega8 Setup for PSPi Version 6

This repository contains the necessary files and instructions for setting up the ATmega8 microcontroller on your PSPi Version 6 board. Please follow the steps below to get it up and running.

## Pre-requisites
- A PSPi Version 6 board.
- Soldering iron and wires.
- avrdude installed on your system and properly configured (will post instructions when I'm able).

## Setup Instructions

### 1. Soldering Wires to the PSPi Board

Before you can flash the ATmega8, you'll need to solder wires to the specified connections on your PSPi Version 6 board. Although an interface is in development and will be available soon to eliminate the need for soldering, for now, this step is essential.

### 2. Flashing Fuses

With the wires soldered, the next step is to flash the fuses to the ATmega8 microcontroller. Open a terminal on your machine where avrdude is installed, and execute the following command:

```bash
sudo avrdude -p m8 -c linuxgpio -U lfuse:w:0xE4:m -U hfuse:w:0xDC:m
```

### 3. Flashing Firmware

Now, it's time to flash the firmware to the ATmega8. Execute the command below in the terminal:

```bash
sudo avrdude -p m8 -c linuxgpio -e -U flash:w:atmega.ino.arduino_standard.hex
```

This command will flash the provided firmware file `atmega.ino.arduino_standard.hex` to the ATmega8 microcontroller.

Now, your PSPi Version 6 board should be set up and ready to use with the ATmega8 microcontroller. If you encounter any issues or need further assistance, feel free to raise an issue in this repository.

## Upcoming Interface

Stay tuned for an upcoming interface that will eliminate the need for soldering wires to the PSPi board. This new interface will simplify the setup process significantly, making it easier and quicker to get your PSPi Version 6 board up and running with the ATmega8 microcontroller.

# ATmega8

Builds and flashes the bootloader and firmware for the ATmega8 microcontroller. For firmware flashing instructions, wiring diagrams, and the easy update method, see the [project wiki](https://github.com/othermod/PSPi-Version-6/wiki).

## Prerequisites

### AVR toolchain

```bash
sudo apt install gcc-avr binutils-avr avr-libc
```

### Arduino AVR core

```bash
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
arduino-cli core install arduino:avr
```

### avrdude (for flashing only)

```bash
sudo apt install avrdude
```

## Building

```bash
make
```

Builds the bootloader and firmware, then merges them into `combined.hex`. Individual targets are also available:

```bash
make bootloader   # build bootloader only
make firmware     # build firmware only
make combine      # merge existing build outputs into combined.hex
```

## Flashing

```bash
sudo make flash
```

Programs the fuses and flashes `combined.hex` via the `linuxgpio` programmer. Must be run as root.

## Cleaning

```bash
make clean
```

Cleans both subdirectories and removes `combined.hex`.

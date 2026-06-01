# Firmware

Firmware for the ATmega8 microcontroller, built against the Arduino AVR core.

## Prerequisites

Two things need to be installed before you can build.

### 1. AVR toolchain

```bash
sudo apt install gcc-avr binutils-avr avr-libc
```

### 2. Arduino AVR core

The build pulls Arduino core source files from `~/.arduino15`. Install `arduino-cli` and then the core:

```bash
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
arduino-cli core install arduino:avr
```

## Building

```bash
make
```

This produces `firmware.hex`. Intermediate build artifacts are written to `build/`.

## Cleaning

```bash
make clean
```

Removes the `build/` directory and `firmware.hex`.

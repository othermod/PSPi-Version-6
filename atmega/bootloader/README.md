# Bootloader

Bootloader for the ATmega8 microcontroller. Sits at `0x1C00` (the top 1KB of flash) and handles firmware loading and checksum verification on startup.

## Prerequisites

The AVR toolchain is the only requirement:

```bash
sudo apt install gcc-avr binutils-avr avr-libc
```

## Building

```bash
make
```

This produces `bootloader.hex` in the current directory.

## Cleaning

```bash
make clean
```

Removes `bootloader.elf` and `bootloader.hex`.

# Bootloader

Compiles the ATmega8 bootloader firmware.

## Build

```
make
```

Outputs `bin/bootloader.hex`.

## Flashing

### Firmware

```
sudo apt install avrdude
sudo avrdude -c linuxgpio -p m8 -U flash:w:bin/bootloader.hex:i
```

### Fuses

```
sudo avrdude -c linuxgpio -p m8 -U lfuse:w:0xE4:m -U hfuse:w:0xDA:m
```

The `linuxgpio` programmer connects directly to the ATmega8 via Raspberry Pi GPIO pins. Use `sudo avrdude -c linuxgpio -p m8 -n` to read back fuses and verify they were programmed correctly.

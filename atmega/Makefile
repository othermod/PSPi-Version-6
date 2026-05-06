AVRDUDE   = sudo avrdude
DUDEFLAGS = -c linuxgpio -p m8

FIRMWARE  = firmware/firmware.hex

.PHONY: all flash build clean

all: build

build:
	$(MAKE) -C bootloader
	$(MAKE) -C firmware

flash:
	$(MAKE) -C bootloader flash
	$(MAKE) -C firmware flash

clean:
	$(MAKE) -C bootloader clean
	$(MAKE) -C firmware clean

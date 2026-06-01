.PHONY: all bootloader firmware combine clean flash

all: combine

bootloader:
	$(MAKE) -C bootloader

firmware:
	$(MAKE) -C firmware

combine: bootloader firmware
	{ head -n -1 firmware/firmware.hex; cat bootloader/bootloader.hex; } > combined.hex

flash:
	@[ "$$(id -u)" -eq 0 ] || { echo "Flash requires root privileges. Re-run as root."; exit 1; }
	avrdude -c linuxgpio -p m8 -U lfuse:w:0xA4:m -U hfuse:w:0xDA:m -U flash:w:combined.hex:i

clean:
	$(MAKE) -C bootloader clean
	$(MAKE) -C firmware clean
	rm -f combined.hex

help:
	@echo "Targets: all, bootloader, firmware, combine, flash, clean, help"

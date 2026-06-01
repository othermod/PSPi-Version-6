.PHONY: all bootloader firmware combine clean flash

all: combine

bootloader:
	@echo "[BUILD] Bootloader"
	$(MAKE) -C bootloader

firmware:
	@echo "[BUILD] Firmware"
	$(MAKE) -C firmware

combine: bootloader firmware
	@echo "[COMBINE] Combining into combined.hex"
	{ head -n -1 firmware/firmware.hex; cat bootloader/bootloader.hex; } > combined.hex

flash: combine
	@echo "[FLASH] Flashing fuses and firmware..."
	avrdude -c linuxgpio -p m8 -U lfuse:w:0xA4:m -U hfuse:w:0xDA:m -U flash:w:combined.hex:i

clean:
	@echo "[CLEAN] Cleaning..."
	$(MAKE) -C bootloader clean
	$(MAKE) -C firmware clean
	rm -f combined.hex

help:
	@echo "Targets: all, bootloader, firmware, combine, flash, clean, help"

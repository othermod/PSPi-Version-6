TARGET     = bootloader
MCU        = atmega8
F_CPU      = 8000000UL
BOOT_START = 0x1C00
FLASH_END  = 0x2000

# Identity trailer in the last 4 bytes of flash: 3 marker bytes + version
# byte (see BOOTLOADER_MARKER_* in firmware/config.h). Written by the patch
# step below, so bootloader code must stay below 0x1FFC.
CODE_LIMIT = 1020

CC         = avr-gcc
OBJCOPY    = avr-objcopy
SIZE       = avr-size

CFLAGS     = -mmcu=$(MCU) -DF_CPU=$(F_CPU) -DBOOTLOADER_START=$(BOOT_START) \
             -Os -Wall -Wextra -ffreestanding -fno-inline-small-functions \
             -fpack-struct -fshort-enums -ffunction-sections -fdata-sections

LDFLAGS    = -mmcu=$(MCU) -nostartfiles -Wl,--section-start=.text=$(BOOT_START) \
             -Wl,--gc-sections -Wl,--relax

# Bootloader version byte, parsed from bootloader.c (decimal or 0xNN)
BL_VERSION = $(shell sed -n 's/^[[:space:]]*#define[[:space:]]\+BOOTLOADER_VERSION[[:space:]]\+\(0[xX][0-9A-Fa-f]\{1,2\}\|[0-9]\{1,3\}\).*/\1/p' bootloader.c)

# Marker bytes, parsed from the defines next to BOOTLOADER_VERSION in
# bootloader.c; the flasher (rpi/firmware/firmware.c) compares against its
# own copy of the same values
MK0 = $(shell sed -n 's/^[[:space:]]*#define[[:space:]]\+BOOTLOADER_MARKER_0[[:space:]]\+\(0[xX][0-9A-Fa-f]\{1,2\}\|[0-9]\{1,3\}\).*/\1/p' bootloader.c)
MK1 = $(shell sed -n 's/^[[:space:]]*#define[[:space:]]\+BOOTLOADER_MARKER_1[[:space:]]\+\(0[xX][0-9A-Fa-f]\{1,2\}\|[0-9]\{1,3\}\).*/\1/p' bootloader.c)
MK2 = $(shell sed -n 's/^[[:space:]]*#define[[:space:]]\+BOOTLOADER_MARKER_2[[:space:]]\+\(0[xX][0-9A-Fa-f]\{1,2\}\|[0-9]\{1,3\}\).*/\1/p' bootloader.c)

all: $(TARGET).hex

$(TARGET).elf: bootloader.c
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $<

$(TARGET).hex: $(TARGET).elf
	@if [ -z "$(BL_VERSION)" ]; then echo "ERROR: BOOTLOADER_VERSION missing in bootloader.c"; exit 1; fi
	@if [ -z "$(MK0)" ] || [ -z "$(MK1)" ] || [ -z "$(MK2)" ]; then echo "ERROR: BOOTLOADER_MARKER_* missing in bootloader.c"; exit 1; fi
	@BLV=$$(( $(BL_VERSION) )); \
	 M0=$$(( $(MK0) )); M1=$$(( $(MK1) )); M2=$$(( $(MK2) )); \
	 for v in $$BLV $$M0 $$M1 $$M2; do \
	     if [ "$$v" -lt 0 ] || [ "$$v" -gt 255 ]; then \
	         echo "ERROR: trailer byte out of range 0-255 ($$v)"; exit 1; fi; done; \
	 PROGSIZE=$$($(SIZE) $< | tail -1 | awk '{print $$1}'); \
	 if [ "$$PROGSIZE" -gt $(CODE_LIMIT) ]; then \
	     echo "ERROR: bootloader code $$PROGSIZE bytes exceeds $(CODE_LIMIT)-byte limit (trailer reserved at 0x1FFC-0x1FFF)"; \
	     exit 1; fi; \
	 DATASIZE=$$($(SIZE) $< | tail -1 | awk '{print $$2+$$3}'); \
	 $(OBJCOPY) -O binary -j .text --pad-to=$(FLASH_END) --gap-fill=0xFF $< $(TARGET).bin; \
	 awk 'BEGIN{printf "%c%c%c%c", '"$$M0"', '"$$M1"', '"$$M2"', '"$$BLV"'}' \
	     | dd of=$(TARGET).bin bs=1 seek=$(CODE_LIMIT) conv=notrunc status=none; \
	 $(OBJCOPY) -I binary -O ihex --change-addresses=$(BOOT_START) $(TARGET).bin $@; \
	 echo "Flash:   $$PROGSIZE bytes used of $(CODE_LIMIT) for bootloader [$$(( $(CODE_LIMIT) - $$PROGSIZE )) bytes free]"; \
	 echo "         (4 bytes reserved for identity trailer at 0x1FFC-0x1FFF)"; \
	 echo "Trailer: marker $$M0 $$M1 $$M2, version $$BLV written at 0x1FFC"; \
	 echo "RAM:     $$DATASIZE bytes used of 1024 [$$(( 1024 - $$DATASIZE )) bytes free]"

clean:
	rm -f $(TARGET).elf $(TARGET).hex $(TARGET).bin

.PHONY: all clean

TARGET   = firmware
MCU      = atmega8
F_CPU    = 8000000UL

# Firmware code limit: bootloader sits at 0x1C00 (7168), last 3 bytes are checksum
DATA_SIZE = 7165

# Color codes
GREEN  = \033[0;32m
RED    = \033[0;31m
NC     = \033[0m

# Verify Arduino AVR core is installed before doing anything
ARDUINO_AVR = $(lastword $(sort $(wildcard $(HOME)/.arduino15/packages/arduino/hardware/avr/*)))

ifeq ($(ARDUINO_AVR),)
ifneq ($(MAKECMDGOALS),clean)
$(info )
$(info Arduino AVR core not found. To compile this firmware you need:)
$(info   1. AVR toolchain:)
$(info      sudo apt install gcc-avr binutils-avr avr-libc)
$(info   2. Arduino AVR core source files:)
$(info      curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh)
$(info      arduino-cli core install arduino:avr)
$(info   3. Run make again)
$(info )
$(error Arduino AVR core not found)
endif
endif

CC      = avr-gcc
CXX     = avr-g++
OBJCOPY = avr-objcopy
AR      = avr-gcc-ar
SIZE    = avr-size

AVRDUDE   = sudo avrdude
DUDEFLAGS = -c linuxgpio -p m8

CORE_DIR    = $(ARDUINO_AVR)/cores/arduino
WIRE_DIR    = $(ARDUINO_AVR)/libraries/Wire/src
VARIANT_DIR = $(ARDUINO_AVR)/variants/standard
EEPROM_DIR  = $(ARDUINO_AVR)/libraries/EEPROM/src

INC = -I$(CORE_DIR) -I$(WIRE_DIR) -I$(WIRE_DIR)/utility -I$(VARIANT_DIR) -I$(EEPROM_DIR) -I.

CFLAGS   = -mmcu=$(MCU) -DF_CPU=$(F_CPU) -DARDUINO=10819 \
           -Os -Wall -flto -ffunction-sections -fdata-sections $(INC)
CXXFLAGS = $(CFLAGS) -fno-exceptions -fpermissive

LDFLAGS  = -mmcu=$(MCU) -Wl,--gc-sections -flto -fuse-linker-plugin -Wl,--defsym=__TEXT_REGION_LENGTH__=$(DATA_SIZE)

CORE_OBJS = $(CORE_DIR)/wiring.o \
            $(CORE_DIR)/wiring_analog.o \
            $(CORE_DIR)/wiring_digital.o \
            $(CORE_DIR)/hooks.o \
            $(CORE_DIR)/main.o

WIRE_OBJS = $(WIRE_DIR)/Wire.o \
            $(WIRE_DIR)/utility/twi.o

.PHONY: all clean flash

all: $(TARGET).hex

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c -o $@ $<

$(TARGET).o: firmware.ino config.h
	$(CXX) $(CXXFLAGS) -x c++ -c -o $@ $<

libcore.a: $(CORE_OBJS)
	$(AR) rcs $@ $^

$(TARGET).elf: $(TARGET).o libcore.a $(WIRE_OBJS)
	$(CXX) $(LDFLAGS) -o $@ $(TARGET).o $(WIRE_OBJS) -L. -lcore

$(TARGET).hex: $(TARGET).elf
	$(OBJCOPY) -O binary -R .eeprom --pad-to=$(DATA_SIZE) --gap-fill=0xFF $< $(TARGET).bin
	od -An -tu1 -v $(TARGET).bin \
	  | awk 'BEGIN{s1=0;s2=0;x=0} \
	         function xorb(a,b,  r,i){r=0;for(i=0;i<8;i++)r+=(int(a/2^i)%2!=int(b/2^i)%2)*2^i;return r} \
	         {for(i=1;i<=NF;i++){b=$$i+0;s1=(s1+b)%256;s2=(s2+s1)%256;x=xorb(x,b)}} \
	         END{printf "%c%c%c",s1,s2,x}' >> $(TARGET).bin
	$(OBJCOPY) -I binary -O ihex $(TARGET).bin $@
	@PROGSIZE=$$($(SIZE) $< | tail -1 | awk '{print $$1}'); \
	 DATASIZE=$$($(SIZE) $< | tail -1 | awk '{print $$2+$$3}'); \
	 DATA_FREE=$$((1024 - $$DATASIZE)); \
	 echo "Flash:   $$PROGSIZE bytes used of $(DATA_SIZE) available (3 bytes reserved for checksum at 0x1BFD-0x1BFF)"; \
	 echo "RAM:     $$DATASIZE bytes used of 1024 [$$DATA_FREE bytes free]"

flash: $(TARGET).hex
	@if $(AVRDUDE) $(DUDEFLAGS) -U flash:w:$<:i 2>&1; then \
			printf "$(GREEN)[OK] Firmware flashed successfully$(NC)\n"; \
	else \
			printf "$(RED)[FAIL] Firmware flashing failed$(NC)\n"; \
			exit 1; \
	fi

clean:
	rm -f $(TARGET).o libcore.a $(TARGET).elf $(TARGET).hex $(TARGET).bin
	rm -f $(CORE_DIR)/wiring.o $(CORE_DIR)/wiring_analog.o $(CORE_DIR)/wiring_digital.o $(CORE_DIR)/hooks.o $(CORE_DIR)/main.o
	rm -f $(WIRE_DIR)/Wire.o $(WIRE_DIR)/utility/twi.o

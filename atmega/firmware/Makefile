TARGET   = firmware
MCU      = atmega8
F_CPU    = 8000000UL

# Firmware code limit: bootloader sits at 0x1C00 (7168), last 3 bytes are checksum
DATA_SIZE = 7165

# Verify Arduino AVR core is installed before doing anything
ARDUINO_AVR = $(lastword $(sort $(wildcard $(HOME)/.arduino15/packages/arduino/hardware/avr/*)))

ifeq ($(ARDUINO_AVR),)
ifneq ($(MAKECMDGOALS),clean)
$(error Arduino AVR core not found. See README.md for setup instructions.)
endif
endif

CC      = avr-gcc
CXX     = avr-g++
OBJCOPY = avr-objcopy
AR      = avr-gcc-ar
SIZE    = avr-size

CORE_DIR    = $(ARDUINO_AVR)/cores/arduino
WIRE_DIR    = $(ARDUINO_AVR)/libraries/Wire/src
VARIANT_DIR = $(ARDUINO_AVR)/variants/standard
EEPROM_DIR  = $(ARDUINO_AVR)/libraries/EEPROM/src  # header-only; no objects needed

INC = -I$(CORE_DIR) -I$(WIRE_DIR) -I$(WIRE_DIR)/utility -I$(VARIANT_DIR) -I$(EEPROM_DIR) -I.

CFLAGS   = -mmcu=$(MCU) -DF_CPU=$(F_CPU) -DARDUINO=10819 \
           -Os -Wall -flto -ffunction-sections -fdata-sections $(INC)
CXXFLAGS = $(CFLAGS) -fno-exceptions -fpermissive

LDFLAGS  = -mmcu=$(MCU) -Wl,--gc-sections -flto -fuse-linker-plugin -Wl,--defsym=__TEXT_REGION_LENGTH__=$(DATA_SIZE)

BUILD_DIR = build

CORE_OBJS = $(BUILD_DIR)/core/wiring.o \
            $(BUILD_DIR)/core/wiring_analog.o \
            $(BUILD_DIR)/core/wiring_digital.o \
            $(BUILD_DIR)/core/hooks.o \
            $(BUILD_DIR)/core/main.o

WIRE_OBJS = $(BUILD_DIR)/wire/Wire.o \
            $(BUILD_DIR)/wire/utility/twi.o

.PHONY: all clean

all: $(TARGET).hex

# Create build subdirectories on demand
$(BUILD_DIR) $(BUILD_DIR)/core $(BUILD_DIR)/wire $(BUILD_DIR)/wire/utility:
	mkdir -p $@

# Firmware source (.ino compiled as C++)
$(BUILD_DIR)/$(TARGET).o: firmware.ino config.h | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) -x c++ -c -o $@ $<

# Arduino core objects
$(BUILD_DIR)/core/%.o: $(CORE_DIR)/%.c | $(BUILD_DIR)/core
	$(CC) $(CFLAGS) -c -o $@ $<

$(BUILD_DIR)/core/%.o: $(CORE_DIR)/%.cpp | $(BUILD_DIR)/core
	$(CXX) $(CXXFLAGS) -c -o $@ $<

# Wire library objects
$(BUILD_DIR)/wire/%.o: $(WIRE_DIR)/%.cpp | $(BUILD_DIR)/wire
	$(CXX) $(CXXFLAGS) -c -o $@ $<

$(BUILD_DIR)/wire/utility/%.o: $(WIRE_DIR)/utility/%.c | $(BUILD_DIR)/wire/utility
	$(CC) $(CFLAGS) -c -o $@ $<

$(BUILD_DIR)/libcore.a: $(CORE_OBJS)
	$(AR) rcs $@ $^

$(BUILD_DIR)/$(TARGET).elf: $(BUILD_DIR)/$(TARGET).o $(BUILD_DIR)/libcore.a $(WIRE_OBJS)
	$(CXX) $(LDFLAGS) -o $@ $< $(WIRE_OBJS) -L$(BUILD_DIR) -lcore

$(TARGET).hex: $(BUILD_DIR)/$(TARGET).elf
	$(OBJCOPY) -O binary -R .eeprom --pad-to=$(DATA_SIZE) --gap-fill=0xFF $< $(BUILD_DIR)/$(TARGET).bin
	od -An -tu1 -v $(BUILD_DIR)/$(TARGET).bin \
	  | LC_ALL=C awk 'BEGIN{s1=0;s2=0;x=0} \
	         function xorb(a,b,  r,i){r=0;for(i=0;i<8;i++)r+=(int(a/2^i)%2!=int(b/2^i)%2)*2^i;return r} \
	         {for(i=1;i<=NF;i++){b=$$i+0;s1=(s1+b)%256;s2=(s2+s1)%256;x=xorb(x,b)}} \
	         END{printf "%c%c%c",s1,s2,x}' >> $(BUILD_DIR)/$(TARGET).bin
	$(OBJCOPY) -I binary -O ihex $(BUILD_DIR)/$(TARGET).bin $@
	@PROGSIZE=$$($(SIZE) $< | tail -1 | awk '{print $$1}'); \
	 DATASIZE=$$($(SIZE) $< | tail -1 | awk '{print $$2+$$3}'); \
	 DATA_FREE=$$((1024 - $$DATASIZE)); \
	 echo "Flash:   $$PROGSIZE bytes used of $(DATA_SIZE) available (3 bytes reserved for checksum at 0x1BFD-0x1BFF)"; \
	 echo "RAM:     $$DATASIZE bytes used of 1024 [$$DATA_FREE bytes free]"

clean:
	rm -rf $(BUILD_DIR)
	rm -f $(TARGET).hex

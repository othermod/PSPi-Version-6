# Cross-compilers
CC_32 = arm-linux-gnueabihf-gcc
CC_64 = aarch64-linux-gnu-gcc

# Paths
BATOCERA_LIBS = /home/user/github/PSPi-Version-6/rpi/libraries/batocera/
RPI_USERLAND = /tmp/rpi-userland
RPI_BCM_HOST_INC = $(RPI_USERLAND)/host_applications/linux/libs/bcm_host/include
COMMON_FLAGS = -O3 -lrt

# Targets
PROGRAMS_32 = main mouse
PROGRAMS_64 = main mouse osd

all: lib_32 lib_64 $(PROGRAMS_32)_32 $(PROGRAMS_64)_64 package

# Compile common library
lib_32:
	$(MAKE) -C lib CC=$(CC_32) CFLAGS="$(COMMON_FLAGS) -I$(RPI_BCM_HOST_INC) -I$(RPI_USERLAND)"
lib_64:
	$(MAKE) -C lib CC=$(CC_64) CFLAGS="$(COMMON_FLAGS) -I$(RPI_BCM_HOST_INC) -I$(RPI_USERLAND)"

# Individual program targets
main_32:
	$(CC_32) -o bin/32bit/main main.c $(COMMON_FLAGS)
main_64:
	$(CC_64) -o bin/64bit/main main.c $(COMMON_FLAGS)

mouse_32:
	$(CC_32) -o bin/32bit/mouse mouse.c $(COMMON_FLAGS)
mouse_64:
	$(CC_64) -o bin/64bit/mouse mouse.c $(COMMON_FLAGS)

osd_64: lib_64
	@mkdir -p bin/64bit
	$(CC_64) -o bin/64bit/osd osd.c $(COMMON_FLAGS) \
		-I$(RPI_BCM_HOST_INC) -I$(RPI_USERLAND) -I$(RPI_USERLAND)/vcinclude -I./common \
		-L./lib -L$(BATOCERA_LIBS) \
		-Wl,-rpath,'$$ORIGIN' \
		-lbcm_host -lasound \
		lib/libraspidmx.a lib/libraspidmxPng.a

# Package target to prepare for FAT32/Lakka
package: osd_64
	@echo "Preparing package for FAT32..."
	@mkdir -p bin/64bit
	@cp lib/libbcm_host.so bin/64bit/
	@cp lib/libasound.so bin/64bit/
	@cp lib/libvchiq_arm.so bin/64bit/
	@cp lib/libvcos.so bin/64bit/
	@cd bin/64bit && patchelf --set-rpath '$$ORIGIN' *.so
	@cd bin/64bit && patchelf --set-rpath '$$ORIGIN' osd
	@echo "Package ready in bin/64bit/"

clean:
	rm -rf bin
	rm -f common/*.o
	rm -f lib/*.a
	$(MAKE) -C lib clean

.PHONY: all lib lib_32 lib_64 package clean

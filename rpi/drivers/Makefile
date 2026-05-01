# Cross-compilers
CC_32 = arm-linux-gnueabihf-gcc
CC_64 = aarch64-linux-gnu-gcc

# Paths
RPI_USERLAND = /tmp/rpi-userland
RPI_BCM_HOST_INC = $(RPI_BCM_HOST_INC)
RPI_BCM_HOST_INC = $(RPI_USERLAND)/host_applications/linux/libs/bcm_host/include
COMMON_FLAGS = -O3 -lrt

# Compile common library
lib_64:
	rm -f common/*.o
	$(MAKE) -C lib ARCH_DIR=64bit CC=$(CC_64) CFLAGS="$(COMMON_FLAGS) -I$(RPI_BCM_HOST_INC) -I$(RPI_USERLAND)"

lib_32:
	rm -f common/*.o
	$(MAKE) -C lib ARCH_DIR=32bit CC=$(CC_32) CFLAGS="$(COMMON_FLAGS) -I$(RPI_BCM_HOST_INC) -I$(RPI_USERLAND)"

# Individual program targets
main_32:
	@mkdir -p bin/32bit
	$(CC_32) -o bin/32bit/main main.c $(COMMON_FLAGS)

mouse_32:
	@mkdir -p bin/32bit
	$(CC_32) -o bin/32bit/mouse mouse.c $(COMMON_FLAGS)

osd_32: lib_32
	@mkdir -p bin/32bit
	$(CC_32) -o bin/32bit/osd osd.c $(COMMON_FLAGS) \
		-I$(RPI_BCM_HOST_INC) -I$(RPI_USERLAND) -I$(RPI_USERLAND)/vcinclude -I./common \
		-L./lib/32bit \
		-Wl,-rpath,'$$ORIGIN' \
		-lbcm_host -lasound \
		lib/32bit/libraspidmx.a lib/32bit/libraspidmxPng.a

main_64:
	@mkdir -p bin/64bit
	$(CC_64) -o bin/64bit/main main.c $(COMMON_FLAGS)

mouse_64:
	@mkdir -p bin/64bit
	$(CC_64) -o bin/64bit/mouse mouse.c $(COMMON_FLAGS)

osd_64: lib_64
	@mkdir -p bin/64bit
	$(CC_64) -o bin/64bit/osd osd.c $(COMMON_FLAGS) \
		-I$(RPI_BCM_HOST_INC) -I$(RPI_USERLAND) -I$(RPI_USERLAND)/vcinclude -I./common \
		-L./lib/64bit \
		-Wl,-rpath,'$$ORIGIN' \
		-lbcm_host -lasound \
		lib/64bit/libraspidmx.a lib/64bit/libraspidmxPng.a

# Package target to prepare for FAT32/Lakka
package: osd_64
	@echo "Preparing package for FAT32..."
	@mkdir -p bin/64bit
	@cp lib/64bit/libbcm_host.so bin/64bit/
	@cp lib/64bit/libvchiq_arm.so.0 bin/64bit/libvchiq_arm.so
	@cp lib/64bit/libvcos.so.0 bin/64bit/libvcos.so
	@cd bin/64bit && patchelf --set-rpath '$$ORIGIN' *.so
	@cd bin/64bit && patchelf --set-rpath '$$ORIGIN' osd
	@echo "Package ready in bin/64bit/"

# Top-level targets
all_64: lib_64 main_64 mouse_64 osd_64 package
all_32: lib_32 main_32 mouse_32 osd_32

clean:
	rm -rf bin
	rm -f common/*.o
	rm -f lib/*.a
	$(MAKE) -C lib clean

.PHONY: all_64 all_32 package clean

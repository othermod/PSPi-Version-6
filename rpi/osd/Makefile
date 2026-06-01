# Cross-compilers
CC_32 = arm-linux-gnueabihf-gcc
CC_64 = aarch64-linux-gnu-gcc

# Paths
RPI_USERLAND = /tmp/rpi-userland
RPI_BCM_HOST_INC = $(RPI_USERLAND)/host_applications/linux/libs/bcm_host/include

CFLAGS_COMMON = -O3 -lrt

# Build for 32-bit architecture
32:
	@mkdir -p bin/32bit
	@rm -f osd_toolkit/32bit/*.a
	@rm -f src/*.o
	@rm -f osd_toolkit/src/*.o
	$(MAKE) -C osd_toolkit ARCH_DIR=32bit CC=$(CC_32) CFLAGS="$(CFLAGS_COMMON) -I$(RPI_BCM_HOST_INC) -I$(RPI_USERLAND) -Iinclude"
	$(CC_32) -o bin/32bit/osd src/osd.c $(CFLAGS_COMMON) \
		-I$(RPI_BCM_HOST_INC) -I$(RPI_USERLAND) -I$(RPI_USERLAND)/vcinclude -Iosd_toolkit \
		-L./vendor/32bit \
		-Wl,-rpath,'$$ORIGIN' \
		-lbcm_host -lasound \
		osd_toolkit/32bit/libraspidmx-32bit.a osd_toolkit/32bit/libraspidmxPng-32bit.a

# Build for 64-bit architecture
64:
	@mkdir -p bin/64bit
	@rm -f osd_toolkit/64bit/*.a
	@rm -f src/*.o
	@rm -f osd_toolkit/src/*.o
	$(MAKE) -C osd_toolkit ARCH_DIR=64bit CC=$(CC_64) CFLAGS="$(CFLAGS_COMMON) -I$(RPI_BCM_HOST_INC) -I$(RPI_USERLAND) -Iinclude"
	$(CC_64) -o bin/64bit/osd src/osd.c $(CFLAGS_COMMON) \
		-I$(RPI_BCM_HOST_INC) -I$(RPI_USERLAND) -I$(RPI_USERLAND)/vcinclude -Iosd_toolkit \
		-L./vendor/64bit \
		-Wl,-rpath,'$$ORIGIN' \
		-lbcm_host -lasound \
		osd_toolkit/64bit/libraspidmx-64bit.a osd_toolkit/64bit/libraspidmxPng-64bit.a

# Clean build artifacts
clean:
	rm -rf bin lib
	rm -f src/*.o
	rm -f osd_toolkit/src/*.o
	rm -f osd_toolkit/osd_toolkit/32bit/*.a osd_toolkit/osd_toolkit/64bit/*.a
	$(MAKE) -C osd_toolkit clean

.PHONY: 32 64 clean

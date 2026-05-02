# Cross-compilers
CC_32 = arm-linux-gnueabihf-gcc
CC_64 = aarch64-linux-gnu-gcc

# Paths
RPI_USERLAND = /tmp/rpi-userland
RPI_BCM_HOST_INC = $(RPI_USERLAND)/host_applications/linux/libs/bcm_host/include

CFLAGS_COMMON = -O3 -lrt

# Build for 32-bit architecture
32:
	@echo "Building 32-bit..."
	@mkdir -p bin/32bit
	@rm -f src/*.o
	$(CC_32) -o bin/32bit/main src/main.c $(CFLAGS_COMMON)
	$(CC_32) -o bin/32bit/mouse src/mouse.c $(CFLAGS_COMMON)
	@echo "32-bit build complete."

# Build for 64-bit architecture
64:
	@echo "Building 64-bit..."
	@mkdir -p bin/64bit
	@rm -f src/*.o
	$(CC_64) -o bin/64bit/main src/main.c $(CFLAGS_COMMON)
	$(CC_64) -o bin/64bit/mouse src/mouse.c $(CFLAGS_COMMON)
	@echo "64-bit build complete."

# Clean build artifacts
clean:
	rm -rf bin
	rm -f src/*.o
	@echo "Clean complete."

.PHONY: 32 64 clean

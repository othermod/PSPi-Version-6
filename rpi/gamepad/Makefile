# Cross-compilers
CC_32 = arm-linux-gnueabi-gcc -march=armv6zk -mfloat-abi=softfp
CC_64 = aarch64-linux-gnu-gcc

# Paths
RPI_USERLAND = /tmp/rpi-userland
RPI_BCM_HOST_INC = $(RPI_USERLAND)/host_applications/linux/libs/bcm_host/include

CFLAGS_COMMON = -O3 -lrt -static

# Build for 32-bit architecture
32:
	@mkdir -p 32
	@rm -f *.o
	$(CC_32) -o 32/gamepad gamepad.c $(CFLAGS_COMMON)

# Build for 64-bit architecture
64:
	@mkdir -p 64
	@rm -f *.o
	$(CC_64) -o 64/gamepad gamepad.c $(CFLAGS_COMMON)

# Clean build artifacts
clean:
	rm -rf 32 64
	rm -f *.o

.PHONY: 32 64 clean

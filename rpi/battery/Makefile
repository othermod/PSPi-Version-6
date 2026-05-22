# Cross-compilers
CC_32 = arm-linux-gnueabi-gcc -march=armv6zk -mfloat-abi=softfp
CC_64 = aarch64-linux-gnu-gcc

CFLAGS_COMMON = -O3 -lrt -static

# Build for 32-bit architecture
32:
	@echo "Building 32-bit battery monitor..."
	@mkdir -p 32
	$(CC_32) -o 32/battery_monitor battery_monitor.c $(CFLAGS_COMMON)
	@echo "32-bit build complete."

# Build for 64-bit architecture
64:
	@echo "Building 64-bit battery monitor..."
	@mkdir -p 64
	$(CC_64) -o 64/battery_monitor battery_monitor.c $(CFLAGS_COMMON)
	@echo "64-bit build complete."

# Clean build artifacts
clean:
	rm -rf 32 64
	@echo "Clean complete."

.PHONY: 32 64 clean

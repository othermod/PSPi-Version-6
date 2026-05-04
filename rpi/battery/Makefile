# Cross-compilers
CC_32 = arm-linux-gnueabihf-gcc
CC_64 = aarch64-linux-gnu-gcc

CFLAGS_COMMON = -O3 -lrt

# Build for 32-bit architecture
32:
	@echo "Building 32-bit battery monitor..."
	@mkdir -p bin/32bit
	$(CC_32) -o bin/32bit/battery_monitor battery_monitor.c $(CFLAGS_COMMON)
	@echo "32-bit build complete."

# Build for 64-bit architecture
64:
	@echo "Building 64-bit battery monitor..."
	@mkdir -p bin/64bit
	$(CC_64) -o bin/64bit/battery_monitor battery_monitor.c $(CFLAGS_COMMON)
	@echo "64-bit build complete."

# Clean build artifacts
clean:
	rm -rf bin
	@echo "Clean complete."

.PHONY: 32 64 clean

# Cross-compilers
CC_64 = aarch64-linux-gnu-gcc

# Paths
LIBDRM_INC = /usr/include/libdrm

CFLAGS_COMMON = -O3 -lrt -static -I$(LIBDRM_INC) -ldrm -lm

# Build for 64-bit architecture
64:
	@mkdir -p 64
	@rm -f *.o
	$(CC_64) -o 64/gamepad_view gamepad_view.c gfx_util.c $(CFLAGS_COMMON)

# Clean build artifacts
clean:
	rm -rf 64 *.o

.PHONY: 64 clean
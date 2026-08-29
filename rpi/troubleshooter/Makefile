# Cross-compilers. The 32-bit build targets armv6 + soft-float (armel), the
# same baseline as rpi/gamepad: Ubuntu's armel libc.a is armv4t-baseline, so
# a fully static binary runs on the original Zero's ARM1176 with no sysroot
# and no fetched packages.
#
# There is no libdrm dependency: the troubleshooter drives the kernel DRM/KMS
# ioctl UAPI directly (<drm/drm.h>, <drm/drm_mode.h>), so there is nothing to
# link beyond libc/libm.
CC_32 = arm-linux-gnueabi-gcc -march=armv6zk -mfloat-abi=softfp
CC_64 = aarch64-linux-gnu-gcc

CFLAGS_COMMON = -O3 -lrt -static -lm

# Build for 32-bit architecture (armv6; runs on every PSPi board incl. Zero 1)
32:
	@mkdir -p 32
	@rm -f *.o
	$(CC_32) -o 32/troubleshooter troubleshooter.c $(CFLAGS_COMMON)

# Build for 64-bit architecture
64:
	@mkdir -p 64
	@rm -f *.o
	$(CC_64) -o 64/troubleshooter troubleshooter.c $(CFLAGS_COMMON)

# Clean build artifacts
clean:
	rm -rf 32 64 *.o

.PHONY: 32 64 clean

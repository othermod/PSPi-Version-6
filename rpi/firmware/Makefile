# Cross-compilers used by GitHub Actions: 32-bit targets armv6 (armv6zk)
# + softfp, statically linked, so the binary runs on the original Zero's
# ARM1176 with no sysroot.
#
# No libdrm dependency: like the troubleshooter, firmware drives the
# kernel DRM/KMS ioctl UAPI (<drm/drm.h>, <drm/drm_mode.h>) directly.
CC_32 = arm-linux-gnueabi-gcc -march=armv6zk -mfloat-abi=softfp
CC_64 = aarch64-linux-gnu-gcc

CFLAGS = -O3 -lrt -lm -static

# Build for 32-bit architecture (armv6; runs on every PSPi board incl. Zero 1)
32:
	@mkdir -p 32
	$(CC_32) -o 32/firmware firmware.c $(CFLAGS)

# Build for 64-bit architecture
64:
	@mkdir -p 64
	$(CC_64) -o 64/firmware firmware.c $(CFLAGS)

clean:
	rm -rf 32 64

.PHONY: 32 64 clean

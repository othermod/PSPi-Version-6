#
# Build static and shared libraries for raspidmx
#

ARCH_DIR ?= .

LIB=raspidmx
LIBPNG=raspidmxPng

OBJS=src/backgroundLayer.o src/imageGraphics.o src/key.o \
 src/font.o src/imageKey.o src/hsv2rgb.o \
 src/imageLayer.o src/image.o src/imagePalette.o

OBJSPNG=src/spriteLayer.o src/loadpng.o src/savepng.o src/scrollingLayer.o

CFLAGS+=-Wall -g -O3

RPI_USERLAND = /tmp/rpi-userland
RPI_BCM_HOST_INC = $(RPI_USERLAND)/host_applications/linux/libs/bcm_host/include
INCLUDES+=-I$(RPI_BCM_HOST_INC) -I$(RPI_USERLAND) -I$(RPI_BCM_HOST_INC)/interface/vcos/pthreads -I$(RPI_BCM_HOST_INC)/interface/vmcs_host/linux

all: $(LIB) $(LIBPNG)

%.o: %.c
	@rm -f $@ 
	$(CC) $(CFLAGS) $(INCLUDES) -Iosd_toolkit/include -g -c $< -o $@ -Wno-deprecated-declarations

$(LIB): $(OBJS)
	@mkdir -p $(ARCH_DIR)
	$(AR) rcs $(ARCH_DIR)/lib$(LIB)-$(ARCH_DIR).a $(OBJS)

$(LIBPNG): $(OBJSPNG)
	@mkdir -p $(ARCH_DIR)
	$(AR) rcs $(ARCH_DIR)/lib$(LIBPNG)-$(ARCH_DIR).a $(OBJSPNG)

clean:
	@rm -f $(OBJS)
	@rm -f lib$(LIB)-$(ARCH_DIR).a lib$(LIBPNG)-$(ARCH_DIR).a
	@find 32bit 64bit -name "*.a" -delete 2>/dev/null; true

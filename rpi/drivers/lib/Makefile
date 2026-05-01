#
# Build static and shared libraries for raspidmx
#

LIB=raspidmx
LIBPNG=raspidmxPng

OBJS=../common/backgroundLayer.o ../common/imageGraphics.o ../common/key.o \
 ../common/font.o ../common/imageKey.o ../common/hsv2rgb.o \
 ../common/imageLayer.o ../common/image.o ../common/imagePalette.o

OBJSPNG=../common/spriteLayer.o ../common/loadpng.o ../common/savepng.o ../common/scrollingLayer.o

CFLAGS+=-Wall -g -O3 -I../common $(shell libpng-config --cflags)
LDFLAGS+=-L/home/user/github/PSPi-Version-6/rpi/libraries/batocera/ -lbcm_host -lm
LDFLAGSPNG=${LDFLAGS} $(shell libpng-config --ldflags)

RPI_USERLAND = /tmp/rpi-userland
RPI_BCM_HOST_INC = $(RPI_USERLAND)/host_applications/linux/libs/bcm_host/include
INCLUDES+=-I$(RPI_BCM_HOST_INC) -I$(RPI_USERLAND) -I$(RPI_BCM_HOST_INC)/interface/vcos/pthreads -I$(RPI_BCM_HOST_INC)/interface/vmcs_host/linux

all: $(LIB) $(LIBPNG)

%.o: %.c
	@rm -f $@ 
	$(CC) $(CFLAGS) $(INCLUDES) -g -c $< -o $@ -Wno-deprecated-declarations

$(LIB): $(OBJS)
	$(AR) rcs lib$(LIB).a $(OBJS)

$(LIBPNG): $(OBJSPNG)
	$(AR) rcs lib$(LIBPNG).a $(OBJSPNG)


clean:
	@rm -f $(OBJS)
	@rm -f lib$(LIB).a

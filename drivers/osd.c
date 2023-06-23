#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <unistd.h>
#include <linux/i2c-dev.h>
#include <sys/ioctl.h>
#include <fcntl.h>
#include <linux/input.h>
#include <linux/uinput.h>
#include <string.h>
#include <assert.h>
#include <strings.h>
#include "font.h"
#include "imageGraphics.h"
#include "imageLayer.h"
#include <math.h>
#include "bcm_host.h"

bool isMute = 0;
uint8_t isCharging = 1;
uint8_t batteryPercent = 75;

// create colors ( format is: red, green, blue, opacity)
static RGBA8_T clearColor = { 0,    0,    0,    0};
static RGBA8_T green =      { 0,    255,  0,    255};
static RGBA8_T red =        { 255,  0,    0,    255};
static RGBA8_T orange =     { 255,  127,  0,    255};
static RGBA8_T white =      { 255,  255,  255,  255};
static RGBA8_T black =      { 0,    0,    0,    255};

void drawBattery(IMAGE_LAYER_T * batteryLayer) {
  IMAGE_T * image = & (batteryLayer -> image);
  //clearImageRGB(image, & clearColor); //the image doesn't need to be erased because the same pixels are being used and colors are changing
  RGBA8_T * batteryColor;
  batteryColor = & green;
  if (batteryPercent < 20) { // sets color depending on battery level
    batteryColor = & orange;
  }
  if (batteryPercent < 10) {
    batteryColor = & red;
  }
  // draw the battery outline and fill with color
  imageBoxFilledRGB(image, 1, 0, 30, 14, & white);
  imageBoxFilledRGB(image, 0, 4, 2, 10, & white);
  imageBoxFilledRGB(image, 2, 1, 29, 13, & black);
  imageBoxFilledRGB(image, 1, 5, 3, 9, & black);
  imageBoxFilledRGB(image, 28 - batteryPercent / 4, 2, 28, 12, batteryColor);
  if (isCharging) {
    RGBA8_T * boltColor;
    if (isCharging == 2) {
      boltColor = & green;
    } else {
      boltColor = & white;
    }
    // draw the lightning bolt to show that the battery is charging
    imageBoxFilledRGB(image, 15, 3, 16, 11, boltColor);
    imageBoxFilledRGB(image, 12, 4, 14, 6, boltColor);
    imageBoxFilledRGB(image, 10, 6, 11, 8, boltColor);
    imageBoxFilledRGB(image, 7, 7, 9, 8, boltColor);
    imageBoxFilledRGB(image, 17, 8, 19, 10, boltColor);
    imageBoxFilledRGB(image, 20, 7, 21, 8, boltColor);
    imageBoxFilledRGB(image, 22, 6, 24, 7, boltColor);
    imageBoxFilledRGB(image, 14, 2, 17, 2, & black);
    imageBoxFilledRGB(image, 17, 2, 17, 7, & black);
    imageBoxFilledRGB(image, 18, 7, 19, 7, & black);
    imageBoxFilledRGB(image, 19, 6, 21, 6, & black);
    imageBoxFilledRGB(image, 21, 5, 25, 5, & black);
    imageBoxFilledRGB(image, 25, 6, 25, 7, & black);
    imageBoxFilledRGB(image, 24, 7, 24, 8, & black);
    imageBoxFilledRGB(image, 23, 8, 22, 8, & black);
    imageBoxFilledRGB(image, 22, 9, 20, 9, & black);
    imageBoxFilledRGB(image, 20, 10, 19, 10, & black);
    imageBoxFilledRGB(image, 19, 11, 17, 11, & black);
    imageBoxFilledRGB(image, 17, 12, 14, 12, & black);
    imageBoxFilledRGB(image, 14, 11, 14, 8, & black);
    imageBoxFilledRGB(image, 14, 7, 12, 7, & black);
    imageBoxFilledRGB(image, 12, 8, 10, 8, & black);
    imageBoxFilledRGB(image, 10, 9, 6, 9, & black);
    imageBoxFilledRGB(image, 6, 8, 6, 8, & black);
    imageBoxFilledRGB(image, 6, 7, 7, 7, & black);
    imageBoxFilledRGB(image, 7, 6, 9, 6, & black);
    imageBoxFilledRGB(image, 9, 5, 11, 5, & black);
    imageBoxFilledRGB(image, 11, 4, 12, 4, & black);
    imageBoxFilledRGB(image, 12, 3, 14, 3, & black);
  }
  changeSourceAndUpdateImageLayer(batteryLayer);
}

void drawMute(IMAGE_LAYER_T * muteLayer) {
  IMAGE_T * image = & (muteLayer -> image);
  // draw the battery outline and fill with color
  if (!isMute) {
    imageBoxFilledRGB(image, 5, 0, 11, 14, & white);
    imageBoxFilledRGB(image, 4, 1, 4, 13, & white);
    imageBoxFilledRGB(image, 3, 2, 3, 12, & white);
    imageBoxFilledRGB(image, 2, 3, 2, 11, & white);
    imageBoxFilledRGB(image, 0, 4, 1, 10, & white);

    imageBoxFilledRGB(image, 6, 1, 10, 13, & black);
    imageBoxFilledRGB(image, 5, 2, 5, 12, & black);
    imageBoxFilledRGB(image, 4, 3, 4, 11, & black);
    imageBoxFilledRGB(image, 3, 4, 3, 10, & black);
    imageBoxFilledRGB(image, 1, 5, 2, 9, & black);

    imageBoxFilledRGB(image, 0, 0, 2, 2, & red);
    imageBoxFilledRGB(image, 2, 2, 4, 4, & red);
    imageBoxFilledRGB(image, 4, 4, 6, 6, & red);
    imageBoxFilledRGB(image, 6, 6, 8, 8, & red);
    imageBoxFilledRGB(image, 8, 8, 10, 10, & red);
    imageBoxFilledRGB(image, 10, 10, 12, 12, & red);
    imageBoxFilledRGB(image, 12, 12, 14, 14, & red);
  } else {
    clearImageRGB(image, & clearColor); // erase the whole image
  }
  changeSourceAndUpdateImageLayer(muteLayer);
}

void clearLayer(IMAGE_LAYER_T * layer) {
  IMAGE_T * image = & (layer -> image);
  clearImageRGB(image, & clearColor);
  changeSourceAndUpdateImageLayer(layer);
}

int main() {

  uint32_t displayNumber = 0;

  bcm_host_init();

  DISPMANX_DISPLAY_HANDLE_T display
    = vc_dispmanx_display_open(displayNumber);
  assert(display != 0);

  DISPMANX_MODEINFO_T info;
  int result = vc_dispmanx_display_get_info(display, & info);
  assert(result == 0);

  static int layer = 100000;

  IMAGE_LAYER_T batteryLayer;
  initImageLayer( & batteryLayer,
    31, // battery image width
    15, // battery image height
    VC_IMAGE_RGBA16);
  createResourceImageLayer( & batteryLayer, layer);

  IMAGE_LAYER_T muteLayer;
  initImageLayer( & muteLayer,
    15, // battery image width
    15, // battery image height
    VC_IMAGE_RGBA16);
  createResourceImageLayer( & muteLayer, layer);

  DISPMANX_UPDATE_HANDLE_T update = vc_dispmanx_update_start(0);
  assert(update != 0);
  int xOffset = info.width - 31;
  int yOffset = 0;
  addElementImageLayerOffset( & batteryLayer, xOffset, yOffset, display, update);
  xOffset = info.width - 46;
  addElementImageLayerOffset( & muteLayer, xOffset, yOffset, display, update);

  result = vc_dispmanx_update_submit_sync(update);
  assert(result == 0);
  while (1) {

    if (batteryPercent) { //if battery % or charging status changed, update the OSD
      drawBattery(& batteryLayer); // make sure this is only done if something changes
    }

    if (isMute) { // only if this changes
      drawMute(& muteLayer);
    }
    usleep(150000);
    }
  destroyImageLayer( & batteryLayer);
  destroyImageLayer( & muteLayer);
  result = vc_dispmanx_display_close(display);
  assert(result == 0);
  //---------------------------------------------------------------------
  return 0;
}

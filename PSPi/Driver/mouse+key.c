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
#include <time.h>
#include <strings.h>
#include "font.h"
#include "imageGraphics.h"
#include "imageLayer.h"
#include <math.h>
#include "bcm_host.h"

#define SENSE_RESISTOR 50
#define I2C_ADDRESS 0x18
#define BATTERY_TH 20
#define BRIGHTNESS_MAX 7
#define MOUSE 0
#define JOYSTICK 1
bool operatingMode = JOYSTICK;
bool textOSD = 1;

volatile bool run = true;

static RGBA8_T clearColor = {0,0,0,0};
static RGBA8_T backgroundColor = { 0, 0, 0, 120 };
static RGBA8_T textColor = { 255, 255, 255, 255 };
static RGBA8_T greenColor = { 0, 255, 0, 255 };
static RGBA8_T redColor = { 255, 0, 0, 255 };
static RGBA8_T orangeColor = { 255, 127, 0, 175 };
static RGBA8_T whiteColor = { 255, 255, 255, 255 }; // red, green, blue, opacity
static RGBA8_T blackColor = { 0, 0, 0, 175 };
static RGBA8_T keyboardBackgroundColor = { 0, 0, 0, 100 };
static int battery = 30;

static float temp = 0.f;

typedef struct {
  uint16_t buttons; // button currentReading
  uint8_t axis0; // first axis
  uint8_t axis1; // second axis
  uint16_t voltage; // raw voltage
  uint16_t amperage; // raw amperage
}
I2C_Struct;

typedef struct {
  uint16_t rawVoltage;
  uint16_t correctedVoltage;
  int amperage;
  int percent;
}
battery_Struct;

battery_Struct batteryData; // create battery struct

void drawBattery(float batval, IMAGE_LAYER_T* batteryLayer){
    IMAGE_T *image = &(batteryLayer->image);
    clearImageRGB(image,&clearColor);
    RGBA8_T *color;
    if (batteryData.percent > 19) {color = &greenColor;} // sets color depending on battery level
    if (batteryData.percent < 20) {color = &orangeColor;}
    if (batteryData.percent < 10) {color = &redColor;}
    imageBoxFilledRGB(image, 1,0,28,14, &whiteColor);
    imageBoxFilledRGB(image, 0,4,2,10, &whiteColor);
    imageBoxFilledRGB(image, 2,1,27,13, &blackColor);
    imageBoxFilledRGB(image, 1,5,3,9, &blackColor);
    imageBoxFilledRGB(image, 3+20-batteryData.percent/5,2,26,12, color);

    //if (battery > 25) {

    //setPixelRGB(image, 15, 15, &whiteColor);
    //setPixelRGB(image, 15, 16, &whiteColor);
    //setPixelRGB(image, 16, 15, &whiteColor);
    //setPixelRGB(image, 16, 16, &whiteColor);
    //}
    changeSourceAndUpdateImageLayer(batteryLayer);
}

void drawChargeIndicator(IMAGE_LAYER_T* chargingLayer){
    IMAGE_T *image = &(chargingLayer->image);
    clearImageRGB(image,&clearColor);
    //to config params
    RGBA8_T *color = &whiteColor;
    if (batteryData.amperage < -10) {
    /*
    imageBoxFilledRGB(image,8,0,13,0, &whiteColor);
    imageBoxFilledRGB(image,6,1,13,1, &whiteColor);
    imageBoxFilledRGB(image,5,2,13,2, &whiteColor);
    imageBoxFilledRGB(image,3,3,21,3, &whiteColor);
    imageBoxFilledRGB(image,1,4,21,4, &whiteColor);
    imageBoxFilledRGB(image,0,5,21,5, &whiteColor);
    imageBoxFilledRGB(image,0,6,21,6, &whiteColor);
    imageBoxFilledRGB(image,0,7,21,7, &whiteColor);
    imageBoxFilledRGB(image,0,8,20,8, &whiteColor);
    imageBoxFilledRGB(image,0,9,18,9, &whiteColor);
    imageBoxFilledRGB(image,8,10,16,10, &whiteColor);
    imageBoxFilledRGB(image,8,11,15,11, &whiteColor);
    imageBoxFilledRGB(image,8,12,13,12, &whiteColor);
    */

    imageBoxFilledRGB(image,10,2,11,10, color);
    imageBoxFilledRGB(image,7,3,9,5, color);
    imageBoxFilledRGB(image,5,5,6,7, color);
    imageBoxFilledRGB(image,2,6,4,7, color);
    imageBoxFilledRGB(image,12,7,14,9, color);
    imageBoxFilledRGB(image,15,6,16,7, color);
    imageBoxFilledRGB(image,17,5,19,6, color);

    imageBoxFilledRGB(image,9,1,12,1, &blackColor);
    imageBoxFilledRGB(image,12,1,12,6, &blackColor);
    imageBoxFilledRGB(image,13,6,14,6, &blackColor);
    imageBoxFilledRGB(image,14,5,16,5, &blackColor);
    imageBoxFilledRGB(image,16,4,20,4, &blackColor);
    imageBoxFilledRGB(image,20,5,20,6, &blackColor);
    imageBoxFilledRGB(image,19,6,19,7, &blackColor);
    imageBoxFilledRGB(image,18,7,17,7, &blackColor);
    imageBoxFilledRGB(image,17,8,15,8, &blackColor);
    imageBoxFilledRGB(image,15,9,14,9, &blackColor);
    imageBoxFilledRGB(image,14,10,12,10, &blackColor);
    imageBoxFilledRGB(image,12,11,9,11, &blackColor);
    imageBoxFilledRGB(image,9,10,9,7, &blackColor);
    imageBoxFilledRGB(image,9,6,7,6, &blackColor);
    imageBoxFilledRGB(image,7,7,5,7, &blackColor);
    imageBoxFilledRGB(image,5,8,1,8, &blackColor);
    imageBoxFilledRGB(image,1,7,1,7, &blackColor);
    imageBoxFilledRGB(image,1,6,2,6, &blackColor);
    imageBoxFilledRGB(image,2,5,4,5, &blackColor);
    imageBoxFilledRGB(image,4,4,6,4, &blackColor);
    imageBoxFilledRGB(image,6,3,7,3, &blackColor);
    imageBoxFilledRGB(image,7,2,9,2, &blackColor);

  }
    changeSourceAndUpdateImageLayer(chargingLayer);
}

void clearLayer(IMAGE_LAYER_T *layer){
    IMAGE_T *image = &(layer->image);
    clearImageRGB(image, &clearColor);
    changeSourceAndUpdateImageLayer(layer);
}

void updateInfo(IMAGE_LAYER_T *infoLayer){
    char buffer[128];
    snprintf(buffer, sizeof(buffer),"%dmA\n%.2fW\n%d%%\nRaw:%.2fV\nCalc:%.2fV\n", batteryData.amperage, batteryData.amperage * batteryData.rawVoltage / 1000000.f, batteryData.percent,  batteryData.rawVoltage/1000.f, batteryData.correctedVoltage/1000.f);
    IMAGE_T *image = &(infoLayer->image);
    clearImageRGB(image, &clearColor);
    int x = 1, y = 1;
    //drawStringRGB(x+1, y, buffer, &backgroundColor, image);
    //drawStringRGB(x-1, y, buffer, &backgroundColor, image);
    //drawStringRGB(x, y+1, buffer, &backgroundColor, image);
    //drawStringRGB(x, y-1, buffer, &backgroundColor, image);
    imageBoxFilledRGB(image,1,1,50,50, &blackColor);
    drawStringRGB(x, y, buffer, &textColor, image);

    //uint8_t keyb [] = {"Q","W","E","R","T","Y"};


    changeSourceAndUpdateImageLayer(infoLayer);
}

void updateKey(IMAGE_LAYER_T *keyLayer){
    char buffer[128];
    snprintf(buffer, sizeof(buffer),"Q   W   E   R   T   Y   U   I   O   P\n\nA   S   D   F   G   H   J   K   L\n\nZ   X   C   V   B   N   M");
    IMAGE_T *image = &(keyLayer->image);
    clearImageRGB(image, &clearColor);
    imageBoxFilledRGB(image,100,100,500,150, &keyboardBackgroundColor);
    int posX = 100;
    int posY = 100;
    drawStringRGB(posX, posY, buffer, &textColor, image);

    //uint8_t keyb [] = {"Q","W","E","R","T","Y"};


    changeSourceAndUpdateImageLayer(keyLayer);
}

int openI2C() {
  int file;
  char * filename = "/dev/i2c-1"; //specify which I2C bus to use
  if ((file = open(filename, O_RDWR)) < 0) {
    fprintf(stderr, "Failed to open the i2c bus"); /* ERROR HANDLING: you can check errno to see what went wrong */
    exit(1);
  }
  return file;
}

void emit(int virtualDevice, int type, int code, int val)
{
   struct input_event ie;
   ie.type = type;
   ie.code = code;
   ie.value = val;
   /* timestamp values below are ignored */
   ie.time.tv_sec = 0;
   ie.time.tv_usec = 0;
   write(virtualDevice, &ie, sizeof(ie));
}

int main(int argc, char * argv[]) {
  uint32_t displayNumber = 0;
  //-------------------------------------------------------------------
  bcm_host_init();
  //---------------------------------------------------------------------
  DISPMANX_DISPLAY_HANDLE_T display
      = vc_dispmanx_display_open(displayNumber);
  assert(display != 0);
  //---------------------------------------------------------------------
  DISPMANX_MODEINFO_T info;
  int result = vc_dispmanx_display_get_info(display, &info);
  assert(result == 0);
  //---------------------------------------------------------------------
  static int layer = 30000;

  IMAGE_LAYER_T infoLayer;
  initImageLayer(&infoLayer, info.width, info.height, VC_IMAGE_RGBA16);
  createResourceImageLayer(&infoLayer, layer);

  IMAGE_LAYER_T keyLayer;
  initImageLayer(&keyLayer, info.width, info.height, VC_IMAGE_RGBA16);
  createResourceImageLayer(&keyLayer, layer);

  IMAGE_LAYER_T batteryLayer;
  initImageLayer(&batteryLayer,
                 30, // battery image width
                 30, // battery image height
                 VC_IMAGE_RGBA16);
  createResourceImageLayer(&batteryLayer, layer);

  IMAGE_LAYER_T chargingLayer;
  initImageLayer(&chargingLayer,
                 30, // charging image width
                 30, // charging image height
                 VC_IMAGE_RGBA16);
  createResourceImageLayer(&chargingLayer, layer+1);

  DISPMANX_UPDATE_HANDLE_T update = vc_dispmanx_update_start(0);
  assert(update != 0);
  int xOffset = 0;
  int yOffset = 0;
  addElementImageLayerOffset(&keyLayer, xOffset, yOffset, display, update);
  xOffset = 0;
  yOffset = 0;
  addElementImageLayerOffset(&infoLayer, xOffset, yOffset, display, update);
  xOffset = 771;
  yOffset = 0;
  addElementImageLayerOffset(&batteryLayer, xOffset, yOffset, display, update);
  xOffset = 775;
  yOffset = 1;
  addElementImageLayerOffset(&chargingLayer, xOffset, yOffset, display, update);

  result = vc_dispmanx_update_submit_sync(update);
  assert(result == 0);

  int I2CFile = openI2C(); // open I2C device
  if (ioctl(I2CFile, I2C_SLAVE, I2C_ADDRESS) < 0) { // initialize communication
    fprintf(stderr, "I2C: Failed to acquire bus access/talk to slave 0x%x\n", I2C_ADDRESS);
    return 0;
  }

  I2C_Struct currentReading; // create I2C data struct

  currentReading.buttons = 0;
  currentReading.axis0 = 127;
  currentReading.axis1 = 127;

  struct uinput_setup usetup; // create uinput device (https://www.kernel.org/doc/html/v4.16/input/uinput.html)
  int virtualMouse = open("/dev/uinput", O_WRONLY | O_NONBLOCK);
  ioctl(virtualMouse, UI_SET_EVBIT, EV_KEY);
  ioctl(virtualMouse, UI_SET_KEYBIT, BTN_LEFT);
  ioctl(virtualMouse, UI_SET_KEYBIT, BTN_RIGHT);
  ioctl(virtualMouse, UI_SET_EVBIT, EV_REL);
  ioctl(virtualMouse, UI_SET_RELBIT, REL_X);
  ioctl(virtualMouse, UI_SET_RELBIT, REL_Y);
  memset(&usetup, 0, sizeof(usetup));
  usetup.id.bustype = BUS_USB;
  usetup.id.vendor = 0x1234; /* sample vendor */
  usetup.id.product = 0x5678; /* sample product */
  strcpy(usetup.name, "Example device");
  ioctl(virtualMouse, UI_DEV_SETUP, &usetup);
  ioctl(virtualMouse, UI_DEV_CREATE);
  sleep(1); // sleep to give time for things to settle

  int count = 0;
  int countOSD = 0;
  while (1) {
    if (read(I2CFile, &currentReading, sizeof(I2C_Struct)) != sizeof(I2C_Struct)) { // read the atmega
      printf("Controller is not detected on the I2C bus.\n");
      sleep(1);
    } else { // everything is ok
      int xcenter = 123;
      int ycenter = 131;
      emit(virtualMouse, EV_REL, REL_X, (currentReading.axis0 - xcenter) / 8);
      emit(virtualMouse, EV_REL, REL_Y, (currentReading.axis1 - ycenter) / 8);
      emit(virtualMouse, EV_KEY, BTN_LEFT, ((currentReading.buttons >> 0x01) & 1));
      emit(virtualMouse, EV_KEY, BTN_RIGHT, ((currentReading.buttons >> 0x00) & 1));
      emit(virtualMouse, EV_SYN, SYN_REPORT, 0);

      if (((currentReading.buttons >> 0x04) & 1) && ((currentReading.buttons >> 0x05) & 1)){
        countOSD++;
        if (countOSD == 200) {
          textOSD = !textOSD;
          clearLayer(&infoLayer);
          clearLayer(&keyLayer);
        }
      } else {
      countOSD = 0;
      }
    }
    if (count == 0) {
      batteryData.rawVoltage = currentReading.voltage * 36300 / 1024 / 64; //set initial battery condition
      batteryData.amperage = (currentReading.voltage - currentReading.amperage) * 10 / 11; //set initial battery condition
      batteryData.amperage = batteryData.amperage * 36300 / 1024 / 64; //set initial battery condition
      batteryData.correctedVoltage = batteryData.rawVoltage + batteryData.amperage / 3; //set initial battery condition
    }
    count++;
    if (count == 66) {
    float batval = battery/100.f;
    battery--;
    if (battery == 0) {battery = 100;}
    drawBattery(batval, &batteryLayer); // this only needs to be done if something changes
    drawChargeIndicator(&chargingLayer); // this only needs to be done if something changes
    if(textOSD) {
        updateInfo(&infoLayer);
        updateKey(&keyLayer);
    }
    count = 1;
    }
    batteryData.rawVoltage = currentReading.voltage * 36300 / 1024 / 64;
    batteryData.amperage = (currentReading.voltage - currentReading.amperage) * 10 / 11;
    batteryData.amperage = batteryData.amperage * 36300 / 1024 / 64;
    batteryData.amperage = batteryData.amperage * (100 / SENSE_RESISTOR);
    int temp = batteryData.rawVoltage + batteryData.amperage / 2.5;
    if (temp > batteryData.correctedVoltage + 25) {batteryData.correctedVoltage++;} // 25mV of hysteresis to keep battery bar from bouncing around
    if (temp < batteryData.correctedVoltage - 25) {batteryData.correctedVoltage--;}
    batteryData.percent = 100-(4150 - batteryData.correctedVoltage)/8.5;
    if (batteryData.percent > 100) {batteryData.percent = 100;}
    if (batteryData.percent < 0) {batteryData.percent = 0;}
    usleep(15000);
  }
  close(I2CFile); // close file
  ioctl(virtualMouse, UI_DEV_DESTROY);
   close(virtualMouse);
   destroyImageLayer(&keyLayer);
   destroyImageLayer(&infoLayer);
   destroyImageLayer(&batteryLayer);
   destroyImageLayer(&chargingLayer);
   result = vc_dispmanx_display_close(display);
   assert(result == 0);
   //---------------------------------------------------------------------
   return 0;
}

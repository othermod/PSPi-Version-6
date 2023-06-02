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

#define SENSE_RESISTOR 50
#define BATTERY_INTERNAL_RESISTANCE 270

#define I2C_ADDRESS 0x06

// bit positions for each button
#define BTN_EAST_BIT_READING ((currentReading.buttons >> 0x00) & 1)
#define BTN_SOUTH_BIT_READING ((currentReading.buttons >> 0x01) & 1)
#define BTN_NORTH_BIT_READING ((currentReading.buttons >> 0x02) & 1)
#define BTN_WEST_BIT_READING ((currentReading.buttons >> 0x03) & 1)
#define BTN_TL_BIT_READING ((currentReading.buttons >> 0x04) & 1)
#define BTN_TR_BIT_READING ((currentReading.buttons >> 0x05) & 1)
#define BTN_SELECT_BIT_READING ((currentReading.buttons >> 0x06) & 1)
#define BTN_START_BIT_READING ((currentReading.buttons >> 0x07) & 1)
#define BTN_DPAD_UP_BIT_READING ((currentReading.buttons >> 0x08) & 1)
#define BTN_DPAD_DOWN_BIT_READING ((currentReading.buttons >> 0x09) & 1)
#define BTN_DPAD_LEFT_BIT_READING ((currentReading.buttons >> 0x0A) & 1)
#define BTN_DPAD_RIGHT_BIT_READING ((currentReading.buttons >> 0x0B) & 1)
#define BTN_HOME_BIT_READING ((currentReading.buttons >> 0x0C) & 1)
#define BTN_DISPLAY_BIT_READING ((currentReading.buttons >> 0x0D) & 1)
#define BTN_MUTE_BIT_READING ((currentReading.buttons >> 0x0E) & 1)
#define STATUS_MUTE_BIT_READING ((currentReading.buttons >> 0x0F) & 1)

// I2C Commands
#define ATMEGA_CHANGE_OPERATING_MODE 0x02 // byte 1 of 2
#define ATMEGA_RESET_TO_BOOTLOADER 0x01 // byte 2

#define ATMEGA_SET_ACTIVE_BRIGHTNESS 0x03
// byte 2 is 0-255 for brightness

#define ATMEGA_CHANGE_BACKLIGHT_SETTING_IN_EEPROM 0x04 // byte 1 of 3
// byte 2 is 0-7 for position
// byte 3 is 0-255 for brightness

#define ATMEGA_CHANGE_MUTE_STATUS 0x05 // byte 1 of 2
#define ATMEGA_MUTE_AUDIO 0x01 // byte 2
#define ATMEGA_UNMUTE_AUDIO 0x02 // byte 2

#define ATMEGA_CHANGE_ORANGE_LED_STATUS 0x06 // byte 1 of 2
#define ATMEGA_FORCE_ORANGE_LED 0x01 // byte 2
#define ATMEGA_UNFORCE_ORANGE_LED 0x02 // byte 2

bool reportingEnabled = 0;
bool gamepadEnabled = 0;
bool mouseEnabled = 0;
bool joystickEnabled = 0;
bool textOSD = 0;
bool isMute = 0;
bool firstLoop = 1;
int textDelay = 0;
int virtualMouse;
int virtualGamepad;
char gpioStatus[2];
int I2CFile; // defining this here so it can be used without passing it to functions
uint8_t writeBuffer[3];

volatile bool run = true;

// create colors ( format is: red, green, blue, opacity)
static RGBA8_T clearColor = { 0,    0,    0,    0};
static RGBA8_T green =      { 0,    255,  0,    255};
static RGBA8_T red =        { 255,  0,    0,    255};
static RGBA8_T orange =     { 255,  127,  0,    255};
static RGBA8_T white =      { 255,  255,  255,  255};
static RGBA8_T black =      { 0,    0,    0,    255};

// get rid of voltage and amperage, and replace with battery % (can do + for charging and - for discharging)
// maybe add 4-bit LCD brightness and have an 8-level indicator when display button is being pressed
typedef struct {
  uint16_t buttons; // 16 buttons stored as 16-bit integer
  uint8_t axis0; // first axis
  uint8_t axis1; // second axis
  uint16_t voltage; // raw voltage
  uint16_t amperage; // raw amperage
  uint8_t brightness;
}
I2C_Struct;

I2C_Struct currentReading; // create I2C data struct
I2C_Struct previousReading; // create second I2C data struct for comparison to check for changes

typedef struct {
  uint16_t rawVoltage;
  uint16_t correctedVoltage;
  int amperage;
  int percent;
  uint8_t isCharging;
}
battery_Struct;

battery_Struct batteryData; // create battery struct
battery_Struct previousBatteryData; // create second battery struct for comparison to check for changes

void drawBattery(IMAGE_LAYER_T * batteryLayer) {
  IMAGE_T * image = & (batteryLayer -> image);
  //clearImageRGB(image, & clearColor); //the image doesn't need to be erased because the same pixels are being used and colors are changing
  RGBA8_T * batteryColor;
  batteryColor = & green;
  if (batteryData.percent < 20) { // sets color depending on battery level
    batteryColor = & orange;
  }
  if (batteryData.percent < 10) {
    batteryColor = & red;
  }
  // draw the battery outline and fill with color
  imageBoxFilledRGB(image, 1, 0, 30, 14, & white);
  imageBoxFilledRGB(image, 0, 4, 2, 10, & white);
  imageBoxFilledRGB(image, 2, 1, 29, 13, & black);
  imageBoxFilledRGB(image, 1, 5, 3, 9, & black);
  imageBoxFilledRGB(image, 28 - batteryData.percent / 4, 2, 28, 12, batteryColor);
  if (batteryData.isCharging) {
    RGBA8_T * boltColor;
    if (batteryData.isCharging == 2) {
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
  changeSourceAndUpdateImageLayer(muteLayer);
}

void drawBrightness(IMAGE_LAYER_T * brightnessLayer) {
  IMAGE_T * image = & (brightnessLayer -> image);
  for (size_t i = 0; i <= currentReading.brightness; i++) {
    imageBoxFilledRGB(image, 100 * i + 40, 400, 100 * i + 60, 420, & black);
    imageBoxFilledRGB(image, 100 * i + 44, 404, 100 * i + 56, 416, & white);
  }
  changeSourceAndUpdateImageLayer(brightnessLayer);
}

void clearLayer(IMAGE_LAYER_T * layer) {
  IMAGE_T * image = & (layer -> image);
  clearImageRGB(image, & clearColor);
  changeSourceAndUpdateImageLayer(layer);
}

void updateInfo(IMAGE_LAYER_T * infoLayer) {
  IMAGE_T * image = & (infoLayer -> image);

    char buffer[128];
    snprintf(buffer, sizeof(buffer), "Power:\n%dmA\n%dmW\nBattery:\n%d%%\nRaw Volt:\n%dmV\nCalc Volt:\n%dmV\n",-batteryData.amperage, -batteryData.amperage * batteryData.rawVoltage / 1000, batteryData.percent, batteryData.rawVoltage, batteryData.correctedVoltage);
    clearImageRGB(image, & clearColor);
    int x = 0, y = 0;
    drawStringRGB(x, y, buffer, & white, image);
    changeSourceAndUpdateImageLayer(infoLayer);
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

void emit(int virtualDevice, int type, int code, int val) {
  struct input_event ie;
  ie.type = type;
  ie.code = code;
  ie.value = val;
  /* timestamp values below are ignored */
  ie.time.tv_sec = 0;
  ie.time.tv_usec = 0;
  write(virtualDevice, & ie, sizeof(ie));
}

void readGPIO(){
  int fdd = open("/sys/class/gpio/gpio11/value", O_RDONLY);
  read(fdd, gpioStatus, 2);
  close(fdd);
}

void sleepMode(IMAGE_LAYER_T * infoLayer){
  IMAGE_T * image = & (infoLayer -> image);
  int i;
    for (i = 0; i < 244; i++) {
      imageHorizontalLineRGB(image, 0, 799, i, & black);
      imageHorizontalLineRGB(image, 0, 799, 480-i, & black);
      i++;
      imageHorizontalLineRGB(image, 0, 799, i, & black);
      imageHorizontalLineRGB(image, 0, 799, 480-i, & black);
      i++;
      imageHorizontalLineRGB(image, 0, 799, i, & black);
      imageHorizontalLineRGB(image, 0, 799, 480-i, & black);
      changeSourceAndUpdateImageLayer(infoLayer);
    }
    writeBuffer[0] = ATMEGA_SET_ACTIVE_BRIGHTNESS;
    writeBuffer[1] = 0x00;
  	if (write(I2CFile,writeBuffer,2) != 2) {
  			/* ERROR HANDLING: i2c transaction failed */
  			printf("Failed to write to the i2c bus.\n");
  		}

  if (reportingEnabled) {printf("Video Playing\n");}
  sleep(0);
  while (!(( *gpioStatus >> 0x00) & 1)){
    if (reportingEnabled) {printf("Still in sleep mode\n");}
    sleep(1);
    readGPIO();
  }
  if (reportingEnabled) {printf("Exiting sleep mode\n");}
    clearImageRGB(image, & clearColor);
    firstLoop = 1; // reset the battery voltage because the voltage probably changed while system was in sleep mode
}

int main(int argc, char * argv[]) {
  int ctr;
     for( ctr=0; ctr < argc; ctr++ ) {
        if (!strcmp("-gamepad", argv[ctr])) {
         gamepadEnabled = 1;
        }
        if (!strcmp("-joystick", argv[ctr])) {
         joystickEnabled = 1;
        }
        if (!strcmp("-mouse", argv[ctr])) {
          mouseEnabled = 1;
        }
        if (!strcmp("-report", argv[ctr])) {
           reportingEnabled = 1;
        }
     }
  if (reportingEnabled) {printf("Mouse Enabled\n");}
  if (reportingEnabled) {printf("Gamepad Enabled\n");}
  if (reportingEnabled) {printf("Reporting Enabled\n");}

  uint32_t displayNumber = 0;

  bcm_host_init();

  DISPMANX_DISPLAY_HANDLE_T display
    = vc_dispmanx_display_open(displayNumber);
  assert(display != 0);

  DISPMANX_MODEINFO_T info;
  int result = vc_dispmanx_display_get_info(display, & info);
  assert(result == 0);

  static int layer = 100000;

  IMAGE_LAYER_T infoLayer;
  initImageLayer( & infoLayer, info.width, info.height, VC_IMAGE_RGBA16);
  createResourceImageLayer( & infoLayer, layer);

  IMAGE_LAYER_T batteryLayer;
  initImageLayer( & batteryLayer,
    31, // battery image width
    15, // battery image height
    VC_IMAGE_RGBA16);
  createResourceImageLayer( & batteryLayer, layer);

  IMAGE_LAYER_T brightnessLayer;
  initImageLayer( & brightnessLayer, info.width, info.height, VC_IMAGE_RGBA16);
  createResourceImageLayer( & brightnessLayer, layer);

  IMAGE_LAYER_T muteLayer;
  initImageLayer( & muteLayer,
    15, // battery image width
    15, // battery image height
    VC_IMAGE_RGBA16);
  createResourceImageLayer( & muteLayer, layer);

  DISPMANX_UPDATE_HANDLE_T update = vc_dispmanx_update_start(0);
  assert(update != 0);
  addElementImageLayerOffset( & infoLayer, 0, 0, display, update);
  int xOffset = info.width - 31;
  int yOffset = 0;
  addElementImageLayerOffset( & batteryLayer, xOffset, yOffset, display, update);
  addElementImageLayerOffset( & brightnessLayer, 0, 0, display, update);
  xOffset = info.width - 46;
  addElementImageLayerOffset( & muteLayer, xOffset, yOffset, display, update);

  result = vc_dispmanx_update_submit_sync(update);
  assert(result == 0);

  I2CFile = openI2C(); // open I2C device
  if (ioctl(I2CFile, I2C_SLAVE, I2C_ADDRESS) < 0) { // initialize communication
    fprintf(stderr, "I2C: Failed to acquire bus access/talk to slave 0x%x\n", I2C_ADDRESS);
    return 0;
  }

  currentReading.buttons = 0;
  currentReading.axis0 = 127;
  currentReading.axis1 = 127;

  if (mouseEnabled) {
    // create uinput devices (https://www.kernel.org/doc/html/v4.16/input/uinput.html)
    struct uinput_setup usetup;  //create mouse
    virtualMouse = open("/dev/uinput", O_WRONLY | O_NONBLOCK);
    ioctl(virtualMouse, UI_SET_EVBIT, EV_KEY);
    ioctl(virtualMouse, UI_SET_KEYBIT, BTN_LEFT);
    ioctl(virtualMouse, UI_SET_KEYBIT, BTN_RIGHT);
    ioctl(virtualMouse, UI_SET_EVBIT, EV_REL);
    ioctl(virtualMouse, UI_SET_RELBIT, REL_X);
    ioctl(virtualMouse, UI_SET_RELBIT, REL_Y);
    memset( & usetup, 0, sizeof(usetup));
    usetup.id.bustype = BUS_USB;
    usetup.id.vendor = 0x1234; /* sample vendor */
    usetup.id.product = 0x5678; /* sample product */
    strcpy(usetup.name, "Example device");
    ioctl(virtualMouse, UI_DEV_SETUP, & usetup);
    ioctl(virtualMouse, UI_DEV_CREATE);
  }

  if (gamepadEnabled) {
    struct uinput_user_dev uidev; // create gamepad
    virtualGamepad = open("/dev/uinput", O_WRONLY | O_NDELAY);
    memset( & uidev, 0, sizeof(uidev));
    ioctl(virtualGamepad, UI_SET_EVBIT, EV_KEY);
    ioctl(virtualGamepad, UI_SET_EVBIT, EV_REL);
    ioctl(virtualGamepad, UI_SET_KEYBIT, BTN_NORTH);
    ioctl(virtualGamepad, UI_SET_KEYBIT, BTN_SOUTH);
    ioctl(virtualGamepad, UI_SET_KEYBIT, BTN_EAST);
    ioctl(virtualGamepad, UI_SET_KEYBIT, BTN_WEST);
    ioctl(virtualGamepad, UI_SET_KEYBIT, BTN_TL);
    ioctl(virtualGamepad, UI_SET_KEYBIT, BTN_TR);
    ioctl(virtualGamepad, UI_SET_KEYBIT, BTN_SELECT);
    ioctl(virtualGamepad, UI_SET_KEYBIT, BTN_START);
    ioctl(virtualGamepad, UI_SET_KEYBIT, BTN_DPAD_UP);
    ioctl(virtualGamepad, UI_SET_KEYBIT, BTN_DPAD_DOWN);
    ioctl(virtualGamepad, UI_SET_KEYBIT, BTN_DPAD_LEFT);
    ioctl(virtualGamepad, UI_SET_KEYBIT, BTN_DPAD_RIGHT);
    ioctl(virtualGamepad, UI_SET_KEYBIT, BTN_1);
    ioctl(virtualGamepad, UI_SET_KEYBIT, BTN_2);
    if (joystickEnabled) {
      ioctl(virtualGamepad, UI_SET_EVBIT, EV_ABS);
      ioctl(virtualGamepad, UI_SET_ABSBIT, ABS_X);
      uidev.absmin[ABS_X] = 55; //center position is 127, minimum is near 50
      uidev.absmax[ABS_X] = 200; //center position is 127, maximum is near 200
      uidev.absflat[ABS_X] = 20; //this appears to be the deadzone
      //uidev.absfuzz[ABS_X] = 0; //what does this do?
      ioctl(virtualGamepad, UI_SET_ABSBIT, ABS_Y);
      uidev.absmin[ABS_Y] = 55; //center position is 127, minimum is near 50
      uidev.absmax[ABS_Y] = 200; //center position is 127, maximum is near 200
      uidev.absflat[ABS_Y] = 20; //this appears to be the deadzone
    }

    snprintf(uidev.name, UINPUT_MAX_NAME_SIZE, "PSPi Controller");
    uidev.id.bustype = BUS_USB;
    uidev.id.vendor = 1;
    uidev.id.product = 5;
    uidev.id.version = 1;
    write(virtualGamepad, & uidev, sizeof(uidev));
    if (ioctl(virtualGamepad, UI_DEV_CREATE)) {
      fprintf(stderr, "Error while creating uinput device!\n");
      exit(1);
    }
  }

  int countOSD = 0;
  uint8_t countGPIO = 0;
  uint8_t showBrightness = 0;
  while (1) {
    if (read(I2CFile, & currentReading, sizeof(I2C_Struct)) != sizeof(I2C_Struct)) { // read the atmega
      printf("Controller is not detected on the I2C bus.\n");
      sleep(1);
    } else { // everything is ok
      int xcenter = 127; // add a calibration procedure
      int ycenter = 127;

      if (mouseEnabled) {
        emit(virtualMouse, EV_REL, REL_X, (currentReading.axis0 - xcenter) / 8);
        emit(virtualMouse, EV_REL, REL_Y, (currentReading.axis1 - ycenter) / 8);
        emit(virtualMouse, EV_KEY, BTN_LEFT, BTN_SOUTH_BIT_READING);
        emit(virtualMouse, EV_KEY, BTN_RIGHT, BTN_EAST_BIT_READING);
        emit(virtualMouse, EV_SYN, SYN_REPORT, 0); // should this happen when nothing was changed? I think it has to for continuous mouse movement.
      }

      if (gamepadEnabled) {
        if (currentReading.buttons!=previousReading.buttons) { //only update if something changed since previous loop
          emit(virtualGamepad, EV_KEY, BTN_EAST, BTN_EAST_BIT_READING);
          emit(virtualGamepad, EV_KEY, BTN_SOUTH, BTN_SOUTH_BIT_READING);
          emit(virtualGamepad, EV_KEY, BTN_NORTH, BTN_NORTH_BIT_READING);
          emit(virtualGamepad, EV_KEY, BTN_WEST, BTN_WEST_BIT_READING);
          emit(virtualGamepad, EV_KEY, BTN_TL, BTN_TL_BIT_READING);
          emit(virtualGamepad, EV_KEY, BTN_TR, BTN_TR_BIT_READING);
          emit(virtualGamepad, EV_KEY, BTN_SELECT, BTN_SELECT_BIT_READING);
          emit(virtualGamepad, EV_KEY, BTN_START, BTN_START_BIT_READING);
          emit(virtualGamepad, EV_KEY, BTN_DPAD_UP, BTN_DPAD_UP_BIT_READING);
          emit(virtualGamepad, EV_KEY, BTN_DPAD_DOWN, BTN_DPAD_DOWN_BIT_READING);
          emit(virtualGamepad, EV_KEY, BTN_DPAD_LEFT, BTN_DPAD_LEFT_BIT_READING);
          emit(virtualGamepad, EV_KEY, BTN_DPAD_RIGHT, BTN_DPAD_RIGHT_BIT_READING);
          emit(virtualGamepad, EV_KEY, BTN_1, BTN_HOME_BIT_READING);
          emit(virtualGamepad, EV_KEY, BTN_2, BTN_SELECT_BIT_READING|BTN_HOME_BIT_READING); // this is the virtual Hotkey button. Select and Home trigger it
        }
        if (joystickEnabled) {
          if (currentReading.axis0!=previousReading.axis0) { //only update if something changed since previous loop
            emit(virtualGamepad, EV_ABS, ABS_X, currentReading.axis0); // should this happen when nothing was changed?
          }
          if (currentReading.axis1!=previousReading.axis1) { //only update if something changed since previous loop
            emit(virtualGamepad, EV_ABS, ABS_Y, currentReading.axis1);
          }
        }
        emit(virtualGamepad, EV_SYN, SYN_REPORT, 0);
      }

      if (BTN_TL_BIT_READING & BTN_TR_BIT_READING) {
        countOSD++;
        if (countOSD == 100) { // if trigger buttons were held for 100 cycles, enable/disable the text OSD
          textOSD = !textOSD;
          textDelay = 0;
          clearLayer( & infoLayer);
        }
      } else {
        countOSD = 0;
      }

    batteryData.rawVoltage = currentReading.voltage * 36300 / 1024 / 64;
    batteryData.amperage = (currentReading.voltage - currentReading.amperage) * 10 / 11;
    batteryData.amperage = batteryData.amperage * 36300 / 1024 / 64;
    batteryData.amperage = batteryData.amperage * (100 / SENSE_RESISTOR);

    if ((batteryData.amperage < -25) & ((batteryData.correctedVoltage < 4100)|(batteryData.isCharging == 0))) {
      batteryData.isCharging = 1;
    } else if ((batteryData.amperage < 25) & (batteryData.correctedVoltage > 4150)) {
      batteryData.isCharging = 2;
    } else if ((batteryData.amperage > 25) & (batteryData.rawVoltage < 4200)) {
      batteryData.isCharging = 0;
    }

    int temp = batteryData.rawVoltage + batteryData.amperage * BATTERY_INTERNAL_RESISTANCE / 1000;
    if (firstLoop) { //set the initial (specifically correctedVoltage) battery condition
      batteryData.correctedVoltage = temp;
      firstLoop = 0;
    }
    if (temp > batteryData.correctedVoltage + 25) {
      batteryData.correctedVoltage++;
    } //25mV of hysteresis to keep battery bar from bouncing around
    if (temp < batteryData.correctedVoltage - 25) {
      batteryData.correctedVoltage--;
    }
    batteryData.percent = 100 - (4150 - batteryData.correctedVoltage) / 8.5;
    if (batteryData.percent > 100) {
      batteryData.percent = 100;
    }
    if (batteryData.percent < 0) {
      batteryData.percent = 0;
    }

    if (!countGPIO) { // check the GPIO pin every 64 loops
      readGPIO();
      if (!(( *gpioStatus >> 0x00) & 1)){ //if the GPIO is low, enter sleep mode
        sleepMode( & infoLayer);
        clearLayer( & infoLayer);
      }
    }
    countGPIO++;
    countGPIO++;
    countGPIO++;
    countGPIO++;

    if ((previousBatteryData.percent != batteryData.percent)|(previousBatteryData.isCharging ^ batteryData.isCharging)) { //if battery % or charging status changed, update the OSD
      drawBattery(& batteryLayer); // make sure this is only done if something changes
      if (reportingEnabled) {
        printf("Updating Image (%d%%, Charging: %d, %dmV corr, %dmV raw, %dmA, Mute: %d, GPIO: %d)\n", batteryData.percent, batteryData.isCharging, batteryData.correctedVoltage, batteryData.rawVoltage, batteryData.amperage, isMute, ( *gpioStatus >> 0x00) & 1);
      }
    }

    if (STATUS_MUTE_BIT_READING ^ isMute) {
      isMute = STATUS_MUTE_BIT_READING;
      if (isMute) {
        drawMute(& muteLayer);
      } else {
        clearLayer( & muteLayer);
      }
    }

    if (textOSD) {
      textDelay++;
      if (textDelay > 50) {
        updateInfo( & infoLayer);
        textDelay = 0;
      }
    }
    if (previousReading.brightness != currentReading.brightness) {
      if (!currentReading.brightness) {
        clearLayer( & brightnessLayer); // do this to remove the other 7 squares when it cycles back to 1 square
      }
      drawBrightness( & brightnessLayer);
      showBrightness = 1;
    }
    if (showBrightness) {
      showBrightness++;
      if(showBrightness == 66) { // keep indicator on screen for 66 cycles (about 1 second)
        clearLayer( & brightnessLayer);
        showBrightness = 0;
      }
    }
    previousReading = currentReading;
    previousBatteryData = batteryData; // copy battery data to previous for use on the next loop
    usleep(15000);
    }
  }
  close(I2CFile); // close file
  ioctl(virtualMouse, UI_DEV_DESTROY);
  close(virtualMouse);
  destroyImageLayer( & infoLayer);
  destroyImageLayer( & batteryLayer);
  destroyImageLayer( & muteLayer);
  destroyImageLayer( & brightnessLayer);
  result = vc_dispmanx_display_close(display);
  assert(result == 0);
  //---------------------------------------------------------------------
  return 0;
}

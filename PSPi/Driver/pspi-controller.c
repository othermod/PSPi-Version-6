#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <linux/i2c-dev.h>
#include <sys/ioctl.h>
#include <fcntl.h>
#include <linux/input.h>
#include <linux/uinput.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>

#define I2C_ADDRESS 0x06 // add something that looks for the arduino address and use the correct commands
#define REFRESH_RATE 60 // how frequently to check buttons and analog in Hz

// Arduino Commands (One Byte)
#define UNMUTE_AUDIO 0x02
#define MUTE_AUDIO 0x03
#define FORCE_ORANGE_LED 0x04
#define UNFORCE_ORANGE_LED 0x05
#define ENTER_STARTUP_MODE 0x06
#define ENTER_ACTIVE_MODE 0x07
#define ENTER_SLEEP_MODE 0x08
// Arduino Commands (Two Bytes)
#define SET_CURRENT_BRIGHTNESS 0x09 // Byte 2 is a number between 0 and 255 that sets the PWM brightness
#define CHANGE_BACKLIGHT_VALUE_POSITION_0 0x0A // Byte 2 is a number between 0 and 255 that is stored as the PWM brightnes for the 8 button pushes (this persists after reboot)
#define CHANGE_BACKLIGHT_VALUE_POSITION_1 0x0B
#define CHANGE_BACKLIGHT_VALUE_POSITION_2 0x0C
#define CHANGE_BACKLIGHT_VALUE_POSITION_3 0x0D
#define CHANGE_BACKLIGHT_VALUE_POSITION_4 0x0E
#define CHANGE_BACKLIGHT_VALUE_POSITION_5 0x0F
#define CHANGE_BACKLIGHT_VALUE_POSITION_6 0x10
#define CHANGE_BACKLIGHT_VALUE_POSITION_7 0x11

// Charge Detection Settings
#define SENSE_RESISTOR 100 // resistance in milliohms

const int sleepTime = 1000000 / REFRESH_RATE;
const int magicNumber = 17; // Number that corrects for internal resistance on LiPo battery
const int rolling = 64; // Number of readings being averaged together. This has to match the atmega variable
bool isCharging = 0;
bool previousIsCharging = 0;
bool isMute = 0;
bool previousIsMute = 0;
bool joystickEnabled = 1;
bool loggingEnabled = 1;
int chargeStatus = 11;
int previousChargeStatus = 0;
int indicationVoltage = 0;
int rollingVoltage = 0;
int amperageDifference = 0;
int calculatedVoltage = 0;
uint16_t rawVolt;
uint16_t rawAmp;

int digitalRead(int pin) {
  FILE * fd;
  char fName[128];
  char val[2];
  // Open pin value file
  sprintf(fName, "/sys/class/gpio/gpio%d/value", pin);
  if ((fd = fopen(fName, "r")) == NULL) {
    printf("Error: can't open pin value\n");
    return false;
  }
  fgets(val, 2, fd);
  fclose(fd);
  return atoi(val);
}

void enterSleepMode(int gpio, int file, int resolution) {
  //printf("Sleep Mode\n");
  char temp[512];
  system("sudo killall pngview 2> /dev/null");
  printf("Displaying Image\n");
  sprintf(temp, "/home/pi/PSPi/Driver/./pngview -n -b 0 -l 100000 sleep%d.png &", resolution);
  system((char * ) temp);
  //system("sudo rfkill block wifi");
  //system("sudo rfkill block bluetooth");
  //system("sudo killall -TSTP retroarch 2>/dev/null");
  //system("sudo killall -TSTP emulationstatio 2>/dev/null");

  printf("Wait for 1 second\n");
  sleep(1);
  printf("Entering Sleep 0x08\n");
  char buf[2] = {
    0x08
  }; //sleep mode
  if (write(file, buf, 2) != 2) {
    /* ERROR HANDLING: i2c transaction failed */
    printf("Failed to write to the i2c bus.\n");
  }
  sleep(1);
  //system("sudo killall pngview 2> /dev/null");
  printf("Holding while GPIO is low\n");
  while (!digitalRead(gpio)) { //stay in this loop while the hold switch is down
    printf("GPIO is %d\n", digitalRead(gpio));
    sleep(2);
  }
  printf("GPIO is %d\n", digitalRead(gpio));
}

void exitSleepMode(int file) {
  //system("sudo killall -CONT retroarch 2>/dev/null");
  //system("sudo killall -CONT emulationstatio 2>/dev/null");
  //system("sudo rfkill unblock wifi");
  //system("sudo rfkill unblock bluetooth");
  printf("Exiting Sleep 0x07\n");
  char buf[2] = {
    0x07
  }; //enable arduino
  if (write(file, buf, 2) != 2) {
    /* ERROR HANDLING: i2c transaction failed */
    printf("Failed to write to the i2c bus.\n");
  }
  isCharging = 0; //reset battery status, so it recalculates
  previousIsCharging = 0;
  previousIsMute = 0;
  chargeStatus = 11;
  previousChargeStatus = 0;
  indicationVoltage = 0;
  rollingVoltage = 0;
  amperageDifference = 0;
  calculatedVoltage = 0;
}

int readResolution() {
  FILE * f = fopen("pspi.cfg", "r"); // stores horizontal resolution to variable so this works with both LCD types
  char buf[4];
  for (int i = 0; i != 0; i++) {
    fgets(buf, 4, f);
  }
  int result;
  fscanf(f, "%d", & result); // would be better to grab it directly, but I'll have to work out the method
  return result;
}

int openI2C() {
  int file;
  char * filename = "/dev/i2c-1"; //specify which I2C bus to use
  //char filename[2048]; //this was the old method
  //sprintf(filename, "/dev/i2c-1");
  if ((file = open(filename, O_RDWR)) < 0) {
    fprintf(stderr, "Failed to open the i2c bus"); /* ERROR HANDLING: you can check errno to see what went wrong */
    exit(1);
  }
  return file;
}

int readI2CSlave(int file, int slaveAddress, void * buf, size_t count) {
  if (ioctl(file, I2C_SLAVE, slaveAddress) < 0) { // initialize communication
    fprintf(stderr, "I2C: Failed to acquire bus access/talk to slave 0x%x\n", slaveAddress);
    return 0;
  }
  int s = 0;
  s = read(file, buf, count);
  return s; // no error
}

int createUInputDevice() {
  int fd;
  fd = open("/dev/uinput", O_WRONLY | O_NDELAY);
  if (fd < 0) {
    fprintf(stderr, "Can't open uinput device!\n");
    exit(1);
  }
  // device structure
  struct uinput_user_dev uidev;
  memset( & uidev, 0, sizeof(uidev));
  // init event
  int ret = 0;
  ret |= ioctl(fd, UI_SET_EVBIT, EV_KEY);
  ret |= ioctl(fd, UI_SET_EVBIT, EV_REL);
  // button
  ret |= ioctl(fd, UI_SET_KEYBIT, BTN_NORTH);
  ret |= ioctl(fd, UI_SET_KEYBIT, BTN_SOUTH);
  ret |= ioctl(fd, UI_SET_KEYBIT, BTN_EAST);
  ret |= ioctl(fd, UI_SET_KEYBIT, BTN_WEST);
  ret |= ioctl(fd, UI_SET_KEYBIT, BTN_TL);
  ret |= ioctl(fd, UI_SET_KEYBIT, BTN_TR);
  ret |= ioctl(fd, UI_SET_KEYBIT, BTN_SELECT);
  ret |= ioctl(fd, UI_SET_KEYBIT, BTN_START);
  ret |= ioctl(fd, UI_SET_KEYBIT, BTN_DPAD_UP);
  ret |= ioctl(fd, UI_SET_KEYBIT, BTN_DPAD_DOWN);
  ret |= ioctl(fd, UI_SET_KEYBIT, BTN_DPAD_LEFT);
  ret |= ioctl(fd, UI_SET_KEYBIT, BTN_DPAD_RIGHT);
  ret |= ioctl(fd, UI_SET_KEYBIT, BTN_1);
  //ret |= ioctl(fd, UI_SET_KEYBIT, BTN_2);
  //ret |= ioctl(fd, UI_SET_KEYBIT, BTN_3);
  //ret |= ioctl(fd, UI_SET_KEYBIT, BTN_4);
  // axis
  if (joystickEnabled) {
    ret |= ioctl(fd, UI_SET_EVBIT, EV_ABS);
    ret |= ioctl(fd, UI_SET_ABSBIT, ABS_X);
    uidev.absmin[ABS_X] = 55; //center position is 127, minimum is near 50
    uidev.absmax[ABS_X] = 200; //center position is 127, maximum is near 200
    uidev.absflat[ABS_X] = 20; //this appears to be the deadzone
    //uidev.absfuzz[ABS_X] = 0; //what does this do?
    ret |= ioctl(fd, UI_SET_ABSBIT, ABS_Y);
    uidev.absmin[ABS_Y] = 55; //center position is 127, minimum is near 50
    uidev.absmax[ABS_Y] = 200; //center position is 127, maximum is near 200
    uidev.absflat[ABS_Y] = 20; //this appears to be the deadzone
  }
  //uidev.absfuzz[ABS_Y] = 0; //what does this do?
  if (ret) {
    fprintf(stderr, "Error while configuring uinput device!\n");
    exit(1);
  }
  snprintf(uidev.name, UINPUT_MAX_NAME_SIZE, "PSPi Controller");
  uidev.id.bustype = BUS_USB;
  uidev.id.vendor = 1;
  uidev.id.product = 5;
  uidev.id.version = 1;
  ret = write(fd, & uidev, sizeof(uidev));
  if (ioctl(fd, UI_DEV_CREATE)) {
    fprintf(stderr, "Error while creating uinput device!\n");
    exit(1);
  }
  return fd;
}

void sendInputEvent(int fd, uint16_t type, uint16_t code, int32_t value) {
  struct input_event ev;
  memset( & ev, 0, sizeof(ev));
  ev.type = type;
  ev.code = code;
  ev.value = value;
  if (write(fd, & ev, sizeof(ev)) < 0) {
    fprintf(stderr, "Error while sending event to uinput device!\n");
  }
  // need to send a sync event
  ev.type = EV_SYN;
  ev.code = SYN_REPORT;
  ev.value = 0;
  write(fd, & ev, sizeof(ev));
  if (write(fd, & ev, sizeof(ev)) < 0) {
    fprintf(stderr, "Error while sending event to uinput device!\n");
  }
}

typedef struct {
  uint16_t buttons; // button status
  uint8_t axis0; // first axis
  uint8_t axis1; // second axis
  uint16_t voltage; // raw voltage
  uint16_t amperage; // raw amperage
}
I2CJoystickStatus;

int readI2CJoystick(int file, I2CJoystickStatus * status) {
  int s = readI2CSlave(file, I2C_ADDRESS, status, sizeof(I2CJoystickStatus));
  if (s != sizeof(I2CJoystickStatus))
    return -1; // error
  return 0; // no error
}

#define TestBitAndSendKeyEvent(oldValue, newValue, bit, event) if ((oldValue & (1 << bit)) != (newValue & (1 << bit))) sendInputEvent(UInputFIle, EV_KEY, event, (newValue & (1 << bit)) == 0 ? 0 : 1);

void updateButtons(int UInputFIle, I2CJoystickStatus * newStatus, I2CJoystickStatus * status) {
  // update button event
  TestBitAndSendKeyEvent(status -> buttons, newStatus -> buttons, 0x00, BTN_EAST);
  TestBitAndSendKeyEvent(status -> buttons, newStatus -> buttons, 0x01, BTN_SOUTH);
  TestBitAndSendKeyEvent(status -> buttons, newStatus -> buttons, 0x02, BTN_NORTH);
  TestBitAndSendKeyEvent(status -> buttons, newStatus -> buttons, 0x03, BTN_WEST);
  TestBitAndSendKeyEvent(status -> buttons, newStatus -> buttons, 0x04, BTN_TL);
  TestBitAndSendKeyEvent(status -> buttons, newStatus -> buttons, 0x05, BTN_TR);
  TestBitAndSendKeyEvent(status -> buttons, newStatus -> buttons, 0x06, BTN_SELECT);
  TestBitAndSendKeyEvent(status -> buttons, newStatus -> buttons, 0x07, BTN_START);
  TestBitAndSendKeyEvent(status -> buttons, newStatus -> buttons, 0x08, BTN_DPAD_UP);
  TestBitAndSendKeyEvent(status -> buttons, newStatus -> buttons, 0x09, BTN_DPAD_DOWN);
  TestBitAndSendKeyEvent(status -> buttons, newStatus -> buttons, 0x0A, BTN_DPAD_LEFT);
  TestBitAndSendKeyEvent(status -> buttons, newStatus -> buttons, 0x0B, BTN_DPAD_RIGHT);
  TestBitAndSendKeyEvent(status -> buttons, newStatus -> buttons, 0x0C, BTN_1);
  //TestBitAndSendKeyEvent(status->buttons, newStatus->buttons, 0x0D, BTN_2);
  //TestBitAndSendKeyEvent(status->buttons, newStatus->buttons, 0x0E, BTN_3);
  //TestBitAndSendKeyEvent(status->buttons, newStatus->buttons, 0x0F, BTN_4);
  if (joystickEnabled) {
    uint8_t joystickValue = newStatus -> axis0;
    if (joystickValue != status -> axis0) {
      sendInputEvent(UInputFIle, EV_ABS, ABS_X, joystickValue);
    }
    joystickValue = newStatus -> axis1;
    if (joystickValue != status -> axis1) {
      sendInputEvent(UInputFIle, EV_ABS, ABS_Y, joystickValue);
    }
  }
}

void startLog() {
  FILE * fp;
  fp = fopen("log.csv", "w");
  fprintf(fp, "rollingVoltage,amperageDifference,calculatedVoltage,indicationVoltage\n");
  fclose(fp);
}

void writeLog() {
  FILE * fp;
  fp = fopen("log.csv", "a");
  fprintf(fp, "%d,%d,%d,%d,%d\n", rollingVoltage, amperageDifference, calculatedVoltage, indicationVoltage);
  fclose(fp);
}

void calculateBattery(int position) {
  // a lot of this math is just converting the raw values to readable voltage
  // test efficiency to see whether it is worth working with raw values instead
  rollingVoltage = rawVolt * 11 * 3300 / 1024 / rolling;
  amperageDifference = (rawVolt - rawAmp) * 10 / 11;
  calculatedVoltage = rollingVoltage + amperageDifference * 10 / magicNumber;
  previousIsCharging = isCharging;
  if (indicationVoltage == 0) {
    indicationVoltage = calculatedVoltage;
  }
  if (isCharging == 0) {
    if (calculatedVoltage < indicationVoltage) {
      indicationVoltage--;
    }
    if (amperageDifference < -25 || rollingVoltage > 4200) {
      isCharging = 1;
    }
  } else {
    if (calculatedVoltage > indicationVoltage) {
      indicationVoltage++;
    }
    if (amperageDifference > 25) {
      isCharging = 0;
    }
  }
  previousChargeStatus = chargeStatus;
  chargeStatus = 0;
  if (indicationVoltage > 3478) {
    chargeStatus = 1;
  }
  if (indicationVoltage > 3549) {
    chargeStatus = 2;
  }
  if (indicationVoltage > 3619) {
    chargeStatus = 3;
  }
  if (indicationVoltage > 3655) {
    chargeStatus = 4;
  }
  if (indicationVoltage > 3725) {
    chargeStatus = 5;
  }
  if (indicationVoltage > 3761) {
    chargeStatus = 6;
  }
  if (indicationVoltage > 3866) {
    chargeStatus = 7;
  }
  if (indicationVoltage > 3927) {
    chargeStatus = 8;
  }
  if (indicationVoltage > 4027) {
    chargeStatus = 9;
  }
  if (indicationVoltage > 4175) {
    chargeStatus = 99;
  }
  if ((previousChargeStatus != chargeStatus) || (previousIsCharging != isCharging) || (previousIsMute != isMute)) { // Change Battery Status
    char temp[512];
    system("sudo killall pngview 2>/dev/null");
    sprintf(temp, "/home/pi/PSPi/Driver/./pngview -n -b 0 -l 100000 -x %d -y 2 /home/pi/PSPi/Driver/PNG/battery%d%d%d.png &", position - 46, isMute, isCharging, chargeStatus);
    system((char * ) temp);
  }
}

void sendCommandToArduino(int file, uint8_t command, uint8_t data) {
  uint8_t buf[] = {
    command,
    data
  };
  if (write(file, buf, 2) != 2) {
    /* ERROR HANDLING: i2c transaction failed */
    printf("Failed to write to the i2c bus.\n");
  }
}

int main(int argc, char * argv[]) {
  int I2CFile = openI2C(); // open I2C device
  I2CJoystickStatus status; // current joystick status
  status.buttons = 0;
  status.axis0 = 127;
  status.axis1 = 127;
  if (argc >= 2) {
    printf("\n----Following Are The Command Line Arguments Passed----");
    for (uint8_t counter = 1; counter < argc; counter++)
      printf("\nargv[%d]: %s", counter, argv[counter]);
    if (argv[counter] = "jsoff") {
      printf("Joystick disabled\n");
      joystickEnabled = 0;
    }
    if (argv[counter] = "logoff") {
      printf("Logging disabled\n");
      loggingEnabled = 0;
    }
  }

  int UInputFIle = createUInputDevice(); // create uinput device
  printf("PSPi Controller Starting\n");
  I2CJoystickStatus newStatus;
  if (readI2CJoystick(I2CFile, & newStatus) != 0) { // check for I2C connection
    printf("Controller is not detected on the I2C bus.\n");
    sleep(1);
  }
  sleep(1);
  int resolution = readResolution();
  system("echo 11 > /sys/class/gpio/export"); //export gpio 11
  if (loggingEnabled) {
    startLog();
  }
  int count = 0;
  //sendCommandToArduino(I2CFile,ENTER_ACTIVE_MODE,0);  //not needed now, atmega goes into idle and active modes on its own now
  while (1) {
    I2CJoystickStatus newStatus; // read new status from I2C
    if (readI2CJoystick(I2CFile, & newStatus) != 0) {
      printf("Controller is not detected on the I2C bus.\n");
      sleep(1);
    } else { // everything is ok
      updateButtons(UInputFIle, & newStatus, & status);
      status = newStatus;
    }
    rawVolt = status.voltage;
    rawAmp = status.amperage;
    previousIsMute = isMute;
    isMute = (status.buttons >> 0x0F) & 1;
    calculateBattery(resolution);
    count++;
    if (count == 60) {
      count = 0;
      if (loggingEnabled) {
        writeLog();
      }
      if (!digitalRead(11)) { //read gpio 11
        enterSleepMode(11, I2CFile, resolution); // gpio 11
        exitSleepMode(I2CFile);
      }
    }
    usleep(sleepTime);
  }
  close(I2CFile); // close file
  ioctl(UInputFIle, UI_DEV_DESTROY);
}

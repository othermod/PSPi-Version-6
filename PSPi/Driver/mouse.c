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

#define I2C_ADDRESS 0x06

typedef struct {
  uint16_t buttons; // button currentReading
  uint8_t axis0; // first axis
  uint8_t axis1; // second axis
  uint16_t voltage; // raw voltage
  uint16_t amperage; // raw amperage
}
I2CJoystickStatus;

int openI2C() {
  int file;
  char * filename = "/dev/i2c-1"; //specify which I2C bus to use
  if ((file = open(filename, O_RDWR)) < 0) {
    fprintf(stderr, "Failed to open the i2c bus"); /* ERROR HANDLING: you can check errno to see what went wrong */
    exit(1);
  }
  return file;
}

void emit(int virtualMouse, int type, int code, int val)
{
   struct input_event ie;
   ie.type = type;
   ie.code = code;
   ie.value = val;
   /* timestamp values below are ignored */
   ie.time.tv_sec = 0;
   ie.time.tv_usec = 0;
   write(virtualMouse, &ie, sizeof(ie));
}

int main(int argc, char * argv[]) {
  int I2CFile = openI2C(); // open I2C device
  if (ioctl(I2CFile, I2C_SLAVE, I2C_ADDRESS) < 0) { // initialize communication
    fprintf(stderr, "I2C: Failed to acquire bus access/talk to slave 0x%x\n", I2C_ADDRESS);
    return 0;
  }

  I2CJoystickStatus currentReading; // create I2C data struct
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

  while (1) {
    if (read(I2CFile, &currentReading, sizeof(I2CJoystickStatus)) != sizeof(I2CJoystickStatus)) { // read the atmega
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
    }
    usleep(15000);
  }
  close(I2CFile); // close file
  ioctl(virtualMouse, UI_DEV_DESTROY);
   close(virtualMouse);
}

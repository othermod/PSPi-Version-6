#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/i2c-dev.h>
#include <linux/input.h>
#include <linux/uinput.h>

#define I2C_ADDRESS 0x10
#define AXIS_DEADZONE_LOW 107
#define AXIS_DEADZONE_HIGH 147
#define AXIS_CENTER 127

typedef struct {
    uint8_t buttonA;
    uint8_t buttonB;
    uint8_t SENSE_SYS;
    uint8_t SENSE_BAT;
    uint8_t STATUS; // 5 bits for brightness level (can use 3 bits because there are only 8 levels), 1 for mute status, 1 for power switch, 1 for hold switch
    uint8_t axis0;
    uint8_t axis1;
    uint8_t JOY_RX;
    uint8_t JOY_RY;
} I2CJoystickStatus;

int openI2C() {
    int file;
    const char * filename = "/dev/i2c-1";
    if ((file = open(filename, O_RDWR)) < 0) {
        fprintf(stderr, "Failed to open the i2c bus.\n");
        exit(1);
    }
    return file;
}

void emit(int virtualMouse, int type, int code, int val) {
    struct input_event ie = {0};
    ie.type = type;
    ie.code = code;
    ie.value = val;
    write(virtualMouse, &ie, sizeof(ie));
}

int main(int argc, char * argv[]) {
    int I2CFile = openI2C(); // open I2C device
    if (ioctl(I2CFile, I2C_SLAVE, I2C_ADDRESS) < 0) {
        fprintf(stderr, "I2C: Failed to acquire bus access or communicate with slave 0x%x\n", I2C_ADDRESS);
        return 0;
    }

    I2CJoystickStatus currentReading = {0, 0, 0, 0, 0, AXIS_CENTER, AXIS_CENTER, 0, 0};

    int virtualMouse = open("/dev/uinput", O_WRONLY | O_NONBLOCK);
    ioctl(virtualMouse, UI_SET_EVBIT, EV_KEY);
    ioctl(virtualMouse, UI_SET_KEYBIT, BTN_LEFT);
    ioctl(virtualMouse, UI_SET_KEYBIT, BTN_RIGHT);
    ioctl(virtualMouse, UI_SET_EVBIT, EV_REL);
    ioctl(virtualMouse, UI_SET_RELBIT, REL_X);
    ioctl(virtualMouse, UI_SET_RELBIT, REL_Y);

    struct uinput_setup usetup = {0};
    usetup.id.bustype = BUS_USB;
    usetup.id.vendor = 0x1234;
    usetup.id.product = 0x5678;
    strcpy(usetup.name, "Example device");

    ioctl(virtualMouse, UI_DEV_SETUP, &usetup);
    ioctl(virtualMouse, UI_DEV_CREATE);
    sleep(1);

    while (1) {
        if (read(I2CFile, &currentReading, sizeof(I2CJoystickStatus)) != sizeof(I2CJoystickStatus)) {
            printf("Controller is not detected on the I2C bus.\n");
            sleep(1);
        } else {
            emit(virtualMouse, EV_REL, REL_X, (currentReading.axis0 - AXIS_CENTER) / 16);
            emit(virtualMouse, EV_REL, REL_Y, (currentReading.axis1 - AXIS_CENTER) / 16);
            emit(virtualMouse, EV_KEY, BTN_LEFT, ((currentReading.buttonA >> 0x03) & 1));
            emit(virtualMouse, EV_KEY, BTN_RIGHT, ((currentReading.buttonA >> 0x06) & 1));
            emit(virtualMouse, EV_SYN, SYN_REPORT, 0);
        }
        usleep(15000);
    }

    close(I2CFile);
    ioctl(virtualMouse, UI_DEV_DESTROY);
    close(virtualMouse);
    return 0;
}

#include <fcntl.h>
#include <linux/i2c-dev.h>
#include <linux/uinput.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <stdint.h>

#define I2C_FILE_NAME "/dev/i2c-1"
#define I2C_ADDR 0x10
#define UINPUT_FILE_NAME "/dev/uinput"

struct uinput_user_dev uidev;
struct input_event     ev;

int main() {
    int i2c_file, uinput_file;
    __s32 value;
    uint8_t data[8];

    // Open the I2C device file
    if ((i2c_file = open(I2C_FILE_NAME, O_RDWR)) < 0) {
        perror("Failed to open the i2c bus");
        return 1;
    }

    if (ioctl(i2c_file, I2C_SLAVE, I2C_ADDR) < 0) {
        perror("Failed to access the i2c device");
        return 1;
    }

    // Open the uinput device file
    if ((uinput_file = open(UINPUT_FILE_NAME, O_WRONLY | O_NONBLOCK)) < 0) {
        perror("Failed to open uinput device");
        return 1;
    }

    memset(&uidev, 0, sizeof(uidev));
    snprintf(uidev.name, UINPUT_MAX_NAME_SIZE, "uinput-sample");
    uidev.id.bustype = BUS_USB;
    uidev.id.vendor  = 0x1;
    uidev.id.product = 0x1;
    uidev.id.version = 1;

    ioctl(uinput_file, UI_SET_EVBIT, EV_KEY);
    ioctl(uinput_file, UI_SET_EVBIT, EV_ABS);

    // Setup gamepad buttons
    for (int i = 0; i < 16; i++) {
        ioctl(uinput_file, UI_SET_KEYBIT, BTN_TRIGGER_HAPPY1 + i);
    }

    // Setup gamepad axes
    ioctl(uinput_file, UI_SET_ABSBIT, ABS_X);
    ioctl(uinput_file, UI_SET_ABSBIT, ABS_Y);
    uidev.absmin[ABS_X] = 0;
    uidev.absmax[ABS_X] = 255;
    uidev.absflat[ABS_X] = 20; // deadzone
    uidev.absfuzz[ABS_X] = 20; // hysteresis
    uidev.absmin[ABS_Y] = 0;
    uidev.absmax[ABS_Y] = 255;
    uidev.absflat[ABS_Y] = 20; // deadzone
    uidev.absfuzz[ABS_Y] = 20; // hysteresis

    write(uinput_file, &uidev, sizeof(uidev));
    if (ioctl(uinput_file, UI_DEV_CREATE)) {
        perror("Failed to create uinput device");
        return 1;
    }

    while (1) {
        if (read(i2c_file, data, 8) != 8) {
            perror("Failed to read from the i2c bus");
            return 1;
        }

        // Update gamepad buttons
        for (int i = 0; i < 16; i++) {
            memset(&ev, 0, sizeof(struct input_event));
            ev.type = EV_KEY;
            ev.code = BTN_TRIGGER_HAPPY1 + i;
            ev.value = !(data[i/8] & (1 << (i%8)));
            write(uinput_file, &ev, sizeof(struct input_event));
        }

        // Update gamepad axes
        for (int i = 0; i < 2; i++) {
            memset(&ev, 0, sizeof(struct input_event));
            ev.type = EV_ABS;
            ev.code = i == 0 ? ABS_X : ABS_Y;
            ev.value = data[2 + i];
            write(uinput_file, &ev, sizeof(struct input_event));
        }

        // Synchronize
        memset(&ev, 0, sizeof(struct input_event));
        ev.type = EV_SYN;
        ev.code = SYN_REPORT;
        ev.value = 0;
        write(uinput_file, &ev, sizeof(struct input_event));

        usleep(10000); // 10 ms delay
    }

    ioctl(uinput_file, UI_DEV_DESTROY);
    close(uinput_file);
    close(i2c_file);

    return 0;
}

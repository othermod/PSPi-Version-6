#include <linux/uinput.h>
#include <linux/i2c-dev.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>
#include <stdio.h>
#include <stdint.h>

#define I2C_DEV_PATH "/dev/i2c-1"
#define UINPUT_DEV_PATH "/dev/uinput"

struct uinput_user_dev uidev;
int fd_i2c, fd_uinput;
uint8_t previous_buttons[2] = {0, 0};
uint8_t previous_axes[2] = {0, 0};

void initialize_gamepad() {
    int i;

    fd_uinput = open(UINPUT_DEV_PATH, O_WRONLY | O_NONBLOCK);
    ioctl(fd_uinput, UI_SET_EVBIT, EV_KEY);
    ioctl(fd_uinput, UI_SET_EVBIT, EV_ABS);

    for (i = 0; i < 16; i++)
        ioctl(fd_uinput, UI_SET_KEYBIT, BTN_TRIGGER_HAPPY1 + i);

    ioctl(fd_uinput, UI_SET_ABSBIT, ABS_X);
    ioctl(fd_uinput, UI_SET_ABSBIT, ABS_Y);

    memset(&uidev, 0, sizeof(uidev));
    snprintf(uidev.name, UINPUT_MAX_NAME_SIZE, "PSPi-Controller");
    uidev.id.bustype = BUS_USB;
    uidev.id.vendor  = 0x1;
    uidev.id.product = 0x1;
    uidev.id.version = 1;

    uidev.absmin[ABS_X] = 30;
    uidev.absmax[ABS_X] = 225;
    uidev.absflat[ABS_X] = 20; // deadzone
    uidev.absfuzz[ABS_X] = 20; // hysteresis
    uidev.absmin[ABS_Y] = 30;
    uidev.absmax[ABS_Y] = 225;
    uidev.absflat[ABS_Y] = 20; // deadzone
    uidev.absfuzz[ABS_Y] = 20; // hysteresis

    write(fd_uinput, &uidev, sizeof(uidev));
    ioctl(fd_uinput, UI_DEV_CREATE);
}

void initialize_i2c() {
    fd_i2c = open(I2C_DEV_PATH, O_RDWR);
    ioctl(fd_i2c, I2C_SLAVE, 0x10);
}

void update_gamepad() {
    struct input_event ev;
    uint8_t buffer[8];
    int i;

    read(fd_i2c, buffer, 8);

    for (i = 0; i < 16; i++) {
        if(((buffer[i / 8] >> (i % 8)) & 1) != ((previous_buttons[i / 8] >> (i % 8)) & 1)) {
            memset(&ev, 0, sizeof(ev));
            ev.type = EV_KEY;
            ev.code = BTN_TRIGGER_HAPPY1 + i;
            ev.value = ((buffer[i / 8] >> (i % 8)) & 1) == 0 ? 1 : 0;
            write(fd_uinput, &ev, sizeof(ev));
            previous_buttons[i / 8] ^= (1 << (i % 8));
        }
    }

    for (i = 0; i < 2; i++) {
        if(buffer[2 + i] != previous_axes[i]) {
            memset(&ev, 0, sizeof(ev));
            ev.type = EV_ABS;
            ev.code = i == 0 ? ABS_X : ABS_Y;
            ev.value = buffer[2 + i];
            write(fd_uinput, &ev, sizeof(ev));
            previous_axes[i] = buffer[2 + i];
        }
    }

    memset(&ev, 0, sizeof(ev));
    ev.type = EV_SYN;
    ev.code = SYN_REPORT;
    ev.value = 0;
    write(fd_uinput, &ev, sizeof(ev));
}

int main() {
    initialize_i2c();
    initialize_gamepad();

    while (1) {
        update_gamepad();
        usleep(16000);
    }

    return 0;
}

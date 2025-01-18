#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/input.h>
#include <linux/uinput.h>
#include <sys/mman.h>
#include <errno.h>

#include "shared.h"

#define AXIS_CENTER 127
#define AXIS_THRESHOLD_LOW 112
#define AXIS_THRESHOLD_HIGH 142

void emit(int virtualMouse, int type, int code, int val) {
    struct input_event ie = {0};
    ie.type = type;
    ie.code = code;
    ie.value = val;
    write(virtualMouse, &ie, sizeof(ie));
}

int main(int argc, char * argv[]) {
    int shm_fd;
    SharedData *shared_data;
    SharedData previous_data = {0};

    while ((shm_fd = shm_open("my_shm", O_RDONLY, 0666)) == -1) {
        if (errno == ENOENT) {
            sleep(1);
        } else {
            perror("shm_open");
            return 1;
        }
    }

    shared_data = mmap(0, sizeof(SharedData), PROT_READ, MAP_SHARED, shm_fd, 0);
    if (shared_data == MAP_FAILED) {
        perror("mmap");
        close(shm_fd);
        return 1;
    }

    int virtualMouse = open("/dev/uinput", O_WRONLY | O_NONBLOCK);
    ioctl(virtualMouse, UI_SET_EVBIT, EV_KEY);
    ioctl(virtualMouse, UI_SET_KEYBIT, KEY_BACK);
    ioctl(virtualMouse, UI_SET_KEYBIT, KEY_FORWARD);
    ioctl(virtualMouse, UI_SET_KEYBIT, KEY_LEFTMETA);
    ioctl(virtualMouse, UI_SET_KEYBIT, BTN_LEFT);
    ioctl(virtualMouse, UI_SET_KEYBIT, BTN_RIGHT);
    ioctl(virtualMouse, UI_SET_KEYBIT, KEY_LEFT);
    ioctl(virtualMouse, UI_SET_KEYBIT, KEY_RIGHT);
    ioctl(virtualMouse, UI_SET_KEYBIT, KEY_UP);
    ioctl(virtualMouse, UI_SET_KEYBIT, KEY_DOWN);
    ioctl(virtualMouse, UI_SET_KEYBIT, KEY_ENTER);
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

    bool shouldEmit = false;
    SharedData current_data;

    while (1) {
        current_data = *shared_data;

        if (previous_data.left_stick_x != current_data.left_stick_x ||
            current_data.left_stick_x > AXIS_THRESHOLD_HIGH ||
            current_data.left_stick_x < AXIS_THRESHOLD_LOW) {
            emit(virtualMouse, EV_REL, REL_X, (current_data.left_stick_x - AXIS_CENTER) / 16);
            previous_data.left_stick_x = current_data.left_stick_x;
            shouldEmit = true;
        }

        if (previous_data.left_stick_y != current_data.left_stick_y ||
            current_data.left_stick_y > AXIS_THRESHOLD_HIGH ||
            current_data.left_stick_y < AXIS_THRESHOLD_LOW) {
            emit(virtualMouse, EV_REL, REL_Y, (current_data.left_stick_y - AXIS_CENTER) / 16);
            previous_data.left_stick_y = current_data.left_stick_y;
            shouldEmit = true;
        }

        // Check if any button states have changed
        if (previous_data.buttons.raw != current_data.buttons.raw) {
            // Map buttons to keyboard/mouse events using the new union structure
            emit(virtualMouse, EV_KEY, KEY_ENTER, current_data.buttons.bits.start);
            emit(virtualMouse, EV_KEY, BTN_LEFT, current_data.buttons.bits.a);
            emit(virtualMouse, EV_KEY, BTN_RIGHT, current_data.buttons.bits.b);
            emit(virtualMouse, EV_KEY, KEY_FORWARD, current_data.buttons.bits.rshoulder);
            emit(virtualMouse, EV_KEY, KEY_BACK, current_data.buttons.bits.lshoulder);
            emit(virtualMouse, EV_KEY, KEY_LEFT, current_data.buttons.bits.dpad_left);
            emit(virtualMouse, EV_KEY, KEY_UP, current_data.buttons.bits.dpad_up);
            emit(virtualMouse, EV_KEY, KEY_DOWN, current_data.buttons.bits.dpad_down);
            emit(virtualMouse, EV_KEY, KEY_RIGHT, current_data.buttons.bits.dpad_right);
            emit(virtualMouse, EV_KEY, KEY_LEFTMETA, current_data.buttons.bits.home);

            previous_data.buttons.raw = current_data.buttons.raw;
            shouldEmit = true;
        }

        if (shouldEmit) {
            emit(virtualMouse, EV_SYN, SYN_REPORT, 0);
            shouldEmit = false;
            usleep(10000);
        } else {
            usleep(20000);
        }
    }

    ioctl(virtualMouse, UI_DEV_DESTROY);
    close(virtualMouse);
    munmap(shared_data, sizeof(SharedData));
    close(shm_fd);
    return 0;
}

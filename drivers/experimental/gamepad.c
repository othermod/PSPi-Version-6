#include <stdio.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <linux/uinput.h>
#include <string.h>

typedef struct {
    uint8_t buttonA;
    uint8_t buttonB;
    uint8_t SENSE_SYS;
    uint8_t SENSE_BAT;
    uint8_t STATUS;
    uint8_t JOY_LX;
    uint8_t JOY_LY;
    uint8_t JOY_RX;
    uint8_t JOY_RY;
} ControllerData;

int setup_uinput_device(int uinput_fd) {
    struct uinput_user_dev uidev;
    memset(&uidev, 0, sizeof(uidev));

    snprintf(uidev.name, UINPUT_MAX_NAME_SIZE, "PSPi-Controller");
    uidev.id.bustype = BUS_USB;
    uidev.id.vendor = 0x1234;
    uidev.id.product = 0x5678;
    uidev.id.version = 1;
    uidev.absmin[ABS_X] = 40;
    uidev.absmax[ABS_X] = 215;
    uidev.absflat[ABS_X] = 20;
    uidev.absfuzz[ABS_X] = 20;
    uidev.absmin[ABS_Y] = 40;
    uidev.absmax[ABS_Y] = 215;
    uidev.absflat[ABS_Y] = 20;
    uidev.absfuzz[ABS_Y] = 20;

    ssize_t ret = write(uinput_fd, &uidev, sizeof(uidev));
    if (ret < 0) {
        perror("Failed to write to uinput device in setup_uinput_device");
        return -1;
    }

    ioctl(uinput_fd, UI_SET_EVBIT, EV_KEY);
    for(int i = 0; i < 16; i++) {
        ioctl(uinput_fd, UI_SET_KEYBIT, BTN_TRIGGER_HAPPY1 + i);
    }

    ioctl(uinput_fd, UI_SET_EVBIT, EV_ABS);
    ioctl(uinput_fd, UI_SET_ABSBIT, ABS_X);
    ioctl(uinput_fd, UI_SET_ABSBIT, ABS_Y);

    return ioctl(uinput_fd, UI_DEV_CREATE);
}

void update_controller_data(ControllerData *shared_data, ControllerData *last_data, int uinput_fd) {
    struct input_event events[18];
    int event_count = 0;

    for(int i = 0; i < 8; i++) {
        if (((shared_data->buttonA >> i) & 1) != ((last_data->buttonA >> i) & 1)) {
            events[event_count].type = EV_KEY;
            events[event_count].code = BTN_TRIGGER_HAPPY1 + i;
            events[event_count].value = (shared_data->buttonA >> i) & 1;
            event_count++;
        }

        if (((shared_data->buttonB >> i) & 1) != ((last_data->buttonB >> i) & 1)) {
            events[event_count].type = EV_KEY;
            events[event_count].code = BTN_TRIGGER_HAPPY9 + i;
            events[event_count].value = (shared_data->buttonB >> i) & 1;
            event_count++;
        }
    }

    // Update joysticks
    if(shared_data->JOY_LX != last_data->JOY_LX) {
        events[event_count].type = EV_ABS;
        events[event_count].code = ABS_X;
        events[event_count].value = shared_data->JOY_LX;
        event_count++;
    }

    if(shared_data->JOY_LY != last_data->JOY_LY) {
        events[event_count].type = EV_ABS;
        events[event_count].code = ABS_Y;
        events[event_count].value = shared_data->JOY_LY;
        event_count++;
    }

    if(event_count > 0) {
        events[event_count].type = EV_SYN;
        events[event_count].code = 0;
        events[event_count].value = 0;
        event_count++;

        ssize_t ret = write(uinput_fd, events, sizeof(struct input_event) * event_count);
        if (ret < 0) {
            perror("Failed to write events in update_controller_data");
            // Handle error as appropriate
        }
    }

    memcpy(last_data, shared_data, sizeof(ControllerData));
}

int main() {
    int uinput_fd;
    ControllerData *shared_data;
    ControllerData last_data;
    memset(&last_data, 0, sizeof(ControllerData));

    int shm_fd;

    uinput_fd = open("/dev/uinput", O_WRONLY | O_NONBLOCK);
    if(uinput_fd < 0) {
        perror("Could not open uinput device");
        return 1;
    }

    if (setup_uinput_device(uinput_fd) != 0) {
        perror("Error setting up uinput device");
        return 1;
    }

    shm_fd = shm_open("my_shm", O_RDWR, 0666);
    shared_data = mmap(0, sizeof(ControllerData), PROT_READ, MAP_SHARED, shm_fd, 0);

    while(1) {
        if(memcmp(shared_data, &last_data, sizeof(ControllerData)) == 0) {
            usleep(16000);
            continue;
        }

        update_controller_data(shared_data, &last_data, uinput_fd);
        usleep(10000);
    }

    ioctl(uinput_fd, UI_DEV_DESTROY);
    close(uinput_fd);
    close(shm_fd);
    return 0;
}

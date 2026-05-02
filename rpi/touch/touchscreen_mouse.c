//https://claude.ai/chat/43f3b908-6278-4e18-b42f-5d14eb039ab8

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <linux/input.h>
#include <linux/uinput.h>
#include <sys/ioctl.h>
#include <linux/i2c-dev.h>
#include <time.h>

#define FT5206_I2C_ADDR 0x38
#define I2C_DEVICE "/dev/i2c-1"

#define TOUCH_REG_NUM_TOUCHES 0x02
#define TOUCH_REG_XH 0x03
#define TOUCH_REG_XL 0x04
#define TOUCH_REG_YH 0x05
#define TOUCH_REG_YL 0x06

#define SCREEN_WIDTH 800
#define SCREEN_HEIGHT 480

#define TOUCH_MAX_X 800
#define TOUCH_MAX_Y 480

#define TAP_THRESHOLD 10
#define TAP_TIMEOUT_MS 200
#define DRAG_THRESHOLD 5
#define LONG_PRESS_THRESHOLD 500
#define LONG_PRESS_DISTANCE 20

int i2c_fd;
int uinput_fd;

typedef struct {
    int x;
    int y;
    struct timespec timestamp;
    int is_touching;
} TouchState;

TouchState last_touch = {0, 0, {0, 0}, 0};
int is_dragging = 0;
int long_press_detected = 0;

int ft5206_read_byte(unsigned char reg) {
    unsigned char buf[1] = {reg};
    if (write(i2c_fd, buf, 1) != 1) {
        return -1;
    }

    if (read(i2c_fd, buf, 1) != 1) {
        return -1;
    }

    return buf[0];
}

int ft5206_init() {
    if ((i2c_fd = open(I2C_DEVICE, O_RDWR)) < 0) {
        perror("Failed to open I2C device");
        return -1;
    }

    if (ioctl(i2c_fd, I2C_SLAVE, FT5206_I2C_ADDR) < 0) {
        perror("Failed to set I2C address");
        close(i2c_fd);
        return -1;
    }

    // Check if the touch controller is present
    if (ft5206_read_byte(TOUCH_REG_NUM_TOUCHES) < 0) {
        fprintf(stderr, "Touch controller not detected\n");
        close(i2c_fd);
        return -1;
    }

    return 0;
}

void emit(int fd, int type, int code, int val) {
    struct input_event ie;

    ie.type = type;
    ie.code = code;
    ie.value = val;
    ie.time.tv_sec = 0;
    ie.time.tv_usec = 0;

    write(fd, &ie, sizeof(ie));
}

int uinput_init() {
    struct uinput_setup usetup;

    uinput_fd = open("/dev/uinput", O_WRONLY | O_NONBLOCK);
    if (uinput_fd < 0) {
        perror("Failed to open uinput device");
        return -1;
    }

    ioctl(uinput_fd, UI_SET_EVBIT, EV_KEY);
    ioctl(uinput_fd, UI_SET_KEYBIT, BTN_LEFT);
    ioctl(uinput_fd, UI_SET_KEYBIT, BTN_RIGHT);
    ioctl(uinput_fd, UI_SET_EVBIT, EV_ABS);
    ioctl(uinput_fd, UI_SET_ABSBIT, ABS_X);
    ioctl(uinput_fd, UI_SET_ABSBIT, ABS_Y);

    memset(&usetup, 0, sizeof(usetup));
    usetup.id.bustype = BUS_USB;
    usetup.id.vendor = 0x1234;
    usetup.id.product = 0x5678;
    strcpy(usetup.name, "FT5206 Touch Mouse");

    struct uinput_abs_setup abs_setup;
    memset(&abs_setup, 0, sizeof(abs_setup));
    abs_setup.code = ABS_X;
    abs_setup.absinfo.minimum = 0;
    abs_setup.absinfo.maximum = SCREEN_WIDTH - 1;
    abs_setup.absinfo.resolution = SCREEN_WIDTH;
    ioctl(uinput_fd, UI_ABS_SETUP, &abs_setup);

    abs_setup.code = ABS_Y;
    abs_setup.absinfo.minimum = 0;
    abs_setup.absinfo.maximum = SCREEN_HEIGHT - 1;
    abs_setup.absinfo.resolution = SCREEN_HEIGHT;
    ioctl(uinput_fd, UI_ABS_SETUP, &abs_setup);

    ioctl(uinput_fd, UI_DEV_SETUP, &usetup);
    ioctl(uinput_fd, UI_DEV_CREATE);

    return 0;
}

long time_diff_ms(struct timespec *t1, struct timespec *t2) {
    return (t2->tv_sec - t1->tv_sec) * 1000 + (t2->tv_nsec - t1->tv_nsec) / 1000000;
}

void ft5206_read_touch_and_emit() {
    int num_touches = ft5206_read_byte(TOUCH_REG_NUM_TOUCHES);
    if (num_touches < 0) {
        fprintf(stderr, "Error reading from touch controller\n");
        return;
    }
    num_touches &= 0x0F;
    
    if (num_touches > 0) {
        int base_addr = 0;
        int x = ((ft5206_read_byte(TOUCH_REG_XH + base_addr) & 0x0F) << 8) | 
                ft5206_read_byte(TOUCH_REG_XL + base_addr);
        int y = ((ft5206_read_byte(TOUCH_REG_YH + base_addr) & 0x0F) << 8) | 
                ft5206_read_byte(TOUCH_REG_YL + base_addr);
        
        if (x < 0 || y < 0) {
            fprintf(stderr, "Error reading touch coordinates\n");
            return;
        }
        
        x = x * SCREEN_WIDTH / TOUCH_MAX_X;
        y = y * SCREEN_HEIGHT / TOUCH_MAX_Y;

        x = (x < 0) ? 0 : ((x >= SCREEN_WIDTH) ? SCREEN_WIDTH - 1 : x);
        y = (y < 0) ? 0 : ((y >= SCREEN_HEIGHT) ? SCREEN_HEIGHT - 1 : y);

        emit(uinput_fd, EV_ABS, ABS_X, x);
        emit(uinput_fd, EV_ABS, ABS_Y, y);
        emit(uinput_fd, EV_SYN, SYN_REPORT, 0);

        struct timespec current_time;
        clock_gettime(CLOCK_MONOTONIC, &current_time);

        if (!last_touch.is_touching) {
            last_touch.x = x;
            last_touch.y = y;
            last_touch.timestamp = current_time;
            last_touch.is_touching = 1;
            long_press_detected = 0;
        } else {
            int dx = x - last_touch.x;
            int dy = y - last_touch.y;
            long dt = time_diff_ms(&last_touch.timestamp, &current_time);

            if (!is_dragging && !long_press_detected && (abs(dx) > DRAG_THRESHOLD || abs(dy) > DRAG_THRESHOLD)) {
                is_dragging = 1;
                emit(uinput_fd, EV_KEY, BTN_LEFT, 1);
                emit(uinput_fd, EV_SYN, SYN_REPORT, 0);
            }

            if (!is_dragging && !long_press_detected && dt > LONG_PRESS_THRESHOLD &&
                abs(dx) < LONG_PRESS_DISTANCE && abs(dy) < LONG_PRESS_DISTANCE) {
                emit(uinput_fd, EV_KEY, BTN_RIGHT, 1);
                emit(uinput_fd, EV_SYN, SYN_REPORT, 0);
                usleep(10000);
                emit(uinput_fd, EV_KEY, BTN_RIGHT, 0);
                emit(uinput_fd, EV_SYN, SYN_REPORT, 0);
                long_press_detected = 1;
            }
        }
    } else if (last_touch.is_touching) {
        struct timespec current_time;
        clock_gettime(CLOCK_MONOTONIC, &current_time);
        long dt = time_diff_ms(&last_touch.timestamp, &current_time);

        if (is_dragging) {
            emit(uinput_fd, EV_KEY, BTN_LEFT, 0);
            emit(uinput_fd, EV_SYN, SYN_REPORT, 0);
            is_dragging = 0;
        } else if (!long_press_detected && dt < TAP_TIMEOUT_MS) {
            emit(uinput_fd, EV_KEY, BTN_LEFT, 1);
            emit(uinput_fd, EV_SYN, SYN_REPORT, 0);
            usleep(10000);
            emit(uinput_fd, EV_KEY, BTN_LEFT, 0);
            emit(uinput_fd, EV_SYN, SYN_REPORT, 0);
        }

        last_touch.is_touching = 0;
        long_press_detected = 0;
    }
}

int main() {
    if (ft5206_init() < 0) {
        fprintf(stderr, "Failed to initialize touch controller. Exiting.\n");
        return 1;
    }

    printf("Touch controller initialized successfully.\n");

    if (uinput_init() < 0) {
        close(i2c_fd);
        return 1;
    }

    printf("uinput device created successfully. Starting touch event loop.\n");

    while (1) {
        ft5206_read_touch_and_emit();
        usleep(10000);  // Sleep for 10ms (100 Hz polling rate)
    }

    ioctl(uinput_fd, UI_DEV_DESTROY);
    close(uinput_fd);
    close(i2c_fd);
    return 0;
}
//compile w/ gcc -O3 gamepad.c -lasound -o gamepad
#include <linux/uinput.h>
#include <linux/i2c-dev.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <alsa/asoundlib.h>

#define I2C_DEV_PATH "/dev/i2c-1"
#define UINPUT_DEV_PATH "/dev/uinput"
#define VOL_INCREASE 1
#define VOL_DECREASE -1

struct uinput_user_dev uidev;
int fd_i2c, fd_uinput;
uint16_t previous_buttons = 65535;
uint8_t previous_axes[2] = {0, 0};

snd_mixer_t *handle;
snd_mixer_elem_t* elem;

void initialize_alsa(const char* card, const char* selem_name) {
    snd_mixer_selem_id_t *sid;

    snd_mixer_open(&handle, 0);
    snd_mixer_attach(handle, card);
    snd_mixer_selem_register(handle, NULL, NULL);
    snd_mixer_load(handle);

    snd_mixer_selem_id_alloca(&sid);
    snd_mixer_selem_id_set_index(sid, 0);
    snd_mixer_selem_id_set_name(sid, selem_name);

    elem = snd_mixer_find_selem(handle, sid);

    if (!elem) {
        fprintf(stderr, "Cannot find simple control '%s',%i\n", snd_mixer_selem_id_get_name(sid), snd_mixer_selem_id_get_index(sid));
    }
}

int change_volume(int operation, long change_value) {
    long minv, maxv, outvol;

    if (!elem) {
        fprintf(stderr, "ALSA mixer element not initialized\n");
        return -1;
    }

    snd_mixer_selem_get_playback_volume_range(elem, &minv, &maxv);
    snd_mixer_selem_get_playback_volume(elem, SND_MIXER_SCHN_MONO, &outvol);

    if (operation == VOL_INCREASE) {
        outvol += change_value;
        if (outvol > maxv) {
            outvol = maxv;
        }
    } else if (operation == VOL_DECREASE) {
        outvol -= change_value;
        if (outvol < minv) {
            outvol = minv;
        }
    } else {
        fprintf(stderr, "Invalid operation\n");
        return -1;
    }

    snd_mixer_selem_set_playback_volume_all(elem, outvol);

    return 0;
}

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

    uint16_t buttons = (buffer[1] << 8) | buffer[0]; // Combine the two bytes into a 16-bit unsigned integer

    for (i = 0; i < 16; i++) {
        if(((buttons >> i) & 1) != ((previous_buttons >> i) & 1)) {
            memset(&ev, 0, sizeof(ev));
            ev.type = EV_KEY;
            ev.code = BTN_TRIGGER_HAPPY1 + i;
            ev.value = ((buttons >> i) & 1) == 0 ? 1 : 0;
            write(fd_uinput, &ev, sizeof(ev));
            previous_buttons ^= (1 << i);

            if (i == 13 && ev.value == 0) {
                change_volume(VOL_INCREASE, 200);
            }

            if (i == 14 && ev.value == 0) {
                change_volume(VOL_DECREASE, 200);
            }
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
    initialize_alsa("default", "Headphone");

    while (1) {
        update_gamepad();
        usleep(16000);
    }

    snd_mixer_close(handle);

    return 0;
}

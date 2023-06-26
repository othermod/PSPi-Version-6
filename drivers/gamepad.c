//compile w/ gcc -O3 gamepad.c -lasound -o gamepad
#include <linux/uinput.h>
#include <linux/i2c-dev.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdbool.h>
#include <alsa/asoundlib.h>

#define I2C_DEV_PATH "/dev/i2c-1"
#define I2C_ADDRESS 0x10
#define UINPUT_DEV_PATH "/dev/uinput"

#define VOL_INCREASE 1
#define VOL_DECREASE -1

#define SENSE_RESISTOR_MILLIOHM 50 // maybe allow the Pi to change this and store in EEPROM
#define VOLTAGE 1 // voltage mode is the initial condition
#define COULOMB 0
#define RESISTOR_A_KOHM 150
#define RESISTOR_B_KOHM 10
#define BATTERY_INTERNAL_RESISTANCE_MILLIOHM 270

struct uinput_user_dev uidev;
int fd_i2c, fd_uinput;
uint16_t previous_buttons = 65535;
uint8_t previous_axes[2] = {0, 0};

uint8_t i2cBuffer[8];

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
    if (fd_uinput < 0) {
        perror("Failed to open uinput device");
        exit(1);
    }
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
    if (fd_i2c < 0) {
        perror("Failed to open the i2c bus");
        exit(1);
    }
    if (ioctl(fd_i2c, I2C_SLAVE, I2C_ADDRESS) < 0) {
        perror("Failed to acquire bus access and/or talk to slave");
        exit(1);
    }
}


void update_gamepad() {
    struct input_event ev;

    int i;

    read(fd_i2c, i2cBuffer, 8);

    uint16_t buttons = (i2cBuffer[1] << 8) | i2cBuffer[0]; // Combine the two bytes into a 16-bit unsigned integer

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
        if(i2cBuffer[2 + i] != previous_axes[i]) {
            memset(&ev, 0, sizeof(ev));
            ev.type = EV_ABS;
            ev.code = i == 0 ? ABS_X : ABS_Y;
            ev.value = i2cBuffer[2 + i];
            write(fd_uinput, &ev, sizeof(ev));
            previous_axes[i] = i2cBuffer[2 + i];
        }
    }

    memset(&ev, 0, sizeof(ev));
    ev.type = EV_SYN;
    ev.code = SYN_REPORT;
    ev.value = 0;
    write(fd_uinput, &ev, sizeof(ev));
}

typedef struct {
  bool calculationMode;
  bool isCharging;
  uint16_t voltageSYSx16;
  uint16_t voltageBATx16;
  uint16_t voltageSYS;
  uint16_t voltageBAT;
  uint16_t rawVoltage;
  uint16_t senseRVoltageDifference;
  uint16_t finalAmperage;
  uint16_t finalVoltage;
} Battery_Structure;

Battery_Structure battery;

void calculateAmperage() {
  //i2cBuffer[6]++; //the voltages are reported slightly lower than they should be, so I'm adding one to the ADC readings
  //i2cBuffer[7]++;
  //i2cBuffer[6]++; //the voltages are reported slightly lower than they should be, so I'm adding one to the ADC readings
  //i2cBuffer[7]++;
  uint16_t readVoltageSYS = i2cBuffer[6] * 3000 / 1024;
  uint16_t readVoltageBAT = i2cBuffer[7] * 3000 / 1024;
  printf("senseSYS: %d\n", i2cBuffer[6]);
  printf("senseBAT: %d\n", i2cBuffer[7]);
  printf("voltageSYS: %d\n", readVoltageSYS);
  printf("voltageBAT: %d\n", readVoltageBAT);

  // rolling average of 16 ADC readings. eliminates some noise and increases accuracy
  battery.voltageSYSx16 = battery.voltageSYSx16 - (battery.voltageSYSx16 / 16) + readVoltageSYS;
  battery.voltageBATx16 = battery.voltageBATx16 - (battery.voltageBATx16 / 16) + readVoltageBAT;
  printf("voltageSYSx16: %d\n", battery.voltageSYSx16);
  printf("voltageBATx16: %d\n", battery.voltageBATx16);
  printf("rollingaveraged: %d\n", battery.voltageSYSx16/16);
  printf("rollingaveraged: %d\n", battery.voltageBATx16/16);

  // amperage step 1 of 3
  // the amperage is measured by calculating the difference between the two voltage readings
  // the rolling averages are 16x the actual reading, so the result has to be divided by 16
  if (battery.voltageSYSx16 > battery.voltageBATx16) {
    battery.isCharging = 0;
    battery.senseRVoltageDifference = (battery.voltageSYSx16 - battery.voltageBATx16) / 16;
  } else {
    battery.isCharging = 1;
    battery.senseRVoltageDifference = (battery.voltageBATx16 - battery.voltageSYSx16) / 16;
  }
  printf("isCharging: %d\n", battery.isCharging);
  // amperage step 2 of 3
  // the amperage reading now has to be corrected because the two resistor voltage dividers skew the voltage drop reading slightly
  battery.senseRVoltageDifference = battery.senseRVoltageDifference*(RESISTOR_A_KOHM+RESISTOR_B_KOHM)/RESISTOR_A_KOHM;
  printf("senseRVoltageDifference: %d\n", battery.senseRVoltageDifference);
  // amperage step 3 of 3
  // calculate the actual amperage using the sense resistor value
  battery.finalAmperage = battery.senseRVoltageDifference*(1000 / SENSE_RESISTOR_MILLIOHM);
  printf("finalAmperage: %d\n", battery.finalAmperage); // the amperage math is tested and functioning perfectly
}

void calculateVoltage() {
  // voltage step 1 of 3
  // the resistor voltage gives us a voltage of 1/16th the actual battery, so the ADC reading must be multiplied x16 to account for this
  // the rolling average already does this, so we can use the voltage reading created from the rolling average
  battery.rawVoltage = battery.voltageSYSx16;
  // the voltage needs one more correction, which will be done after the voltage drop on the resistor is calculated
  // voltage step 2 of 3
  // add the voltage drop to the read voltage system side, which will give the actual battery voltage
  if (battery.isCharging) { // need to add or subtract depending on whether it is charging
    battery.rawVoltage = battery.rawVoltage - battery.senseRVoltageDifference;
  } else {
    battery.rawVoltage = battery.rawVoltage + battery.senseRVoltageDifference;
  }
  printf("rawVoltage: %d\n", battery.rawVoltage);
  // voltage step 3 of 3
  // the final step is to determine the actual battery voltage, because the battery has internal resistance and the voltage is affected by charging and discharging it
  // we have to estimate what the voltage would be in an idle state
  if (battery.isCharging) {
  battery.finalVoltage = battery.rawVoltage - battery.finalAmperage * BATTERY_INTERNAL_RESISTANCE_MILLIOHM / 1000;
  } else {
  battery.finalVoltage = battery.rawVoltage + battery.finalAmperage * BATTERY_INTERNAL_RESISTANCE_MILLIOHM / 1000;
  }
}

int main() {
    initialize_i2c();
    initialize_gamepad();
    initialize_alsa("default", "Headphone");
    uint8_t report = 1;

    while (1) {
      report++;
      report &= 0b00000111;
      if (!report) {
        calculateAmperage();
        calculateVoltage();
      }
        update_gamepad();
        usleep(16000);
    }

    snd_mixer_close(handle);

    return 0;
}

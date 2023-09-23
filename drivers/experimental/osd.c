/* TODO
1. The switch on the left can be used for enabling/disabling wifi, and the LED can signal when wifi is connected
2. Add volume osd indicator
3. is two-way communication possible now? would it need to be in main.c?
*/
#include <fcntl.h>
#include <unistd.h>
#include <string.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdbool.h>
#include <alsa/asoundlib.h>

#include <assert.h>
#include "imageGraphics.h"
#include "imageLayer.h"
#include <math.h>
#include "bcm_host.h"
#include <sys/mman.h>
#include <errno.h>

#define VOL_INCREASE 1
#define VOL_DECREASE -1

#define SENSE_RESISTOR_MILLIOHM 50 // maybe allow the Pi to change this and store in EEPROM
#define RESISTOR_A_KOHM 150
#define RESISTOR_B_KOHM 10
#define BATTERY_INTERNAL_RESISTANCE_MILLIOHM 250
#define DISCHARGING 0
#define CHARGING 1
#define CHARGED 2

uint8_t brightness = 0;

snd_mixer_t *handle;
snd_mixer_elem_t* elem;

void initialize_alsa(const char* card) {
    snd_mixer_open(&handle, 0);
    snd_mixer_attach(handle, card);
    snd_mixer_selem_register(handle, NULL, NULL);
    snd_mixer_load(handle);

    snd_mixer_selem_id_t *sid;
    snd_mixer_selem_id_alloca(&sid);

    elem = NULL;
    for (elem = snd_mixer_first_elem(handle); elem; elem = snd_mixer_elem_next(elem)) {
        if (snd_mixer_selem_is_active(elem)) {
            snd_mixer_selem_get_id(elem, sid);
            if (snd_mixer_selem_has_playback_volume(elem)) {
                //printf("Found active volume element: %s\n", snd_mixer_selem_id_get_name(sid));
                break;
            }
        }
    }

    if (!elem) {
        fprintf(stderr, "No suitable volume element found\n");
        snd_mixer_close(handle);
        return;
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

void update_gamepad() {
  change_volume(VOL_INCREASE, 200);
  change_volume(VOL_DECREASE, 200);
}

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

uint16_t readVoltageSYS;
uint16_t readVoltageBAT;

typedef struct {
  bool isCharging;
  uint16_t voltageSYSx16;
  uint16_t voltageBATx16;
  uint16_t voltageSYS;
  uint16_t voltageBAT;
  uint16_t rawVoltage;
  int senseRVoltageDifference;
  int finalAmperage;
  uint16_t finalVoltage;
  uint16_t indicatorVoltage;
  uint8_t chargeIndicator;
  int percent;
} Battery_Structure;

Battery_Structure battery;

void calculateAmperage() {

  battery.voltageSYSx16 = battery.voltageSYSx16 - (battery.voltageSYSx16 / 16) + readVoltageSYS;
  battery.voltageBATx16 = battery.voltageBATx16 - (battery.voltageBATx16 / 16) + readVoltageBAT;
  if (battery.voltageSYSx16 > battery.voltageBATx16) {
    battery.isCharging = 0;
  } else {
    battery.isCharging = 1;
  }
  battery.senseRVoltageDifference = (battery.voltageBATx16 - battery.voltageSYSx16) / 16;
  battery.senseRVoltageDifference = battery.senseRVoltageDifference*(RESISTOR_A_KOHM+RESISTOR_B_KOHM)/RESISTOR_A_KOHM;
  battery.finalAmperage = battery.senseRVoltageDifference*(1000 / SENSE_RESISTOR_MILLIOHM);

}

void calculateVoltage() {
  battery.rawVoltage = battery.voltageSYSx16;
  battery.rawVoltage = battery.rawVoltage - battery.senseRVoltageDifference;
  battery.finalVoltage = battery.rawVoltage - battery.finalAmperage * BATTERY_INTERNAL_RESISTANCE_MILLIOHM / 1000;
  if (battery.finalVoltage > battery.indicatorVoltage + 25) {
    battery.indicatorVoltage++;
  } else if (battery.finalVoltage < battery.indicatorVoltage - 25) {
    battery.indicatorVoltage--;
  }
}

bool isMute = 0;

// create colors ( format is: red, green, blue, opacity)
static RGBA8_T clearColor = { 0,    0,    0,    0};
static RGBA8_T green =      { 0,    255,  0,    255};
RGBA8_T red =               { 255,  0,    0,    255};
static RGBA8_T backwardRed =        { 0,  0,    255,    255};
RGBA8_T orange =     { 255,  127,  0,    255};
static RGBA8_T backwardOrange =     { 0,  127,  255,    255};
static RGBA8_T white =      { 255,  255,  255,  255};
static RGBA8_T black =      { 0,    0,    0,    255};

void drawBattery(IMAGE_LAYER_T * batteryLayer) {
  IMAGE_T * image = & (batteryLayer -> image);
  //clearImageRGB(image, & clearColor); //the image doesn't need to be erased because the same pixels are being used and colors are changing
  RGBA8_T * batteryColor;
  batteryColor = & green;
  if (battery.percent < 20) { // sets color depending on battery level
    batteryColor = & orange;
  }
  if (battery.percent < 10) {
    batteryColor = & red;
  }
  // draw the battery outline and fill with color
  imageBoxFilledRGB(image, 1, 0, 30, 14, & white);
  imageBoxFilledRGB(image, 0, 4, 2, 10, & white);
  imageBoxFilledRGB(image, 2, 1, 29, 13, & black);
  imageBoxFilledRGB(image, 1, 5, 3, 9, & black);


  imageBoxFilledRGB(image, 28 - battery.percent / 4, 2, 28, 12, batteryColor);
  if (battery.chargeIndicator) {
    RGBA8_T * boltColor;
    if (battery.chargeIndicator == CHARGED) {
      boltColor = & green;
    } else {
      boltColor = & white;
    }
    // draw the lightning bolt to show that the battery is charging
    imageBoxFilledRGB(image, 15, 3, 16, 11, boltColor);
    imageBoxFilledRGB(image, 12, 4, 14, 6, boltColor);
    imageBoxFilledRGB(image, 10, 6, 11, 8, boltColor);
    imageBoxFilledRGB(image, 7, 7, 9, 8, boltColor);
    imageBoxFilledRGB(image, 17, 8, 19, 10, boltColor);
    imageBoxFilledRGB(image, 20, 7, 21, 8, boltColor);
    imageBoxFilledRGB(image, 22, 6, 24, 7, boltColor);
    imageBoxFilledRGB(image, 14, 2, 17, 2, & black);
    imageBoxFilledRGB(image, 17, 2, 17, 7, & black);
    imageBoxFilledRGB(image, 18, 7, 19, 7, & black);
    imageBoxFilledRGB(image, 19, 6, 21, 6, & black);
    imageBoxFilledRGB(image, 21, 5, 25, 5, & black);
    imageBoxFilledRGB(image, 25, 6, 25, 7, & black);
    imageBoxFilledRGB(image, 24, 7, 24, 8, & black);
    imageBoxFilledRGB(image, 23, 8, 22, 8, & black);
    imageBoxFilledRGB(image, 22, 9, 20, 9, & black);
    imageBoxFilledRGB(image, 20, 10, 19, 10, & black);
    imageBoxFilledRGB(image, 19, 11, 17, 11, & black);
    imageBoxFilledRGB(image, 17, 12, 14, 12, & black);
    imageBoxFilledRGB(image, 14, 11, 14, 8, & black);
    imageBoxFilledRGB(image, 14, 7, 12, 7, & black);
    imageBoxFilledRGB(image, 12, 8, 10, 8, & black);
    imageBoxFilledRGB(image, 10, 9, 6, 9, & black);
    imageBoxFilledRGB(image, 6, 8, 6, 8, & black);
    imageBoxFilledRGB(image, 6, 7, 7, 7, & black);
    imageBoxFilledRGB(image, 7, 6, 9, 6, & black);
    imageBoxFilledRGB(image, 9, 5, 11, 5, & black);
    imageBoxFilledRGB(image, 11, 4, 12, 4, & black);
    imageBoxFilledRGB(image, 12, 3, 14, 3, & black);
  }
  changeSourceAndUpdateImageLayer(batteryLayer);
}

void drawMute(IMAGE_LAYER_T * muteLayer) {
  IMAGE_T * image = & (muteLayer -> image);
  // draw the battery outline and fill with color
  if (isMute) {
    imageBoxFilledRGB(image, 5, 0, 11, 14, & white);
    imageBoxFilledRGB(image, 4, 1, 4, 13, & white);
    imageBoxFilledRGB(image, 3, 2, 3, 12, & white);
    imageBoxFilledRGB(image, 2, 3, 2, 11, & white);
    imageBoxFilledRGB(image, 0, 4, 1, 10, & white);

    imageBoxFilledRGB(image, 6, 1, 10, 13, & black);
    imageBoxFilledRGB(image, 5, 2, 5, 12, & black);
    imageBoxFilledRGB(image, 4, 3, 4, 11, & black);
    imageBoxFilledRGB(image, 3, 4, 3, 10, & black);
    imageBoxFilledRGB(image, 1, 5, 2, 9, & black);

    imageBoxFilledRGB(image, 0, 0, 2, 2, & red);
    imageBoxFilledRGB(image, 2, 2, 4, 4, & red);
    imageBoxFilledRGB(image, 4, 4, 6, 6, & red);
    imageBoxFilledRGB(image, 6, 6, 8, 8, & red);
    imageBoxFilledRGB(image, 8, 8, 10, 10, & red);
    imageBoxFilledRGB(image, 10, 10, 12, 12, & red);
    imageBoxFilledRGB(image, 12, 12, 14, 14, & red);
  } else {
    clearImageRGB(image, & clearColor); // erase the whole image
  }
  changeSourceAndUpdateImageLayer(muteLayer);
}

void drawBrightness(IMAGE_LAYER_T * brightnessLayer) {
  IMAGE_T * image = & (brightnessLayer -> image);
  for (size_t i = 0; i <= brightness; i++) {
    imageBoxFilledRGB(image, 100 * i + 40, 400, 100 * i + 60, 420, & black);
    imageBoxFilledRGB(image, 100 * i + 44, 404, 100 * i + 56, 416, & white);
  }
  changeSourceAndUpdateImageLayer(brightnessLayer);
}

void clearLayer(IMAGE_LAYER_T * layer) {
  IMAGE_T * image = & (layer -> image);
  clearImageRGB(image, & clearColor);
  changeSourceAndUpdateImageLayer(layer);
}

int is_pi4() {
    FILE *cpuinfo = fopen("/proc/cpuinfo", "r");
    if (cpuinfo == NULL) {
        perror("Failed to open /proc/cpuinfo");
        exit(EXIT_FAILURE);
    }

    char line[256];
    while (fgets(line, sizeof(line), cpuinfo)) {
        if (strncmp(line, "Revision", 8) == 0) {
            char *revision = strtok(line, ":");
            revision = strtok(NULL, ":"); // this will get the value part

            if (revision) {
                // Removing any leading whitespace
                while (*revision == ' ' || *revision == '\t') {
                    ++revision;
                }

                // Here are some revision codes for Pi4/CM4
                // This is not exhaustive and may need updates if new revisions appear
                if (strstr(revision, "c031") || strstr(revision, "b031") ||
                    strstr(revision, "c03112") || strstr(revision, "d03114")) {
                    fclose(cpuinfo);
                    return 1;
                }
            }
        }
    }

    fclose(cpuinfo);
    return 0;
}

void set_all_cpus_governor(int mode) {
    const char* governor = mode ? "powersave" : "ondemand";

    for (int i = 0; i < 4; i++) {
        char path[100];
        snprintf(path, sizeof(path), "/sys/devices/system/cpu/cpu%d/cpufreq/scaling_governor", i);

        FILE* file = fopen(path, "w");
        if (file == NULL) {
            perror("Failed to open the governor file");
            exit(1);
        }

        fprintf(file, "%s", governor);
        fclose(file);
    }
}

int main() {
  //check for Pi4, and adjust color order
  if (is_pi4()) {
     red =  backwardRed;
     orange =  backwardOrange;
  }
  int shm_fd;
  ControllerData *shared_data;

  while ((shm_fd = shm_open("my_shm", O_RDONLY, 0666)) == -1) {
      if (errno == ENOENT) {
          sleep(1);
      } else {
          perror("shm_open");
          return 1;
      }
  }

  shared_data = mmap(0, sizeof(ControllerData), PROT_READ, MAP_SHARED, shm_fd, 0);
  if (shared_data == MAP_FAILED) {
      perror("mmap");
      close(shm_fd);
      return 1;
  }

  uint32_t displayNumber = 0;

  bcm_host_init();

  DISPMANX_DISPLAY_HANDLE_T display
    = vc_dispmanx_display_open(displayNumber);
  assert(display != 0);

  DISPMANX_MODEINFO_T info;
  int result = vc_dispmanx_display_get_info(display, & info);
  assert(result == 0);

  static int layer = 100000;

  IMAGE_LAYER_T batteryLayer;
  initImageLayer( & batteryLayer,
    31, // battery image width
    15, // battery image height
    VC_IMAGE_RGBA16);
  createResourceImageLayer( & batteryLayer, layer);

  IMAGE_LAYER_T brightnessLayer;
  initImageLayer( & brightnessLayer, info.width, info.height, VC_IMAGE_RGBA16);
  createResourceImageLayer( & brightnessLayer, layer);

  IMAGE_LAYER_T muteLayer;
  initImageLayer( & muteLayer,
    15, // battery image width
    15, // battery image height
    VC_IMAGE_RGBA16);
  createResourceImageLayer( & muteLayer, layer);

  DISPMANX_UPDATE_HANDLE_T update = vc_dispmanx_update_start(0);
  assert(update != 0);
  int xOffset = info.width - 31;
  int yOffset = 0;
  addElementImageLayerOffset( & batteryLayer, xOffset, yOffset, display, update);
  addElementImageLayerOffset( & brightnessLayer, 0, 0, display, update);
  xOffset = info.width - 46;
  addElementImageLayerOffset( & muteLayer, xOffset, yOffset, display, update);

  result = vc_dispmanx_update_submit_sync(update);
  assert(result == 0);
    initialize_alsa("default");
    uint8_t previousCharging = 0;
    uint8_t previousPercent = 0;
    uint8_t previousStatus = shared_data->STATUS;
    battery.indicatorVoltage = 3300;
    uint8_t showBrightness = 0;
    isMute = shared_data->STATUS & 0b10000000;
    brightness = shared_data->STATUS & 0b00000111;
    bool governor = 0;
    drawMute(& muteLayer);
    while (1) {

      //read the battery voltage from memory
      readVoltageSYS = shared_data->SENSE_SYS * 3000 / 1024;
      readVoltageBAT = shared_data->SENSE_BAT * 3000 / 1024;

      calculateAmperage();
      calculateVoltage();

        battery.percent = 100 - (4010 - battery.indicatorVoltage) / 8.5;
        if (battery.percent < 0) {
          battery.percent = 0;
        } else if (battery.percent > 100) {
          battery.percent = 100;
        }
        if (battery.finalAmperage < -60) {
          battery.chargeIndicator = DISCHARGING; }
        if (battery.finalAmperage >= 0) {
          battery.chargeIndicator = CHARGING;}
        if ((battery.indicatorVoltage > 4000) & (battery.finalAmperage > -40)) {
          battery.chargeIndicator = CHARGED;}
        if ((previousCharging != battery.chargeIndicator)|(battery.percent != previousPercent)) {
          drawBattery(& batteryLayer); // make sure this is only done if something changes
        }

        if (previousStatus != shared_data->STATUS) {
          //see whether brightness changed
          if (brightness != (shared_data->STATUS & 0b00000111)) {
            brightness = shared_data->STATUS & 0b00000111;
            //printf("%d\n", brightness);
            showBrightness = 10;
            if (brightness == 0b00000000) {
              clearLayer( & brightnessLayer); // do this to remove the other 7 squares when it cycles back to 1 square
            }
            drawBrightness( & brightnessLayer);

          }
          //see whether mute status changed
          if (isMute != (shared_data->STATUS & 0b10000000)) {
            isMute = shared_data->STATUS & 0b10000000; // maybe bitshift and make boolean
            //if (isMute){
              drawMute(& muteLayer);
            //} else {
              //clearLayer( & muteLayer);
          //  }
          }
          //see whether powersave status changed
          if (governor != (shared_data->STATUS & 0b01000000)) {
            governor = shared_data->STATUS & 0b01000000; // maybe bitshift and make boolean
              set_all_cpus_governor(governor);
          }
          previousStatus = shared_data->STATUS;
        }

        if ((shared_data->buttonB >> 5) & 1) {
          change_volume(VOL_INCREASE, 100);
        }

        if ((shared_data->buttonB >> 6) & 1) {
          change_volume(VOL_DECREASE, 100);
        }

        if (showBrightness) {
          showBrightness--;
          if (!showBrightness){
            clearLayer( & brightnessLayer);
          }
        }

        previousPercent = battery.percent;
        previousCharging = battery.chargeIndicator;
        usleep(100000);
    }

    snd_mixer_close(handle);
    destroyImageLayer( & batteryLayer);
    destroyImageLayer( & brightnessLayer);
    destroyImageLayer( & muteLayer);
    result = vc_dispmanx_display_close(display);
    assert(result == 0);
    munmap(shared_data, sizeof(ControllerData));
    close(shm_fd);

    return 0;
}

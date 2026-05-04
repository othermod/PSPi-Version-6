#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <errno.h>

#define SENSE_RESISTOR_MILLIOHM              50
#define RESISTOR_A_KOHM                      150
#define RESISTOR_B_KOHM                      10
#define BATTERY_INTERNAL_RESISTANCE_MILLIOHM 256
#define DISCHARGING 0
#define CHARGING    1
#define CHARGED     2

#define BAT_DIR   "/sys/class/power_supply/BAT0"
#define POWER_DIR "/sys/class/power_supply/BAT0/power"

// --- Shared memory layout ---------------------------------------------------

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

// --- Battery state ----------------------------------------------------------

typedef struct {
    bool     isCharging;
    uint16_t voltageSYSx16;
    uint16_t voltageBATx16;
    int      senseRVoltageDifference;
    int      finalAmperage;
    uint16_t rawVoltage;
    uint16_t finalVoltage;
    uint16_t indicatorVoltage;
    uint8_t  chargeIndicator;
    int      percent;
} Battery_Structure;

Battery_Structure battery;
uint16_t readVoltageSYS;
uint16_t readVoltageBAT;

void calculateAmperage() {
    battery.voltageSYSx16 = battery.voltageSYSx16 - (battery.voltageSYSx16 / 8) + readVoltageSYS;
    battery.voltageBATx16 = battery.voltageBATx16 - (battery.voltageBATx16 / 8) + readVoltageBAT;
    battery.isCharging = (battery.voltageSYSx16 <= battery.voltageBATx16);
    battery.senseRVoltageDifference = (battery.voltageBATx16 - battery.voltageSYSx16) / 16;
    battery.senseRVoltageDifference = battery.senseRVoltageDifference * (RESISTOR_A_KOHM + RESISTOR_B_KOHM) / RESISTOR_A_KOHM;
    battery.finalAmperage = battery.senseRVoltageDifference * (1000 / SENSE_RESISTOR_MILLIOHM);
}

void calculateVoltage() {
    battery.rawVoltage   = battery.voltageSYSx16 - battery.senseRVoltageDifference;
    battery.finalVoltage = battery.rawVoltage - battery.finalAmperage * BATTERY_INTERNAL_RESISTANCE_MILLIOHM / 1000;
    if      (battery.finalVoltage > battery.indicatorVoltage + 25) battery.indicatorVoltage++;
    else if (battery.finalVoltage < battery.indicatorVoltage - 25) battery.indicatorVoltage--;
}

void calculateBatteryStatus() {
    battery.percent = 100 - (4025 - battery.indicatorVoltage) / 7.5;
    if      (battery.percent < 0)   battery.percent = 0;
    else if (battery.percent > 100) battery.percent = 100;

    if (battery.finalAmperage < -60)  battery.chargeIndicator = DISCHARGING;
    if (battery.finalAmperage >= 0)   battery.chargeIndicator = CHARGING;
    if ((battery.indicatorVoltage > 4050) && (battery.finalAmperage > -40))
                                      battery.chargeIndicator = CHARGED;
}

// --- sysfs helpers ----------------------------------------------------------

static int write_file(const char *path, const char *value) {
    FILE *f = fopen(path, "w");
    if (!f) {
        fprintf(stderr, "Failed to open %s: %s\n", path, strerror(errno));
        return -1;
    }
    fprintf(f, "%s", value);
    fclose(f);
    return 0;
}

static int setup_sysfs() {
    if (mount("tmpfs", "/sys/class/power_supply/", "tmpfs", 0, NULL) != 0) {
        fprintf(stderr, "Failed to mount tmpfs: %s\n", strerror(errno));
        return -1;
    }

    if (mkdir(BAT_DIR,   0755) != 0 && errno != EEXIST) {
        fprintf(stderr, "Failed to create %s: %s\n", BAT_DIR,   strerror(errno)); return -1;
    }
    if (mkdir(POWER_DIR, 0755) != 0 && errno != EEXIST) {
        fprintf(stderr, "Failed to create %s: %s\n", POWER_DIR, strerror(errno)); return -1;
    }

    // Static attributes
    write_file(BAT_DIR "/type",          "Battery\n");
    write_file(BAT_DIR "/technology",    "Li-ion\n");
    write_file(BAT_DIR "/present",       "1\n");
    write_file(BAT_DIR "/capacity_level","Normal\n");
    write_file(BAT_DIR "/charge_full",   "1000000\n");

    return 0;
}

static void update_sysfs() {
    char buf[32];

    const char *status = (battery.chargeIndicator == CHARGING ||
                          battery.chargeIndicator == CHARGED)
                         ? "Charging\n" : "Discharging\n";
    const char *online = (battery.chargeIndicator == CHARGING ||
                          battery.chargeIndicator == CHARGED)
                         ? "1\n" : "0\n";

    snprintf(buf, sizeof(buf), "%d\n", battery.percent * 10000);
    write_file(BAT_DIR "/charge_now", buf);

    snprintf(buf, sizeof(buf), "%d\n", battery.percent);
    write_file(BAT_DIR "/capacity", buf);

    write_file(BAT_DIR "/status",        status);
    write_file(BAT_DIR "/power/online",  online);
}

// --- Main -------------------------------------------------------------------

int main() {
    if (setup_sysfs() != 0) return 1;

    int shm_fd;
    while ((shm_fd = shm_open("my_shm", O_RDONLY, 0666)) == -1) {
        if (errno == ENOENT) sleep(1);
        else { perror("shm_open"); return 1; }
    }

    ControllerData *shared_data = mmap(0, sizeof(ControllerData), PROT_READ, MAP_SHARED, shm_fd, 0);
    if (shared_data == MAP_FAILED) {
        perror("mmap");
        close(shm_fd);
        return 1;
    }

    // Seed the smoothing filter
    battery.voltageSYSx16    = shared_data->SENSE_SYS * 16;
    battery.voltageBATx16    = shared_data->SENSE_SYS * 16;
    battery.indicatorVoltage = 3800;

    uint8_t prev_chargeIndicator = 255; // force a write on first iteration
    int     prev_percent         = -1;

    while (1) {
        readVoltageSYS = shared_data->SENSE_SYS * 3000 / 1024;
        readVoltageBAT = shared_data->SENSE_BAT * 3000 / 1024;

        calculateAmperage();
        calculateVoltage();
        calculateBatteryStatus();

        if (battery.chargeIndicator != prev_chargeIndicator ||
            battery.percent         != prev_percent) {

            update_sysfs();

            prev_chargeIndicator = battery.chargeIndicator;
            prev_percent         = battery.percent;
        }

        usleep(50000);
    }

    munmap(shared_data, sizeof(ControllerData));
    close(shm_fd);
    return 0;
}

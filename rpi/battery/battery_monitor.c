#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <time.h>
#include <sys/mman.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <errno.h>

#define SENSE_RESISTOR_MILLIOHM              50
#define RESISTOR_A_KOHM                      150
#define RESISTOR_B_KOHM                      10
#define BATTERY_INTERNAL_RESISTANCE_MILLIOHM     230
#define BATTERY_INTERNAL_RESISTANCE_LOW_MILLIOHM 150
#define DISCHARGING 0
#define CHARGING    1
#define CHARGED     2

#define BAT_DIR   "/sys/class/power_supply/BAT0"
#define POWER_DIR "/sys/class/power_supply/BAT0/power"

// --- Shared memory layout ---------------------------------------------------

typedef struct {
    uint8_t buttonA;
    uint8_t buttonB;
    uint8_t adc_sys;   // raw 8-bit ADC reading, system side of sense resistor
    uint8_t adc_bat;   // raw 8-bit ADC reading, battery side of sense resistor
    uint8_t STATUS;
    uint8_t JOY_LX;
    uint8_t JOY_LY;
    uint8_t JOY_RX;
    uint8_t JOY_RY;
} ControllerData;

// --- Battery state ----------------------------------------------------------

typedef struct {
    uint16_t sys_mv_filtered;   // IIR-smoothed system voltage (x16 fixed-point, mV)
    uint16_t bat_mv_filtered;   // IIR-smoothed battery voltage (x16 fixed-point, mV)
    int      sense_drop_mv;     // voltage drop across sense resistor + divider correction (mV)
    int      current_ma;        // estimated current: negative = discharging, positive = charging
    uint16_t adjusted_sys_mv;   // system voltage minus sense resistor drop (mV)
    uint16_t open_circuit_mv;   // estimated open-circuit battery voltage (mV)
    uint16_t display_mv;        // slow-moving voltage used for percent calculation (mV)
    uint8_t  charge_state;      // DISCHARGING, CHARGING, or CHARGED
    int      percent;           // battery level 0-100
} Battery;

Battery battery;
uint16_t sys_mv;   // converted system voltage for this iteration (mV)
uint16_t bat_mv;   // converted battery voltage for this iteration (mV)

void calculateAmperage() {
    // Update IIR low-pass filters (weight ~1/8 new sample)
    battery.sys_mv_filtered = battery.sys_mv_filtered - (battery.sys_mv_filtered / 8) + sys_mv;
    battery.bat_mv_filtered = battery.bat_mv_filtered - (battery.bat_mv_filtered / 8) + bat_mv;

    // Derive current from voltage drop across the sense resistor,
    // corrected for the voltage divider ratio
    battery.sense_drop_mv = (battery.bat_mv_filtered - battery.sys_mv_filtered) / 16;
    battery.sense_drop_mv = battery.sense_drop_mv * (RESISTOR_A_KOHM + RESISTOR_B_KOHM) / RESISTOR_A_KOHM;
    battery.current_ma    = battery.sense_drop_mv * (1000 / SENSE_RESISTOR_MILLIOHM);
}

static int get_internal_resistance_milliohm() {
    // Internal resistance scales with SOC.
    // Uses battery.percent from the previous iteration, self-correcting on each pass.
    if (battery.percent <= 0)   return BATTERY_INTERNAL_RESISTANCE_LOW_MILLIOHM;
    if (battery.percent >= 100) return BATTERY_INTERNAL_RESISTANCE_MILLIOHM;

    return BATTERY_INTERNAL_RESISTANCE_LOW_MILLIOHM
        + (BATTERY_INTERNAL_RESISTANCE_MILLIOHM - BATTERY_INTERNAL_RESISTANCE_LOW_MILLIOHM)
        * battery.percent / 100;
}

void calculateVoltage() {
    // Remove the sense resistor drop to get closer to true battery voltage
    battery.adjusted_sys_mv = battery.sys_mv_filtered - battery.sense_drop_mv;

    // Compensate for internal resistance.
    // R_internal scales with SOC
    battery.open_circuit_mv = battery.adjusted_sys_mv
    - battery.current_ma * get_internal_resistance_milliohm() / 1000;

    // Nudge the display voltage one step toward open_circuit_mv,
    // ignoring noise within a ±25mV hysteresis band
    if      (battery.open_circuit_mv > battery.display_mv + 25) battery.display_mv++;
    else if (battery.open_circuit_mv < battery.display_mv - 25) battery.display_mv--;
}

void calculateBatteryStatus() {
    // Linear map: 3.025V = 0%, 4.025V = 100% (7.5mV per percent)
    battery.percent = 100 - (4025 - battery.display_mv) / 7.5;
    if      (battery.percent < 0)   battery.percent = 0;
    else if (battery.percent > 100) battery.percent = 100;

    // Determine charge state from current flow
    if (battery.current_ma < -60)  battery.charge_state = DISCHARGING;
    if (battery.current_ma >= 0)   battery.charge_state = CHARGING;
    if (battery.display_mv > 4050 && battery.current_ma > -40)
        battery.charge_state = CHARGED;
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

    write_file(BAT_DIR "/type",          "Battery\n");
    write_file(BAT_DIR "/technology",    "Li-ion\n");
    write_file(BAT_DIR "/present",       "1\n");
    write_file(BAT_DIR "/capacity_level","Normal\n");
    write_file(BAT_DIR "/charge_full",   "1000000\n");

    return 0;
}

static void update_sysfs() {
    char buf[32];

    bool plugged_in = (battery.charge_state == CHARGING ||
    battery.charge_state == CHARGED);

    snprintf(buf, sizeof(buf), "%d\n", battery.percent * 10000);
    write_file(BAT_DIR "/charge_now",   buf);

    snprintf(buf, sizeof(buf), "%d\n", battery.percent);
    write_file(BAT_DIR "/capacity",     buf);

    write_file(BAT_DIR "/status",       plugged_in ? "Charging\n"  : "Discharging\n");
    write_file(BAT_DIR "/power/online", plugged_in ? "1\n"         : "0\n");
}

// --- Main -------------------------------------------------------------------

int main(int argc, char *argv[]) {
    bool verbose = false;
    bool logging = false;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--verbose") == 0) verbose = true;
        if (strcmp(argv[i], "--logging") == 0) logging = true;
    }

    if (setup_sysfs() != 0) return 1;

    FILE *log_file = NULL;
    if (logging) {
        log_file = fopen("/tmp/battery_monitor.csv", "a");
        if (!log_file) {
            fprintf(stderr, "Failed to open log file: %s\n", strerror(errno));
            return 1;
        }
        // Write header if file is empty
        fseek(log_file, 0, SEEK_END);
        if (ftell(log_file) == 0)
            fprintf(log_file, "timestamp,percent,charge_state,ocv_mv,display_mv,current_ma,r_internal_mohm\n");
    }

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

    // Wait for the first valid ADC sample -- shm may exist before
    // the producer has written its first reading
    while (shared_data->adc_sys == 0 || shared_data->adc_bat == 0)
        usleep(10000);

    // Seed the smoothing filters at their steady-state value (8 * sys_mv)
    sys_mv = shared_data->adc_sys * 3000 / 1024;
    bat_mv = shared_data->adc_bat * 3000 / 1024;
    battery.sys_mv_filtered = sys_mv * 8;
    battery.bat_mv_filtered = bat_mv * 8;
    battery.percent         = 50; // reasonable starting point for resistance lookup

    // Run the pipeline once to get a real initial OCV estimate
    calculateAmperage();
    calculateVoltage();
    calculateBatteryStatus();
    battery.display_mv = battery.open_circuit_mv;

    uint8_t prev_charge_state = 255; // force a write on first iteration
    int     prev_percent      = -1;
    int     log_ticks         = 0;
    const int LOG_INTERVAL    = 1200; // 1200 * 50ms = 60 seconds

    while (1) {
        // Convert raw ADC values to millivolts (10-bit ATmega ADC, 3.0V reference)
        sys_mv = shared_data->adc_sys * 3000 / 1024;
        bat_mv = shared_data->adc_bat * 3000 / 1024;

        calculateAmperage();
        calculateVoltage();
        calculateBatteryStatus();

        const char *state_str[] = { "DISCHARGING", "CHARGING", "CHARGED" };

        if (battery.charge_state != prev_charge_state ||
            battery.percent       != prev_percent) {

            if (verbose) {
                printf("[battery] %3d%%  %s  ocv=%dmV  display=%dmV  current=%dmA  r_internal=%dmΩ\n",
                    battery.percent,
                    state_str[battery.charge_state],
                    battery.open_circuit_mv,
                    battery.display_mv,
                    battery.current_ma,
                    get_internal_resistance_milliohm());
                fflush(stdout);
            }

            update_sysfs();

            prev_charge_state = battery.charge_state;
            prev_percent      = battery.percent;
        }

        if (logging && ++log_ticks >= LOG_INTERVAL) {
            log_ticks = 0;
            time_t now = time(NULL);
            struct tm *t = localtime(&now);
            char timestamp[32];
            strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", t);
            fprintf(log_file, "%s,%d,%s,%d,%d,%d,%d\n",
                timestamp,
                battery.percent,
                state_str[battery.charge_state],
                battery.open_circuit_mv,
                battery.display_mv,
                battery.current_ma,
                get_internal_resistance_milliohm());
            fflush(log_file);
        }

        usleep(50000); // poll every 50ms
    }

    munmap(shared_data, sizeof(ControllerData));
    close(shm_fd);
    return 0;
}

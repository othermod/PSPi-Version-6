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

#define SENSE_RESISTOR_MILLIOHM                     50
#define RESISTOR_A_KOHM                             150
#define RESISTOR_B_KOHM                             10
#define BATTERY_INTERNAL_RESISTANCE_FULL_MILLIOHM   210
#define BATTERY_INTERNAL_RESISTANCE_EMPTY_MILLIOHM  190
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
    if (battery.percent <= 0)   return BATTERY_INTERNAL_RESISTANCE_EMPTY_MILLIOHM;
    if (battery.percent >= 100) return BATTERY_INTERNAL_RESISTANCE_FULL_MILLIOHM;

    return BATTERY_INTERNAL_RESISTANCE_EMPTY_MILLIOHM
    + (BATTERY_INTERNAL_RESISTANCE_FULL_MILLIOHM - BATTERY_INTERNAL_RESISTANCE_EMPTY_MILLIOHM)
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

// Voltage (mV) corresponding to each SOC level 0..99%.
// soc_mv_table[i] = voltage at which the battery is considered i% full.
// Derived from a real discharge log: 11891 samples split into 100 equal
// time-buckets, median display_mv taken per bucket, ties nudged +1mV
// to preserve strict monotonicity.
static const uint16_t soc_mv_table[100] = {
    3270, 3288, 3295, 3301, 3323, // 0-4%
    3333, 3340, 3341, 3360, 3377, // 5-9%
    3380, 3381, 3386, 3388, 3398, // 10-14%
    3423, 3424, 3428, 3430, 3431, // 15-19%
    3432, 3434, 3436, 3438, 3454, // 20-24%
    3472, 3473, 3474, 3475, 3476, // 25-29%
    3477, 3479, 3480, 3481, 3482, // 30-34%
    3485, 3486, 3498, 3506, 3507, // 35-39%
    3509, 3512, 3513, 3514, 3515, // 40-44%
    3516, 3521, 3529, 3546, 3555, // 45-49%
    3558, 3562, 3565, 3566, 3570, // 50-54%
    3583, 3605, 3607, 3613, 3616, // 55-59%
    3621, 3637, 3656, 3657, 3659, // 60-64%
    3664, 3685, 3703, 3704, 3709, // 65-69%
    3715, 3731, 3748, 3755, 3758, // 70-74%
    3761, 3787, 3796, 3799, 3805, // 75-79%
    3807, 3830, 3837, 3838, 3840, // 80-84%
    3845, 3880, 3881, 3885, 3889, // 85-89%
    3904, 3925, 3929, 3934, 3940, // 90-94%
    3975, 3977, 3981, 4014, 4020, // 95-99%
};

static int percent_from_voltage(uint16_t mv) {
    if (mv <= soc_mv_table[0])  return 0;
    if (mv >  soc_mv_table[99]) return 100;
    for (int i = 99; i >= 0; i--) {
        if (mv >= soc_mv_table[i]) return i;
    }
    return 0;
}

void calculateBatteryStatus() {
    battery.percent = percent_from_voltage(battery.display_mv);

    // Determine charge state from current flow
    if (battery.current_ma < -60)  battery.charge_state = DISCHARGING;
    if (battery.current_ma >= 0)   battery.charge_state = CHARGING;
    if (battery.display_mv > 4000 && abs(battery.current_ma) < 50)
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

    snprintf(buf, sizeof(buf), "%d\n", battery.percent * 20000);
    write_file(BAT_DIR "/charge_now",   buf);

    snprintf(buf, sizeof(buf), "%d\n", battery.percent);
    write_file(BAT_DIR "/capacity",     buf);

    const char *status_str;
    if      (battery.charge_state == CHARGED)  status_str = "Full\n";
    else if (battery.charge_state == CHARGING) status_str = "Charging\n";
    else                                        status_str = "Discharging\n";

    write_file(BAT_DIR "/status",       status_str);
    write_file(BAT_DIR "/power/online", plugged_in ? "1\n"         : "0\n");
}

// --- Main -------------------------------------------------------------------

int main(int argc, char *argv[]) {
    bool verbose = false;
    bool logging = false;
    int  log_interval_sec = 60;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--verbose") == 0) verbose = true;
        if (strcmp(argv[i], "--logging") == 0) {
            logging = true;
            if (i + 1 < argc && argv[i + 1][0] != '-') {
                log_interval_sec = atoi(argv[++i]);
                if (log_interval_sec < 1) log_interval_sec = 1;
            }
        }
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
    const int LOG_INTERVAL    = log_interval_sec * 20; // 20 ticks per second (50ms each)

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

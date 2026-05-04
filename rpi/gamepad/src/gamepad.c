#include <stdio.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <linux/i2c-dev.h>
#include <sys/ioctl.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <net/if.h>
#include <linux/rtnetlink.h>
#include <sys/socket.h>
#include <linux/uinput.h>
#include <linux/input.h>
#include <time.h>

#define DEFAULT_POLLING_DELAY_MS 16000
#define FAST_POLLING_DELAY_MS 8000
#define DEFAULT_DIMMING_TIMEOUT_SEC 120

// Global counter for power management
int poweroff_counter = 0;
int crc_error_count = 0;

unsigned int polling_delay = DEFAULT_POLLING_DELAY_MS;

#define INTERFACE_NAME "wlan0"

// Configuration flags
bool enable_crc = true;
bool is_dim = false;
bool is_idle = false;
uint32_t previous_status;
bool wifi_enabled = false;
bool wifi_connected = false;
uint8_t wifi_check_trigger = 0;
uint16_t input_count = 0;
uint32_t time_at_last_change;
bool has_wifi = true;
uint8_t extra_button_base_idx;

uint8_t brightness;
#define DATASIZE 11

// Default Controller configuration
uint8_t joystick_count = 1;
uint32_t dimming_timeout = 0;

// Input type selection
enum { INPUT_GAMEPAD, INPUT_MOUSE, INPUT_NONE };
int input_type = INPUT_GAMEPAD;

// PSPi controller board data structure (11 bytes)
typedef struct {
    union {
        struct Buttons {
            uint16_t mute:1;         // bit 0  - Unused (Mute)
            uint16_t select:1;        // bit 1  - Back (Select)
            uint16_t start:1;         // bit 2  - Start
            uint16_t a:1;            // bit 3  - A
            uint16_t x:1;            // bit 4  - X
            uint16_t y:1;            // bit 5  - Y
            uint16_t b:1;            // bit 6  - B
            uint16_t rshoulder:1;    // bit 7  - Right Shoulder
            uint16_t lshoulder:1;    // bit 8  - Left Shoulder
            uint16_t dpad_left:1;    // bit 9  - D-Pad Left
            uint16_t dpad_up:1;      // bit 10 - D-Pad Up
            uint16_t dpad_down:1;    // bit 11 - D-Pad Down
            uint16_t dpad_right:1;   // bit 12 - D-Pad Right
            uint16_t vol_minus:1;    // bit 13 - Unused (Vol-)
            uint16_t vol_plus:1;     // bit 14 - Unused (Vol+)
            uint16_t home:1;         // bit 15 - Guide (Home)
        } bits;
        uint16_t raw;
    } buttons;
    uint8_t system_voltage;      // System voltage reading
    uint8_t battery_voltage;     // Battery voltage reading
    union {
        struct Status {
            uint8_t brightness:3;     // Bits 0-2: Display brightness level (1-8)
            uint8_t headphones:1;       // Bit 3: Reserved for future use
            uint8_t sd_pressed:1;     // Bit 4: SD button status
            uint8_t sleeping:1;       // Bit 5: Sleep status
            uint8_t left_switch:1;    // Bit 6: Left switch status
            uint8_t muted:1;          // Bit 7: Mute status
        } bits;
        uint8_t raw;
    } status_flags;
    uint8_t left_stick_x;
    uint8_t left_stick_y;
    union {
        struct RightX {
            uint8_t button:1;    // Button data in bit 0
            uint8_t position:7;  // Position data in bits 1-7
        } bits;
        uint8_t raw;
    } right_stick_x;
    union {
        struct RightY {
            uint8_t button:1;    // Button data in bit 0
            uint8_t position:7;  // Position data in bits 1-7
        } bits;
        uint8_t raw;
    } right_stick_y;
    uint8_t crc_high;
    uint8_t crc_low;
} SharedData;



// Global structs for controller state
SharedData *shared_memory_data;
SharedData current_controller_data;
SharedData previous_controller_state;
SharedData previous_mouse_data = {0};

// Global file descriptors
int controller_board_fd;
int virtual_gamepad_fd = -1;
int virtual_mouse_fd = -1;
int wifi_monitor_fd;
int shared_memory_fd;

// Global netlink request structure
struct {
    struct nlmsghdr nlh;
    struct ifinfomsg ifi;
} wifi_status_request;

#define BUTTON_CONFIG_STICK 0
#define BUTTON_CONFIG_TRIGGER 1

bool extra_buttons = false;
bool button_config = BUTTON_CONFIG_TRIGGER;

void parse_command_line_args(int argc, char *argv[]) {
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--help") == 0 || strcmp(argv[i], "-h") == 0) {
            printf("Usage: [options]\n");
            printf("Options:\n");
            printf("  --input <gamepad|mouse|none>  Select input device type (default: gamepad)\n");
            printf("  --nocrc                       Disable CRC checks\n");
            printf("  --joysticks <num>             Set number of joysticks (0-2, gamepad only)\n");
            printf("  --dim <seconds>               Enable dimming after <seconds> idle (1-3600, default: 120)\n");
            printf("  --fast                        Enable fast mode (double input polling rate)\n");
            printf("  --extrabuttons [trigger|stick] Enable extra buttons (trigger/stick, gamepad only)\n");
            printf("  --help, -h                    Display this help and exit\n");
            exit(0);
        } else if (strcmp(argv[i], "--nocrc") == 0) {
            enable_crc = false;
            printf("CRC Disabled\n");
        } else if (strcmp(argv[i], "--input") == 0) {
            if (i + 1 < argc) {
                if (strcmp(argv[i + 1], "gamepad") == 0) {
                    input_type = INPUT_GAMEPAD;
                    printf("Input type: gamepad\n");
                } else if (strcmp(argv[i + 1], "mouse") == 0) {
                    input_type = INPUT_MOUSE;
                    printf("Input type: mouse\n");
                } else if (strcmp(argv[i + 1], "none") == 0) {
                    input_type = INPUT_NONE;
                    printf("Input type: none\n");
                } else {
                    printf("Invalid input type '%s'. Use gamepad, mouse, or none.\n", argv[i + 1]);
                    exit(1);
                }
                i++;
            } else {
                printf("No input type specified for --input\n");
                exit(1);
            }
        } else if (strcmp(argv[i], "--joysticks") == 0) {
            if (input_type != INPUT_GAMEPAD) {
                printf("Warning: --joysticks is only valid with --input gamepad\n");
                continue;
            }
            if (i + 1 < argc) {
                joystick_count = atoi(argv[++i]);
                if (joystick_count < 0 || joystick_count > 2) {
                    printf("Invalid number of joysticks. Must be between 0 and 2.\n");
                    exit(1);
                }
                printf("Number of joysticks: %d\n", joystick_count);
            } else {
                printf("No number specified for --joysticks\n");
                exit(1);
            }
        } else if (strcmp(argv[i], "--dim") == 0) {
            if (i + 1 < argc && atoi(argv[i + 1]) >= 1 && atoi(argv[i + 1]) <= 3600) {
                dimming_timeout = atoi(argv[++i]);
                printf("Dimming enabled: %d seconds\n", dimming_timeout);
            } else {
                dimming_timeout = DEFAULT_DIMMING_TIMEOUT_SEC;
                printf("Dimming enabled: default 120 seconds\n");
            }
        } else if (strcmp(argv[i], "--fast") == 0) {
            printf("Gotta go fast\n");
            polling_delay = FAST_POLLING_DELAY_MS;
        } else if (strcmp(argv[i], "--extrabuttons") == 0) {
            if (input_type != INPUT_GAMEPAD) {
                printf("Warning: --extrabuttons is only valid with --input gamepad\n");
                continue;
            }
            extra_buttons = true;
            if (i + 1 < argc) {
                if (strcmp(argv[i + 1], "trigger") == 0) {
                    button_config = BUTTON_CONFIG_TRIGGER;
                    i++;
                } else if (strcmp(argv[i + 1], "stick") == 0) {
                    button_config = BUTTON_CONFIG_STICK;
                    i++;
                }
            }
            extra_button_base_idx = 1 + (button_config * 7);
            printf("Extra buttons enabled: %s mode\n",
                   button_config == BUTTON_CONFIG_TRIGGER ? "trigger" : "stick");
        }
    }
}

// CRC-16-CCITT lookup table
static uint16_t crc16_ccitt_table[256];

static void init_crc16_ccitt_table(void) {
    const uint16_t poly = 0x1021;
    for (uint16_t i = 0; i < 256; i++) {
        uint16_t crc = i << 8;
        for (uint8_t j = 0; j < 8; j++) {
            if (crc & 0x8000) {
                crc = (crc << 1) ^ poly;
            } else {
                crc <<= 1;
            }
        }
        crc16_ccitt_table[i] = crc;
    }
}

uint16_t compute_crc16_ccitt(const uint8_t *data, uint8_t length) {
    uint16_t crc = 0xFFFF;
    for (uint8_t i = 0; i < length; i++) {
        crc = (crc << 8) ^ crc16_ccitt_table[((crc >> 8) ^ data[i]) & 0xFF];
    }
    return crc;
}

void cleanup_resources(void) {
    if (virtual_gamepad_fd >= 0) {
        ioctl(virtual_gamepad_fd, UI_DEV_DESTROY);
        close(virtual_gamepad_fd);
    }
    if (virtual_mouse_fd >= 0) {
        ioctl(virtual_mouse_fd, UI_DEV_DESTROY);
        close(virtual_mouse_fd);
    }
    if (wifi_monitor_fd >= 0) {
        close(wifi_monitor_fd);
    }
    if (controller_board_fd >= 0) {
        close(controller_board_fd);
    }
    if (shared_memory_data) {
        munmap(shared_memory_data, sizeof(SharedData));
    }
    if (shared_memory_fd >= 0) {
        close(shared_memory_fd);
    }
}

void init_i2c(void) {
    controller_board_fd = open("/dev/i2c-1", O_RDWR);
    if (controller_board_fd < 0) {
        perror("Failed to open i2c bus");
        cleanup_resources();
        exit(1);
    }
    if (ioctl(controller_board_fd, I2C_SLAVE, 0x10) < 0) {
        perror("Failed to set i2c slave");
        close(controller_board_fd);
        cleanup_resources();
        exit(1);
    }
}

bool read_i2c_data(void) {
    if (read(controller_board_fd, &current_controller_data, DATASIZE) != DATASIZE) {
        perror("Failed to read from i2c device");
        sleep(1);
        return false;
    }
    if (enable_crc) {
        uint16_t computed_crc = compute_crc16_ccitt((const uint8_t*)&current_controller_data, 9);
        uint16_t received_crc = (current_controller_data.crc_high << 8) | current_controller_data.crc_low;
        if (computed_crc != received_crc) {
            printf("CRC Error - Expected: 0x%04X, Received: 0x%04X\n",
                   computed_crc, received_crc);
            crc_error_count++;
            return false;
        }
    }
    *shared_memory_data = current_controller_data;
    return true;
}

#define CMD_BRIGHTNESS 0x22

static inline void write_i2c_command(int fd, uint8_t cmd, uint8_t value) {
    uint8_t i2c_data[4] = {cmd, value, 0, 0};
    write(fd, i2c_data, 4);
}

void init_shared_memory(void) {
    shared_memory_fd = shm_open("my_shm", O_CREAT | O_RDWR, 0666);
    ftruncate(shared_memory_fd, sizeof(SharedData));
    shared_memory_data = mmap(0, sizeof(SharedData), PROT_WRITE, MAP_SHARED, shared_memory_fd, 0);
}

// ---- Gamepad uinput ----

int setup_uinput_gamepad(int uinput_fd) {
    // UI_SET_* ioctls must come before the uinput_user_dev write.
    ioctl(uinput_fd, UI_SET_EVBIT, EV_KEY);
    // Register the exact keycodes the real PS3 hid-sony driver uses.
    // RetroArch/Lakka scans these numerically to assign joydev button indices,
    // so they must match what the PS3 autoconfig profile expects.
    ioctl(uinput_fd, UI_SET_KEYBIT, BTN_SOUTH);       // joydev 0  - cross
    ioctl(uinput_fd, UI_SET_KEYBIT, BTN_EAST);        // joydev 1  - circle
    ioctl(uinput_fd, UI_SET_KEYBIT, BTN_NORTH);       // joydev 2  - triangle
    ioctl(uinput_fd, UI_SET_KEYBIT, BTN_WEST);        // joydev 3  - square
    ioctl(uinput_fd, UI_SET_KEYBIT, BTN_TL);          // joydev 4  - L1
    ioctl(uinput_fd, UI_SET_KEYBIT, BTN_TR);          // joydev 5  - R1
    ioctl(uinput_fd, UI_SET_KEYBIT, BTN_TL2);         // joydev 6  - L2
    ioctl(uinput_fd, UI_SET_KEYBIT, BTN_TR2);         // joydev 7  - R2
    ioctl(uinput_fd, UI_SET_KEYBIT, BTN_SELECT);      // joydev 8  - select
    ioctl(uinput_fd, UI_SET_KEYBIT, BTN_START);       // joydev 9  - start
    ioctl(uinput_fd, UI_SET_KEYBIT, BTN_MODE);        // joydev 10 - PS button
    ioctl(uinput_fd, UI_SET_KEYBIT, BTN_THUMBL);      // joydev 11 - L3
    ioctl(uinput_fd, UI_SET_KEYBIT, BTN_THUMBR);      // joydev 12 - R3
    ioctl(uinput_fd, UI_SET_KEYBIT, BTN_DPAD_UP);     // joydev 13 - d-pad up
    ioctl(uinput_fd, UI_SET_KEYBIT, BTN_DPAD_DOWN);   // joydev 14 - d-pad down
    ioctl(uinput_fd, UI_SET_KEYBIT, BTN_DPAD_LEFT);   // joydev 15 - d-pad left
    ioctl(uinput_fd, UI_SET_KEYBIT, BTN_DPAD_RIGHT);  // joydev 16 - d-pad right

    ioctl(uinput_fd, UI_SET_EVBIT, EV_ABS);
    ioctl(uinput_fd, UI_SET_ABSBIT, ABS_X);
    ioctl(uinput_fd, UI_SET_ABSBIT, ABS_Y);
    ioctl(uinput_fd, UI_SET_ABSBIT, ABS_RX);
    ioctl(uinput_fd, UI_SET_ABSBIT, ABS_RY);

    struct uinput_user_dev uidev;
    memset(&uidev, 0, sizeof(uidev));
    snprintf(uidev.name, UINPUT_MAX_NAME_SIZE, "PS3 Controller");
    uidev.id.bustype = BUS_USB;
    uidev.id.vendor  = 0x054c;
    uidev.id.product = 0x0268;
    uidev.id.version = 0x0110;

    // Left stick: full 8-bit hardware output, usable range 40-215, center ~127.
    uidev.absmin[ABS_X]  = 40;  uidev.absmax[ABS_X]  = 215;
    uidev.absflat[ABS_X] = 20;  uidev.absfuzz[ABS_X] = 20;
    uidev.absmin[ABS_Y]  = 40;  uidev.absmax[ABS_Y]  = 215;
    uidev.absflat[ABS_Y] = 20;  uidev.absfuzz[ABS_Y] = 20;

    // Right stick: 7-bit position field, range 0-127, center ~63.
    uidev.absmin[ABS_RX]  = 0;   uidev.absmax[ABS_RX]  = 127;
    uidev.absflat[ABS_RX] = 10;  uidev.absfuzz[ABS_RX] = 10;
    uidev.absmin[ABS_RY]  = 0;   uidev.absmax[ABS_RY]  = 127;
    uidev.absflat[ABS_RY] = 10;  uidev.absfuzz[ABS_RY] = 10;

    ssize_t ret = write(uinput_fd, &uidev, sizeof(uidev));
    if (ret < 0) {
        perror("Failed to write to uinput device in setup_uinput_gamepad");
        return -1;
    }

    if (ioctl(uinput_fd, UI_DEV_CREATE) < 0) {
        perror("Failed to create uinput device");
        return -1;
    }

    // Initialize all axes to their center values before any real data arrives.
    // Left stick center is 127 (midpoint of 40-215).
    // Right stick center is 63 (midpoint of 0-127).
    // Sending 127 for ABS_RX/ABS_RY was the previous bug: with absmax=127,
    // that value means full deflection, causing RetroArch to scroll immediately.
    struct input_event events[5] = {
        {.type = EV_ABS, .code = ABS_X,  .value = 127},
        {.type = EV_ABS, .code = ABS_Y,  .value = 127},
        {.type = EV_ABS, .code = ABS_RX, .value = 63},
        {.type = EV_ABS, .code = ABS_RY, .value = 63},
        {.type = EV_SYN, .code = SYN_REPORT, .value = 0}
    };
    write(uinput_fd, events, sizeof(events));
    return 0;
}

void init_virtual_gamepad(void) {
    virtual_gamepad_fd = open("/dev/uinput", O_WRONLY | O_NONBLOCK);
    if (virtual_gamepad_fd < 0) {
        perror("Could not open uinput device");
        cleanup_resources();
        exit(1);
    }
    if (setup_uinput_gamepad(virtual_gamepad_fd) != 0) {
        perror("Error setting up uinput device");
        close(virtual_gamepad_fd);
        cleanup_resources();
        exit(1);
    }
}

// ---- Mouse uinput ----

void init_virtual_mouse(void) {
    virtual_mouse_fd = open("/dev/uinput", O_WRONLY | O_NONBLOCK);
    if (virtual_mouse_fd < 0) {
        perror("Could not open uinput device");
        cleanup_resources();
        exit(1);
    }

    ioctl(virtual_mouse_fd, UI_SET_EVBIT, EV_KEY);
    ioctl(virtual_mouse_fd, UI_SET_KEYBIT, KEY_BACK);
    ioctl(virtual_mouse_fd, UI_SET_KEYBIT, KEY_FORWARD);
    ioctl(virtual_mouse_fd, UI_SET_KEYBIT, KEY_LEFTMETA);
    ioctl(virtual_mouse_fd, UI_SET_KEYBIT, BTN_LEFT);
    ioctl(virtual_mouse_fd, UI_SET_KEYBIT, BTN_RIGHT);
    ioctl(virtual_mouse_fd, UI_SET_KEYBIT, KEY_LEFT);
    ioctl(virtual_mouse_fd, UI_SET_KEYBIT, KEY_RIGHT);
    ioctl(virtual_mouse_fd, UI_SET_KEYBIT, KEY_UP);
    ioctl(virtual_mouse_fd, UI_SET_KEYBIT, KEY_DOWN);
    ioctl(virtual_mouse_fd, UI_SET_KEYBIT, KEY_ENTER);

    ioctl(virtual_mouse_fd, UI_SET_EVBIT, EV_REL);
    ioctl(virtual_mouse_fd, UI_SET_RELBIT, REL_X);
    ioctl(virtual_mouse_fd, UI_SET_RELBIT, REL_Y);

    struct uinput_setup usetup = {0};
    usetup.id.bustype = BUS_USB;
    usetup.id.vendor = 0x1234;
    usetup.id.product = 0x5678;
    strcpy(usetup.name, "Example device");

    ioctl(virtual_mouse_fd, UI_DEV_SETUP, &usetup);
    ioctl(virtual_mouse_fd, UI_DEV_CREATE);
    sleep(1);
}

// ---- Gamepad event emission ----

typedef struct { uint16_t hw_mask; uint16_t keycode; } ButtonMap;
static const ButtonMap button_map[] = {
    { 0x0008, BTN_SOUTH       },  // a/cross       -> joydev 0
    { 0x0040, BTN_EAST        },  // b/circle      -> joydev 1
    { 0x0020, BTN_NORTH       },  // y/triangle    -> joydev 2
    { 0x0010, BTN_WEST        },  // x/square      -> joydev 3
    { 0x0100, BTN_TL          },  // lshoulder/L1  -> joydev 4
    { 0x0080, BTN_TR          },  // rshoulder/R1  -> joydev 5
    // BTN_TL2 / BTN_TR2 (joydev 6/7) come from extra_buttons path
    { 0x0002, BTN_SELECT      },  // select/back   -> joydev 8
    { 0x0004, BTN_START       },  // start         -> joydev 9
    { 0x8000, BTN_MODE        },  // home/PS       -> joydev 10
    // BTN_THUMBL / BTN_THUMBR (joydev 11/12) come from extra_buttons path
    { 0x0400, BTN_DPAD_UP     },  // d-pad up      -> joydev 13
    { 0x0800, BTN_DPAD_DOWN   },  // d-pad down    -> joydev 14
    { 0x0200, BTN_DPAD_LEFT   },  // d-pad left    -> joydev 15
    { 0x1000, BTN_DPAD_RIGHT  },  // d-pad right   -> joydev 16
};

void update_gamepad_events(int uinput_fd) {
    struct input_event events[20];
    int event_count = 0;

    uint16_t changed_buttons = previous_controller_state.buttons.raw ^ current_controller_data.buttons.raw;
    if (changed_buttons) {
        for (size_t i = 0; i < sizeof(button_map) / sizeof(button_map[0]); i++) {
            if (changed_buttons & button_map[i].hw_mask) {
                events[event_count].type  = EV_KEY;
                events[event_count].code  = button_map[i].keycode;
                events[event_count].value = (current_controller_data.buttons.raw & button_map[i].hw_mask) != 0;
                event_count++;
            }
        }
    }

    if (joystick_count >= 1) {
        if (previous_controller_state.left_stick_x != current_controller_data.left_stick_x) {
            events[event_count].type  = EV_ABS;
            events[event_count].code  = ABS_X;
            events[event_count].value = current_controller_data.left_stick_x;
            event_count++;
        }
        if (previous_controller_state.left_stick_y != current_controller_data.left_stick_y) {
            events[event_count].type  = EV_ABS;
            events[event_count].code  = ABS_Y;
            events[event_count].value = current_controller_data.left_stick_y;
            event_count++;
        }
    }

    if (joystick_count == 2) {
        if (previous_controller_state.right_stick_x.raw != current_controller_data.right_stick_x.raw) {
            events[event_count].type  = EV_ABS;
            events[event_count].code  = ABS_RX;
            events[event_count].value = current_controller_data.right_stick_x.bits.position;
            event_count++;
        }
        if (previous_controller_state.right_stick_y.raw != current_controller_data.right_stick_y.raw) {
            events[event_count].type  = EV_ABS;
            events[event_count].code  = ABS_RY;
            events[event_count].value = current_controller_data.right_stick_y.bits.position;
            event_count++;
        }
    }

    if (extra_buttons) {
        uint16_t btn_y = (button_config == BUTTON_CONFIG_TRIGGER) ? BTN_TL2    : BTN_THUMBL;
        uint16_t btn_x = (button_config == BUTTON_CONFIG_TRIGGER) ? BTN_TR2    : BTN_THUMBR;

        if (previous_controller_state.right_stick_y.bits.button != current_controller_data.right_stick_y.bits.button) {
            events[event_count].type  = EV_KEY;
            events[event_count].code  = btn_y;
            events[event_count].value = current_controller_data.right_stick_y.bits.button;
            event_count++;
        }
        if (previous_controller_state.right_stick_x.bits.button != current_controller_data.right_stick_x.bits.button) {
            events[event_count].type  = EV_KEY;
            events[event_count].code  = btn_x;
            events[event_count].value = current_controller_data.right_stick_x.bits.button;
            event_count++;
        }
    }

    if (event_count > 0) {
        events[event_count].type  = EV_SYN;
        events[event_count].code  = SYN_REPORT;
        events[event_count].value = 0;
        event_count++;
        write(uinput_fd, events, sizeof(struct input_event) * event_count);
    }
}

// ---- Mouse event emission ----

#define AXIS_CENTER 127
#define AXIS_THRESHOLD_LOW 112
#define AXIS_THRESHOLD_HIGH 142

void update_mouse_events(int uinput_fd) {
    struct input_event events[20];
    int event_count = 0;
    bool changed = false;

    // Left stick -> REL_X
    if (previous_mouse_data.left_stick_x != current_controller_data.left_stick_x ||
        current_controller_data.left_stick_x > AXIS_THRESHOLD_HIGH ||
        current_controller_data.left_stick_x < AXIS_THRESHOLD_LOW) {
        events[event_count].type = EV_REL;
    events[event_count].code = REL_X;
    events[event_count].value = (current_controller_data.left_stick_x - AXIS_CENTER) / 16;
    event_count++;
    previous_mouse_data.left_stick_x = current_controller_data.left_stick_x;
    changed = true;
        }

        // Left stick -> REL_Y
        if (previous_mouse_data.left_stick_y != current_controller_data.left_stick_y ||
            current_controller_data.left_stick_y > AXIS_THRESHOLD_HIGH ||
            current_controller_data.left_stick_y < AXIS_THRESHOLD_LOW) {
            events[event_count].type = EV_REL;
        events[event_count].code = REL_Y;
        events[event_count].value = (current_controller_data.left_stick_y - AXIS_CENTER) / 16;
        event_count++;
        previous_mouse_data.left_stick_y = current_controller_data.left_stick_y;
        changed = true;
            }

            // Buttons — only emit changed bits
            uint16_t changed_buttons = previous_mouse_data.buttons.raw ^ current_controller_data.buttons.raw;
            if (changed_buttons) {
                if (changed_buttons & (1 << 2)) { // start -> KEY_ENTER
                    events[event_count].type = EV_KEY;
                    events[event_count].code = KEY_ENTER;
                    events[event_count].value = current_controller_data.buttons.bits.start;
                    event_count++;
                }
                if (changed_buttons & (1 << 3)) { // a -> BTN_LEFT
                    events[event_count].type = EV_KEY;
                    events[event_count].code = BTN_LEFT;
                    events[event_count].value = current_controller_data.buttons.bits.a;
                    event_count++;
                }
                if (changed_buttons & (1 << 6)) { // b -> BTN_RIGHT
                    events[event_count].type = EV_KEY;
                    events[event_count].code = BTN_RIGHT;
                    events[event_count].value = current_controller_data.buttons.bits.b;
                    event_count++;
                }
                if (changed_buttons & (1 << 7)) { // rshoulder -> KEY_FORWARD
                    events[event_count].type = EV_KEY;
                    events[event_count].code = KEY_FORWARD;
                    events[event_count].value = current_controller_data.buttons.bits.rshoulder;
                    event_count++;
                }
                if (changed_buttons & (1 << 8)) { // lshoulder -> KEY_BACK
                    events[event_count].type = EV_KEY;
                    events[event_count].code = KEY_BACK;
                    events[event_count].value = current_controller_data.buttons.bits.lshoulder;
                    event_count++;
                }
                if (changed_buttons & (1 << 9)) { // dpad_left -> KEY_LEFT
                    events[event_count].type = EV_KEY;
                    events[event_count].code = KEY_LEFT;
                    events[event_count].value = current_controller_data.buttons.bits.dpad_left;
                    event_count++;
                }
                if (changed_buttons & (1 << 10)) { // dpad_up -> KEY_UP
                    events[event_count].type = EV_KEY;
                    events[event_count].code = KEY_UP;
                    events[event_count].value = current_controller_data.buttons.bits.dpad_up;
                    event_count++;
                }
                if (changed_buttons & (1 << 11)) { // dpad_down -> KEY_DOWN
                    events[event_count].type = EV_KEY;
                    events[event_count].code = KEY_DOWN;
                    events[event_count].value = current_controller_data.buttons.bits.dpad_down;
                    event_count++;
                }
                if (changed_buttons & (1 << 12)) { // dpad_right -> KEY_RIGHT
                    events[event_count].type = EV_KEY;
                    events[event_count].code = KEY_RIGHT;
                    events[event_count].value = current_controller_data.buttons.bits.dpad_right;
                    event_count++;
                }
                if (changed_buttons & (1 << 15)) { // home -> KEY_LEFTMETA
                    events[event_count].type = EV_KEY;
                    events[event_count].code = KEY_LEFTMETA;
                    events[event_count].value = current_controller_data.buttons.bits.home;
                    event_count++;
                }
                previous_mouse_data.buttons.raw = current_controller_data.buttons.raw;
                changed = true;
            }

            if (changed) {
                events[event_count].type = EV_SYN;
                events[event_count].code = SYN_REPORT;
                events[event_count].value = 0;
                event_count++;
                write(uinput_fd, events, sizeof(struct input_event) * event_count);
            }
}

// ---- WiFi monitoring ----

void init_wifi_monitoring(void) {
    wifi_monitor_fd = socket(AF_NETLINK, SOCK_RAW, NETLINK_ROUTE);
    if (wifi_monitor_fd == -1) {
        perror("Error creating netlink socket");
        has_wifi = false;
        return;
    }

    int ifindex = if_nametoindex(INTERFACE_NAME);
    if (ifindex == 0) {
        perror("Error getting interface index");
        has_wifi = false;
        close(wifi_monitor_fd);
        wifi_monitor_fd = -1;
        return;
    }

    memset(&wifi_status_request, 0, sizeof(wifi_status_request));
    wifi_status_request.nlh.nlmsg_len = NLMSG_LENGTH(sizeof(struct ifinfomsg));
    wifi_status_request.nlh.nlmsg_flags = NLM_F_REQUEST;
    wifi_status_request.nlh.nlmsg_type = RTM_GETLINK;
    wifi_status_request.ifi.ifi_family = AF_UNSPEC;
    wifi_status_request.ifi.ifi_index = ifindex;
}

void check_wifi_status(void) {
    char wifi_status_buffer[4096];
    send(wifi_monitor_fd, &wifi_status_request, wifi_status_request.nlh.nlmsg_len, 0);
    int len = recv(wifi_monitor_fd, wifi_status_buffer, sizeof(wifi_status_buffer), 0);
    struct nlmsghdr *nh = (struct nlmsghdr *)wifi_status_buffer;

    if (nh->nlmsg_type == RTM_NEWLINK) {
        struct ifinfomsg *ifi = NLMSG_DATA(nh);
        wifi_enabled = ifi->ifi_flags & IFF_UP;
        bool check_connection = ifi->ifi_flags & IFF_RUNNING;

        if (check_connection != wifi_connected) {
            wifi_connected = check_connection;
            uint8_t i2c_data[4];
            i2c_data[0] = 0x20;
            i2c_data[1] = wifi_connected ? 1 : 0;
            write(controller_board_fd, i2c_data, 4);
        }
    }
}

// ---- Idle / dimming ----

void check_idle_state(int i2c_fd) {
    uint32_t status = (current_controller_data.buttons.raw << 18) |
    ((current_controller_data.left_stick_x & 0xF0) << 4) |
    (current_controller_data.left_stick_y >> 4);

    const time_t current_time = time(NULL);

    if (previous_status == status) {
        if (!is_idle) {
            time_at_last_change = current_time;
            is_idle = true;
        }

        if (!is_dim && (current_time - time_at_last_change >= dimming_timeout)) {
            brightness = current_controller_data.status_flags.bits.brightness + 1;
            write_i2c_command(i2c_fd, CMD_BRIGHTNESS, 1);
            is_dim = true;
        }
    } else {
        is_idle = false;

        if (is_dim && current_controller_data.status_flags.bits.brightness == 0) {
            write_i2c_command(i2c_fd, CMD_BRIGHTNESS, brightness);
            is_dim = false;
        }

        previous_status = status;
    }
}

// ---- Power management ----

void check_for_shutdown_condition(void) {
    if (shared_memory_data->status_flags.bits.sd_pressed || (shared_memory_data->system_voltage <= 128)) {
        poweroff_counter++;
        if (poweroff_counter > 10) {
            system("poweroff");
            exit(0);
        }
    } else {
        poweroff_counter = 0;
    }
}

// ---- Main ----

int main(int argc, char *argv[]) {
    parse_command_line_args(argc, argv);
    init_crc16_ccitt_table();
    init_i2c();
    init_shared_memory();

    switch (input_type) {
        case INPUT_GAMEPAD:
            init_virtual_gamepad();
            break;
        case INPUT_MOUSE:
            init_virtual_mouse();
            break;
        case INPUT_NONE:
            break;
    }

    if (has_wifi) {
        init_wifi_monitoring();
    }

    while (1) {
        if (!read_i2c_data()) {
            continue;
        }

        check_for_shutdown_condition();

        if (has_wifi && wifi_check_trigger == 0) {
            check_wifi_status();
        }

        if (dimming_timeout) {
            check_idle_state(controller_board_fd);
        }

        switch (input_type) {
            case INPUT_GAMEPAD:
                if (previous_controller_state.buttons.raw != current_controller_data.buttons.raw ||
                    memcmp(&previous_controller_state.left_stick_x, &current_controller_data.left_stick_x, 4) != 0) {
                    update_gamepad_events(virtual_gamepad_fd);
                previous_controller_state = current_controller_data;
                    }
                    break;
            case INPUT_MOUSE:
                update_mouse_events(virtual_mouse_fd);
                break;
            case INPUT_NONE:
                break;
        }

        wifi_check_trigger++;

        if (current_controller_data.status_flags.bits.sleeping) {
            usleep(100000);
        } else {
            usleep(polling_delay);
        }
    }

    cleanup_resources();
    return 0;
}

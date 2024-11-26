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
bool gamepad_enabled = true;
bool is_dim = false;
bool is_idle = false;
uint32_t previous_status;
bool wifi_enabled = false;
bool wifi_connected = false;
uint8_t wifi_check_trigger = 0;
uint16_t input_count = 0;
uint32_t time_at_last_change;
bool has_wifi = true;  // Assume WiFi is available initially
uint8_t extra_button_base_idx;

uint8_t brightness;
#define DATASIZE 11

// Default Controller configuration
uint8_t joystick_count = 1;
uint32_t dimming_timeout = 0;

#include "shared.h"

// Global structs for controller state
SharedData *shared_memory_data;
SharedData current_controller_data;
SharedData previous_controller_state;

// Global file descriptors
int controller_board_fd;     // File descriptor for PSPi control board I2C communication
int virtual_gamepad_fd;      // File descriptor for virtual controller/gamepad
int wifi_monitor_fd;         // File descriptor for monitoring WiFi interface
int shared_memory_fd;        // File descriptor for inter-process shared memory

// Global netlink request structure
struct {
    struct nlmsghdr nlh;
    struct ifinfomsg ifi;
} wifi_status_request;

#define BUTTON_CONFIG_STICK 0
#define BUTTON_CONFIG_TRIGGER 1

// Add to global variables section
bool extra_buttons = false;
bool button_config = BUTTON_CONFIG_TRIGGER;  // Default to trigger configuration

void parse_command_line_args(int argc, char *argv[]) {
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--help") == 0 || strcmp(argv[i], "-h") == 0) {
            printf("Usage: [options]\n");
            printf("Options:\n");
            printf("  --nocrc                         Disable CRC checks\n");
            printf("  --joysticks <num>               Set number of joysticks, where <num> is between 0 and 2\n");
            printf("  --dim <seconds>                 Enable dimming after <seconds>, between 1 and 3600\n");
            printf("  --fast                          Enable fast mode (double input polling rate)\n");
            printf("  --nogamepad                     Disable all gamepad buttons and joysticks\n");
            printf("  --extrabuttons [trigger|stick]  Enable extra buttons (default: trigger)\n");
            printf("  --help, -h                      Display this help and exit\n");
            exit(0);
        } else if (strcmp(argv[i], "--nocrc") == 0) {
            enable_crc = 0;
            printf("CRC Disabled\n");
        } else if (strcmp(argv[i], "--joysticks") == 0) {
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
            polling_delay = FAST_POLLING_DELAY_MS;  // Set to 8ms for fast mode
        } else if (strcmp(argv[i], "--nogamepad") == 0) {
            printf("Gamepad disabled\n");
            gamepad_enabled = false;
        } else if (strcmp(argv[i], "--extrabuttons") == 0) {
            extra_buttons = true;
            // Check if next argument exists and is a valid configuration
            if (i + 1 < argc) {
                if (strcmp(argv[i + 1], "trigger") == 0) {
                    button_config = BUTTON_CONFIG_TRIGGER;
                    i++; // Skip the next argument
                } else if (strcmp(argv[i + 1], "stick") == 0) {
                    button_config = BUTTON_CONFIG_STICK;
                    i++; // Skip the next argument
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

// Initialize the CRC-16-CCITT lookup table
static void init_crc16_ccitt_table(void) {
    const uint16_t poly = 0x1021; // CRC-16-CCITT polynomial

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

// Compute CRC-16-CCITT using lookup table
uint16_t compute_crc16_ccitt(const uint8_t *data, uint8_t length) {
    uint16_t crc = 0xFFFF; // Initial value for CRC-16-CCITT

    for (uint8_t i = 0; i < length; i++) {
        // Use the lookup table to compute the CRC
        crc = (crc << 8) ^ crc16_ccitt_table[((crc >> 8) ^ data[i]) & 0xFF];
    }

    return crc;
}

void cleanup_resources() {
    close(wifi_monitor_fd);
    close(controller_board_fd);
    if (gamepad_enabled) {
        ioctl(virtual_gamepad_fd, UI_DEV_DESTROY);
        close(virtual_gamepad_fd);
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

    // Only update shared memory if read and CRC were successful
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

int setup_uinput_device(int uinput_fd) {
    struct uinput_user_dev uidev;
    memset(&uidev, 0, sizeof(uidev));
    // making compatible with 030000004c0500006802000010010000,PS3 Controller in the SDL Database
    // make the driver create all buttons and analog sticks, but only update the extra ones when enabled in the driver
    snprintf(uidev.name, UINPUT_MAX_NAME_SIZE, "PS3 Controller");
    uidev.id.bustype = BUS_USB;
    uidev.id.vendor = 0x054c;
    uidev.id.product = 0x0268;
    uidev.id.version = 0x0110;

    // Left Joystick
    uidev.absmin[ABS_X] = 40;
    uidev.absmax[ABS_X] = 215;
    uidev.absflat[ABS_X] = 20;
    uidev.absfuzz[ABS_X] = 20;
    uidev.absmin[ABS_Y] = 40;
    uidev.absmax[ABS_Y] = 215;
    uidev.absflat[ABS_Y] = 20;
    uidev.absfuzz[ABS_Y] = 20;

    // Right Joystick
    uidev.absmin[ABS_RX] = 40;
    uidev.absmax[ABS_RX] = 215;
    uidev.absflat[ABS_RX] = 20;
    uidev.absfuzz[ABS_RX] = 20;
    uidev.absmin[ABS_RY] = 40;
    uidev.absmax[ABS_RY] = 215;
    uidev.absflat[ABS_RY] = 20;
    uidev.absfuzz[ABS_RY] = 20;

    ssize_t ret = write(uinput_fd, &uidev, sizeof(uidev));
    if (ret < 0) {
        perror("Failed to write to uinput device in setup_uinput_device");
        return -1;
    }

    ioctl(uinput_fd, UI_SET_EVBIT, EV_KEY);
    for(int i = 0; i < 17; i++) {
        ioctl(uinput_fd, UI_SET_KEYBIT, BTN_TRIGGER_HAPPY1 + i);
    }

    ioctl(uinput_fd, UI_SET_EVBIT, EV_ABS);
    ioctl(uinput_fd, UI_SET_ABSBIT, ABS_X);
    ioctl(uinput_fd, UI_SET_ABSBIT, ABS_Y);
    ioctl(uinput_fd, UI_SET_ABSBIT, ABS_RX);
    ioctl(uinput_fd, UI_SET_ABSBIT, ABS_RY);

    if (ioctl(uinput_fd, UI_DEV_CREATE) < 0) {
        perror("Failed to create uinput device");
        return -1;
    }

    // Initialize joysticks to center position after device creation
    struct input_event events[5] = {
        {.type = EV_ABS, .code = ABS_X,  .value = 127},
        {.type = EV_ABS, .code = ABS_Y,  .value = 127},
        {.type = EV_ABS, .code = ABS_RX, .value = 127},
        {.type = EV_ABS, .code = ABS_RY, .value = 127},
        {.type = EV_SYN, .code = SYN_REPORT, .value = 0}
    };

    write(uinput_fd, events, sizeof(events));

    return 0;
}

void init_virtual_gamepad(void) {
    if (!gamepad_enabled) return;

    virtual_gamepad_fd = open("/dev/uinput", O_WRONLY | O_NONBLOCK);
    if(virtual_gamepad_fd < 0) {
        perror("Could not open uinput device");
        cleanup_resources();
        exit(1);
    }

    if (setup_uinput_device(virtual_gamepad_fd) != 0) {
        perror("Error setting up uinput device");
        close(virtual_gamepad_fd);
        cleanup_resources();
        exit(1);
    }
}

#define BUTTON_CONFIG_STICK 0
#define BUTTON_CONFIG_TRIGGER 1

void update_controller_data(int uinput_fd) {
    static const uint16_t button_map[] = {
        0x0002,  // select
        0x0000,  // left_stick (when in stick mode)
        0x0000,  // right_stick (when in stick mode)
        0x0004,  // start
        0x0400,  // dpad_up
        0x1000,  // dpad_right
        0x0800,  // dpad_down
        0x0200,  // dpad_left
        0x0000,  // left_stick (when in trigger mode)
        0x0000,  // right_stick (when in trigger mode)
        0x0100,  // lshoulder
        0x0080,  // rshoulder
        0x0020,  // y
        0x0040,  // b
        0x0008,  // a
        0x0010,  // x
        0x8000   // home
    };

    struct input_event events[20];
    int event_count = 0;

    uint16_t changed_buttons = previous_controller_state.buttons.raw ^ current_controller_data.buttons.raw;
    if (changed_buttons) {
        for (size_t i = 0; i < sizeof(button_map)/sizeof(button_map[0]); i++) {
            if (button_map[i] && (changed_buttons & button_map[i])) {
                events[event_count].type = EV_KEY;
                events[event_count].code = BTN_TRIGGER_HAPPY1 + i;
                events[event_count].value = (current_controller_data.buttons.raw & button_map[i]) != 0;
                event_count++;
            }
        }
    }

    // Handle left stick if enabled
    if (joystick_count >= 1) {
        if (previous_controller_state.left_stick_x != current_controller_data.left_stick_x) {
            events[event_count].type = EV_ABS;
            events[event_count].code = ABS_X;
            events[event_count].value = current_controller_data.left_stick_x;
            event_count++;
        }
        if (previous_controller_state.left_stick_y != current_controller_data.left_stick_y) {
            events[event_count].type = EV_ABS;
            events[event_count].code = ABS_Y;
            events[event_count].value = current_controller_data.left_stick_y;
            event_count++;
        }
    }

    // Handle right stick if enabled
    if (joystick_count == 2) {
        if (previous_controller_state.right_stick_x.raw != current_controller_data.right_stick_x.raw) {
            events[event_count].type = EV_ABS;
            events[event_count].code = ABS_RX;
            events[event_count].value = current_controller_data.right_stick_x.bits.position;
            event_count++;
        }
        if (previous_controller_state.right_stick_y.raw != current_controller_data.right_stick_y.raw) {
            events[event_count].type = EV_ABS;
            events[event_count].code = ABS_RY;
            events[event_count].value = current_controller_data.right_stick_y.bits.position;
            event_count++;
        }

        // Handle stick buttons if extra buttons are enabled
        if (extra_buttons) {
            // Use the global base index, right button is +1

            if (previous_controller_state.right_stick_x.bits.button != current_controller_data.right_stick_x.bits.button) {
                events[event_count].type = EV_KEY;
                events[event_count].code = BTN_TRIGGER_HAPPY1 + extra_button_base_idx + 1;
                events[event_count].value = current_controller_data.right_stick_x.bits.button;
                event_count++;
            }

            if (previous_controller_state.right_stick_y.bits.button != current_controller_data.right_stick_y.bits.button) {
                events[event_count].type = EV_KEY;
                events[event_count].code = BTN_TRIGGER_HAPPY1 + extra_button_base_idx;
                events[event_count].value = current_controller_data.right_stick_y.bits.button;
                event_count++;
            }
        }
    }

    // Only write if we have events plus sync
    if (event_count > 0) {
        events[event_count].type = EV_SYN;
        events[event_count].code = SYN_REPORT;
        events[event_count].value = 0;
        event_count++;

        write(uinput_fd, events, sizeof(struct input_event) * event_count);
    }
}

void init_wifi_monitoring(void) {
    wifi_monitor_fd = socket(AF_NETLINK, SOCK_RAW, NETLINK_ROUTE);
    if (wifi_monitor_fd == -1) {
        perror("Error creating netlink socket");
        has_wifi = 0;
        cleanup_resources();
        exit(1);
    }

    int ifindex = if_nametoindex(INTERFACE_NAME);
    if (ifindex == 0) {
        perror("Error getting interface index");
        has_wifi = 0;
        cleanup_resources();
        exit(1);
    }

    memset(&wifi_status_request, 0, sizeof(wifi_status_request));
    wifi_status_request.nlh.nlmsg_len = NLMSG_LENGTH(sizeof(struct ifinfomsg));
    wifi_status_request.nlh.nlmsg_flags = NLM_F_REQUEST;
    wifi_status_request.nlh.nlmsg_type = RTM_GETLINK;
    wifi_status_request.ifi.ifi_family = AF_UNSPEC;
    wifi_status_request.ifi.ifi_index = ifindex;
}

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

void check_wifi_status(void) {
    char wifi_status_buffer[4096];
    send(wifi_monitor_fd, &wifi_status_request, wifi_status_request.nlh.nlmsg_len, 0);
    int len = recv(wifi_monitor_fd, wifi_status_buffer, sizeof(wifi_status_buffer), 0);
    struct nlmsghdr *nh = (struct nlmsghdr *)wifi_status_buffer;
    bool check_connection = 0;

    if (nh->nlmsg_type == RTM_NEWLINK) {
        struct ifinfomsg *ifi = NLMSG_DATA(nh);
        wifi_enabled = ifi->ifi_flags & IFF_UP;
        check_connection = ifi->ifi_flags & IFF_RUNNING;

        if (check_connection != wifi_connected) {
            wifi_connected = check_connection;
            uint8_t i2c_data[4];
            i2c_data[0] = 0x20;
            i2c_data[1] = wifi_connected ? 1 : 0;
            write(controller_board_fd, i2c_data, 4);
        }
    }
}

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
    }
    else {
        is_idle = false;

        if (is_dim && current_controller_data.status_flags.bits.brightness == 0) {
            write_i2c_command(i2c_fd, CMD_BRIGHTNESS, brightness);
            is_dim = false;
        }

        previous_status = status;
    }
}

int main(int argc, char *argv[]) {
    parse_command_line_args(argc, argv);
    init_crc16_ccitt_table();
    init_i2c();
    init_virtual_gamepad();
    init_shared_memory();
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

        if (gamepad_enabled) {
            if (previous_controller_state.buttons.raw != current_controller_data.buttons.raw || memcmp(&previous_controller_state.left_stick_x, &current_controller_data.left_stick_x, 4) != 0) {
                update_controller_data(virtual_gamepad_fd);
                previous_controller_state = current_controller_data;
            }
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

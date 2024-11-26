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

unsigned int polling_delay = DEFAULT_POLLING_DELAY_MS;  // Default to 16ms

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

uint8_t brightness;
#define DATASIZE 11

// Default Controller configuration
uint8_t joystick_count = 1;
uint32_t dimming_timeout = 0;

#include "shared.h"

SharedData *shared_memory_data;
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

void parse_command_line_args(int argc, char *argv[]) {
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--help") == 0 || strcmp(argv[i], "-h") == 0) {
            printf("Usage: [options]\n");
            printf("Options:\n");
            printf("  --nocrc            Disable CRC checks\n");
            printf("  --joysticks <num>  Set number of joysticks, where <num> is between 0 and 2\n");
            printf("  --dim <seconds>    Enable dimming after <seconds>, between 1 and 3600\n");
            printf("  --fast             Enable fast mode (double input polling rate)\n");
            printf("  --nogamepad        Display the gamepad\n");
            printf("  --help, -h         Display this help and exit\n");
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
            gamepad_enabled = 0;
        }
    }
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

uint16_t compute_crc16_ccitt(const uint8_t *data, uint8_t length) { // change this and the data to be 16bit to match atmega.
    uint16_t crc = 0xFFFF; // Initial value for CRC-16-CCITT
    uint16_t poly = 0x1021; // Polynomial for CRC-16-CCITT

    for (uint8_t i = 0; i < length; i++) {
        crc ^= ((uint16_t)data[i] << 8);
        for (uint8_t j = 0; j < 8; j++) {
            if (crc & 0x8000) {
                crc = (crc << 1) ^ poly;
            } else {
                crc <<= 1;
            }
        }
    }
    return crc;
}

void update_controller_data(int uinput_fd) {
    struct input_event event;
    memset(&event, 0, sizeof(event));

    // Array defining button order for BTN_TRIGGER_HAPPY mappings
    const bool button_order[] = {
        shared_memory_data->buttons.bits.select,
        0,
        0,
        shared_memory_data->buttons.bits.start,
        shared_memory_data->buttons.bits.dpad_up,
        shared_memory_data->buttons.bits.dpad_right,
        shared_memory_data->buttons.bits.dpad_down,
        shared_memory_data->buttons.bits.dpad_left,
        shared_memory_data->right_stick_x.bits.button,
        shared_memory_data->right_stick_y.bits.button,
        shared_memory_data->buttons.bits.lshoulder,
        shared_memory_data->buttons.bits.rshoulder,
        shared_memory_data->buttons.bits.y,
        shared_memory_data->buttons.bits.b,
        shared_memory_data->buttons.bits.a,
        shared_memory_data->buttons.bits.x,
        shared_memory_data->buttons.bits.home
    };

    // Update buttons in specified order
    for(size_t i = 0; i < sizeof(button_order) / sizeof(button_order[0]); i++) {
        event.type = EV_KEY;
        event.code = BTN_TRIGGER_HAPPY1 + i;
        event.value = button_order[i];

        ssize_t ret = write(uinput_fd, &event, sizeof(event));
        if (ret < 0) {
            perror("Failed to write button event in update_controller_data");
        }
    }

    // Handle left stick if enabled
    if (joystick_count) {
        event.type = EV_ABS;
        event.code = ABS_X;
        event.value = shared_memory_data->left_stick_x;
        write(uinput_fd, &event, sizeof(event));

        event.code = ABS_Y;
        event.value = shared_memory_data->left_stick_y;
        write(uinput_fd, &event, sizeof(event));

        event.type = EV_SYN;
        event.code = SYN_REPORT;
        event.value = 0;
        write(uinput_fd, &event, sizeof(event));
    }

    // Handle right stick if enabled
    if (joystick_count == 2) {
        event.type = EV_ABS;
        event.code = ABS_RX;
        event.value = shared_memory_data->right_stick_x.bits.position;
        write(uinput_fd, &event, sizeof(event));

        event.code = ABS_RY;
        event.value = shared_memory_data->right_stick_y.bits.position;
        write(uinput_fd, &event, sizeof(event));

        event.type = EV_SYN;
        event.code = SYN_REPORT;
        event.value = 0;
        write(uinput_fd, &event, sizeof(event));
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

bool read_i2c_data(void) {
    if (read(controller_board_fd, shared_memory_data, DATASIZE) != DATASIZE) {
        perror("Failed to read from i2c device");
        sleep(1);
        return false;
    }
    if (enable_crc) {
        uint16_t computed_crc = compute_crc16_ccitt((const uint8_t*)shared_memory_data, 9);
        uint16_t received_crc = (shared_memory_data->crc_high << 8) | shared_memory_data->crc_low;
        if (computed_crc != received_crc) {
            printf("CRC Error - Expected: 0x%04X, Received: 0x%04X\n",
                   computed_crc, received_crc);
            crc_error_count++;
            return false;
        }
    }
    return true;
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

void manage_display_brightness(int i2c_fd) {
    uint32_t status = 0;
    status |= (uint32_t)shared_memory_data->buttons.raw << 18;
    status |= (uint32_t)(shared_memory_data->left_stick_x >> 4) << 4;
    status |= (uint32_t)(shared_memory_data->left_stick_y >> 4);

    if (previous_status == status) {
        if (is_idle == 0) {
            time_at_last_change = time(NULL);
        }
        is_idle = 1;
        if (time_at_last_change + dimming_timeout <= time(NULL)) {
            if (!is_dim) {
                uint8_t i2c_data[4];
                i2c_data[0] = 0x22;
                i2c_data[1] = 1;
                write(i2c_fd, i2c_data, 4);
                is_dim = 1;
                brightness = shared_memory_data->status_flags.bits.brightness;
                brightness++;
            }
        }
    } else {
        is_idle = 0;
        if (is_dim) {
            time_at_last_change = time(NULL);
            uint8_t temp = shared_memory_data->status_flags.bits.brightness;

            if (temp == 0) {
                uint8_t i2c_data[4];
                i2c_data[0] = 0x22;
                i2c_data[1] = brightness;
                write(i2c_fd, i2c_data, 4);
            }

            is_dim = 0;
        }
    }

    previous_status = status;
}

int main(int argc, char *argv[]) {
    parse_command_line_args(argc, argv);
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
            manage_display_brightness(controller_board_fd);
        }

        if (gamepad_enabled) {
            // Compare raw data instead of individual fields for efficiency
            if (memcmp(&previous_controller_state, shared_memory_data, sizeof(SharedData)) != 0) {
                update_controller_data(virtual_gamepad_fd);
                previous_controller_state = *shared_memory_data;
            }
        }

        wifi_check_trigger++;

        if (shared_memory_data->status_flags.bits.sleeping) {
            usleep(100000);
        } else {
            usleep(polling_delay);
        }
    }

    cleanup_resources();
    return 0;
}

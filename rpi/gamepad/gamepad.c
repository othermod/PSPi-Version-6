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
#include <linux/uinput.h>
#include <linux/input.h>
#include <time.h>

#define DEFAULT_POLLING_DELAY_MS 16000
#define FAST_POLLING_DELAY_MS 8000
#define DEFAULT_DIMMING_TIMEOUT_SEC 120
#define I2C_DEVICE_ADDRESS 0x10

// Append one input_event to an array and advance the count.
#define EMIT(ev, cnt, t, c, v) \
do { (ev)[(cnt)].type = (t); (ev)[(cnt)].code = (c); \
    (ev)[(cnt)].value = (v); (cnt)++; } while (0)

    // Global counter for power management
    int poweroff_counter = 0;

    unsigned int polling_delay = DEFAULT_POLLING_DELAY_MS;

    // Configuration flags
    bool enable_crc = true;
    bool verbose = false;
    bool is_dim = false;
    bool is_idle = false;
    uint32_t previous_status;
    time_t time_at_last_change;
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
                uint16_t vol_plus:1;     // bit 13 - Unused (Vol+)
                uint16_t vol_minus:1;    // bit 14 - Unused (Vol-)
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
    int virtual_keyboard_fd = -1;
    int virtual_mouse_fd = -1;
    int shared_memory_fd;

    #define BUTTON_CONFIG_STICK 0
    #define BUTTON_CONFIG_TRIGGER 1

    bool extra_buttons = false;
    bool button_config = BUTTON_CONFIG_TRIGGER;

    // Axis calibration defaults (shared by left and right sticks)
    int axis_min      = 40;
    int axis_max      = 215;
    int axis_flat     = 20;
    #define AXIS_FUZZ 4
    int axis_center_lx = 127;
    int axis_center_ly = 127;
    int axis_center_rx = 127;
    int axis_center_ry = 127;

    bool autocenter = false;

    void parse_command_line_args(int argc, char *argv[]) {
        for (int i = 1; i < argc; i++) {
            if (strcmp(argv[i], "--help") == 0 || strcmp(argv[i], "-h") == 0) {
                puts("Usage: [options]\n"
                "  --input <gamepad|mouse|none>   Select input device type (default: gamepad)\n"
                "  --nocrc                        Disable CRC checks\n"
                "  --joysticks <num>              Set number of joysticks (0-2, gamepad only)\n"
                "  --deadzone <value>             Set stick deadzone flat value (0-100, default: 20, gamepad only)\n"
                "  --autocenter                   Use stick position at startup as center point (gamepad only)\n"
                "  --dim <seconds>                Enable dimming after <seconds> idle (1-3600, default: 120)\n"
                "  --fast                         Enable fast mode (double input polling rate)\n"
                "  --verbose                      Show verbose output (e.g. CRC errors)\n"
                "  --extrabuttons [trigger|stick] Enable extra buttons (trigger/stick, gamepad only)\n"
                "  --help, -h                     Display this help and exit");
                exit(0);
            } else if (strcmp(argv[i], "--nocrc") == 0) {
                enable_crc = false;
                printf("CRC Disabled\n");
            } else if (strcmp(argv[i], "--verbose") == 0) {
                verbose = true;
                printf("Verbose mode enabled\n");
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
            } else if (strcmp(argv[i], "--deadzone") == 0) {
                if (i + 1 < argc) {
                    int dz = atoi(argv[++i]);
                    if (dz < 0 || dz > 100) {
                        printf("Invalid deadzone value. Must be between 0 and 100.\n");
                        exit(1);
                    }
                    axis_flat = dz;
                    printf("Deadzone: %d\n", axis_flat);
                } else {
                    printf("No value specified for --deadzone\n");
                    exit(1);
                }
            } else if (strcmp(argv[i], "--autocenter") == 0) {
                autocenter = true;
                printf("Autocenter enabled\n");
            } else if (strcmp(argv[i], "--extrabuttons") == 0) {
                if (input_type != INPUT_GAMEPAD) {
                    printf("Warning: --extrabuttons is only valid with --input gamepad\n");
                    continue;
                }
                if (i + 1 >= argc) {
                    printf("No value specified for --extrabuttons. Use trigger, stick, or disabled.\n");
                    exit(1);
                }
                if (strcmp(argv[i + 1], "disabled") == 0) {
                    extra_buttons = false;
                    i++;
                } else if (strcmp(argv[i + 1], "trigger") == 0) {
                    extra_buttons = true;
                    button_config = BUTTON_CONFIG_TRIGGER;
                    i++;
                } else if (strcmp(argv[i + 1], "stick") == 0) {
                    extra_buttons = true;
                    button_config = BUTTON_CONFIG_STICK;
                    i++;
                } else {
                    printf("Invalid extrabuttons value '%s'. Use trigger, stick, or disabled.\n", argv[i + 1]);
                    exit(1);
                }
                printf("Extra buttons: %s\n",
                       extra_buttons ? (button_config == BUTTON_CONFIG_TRIGGER ? "enabled (trigger)" : "enabled (stick)") : "disabled");
            } else {
                printf("Unknown argument '%s'\n", argv[i]);
                exit(1);
            }
        }
    }

    // CRC-16-CCITT lookup table
    static uint16_t crc16_ccitt_table[256];

    static void init_crc16_ccitt_table(void) {
        const uint16_t poly = 0x1021;
        for (uint16_t i = 0; i < 256; i++) {
            uint16_t crc = i << 8;
            for (uint8_t j = 0; j < 8; j++)
                crc = (crc & 0x8000) ? (crc << 1) ^ poly : crc << 1;
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

        void init_virtual_keyboard(void) {
        virtual_keyboard_fd = open("/dev/uinput", O_WRONLY | O_NONBLOCK);
        if (virtual_keyboard_fd < 0) {
            perror("Could not open uinput device for keyboard");
            return;
        }

        ioctl(virtual_keyboard_fd, UI_SET_EVBIT, EV_KEY);
        ioctl(virtual_keyboard_fd, UI_SET_KEYBIT, KEY_VOLUMEUP);
        ioctl(virtual_keyboard_fd, UI_SET_KEYBIT, KEY_VOLUMEDOWN);

        struct uinput_user_dev uidev = {0};
        snprintf(uidev.name, UINPUT_MAX_NAME_SIZE, "PSPi Keyboard");
        uidev.id = (struct input_id){ BUS_USB, 0x1234, 0x5678, 0 };

        if (write(virtual_keyboard_fd, &uidev, sizeof(uidev)) < 0) {
            perror("Failed to write uinput_user_dev for keyboard");
            close(virtual_keyboard_fd);
            virtual_keyboard_fd = -1;
            return;
        }
        if (ioctl(virtual_keyboard_fd, UI_DEV_CREATE) < 0) {
            perror("Failed to create uinput keyboard device");
            close(virtual_keyboard_fd);
            virtual_keyboard_fd = -1;
            return;
        }
        printf("Virtual keyboard created\n");
    }

void cleanup_resources(void) {
        if (virtual_gamepad_fd >= 0) {
            ioctl(virtual_gamepad_fd, UI_DEV_DESTROY);
            close(virtual_gamepad_fd);
        }
        if (virtual_keyboard_fd >= 0) {
            ioctl(virtual_keyboard_fd, UI_DEV_DESTROY);
            close(virtual_keyboard_fd);
        }
        if (virtual_mouse_fd >= 0) {
            ioctl(virtual_mouse_fd, UI_DEV_DESTROY);
            close(virtual_mouse_fd);
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
        if (ioctl(controller_board_fd, I2C_SLAVE, I2C_DEVICE_ADDRESS) < 0) {
            perror("Failed to set i2c slave");
            cleanup_resources();
            exit(1);
        }
        uint8_t probe;
        if (read(controller_board_fd, &probe, 1) < 1) {
            fprintf(stderr, "No I2C device found at address 0x10\n");
            cleanup_resources();
            exit(1);
        }
    }

    bool read_i2c_data(void) {
        read(controller_board_fd, &current_controller_data, DATASIZE);
        if (enable_crc) {
            uint16_t computed_crc = compute_crc16_ccitt((const uint8_t*)&current_controller_data, 9);
            uint16_t received_crc = (current_controller_data.crc_high << 8) | current_controller_data.crc_low;
            if (computed_crc != received_crc) {
                if (verbose) {
                    printf("CRC Error - Expected: 0x%04X, Received: 0x%04X | Data: ",
                           computed_crc, received_crc);
                    const uint8_t *d = (const uint8_t *)&current_controller_data;
                    for (int b = 0; b < DATASIZE; b++) printf("0x%02X ", d[b]);
                    printf("\n");
                }
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
        if (shared_memory_fd < 0) {
            perror("Failed to open shared memory");
            cleanup_resources();
            exit(1);
        }
        if (ftruncate(shared_memory_fd, sizeof(SharedData)) < 0) {
            perror("Failed to resize shared memory");
            cleanup_resources();
            exit(1);
        }
        shared_memory_data = mmap(0, sizeof(SharedData), PROT_WRITE, MAP_SHARED, shared_memory_fd, 0);
        if (shared_memory_data == MAP_FAILED) {
            perror("Failed to map shared memory");
            cleanup_resources();
            exit(1);
        }
    }

    // ---- Gamepad uinput ----

    // Set all four calibration fields for one ABS axis in a uinput_user_dev.
    #define SET_ABS(dev, ax, mn, mx, fl, fz) \
    do { (dev).absmin[(ax)]=(mn); (dev).absmax[(ax)]=(mx); \
        (dev).absflat[(ax)]=(fl); (dev).absfuzz[(ax)]=(fz); } while(0)

        int setup_uinput_gamepad(int uinput_fd) {
            // UI_SET_* ioctls must come before writing uinput_user_dev.
            ioctl(uinput_fd, UI_SET_EVBIT, EV_KEY);
            // Keycodes match the real PS3 hid-sony driver layout, producing button
            // indices that match SDL gamecontrollerdb GUID 030000004c0500006802000011810000:
            //   b0=a(cross)  b1=b(circle)  b2=y(triangle)  b3=x(square)
            //   b4=leftshoulder(L1)    b5=rightshoulder(R1)
            //   b6=BTN_TL2  b7=BTN_TR2  (index placeholders; L2/R2 are axes a2/a5)
            //   b8=back  b9=start  b10=guide
            //   b11=leftstick(L3)  b12=rightstick(R3)
            //   b13=dpup  b14=dpdown  b15=dpleft  b16=dpright
            // BTN_TL2/BTN_TR2 must be registered to push BTN_SELECT to index b8.
            // In --extrabuttons trigger mode they also receive button events so ES
            // sees L2/R2 as digital buttons (pageup/pagedown) in addition to axes.
            static const uint16_t ps3_keys[] = {
                BTN_SOUTH,      // b0  - a / cross
                BTN_EAST,       // b1  - b / circle
                BTN_NORTH,      // b2  - y / triangle
                BTN_WEST,       // b3  - x / square
                BTN_TL,         // b4  - leftshoulder  (L1)
                BTN_TR,         // b5  - rightshoulder (R1)
                BTN_TL2,        // b6  - L2 button (also emitted as ABS_Z axis)
                BTN_TR2,        // b7  - R2 button (also emitted as ABS_RZ axis)
                BTN_SELECT,     // b8  - back
                BTN_START,      // b9  - start
                BTN_MODE,       // b10 - guide / PS button
                BTN_THUMBL,     // b11 - leftstick  (L3, extra_buttons stick)
                BTN_THUMBR,     // b12 - rightstick (R3, extra_buttons stick)
                BTN_DPAD_UP,    // b13 - dpup
                BTN_DPAD_DOWN,  // b14 - dpdown
                BTN_DPAD_LEFT,  // b15 - dpleft
                BTN_DPAD_RIGHT, // b16 - dpright
            };
            for (size_t i = 0; i < sizeof(ps3_keys)/sizeof(ps3_keys[0]); i++)
                ioctl(uinput_fd, UI_SET_KEYBIT, ps3_keys[i]);

            // Axis order must match hid-sony: X, Y, Z(L2), RX, RY, RZ(R2).
            // joydev assigns sequential indices so SDL sees:
            //   a0=leftx  a1=lefty  a2=lefttrigger  a3=rightx  a4=righty  a5=righttrigger
            ioctl(uinput_fd, UI_SET_EVBIT, EV_ABS);
            ioctl(uinput_fd, UI_SET_ABSBIT, ABS_X);
            ioctl(uinput_fd, UI_SET_ABSBIT, ABS_Y);
            ioctl(uinput_fd, UI_SET_ABSBIT, ABS_Z);    // L2 trigger axis
            ioctl(uinput_fd, UI_SET_ABSBIT, ABS_RX);
            ioctl(uinput_fd, UI_SET_ABSBIT, ABS_RY);
            ioctl(uinput_fd, UI_SET_ABSBIT, ABS_RZ);   // R2 trigger axis

            struct uinput_user_dev uidev = {0};
            snprintf(uidev.name, UINPUT_MAX_NAME_SIZE, "PS3 Controller");
            uidev.id = (struct input_id){ BUS_USB, 0x054c, 0x0268, 0x8111 };
            SET_ABS(uidev, ABS_X,  axis_min, axis_max, axis_flat, AXIS_FUZZ);
            SET_ABS(uidev, ABS_Y,  axis_min, axis_max, axis_flat, AXIS_FUZZ);
            SET_ABS(uidev, ABS_Z,  0, 255, 0, 0);      // L2: digital 0 or 255, no deadzone
            // Right stick: 7-bit position field shifted to 8-bit space, same range as left.
            SET_ABS(uidev, ABS_RX, axis_min, axis_max, axis_flat, AXIS_FUZZ);
            SET_ABS(uidev, ABS_RY, axis_min, axis_max, axis_flat, AXIS_FUZZ);
            SET_ABS(uidev, ABS_RZ, 0, 255, 0, 0);      // R2: digital 0 or 255, no deadzone

            if (write(uinput_fd, &uidev, sizeof(uidev)) < 0) {
                perror("Failed to write uinput_user_dev");
                return -1;
            }
            if (ioctl(uinput_fd, UI_DEV_CREATE) < 0) {
                perror("Failed to create uinput device");
                return -1;
            }

            // Initialize axes: sticks to center, triggers to 0 (not pressed).
            struct input_event init_events[7];
            int n = 0;
            EMIT(init_events, n, EV_ABS, ABS_X,  axis_center_lx);
            EMIT(init_events, n, EV_ABS, ABS_Y,  axis_center_ly);
            EMIT(init_events, n, EV_ABS, ABS_Z,  0);
            EMIT(init_events, n, EV_ABS, ABS_RX, axis_center_rx);
            EMIT(init_events, n, EV_ABS, ABS_RY, axis_center_ry);
            EMIT(init_events, n, EV_ABS, ABS_RZ, 0);
            EMIT(init_events, n, EV_SYN, SYN_REPORT, 0);
            write(uinput_fd, init_events, sizeof(struct input_event) * n);
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

            static const uint16_t mouse_keys[] = {
                KEY_BACK, KEY_FORWARD, KEY_LEFTMETA,
                BTN_LEFT, BTN_RIGHT,
                KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN, KEY_ENTER,
            };
            ioctl(virtual_mouse_fd, UI_SET_EVBIT, EV_KEY);
            for (size_t i = 0; i < sizeof(mouse_keys)/sizeof(mouse_keys[0]); i++)
                ioctl(virtual_mouse_fd, UI_SET_KEYBIT, mouse_keys[i]);

            ioctl(virtual_mouse_fd, UI_SET_EVBIT, EV_REL);
            ioctl(virtual_mouse_fd, UI_SET_RELBIT, REL_X);
            ioctl(virtual_mouse_fd, UI_SET_RELBIT, REL_Y);

            struct uinput_setup usetup = {0};
            usetup.id = (struct input_id){ BUS_USB, 0x1234, 0x5678, 0 };
            strcpy(usetup.name, "Example device");
            ioctl(virtual_mouse_fd, UI_DEV_SETUP, &usetup);
            ioctl(virtual_mouse_fd, UI_DEV_CREATE);
            sleep(1);
        }

        // ---- Gamepad event emission ----

        typedef struct { uint16_t hw_mask; uint16_t keycode; } ButtonMap;
        static const ButtonMap button_map[] = {
            { 0x0002, BTN_SELECT     },  // select   -> b8  back
            { 0x0004, BTN_START      },  // start    -> b9
            { 0x0400, BTN_DPAD_UP    },  // dpup     -> b13
            { 0x1000, BTN_DPAD_RIGHT },  // dpright  -> b16
            { 0x0800, BTN_DPAD_DOWN  },  // dpdown   -> b14
            { 0x0200, BTN_DPAD_LEFT  },  // dpleft   -> b15
            // L2/R2 handled in extra_buttons as ABS_Z/ABS_RZ axes + BTN_TL2/BTN_TR2
            { 0x0100, BTN_TL         },  // L1       -> b4  leftshoulder
            { 0x0080, BTN_TR         },  // R1       -> b5  rightshoulder
            { 0x0020, BTN_NORTH      },  // triangle -> b2  y
            { 0x0040, BTN_EAST       },  // circle   -> b1  b
            { 0x0008, BTN_SOUTH      },  // cross    -> b0  a
            { 0x0010, BTN_WEST       },  // square   -> b3  x
            { 0x8000, BTN_MODE       },  // PS btn   -> b10 guide
        };

        void update_gamepad_events(int uinput_fd) {
            struct input_event events[20];
            int n = 0;

            uint16_t changed = previous_controller_state.buttons.raw ^ current_controller_data.buttons.raw;
            for (size_t i = 0; changed && i < sizeof(button_map)/sizeof(button_map[0]); i++) {
                if (changed & button_map[i].hw_mask)
                    EMIT(events, n, EV_KEY, button_map[i].keycode,
                         (current_controller_data.buttons.raw & button_map[i].hw_mask) != 0);
            }

            if (joystick_count >= 1) {
                if (previous_controller_state.left_stick_x != current_controller_data.left_stick_x)
                    EMIT(events, n, EV_ABS, ABS_X, current_controller_data.left_stick_x);
                if (previous_controller_state.left_stick_y != current_controller_data.left_stick_y)
                    EMIT(events, n, EV_ABS, ABS_Y, current_controller_data.left_stick_y);
            }

            if (joystick_count == 2) {
                if (previous_controller_state.right_stick_x.raw != current_controller_data.right_stick_x.raw)
                    EMIT(events, n, EV_ABS, ABS_RX, current_controller_data.right_stick_x.bits.position << 1);
                if (previous_controller_state.right_stick_y.raw != current_controller_data.right_stick_y.raw)
                    EMIT(events, n, EV_ABS, ABS_RY, current_controller_data.right_stick_y.bits.position << 1);
            }

            if (extra_buttons) {
                if (button_config == BUTTON_CONFIG_TRIGGER) {
                    // L2/R2: emit as both axis (SDL/RetroArch) and button (ES pageup/pagedown)
                    if (previous_controller_state.right_stick_y.bits.button != current_controller_data.right_stick_y.bits.button) {
                        EMIT(events, n, EV_ABS, ABS_Z,   current_controller_data.right_stick_y.bits.button ? 255 : 0);
                        EMIT(events, n, EV_KEY, BTN_TL2, current_controller_data.right_stick_y.bits.button);
                    }
                    if (previous_controller_state.right_stick_x.bits.button != current_controller_data.right_stick_x.bits.button) {
                        EMIT(events, n, EV_ABS, ABS_RZ,  current_controller_data.right_stick_x.bits.button ? 255 : 0);
                        EMIT(events, n, EV_KEY, BTN_TR2, current_controller_data.right_stick_x.bits.button);
                    }
                } else {
                    // L3/R3 stick click
                    if (previous_controller_state.right_stick_y.bits.button != current_controller_data.right_stick_y.bits.button)
                        EMIT(events, n, EV_KEY, BTN_THUMBL, current_controller_data.right_stick_y.bits.button);
                    if (previous_controller_state.right_stick_x.bits.button != current_controller_data.right_stick_x.bits.button)
                        EMIT(events, n, EV_KEY, BTN_THUMBR, current_controller_data.right_stick_x.bits.button);
                }
            }

            if (n > 0) {
                EMIT(events, n, EV_SYN, SYN_REPORT, 0);
                write(uinput_fd, events, sizeof(struct input_event) * n);
            }
        }

        // ---- Mouse event emission ----

        #define AXIS_CENTER 127
        #define AXIS_THRESHOLD_LOW 112
        #define AXIS_THRESHOLD_HIGH 142

            void update_keyboard_events(void) {
        if (virtual_keyboard_fd < 0) return;

        struct input_event events[4];
        int n = 0;

        if (previous_controller_state.buttons.bits.vol_plus != current_controller_data.buttons.bits.vol_plus)
            EMIT(events, n, EV_KEY, KEY_VOLUMEUP, current_controller_data.buttons.bits.vol_plus);
        if (previous_controller_state.buttons.bits.vol_minus != current_controller_data.buttons.bits.vol_minus)
            EMIT(events, n, EV_KEY, KEY_VOLUMEDOWN, current_controller_data.buttons.bits.vol_minus);

        if (n > 0) {
            EMIT(events, n, EV_SYN, SYN_REPORT, 0);
            write(virtual_keyboard_fd, events, sizeof(struct input_event) * n);
        }
    }

void update_mouse_events(int uinput_fd) {
            struct input_event events[20];
            int n = 0;

            // Left stick -> relative mouse movement
            bool x_moving = current_controller_data.left_stick_x > AXIS_THRESHOLD_HIGH ||
            current_controller_data.left_stick_x < AXIS_THRESHOLD_LOW;
            bool y_moving = current_controller_data.left_stick_y > AXIS_THRESHOLD_HIGH ||
            current_controller_data.left_stick_y < AXIS_THRESHOLD_LOW;

            if (previous_mouse_data.left_stick_x != current_controller_data.left_stick_x || x_moving) {
                EMIT(events, n, EV_REL, REL_X, (current_controller_data.left_stick_x - AXIS_CENTER) / 16);
                previous_mouse_data.left_stick_x = current_controller_data.left_stick_x;
            }
            if (previous_mouse_data.left_stick_y != current_controller_data.left_stick_y || y_moving) {
                EMIT(events, n, EV_REL, REL_Y, (current_controller_data.left_stick_y - AXIS_CENTER) / 16);
                previous_mouse_data.left_stick_y = current_controller_data.left_stick_y;
            }

            // Buttons: hw bitmask -> key code table
            static const ButtonMap mouse_map[] = {
                { 1 << 2,  KEY_ENTER    },  // start
                { 1 << 3,  BTN_LEFT     },  // a
                { 1 << 6,  BTN_RIGHT    },  // b
                { 1 << 7,  KEY_FORWARD  },  // rshoulder
                { 1 << 8,  KEY_BACK     },  // lshoulder
                { 1 << 9,  KEY_LEFT     },  // dpad_left
                { 1 << 10, KEY_UP       },  // dpad_up
                { 1 << 11, KEY_DOWN     },  // dpad_down
                { 1 << 12, KEY_RIGHT    },  // dpad_right
                { 1 << 15, KEY_LEFTMETA },  // home
            };
            uint16_t changed_buttons = previous_mouse_data.buttons.raw ^ current_controller_data.buttons.raw;
            for (size_t i = 0; changed_buttons && i < sizeof(mouse_map)/sizeof(mouse_map[0]); i++) {
                if (changed_buttons & mouse_map[i].hw_mask)
                    EMIT(events, n, EV_KEY, mouse_map[i].keycode,
                         (current_controller_data.buttons.raw & mouse_map[i].hw_mask) != 0);
            }
            if (changed_buttons)
                previous_mouse_data.buttons.raw = current_controller_data.buttons.raw;

            if (n > 0) {
                EMIT(events, n, EV_SYN, SYN_REPORT, 0);
                write(uinput_fd, events, sizeof(struct input_event) * n);
            }
        }

        // ---- Idle / dimming ----

        static inline time_t monotonic_seconds(void) {
            struct timespec ts;
            clock_gettime(CLOCK_MONOTONIC, &ts);
            return ts.tv_sec;
        }

        void check_idle_state(int i2c_fd) {
            uint32_t status = (current_controller_data.buttons.raw << 18) |
            ((current_controller_data.left_stick_x & 0xF0) << 4) |
            (current_controller_data.left_stick_y >> 4);

            const time_t current_time = monotonic_seconds();

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

        void sample_axis_centers(void) {
            read_i2c_data();
            axis_center_lx = current_controller_data.left_stick_x;
            axis_center_ly = current_controller_data.left_stick_y;
            axis_center_rx = current_controller_data.right_stick_x.bits.position << 1;
            axis_center_ry = current_controller_data.right_stick_y.bits.position << 1;
            printf("Axis centers: lx=%d ly=%d rx=%d ry=%d\n",
                   axis_center_lx, axis_center_ly, axis_center_rx, axis_center_ry);
        }

        // ---- Main ----

        int main(int argc, char *argv[]) {
            parse_command_line_args(argc, argv);
            init_crc16_ccitt_table();
            init_i2c();
            init_shared_memory();
            if (autocenter) {
                sample_axis_centers();
            }

            switch (input_type) {
                case INPUT_GAMEPAD:
                    init_virtual_gamepad();
                    init_virtual_keyboard();
                    break;
                case INPUT_MOUSE:
                    init_virtual_mouse();
                    break;
                case INPUT_NONE:
                    break;
            }

            while (1) {
                if (!read_i2c_data()) {
                    continue;
                }

                check_for_shutdown_condition();

                if (dimming_timeout) {
                    check_idle_state(controller_board_fd);
                }

                switch (input_type) {
                    case INPUT_GAMEPAD:
                        if (previous_controller_state.buttons.raw != current_controller_data.buttons.raw ||
                            memcmp(&previous_controller_state.left_stick_x, &current_controller_data.left_stick_x, 4) != 0) {
                            update_gamepad_events(virtual_gamepad_fd);
                            update_keyboard_events();
                        previous_controller_state = current_controller_data;
                            }
                            break;
                    case INPUT_MOUSE:
                        update_mouse_events(virtual_mouse_fd);
                        break;
                    case INPUT_NONE:
                        break;
                }

                if (current_controller_data.status_flags.bits.sleeping) {
                    usleep(100000);
                } else {
                    usleep(polling_delay);
                }
            }

            cleanup_resources();
            return 0;
        }

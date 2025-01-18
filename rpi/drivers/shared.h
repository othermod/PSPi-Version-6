#ifndef SHARED_DATA_H
#define SHARED_DATA_H

#include <stdint.h>

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
            uint8_t reserved:1;       // Bit 3: Reserved for future use
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



#endif // SHARED_DATA_H

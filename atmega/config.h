// System Configuration
#define NORMAL_MODE_LOOP_MS 1       // Main loop interval in ms
#define SLEEP_MODE_LOOP_MS 5       // Sleep mode loop interval in ms

// Button configuration macros
#define BTN_DEBOUNCE_LOOPS 10  // Buttons will remain "pressed" for this many loops

// Poweroff Configuration
#define RPI_TIMEOUT 500       // RPi detection timeout number of loops
#define PWR_DOWN_DELAY 10000  // Power down delay in ms

// Sleep Configuration
#define SLEEP_EXIT_LOOPS 100    // Number of consecutive loops needed to exit sleep mode (100 * SLEEP_MODE_LOOP_MS = 500ms)

#define I2C_ADDR 0x10
#define I2C_IDLE_TRIGGER 200    // I2C timeout in number of NORMAL_MODE_LOOP_MS loops

// EEPROM Addresses
#define EEPROM_BRIGHT_ADDR 0
#define EEPROM_MUTE_ADDR 4

// Battery Thresholds (ADC values)
#define BAT_LOW 1095     // Low battery: 3.208V
#define BAT_GOOD 1216    // Good battery: 3.562V

// Brightness Configuration
#define BRIGHTNESS_DEFAULT 4 // 0-7 are valid

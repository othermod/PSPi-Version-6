#include <Wire.h>
#include <EEPROM.h>

// System state and I2C data structures
struct SystemState {
  // Input states
  uint16_t shiftRegister;   // Combined shift register input
  uint8_t debounceCount[16];  // Keep array of counters
  bool dispPressed;           // Corrected from uint16_t
  bool mutePressed;

  // System measurements
  uint16_t sysVolt;
  uint16_t batVolt;
  uint16_t rpiTimeout;
  uint8_t idleCounter;
  uint8_t powerLED;

  // systemStatus flags
  bool batLow;
  bool mute;
  bool idle;
  bool sleeping;
  bool forceLedOrange;
  bool sleepDir;
  bool wifiEnabled;
  uint8_t sleepExitCounter;
};

struct i2cStructure {
    uint16_t buttons;  // Combined button states
    uint8_t senseSys;
    uint8_t senseBat;
    union {
        struct Status {
            uint8_t brightness : 3;  // Bits 0-2: Display brightness level (1-8)
            bool reserved : 1;       // Bit 3: Reserved for future use
            bool sdPressed : 1;      // Bit 4: SD button status
            bool sleeping : 1;       // Bit 5: Sleep status
            bool leftSwitch : 1;     // Bit 6: Left switch status
            bool muted : 1;          // Bit 7: Mute status
        } status;
        uint8_t systemStatus;        // Access as raw byte
    };
    uint8_t joyLX;
    uint8_t joyLY;
    uint8_t joyRX;
    uint8_t joyRY;
    uint8_t crc16H;
    uint8_t crc16L;
};

// Global state declarations
SystemState state;
i2cStructure i2cdata;
volatile byte rxData[3];
volatile bool pendingCommand = false;
unsigned long lastUpdateTime = 0;

#include "config.h"
#include "low_level_commands.h"
#include "high_level_commands.h"

void setup() {
  initHardware();
  // initialize settings with defaults
  state.sysVolt = BAT_GOOD;
  i2cdata.status.brightness = BRIGHTNESS_DEFAULT;
  state.powerLED = LED_FULL_GREEN;
  state.idle = true; // start with audio muted. make sure it is muted in hardware
  state.idleCounter = 0; // prob not needed
  
  readEEPROM();
  
  Wire.begin(I2C_ADDR);
  Wire.onRequest(onRequest);
  Wire.onReceive(onReceive);

  startupSequence(); 
}

void loop() {
  checkForIncomingI2CCommand();     // Process any pending I2C commands immediately
  
  unsigned long currentTime = millis();
  if (UPDATE_INTERVAL_REACHED) {    // Check if it's time to scan inputs
    lastUpdateTime = currentTime;
    mandatoryFunctions();           // Always update critical system states at interval
    if (state.sleeping) {
      sleepModeFunctions();         // update only when in sleep mode (at lower frequency)
    } else {
      normalModeFunctions();        // update only when in normal mode
    }
  }
}

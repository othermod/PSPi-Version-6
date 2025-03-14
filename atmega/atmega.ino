#include <Wire.h>
#include <EEPROM.h>

struct SystemState {
  uint8_t debounceCount[16];
  bool dispPressed;
  bool mutePressed;
  uint16_t sysVolt;
  uint16_t batVolt;
  uint16_t rpiTimeout;
  uint8_t idleTimeout;
  uint8_t powerLED;
  bool batLow;
  bool mute;
  bool idle;
  bool sleeping;
  bool forceLedOrange;
  bool sleepPulseDirection;
  uint8_t wifiState;     // 0=disabled, 1=enabled, 2=connecting
  uint8_t wifiBlinkCounter;  // Counter for WiFi LED blinking - will roll over naturally
  bool crcEnabled;
  uint8_t sleepExitCounter;
};

struct i2cStructure {
  uint16_t buttons;  // Combined button states
  uint8_t senseSys;
  uint8_t senseBat;
  union {
    struct Status {
      uint8_t brightness : 3;  // Bits 0-2: Display brightness level (1-8)
      bool headphones : 1;     // Bit 3: Headphone plug status. 0 = unplugged
      bool sdPressed : 1;      // Bit 4: SD button status
      bool sleeping : 1;       // Bit 5: Sleep status
      bool leftSwitch : 1;     // Bit 6: Left switch status
      bool muted : 1;          // Bit 7: Mute status
    } status;
    uint8_t systemStatus;      // Access as full byte
  };
  uint8_t joyLX;
  uint8_t joyLY;
  union {
    struct JoyRX {
      bool extraButton : 1;   // Bit 0: Button state from BTN_EXTRA1
      uint8_t analog : 7;      // Bits 1-7: Analog value
    } joyRXBits;
    uint8_t joyRX;             // Access as full byte
  };
  union {
    struct JoyRY {
      bool extraButton : 1;   // Bit 0: Button state from BTN_EXTRA2
      uint8_t analog : 7;      // Bits 1-7: Analog value
    } joyRYBits;
    uint8_t joyRY;             // Access as full byte
  };
  uint8_t crc16H;
  uint8_t crc16L;
};

SystemState state;
i2cStructure i2cdata;
volatile byte rxData[3];
volatile bool pendingCommand = false;
unsigned long lastUpdateTime = 0;

#include "defines.h"
#include "functions.h"

void setup() {
  initHardware();
  state.sysVolt = BAT_GOOD;
  state.powerLED = LED_FULL_GREEN;
  state.idle = true; // start with audio muted. make sure it is muted in hardware
  //EN_AMP (D0): IP,NP
  //EN_AUDIO_POWER (D7): OP,DL
  state.idleTimeout = 0;
  state.rpiTimeout = 1; // must be > 0 so display turns on when RPi is detected
  state.crcEnabled = true;
  state.wifiState = 0; // Initialize WiFi as disabled

  readEEPROM(); // reads mute and brightness from eeprom. doesnt yet set them in hardware.

  Wire.begin(I2C_ADDR);
  Wire.onRequest(onRequest);
  Wire.onReceive(onReceive);

  //delay(500);         // this is here to prevent a flicker if the Pi GPIO isn't stable at poweroff. still needed?
  setPinHigh(EN_5V);  // this powers the raspberry pi on. EN_5V pin was OP,DL at startup
  //disableDisplay();   // not needed. pin is already low
}

void normalModeFunctions() {
  readJoysticks();
  readSPIButtons();
  checkMuteButton();
  checkLeftSwitch();
  checkShutdownButton();
  checkDisplayButton();
  checkHeadphones();
  
  // Handle WiFi LED blinking if in connecting state
  if (state.wifiState == 2) {
    toggleWiFiLED();
  }
}

void mandatoryFunctions() {
  readBattery();
  checkHoldSwitch();
  checkForInactiveI2C();
  checkRPi();
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

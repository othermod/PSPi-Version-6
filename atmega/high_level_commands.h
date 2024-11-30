// I2C Command IDs
#define CMD_WIFI 0x20
#define CMD_LED 0x21
#define CMD_BRIGHT 0x22
#define CMD_MUTE 0x23

#define FADE_TO_ORANGE 0
#define FADE_TO_GREEN 1

void restoreBrightnessFromEEPROM() {
  i2cdata.status.brightness = EEPROM.read(EEPROM_BRIGHT_ADDR); // Load brightness from EEPROM
}

void restoreMuteStatusFromEEPROM() {
  state.mute = EEPROM.read(EEPROM_MUTE_ADDR) == 1;
}

void storeSettings() {
    EEPROM.update(EEPROM_BRIGHT_ADDR, i2cdata.status.brightness);
    EEPROM.update(EEPROM_MUTE_ADDR, state.mute);
}

void enableDisplay() {
    initBacklight();
    setBrightness();
}

void heartbeatLED() {
    state.powerLED += state.sleepDir ? 1 : -1;
    if (state.powerLED == LED_FULL_GREEN) {
        state.sleepDir = !state.sleepDir;
        delay(1000); // pause only when LED is full green
    } else if (state.powerLED == LED_FULL_ORANGE) {
        state.sleepDir = !state.sleepDir;
    }
    if (state.batLow) state.powerLED = LED_FULL_ORANGE; // always set power led to orange if battery is low
    togglePowerLED();
}

void checkMuteButton() { // this does into hl
  if (READ_MUTE_BUTTON) {
    state.mutePressed = true;
  } else if (state.mutePressed) { // checks whether a previously pressed button was released. only occurs if mute is not pressed on this loop
    state.mute = !state.mute;
    toggleAudioCircuit();
    state.mutePressed = false;
  }
}

void enterSleep() {
    i2cdata.status.sleeping = true;
    state.sleeping = true;
    state.sleepExitCounter = 0;
    disableDisplay();
    toggleAudioCircuit();
    if (state.batLow || state.forceLedOrange) {
        state.sleepDir = FADE_TO_GREEN;
        state.powerLED = LED_FULL_ORANGE;
    } else {
        state.sleepDir = FADE_TO_ORANGE;
        state.powerLED = LED_FULL_GREEN;
    }
}

void exitSleep() {
    i2cdata.status.sleeping = false;
    state.sleeping = false;
    enableDisplay();
    toggleAudioCircuit();
    togglePowerLED();
}

void checkHoldSwitch() {
    bool holdSwitchUp = readPin(BTN_HLD);
    if (state.sleeping) {
        // Handle sleep exit logic
        if (holdSwitchUp) {
            state.sleepExitCounter++;
            if (state.sleepExitCounter == SLEEP_EXIT_LOOPS) {
                exitSleep();
            }
        } else {
            state.sleepExitCounter = 0;  // Reset counter if switch goes low. Prevents momentary LCD flicker caused by worn out power switches.
        }
    } else if (!holdSwitchUp) {
        enterSleep();
    }
}

void checkRPi() {
    if (readPin(RPI_DET)) {
        if (state.rpiTimeout) {
            enableDisplay();
            state.rpiTimeout = 0;
        }
    } else {
        if (!state.rpiTimeout) disableDisplay();
        if (state.rpiTimeout > RPI_TIMEOUT) {
            storeSettings();
            setPinLow(EN_5V);
            delay(PWR_DOWN_DELAY);
        } else {
            state.rpiTimeout++;
        }
    }
}

void processI2CCommand() {
    switch (rxData[0]) {
        case CMD_WIFI:
            state.wifiEnabled = rxData[1];
            toggleWiFiLED();
            break;
            
        case CMD_LED:
            state.forceLedOrange = rxData[1];
            togglePowerLED();
            break;
            
        case CMD_BRIGHT:
            if (rxData[1] >= 1 && rxData[1] <= 8) {
                i2cdata.status.brightness = rxData[1] - 1;  // Store 1-8 to the status, subtract 1 so its correct
                if (!state.sleeping) { // don't actually set it while in sleep mode. itll set when returning from sleep.
                  setBrightness();
                }
            }
            break;
            
        case CMD_MUTE:
            state.mute = rxData[1];
            if (!state.sleeping) { // don't actually set it while in sleep mode. itll set when returning from sleep.
              toggleAudioCircuit();
            }
            break;
    }
}

void onRequest() {
    calculateCRC();
    Wire.write((const uint8_t*)&i2cdata, sizeof(i2cdata));
    
    if (state.idle) {
        state.idle = false;
        toggleAudioCircuit();
    }
    state.idleCounter = 0;
}

void onReceive(int numBytes) {
    if (numBytes == 4) {
        for(int i = 0; i < 4; i++) rxData[i] = Wire.read();
        pendingCommand = true;
    }
}

void checkForIncomingI2CCommand() {
  if (pendingCommand) {
    processI2CCommand();
    pendingCommand = false;
  }
}

void checkForInactiveI2C() {
  // If no I2C activity is detected for a certain period,
  // mark the I2C as idle and toggle audio circuit
  // This prevents popping noises at boot and shutdown
  if (state.idleCounter < I2C_IDLE_TRIGGER) {
    state.idleCounter++;
    if (state.idleCounter == I2C_IDLE_TRIGGER) {
      state.idle = true;
      toggleAudioCircuit();
    }
  }
}

void normalModeFunctions() {
  readJoysticks();
  readSPIButtons();
  debounceSPIButtons();
  checkMuteButton();
  checkLeftSwitch();
  checkShutdownButton();
  checkDisplayButton();
}

void mandatoryFunctions() {
  readBattery();                    // always check battery systemStatus
  checkHoldSwitch();                // always check the hold switch
  checkForInactiveI2C();            // always check for inactive i2c
  checkRPi();                       // Always check RPi systemStatus
}

void startupSequence() {
  delay(500);         // this is here to prevent a flicker at poweroff. still needed?
  setPinHigh(EN_5V);  // this powers the raspberry pi on

  disableDisplay();   // this makes it so that the lcd backlight is disabled until the raspberry pi gpio goes high
  state.rpiTimeout++; // this triggers the display to power on when the raspberry pi gpio goes high
}

void sleepModeFunctions() {
  heartbeatLED();
}

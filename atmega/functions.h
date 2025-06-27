void initHardware() {
  // Port and pin initialization
  DDRB = 0b11111100;
  PORTB = 0b00101011;
  DDRD = 0b10001000;
  PORTD = 0b01110100;

  /*Pins are set as follows
    BTN_DISP (B0): IP,PU
    BTN_EXTRA2 (B1): IP,PU
    LCD_CONTROL (B2): OP,DL
    LED_BAT (B3): OP,DH
    SPI_IN (B4): OP,DL
    SPI_CLK (B5): OP,DH
    EN_5V (B6): OP,DL
    LED_WIFI (B7): OP,DL

    EN_AMP (D0): IP,NP
    RPI_DETECT (D1): IP,NP
    BTN_EXTRA1 (D2): IP,PU
    SPI_LD (D3): OP,DL
    BTN_SHUTDOWN (D4): IP,PU
    BTN_HLD (D5): IP,PU
    SWITCH_WIFI (D6): IP,PU
    EN_AUDIO_POWER (D7): OP,DL // make sure driving this on earlier boards is ok
  */

  // Configure Timer for PWM
  TMR_CTRL = TMR_CTRL_INIT;
  TMR_B_INIT;
  LED_BAT_COLOR = LED_FULL_GREEN;
}

void calculateCRC() {
  // Calculate CRC16-CCITT over first 9 bytes of i2cdata
  uint16_t crc = 0xFFFF;
  uint16_t poly = 0x1021;

  // Process each byte of i2cdata structure (excluding CRC bytes)
  const uint8_t* data = (const uint8_t*)&i2cdata;
  for (uint8_t i = 0; i < 9; i++) {
    crc ^= ((uint16_t)data[i] << 8);
    for (uint8_t j = 0; j < 8; j++) {
      crc = (crc & 0x8000) ? ((crc << 1) ^ poly) : (crc << 1);
    }
  }

  // Store CRC in i2cdata structure
  i2cdata.crc16H = crc >> 8;
  i2cdata.crc16L = crc & 0xFF;
}

void readEEPROM() {
  i2cdata.status.brightness = EEPROM.read(EEPROM_BRIGHT_ADDR);
  state.mute = EEPROM.read(EEPROM_MUTE_ADDR);
}

void writeMuteStatusToEEPROM() {
  EEPROM.update(EEPROM_MUTE_ADDR, state.mute);
}

void writeBrightnessToEEPROM() {
  EEPROM.update(EEPROM_BRIGHT_ADDR, i2cdata.status.brightness);
}

void setBatteryLED() {
  uint8_t color = LED_FULL_GREEN; // set default state
  if (state.batLow || state.forceLedOrange) {
    color = LED_FULL_ORANGE;
  } else if (state.sleeping) {
    color = state.powerLED;  // Use current sleep PWM value, but only if orange isnt forced
  }
  LED_BAT_COLOR = color;
}

void toggleWiFiLED() {
  switch (state.wifiState) {
    case 0:  // WiFi Disabled
      setPinLow(LED_WIFI);
      break;

    case 1:  // WiFi Enabled
      setPinHigh(LED_WIFI);
      break;

    case 2:  // WiFi Connecting - blink the LED
      state.wifiBlinkCounter++; // Increment and let it roll over
      if (state.wifiBlinkCounter == 0) {
        setPinHigh(LED_WIFI);  // LED on when counter is 0
      } else if (state.wifiBlinkCounter == 128) {
        setPinLow(LED_WIFI);   // LED off when counter is 128 (50% duty cycle)
      }
      break;

    default:
      setPinLow(LED_WIFI);  // Default to off for unknown states
      break;
  }
}

void readBattery() {
  //the adc read
  state.sysVolt = state.sysVolt - (state.sysVolt >> VOLT_AVG_SHIFT) + analogRead(SENS_SYS);
  state.batVolt = state.batVolt - (state.batVolt >> VOLT_AVG_SHIFT) + analogRead(SENS_BAT);

  bool newBatLow = state.batLow ?
                   (state.sysVolt <= BAT_GOOD) :
                   (state.sysVolt < BAT_LOW);

  if (newBatLow != state.batLow) {
    state.batLow = newBatLow;
    setBatteryLED();
  }
  //update i2c data
  i2cdata.senseSys = state.sysVolt >> VOLT_8BIT_SHIFT;
  i2cdata.senseBat = state.batVolt >> VOLT_8BIT_SHIFT;
}

void setBrightness() {
  byte bytesToSend[] = {LCD_ADDR, i2cdata.status.brightness * 4 + 1};

  noInterrupts();
  for (int byte = 0; byte < 2; byte++) {
    // Start condition
    delayMicroseconds(T_START);

    // Send each bit MSB first
    for (int i = 7; i >= 0; i--) {
      bool bit = bytesToSend[byte] & (1 << i);
      setPinLow(LCD_CONTROL);
      delayMicroseconds(bit ? T_L_HB : T_L_LB);
      setPinHigh(LCD_CONTROL);
      delayMicroseconds(bit ? T_H_HB : T_H_LB);
    }

    // End of byte sequence
    setPinLow(LCD_CONTROL);
    delayMicroseconds(T_EOS);
    setPinHigh(LCD_CONTROL);
  }

  interrupts();
}

void disableDisplay() {
  setPinLow(LCD_CONTROL);
}

void initBacklight() {
  setPinLow(LCD_CONTROL);
  delayMicroseconds(T_OFF);
  setPinHigh(LCD_CONTROL);
  delayMicroseconds(150);
  setPinLow(LCD_CONTROL);
  delayMicroseconds(300);
  setPinHigh(LCD_CONTROL);
}

void readSPIButtons() {
  setPinLow(SPI_LD);
  delayMicroseconds(5);
  setPinHigh(SPI_LD);
  uint16_t data = 0;

  // Read both bytes in sequence, lower byte first then upper byte
  for (uint8_t byte = 0; byte < 2; byte++) {
    for (uint8_t bit = 0; bit < 8; bit++) {
      setPinLow(SPI_CLK);
      delayMicroseconds(1);
      if (readPin(SPI_IN)) {
        // For first byte (byte=0), shifts are 7 down to 0
        // For second byte (byte=1), shifts are 15 down to 8
        data |= (1 << (7 - bit + (byte * 8)));
      }
      setPinHigh(SPI_CLK);
      delayMicroseconds(1);
    }
  }

  // Invert data so a 1 means pressed
  data = ~data;

  // Debounce buttons using data directly
  uint16_t newButtonState = 0;

  for (uint8_t i = 0; i < 16; ++i) {
    bool btn = data & (1 << i);
    if (btn) {
      state.debounceCount[i] = BTN_DEBOUNCE_LOOPS;
    } else if (state.debounceCount[i] > 0) {
      state.debounceCount[i]--;
    }
    if (state.debounceCount[i] != 0) {
      newButtonState |= (1 << i);
    }
  }

  i2cdata.buttons = newButtonState;
}

void readJoysticks() {
  i2cdata.joyLX = analogRead(JOY_LX) >> 2;
  i2cdata.joyLY = analogRead(JOY_LY) >> 2;
  i2cdata.joyRX = analogRead(JOY_RX) >> 2;
  i2cdata.joyRY = analogRead(JOY_RY) >> 2;
  i2cdata.joyRXBits.extraButton = !readPin(BTN_EXTRA1); // extra button state
  i2cdata.joyRYBits.extraButton = !readPin(BTN_EXTRA2); // extra button state
}

void checkLeftSwitch() {
  i2cdata.status.leftSwitch = !readPin(SWITCH_WIFI);
}

void checkShutdownButton() {
  i2cdata.status.sdPressed = !readPin(BTN_SHUTDOWN);
}

void checkDisplayButton() {
  if (!readPin(BTN_DISP)) {
    state.dispPressed = true;
  } else if (state.dispPressed) {
    i2cdata.status.brightness++; // increment to next brightness. valid brightness levels are 0-7. this will roll over to 0 because it is only 3 bits
    state.dispPressed = false;
    setBrightness();
    writeBrightnessToEEPROM();
  }
}

// EN_AMP is only used as open drain because its also driven low by the headphone board
// this could be used to detect whether the headphones are plugged in
void toggleAudioCircuit() {
  if (state.mute or state.idle or state.sleeping) {
    setPinAsOutput(EN_AMP);
    delay(1);
    setPinLow(EN_AUDIO_POWER);
    i2cdata.status.muted = true;
  } else {
    setPinAsInput(EN_AMP);
    delay(1);
    setPinHigh(EN_AUDIO_POWER);
    i2cdata.status.muted = false;
  }
}

void enableDisplay() {
  initBacklight();
  setBrightness();
}

void heartbeatLED() {
  static uint8_t pauseCounter = 0;
  // If at full green and in pause mode
  if (state.powerLED == LED_FULL_GREEN && pauseCounter > 0) {
    pauseCounter--;
    if (pauseCounter == 0) {
      state.sleepPulseDirection = !state.sleepPulseDirection; // End pause, reverse direction
    }
    setBatteryLED();
    return; // Stay at full green during pause
  }
  // Normal LED fading
  state.powerLED += state.sleepPulseDirection ? 1 : -1;
  if (state.powerLED == LED_FULL_GREEN) {
    pauseCounter = 200; // Start 1-second pause (200 * 5ms)
  } else if (state.powerLED == LED_FULL_ORANGE) {
    state.sleepPulseDirection = !state.sleepPulseDirection;
  }
  if (state.batLow) state.powerLED = LED_FULL_ORANGE;
  setBatteryLED();
}

void checkMuteButton() { // this does into hl
  if (READ_MUTE_BUTTON) {
    state.mutePressed = true;
  } else if (state.mutePressed) { // checks whether a previously pressed button was released. only occurs if mute is not pressed on this loop
    state.mute = !state.mute;
    toggleAudioCircuit();
    state.mutePressed = false;
    writeMuteStatusToEEPROM();
  }
}

void enterSleep() {
  i2cdata.status.sleeping = true;
  state.sleeping = true;
  state.sleepExitCounter = 0;
  disableDisplay();
  toggleAudioCircuit();
  if (state.batLow || state.forceLedOrange) {
    state.sleepPulseDirection = FADE_TO_GREEN;
    state.powerLED = LED_FULL_ORANGE;
  } else {
    state.sleepPulseDirection = FADE_TO_ORANGE;
    state.powerLED = LED_FULL_GREEN;
  }
}

void exitSleep() {
  i2cdata.status.sleeping = false;
  state.sleeping = false;
  enableDisplay();
  toggleAudioCircuit();
  setBatteryLED();
}

void checkHoldSwitch() {
  bool holdSwitchIsDown = !readPin(BTN_HLD);
  if (state.sleeping) {
    if (!holdSwitchIsDown) { // Sleep exit logic
      state.sleepExitCounter++;
      if (state.sleepExitCounter == SLEEP_EXIT_LOOPS) { // Delay to prevent LCD flicker caused by worn out switches.
        exitSleep();
      }
    } else {
      state.sleepExitCounter = 0;
    }
  } else if (holdSwitchIsDown) {
    enterSleep();
  }
}

void checkRPi() {
  if (readPin(RPI_DETECT)) {
    if (state.rpiTimeout) {
      enableDisplay();
      state.rpiTimeout = 0;
    }
  } else {
    if (!state.rpiTimeout) disableDisplay();
    if (state.rpiTimeout > RPI_TIMEOUT) {
      setPinLow(EN_5V);
      while (1) {} // Infinite loop until power is cut
    } else {
      state.rpiTimeout++;
    }
  }
}

void processI2CCommand() {
  switch (rxData[0]) {
    case CMD_WIFI:
      state.wifiState = rxData[1];
      state.wifiBlinkCounter = 127; // ensures the blinking LED always starts OFF
      toggleWiFiLED();
      break;

    case CMD_LED:
      state.forceLedOrange = rxData[1];
      setBatteryLED();
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
      if (!state.sleeping) { // never actually set it while in sleep mode. itll set when returning from sleep.
        toggleAudioCircuit();
      }
      break;

    case CMD_CRC:
      state.crcEnabled = rxData[1];
      break;
  }
}
void onRequest() {
  if (state.crcEnabled) {
    calculateCRC();
  }

  Wire.write((const uint8_t*)&i2cdata, sizeof(i2cdata));

  if (state.idle) {
    state.idle = false;
    toggleAudioCircuit();
  }
  state.idleTimeout = 0;
}

void onReceive(int numBytes) {
  if (numBytes == 4) {
    for (int i = 0; i < 4; i++) rxData[i] = Wire.read();
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
  // Audio is disabled unless I2C is active. This prevents popping sounds at bootup and shutdown.
  if (state.idleTimeout < I2C_IDLE_TRIGGER) {
    state.idleTimeout++;
    if (state.idleTimeout == I2C_IDLE_TRIGGER) {
      state.idle = true;
      toggleAudioCircuit();
    }
  }
}

void checkHeadphones() {
  if (!state.mute) {
    i2cdata.status.headphones = readPin(EN_AMP);
  }
}

void sleepModeFunctions() {
  heartbeatLED();
}

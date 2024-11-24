// Loop control
#define UPDATE_INTERVAL_REACHED currentTime - lastUpdateTime >= (state.sleeping ? SLEEP_MODE_LOOP_MS : NORMAL_MODE_LOOP_MS)

// Port B pins
#define BTN_DISP B,0
#define BTN_EX2 B,1
#define LCD_1W B,2
#define LED_ORG B,3
#define SPI_IN B,4
#define SPI_CLK B,5
#define EN_5V B,6
#define LED_L_WIFI B,7

// Port D pins
#define EN_AMP D,0
#define RPI_DET D,1
#define BTN_EX1 D,2
#define SPI_LD D,3
#define BTN_SD D,4
#define BTN_HLD D,5
#define SW_L D,6
#define EN_AUD D,7

// ADC pins
#define JOY_RX 0
#define JOY_RY 1
#define SENS_SYS 2
#define SENS_BAT 3
#define JOY_LX 6
#define JOY_LY 7

// ADC processing macros
#define VOLT_AVG_SHIFT 4     // Voltage averaging shift
#define VOLT_8BIT_SHIFT 3    // Voltage to 8-bit conversion

// Port initialization values
#define PORTB_INIT 0b00101011
#define DDRB_INIT 0b11111100
#define PORTD_INIT 0b01110100
#define DDRD_INIT 0b00001000

// Timer configuration macros
#if defined(__AVR_ATmega8__)|(__AVR_ATmega8A__)
    #define TMR_CTRL TCCR2
    #define TMR_CTRL_INIT ((1<<WGM21)|(1<<WGM20)|(1<<COM21)|(1<<CS20))
    #define TMR_OCR OCR2
    #define TMR_B_INIT
#elif defined(__AVR_ATmega328P__)
    #define TMR_CTRL TCCR2A
    #define TMR_CTRL_INIT ((1<<WGM21)|(1<<WGM20)|(1<<COM2A1))
    #define TMR_OCR OCR2A
    #define TMR_B_INIT TCCR2B=(1<<CS20)
#else
    #error "Unsupported MCU"
#endif

// GPIO Port manipulation macros
#define DDR(p) DDR##p
#define PORT(p) PORT##p
#define PIN(p) PIN##p
#define BIT(n) (1<<n)

// GPIO Pin control macros
#define setOutMode(p,n) DDR(p)|=BIT(n)
#define setInMode(p,n) DDR(p)&=~BIT(n)
#define setHigh(p,n) PORT(p)|=BIT(n)
#define setLow(p,n) PORT(p)&=~BIT(n)
#define getPin(p,n) (PIN(p)&BIT(n))

// GPIO Simplified pin interface macros
#define setPinAsOutput(pin) setOutMode(pin)
#define setPinAsInput(pin) setInMode(pin)
#define setPinHigh(pin) setHigh(pin)
#define setPinLow(pin) setLow(pin)
#define readPin(pin) getPin(pin)

// TPS61160 Backlight EasyScale Protocoli
#define LCD_ADDR 0x72

// LCD timing parameters (microseconds)
#define T_START 10   // Start condition
#define T_EOS 10     // End of sequence
#define T_H_LB 10    // High time, low bit
#define T_H_HB 25    // High time, high bit
#define T_L_LB 25    // Low time, low bit
#define T_L_HB 10    // Low time, high bit
#define T_OFF 3000   // Reset time

#define READ_MUTE_BUTTON i2cdata.buttons & 0b0000000000000001

#define LED_FULL_GREEN 255
#define LED_FULL_ORANGE 0

// Hardware initialization
void initHardware() {
    // Configure ports
    DDRB = DDRB_INIT;
    PORTB = PORTB_INIT;
    DDRD = DDRD_INIT;
    PORTD = PORTD_INIT;

    // Configure Timer for PWM
    TMR_CTRL = TMR_CTRL_INIT;
    TMR_B_INIT;
    TMR_OCR = LED_FULL_GREEN;
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

void togglePowerLED() {
    uint8_t targetPWM = LED_FULL_GREEN; // set default state
    if (state.batLow || state.forceLedOrange) {
        targetPWM = LED_FULL_ORANGE;
    } else if (state.sleeping){
        targetPWM = state.powerLED;  // Use current sleep PWM value, but only if orange isnt forced
    }    
    TMR_OCR = targetPWM;
}

void toggleWiFiLED() {
    if (state.wifiEnabled) {
        setPinHigh(LED_L_WIFI);
    } else {
        setPinLow(LED_L_WIFI);
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
        togglePowerLED();
    }
    //update i2c data
    i2cdata.senseSys = state.sysVolt >> VOLT_8BIT_SHIFT;
    i2cdata.senseBat = state.batVolt >> VOLT_8BIT_SHIFT;
}

void setBrightness() {
    byte bytesToSend[] = {LCD_ADDR,i2cdata.status.brightness * 4 + 1};
    
    noInterrupts();  
    for (int byte = 0; byte < 2; byte++) {
        // Start condition
        delayMicroseconds(T_START);
        
        // Send each bit MSB first
        for (int i = 7; i >= 0; i--) {
            bool bit = bytesToSend[byte] & (1 << i);
            setPinLow(LCD_1W);
            delayMicroseconds(bit ? T_L_HB : T_L_LB);
            setPinHigh(LCD_1W);
            delayMicroseconds(bit ? T_H_HB : T_H_LB);
        }
        
        // End of byte sequence
        setPinLow(LCD_1W);
        delayMicroseconds(T_EOS);
        setPinHigh(LCD_1W);
    }
    
    interrupts();
}

void disableDisplay() {
    setPinLow(LCD_1W);
}

void initBacklight() {
    setPinLow(LCD_1W);
    delayMicroseconds(T_OFF);
    setPinHigh(LCD_1W);
    delayMicroseconds(150);
    setPinLow(LCD_1W);
    delayMicroseconds(300);
    setPinHigh(LCD_1W);
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
  
  state.shiftRegister = ~data;
}

void debounceSPIButtons() {
  uint16_t newButtonState = 0;
  
  for (uint8_t i = 0; i < 16; ++i) {
    bool btn = state.shiftRegister & (1 << i);
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
    i2cdata.joyRX = (analogRead(JOY_RX) >> 2 & 0b11111110) | (!readPin(BTN_EX1));
    i2cdata.joyRY = (analogRead(JOY_RY) >> 2 & 0b11111110) | (!readPin(BTN_EX2));   
}

void checkLeftSwitch() {
    i2cdata.status.leftSwitch = !readPin(SW_L);
}

void checkShutdownButton() {
    i2cdata.status.sdPressed = !readPin(BTN_SD);
}

void checkDisplayButton() {
    if (!readPin(BTN_DISP)) {
        state.dispPressed = true;
    } else if (state.dispPressed) {
        i2cdata.status.brightness++; // increment to next brightness. valid brightness levels are 0-7. this will roll over to 0 because it is only 3 bits
        state.dispPressed = false;
        setBrightness();
    }
}

// EN_AMP is only used as open drain because its also driven  low by the headphone board
// this could be used to detect whether the headphones are plugged in
void toggleAudioCircuit() {
    if (state.mute or state.idle or state.sleeping) {
        setPinAsOutput(EN_AMP);
        delay(1);
        setPinLow(EN_AUD);
        i2cdata.status.muted = true;
    } else {
        setPinAsInput(EN_AMP);
        delay(1);
        setPinHigh(EN_AUD);
        i2cdata.status.muted = false;
    }
}

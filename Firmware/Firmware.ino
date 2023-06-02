#define BACKLIGHT_ADDRESS 0x72

// I had issues when setting values close to the minimum
#define tSTART 10 // minimum of 2 microseconds
#define tEOS 10 // minimum of 2 microseconds
#define tH_LB 10 // minimum of 2 microseconds
#define tH_HB 25 // minimum of 4 microseconds
#define tL_LB 25 // minimum of 4 microseconds
#define tL_HB 10 // minimum of 2 microseconds

#define toff 3000 // minimum of 2500 microseconds to reset the chip

#define tes_win 1000 // microseconds

#define PB1_LOW PORTB &= B11111101
#define PB1_HIGH PORTB |= B00000010

byte brightness = 15;

void setup() {
//        LEFT_SWITCH
//        |EN_5V0
//        ||SHIFT_CLOCK
//        |||SHIFT_DATA_BUFFERED
//        ||||PWM_ORANGE_LCD
//        |||||OPEN1
//        ||||||PWM_LCD
//        |||||||BTN_DISPLAY
//        ||||||||
  DDRB = B00000010; // set PORTB (0 is input, 1 is output)
  
//        EN_AUDIO
//        |LED_LEFT_GPIO
//        ||BTN_HOLD
//        |||EN_SYS_MEGA
//        ||||SHIFT_LATCH
//        |||||AUDIO_GAIN_0
//        ||||||AUDIO_GAIN_1
//        |||||||BTN_SD
//        ||||||||
  DDRD = B00000000; // set PORTD (0 is input, 1 is output)
  PORTB = B11111111; // set PORTD (0 is low, 1 is high)
  PORTD = B11111111;

  // Startup sequence for EasyScale mode
  PB1_LOW; // LOW
  delayMicroseconds(toff);

  // both of these must occur within 1000 microseconds of resetting the chip
  PB1_HIGH; // HIGH
  delayMicroseconds(150); // keep CTRL high for more than 100 microseconds
  PB1_LOW; // LOW
  delayMicroseconds(300); // drive CTRL low for more than 260 microseconds
  setBrightness(brightness); // set the initial brightness of 50%
}

void setBrightness(byte brightness) { // can be 0-31, 0 must be handled correctly
  startCondition();
  sendByte(BACKLIGHT_ADDRESS); 
  endOfStream();
  startCondition();
  sendByte(brightness);
  endOfStream();
  PB1_HIGH; // leave CTRL_PIN in a HIGH state
}

void startCondition() {
  PB1_HIGH; // HIGH
  delayMicroseconds(tSTART);
}

void endOfStream() {
  PB1_LOW; // LOW
  delayMicroseconds(tEOS);
}

void sendBit(bool bit) {
  if (bit) { // Send High Bit
    PB1_LOW; // LOW
    delayMicroseconds(tL_HB);
    PB1_HIGH; // HIGH
    delayMicroseconds(tH_HB);
  } else { // Send Low Bit
    PB1_LOW; // LOW
    delayMicroseconds(tL_LB);
    PB1_HIGH; // HIGH
    delayMicroseconds(tH_LB);
  }
}

void sendByte(byte dataByte) {
  for (int i = 7; i >= 0; i--) {
    sendBit(bitRead(dataByte, i));
  }
}

byte inputsB;
byte inputsD;
bool displayChangeActive = 0;

#define BTN_DISPLAY bitRead(inputsB,0)
#define BTN_OPEN1 bitRead(inputsB,2)
#define BTN_LEFT_SWITCH bitRead(inputsB,7)
#define BTN_SD bitRead(inputsB,0)
#define EN_SYS_MEGA bitRead(inputsD,4)
#define BTN_HOLD bitRead(inputsB,5)

void scanArduinoInputs() {
  //scan the GPIOs that are used for input
  inputsB = PINB;
  inputsD = PINB;
  if (!BTN_DISPLAY) {
      displayChangeActive = 1;
    } else {
      if (displayChangeActive == 1) {
        brightness = brightness + 4;
      if (brightness > 31) {
        brightness = 1;
      }
      displayChangeActive = 0;
      setBrightness(brightness);
      }
    }
}

void loop() {
  scanArduinoInputs();
  //scanShiftRegisters();
  
  delay(10); // Delay for 1 second
}

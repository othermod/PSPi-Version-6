#include <Wire.h>
#include <SPI.h>

#define I2C_ADDRESS 0x10
#define BACKLIGHT_ADDRESS 0x72

// LCD backlight chip timings
// I had issues when setting values close to the minimum
#define tSTART 10 // minimum of 2 microseconds
#define tEOS 10 // minimum of 2 microseconds
#define tH_LB 10 // minimum of 2 microseconds
#define tH_HB 25 // minimum of 4 microseconds
#define tL_LB 25 // minimum of 4 microseconds
#define tL_HB 10 // minimum of 2 microseconds
#define toff 3000 // minimum of 2500 microseconds to reset the chip

// Define all of the GPIO pins in a way that the macro can read
#define BTN_DISPLAY B,0
#define ONEWIRE_LCD B,1
#define OPEN1 B,2
#define PWM_LED_ORANGE B,3
#define SHIFT_DATA_IN B,4
#define CLOCK B,5
#define EN_5V0 B,6
#define LEFT_SWITCH B,7

#define BTN_SD D,0
#define AUDIO_GAIN_1 D,1
#define AUDIO_GAIN_0 D,2
#define SHIFT_LOAD D,3
#define DETECT_RPI D,4
#define BTN_HOLD D,5
#define LED_LEFT D,6
#define EN_AUDIO D,7

// Create macros to directly read and write GPIO pins
#define WRITE_PIN_HELPER(port, pin, state) \
  do { \
    if (state == HIGH) PORT ## port |= (1 << pin); \
    else PORT ## port &= ~(1 << pin); \
  } while (0)

#define writePin(pinAndPort, state) WRITE_PIN_HELPER(pinAndPort, state)

#define READ_PIN_HELPER(port, pin) ((PIN ## port >> pin) & 1)

#define readPin(pinAndPort) READ_PIN_HELPER(pinAndPort)

#define SET_PIN_DIR_HELPER(port, pin, mode) \
  do { \
    if (mode == OUTPUT) DDR ## port |= (1 << pin); \
    else DDR ## port &= ~(1 << pin); \
  } while (0)

#define setPinDirection(pinAndPort, mode) SET_PIN_DIR_HELPER(pinAndPort, mode)

#define DEBOUNCE_CYCLES 5 // keep the button pressed for this many loops. can be 0-255. each loop is 10ms

#define JOY_RX_PIN 0
#define JOY_RY_PIN 1
#define SENSE_SYS_PIN 2
#define SENSE_BAT_PIN 3
#define JOY_LX_PIN 6
#define JOY_LY_PIN 7

byte brightness = 15;
uint16_t detectTimeout = 0;
byte arduinoInputsPortB;
byte arduinoInputsPortD;
bool displayButtonPressed = 0;
bool muteButtonPressed = 0;
unsigned long previousMillis = 0;
const long interval = 10; // ms delay between the start of each loop
uint8_t debouncePortB[8] = {0}; // button stays pressed for a few cycles to debounce and to make sure the button press isn't missed
uint8_t debouncePortD[8] = {0};

struct I2C_Structure { // define the structure layout for transmitting I2C data to the Raspberry Pi
  uint8_t buttonA; // button status
  uint8_t buttonB; // button status
  uint8_t JOY_LX;
  uint8_t JOY_LY;
  uint8_t JOY_RX;
  uint8_t JOY_RY;
  uint8_t SENSE_SYS;
  uint8_t SENSE_BAT;
  // uint8_t misc; // 5 bits for brightness level, 1 for mute status,
};

I2C_Structure I2C_data; // create the structure for the I2C data

void setup() {
  // These and the macro will go away once pin states are verified, and I will just do this once with a single command for each port
  setPinDirection(BTN_DISPLAY, INPUT);
  setPinDirection(ONEWIRE_LCD, OUTPUT);
  setPinDirection(OPEN1, INPUT);
  setPinDirection(PWM_LED_ORANGE, OUTPUT);
  setPinDirection(SHIFT_DATA_IN, INPUT);
  setPinDirection(CLOCK, OUTPUT);
  setPinDirection(EN_5V0, OUTPUT);
  setPinDirection(LEFT_SWITCH, INPUT);

  setPinDirection(BTN_SD, INPUT);
  setPinDirection(AUDIO_GAIN_1, OUTPUT);
  setPinDirection(AUDIO_GAIN_0, OUTPUT);
  setPinDirection(SHIFT_LOAD, OUTPUT);
  setPinDirection(DETECT_RPI, INPUT);
  setPinDirection(BTN_HOLD, INPUT);
  setPinDirection(LED_LEFT, OUTPUT);
  setPinDirection(EN_AUDIO, OUTPUT);

  PORTB = B11101101; // ONEWIRE_LCD low. disable pullup on SHIFT_DATA_IN
  PORTD = B11101001; // AUDIO_GAIN_0, AUDIO_GAIN_1 low. disable pullup on DETECT_RPI

  Wire.begin(I2C_ADDRESS);  // join i2c bus
  Wire.onRequest(requestEvent); // register event
  SPI.begin();
  SPI.setBitOrder(MSBFIRST); // can this be removed?
  (SPI_MODE0); // can this be removed?

  // this disables the backlight and audio until the Pi is detected
  enterSleep();
  // this ensures that the backlight and audio will enable as soon as the Pi is detected at boot
  // this may go away if I use a different GPIO from the CM4 that stays low for a few seconds
  // check to see what happens when reboots occur
  detectTimeout++;
}

void initializeBacklight() {
  // Startup sequence for EasyScale mode
  writePin(ONEWIRE_LCD, LOW); // LOW
  delayMicroseconds(toff); // lcd has to be off this long to reset before initializing
  // both of these must occur within 1000 microseconds of resetting the chip
  writePin(ONEWIRE_LCD, HIGH);
  delayMicroseconds(150); // keep CTRL high for more than 100 microseconds
  writePin(ONEWIRE_LCD, LOW);
  delayMicroseconds(300); // drive CTRL low for more than 260 microseconds
  setBrightness(brightness); // set the brightness
}

void setBrightness(byte brightness) { // can be 0-31, 0 must be handled correctly
  sendByte(BACKLIGHT_ADDRESS); // just combine this into the sendByte function, since address must be sent?
  sendByte(brightness);
  writePin(ONEWIRE_LCD, HIGH);
}

void sendBit(bool bit) {
    writePin(ONEWIRE_LCD, LOW);
    delayMicroseconds(bit ? tL_HB : tL_LB);
    writePin(ONEWIRE_LCD, HIGH);
    delayMicroseconds(bit ? tH_HB : tH_LB);
}

void sendByte(byte dataByte) {
  writePin(ONEWIRE_LCD, HIGH); // HIGH start condition
  delayMicroseconds(tSTART);
  for (int i = 7; i >= 0; i--) {
    sendBit(bitRead(dataByte, i));
  }
  writePin(ONEWIRE_LCD, LOW); // LOW end condition
  delayMicroseconds(tEOS);
}

void readArduinoInputs() {
  // Probably a better idea to store all the pins into a variable and cycle through them to check statuses
  // scan the GPIOs that are used for input
  // also, do these pins benefit from debouncing?
  arduinoInputsPortB = PINB;
  arduinoInputsPortD = PIND;
  //can put these in main or here. just do it after inputs are scanned
  detectRPi();
  detectDisplayButton();
}

void readShiftRegisterInputs(){
  // Prepare 74HC165D for parallel load
  writePin(SHIFT_LOAD, LOW);
  delayMicroseconds(5); // give some time to setup, you may not need this
  writePin(SHIFT_LOAD, HIGH);

  // Use hardware SPI to read 2 bytes from the 74HC165D chips and store them for I2C. Will add debouncing once all other basic functions work.
  byte shiftRegisterInput1 = SPI.transfer(0);
  byte shiftRegisterInput2 = SPI.transfer(0);

    //add debouncing

  I2C_data.buttonA = shiftRegisterInput1;
  I2C_data.buttonB = shiftRegisterInput2;
}

void detectDisplayButton() {
  // Handle Display button being pressed
  if (!readPin(BTN_DISPLAY)) {
      displayButtonPressed = 1;
    } else {
      // increase the brightness when the Display button is released
      if (displayButtonPressed == 1) {
        brightness = (brightness + 4) & B00011111; // &ing the byte should keep the brightness from going past 31. it will return to 00000001 when it passes 31
        displayButtonPressed = 0;
        setBrightness(brightness);
      }
    }
}

/*
void detectMuteButton() {
  // Handle Mute button being pressed
  if (!readPin(BTN_MUTE)) {
      muteButtonPressed = 1;
    } else {
      // invert EN_AUDIO when the mute button is released
      // can alse handle mute being held to increase hardware amplification
      if (muteButtonPressed == 1) {
        // invert EN_AUDIO
        // should the mute status save in eeprom?
        muteButtonPressed = 0;
      }
    }
}
*/
void detectRPi() {
  // some of the stuff below can be added to sleep and unsleep functions, and be used for this and sleep
  // Handle Raspberry Pi not detected
  if (!readPin(DETECT_RPI)) { //rpi isnt detected
    if (!detectTimeout){ // if the timeout sequence hasnt started yet, begin it by killing audio and lcd
      enterSleep();
    }
    detectTimeout++;
    if (detectTimeout > 500) {  // if the timeout reaches 5 seconds, kill power
      writePin(EN_5V0, LOW);
    }
  } else {
    if (detectTimeout){ // if the pi is detected during the timeout, enable audio and LCD
      wakeFromSleep();
      detectTimeout = 0;
    }
  }
}

void enterSleep() {
  writePin(EN_AUDIO, LOW);
  writePin(ONEWIRE_LCD, LOW);
}

void wakeFromSleep() {
  writePin(EN_AUDIO, HIGH);
  initializeBacklight(); // re-initialize and enable backlight
}

void requestEvent(){
  Wire.write((char*) &I2C_data, sizeof(I2C_data)); // send the data to the Pi
}

void readAnalogInputs(){
  I2C_data.JOY_RX=(analogRead(JOY_RX_PIN) >> 2); // read the ADCs, and reduce from 10 to 8 bits
  I2C_data.JOY_RY=(analogRead(JOY_RY_PIN) >> 2);
  I2C_data.SENSE_SYS=(analogRead(SENSE_SYS_PIN)); // don't bitshift this. it is never above 100
  I2C_data.SENSE_BAT=(analogRead(SENSE_BAT_PIN)); // don't bitshift this. it is never above 100
  I2C_data.JOY_LX=(analogRead(JOY_LX_PIN) >> 2);
  I2C_data.JOY_LY=(analogRead(JOY_LY_PIN) >> 2);
}

void loop() {
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    // save the last time the loop was executed
    previousMillis = currentMillis;
    readArduinoInputs();
    readShiftRegisterInputs();
    readAnalogInputs();
  }
}

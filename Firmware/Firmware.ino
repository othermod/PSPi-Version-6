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
#define LED_LEFT_GPIO D,6
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

#define ANALOG_PIN1 0
#define ANALOG_PIN2 1
#define ANALOG_PIN3 2
#define ANALOG_PIN4 3
#define ANALOG_PIN5 6
#define ANALOG_PIN6 7

byte brightness = 15;
uint16_t detectTimeout = 0;

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
  setPinDirection(LED_LEFT_GPIO, OUTPUT);
  setPinDirection(EN_AUDIO, OUTPUT);

  PORTB = B11101101; // ONEWIRE_LCD low. disable pullup on SHIFT_DATA_IN
  PORTD = B11101001; // AUDIO_GAIN_0, AUDIO_GAIN_1 low. disable pullup on DETECT_RPI

  Wire.begin(I2C_ADDRESS);  // join i2c bus
  Wire.onRequest(requestEvent); // register event
  SPI.begin();
  SPI.setBitOrder(MSBFIRST); // can this be removed?
  (SPI_MODE0); // can this be removed?
  //initializeBacklight(); this doesnt need to be here, because DETECT_RPI should never be high initially and the timeout should enable it
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
  if (bit) { // Send High Bit
    writePin(ONEWIRE_LCD, LOW);
    delayMicroseconds(tL_HB);
    writePin(ONEWIRE_LCD, HIGH);
    delayMicroseconds(tH_HB);
  } else { // Send Low Bit
    writePin(ONEWIRE_LCD, LOW);
    delayMicroseconds(tL_LB);
    writePin(ONEWIRE_LCD, HIGH);
    delayMicroseconds(tH_LB);
  }
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

byte inputsB;
byte inputsD;
bool displayChangeActive = 0;

void scanArduinoInputs() {
  //scan the GPIOs that are used for input
  inputsB = PINB;
  inputsD = PINB;
  // Handle Display button being pressed
  // Probably a better idea to store the 8 pins into a variable and check that instead
  // also, do these pins benefit from debouncing?
  if (!readPin(BTN_DISPLAY)) {
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
    // some of the stuff below can be added to sleep and unsleep functions, and be used for this and sleep
    // Handle Raspberry Pi not detected
    if (!readPin(DETECT_RPI)) { //rpi isnt detected
      if (!detectTimeout){ // if the timeout sequence hasnt started yet, begin it by killing audio and lcd
        writePin(EN_AUDIO, LOW);
        writePin(ONEWIRE_LCD, LOW);
      }
      detectTimeout++;
      if (detectTimeout > 500) {  // if the timeout reaches 5 seconds, kill power
        writePin(EN_5V0, LOW);
      }
    } else {
      if (!detectTimeout){ // if the pi is detected during the timeout, enable audio and LCD
        writePin(EN_AUDIO, HIGH);
        initializeBacklight(); // re-initialize and enable backlight
        detectTimeout = 0;
      }
    }
}

unsigned long previousMillis = 0;
const long interval = 10; // ms delay between the start of each loop

uint8_t debouncePortB[8] = {0}; // button stays pressed for a few cycles to debounce and to make sure the button press isn't missed
uint8_t debouncePortD[8] = {0};

struct I2C_Structure { // define the structure layout for transmitting I2C data to the Raspberry Pi
  uint8_t buttonA; // button status
  uint8_t buttonB; // button status
  uint8_t analog1;
  uint8_t analog2;
  uint8_t analog3;
  uint8_t analog4;
  uint8_t analog5;
  uint8_t analog6;
};

I2C_Structure I2C_data; // create the structure for the I2C data

void requestEvent(){
  Wire.write((char*) &I2C_data, sizeof(I2C_data)); // send the data to the Pi
}

void scanShiftRegisters(){
  // Prepare 74HC165D for parallel load
  writePin(SHIFT_LOAD, LOW);
  delayMicroseconds(5); // give some time to setup, you may not need this
  writePin(SHIFT_LOAD, HIGH);

  // Use hardware SPI to read 2 bytes from the 74HC165D chips and store them for I2C. Will add debouncing once all other basic functions work.
  byte highByte = SPI.transfer(0);
  byte lowByte = SPI.transfer(0);
  I2C_data.buttonA = highByte;
  I2C_data.buttonB = lowByte;
}

void readAnalog(){
  I2C_data.analog1=(analogRead(ANALOG_PIN1) >> 2); // read the ADCs, and reduce from 10 to 8 bits
  I2C_data.analog2=(analogRead(ANALOG_PIN2) >> 2);
  I2C_data.analog3=(analogRead(ANALOG_PIN3) >> 2);
  I2C_data.analog4=(analogRead(ANALOG_PIN4) >> 2);
  I2C_data.analog5=(analogRead(ANALOG_PIN5) >> 2);
  I2C_data.analog6=(analogRead(ANALOG_PIN6) >> 2);
}

void loop() {
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    // save the last time the loop was executed
    previousMillis = currentMillis;
    scanArduinoInputs();
    scanShiftRegisters();
    readAnalog();
  }
}

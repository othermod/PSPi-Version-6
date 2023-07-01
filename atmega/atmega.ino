/* TODO
1. Forced poweroff will be more gentle if the arduino detects the power button being held and kills 5v after 2 seconds, and then kills all power
2. The lcd is not switching brightness reliably, so try increasing the delays
3. Mute audio as soon as I2C communication stops. Do this by inverting the inputs from the shift register, and checking whether both bytes are 0
4. Set up button debouncing
*/

#include <Wire.h>
#include <SPI.h>
#include "Pin_Macros.h"
#include "LCD_Timings.h"
#include "GPIO.h"

#define I2C_ADDRESS 0x10

#define DEBOUNCE_CYCLES 5 // keep the button pressed for this many loops. can be 0-255. each loop is 10ms

byte brightness = 0b00000001;
uint16_t detectTimeout = 0;

byte arduinoInputsB;
byte arduinoInputsD;
byte registerInputs1;
byte registerInputs2;

bool displayButtonPressed = 0;
bool muteButtonPressed = 0;
unsigned long previousMillis = 0;
const long interval = 10; // ms delay between the start of each loop
uint8_t debouncePortB[8] = {0}; // button stays pressed for a few cycles to debounce and to make sure the button press isn't missed
uint8_t debouncePortD[8] = {0};

// define the structure layout for transmitting I2C data to the Raspberry Pi
// the first 4 bytes must be read continuously.
// STATUS is read at whatever interval is needed
// left joystick can be read less often
// right joystick is only read when it is enabled
struct I2C_Structure {
  uint8_t buttonA; // button status
  uint8_t buttonB; // button status
  uint8_t SENSE_SYS;
  uint8_t SENSE_BAT;
  uint8_t STATUS; // 5 bits for brightness level (can use 3 bits because there are only 8 levels), 1 for mute status, 1 for power switch, 1 for hold switch
  uint8_t JOY_LX;
  uint8_t JOY_LY;
  uint8_t JOY_RX;
  uint8_t JOY_RY;

};

I2C_Structure I2C_data; // create the structure for the I2C data

#define BTN_MUTE I2C_data.buttonA & B00000001

void setup() {
  // These and the macros will go away once pin states are verified, and I will just do this once with a single command for each port
  setPinAsInput(BTN_DISPLAY);
  setPinAsInput(SUPERVISOR);
  setPinAsInput(SHIFT_DATA_IN);
  setPinAsInput(LEFT_SWITCH);
  setPinAsInput(BTN_SD);
  setPinAsInput(DETECT_RPI);
  setPinAsInput(BTN_HOLD);
  setPinAsOutput(ONEWIRE_LCD);
  setPinAsOutput(PWM_LED_ORANGE);
  setPinAsOutput(CLOCK);
  setPinAsOutput(EN_5V0);
  setPinAsOutput(AUDIO_GAIN_1);
  setPinAsOutput(AUDIO_GAIN_0);
  setPinAsOutput(SHIFT_LOAD);
  setPinAsOutput(LED_LEFT);
  setPinAsOutput(EN_AUDIO);

  // SHIFT_DATA_IN is controlled by SPI
  // CLOCK is controlled by SPI
  setPinLow(ONEWIRE_LCD);
  setPinLow(PWM_LED_ORANGE); // will probably do PWM instead
  setPinLow(EN_5V0);
  setPinLow(AUDIO_GAIN_1);
  setPinLow(AUDIO_GAIN_0);
  setPinLow(SHIFT_LOAD);
  setPinLow(DETECT_RPI);
  setPinLow(LED_LEFT);
  setPinLow(EN_AUDIO);
  setPinHigh(BTN_DISPLAY);
  setPinHigh(SUPERVISOR);
  setPinHigh(LEFT_SWITCH);
  setPinHigh(BTN_SD);
  setPinHigh(BTN_HOLD);

  Wire.begin(I2C_ADDRESS);  // join i2c bus
  Wire.onRequest(requestEvent); // register event
  SPI.begin();
  SPI.setBitOrder(MSBFIRST); // can this be removed?
  (SPI_MODE0); // can this be removed?
  delay(500);
  setPinHigh(EN_5V0);

  // this disables the backlight and audio until the Pi is detected
  enterSleep();
  // this ensures that the backlight will enable as soon as the Pi is detected at boot
  // this may go away if I use a different GPIO from the CM4 that stays low for a few seconds
  // check to see what happens when reboots occur
  // enable audio after i2c activity begins
  detectTimeout++;
}

void initializeBacklight() {
  // Startup sequence for EasyScale mode
  setPinLow(ONEWIRE_LCD); // LOW
  delayMicroseconds(toff); // lcd has to be off this long to reset before initializing
  // both of these must occur within 1000 microseconds of resetting the chip
  setPinHigh(ONEWIRE_LCD);
  delayMicroseconds(150); // keep CTRL high for more than 100 microseconds
  setPinLow(ONEWIRE_LCD);
  delayMicroseconds(300); // drive CTRL low for more than 260 microseconds
  setBrightness(brightness); // set the brightness
}

void setBrightness(byte brightness) { // can be 0-31, 0 must be handled correctly
  sendByte(BACKLIGHT_ADDRESS); // just combine this into the sendByte function, since address must be sent?
  sendByte(brightness);
  //setPinHigh(ONEWIRE_LCD);
}

void sendBit(bool bit) {
    setPinLow(ONEWIRE_LCD);
    delayMicroseconds(bit ? tL_HB : tL_LB);
    setPinHigh(ONEWIRE_LCD);
    delayMicroseconds(bit ? tH_HB : tH_LB);
}

void sendByte(byte dataByte) {
  //setPinHigh(ONEWIRE_LCD); // start condition is already high, because the previous byte ended high
  noInterrupts(); // disable interrupts to i2c requests don't affect timings
  delayMicroseconds(tSTART);
  for (int i = 7; i >= 0; i--) {
    sendBit(bitRead(dataByte, i));
  }
  setPinLow(ONEWIRE_LCD); // LOW end condition to signify end of byte
  delayMicroseconds(tEOS);
  setPinHigh(ONEWIRE_LCD); //end with pin high
  interrupts(); // enable interrupts again
}

void readArduinoInputs() {
  // Probably a better idea to store all the pins into a variable and cycle through them to check statuses
  // scan the GPIOs that are used for input
  // also, do these pins benefit from debouncing?
  arduinoInputsB = PINB;
  arduinoInputsD = PIND;
  //can put these in main or here. just do it after inputs are scanned
  detectRPi();
  detectDisplayButton();
}

void readShiftRegisterInputs(){
  // Prepare 74HC165D for parallel load
  setPinLow(SHIFT_LOAD);
  delayMicroseconds(5); // give some time to setup, you may not need this
  setPinHigh(SHIFT_LOAD);

  // Use hardware SPI to read 2 bytes from the 74HC165D chips and store them for I2C. Will add debouncing once all other basic functions work.
  // Flip every bit so that 1 means pressed. This will also be used in the the dimming/low lower function.
  registerInputs1 = ~SPI.transfer(0);
  registerInputs2 = ~SPI.transfer(0);

    //add debouncing
  I2C_data.buttonA = registerInputs1;
  I2C_data.buttonB = registerInputs2;
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
        I2C_data.STATUS = (I2C_data.STATUS & B11111000) | (((brightness - 1) / 4) & B00000111); // store the brightness level for transmission over i2c. there are only 8 levels, so only use 3 bits.
        setBrightness(brightness);
      }
    }
}

void detectMuteButton() {
  // Handle Display button being pressed
  if (BTN_MUTE) {
      muteButtonPressed = 1;
    } else {
      // invert EN_AUDIO
      if (muteButtonPressed == 1) {
        if (readPin(EN_AUDIO)) {
          setPinLow(EN_AUDIO);
        } else {
          setPinHigh(EN_AUDIO);
        }
        muteButtonPressed = 0;
      }
    }
}

void detectRPi() {
  // some of the stuff below can be added to sleep and unsleep functions, and be used for this and sleep
  // Handle Raspberry Pi not detected
  if (!readPin(DETECT_RPI)) { //rpi isnt detected
    if (!detectTimeout){ // if the timeout sequence hasnt started yet, begin it by killing audio and lcd
      enterSleep();
    }
    detectTimeout++;
    if (detectTimeout > 500) {  // if the timeout reaches 5 seconds, kill power
      setPinLow(EN_5V0);
    }
  } else {
    if (detectTimeout){ // if the pi is detected during the timeout, enable audio and LCD
      wakeFromSleep();
      detectTimeout = 0;
    }
  }
}

void enterSleep() {
  setPinLow(EN_AUDIO);
  setPinLow(ONEWIRE_LCD);
}

void wakeFromSleep() {
  setPinHigh(EN_AUDIO);
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
    detectMuteButton();
  }
}

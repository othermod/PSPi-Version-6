/* TODO
1. Forced poweroff will be more gentle if the arduino detects the power button being held and kills 5v after 2 seconds, and then kills all power. It can mute&kill audio too
2. Mute audio as soon as I2C communication stops?
3. Mute audio before enabling and disabling the audio LDO
4. Set up 30-50ms button debouncing.
5. Allow receiving of commands over I2C (dimming, mute)?
6. Allow button combos to change behaviors? Dim/kill lcd
*/

#include <Wire.h>
//#include <SPI.h>
#include "Pin_Macros.h"
#include "LCD_Timings.h"
#include "GPIO.h"

// Buffer and flag for received I2C data
volatile byte receivedData[3];
volatile byte receivedCRC;
volatile bool dataReceived = false;

#define I2C_ADDRESS 0x10

#define DEBOUNCE_CYCLES 5 // keep the button pressed for this many loops. can be 0-255. each loop is 10ms
#define LOW_BATTERY_THRESHOLD 68 // 3.2v
#define GOOD_BATTERY_THRESHOLD 76 // 3.6v

byte brightness = B00000001;
uint16_t detectTimeout = 0;

byte arduinoInputsB;
byte arduinoInputsD;
byte registerInputs1;
byte registerInputs2;

bool displayButtonPressed = false;
bool muteButtonPressed = false;
bool isMute = false;
bool idleI2C = true; // the atmega starts with audio muted until i2c is accessed, so it avoids popping sounds
bool sleepMode = false;
uint8_t idleI2Ccounter = 0;
bool batteryLow = false;
bool forceOrangeLED = false;

unsigned long previousMillis = 0;
const long interval = 10; // ms delay between the start of each loop

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
  uint8_t STATUS = 0; // MUTE|LEFT_SWITCH|HOLD|POWER|(unused)|BRIGHTNESS|BRIGHTNESS|BRIGHTNESS
  uint8_t JOY_LX;
  uint8_t JOY_LY;
  uint8_t JOY_RX;
  uint8_t JOY_RY;
  uint8_t CRC8;

};

I2C_Structure I2C_data; // create the structure for the I2C data

#define BTN_MUTE I2C_data.buttonA & B00000001

void setup() {


  Wire.begin(I2C_ADDRESS);  // join i2c bus
  Wire.onRequest(requestEvent); // send data to rpi
  Wire.onReceive(receiveEvent); // receive data from rpi
  //SPI.begin();
  //SPI.setBitOrder(MSBFIRST); // can this be removed?
  //(SPI_MODE0); // can this be removed?

  // These and the macros will go away once pin states are verified, and I will just do this once with a single command for each port
  setPinAsInput(BTN_DISPLAY);
  setPinAsInput(BTN_EXTRA_2);
  setPinAsOutput(ONEWIRE_LCD);
  setPinAsOutput(PWM_LED_ORANGE);
  setPinAsInput(SPI_DATA_IN);
  setPinAsOutput(SPI_CLOCK);
  setPinAsOutput(EN_5V0);
  setPinAsOutput(LED_LEFT);

  setPinAsInput(BTN_EXTRA_1);

  setPinAsInput(EN_AMP);
  setPinAsInput(DETECT_RPI);

  setPinAsOutput(SPI_SHIFT_LOAD);
  setPinAsInput(BTN_SD);
  setPinAsInput(BTN_HOLD);
  setPinAsInput(LEFT_SWITCH);
  setPinAsOutput(EN_AUDIO);

  // SPI_DATA_IN is controlled by SPI
  // SPI_CLOCK is controlled by SPI
  setPinLow(ONEWIRE_LCD);
  setPinHigh(PWM_LED_ORANGE); // will probably do PWM instead
  setPinLow(EN_5V0);
  setPinLow(EN_AMP);
  //setPinLow(AUDIO_GAIN_0);
  setPinLow(SPI_SHIFT_LOAD);
  setPinLow(DETECT_RPI);
  setPinLow(LED_LEFT);
  setPinLow(EN_AUDIO);
  setPinHigh(BTN_DISPLAY);
  setPinHigh(BTN_EXTRA_2);
  setPinHigh(LEFT_SWITCH);
  setPinHigh(BTN_SD);
  setPinHigh(BTN_HOLD);
  setPinHigh(BTN_EXTRA_1);

  delay(500);
  setPinHigh(EN_5V0);

  // this disables the backlight and audio until the Pi is detected
  disableDisplay();
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
  setPinHigh(ONEWIRE_LCD);
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
  // scan the GPIOs that are used for input
  // do these pins benefit from debouncing?
  arduinoInputsB = PINB;
  arduinoInputsD = PIND;
}

uint8_t bitBangSPIReadByte() {
    uint8_t data = 0;

    for (uint8_t i = 0; i < 8; i++) {
        // Set clock low
        setPinLow(SPI_CLOCK);
        // Allow some time for data to settle. Depending on your setup, you might not need this delay.
        delayMicroseconds(1);
        // Read the bit and shift it into our data byte
        if (readPin(SPI_DATA_IN)) {
            data |= (1 << (7 - i)); // Read MSB first
        }
        // Set clock high to signal end of bit read
        setPinHigh(SPI_CLOCK);
        // Again, provide a small delay if necessary.
        delayMicroseconds(1);
    }
    return data;
}

void readShiftRegisterInputs(){
  // Prepare 74HC165D for parallel load
  setPinLow(SPI_SHIFT_LOAD);
  delayMicroseconds(5); // give some time to setup, you may not need this
  setPinHigh(SPI_SHIFT_LOAD);

  // Use hardware SPI to read 2 bytes from the 74HC165D chips and store them for I2C. Will add debouncing once all other basic functions work.
  // Flip every bit so that 1 means pressed. This will also be used in the dimming/low power function.
  // add debouncing?
  //I2C_data.buttonA = ~SPI.transfer(0);
  //I2C_data.buttonB = ~SPI.transfer(0);
  I2C_data.buttonA = ~bitBangSPIReadByte();
  I2C_data.buttonB = ~bitBangSPIReadByte();
}

//create functions for each thing
void detectButtons() {
  detectMute();
  detectLeftSwitch();
  detectHoldSwitch();
  detectShutdownButton();
  detectDisplayButton();
  detectRPi();
}

void detectMute() {
  if (BTN_MUTE) {
    muteButtonPressed = 1;
  } else {
    // invert EN_AUDIO
    if (muteButtonPressed == 1) {
      if (isMute == false) {
        I2C_data.STATUS |= B10000000; // Set bit 7
        isMute = true;
        setMuteStatus();
      } else {
        I2C_data.STATUS &= B01111111; // Clear bit 7
        isMute = false;
        setMuteStatus();
      }
      muteButtonPressed = 0;
    }
  }
}

void detectLeftSwitch() {
  if (readPin(LEFT_SWITCH)) {
    I2C_data.STATUS &= B10111111; // Clear bit 6
  } else {
    I2C_data.STATUS |= B01000000; // Set bit 6
  }
}

void detectHoldSwitch() {
  if (sleepMode) {
    // check whether we should exit sleep mode
    if (readPin(BTN_HOLD)) {
      // exit sleep mode
      I2C_data.STATUS &= B11011111; // Clear bit 5 // this lets the Pi know whether the hold switch is down
      sleepMode = false;
      // now need to deal with the possibility that the power switch is accidentally pressed. just adding a small delay before getting back to scanning all inputs
      // really need to just ignore the power button alone for a second or two, but a delay will work for now
      delay(500);
      enableDisplay();
      setMuteStatus();
    }
  } else {
    // check whether we should enter sleep mode
    if (!readPin(BTN_HOLD)) {
      I2C_data.STATUS |= B00100000; // Set bit 5
      sleepMode = true;
      disableDisplay();
      setMuteStatus();
    }
  }
}

void detectShutdownButton() {
  if (readPin(BTN_SD)) {
    I2C_data.STATUS &= B11101111; // Clear bit 4
  } else {
    I2C_data.STATUS |= B00010000; // Set bit 4
  }
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
        I2C_data.STATUS = (I2C_data.STATUS & B11111000) | ((brightness >> 2) & B00000111); // store the brightness level for transmission over i2c. there are only 8 levels, so use 3 bits.
        setBrightness(brightness);
      }
    }
}

void detectRPi() {
    if (readPin(DETECT_RPI)) {  // Raspberry Pi is detected
        if (detectTimeout) {  // if the pi is detected during the timeout
            enableDisplay();
            detectTimeout = 0;
        }
    } else {  // Raspberry Pi is not detected
        if (!detectTimeout) {  // if the timeout sequence hasn't started yet
            disableDisplay();
        }

        if (detectTimeout > 500) {  // if the timeout reaches 5 seconds
            setPinLow(EN_5V0);
        } else {
          detectTimeout++;
        }
    }
}

uint8_t computeCRC8_direct(const uint8_t *data, uint8_t length) {
    uint8_t crc = 0;
    uint8_t poly = 0x07; // Corresponds to the polynomial x^8 + x^2 + x + 1

    for (uint8_t i = 0; i < length; i++) {
        crc ^= data[i];
        for (uint8_t j = 0; j < 8; j++) {
            if (crc & 0x80) {
                crc = (crc << 1) ^ poly;
            } else {
                crc <<= 1;
            }
        }
    }
    return crc;
}

void setOrangeLED() {
  (batteryLow || forceOrangeLED) ? setPinLow(PWM_LED_ORANGE) : setPinHigh(PWM_LED_ORANGE);
}

void processReceivedData() {
  if (receivedData[0] == 0x20) { // this command sets the WiFi LED high or low
    (receivedData[1]) ? setPinHigh(LED_LEFT) : setPinLow(LED_LEFT);
  }
  if (receivedData[0] == 0x21) { // this command is LED_ON and LED_OFF. It just sets flag that determines whether the LED stays orange. It must always turn orange when the battery is low. LED may also PWM pulse when I2C data goes idle?
    forceOrangeLED = receivedData[1];
    setOrangeLED();
  }
  if (receivedData[0] == 0x22) { // this command is DISPLAY_ON and DISPLAY_OFF. will also need something to override display off when a button is pressed, in case the pi doesnt sent it for some reason

  }
  dataReceived = false;
}

void requestEvent() {
  // Compute the CRC-8 value for the data, excluding the CRC8 byte itself
  I2C_data.CRC8 = computeCRC8_direct((const uint8_t*) &I2C_data, sizeof(I2C_data) - 1);

  // Send the data, including the computed CRC8 value, to the Raspberry Pi
  Wire.write((const uint8_t*) &I2C_data, sizeof(I2C_data));
  if (idleI2C) {
    idleI2C = false;
    setMuteStatus();
  }
  idleI2Ccounter = 0;
}

void receiveEvent(int numBytes) {
  if (numBytes == 4) {  // Ensure we're receiving the expected 4 bytes
    receivedData[0] = Wire.read();
    receivedData[1] = Wire.read();
    receivedData[2] = Wire.read();
    receivedData[3] = Wire.read();
    dataReceived = true;  // Set the flag to notify the main loop
  }
}

void readAnalogInputs() {
  I2C_data.JOY_RX = (analogRead(JOY_RX_PIN) >> 2);
  I2C_data.JOY_RY = (analogRead(JOY_RY_PIN) >> 2);
  I2C_data.SENSE_SYS = (analogRead(SENSE_SYS_PIN));
  I2C_data.SENSE_BAT = (analogRead(SENSE_BAT_PIN));
  // handle low battery LED
  if (batteryLow == true) {
    if (I2C_data.SENSE_SYS > GOOD_BATTERY_THRESHOLD) {
      batteryLow = false;
      setOrangeLED();
    }
  } else {
    if (I2C_data.SENSE_SYS < LOW_BATTERY_THRESHOLD) {
      batteryLow = true;
      setOrangeLED();
      }
    }

  I2C_data.JOY_LX = (analogRead(JOY_LX_PIN) >> 2);
  I2C_data.JOY_LX = (I2C_data.JOY_LX & B11111110) | readPin(BTN_EXTRA_1); // use LSB for value of extra button 1, to avoid having to send an extra byte for button data

  I2C_data.JOY_LY = (analogRead(JOY_LY_PIN) >> 2);
  I2C_data.JOY_LY = (I2C_data.JOY_LY & B11111110) | readPin(BTN_EXTRA_2); // use LSB for value of extra button 2
}

void setMuteStatus() {
  // mute the audio whenever any of the conditions is true
  if (isMute || idleI2C || sleepMode) {
    // turn off the amplifier, then disable power to audio
    setPinAsOutput(EN_AMP);
    delay(1); // tinker with this value, may only need to be a few milli or even microseconds
    setPinLow(EN_AUDIO);
  } else {
    // enable power to audio, then turn on the amplifier
    setPinAsInput(EN_AMP);
    delay(1);
    setPinHigh(EN_AUDIO);
  }
}

void disableDisplay() {
  setPinLow(ONEWIRE_LCD);
}

void enableDisplay() {
  initializeBacklight(); // re-initialize and enable backlight
}

void loop() {
  // the functions run, on average, every 10 milliseconds
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    // save the last time the loop was executed
    previousMillis = currentMillis;
    // when in sleep mode, only scan analog (for battery) and scan for hold switch
    // still transmit some things (maybe just battery, so pi knows to emergency shutdown)
    readArduinoInputs(); // this always happens
    readAnalogInputs(); // this always happens, prob need to set all 4 joysticks to center point (and dont forget extra buttons)
    if (sleepMode) {
      I2C_data.buttonA = B00000000; // buttons are set to unpressed at all times when in sleep mode
      I2C_data.buttonB = B00000000;
      detectHoldSwitch();
    } else {
      readShiftRegisterInputs(); // this doesn't happen when the hold switch is down
      detectButtons(); // this doesn't happen when the hold switch is down
    }

    if (idleI2Ccounter < 25) {
      idleI2Ccounter++;
      if (idleI2Ccounter == 25) {  // if no i2c for 250 milliseconds, mute the audio
        idleI2C = true;
        setMuteStatus();
      }
    }
  }

  if (dataReceived) { // if data was received from the rpi
    processReceivedData(); // process the data
    dataReceived = false;  // Clear the flag after processing
  }
  delay(1); //sleep for a millisecond
}

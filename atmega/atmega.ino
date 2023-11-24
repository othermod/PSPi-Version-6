#include <Wire.h>
#include <EEPROM.h>
#include "Pin_Macros.h"
#include "LCD_Timings.h"

// Buffer and flag for received I2C data
volatile byte receivedData[3];
volatile bool dataReceived = false;

#define I2C_ADDRESS 0x10
#define BRIGHTNESS_ADDRESS 0
#define MUTE_ADDRESS 4

#define DEBOUNCE_CYCLES 5 // keep the button pressed for this many loops. can be 0-255. each loop is 10ms
#define EMERGENCY_SHUTOFF_THRESHOLD 1050 // 3.076v (1050 * 3000 / 1024)
#define LOW_BATTERY_THRESHOLD 1095 // 3.208v (1095 * 3000 / 1024)
#define GOOD_BATTERY_THRESHOLD 1216 // 3.562v (1216 * 3000 / 1024)
#define BTN_MUTE I2C_data.buttonA & B00000001

// I2C Receiving Commands
#define CMD_SET_WIFI_LED 0x20
#define CMD_SET_LED_STATE 0x21
#define CMD_SET_BRIGHTNESS 0x22
#define CMD_SET_IDLE_ACTION 0x23

byte brightness = B00000001;
uint16_t detectRPiTimeout = 0;
uint16_t senseSYSAverage = GOOD_BATTERY_THRESHOLD; // keeps the battery LED from starting orange
uint16_t senseBATAverage;
byte registerInputs1;
byte registerInputs2;

uint16_t displayButtonPressed = 0;
bool muteButtonPressed = false;
bool isMute = false;
bool isIdleI2C = true; // the atmega starts with audio muted until i2c is accessed, so it avoids popping sounds

bool sleepIndicatorDirection = 0;
uint8_t sleepIndicatorPWM = 255;

bool isSleeping = false;
uint8_t idleI2Ccounter = 0;
bool batteryLow = false;
bool forceOrangeLED = false;

unsigned long previousMillis = 0;
const long interval = 10; // ms delay between the start of each loop

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
  uint8_t CRC16_high; // High byte of 16-bit CRC
  uint8_t CRC16_low;  // Low byte of 16-bit CRC
};

I2C_Structure I2C_data; // create the structure for the I2C data

void setup() {
  Wire.begin(I2C_ADDRESS);  // join i2c bus
  Wire.onRequest(requestEvent); // send data to rpi
  Wire.onReceive(receiveEvent); // receive data from rpi

  byte eepromValue = EEPROM.read(BRIGHTNESS_ADDRESS) & B00011111; // Read and mask the value
  if ((eepromValue & B00000001) && !(eepromValue & B00000010)) {
    brightness = eepromValue; // Valid value, update the global variable
  } else {
    EEPROM.write(BRIGHTNESS_ADDRESS, brightness); // Invalid value, reset EEPROM
  }

  eepromValue = EEPROM.read(MUTE_ADDRESS); // Read and mask the value
  if (eepromValue == 1) {
    isMute = true;
  }

  // Port B Configuration
  DDRB  = B11111100;  // 7: LED_LEFT, 6: EN_5V0, 5: SPI_CLOCK, 4: SPI_DATA_IN, 3: PWM_LED_ORANGE, 2: ONEWIRE_LCD, 1: BTN_EXTRA_2, 0: BTN_DISPLAY
  PORTB = B00101011;  // 7: LED_LEFT (low), 6: EN_5V0 (low), 5: SPI_CLOCK (high), 4: SPI_DATA_IN (low), 3: PWM_LED_ORANGE (high), 2: ONEWIRE_LCD (low), 1: BTN_EXTRA_2 (high), 0: BTN_DISPLAY (high)
  // Port D Configuration
  DDRD  = B00001000;  // 7: EN_AUDIO, 6: LEFT_SWITCH, 5: BTN_HOLD, 4: BTN_SD, 3: SPI_SHIFT_LOAD, 2: BTN_EXTRA_1, 1: DETECT_RPI, 0: EN_AMP
  PORTD = B01110100;  // 7: EN_AUDIO (low), 6: LEFT_SWITCH (high), 5: BTN_HOLD (high), 4: BTN_SD (high), 3: SPI_SHIFT_LOAD (low), 2: BTN_EXTRA_1 (high), 1: DETECT_RPI (low), 0: EN_AMP (low)
  // set up the PWM pin, and set the state to high so it stays green
  #if defined(__AVR_ATmega8A__)
    TCCR2 |= (1 << WGM21) | (1 << WGM20);
    TCCR2 |= (1 << COM21);
    TCCR2 |= (1 << CS20);
    OCR2 = 255;
  #elif defined(__AVR_ATmega328P__)
    TCCR2A |= (1 << WGM21) | (1 << WGM20);
    TCCR2A |= (1 << COM2A1);
    TCCR2B |= (1 << CS20);
    OCR2A = 255;
  #endif

  delay(500);
  setPinHigh(EN_5V0);

  // this disables the backlight and audio until the Pi is detected
  disableDisplay();
  detectRPiTimeout++;
}

void initializeBacklight() {
  // Startup sequence for EasyScale
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
  I2C_data.STATUS = (I2C_data.STATUS & B11111000) | ((brightness >> 2) & B00000111); // store the brightness level for transmission over i2c. there are only 8 levels, so use 3 bits.
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
        setPinHigh(SPI_CLOCK); // Set clock high to signal end of bit read
        delayMicroseconds(1); // Again, provide a small delay if necessary.
    }
    return data;
}

void readShiftRegisterInputs() {
  // Prepare 74HC165D for parallel load
  setPinLow(SPI_SHIFT_LOAD);
  delayMicroseconds(5); // give some time to setup, you may not need this
  setPinHigh(SPI_SHIFT_LOAD);

  // Use bitbanged SPI to read 2 bytes from the 74HC165D chips and store them for I2C. Was using hardware, but it was taking control of MOSI.
  // Flip every bit so that 1 means pressed. This will also be used in the dimming/low power function.
  I2C_data.buttonA = ~bitBangSPIReadByte();
  I2C_data.buttonB = ~bitBangSPIReadByte();
}

//create functions for each thing
void detectButtons() {
  detectMuteButton();
  detectLeftSwitch();
  detectHoldSwitch();
  detectShutdownButton();
  detectDisplayButton();
  detectRPi();
}

void detectMuteButton() {
  if (BTN_MUTE) {
    muteButtonPressed = 1;
  } else {
    // invert EN_AUDIO
    if (muteButtonPressed == 1) {
      if (isMute == false) {
        isMute = true;
        setMuteStatus();
      } else {
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
  if (isSleeping) {
    // check whether we should exit sleep mode
    if (readPin(BTN_HOLD)) {
      // exit sleep mode
      I2C_data.STATUS &= B11011111; // Clear bit 5
      isSleeping = false;
      delay(500);
      enableDisplay();
      setMuteStatus();

      // disable PWM mode on orange LED
      setOrangeLED();
    }
  } else {
    // check whether we should enter sleep mode
    if (!readPin(BTN_HOLD)) {
      I2C_data.STATUS |= B00100000; // Set bit 5
      isSleeping = true;
      disableDisplay();
      setMuteStatus();
      sleepIndicatorPWM = 255; // start the pwm at full green
      sleepIndicatorDirection = 0;
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
      if (displayButtonPressed) {
        brightness = (brightness + 4) & B00011111; // &ing the byte should keep the brightness from going past 31. it will return to 00000001 when it passes 31
        displayButtonPressed = 0;
        setBrightness(brightness);
      }
    }
}

void storeBrightnessMute() {
  EEPROM.update(BRIGHTNESS_ADDRESS, brightness);
  EEPROM.update(MUTE_ADDRESS, isMute);
}

void detectRPi() {
    if (readPin(DETECT_RPI)) {  // Raspberry Pi is detected
        if (detectRPiTimeout) {  // if the pi is detected during the timeout
            enableDisplay();
            detectRPiTimeout = 0;
        }
    } else {  // Raspberry Pi is not detected
        if (!detectRPiTimeout) {  // if the timeout sequence hasn't started yet
            disableDisplay();
        }

        if (detectRPiTimeout > 500) {  // if the timeout reaches 5 seconds
           storeBrightnessMute(); // save the current brightness to eeprom
           setPinLow(EN_5V0);
           delay(10000); // prevent flicker, guarantee poweroff
        } else {
          detectRPiTimeout++;
        }
    }
}

uint16_t computeCRC16_CCITT(const uint8_t *data, uint8_t length) {
    uint16_t crc = 0xFFFF; // Initial value for CRC-16-CCITT
    uint16_t poly = 0x1021; // Polynomial for CRC-16-CCITT

    for (uint8_t i = 0; i < length; i++) {
        crc ^= ((uint16_t)data[i] << 8);
        for (uint8_t j = 0; j < 8; j++) {
            if (crc & 0x8000) {
                crc = (crc << 1) ^ poly;
            } else {
                crc <<= 1;
            }
        }
    }
    return crc;
}

void setOrangeLED() {
  #if defined(__AVR_ATmega8A__)
    (batteryLow || forceOrangeLED) ? OCR2 = 0 : OCR2 = 255;
  #elif defined(__AVR_ATmega328P__)
    (batteryLow || forceOrangeLED) ? OCR2A = 0 : OCR2A = 255;
  #endif
}

void processReceivedData() {
  switch (receivedData[0]) {
    case CMD_SET_WIFI_LED:
      if (receivedData[1]) {
        setPinHigh(LED_LEFT);
      } else {
        setPinLow(LED_LEFT);
      }
      break;
    case CMD_SET_LED_STATE:
      forceOrangeLED = receivedData[1];
      setOrangeLED();
      break;
    case CMD_SET_BRIGHTNESS:
      if (receivedData[1] >= 1 && receivedData[1] <= 8) {
        brightness = 1 + 4 * (receivedData[1] - 1);
        setBrightness(brightness);
      }
      break;
    case CMD_SET_IDLE_ACTION:
      // turn on off ability to dim LCD after being idle for numbee mins (allow setting of the time too with another command)
      // any button, including display button, should brighten it again
      // maybe too complicated
      // byte one is Command
      //byte 2 is num of minutes to wait (0 turns off dimming)
      break;

    default:
      // Handle unknown command
      // Add error handling if required

      break;
  }
}


void requestEvent() {
  // Temporary variable for CRC calculation
  uint16_t tempCRC = computeCRC16_CCITT((const uint8_t*) &I2C_data, 9);

  // Split the 16-bit CRC into two 8-bit values and store them in the structure
  I2C_data.CRC16_high = (uint8_t)(tempCRC >> 8);
  I2C_data.CRC16_low = (uint8_t)(tempCRC & 0xFF);

  // Send the data, including the CRC bytes, to the Raspberry Pi
  Wire.write((const uint8_t*) &I2C_data, sizeof(I2C_data));

  // check to see whether audio was muted due to idle i2c. if so, re-enable audio
  if (isIdleI2C) {
    isIdleI2C = false;
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
  I2C_data.JOY_LX = analogRead(JOY_LX_PIN) >> 2;
  I2C_data.JOY_LY = analogRead(JOY_LY_PIN) >> 2;
  I2C_data.JOY_RX = (analogRead(JOY_RX_PIN) >> 2 & B11111110) | (readPin(BTN_EXTRA_1) ? 0 : 1); // right joysticks also contain extra button data
  I2C_data.JOY_RY = (analogRead(JOY_RY_PIN) >> 2 & B11111110) | (readPin(BTN_EXTRA_2) ? 0 : 1);

  senseSYSAverage = senseSYSAverage - (senseSYSAverage >> 4) + analogRead(SENSE_SYS_PIN);  // create an average of 16 readings
  senseBATAverage = senseBATAverage - (senseBATAverage >> 4) + analogRead(SENSE_BAT_PIN);

  I2C_data.SENSE_SYS = senseSYSAverage >> 3; // bitshift i2c data by 3, since it will fit into a byte
  I2C_data.SENSE_BAT = senseBATAverage >> 3;

  if (batteryLow) {
    if (senseSYSAverage > GOOD_BATTERY_THRESHOLD) {
      batteryLow = false;
      setOrangeLED();
    }
  } else {
    if (senseSYSAverage < LOW_BATTERY_THRESHOLD) {
      batteryLow = true;
      setOrangeLED();
    }
  }
}

void setMuteStatus() {
  // mute the audio whenever any of the conditions is true
  if (isMute || isIdleI2C || isSleeping) {
    // turn off the amplifier, then disable power to audio
    setPinAsOutput(EN_AMP);
    delay(1); // tinker with this value, may only need to be a few milli or even microseconds
    setPinLow(EN_AUDIO);
    I2C_data.STATUS |= B10000000; // Set bit 7
  } else {
    // enable power to audio, then turn on the amplifier
    setPinAsInput(EN_AMP);
    delay(1);
    setPinHigh(EN_AUDIO);
    I2C_data.STATUS &= B01111111; // Clear bit 7
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
    readAnalogInputs(); // this always happens, prob need to set all 4 joysticks to center point (and dont forget extra buttons)
    if (isSleeping) {

      // set the PWM duty
      if (sleepIndicatorDirection == 1) {
        sleepIndicatorPWM++;
        if (sleepIndicatorPWM == 255) {
          sleepIndicatorDirection = 0;
        }
      }
      else {
        sleepIndicatorPWM--;
        if (sleepIndicatorPWM == 0) {
          sleepIndicatorDirection = 1;
        }
      }
      if (batteryLow) { // make sure LED stays orange when battery is low
        sleepIndicatorPWM = 0;
      }
      #if defined(__AVR_ATmega8A__)
        OCR2 = sleepIndicatorPWM;
      #elif defined(__AVR_ATmega328P__)
        OCR2A = sleepIndicatorPWM;
      #endif
      if ((sleepIndicatorPWM == 0) | (sleepIndicatorPWM == 255)) {
        delay(500); // keep LED green or red on for a moment
      }
      detectHoldSwitch();
      detectRPi(); // this is needed in case the hold switch is down when the pi is removed or powers off
    } else {
      readShiftRegisterInputs(); // this doesn't happen when the hold switch is down
      detectButtons(); // this doesn't happen when the hold switch is down
    }

    if (idleI2Ccounter < 25) {
      idleI2Ccounter++;
      if (idleI2Ccounter == 25) {  // if no i2c for 250 milliseconds, mute the audio
        isIdleI2C = true;
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

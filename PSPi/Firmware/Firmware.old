#include <avr/wdt.h>
#include <Wire.h>
#include <avr/sleep.h>
#include <EEPROM.h>
#include "pins_arduino.h"

#define I2C_ADDRESS 0x06
#define SWITCH_DEBOUNCE_TIME 50 // ms
//-----------------------------------------------------------
// Analog Pins
#define VOLTAGE_PIN 2
#define AMPERAGE_PIN 3
#define ANALOG_PIN_X 7
#define ANALOG_PIN_Y 6
//-----------------------------------------------------------
// I2C Commands
#define CHANGE_OPERATING_MODE 0x02 // byte 1
#define RESET_TO_BOOTLOADER 0x01 // byte 2

#define SET_ACTIVE_BRIGHTNESS 0x03
// byte 2 is 0-255 for brightness

#define CHANGE_BACKLIGHT_SETTING_IN_EEPROM 0x04 // byte 1
// byte 2 is 0-7 for position
// byte 3 is 0-255 for brightness

#define CHANGE_MUTE_STATUS 0x05 // byte 1
#define MUTE_AUDIO 0x01 // byte 2
#define UNMUTE_AUDIO 0x02 // byte 2

#define CHANGE_ORANGE_LED_STATUS 0x06 // byte 1
#define FORCE_ORANGE_LED 0x01 // byte 2
#define UNFORCE_ORANGE_LED 0x02 // byte 2
//-----------------------------------------------------------
// EEPROM Positions
#define BACKLIGHT_START_POSITION 8
//-----------------------------------------------------------
// Modes
#define ACTIVE_MODE 1
#define IDLE_MODE 2
#define STARTUP_MODE 3 // in case something should be configured on the atmega at startup? probably not
//-----------------------------------------------------------
byte sleepBlinker = 0;
byte operatingMode = IDLE_MODE;
byte PWMarray[8];
uint16_t idleCounter = 0;

byte backlightActivePosition;
uint16_t DisplayButtonPressed = 0;
bool MuteButtonPressed = 0;
bool forcedOrangeLED = 0;
bool orangeLEDstatus = 0;
byte receivedData[] = {0,0,0,0,0,0,0,0,0};

const int rolling = 64;
uint16_t AVGvolt = 119 * rolling;
uint16_t AVGamp = 119 * rolling;
unsigned long timeOfLastRequest = millis();

// gpio mapping
#define BTN_DPAD_UP 0
#define BTN_DPAD_DOWN 1
#define BTN_DPAD_RIGHT 2
#define BTN_TR 3
#define BTN_A 4
#define PWM_PIN 5
#define BTN_B 6
#define BTN_START 7
#define BTN_SELECT 8
#define BTN_DISPLAY 9
#define BTN_HOME 10
#define BTN_MUTE 11
#define LOWBATT_PIN 12
#define MUTE_OUTPUT 13
#define BTN_TL 14
#define BTN_DPAD_LEFT 15
#define BTN_X 20
#define BTN_Y 21

struct InputSwitch {
  unsigned char pin;
  unsigned char state;
  unsigned long time;
  unsigned char bitPosition;
};

// the (up to 16) buttons (arduino pin #, state, time, bitPosition)
InputSwitch switches[] = {
  {BTN_A,         HIGH,0,0x00}, // A
  {BTN_B,         HIGH,0,0x01}, // B
  {BTN_X,         HIGH,0,0x02}, // X
  {BTN_Y,         HIGH,0,0x03}, // Y
  {BTN_TL,        HIGH,0,0x04}, // LTRIGGER
  {BTN_TR,        HIGH,0,0x05}, // RTRIGGER
  {BTN_SELECT,    HIGH,0,0x06}, // SELECT
  {BTN_START,     HIGH,0,0x07}, // START
  {BTN_DPAD_UP,   HIGH,0,0x08}, // UP
  {BTN_DPAD_DOWN, HIGH,0,0x09}, // DOWN
  {BTN_DPAD_LEFT, HIGH,0,0x0A}, // LEFT
  {BTN_DPAD_RIGHT,HIGH,0,0x0B}, // RIGHT
  {BTN_HOME,      HIGH,0,0x0C}, // HOME
  {BTN_DISPLAY,   HIGH,0,0x0D}, // DISPLAY BUTTON
  {BTN_MUTE,      HIGH,0,0x0E}, // MUTE BUTTON
  {MUTE_OUTPUT,   HIGH,0,0x0F}, // MUTE STATUS
};

// return true if switch state has changed!
bool updateSwitch(struct InputSwitch *sw)
{
  int newState = digitalRead(sw->pin);
  if (newState != sw->state && millis() - sw->time > SWITCH_DEBOUNCE_TIME)
  {
    // change state!
    sw->state = newState;
    // record last update
    sw->time = millis();
    return true;
  }

  // else
  return false;
}

// I2C data definition
struct I2CJoystickStatus
{
  uint16_t buttons; // button status
  byte axis0; // first axis
  byte axis1; // second axis
  uint16_t voltage; // rolling average of voltage
  uint16_t amperage;  // rolling average of amperage
  byte brightness;
};

I2CJoystickStatus joystickStatus;

void scanAnalog(){
  // read analog stick values, change to 8 bit because it doesnt need more accuracy
  joystickStatus.axis0 = analogRead(ANALOG_PIN_X) / 4;
  joystickStatus.axis1 = analogRead(ANALOG_PIN_Y) / 4;

  // Keep a rolling average of the battery and amperage ADC readings. Divide the readings by "rolling" on Pi to get the ADC value.
  AVGvolt = AVGvolt - (AVGvolt / rolling) + analogRead(VOLTAGE_PIN);
  joystickStatus.voltage = AVGvolt;
  AVGamp = AVGamp - (AVGamp / rolling) + analogRead(AMPERAGE_PIN);
  joystickStatus.amperage = AVGamp;

  //Orange LED when battery is below 3.3v. Green LED when battery is above 3.5v.
  if (orangeLEDstatus == 0){
    // If orange LED is off
    if ((joystickStatus.voltage < 6000) or(forcedOrangeLED == 1))
    {
      // See whether orange LED should be turned on
      digitalWrite(LOWBATT_PIN, 1);
      orangeLEDstatus = 1;
    }
  }
  else
  {
    // If orange LED is on
    if ((joystickStatus.voltage > 6300) and(forcedOrangeLED == 0)) {
      // See whether orange LED should be turned off
      digitalWrite(LOWBATT_PIN, 0);
      orangeLEDstatus = 0;
    }
  }
}

void scanInput(){
  for (int i = 0; i < sizeof(switches) / sizeof(InputSwitch); i++) {
    if (updateSwitch(&switches[i]))
    {
      if (switches[i].state == HIGH)  // button released
        joystickStatus.buttons &= ~(1 << switches[i].bitPosition);
      else  // button pressed
        joystickStatus.buttons |= (1 << switches[i].bitPosition);
    }
  }

  static uint16_t oldButtons = 0;
  if (joystickStatus.buttons != oldButtons) {
    oldButtons = joystickStatus.buttons;
  }
}

void checkDisplay(){
  // Check if Display button is pressed
  if (((joystickStatus.buttons >> 0x0D) &1) == 1)  {
    DisplayButtonPressed++;
    // check whether button was held for 2.5s to update eeprom
    // write eeprom. show it by flashing the screen
    if (DisplayButtonPressed == 250) {
      analogWrite(PWM_PIN, 0);
      delay(100);
      analogWrite(PWM_PIN, PWMarray[backlightActivePosition]);
      EEPROM.update(BACKLIGHT_START_POSITION, backlightActivePosition);
    }
  }  else  {
    // when button is not pressed, check whether it was pressed on the last loop
    // also make sure the button wasn't previously held to update the eeprom. if so, don't change the brightness
    if ((DisplayButtonPressed > 0) && (DisplayButtonPressed) < 250)    {
      // Cycle to next brightness setting
      backlightActivePosition++;
      if (backlightActivePosition > 7) {backlightActivePosition = 0;}
      joystickStatus.brightness = backlightActivePosition;
      // Set brightness from current position
      analogWrite(PWM_PIN, PWMarray[backlightActivePosition]);
    }
    // remember that Display button is not pressed on this loop
    DisplayButtonPressed = 0;
  }
}

void checkMute(){
  if ((((joystickStatus.buttons >> 0x0E) &1) == 1) and(MuteButtonPressed == 0))  {
    // If Mute button is pressed
    digitalWrite(MUTE_OUTPUT, (!digitalRead(MUTE_OUTPUT))); // Invert Mute Condition on Amplifier
    MuteButtonPressed = 1;
  }

  if ((((joystickStatus.buttons >> 0x0E) &1) == 0) and(MuteButtonPressed == 1))  {
    // If Mute button is not pressed
    MuteButtonPressed = 0;
  }
}

void performTask(){
  switch (receivedData[0]){
    
    case CHANGE_MUTE_STATUS:
      if (receivedData[1] = MUTE_AUDIO){
        digitalWrite(MUTE_OUTPUT, 1);
      }
      if (receivedData[1] = UNMUTE_AUDIO){
        digitalWrite(MUTE_OUTPUT, 0);
      }
      break;

    case CHANGE_ORANGE_LED_STATUS:
      if (receivedData[1] = FORCE_ORANGE_LED){
        forcedOrangeLED = 1;
      }
      if (receivedData[1] = UNFORCE_ORANGE_LED){
        forcedOrangeLED = 0;
      }
      break;

    case CHANGE_OPERATING_MODE:
      if (receivedData[1] = RESET_TO_BOOTLOADER){
        softwareReset( WDTO_60MS);
      }
      break;

    case SET_ACTIVE_BRIGHTNESS:
      analogWrite(PWM_PIN, receivedData[1]);
      break;

    case CHANGE_BACKLIGHT_SETTING_IN_EEPROM:
      if (receivedData[1] > 7){ // byte 2 is the position, only 0-7 is valid
        break;
      }
      EEPROM.update(receivedData[1], receivedData[2]); //update the eeprom, using value from byte 3
      PWMarray[receivedData[1]] =  receivedData[1]; //update the active array with new value from byte 2
      analogWrite(PWM_PIN, PWMarray[backlightActivePosition]); // update active brightness using new array, in case the value changed
      break;
  }
}

// function that executes whenever data is requested by master
// this function is registered as an event, see setup()
void requestEvent(){
  Wire.write((char*) &joystickStatus, sizeof(I2CJoystickStatus)); // send the data to the Pi
  idleCounter = 0;
}

void receiveEvent(int numBytes){
  int i = 0;
  while (Wire.available() > 0){
    receivedData[i] = Wire.read();
    i++;
  }
}

void setup(){
  Wire.begin(I2C_ADDRESS);  // join i2c bus
  Wire.onRequest(requestEvent); // register event
  Wire.onReceive(receiveEvent); // register event

  //read PWM values from EEPROM
  int arraySum = 0;
  for (int i = 0; i < 8; i++) {
    PWMarray[i] = EEPROM.read(i);
    if (PWMarray[i] == 255 ){
      arraySum++;
    }
  }
  
  // check the array and see whether its all 255s, the default value after flashing new firmware
  // if so, overwrite the array and overwrite the eeprom with the specified values
  if (arraySum == 8) { 
    PWMarray[0] = {55}; 
    PWMarray[1] = {62};
    PWMarray[2] = {69};
    PWMarray[3] = {75};
    PWMarray[4] = {80};
    PWMarray[5] = {90};
    PWMarray[6] = {100};
    PWMarray[7] = {255};
    for (int i = 0; i < 8; i++)  {
       EEPROM.update(i, PWMarray[i]);
    }
  }

  // check the eeprom position, and if > 7, write a 2
  backlightActivePosition = EEPROM.read(BACKLIGHT_START_POSITION); //read default position from EEPROM
  if (backlightActivePosition > 7) {
    backlightActivePosition = 2;
  }

  pinMode(LOWBATT_PIN, OUTPUT);
  digitalWrite(LOWBATT_PIN, 0);
  pinMode(MUTE_OUTPUT, OUTPUT);
  //Mute audio until i2c communication wakes the atmega
  digitalWrite(MUTE_OUTPUT, 0);
  // default button and joystick values
  joystickStatus.buttons = 0;
  joystickStatus.axis0 = 127;
  joystickStatus.axis1 = 127;
  // pin configuration
  for (int i = 0; i < sizeof(switches) / sizeof(InputSwitch); i++)  {
    pinMode(switches[i].pin, INPUT_PULLUP);
  }

  //Start initial brightness setting on PWM pin
  pinMode(PWM_PIN, OUTPUT);
  // in case the eeprom data is bad, just set maximum brightness
  if (backlightActivePosition > 7)  {backlightActivePosition = 7;}
  analogWrite(PWM_PIN, PWMarray[backlightActivePosition]);
}

//void resetFunc() { asm volatile ("jmp 0x00"); } // couldn't make this work. Wasn't fully resetting? Using watchdog instead

void softwareReset( uint8_t prescaller) {
  // start watchdog with the provided prescaller
  wdt_enable( prescaller);
  // wait for the prescaller time to expire
  // without sending the reset signal by using
  // the wdt_reset() method
  while(1) {}
}

byte blink = 0;
void loop() {
  if (operatingMode == ACTIVE_MODE){
    scanInput();
    checkDisplay();
    checkMute();
    if (idleCounter == 200) { // go to idle mode when i2c communication doesn't happen for 2 seconds
      operatingMode = IDLE_MODE;
    } else {
      idleCounter++;
      }
  } else if (operatingMode == IDLE_MODE){
    if (blink == 0) {
      forcedOrangeLED = !forcedOrangeLED;
    }
    blink++;
    if (idleCounter == 0) {
      operatingMode = ACTIVE_MODE;
      forcedOrangeLED = 0;
      analogWrite(PWM_PIN, PWMarray[backlightActivePosition]);
    }
  }

  if (receivedData[0] > 0) {
    //if Pi sent a command
    performTask();
    receivedData[0] = 0;
  }
 
  scanAnalog();
  delay(10);
}

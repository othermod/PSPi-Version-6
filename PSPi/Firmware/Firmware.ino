#include <Wire.h>
#include <avr/sleep.h>
#include "pins_arduino.h"

// ------------------------------------------
// Configuration
// ------------------------------------------
#define I2C_ADDRESS 0x18
#define SWITCH_DEBOUNCE_TIME 50 // ms

//Analog
#define ANALOG_PIN_X 7
#define ANALOG_PIN_Y 6
#define VOLTAGE_PIN 2
#define AMPERAGE_PIN 3

//Output
#define PWM_PIN 5
#define LOWBATT_PIN 12
#define MUTE_PIN 13

int PWMarray[] = {55,62,69,75,80,90,100,255};
int PWMposition = 1;
bool DisplayButtonPressed = 0;
bool MuteButtonPressed = 0;
bool forcedOrangeLED = 0;
bool orangeLEDstatus = 0;
const int rolling = 64;
uint16_t AVGvolt = 119 * rolling;
uint16_t AVGamp = 119 * rolling;

// button position in uint16_t buttons
#define BTN_A           0x00
#define BTN_B           0x01
#define BTN_X           0x02
#define BTN_Y           0x03
#define BTN_TL          0x04
#define BTN_TR          0x05
#define BTN_SELECT      0x06
#define BTN_START       0x07
#define BTN_DPAD_UP     0x08
#define BTN_DPAD_DOWN   0x09
#define BTN_DPAD_LEFT   0x0A
#define BTN_DPAD_RIGHT  0x0B
#define BTN_1           0x0C
#define BTN_DISPLAY     0x0D
#define BTN_MUTE        0x0E
#define MUTE_OUTPUT     0x0F

struct InputSwitch {
  unsigned char pin;
  unsigned char state;
  unsigned long time;
  unsigned char code;
};

// the (up to 16) buttons (arduino pin #, state, time, code)
InputSwitch switches[] = {
  {4,  HIGH, 0, BTN_A},          // A
  {6,  HIGH, 0, BTN_B},          // B
  {20, HIGH, 0, BTN_X},          // X
  {21, HIGH, 0, BTN_Y},          // Y
  {14, HIGH, 0, BTN_TL},         // LTRIGGER
  {3,  HIGH, 0, BTN_TR},         // RTRIGGER
  {8,  HIGH, 0, BTN_SELECT},     // SELECT
  {7,  HIGH, 0, BTN_START},      // START
  {0,  HIGH, 0, BTN_DPAD_UP},    // UP
  {1,  HIGH, 0, BTN_DPAD_DOWN},  // DOWN
  {15, HIGH, 0, BTN_DPAD_LEFT},  // LEFT
  {2,  HIGH, 0, BTN_DPAD_RIGHT}, // RIGHT
  {10, HIGH, 0, BTN_1},          // HOME
  {9,  HIGH, 0, BTN_DISPLAY},    // DISPLAY BUTTON
  {11, HIGH, 0, BTN_MUTE},       // MUTE BUTTON
  {13, HIGH, 0, MUTE_OUTPUT},    // MUTE STATUS
};

// return true if switch state has changed!
bool updateSwitch(struct InputSwitch *sw) {
  int newState = digitalRead(sw->pin);
  if(newState != sw->state && millis() - sw->time > SWITCH_DEBOUNCE_TIME) {
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
struct I2CJoystickStatus {
  uint16_t buttons; // button status
  uint8_t axis0; // first axis
  uint8_t axis1; // second axis
  uint16_t voltage; // rolling average of voltage
  uint16_t amperage; // rolling average of amperage
};

I2CJoystickStatus joystickStatus;

void setup() {
  Wire.begin(I2C_ADDRESS);      // join i2c bus 
  Wire.onRequest(requestEvent); // register event
  Wire.onReceive(receiveEvent); // register event

  //Blink the Low Battery LED to show that ATMega is starting
  pinMode(LOWBATT_PIN, OUTPUT);
  digitalWrite(LOWBATT_PIN, 0);
  delay(500);
  digitalWrite(LOWBATT_PIN, 1);
  delay(500);
  digitalWrite(LOWBATT_PIN, 0);
  delay(500);
  digitalWrite(LOWBATT_PIN, 1);
  delay(500);
  digitalWrite(LOWBATT_PIN, 0);

  // default button and joystick status
  joystickStatus.buttons = 0;
  joystickStatus.axis0 = 127;
  joystickStatus.axis1 = 127;
  
  // pin configuration
  for(int i = 0; i < sizeof(switches) / sizeof(InputSwitch); i++) {
    pinMode(switches[i].pin, INPUT_PULLUP);
  }

  //Unmute audio at startup and put the pin set it as output (the loop above set it to input).
  pinMode(MUTE_PIN, OUTPUT);
  digitalWrite(MUTE_PIN, 0);
  
  //Start initial brightness setting on PWM pin
  pinMode(PWM_PIN, OUTPUT);
  analogWrite(PWM_PIN, PWMarray[PWMposition]);

}

void scanAnalog() {
  // read analog stick values, change to 8 bit because it doesnt need more accuracy
  joystickStatus.axis0 = analogRead(ANALOG_PIN_X) / 4;
  joystickStatus.axis1 = analogRead(ANALOG_PIN_Y) / 4;
  
  // Keep a rolling average of the battery and amperage ADC readings. Divide the readings by "rolling" on Pi to get the ADC value.
  AVGvolt = AVGvolt - (AVGvolt / rolling) + analogRead(VOLTAGE_PIN);
  joystickStatus.voltage = AVGvolt;
  AVGamp = AVGamp - (AVGamp / rolling) + analogRead(AMPERAGE_PIN);
  joystickStatus.amperage = AVGamp;
  
  //Orange LED when battery is below 3.3v. Green LED when battery is above 3.5v.
  if (orangeLEDstatus == 0){                                                  // If orange LED is off
    if ((joystickStatus.voltage < 6000) or (forcedOrangeLED == 1)) {          // See whether orange LED should be turned on
      digitalWrite(LOWBATT_PIN, 1);
      orangeLEDstatus = 1;
    }
  }
  else {                                                                      // If orange LED is on
    if ((joystickStatus.voltage > 6300) and (forcedOrangeLED == 0)) {         // See whether orange LED should be turned off
      digitalWrite(LOWBATT_PIN, 0);
      orangeLEDstatus = 0;
    }
  }
}

void scanInput() {
  for(int i = 0; i < sizeof(switches) / sizeof(InputSwitch); i++) {
    if(updateSwitch(&switches[i])) {
      if(switches[i].state == HIGH) // button released
        joystickStatus.buttons &= ~(1 << switches[i].code);
      else // button pressed
        joystickStatus.buttons |= (1 << switches[i].code);
    }
  }
  static uint16_t oldButtons = 0;
  if(joystickStatus.buttons != oldButtons) {
    oldButtons = joystickStatus.buttons;
  }
}

void checkDisplay() {
    if(((joystickStatus.buttons >> BTN_DISPLAY) & 1) == 1){                                     // Check if Display button is pressed
      if (DisplayButtonPressed == 0){                                                           // ans wasn't pressed on the previous loop
        DisplayButtonPressed = 1;                                                               // remember that Display button is pressed on this loop
        PWMposition++;
        if(PWMposition > 7) {                                                                   // Cycle to next brightness setting
          PWMposition = 0;
        }
        analogWrite(PWM_PIN, PWMarray[PWMposition]);                                            // Change brightness
      }
    }
    else{                                                                                       // If Display button is not pressed
      DisplayButtonPressed = 0;                                                                 // remember that Display button is not pressed on this loop
    }
}

void checkMute() {
    if((((joystickStatus.buttons >> BTN_MUTE) & 1) == 1) and (MuteButtonPressed == 0)){         // If Mute button is pressed
      digitalWrite(MUTE_PIN, (! digitalRead(MUTE_PIN)));                                        // Invert Mute Condition on Amplifier
      MuteButtonPressed = 1;
    }
    if((((joystickStatus.buttons >> BTN_MUTE) & 1) == 0) and (MuteButtonPressed == 1)){         // If Mute button is not pressed
      MuteButtonPressed = 0;
    }
}

void loop() {
  scanAnalog();
  scanInput();
  checkDisplay();
  checkMute();
  delay(10);
}

// function that executes whenever data is requested by master
// this function is registered as an event, see setup()
void requestEvent() {
  Wire.write((char *)&joystickStatus, sizeof(I2CJoystickStatus)); 
}

void receiveEvent(int numBytes) {
  uint8_t receivedData = Wire.read();
  if (receivedData == 0) // enter sleep mode
    analogWrite(PWM_PIN, 0);
  if (receivedData == 1)
    analogWrite(PWM_PIN, PWMarray[PWMposition]); // return from sleep mode
  if (receivedData == 2)
    digitalWrite(MUTE_PIN, 0);
  if (receivedData == 3)
    digitalWrite(MUTE_PIN, 1);
  if (receivedData == 4)
    forcedOrangeLED = 1;
  if (receivedData == 5)
    forcedOrangeLED = 0;
  if (receivedData > 40)
    analogWrite(PWM_PIN, receivedData);
}

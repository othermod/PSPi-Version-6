#include <Wire.h>

#define I2C_ADDRESS 0x10

// Digital Input Port B
#define SET_PORTB_PINS_AS_INPUTS DDRB &= B00000000
#define ENABLE_PULLUPS_ON_PORTB  PORTB = B11111111
#define READ_PORTB_PINS          PINB

// Digital Input Port D
#define SET_PORTD_PINS_AS_INPUTS DDRD &= B00000000
#define ENABLE_PULLUPS_ON_PORTD  PORTD = B11111111
#define READ_PORTD_PINS          PIND

#define DEBOUNCE_CYCLES 5 // keep the button pressed for this many loops. can be 0-255. each loop is 10ms
#define ANALOG_PIN1 0
#define ANALOG_PIN2 1
#define ANALOG_PIN3 2
#define ANALOG_PIN4 3
#define ANALOG_PIN5 6
#define ANALOG_PIN6 7

unsigned long previousMillis = 0;
const long interval = 10; // interval at which to blink (milliseconds)

uint8_t debouncePortB[8] = {0}; // button stays pressed for a few cycles to debounce and to make sure the button press isn't missed
uint8_t debouncePortD[8] = {0};

struct I2C_Structure { // define the structure layout for transmitting I2C data to the Raspberry Pi
  uint8_t buttonsPortB; // button status
  uint8_t buttonsPortD; // button status
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

void readButtons(){
  //Pin registers are accessed directly. This reads all 8 GPIOs on each register with one command.
  byte readingB = ~READ_PORTB_PINS; // read the pins and invert them, so that a 1 means pushed
  byte readingD = ~READ_PORTD_PINS;

  byte i;
  for(i=0;i<8;i++) {
    // for port B buttons
    if ((readingB >> i) & 1) {            // if this button is pressed
      debouncePortB[i] = DEBOUNCE_CYCLES; // begin the debounce function for this button
    }
    else {                                // if this button is not pressed
      if (debouncePortB[i]) {             // if debounce function is active ( > 0)
        debouncePortB[i]--;               // decrement the debounce function
        readingB = readingB|(1<<i);       // keep this pin pressed
      }
    }
    // for port D buttons
    if ((readingD >> i) & 1){             // if this button is pressed
      debouncePortD[i] = DEBOUNCE_CYCLES; // begin the debounce function for this button
    }
    else {                                // if this button is not pressed
      if (debouncePortD[i]) {             // if debounce function is active ( > 0)
        debouncePortD[i]--;               // decrement the debounce function
        readingD = readingD|(1<<i);       // keep this pin pressed
      }
    }
  }
  I2C_data.buttonsPortB = readingB; // copy the completed readings into the i2c variable to be read by the Raspberry Pi
  I2C_data.buttonsPortD = readingD;
}

void readAnalog(){
  I2C_data.analog1=(analogRead(ANALOG_PIN1) >> 2); // read the ADCs, and reduce from 10 to 8 bits
  I2C_data.analog2=(analogRead(ANALOG_PIN2) >> 2);
  I2C_data.analog3=(analogRead(ANALOG_PIN3) >> 2);
  I2C_data.analog4=(analogRead(ANALOG_PIN4) >> 2);
  I2C_data.analog5=(analogRead(ANALOG_PIN5) >> 2);
  I2C_data.analog6=(analogRead(ANALOG_PIN6) >> 2);
}

void setup(){
  Wire.begin(I2C_ADDRESS);  // join i2c bus
  Wire.onRequest(requestEvent); // register event
  SET_PORTB_PINS_AS_INPUTS;
  ENABLE_PULLUPS_ON_PORTB;
  SET_PORTD_PINS_AS_INPUTS;
  ENABLE_PULLUPS_ON_PORTD;
}

void loop() {
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    // save the last time the loop was executed
    previousMillis = currentMillis;

    // Your functions here
    readButtons();
    readAnalog();
  }
}

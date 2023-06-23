#define SENSE_RESISTOR_MILLIOHM 100 // maybe allow the Pi to change this and store in EEPROM
#define VOLTAGE 1 // voltage mode is the initial condition
#define RESISTOR_A_KOHM 150
#define RESISTOR_B_KOHM 10
#define BATTERY_INTERNAL_RESISTANCE_MILLIOHM 270

// when the atmega begins, it should detect voltage based off voltage and amperage.
// when pi initializes, it switches to coloumb counting. create variable for capacity and allow pi to transmit it to the atmega

struct Battery_Structure {
  bool calculationMode;
  uint16_t ADCReadingSys; // will this ever be bigger than 1 byte?
  uint16_t ADCReadingBat; // will this ever be bigger than 1 byte?
  uint16_t rollingAverageADCSys; // should stay under 2 bytes in all situations
  uint16_t rollingAverageADCBat; // should stay under 2 bytes in all situations
  unsigned long voltageSys; // should stay under 4 bytes in all situations
  unsigned long voltageBat; // should stay under 4 bytes in all situations
  uint16_t actualVoltage;
  int actualVoltageDropAcrossSenseResistor;
  int actualAmperage;
  int correctedVoltage;
};

Battery_Structure BATTERY_DATA;

void readADCs() {
  BATTERY_DATA.ADCReadingSys = analogRead(7);
  BATTERY_DATA.ADCReadingBat = analogRead(6);
}

void calculateVoltages() {

  // rolling average of 16 ADC readings. this just eliminates some noise and increases resolution
  BATTERY_DATA.rollingAverageADCSys = BATTERY_DATA.rollingAverageADCSys - (BATTERY_DATA.rollingAverageADCSys / 16) + BATTERY_DATA.ADCReadingSys;

  BATTERY_DATA.rollingAverageADCBat = BATTERY_DATA.rollingAverageADCBat - (BATTERY_DATA.rollingAverageADCBat / 16) + BATTERY_DATA.ADCReadingBat;

  // the voltage will be 16x larger than the actual reading. factor this in later
  BATTERY_DATA.voltageSys = BATTERY_DATA.rollingAverageADCSys; // copy 2 byte variable to 4 byte variable so there's enough size
  BATTERY_DATA.voltageSys = BATTERY_DATA.voltageSys * 825 / 256; // Actually 3300 / 1024. can also do bitshift instead. End result will be (voltageSys * 825 ) >> 8

  BATTERY_DATA.voltageBat = BATTERY_DATA.rollingAverageADCBat;
  BATTERY_DATA.voltageBat = BATTERY_DATA.voltageBat * 825 / 256;

  // voltage step 1 of 3
  // the resistor voltage gives us a voltage of 1/16th the actual battery, so the ADC reading must be multiplied x16 to account for this
  // the rolling average already does this, so we can use the voltage reading created from the rolling average
  BATTERY_DATA.actualVoltage = BATTERY_DATA.voltageSys;
  // the voltage needs one more correction, which will be done after the voltage drop on the resistor is calculated

  // amperage step 1 of 3
  // the amperage is measured by calculating the difference between the two voltage readings
  BATTERY_DATA.actualVoltageDropAcrossSenseResistor = (BATTERY_DATA.voltageSys - BATTERY_DATA.voltageBat) / 16; // the rolling averages are 16x the actual reading, so the result has to be divided by 16

  // amperage step 2 of 3
  // the amperage reading now has to be corrected because the two resistor voltage dividers slightly skew the voltage drop reading slightly
  BATTERY_DATA.actualVoltageDropAcrossSenseResistor = BATTERY_DATA.actualVoltageDropAcrossSenseResistor*(RESISTOR_A_KOHM+RESISTOR_B_KOHM)/RESISTOR_A_KOHM;

  // amperage step 3 of 3
  // calculate the actual amperage using the sense resistor value
  BATTERY_DATA.actualAmperage = BATTERY_DATA.actualVoltageDropAcrossSenseResistor*(1000 / SENSE_RESISTOR_MILLIOHM);

  // voltage step 2 of 3
  // add the voltage drop to the read voltage system side, which will give the actual battery voltage
  BATTERY_DATA.actualVoltage = BATTERY_DATA.actualVoltage - BATTERY_DATA.actualVoltageDropAcrossSenseResistor; // make sure 2 bytes is large enough for all situations

  // voltage step 3 of 3
  // the final step is to determine the actual battery voltage, because the battery has internal resistance and the votlage is affected by charging and discharging it
  // we have to estimate what the voltage would be in an idle state
  BATTERY_DATA.correctedVoltage = BATTERY_DATA.actualVoltage + BATTERY_DATA.actualAmperage * BATTERY_INTERNAL_RESISTANCE_MILLIOHM / 1000;
}

void determineBatteryPercent() {
  if (BATTERY_DATA.calculationMode = VOLTAGE) {  // stay in voltage mode long enough to estimate the state of charge, then switch to coulomb counting
    //start with rollingAverageADCSys and rollingAverageADCBat. they are 16x larger than the ADC reading, so factor this in when converting to a voltage
    //convert the readings to a voltage

//    I2C_DATA.voltageSys = rollingAverageADCSys;
//    I2C_DATA.voltageBat = rollingAverageADCBat;
    //from pspi v6
    //int voltageDifference = voltageSys-voltageBat;
    //int amperage = voltageDifference * 1000 * (160 / 150) / SENSE_RESISTOR_MILLIOHM;  //the 160/150 accounts for the 150/10 voltage divider. Make sure the numerator and denomonator are correct
    //int actualVoltage = readVoltage * 16 + amperage / 10;
    //int rawVoltage = readVoltage * 16;
    //printf("\nreadVoltageADC: %d", I2C_DATA.voltage);
    //printf("\nreadAmperageADC: %d", I2C_DATA.amperage + 255 * (I2C_DATA.amperage < 50)); // the last part is just for the 8 bit rollover. just tinkering
    //printf("\nreadVoltage: %d", readVoltage);
    //printf("\nreadAmperage: %d", readAmperage);
    //printf("\nvoltageDifference: %d", voltageDifference);
    //printf("\namperage: %d", -amperage);
    //printf("\ncalculatedVoltage: %d", actualVoltage);
    //printf("\nrawVoltage: %d", rawVoltage);
    //from pspi v5
    //batteryData.rawVoltage = currentReading.voltage * 36300 / 1024 / 64;
    //batteryData.amperage = (currentReading.voltage - currentReading.amperage) * 10 / 11;
    //batteryData.amperage = batteryData.amperage * 36300 / 1024 / 64;
    //batteryData.amperage = batteryData.amperage * (100 / SENSE_RESISTOR_MILLIOHM);

    //if ((batteryData.amperage < -25) & ((batteryData.correctedVoltage < 4100)|(batteryData.isCharging == 0))) {
    //  batteryData.isCharging = 1;
    //} else if ((batteryData.amperage < 25) & (batteryData.correctedVoltage > 4150)) {
    //  batteryData.isCharging = 2;
    //} else if ((batteryData.amperage > 25) & (batteryData.rawVoltage < 4200)) {
    //  batteryData.isCharging = 0;
    //}

    //int temp = batteryData.rawVoltage + batteryData.amperage * BATTERY_INTERNAL_RESISTANCE / 1000;
    //if (firstLoop) { //set the initial (specifically correctedVoltage) battery condition
    //  batteryData.correctedVoltage = temp;
    //  firstLoop = 0;
    //}
    //hysteresis
    //if (temp > batteryData.correctedVoltage + 25) {
    //  batteryData.correctedVoltage++;
    //} //25mV of hysteresis to keep battery bar from bouncing around
    //if (temp < batteryData.correctedVoltage - 25) {
    //  batteryData.correctedVoltage--;
    //}
    //batteryData.percent = 100 - (4150 - batteryData.correctedVoltage) / 8.5;
    //if (batteryData.percent > 100) {
    //  batteryData.percent = 100;
    //}
    //if (batteryData.percent < 0) {
    //  batteryData.percent = 0;
    //}
  } else {

  }
}
void setup(){
  Wire.begin(I2C_ADDRESS);  // join i2c bus
  Wire.onRequest(requestEvent); // register event
  SET_PORTB_PINS_AS_INPUTS;
  ENABLE_PULLUPS_ON_PORTB;
  SET_PORTD_PINS_AS_INPUTS;
  ENABLE_PULLUPS_ON_PORTD;
  BATTERY_DATA.rollingAverageADCSys = analogRead(7) * 16; // set up the initial condition
  BATTERY_DATA.rollingAverageADCBat = analogRead(6) * 16; // set up the initial condition
  //Serial.begin(9600);
}

 void loop(){
  while (1){
    readButtons();            // read all 16 GPIOs
    readADCs();          // read both joysticks (4 ADCs)
    calculateVoltages();
    determineBatteryPercent();
    I2C_DATA.actualVoltage = BATTERY_DATA.actualVoltage;
    I2C_DATA.actualAmperage = BATTERY_DATA.actualAmperage;
    I2C_DATA.correctedVoltage = BATTERY_DATA.correctedVoltage;
    //Serial.println();
    //Serial.println(BATTERY_DATA.actualVoltage);
    //Serial.println(BATTERY_DATA.actualAmperage);
    //Serial.println(BATTERY_DATA.correctedVoltage);
    delay(100); // will have to make the delay more precise for coulomb counting to work
  }
}

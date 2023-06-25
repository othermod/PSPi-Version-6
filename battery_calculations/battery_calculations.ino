#define SENSE_RESISTOR_MILLIOHM 100 // maybe allow the Pi to change this and store in EEPROM
#define VOLTAGE 1 // voltage mode is the initial condition
#define COULOMB 0
#define RESISTOR_A_KOHM 150
#define RESISTOR_B_KOHM 10
#define BATTERY_INTERNAL_RESISTANCE_MILLIOHM 270

// when the atmega begins, it should detect voltage based off voltage and amperage.
// when pi initializes, it switches to coloumb counting. create variable for capacity and allow pi to transmit it to the atmega

typedef struct {
  bool calculationMode;
  bool isCharging;
  uint16_t voltageSYSx16;
  uint16_t voltageBATx16;
  uint32_t voltageSYS;
  uint32_t voltageBAT;
  uint16_t rawVoltage;
  uint16_t senseRVoltageDifference;
  uint16_t finalAmperage;
  uint16_t finalVoltage;
} Battery_Structure;

Battery_Structure battery;

void calculateAmperage() {
  uint16_t readVoltageSYS = analogRead(7) * 3000 / 1024;
  uint16_t readVoltageBAT = analogRead(6) * 3000 / 1024;

  // rolling average of 16 ADC readings. eliminates some noise and increases accuracy
  battery.voltageSYSx16 = battery.voltageSYSx16 - (battery.voltageSYSx16 / 16) + readVoltageSYS;
  battery.voltageBATx16 = battery.voltageBATx16 - (battery.voltageBATx16 / 16) + readVoltageBAT;

  // amperage step 1 of 3
  // the amperage is measured by calculating the difference between the two voltage readings
  // the rolling averages are 16x the actual reading, so the result has to be divided by 16
  if (battery.voltageSYSx16 > battery.voltageBATx16) {
    battery.isCharging = 1;
    battery.senseRVoltageDifference = (battery.voltageSYSx16 - battery.voltageBATx16) / 16;
  } else {
    battery.isCharging = 0;
    battery.senseRVoltageDifference = (battery.voltageBATx16 - battery.voltageSYSx16) / 16;
  }
  // amperage step 2 of 3
  // the amperage reading now has to be corrected because the two resistor voltage dividers skew the voltage drop reading slightly
  battery.senseRVoltageDifference = battery.senseRVoltageDifference*(RESISTOR_A_KOHM+RESISTOR_B_KOHM)/RESISTOR_A_KOHM;
  // amperage step 3 of 3
  // calculate the actual amperage using the sense resistor value
  battery.finalAmperage = battery.senseRVoltageDifference*(1000 / SENSE_RESISTOR_MILLIOHM);
}

void calculateVoltage() {
  // voltage step 1 of 3
  // the resistor voltage gives us a voltage of 1/16th the actual battery, so the ADC reading must be multiplied x16 to account for this
  // the rolling average already does this, so we can use the voltage reading created from the rolling average
  battery.rawVoltage = battery.voltageSYSx16;
  // the voltage needs one more correction, which will be done after the voltage drop on the resistor is calculated
  // voltage step 2 of 3
  // add the voltage drop to the read voltage system side, which will give the actual battery voltage
  if (battery.isCharging) { // need to add or subtract depending on whether it is charging
    battery.rawVoltage = battery.rawVoltage - battery.senseRVoltageDifference;
  } else {
    battery.rawVoltage = battery.rawVoltage + battery.senseRVoltageDifference;
  }
  // voltage step 3 of 3
  // the final step is to determine the actual battery voltage, because the battery has internal resistance and the voltage is affected by charging and discharging it
  // we have to estimate what the voltage would be in an idle state
  if (battery.isCharging) {
  battery.finalVoltage = battery.rawVoltage - battery.finalAmperage * BATTERY_INTERNAL_RESISTANCE_MILLIOHM / 1000;
  } else {
  battery.finalVoltage = battery.rawVoltage + battery.finalAmperage * BATTERY_INTERNAL_RESISTANCE_MILLIOHM / 1000;
  }
}

void determineBatteryPercent() {
  if (battery.calculationMode == VOLTAGE) {  // stay in voltage mode long enough to estimate the state of charge, then switch to coulomb counting

  } else {

  }
}

void setup(){
  battery.voltageSYSx16 = analogRead(7) * 16; // set up the initial condition
  battery.voltageBATx16 = analogRead(6) * 16; // set up the initial condition
  //Serial.begin(9600);
}

 void loop(){
  while (1){
    calculateAmperage();
    calculateVoltage(); // this isnt needed after switching to coulomb mode
    determineBatteryPercent();
    delay(100); // will have to make the delay more precise for coulomb counting to work
  }
}

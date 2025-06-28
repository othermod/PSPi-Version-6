#define NORMAL_MODE_LOOP_MS 1       // Main loop interval
#define SLEEP_MODE_LOOP_MS 5       // Sleep mode loop interval
#define BTN_DEBOUNCE_LOOPS 10  // Buttons will remain "pressed" for this many loops
#define RPI_TIMEOUT 1000       // RPi detection timeout number of loops before forcing poweroff
#define SLEEP_EXIT_LOOPS 100    // Number of consecutive loops needed to exit sleep mode
#define I2C_ADDR 0x10
#define I2C_IDLE_TRIGGER 200    // Loops before entering idle mode
#define EEPROM_BRIGHT_ADDR 0
#define EEPROM_MUTE_ADDR 4
#define BAT_LOW 1095     // 3.2V
#define BAT_GOOD 1216    // 3.5V
#define BRIGHTNESS_DEFAULT 4 // 0-7 are valid
#define MUTE_DEFAULT 1 // 0-1 are valid
#define UPDATE_INTERVAL_REACHED currentTime - lastUpdateTime >= (state.sleeping ? SLEEP_MODE_LOOP_MS : NORMAL_MODE_LOOP_MS)

// Port B pins
#define BTN_DISP    B,0  // PB0
#define BTN_EXTRA2  B,1  // PB1
#define LCD_CONTROL B,2  // PB2
#define LED_BAT     B,3  // PB3
#define SPI_IN      B,4  // PB4
#define SPI_CLK     B,5  // PB5
#define EN_5V       B,6  // PB6
#define LED_WIFI    B,7  // PB7

// Port D pins
#define EN_AMP         D,0  // PD0
#define RPI_DETECT     D,1  // PD1
#define BTN_EXTRA1     D,2  // PD2
#define SPI_LD         D,3  // PD3
#define BTN_SHUTDOWN   D,4  // PD4
#define BTN_HLD        D,5  // PD5
#define SWITCH_WIFI    D,6  // PD6
#define EN_AUDIO_POWER D,7  // PD7

// ADC
#define JOY_RX 0
#define JOY_RY 1
#define SENS_SYS 2
#define SENS_BAT 3
#define JOY_LX 6
#define JOY_LY 7

// ADC processing macros
#define VOLT_AVG_SHIFT 4     // Voltage averaging shift
#define VOLT_8BIT_SHIFT 3    // Voltage shift to fit into 8-bits

// Timer configuration macros
#if defined(__AVR_ATmega8__)|(__AVR_ATmega8A__)
  #define TMR_CTRL TCCR2
  #define TMR_CTRL_INIT ((1<<WGM21)|(1<<WGM20)|(1<<COM21)|(1<<CS20))
  #define SET_BAT_LED OCR2
  #define TMR_B_INIT
#elif defined(__AVR_ATmega328P__)
  #define TMR_CTRL TCCR2A
  #define TMR_CTRL_INIT ((1<<WGM21)|(1<<WGM20)|(1<<COM2A1))
  #define SET_BAT_LED OCR2A
  #define TMR_B_INIT TCCR2B=(1<<CS20)
#else
  #error "Unsupported MCU"
#endif

// GPIO Port manipulation macros
#define DDR(p) DDR##p
#define PORT(p) PORT##p
#define PIN(p) PIN##p
#define BIT(n) (1<<n)

// GPIO Pin control macros
#define setOutMode(p,n) DDR(p)|=BIT(n)
#define setInMode(p,n) DDR(p)&=~BIT(n)
#define setHigh(p,n) PORT(p)|=BIT(n)
#define setLow(p,n) PORT(p)&=~BIT(n)
#define getPin(p,n) (PIN(p)&BIT(n))

// GPIO Simplified pin interface macros
#define setPinAsOutput(pin) setOutMode(pin)
#define setPinAsInput(pin) setInMode(pin)
#define setPinHigh(pin) setHigh(pin)
#define setPinLow(pin) setLow(pin)
#define readPin(pin) getPin(pin)

// TPS61160 Backlight EasyScale Protocol
#define LCD_ADDR 0x72

// LCD timing (microseconds)
#define T_START 10   // Start condition
#define T_EOS 10     // End of sequence
#define T_H_LB 10    // High time, low bit
#define T_H_HB 25    // High time, high bit
#define T_L_LB 25    // Low time, low bit
#define T_L_HB 10    // Low time, high bit
#define T_OFF 3000   // Reset time

#define READ_MUTE_BUTTON i2cdata.buttons & 0b0000000000000001

#define LED_FULL_GREEN 255
#define LED_FULL_ORANGE 0

// I2C Command IDs
#define CMD_WIFI 0x20
#define CMD_LED 0x21
#define CMD_BRIGHT 0x22
#define CMD_MUTE 0x23
#define CMD_CRC 0x24

#define FADE_TO_ORANGE 0
#define FADE_TO_GREEN 1

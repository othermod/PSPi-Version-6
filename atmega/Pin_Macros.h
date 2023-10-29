// Define all of the GPIO pins in a way that the macros can read/write
#define BTN_DISPLAY B,0
#define BTN_EXTRA_2 B,1
#define ONEWIRE_LCD B,2
#define PWM_LED_ORANGE B,3
#define SPI_DATA_IN B,4
#define SPI_CLOCK B,5
#define EN_5V0 B,6
#define LED_LEFT B,7

#define EN_AMP D,0
#define DETECT_RPI D,1
#define BTN_EXTRA_1 D,2
#define SPI_SHIFT_LOAD D,3
#define BTN_SD D,4
#define BTN_HOLD D,5
#define LEFT_SWITCH D,6
#define EN_AUDIO D,7

// Define all of the analog pins
#define JOY_RX_PIN 0
#define JOY_RY_PIN 1
#define SENSE_SYS_PIN 2
#define SENSE_BAT_PIN 3
#define JOY_LX_PIN 6
#define JOY_LY_PIN 7

#define DDR(port) DDR##port
#define PORT(port) PORT##port
#define PIN(port) PIN##port
#define BIT(pin) (1 << pin)

#define pinModeOutput(port, pin) DDR(port) |= BIT(pin)
#define pinModeInput(port, pin) DDR(port) &= ~BIT(pin)
#define pinWriteHigh(port, pin) PORT(port) |= BIT(pin)
#define pinWriteLow(port, pin) PORT(port) &= ~BIT(pin)
#define pinRead(port, pin) (PIN(port) & BIT(pin))

#define setPinAsOutput(pin) pinModeOutput(pin)
#define setPinAsInput(pin) pinModeInput(pin)
#define setPinHigh(pin) pinWriteHigh(pin)
#define setPinLow(pin) pinWriteLow(pin)
#define readPin(pin) pinRead(pin)

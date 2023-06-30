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

# PSPi 6: 2023.08.12 Prototype Notes and Fixes

## Components to be Placed Manually

**Note**: This prototype has different manual components than later revisions. Use this list instead of the one in boards/README.md.

The following components are not available for automatic placement and must be placed manually:

1. **Gold Plated Beads/Pads for Joystick Contact**: [AliExpress Link for 1.0mm Beads](https://s.click.aliexpress.com/e/_DDhnfcj) or [AliExpress Link for 1.3mm](https://s.click.aliexpress.com/e/_DEbcF3V)
2. **PSP Barrel Jack SMD Connector**: [AliExpress Link](https://s.click.aliexpress.com/e/_DErpHYb)
3. **PSP Headphone Jack Connector**: [AliExpress Link](https://s.click.aliexpress.com/e/_DDpWHFz)
4. **miniUSB Connector**: [LCSC Link](https://www.lcsc.com/product-detail/_Jing-Extension-of-the-Electronic-Co-_C13453.html)

## Current Bugs

### Bug 1: [Audio Hiss on CM4]
- **Issue**: [The CM4 has a bug in the PWM audio, and always has a slight hiss. This isn't noticeable on headphones, but the amplifier makes it loud on the speakers]
- **Fix**: [Replace C21 and C25 with 1uF capacitors. Replace R20 and R29 with 100 Ohm resistors. Solder 2 100nF capacitors, one between the right pad of C14 and GND and one between the left pad of C33 and GND.]

### Bug 2: [Headphone/Speaker Switching]
- **Issue**: [The speakers should disable only when headphones are plugged in, but they stay disabled at all times]
- **Fix**: [Solder two 10k resistors. One between the left pad of C43 and the top pad of C25, the other between the left pad of C42 and the bottom pad of C21]

### Bug 3: [Activity LED Not working on CM4]
- **Issue**: [The activity LED works on the Pi Zero, but not on the CM4]
- **Fix**: [Remove Q7 and replace with a 0 Ohm (or at least <1K Ohm) resistor. The resistor should connect across the top and right pads where Q7 was positioned]

### Bug 4: [USB Disabled Until Audio Plays]
- **Issue**: [The USB mux uses the second audio pin to switch between Pi0 and CM4 USB routing. Sometimes this pin starts driven high, and other times it starts driven low. When it starts low, USB won't work until audio plays]
- **Fix**: [Add a short silent audio wav file to rc.local, so that audio initializes at bootup. This will be corrected in hardware in the production release.]

### Bug 5: [Flickering Charge LED During Charging]
- **Issue**: [The Charge IC pulses the LED quickly, and it causes the green and orange LEDs to show simultaneously]
- **Fix**: [Remove R5 (2K Ohm) and replace it with a 100K Ohm resistor]

### Bug 6: [Spontaneous Power-On When Charging]
- **Issue**: The board powers on unexpectedly when a charger is connected, or when the board reaches high temperatures
- **Root Cause**: Temperature-dependent reverse leakage current in diodes D3 and D4 (marked W1). As the board temperature increases, these diodes allow an increasing amount of reverse leakage current, which enables the power-on circuit. Charging exacerbates this by adding heat and maintaining battery at full voltage
- **Fix**: Replace diodes D3 and D4 with BAV70 diodes (marked A4). The BAV70 has better temperature stability and lower reverse leakage. LCSC C2501 / BAV70,215 (~$0.02 per unit). This fix has been validated in testing at 100°C board temperature.

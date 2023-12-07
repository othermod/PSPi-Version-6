# PSPi 6: 2023.08.12 Prototype Notes and Fixes

## Ordering Notes
- All boards in this project are 0.8mm thick. The default size for PCBs is 1.6mm, so make sure to change it.
- The PSPi 6 mainboard needs double-sided assembly, which is pricey.
- The CM4 carrier also needs both sides be placed, but it is not too difficult to solder the GPIO header, SD card, and switch if you want to save some money.
- The headphone board only needs single sided assembly.

## Components to be Placed Manually

Some components are not available for automatic placement and must be placed manually. Below is the list of these components with links to purchase them:

1. **Gold Plated Beads/Pads for Joystick Contact**: [AliExpress Link for 1.0mm Beads](https://s.click.aliexpress.com/e/_DDhnfcj) or [AliExpress Link for 1.3mm](https://s.click.aliexpress.com/e/_DEbcF3V)
2. **PSP Barrel Jack SMD Connector**: [AliExpress Link](https://s.click.aliexpress.com/e/_DErpHYb)
3. **PSP Headphone Jack Connector**: [AliExpress Link](https://s.click.aliexpress.com/e/_DDpWHFz)
4. **miniUSB Connector**: [LCSC Link](https://www.lcsc.com/product-detail/_Jing-Extension-of-the-Electronic-Co-_C13453.html)

The following items are also needed:
1. **M2.5x6mm Standoffs**: [AliExpress Link](https://s.click.aliexpress.com/e/_DBPcEQb)
2. **M2.5 Washer (0.5mm Thick)**: [AliExpress Link](https://s.click.aliexpress.com/e/_DFXVGBT)
3. **M2.5 Screw (3mm Long)**: [AliExpress Link](https://s.click.aliexpress.com/e/_Dlp9Lxn)
4. **M2.5 Screw (5mm Long)**: [AliExpress Link](https://s.click.aliexpress.com/e/_Dlp9Lxn)
5. **Pin Protection 3D Print**

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

# PSPi 6: 2023.08.12 Prototype Notes and Fixes

## Ordering Notes
- When ordering the PCB, you may encounter a designator error for U22. This is just a component library error for the board outline and can be safely ignored.
- The PSPi 6 mainboard needs double-sided assembly, which is pricey. The CM4 carrier also needs both sides be placed, but it is not too difficult to solder the GPIO header, SD card, and switch if you want to save some money. The headphone board only needs single sided assembly.

## Hardware Bugs and Manual Fixes

### Bug 1: [Headphone/Speaker Switching]
- **Issue**: [The speakers should disable only when headphones are plugged in, but they stay disabled at all times]
- **Fix**: [Solder two 10k resistors in the positions shown below]
- **Photos/Drawings**: [Include photos or drawings to visualize the fix]

### Bug 2: [Activity LED Not working on CM4]
- **Issue**: [The activity LED works on the Pi Zero, but not on the CM4]
- **Fix**: [Remove D? and replace with a 0 ohm (or at least <1k ohm) resistor, as shown below]
- **Photos/Drawings**: [Include photos or drawings to visualize the fix]

### Bug 3: [Audio Hiss on CM4]
- **Issue**: [The CM4 has a bug in the PWM audio, and always has a slight hiss. This isn't noticeable on headphones, but the amplifier makes it loud on the speakers]
- **Fix**: [Solder 100nf capacitors as shown. Solder 1uf capacitors as shown. Replace 220 ohm resistors shown with 100 ohm resistors.]
- **Photos/Drawings**: [Include photos or drawings to visualize the fix]

### Additional Resources
- [Links to external resources, datasheets, forums, etc.]

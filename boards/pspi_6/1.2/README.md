# PSPi 6 PCB 1.2 Notes and Fixes

## Changes Since Previous PCB
- Made the headphone pads slightly larger.
- Added gnd to firmware flashing pads.
- The board now accepts the custom through-hole joystick pads
- Swapped components to deal with shortages.
- No changes to Headphone and Carrier boards. Use 1.1 version.

## Current Bugs

### Bug 1: [Spontaneous Power-On When Charging]
- **Issue**: The board powers on unexpectedly when a charger is connected, or when the board reaches high temperatures
- **Root Cause**: Temperature-dependent reverse leakage current in diodes D3 and D4 (marked W1). As the board temperature increases, these diodes allow an increasing amount of reverse leakage current, which enables the power-on circuit. Charging exacerbates this by adding heat and maintaining battery at full voltage
- **Fix**: Replace diodes D3 and D4 with BAV70 diodes (marked A4). The BAV70 has better temperature stability and lower reverse leakage. LCSC C2501 / BAV70,215 (~$0.02 per unit). This fix has been validated in testing at 100°C board temperature.

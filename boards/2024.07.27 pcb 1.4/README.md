# PSPi 6 PCB 1.4 Notes and Fixes

## Notes

- PCB 1.4 was produced before the spontaneous power-on fix was implemented. Boards with this revision may be affected by the issue.
- Orders placed on or after April 1, 2026 include the corrected BAV70 diode instead of the BAT54C.
- The current BOM shows the updated component (BAV70 instead of BAT54C).
- If you have a PCB 1.4 board and are experiencing spontaneous power-on behavior, please apply the fix described below.

## Current Bugs

### Bug 1: [Spontaneous Power-On When Charging]
- **Issue**: The board powers on unexpectedly when a charger is connected, or when the board reaches high temperatures
- **Root Cause**: Temperature-dependent reverse leakage current in diodes D3 and D4 (marked W1). As the board temperature increases, these diodes allow an increasing amount of reverse leakage current, which enables the power-on circuit. Charging exacerbates this by adding heat and maintaining battery at full voltage
- **Fix**: Replace diodes D3 and D4 with BAV70 diodes (marked A4). The BAV70 has better temperature stability and lower reverse leakage. LCSC C2501 / BAV70,215 (~$0.02 per unit). This fix has been validated in testing at 100°C board temperature.

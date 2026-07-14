# PSPi 6 PCB 1.5 Notes

## Changes Since Previous PCB

- **Dual color WiFi LED**: Orange when enabled and not connected, green when connected. Off when the switch is down (was just green/off previously)
- **Power-on fix**: Swapped BAV70 in place of BAT54C to fix high current/heat power-on issue
- **DC jack power control**: Use EN_5V to control power flow to DC jack (instead of V_USB). This will kill external power input/output earlier and prevent issues where the FETs may latch on when the board is over 100°C (please never do this)

## Notes

- Testing in progress

## Board Layout


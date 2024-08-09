# PSPi 6 PCB 1.3 Notes and Fixes

## Ordering Notes
- All boards in this project are 0.8mm thick. The default size for PCBs is 1.6mm, so make sure to change it.
- The PSPi 6 mainboard needs double-sided assembly, which is pricey.
- The CM4 carrier also needs both sides be placed, but it is not too difficult to solder the GPIO header, SD card, and switch if you want to save some money.
- The headphone board only needs single sided assembly.

## Components to be Placed Manually

Some components are not available for automatic placement and must be placed manually. Below is the list of these components with links to purchase them:

1. **Gold Plated Pads for Joystick Contact (4ea needed for each board)**:
   - Option 1: [AliExpress Link for 1.3mm Pads](https://s.click.aliexpress.com/e/_DEbcF3V)
     - These pads need to be soldered into place by the user.
   - Option 2: [othermod's Custom Manufactured Pin](https://othermod.com/product/pspi-6-joystick-contact-pads/)
     - These are custom manufactured pins that don't require soldering, making assembly easier. Soldering is optional for added durability.
2. **PSP Barrel Jack SMD Connector**: [AliExpress Link](https://s.click.aliexpress.com/e/_DErpHYb)
3. **PSP Headphone Jack Connector**: [AliExpress Link](https://s.click.aliexpress.com/e/_DDpWHFz)

The following items are also needed:
1. **M2.5x6mm Standoffs**: [AliExpress Link](https://s.click.aliexpress.com/e/_DBPcEQb)
2. **M2.5 Washer (0.5mm Thick)**: [AliExpress Link](https://s.click.aliexpress.com/e/_DFXVGBT)
3. **M2.5 Screw (3mm Long)**: [AliExpress Link](https://s.click.aliexpress.com/e/_Dlp9Lxn)
4. **M2.5 Screw (5mm Long)**: [AliExpress Link](https://s.click.aliexpress.com/e/_Dlp9Lxn)
5. **Pin Protection 3D Print**

## Project Files
Access the editable schematics and PCBs on EasyEDA:
- [PSPi 6](https://oshwlab.com/adamseamster/pspi-zero-version-5_copy_copy)
- [CM4 Carrier Interface](https://oshwlab.com/adamseamster/pspi-version-6-cm4-interface)
- [Headphone Board](https://oshwlab.com/adamseamster/pspi-6-headphone-board)

## Changes Since Previous PCB
- Tweaked the joystick GND pad to make soldering easier.
- No changes to Headphone and Carrier boards. Use 1.1 version.

## Current Bugs
No known bugs

![Top](top.png)
![Bottom](bottom.png)

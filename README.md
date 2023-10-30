# PSPi 6
Welcome to the PSPi 6 GitHub repository! This project is a combination of hardware and software development aiming to retrofit a PSP with almost every type of Raspberry Pi.

![PSPi](https://othermod.com/wp-content/uploads/IMG_8727.jpg)

## 1. Operating System Images


I provide OS images to get you started quickly. You can download them [here](https://drive.proton.me/urls/04X9SX1KG8#zOBARZruUlqs).

I'm using only RetroPie during development, and will create images for the others once I have firmware and drivers more polished.

| Operating System | Zero (32-bit) | Zero 2W (32-bit) | Zero 2W (64-bit) | CM4 (32-bit) | CM4 (64-bit) |
|------------------|---------------|------------------|------------------|--------------|--------------|
| RetroPie         | ☑️             |                  |                  | ☑️            |            |
| Lakka            |               |                  |                  |              |              |
| Ubuntu           |               |                  |                  |              |           |
| Raspberry Pi OS  |               |                  |                  |              |           |
| Batocera         |               |                  |                  |              |              |
| Kali             |               |                  |                  |              |              |

Note: OS compatibility varies across different Raspberry Pi models.

## 2. Compatibility:
- **Supported PSP Cases:** Works with the original PSP 1000 shell only.
- **Supported Raspberry Pi Models**:
    - Compatible with all 40-pin Raspberry Pi versions.
    - Compatible with the CM4 using the optional CM4 Carrier board.
    - **Size Compatibility:** Only the Raspberry Pi Zero, Zero 2W, and CM4 can be housed within the PSP shell.
    - **Plug-and-Play**:
        - The 40-pin models require no soldering and can be directly plugged in if they have a header.
        - The CM4 boards require no soldering.
    - **USB Data Connection for Pi Zero:** Achievable through the soldering of 2 wires.

## 3. Video and Display:
- **LCD Compatibility:** Designed for a high resolution [800x480 LCD](https://www.ebay.com/itm/4-3-inch-800x480-IPS-TFT-LCD-Module-All-Viewing-Optional-TouchScreen-Display-/292806918081?mkcid=1&mkrid=711-53200-19255-0&siteid=0&campid=5338322564&customid=&toolid=10001&mkevt=1), but works with many 40-pin LCDs.
- **Color Depth**:
    - 21-bit DPI 777 when using 40-pin Raspberry Pi boards.
    - 24-bit DPI 888 when using the Raspberry Pi CM4.
- **Brightness Control:** 8 levels of adjustment available via display button, with real-time feedback provided on the OSD.

## 4. Power Management:
- **Power On/Off:** Controlled via a momentary push switch, featuring graceful startup and shutdown procedures.
- **Forced Power Off:** Can be achieved by holding the power button for 3-5 seconds.
- **Charging and Battery Management**:
    - Supports 3.7v batteries with a JST PH 2.0mm connector.
    - Charge using the miniUSB or barrel jack (at up to 1.35 amps).
    - Efficient charging using a switching regulator with minimal heat generation.
    - Real-time battery status and charge levels displayed on the OSD.
    - Auto shutdown when the battery is depleted.
    - Auto forced power-off when the battery voltage drops below 3.08v.
- **Power Supply and USB**:
    - The board works using only external power when no battery is installed.
    - The miniUSB provides power to external devices only when the PSPi is powered on, with one exception. If the barrel jack is plugged in, the power from the barrel jack will pass through directly to the miniUSB port. This is useful when a USB device needs extra power.
    - Internal boost IC provides a stable 5.0v supply to the Raspberry Pi.

## 5. Audio:
- **Audio Quality:** PWM audio signal processed through a low-noise buffer and filters for enhanced quality.
- **Headphone Integration:** Automatic speaker muting upon headphone connection.
- **Volume and Mute Controls:** Adjustable via buttons, with immediate feedback displayed on the OSD.

## 6. Input/Output and Controls:
- **Microcontroller:** Atmega8a manages buttons, joysticks, battery, and LCD brightness, limiting the number of calculations done on the Pi.
- **Solder Pads:**
    - **Additional Inputs:** The board includes pads for 2 additional analog axes (a single joystick) and two additional buttons.
    - **I2C:** The board includes pads for SDA and SCL, enabling the use of additional I2C devices.
    - **Touch:** Includes the connections necessary to use a touch panel. More details will come at a later time.
- **Left Switch:** Used to cycle between high power and power efficiency modes (programmable).
- **Power Switch:**
    - Sliding upward momentarily powers the PSPi on.
    - When on, another momentary press will shut the OS down and power the PSPi off.
    - Holding it upward for 3-5 seconds will force the PSPi to power off.
    - Placing it into the Hold position will activate a locked sleep mode, disabling audio, input, and the LCD. More details below.
- **Display Button:**
    - Pressing the Display button will cycle the backlight through 8 brightness levels.
    - Holding the Display button for 2 seconds will set the current brightness level to the default brightness at bootup.
- **LED Indicators:**
    - SD and eMMC activity indicator is above the left switch.
    - WiFi connection status indicator is below the left switch (programmable).
    - Power status is indicated by the right LED. Normal status is a green LED, which turns orange for charging or low battery.
- **RTC (Real-Time Clock):**
  - The PSPi 6 board includes an RTC chip to keep track of the time and date, even when the system is powered off.

## 7. Efficiency and Power Saving
- **Power Save Mode:**
  - The left switch puts the Raspberry Pi into a lower power mode using the governor.
  - It changes the color of the battery outline when the left switch is down, to show the powersave status.
  - This will also disable WiFi, depending on whether it's configured to do that.
- **Sleep Mode:**
  - The Raspberry Pi doesn't have a sleep mode, but this is the next best thing.
  - Enter by sliding the power switch to the hold position (down), exit by sliding the switch back to the up position.
  - The ATmega microcontroller will turn off the screen and cut power to the audio circuits, ensuring a significant reduction in power consumption.
  - The controls are locked to prevent any accidental inputs during sleep mode.
  - The Raspberry Pi detects that the device is entering sleep mode, pauses the drivers, and switches the CPU governor to powersave mode. If RetroArch is running, it will also be paused to save resources.
  - This will also disable WiFi, if it's configured to do that.
  - This feature is particularly useful for preserving battery life during extended gaming sessions, allowing you to take breaks without needing to shut down the device completely. Pick up right where you left off, while minimizing power consumption during breaks.
- **Mute:** Kills power to the audio circuits, reducing power usage.
- **Component Selection**:
    - The board uses as many of the Raspberry Pi's integrated features as possible, helping it to consume minimal power.
    - It gives 4 - 8 hours of playtime when using a Raspberry Pi Zero, and up to 18 hours when the system is idle.
    - You'll get 2 - 4 hours of playtime when using a Raspberry Pi CM4, and more when idle.
- **Code Efficiency:** All functionalities are programmed in C for optimal performance.

## Items Needed to Complete the Project
- **Genuine PSP 1000:**
  - The best option is to use a complete PSP 1000 series. The PSP mainboard, headphone board, and disc drive are not needed, but many other internal parts are, such as:
    - The shell. The aftermarket ones are not good quality, so the best option is to use a genuine shell.
    - WiFi antenna. The CM4 uses the same antenna connector, and the PSP's stock antenna works well with it.
    - LCD bracket. The metal bracket holds the LCD and retains the back cover.
    - Control panel on LCD bracket. This has many of the buttons, such as Display, Mute, and Volume.
    - Power board. The board in the right of the shell, that has the power switch and LEDs.
    - D-pad. There is a plastic brace and film for the d-pad controls.
    - Rubber membranes for buttons.
    - Shoulder buttons and membrane.
    - Internal speakers for audio.
    - Joystick and rubber interface.
- **PSPi 6 Required Parts:**
  - If using only a 40-pin Raspberry Pi, such as a Pi Zero 2W, then you need the PSPi 6 board itself. The Raspberry Pi boards plug directly into it.
  - If you intend to use this on the go, you need a battery with a JST PH 2.0mm connector
  - Aftermarket LCD.
- **PSPi 6 Optional Parts:**
  - PSPi 6 CM4 Carrier. This is an adapter board that allows you to use a Raspberry Pi CM4 on the PSPi.
  - PSPi 6 Headphone Board. This allows you to use headphones with the PSPi.

## Resources

- [**Code for Raspberry Pi**](https://github.com/othermod/PSPi-Version-6/tree/main/drivers): Essential code for integrating the Raspberry Pi and Atmega with the PSPi system.
- [**Firmware for Atmega**](https://github.com/othermod/PSPi-Version-6/tree/main/atmega): Firmware for the Atmega8a microcontroller within the PSPi.
- [**PCB and Schematics**](https://github.com/othermod/PSPi-Version-6/tree/main/boards): Hardware design files and schematics for the PSPi. Also available on [EasyEDA](https://oshwlab.com/adamseamster/pspi-zero-version-5_copy_copy).

## Ordering
The boards can be ordered from the manufacturer at any point, but please be aware that the project is still in the testing phase and changes may be made. Some assembly will be required if you order from them, and they are quite expensive in low quantities. I'll also sell these boards on my website when they are ready.

## Status
The project is still a work in progress, and although the basic functions are now up and running, there are still a few tweaks and improvements to be made.

## Community and Contributions
This project is a one-man-show, but any help or input is welcome and appreciated. Whether you are a designer, coder, tester, or just someone with ideas to share, your contributions are highly valued. You can also contribute by spreading the word and sharing the project with others, or by supporting monetarily.

## Stay Connected

- [**Discord**](https://discord.gg/V96c3JC): Join for the latest discussions and updates.
- [**YouTube**](https://youtube.com/othermod): Subscribe for video updates and demonstrations.

## License

The hardware is licensed under Creative Commons (CC BY-SA).

##### You are free to:

- **Share:** Copy and redistribute the material in any medium or format.
- **Adapt:** Remix, transform, and build upon the material for any purpose, even commercially.

##### Under the following terms:

- **Attribution:** You must give appropriate credit and indicate if changes were made.
- **ShareAlike:** If you remix, transform, or build upon the material, you must distribute your contributions under the same license as the original.

## Contact

Feel free to [reach out](https://linktr.ee/othermod) if you have any thoughts, suggestions, or ideas.

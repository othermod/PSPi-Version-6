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

## 2. Pi Compatibility:
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
- **Battery Management**:
    - Supports various 3.7v batteries with JST PH 2.0mm connector.
    - Real-time battery status and charge levels displayed on the OSD.
    - Auto power-off feature for battery levels below 3.08v.
- **Charging and Power Supply**:
    - USB or barrel jack charging at 1.35 amps, capable of supporting external devices.
    - Efficient charging using a switching regulator with minimal heat generation.
    - Ensures a stable 5.0v supply to the Raspberry Pi.
    - Includes a miniUSB port for powering external USB devices when the system is on.
- **Efficiency**:
    - Designed to consume minimal power.
    - 4 - 8 hours of playtime when using a Raspberry Pi Zero. Up to 18 hours when the system is idle.
    - 2 - 4 hours of playtime when using a Raspberry Pi CM4.

## 5. Audio Features:
- **Audio Quality:** PWM audio signal processed through a low-noise buffer and filters for enhanced quality.
- **Headphone Integration:** Automatic speaker muting upon headphone connection.
- **Volume and Mute Controls:** Adjustable via buttons, with immediate feedback displayed on the OSD.

## 6. Input/Output and Controls:
- **Microcontroller:** Atmega8a manages buttons, joysticks, battery, and LCD brightness, limiting the number of calculations done on the Pi.
- **Energy Efficiency:** Left switch is programmable, and used to cycle between high power and power efficiency modes.
- **Sleep Mode:** Hold switch activates a locked sleep mode, disabling audio, input, and the LCD.
- **LED Indicators**:
    - SD and eMMC activity indicator is above the left switch.
    - WiFi connection status indicator is below the left switch (programmable).
    - Power status is indicated by the right LED. Normal status is a green LED, which turns orange for charging or low battery.
- **Code Efficiency:** All functionalities are programmed in C for optimal performance.
- **RTC (Real-Time Clock):**
  - The PSPi 6 board includes an RTC chip to keep track of the time and date, even when the system is powered off.

## Resources

- [**Code for Raspberry Pi**](https://github.com/othermod/PSPi-Version-6/tree/main/drivers): Essential code for integrating the Raspberry Pi with the PSPi system.
- [**Firmware for Atmega**](https://github.com/othermod/PSPi-Version-6/tree/main/atmega): Firmware to empower the Atmega8a microcontroller within the PSPi.
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

## Contact

Feel free to [reach out](https://linktr.ee/othermod) if you have any thoughts, suggestions, or ideas.

# PSPi 6 Project - Getting Started Guide

This guide will help you determine what needs to be purchased, and get you started with assembling and setting up the PSPi 6.

## Operating System Images

To get started quickly, you can download the pre-configured OS images provided:

- Download here: [OS Images for PSPi 6](https://drive.proton.me/urls/04X9SX1KG8#zOBARZruUlqs)
- Only the RetroPie images are currently available while I'm developing the software. More will come soon.

The following table outlines the images I have available for the various operating systems and Raspberry Pi models:

| Operating System | Zero (32-bit) | Zero 2W (32-bit) | Zero 2W (64-bit) | CM4 (32-bit) | CM4 (64-bit) |
|------------------|:-------------:|:----------------:|:----------------:|:------------:|:------------:|
| RetroPie         | ☑️            |                  |                  | ☑️           |              |
| Lakka            |               |                  |                  |              |              |
| Ubuntu           |               |                  |                  |              |              |
| Raspberry Pi OS  |               |                  |                  |              |              |
| Batocera         |               |                  |                  |              |              |
| Kali             |               |                  |                  |              |              |

_Note: OS compatibility may vary across different Raspberry Pi models._

## Compatibility

#### Supported PSP Cases

- PSP 1000 Shell: The PSPi is designed only for the original PSP 1000 series. This should be compatible with any model in the original 1000 series, such as PSP-1000, 1001, or 1002.

#### Supported Raspberry Pi Models
  - **40-pin Versions**: Compatible with all models featuring a 40-pin GPIO header.
  - **Compute Module 4**: Can be used with the optional CM4 Carrier board.
  - **Size Compatibility**: The PSP shell houses the Raspberry Pi Zero, Zero 2W, and CM4 with no case modification needed. It will not house the larger Raspberry Pi 3, 4, and 5 boards.
  - **Installation Ease**:
    - 40-pin models: Direct plug-and-play with a pre-soldered header. USB requires soldering two wires.
    - CM4 boards: Solder-free setup using the CM4 Carrier.

## Required Items

#### Required from a Genuine PSP 1000 Series:
- **Shell**: Look for a genuine shell. Aftermarket ones tend to be lower quality.
- **Internal Components**: The easiest method is just to buy a complete PSP 1000, but if you want to piece one together, here is the list of parts needed:
  - **WiFi Antenna**: The CM4 uses the same antenna connector, making the PSP's stock antenna compatible.
  - **LCD Bracket**: A metal bracket that holds the LCD and retains the back cover.
  - **Control Panel**: Located on the LCD bracket, includes buttons like Display, Mute, and Volume.
  - **Power Board**: Houses the power switch and LEDs, located on the right side of the shell.
  - **D-pad**: Includes a plastic brace and film for the controls.
  - **Rubber Membranes**: For buttons.
  - **Shoulder Buttons and Membrane**.
  - **Internal Speakers**: For audio.
  - **Joystick and Rubber Interface**.

#### Required Aftermarket Parts:
- **PSPi 6 Board:** The main board of the project, compatible with all 40-pin Raspberry Pi models. Raspberry Pi boards can plug directly into it.
- **Battery:** If you plan to use your PSPi 6 on the go, you'll need a battery with a JST PH 2.0mm connector.
- **LCD:** The original PSP-1000 LCD will not work with the PSPi 6.

#### Optional Parts:
- **CM4 Carrier**: An adapter board that allows you to use a Raspberry Pi CM4 in the PSPi.
- **Headphone Board**: Allows you to use headphones with your PSPi 6.

## RAM and Storage Recommendations

#### RAM Recommendations

- **For Emulation**: Any RAM amount is probably fine.
- **For Full Operating Systems**: At least 4GB of RAM on the CM4 is recommended, and the more the better.

#### Storage Recommendations

##### Raspberry Pi Compute Module 4 (CM4)

- **eMMC Storage**: Slightly faster at bootup, but the storage size is fixed. You cannot use an SD card in the eMMC version.
- **Lite Version**: Flexible, uses SD cards for storage. Best if you expect to store large amounts of data.

##### SD Card

- **Maximum Size**: Up to 1TB.
- **Recommended Speed**: UHS-I U3 or higher.

## OS Performance and Battery Life Considerations

#### Raspberry Pi Zero

- Runs 16-bit era games well; struggles with PlayStation 1 and N64.
- Good when using a lightweight OS and performing basic tasks.
- Will give the longest time between battery charges, between 4 and 18 hours depending on the task.

#### Raspberry Pi Zero 2W

- Runs 16-bit era games smoothly; some PlayStation 1 titles are playable.
- Better multitasking and improved performance in OS.
- Still very efficient, and will give a long use time between 3 and 12 hours.

#### Raspberry Pi Compute Module 4 (CM4)

- Broad emulation compatibility, suitable for modern console games.
- Supports a variety of 32-bit and 64-bit operating systems with robust performance.
- Battery life will not be as good when using the CM4, and you can expect 2-4 hours, maybe up to 6.

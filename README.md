# PSPi 6
Welcome to the PSPi 6 GitHub repository! This project is a combination of hardware and software development aiming to retrofit a PSP with almost every type of Raspberry Pi.

![PSPi](https://othermod.com/wp-content/uploads/IMG_8727.jpg)

### Hardware Features

|Feature|Description|
|-|-|
| **Improved Display** | Uses an [aftermarket 800x480 LCD](https://www.ebay.com/itm/4-3-inch-800x480-IPS-TFT-LCD-Module-All-Viewing-Optional-TouchScreen-Display-/292806918081?mkcid=1&mkrid=711-53200-19255-0&siteid=0&campid=5338322564&customid=&toolid=10001&mkevt=1) instead of the original 480x272 one. <br>21-bit color with Pi Zero, and 24-bit with Compute Module.|
| **High Efficiency** | Designed to consume minimal power. <br>Dimmable backlight allows up to 8 hours of playtime with Raspberry Pi Zero.|
| **Battery Charging** | Efficient charger with minimal heat generation. <br>Charge via barrel jack or miniUSB connector.|
| **Audio** | Isolated buffer-filter-amplifier circuit for improved audio and minimal noise.|
| **Smart Power Circuits** | Handles the different Raspberry Pi versions. Includes quick power on/off, graceful shutdown, and forced power-off.|
| **Microcontroller** | Uses atmega8a for input and battery sensing, limiting calculations done on the Pi.|
| **Compatibility** | Fits PSP 1000 series only.<br>Works with 40-pin Raspberry Pi boards. Compatible with Raspberry Pi CM4 when using the optional Carrier board.<br>Only the Zero/2W and CM4 fit into the shell.|

## Software Features
| Feature                        | Description                                                                                                     |
|-|-|
| **Operating Systems Supported**| RetroPie: Minimal interface, decent playtime.<br> Lakka: Visually appealing but uses more processing power.<br> Ubuntu: Full Linux OS. |
| **Software Volume Adjustment** | Supports adjustment for headphone/speaker volume.                                                      |
| **OSD** | Displays remaining battery capacity.                                                                           |
| **Development Status**         | Software is still in development and will be improved as the board gets closer to release.                      |

### Resources Included Here
| Resource | Description | Link |
|-|-|-|
| **Code for Raspberry Pi** | Necessary code for the Raspberry Pi that forms the brains of the PSPi. | [GitHub](https://github.com/othermod/PSPi-Version-6/tree/main/drivers) |
| **Firmware for atmega**   | Firmware for the atmega microcontroller used in the PSPi. | [GitHub](https://github.com/othermod/PSPi-Version-6/tree/main/atmega) |
| **PCB and Schematics**    | PCB and schematics for the PSPi. | [GitHub](https://github.com/othermod/PSPi-Version-6/tree/main/boards) |

## Status
The project is still a work in progress, and although the basic functions are now up and running, there are still a few tweaks and improvements to be made.

## Contribute
This project is a one-man-show but any help or input is welcome and appreciated. Whether you have experience with design, coding, testing, or just have some ideas for improvement, your contribution is valuable. You can also contribute by spreading the word and sharing the project with others. Financial contributions are also greatly appreciated to help cover the cost of prototypes and speed up testing and improvements.

## Follow the Project
You can follow along with the project on [EasyEDA](https://oshwlab.com/adamseamster/pspi-zero-version-5_copy_copy) or [Discord](https://discord.gg/V96c3JC) for constant updates, or on [YouTube](https://youtube.com/othermod) for occasional updates.

## Ordering
The boards can be ordered from the manufacturer at any point, but please be aware that the project is still in the testing phase and changes may be made. Some assembly will be required if you order from them, and they are quite expensive in low quantities. I'll also eventually sell these board on my website.

## Contact
If you have any thoughts, suggestions, or ideas, please feel free to reach out.

*Thank you for your interest in the PSPi project, and stay tuned for more updates.*

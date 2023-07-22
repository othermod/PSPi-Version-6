# PSPi 6
Welcome to the PSPi 6 GitHub repository! This project is a combination of hardware and software development aiming to retrofit a PSP with almost every type of Raspberry Pi.

![PSPi](https://othermod.com/wp-content/uploads/IMG_8727.jpg)

## Hardware Features
- **Improved Display:** The new board uses 7 bits for each color when using the Pi Zero and 8 bits for each color when using the Compute Module, improving color depth for images and videos.
- **LCD Power Consumption:** Adjustments have been made to the LCD components to reduce power consumption when the screen is off.
- **Battery Charging:** A new battery charger has been added, charging the battery faster with almost no heat generation.
- **Power Circuits Overhaul:** All of the power circuits underwent a major overhaul, better handling the high current of the Compute Module and gracefully managing power on and power off.
- **Microcontroller:** The board uses an atmega8a, a cost-effective microcontroller functionally identical to the atmega328p used in Arduino boards for this specific application.
- **Board Shape:** Changes to the board shape have made it closer to the shape of the original PSP board, simplifying the speaker connections.
- **Compatibility:** This new board features a 40-pin Raspberry Pi female connector and is compatible with all standard 40-pin Raspberry Pi boards.

## Software Features
- **Supports RetroPie, Lakka, and many more operating systems:** RetroPie provides a great, minimal interface that gives decent play time because it isn’t doing too much in the background when its idle. Lakka looks great on the PSP but uses a ton of processing power and drains the battery faster. I plan to get Ubuntu working next.
- **Software Volume Adjustment:** The board now supports software volume adjustment, and both the headphone and speaker volume adjust.
- **Battery Calculation and Indication:** The software displays the battery capacity remaining at all times.
- The software is still somewhat basic, and being used to test some of the hardware functions. It will be gradually improved as the board gets closer to release.

## Resources Included Here
- **Code for Raspberry Pi:** This repository includes the necessary code for the Raspberry Pi that forms the brains of the PSPi.
- **Firmware for atmega:** The firmware for the atmega microcontroller used in the PSPi is also part of this repository.
- **PCB and Schematics:** You can find the PCB and schematics on EasyEDA at [this link](https://oshwlab.com/adamseamster/pspi-zero-version-5_copy_copy).

## Status
The project is still a work in progress, and although the basic functions are now up and running, there are still a few tweaks and improvements to be made.

## Contribute
This project is a one-man-show but any help or input is welcome and appreciated. Whether you have experience with design, coding, testing, or just have some ideas for improvement, your contribution is valuable. You can also contribute by spreading the word and sharing the project with others. Financial contributions are also greatly appreciated to help cover the cost of prototypes and speed up testing and improvements.

## Follow the Project
You can follow along with the project on [EasyEDA](https://oshwlab.com/adamseamster/pspi-zero-version-5_copy_copy) or [Discord](https://discord.gg/V96c3JC) for constant updates, or on [YouTube](youtube.com/othermod) for occasional updates.

## Ordering
The boards can be ordered from the manufacturer at any point, but please be aware that the project is still in the testing phase and changes may be made. Some assembly will be required if you order from them, and they are quite expensive in low quantities. I'll also eventually sell these board on my website.

## Links
- YouTube Playlist: [PSPi Project Playlist](#)
- EasyEDA Project: [PSPi Version 6 on EasyEDA](https://oshwlab.com/adamseamster/pspi-zero-version-5_copy_copy)
- Discord: [PSPi Discord Server](#)

## Contact
If you have any thoughts, suggestions, or ideas, please feel free to reach out. Contributions, either by helping with the design, coding, testing, or just recommending improvements, are always welcome.

*Thank you for your interest in the PSPi project, and stay tuned for more updates.*

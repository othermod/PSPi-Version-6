# PSPi 6: Raspberry Pi in a PSP

![PSPi](https://othermod.com/wp-content/uploads/IMG_8727.jpg)

This is my passion project that transforms the classic PSP 1000 into a modern handheld using a Raspberry Pi. This page documents the combination of hardware and software development.

## 🎮 What is PSPi 6?

PSPi 6 is a custom circuit board that replaces the mainboard of a PSP 1000, allowing you to use a Raspberry Pi as its brain. This means you can:

- Play retro games and emulators
- Run full Linux distributions and use it as a portable computer
- Use most software that works on a Raspberry Pi

## ✨ Key Features

- **Display**: High quality [800x480 LCD](https://othermod.com/product/4-3-800x480-lcd/) with adjustable brightness
- **Power Management**: Efficient charging, real-time battery monitoring, and power-saving modes
- **Audio**: Play audio through the PSP speakers or headphones
  - Control volume and mute using the PSP buttons
  - *Note: The Pi Zero and CM4 Carrier give mono audio. The Universal Carrier is planned to output stereo*
- **Controls**: All original PSP buttons and joystick are used
  - The board allows for two extra buttons and an extra joystick
- **Indicators**: LED indicators and on-screen display for system status
- **Open Design**: Customizable open-source hardware under Creative Commons license

For a comprehensive list of features and technical details, please visit the [Features Wiki Page](https://github.com/othermod/PSPi-Version-6/wiki/1.-Features).

## 🧩 Compatibility

- **PSP Model**: Works exclusively with PSP 1000 series. Visit the [PSP Compatibility Wiki Page](https://github.com/othermod/PSPi-Version-6/wiki/2.-PSP-Compatibility) page for more details
- **Raspberry Pi**:
  - Fits Raspberry Pi Zero, Zero 2W, and CM4 (with CM4 Carrier board)
  - Electrically compatible with all 40-pin Raspberry Pis, but only the Zero/Zero 2 fit into the shell
  - The [Raspberry Pi Compatibility Wiki Page](https://github.com/othermod/PSPi-Version-6/wiki/3.-Raspberry-Pi-Compatibility) will help you decide which Raspberry Pi model you want to use.
- **Operating Systems**: RetroPie, Lakka, Ubuntu, Raspberry Pi OS, Batocera, Kali, and more!

## 🚀 Getting Started

- **Gather Components**: Check the [Components Required Wiki Page](https://github.com/othermod/PSPi-Version-6/wiki/4.-Components-Required) for a full list.
- **Assembly**: Follow the guides on the [Board Installation Wiki](https://github.com/othermod/PSPi-Version-6/wiki/5.-Board-Installation). Video tutorials are available, and a full guide is in the works.
- **Software Setup**: Use the [Operating Systems Wiki Page](https://github.com/othermod/PSPi-Version-6/wiki/6.-Operating-Systems) to install your chosen OS.

Having issues? Visit the [Troubleshooting Wiki Page](https://github.com/othermod/PSPi-Version-6/wiki/Troubleshooting).

## 📁 Project Resources

- **[Raspberry Pi Code](https://github.com/othermod/PSPi-Version-6/tree/main/drivers)**: Drivers and software for the Raspberry Pi.
- **[Atmega Firmware](https://github.com/othermod/PSPi-Version-6/tree/main/atmega)**: Code for the Atmega8a microcontroller that manages power and inputs.
- **[PCB and Schematics](https://github.com/othermod/PSPi-Version-6/tree/main/boards)**: Hardware design files for those who want to manufacture boards modify the design.

## 🛒 How to Get a PSPi 6

1. **Buy a Ready-Made Board**: Available now at [othermod.com](https://othermod.com/product/pspi-6-board/). Perfect for those who want more of a plug-and-play experience.

2. **Make Your Own**: You can use the provided PCB files to manufacture your own board:
   - Download the design files from the [boards folder](https://github.com/othermod/PSPi-Version-6/tree/main/boards).
   - Send the files to a PCB manufacturer of your choice. I use [JLCPCB](https://jlcpcb.com/?from=othermod) for every board I sell.
   - Source the components and assemble the board yourself.

   Note: This option requires advanced skills in electronics and soldering.

## 🚧 Project Status

PSPi 6 board development is complete and boards are shipping. I do sometimes make minor changes to the board, but nothing that affects the important features. I'm continually improving documentation and working on guides to help users get the most out of their PSPi 6.

## 🤝 Community and Contributions

While PSPi 6 is primarily my personal project, I welcome contributions from the community. Whether you're a coder, designer, or just have great ideas, your input can help make PSPi 6 even better. Here's how you can contribute:

- Report bugs or suggest features
- Join the Discord and share your mods or help others with troubleshooting.
- Help improve documentation and guides
- Spread the word about the PSPi 6!

## 📢 Stay Connected

- [**Discord**](https://discord.gg/V96c3JC): Join the community for discussions, support, and sharing your builds.
- [**YouTube**](https://youtube.com/othermod): Subscribe for video tutorials and project updates.
- [**Contact**](https://linktr.ee/othermod): Reach me on various platforms.

## 📜 License

The PSPi 6 hardware design is open-source under the Creative Commons (CC BY-SA) license. You're free to share and adapt the material, as long as you give appropriate credit.

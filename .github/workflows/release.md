## What's Changed

- RetroPie ships with the controller fully preconfigured, so the input wizard never runs on first boot
- The battery icon now appears reliably in Kali
- Changed the actions of some buttons when in mouse mode
- Added Ubuntu

## Compute Module 5 Reminder

- Power draw is very high. The small battery can be overwhelmed, so the system may cut off if power demand spikes. The hardware gets very hot.
- Audio through headphones and speakers does not work on the CM5 with the CM4 carrier. The pins changed, so no software change will fix this. Use Bluetooth or USB audio.

## Using the Mouse (Desktop Images)

Raspberry Pi OS, Kali, and Ubuntu boot with the controller acting as a mouse. The left stick moves the on-screen cursor, the d-pad navigates menus, and the buttons handle clicks and confirmations.

| Control | Action |
|---|---|
| **Left stick** | Move the mouse cursor |
| **D-pad** | Navigate menus (arrow keys) |
| **Cross** | Select / confirm (Enter) |
| **Circle** | Back / cancel (Esc) |
| **R1** | Mouse left click |
| **L1** | Mouse right click |
| **Home** | Open the app menu / overview (Super) |

## Images

### Batocera
![Batocera EmulationStation menu](https://raw.githubusercontent.com/wiki/othermod/PSPi-Version-6/releases/batocera.png)

**Boards:** Zero 1, Zero 2 W, CM4, CM5

A turn-key retro-gaming OS with its own EmulationStation-based UI and a built-in settings menu. Emulators and the PSPi controls are preconfigured.

Username: `root`
Password: `linux`

---

### Kali
![Kali desktop](https://raw.githubusercontent.com/wiki/othermod/PSPi-Version-6/releases/kali.png)

**Boards:** Zero 2 W, CM4, CM5

A security and penetration-testing distro, not gaming-focused. It boots into mouse mode like Raspberry Pi OS. The on-screen keyboard can be enabled by clicking the button in the taskbar that looks like a person, making it possible to log in without a physical keyboard.

Username: `kali`
Password: `kali`

---

### Lakka
![Lakka booting to the RetroArch menu](https://raw.githubusercontent.com/wiki/othermod/PSPi-Version-6/releases/lakka.png)

**Boards:** Zero 1, Zero 2 W, CM4, CM5

The minimal RetroArch-only option. It boots straight into the RetroArch menu with the PSPi controls and menu layout preconfigured.

Username: `root`
Password: `root`

---

### Raspberry Pi OS
![Raspberry Pi OS desktop](https://raw.githubusercontent.com/wiki/othermod/PSPi-Version-6/releases/pios.png)

**Boards:** 
64-bit image: Zero 2 W, CM4, CM5 
32-bit image: all boards

The general-purpose desktop. It's a lean OS that performs well. The on-screen keyboard (Squeekboard) starts automatically at boot.

**First boot:** The first boot takes a couple of minutes. The filesystem expands to fill your SD card, and the screen may stay blank or black while it works. This is normal, so be patient. Don't power off during the expansion.

Username: `pi`
Password: `raspberry`

---

### Recalbox
![Recalbox EmulationStation menu](https://raw.githubusercontent.com/wiki/othermod/PSPi-Version-6/releases/recalbox.png)

**Boards:** Zero 1, Zero 2 W, CM4, CM5

An EmulationStation-based retro OS and the main alternative to Batocera if you prefer a different ecosystem. Note: Recalbox doesn't show a battery icon yet, so you won't see charge level on screen.

Username: `root`
Password: `recalboxroot`

---

### RetroPie
![RetroPie EmulationStation menu](https://raw.githubusercontent.com/wiki/othermod/PSPi-Version-6/releases/retropie.png)

**Boards:** Zero 1, Zero 2 W, CM4, CM5

The classic Raspberry Pi retro-gaming OS. It boots straight into EmulationStation, is very efficient, and uses very little battery when games aren't being played.

**First boot:** The first boot takes a couple of minutes. The filesystem expands to fill your SD card, and the screen may stay blank or black while it works. This is normal, so be patient. Don't power off during the expansion.

Username: `pi`
Password: `othermod`

---

### TS Dash
![TS Dash dashboard](https://raw.githubusercontent.com/wiki/othermod/PSPi-Version-6/releases/tsdash.png)

**Boards:** Zero 1, Zero 2 W, CM4

EFI Analytics TS Dash Pro turns the PSPi into an automotive digital dash for MegaSquirt EFI systems. The kiosk app boots straight to the dash on the PSPi LCD, and the joystick acts as a mouse so you can navigate dashes and on-screen buttons without a touchscreen.

**First boot:** The first boot takes a couple of minutes. The filesystem expands to fill your SD card, and the screen may stay blank or black while it works. This is normal, so be patient. Don't power off during the expansion.

Username: `pi`
Password: `raspberry`

---

### Ubuntu
![Ubuntu desktop](https://raw.githubusercontent.com/wiki/othermod/PSPi-Version-6/releases/ubuntu.png)

**Boards:** CM4, CM5

Ubuntu 26.04 LTS with the full GNOME desktop.

Username: `ubuntu`
Password: `othermod`

---

**Full Changelog**: https://github.com/othermod/PSPi-Version-6/compare/v2.4.2...v2.4.3

## What's Changed

- RetroPie now has Steam Link included by default
- Batocera now has Moonlight included by default
- RetroPie ships with the controller fully preconfigured, so the input wizard never runs on first boot
- Recalbox is now available for the Zero 1
- The battery icon now appears reliably in Ubuntu and Kali
- The WiFi signal stays on screen even when WiFi is slow to connect at boot

## Compute Module 5 Reminder

- Power draw is very high. The system may cut off if power demand spikes, and the hardware gets very hot.
- Audio through headphones and speakers does not work on the CM5 with the CM4 carrier. The pins changed, so no software change will fix this. Use Bluetooth or USB audio.

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

Username: `pi`
Password: `othermod`

---

### Ubuntu
![Ubuntu desktop](https://raw.githubusercontent.com/wiki/othermod/PSPi-Version-6/releases/ubuntu.png)

**Boards:** CM4, CM5

Ubuntu 26.04 LTS with the full GNOME desktop.

Username: `ubuntu`
Password: `othermod`

---

**Full Changelog**: https://github.com/othermod/PSPi-Version-6/compare/v2.4.2...v2.4.3

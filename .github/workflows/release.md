## What's Changed

- RetroPie now has Steam Link included by default
- Batocera now has Moonlight included by default
- The WiFi signal monitor now retries at boot and restarts automatically if it stops, so the signal stays on even when WiFi comes up slowly
- The gamepad now restarts itself if it crashes, and reads every setting from pspi.conf
- RetroPie ships with the controller fully preconfigured, so the input wizard never runs on first boot
- Recalbox is now available for the Zero 1
- Ubuntu and Kali load the battery module at boot, so the battery icon appears reliably
- All image downloads are now checksum-verified, and every finished image is verified before release

## Compute Module 5 Reminder

- Power draw is very high. The system may cut off if power demand spikes, and the hardware gets very hot.
- Audio through headphones and speakers does not work on the CM5 with the CM4 carrier. The pins changed, so no software change will fix this. Use Bluetooth or USB audio.

## Images

### Batocera
![Batocera EmulationStation menu](https://raw.githubusercontent.com/wiki/othermod/PSPi-Version-6/releases/batocera.png)

**Boards:** Zero 1, Zero 2 W, CM4, CM5

A turn-key retro-gaming OS with its own EmulationStation-based UI and a built-in settings menu. Audio is heavily reworked for the PSPi: PipeWire is disabled in favor of ALSA, RetroArch uses the ALSA thread driver, and a compatibility shim routes the OS volume control to the BCM2835 PWM audio hardware (PipeWire otherwise spikes CPU usage on this hardware).

Username: `root`
Password: `linux`

---

### Kali
![Kali desktop](https://raw.githubusercontent.com/wiki/othermod/PSPi-Version-6/releases/kali.png)

**Boards:** Zero 2 W, CM4, CM5

A security and penetration-testing distro, not gaming-focused. It boots into mouse mode like Raspberry Pi OS.

Username: `kali`
Password: `kali`

---

### Lakka
![Lakka booting to the RetroArch menu](https://raw.githubusercontent.com/wiki/othermod/PSPi-Version-6/releases/lakka.png)

**Boards:** Zero 1, Zero 2 W, CM4, CM5

The pure RetroArch option: the entire OS is RetroArch, with no separate front-end or desktop. It boots straight into the RetroArch menu and uses a read-only (squashfs) root filesystem, so it stays small and consistent between boots. This is the Libretro reference build, with PSPi button mapping and menu layout already applied.

Username: `root`
Password: `root`

---

### Raspberry Pi OS
![Raspberry Pi OS desktop](https://raw.githubusercontent.com/wiki/othermod/PSPi-Version-6/releases/pios.png)

**Boards:** 
64-bit image: Zero 2 W, CM4, CM5 
32-bit image: all boards

The general-purpose desktop, not a gaming image. It boots into mouse mode by default because the desktop is more usable with a pointer than a gamepad (switch `input_type` in `pspi.conf` on the boot partition for gamepad mode). The on-screen keyboard (Squeekboard) starts automatically at boot. This is the "it's just a Linux computer" option.

Username: `pi`
Password: `raspberry`

---

### Recalbox
![Recalbox EmulationStation menu](https://raw.githubusercontent.com/wiki/othermod/PSPi-Version-6/releases/recalbox.png)

**Boards:** Zero 2 W, CM4, CM5

Another EmulationStation-based retro OS, similar in spirit to Batocera but a different ecosystem. The stock hardware-detection and add-on scripts are stripped out to prevent the GPIO conflicts that caused LCD color issues at startup. Note that Recalbox has no battery icon (haven't investigated why, just yet), so charge level is not shown on screen.

Username: `root`
Password: `recalboxroot`

---

### RetroPie
![RetroPie EmulationStation menu](https://raw.githubusercontent.com/wiki/othermod/PSPi-Version-6/releases/retropie.png)

**Boards:** Zero 1, Zero 2 W, CM4, CM5

RetroPie installed on top of Raspberry Pi OS Lite. The `pi` user auto-logs-in on boot and EmulationStation starts straight away. Audio is set to the analog/PCM output, the A/B and OK/cancel buttons are swapped for the PSPi layout, and ROMs can be added via a USB drive or the built-in Samba (network) share.

Username: `pi`
Password: `othermod`

---

### Ubuntu
![Ubuntu desktop](https://raw.githubusercontent.com/wiki/othermod/PSPi-Version-6/releases/ubuntu.png)

**Boards:** CM4, CM5

Ubuntu 26.04 LTS with the full GNOME desktop — the “it's a real Linux computer” option. Ships with the PSPi battery kernel module so the battery icon works, boots into mouse mode, and has the built-in GNOME on-screen keyboard enabled.

Username / Password: created during the first-boot setup wizard (there is no default user).

---

**Full Changelog**: https://github.com/othermod/PSPi-Version-6/compare/v2.4.2...v2.4.3

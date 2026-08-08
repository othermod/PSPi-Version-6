## What's Changed

- **New images:** Kali (Zero 2 W, CM4, CM5) and RetroPie (Zero 1, Zero 2 W, CM4, CM5)
  are now available.

## Downloading the Images

GitHub limits individual release assets to 2 GiB, so larger images are split into
multi-volume `.7z` archives (named `IMAGE.img.xz.7z.001`, `.002`, ...). Download
all parts for an image into the same folder, then open the `.001` file with 7-Zip
(Windows/Linux) or Keka (Mac) to reassemble it automatically.

`pspi-binaries-v<version>.tar.gz` contains the pre-built driver binaries (gamepad,
battery monitor, RTC, WiFi monitor, firmware updater, and device-tree overlays)
for users who want to patch their own image.

## Compute Module 5 Reminder

- Power draw is very high. The system may cut off if power demand spikes, and the
  hardware gets very hot.
- Audio through headphones and speakers does not work on the CM5 with the CM4
  carrier. The pins changed, so no software change will fix this. Use Bluetooth or
  USB audio.

## Images

### Lakka
![Lakka booting to the RetroArch menu](lakka.png)

**Boards:** Zero 1, Zero 2 W, CM4, CM5

The pure RetroArch option: the entire OS is RetroArch, with no separate front-end
or desktop. It boots straight into the RetroArch menu and uses a read-only
(squashfs) root filesystem, so it stays small and consistent between boots. This
is the Libretro reference build, with PSPi button mapping and menu layout already
applied.

Username: `root`
Password: `root`

### Batocera
![Batocera EmulationStation menu](batocera.png)

**Boards:** Zero 1, Zero 2 W, CM4, CM5

A turn-key retro-gaming OS with its own EmulationStation-based UI and a built-in
settings menu. Audio is heavily reworked for the PSPi: PipeWire is disabled in
favor of ALSA, RetroArch uses the ALSA thread driver, and a compatibility shim
routes the OS volume control to the BCM2835 PWM audio hardware (PipeWire otherwise
spikes CPU usage on this hardware).

Username: `root`
Password: `linux`

### Recalbox
![Recalbox EmulationStation menu](recalbox.png)

**Boards:** Zero 2 W, CM4, CM5

Another EmulationStation-based retro OS, similar in spirit to Batocera but a
different ecosystem. The stock hardware-detection and add-on scripts are stripped
out to prevent the GPIO conflicts that caused LCD color issues at startup. Note
that Recalbox has no battery icon, so charge level is not shown on screen.

Username: `root`
Password: `recalboxroot`

### RetroPie
![RetroPie EmulationStation menu](retropie.png)

**Boards:** Zero 1, Zero 2 W, CM4, CM5

RetroPie installed on top of Raspberry Pi OS Lite. The `pi` user auto-logs-in on
boot and EmulationStation starts straight away. Audio is set to the analog/PCM
output, the A/B and OK/cancel buttons are swapped for the PSPi layout, and ROMs
can be added via a USB drive or the built-in Samba (network) share.

[How to SSH with RetroPie](https://retropie.org.uk/docs/SSH/)

Username: `pi`
Password: `othermod`

### Raspberry Pi OS
![Raspberry Pi OS desktop](raspios.png)

**Boards:** 64-bit image: Zero 2 W, CM4, CM5 · 32-bit image: all boards

The general-purpose desktop, not a gaming image. It boots into mouse mode by
default because the desktop is more usable with a pointer than a gamepad (switch
`input_type` in `pspi.conf` on the boot partition for gamepad mode). The on-screen
keyboard (Squeekboard) starts automatically at boot. This is the "it's just a Linux
computer" option.

Username: `pi`
Password: `raspberry`

### Kali
![Kali desktop](kali.png)

**Boards:** Zero 2 W, CM4, CM5 (CM5 uses the CM4 image)

A security and penetration-testing distro, not gaming-focused. It boots into mouse
mode like Raspberry Pi OS. Because Kali reads the battery through UPower rather
than the tmpfs the battery monitor writes, a real `pspi_battery` kernel module is
built per installed kernel so the desktop shows charge level natively.

Username: `kali`
Password: `kali`

### Firmware
<!-- screenshot: not needed (headless utility) -->

**Boards:** all boards

Not an operating system. A one-shot utility image that flashes updated firmware to
the ATmega microcontroller over a bit-banged I2C bus, then powers off. There is no
login or UI. Use it to update the ATmega firmware; boards revision 1.5 and later
already have the bootloader and can self-update.

## What's Changed

<!-- Fill in per-release changelog. Group by topic, e.g. Images, Gamepad Driver,
     Battery & Power, WiFi, Power & Stability. -->

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
<!-- screenshot: Lakka RetroArch menu -->

The pure RetroArch option: the entire OS is RetroArch, with no separate front-end
or desktop. It boots straight into the RetroArch menu and uses a read-only
(squashfs) root filesystem, so it stays small and consistent between boots. This
is the Libretro reference build, with PSPi button mapping and menu layout already
applied.

Username: `root`
Password: `root`

### Batocera
<!-- screenshot: Batocera EmulationStation UI -->

A turn-key retro-gaming OS with its own EmulationStation-based UI and a built-in
settings menu. Audio is heavily reworked for the PSPi: PipeWire is disabled in
favor of ALSA, RetroArch uses the ALSA thread driver, and a compatibility shim
routes the OS volume control to the BCM2835 PWM audio hardware (PipeWire otherwise
spikes CPU usage on this hardware).

Username: `root`
Password: `linux`

### Recalbox
<!-- screenshot: Recalbox EmulationStation UI -->

Another EmulationStation-based retro OS, similar in spirit to Batocera but a
different ecosystem. The stock hardware-detection and add-on scripts are stripped
out to prevent the GPIO conflicts that caused LCD color issues at startup. Note
that Recalbox has no battery icon, so charge level is not shown on screen.

Username: `root`
Password: `recalboxroot`

### RetroPie
<!-- screenshot: RetroPie EmulationStation UI -->

RetroPie installed on top of Raspberry Pi OS Lite. Unlike the standalone retro
OSes above, this builds RetroPie from RetroPie-Setup: flash the image with
Raspberry Pi Imager and complete the WiFi setup first, then on first boot it
downloads and installs RetroPie over the network. This takes upwards of an hour,
so keep the PSPi charging. After install it boots into EmulationStation.

[How to SSH with RetroPie](https://retropie.org.uk/docs/SSH/)

Username: `pi`
Password: `othermod`

### Raspberry Pi OS
<!-- screenshot: Raspberry Pi OS desktop -->

The general-purpose desktop, not a gaming image. It boots into mouse mode by
default because the desktop is more usable with a pointer than a gamepad (switch
`input_type` in `pspi.conf` on the boot partition for gamepad mode). The on-screen
keyboard (Squeekboard) starts automatically at boot. This is the "it's just a Linux
computer" option.

Username: `pi`
Password: `raspberry`

### Kali
<!-- screenshot: Kali desktop -->

A security and penetration-testing distro, not gaming-focused. It boots into mouse
mode like Raspberry Pi OS. Because Kali reads the battery through UPower rather
than the tmpfs the battery monitor writes, a real `pspi_battery` kernel module is
built per installed kernel so the desktop shows charge level natively.

Username: `kali`
Password: `kali`

### Firmware
<!-- screenshot: not needed (headless utility) -->

Not an operating system. A one-shot utility image that flashes updated firmware to
the ATmega microcontroller over a bit-banged I2C bus, then powers off. There is no
login or UI. Use it to update the ATmega firmware; boards revision 1.5 and later
already have the bootloader and can self-update.

## Firmware Update Guide for Raspberry Pi Compute Module 4 (PSPi 6)

### Introduction
This guide is designed to update the firmware of the Raspberry Pi Compute Module 4 (CM4) for compatibility with the PSPi 6. The recent firmware update in early 2023 altered the CM4's default configuration, affecting its power-down behavior. This guide will help revert that change so that the CM4 powers down correctly, ensuring compatibility with PSPi 6.

---

### For Windows Users

#### Steps

1. **Download and Install `rpiboot`**
   - Download the `rpiboot` executable from this link:
    - https://raw.githubusercontent.com/othermod/PSPi-Version-6/main/rpi/eeprom/rpiboot_setup.exe
   - Run the installer and follow the on-screen instructions.

2. **Download the Modified Firmware Files**
   - Delete the original `pieeprom.bin` and `pieeprom.sig` files from the installation folder, typically `C:\Program Files (x86)\Raspberry Pi\recovery\`
   - Download the modified `pieeprom.bin` and `pieeprom.sig` files:
      - https://raw.githubusercontent.com/othermod/PSPi-Version-6/main/rpi/eeprom/pieeprom.bin
      - https://raw.githubusercontent.com/othermod/PSPi-Version-6/main/rpi/eeprom/pieeprom.sig
   - Place them into the directory where `rpiboot` was installed, typically `C:\Program Files (x86)\Raspberry Pi\recovery\`

3. **Connect the PSPi 6**
  - Connect the PSPi 6 to your PC using a USB to miniUSB cable.
  - Ensure the switch on the CM4 Carrier is set to USB Boot.
  - Power the PSPi on.

4. **Flash the Firmware**
   - Open the Command Prompt.
   - Navigate to the `usbboot` directory: `cd "C:\Program Files (x86)\Raspberry Pi\"`
   - Run `rpiboot -d recovery`
   - The update is complete when the activity LED on the PSPi 6 begins steadily blinking.

5. **Finalize the Update**
   - Unplug the USB cable from the PSPi 6.
   - Power off the PSPi by holding the power button for a few seconds.
   - Set the switch on the CM4 Carrier to SD/eMMC.

---

### For Linux Users

#### Steps

1. **Install Dependencies**
   - Install libusb: `sudo apt install libusb-1.0-0-dev`
   - Install Git: `sudo apt install git`

2. **Clone and Build usbboot**
   - `git clone --depth=1 https://github.com/raspberrypi/usbboot`
   - `cd usbboot`
   - `make`

3. **Modify Bootloader Configuration**
   - Navigate to the `recovery` directory.
   - Edit or create a `boot.conf` file with the necessary configuration for PSPi 6.
     - Open `boot.conf` in a text editor: `nano boot.conf`
     - Modify the file to match the following configuration:
       ```
       [all]
       BOOT_UART=0
       WAKE_ON_GPIO=0
       POWER_OFF_ON_HALT=1

       # Boot Order Codes, from https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#BOOT_ORDER
       # Try SD first (1), followed by, USB PCIe, NVMe PCIe, USB SoC XHCI then network
       BOOT_ORDER=0xf25641

       # Set to 0 to prevent bootloader updates from USB/Network boot
       # For remote units EEPROM hardware write protection should be used.
       ENABLE_SELF_UPDATE=1
       ```
     - Save the changes and exit the editor (in nano, press `CTRL+X`, then `Y`, and `Enter`).

4. **Build the Firmware Files**
   - Run `./update-pieeprom.sh` to create `pieeprom.bin` and `pieeprom.sig`.

5. **Connect the PSPi 6**
   - Connect the PSPi 6 to your PC using a USB to miniUSB cable.
   - Ensure the switch on the CM4 Carrier is set to USB Boot.
   - Power the PSPi on.

6. **Flash the Firmware**
   - Run `./rpiboot -d recovery`.
   - The update is complete when the activity LED on the PSPi 6 starts blinking.

7. **Finalize the Update**
   - Unplug the USB cable from the PSPi 6.
   - Power off the PSPi by holding the power button for a few seconds.
   - Set the switch on the CM4 Carrier to SD/eMMC.

---

### Conclusion
Your CM4 should now allow the PSPi 6 to fully power off once the shutdown completes. If your system doesn't power off, it may be due to incompatibilities with Windows and certain versions of rpiboot. Try uninstalling rpiboot (search rpiboot from the Start menu, and click Uninstall rpiboot), and then re-performing the process using the older version I now have linked above.

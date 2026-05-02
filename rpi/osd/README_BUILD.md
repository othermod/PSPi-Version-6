# PSPi Drivers Build Prerequisites & Instructions

## 1. System Packages (Ubuntu/Debian)
Install these packages before building:
```bash
sudo apt-get update
sudo apt-get install -y \
    gcc-aarch64-linux-gnu \
    patchelf \
    libasound2-dev
```

For 32-bit builds, also install:
```bash
sudo apt-get install -y gcc-arm-linux-gnueabihf binutils-arm-linux-gnueabihf
```

For the 32-bit `libasound.so` dependency, extract the ARM32 version from the Debian package:
```bash
dpkg -x libasound2_*.deb /tmp/libasound2
cp /tmp/libasound2/usr/lib/arm-linux-gnueabihf/libasound.so.2.0.0 lib/32bit/libasound.so
```

## 2. Raspberry Pi Headers
Clone the userland repository:
```bash
git clone --depth 1 https://github.com/raspberrypi/userland.git /tmp/rpi-userland
```

## 3. Target Libraries
The `osd` driver requires Raspberry Pi GPU firmware libraries. Place them in **both** `lib/32bit/` and `lib/64bit/`:
*   `libbcm_host.so`
*   `libasound.so`
*   `libvchiq_arm.so` (and `.so.0`)
*   `libvcos.so` (and `.so.0`)

Each directory needs its own copy of the architecture-matched libraries.

## 4. Architecture Notes
*   **`osd`**: Builds for both 64-bit (AArch64) and 32-bit (ARMHF).
*   **`main` & `mouse`**: Available for both 32-bit (ARMHF) and 64-bit (AArch64).
*   The `package` target prepares the self-contained `bin/64bit/` folder for FAT32/Lakka deployment.

## 5. Building
From the `rpi/drivers/` directory:
```bash
# Build osd 64-bit and prepare the FAT32/Lakka package
make package

# Build everything for both architectures
make all_64 all_32

# The ready-to-use folder will be in:
# bin/64bit/
# bin/32bit/
```

To build individual targets:
```bash
make main_64 mouse_64 osd_64   # 64-bit
make main_32 mouse_32 osd_32   # 32-bit
```

## 6. Deployment to Raspberry Pi
1.  Copy the entire `bin/64bit/` folder to your Raspberry Pi.
2.  The `osd` binary is self-contained — all required libraries are included in the same folder.
3.  It is compatible with FAT32 filesystems (no symlinks).

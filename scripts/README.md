## Environment Setup Commands

Run these commands in order to set up the build environment:

```bash
# 1. Update package lists
sudo apt-get update

# 2. Install required packages
sudo apt-get install -y \
  gcc-arm-linux-gnueabi \
  g++-arm-linux-gnueabi \
  binutils-arm-linux-gnueabi \
  gcc-aarch64-linux-gnu \
  g++-aarch64-linux-gnu \
  gcc-14-aarch64-linux-gnu \
  libc6-arm64-cross \
  kmod \
  curl \
  squashfs-tools \
  gcc-avr \
  binutils-avr \
  avr-libc \
  device-tree-compiler \
  fdisk \
  e2fsprogs \
  qemu-user-static \
  binfmt-support
```

The last four packages (`fdisk`, `e2fsprogs`, `qemu-user-static`, `binfmt-support`) are
required only by the **retropie** distro, which expands the base image and installs
RetroPie inside a QEMU chroot. All other distros need only the cross-toolchain and the
squashfs/AVR/device-tree tools above.

Note that on Ubuntu 24.04 and newer, `fdisk` is a separate package from `util-linux`
and must be installed explicitly.

The **ubuntu** distro (desktop image) additionally needs the following to build the
`pspi_battery` kernel module on the host:

- `gcc-14-aarch64-linux-gnu` — aarch64 cross gcc >= 14 (the kernel uses
  `-fmin-function-alignment`, unsupported by gcc 13 and older); `gcc-14-aarch64-linux-gnu`
  is installed on top of `gcc-aarch64-linux-gnu`/`gcc-13`.
- `libc6-arm64-cross` — the QEMU loader at `/usr/aarch64-linux-gnu`, needed to run the
  header package's prebuilt arm64 `modpost` on an x86_64 host (set via `QEMU_LD_PREFIX`).
- `kmod` — provides `depmod`, used to regenerate the module metadata in the image.
- `curl` — used to resolve the matching kernel-headers package from the Ubuntu archive.

This also requires **network access to `ports.ubuntu.com`** at build time, since the
preinstalled Ubuntu image ships no kernel headers (unlike Kali), so the patcher fetches
the matching `linux-headers-<kernel>` packages from the Ubuntu arm64 archive and
cross-compiles `pspi_battery.ko` against them.

# 3. Download and install Arduino CLI
wget -qO /tmp/arduino-cli.tar.gz https://github.com/arduino/arduino-cli/releases/download/v1.5.0/arduino-cli_1.5.0_Linux_64bit.tar.gz
sudo tar xzf /tmp/arduino-cli.tar.gz -C /usr/local
sudo chmod +x /usr/local/arduino-cli

# 4. Initialize Arduino CLI and install AVR core without sudo
mkdir -p /home/user/.arduino15
chmod 755 /home/user/.arduino15
/usr/local/arduino-cli config init
/usr/local/arduino-cli core install arduino:avr

## Building an Image

Navigate to the project directory and run the build script:

```bash
cd /home/user/github/PSPi-Version-6
sudo ./scripts/patcher.sh --distro <distro_name> --target <target>
```
### Examples

```bash
# Build Lakka for CM4
sudo ./scripts/patcher.sh --distro lakka --target cm4

# Build Batocera for CM4
sudo ./scripts/patcher.sh --distro batocera --target cm4
```
## Output Location

Final images are written to `~/pspi/patched_images/`

Cache (downloaded base images) is stored in `~/pspi/stock_images/`

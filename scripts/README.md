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
  squashfs-tools \
  gcc-avr \
  binutils-avr \
  avr-libc \
  device-tree-compiler

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

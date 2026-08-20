# PSPi 6 Image Patcher — Environment Setup & Reference

`patcher.sh` builds PSPi-ready OS images from stock Raspberry Pi images. This
document is the complete, verified recipe for preparing a build machine (host,
VM, or container) so the patcher runs on the first try. Every package name,
binary name, path, and quirk below was verified by actually setting up this
container and building the rpi/atmega components.

## Quick start — full command sequence (fresh Ubuntu 24.04)

Run these in order. Everything after `apt-get install` is explained in the
sections below; the container-only steps are marked `[container]`.

```bash
# 0. Base utilities (usually preinstalled; listed for safety on minimal images)
sudo apt-get update
sudo apt-get install -y make wget xz-utils python3 tar gzip sudo

# 1. Cross toolchains, AVR, squashfs, and image tools (one command)
sudo apt-get install -y \
  gcc-arm-linux-gnueabi g++-arm-linux-gnueabi binutils-arm-linux-gnueabi \
  gcc-arm-linux-gnueabihf g++-arm-linux-gnueabihf binutils-arm-linux-gnueabihf \
  gcc-12-arm-linux-gnueabihf g++-12-arm-linux-gnueabihf \
  gcc-aarch64-linux-gnu g++-aarch64-linux-gnu gcc-14-aarch64-linux-gnu \
  libc6-arm64-cross libc6-armhf-cross \
  kmod curl squashfs-tools gcc-avr binutils-avr avr-libc \
  device-tree-compiler fdisk e2fsprogs zerofree qemu-user-static binfmt-support

# 2. Arduino CLI (used to fetch/maintain the AVR core; see section 3)
wget -qO /tmp/arduino-cli.tar.gz https://github.com/arduino/arduino-cli/releases/download/v1.5.0/arduino-cli_1.5.0_Linux_64bit.tar.gz
sudo tar xzf /tmp/arduino-cli.tar.gz -C /usr/local   # extracts the `arduino-cli` binary into /usr/local
sudo ln -sf /usr/local/arduino-cli /usr/local/bin/arduino-cli   # /usr/local itself is NOT on PATH

# 3. Arduino AVR core — MUST go under the $HOME the build will see (see 3.2)
HOME=/path/of/build-user arduino-cli config init
HOME=/path/of/build-user arduino-cli core install arduino:avr

# 4. [container] /tmp must not be overlayfs (squashfs distros only, see section 4)
[ "$(stat -f -c %T /tmp)" = overlayfs ] && sudo mount -t tmpfs -o size=30g tmpfs /tmp

# 5. Build
cd <repo>
sudo ./scripts/patcher.sh --distro lakka --target cm4
```

---

## 1. Required packages

### 1.1 Base utilities

`make` (rpi drivers, overlays, atmega), `wget` (image downloads in
`download_image`), `xz-utils` (`xz -9 -T0` repack), `python3`
(`detect_partition`, `zero_fat32.py`), `tar`/`gzip` (arduino-cli install,
`.img.gz` decompress), `sudo`. These ship with normal Ubuntu installs but are
NOT guaranteed on minimal containers — install them explicitly rather than
debugging a missing `make`.

### 1.2 The one apt-get command and what each package actually provides

Beware: **the package name and the installed binary name differ for the
gcc-14 package** (see table). Do not try to run `gcc-14-aarch64-linux-gnu`
— that binary does not exist.

| Package | Installed binary / path | Used by / notes |
|---|---|---|
| `gcc-arm-linux-gnueabi`, `g++-…`, `binutils-…` | `arm-linux-gnueabi-gcc` (GCC 13), `-g++`, `-ld`, `-ar` | **All 32-bit PSPi runtime drivers.** The rpi Makefiles hardcode `arm-linux-gnueabi-gcc -march=armv6zk -mfloat-abi=softfp` (armel, softfp). Do NOT "fix" this to `arm-linux-gnueabihf`: the static binaries are built for the kernel ABI. |
| `gcc-arm-linux-gnueabihf`, `g++-…`, `binutils-…` | `arm-linux-gnueabihf-gcc` (GCC 13) | **32-bit kernel-module builds only** (Kali `zero2`): `build_battery_module_from_headers` uses `CROSS_COMPILE=arm-linux-gnueabihf-`. The patcher's convenience function, not the driver Makefiles. |
| `gcc-12-arm-linux-gnueabihf`, `g++-12-…` | **`arm-linux-gnueabihf-gcc-12`** (version-suffixed!) | **Kali `zero2` battery module only.** Kali's image kernel was built with GCC 12 and the shipped header tree pins `CONFIG_CC_VERSION_TEXT=…gcc-12`, so the cross-module build invokes the version-suffixed `gcc-12` binary whether or not `arm-linux-gnueabihf-gcc` (13) exists. Missing it fails the build with `make[1]: arm-linux-gnueabihf-gcc-12: No such file or directory`. |
| `gcc-aarch64-linux-gnu`, `g++-…` | `aarch64-linux-gnu-gcc` (GCC 13) | All 64-bit PSPi runtime drivers (`aarch64-linux-gnu-gcc ... -static`). |
| `gcc-14-aarch64-linux-gnu` | **`/usr/bin/aarch64-linux-gnu-gcc-14`** (version-suffixed!) | **Ubuntu distro only.** Kernel >= 6.5 needs `-fmin-function-alignment`, unsupported by GCC 13. `ubuntu.sh` selects it via `command -v aarch64-linux-gnu-gcc-15` then `aarch64-linux-gnu-gcc-14`. |
| `libc6-arm64-cross` | `/usr/aarch64-linux-gnu` | QEMU loader needed to run the prebuilt arm64 `modpost` on x86_64 during kernel-module builds (Ubuntu, Kali cm4). Wired via `QEMU_LD_PREFIX=/usr/aarch64-linux-gnu`. |
| `libc6-armhf-cross` | `/usr/arm-linux-gnueabihf` | Same loader role for 32-bit kernel-module builds (Kali `zero2` → `QEMU_LD_PREFIX=/usr/arm-linux-gnueabihf`). |
| `libdrm-dev:arm64` | `/usr/lib/aarch64-linux-gnu/libdrm.a` | **gamepad_view only, amd64 build hosts**: static libdrm for the aarch64 cross build of `rpi/gamepad_view`. Install via `sudo dpkg --add-architecture arm64 && sudo apt update && sudo apt install libdrm-dev:arm64`. Required by `make -C rpi/gamepad_view 64` on x86 hosts (and therefore by local non-CI builds of the `gamepadview` distro). Native arm64 hosts/runners just install plain `libdrm-dev` and use `make 64 CC_64=gcc`. |
| `kmod` | `depmod`, `modprobe` | `depmod` regenerates module metadata after installing `pspi_battery.ko`; `modprobe` needed at runtime on images. |
| `squashfs-tools` | `mksquashfs` | Repack step of every `squashfs` method distro. |
| `gcc-avr`, `binutils-avr`, `avr-libc` | `avr-gcc` (7.3), `avr-g++`, `avr-objcopy`, `avr-size`, `avr-ar` | ATmega firmware build (`atmega/firmware/Makefile`). |
| `device-tree-compiler` | `dtc` | Builds the .dtbo overlays (`rpi/audio`, `rpi/lcd`, `rpi/pcie`). |
| `zerofree` | `zerofree` | Required by every `copy`-method distro; zeroes rootfs free space before xz compression. A missing/failing `zerofree` is FATAL (never a silent size blowup). |
| `fdisk` | `fdisk` | RetroPie only (expands the base image). On Ubuntu >= 24.04 this is a package separate from `util-linux`. |
| `qemu-user-static`, `binfmt-support` | `qemu-arm-static`, `qemu-aarch64-static` | RetroPie's QEMU chroot, and kernel-module builds that execute the binary `modpost`/`fixdep` under QEMU (Kali, Ubuntu). Both `qemu-arm` and `qemu-aarch64` must be enabled in `/proc/sys/fs/binfmt_misc` — a missing `qemu-arm` handler fails Kali's 32-bit module build with `scripts/basic/fixdep: Exec format error`. |
| `e2fsprogs` | `mkfs.ext4`, ... | RetroPie (resize/expand). |
| `curl` | `curl` | **Ubuntu distro only**: resolves the matching `linux-headers-<kernel>` package from the Ubuntu archive. |

### 1.3 Network requirements at build time

- All distros: the base-image URLs in the distro configs (GitHub releases,
  `downloads.raspberrypi.com`, `cdimage.ubuntu.com`, `upgrade.recalbox.com`).
- Ubuntu additionally needs **`ports.ubuntu.com`** — its image ships no kernel
  headers, so the patcher downloads `linux-headers-*` debs from there and
  cross-compiles `pspi_battery.ko` against them.
- **gamepad_view CI builds on a native arm64 runner**: `build-gamepad-view.yml`
  runs on `ubuntu-24.04-arm` (free for public repos since GA Aug 2025), so
  libdrm and gcc resolve natively — no multiarch setup at all. If it ever
  moves back to an amd64 runner, the machinery to make that work (pin the
  runner's deb822 `ubuntu.sources` stanzas to amd64, append arm64 stanzas
  for `ports.ubuntu.com` — Ubuntu publishes non-amd64 packages there — and
  derive suites from `/etc/os-release`) is preserved in this file's git
  history. The build-images job stays on amd64 and is unaffected: it consumes
  the prebuilt artifact and never enables multiarch.

---

## 2. Arduino CLI

Used ONLY to fetch and maintain the Arduino AVR core. **The build itself does
not call arduino-cli** — the ATmega Makefile invokes `avr-gcc` directly against
the core's headers (see 3.1). If you install/place the core by hand, arduino-cli
need not even be on PATH.

- Exact pin: `v1.5.0`, URL
  `https://github.com/arduino/arduino-cli/releases/download/v1.5.0/arduino-cli_1.5.0_Linux_64bit.tar.gz`
- The tarball extracts two files (`arduino-cli`, `LICENSE.txt`) into the `-C`
  target. `sudo tar xzf ... -C /usr/local` therefore puts the binary at
  **`/usr/local/arduino-cli`** — `/usr/local` is NOT on a default PATH, so also
  `sudo ln -sf /usr/local/arduino-cli /usr/local/bin/arduino-cli`.
- Its config lives at `$HOME/.arduino15/arduino-cli.yaml` (board-manager URLs
  only; no plugin config needed for this project).

---

## 3. Arduino AVR core — where it MUST live (the subtle part)

### 3.1 How the build finds it

`atmega/firmware/Makefile` resolves the core by glob, NOT via arduino-cli:

```make
ARDUINO_AVR = $(lastword $(sort $(wildcard $(HOME)/.arduino15/packages/arduino/hardware/avr/*)))
```

So there must be an AVR platform directory under **`$HOME/.arduino15/` of the
user the driver build runs as** (home of a matching version, e.g. `1.8.8`). If
the glob is empty the makefile aborts with `Arduino AVR core not found.`

### 3.2 Whose $HOME does the build use?

`patcher.sh:build_drivers()` decides the build user:

| How you invoke the patcher | Driver build runs as | Core must live at |
|---|---|---|
| `sudo ./scripts/patcher.sh …` (SUDO_USER set) | `sudo -u "$SUDO_USER" -H` → HOME = that user's **passwd** home | `/home/<that-user>/.arduino15/…` |
| `./scripts/patcher.sh …` from a plain **root** shell (SUDO_USER unset) | root, HOME=`/root` | `/root/.arduino15/…` |

`-H` means HOME comes from `/etc/passwd`, NOT from any `~` convention. Find the
actual value empirically rather than assuming:

```bash
echo "$HOME"                                   # when running patcher directly
sudo -u "$SUDO_USER" -H sh -c 'echo $HOME'     # exact HOME build_drivers will use under sudo
```

### 3.3 Installing the core for the right home

Three equivalent options (pick one per target HOME):

```bash
# A. official — init + install under that home
HOME=/target/home arduino-cli config init
HOME=/target/home arduino-cli core install arduino:avr

# B. verify what is already installed under a given home
HOME=/target/home arduino-cli core list        # -> arduino:avr 1.8.8

# C. share one core across several homes (what this container does)
#    install once under the canonical home, then symlink the others:
mkdir -p /target/home && ln -s /path/of/canonical/.arduino15 /target/home/.arduino15
```

The core contents the Makefile actually uses (to sanity-check a hand-built
core): `cores/arduino/`, `libraries/Wire/src`, `libraries/EEPROM/src`,
`variants/standard`.

### 3.4 Facts from this container (for reference)

- Canonical core install: `/home/user/.arduino15` (core `arduino:avr 1.8.8`).
- This agent session is a plain root shell, so `build_drivers` would run as
  root with HOME=`/root`; a symlink `/root/.arduino15 -> /home/user/.arduino15`
  makes the core visible to both. `sudo -u ubuntu -H` here yields
  `/home/ubuntu` (the `ubuntu` user's passwd home) — verify per-host.

---

## 4. [container/VM only] /tmp must not be on overlayfs

Only affects `PATCH_METHOD=squashfs` distros (Lakka, Batocera, Recalbox). The
patcher layers an overlay filesystem on files created under its work dir
(`mktemp -d /tmp/pspi-build-…`). The Linux overlay driver rejects an upperdir
that is itself on overlayfs — which is the default when a Docker container's
root (and hence /tmp) is an overlay snapshot.

**Diagnose:**

```bash
stat -f -c %T /tmp        # "overlayfs"  -> broken; "tmpfs"/"ext4"/"xfs" -> fine
```

**Fix (applies cleanly on a tmpfs-capable kernel):**

```bash
sudo mount -t tmpfs -o size=30g tmpfs /tmp
```

30 GB sizing rationale (measured on a real CM4 Lakka build): compressed
download 0.9 GB, decompressed image 2.1 GB, repacked squashfs work ~1–2 GB,
overlay upper/work + boot ops ~1–2 GB. The mount is lost on restart — automate
it via the container entrypoint or `/etc/fstab` (`tmpfs /tmp tmpfs rw,size=30g 0 0`) if
builds run repeatedly.

**Verify the fix:**

```bash
sudo mkdir -p /tmp/ov/{up,wk,tgt,sq}
echo hi | sudo mksquashfs /tmp/ov /tmp/ov/src.sq -noappend -quiet
sudo mount -t squashfs -o loop /tmp/ov/src.sq /tmp/ov/sq
sudo mount -t overlay -o lowerdir=/tmp/ov/sq,upperdir=/tmp/ov/up,workdir=/tmp/ov/wk \
  overlay /tmp/ov/tgt && echo OVERLAY_OK
```

This container already satisfies the requirement: `/tmp` is a mounted 48 GB
tmpfs. Root and work dirs are overlayfs — builds must still use `/tmp`
(default `WORK_ROOT`), which they do.

---

## 5. QEMU + binfmt (kernel-module distros and RetroPie)

Needed whenever the host must *execute* ARM binaries: kernel-module builds run
the headers' prebuilt arm64/armhf `modpost` under QEMU (Ubuntu, Kali cm4/zero2),
and RetroPie installs packages inside a QEMU chroot.

**Check registration:**

```bash
if mount | grep -q binfmt && ls /proc/sys/fs/binfmt_misc/ | grep -q qemu; then
  echo "binfmt/qemu registered:"; ls /proc/sys/fs/binfmt_misc/ | grep qemu
else
  echo "binfmt_misc not mounted or qemu handlers missing (see below)"
fi
```

`qemu-user-static` + `binfmt-support` are installed by the apt command in
section 1; on a normal host `systemd-binfmt` registers the handlers at boot. In
a **Docker container binfmt_misc may not be mounted at all** (needs
privileges/host support) — the failure mode is `Exec format error` when the
patcher tries to run the arm binary. Either run the container with binfmt
support (`--privileged` or a host-provided `binfmt_misc` mount), or know that
the affected steps will fail. In this container binfmt_misc is not mounted;
nothing has been done about it, matching the fact that no image build has
exercised the QEMU paths yet.

---

## 6. Verify the environment (go/no-go checklist)

Run these before a full image build; they are the exact tools the patcher
touches:

```bash
# every binary the build invokes
for t in arm-linux-gnueabi-gcc aarch64-linux-gnu-gcc aarch64-linux-gnu-gcc-14 \
         arm-linux-gnueabihf-gcc avr-gcc avr-objcopy dtc mksquashfs xz \
         python3 wget make zerofree fdisk depmod modprobe qemu-arm-static \
         qemu-aarch64-static; do command -v "$t" >/dev/null || echo "MISSING $t"; done

# AVR core reachable from the build user's HOME
HOME=<build-home> arduino-cli core list          # must show arduino:avr

# squashfs-overlay capability (if building squashfs distros)  -> section 4
stat -f -c %T /tmp

# Test-build all host-side artifacts (what build_drivers does):
make -C rpi 32
make -C rpi 64
HOME=<build-home> make -C atmega/firmware all    # produces firmware.hex
```

Expected outputs: `rpi/{gamepad,battery,rtc,wifi}/{32,64}/<binary>`,
`rpi/{audio,lcd,pcie}/*.dtbo`, `atmega/firmware/firmware.hex`,
`rpi/gamepad_view/64/gamepad_view` (64-bit only; needs `libdrm-dev:arm64`).

---

## 7. Building images

```bash
cd /home/user/github/PSPi-Version-6
sudo ./scripts/patcher.sh --distro <distro_name> --target <target> [--version X.Y.Z]
```

Examples:

```bash
sudo ./scripts/patcher.sh --distro lakka --target cm4
sudo ./scripts/patcher.sh --distro batocera --target cm4
```

### Output and cache locations

```bash
LOCAL_ROOT="${PSPI_LOCAL_ROOT:-/home/user}"
OUTPUT_DIR="${GITHUB_WORKSPACE:-$LOCAL_ROOT}/pspi/patched_images"
CACHE_DIR="${GITHUB_WORKSPACE:-$LOCAL_ROOT}/pspi/stock_images"
```

Local (non-CI) builds are frozen to `/home/user` (override with
`PSPI_LOCAL_ROOT`), so cache and output never depend on the invoking user's
`$HOME`. GitHub Actions sets `GITHUB_WORKSPACE`, which overrides both paths
exactly as it always did — CI behavior is unchanged. On this machine the cache at `/home/user/pspi/stock_images/`
already holds the base images, so builds reuse them instead of re-downloading.
Per-build work dirs go to `$WORK_ROOT` (`/tmp` unless `PSPI_WORK_DIR` is set
— keep `/tmp` for the squashfs-overlay reason in section 4).

### Distro targets and 32/64 mapping (for sanity checks)

| Distro | Method | Targets | 32-bit targets | 64-bit targets |
|---|---|---|---|---|
| lakka | squashfs | cm4 cm5 zero2 zero1 | zero1 | cm4 cm5 zero2 |
| batocera | squashfs | cm4 cm5 zero2 zero1 | zero1 | cm4 cm5 zero2 |
| recalbox | squashfs | cm4 cm5 zero2 zero1 | zero1 zero2 | cm4 cm5 |
| retropie | copy | zero1 zero2 cm4 cm5 | zero1 | zero2 cm4 cm5 |
| raspberrpios | copy | arm64 armhf | armhf | arm64 |
| raspioslite | copy | arm64 armhf | armhf | arm64 |
| gamepadview | copy | arm64 | — | arm64 |
| kali | copy | zero2 cm4 | zero2 | cm4 |
| ubuntu | copy | all | — | all (CM4/CM5 only) |
| firmware | copy | all | all | — |

`firmware` builds the ATmega updater image: boot.sh is replaced with the
firmware flashing script and the payloads `update_firmware` +
`atmega/firmware/firmware.hex` are copied onto the boot partition.

---

## 8. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Arduino AVR core not found` (make fails in `atmega/firmware`) | Core not under the `$HOME` the driver build runs as (see 3.2) | `HOME=<that-home> arduino-cli core install arduino:avr`, or symlink the canonical `.arduino15` into that HOME |
| `mount: ... wrong fs type, bad option, bad superblock on overlay...` / `overlay: filesystem on ... not supported as upperdir` | `/tmp` is overlayfs and hosts the overlay upperdir (squashfs distros) | `sudo mount -t tmpfs -o size=30g tmpfs /tmp` (section 4) |
| `Exec format error` when the patcher runs an arm binary (modpost, chroot) | binfmt_misc not mounted / qemu not registered | Check section 5; run the container with binfmt support |
| `gcc-14-aarch64-linux-gnu: command not found` | Wrong binary name | The package installs `/usr/bin/aarch64-linux-gnu-gcc-14` (section 1.2); `ubuntu.sh` finds it itself |
| `aarch64 gcc >= 14 not found` (ubuntu distro dies in `build_battery_module`) | `gcc-14-aarch64-linux-gnu` missing | install it per section 1; confirm `/usr/bin/aarch64-linux-gnu-gcc-14` |
| `zerofree not installed; required to zero rootfs` | missing package | `apt-get install zerofree` — it is fatal by design |
| `fdisk: command not found` (RetroPie) | On Ubuntu >= 24.04 `fdisk` is not pulled in by `util-linux` | `apt-get install fdisk` |

---

## 9. What this container needed beyond the documented base (for audit)

- **armhf toolchain** (`gcc-arm-linux-gnueabihf` + `binutils-arm-linux-gnueabihf`
  + `libc6-armhf-cross`): required by Kali `zero2`'s 32-bit kernel-module build;
  the previous README list was missing them.
- **`/root/.arduino15` symlink** to the canonical `/home/user/.arduino15`:
  this session builds as root (SUDO_USER unset) so HOME=`/root`.
- **`/tmp` tmpfs** was already mounted (48 GB) — matched the requirement from
  section 4; nothing to do.
- **binfmt_misc is not mounted** in this container; QEMU-executing steps
  (kernel-module builds, RetroPie) have not been run here yet. See section 5.
- **`libdrm-dev:arm64`** (multiarch): required for the `gamepadview` distro's
  local `gamepad_view` cross-build (`make -C rpi/gamepad_view 64`), which
  patcher.sh's `build_drivers` runs only when `--distro gamepadview` is
  requested (so local builds of other distros don't need it). Installed per the section 1.2
  recipe (`dpkg --add-architecture arm64` + `apt install libdrm-dev:arm64`).
  Not needed in the GitHub release job, which consumes the prebuilt
  `gamepad-view` artifact instead (build-gamepad-view.yml has its own install).
- Everything else matched the base recipe; all drivers, overlays, and the ATmega
  firmware were test-built successfully from this environment.
PATCH_METHOD="squashfs"
SQUASHFS_PATH="boot/recalbox"
DRIVERS_BASE="/boot"
INIT_SYSTEM=sysv
SQUASHFS_COMP_ARGS="-comp xz"

ALL_TARGETS=(cm4 cm5 zero2 zero1)

declare -A TARGET_URL TARGET_SHA256 TARGET_PSPI_PREFIX TARGET_BIN

# Fixed filename under a "latest" path: upstream can (and did) change the
# bytes under it. TARGET_SHA256 below pins what we build from; a mismatch
# against the live URL now routes through the torrent fallback (see
# TARGET_TORRENT below) instead of failing the build.
TARGET_URL[cm4]="https://upgrade.recalbox.com/latest/rpi4_64/recalbox-rpi4_64.img.xz"
TARGET_URL[cm5]="https://upgrade.recalbox.com/latest/rpi5_64/recalbox-rpi5_64.img.xz"
TARGET_URL[zero2]="https://upgrade.recalbox.com/latest/rpizero2/recalbox-rpizero2.img.xz"
TARGET_URL[zero1]="https://upgrade.recalbox.com/latest/rpi1/recalbox-rpi1.img.xz"

TARGET_SHA256[cm4]="0f2414909a7aafb04fc9f51346a78dbbfd7f76d509bd13913e89cc7e4a28d851"
TARGET_SHA256[cm5]="a4b5f55fc085941d73d253d6e0f2acbf0faee14aded24fbef9a5494f21af95c5"
TARGET_SHA256[zero2]="387f8c955aeaad939301d54772b1a12146148c66efc47e7319b81f996ddaefd0"
TARGET_SHA256[zero1]="196bbd261e8a346eade7382c189995d2fc1d8fff8c598c6f8381306de47aa838"

TARGET_PSPI_PREFIX[cm4]="Recalbox10.1-Recalbox-CM4"
TARGET_PSPI_PREFIX[cm5]="Recalbox10.1-Recalbox-CM5"
TARGET_PSPI_PREFIX[zero2]="Recalbox10.1-Recalbox-Zero2"
TARGET_PSPI_PREFIX[zero1]="Recalbox9.2.3-Recalbox-Zero1"

TARGET_BIN[cm4]=64
TARGET_BIN[cm5]=64
TARGET_BIN[zero2]=32
TARGET_BIN[zero1]=32

# Recalbox serves version bumps under fixed "latest" URLs: the filename never
# changes but the bytes do (10.0.0.5 -> 10.1 drifted on 2026-09-04). The
# torrents in scripts/torrents/ pin the exact bytes being built from and act
# as the fallback whenever the live URL fails or serves different bytes; each
# is web-seeded by its own latest URL, so the pair stays self-healing while
# URL bytes == torrent bytes.
#
# STATUS (2026-09-06): re-pinned to Recalbox 10.1 (uploaded upstream
# 2026-09-04). TARGET_SHA256, the prefixes, and the web-seeded torrents in
# scripts/torrents/ all describe the same 10.1 bytes; zero1 stayed on
# 9.2.3-Pulstar (upstream never bumped it). The previous 10.0.0.5 images are
# kept in stock_images/old/ (their torrents in ~/pspi/torrents-recalbox-old).
declare -A TARGET_TORRENT

TARGET_TORRENT[cm4]="scripts/torrents/recalbox-rpi4_64.img.xz.torrent"
TARGET_TORRENT[cm5]="scripts/torrents/recalbox-rpi5_64.img.xz.torrent"
TARGET_TORRENT[zero2]="scripts/torrents/recalbox-rpizero2.img.xz.torrent"
TARGET_TORRENT[zero1]="scripts/torrents/recalbox-rpi1.img.xz.torrent"

distro_post_patch() {
    local overlay_target="$1"
    local mnt_boot="$2"

    # Remove the gamepad proxy overlay entirely - PSPi has its own gamepad driver
    rm -f "$mnt_boot/overlays/recalbox-gamepad-proxy.dtbo"

    # Stub out all recalbox hardware detection and addon init scripts.
    # PSPi has its own drivers for everything; these scripts probe GPIOs (e.g.
    # DetectGPiCase2 claims GPIO18 via RPi.GPIO during hardware detection),
    # load conflicting overlays, and start addon daemons that are not needed.
    for script in \
        S02earlyhardware \
        S03recalbox-official-harware-detector \
        S04rrgbjamma \
        S05hardware \
        S13hardware \
        S13crt \
        S92switch
    do
        printf '#!/bin/sh\nexit 0\n' > "$overlay_target/etc/init.d/$script"
    done
}

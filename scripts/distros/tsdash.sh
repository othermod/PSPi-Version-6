# TS Dash (EFI Analytics) "Reference" SD image for Raspberry Pi 3/4.
#
# Base: "Raspberry Pi reference 2022-04-04" pi-gen stage4 (full LXDE desktop),
# Bullseye, kernel 5.15.61. Boot partition is a classic 256 MB vfat mounted at
# /boot (Bullseye-era fstab; NOT /boot/firmware), rootfs is ext4 -> copy method.
#
# TS Dash is a Java kiosk app (/home/pi/Apps/TSDash/TSDash.sh) auto-logged-in
# as user pi via LightDM and started from /etc/xdg/lxsession/LXDE-pi/autostart
# (`@/home/pi/Apps/TSDash/TSDash.sh`). The patcher is purely additive here:
# pspi.conf/boot.sh/drivers/overlays go on /boot, the systemd units start the
# PSPi daemons, and the stock LXDE session keeps launching TS Dash unchanged.
#
# 2022 image, kernel 5.15 -> we target CM4, Zero 2 W, and Zero 1 (armv6
# kernel.img + bcm2708 dtbs are shipped, one 32-bit image boots all three).
# CM5/Pi5 need kernel >= 6.6 (bcm2712), which this image does not have; EFI
# Analytics has no Pi 5 image yet either.
#
# The gamepad is set to mouse input so the joystick drives the TS Dash GUI
# (on-screen buttons; TS Dash also navigates dashes with arrows/ENTER via the
# gamepad's virtual keyboard).
#
# Kernel-5.15-specific overrides in distro_post_patch (kernel 5.15 is old):
#   - audio: the generic config.txt references the kernel6+ audio overlay; the
#     legacy snd_bcm2835 driver in 5.15 needs the kernel5- variant instead
#     (brcm,disable-headphones prop on &audio vs snd_bcm2835.enable_headphones
#     bootarg). Both .dtbo files are installed; only the dtoverlay= ref flips.
#   - display: kernel 5.15 has no usable KMS DPI path for the panel, so the
#     stock vc4-kms-v3d and the generic KMS-based pspi-lcd-overlay are disabled
#     and the display falls back to the v1.1 recipe: legacy firmware DPI
#     (enable_dpi_lcd + gpio= pinmux + dpi_timings) with vc4-fkms-v3d on top.

PATCH_METHOD="copy"
DRIVERS_BASE="/boot"
INIT_SYSTEM="systemd"

# Single target: one source image + one 32-bit driver set. Board-specific
# behavior (gpio-poweroff, act_led, LCD variant) is selected at RUNTIME by the
# conditional filter tags the patcher appends to config.txt ([cm4]/[pi02]/[pi0]
# sections), so the same patched image is written to any supported board's SD
# card. Output names the boards it actually boots: CM4, Zero 2 W, Zero 1
# (NOT CM5 -- this 2022 kernel has no bcm2712 support, so the image cannot be
# called "all boards"). Same single-image model as raspberrpios's armhf target.
ALL_TARGETS=(all)

declare -A TARGET_URL TARGET_SHA256 TARGET_PSPI_PREFIX TARGET_BIN

TARGET_URL[all]="https://www.efianalytics.com/TSDash/download/2022-10-19_TSDash_Reference.img.gz"
TARGET_SHA256[all]="bbcf9581227db1c3363d9d6eb9ef3219a7eb89900af684cf5e452817f89cc50f"
TARGET_PSPI_PREFIX[all]="TSDash-Reference-32bit-Zero1-Zero2-CM4-PSPi6"
TARGET_BIN[all]=32

distro_post_patch() {
    local rootfs_target="$1"
    local mnt_boot="$2"
    # work_dir="$3", BIN="$4" -- not needed here

    # TS Dash is a kiosk GUI: the joystick drives the cursor and on-screen
    # buttons (arrows/ENTER still arrive via the gamepad's virtual keyboard).
    set_input_mouse "$mnt_boot"

    # A dash cluster is always on: disable the idle backlight dim so the
    # screen never goes dark while driving (stock pspi.conf enables it).
    sed -i 's/^enable_dim=true/enable_dim=false/' "$mnt_boot/pspi.conf"
    grep -q '^enable_dim=false' "$mnt_boot/pspi.conf" \
        || die "[tsdash] could not disable dimming in $mnt_boot/pspi.conf"
    echo "  [tsdash] Disabled idle dimming (enable_dim=false)"

    # --- Old-kernel (5.15) audio: flip the PSPi audio overlay references from
    # the kernel6+ variant to the kernel5- (legacy snd_bcm2835) variant. Both
    # .dtbo files are on the boot partition; only config.txt is wrong.
    if grep -qF 'dtoverlay=pspi-audio-cm4-kernel6+' "$mnt_boot/config.txt"; then
        sed -i 's|^dtoverlay=pspi-audio-cm4-kernel6+|dtoverlay=pspi-audio-cm4-kernel5-|' "$mnt_boot/config.txt"
    else
        die "[tsdash] pspi-audio-cm4-kernel6+ line not found in config.txt (generic PSPi section missing?)"
    fi
    if grep -qF 'dtoverlay=pspi-audio-zero-kernel6+' "$mnt_boot/config.txt"; then
        sed -i 's|^dtoverlay=pspi-audio-zero-kernel6+|dtoverlay=pspi-audio-zero-kernel5-|' "$mnt_boot/config.txt"
    else
        die "[tsdash] pspi-audio-zero-kernel6+ line not found in config.txt (generic PSPi section missing?)"
    fi
    echo "  [tsdash] Audio overlays switched to kernel5- variant (legacy snd_bcm2835)"

    # --- Old-kernel (5.15) display: legacy firmware DPI + FKMS (v1.1 recipe).
    # config.txt can't un-set a dtoverlay/dtparam/scalar later, so stock and
    # generic conflicts are commented in place, then the legacy DPI + per-board
    # FKMS sections are appended. Display output ONLY: the v1.1 clock, GPU-mem,
    # and i2c lines are deliberately omitted (i2c already works on this image).
    local cfg="$mnt_boot/config.txt"
    if grep -q '^display_auto_detect=1' "$cfg"; then
        sed -i 's|^display_auto_detect=1|# PSPi old-kernel LCD (was: display_auto_detect=1)|' "$cfg"
    fi
    if grep -q '^max_framebuffers=2' "$cfg"; then
        sed -i 's|^max_framebuffers=2|# PSPi old-kernel LCD (was: max_framebuffers=2)|' "$cfg"
    fi
    if grep -q '^dtoverlay=vc4-kms-v3d' "$cfg"; then
        sed -i 's|^dtoverlay=vc4-kms-v3d|# PSPi old-kernel LCD (was: dtoverlay=vc4-kms-v3d)|' "$cfg"
    fi
    if grep -q '^dtoverlay=pspi-lcd-overlay' "$cfg"; then
        sed -i 's|^dtoverlay=pspi-lcd-overlay.*|# PSPi old-kernel LCD disabled: &|' "$cfg"
    else
        die "[tsdash] no dtoverlay=pspi-lcd-overlay in config.txt (generic PSPi lines missing?)"
    fi
    echo "  [tsdash] Disabled KMS display path (vc4-kms-v3d, pspi-lcd-overlay, auto-detect, fbufs=2)"

    cat >> "$cfg" <<'EOF'

# --- PSPi | TS Dash | legacy firmware DPI + FKMS (kernel 5.15) ---
# Firmware drives the DPI panel directly; FKMS provides the DRM/GL layer.
[all]
disable_fw_kms_setup=1
enable_dpi_lcd=1
display_default_lcd=1
dpi_group=2
dpi_mode=87
dpi_output_format=503863
display_auto_detect=0
max_framebuffers=1

[cm4]
# 24-bit DPI: clock/DE on GPIO 0-1, I2C1 on 2-3, color on 4-27
gpio=0=a2,np
gpio=1=a2,np
gpio=2=a0,np
gpio=3=a0,np
gpio=4-27=a2,np
dpi_timings=800 0 8 4 8 480 0 8 4 8 0 0 0 60 0 25000000 6
dtoverlay=vc4-fkms-v3d,cma-512

[pi0]
# 21-bit DPI: clock/DE on GPIO 0-1, I2C1 on 2-3, color on 5-27 minus 12/20
gpio=0=a2,np
gpio=1=a2,np
gpio=2=a0,np
gpio=3=a0,np
gpio=5-11=a2,np
gpio=13-19=a2,np
gpio=21-27=a2,np
dpi_timings=800 0 8 4 8 480 0 8 4 8 0 0 0 60 0 32000000 6
dtoverlay=vc4-fkms-v3d

[pi02]
# Zero 2 W (BCM2710): same 21-bit DPI layout as Pi Zero
gpio=0=a2,np
gpio=1=a2,np
gpio=2=a0,np
gpio=3=a0,np
gpio=5-11=a2,np
gpio=13-19=a2,np
gpio=21-27=a2,np
dpi_timings=800 0 8 4 8 480 0 8 4 8 0 0 0 60 0 32000000 6
dtoverlay=vc4-fkms-v3d

[all]
EOF
    echo "  [tsdash] Legacy firmware DPI + FKMS sections appended (display output only)"
}
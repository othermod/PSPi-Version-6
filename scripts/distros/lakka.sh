PATCH_METHOD="squashfs"
SQUASHFS_PATH="SYSTEM"
DRIVERS_BASE="/flash"
VC4_REQUIRED=true
INIT_SYSTEM=systemd
SQUASHFS_COMP_ARGS=""

# --- Targets ---

ALL_TARGETS=(cm4 cm5 zero2 zero1)

declare -A TARGET_URL TARGET_SHA256 TARGET_PSPI_PREFIX TARGET_BIN

TARGET_URL[cm4]="https://github.com/libretro/Lakka-LibreELEC/releases/download/v6.1/Lakka-RPi4.aarch64-6.1.img.gz"
TARGET_URL[cm5]="https://github.com/libretro/Lakka-LibreELEC/releases/download/v6.1/Lakka-RPi5.aarch64-6.1.img.gz"
TARGET_URL[zero2]="https://github.com/libretro/Lakka-LibreELEC/releases/download/v6.1/Lakka-RPi3.aarch64-6.1.img.gz"
TARGET_URL[zero1]="https://github.com/libretro/Lakka-LibreELEC/releases/download/v6.1/Lakka-RPi.arm-6.1.img.gz"

TARGET_SHA256[cm4]="9e541bd8d092c63a65c5b7c66295ff9d3c3fc073d6bb6229560526c1c505ca11"
TARGET_SHA256[cm5]="b2fd310742c612b6f7f221540518f03845a75f8e5d0b55c0c2abeb81da8c5bb3"
TARGET_SHA256[zero2]="e72cf352cbaaf0366fc7f46650b0e5335786b6119cdcaf086a0ecee2355ac742"
TARGET_SHA256[zero1]="c331c30d4dc52fbae168d16b844c18833a1e7e790039ceb5f2d2acc6c9b09414"

TARGET_PSPI_PREFIX[cm4]="Lakka6.1-CM4-PSPi6"
TARGET_PSPI_PREFIX[cm5]="Lakka6.1-CM5-PSPi6"
TARGET_PSPI_PREFIX[zero2]="Lakka6.1-Zero2-PSPi6"
TARGET_PSPI_PREFIX[zero1]="Lakka6.1-Zero1-PSPi6"

TARGET_BIN[cm4]=64
TARGET_BIN[cm5]=64
TARGET_BIN[zero2]=64
TARGET_BIN[zero1]=32

distro_post_patch() {
    local overlay_target="$1"
    # mnt_boot="$2"  work_dir="$3"  BIN="$4" -- not needed here

    local cfg="$overlay_target/etc/retroarch.cfg"
    sed -i 's/menu_swap_ok_cancel_buttons = "false"/menu_swap_ok_cancel_buttons = "true"/'  "$cfg"
    sed -i 's/xmb_layout = "0"/xmb_layout = "2"/'                                          "$cfg"
    sed -i 's/xmb_menu_color_theme = .*/xmb_menu_color_theme = "2"/'                       "$cfg"
    sed -i 's/menu_shader_pipeline = .*/menu_shader_pipeline = "0"/'                        "$cfg"
    sed -i 's/input_volume_up = "add"/input_volume_up = "volumeup"/'                        "$cfg"
    sed -i 's/input_volume_down = "subtract"/input_volume_down = "volumedown"/'             "$cfg"
}

distro_post_write() {
    local mnt_boot="$1"
    # BIN="$2" -- not needed here

    md5sum "$mnt_boot/SYSTEM" > "$mnt_boot/SYSTEM.md5"
}

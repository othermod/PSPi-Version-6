source "arm" "lakka_zero_arm" {
  file_urls = ["./Lakka-RPi2.arm-4.3-Base.img.gz"]
  # file_checksum_url     = "file:./Lakka-RPi2.arm-4.3-Base.img.sha256"
  # file_urls             = ["https://github.com/libretro/Lakka-LibreELEC/releases/download/v4.3/Lakka-RPi.arm-4.3.img.gz"]
  # file_checksum_url     = "https://github.com/libretro/Lakka-LibreELEC/releases/download/v4.3/Lakka-RPi.arm-4.3.img.gz.sha256"
  file_checksum_type    = "none"
  file_target_extension = "gz"
  file_unarchive_cmd    = ["gunzip", "$ARCHIVE_PATH"]
  image_build_method    = "reuse"
  image_path            = "PSPi 6 Lakka 4.3 32bit Zero ${var.pspi_version}.img"
  image_size            = "8G"
  image_type            = "dos"
  image_setup_extra = [
    [
      "sed", "-i", "s/quiet/quiet textmode retroarch=0 ssh/g", "$MOUNTPOINT/flash/cmdline.txt"
    ],
    [
      "cat", "$MOUNTPOINT/flash/cmdline.txt"
    ]
  ]

  # configure boot partition
  image_partitions {
    name                    = "boot"
    type                    = "c"
    start_sector            = "8192"
    filesystem              = "vfat"
    filesystem_make_options = ["-L", "LAKKA"]
    size                    = "2G"
    mountpoint              = "/flash"
  }

  # configure root partition
  image_partitions {
    name                    = "root"
    type                    = "83"
    start_sector            = "4202496"
    filesystem              = "ext4"
    filesystem_make_options = ["-L", "LAKKA_DISK"]
    size                    = "0"
    mountpoint              = "/"
  }

  image_chroot_env             = ["PATH=/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin"]

  # qemu binary paths
  qemu_binary_source_path      = "/usr/bin/qemu-arm-static"
  qemu_binary_destination_path = "/usr/bin/qemu-arm-static"
}

source "arm" "lakka_cm4_arm64" {
  file_urls             = ["https://github.com/libretro/Lakka-LibreELEC/releases/download/v4.3/Lakka-RPi4.aarch64-4.3.img.gz"]
  file_checksum_url     = "https://github.com/libretro/Lakka-LibreELEC/releases/download/v4.3/Lakka-RPi4.aarch64-4.3.img.gz.sha256"
  file_checksum_type    = "sha256"
  file_target_extension = "gz"
  file_unarchive_cmd    = ["gunzip", "$ARCHIVE_PATH"]
  image_build_method    = "reuse"
  image_path            = "PSPi 6 Lakka 4.3 64bit CM4 ${var.pspi_version}.img.gz"
  image_size            = "4G"
  image_type            = "dos"

  # configure boot partition
  image_partitions {
    name         = "boot"
    type         = "c"
    start_sector = "2048"
    filesystem   = "fat"
    size         = "256M"
    mountpoint   = "/boot"
  }

  # configure root partition
  image_partitions {
    name         = "root"
    type         = "83"
    start_sector = "526336"
    filesystem   = "ext4"
    size         = "0"
    mountpoint   = "/"
  }

  image_chroot_env             = ["PATH=/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin"]

  # qemu binary paths
  qemu_binary_source_path      = "/usr/bin/qemu-aarch64-static"
  qemu_binary_destination_path = "/usr/bin/qemu-aarch64-static"
}
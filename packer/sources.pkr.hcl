source "arm" "raspios_pizero_arm" {
  file_urls             = ["https://downloads.raspberrypi.com/raspios_lite_armhf/images/raspios_lite_armhf-2023-12-11/2023-12-11-raspios-bookworm-armhf-lite.img.xz"]
  file_checksum_url     = "https://downloads.raspberrypi.com/raspios_lite_armhf/images/raspios_lite_armhf-2023-12-11/2023-12-11-raspios-bookworm-armhf-lite.img.xz.sha256"
  file_checksum_type    = "sha256"
  file_target_extension = "xz"
  file_unarchive_cmd    = ["xz", "--decompress", "$ARCHIVE_PATH"]
  image_build_method    = "reuse"
  image_path            = "PSPi 6 Raspbian 4.3 32bit Lite ${var.pspi_version}.img.gz"
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
  qemu_binary_source_path      = "/usr/bin/qemu-arm-static"
  qemu_binary_destination_path = "/usr/bin/qemu-arm-static"
}

source "arm" "raspios_cm4_arm64" {
  file_urls             = ["https://downloads.raspberrypi.com/raspios_lite_arm64/images/raspios_lite_arm64-2023-12-11/2023-12-11-raspios-bookworm-arm64-lite.img.xz"]
  file_checksum_url     = "https://downloads.raspberrypi.com/raspios_lite_arm64/images/raspios_lite_arm64-2023-12-11/2023-12-11-raspios-bookworm-arm64-lite.img.xz.sha256"
  file_checksum_type    = "sha256"
  file_target_extension = "xz"
  file_unarchive_cmd    = ["xz", "--decompress", "$ARCHIVE_PATH"]
  image_build_method    = "reuse"
  image_path            = "PSPi 6 Raspbian 4.3 64bit CM4 ${var.pspi_version}.img.gz"
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

source "arm" "lakka_pizero_arm" {
  file_urls             = ["https://github.com/libretro/Lakka-LibreELEC/releases/download/v4.3/Lakka-RPi.arm-4.3.img.gz"]
  file_checksum_url     = "https://github.com/libretro/Lakka-LibreELEC/releases/download/v4.3/Lakka-RPi.arm-4.3.img.gz.sha256"
  file_checksum_type    = "sha256"
  file_target_extension = "gz"
  file_unarchive_cmd    = ["gunzip", "$ARCHIVE_PATH"]
  image_build_method    = "reuse"
  image_path            = "PSPi 6 Lakka 4.3 32bit Zero ${var.pspi_version}.img.gz"
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

source "arm" "retropie_pizero_arm" {
  file_urls             = ["https://github.com/RetroPie/RetroPie-Setup/releases/download/4.8/retropie-buster-4.8-rpi2_3_zero2w.img.gz"]
  file_checksum         = "224e64d8820fc64046ba3850f481c87e"
  file_checksum_type    = "md5"
  file_target_extension = "gz"
  file_unarchive_cmd    = ["gunzip", "$ARCHIVE_PATH"]
  image_build_method    = "resize"
  image_path            = "PSPi 6 RetroPie 4.8 32bit Zero ${var.pspi_version}.img.gz"
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
  qemu_binary_source_path      = "/usr/bin/qemu-arm-static"
  qemu_binary_destination_path = "/usr/bin/qemu-arm-static"
}

source "arm" "retropie_cm4_arm" {
  file_urls             = ["https://github.com/RetroPie/RetroPie-Setup/releases/download/4.8/retropie-buster-4.8-rpi4_400.img.gz"]
  file_checksum         = "b5daa6e7660a99c246966f3f09b4014b"
  file_checksum_type    = "md5"
  file_target_extension = "gz"
  file_unarchive_cmd    = ["gunzip", "$ARCHIVE_PATH"]
  image_build_method    = "resize"
  image_path            = "PSPi 6 RetroPie 4.8 32bit CM4 ${var.pspi_version}.img.gz"
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

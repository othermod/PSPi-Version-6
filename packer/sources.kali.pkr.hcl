source "cross" "kali_zero2_armhf" {
  file_urls             = ["https://kali.download/arm-images/kali-2024.4/kali-linux-2024.4-raspberry-pi-zero-2-w-armhf.img.xz"]
  file_checksum         = "8424419091b76a062263762fb687cf6a41ee037d6d3dfb2367bb929270073275"
  file_checksum_type    = "sha256"
  file_target_extension = "xz"
  file_unarchive_cmd    = ["xz", "--decompress", "$ARCHIVE_PATH"]
  image_build_method    = "resize"
  image_path            = "Kali2024.4-Zero2-PSPi6-${var.pspi_version}.img"
  image_size            = "13G"
  image_type            = "dos"

  # configure boot partition
  image_partitions {
    name         = "boot"
    type         = "c"
    start_sector = "2048"
    filesystem   = "vfat"
    size         = "255M"
    mountpoint   = "/boot"
  }

  # configure root partition
  image_partitions {
    name         = "root"
    type         = "83"
    start_sector = "524288"
    filesystem   = "ext4"
    size         = "0"
    mountpoint   = "/"
  }

  image_chroot_env             = ["PATH=/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin"]

  # qemu binary paths
  qemu_binary_source_path      = "/usr/bin/qemu-arm-static"
  qemu_binary_destination_path = "/usr/bin/qemu-arm-static"
}

source "cross" "kali_cm4_arm64" {
  file_urls             = ["https://kali.download/arm-images/kali-2024.4/kali-linux-2024.4-raspberry-pi-arm64.img.xz"]
  file_checksum         = "2862b309deb2d4bbdc6f8924f1ba26f67863df5c6c4a9bbfbbb5afa0ce368a4c"
  file_checksum_type    = "sha256"
  file_target_extension = "xz"
  file_unarchive_cmd    = ["xz", "--decompress", "$ARCHIVE_PATH"]
  image_build_method    = "resize"
  image_path            = "Kali2024.4-CM4-PSPi6-${var.pspi_version}.img"
  image_size            = "15G"
  image_type            = "dos"

  # configure boot partition
  image_partitions {
    name         = "boot"
    type         = "c"
    start_sector = "2048"
    filesystem   = "vfat"
    size         = "255M"
    mountpoint   = "/boot"
  }

  # configure root partition
  image_partitions {
    name         = "root"
    type         = "83"
    start_sector = "524288"
    filesystem   = "ext4"
    size         = "0"
    mountpoint   = "/"
  }

  image_chroot_env             = ["PATH=/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin"]

  # qemu binary paths
  qemu_binary_source_path      = "/usr/bin/qemu-aarch64-static"
  qemu_binary_destination_path = "/usr/bin/qemu-aarch64-static"
}
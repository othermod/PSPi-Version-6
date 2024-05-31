source "arm" "kali_zero2_armhf" {
  file_urls             = ["https://kali.download/arm-images/kali-2023.4/kali-linux-2023.4-raspberry-pi-zero-2-w-armhf.img.xz"]
  file_checksum         = "41f88cbecd97a3731768b88a396265f5cf51455c81452618f18cc53cbcc0ff9a"
  file_checksum_type    = "sha256"
  file_target_extension = "xz"
  file_unarchive_cmd    = ["xz", "--decompress", "$ARCHIVE_PATH"]
  image_build_method    = "resize"
  image_path            = "Kali2023.4-Zero2-PSPi6-${var.pspi_version}.img"
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

source "arm" "kali_cm4_arm64" {
  file_urls             = ["https://kali.download/arm-images/kali-2023.4/kali-linux-2023.4-raspberry-pi-arm64.img.xz"]
  file_checksum         = "ddee8c78f7e13b1ca3adf6e64115546727a5d525fd2ee51cac3d16b3f41717ec"
  file_checksum_type    = "sha256"
  file_target_extension = "xz"
  file_unarchive_cmd    = ["xz", "--decompress", "$ARCHIVE_PATH"]
  image_build_method    = "resize"
  image_path            = "Kali2023.4-CM4-PSPi6-${var.pspi_version}.img"
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
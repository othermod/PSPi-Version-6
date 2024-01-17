source "arm" "recalbox_zero_arm" {
  file_urls             = ["https://upgrade.recalbox.com/latest/download-wizard/rpi1/recalbox-rpi1.img.xz"]
  file_checksum         = "DC420DB300664567CA89F5D521B916B0"
  file_checksum_type    = "md5"
  file_target_extension = "xz"
  file_unarchive_cmd    = ["xz", "--decompress", "$ARCHIVE_PATH"]
  image_build_method    = "reuse"
  image_path            = "PSPi6.Recalbox9.1.Zero.${var.pspi_version}.img.gz"
  image_size            = "4G"
  image_type            = "dos"

  # configure boot partition
  image_partitions {
    name         = "boot"
    type         = "c"
    start_sector = "2048"
    filesystem   = "vfat"
    size         = "3G"
    mountpoint   = "/"
  }

  image_chroot_env             = ["PATH=/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin"]

  # qemu binary paths
  qemu_binary_source_path      = "/usr/bin/qemu-arm-static"
  qemu_binary_destination_path = "/usr/bin/qemu-arm-static"
}

source "arm" "recalbox_zero2_arm64" {
  file_urls             = ["https://upgrade.recalbox.com/latest/download-wizard/rpizero2/recalbox-rpizero2.img.xz"]
  file_checksum         = "FC43CDCB2D5492B78AA1D1CA27EFB36A"
  file_checksum_type    = "md5"
  file_target_extension = "xz"
  file_unarchive_cmd    = ["xz", "--decompress", "$ARCHIVE_PATH"]
  image_build_method    = "reuse"
  image_path            = "PSPi6.Recalbox9.1.Zero2.${var.pspi_version}.img.gz"
  image_size            = "4G"
  image_type            = "dos"

  # configure boot partition
  image_partitions {
    name         = "boot"
    type         = "c"
    start_sector = "2048"
    filesystem   = "vfat"
    size         = "3G"
    mountpoint   = "/"
  }

  image_chroot_env             = ["PATH=/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin"]

  # qemu binary paths
  qemu_binary_source_path      = "/usr/bin/qemu-aarch64-static"
  qemu_binary_destination_path = "/usr/bin/qemu-aarch64-static"
}

source "arm" "recalbox_cm4_arm64" {
  file_urls             = ["https://upgrade.recalbox.com/latest/download-wizard/rpi4_64/recalbox-rpi4_64.img.xz"]
  file_checksum         = "0346EA505B55EF0D3177A02630D51B4F"
  file_checksum_type    = "md5"
  file_target_extension = "xz"
  file_unarchive_cmd    = ["xz", "--decompress", "$ARCHIVE_PATH"]
  image_build_method    = "reuse"
  image_path            = "PSPi6.Recalbox9.1.CM4.${var.pspi_version}.img.gz"
  image_size            = "4G"
  image_type            = "dos"

  # configure boot partition
  image_partitions {
    name         = "boot"
    type         = "c"
    start_sector = "2048"
    filesystem   = "vfat"
    size         = "3G"
    mountpoint   = "/"
  }

  image_chroot_env             = ["PATH=/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin"]

  # qemu binary paths
  qemu_binary_source_path      = "/usr/bin/qemu-aarch64-static"
  qemu_binary_destination_path = "/usr/bin/qemu-aarch64-static"
}
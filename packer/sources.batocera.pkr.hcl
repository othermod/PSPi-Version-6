source "arm" "batocera_zero2_arm" {
  file_urls             = ["https://updates.batocera.org/bcm2836/stable/last/batocera-bcm2836-36-20230311.img.gz"]
  file_checksum_url     = "https://mirrors.o2switch.fr/batocera/bcm2836/stable/last/batocera-bcm2836-36-20230311.img.gz.sha256"
  file_checksum_type    = "sha256"
  file_target_extension = "gz"
  file_unarchive_cmd    = ["gunzip", "$ARCHIVE_PATH"]
  image_build_method    = "resize"
  image_path            = "PSPi6.Batocera36.Zero2.${var.pspi_version}.img.gz" 
  image_size            = "4G" 
  image_type            = "dos"

  # configure boot partition
  image_partitions {
    name         = "boot"
    type         = "c"
    start_sector = "2048"
    filesystem   = "vfat"
    size         = "3G"
    mountpoint   = "/boot"
  }

  # configure root partition
  image_partitions {
    name         = "root"
    type         = "83"
    start_sector = "6293504"
    filesystem   = "ext4"
    size         = "0"
    mountpoint   = "/"
  }

  image_chroot_env             = ["PATH=/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin"]

  # qemu binary paths
  qemu_binary_source_path      = "/usr/bin/qemu-aarch64-static"
  qemu_binary_destination_path = "/usr/bin/qemu-aarch64-static"
}

source "arm" "batocera_cm4_arm64" {
  file_urls             = ["https://updates.batocera.org/bcm2711/stable/last/batocera-bcm2711-bcm2711-38-20231014.img.gz"]
  file_checksum_url     = "https://mirrors.o2switch.fr/batocera/bcm2711/stable/last/batocera-bcm2711-bcm2711-38-20231014.img.gz.sha256"
  file_checksum_type    = "sha256"
  file_target_extension = "gz"
  file_unarchive_cmd    = ["gunzip", "$ARCHIVE_PATH"]
  image_build_method    = "reuse"
  image_path            = "PSPi6.Batocera36.CM4.${var.pspi_version}.img.gz"
  image_size            = "8G"
  image_type            = "dos"

  # configure boot partition
  image_partitions {
    name         = "boot"
    type         = "c"
    start_sector = "2048"
    filesystem   = "vfat"
    size         = "256M"
    mountpoint   = "/boot"
  }

  # configure root partition
  image_partitions {
    name         = "root"
    type         = "83"
    start_sector = "6293504"
    filesystem   = "ext4"
    size         = "0"
    mountpoint   = "/"
  }

  image_chroot_env             = ["PATH=/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin"]

  # qemu binary paths
  qemu_binary_source_path      = "/usr/bin/qemu-aarch64-static"
  qemu_binary_destination_path = "/usr/bin/qemu-aarch64-static"
}
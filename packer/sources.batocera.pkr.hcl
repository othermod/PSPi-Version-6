# Base images are used as a (hopefully) temporary measure to resolve complications with SHARE partition.
# Have been unable to solve without needing to do an initial boot on hardware
# The base build should only require config.txt & overlays in order to guarantee a good initial boot on hardware
# After initial boot, SD card is manually captured with Win32DiskImager and Shrunk with PiShrink. This can be done with WSL if on windows)
# pishrink.sh -v -Z -a imagename.img
# https://win32diskimager.org/
# https://github.com/Drewsif/PiShrink
# Base image is then rehosted to be used for a final build
# Base image should not need to be updated unless we're changing source image from batocera 
source "arm" "batocera_zero_arm_base" {
  file_urls             = ["https://updates.batocera.org/bcm2835/stable/last/batocera-bcm2835-36-20230310.img.gz"]
  file_checksum_url     = "https://mirrors.o2switch.fr/batocera/bcm2835/stable/last/batocera-bcm2835-36-20230310.img.gz.sha256"
  file_checksum_type    = "sha256"
  file_target_extension = "gz"
  file_unarchive_cmd    = ["gunzip", "$ARCHIVE_PATH"]
  image_build_method    = "reuse"
  image_path            = "PSPi6.Batocera36.Zero.Base.${var.pspi_version}.img" 
  image_size            = "5G" 
  image_type            = "dos"

  # configure boot partition
  image_partitions {
    name         = "boot"
    type         = "c"
    start_sector = "2048"
    filesystem   = "vfat"
    size         = "4G"
    mountpoint   = "/boot"
  }

  image_chroot_env             = ["PATH=/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin"]

  # qemu binary paths
  qemu_binary_source_path      = "/usr/bin/qemu-aarch64-static"
  qemu_binary_destination_path = "/usr/bin/qemu-aarch64-static"
}

source "arm" "batocera_zero2_arm64_base" {
  file_urls             = ["https://updates.batocera.org/bcm2836/stable/last/batocera-bcm2836-36-20230311.img.gz"]
  file_checksum_url     = "https://mirrors.o2switch.fr/batocera/bcm2836/stable/last/batocera-bcm2836-36-20230311.img.gz.sha256"
  file_checksum_type    = "sha256"
  file_target_extension = "gz"
  file_unarchive_cmd    = ["gunzip", "$ARCHIVE_PATH"]
  image_build_method    = "reuse"
  image_path            = "PSPi6.Batocera36.Zero2.Base.${var.pspi_version}.img" 
  image_size            = "5G" 
  image_type            = "dos"

  # configure boot partition
  image_partitions {
    name         = "boot"
    type         = "c"
    start_sector = "2048"
    filesystem   = "vfat"
    size         = "4G"
    mountpoint   = "/boot"
  }

  image_chroot_env             = ["PATH=/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin"]

  # qemu binary paths
  qemu_binary_source_path      = "/usr/bin/qemu-arm-static"
  qemu_binary_destination_path = "/usr/bin/qemu-arm-static"
}

source "arm" "batocera_cm4_arm64_base" {
  file_urls             = ["https://updates.batocera.org/bcm2711/stable/last/batocera-bcm2711-bcm2711-38-20231014.img.gz"]
  file_checksum_url     = "https://mirrors.o2switch.fr/batocera/bcm2711/stable/last/batocera-bcm2711-bcm2711-38-20231014.img.gz.sha256"
  file_checksum_type    = "sha256"
  file_target_extension = "gz"
  file_unarchive_cmd    = ["gunzip", "$ARCHIVE_PATH"]
  image_build_method    = "reuse"
  image_path            = "PSPi6.Batocera38.CM4.Base.${var.pspi_version}.img"
  image_size            = "5G"
  image_type            = "dos"

  # configure boot partition
  image_partitions {
    name         = "boot"
    type         = "c"
    start_sector = "2048"
    filesystem   = "vfat"
    size         = "4G"
    mountpoint   = "/boot"
  }

  image_chroot_env             = ["PATH=/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin"]

  # qemu binary paths
  qemu_binary_source_path      = "/usr/bin/qemu-aarch64-static"
  qemu_binary_destination_path = "/usr/bin/qemu-aarch64-static"
}

# Final image builds from base image
source "arm" "batocera_cm4_arm64" {
  file_urls             = ["https://stpspiproduseast001.blob.core.windows.net/pspi6/PSPi6.Batocera38.CM4.Base.img.xz"]
  file_checksum_url     = "https://stpspiproduseast001.blob.core.windows.net/pspi6/PSPi6.Batocera38.CM4.Base.img.xz.sha256"
  file_checksum_type    = "sha256"
  file_target_extension = "xz"
  file_unarchive_cmd    = ["xz", "--decompress", "$ARCHIVE_PATH"]
  image_build_method    = "resize"
  image_path            = "PSPi6.Batocera38.CM4.${var.pspi_version}.img"
  image_size            = "5G"
  image_type            = "dos"

  # configure boot partition
  image_partitions {
    name         = "boot"
    type         = "c"
    start_sector = "2048"
    filesystem   = "vfat"
    size         = "4G"
    mountpoint   = "/boot"
  }

  # configure root partition
  image_partitions {
    name         = "share"
    type         = "83"
    start_sector = "8390656"
    filesystem   = "ext4"
    size         = "0"
    mountpoint   = "/userdata"
  }

  image_chroot_env             = ["PATH=/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin"]

  # qemu binary paths
  qemu_binary_source_path      = "/usr/bin/qemu-aarch64-static"
  qemu_binary_destination_path = "/usr/bin/qemu-aarch64-static"
}
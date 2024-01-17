# 
# Raspbian
# 

source "arm" "raspios_zero_arm" {
  file_urls             = ["https://downloads.raspberrypi.com/raspios_full_armhf/images/raspios_full_armhf-2023-12-06/2023-12-05-raspios-bookworm-armhf-full.img.xz"]
  file_checksum_url     = "https://downloads.raspberrypi.com/raspios_full_armhf/images/raspios_full_armhf-2023-12-06/2023-12-05-raspios-bookworm-armhf-full.img.xz.sha256"
  file_checksum_type    = "sha256"
  file_target_extension = "xz"
  file_unarchive_cmd    = ["xz", "--decompress", "$ARCHIVE_PATH"]
  image_build_method    = "resize"
  image_path            = "PSPi6.PiOS4.3.Zero.${var.pspi_version}.img"
  image_size            = "4G"
  image_type            = "dos"

  # configure boot partition
  image_partitions {
    name         = "boot"
    type         = "c"
    start_sector = "8192"
    filesystem   = "vfat"
    size         = "256M"
    mountpoint   = "/boot"
  }

  # configure root partition
  image_partitions {
    name         = "root"
    type         = "83"
    start_sector = "532480"
    filesystem   = "ext4"
    size         = "0"
    mountpoint   = "/"
  }

  image_chroot_env             = ["PATH=/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin"]

  # qemu binary paths
  qemu_binary_source_path      = "/usr/bin/qemu-arm-static"
  qemu_binary_destination_path = "/usr/bin/qemu-arm-static"
}

source "arm" "raspios_cm4_zero2_arm64" {
  file_urls             = ["https://downloads.raspberrypi.com/raspios_arm64/images/raspios_arm64-2023-12-06/2023-12-05-raspios-bookworm-arm64.img.xz"]
  file_checksum_url     = "https://downloads.raspberrypi.com/raspios_arm64/images/raspios_arm64-2023-12-06/2023-12-05-raspios-bookworm-arm64.img.xz.sha256"
  file_checksum_type    = "sha256"
  file_target_extension = "xz"
  file_unarchive_cmd    = ["xz", "--decompress", "$ARCHIVE_PATH"]
  image_build_method    = "resize"
  image_path            = "PSPi6.PiOS4.3.CM4-Zero2.${var.pspi_version}.img"
  image_size            = "8G"
  image_type            = "dos"

  # configure boot partition
  image_partitions {
    name         = "boot"
    type         = "c"
    start_sector = "8192"
    filesystem   = "vfat"
    size         = "512M"
    mountpoint   = "/boot"
  }

  # configure root partition
  image_partitions {
    name         = "root"
    type         = "83"
    start_sector = "1056768"
    filesystem   = "ext4"
    size         = "0"
    mountpoint   = "/"
  }

  image_chroot_env             = ["PATH=/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin"]

  # qemu binary paths
  qemu_binary_source_path      = "/usr/bin/qemu-aarch64-static"
  qemu_binary_destination_path = "/usr/bin/qemu-aarch64-static"
}

# 
# Lakka
# 

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

# 
# RetroPie
# 

source "arm" "retropie_zero_arm" {
  file_urls             = ["https://github.com/RetroPie/RetroPie-Setup/releases/download/4.8/retropie-buster-4.8-rpi1_zero.img.gz"]
  file_checksum         = "95A6F84453DF36318830DE7E8507170E"
  file_checksum_type    = "md5"
  file_target_extension = "gz"
  file_unarchive_cmd    = ["gunzip", "$ARCHIVE_PATH"]
  image_build_method    = "resize"
  image_path            = "PSPi6.RetroPie4-8.Zero.${var.pspi_version}.img"
  image_size            = "4G"
  image_type            = "dos"

  # configure boot partition
  image_partitions {
    name         = "boot"
    type         = "c"
    start_sector = "8192"
    filesystem   = "vfat"
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

source "arm" "retropie_zero2_arm64" {
  file_urls             = ["https://github.com/RetroPie/RetroPie-Setup/releases/download/4.8/retropie-buster-4.8-rpi2_3_zero2w.img.gz"]
  file_checksum         = "224e64d8820fc64046ba3850f481c87e"
  file_checksum_type    = "md5"
  file_target_extension = "gz"
  file_unarchive_cmd    = ["gunzip", "$ARCHIVE_PATH"]
  image_build_method    = "resize"
  image_path            = "PSPi6.RetroPie4-8.Zero2.${var.pspi_version}.img"
  image_size            = "4G"
  image_type            = "dos"

  # configure boot partition
  image_partitions {
    name         = "boot"
    type         = "c"
    start_sector = "8192"
    filesystem   = "vfat"
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

source "arm" "retropie_cm4_arm" {
  file_urls             = ["https://github.com/RetroPie/RetroPie-Setup/releases/download/4.8/retropie-buster-4.8-rpi4_400.img.gz"]
  file_checksum         = "b5daa6e7660a99c246966f3f09b4014b"
  file_checksum_type    = "md5"
  file_target_extension = "gz"
  file_unarchive_cmd    = ["gunzip", "$ARCHIVE_PATH"]
  image_build_method    = "resize"
  image_path            = "PSPi6.RetroPie4-8.CM4.${var.pspi_version}.img.gz"
  image_size            = "4G"
  image_type            = "dos"

  # configure boot partition
  image_partitions {
    name         = "boot"
    type         = "c"
    start_sector = "8192"
    filesystem   = "vfat"
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

# 
# Batocera 
# 

source "arm" "batocera_zero2_arm" {
  file_urls             = ["https://updates.batocera.org/bcm2836/stable/last/batocera-bcm2836-36-20230311.img.gz"]
  file_checksum_url     = "https://mirrors.o2switch.fr/batocera/bcm2836/stable/last/batocera-bcm2836-36-20230311.img.gz.sha256"
  file_checksum_type    = "sha256"
  file_target_extension = "gz"
  file_unarchive_cmd    = ["gunzip", "$ARCHIVE_PATH"]
  image_build_method    = "resize"
  image_path            = "PSPi 6 Batocera 36 Pi Zero 2 ${var.pspi_version}.img.gz" 
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
  image_path            = "PSPi 6 Batocera 36 CM4 ${var.pspi_version}.img.gz"
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

source "arm" "recalbox_cm4_arm64" {
  file_urls             = ["https://upgrade.recalbox.com/latest/download-wizard/rpi4_64/recalbox-rpi4_64.img.xz"]
  file_checksum         = "0346EA505B55EF0D3177A02630D51B4F"
  file_checksum_type    = "md5"
  file_target_extension = "xz"
  file_unarchive_cmd    = ["xz", "--decompress", "$ARCHIVE_PATH"]
  image_build_method    = "resize"
  image_path            = "PSPi6.Recalbox9.1.CM4.${var.pspi_version}.img.gz"
  image_size            = "4G"
  image_type            = "dos"

  # configure boot partition
  image_partitions {
    name         = "boot"
    type         = "c"
    start_sector = "8192"
    filesystem   = "vfat"
    size         = "256M"
    mountpoint   = "/boot"
  }

  # configure root partition
  image_partitions {
    name         = "root"
    type         = "83"
    start_sector = "532480"
    filesystem   = "ext4"
    size         = "0"
    mountpoint   = "/"
  }

  image_chroot_env             = ["PATH=/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin"]

  # qemu binary paths
  qemu_binary_source_path      = "/usr/bin/qemu-aarch64-static"
  qemu_binary_destination_path = "/usr/bin/qemu-aarch64-static"
}

source "arm" "recalbox_zero_arm" {
  file_urls             = ["https://upgrade.recalbox.com/latest/download-wizard/rpi1/recalbox-rpi1.img.xz"]
  file_checksum         = "DC420DB300664567CA89F5D521B916B0"
  file_checksum_type    = "md5"
  file_target_extension = "xz"
  file_unarchive_cmd    = ["xz", "--decompress", "$ARCHIVE_PATH"]
  image_build_method    = "resize"
  image_path            = "PSPi6.Recalbox9.1.Zero.${var.pspi_version}.img.gz"
  image_size            = "4G"
  image_type            = "dos"

  # configure boot partition
  image_partitions {
    name         = "boot"
    type         = "c"
    start_sector = "8192"
    filesystem   = "vfat"
    size         = "256M"
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
  image_build_method    = "resize"
  image_path            = "PSPi6.Recalbox9.1.Zero2.${var.pspi_version}.img.gz"
  image_size            = "4G"
  image_type            = "dos"

  # configure boot partition
  image_partitions {
    name         = "boot"
    type         = "c"
    start_sector = "8192"
    filesystem   = "vfat"
    size         = "256M"
    mountpoint   = "/"
  }

  image_chroot_env             = ["PATH=/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin"]

  # qemu binary paths
  qemu_binary_source_path      = "/usr/bin/qemu-aarch64-static"
  qemu_binary_destination_path = "/usr/bin/qemu-aarch64-static"
}
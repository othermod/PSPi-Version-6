source "arm" "raspios_bookworm_arm64" {
  file_urls             = ["https://downloads.raspberrypi.com/raspios_lite_arm64/images/raspios_lite_arm64-2023-12-11/2023-12-11-raspios-bookworm-arm64-lite.img.xz"]
  file_checksum_url     = "https://downloads.raspberrypi.com/raspios_lite_arm64/images/raspios_lite_arm64-2023-12-11/2023-12-11-raspios-bookworm-arm64-lite.img.xz.sha256"
  file_checksum_type    = "sha256"
  file_target_extension = "xz"
  file_unarchive_cmd    = ["xz", "--decompress", "$ARCHIVE_PATH"]
  image_build_method    = "reuse"
  image_path            = "2023-12-11-raspios-bookworm-arm64-lite.img"
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

build {
  # specify the build source image
  sources = [
    "source.arm.raspios_bookworm_arm64"
  ]

  # install and start cloud init
  provisioner "shell" {
    scripts = [
      "${path.root}usr/local/bin/install-cloud-init.sh"
    ]
  }

  # configure cloud init (datasource)
  provisioner "file" {
    source = "${path.root}etc/cloud/cloud.cfg.d/99_datasource.cfg"
    destination = "/etc/cloud/cloud.cfg.d/99_datasource.cfg"
  }

  # configure cloud init (users)
  provisioner "file" {
    source = "${path.root}etc/cloud/cloud.cfg.d/99_user.cfg"
    destination = "/etc/cloud/cloud.cfg.d/99_user.cfg"
  }

  # set hostname via dhcp
  provisioner "shell" {
    inline = ["echo 'pspi6' > /etc/hostname"]
  }

  # disable file system resize, this is already done by packer
  provisioner "shell" {
    inline = ["rm /etc/init.d/resize2fs_once"]
  }

  # disable the customization dialog, that raspberry pi os will show at boot
  provisioner "shell" {
    inline = ["rm /usr/lib/systemd/system/userconfig.service"]
  }
}
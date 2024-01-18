build {
  # specify the build source image
  sources = [
    # "source.arm.batocera_zero_arm",
    # "source.arm.batocera_zero2_arm64",
    "source.arm.batocera_cm4_arm64"
  ]

  provisioner "shell-local" {
    inline = ["echo waiting for automatic disk resize"]
    pause_before = "1m"
  }

  # Upload config.txt
  provisioner "file" {
    source = "${path.root}/../rpi/configs/batocera.txt"
    destination = "/boot/config.txt"
  }

  # Upload drivers
  provisioner "file" {
    source = "${path.root}/../rpi/drivers/bin/"
    destination = "/boot/drivers"
  }

  # Upload overlays
  provisioner "file" {
    source = "${path.root}/../rpi/overlays/"
    destination = "/boot/overlays"
  }

  # Upload custom.sh
  # provisioner "file" {
  #   source = "${path.root}/../rpi/scripts/batocera/custom.sh"
  #   destination = "/userdata/system/custom.sh"
  # }
}

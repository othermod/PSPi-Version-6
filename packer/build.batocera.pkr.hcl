build {
  # Don't need to build base unless updating its upstream source
  sources = [
    ####
    # "source.arm.batocera_zero_arm_base",
    # "source.arm.batocera_zero2_arm64_base",
    # "source.arm.batocera_cm4_arm64_base",
    ####
    # "source.arm.batocera_zero_arm",
    # "source.arm.batocera_zero2_arm64",
    "arm.batocera.cm4_arm64"
  ]

  # Upload config.txt
  provisioner "file" {
    source = "${path.root}/../rpi/configs/batocera/config.txt"
    destination = "/boot/config.txt"
  }

  # Upload overlays
  provisioner "file" {
    source = "${path.root}/../rpi/overlays/"
    destination = "/boot/overlays"
  }

  # Upload drivers
  provisioner "file" {
    only = [
      "source.arm.batocera_zero_arm", 
      "source.arm.batocera_zero2_arm64", 
      "source.arm.batocera.cm4_arm64"
    ]
    source = "${path.root}/../rpi/drivers/bin/"
    destination = "/boot/drivers"
  }

  # Upload custom.sh
  provisioner "file" {
    only = [
      "source.arm.batocera_zero_arm", 
      "source.arm.batocera_zero2_arm64", 
      "source.arm.batocera.cm4_arm64"
    ]
    source = "${path.root}/../rpi/scripts/batocera/custom.sh"
    destination = "/userdata/system/custom.sh"
  }

  # Upload resize.sh
  provisioner "file" {
    only = [
      "source.arm.batocera_zero_arm", 
      "source.arm.batocera_zero2_arm64", 
      "source.arm.batocera.cm4_arm64"
    ]
    source = "${path.root}/../rpi/scripts/batocera/resize.sh"
    destination = "/userdata/system/resize.sh"
  }
}

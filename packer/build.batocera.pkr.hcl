build {
  name = "batocera"
  # Don't need to build base unless updating its upstream source
  sources = [
    ####
    # "arm.batocera_zero_arm_base",
    # "arm.batocera_zero2_arm64_base",
    # "arm.batocera_cm4_arm64_base",
    ####
    # "arm.batocera_zero_arm",
    # "arm.batocera_zero2_arm64",
    "arm.batocera_cm4_arm64"
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
      "batocera.arm.batocera_zero_arm", 
      "batocera.arm.batocera_zero2_arm64", 
      "batocera.arm.batocera.cm4_arm64"
    ]
    source = "${path.root}/../rpi/drivers/bin/"
    destination = "/boot/drivers"
  }

  # Upload custom.sh
  provisioner "file" {
    only = [
      "batocera.arm.batocera_zero_arm", 
      "batocera.arm.batocera_zero2_arm64", 
      "batocera.arm.batocera.cm4_arm64"
    ]
    source = "${path.root}/../rpi/scripts/batocera/custom.sh"
    destination = "/userdata/system/custom.sh"
  }

  # Upload resize.sh
  provisioner "file" {
    only = [
      "batocera.arm.batocera_zero_arm", 
      "batocera.arm.batocera_zero2_arm64", 
      "batocera.arm.batocera.cm4_arm64"
    ]
    source = "${path.root}/../rpi/scripts/batocera/resize.sh"
    destination = "/userdata/system/resize.sh"
  }

  # Upload multimedia_keys.conf
  provisioner "file" {
    only = [
      "batocera.arm.batocera_zero_arm", 
      "batocera.arm.batocera_zero2_arm64", 
      "batocera.arm.batocera.cm4_arm64"
    ]
    source = "${path.root}/../rpi/configs/batocera/multimedia_keys.conf"
    destination = "/userdata/system/configs/multimedia_keys.conf"
  }
}

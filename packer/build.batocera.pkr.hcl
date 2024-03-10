build {
  name = "batocera"
  # Don't need to build base unless updating its upstream source
  sources = [
    ####
    # "arm.batocera36_zero_arm_base",
    # "arm.batocera36_zero2_arm64_base",
    # "arm.batocera38_cm4_arm64_base",
    # "arm.batocera39_cm4_arm64_base"
    ####
    # "arm.batocera36_zero_arm",
    # "arm.batocera36_zero2_arm64",
    "arm.batocera38_cm4_arm64",
    "arm.batocera39_cm4_arm64"
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
      "arm.batocera36_zero_arm", 
      "arm.batocera36_zero2_arm64", 
      "arm.batocera38_cm4_arm64",
      "arm.batocera39_cm4_arm64"
    ]
    source = "${path.root}/../rpi/drivers/bin/"
    destination = "/boot/drivers"
  }

  # Upload custom.sh
  provisioner "file" {
    only = [
      "arm.batocera36_zero_arm", 
      "arm.batocera36_zero2_arm64", 
      "arm.batocera38_cm4_arm64",
      "arm.batocera39_cm4_arm64"
    ]
    source = "${path.root}/../rpi/scripts/batocera/custom.sh"
    destination = "/userdata/system/custom.sh"
  }

  # Upload resize.sh
  provisioner "file" {
    only = [
      "arm.batocera36_zero_arm", 
      "arm.batocera36_zero2_arm64", 
      "arm.batocera38_cm4_arm64",
      "arm.batocera39_cm4_arm64"
    ]
    source = "${path.root}/../rpi/scripts/batocera/resize.sh"
    destination = "/userdata/system/resize.sh"
  }

  # Upload multimedia_keys.conf
  provisioner "file" {
    only = [
      "arm.batocera36_zero_arm", 
      "arm.batocera36_zero2_arm64", 
      "arm.batocera38_cm4_arm64",
      "arm.batocera39_cm4_arm64"
    ]
    source = "${path.root}/../rpi/configs/batocera/multimedia_keys.conf"
    destination = "/userdata/system/configs/multimedia_keys.conf"
  }
}

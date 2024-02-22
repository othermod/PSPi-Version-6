build {
  name = "lakka"

  # Don't need to build base unless updating its upstream source
  sources = [
    "arm.lakka_zero_zero2_arm",
    "arm.lakka_cm4_arm64"
  ]

  # Upload config.txt
  provisioner "file" {
    source = "${path.root}/../rpi/configs/lakka/config.txt"
    destination = "/boot/config.txt"
  }

  # Upload overlays
  provisioner "file" {
    source = "${path.root}/../rpi/overlays/"
    destination = "/storage/overlays"
  }

  # Upload drivers
  provisioner "file" {
    source = "${path.root}/../rpi/drivers/bin/"
    destination = "/flash/drivers"
  }

  # Upload controller config
  provisioner "file" {
    source = "${path.root}/../rpi/configs/lakka/PSPi-Controller.cfg"
    destination = "/storage/joypads/udev/PSPi-Controller.cfg"
  }

  # Upload resize script
  provisioner "file" {
    source = "${path.root}/../rpi/scripts/lakka/resize.sh"
    destination = "/storage/.config/resize.sh"
  }

  # Upload Autostart Scripts for 32 bit
  provisioner "file" {
    only = [
      "source.arm.lakka_zero_zero2_arm"
    ]
    source = "${path.root}/../rpi/scripts/lakka/autostart_32.sh"
    destination = "/storage/.config/autostart.sh"
  }

  # Upload Autostart Scripts for 64 bit
  provisioner "file" {
    only = [
      "source.arm.lakka_cm4_arm64"
    ]
    source = "${path.root}/../rpi/scripts/lakka/autostart_64.sh"
    destination = "/storage/.config/autostart.sh"
  }
}

build {
  name = "recalbox"
  
  sources = [
    "arm.recalbox_cm4_arm64"
  ]

  # Upload config.txt
  provisioner "file" {
    source = "${path.root}/../rpi/configs/recalbox/config.txt"
    destination = "/boot/config.txt"
  }

  # Upload recalbox-user-config.txt
  provisioner "file" {
    source = "${path.root}/../rpi/configs/recalbox/recalbox-user-config.txt"
    destination = "/boot/recalbox-user-config.txt"
  }  

  # Upload overlays
  provisioner "file" {
    source = "${path.root}/../rpi/overlays/"
    destination = "/boot/overlays"
  }

  # Upload drivers
  provisioner "file" {
    source = "${path.root}/../rpi/drivers/bin/"
    destination = "/boot/drivers"
  }
}

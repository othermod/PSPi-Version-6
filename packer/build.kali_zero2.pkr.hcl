build {
  name = "kali_zero2"

  sources = [
    "arm.kali_zero2_armhf"
  ]

  # Upload config.txt
  provisioner "file" {
    source = "${path.root}/../rpi/configs/kali/config.txt"
    destination = "/boot/config.txt"
  }

  # Upload overlays
  provisioner "file" {
    source = "${path.root}/../rpi/overlays/"
    destination = "/boot/overlays"
  }

  # Upload drivers
  provisioner "file" {
    source = "${path.root}/../rpi/drivers/bin/"
    destination = "/usr/bin/"
  }

  # Upload services
  provisioner "file" {
    source = "${path.root}/../rpi/services/"
    destination = "/etc/systemd/system/"
  }
  
  # Install pspi6 drivers & services
  provisioner "shell" {
    execute_command  = "sudo sh -c '{{ .Vars }} {{ .Path }}'"
    scripts = [
      "${path.root}scripts/installers/install-pspi6.sh"
    ]
    env = {
      "OS" = "Kali"
    }
  }
}

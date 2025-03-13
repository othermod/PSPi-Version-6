build {
  name = "kali_cm4"

  sources = [
    "source.cross.kali_cm4_arm64"
  ]

  # Upload config.txt
  provisioner "file" {
    source = "${path.root}/../rpi/configs/kali/config.txt"
    destination = "/boot/config.txt"
  }

  # Upload cm4.txt
  provisioner "file" {
    source = "${path.root}/../rpi/configs/cm4.txt"
    destination = "/boot/cm4.txt"
  }

  # Upload pi0.txt
  provisioner "file" {
    source = "${path.root}/../rpi/configs/pi0.txt"
    destination = "/boot/pi0.txt"
  }

  # Upload pspi.conf
  provisioner "file" {
    source = "${path.root}/../rpi/configs/pspi.conf"
    destination = "/boot/pspi.conf"
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

  # Upload start_main.sh
  provisioner "file" {
    source = "${path.root}/../rpi/scripts/kali/start_main.sh"
    destination = "/usr/local/bin/start_main.sh"
  }

  # Upload start_osd.sh
  provisioner "file" {
    source = "${path.root}/../rpi/scripts/kali/start_osd.sh"
    destination = "/usr/local/bin/start_osd.sh"
  }

  # Upload start_mouse.sh
  provisioner "file" {
    source = "${path.root}/../rpi/scripts/kali/start_mouse.sh"
    destination = "/usr/local/bin/start_mouse.sh"
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

build {
  name = "kali_zero2"

  sources = [
    "source.cross.kali_zero2_armhf"
  ]

  # Upload config.txt
  provisioner "file" {
    source = "${path.root}/../rpi/configs/kali/config.txt"
    destination = "/boot/config.txt"
  }

  # Upload cm4.txt
  provisioner "file" {
    source = "${path.root}/../rpi/configs/cm4.txt"
    destination = "/boot/cm4.txt"
  }

  # Upload pi0.txt
  provisioner "file" {
    source = "${path.root}/../rpi/configs/pi0.txt"
    destination = "/boot/pi0.txt"
  }

  # Upload pspi.conf
  provisioner "file" {
    source = "${path.root}/../rpi/configs/pspi.conf"
    destination = "/boot/pspi.conf"
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

  # Upload start_main.sh
  provisioner "file" {
    source = "${path.root}/../rpi/scripts/kali/start_main.sh"
    destination = "/usr/local/bin/start_main.sh"
  }

  # Upload start_osd.sh
  provisioner "file" {
    source = "${path.root}/../rpi/scripts/kali/start_osd.sh"
    destination = "/usr/local/bin/start_osd.sh"
  }

  # Upload start_mouse.sh
  provisioner "file" {
    source = "${path.root}/../rpi/scripts/kali/start_mouse.sh"
    destination = "/usr/local/bin/start_mouse.sh"
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
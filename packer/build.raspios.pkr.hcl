build {
  name = "raspios"

  sources = [
    "arm.raspios_cm4_zero2_arm64"
  ]

  # Configure raspberry pi
  provisioner "shell" {
    execute_command  = "sudo sh -c '{{ .Vars }} {{ .Path }}'"
    scripts = [
      "${path.root}scripts/installers/config-pi.sh"
    ]
  }

  # Update OS & Install Dependencies
  provisioner "shell" {
    execute_command  = "sudo sh -c '{{ .Vars }} {{ .Path }}'"
    scripts = [
      "${path.root}scripts/installers/apt.sh"
    ]
  }

  # Reboot
  provisioner "shell" {
    execute_command   = "sudo sh -c '{{ .Vars }} {{ .Path }}'"
    expect_disconnect = true
    inline            = ["echo 'Reboot VM'", "reboot"]
  }

  # Upload config.txt
  provisioner "file" {
    source = "${path.root}/../rpi/configs/raspios/config.txt"
    destination = "/boot/firmware/config.txt"
  }

  # Upload cm4.txt
  provisioner "file" {
    source = "${path.root}/../rpi/configs/cm4.txt"
    destination = "/boot/firmware/cm4.txt"
  }

  # Upload pi0.txt
  provisioner "file" {
    source = "${path.root}/../rpi/configs/pi0.txt"
    destination = "/boot/firmware/pi0.txt"
  }

  # Upload pspi.conf
  provisioner "file" {
    source = "${path.root}/../rpi/configs/pspi.conf"
    destination = "/boot/firmware/pspi.conf"
  }

  # Upload overlays
  provisioner "file" {
    source = "${path.root}/../rpi/overlays/"
    destination = "/boot/firmware/overlays/"
  }

  # Upload libraries
  provisioner "file" {
    source = "${path.root}/../rpi/libraries/raspios/"
    destination = "/usr/lib/"
  }  

  # Upload drivers
  provisioner "file" {
    source = "${path.root}/../rpi/drivers/bin/"
    destination = "/usr/bin/"
  }

  # Upload start_main.sh
  provisioner "file" {
    source = "${path.root}/../rpi/scripts/raspios/start_main.sh"
    destination = "/usr/local/bin/start_main.sh"
  }

  # Upload start_osd.sh
  provisioner "file" {
    source = "${path.root}/../rpi/scripts/raspios/start_osd.sh"
    destination = "/usr/local/bin/start_osd.sh"
  }

  # Upload start_mouse.sh
  provisioner "file" {
    source = "${path.root}/../rpi/scripts/raspios/start_mouse.sh"
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
      "OS" = "Raspios"
    }
  }

  # Reboot
  provisioner "shell" {
    execute_command   = "sudo sh -c '{{ .Vars }} {{ .Path }}'"
    expect_disconnect = true
    inline            = ["echo 'Reboot VM'", "reboot"]
  }

  # disable the customization dialog, that raspberry pi os will show at boot
  provisioner "shell" {
    execute_command  = "sudo sh -c '{{ .Vars }} {{ .Path }}'"
    scripts = [
      "${path.root}scripts/installers/disable-userconfig.sh"
    ]
  }

  # Cleanup
  provisioner "shell" {
    execute_command  = "sudo sh -c '{{ .Vars }} {{ .Path }}'"
    scripts = [
      "${path.root}scripts/installers/cleanup.sh"
    ]
  }
}

build {
  name = "raspios"

  source "source.arm.raspios_zero_arm" {
    name = "zero_arm"
  }
  source "source.arm.raspios_cm4_zero2_arm64" {
    name = "cm4_zero2_arm64"
  }
  # specify the build source image
  # sources = [
  #   "source.arm.raspios_zero_arm",
  #   "source.arm.raspios_cm4_zero2_arm64"
  # ]

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

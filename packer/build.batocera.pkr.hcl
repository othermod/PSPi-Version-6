build {
  # specify the build source image
  sources = [
    # "source.arm.batocera_zero2_arm",
    "source.arm.batocera_cm4_arm64"
  ]

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
  provisioner "file" {
    source = "${path.root}/../rpi/scripts/batocera/custom.sh"
    destination = "/userdata/system/custom.sh"
  }  

  # Install pspi6 drivers & services
  provisioner "shell" {
    execute_command  = "sudo sh -c '{{ .Vars }} {{ .Path }}'"
    scripts = [
      "${path.root}scripts/installers/install-pspi6.sh"
    ]
    env = {
      "OS" = "Batocera"
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
    only = [
      "source.arm.raspios_zero_arm",
      "source.arm.raspios_cm4_zero2_arm64"
    ]

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

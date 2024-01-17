build {
  # specify the build source image
  sources = [
    "source.arm.raspios_zero_arm",
    "source.arm.raspios_cm4_zero2_arm64",
    # "source.arm.lakka_zero_arm",
    # "source.arm.lakka_cm4_arm64",
    "source.arm.retropie_zero_arm",
    "source.arm.retropie_zero2_arm"
    "source.arm.retropie_cm4_arm"
    # "source.arm.batocera_zero2_arm",
    # "source.arm.batocera_cm4_arm64"
  ]

  # Configure raspberry pi
  provisioner "shell" {
    execute_command  = "sudo sh -c '{{ .Vars }} {{ .Path }}'"
    scripts = [
      "${path.root}scripts/installers/config-pi.sh"
    ]
  }

  provisioner "shell" {
    execute_command   = "sudo sh -c '{{ .Vars }} {{ .Path }}'"
    expect_disconnect = true
    inline            = ["echo 'Reboot VM'", "reboot"]
  }

  # 
  provisioner "shell" {
    execute_command  = "sudo sh -c '{{ .Vars }} {{ .Path }}'"
    scripts = [
      "${path.root}scripts/installers/apt.sh"
    ]
  }

  provisioner "shell" {
    execute_command = "sudo sh -c '{{ .Vars }} {{ .Path }}'"
    inline          = [
      "mkdir ${var.packer_folder}", 
      "chmod 777 ${var.packer_folder}"
    ]
  }

  # Upload pspi6 installer & config files
  provisioner "file" {
    source = "${path.root}/../rpi"
    destination = "${var.temp_folder}"
  }

  # Install pspi6 drivers & services
  provisioner "shell" {
    execute_command  = "sudo sh -c '{{ .Vars }} {{ .Path }}'"
    scripts = [
      "${path.root}scripts/installers/install-pspi6.sh"
    ]
  }

  # disable the customization dialog, that raspberry pi os will show at boot
  provisioner "shell" {
    only = [
      "source.arm.raspios_pizero_arm",
      "source.arm.raspios_cm4_arm64"
    ]

    execute_command  = "sudo sh -c '{{ .Vars }} {{ .Path }}'"
    scripts = [
      "${path.root}scripts/installers/disable-userconfig.sh"
    ]
  }

  # disable the customization dialog, that raspberry pi os will show at boot
  provisioner "shell" {
    execute_command  = "sudo sh -c '{{ .Vars }} {{ .Path }}'"
    scripts = [
      "${path.root}scripts/installers/cleanup.sh"
    ]
  }  
}

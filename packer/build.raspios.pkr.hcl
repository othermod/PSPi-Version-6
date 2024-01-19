build {
  # specify the build source image
  sources = [
    "source.arm.raspios_zero_arm",
    "source.arm.raspios_cm4_zero2_arm64"
  ]

  # Configure raspberry pi
  provisioner "shell" {
    execute_command  = "sudo sh -c '{{ .Vars }} {{ .Path }}'"
    scripts = [
      "${path.root}scripts/installers/config-pi.sh"
    ]
  }

  # Reboot
  provisioner "shell" {
    execute_command   = "sudo sh -c '{{ .Vars }} {{ .Path }}'"
    expect_disconnect = true
    inline            = ["echo 'Reboot VM'", "reboot"]
  }

  # Update OS & Install Dependencies
  provisioner "shell" {
    execute_command  = "sudo sh -c '{{ .Vars }} {{ .Path }}'"
    scripts = [
      "${path.root}scripts/installers/apt.sh"
    ]
  }

  # Create upload folder
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

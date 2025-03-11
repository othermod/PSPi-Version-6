build {
  name = "drivers"

  sources = [
    "source.cross.drivers_raspios_lite_arm64"
  ]

  # Create /packer directory
  provisioner "shell" {
    execute_command = "sudo sh -c '{{ .Vars }} {{ .Path }}'"
    inline          = ["mkdir /packer", "chmod 777 /packer"]
  }

  # Upload driver source
  provisioner "file" {
    source      = "${path.root}/../rpi/drivers/"
    destination = "/packer/drivers/"
  }

  # Build drivers
  provisioner "shell" {
    execute_command  = "sudo sh -c '{{ .Vars }} {{ .Path }}'"
    scripts = [
      "${path.root}scripts/installers/build-drivers.sh"
    ]
  }
}
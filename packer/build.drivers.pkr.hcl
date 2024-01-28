build {
  name = "drivers"

  sources = [
    # "arm.drivers_32bit",
    "arm.drivers_64bit"
  ]

  provisioner "shell" {
    execute_command = "sudo sh -c '{{ .Vars }} {{ .Path }}'"
    inline          = ["mkdir /packer", "chmod 777 /packer"]
  }

  # Upload drivers
  provisioner "file" {
    source      = "${path.root}/../rpi/drivers/"
    destination = "/packer/drivers/"
  }

  # Build Drivers
  provisioner "shell" {
    execute_command  = "sudo sh -c '{{ .Vars }} {{ .Path }}'"
    scripts = [
      "${path.root}scripts/installers/build-drivers.sh"
    ]
  }
}
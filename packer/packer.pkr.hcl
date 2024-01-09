packer {
  required_plugins {
    arm = {
      version = ">= 1.0.1"
      source = "github.com/mkaczanowski/packer-builder-arm"
    }
  }
}
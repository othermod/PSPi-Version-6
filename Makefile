# Builds every PSPi component inside the toolchain container (see Dockerfile),
# so the only host requirement is docker or podman. Outputs land in out/, laid
# out like the CI pspi-driver-binaries artifact that scripts/patcher.sh
# consumes via --driver-binaries.
#
#   make                  build everything
#   make gamepad lcd      build specific components
#   make shell            open a shell in the build container
#   make clean
#
# Uses docker if installed, otherwise podman; override with CONTAINER_ENGINE.
# SKIP_IMAGE=1 skips building the container image (CI builds it separately
# with layer caching). NATIVE=1 builds with the host's own toolchain instead
# of the container; the container invocation sets it too.

BINARIES := gamepad battery rtc firmware troubleshooter
OVERLAYS := audio lcd pcie
TARGETS  := $(BINARIES) $(OVERLAYS) atmega
OUT      := out

.PHONY: all clean image shell $(TARGETS)

ifndef NATIVE

CONTAINER_ENGINE ?= $(shell command -v docker || command -v podman)
ifeq ($(CONTAINER_ENGINE),)
$(error Neither docker nor podman found; install one to build)
endif
IMAGE    ?= pspi-builder
# Pinned so builds are identical on arm64 hosts (eg. Apple Silicon)
PLATFORM := linux/amd64

# Run as the invoking user so outputs aren't owned by root. Rootless podman
# needs keep-id; docker and rootful podman take an explicit --user. Only
# podman's `info` has this field, so a docker -> podman shim is handled too.
ifeq ($(shell $(CONTAINER_ENGINE) info --format '{{.Host.Security.Rootless}}' 2>/dev/null),true)
RUN_USER := --userns=keep-id
else
RUN_USER := --user $(shell id -u):$(shell id -g)
endif

RUN := $(CONTAINER_ENGINE) run --rm $(RUN_USER) --platform $(PLATFORM) \
       -v "$(CURDIR)":/src:z $(IMAGE)

ifndef SKIP_IMAGE
IMAGE_DEP := image
endif

all $(TARGETS) clean: $(IMAGE_DEP)
	$(RUN) make $@ NATIVE=1

shell: $(IMAGE_DEP)
	$(CONTAINER_ENGINE) run --rm -it $(RUN_USER) --platform $(PLATFORM) \
		-v "$(CURDIR)":/src:z -e NATIVE=1 $(IMAGE) bash

image:
	$(CONTAINER_ENGINE) build --platform $(PLATFORM) -t $(IMAGE) .

else # native build, on the host or inside the container

all: $(TARGETS)

$(BINARIES):
	$(MAKE) -C rpi/$@ 32 64
	rm -rf $(OUT)/$@ && mkdir -p $(OUT)/$@
	cp -r rpi/$@/32 rpi/$@/64 $(OUT)/$@/

$(OVERLAYS):
	$(MAKE) -C rpi/$@
	rm -rf $(OUT)/$@ && mkdir -p $(OUT)/$@
	cp rpi/$@/*.dtbo $(OUT)/$@/

# Cleaned first: the atmega makefiles only track source timestamps, so objects
# left from a build with another toolchain or Arduino core would be reused
atmega:
	$(MAKE) -C atmega clean
	$(MAKE) -C atmega all
	rm -rf $(OUT)/atmega-firmware && mkdir -p $(OUT)/atmega-firmware
	cp atmega/firmware/firmware.hex atmega/bootloader/bootloader.hex \
	   atmega/combined.hex $(OUT)/atmega-firmware/

clean:
	for dir in $(BINARIES) $(OVERLAYS); do $(MAKE) -C rpi/$$dir clean; done
	$(MAKE) -C atmega clean
	rm -rf $(OUT)

endif

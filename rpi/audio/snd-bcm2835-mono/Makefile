# Out-of-tree build of the snd-bcm2835 mono-downmix module.
#
# Upstream source is fetched and patched at build time. Nothing is vendored.
# Requires git and patch on the build machine.
#
# Inputs (normally supplied by PSPi-6-Audio-Modules/build.sh, but settable by hand):
#   UPSTREAM_COMMIT   exact raspberrypi/linux commit matching the target kernel
#   KDIR              prepared kernel build tree (headers or full source +
#                     modules_prepare) whose vermagic matches the target
#   ARCH              target arch (arm64/arm), empty for native
#   CROSS_COMPILE     toolchain prefix, empty for native
#   KBUILD_MODPOST_WARN  1 to tolerate the missing Module.symvers that is
#                     normal when building against a prepared-only tree
#                     (safe when the target has CONFIG_MODVERSIONS off)

UPSTREAM_REPO   ?= https://github.com/raspberrypi/linux
UPSTREAM_PATH   := drivers/staging/vc04_services

# The whole vc04_services tree is taken so the driver's relative includes
# of the vchiq headers resolve without any copies.
SPARSE_PATHS    := $(UPSTREAM_PATH)

SRC          := upstream/$(UPSTREAM_PATH)/bcm2835-audio
KBUILD_MODPOST_WARN ?= 1
MODPOST_ENV  := KBUILD_MODPOST_WARN=$(KBUILD_MODPOST_WARN)

# obj-m += snd-bcm2835.o and its component objects, written into the
# fetched tree as Kbuild so `make M=...` builds the right module.
KBUILD_LINE   := obj-m += snd-bcm2835.o
KBUILD_EXTRA  := snd-bcm2835-y := bcm2835.o bcm2835-ctl.o bcm2835-pcm.o bcm2835-vchiq.o

KO := $(SRC)/snd-bcm2835.ko

all: $(KO)

$(KO): upstream/.patched
	$(MODPOST_ENV) $(MAKE) -C $(KDIR) ARCH=$(ARCH) CROSS_COMPILE=$(CROSS_COMPILE) \
		M=$(CURDIR)/$(SRC) modules

# Blobless, shallow, sparse fetch of the driver directory at the pinned commit.
upstream/.fetched:
	rm -rf upstream
	git init -q upstream
	cd upstream && \
	  git remote add origin $(UPSTREAM_REPO) && \
	  git fetch -q --depth 1 --filter=blob:none origin $(UPSTREAM_COMMIT) && \
	  git sparse-checkout init --cone && \
	  git sparse-checkout set $(SPARSE_PATHS) && \
	  git checkout -q FETCH_HEAD
	touch $@

upstream/.patched: upstream/.fetched mono_mix.patch
	cd upstream && git checkout -q -- $(UPSTREAM_PATH)
	cd upstream && patch -p1 -s < $(CURDIR)/mono_mix.patch
	printf '%s\n%s\n' '$(KBUILD_LINE)' '$(KBUILD_EXTRA)' > $(SRC)/Kbuild
	touch $@

# Print the vermagic the built module will carry, for comparison against
# the target's `modinfo -F vermagic`. Reads from the prepared KDIR.
vermagic:
	@$(MAKE) -sC $(KDIR) ARCH=$(ARCH) kernelrelease 2>/dev/null || \
	  grep -h UTS_RELEASE $(KDIR)/include/generated/utsrelease.h 2>/dev/null || \
	  echo "KDIR not prepared: $(KDIR)"

clean:
	@test -d $(SRC) && $(MAKE) -C $(KDIR) ARCH=$(ARCH) CROSS_COMPILE=$(CROSS_COMPILE) \
		M=$(CURDIR)/$(SRC) clean || true
	rm -f upstream/.patched

distclean: clean
	rm -rf upstream

.PHONY: all clean distclean vermagic

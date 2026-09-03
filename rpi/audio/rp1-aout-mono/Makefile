# Out-of-tree build of the rp1_aout mono-downmix module (CM5 / RP1 audio).
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
UPSTREAM_PATH   := sound/soc/raspberrypi

SRC          := upstream/$(UPSTREAM_PATH)
KBUILD_MODPOST_WARN ?= 1
MODPOST_ENV  := KBUILD_MODPOST_WARN=$(KBUILD_MODPOST_WARN)

KBUILD_LINE  := obj-m += rp1_aout.o

KO := $(SRC)/rp1_aout.ko

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
	  git sparse-checkout set $(UPSTREAM_PATH) && \
	  git checkout -q FETCH_HEAD
	touch $@

upstream/.patched: upstream/.fetched mono_mix.patch
	cd upstream && git checkout -q -- $(UPSTREAM_PATH)
	cd upstream && patch -p1 -s < $(CURDIR)/mono_mix.patch
	printf '%s\n' '$(KBUILD_LINE)' > $(SRC)/Kbuild
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

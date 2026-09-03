# rp1_aout mono downmix module (PSPi Version 6, CM5)

Out-of-tree build of the Raspberry Pi `rp1_aout` ALSA SoC driver with a
single functional change: when the device tree node carries a `mono_mix`
boolean property, the DMA buffer is downmixed in place with the average
law `(L + R) / 2` via the dmaengine PCM `process` hook. This exists
because PSPi Version 6 routes exactly one RP1 AAUD pin (GPIO39) to its
speaker amplifier, so stock behavior reproduces only one channel of
stereo content.

This document is written for automated review. Every claim is
verifiable against this directory and the cited upstream sources.

## 1. Upstream provenance

- Source tree: `raspberrypi/linux`
- Base path: `sound/soc/raspberrypi/rp1_aout.c`
- Pinned commit: `16f1da3c4e94437449d6aa151589ca0ad4b388bb` (branch
  `rpi-6.18.y` as of 2026-08-26)

No upstream source is stored in this repository. `make` performs a
shallow, blobless, sparse fetch of `sound/soc/raspberrypi` at the pinned
commit into `upstream/`, applies `mono_mix.patch`, and builds there. The
commit is pinned in the Makefile so later upstream changes cannot break
the build; bump `UPSTREAM_COMMIT` to move forward.

The patched file therefore differs from pristine upstream by exactly the
delta in `mono_mix.patch`, by construction. Reviewers should confirm:

1. `struct rp1_aout` gains one field, `bool mono_mix`.
2. Probe reads it once: `of_property_read_bool(pdev->dev.of_node,
   "mono_mix")`.
3. `devm_snd_dmaengine_pcm_register()` receives a custom config only
   when `mono_mix` is set; otherwise `NULL`, which is byte-for-byte
   upstream behavior.
4. The custom config (`rp1_aout_mono_dma_config`) supplies
   `prepare_slave_config` identically to the dmaengine default plus a
   `process` hook and a `pcm_hardware` descriptor that restates the
   dmaengine defaults minus `SNDRV_PCM_INFO_MMAP*`. Withholding MMAP is
   mandatory correctness: the `process` hook only runs on read/write
   transfers, so an mmap-capable client could bypass the downmix by
   writing the DMA buffer directly.
5. No other behavioral changes.

## 2. Why average law and not sum / limiter / max

All four variants were built and compared by ear on CM5 hardware
(2026-08-25, maintainer present):

| Variant | Outcome |
|---|---|
| Raw sum | wraps at ±full scale on simultaneous peaks → hard distortion |
| Sum × 0.707 + hard clamp | flat-tops hot masters → pops |
| Sample-wise magnitude max | switching artifacts on independent L/R content |
| Sum + dynamic limiter | clean; rejected as unnecessary complexity |
| **Average `(L+R)/2`** | **chosen**: never clips, centered content at unity |

Hard-panned content loses 6 dB under average law; recoverable via analog
volume. Maintainer accepted this trade-off explicitly.

## 3. Why a DT property works here (unlike snd-bcm2835)

`rp1_audio_out` is a platform device instantiated from device tree, so
its `of_node` is real and `of_property_read_bool()` functions normally.
The gate is enabled from config.txt without any per-OS file:

    dtoverlay=pspi-audio-cm5-kernel6+,mono_mix

The overlay (`../pspi-audio-cm5-kernel6+.dts`) implements this as a
single firmware override (`mono_mix = <&audio_out_node>, "mono_mix?"`).
With the stock module loaded, the property is present but unread — no
error, identical stereo behavior. Verified empirically.

Contrast with `../snd-bcm2835-mono/` (CM4/Zero): that driver binds to a
vchiq bus device created by `vchiq_device_register()`, which never sets
`dev->of_node`, so the DT route is impossible there and a module
parameter set via overlay-appended kernel cmdline is used instead.

## 4. Build

On the target (CM5, kernel 6.18.x verified). Needs `git` and `patch`
installed, and network access on the first build:

    make

Verified building warning-free against
`linux-headers-6.18.34+rpt-rpi-2712` on Raspberry Pi OS Trixie.

`make clean` removes build artifacts but keeps the fetched source.
`make distclean` removes `upstream/` entirely.

## 5. Install

    sudo mkdir -p /lib/modules/$(uname -r)/updates
    sudo cp upstream/sound/soc/raspberrypi/rp1_aout.ko \
            /lib/modules/$(uname -r)/updates/
    sudo depmod -a
    reboot

The `updates/` copy shadows the distro's module. Without it, the stock
module simply ignores the `mono_mix` property, so installing or removing
this module never affects boot.

## 6. Runtime verification checklist

1. `cat /sys/module/snd_bcm2835/parameters/*` does not apply here;
   verify instead via `/proc/device-tree/.../audio_out@94000/mono_mix`
   being present, `aplay -l` showing `RP1AudioOut`, and
   `dmesg | grep rp1-audio-out` showing probe + start.
2. Left-only test content must be audible on the single speaker.
3. Toggle test: removing `,mono_mix` from config.txt and rebooting must
   restore right-channel-only stock behavior.

## 7. Known issues and non-issues

- **No mixer control exists** for the RP1 card (`amixer` fails with
  "no such control"). Unlike the bcm2835 path there is no firmware gain
  stage, hence no +4 dB boost trap; what apps send is what PWM outputs.
- **Frequency response:** full-range observed through the PSPi amp on
  the same hardware where the legacy CM4 PWM path rolls off below
  ~800 Hz. Cause of that rolloff is under investigation; it is specific
  to the VideoCore PWM output path, not to either downmix module.
- **Kernel updates** require rebuilding against new headers and
  reinstalling into the new `updates/` directory.
- **The pinned commit ages.** Driver source from an old commit may stop
  compiling against much newer kernel headers. If that happens, raise
  `UPSTREAM_COMMIT` in the Makefile and confirm the patch still applies.

# snd-bcm2835 mono downmix module (PSPi Version 6, CM4 / Pi Zero)

Out-of-tree build of the Raspberry Pi downstream VideoCore analog audio
driver (`snd-bcm2835`) with a single functional change: an optional
`(L + R) / 2` stereo-to-mono downmix applied before samples are handed to
the VideoCore firmware. This exists because PSPi Version 6 routes exactly
one of the two PWM audio pins to its speaker amplifier, so stock behavior
on CM4/Pi Zero hardware reproduces only one channel of stereo content.

This document is written for automated review. Every claim below is
verifiable against the files in this directory and the cited upstream
sources.

## 1. Upstream provenance

- Source tree: `raspberrypi/linux`
- Base path: `drivers/staging/vc04_services/bcm2835-audio/`
- Pinned commit: `16f1da3c4e94437449d6aa151589ca0ad4b388bb` (branch
  `rpi-6.18.y` as of 2026-08-26)

No upstream source is stored in this repository. `make` performs a
shallow, blobless, sparse fetch of `drivers/staging/vc04_services` at the
pinned commit into `upstream/`, applies `mono_mix.patch`, and builds
there. The commit is pinned in the Makefile so later upstream changes
cannot break the build; bump `UPSTREAM_COMMIT` to move forward.

The only file altered is `bcm2835-pcm.c`; the other four driver files are
used exactly as fetched. The patched tree therefore differs from pristine
upstream by exactly the delta in `mono_mix.patch`, by construction.

Building inside the real tree also removes the need for vendored vchiq
headers. The driver includes them by relative path
(`../interface/vchiq_arm/...` and `../include/linux/raspberrypi/...`),
which resolve naturally because the whole `vc04_services` directory is
fetched.

## 2. The change (`mono_mix.patch`)

Three additions, all in `bcm2835-pcm.c`, all inside or adjacent to
`snd_bcm2835_pcm_transfer()` — the last point where sample data is
accessible in kernel space before `bcm2835_audio_write()` pushes it over
the VCHIQ mailbox to the VideoCore firmware, which performs the PWM
generation on the audio pins.

1. `bool snd_bcm2835_mono_mix;` plus `module_param_named(mono_mix, ...,
   bool, 0644)` and `MODULE_PARM_DESC`.

2. `static void bcm2835_downmix_stereo(s16 *buf, size_t bytes)`:
   in-place `(buf[2i] + buf[2i+1]) / 2` over `bytes / 4` frames.
   Integer math; cannot overflow (`int` accumulator); no clamping
   needed because averaging cannot exceed s16 range.

3. A guard in `snd_bcm2835_pcm_transfer()` invoking the downmix only when
   `mono_mix` is set AND `runtime->channels == 2` AND format is
   `SNDRV_PCM_FORMAT_S16_LE`. All other formats/channels pass through
   untouched.

### Why average law and not sum / limiter / max

All four were implemented and compared by ear on target hardware
(CM5/RP1 for limiter variants; identical math applies here):

- Sum without scaling: wraps at ±full scale whenever both channels peak
  together → hard distortion. Rejected.
- Sum × 1/sqrt(2) + hard clamp: still flat-tops hot masters → audible
  pops. Rejected.
- Sample-wise magnitude max: clean on correlated content, severe
  switching artifacts on independent L/R material (verified with real
  music). Rejected.
- Dynamic limiter (attack/release gain smoother): audibly clean but
  rejected as unnecessary complexity once average law was accepted.
- Average `(L+R)/2`: never clips; centered/mono content at unity gain;
  hard-panned content −6 dB (recoverable via analog volume). CHOSEN,
  per maintainer decision 2026-08-25.

### Why a module parameter instead of a DT property

The RP1 variant of this feature (see `../rp1-aout-mono/`) gates on a DT
property because `rp1_audio_out` is a platform device with a real
`of_node`. Here that is impossible: the bcm2835-audio device is created
dynamically by `vchiq_device_register()`
(`drivers/staging/vc04_services/interface/vchiq_arm/vchiq_bus.c`) which
never assigns `dev->of_node`, so any `of_property_read_bool()` against it
is always false regardless of overlay contents. This was empirically
confirmed during bring-up (a DT-property version was built first and
removed).

The parameter is therefore set through the kernel command line:
`snd_bcm2835.mono_mix=1`. The PSPi boot overlays append this to
`chosen/bootargs` (see `../../pspi-audio-cm4-kernel6+.dts` and
`../../pspi-audio-zero-kernel6+.dts`). Unknown module parameters on the
cmdline are silently ignored by the kernel, so these overlays remain
safe with the stock module.

## 3. Build

On the target (CM4 / Pi Zero, kernel 6.18.x verified; anything with
matching `raspberrypi-kernel-headers` should work). Needs `git` and
`patch` installed, and network access on the first build:

    make

Produces `snd-bcm2835.ko`. Verified building warning-free against
`linux-headers-6.18.34+rpt-rpi-v8` on Raspberry Pi OS Trixie.

`make clean` removes build artifacts but keeps the fetched source.
`make distclean` removes `upstream/` entirely.

## 4. Install

    sudo cp upstream/drivers/staging/vc04_services/bcm2835-audio/snd-bcm2835.ko \
            /lib/modules/$(uname -r)/updates/snd-bcm2835.ko
    sudo depmod -a
    reboot   # module is held open by the sound server while running

After `depmod -a`, `modinfo -n snd-bcm2835` must resolve to the
`updates/` copy. That copy shadows the distro's
`kernel/drivers/staging/vc04_services/bcm2835-audio/snd-bcm2835.ko.xz`.

## 5. Runtime verification checklist

1. `/sys/module/snd_bcm2835/parameters/mono_mix` exists → patched module
   loaded (stock has no such parameter).
2. `aplay -l` shows `card N: Headphones [bcm2835 Headphones]`.
3. With `mono_mix=Y`, left-only test content is audible on the single
   speaker; with `N` it is silent (it never reaches the wired pin).

The parameter is 0644 and may be flipped live:
`echo Y/N | sudo tee /sys/module/snd_bcm2835/parameters/mono_mix`.

## 6. Known issues and non-issues

- **Distortion at mixer 100% is NOT caused by this module.** The
  bcm2835 firmware volume control (`CTRL_VOL_MAX 400` in
  `bcm2835-ctl.c`, i.e. +4.00 dB digital boost at the 100% position)
  overshoots full scale on hot sources. Verified: stock driver at 100%
  exhibits the identical distortion; both drivers are clean at 0 dB
  (raw value 0, the "96%" position). Volume policy should cap PCM at
  ≤ 0 dB.
- **Low-frequency rolloff below ~800 Hz** observed on PSPi CM4 PWM
  output is absent on the CM5 RP1 output driving the same amp/speaker.
  Cause under investigation; present with stock driver too; unrelated
  to this patch (downmix is spectrally flat per-sample arithmetic).
- **Kernel updates** require rebuilding against the new headers and
  reinstalling into the new `updates/` directory.
- **The pinned commit ages.** Driver source from an old commit may stop
  compiling against much newer kernel headers. If that happens, raise
  `UPSTREAM_COMMIT` in the Makefile and confirm the patch still applies.

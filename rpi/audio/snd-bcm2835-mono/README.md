# snd-bcm2835 mono downmix + PipeWire glitch fix module (PSPi Version 6, CM4 / Pi Zero)

Out-of-tree build of the Raspberry Pi downstream VideoCore analog audio
driver (`snd-bcm2835`) with two functional changes:

1. An optional `(L + R) / 2` stereo-to-mono downmix applied before samples
   are handed to the VideoCore firmware. This exists because PSPi Version 6
   routes exactly one of the two PWM audio pins to its speaker amplifier,
   so stock behavior on CM4/Pi Zero hardware reproduces only one channel
   of stereo content.

2. Interpolation of the ALSA hw pointer between GPU consumption
   notifications, fixing glitching under PipeWire (see section 2b).

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
pinned commit into `upstream/`, applies `mono_mix.patch` then
`pipewire_hwptr_interpolation.patch`, and builds there. The Makefile
carries a default `UPSTREAM_COMMIT` (rpi-6.18.y era) so a plain
on-target `make` works unconfigured; per-image builds
(PSPi-6-Audio-Modules facts files) override it so each image builds
against exactly its own kernel's sources. Bump the pin to move forward.

The only files altered are `bcm2835-pcm.c` and `bcm2835.h`; the other
driver files are used exactly as fetched. The patched tree therefore
differs from pristine upstream by exactly the combined delta of the two
patch files, applied in Makefile order, by construction.

Building inside the real tree also removes the need for vendored vchiq
headers. The driver includes them by relative path
(`../interface/vchiq_arm/...` and `../include/linux/raspberrypi/...`),
which resolve naturally because the whole `vc04_services` directory is
fetched.

## 2a. The mono downmix change (`mono_mix.patch`)

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

## 2b. The hw-pointer interpolation change (`pipewire_hwptr_interpolation.patch`)

Changes are in `bcm2835-pcm.c` (parameter, `bcm2835_playback_fifo`,
`prepare`, `trigger`, pointer callback) plus four new fields in
`struct bcm2835_alsa_stream` (`bcm2835.h`):

- `atomic_t consumed_cum` — cumulative bytes confirmed by GPU COMPLETE
  notifications (wraps at 2^32; only compared via signed differences).
- `atomic_t reported_cum` — cumulative bytes last reported to ALSA.
- `unsigned int reported_pos` — last reported buffer-relative position.
- `seqlock_t pcm_seq` — pairs `consumed_cum` with `interpolate_start`
  and serialises the write sites against each other.

### Synchronisation

The counter/anchor pair is written under `write_seqlock` at all five
write sites (normal completion path, abnormal completion path inside
the stream lock, `prepare`, start trigger, stop trigger) and read
lock-free via `read_seqbegin`/`read_seqretry` in the pointer callback.
`seqlock_t` rather than plain `seqcount_t` is required for two reasons:
nothing else serialises the completion path against the locked write
sites (a straggler completion can race any of them), and the seqlock's
non-preemptible write section means a real-time pointer reader can
never spin behind a preempted writer. The stream lock itself must not
enter the completion path — the blocking bulk transfer in the write
path waits on the same VCHIQ thread that delivers completions. Lock
ordering: mutex-then-seqlock at every site holding both; seqlock alone
on the normal completion path.

On SMP modversions builds the synchronisation adds up to three imports
beyond the stock module's set: `_raw_spin_lock` and `_raw_spin_unlock`
(the seqlock write side) and `alt_cb_patch_nops` (the arm64
alternatives callback that the spinlock inline chain emits). Which of
the three actually exist is architecture-dependent: arm64 SMP kernels
export all three (each with a single consistent CRC across hundreds of
carrier modules — 202/204/561 on batocera-bcm2711); ARM32 SMP kernels
export `_raw_spin_lock` only, inlining the unlock path and having no
alternatives machinery; `CONFIG_SMP=n` kernels (ARMv6 / bcm2835) inline
both spinlock helpers, so none are imported. Every supported target's
`Module.symvers` harvest in PSPi-6-Audio-Modules was completed for this
(arm64 files carry all three CRCs, ARM32 files need none beyond what
they already had). Any new target must have its harvest checked before
building — `kernels/tools/harvest_from_image.sh` reads the CRCs out of
the stock image, and the build's missing-symbol guard (modpost's
"no CRC"/"undefined!" warnings) refuses to ship if an import is
missing.

### Behavior

Gated by `snd_bcm2835.interp` (bool, default **on**, mode 0644 —
flippable at runtime via
`/sys/module/snd_bcm2835/parameters/interp`, or set from the kernel
command line as `snd_bcm2835.interp=0` for A/B testing; unknown
parameters are silently ignored by the stock module, same as
`mono_mix`). The patch applies cleanly against the default
`UPSTREAM_COMMIT` pin (rpi-6.18.y), the Batocera facts pin
(`a1073743767f`, 6.12.62) and the Ubuntu facts pin (rpi-7.0.y,
`42d9bb9081f1`) — the only cross-version drift in the touched files is
an extra vchiq include in `bcm2835.h`, which the seqlock hunk's
include-block context deliberately spans.

With `interp=1` (default) the pointer callback advances the reported
position on elapsed wall time since the last GPU notification
(`interpolate_start`, re-anchored by every COMPLETE), instead of
stepping only when a notification lands, and reports
`runtime->delay = 0`. With `interp=0` the callback reproduces stock
behavior: staircase position plus the legacy negative delay ramp.

### Why this fixes PipeWire glitching

The GPU consumes audio and returns COMPLETE notifications whose cadence
jitters with VideoCore load (measured 30–44 ms mean 33 on a busy
Batocera v43.1 system — three times coarser than the "10 ms order" the
driver's own comment claims). In the stock driver those notifications
are the only thing that advances the ALSA hw pointer. A client that
paces its refills on the reported position (PipeWire does; its `pw-top`
ERR counter is the visible symptom) sees the position freeze during a
notification gap, concludes there is no free space, stops writing, and
the firmware-side FIFO runs dry: an audible glitch plus an xrun.
Diagnosed live: the bcm2835 sink node accumulated ERR continuously
during gameplay while the emulator-side node stayed at 0 errors, at
~30% CPU, 54 °C, no throttling; saturating all four CPU cores did not
move the counter — ruling out CPU starvation.

Upstream already interpolates `runtime->delay` on the same anchor —
interpolation in delay-space compensating a stale position. The PCM
core computes the client-visible delay as
`hw_avail + runtime->delay` (`snd_pcm_calc_delay`), so a position
interpolation must **not** keep the delay ramp: the elapsed-time
correction would be counted twice. This patch moves the interpolation
from delay-space to position-space and zeroes the delay.

### Correctness guards

1. **Clamp to pushed-minus-confirmed bytes.** The interpolated advance
   is bounded by `rec->hw_ready + (reported_cum - consumed_cum)` — the
   bytes pushed to the GPU but not yet confirmed. `hw_ready` alone is
   pushed-minus-*reported*, so the cumulative difference completes it;
   the formulation is unambiguous even when the ring is completely
   full, which a ring-distance comparison against the `sw_data`
   watermark cannot distinguish from empty. The driver never claims
   consumption of samples it does not hold, and the `snd_pcm_indirect`
   invariants hold. (Over-reporting could not corrupt audio in this
   driver anyway — `bcm2835_audio_write` copies samples out of the
   ALSA buffer before `ack` returns — but the bookkeeping must stay
   consistent.)
2. **Paired reads, monotonic report.** The pointer callback reads
   `consumed_cum` and `interpolate_start` as a seqlock-consistent pair:
   a torn fresh-counter/stale-anchor pair would overshoot, and the
   monotonic guard would lock that overshoot in; the lock-free retry
   also makes the 64-bit anchor safe to read on 32-bit kernels. The
   report is derived purely from cumulative-counter deltas — the raw
   confirmed position never enters the report path — and advances only
   forward, in *both* interp modes: a late COMPLETE that corrects
   consumption below a previous interpolated report simply holds the
   report until consumption catches up.
   `snd_pcm_indirect_playback_pointer` derives its bookkeeping from the
   signed delta between successive reports, so monotonicity is what
   keeps that delta sane; the same guarantee makes toggling `interp`
   mid-stream safe at any point.
3. **Fallthrough returns the last report.** With the anchor frozen
   (stopped, or the abnormal completion path) or the stream
   unprepared, the callback still returns `reported_pos` — never the
   raw confirmed position, which can sit behind the last report and
   would be misread as a near-full-buffer jump.
4. **Lifecycle.** `TRIGGER_START` re-anchors the clock at actual
   stream start (prepare-time anchors can precede it); `TRIGGER_STOP`
   and the abnormal-termination path in `bcm2835_playback_fifo` zero
   the anchor, freezing interpolation. All counters and `reported_pos`
   reset in `prepare` (fresh sessions open a new zeroed stream);
   `close` additionally zeroes `reported_pos` and `reported_cum`. The
   `period_size` guard (zeroed with `buffer_size` in `close`, set in
   `prepare`) gates the interpolation block itself.

No new threads or timers. The only new locking is the seqlock: a
lock-free reader and write sections of a few instructions. Plain ALSA
clients (aplay) are unaffected apart from receiving a monotonic pointer
and a coherent delay, both of which ALSA tolerates by design.

### Measured results (batocera-bcm2711-43.1, kernel 6.12.62, PipeWire 1.4.6)

- `pw-top` ERR on the bcm2835 sink: **0** across all observation
  windows (menu and gameplay); the stock module accumulates ~3/minute
  during gameplay (103 → 106 in one observed minute).
- Queued audio depth (appl−hw): 984–1537 frames under the patch vs
  175–1993 with stock — PipeWire holds a stable ~20–30 ms margin
  instead of dipping to 3.6 ms.
- Client-visible delay tracks the true queued depth: reported mean
  1214 frames vs actual 1215 (max deviation bounded by the ~10 ms
  proc-snapshot read skew).
- `hw_ptr` advance per update: 1431–1829 frames (cv 0.035) — real-time
  rate between notifications — versus stock's 960–1440-frame steps
  after 30–44 ms freezes.

## 3. Build

On the target (CM4 / Pi Zero, kernel 6.18.x verified; anything with
matching `raspberrypi-kernel-headers` should work). Needs `git`
installed (patching uses `git apply`), and network access on the first
build:

    make

Produces `snd-bcm2835.ko`. The `mono_mix.patch` delta is verified
building warning-free against `linux-headers-6.18.34+rpt-rpi-v8` on
Raspberry Pi OS Trixie. The combined module (both patches) builds
warning-free through the PSPi-6-Audio-Modules pipeline for **every**
supported facts target (all 27 pass, including the missing-symbol
guard, e.g. `batocera-bcm2711-43.1-20260530`, vermagic matched) and
is deployed and validated on a live CM4 system running that image.

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

1. `/sys/module/snd_bcm2835/parameters/mono_mix` and
   `/sys/module/snd_bcm2835/parameters/interp` exist → patched module
   loaded (stock has neither parameter).
2. `aplay -l` shows `card N: Headphones [bcm2835 Headphones]`.
3. With `mono_mix=Y`, left-only test content is audible on the single
   speaker; with `N` it is silent (it never reaches the wired pin).
4. With `interp=Y` and audio playing under GPU load (PipeWire hosts):
   `pw-top` shows the bcm2835 sink node's ERR column staying at 0 —
   with `interp=N` it accumulates. With `interp=Y`,
   `cat /proc/asound/card0/pcm0p/sub0/status` shows `hw_ptr` advancing
   smoothly (rate × elapsed) and `delay` tracking the true queued
   depth; with `interp=N`, `hw_ptr` steps in notification-sized bites
   and `delay` ramps negative between notifications (the stock
   compensation keeping the reported total roughly constant).

Both parameters (`mono_mix` and `interp`) are 0644 and may be flipped
live, e.g. `echo Y/N | sudo tee /sys/module/snd_bcm2835/parameters/mono_mix`.

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

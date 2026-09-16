# ArpSID v965 C64 Teaser — RC1 Audit Report

## Verdict

A complete source, runtime-model, VIC-II, music, scroller, build and package pass found and repaired the remaining concrete defects in the previous single-bank release. The final architecture has one VIC bank, one beat-envelope frame authority, one VSync scroller authority, one CIA2 bank-write authority and enforced compile-time memory guards in both ACME and the fallback builder.

## Findings and repairs

### 1. Sprite updates could enter visible sprite time

The old top order was:

```text
MusicTick -> BeatRasterTick -> VuBarsTick -> StarTick
```

`VuBarsTick` costs up to 1765 modeled cycles. Placing it before `StarTick` delayed sprite X/Y/color/pointer writes toward the first sprite at Y=$38.

Repair:

```text
MusicTick -> BeatRasterTick -> StarTick -> VuBarsTick
```

The maximum `MusicTick + BeatRasterTick + StarTick` path is now 3044 cycles. Including IRQ entry, register setup and JSR overhead, sprite state completes before the first sprite DMA line.

### 2. BeatEnv changed mid-frame

`StarTick` previously used the incoming beat value for expansion, then reduced `BeatEnv` before shape, speed and color logic. Bitmap reaction, expansion and sparkle therefore observed different beat values in one frame.

Repair:

- `StarTick` no longer mutates `BeatEnv`.
- `BeatEnvDecay` is the only decay owner.
- It runs after `BeatRasterTick`, `StarTick`, and `VuBarsTick`.
- The music filter and every visual consumer now observe one immutable per-frame beat value.

### 3. Heavy lower-border scroller depended on PAL frame tail

The previous scroller ran at raster `$fb`. PAL provides enough frame-tail time, but shorter raster standards leave very little time before line 0.

Repair:

- `Scroller_Tick` now runs once from `IrqTop` at raster 0.
- Text screen/Color RAM are not displayed until raster `$d3`, so movement remains invisible and tear-free.
- `IrqBottom` is call-free and only restores the line-0 vector.
- Maximum complete raster-0 work is 6545 modeled cycles. With a conservative 1500-cycle VIC steal allowance it remains 8045 cycles, far below the `$d2` split budget.

### 4. CIA2 bank register was rewritten every frame

The display already uses one permanent VIC bank. Rewriting cached `$dd00` from `IrqTop` was unnecessary and could overwrite upper CIA2/user-port output bits changed by external code or hardware use.

Repair:

- `$dd00` is written exactly once during startup.
- The upper six bits are preserved.
- No raster handler touches `$dd00`.

### 5. NMI vector was installed after lengthy startup work

With HIRAM disabled, vectors come from RAM. The old code installed `$fffa/$fffb` only after asset copy and subsystem initialization.

Repair:

- `NmiStub` is installed immediately after `$01=$35`.
- The stub preserves A and reads CIA2 `$dd0d` to clear a possible FLAG source.
- VIC pending flags are cleared with `$0f` before raster IRQ bit 0 is enabled.

### 6. Fallback builder ignored source assertions

The Python assembler skipped `!if/!error`, so it could build a PRG after source memory guards became true.

Repair:

- The builder evaluates packaged `!if` blocks after label resolution.
- A true condition terminates the build with the source `!error` message.
- `verify_builder_assertions.py` mutates the code guard to true in a temporary project and proves that the build fails.

### 7. SID cutoff-low values used ignored bits

`$d415` exposes only bits 0–2. The overlay table contained values through `$0f`.

Repair:

- Table data is normalized to 0–7.
- The write path also applies `AND #$07` defensively.

### 8. Dead and misleading logic

- Removed an unreachable duplicate `JMP MB_Effects`.
- Added `CLC` before the beat sprite speed bonus so it is exactly +7 regardless of prior carry.
- Renamed `ScrollerSpeedQ4` to `ScrollerSpeedQ2`, matching its two fractional bits.

## Final VIC-II layout

```text
VIC bank 1 ($4000-$7fff)
  $4400 bitmap screen
  $47f8 sprite pointers
  $4c00 text screen
  $5000 charset
  $6000 bitmap
  $7f80 sprites
```

The text screen cannot alias bitmap sprite pointers and the bank has no VIC character-ROM shadow.

## Raster proof

- Main loop is a 3-cycle `JMP`, bounding raster-entry phase to two cycles.
- `$d2` has no badline or sprite DMA.
- `$d016` completes at cycle 55.
- `$d018` completes at cycle 61.
- `$d011` completes at absolute cycle 67, around `$d3` cycle 4.
- Row handoffs `$e2/$ea/$f2` write `$d016` in the right border after the preceding glyph scanline.
- `IrqBottom $fb` contains no JSR and returns quickly enough on both long and short frame tails.

## Runtime proof

The executable NMOS-6502 model initializes the scroller exactly as `Start` does, then runs 1536 integrated frames:

```text
MusicTick
BeatRasterTick
StarTick
VuBarsTick
BeatEnvDecay
Scroller_Tick
```

Results:

- maximum MusicTick: 1808 cycles;
- maximum pre-sprite path: 3044 cycles;
- maximum visual top core: 4830 cycles;
- maximum full raster-0 work: 6545 cycles;
- conservative VIC steal allowance: 1500 cycles;
- maximum Scroller_Tick: 2480 cycles;
- stack balanced;
- no SID writes outside `$d400-$d418`;
- zero playback writes to `$d418`;
- cutoff low written before high;
- 640 calm BeatEnv frames;
- four arrangement sections and closure verified.

The independent scroller model runs 4096 frames and verifies 0.75/1.00/1.25/1.50 pixels per frame, offsets 7/5/3/1, full 360-character wraps, continuous rainbow phases and unchanged sprite pointers.

## Build/package proof

- source memory `!if/!error` assertions enforced by fallback builder;
- optional ACME/Python byte parity remains enabled;
- deterministic PRG and label map;
- exact runtime asset copies;
- complete package manifest;
- no duplicate production ASM, backup or cache files.

## External boundary

ACME, VICE and physical C64 hardware were unavailable. Real silicon remains the final external validation boundary. No claim of cycle-exact analog SID output is made beyond the tested source/runtime contracts.

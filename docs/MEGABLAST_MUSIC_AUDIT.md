# Low-level audit — UBER SOUND SOLUTION / Megablast final

## Executive verdict

The previous final release played correctly, but it was not fully closed. Its static checks passed while several real state, timing, hygiene and robustness issues remained. This revision fixes the concrete defects found and adds semantic plus executable verification.

## Issues found and repaired

### 1. Filter authority was split

`MB_FiltUpdate` wrote `$d416`, then `MB_GrooveOverlay` overwrote `$d416` in the same frame. The slow wah state advanced but had no audible authority.

**Repair:** `MB_FiltUpdate` now updates state only. `MB_GrooveOverlay` is the single cutoff writer and combines slow sweep, section bias, 16-step accent and BeatEnv with saturation at `$cf`.

### 2. Beat envelope never became calm

Bass notes occur every 12 frames, while `BeatEnv` was reset to 15 and decayed by only one. It was reset before reaching zero.

**Repair:** decay is two units per frame with a zero clamp. A 48-frame simulation now contains 20 calm frames.

### 3. Frequency routine could stall on invalid notes

`MB_CalcFreq` supports notes 0..83. A note of 84 or more could decrement the octave counter below zero and execute an extremely long shift loop.

**Repair:** clamp input notes to 83 before octave division. Pattern verification also enforces note and arpeggio limits.

### 4. Pattern corruption had unsafe failure modes

Zero durations underflowed to 255 frames, and instrument commands above `$83` could index outside four-entry instrument tables.

**Repair:** zero durations become one frame; invalid instruments fall back to instrument zero.

### 5. Visual music clock was frozen

`MusicStep` remained zero after startup even though several visual routines used it.

**Repair:** `MB_Frame` is copied to `MusicStep` every tick.

### 6. PWM clamp did not match its contract

The old triangle update briefly allowed high nibbles `$01` and `$0e`, despite claiming to stay away from near-zero and near-full widths.

**Repair:** explicit lower `$200` and upper `$dff` clamps.

### 7. Sprite baseline logic was inconsistent

Initialization indexed 16-entry X/Y arrays with even register offsets, while beat animation indexed the first eight Y values. After beat movement ended, Y was not restored.

**Repair:** initialization uses sprite index 0..7 and VIC register offset 0,2,..14 separately. Every frame writes either the beat-offset Y or the exact baseline Y. Stack paths are balanced.

### 8. Release contained inactive runtime payload

A large Boys compressed-track/frequency block remained assembled after the active message data. It was unused but consumed asset budget and preserved contradictory active markers.

**Repair:** removed inactive Boys/Airbase runtime data and unused visual tables. Asset usage dropped from 16121 to 14912 bytes; headroom increased from 263 to 1472 bytes.

### 9. Source and verification split-brain

`uber_intro_full.asm` contained an older player, and several differently named verification scripts were identical shallow token checks.

**Repair:** the duplicate source was removed. `src/uber_intro.asm` is the single production authority. Verification is split into asset, syntax/assembler, hygiene, stream, deep semantic, executable 6502, reproducibility, release-contract and complete SHA-256 coverage checks.


### 10. Same-frame BeatEnv authority

The sprite routine previously decayed `BeatEnv` after expansion but before shape, speed and color processing. Different visual consumers therefore observed different values in one frame.

**Repair:** `BeatEnvDecay` is the only decay owner and runs after bitmap reaction, sprites and VU. Music/filter and all visuals now consume one immutable per-frame value.

### 11. Pre-visible sprite deadline

The VU color loop previously ran before sprite state updates.

**Repair:** sprite X/Y/color/pointer writes run before VU. The maximum music + bitmap reaction + sprite path is 3044 modeled cycles and completes before the first sprite DMA line.

## Pattern and music results

- Chord: 4 events / 192 frames.
- Bass: 32 events / 384 frames.
- Lead: 32 events / 384 frames.
- All lanes re-align at 384 frames.
- Route/filter macro cycle: 1536 frames.
- No rest commands in active lanes.
- Bass notes remain chord tones of Am–F–C–G.
- Lead remains in the C-major/A-minor pitch set.
- Maximum note after arpeggio expansion: 79, below the 83 limit.

## Executable runtime results

The packaged PRG was loaded into a small NMOS-6502 execution model. `SID_Init` ran once, followed by 1536 complete `MusicTick` calls and the closure frame.

- `SID_Init`: 480 modeled cycles.
- Maximum music tick: 1808 cycles.
- Average music tick: 1081.4 cycles.
- Stack balance: pass.
- SID address range: pass.
- `$d418` writes during playback: zero.
- `$d415` before `$d416`: pass on every frame.
- Section sequence: 0 → 1 → 2 → 3 → 0.

## Remaining external validation boundary

The sandbox does not provide ACME, VICE, analog SID capture or real C64 hardware. The package therefore proves deterministic assembly, memory layout, stream semantics and modeled 6502 execution, but does not claim analog 6581/8580 output has been hardware-captured in this environment.

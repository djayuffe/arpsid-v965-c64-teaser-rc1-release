# Release notes — MEGABLAST DEEP-AUDITED FINAL

Date: 2026-07-12

## Fixed

- Slow filter state was previously dead because its SID write was overwritten later in the same tick. The overlay now composes live slow wah, section bias, rhythmic accent and beat accent into one bounded cutoff.
- `BeatEnv` previously lasted longer than the 12-frame bass interval, keeping visuals and filter accent permanently active. It now decays by two and produces real calm frames.
- Added a hard note clamp at 83, preventing malformed or future pattern data from underflowing the octave shift counter and stalling an IRQ.
- Added safe handling for zero note/rest durations and invalid instrument commands.
- Corrected PWM boundaries to exactly `$200..$dff`.
- `MusicStep` now follows `MB_Frame` instead of remaining zero.
- Sprite X/Y initialization now uses consistent eight-entry tables; Y returns to baseline after fly-off.
- Removed 1209 bytes of obsolete Boys/Airbase runtime data and unused visual tables.
- Removed duplicate/inactive release inputs and synchronized both source entry files.

## Verified

- Stream grammar, lane lengths, source-prefix fidelity and harmonic constraints.
- 192/384/384-frame lanes re-align every 384 frames.
- Four-section macro cycle is 1536 frames.
- No active rest commands or silent bars.
- Executable NMOS-6502 simulation: 1536 frames plus closure frame.
- Maximum `MusicTick`: 1808 modeled cycles; average: 1082.5.
- No play-time `$d418` writes.
- SID writes stay inside `$d400..$d418`.
- Filter cutoff is written `$d415` then `$d416` every tick.
- Stack returns balanced on every tested routine call.
- Asset block: 14912 / 16384 bytes; 1472 bytes headroom.

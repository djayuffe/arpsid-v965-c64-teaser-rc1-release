# ArpSID v965 C64 Teaser — RC1 Release Notes

## Final runtime repairs

- Reordered top-frame work so sprite pointer/X/Y/color updates complete before first sprite DMA.
- Introduced `BeatEnvDecay` as the single frame-boundary beat-envelope owner.
- Moved `Scroller_Tick` from raster `$fb` to raster 0; text remains invisible until `$d3`.
- Reduced `IrqBottom` to a lightweight, call-free vector reset.
- Removed per-frame CIA2 `$dd00` writes; bank 1 is selected exactly once at startup.
- Installed the RAM NMI vector before asset copying and made the stub preserve A/acknowledge CIA2.
- Cleared all VIC pending IRQ flags before enabling raster IRQ only.
- Removed duplicate unreachable tracker jump.
- Fixed sprite beat-speed carry dependence.
- Normalized and masked SID cutoff-low bits.
- Renamed the scroll rate table to the accurate Q2 name.

## Build hardening

- The deterministic Python assembler now enforces packaged `!if/!error` memory assertions.
- Added a mutation test proving a true source assertion stops the build.
- Preserved optional byte-for-byte ACME parity when ACME is present.

## Preserved presentation

- original UBER SOUND SOLUTION bitmap;
- four independent rainbow scrollers;
- 0.75/1.00/1.25/1.50 pixel-per-frame rates;
- 7/5/3/1 starting offsets;
- clean glyph edge handoffs;
- full 360-character loops;
- audited three-voice Megablast arrangement;
- static `$d418=$1f` policy.

## Verified

- clean deterministic rebuild: PASS
- fallback assertion mutation test: PASS
- 1536 integrated music/visual/scroller frames: PASS
- 4096-frame independent scroller run: PASS
- pre-sprite deadline: PASS, max 3044 modeled cycles
- full raster-0 budget: PASS, max 6545 modeled cycles plus 1500-cycle conservative VIC allowance
- single CIA2 bank write: PASS
- NMI startup order: PASS
- runtime asset equality: PASS
- sprite-pointer isolation: PASS
- original asset hashes: PASS
- complete manifest coverage: PASS

External ACME, VICE and physical-C64 validation remain explicitly unperformed in this environment.

## RC1 packaging

- Froze the fully audited source and binary as release candidate 1.
- Renamed the top-level deliverable to `ARPSID_V965_TEASER_RC1.prg`.
- Updated package identity, release contract and manifest without changing the verified program payload.
- RC1 promotion remains contingent on external emulator or real-C64 smoke testing.

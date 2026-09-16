# ArpSID v965 C64 teaser feature map

The four scroller lanes are condensed from the authoritative ArpSID v965 low-level handoff included beside this file.

## Row 21 — canonical pipeline and realtime ownership

Canonical timed-event order, emergency queue headroom, no-output full-pipeline continuation, immutable prepared state roots, coherent telemetry, sample-boundary structural changes, and bounded realtime execution.

## Row 22 — engine family

BitPerfect/classic SID, SID-register synthesis, DrSID, SID808, DIGI sampling, authentic `$D418`, C64 PSID/RSID, PHI2 telemetry, multi-SID routing, and the shared canonical core.

## Row 23 — timing law

Exact ARP offsets, shared sequencer/KIT/DIGI boundaries, exact post-FX automation time, PAL/NTSC transitions, cycle-stamped SID writes, rollback-atomic C64 service, block-partition conservation, and removal of hidden secondary clocks.

## Row 24 — wrappers, state and telemetry

AUv2, AUv3, VST3, C64 PSID/RSID, no-output rendering, immutable GUI snapshots, explicit strict/compatible C64 status, preset/kit/DIGI/state persistence, clean transport transitions, and PAL/NTSC/multi-SID telemetry.

## C64 presentation contract

- `IrqTop` at raster 0 is the music, visual, beat-decay, and scroller frame authority.
- `MusicTick`, bitmap reaction, sprites and VU consume one same-frame BeatEnv value.
- `BeatEnvDecay` advances the envelope exactly once after all consumers.
- `Scroller_Tick` runs after sprite/VU work while text RAM remains invisible.
- `IrqSplit` enters text mode and installs row-21 fine-X.
- `$e2/$ea/$f2` right-border IRQs install row-22/23/24 fine-X independently.
- `IrqBottom $fb` is lightweight and performs no bulk screen/Color-RAM work.
- Speeds are independently fixed at 0.75/1.00/1.25/1.50 pixels per frame.
- Initial fine-X phases are 7/5/3/1.
- Initial visible text uses characters 0–39; stream pointers continue at 40 and wrap to 0 after character 359.
- Four explicit rainbow phases continue across pointer page boundaries and full message loops.
- The scroller never writes SID, border, or sprite state.

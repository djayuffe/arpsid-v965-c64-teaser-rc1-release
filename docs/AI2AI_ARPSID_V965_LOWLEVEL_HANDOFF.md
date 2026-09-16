# AI2AI — ArpSID v965 low-level engineering handoff

**Package identity:** `0.0.690-pass380-v965-canonical-render-pipeline-closure`  
**Document role:** authoritative engineering handoff for the next AI agent or senior developer  
**Primary audience:** low-level DSP, realtime audio, AUv2/AUv3, VST3, C64/SID emulation, test and release engineers  
**Source state represented:** the v965 source package delivered with this document  
**Last documentation consolidation:** 2026-07-12

---

## 0. Read this first

This document replaces the old chronological `AI2AI.md` overlay that mixed current source truth with historical machine paths, installed-binary hashes, superseded hypotheses and release counts from many earlier passes.

Use this file as the starting point for all future work.

The governing rule is:

> Do not infer current behavior from an old release note, TODO entry, installed component hash or historical incident log. Confirm current source, current tests and current package identity first.

Historical documents remain valuable for causality and regressions, but they are not stronger than current production code and current executable evidence.

### 0.1 Evidence labels

Every engineering statement should be mentally classified as one of these:

| Label | Meaning |
|---|---|
| `VERIFIED-SOURCE` | Directly confirmed in the current v965 source tree. |
| `VERIFIED-TEST` | Confirmed by an executable or source-contract test against current v965. |
| `VERIFIED-PACKAGE` | Confirmed by package guards, manifest or archive inspection. |
| `HISTORICAL` | Confirmed for an older build or field incident, not necessarily re-run on v965. |
| `INFERRED` | Strong inference from code or evidence, but not directly exercised. |
| `EXTERNAL-REQUIRED` | Requires macOS, Logic, auval, signing services, a real VST3 SDK or hardware not present in the Linux audit environment. |
| `OPEN` | Known remaining work or unclosed proof obligation. |

Never silently promote `HISTORICAL`, `INFERRED` or `EXTERNAL-REQUIRED` to current verified truth.

### 0.2 Current compact verdict

`VERIFIED-SOURCE` and `VERIFIED-TEST`:

- The canonical render pipeline repair is integrated as v965.
- The v962 user-kit/popout GUI changes, v963 accessibility/tooltips and v964 C64 SIDPLAY telemetry changes are preserved.
- One canonical timed-event order now survives ingress, storage and dispatch.
- ARP, sequencer, KIT and DIGI timing are tied to explicit event or boundary offsets rather than a second implicit clock.
- Structural engine and PAL/NTSC changes are protected from splitting one physical output sample between incompatible timing domains.
- Post-FX parameter changes are applied on the canonical sample timeline.
- AU no-output processing advances runtime, DSP, FX and telemetry through preallocated scratch.
- GUI telemetry reads render-published data rather than live non-atomic render state.
- v965 registers 479 CTest tests.
- The focused v965 validation set passed 18/18 tests.
- Source-tree, audit-closure and version-coherence guards passed in the repair environment.

`OPEN` or `EXTERNAL-REQUIRED`:

- A clean, full, single-configuration build and execution of all 479 tests has not been newly completed for v965.
- macOS AUv2/AUv3, Logic, auval, code signing, notarization and installer validation have not been newly reproduced for v965.
- The production VST3 target has not been built against the real Steinberg SDK in the Linux repair environment.
- Full ASan/UBSan coverage of the largest kernel translation unit has not completed.
- Host-facing parameter display and text parsing still contain known semantic split-brain risks.
- VST3 string conversion still contains an ASCII-byte-to-UTF-16 shortcut and unconditional editor diagnostics.
- The test build graph remains inefficient because heavyweight implementation is recompiled into many separate test executables.
- Strict C64 physical exactness remains bounded by the explicit limits documented in `C64_EXACTNESS_BOUNDARIES.md`.

---

## 1. Truth hierarchy and source navigation

When documents disagree, use this order:

1. Current production source and data structures.
2. Current executable tests that exercise the behavior.
3. Current package guards and SHA-256 manifest.
4. Current v965 repair and validation reports.
5. Current STATUS/TODO entries.
6. Historical release notes and incident documents.
7. Comments that are not guarded by tests.

### 1.1 Primary current documents

| File | Role |
|---|---|
| `VERSION.txt` | Canonical package identifier. |
| `README.md` | Current release overview and user/developer entry point. |
| `STATUS.md` | Current and historical closure ledger. Read the newest section first. |
| `TODO.md` | Historical closure chronology plus current external sign-off statement. |
| `ARPSID_V965_CANONICAL_PIPELINE_REPAIR_REPORT.md` | One-to-one mapping from pipeline audit findings to repairs and tests. |
| `ARPSID_V965_VALIDATION.md` | Focused test and package validation record. |
| `OWNERSHIP_MAP.md` | Render/non-RT/C64/telemetry ownership rules. |
| `REALTIME_ROLLBACK_JOURNAL.md` | C64 transaction rollback design. |
| `C64_EXACTNESS_BOUNDARIES.md` | Honest strict/compatible physical-exactness boundary. |
| `RELEASE_NOTES_V965.md` | v965 release delta. |
| `RELEASE_CONTENTS.sha256` | Source-only package integrity manifest. |

### 1.2 Never trust these without revalidation

- Absolute workspace paths from old Macs.
- Old installed component hashes.
- Old CTest counts.
- Statements such as “no open issues remain” in an older section.
- An old `auval` pass as proof that the current binary passes.
- A source-contract grep test as proof of runtime audio behavior unless paired with an executable behavior test.
- A UI control declaration as proof that the control is constructed, visible, enabled and wired.
- A telemetry field declaration as proof that it is published, copied and consumed.

---

## 2. Product and wrapper topology

ArpSID is not one simple synthesizer. It is a family of wrappers and runtime personalities sharing a large canonical core.

### 2.1 Product surfaces

`VERIFIED-SOURCE`:

- AUv2 component family.
- AUv3 extension and wrapper app paths on macOS.
- Phase2/VST3 processor/controller path.
- macOS standalone host path.
- Shared GUI and telemetry models.
- C64 PSID/RSID player flavor.
- BitPerfect/classic SID synthesis.
- Direct SID-register/SynthMode synthesis.
- DrSID drum synthesis.
- SID808 engine and factory-kit logic.
- DIGI sampler and authentic `$D418` stream playback.
- Sequencer, arpeggiator, KIT routing, MIX and post-FX.

### 2.2 AUv2 component identities

Historical and source-level product identities use Audio Unit type `aumu`, manufacturer `ASID`, with multiple subtypes including:

- `ArpS`
- `ArIn`
- `DrSD`
- `S808`
- `C64P`

Do not assume all flavors expose identical overlays or runtime capabilities. The v965 capability contract intentionally makes differences explicit.

### 2.3 Wrapper capability law

`VERIFIED-SOURCE`:

- AU owns canonical core rendering plus AU-specific KIT/DIGI/MIX overlay layers.
- Phase2/VST owns canonical core, fractional rendering, exact post-FX and no-output continuation.
- A wrapper must not claim support for a layer it does not instantiate.
- “Parity” means shared contracts where capabilities overlap, not forced feature identity between wrappers.

Main declaration:

- `include/arpsid/core/sid_render_pipeline_capabilities.h`

When adding a new layer, update capability declarations, wrapper implementation, telemetry and tests together.

---

## 3. Canonical end-to-end render pipeline

The intended production chain is:

```text
host transport / MIDI / automation / async intents
    -> canonical timed events
    -> processBlock() or processCanonicalBlockPhase2_()
    -> SidRuntimeModel and canonical parameter/state policy
    -> SidHostCycleDispatcher
    -> sample / cycle / subphase slicing
    -> selected audible engine
       - BitPerfect/classic
       - SID register/SynthMode
       - DrSID / SID808 as applicable
       - C64 PSID/RSID player path when selected by product flavor
    -> sequencer/KIT/DIGI overlays where supported
    -> MIX / reverb / limiter / Hi-Fi where supported
    -> render-owned telemetry publication
    -> GUI reads immutable/atomic snapshots
```

Every arrow is an authority boundary. Most historical defects came from introducing a second authority on one of these boundaries.

---

## 4. Canonical event ingress

### 4.1 Event sources

Events may originate from:

- host transport state
- host MIDI note/controller/program traffic
- host automation points
- AU asynchronous MIDI/parameter intent rings
- internal arpeggiator gates
- internal sequencer events
- panic/all-notes-off/all-sound-off controls
- state/preset transitions
- C64 timed SID writes

### 4.2 Canonical event requirements

Every event entering the final queue must have enough identity to preserve intent:

- sample offset
- event kind
- channel/note/controller/parameter identity
- value
- host note ID or canonical synthetic anonymous identity when applicable
- arrival order
- resolved cycle/subphase timing when physically meaningful
- internal-origin marker where required

### 4.3 Same-sample order law

`VERIFIED-SOURCE`, v965:

- Emergency sample-boundary kills and physical cycle/subphase timing have explicit precedence.
- Otherwise, canonical `arrival_order` survives ingress merge, queue storage and dispatch.
- Event-type priority is not allowed to silently reorder valid same-sample traffic.
- Event-type priority may be used only as a malformed or missing-token fallback.

Main file:

- `include/arpsid/core/sid_event_queue.h`

Relevant tests:

- `IngressParityTimingAuthorityV910Tests`
- `SidRuntimeSameSamplePolicyV891Tests`
- `CanonicalRenderPipelineClosureV965Tests`

### 4.4 Queue saturation law

`VERIFIED-SOURCE`, v965:

The fixed-capacity queue reserves headroom for events that prevent stuck state or undefined transport behavior:

- NoteOff
- AllNotesOff
- AllSoundOff
- Panic
- transport boundaries

A higher-importance incoming event may replace lower-priority traffic at saturation. Replacement must recompute resolved-cycle metadata.

Forbidden regression:

```text
queue fills with automation/note-on traffic
    -> note-off is rejected
    -> voice remains held indefinitely
```

### 4.5 New event-type checklist

When adding an event type:

1. Define payload and default initialization.
2. Define sample-order behavior.
3. Define whether cycle/subphase timing is meaningful.
4. Define saturation priority.
5. Define state mutation owner.
6. Define backend projection owner.
7. Define rollback behavior.
8. Define telemetry if externally visible.
9. Add same-sample and queue-full tests.
10. Confirm AU and Phase2 ingress produce equivalent canonical events.

---

## 5. AU render entry: `processBlock()` / kernel processing

The AU kernel is concentrated in:

- `source/au3/ArpSIDDSPKernel.hpp`
- `source/au3/ArpSIDDSPKernelAdapter.mm`
- `source/au3/ArpSIDAudioUnit.mm`

### 5.1 High-level AU block responsibilities

The render path is expected to:

1. Validate frame count and output topology.
2. Select real output or fixed scratch output.
3. Drain prepared state and PSID handoffs.
4. Snapshot transport and host timing.
5. Drain asynchronous MIDI/parameter intents.
6. Merge host events and automation into canonical events.
7. Generate internal ARP/sequencer events on the same block timeline.
8. Resolve structural-boundary policy.
9. Dispatch sample/cycle/subphase intervals.
10. Render the selected engine.
11. Apply supported overlays.
12. Apply post-FX on exact event boundaries.
13. Publish telemetry.
14. Preserve delayed-write and fractional state for the next block.

### 5.2 No-output law

`VERIFIED-SOURCE`, v965:

No output bus does **not** mean no processing.

The AU path must run the full pipeline into fixed, preallocated stereo scratch and discard only the resulting samples. It must still advance:

- canonical event consumption
- transport state
- oscillators and envelopes
- delayed SID writes
- C64 execution where active
- reverb/limiter/Hi-Fi state
- telemetry generations

Never reintroduce an early return based solely on a missing output pointer.

### 5.3 Oversized parent blocks

AU can process a parent block in bounded chunks. Any new block-level state must be designed so chunking does not:

- duplicate transport boundaries
- duplicate note events
- reset fractional phase
- restart post-FX interpolation
- republish inconsistent telemetry
- misinterpret offsets as relative to the wrong chunk

Add explicit tests for frame counts around every internal maximum:

- max - 1
- max
- max + 1
- 2 × max - 1
- 2 × max
- 2 × max + 1

---

## 6. Phase2/VST render entry

Main implementation:

- `source/arpsid_processor_phase2.h`
- `source/arpsid_processor_phase2.cpp`
- `source/arpsid_controller.cpp`

### 6.1 Processor responsibilities

`processCanonicalBlockPhase2_()` follows the canonical runtime contracts but does not instantiate every AU overlay.

Required guarantees:

- canonical event normalization
- runtime-state consistency
- sample/cycle/subphase slicing
- selected engine execution
- exact post-FX automation timeline
- no-output continuation
- bounded oversize handling
- coherent telemetry publication

### 6.2 Oversize law

`VERIFIED-SOURCE`, v965:

- Processing capacity is established before publishing mutable block state.
- A transient block within preallocated emergency capacity continues normally.
- A block beyond actual fixed capacity is rejected before partial mutation.

Forbidden sequence:

```text
publish new process size
mutate scratch/runtime state
then discover capacity failure
```

### 6.3 Controller is not DSP truth

The VST edit controller owns host presentation, program lists, MIDI mapping and GUI connection. It must not invent a second parameter law.

Current open risks in `source/arpsid_controller.cpp` are listed in Section 22.

---

## 7. Runtime model and state authority

Main files:

- `include/arpsid/core/sid_runtime_model.h`
- canonical state-root types and helpers under `include/arpsid/core/sid_runtime_*`
- `include/arpsid/core/sid_runtime_state_root_presentation.h`
- `include/arpsid/core/sid_runtime_parameter_services.h`
- `include/arpsid/core/sid_runtime_execution.h`
- `include/arpsid/core/sid_runtime_backend.h`
- `include/arpsid/core/sid_runtime_target_adapter.h`
- `include/arpsid/core/sid_runtime_shared_kernel.h`

### 7.1 State-root lifecycle

The canonical lifecycle is:

```text
non-RT producer
    -> parse/copy state
    -> canonicalize semantic values
    -> hydrate prepared fixed-size representation
    -> publish immutable prepared root through mailbox
render thread
    -> consume ownership
    -> apply by bounded swap/install
    -> reconcile wrapper-local fixed-size policy if required
    -> never recanonicalize or allocate
```

### 7.2 Ownership invariant

A producer owns a mailbox slot until publication. After publication, it must not mutate it. Render ownership begins only after successful consumption.

### 7.3 Parameter mutation authority

For every parameter, determine exactly one owner for each stage:

- normalized host value
- semantic interpretation
- runtime-state mutation
- engine projection
- telemetry presentation
- persistence encoding

`VariantChange` was historically applied twice. v965 establishes:

- canonical state application owns runtime mutation
- event execution owns concrete backend projection only

Do not combine the two again.

### 7.4 Dirty fallback generation law

When a realtime intent queue is full, fallback state must be generation ordered. An older queued value must not overwrite a newer fallback value when the queue later drains.

Any new fallback path must preserve normal side effects. Directly writing the parameter image without invoking semantic/runtime policy is incorrect.

---

## 8. Structural parameters and timing-domain transitions

Structural parameters include at least:

- render mode / engine selection
- SID model where it changes physical clock or engine configuration
- PAL/NTSC clock domain
- potentially oversampling or backend changes that alter interval ownership

### 8.1 Sample ownership law

One output sample must not be partially owned by two incompatible engines or clock domains.

`VERIFIED-SOURCE`, v965:

- A block containing a structural change uses sample-boundary-safe slicing.
- Fractional cycle slicing is bypassed for the affected transition block where necessary.
- Subsequent blocks configure the Q32 clock from the new physical clock.

### 8.2 Why this matters

A mid-sample transition can otherwise create:

- pre-transition fractional accumulation that is discarded
- hybrid audio from two engines in one sample
- finalization on the wrong engine
- a dispatcher using old PAL cycles while the engine uses NTSC
- filter/envelope discontinuity
- delayed writes landing in the wrong domain

### 8.3 Acceptance test pattern

For every new structural parameter:

1. Place the change at sample 0.
2. Place it mid-block.
3. Place it at the final sample.
4. Combine it with a cycle-stamped SID write.
5. Combine it with NoteOn and NoteOff on the same sample.
6. Verify no NaN, spike, lost voice, stale clock or fractional residue.
7. Verify the next block starts in the new domain.

---

## 9. `SidHostCycleDispatcher` and physical timing

The dispatcher translates canonical host-block time into physical SID time.

### 9.1 Required timing quantities

- host sample rate
- active SID clock rate
- Q32 or equivalent fractional cycle accumulator
- current sample span
- cycle offset within the block
- subphase within a cycle or sample where represented
- carry into the next sample/block

### 9.2 Core invariant

The total physical cycle advance must be conserved across block partitioning.

Rendering one block of `N` samples must advance the same physical time as rendering two adjacent blocks whose sample counts sum to `N`, subject only to intentionally defined structural boundaries.

### 9.3 Cycle-stamped writes

A cycle-stamped event must:

- be clamped to the valid physical cycle budget
- retain ordering relative to other cycle/subphase events
- not be silently demoted to a generic sample event unless the active mode explicitly lacks fractional support
- not retain stale resolved-cycle metadata after queue replacement

### 9.4 Required test dimensions

- 44.1 kHz, 48 kHz, 88.2 kHz, 96 kHz
- PAL and NTSC
- block sizes 1, 2, 3, 63, 64, 127, 128, 255, 256, 511, 512, 1024
- alternating block sizes
- no-output blocks
- transport discontinuity
- structural parameter change
- queue overflow and replacement

---

## 10. Engine authority

### 10.1 BitPerfect / classic

Main file:

- `include/arpsid/engines/bitperfect_engine.h`

Responsibilities include:

- SID-like register and waveform behavior
- ADSR and filter behavior
- glide/portamento law
- fractional interval rendering
- voice and note handling consistent with canonical runtime policy

v965 specifically preserves fractional slicing while materializing ARP gates into the canonical queue.

Forbidden regression:

```text
ARP enabled
    -> disable fractional render globally
    -> cycle-stamped writes collapse to sample boundary
```

### 10.2 SID register / SynthMode

Relevant files include runtime synth scheduler, performance and voice-policy headers under:

- `include/arpsid/core/sid_runtime_synth_*`
- SID register engine implementation under `include/arpsid/engines/`

Important identity law:

- Real host note IDs must remain protected.
- Raw MIDI or replayed anonymous notes use stable synthetic anonymous identities.
- Anonymous NoteOff must not steal a real positive host-noteId voice.
- Canonical `voiceToken` should be preferred where present.

### 10.3 DrSID

DrSID is a distinct audible engine and drum authority, not merely a register preset.

Audit dimensions:

- factory kit identity
- per-hit register microprogram
- cold-first-block audibility
- transport stop/start preservation
- kit parameter authority
- bridge enable/disable policy
- channel-10 GM projection
- telemetry mode publication

### 10.4 SID808

SID808 includes its own staged musical-shape logic and factory range. It must not be silently treated as canonical DrSID or generic patch-bank traffic.

Audit dimensions:

- kick pitch-drop stages
- tom pitch movement
- hat ring/tail behavior
- clap burst train
- cowbell partial/tail behavior
- filter routing
- force-idle/panic cleanup
- canonical factory slot identity

### 10.5 C64 PSID/RSID player

C64 player is a product/component authority, not a normal synth `renderMode` value.

`SidRuntimeRenderMode::C64Psid` is a telemetry sentinel only. Do not use it to merge player and synth state machines.

---

## 11. Arpeggiator timing

Main file:

- `include/arpsid/engines/arpeggiator.h`

### 11.1 v961 gate-off law

The arpeggiator distinguishes:

- a pending normal gate-off at the duty-cycle position
- an explicit request to flush a sounding note at the next block start after rewind/jump/reset

Do not collapse these meanings into one flag.

### 11.2 v965 same-block law

`VERIFIED-SOURCE`:

- A render-local ARP simulation replays canonical same-block MIDI and relevant automation.
- It emits internal gates at exact sample offsets into the same final queue.
- It installs the exact final ARP state after dispatch.
- It does not double-advance the live arpeggiator.
- A new NoteOn must not wait one block before the first ARP event.

### 11.3 ARP regression matrix

Test:

- mono, legato, unison and poly
- fixed and host-synced rates
- very slow rate
- very fast rate
- gate lengths near 0 and 1
- portamento ARP glide on/off
- same-sample NoteOn plus rate/gate automation
- rewind and transport stop/start
- queue saturation
- block sizes smaller and larger than one ARP step

---

## 12. Sequencer, KIT and DIGI boundaries

Main files:

- `source/au3/ArpSIDSequencerEngine.h`
- AU kernel integration in `source/au3/ArpSIDDSPKernel.hpp`
- Phase2 sequencer integration in `source/arpsid_processor_phase2.cpp`

### 12.1 Explicit boundary law

`SequencerEngine::advanceWindow()` publishes every boundary as a pair equivalent to:

```text
{ stepIndex, sampleOffset }
```

The same boundary list drives:

- melodic sequencer events
- KIT routing
- float DIGI triggers
- authentic D418 triggers

### 12.2 Forbidden old shape

```text
advance sequencer for whole block
read only final step index
read one countdown value
trigger one overlay at sample zero
```

That collapses multiple steps in one block and creates a second sequencer clock.

### 12.3 Boundary tests

Required cases:

- zero boundaries in a block
- one boundary at sample 0
- one boundary at final sample
- multiple boundaries
- wrap from final sequence step to step 0
- swing
- host-tempo following
- internal tempo
- state restore mid-session
- stop/start and rewind
- mixed KIT targets
- D418 PAL/NTSC retime with active voices

---

## 13. DIGI and authentic `$D418`

Main files include:

- `include/arpsid/engines/digi_sampler_engine.h`
- `include/arpsid/engines/digi_d418_stream_engine.h`
- DIGI GUI/state models under `include/arpsid/gui/`

### 13.1 Active-clock law

`VERIFIED-SOURCE`, v965:

Authentic D418 playback follows the active SID clock. It must not use a fixed PAL PHI2 rate when the main runtime is NTSC.

`updateTimingPreserveVoices()` changes timing without killing active sample voices.

### 13.2 DIGI authority questions

For every DIGI change, answer:

- Is the source device input, system output tap, internal SID or stored sample?
- Is the data float PCM or authentic 4-bit nibble stream?
- Which clock owns playback?
- Which thread owns capture and conversion?
- Is the sample bank copied, swapped or referenced?
- What happens on state restore?
- What happens with no output bus?
- How is truncation reported?
- Is telemetry frame-coherent with scalar state?

### 13.3 Large-object caution

DIGI banks and GUI realtime model snapshots are large. Historical Logic crashes proved that large return-by-value or stack-local copies in AU host worker threads can exceed the host stack.

Never reintroduce:

- local `DigiSampleBankBlob` copies on host callback stacks
- local full `GuiRealtimeModelSnapshot_` construction in publication paths
- full `C64Platform` stack snapshots

Use object-owned storage, mailbox producer slots or heap/preallocated ownership outside realtime as appropriate.

---

## 14. Post-FX timeline

Main file:

- `include/arpsid/core/sid_postfx_timeline.h`

### 14.1 Exact offset law

`VERIFIED-SOURCE`, v965:

- Post-FX state is captured at block start.
- Canonical parameter changes create exact sample boundaries.
- Reverb and limiter are applied sample-by-sample where required.
- Hi-Fi processing is applied in exact contiguous segments.
- A value that arrives at sample `K` must not affect samples `< K`.

### 14.2 Parameters requiring semantic consistency

At minimum:

- reverb mix/send/decay or related controls
- limiter attack/release/threshold
- Hi-Fi enable/mode/amount controls

The DSP law and host display/parser law must be shared. This remains an outstanding host-presentation issue even though the render timeline itself is repaired.

### 14.3 Post-FX test pattern

For each automatable post-FX parameter:

1. Render constant input.
2. Change value at several offsets.
3. Compare prefix samples against a control block with no change.
4. Confirm prefix identity within numerical tolerance.
5. Confirm suffix uses the new value.
6. Repeat with no output bus.
7. Repeat across chunk boundaries.
8. Repeat with two changes in one block.

---

## 15. Telemetry architecture

### 15.1 Ownership law

Render publishes. GUI consumes snapshots. GUI must not read live engine or render-parameter objects directly.

### 15.2 Publication mechanisms

The code uses atomics and triple-buffer/mailbox-style snapshots depending on data size and coherence needs.

### 15.3 v965 coherence law

`VERIFIED-SOURCE`:

- DrSID mode, ARP/SEQ state and parameter presentation are render-published.
- DIGI, oscillator and C64 scope snapshots are copied only when their `frameId` matches the scalar telemetry frame.

### 15.4 Telemetry field audit method

For every telemetry field, trace all stages:

```text
declaration
    -> render writer
    -> atomic/snapshot storage
    -> adapter copy
    -> public telemetry structure
    -> GUI or host consumer
    -> reset/default behavior
```

v964 found two fields that were declared and kernel-published but omitted by the adapter. Future telemetry audits must be family-based, not spot checks.

### 15.5 Telemetry anti-patterns

- Reading a live non-atomic engine field from GUI thread.
- Copying scalar telemetry from frame N and scope from frame N-1 without labeling it.
- Publishing fake fallback values that look authoritative.
- Deriving “exact” player time from an unsuitable counter.
- Resetting counters in the GUI rather than at the owning runtime boundary.
- Adding a field without adapter-family invariants.

---

## 16. Realtime ownership and forbidden operations

The practical ownership map is documented in `OWNERSHIP_MAP.md`.

### 16.1 Render-owned paths

Must remain lock-free, allocation-free and bounded:

- AU kernel processing and helpers
- Phase2 processing
- prepared state-root install
- C64 playback execution
- SID timed-write projection
- BitPerfect/SID-register/DrSID/SID808/DIGI rendering
- render-side mailbox consumption
- post-FX
- telemetry publication

### 16.2 Non-RT producer work

May allocate and perform semantic work before publication:

- UI edits
- preset/bank loading
- state-root canonicalization/hydration
- sample import/export
- file and URL handling
- security-scoped bookmarks
- Objective-C UI work
- release packaging

### 16.3 Hard prohibitions on render thread

Do not add:

- heap allocation
- filesystem access
- Objective-C messaging unless explicitly proven realtime-safe and unavoidable
- locks or condition variables
- logging to stderr
- container growth
- JSON parsing
- URL/bookmark resolution
- semantic state canonicalization
- full-platform copies
- unbounded retry loops

### 16.4 Realtime audit commands

Use repository guards first, then compiler/static tooling:

```bash
python3 scripts/verify_source_tree.py
python3 scripts/check_audit_closure.py
rg -n 'new |delete |malloc|calloc|realloc|free\(|std::vector|std::string|mutex|lock_guard|unique_lock|fstream|fprintf|printf|NSLog' \
  source/au3/ArpSIDDSPKernel.hpp source/arpsid_processor_phase2.cpp include/arpsid/core include/arpsid/engines
```

A grep hit is not automatically a defect. Trace whether it is reachable from render and whether storage is preallocated.

---

## 17. C64 PSID/RSID architecture

Core areas include:

- `include/arpsid/core/c64_psid_runtime.h`
- C64 platform, PHI2 machine and SID bridge headers under `include/arpsid/core/`
- AU kernel player integration

### 17.1 Strict RSID truth

Strict RSID may claim a strict PHI2 path only when the PHI2 machine is active and ready.

If PHI2 is unavailable:

- strict mode must refuse or explicitly downgrade
- it must not fall back to semantic Mos6510 execution and still report strict-clean

### 17.2 Compatible path truth

Mos6510 semantic execution is compatibility infrastructure. It is not proof of cycle-physical behavior.

Telemetry must expose compatibility, downgrade or observed physical risk.

### 17.3 PSID `playAddress == 0`

Use the explicit continuous-machine runner. Do not route a non-RSID image through an RSID-only runner.

### 17.4 SID pseudo/system byte `$D41D`

Physical live SID registers are `$D400-$D418`. Local register `0x1D` is an ArpSID pseudo/system byte used for model/PAL-style state. Generic paths must route it through `writeSystemByte()`, not physical `write()`.

### 17.5 Observed downgrade ledger

Observed risk reporting should cover, as applicable:

- timed-write overflow
- dropped multi-SID writes
- SID read/open-bus uncertainty
- invalid chip access
- SID hole writes
- read-modify-write SID behavior
- opcode fallback or approximation
- PSID-CIA compatibility service

Never hide a physical-risk observation because audio remained audible.

---

## 18. C64 render transactions and rollback

Design reference:

- `REALTIME_ROLLBACK_JOURNAL.md`

### 18.1 Transaction law

A C64 play/service attempt that may fail or overflow must be atomic across:

- bridge timed writes
- SID register image/readback counters
- PHI2 machine state
- CPU/CIA/VIC/open-bus state
- RAM and Color RAM mutations
- diagnostic ledgers

### 18.2 Current bounded journal

The platform snapshots small scalar machine state and journals first writes to bounded RAM/Color RAM address logs.

Current documented capacities:

```text
RenderMutationJournal::kMaxDirtyRam   = 8192
RenderMutationJournal::kMaxDirtyColor = 1024
```

### 18.3 Required failure behavior

If a transaction cannot complete:

- no partial SID write batch remains audible
- platform state rolls back
- bridge state rolls back
- overflow/failure telemetry increments honestly
- the next block starts from the pre-transaction state

### 18.4 Future hardening

`OPEN`, lower priority:

- Device-specific dirty journals for CIA/VIC internals could reduce direct snapshot size further.
- Add stress tests that deliberately approach every journal capacity.
- Add failure injection at each transaction stage.
- Verify rollback under multi-SID and D418 activity.

---

## 19. GUI architecture and wiring

Main Objective-C++ implementation:

- `source/au3/ArpSIDViewController.mm`
- related panel headers under `source/au3/`
- VST GUI under `source/gui/`

### 19.1 GUI rules

- GUI is a snapshot consumer, not runtime authority.
- Every action selector must resolve.
- Every declared control intended for users must be constructed and placed.
- Every disabled state must have a re-enable path.
- Every notification post should have a justified observer and teardown behavior.
- CVDisplayLink or timers must pause when occluded or static.
- Large realtime models must not be copied on the host stack.

### 19.2 v962-v964 preserved closures

`VERIFIED-SOURCE` and focused tests:

- DrSID user-kit library strip is constructed and wired.
- SIDCORE popout handles Cmd-F and Cmd-W.
- Mixer and DIGI controls have improved tooltip coverage.
- strips/pad grid/piano expose accessibility information.
- C64 SIDPLAY load failures surface precise parse/load reasons.
- player info includes observed timing facts without fabricated elapsed time.

### 19.3 Next GUI audit

`OPEN`, recommended:

- keyboard-only navigation across all tabs and popup surfaces
- VoiceOver reading order and value updates during live telemetry
- high-contrast and Reduce Motion modes
- scaling above and below typical Retina dimensions
- localization expansion and Unicode rendering
- state restoration when panels are popped out or host window is recreated
- VST GUI parity for controls introduced primarily in AU UI

---

## 20. Factory, preset and bank authority

The canonical factory space has historically expanded beyond old 128-slot assumptions.

Current rules inherited by v965 include:

- factory identity uses the canonical full slot count
- legacy bank file formats may expose a smaller compatibility subset
- extended slots must not alias to slot 127
- DrSID, SID808 and DIGI ranges have distinct payload/presentation semantics
- GUI labels, VST program lists, state roots and bank files must agree on identity

### 20.1 Audit checklist

For boundary slots, always test:

- first slot
- last slot of each family
- first slot of next family
- slot 127
- slot 128
- final canonical slot
- save/load roundtrip
- host program selection
- GUI selection/highlight
- state-root persistence
- factory payload semantic mode

### 20.2 Do not use a generic 7-bit MIDI helper

MIDI Program Change is 7-bit. Canonical internal factory identity may not be. Keep compatibility translation at the boundary instead of shrinking internal identity.

---

## 21. Completed v965 pipeline audit closure

The following findings are considered source-closed in v965, subject to the stated validation limits:

| ID | Closed defect | Current repair principle |
|---|---|---|
| `PIPE-001` | conflicting same-sample ordering laws | one canonical arrival order with explicit physical/emergency exceptions |
| `PIPE-002` | post-FX value leaking before event offset | exact post-FX timeline segments |
| `PIPE-003` | multiple sequencer steps collapsed for KIT/DIGI | explicit per-step boundary list |
| `PIPE-004` | mid-sample engine ownership split | structural transition block uses sample-safe slicing |
| `PIPE-005` | old dispatcher clock with new engine clock | structural clock transition policy |
| `PIPE-006` | GUI reading live render fields | render-published atomics/snapshots |
| `PIPE-007` | AU no-output freezes runtime | fixed scratch full-pipeline rendering |
| `PIPE-008` | ambiguous AU/VST overlay parity | explicit capability contract |
| `PIPE-009` | independent snapshot frames combined | frame-ID matching |
| `PIPE-010` | D418 fixed to PAL | active SID clock retiming |
| `PIPE-011` | Phase2 oversized block partial/drop behavior | preallocated capacity and side-effect-free rejection |
| `PIPE-012` | ARP disables fractional authority | canonical internal ARP events |
| `PIPE-013` | release starvation at queue full | reserved emergency/release headroom |
| `PIPE-014` | stale cycle metadata after replacement | recomputation on replacement |
| `PIPE-015` | duplicate VariantChange mutation | state application mutates once; execution projects |

Main regression test:

- `source/tests/canonical_render_pipeline_closure_v965_tests.cpp`

Do not modify any of these contracts without updating that test and at least one dynamic audio/timing test.

---

## 22. Outstanding engineering work

This is the most important forward-looking section. Items are ordered by expected user impact and release risk.

### 22.1 P1 — unify host parameter presentation and parsing

**Status:** `OPEN`  
**Primary files:**

- `source/parameter_ids.h`
- `source/arpsid_controller.cpp`
- `source/au2/ArpSIDAUv2Component.mm`
- AUv3 parameter tree/presentation code
- DSP law helpers such as portamento, LFO, sequencer tempo and post-FX mappings

#### Problem

VST3 and AUv2 contain wrapper-local generic formulas based on unit strings. These formulas do not reliably match the actual parameter-specific DSP laws.

Examples found in the audit:

- LFO normalized `0.2` may be displayed as `4000 Hz` by a linear host formatter while the DSP uses an exponential curve around `0.2885 Hz`.
- Limiter attack normalized `0.08` may display as `160 ms` while the canonical DSP law is `1.6 ms`.
- Limiter release normalized `0.35` may display as `700 ms` while the canonical law is `356.5 ms`.
- Portamento normalized `0.5` may display as `2.5 s` while the canonical quadratic law is `1.25 s`.
- Sequencer tempo normalized `0.4` may display as `136 BPM` in one wrapper while runtime mapping is `132 BPM` where the active law is `20 + 280 × norm`.
- VST `getParamValueByString()` currently ignores parameter identity and clamps the first numeric token directly to `[0,1]`. Text such as `160 bpm` therefore becomes normalized `1.0`, not the inverse of the display law.
- Semantic values such as `ON`, `OFF`, chip revision labels or oversampling labels need parameter-aware parsing.

#### Required architecture

Create one shared, parameter-ID-aware presentation service, for example:

```cpp
struct SidParameterPresentation {
    static bool formatNormalized(int paramId,
                                 float normalized,
                                 char* dst,
                                 std::size_t dstSize) noexcept;

    static bool parseToNormalized(int paramId,
                                  std::string_view text,
                                  float& normalizedOut) noexcept;

    static ParameterUnitDescriptor unit(int paramId) noexcept;
};
```

The service must use the same canonical helper functions as DSP/runtime policy. Wrappers should delegate; they should not duplicate formulas.

#### Acceptance criteria

- `parse(format(v))` roundtrips for representative and boundary values.
- Formatting agrees with DSP semantic values within declared precision.
- All booleans/enums/indexed values accept labels and numeric forms.
- Locale behavior is explicitly defined.
- Invalid input returns failure without changing the current value.
- AUv2, AUv3 and VST3 produce equivalent semantic text.
- Unit metadata comes from the same descriptor.

#### Required tests

- exhaustive or sampled roundtrip for every parameter
- wrapper parity tests
- specific regression values listed above
- Unicode degree symbol and non-ASCII patch names
- malformed input, whitespace, suffixes and case-insensitive labels

Suggested closure name:

- `ParameterPresentationAuthorityV966Tests`

### 22.2 P1 — proper VST UTF-8 to UTF-16 conversion

**Status:** `OPEN`  
**Primary file:** `source/arpsid_controller.cpp`

#### Problem

`utf8ToTChar()` currently casts each UTF-8 byte to one `TChar`. This is not UTF-8 decoding. Multi-byte characters become corrupt UTF-16 code units.

Affected surfaces may include:

- `Chip Temperature °C`
- factory patch names
- localized labels
- user content that crosses the controller boundary

#### Required repair

Use Steinberg SDK string utilities when available or implement a bounded, tested UTF-8 decoder that:

- emits valid UTF-16
- handles surrogate pairs
- replaces malformed sequences deterministically
- always null-terminates
- never writes beyond `String128`
- avoids heap allocation in controller callbacks where practical

#### Acceptance criteria

- ASCII remains identical.
- `°`, accented Latin, Greek, Cyrillic and a supplementary-plane code point roundtrip.
- malformed UTF-8 does not overrun or produce unterminated output.
- truncation never splits a surrogate pair.

### 22.3 P1 — clean full 479-test build and run

**Status:** `OPEN PROOF OBLIGATION`

The focused 18-test set passed, but a release candidate should have one clean build directory and one complete CTest result.

#### Required command shape

```bash
rm -rf build/full-release
cmake -S . -B build/full-release -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
cmake --build build/full-release --parallel <safe-job-count>
ctest --test-dir build/full-release --output-on-failure
```

#### Acceptance criteria

- all configured targets build from clean source
- 479/479 tests pass, or test inventory change is explained and versioned
- no stale absolute paths
- no dependence on objects from previous builds
- report includes compiler, version, generator, flags, OS and test duration

### 22.4 P1 — macOS AU release closure for v965

**Status:** `EXTERNAL-REQUIRED`

Run on a supported Mac with the intended Xcode/SDK and Logic version.

#### Required proof

- clean AUv2 and AUv3 build
- all five AUv2 flavors installed and visible
- strict `auval` for each flavor
- AUv3 wrapper smoke
- Logic load, editor open/close, transport, automation and preset restore
- no new `AUHostingServiceXPC` crash reports
- no stack overflow in GUI realtime publication
- no stuck notes after stop/start, rewind or mode transition
- no-output/offline render behavior
- codesign verification
- notarization if distribution requires it

Use the existing build helper:

```bash
./build.sh --macos-closure --closure-log-dir ./release-logs
```

Do not copy old v964 `auval` results and label them as v965 proof.

### 22.5 P1 — production VST3 SDK build and host matrix

**Status:** `EXTERNAL-REQUIRED`

#### Required proof

- build against the real supported Steinberg SDK revision
- validator pass
- instantiate in at least two major VST3 hosts
- parameter text entry and automation roundtrip
- program list and preset selection
- no-output/offline render
- block-size changes
- state save/restore
- GUI Unicode and scaling

The parameter presentation and UTF conversion issues should be repaired before declaring this closed.

### 22.6 P2 — sanitizer and fuzzing closure

**Status:** `OPEN`

#### Sanitizers

Run smaller modules and then the largest feasible integrations under:

- AddressSanitizer
- UndefinedBehaviorSanitizer
- ThreadSanitizer on non-realtime test harnesses where timing distortion is acceptable

Avoid claiming render performance from sanitizer builds.

#### Fuzz targets

Recommended targets:

- PSID/RSID parser
- state-root codec
- preset/bank file parser
- DIGI kit/sample metadata parser
- parameter text parser
- MIDI/event queue with random same-sample order and saturation
- C64 relocation/bootstrap validation

Acceptance criteria:

- bounded memory and runtime
- deterministic rejection reason
- no crash, UB or unbounded allocation
- corpus containing known historical malformed cases

### 22.7 P2 — test build graph refactor

**Status:** `OPEN`

#### Problem

Many tests independently compile very large implementation/header surfaces, including the forensic patch bank and AU kernel. This caused repeated multi-minute compilations and memory pressure during v965 validation.

#### Goal

Reduce duplicate compilation without weakening isolation.

Possible approach:

- object libraries for stable heavyweight implementation
- smaller linkable runtime-test support library
- explicit test seams instead of textual inclusion
- unity build only where diagnostics remain usable
- separate source-contract tests from runtime behavior tests

Acceptance criteria:

- clean full build time and peak memory materially reduced
- test count and coverage preserved
- compile definitions remain correct per target
- no ODR violations
- no hidden dependency on test ordering

### 22.8 P2 — remove unconditional VST editor stderr logging

**Status:** `OPEN`

`source/arpsid_controller.cpp` writes `createView` diagnostics directly to stderr.

Required behavior:

- disabled by default in release
- compile-time or runtime diagnostic gate
- no raw pointer disclosure in normal builds
- never reachable from realtime audio callbacks

Also audit `source/arpsid_log.h` call sites to confirm no render-thread logging.

### 22.9 P2 — unit vocabulary normalization

**Status:** `OPEN`, closely related to 22.1

Current code uses variants such as:

- `%` versus `pct`
- `cent` versus `ct`
- `x` versus indexed/ratio semantics
- `src` versus indexed source labels
- `byte` and `steps`

Replace stringly typed unit dispatch with an enum/descriptor. Unit text for display should be separate from semantic unit identity.

### 22.10 P2 — static-analyzer cleanup and stronger policy

**Status:** `OPEN`

Earlier Clang analysis found dead assignments, including queue-overflow logic. These were not proven memory errors, but cleanup matters in authority code.

Required work:

- rerun Clang analyzer on current v965
- enable warning-clean builds for GCC and Clang
- classify each warning
- add `-Werror` selectively for stable modules
- add tests before changing overflow or timing code

### 22.11 P2 — deeper C64 physical-exactness validation

**Status:** `OPEN RESEARCH/VALIDATION`

The source has honest strict/compatible boundaries, but full physical exactness is a larger claim.

Audit areas:

- CIA timer and interrupt edge timing
- VIC-II BA/AEC/badline and sprite DMA timing
- open-bus decay model
- illegal and approximate opcode behavior
- SID readback `$D41B/$D41C`
- ROM-dependent startup behavior
- RSID BASIC policy
- multi-SID address/model/channel routing
- D418 interaction with player writes
- timing under transaction rollback and overflow

Use external traces and audio/register golden references where licensing and provenance permit.

### 22.12 P3 — reduce rollback snapshot footprint

**Status:** `OPEN OPTIONAL HARDENING`

Implement device-specific dirty journals for CIA/VIC internals only if profiling shows meaningful value. Preserve bounded behavior and rollback proof.

### 22.13 P3 — documentation chronology compaction

**Status:** `OPEN MAINTENANCE`

README, STATUS and TODO contain very long historical sections. Preserve forensic history, but consider:

- concise current front page
- generated release index
- archived historical ledger under `docs/history/`
- machine-readable closure registry
- no source tests that depend on fragile prose casing unless the prose is itself a required contract

---

## 23. Full audit playbook for the next pass

### 23.1 Package and identity audit

Check:

```bash
cat VERSION.txt
python3 scripts/check_version_coherence.py
python3 scripts/verify_source_tree.py
python3 scripts/check_audit_closure.py
sha256sum -c RELEASE_CONTENTS.sha256
```

Confirm:

- archive name, VERSION, README, STATUS, TODO, release notes and newest tests agree
- no build directories, `.git`, crash logs or local absolute paths in release ZIP
- manifest covers every intended file except itself

### 23.2 All-files audit

Create an inventory by category:

- production C/C++/Objective-C++
- headers
- tests
- scripts
- CMake/build files
- resources
- presets/calibration data
- documentation
- external vendored code

For each production file record:

- responsibility
- entry points
- outgoing calls
- thread ownership
- mutable state
- allocations
- I/O
- failure mode
- tests touching it

### 23.3 Call-graph audit

Start from these roots:

- AU render callback into kernel processing
- Phase2 `process()` into canonical processing
- state restore scheduling and apply
- PSID/RSID load and render
- GUI telemetry poll
- preset/bank import/export

Trace indirect calls, function pointers, Objective-C selectors and template dispatch manually where static call graphs cannot resolve them.

### 23.4 Authority audit

For every mutable concept, identify one owner:

- transport position
- host tempo
- sequencer phase
- ARP phase
- held-note ledger
- voice allocation
- render mode
- SID model and clock
- parameter image
- state root
- SID register image
- C64 platform state
- telemetry frame
- preset/factory identity

Search for duplicate mirrors and prove synchronization or eliminate one.

### 23.5 Timing audit

For every event path, answer:

- Who assigns sample offset?
- Who assigns cycle/subphase?
- Is the offset block-relative or chunk-relative?
- Can it be sorted again?
- Can it be dropped?
- Does no-output processing advance it?
- Does state restore reset it?
- Is PAL/NTSC change atomic relative to it?

### 23.6 Realtime audit

Use call reachability, not filename assumptions.

Check:

- allocation
- locks
- logging
- syscalls
- Objective-C
- container growth
- large stack locals
- unbounded loops
- exception paths
- shared mutable non-atomic reads

### 23.7 State/persistence audit

Roundtrip:

- parameter image
- state root
- GUI models
- kit/preset bank
- DIGI sample bank
- PSID player state where supported

Test malformed, missing, old-version and forward-version data.

### 23.8 Telemetry audit

Generate a field family table and verify declaration-to-consumer chain. Include defaults, reset ownership and frame coherence.

### 23.9 GUI reverse-wiring audit

Perform both directions:

- every control -> action exists
- every action intended for users -> at least one live control or shortcut

Also inspect controls built conditionally by tab/flavor.

### 23.10 Factory/default audit

Test every canonical factory slot, not only representative slots. Validate payload mode, name, default params, GUI identity and audible non-silence where appropriate.

### 23.11 Release audit

Require:

- clean source
- clean build
- complete test run
- platform validators
- binary hashes
- reproducible logs
- artifact manifest
- explicit unproved boundaries

---

## 24. Test strategy

### 24.1 Test classes

| Class | Purpose |
|---|---|
| Source-contract | Prevent forbidden source shapes or missing integration tokens. |
| Unit | Validate pure laws and data transformations. |
| Runtime behavior | Execute kernel/processor behavior. |
| Audio behavior | Verify audible/non-silent shape, RMS, peak, duty or spectral expectations. |
| Timing | Verify sample/cycle/subphase offsets and clock conservation. |
| State/persistence | Roundtrip and ownership tests. |
| GUI wiring | Verify construction, selectors and accessibility source contracts. |
| Platform | AU/VST validators and host smoke tests. |
| Release | Version, manifest and package cleanliness. |

No single class replaces all others.

### 24.2 Golden-test caution

Golden audio and register traces are valuable but can freeze bugs. Pair them with invariant tests explaining why the trace is correct.

### 24.3 Randomized deterministic tests

Use fixed seeds and print the seed on failure for:

- event ordering
- block partitioning
- note identity
- queue saturation
- state roundtrip
- C64 mutation journal

### 24.4 Differential block partition test

For deterministic configurations:

```text
render N samples in one block
render same N samples split into random block sizes
compare audio, final state, timed writes and telemetry counters
```

Exclude or separately model intentionally host-block-dependent telemetry.

---

## 25. Build and validation commands

### 25.1 Basic Linux/source validation

```bash
./build.sh --build-dir build-release --config Release --parallel 4
```

Focused tests:

```bash
./build.sh --build-dir build-release \
  --test-filter 'CanonicalRenderPipelineClosureV965|VersionCoherenceV965|RuntimeBehaviorClosureV952' \
  --parallel 4
```

Curated release checks:

```bash
./build.sh --release-check --parallel 4
```

Source package:

```bash
./build.sh --package-release --parallel 4
```

### 25.2 Full CTest

```bash
ctest --test-dir build-release --output-on-failure
```

To inspect inventory:

```bash
ctest --test-dir build-release -N
```

### 25.3 macOS closure

```bash
./build.sh --macos-closure --closure-log-dir ./release-logs --parallel 8
```

### 25.4 AUv2 strict validation only

```bash
./build.sh --install-auv2 --clear-au-cache --validate-auv2 --parallel 8
```

### 25.5 Patch hygiene

```bash
git diff --check
python3 scripts/verify_source_tree.py
python3 scripts/check_audit_closure.py
python3 scripts/check_version_coherence.py
```

---

## 26. Change protocol for future AI agents

### 26.1 Before editing

1. Read `VERSION.txt`, the first section of README/STATUS/TODO and this file.
2. Identify current package lineage.
3. Search for a newer implementation already solving the request.
4. Find all wrappers and tests for the relevant concept.
5. State the invariant that must remain true.
6. Create a minimal failing regression test when feasible.

### 26.2 During editing

- Change the owner, not every mirror independently.
- Prefer shared laws/services over wrapper formulas.
- Keep render paths bounded and allocation-free.
- Preserve later user changes when porting an older patch.
- Do not rename historical tests casually.
- Do not weaken a test to match a new implementation unless the old assertion is demonstrably wrong.
- Record why a structural change is safe across sample and block boundaries.

### 26.3 After editing

1. Run the new regression test.
2. Run adjacent closure tests.
3. Run ownership/timing/realtime guards.
4. Run version and source guards.
5. Inspect `git diff --check`.
6. Update release notes, STATUS, TODO and AI2AI only with current facts.
7. Regenerate the release manifest after all documentation changes.
8. Verify the archive itself, not only the working tree.

### 26.4 Never claim “100%” without defining the boundary

Use precise language:

- “source-complete for the audited Linux-buildable path”
- “18 focused tests passed”
- “macOS host validation remains external”
- “strict PHI2 path clean under these conditions”

Do not claim universal correctness, hardware equivalence or release readiness without corresponding proof.

---

## 27. Required evidence format for a new closure

Every significant closure report should include:

1. Package identity.
2. User-visible symptom.
3. Root cause.
4. Exact authority/timing invariant violated.
5. Production files changed.
6. Why the repair is realtime-safe.
7. Regression test names.
8. Exact commands run.
9. Results.
10. External validation limits.
11. SHA-256 of delivered artifact.
12. Remaining known risks.

Avoid reports that only say “fixed all issues.”

---

## 28. High-risk anti-pattern registry

Do not reintroduce any of the following:

### Event/timing

- sorting canonical events twice with different comparators
- using final block state to infer all step boundaries
- using a separate overlay countdown clock
- disabling fractional rendering just because ARP is active
- changing engine clock without changing dispatcher policy
- dropping NoteOff at queue saturation
- retaining resolved-cycle flags after replacing an event

### State/authority

- applying the same semantic state mutation in state apply and backend execution
- recanonicalizing state roots on render thread
- copying old host snapshots over newer runtime authority
- storing full canonical factory identity in a 7-bit helper

### Realtime

- early return on no output
- heap allocation or Objective-C UI work from render
- stderr logging from audio callback
- large GUI/DIGI/C64 objects on host stack
- whole-platform rollback copy

### Telemetry

- GUI reads of live render state
- fake authoritative fallback values
- combining unmatched frame IDs
- declared fields omitted in adapter copy

### Host presentation

- generic unit-string formulas that differ from DSP law
- parameter parser that ignores parameter ID
- byte-casting UTF-8 into UTF-16

### Release

- stale VERSION against newer tests
- manifest generated before final docs change
- release ZIP containing `.git` or build output
- quoting old auval/full-CTest results as current proof

---

## 29. Suggested roadmap

### Milestone A — v966 host parameter authority

Deliver:

- shared parameter presentation/parse service
- typed unit descriptor
- AUv2/AUv3/VST3 delegation
- Unicode-safe VST strings
- exhaustive roundtrip tests

This is the highest-value next source change because current host text can misrepresent real DSP behavior.

### Milestone B — v967 complete verification infrastructure

Deliver:

- test build graph refactor
- clean 479+ full suite in Release
- Clang/GCC warning-clean report
- targeted ASan/UBSan/fuzz suite
- reproducible validation manifest

### Milestone C — v968 platform release closure

Deliver on macOS/real SDK:

- AUv2/AUv3 build and host matrix
- Logic automation/preset/no-output tests
- VST3 validator and multi-host matrix
- signing/notarization/installer proof

### Milestone D — physical C64 validation expansion

Deliver:

- external register/audio trace corpus
- CIA/VIC/illegal-opcode risk matrix
- stricter multi-SID and readback validation
- explicit exact/compatible badges tied to observed proof

---

## 30. Fast start for the next agent

Run:

```bash
cat VERSION.txt
sed -n '1,120p' AI2AI.md
sed -n '1,160p' ARPSID_V965_CANONICAL_PIPELINE_REPAIR_REPORT.md
python3 scripts/check_version_coherence.py
python3 scripts/verify_source_tree.py
python3 scripts/check_audit_closure.py
```

Then choose one task only.

For the recommended next task, inspect:

```bash
sed -n '1,380p' source/arpsid_controller.cpp
sed -n '180,360p' source/au2/ArpSIDAUv2Component.mm
rg -n 'normTo|FromNormalized|ToNormalized|TempoBpm|Lfo|Limiter|Portamento' source include
```

Build a shared semantic map before modifying wrapper code.

---

## Appendix A — focused v965 validation set

The final merged v965 source passed these focused tests in the repair environment:

1. `FractionalSmoke`
2. `DigiD418StreamEngineV698Tests`
3. `SeqSwingTempoV571Tests`
4. `KitMixedTargetRuntimeV650Tests`
5. `TelemetryRuntimeCoherencyV745Tests`
6. `SidRuntimeSameSamplePolicyV891Tests`
7. `Phase2NoOutputFxClosureV908Tests`
8. `IngressParityTimingAuthorityV910Tests`
9. `RenderModeTransitionKitPreservationV942Tests`
10. `StateRootStagingParityV951Tests`
11. `RuntimeBehaviorClosureV952Tests`
12. `ArpAudioRenderV954Tests`
13. `ArpGateOffTimingV961Tests`
14. `GuiUserKitAndPopoutWiringV962Tests`
15. `GuiA11yTooltipCoverageV963Tests`
16. `C64SidplayTelemetryV964Tests`
17. `CanonicalRenderPipelineClosureV965Tests`
18. `VersionCoherenceV965Tests`

This list is not a substitute for the open full-suite proof obligation.

---

## Appendix B — main implementation map

### Canonical runtime and timing

- `include/arpsid/core/sid_event_queue.h`
- `include/arpsid/core/sid_runtime_model.h`
- `include/arpsid/core/sid_runtime_backend.h`
- `include/arpsid/core/sid_runtime_execution.h`
- `include/arpsid/core/sid_runtime_engine_ops.h`
- `include/arpsid/core/sid_runtime_parameter_services.h`
- `include/arpsid/core/sid_runtime_shared_kernel.h`
- `include/arpsid/core/sid_runtime_target_adapter.h`
- `include/arpsid/core/sid_postfx_timeline.h`
- `include/arpsid/core/sid_render_pipeline_capabilities.h`

### Engines

- `include/arpsid/engines/bitperfect_engine.h`
- `include/arpsid/engines/arpeggiator.h`
- DrSID/SID-register/SID808 engine headers under `include/arpsid/engines/`
- `include/arpsid/engines/digi_sampler_engine.h`
- `include/arpsid/engines/digi_d418_stream_engine.h`

### AU

- `source/au3/ArpSIDDSPKernel.hpp`
- `source/au3/ArpSIDDSPKernelAdapter.mm`
- `source/au3/ArpSIDDSPKernelAdapter.h`
- `source/au3/ArpSIDAudioUnit.mm`
- `source/au3/ArpSIDSequencerEngine.h`
- `source/au3/ArpSIDViewController.mm`
- `source/au2/ArpSIDAUv2Component.mm`

### Phase2/VST

- `source/arpsid_processor_phase2.h`
- `source/arpsid_processor_phase2.cpp`
- `source/arpsid_controller.cpp`
- `source/factory.cpp`
- VST GUI files under `source/gui/`

### C64

- `include/arpsid/core/c64_psid_runtime.h`
- C64 platform/PHI2/SID bridge headers under `include/arpsid/core/`
- player integration in AU kernel and runtime adapters

### State, patch and factory

- `source/parameter_ids.h`
- `source/factory_patch_params.h`
- `source/forensic_patch_bank.cpp`
- `include/arpsid/patchbank/`
- `include/arpsid/core/sid_state_codec.h`

### Tests and release guards

- `source/tests/`
- `scripts/verify_source_tree.py`
- `scripts/check_audit_closure.py`
- `scripts/check_version_coherence.py`
- `build.sh`
- `CMakeLists.txt`

---

## Appendix C — historical incident lessons that still matter

These are historical, but the engineering lessons remain current:

1. A Logic pre-editor crash was traced to host stack exhaustion from very large GUI/DIGI snapshot copies. The durable lesson is to inspect stack size and copy shape, not just pointer alignment.
2. C64 choppiness was linked to compressing stale passive-cycle debt into the current buffer. The durable lesson is that catch-up must respect the physical span representable by the current audio block.
3. ARP attenuation was actually a gate-off-at-next-block bug. The durable lesson is to measure per-step timing before diagnosing gain staging.
4. Silent or weak DrSID/SID808 paths often came from authority or routing mismatch, not missing oscillator code.
5. Telemetry declarations can remain dead for many releases if adapter-family coverage is not tested.
6. A source package can be hash-consistent yet version-incoherent. Integrity does not prove semantic release identity.

---

## Appendix D — definition of done

A future release is not “done” merely because it compiles.

For a source-level closure:

- root cause identified
- authority/timing invariant defined
- production repair implemented
- focused tests pass
- neighboring regressions pass
- source/version/package guards pass
- validation limits stated

For a release closure:

- full clean test suite passes
- platform binaries build
- host validators pass
- representative host sessions pass
- signing/notarization/installer pass where required
- archive manifest verifies
- artifact hash published
- no known P0/P1 issue remains hidden behind “external validation” wording

---

**End of authoritative v965 AI2AI handoff.**

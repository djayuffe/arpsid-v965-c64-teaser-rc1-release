#!/usr/bin/env python3
"""Deep semantic audit for the integrated Megablast music/runtime."""
from __future__ import annotations
from pathlib import Path
from math import gcd
import hashlib
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
ASM_PATH = ROOT / "src" / "uber_intro.asm"
SRC_PATH = ROOT / "source_music" / "megablast_cracktro_v3.asm"
PRG_PATH = ROOT / "build" / "uber_sound_solution.prg"
MAP_PATH = ROOT / "build" / "uber_sound_solution.lbl"

errors: list[str] = []
notes: list[str] = []

def fail(msg: str) -> None:
    errors.append(msg)

def require(cond: bool, msg: str) -> None:
    if not cond:
        fail(msg)

def strip_comments(text: str) -> str:
    return "\n".join(line.split(";", 1)[0] for line in text.splitlines())

def block(text: str, start_label: str, end_label: str) -> str:
    try:
        start = text.index(start_label + ":")
        end = text.index(end_label + ":", start)
    except ValueError as exc:
        fail(f"missing block boundary: {exc}")
        return ""
    return text[start:end]

def byte_values(text: str, label: str, next_label: str) -> list[int]:
    body = block(text, label, next_label)
    out: list[int] = []
    for line in body.splitlines()[1:]:
        line = line.split(";", 1)[0]
        if "!byte" not in line:
            continue
        args = line.split("!byte", 1)[1]
        for raw in args.split(","):
            tok = raw.strip()
            if not tok:
                continue
            if tok.startswith("$"):
                out.append(int(tok[1:], 16))
            elif re.fullmatch(r"\d+", tok):
                out.append(int(tok))
            else:
                fail(f"unsupported byte token {tok!r} in {label}")
    return out

def parse_stream(name: str, data: list[int]) -> tuple[int, list[tuple[int, int, int]], int]:
    """Return total frames, note events (frame,note,inst), and rest count."""
    pos = 0
    frame = 0
    inst = 0
    events: list[tuple[int, int, int]] = []
    rests = 0
    commands = 0
    while pos < len(data):
        commands += 1
        if commands > len(data) * 2 + 8:
            fail(f"{name}: command parser did not converge")
            break
        op = data[pos]
        pos += 1
        if op == 0xFE:
            require(pos == len(data), f"{name}: bytes remain after loop marker")
            return frame, events, rests
        if op == 0xFF:
            require(pos < len(data), f"{name}: rest missing duration")
            if pos >= len(data):
                break
            dur = data[pos]
            pos += 1
            require(dur > 0, f"{name}: zero rest duration")
            frame += max(dur, 1)
            rests += 1
            continue
        if op >= 0x80:
            idx = op & 0x7F
            require(idx < 4, f"{name}: invalid instrument {idx}")
            inst = idx if idx < 4 else 0
            continue
        require(op <= 83, f"{name}: note {op} outside calcFreq range 0..83")
        require(pos < len(data), f"{name}: note missing duration")
        if pos >= len(data):
            break
        dur = data[pos]
        pos += 1
        require(dur > 0, f"{name}: zero note duration")
        events.append((frame, op, inst))
        frame += max(dur, 1)
    fail(f"{name}: missing $fe loop marker")
    return frame, events, rests

def lcm(a: int, b: int) -> int:
    return a // gcd(a, b) * b

asm = ASM_PATH.read_text()
code = strip_comments(asm)
src = SRC_PATH.read_text()

# Source/tree authority.
require("MEGABLAST_DEEP_AUDIT_FIX_ACTIVE" in asm, "deep-audit marker missing")
require(not (ROOT / "src" / "uber_intro_full.asm").exists(),
        "duplicate source src/uber_intro_full.asm reintroduced")
require(SRC_PATH.exists(), "active Megablast source archive missing")
for stale in ("DadTrack_", "DadSeqCh", "DadFreqLo:", "AirbaseSongData:", "AirbaseMusicPlay:"):
    require(stale not in asm, f"stale inactive runtime data/token remains: {stale}")

# Active stream grammar and musical timing.
chord = byte_values(asm, "MB_ChordData", "MB_BassData")
bass = byte_values(asm, "MB_BassData", "MB_LeadData")
lead = byte_values(asm, "MB_LeadData", "MB_StartLo")
chord_frames, chord_events, chord_rests = parse_stream("chord", chord)
bass_frames, bass_events, bass_rests = parse_stream("bass", bass)
lead_frames, lead_events, lead_rests = parse_stream("lead", lead)
require((chord_frames, bass_frames, lead_frames) == (192, 384, 384),
        f"unexpected lane lengths {(chord_frames,bass_frames,lead_frames)}")
realign = lcm(lcm(chord_frames, bass_frames), lead_frames)
require(realign == 384, f"lane re-alignment drift: {realign} frames")
require(chord_rests == bass_rests == lead_rests == 0, "active arrangement unexpectedly contains silent rest commands")
require(len(chord_events) == 4, f"chord event count {len(chord_events)} != 4")
require(len(bass_events) == 32, f"bass event count {len(bass_events)} != 32")
require(len(lead_events) == 32, f"lead event count {len(lead_events)} != 32")

# Source fidelity: original material must be an exact prefix, extensions follow it.
src_chord = byte_values(src, "chordData", "bassData")
src_bass = byte_values(src, "bassData", "leadData")
src_lead = byte_values(src, "leadData", "v_startLo")
require(chord == src_chord, "chord stream no longer matches uploaded source")
require(bass[:len(src_bass)-1] == src_bass[:-1] and bass[-1] == 0xFE,
        "bass source motif is not preserved as exact prefix")
require(lead[:len(src_lead)-1] == src_lead[:-1] and lead[-1] == 0xFE,
        "lead source motif is not preserved as exact prefix")

# Harmonic sanity for the extended arrangement.
# Note numbering is C-based modulo 12; progression is Am, F, C, G, 48 frames each.
triads = ({9, 0, 4}, {5, 9, 0}, {0, 4, 7}, {7, 11, 2})
for frame, note, _inst in bass_events:
    chord_idx = (frame % 192) // 48
    require(note % 12 in triads[chord_idx],
            f"bass note {note} at frame {frame} conflicts with chord {chord_idx}")
diatonic = {0, 2, 4, 5, 7, 9, 11}
for frame, note, _inst in lead_events:
    require(note % 12 in diatonic, f"lead note {note} at frame {frame} leaves C-major/A-minor scale")
arp_max = max((note + (7 if inst in (2, 3) else 0)) for _, note, inst in chord_events + bass_events + lead_events)
require(arp_max <= 83, f"note+arp maximum {arp_max} exceeds frequency-table range")

# Runtime guards and state ownership.
for marker in (
    "MB_NoteDurationOk:", "MB_RestDurationOk:", "MB_InstValid:",
    "cmp #84", "MB_CalcFreqInRange:", "sta MusicStep",
    "MB_SectionBias:", "MB_CutAccent:", "MB_CutWork:",
):
    require(marker in asm, f"missing runtime guard/state marker {marker}")
filt = block(asm, "MB_FiltUpdate", "MB_GrooveOverlay")
over = block(asm, "MB_GrooveOverlay", "MB_BaseLo")
require("SID+22" not in filt and "$d416" not in filt.lower(), "slow filter update still writes a value that overlay immediately shadows")
for token in ("MB_FiltVal", "MB_SectionBias,x", "MB_CutAccent,x", "BeatEnv"):
    require(token in over, f"groove filter composition missing {token}")
require(over.find("sta SID+21") < over.find("sta SID+22"), "filter cutoff is not written low-byte before high-byte")
require("SID+24" not in over and "$d418" not in over.lower(), "groove overlay touches master volume")
require(len(re.findall(r"(?m)^\s*sta\s+SID\+24\b", code)) == 1, "master volume must be written exactly once during SID init")

# Gate-off, PWM and visual beat coupling.
gate = block(asm, "MB_GateOff", "MB_CalcFreq")
require(all(tok in gate for tok in ("and #$fe", "pha", "pla", "sta SID+4,y")), "gate-off waveform preservation is incomplete")
pwm = block(asm, "MB_PWMUpdate", "MB_FiltUpdate")
for token in ("lda #$0d", "lda #$02", "sta MB_PWMhi"):
    require(token in pwm, f"exact PWM clamp missing {token}")
decay = block(asm, "BeatEnvDecay", "SID_Init")
require("sbc #2" in decay and "sta BeatEnv" in decay,
        "single beat-envelope decay authority is missing")
require("sbc #2" not in block(asm, "StarTick", "BeatEnvDecay"),
        "StarTick must not mutate BeatEnv mid-frame")
require("cmp #$0c" in asm, "strong-beat sprite threshold no longer matches BeatEnv peak")
require("StarTick_y_baseline:" in asm and "jmp StarTick_y_store" in asm,
        "sprite Y baseline restore is not stack-safe")

# Simulate BeatEnv cadence: bass triggers every 12 frames, envelope must hit zero in each interval.
env = 0
calm = 0
triggers = {frame for frame, _note, _inst in bass_events}
for frame in range(48):
    if frame in triggers:
        env = 15
    if env:
        env = 0 if env < 3 else env - 2
    if env == 0:
        calm += 1
require(calm >= 12, f"beat envelope still effectively permanent; only {calm} calm frames in 48")

# Memory/build contract.
require(PRG_PATH.exists(), "built PRG missing")
if PRG_PATH.exists():
    prg = PRG_PATH.read_bytes()
    require(len(prg) >= 4, "PRG too short")
    if len(prg) >= 2:
        load = prg[0] | (prg[1] << 8)
        end = load + len(prg) - 2
        require(load == 0x0801, f"PRG load address ${load:04x} != $0801")
        require(end <= 0xc000, f"PRG end ${end:04x} crosses $c000")
if MAP_PATH.exists():
    labels: dict[str, int] = {}
    for line in MAP_PATH.read_text().splitlines():
        m = re.fullmatch(r"(\w+) = \$([0-9a-fA-F]{4})", line)
        if m:
            labels[m.group(1)] = int(m.group(2), 16)
    require(labels.get("Start") == 0x1000, "Start label moved from $1000")
    require(labels.get("asset_end", 0x10000) <= 0xc000, "asset_end crosses $c000")
    require(labels.get("MessageModesEnd") == labels.get("asset_end"), "unexpected stale data remains after active message tables")

# Static hygiene: no accidental unreferenced labels except entry/fall-through markers.
labels = re.findall(r"(?m)^\s*([A-Za-z_]\w*):", code)
allowed_single = {"Start", "MB_PWMUp", "MB_FiltUp", "asset_start", "asset_end"}
for label in labels:
    count = len(re.findall(r"\b" + re.escape(label) + r"\b", code))
    if count == 1 and label not in allowed_single:
        fail(f"unreferenced label/data block remains: {label}")

if errors:
    print("FAIL: deep Megablast music/runtime audit")
    for err in errors:
        print(" -", err)
    sys.exit(1)

print("PASS: deep Megablast music/runtime audit")
print(
    f"lane_frames={chord_frames}/{bass_frames}/{lead_frames} realign={realign} "
    f"events={len(chord_events)}/{len(bass_events)}/{len(lead_events)} "
    f"arrangement_cycle={realign*4} max_note_with_arp={arp_max} calm_frames_48={calm}"
)
print(f"prg_sha256={hashlib.sha256(PRG_PATH.read_bytes()).hexdigest()}")

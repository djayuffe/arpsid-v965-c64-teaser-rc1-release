#!/usr/bin/env python3
from pathlib import Path
import re, sys
ROOT=Path(__file__).resolve().parents[1]
asm=(ROOT/'src'/'uber_intro.asm').read_text()
errors=[]
def require(cond,msg):
    if not cond: errors.append(msg)
require('MEGABLAST_CONTINUE_PLUS_ACTIVE' in asm, 'missing continue-plus marker')
# Gate-off must preserve computed waveform-off through PHA/PLA and must not write SID offset as control.
mg=re.search(r'MB_GateOff:(.*?)(?=\nMB_CalcFreq:)', asm, re.S)
require(mg is not None, 'missing MB_GateOff block')
if mg:
    b=mg.group(1)
    require('lda MB_InstWave,y' in b and 'and #$fe' in b, 'gateoff does not compute waveform-off')
    require('pha' in b and 'pla' in b, 'gateoff does not preserve waveform-off while loading SID offset')
    bad='and #$fe\n        lda MB_SidOff,x\n        tay\n        sta SID+4,y'
    require(bad not in b, 'old gateoff bug still present: SID offset written to control register')
# Longer evolving arrangement data should exceed source 16-step bass/lead and 4-chord loop.
for label, min_pairs in [('MB_BassData:',32),('MB_LeadData:',32)]:
    m=re.search(re.escape(label)+r'(.*?)(?=\nMB_[A-Za-z]+Data:|\nMB_StartLo:)', asm, re.S)
    require(m is not None, f'missing {label}')
    if m:
        nums=[int(x) for x in re.findall(r'(?<![\$\w])([0-9]{1,3})(?![\w])', m.group(1))]
        # after the instrument byte line, note/duration pairs dominate; require enough note/duration numbers.
        require(len(nums) >= min_pairs*2, f'{label} not extended enough: numeric bytes={len(nums)}')
require('MB_GrooveOverlay:' in asm, 'missing groove overlay')
require('jsr MB_GrooveOverlay' in asm, 'MusicTick does not call groove overlay')
require('MB_RouteTab:' in asm and '$73' in asm, 'section route/resonance table missing acid route')
require('inc MB_Section' in asm and 'and #$03' in asm, 'bass-loop section sequencer missing')
# Ensure overlay stays crackle-safe: no store to SID+24 or $d418 in groove block.
mo=re.search(r'MB_GrooveOverlay:(.*?)(?=\nMB_BaseLo:)', asm, re.S)
if mo:
    gb=mo.group(1)
    require('SID+24' not in gb and '$d418' not in gb.lower(), 'groove overlay touches master volume')
else:
    require(False, 'cannot locate groove overlay body')
if errors:
    print('FAIL: Megablast continue-plus verifier')
    for e in errors: print(' -', e)
    sys.exit(1)
print('PASS: Megablast continue-plus verifier')
print('gateoff_fixed=1 extended_bass_lead=1 section_overlay=1 no_d418_pump=1')

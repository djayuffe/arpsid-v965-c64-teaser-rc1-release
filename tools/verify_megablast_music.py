#!/usr/bin/env python3
from pathlib import Path
import re, sys
ROOT=Path(__file__).resolve().parents[1]
asm=(ROOT/'src'/'uber_intro.asm').read_text()
src=(ROOT/'source_music'/'megablast_cracktro_v3.asm').read_text()
errors=[]
def require(c,m):
    if not c: errors.append(m)
# Ensure uploaded source is archived and the imported data blocks match expected bytes.
expect={
'MB_ChordData:': ['$83,57,48','$82,53,48','$82,48,48','$82,55,48','$fe'],
'MB_BassData:': ['33,12, 33,12, 28,12, 33,12','29,12, 29,12, 36,12, 29,12','36,12, 36,12, 31,12, 36,12','31,12, 31,12, 38,12, 31,12','$fe'],
'MB_LeadData:': ['64,12, 69,12, 72,12, 71,12','65,12, 69,12, 72,12, 69,12','64,12, 67,12, 72,12, 67,12','62,12, 67,12, 71,12, 74,12','$fe'],
}
for label, snippets in expect.items():
    require(label in asm, f'missing {label}')
    for snip in snippets:
        require(snip in asm, f'imported data missing snippet {snip}')
        require(snip in src, f'archived source missing snippet {snip}')
for marker in ['cmp #$fe','cmp #$ff','cmp #$80','MB_InstCommand:', 'MB_LoopCommand:', 'MB_RestCommand:']:
    require(marker in asm, f'player missing tracker behavior {marker}')
require('sta BeatEnv' in asm and 'drive existing visual beat envelope' in asm, 'bass visual beat link missing')
require('sta SID+24' in asm and 'lda #$1f' in asm, 'static full SID volume init missing')
if errors:
    print('FAIL: Megablast music import verifier')
    for e in errors: print(' -', e)
    sys.exit(1)
print('PASS: Megablast music import verifier')
print('source=megablast_cracktro_v3 voices=3 chord_bass_lead=1 tracker_loop=$fe rest=$ff inst=$80_plus')

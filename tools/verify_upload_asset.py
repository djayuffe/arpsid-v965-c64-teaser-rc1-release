#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
ROOT=Path(__file__).resolve().parents[1]
expected={
    'assets/uber_bitmap.bin':8000,
    'assets/uber_screen.bin':1000,
    'assets/uber_color.bin':1000,
    'assets/uber_custom_font.bin':2048,
    'source_music/megablast_cracktro_v3.asm':None,
}
errors=[]
for rel,size in expected.items():
    p=ROOT/rel
    if not p.is_file(): errors.append(f'missing {rel}'); continue
    if size is not None and p.stat().st_size!=size:
        errors.append(f'{rel}: {p.stat().st_size} bytes, expected {size}')
# Eliminate ambiguous duplicate/inactive inputs from the release tree.
for stale in ('assets/uber_charset.bin','source_music/boys.asm','source_music/Airbase_-_Genie__Splint_Vs_F_w_Remix__V2.asm'):
    if (ROOT/stale).exists(): errors.append(f'stale or duplicate input remains: {stale}')
if errors:
    print('FAIL: upload/assets contract'); [print(' -',e) for e in errors]; sys.exit(1)
print('PASS: upload/assets contract')
for rel in expected:
    p=ROOT/rel
    print(f'{rel} bytes={p.stat().st_size} sha256={hashlib.sha256(p.read_bytes()).hexdigest()}')

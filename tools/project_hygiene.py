#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
errors=[]
canon=ROOT/'src/uber_intro.asm'
if not canon.is_file():
    errors.append('canonical source missing: src/uber_intro.asm')
if (ROOT/'src/uber_intro_full.asm').exists():
    errors.append('duplicate full source remains: src/uber_intro_full.asm')
for p in ROOT.rglob('*'):
    if p.is_dir() and p.name=='__pycache__': errors.append(f'cache directory included: {p.relative_to(ROOT)}')
    if p.is_file() and (p.name.endswith(('~','.bak','.orig','.rej')) or '.pre_' in p.name or p.name=='.DS_Store'):
        errors.append(f'backup/temp file included: {p.relative_to(ROOT)}')
if canon.is_file():
    text=canon.read_text()
    for stale in ('DadTrack_','DadSeqCh','AirbaseMusicPlay:','AirbaseSongData:','BOYS_NATIVE_COMPRESSED_DATA'):
        if stale in text: errors.append(f'stale inactive runtime token: {stale}')
if errors:
    print('FAIL: project hygiene'); [print(' -',e) for e in errors]; sys.exit(1)
print('PASS: project hygiene')
print('canonical_source=src/uber_intro.asm duplicate_sources=0 stale_runtime_data=0 backup_files=0')

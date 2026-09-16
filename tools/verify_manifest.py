#!/usr/bin/env python3
"""Verify hashes and prove that SHA256SUMS covers every packaged file."""
from pathlib import Path
import hashlib, sys
ROOT=Path(__file__).resolve().parents[1]
manifest=ROOT/'SHA256SUMS.txt'; errors=[]; count=0; listed={}
if not manifest.exists():
    print('FAIL: SHA256 manifest missing'); sys.exit(1)
for n,line in enumerate(manifest.read_text().splitlines(),1):
    if not line.strip(): continue
    try: expected,rel=line.split(None,1)
    except ValueError: errors.append(f'line {n}: malformed'); continue
    rel=rel.strip().lstrip('*')
    if rel in listed: errors.append(f'line {n}: duplicate entry {rel}'); continue
    if rel.startswith('/') or '..' in Path(rel).parts: errors.append(f'line {n}: unsafe path {rel}'); continue
    listed[rel]=expected
    p=ROOT/rel
    if not p.is_file(): errors.append(f'line {n}: missing {rel}'); continue
    got=hashlib.sha256(p.read_bytes()).hexdigest(); count+=1
    if got!=expected: errors.append(f'{rel}: {got} != {expected}')
actual={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt'}
missing=sorted(actual-set(listed))
extra=sorted(set(listed)-actual)
for rel in missing: errors.append(f'unmanifested packaged file: {rel}')
for rel in extra: errors.append(f'manifest entry has no packaged file: {rel}')
if errors:
    print('FAIL: SHA256 manifest'); [print(' -',e) for e in errors]; sys.exit(1)
print(f'PASS: SHA256 manifest files={count} coverage=complete')

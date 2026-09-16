#!/usr/bin/env python3
"""Regenerate the complete release SHA-256 manifest in stable path order."""
from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'SHA256SUMS.txt'
files=sorted((p for p in ROOT.rglob('*') if p.is_file() and p!=out), key=lambda p:p.relative_to(ROOT).as_posix())
out.write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT).as_posix()}\n' for p in files))
print(f'Wrote {out} files={len(files)}')

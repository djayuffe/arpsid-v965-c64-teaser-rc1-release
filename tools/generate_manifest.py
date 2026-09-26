#!/usr/bin/env python3
"""Regenerate the complete release SHA-256 manifest in stable path order."""
from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'SHA256SUMS.txt'
EXCLUDED_PARTS={'.git', '__pycache__'}


def packaged_file(path: Path) -> bool:
    relative=path.relative_to(ROOT)
    return path.is_file() and path!=out and not any(part in EXCLUDED_PARTS for part in relative.parts) and path.suffix!='.pyc'


files=sorted((p for p in ROOT.rglob('*') if packaged_file(p)), key=lambda p:p.relative_to(ROOT).as_posix())
out.write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT).as_posix()}\n' for p in files))
print(f'Wrote {out} files={len(files)}')

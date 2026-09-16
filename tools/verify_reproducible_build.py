#!/usr/bin/env python3
"""Prove that the deterministic assembler reproduces both PRG and label map."""
from pathlib import Path
import hashlib, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
prg=ROOT/'build/uber_sound_solution.prg'
lbl=ROOT/'build/uber_sound_solution.lbl'
errors=[]
if not prg.is_file() or not lbl.is_file():
    errors.append('build artifacts missing before reproducibility check')
else:
    before_prg=prg.read_bytes(); before_lbl=lbl.read_bytes()
    run=subprocess.run([sys.executable, str(ROOT/'tools/build_prg_python.py')], cwd=ROOT, text=True, capture_output=True)
    if run.returncode:
        errors.append('deterministic rebuild failed: '+(run.stderr or run.stdout).strip())
    else:
        if prg.read_bytes()!=before_prg: errors.append('PRG differs after deterministic rebuild')
        if lbl.read_bytes()!=before_lbl: errors.append('label map differs after deterministic rebuild')
if errors:
    print('FAIL: reproducible build'); [print(' -',e) for e in errors]; sys.exit(1)
print('PASS: reproducible build')
print('prg_sha256='+hashlib.sha256(prg.read_bytes()).hexdigest())
print('labels_sha256='+hashlib.sha256(lbl.read_bytes()).hexdigest())

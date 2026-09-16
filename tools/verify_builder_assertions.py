#!/usr/bin/env python3
"""Prove the fallback assembler enforces source !if/!error memory guards."""
from pathlib import Path
import shutil, subprocess, sys, tempfile

ROOT = Path(__file__).resolve().parents[1]
errors=[]

def req(cond,msg):
    if not cond: errors.append(msg)

builder=(ROOT/'tools/build_prg_python.py').read_text()
req('Enforce ACME-style compile-time assertions' in builder,
    'fallback builder assertion implementation missing')

with tempfile.TemporaryDirectory(prefix='arpsid_builder_guard_') as td:
    t=Path(td)
    (t/'src').mkdir(); (t/'tools').mkdir(); (t/'assets').mkdir()
    shutil.copy2(ROOT/'tools/build_prg_python.py',t/'tools/build_prg_python.py')
    for f in (ROOT/'assets').iterdir():
        if f.is_file(): shutil.copy2(f,t/'assets'/f.name)
    source=(ROOT/'src/uber_intro.asm').read_text()
    source=source.replace('!if code_end > $4000 {','!if 1 {',1)
    (t/'src/uber_intro.asm').write_text(source)
    r=subprocess.run([sys.executable,str(t/'tools/build_prg_python.py')],cwd=t,text=True,capture_output=True)
    req(r.returncode!=0,'mutated true !if assertion did not stop fallback build')
    req('Code grew into VIC bank 1 display memory at $4000.' in (r.stdout+r.stderr),
        'fallback assertion failure did not preserve !error message')

if errors:
    print('FAIL: fallback builder assertion audit')
    for e in errors: print(' -',e)
    sys.exit(1)
print('PASS: fallback builder assertion audit')
print('true_if_stops_build=1 error_message_preserved=1')

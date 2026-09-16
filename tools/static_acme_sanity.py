#!/usr/bin/env python3
from pathlib import Path
import re, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'src/uber_intro.asm').read_text()
errors=[]
def req(c,m):
    if not c: errors.append(m)
req('!cpu 6510' in s,'explicit !cpu 6510 missing')
req(re.search(r'(?m)^Start:\n\s*sei\n\s*cld\b',s) is not None,'Start must clear decimal mode immediately after SEI')
req('PAGE_COPY_STARTUP_OPTIMIZATION_ACTIVE' in s,'page-copy optimization marker missing')
req(all(tok in s for tok in ('CopyCount_page:','CopyCount_page_loop:','CopyCount_tail:','CopyCount_tail_loop:')),'page/tail copy implementation missing')
req('code_end:' in s and '!if code_end > $4000' in s,'code boundary guard missing')
req('asset_start:' in s and '!error "Asset block crossed $c000."' in s,'asset boundary guard missing')
req('Enforce ACME-style compile-time assertions' in (ROOT/'tools/build_prg_python.py').read_text(),'fallback builder does not enforce !if assertions')

req(s.count('sta $dd00')==1,'CIA2 VIC-bank register must be written exactly once at startup')
req('jsr MusicTick' in s and re.search(r'jsr MusicTick[\s\S]{0,220}jsr BeatRasterTick[\s\S]{0,220}jsr StarTick[\s\S]{0,220}jsr VuBarsTick[\s\S]{0,220}jsr BeatEnvDecay',s),
    'top IRQ must update sprites before VU and decay BeatEnv once last')
req(len(re.findall(r'(?m)^\s*jmp MB_Effects\s*$',s))==2,'unexpected MB_Effects jump count/dead duplicate jump')
req('and #$07\n        sta SID+21' in s,'SID cutoff-low write must mask to bits 0..2')
req(re.search(r'NmiStub:\n\s*;[^\n]*\n(?:\s*;[^\n]*\n)*\s*pha\n\s*lda \$dd0d\n\s*pla\n\s*rti',s) is not None,'NMI stub must preserve A and acknowledge CIA2')
start=s[s.index('Start:'):s.index('InstallAssets:')]
req(start.index('sta $01') < start.index('sta $fffa') < start.index('jsr InstallAssets'),
    'NMI vector must be installed before lengthy startup work')
req('lda #$0f' in start and 'sta $d019' in start and 'sta $d01a' in start,
    'startup must clear all VIC IRQ flags before enabling raster IRQ')

for n,line in enumerate(s.splitlines(),1):
    code=line.split(';',1)[0]
    if re.search(r'^\s*\.[A-Za-z_]\w*:',code): errors.append(f'dot-local label at line {n}')
# The fallback assembler is also a strict syntax/branch/range pass.
r=subprocess.run([sys.executable,str(ROOT/'tools/build_prg_python.py')],cwd=ROOT,text=True,capture_output=True)
if r.returncode: errors.append('Python assembler failed: '+(r.stderr or r.stdout).strip())
if errors:
    print('FAIL: static ACME/source sanity'); [print(' -',e) for e in errors]; sys.exit(1)
print('PASS: static ACME/source sanity')
print(r.stdout.strip())

#!/usr/bin/env python3
from pathlib import Path
import re, sys
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'src/uber_intro.asm'; OUT=ROOT/'build/uber_sound_solution.prg'
lines=SRC.read_text().splitlines(); const={}; labels={}
op={
('nop','impl'):0xea,('clc','impl'):0x18,('sec','impl'):0x38,('cld','impl'):0xd8,('cli','impl'):0x58,('dex','impl'):0xca,('dey','impl'):0x88,('inx','impl'):0xe8,('iny','impl'):0xc8,('pha','impl'):0x48,('pla','impl'):0x68,('rti','impl'):0x40,('rts','impl'):0x60,('sei','impl'):0x78,('tax','impl'):0xaa,('tay','impl'):0xa8,('txa','impl'):0x8a,('txs','impl'):0x9a,('tya','impl'):0x98,
('lda','imm'):0xa9,('lda','zp'):0xa5,('lda','zpx'):0xb5,('lda','abs'):0xad,('lda','absx'):0xbd,('lda','absy'):0xb9,('lda','indy'):0xb1,
('sta','zp'):0x85,('sta','zpx'):0x95,('sta','abs'):0x8d,('sta','absx'):0x9d,('sta','absy'):0x99,('sta','indy'):0x91,
('sty','zp'):0x84,('sty','zpx'):0x94,('sty','abs'):0x8c,
('ldx','imm'):0xa2,('ldx','zp'):0xa6,('ldx','abs'):0xae,('ldy','imm'):0xa0,('ldy','zp'):0xa4,('ldy','zpx'):0xb4,('ldy','abs'):0xac,('ldy','absx'):0xbc,
('adc','imm'):0x69,('adc','zp'):0x65,('adc','zpx'):0x75,('adc','abs'):0x6d,('adc','absx'):0x7d,('adc','absy'):0x79,
('sbc','imm'):0xe9,('sbc','zp'):0xe5,('sbc','zpx'):0xf5,('sbc','abs'):0xed,('sbc','absx'):0xfd,('sbc','absy'):0xf9,
('and','imm'):0x29,('and','zp'):0x25,('and','zpx'):0x35,('and','abs'):0x2d,('and','absx'):0x3d,('and','absy'):0x39,
('ora','imm'):0x09,('ora','zp'):0x05,('ora','zpx'):0x15,('ora','abs'):0x0d,('ora','absx'):0x1d,('ora','absy'):0x19,
('eor','imm'):0x49,('eor','zp'):0x45,('eor','zpx'):0x55,('eor','abs'):0x4d,('eor','absx'):0x5d,('eor','absy'):0x59,
('cmp','imm'):0xc9,('cmp','zp'):0xc5,('cmp','zpx'):0xd5,('cmp','abs'):0xcd,('cmp','absx'):0xdd,('cmp','absy'):0xd9,
('cpx','imm'):0xe0,('cpx','zp'):0xe4,('cpx','abs'):0xec,
('dec','zp'):0xc6,('dec','zpx'):0xd6,('dec','abs'):0xce,('dec','absx'):0xde,('inc','zp'):0xe6,('inc','zpx'):0xf6,('inc','abs'):0xee,('inc','absx'):0xfe,
('bit','abs'):0x2c,('bit','zp'):0x24,('asl','acc'):0x0a,('asl','zp'):0x06,('asl','zpx'):0x16,('asl','abs'):0x0e,('asl','absx'):0x1e,('lsr','acc'):0x4a,('lsr','zp'):0x46,('lsr','zpx'):0x56,('lsr','abs'):0x4e,('lsr','absx'):0x5e,('ror','acc'):0x6a,('ror','zp'):0x66,('ror','zpx'):0x76,('ror','abs'):0x6e,('ror','absx'):0x7e,
('jmp','abs'):0x4c,('jsr','abs'):0x20,('bne','rel'):0xd0,('beq','rel'):0xf0,('bcc','rel'):0x90,('bcs','rel'):0xb0,('bpl','rel'):0x10,('bmi','rel'):0x30}
rel={'bne','beq','bcc','bcs','bpl','bmi'}
def strip(l): return l.split(';',1)[0].strip()
def toks(arg): return [x.strip() for x in arg.split(',') if x.strip()]
def expr(e,pc=0,undef_abs=False):
    e=e.strip(); lh=None
    if e.startswith('<') or e.startswith('>'): lh=e[0]; e=e[1:].strip()
    e=re.sub(r'\$([0-9a-fA-F]+)', lambda m:str(int(m.group(1),16)), e)
    e=re.sub(r'%([01]+)', lambda m:str(int(m.group(1),2)), e)
    env={**const,**labels,'__PC__':pc}
    try: v=eval(e, {'__builtins__':{}}, env)
    except NameError:
        if undef_abs: v=0x100
        else: raise
    if lh=='<': return v&255
    if lh=='>': return (v>>8)&255
    return v
def bytes_arg(arg,pc=0): return [expr(t,pc)&255 for t in toks(arg)]
def mode(arg,mn,pc,pass1=False):
    a=arg.strip(); lo=a.lower().replace(' ','')
    if mn in ('asl','lsr') and (not a or lo=='a'): return 'acc',0
    if not a: return 'impl',0
    if a.startswith('#'): return 'imm',expr(a[1:],pc,pass1)&255
    if lo.startswith('(') and lo.endswith('),y'): return 'indy',expr(a[a.find('(')+1:a.rfind(')')],pc,pass1)&255
    idx=None; base=a
    if lo.endswith(',x'): idx='x'; base=a[:-2]
    elif lo.endswith(',y'): idx='y'; base=a[:-2]
    val=expr(base.strip(),pc,pass1); zp=0<=val<256
    if idx=='x': return ('zpx' if zp else 'absx'),val
    if idx=='y': return 'absy',val
    return ('zp' if zp else 'abs'),val
def insn_size(mn,arg,pc):
    if mn in rel: return 2
    m,v=mode(arg,mn,pc,True)
    if (mn,m) not in op: raise SystemExit(f'unsupported {mn} {m} {arg}')
    return 1+(0 if m in ('impl','acc') else 1 if m in ('imm','zp','zpx','indy') else 2)
def iter_lines():
    for raw in lines:
        c=strip(raw)
        if c and not c.startswith('!cpu'): yield raw,c
pc=None
for raw,c in iter_lines():
    if re.match(r'^[A-Za-z_]\w*\s*=', c):
        n,e=[x.strip() for x in c.split('=',1)]; const[n]=expr(e,pc or 0,True); continue
    if c.startswith('*'):
        pc=expr(c.split('=',1)[1],pc or 0,True); continue
    if pc is None: continue
    while True:
        m=re.match(r'^([A-Za-z_]\w*):\s*(.*)$',c)
        if not m: break
        labels[m.group(1)]=pc; c=m.group(2).strip()
        if not c: break
    if not c or c.startswith(('!if','}','!error')): continue
    if '!bin' in c:
        f=re.search(r'"([^"]+)"',c).group(1); pc+=(ROOT/f).stat().st_size; continue
    if '!byte' in c: pc+=len(bytes_arg(c.split('!byte',1)[1],pc)); continue
    mn,*rest=c.split(None,1); pc+=insn_size(mn.lower(),rest[0] if rest else '',pc)

# Enforce ACME-style compile-time assertions used by this source. The previous
# fallback builder silently skipped !if/!error blocks, which could create a PRG
# even after code or assets crossed a protected memory boundary.
for i, raw in enumerate(lines):
    c=strip(raw)
    m=re.match(r'^!if\s+(.+?)\s*\{\s*$', c)
    if not m:
        continue
    condition=expr(m.group(1),0)
    depth=1; error_message='compile-time assertion failed: '+m.group(1)
    j=i+1
    while j < len(lines) and depth:
        inner=strip(lines[j])
        depth += inner.count('{') - inner.count('}')
        em=re.match(r'^!error\s+"([^"]*)"', inner)
        if em:
            error_message=em.group(1)
        j+=1
    if depth:
        raise SystemExit(f'unterminated !if block at line {i+1}')
    if condition:
        raise SystemExit(error_message)

mem=bytearray(65536); used=[]; pc=None
def emit(bs):
    global pc
    end=pc+len(bs)
    for a,b in used:
        if pc < b and end > a:
            raise SystemExit(f'output overlap ${pc:04x}-${end-1:04x} with ${a:04x}-${b-1:04x}')
    mem[pc:end]=bytes(bs); used.append((pc,end)); pc=end
def word(v): return [v&255,(v>>8)&255]
for raw,c in iter_lines():
    if re.match(r'^[A-Za-z_]\w*\s*=', c): continue
    if c.startswith('*'):
        pc=expr(c.split('=',1)[1],pc or 0); continue
    if pc is None: continue
    while True:
        m=re.match(r'^([A-Za-z_]\w*):\s*(.*)$',c)
        if not m: break
        c=m.group(2).strip()
        if not c: break
    if not c or c.startswith(('!if','}','!error')): continue
    if '!bin' in c:
        f=re.search(r'"([^"]+)"',c).group(1); emit((ROOT/f).read_bytes()); continue
    if '!byte' in c:
        emit(bytes_arg(c.split('!byte',1)[1],pc)); continue
    mn,*rest=c.split(None,1); mn=mn.lower(); arg=rest[0] if rest else ''
    if mn in rel:
        target=expr(arg,pc); off=target-(pc+2)
        if off<-128 or off>127: raise SystemExit(f'branch out of range {raw}: {off}')
        emit([op[(mn,'rel')], off&255]); continue
    m,v=mode(arg,mn,pc); code=op.get((mn,m))
    if code is None: raise SystemExit(f'unsupported {mn} {m} {arg} line {raw}')
    bs=[code]
    if m in ('imm','zp','zpx','indy'): bs.append(v&255)
    elif m not in ('impl','acc'): bs+=word(v)
    emit(bs)
start=min(a for a,b in used); end=max(b for a,b in used)
OUT.parent.mkdir(exist_ok=True); OUT.write_bytes(bytes([start&255,start>>8])+bytes(mem[start:end]))
map_out=OUT.with_suffix('.lbl')
map_out.write_text('\n'.join(f'{name} = ${addr:04x}' for name,addr in sorted(labels.items(), key=lambda kv:(kv[1],kv[0])))+'\n')
print(f'Built {OUT} load=${start:04x} end=${end:04x} size={OUT.stat().st_size} labels={len(labels)}')

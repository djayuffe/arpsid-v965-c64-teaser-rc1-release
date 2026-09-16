#!/usr/bin/env python3
"""Verify the single-bank VIC-II layout and PAL raster handoff budgets."""
from pathlib import Path
import re, sys
ROOT=Path(__file__).resolve().parents[1]
asm=(ROOT/'src/uber_intro.asm').read_text()
labels={}
for line in (ROOT/'build/uber_sound_solution.lbl').read_text().splitlines():
    m=re.fullmatch(r'(\w+) = \$([0-9a-fA-F]{4})',line)
    if m: labels[m.group(1)]=int(m.group(2),16)
errors=[]
def req(c,m):
    if not c: errors.append(m)
def block(a,b):
    try: return asm[asm.index(a+':'):asm.index(b+':',asm.index(a+':'))]
    except ValueError:
        errors.append(f'missing block {a}..{b}'); return ''

req('VIC_VISIBLE_TEXT_BANK_FIX_ACTIVE' in asm,'VIC-visible text-bank fix marker missing')
req('SINGLE_VIC_BANK1_DISPLAY_ACTIVE' in asm,'single VIC-bank marker missing')
req('RASTER_BANK_SWITCH_REMOVED_ACTIVE' in asm,'raster bank-switch removal marker missing')
req('SCREEN_ADDR   = $4400' in asm,'bitmap screen must be $4400')
req('TEXT_SCREEN_ADDR = $4c00' in asm,'text screen must be $4c00')
req('CHARSET_ADDR  = $5000' in asm,'charset must be $5000')
req('BITMAP_ADDR   = $6000' in asm,'bitmap must be $6000')
req('SPRITE_BASE   = $7f80' in asm,'sprite base must be $7f80')
req('ASSET_ADDR    = $8000' in asm,'asset source must start at $8000')
req('SPLIT_LINE    = $d2' in asm,'mode handoff must occur on final bitmap scanline $d2')
req('zpVicBank1' not in asm,'stale cached VIC-bank value remains')
req(len(re.findall(r'(?m)^\s*sta \$dd00\b',asm))==1,'VIC bank must be selected exactly once at startup')
req('zpVicBank0' not in asm and 'zpVicBank3' not in asm,'obsolete multi-bank authority remains')

bank_base=0x4000
screen=0x4400; text_screen=0x4c00; charset=0x5000; bitmap=0x6000; sprites=0x7f80
for name,addr in [('screen',screen),('text screen',text_screen),('charset',charset),('bitmap',bitmap),('sprites',sprites)]:
    req((addr & 0xc000)==bank_base,f'{name} is not in VIC bank 1')
req((screen-bank_base)==0x0400,'bitmap screen is not bank-relative $0400')
req((text_screen-bank_base)==0x0c00,'text screen is not bank-relative $0c00')
req((charset-bank_base)==0x1000,'charset is not bank-relative $1000')
req((bitmap-bank_base)==0x2000,'bitmap is not bank-relative $2000')
req(text_screen+1000<=charset,'text screen overlaps charset')
req(charset+2048<=bitmap,'charset overlaps bitmap')
req(bitmap+8000<=sprites,'bitmap overlaps sprite payload')
req(sprites+128<=0x8000,'sprite payload crosses VIC bank 1')

code_end=labels.get('code_end',0xffff); asset_start=labels.get('asset_start',0)
req(code_end<=0x4000,f'code end ${code_end:04x} overlaps VIC bank 1 display memory')
req(asset_start>=0x8000,f'asset source ${asset_start:04x} starts below safe source region')
req(labels.get('asset_end',0xffff)<=0xc000,'asset source crosses $c000')

for row in range(20,25):
    req(f'TEXT_SCREEN_ADDR+40*{row}' in asm,f'row {row} missing dedicated text-screen write')
    req(re.search(r'(?<!TEXT_)SCREEN_ADDR\+40\*'+str(row)+r'\b',asm) is None,f'row {row} still writes bitmap screen')
req('sta SCREEN_ADDR+$03f8,x' in asm,'relocatable sprite-pointer writes missing')
req('TEXT_SCREEN_ADDR+40*24+39' in asm,'row-24 hidden insertion column missing')

top=block('IrqTop','IrqSplit')
req('sta $dd00' not in top,'top IRQ must not rewrite CIA2/user-port bank bits')
req(top.index('lda #$18')<top.index('sta $d018'),'top bitmap $d018 order is invalid')

split=block('IrqSplit','IrqTextRow2')
nops=len(re.findall(r'(?m)^\s*nop\s*$',split))
req(nops==11,f'split handoff uses {nops} NOPs, expected 11')
for tok in ('lda zpScrollFine1','sta $d016','lda #$34','sta $d018','lda #$1b','sta $d011'):
    req(tok in split,f'split handoff missing {tok}')
req('sta $dd00' not in split,'timing-critical split still switches VIC banks')
if all(tok in split for tok in ('lda zpScrollFine1','sta $d016','lda #$34','sta $d018','lda #$1b','sta $d011')):
    req(split.index('nop')<split.index('lda zpScrollFine1')<split.index('sta $d016')<split.index('lda #$34')<split.index('sta $d018')<split.index('lda #$1b')<split.index('sta $d011'),
        'split screen/mode/fine-X write order is unsafe')

# PAL cycle envelope. Main loop is a 3-cycle JMP and line $d2 has no sprite DMA,
# limiting entry jitter to two cycles. Removing CIA2 bank writes creates margin.
base=7+13+6+nops*2
d016_complete=base+3+4
d018_complete=d016_complete+2+4
d011_complete=d018_complete+2+4
jitter=2
req(55<=d016_complete<=57,f'$d016 completion cycle {d016_complete} not in 38-column right border')
req(d018_complete+jitter<=63,f'$d018 can spill beyond raster $d2: {d018_complete}+{jitter}')
req(d011_complete+jitter<63+14,f'$d011 can miss row-20 badline recognition: {d011_complete}+{jitter}')

top=block('IrqTop','IrqSplit')
bottom=block('IrqBottom','BeatRasterTick')
req('jsr Scroller_Tick' in top,'raster-0 IRQ does not own the VSync scroller')
req('jsr Scroller_Tick' not in bottom,'frame-tail IRQ still performs heavy scrolling')
req(len(re.findall(r'(?m)^\s*jsr\s+',bottom))==0,'frame-tail IRQ must remain call-free and bounded')

if errors:
    print('FAIL: VIC screen/raster isolation audit')
    for e in errors: print(' -',e)
    sys.exit(1)
print('PASS: VIC screen/raster isolation audit')
print(f'vic_bank=1 bitmap_screen=$4400 text_screen=$4c00 charset=$5000 bitmap=$6000 sprite_ptr=$47f8-$47ff split=$d2 d016_cycle={d016_complete} d018_cycle={d018_complete} d011_abs={d011_complete} asset=${asset_start:04x}-${labels.get("asset_end",0):04x}')

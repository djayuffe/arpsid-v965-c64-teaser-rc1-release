#!/usr/bin/env python3
"""Guard the VIC-II glyph-edge repair for independent text-row scrolling."""
from pathlib import Path
import re, sys
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'src/uber_intro.asm').read_text()
errors=[]
def req(c,m):
    if not c: errors.append(m)
def block(a,b):
    try: return s[s.index(a+':'):s.index(b+':',s.index(a+':'))]
    except ValueError:
        errors.append(f'missing block {a}..{b}'); return ''
for marker in ('GLYPH_EDGE_CLEAN_SCROLL_ACTIVE','RIGHT_BORDER_D016_HANDOFF_ACTIVE','TEXT_38_COLUMN_EDGE_GUARD_ACTIVE','BITMAP_TO_TEXT_LAST_SCANLINE_HANDOFF_ACTIVE'):
    req(marker in s,f'missing {marker}')
req('SPLIT_LINE    = $d2' in s,'bitmap/text split is not on raster $d2')
for token in ('TEXT_ROW2_LINE = $e2','TEXT_ROW3_LINE = $ea','TEXT_ROW4_LINE = $f2','BOTTOM_LINE   = $fb'):
    req(token in s,f'missing corrected raster boundary {token}')
parts=(
    ('IrqSplit','IrqTextRow2','zpScrollFine1',True),
    ('IrqTextRow2','IrqTextRow3','zpScrollFine2',True),
    ('IrqTextRow3','IrqTextRow4','zpScrollFine3',True),
    ('IrqTextRow4','IrqBottom','zpScrollFine4',True),
)
write_cycles=[]
for a,b,fine,late in parts:
    body=block(a,b)
    req(f'lda {fine}' in body,f'{a} does not load {fine}')
    req('and #$07' not in body,f'{a} contains unnecessary late-cycle AND before $d016')
    req('ora #$08' not in body,f'{a} re-enables 40-column edge fetch')
    req('sta $d016' in body,f'{a} does not write $d016')
    if late:
        nops=len(re.findall(r'(?m)^\s*nop\s*$',body))
        req(nops==11,f'{a} delay has {nops} NOPs, expected 11')
        # PAL NMOS model: IRQ entry 7 + save/ack 19 + delay 22 + LDAzp 3
        # + STAabs 4 = completion at cycle 55.
        completion=7+19+nops*2+3+4
        write_cycles.append(completion)
        req(55<=completion<=59,f'{a} $d016 completion cycle {completion} outside right border')
        req(body.index('sta $d019') < body.index('nop') < body.index(f'lda {fine}') < body.index('sta $d016'),
            f'{a} late-write order is wrong')
# Charset source itself must remain exact and its main alphabet must preserve
# an empty right edge and bottom scanline; this distinguishes timing damage
# from an actual font-data regression.
font=(ROOT/'assets/uber_custom_font.bin').read_bytes()
req(len(font)==2048,f'font size {len(font)} != 2048')
for code in range(1,27):
    glyph=font[code*8:(code+1)*8]
    req(len(glyph)==8,f'glyph {code} truncated')
    req(all((row & 1)==0 for row in glyph),f'glyph {code} rightmost source pixel is not blank')
    req(glyph[-1]==0,f'glyph {code} bottom source scanline is not blank')
if errors:
    print('FAIL: glyph-edge clean scroller audit')
    for e in errors: print(' -',e)
    sys.exit(1)
print('PASS: glyph-edge clean scroller audit')
print(f'mode=38_column handoff_rasters=d2/e2/ea/f2 d016_completion_cycles={write_cycles} font_source_edges=clean')

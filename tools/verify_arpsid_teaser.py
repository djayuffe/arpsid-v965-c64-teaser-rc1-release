#!/usr/bin/env python3
"""Verify ArpSID v965 teaser branding, feature payload and VSync scroller authority."""
from pathlib import Path
import re, sys, hashlib

ROOT=Path(__file__).resolve().parents[1]
ASM=ROOT/'src/uber_intro.asm'
MAP=ROOT/'build/uber_sound_solution.lbl'
errors=[]
def req(cond,msg):
    if not cond: errors.append(msg)

s=ASM.read_text()
code='\n'.join(line.split(';',1)[0] for line in s.splitlines())
req('ARPSID_V965_TEASER_RELEASE_ACTIVE' in s,'teaser release marker missing')
req('VBLANK_SYNCED_SMOOTH_SCROLLER_ACTIVE' in s,'VSync scroller marker missing')
req('VBLANK_TOP_SCROLLER_AUTHORITY_ACTIVE' in s,'VBlank-top authority marker missing')
req('VARIABLE_SPEED_RAINBOW_SCROLLER_ACTIVE' in s,'variable-speed rainbow marker missing')
req('INDEPENDENT_ROW_OFFSET_SPEED_SCROLLER_ACTIVE' in s,'independent row offset/speed marker missing')
req('ORIGINAL_UBER_BACKGROUND_RESTORED_ACTIVE' in s,'original background marker missing')
req('GLYPH_EDGE_CLEAN_SCROLL_ACTIVE' in s,'glyph edge-clean marker missing')
req('RIGHT_BORDER_D016_HANDOFF_ACTIVE' in s,'right-border handoff marker missing')
req('TEXT_38_COLUMN_EDGE_GUARD_ACTIVE' in s,'38-column edge guard marker missing')
req('FULL_MESSAGE_LOOP_AND_COLOR_PHASE_FIX_ACTIVE' in s,'full-message/color-phase fix marker missing')
req('SEPARATE_TEXT_SCREEN_SPRITE_POINTER_FIX_ACTIVE' in s,'dedicated text-screen marker missing')
req('BITMAP_TO_TEXT_LAST_SCANLINE_HANDOFF_ACTIVE' in s,'bitmap/text handoff marker missing')
req('COMPACT_ASSET_SOURCE_LAYOUT_ACTIVE' in s,'compact asset-layout marker missing')
req('BINARY_ARITHMETIC_STARTUP_GUARD_ACTIVE' in s,'binary arithmetic startup marker missing')
req('PAGE_COPY_STARTUP_OPTIMIZATION_ACTIVE' in s,'page-copy startup marker missing')
req('VIC_VISIBLE_TEXT_BANK_FIX_ACTIVE' in s,'VIC-visible text-bank marker missing')
req('SINGLE_VIC_BANK1_DISPLAY_ACTIVE' in s,'single VIC-bank marker missing')
req('RASTER_BANK_SWITCH_REMOVED_ACTIVE' in s,'raster bank-switch removal marker missing')
req('SID_CUTOFF_LOW_BITS_CLEAN_ACTIVE' in s,'SID cutoff-low marker missing')
req('BUILDER_ASSERTION_ENFORCEMENT_ACTIVE' in s,'builder assertion marker missing')
req('CIA2_SINGLE_WRITE_AUTHORITY_ACTIVE' in s,'CIA2 single-write marker missing')
req('SPRITE_PREVISIBLE_UPDATE_ORDER_ACTIVE' in s,'pre-visible sprite order marker missing')
req('UNIFIED_BEAT_FRAME_AUTHORITY_ACTIVE' in s,'unified beat-frame marker missing')
req(re.search(r'(?m)^Start:\n\s*sei\n\s*cld\b',s) is not None,'Start does not force binary arithmetic')
for token in ('SCROLL_FINE_ROW1_START = $07','SCROLL_FINE_ROW2_START = $05','SCROLL_FINE_ROW3_START = $03','SCROLL_FINE_ROW4_START = $01','SCROLL_FINE_WRAP = $07'):
    req(token in s,f'row fine offset contract missing {token}')
req('zpScrollFine1 = $05' in s,'row-1 scroller authority not fixed in zero page')
req('zpScrollFrame' not in s,'unused shared scroll-frame state remains')
for zp in ('zpScrollFrac1 = $18','zpScrollFrac2 = $19','zpScrollFrac3 = $1a','zpScrollFrac4 = $1b','zpScrollFine2 = $1c','zpScrollFine3 = $1d','zpScrollFine4 = $1e','zpScrollSteps = $1f'):
    req(zp in s,f'scroller state missing {zp}')
for zp in ('zpColorPhase1 = $20','zpColorPhase2 = $21','zpColorPhase3 = $22','zpColorPhase4 = $23'):
    req(zp in s,f'continuous rainbow state missing {zp}')
req('SPLIT_LINE    = $d2' in s,'text split must occur on final scanline before row-20 badline')
req('TEXT_SCREEN_ADDR = $4c00' in s,'dedicated text screen is not fixed at $4c00')
req('CHARSET_ADDR  = $5000' in s,'dedicated text charset is not fixed at $5000')
req('zpVicBank1' not in s,'stale cached VIC-bank state remains')
req(len(re.findall(r'(?m)^\s*sta \$dd00\b',code))==1,'VIC bank must be selected exactly once at startup')
req('zpVicBank0' not in s and 'zpVicBank3' not in s,'obsolete multi-bank state remains')
req('SCREEN_ADDR   = $4400' in s,'bitmap screen authority moved unexpectedly')
req('BITMAP_ADDR   = $6000' in s,'bitmap authority moved unexpectedly')
req('SPRITE_BASE   = $7f80' in s,'sprite payload authority moved unexpectedly')
req('ASSET_ADDR    = $8000' in s,'asset source block is not at $8000')
for token in ('TEXT_ROW2_LINE = $e2','TEXT_ROW3_LINE = $ea','TEXT_ROW4_LINE = $f2','BOTTOM_LINE   = $fb'):
    req(token in s,f'row raster contract missing {token}')

# Prove one lower-border update owner and four row-specific VIC phases.
req(len(re.findall(r'(?m)^\s*jsr\s+Scroller_Tick\b',code))==1,'Scroller_Tick must have exactly one call site')
def block(a,b):
    try: return s[s.index(a+':'):s.index(b+':',s.index(a+':'))]
    except ValueError:
        errors.append(f'missing block {a}..{b}');return ''
split=block('IrqSplit','IrqTextRow2')
row2irq=block('IrqTextRow2','IrqTextRow3')
row3irq=block('IrqTextRow3','IrqTextRow4')
row4irq=block('IrqTextRow4','IrqBottom')
bottom=block('IrqBottom','BeatRasterTick')
scroll=block('Scroller_Tick','Scroller_AdvancePtr1')
top=block('IrqTop','IrqSplit')
req('jsr Scroller_Tick' not in split+row2irq+row3irq+row4irq+bottom,'non-VBlank IRQ still performs heavy scrolling')
req('jsr Scroller_Tick' in top,'Scroller_Tick is not owned by raster-0 IrqTop')
req(top.index('jsr StarTick') < top.index('jsr VuBarsTick') < top.index('jsr BeatEnvDecay') < top.index('jsr Scroller_Tick'),
    'top visual/scroller order is unsafe')
irq_contract=(
    (split,'zpScrollFine1','IrqTextRow2','TEXT_ROW2_LINE',True),
    (row2irq,'zpScrollFine2','IrqTextRow3','TEXT_ROW3_LINE',True),
    (row3irq,'zpScrollFine3','IrqTextRow4','TEXT_ROW4_LINE',True),
    (row4irq,'zpScrollFine4','IrqBottom','BOTTOM_LINE',True),
)
for body,fine,next_irq,line,late in irq_contract:
    for token in (f'lda {fine}','sta $d016',f'lda #<{next_irq}',f'lda #>{next_irq}',f'lda #{line}','sta $d012'):
        req(token in body,f'row IRQ contract missing {token}')
    req('ora #$08' not in body,'text row accidentally enables 40-column edge artifacts')
    if late:
        req(len(re.findall(r'(?m)^\s*nop\s*$',body))>=11,'row handoff is not delayed into the right border')
        req(body.index('nop') < body.index(f'lda {fine}') < body.index('sta $d016'),'late row phase write order is wrong')
for token in ('jsr Scroller_UpdateRow1','jsr Scroller_UpdateRow2','jsr Scroller_UpdateRow3','jsr Scroller_UpdateRow4'):
    req(token in scroll,f'independent scroller dispatcher missing {token}')
for row in range(1,5):
    update=block(f'Scroller_UpdateRow{row}',f'Scroller_UpdateRow{row+1}' if row<4 else 'Scroller_StepPixel1')
    for token in (f'lda zpScrollFrac{row}',f'adc ScrollerSpeedQ2+{row-1}',f'sta zpScrollFrac{row}',f'jsr Scroller_StepPixel{row}'):
        req(token in update,f'row {row} speed authority missing {token}')
    step_end=f'Scroller_StepPixel{row+1}' if row<4 else 'Scroller_AdvancePtr1'
    step=block(f'Scroller_StepPixel{row}',step_end)
    for token in (f'lda zpScrollFine{row}',f'dec zpScrollFine{row}','lda #SCROLL_FINE_WRAP',f'sta zpScrollFine{row}',f'ldx zpColorPhase{row}',f'ScrollColorRow{row}',f'inc zpColorPhase{row}',f'jsr Scroller_AdvancePtr{row}'):
        req(token in step,f'row {row} pixel/shift routine missing {token}')
req('ScrollerSpeedQ2:\n        !byte 3,4,5,6' in s,'row speed table is not 0.75/1.00/1.25/1.50 px/frame')
req('MB_Section' not in scroll,'text row speed incorrectly depends on shared music-section phase')
req('sta $d016' not in scroll,'Scroller_Tick must not race VIC register writes outside row IRQs')
req(len(re.findall(r'(?m)^\s*sta\s+\$d016\b',split+row2irq+row3irq+row4irq))==4,'expected exactly four row-specific $d016 writes')
req('sta $dd00' not in split,'text split still performs a timing-sensitive VIC bank switch')
req('lda #$34' in split and 'sta $d018' in split,'text split does not select $4c00 screen/$5000 charset')
req(split.index('nop') < split.index('lda zpScrollFine1') < split.index('sta $d016') < split.index('lda #$34') < split.index('sta $d018') < split.index('lda #$1b') < split.index('sta $d011'),
    'bitmap-to-text screen/mode handoff order is wrong')
for row in range(20,25):
    req(f'TEXT_SCREEN_ADDR+40*{row}' in s,f'text row {row} is not stored in dedicated text screen')
    req(re.search(r'(?<!TEXT_)SCREEN_ADDR\+40\*'+str(row)+r'\b',s) is None,f'text row {row} still aliases bitmap screen/sprite pointers')


# Initial seeding starts at +40, but every completed stream must wrap to the
# actual message base so the title row is not skipped on subsequent cycles.
init=block('Scroller_InitPointers','Scroller_Clear')
for name in ('MessageFeatures','MessageEngine','MessageFunction','MessageModes'):
    req(f'#<({name}+40)' in init and f'#>({name}+40)' in init,
        f'{name} initial pointer must continue after the seeded 40 characters')
for row,(name,end) in enumerate((('MessageFeatures','MessageFeaturesEnd'),('MessageEngine','MessageEngineEnd'),('MessageFunction','MessageFunctionEnd'),('MessageModes','MessageModesEnd')),1):
    adv=block(f'Scroller_AdvancePtr{row}',f'Scroller_AdvancePtr{row+1}' if row<4 else 'Scroller_InitPointers')
    req(f'cmp #<{end}' in adv and f'cmp #>{end}' in adv,f'row {row} end test missing')
    req(f'lda #<{name}' in adv and f'lda #>{name}' in adv,f'row {row} does not wrap to full message base')
    req(f'{name}+40' not in adv,f'row {row} still skips the first 40 characters after wrap')
for token in ('lda #$08','sta zpColorPhase1','sta zpColorPhase2','sta zpColorPhase3','sta zpColorPhase4'):
    req(token in init,f'continuous rainbow initialization missing {token}')

# Parse only numeric !byte payloads and decode the four feature lanes.
def bytes_between(label,end):
    body=block(label,end)
    vals=[]
    for line in body.splitlines():
        if '!byte' not in line: continue
        for tok in line.split('!byte',1)[1].split(','):
            tok=tok.strip()
            if tok.startswith('$'): vals.append(int(tok[1:],16))
            elif tok.isdigit(): vals.append(int(tok))
    return vals
def decode(vals):
    out=[]
    for v in vals:
        if v==0: out.append(' ')
        elif 1<=v<=26: out.append(chr(64+v))
        elif 0x20<=v<=0x29: out.append(str(v-0x20))
        else: out.append('?')
    return ''.join(out)
lanes={
 'MessageFeatures':'MessageFeaturesEnd',
 'MessageEngine':'MessageEngineEnd',
 'MessageFunction':'MessageFunctionEnd',
 'MessageModes':'MessageModesEnd',
}
text={k:decode(bytes_between(k,v)) for k,v in lanes.items()}
for name,t in text.items():
    req(len(t)==360,f'{name} length {len(t)} != 360')
    req(len(t)%40==0,f'{name} not aligned to 40-column clauses')
phrases=(
 'ARPSID V965  CANONICAL RENDER PIPELINE',
 'NO OUTPUT STILL RUNS THE FULL PIPELINE',
 'BITPERFECT CLASSIC SID SYNTHESIS',
 'DRSID DRUM ENGINE AND FACTORY KITS',
 'DIGI SAMPLER AND AUTHENTIC D418',
 'TIMING  SAMPLE CYCLE SUBPHASE AUTHORITY',
 'ARP GATES LAND AT EXACT SAMPLE OFFSETS',
 'SEQUENCER KIT DIGI SHARE BOUNDARIES',
 'POST FX STARTS EXACTLY AT EVENT TIME',
 'HOSTS  AU2 AU3 VST3 C64 PSID RSID',
 'GUI READS IMMUTABLE SNAPSHOTS',
 'ARPSID V965  BUILT FOR REALTIME AUDIO',
)
joined='\n'.join(text.values())
for phrase in phrases: req(phrase in joined,f'feature payload missing: {phrase}')

# Branding asset contract: exact sizes and non-trivial multicolor use.
assets={'assets/uber_bitmap.bin':8000,'assets/uber_screen.bin':1000,'assets/uber_color.bin':1000}
for rel,size in assets.items():
    p=ROOT/rel;req(p.is_file(),f'missing {rel}')
    if p.is_file(): req(p.stat().st_size==size,f'{rel} size mismatch')
bitmap=(ROOT/'assets/uber_bitmap.bin').read_bytes() if (ROOT/'assets/uber_bitmap.bin').exists() else b''
screen=(ROOT/'assets/uber_screen.bin').read_bytes() if (ROOT/'assets/uber_screen.bin').exists() else b''
color=(ROOT/'assets/uber_color.bin').read_bytes() if (ROOT/'assets/uber_color.bin').exists() else b''
req(hashlib.sha256(bitmap).hexdigest()=='93da2cc04f5ce81ea8cb594a658f63024801edd0589cc717e96635a69beac53a','original bitmap hash mismatch')
req(hashlib.sha256(screen).hexdigest()=='8f6bd03ebba0c4c656f0793534d2f4380ee0c19e883d73a10112a40390c5dfcd','original screen hash mismatch')
req(hashlib.sha256(color).hexdigest()=='5740003643a51ea11280e215cba5df15c2d586e444ed21755e2af07c78b41faa','original color hash mismatch')
req(len(set(bitmap))>24,'teaser bitmap is unexpectedly trivial')
req(sum(b!=0 for b in bitmap[:20*40*8])>600,'ARPSID logo bitmap density too low')
req((ROOT/'ARPSID_TEASER_PREVIEW.png').is_file(),'teaser preview missing')
req((ROOT/'docs/AI2AI_ARPSID_V965_LOWLEVEL_HANDOFF.md').is_file(),'feature-source handoff copy missing')
req((ROOT/'docs/ARPSID_TEASER_FEATURE_MAP.md').is_file(),'feature mapping document missing')

# Label-level memory contract.
if MAP.exists():
    labels={}
    for line in MAP.read_text().splitlines():
        m=re.fullmatch(r'(\w+) = \$([0-9a-fA-F]{4})',line)
        if m: labels[m.group(1)]=int(m.group(2),16)
    for name in ('IrqTop','IrqSplit','IrqTextRow2','IrqTextRow3','IrqTextRow4','IrqBottom','Scroller_Tick','Scroller_UpdateRow1','Scroller_UpdateRow4','Scroller_StepPixel1','Scroller_StepPixel4','ScrollerSpeedQ2','ScrollColorRow1','MessageFeatures','MessageModesEnd','code_end','asset_end'):
        req(name in labels,f'label map missing {name}')
    if all(x in labels for x in ('IrqTop','IrqSplit','IrqTextRow2','IrqTextRow3','IrqTextRow4','IrqBottom','Scroller_Tick')):
        req(labels['IrqTop']<labels['IrqSplit']<labels['IrqTextRow2']<labels['IrqTextRow3']<labels['IrqTextRow4']<labels['IrqBottom']<labels['Scroller_Tick'],'IRQ/scroller layout order unexpected')
    if 'code_end' in labels: req(labels['code_end']<=0x4000,'code crosses VIC bank 1 display memory')
    if 'asset_end' in labels: req(labels['asset_end']<=0xc000,'asset block crosses $c000')
    if all(x in labels for x in ('code_end','asset_start')): req(labels['code_end']<=0x4000<0x8000<=labels['asset_start'],'code/display/asset ordering is unsafe')
else:
    errors.append('label map missing')

if errors:
    print('FAIL: ArpSID v965 teaser verifier')
    for e in errors: print(' -',e)
    sys.exit(1)
print('PASS: ArpSID v965 teaser verifier')
print('scroller=independent_rows speeds=0.75/1.00/1.25/1.50 offsets=7/5/3/1 owner=IrqTop_raster0 row_irqs=d2/e2/ea/f2 edge_guard=38col_right_border vic_bank=1 bitmap_screen=$4400 text_screen=$4c00 charset=$5000 bitmap=$6000 bank_switches_in_split=0 rainbow=continuous_color_phase message_bytes=1440 background=original_uber')
print('bitmap_sha256='+hashlib.sha256(bitmap).hexdigest())

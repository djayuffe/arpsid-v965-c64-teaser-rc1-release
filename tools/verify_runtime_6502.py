#!/usr/bin/env python3
"""Execute SID_Init and 1536 MusicTick calls in a small NMOS-6502 verifier."""
from __future__ import annotations
from pathlib import Path
import re, sys

ROOT=Path(__file__).resolve().parents[1]
PRG=ROOT/'build/uber_sound_solution.prg'
LBL=ROOT/'build/uber_sound_solution.lbl'
errors=[]
def req(c,m):
    if not c: errors.append(m)

labels={}
for line in LBL.read_text().splitlines():
    m=re.fullmatch(r'(\w+) = \$([0-9a-fA-F]{4})',line)
    if m: labels[m.group(1)]=int(m.group(2),16)
for name in ('InstallAssets','InstallStarSprites','SID_Init','MusicTick','MB_VDur','MB_Section','MB_Frame','MB_FiltVal','Scroller_Clear','Scroller_Tick','ScrollerSpeedQ2','ScrollColorRow1','ScrollColorRow2','ScrollColorRow3','ScrollColorRow4','MessageFeatures','MessageFeaturesEnd','MessageEngine','MessageEngineEnd','MessageFunction','MessageFunctionEnd','MessageModes','MessageModesEnd','BeatEnvDecay'):
    req(name in labels,f'missing map label {name}')

raw=PRG.read_bytes(); load=raw[0]|raw[1]<<8
mem=bytearray(65536); mem[load:load+len(raw)-2]=raw[2:]

C=0x01; Z=0x02; I=0x04; D=0x08; B=0x10; U=0x20; V=0x40; N=0x80
class CPU:
    def __init__(self):
        self.a=self.x=self.y=0; self.sp=0xff; self.p=U; self.pc=0; self.cycles=0
        self.writes=[]
    def setnz(self,v):
        self.p=(self.p & ~(N|Z)) | (Z if (v&255)==0 else 0) | (N if v&0x80 else 0)
        return v&255
    def push(self,v): mem[0x100+self.sp]=v&255; self.sp=(self.sp-1)&255
    def pull(self): self.sp=(self.sp+1)&255; return mem[0x100+self.sp]
    def rd(self,a): return mem[a&0xffff]
    def wr(self,a,v):
        a&=0xffff; v&=255; mem[a]=v; self.writes.append((a,v))
    def fetch(self): v=self.rd(self.pc); self.pc=(self.pc+1)&0xffff; return v
    def word(self): lo=self.fetch(); return lo | self.fetch()<<8
    def addr(self,mode):
        cross=False
        if mode=='zp': return self.fetch(),False
        if mode=='zpx': return (self.fetch()+self.x)&255,False
        if mode=='abs': return self.word(),False
        if mode=='absx':
            b=self.word(); a=(b+self.x)&0xffff; return a,(b&0xff00)!=(a&0xff00)
        if mode=='absy':
            b=self.word(); a=(b+self.y)&0xffff; return a,(b&0xff00)!=(a&0xff00)
        if mode=='indy':
            z=self.fetch(); b=self.rd(z)|self.rd((z+1)&255)<<8; a=(b+self.y)&0xffff
            return a,(b&0xff00)!=(a&0xff00)
        raise AssertionError(mode)
    def adc(self,v):
        a=self.a; c=1 if self.p&C else 0; r=a+v+c; out=r&255
        self.p=(self.p&~(C|V)) | (C if r>255 else 0) | (V if (~(a^v)&(a^out)&0x80) else 0)
        self.a=self.setnz(out)
    def sbc(self,v): self.adc(v^0xff)
    def cmp(self,r,v):
        d=(r-v)&0x1ff; self.p=(self.p&~C)|(C if r>=v else 0); self.setnz(d&255)
    def branch(self,cond):
        off=self.fetch(); off=off-256 if off&0x80 else off; self.cycles+=2
        if cond:
            old=self.pc; self.pc=(self.pc+off)&0xffff; self.cycles+=1+((old&0xff00)!=(self.pc&0xff00))
    def step(self):
        op=self.fetch()
        # implied / transfer / stack
        if op==0x18: self.p&=~C; self.cycles+=2; return
        if op==0x38: self.p|=C; self.cycles+=2; return
        if op==0xd8: self.p&=~D; self.cycles+=2; return
        if op==0xca: self.x=self.setnz(self.x-1); self.cycles+=2; return
        if op==0x88: self.y=self.setnz(self.y-1); self.cycles+=2; return
        if op==0xe8: self.x=self.setnz(self.x+1); self.cycles+=2; return
        if op==0xc8: self.y=self.setnz(self.y+1); self.cycles+=2; return
        if op==0x48: self.push(self.a); self.cycles+=3; return
        if op==0x68: self.a=self.setnz(self.pull()); self.cycles+=4; return
        if op==0xaa: self.x=self.setnz(self.a); self.cycles+=2; return
        if op==0xa8: self.y=self.setnz(self.a); self.cycles+=2; return
        if op==0x8a: self.a=self.setnz(self.x); self.cycles+=2; return
        if op==0x98: self.a=self.setnz(self.y); self.cycles+=2; return
        if op==0xea:
            self.cycles+=2; return
        if op==0x60:
            lo=self.pull(); hi=self.pull(); self.pc=((hi<<8)|lo)+1 & 0xffff; self.cycles+=6; return
        # control flow
        if op==0x4c: self.pc=self.word(); self.cycles+=3; return
        if op==0x20:
            a=self.word(); ret=(self.pc-1)&0xffff; self.push(ret>>8); self.push(ret); self.pc=a; self.cycles+=6; return
        if op in (0xd0,0xf0,0x90,0xb0,0x10,0x30):
            cond={0xd0:not(self.p&Z),0xf0:bool(self.p&Z),0x90:not(self.p&C),0xb0:bool(self.p&C),0x10:not(self.p&N),0x30:bool(self.p&N)}[op]
            self.branch(cond); return
        # accumulator shifts
        if op==0x0a:
            self.p=(self.p&~C)|(C if self.a&0x80 else 0); self.a=self.setnz((self.a<<1)&255); self.cycles+=2; return
        if op==0x4a:
            self.p=(self.p&~C)|(self.a&1); self.a=self.setnz(self.a>>1); self.cycles+=2; return
        if op==0x6a:
            c=0x80 if self.p&C else 0; nc=self.a&1; self.a=self.setnz((self.a>>1)|c); self.p=(self.p&~C)|nc; self.cycles+=2; return
        # load/store/ALU mode maps
        loads={0xa9:('imm',2),0xa5:('zp',3),0xb5:('zpx',4),0xad:('abs',4),0xbd:('absx',4),0xb9:('absy',4),0xb1:('indy',5)}
        ldxs={0xa2:('imm',2),0xa6:('zp',3),0xae:('abs',4)}
        ldys={0xa0:('imm',2),0xa4:('zp',3),0xb4:('zpx',4),0xac:('abs',4),0xbc:('absx',4)}
        if op in loads:
            m,c=loads[op]
            if m=='imm': v=self.fetch(); cross=False
            else: a,cross=self.addr(m); v=self.rd(a)
            self.a=self.setnz(v); self.cycles+=c+(1 if cross and m in ('absx','absy','indy') else 0); return
        if op in ldxs:
            m,c=ldxs[op]; v=self.fetch() if m=='imm' else self.rd(self.addr(m)[0]); self.x=self.setnz(v); self.cycles+=c; return
        if op in ldys:
            m,c=ldys[op];
            if m=='imm': v=self.fetch(); cross=False
            else: a,cross=self.addr(m); v=self.rd(a)
            self.y=self.setnz(v); self.cycles+=c+(1 if cross and m=='absx' else 0); return
        stores={0x85:('zp',3),0x95:('zpx',4),0x8d:('abs',4),0x9d:('absx',5),0x99:('absy',5),0x91:('indy',6)}
        if op in stores:
            m,c=stores[op]; a,_=self.addr(m); self.wr(a,self.a); self.cycles+=c; return
        stys={0x84:('zp',3),0x94:('zpx',4),0x8c:('abs',4)}
        if op in stys:
            m,c=stys[op]; a,_=self.addr(m); self.wr(a,self.y); self.cycles+=c; return
        groups={
          'adc':{0x69:('imm',2),0x65:('zp',3),0x75:('zpx',4),0x6d:('abs',4),0x7d:('absx',4),0x79:('absy',4)},
          'sbc':{0xe9:('imm',2),0xe5:('zp',3),0xf5:('zpx',4),0xed:('abs',4),0xfd:('absx',4),0xf9:('absy',4)},
          'and':{0x29:('imm',2),0x25:('zp',3),0x35:('zpx',4),0x2d:('abs',4),0x3d:('absx',4),0x39:('absy',4)},
          'ora':{0x09:('imm',2),0x05:('zp',3),0x15:('zpx',4),0x0d:('abs',4),0x1d:('absx',4),0x19:('absy',4)},
          'eor':{0x49:('imm',2),0x45:('zp',3),0x55:('zpx',4),0x4d:('abs',4),0x5d:('absx',4),0x59:('absy',4)},
          'cmp':{0xc9:('imm',2),0xc5:('zp',3),0xd5:('zpx',4),0xcd:('abs',4),0xdd:('absx',4),0xd9:('absy',4)},
        }
        for name,tab in groups.items():
            if op in tab:
                m,c=tab[op]
                if m=='imm': v=self.fetch(); cross=False
                else: a,cross=self.addr(m); v=self.rd(a)
                if name=='adc': self.adc(v)
                elif name=='sbc': self.sbc(v)
                elif name=='and': self.a=self.setnz(self.a&v)
                elif name=='ora': self.a=self.setnz(self.a|v)
                elif name=='eor': self.a=self.setnz(self.a^v)
                else: self.cmp(self.a,v)
                self.cycles+=c+(1 if cross and m in ('absx','absy') else 0); return
        if op in (0xe0,0xe4,0xec):
            if op==0xe0: v=self.fetch(); c=2
            elif op==0xe4: v=self.rd(self.fetch()); c=3
            else: v=self.rd(self.word()); c=4
            self.cmp(self.x,v); self.cycles+=c; return
        if op in (0x24,0x2c):
            if op==0x24: v=self.rd(self.fetch()); c=3
            else: v=self.rd(self.word()); c=4
            self.p=(self.p & ~(N|V|Z)) | (N if v&0x80 else 0) | (V if v&0x40 else 0) | (Z if (self.a&v)==0 else 0)
            self.cycles+=c; return
        # inc/dec and memory shifts
        rmw={0xe6:('inc','zp',5),0xf6:('inc','zpx',6),0xee:('inc','abs',6),0xfe:('inc','absx',7),
             0xc6:('dec','zp',5),0xd6:('dec','zpx',6),0xce:('dec','abs',6),0xde:('dec','absx',7),
             0x46:('lsr','zp',5),0x56:('lsr','zpx',6),0x4e:('lsr','abs',6),0x5e:('lsr','absx',7),
             0x66:('ror','zp',5),0x76:('ror','zpx',6),0x6e:('ror','abs',6),0x7e:('ror','absx',7)}
        if op in rmw:
            name,m,c=rmw[op]; a,_=self.addr(m); v=self.rd(a)
            if name=='inc': v=(v+1)&255
            elif name=='dec': v=(v-1)&255
            elif name=='lsr': self.p=(self.p&~C)|(v&1); v>>=1
            else:
                oldc=0x80 if self.p&C else 0; nc=v&1; v=(v>>1)|oldc; self.p=(self.p&~C)|nc
            self.wr(a,v); self.setnz(v); self.cycles+=c; return
        raise RuntimeError(f'unsupported opcode ${op:02x} at ${(self.pc-1)&0xffff:04x}')

cpu=CPU()
def call(addr,max_steps=20000):
    sentinel=0xff00; before_sp=cpu.sp; before_cycles=cpu.cycles; cpu.writes=[]
    ret=(sentinel-1)&0xffff; cpu.push(ret>>8); cpu.push(ret); cpu.pc=addr
    steps=0
    while cpu.pc!=sentinel:
        cpu.step(); steps+=1
        if steps>max_steps: raise RuntimeError(f'routine ${addr:04x} exceeded {max_steps} instructions at ${cpu.pc:04x}')
    req(cpu.sp==before_sp,f'stack imbalance in routine ${addr:04x}: {before_sp:02x}->{cpu.sp:02x}')
    return cpu.cycles-before_cycles,list(cpu.writes)

try:
    asset_install_cycles,_=call(labels['InstallAssets'],max_steps=500000)
    req(bytes(mem[0x6000:0x6000+8000])==(ROOT/'assets/uber_bitmap.bin').read_bytes(),'runtime bitmap copy mismatch')
    req(bytes(mem[0x4400:0x4400+1000])==(ROOT/'assets/uber_screen.bin').read_bytes(),'runtime bitmap-screen copy mismatch')
    req(bytes(mem[0xd800:0xd800+1000])==(ROOT/'assets/uber_color.bin').read_bytes(),'runtime Color RAM copy mismatch')
    req(bytes(mem[0x5000:0x5000+2048])==(ROOT/'assets/uber_custom_font.bin').read_bytes(),'runtime charset copy mismatch')
    sprite_init_cycles,_=call(labels['InstallStarSprites'],max_steps=50000)
    init_cycles,init_writes=call(labels['SID_Init'])
    req(any(a==0xd418 and v==0x1f for a,v in init_writes),'SID init did not set static $d418=$1f')
    req(mem[labels['MB_Section']]==0,'section not initialized to zero')
    # Mirror the exact scroller state established by Start before the first IRQ.
    integrated_scroll_clear_cycles,_=call(labels['Scroller_Clear'],max_steps=50000)
    mem[0x05]=7
    mem[0x1c]=5; mem[0x1d]=3; mem[0x1e]=1
    for a in (0x18,0x19,0x1a,0x1b,0x1f): mem[a]=0
    max_cycles=0; total_cycles=0; max_top_core_cycles=0; total_top_core_cycles=0; max_pre_sprite_cycles=0; max_full_vblank_cycles=0; calm_frames=0; sid24_tick_writes=0; bad_sid=[]; cutoff_order_errors=0; section_at=[]
    for frame in range(1536):
        cyc,writes=call(labels['MusicTick'])
        total_cycles+=cyc; max_cycles=max(max_cycles,cyc)
        sid=[(a,v) for a,v in writes if 0xd400<=a<=0xd7ff]
        bad_sid += [(frame,a,v) for a,v in sid if not 0xd400<=a<=0xd418]
        sid24_tick_writes += sum(a==0xd418 for a,_ in sid)
        addrs=[a for a,_ in sid]
        if 0xd415 not in addrs or 0xd416 not in addrs or addrs.index(0xd415)>addrs.index(0xd416): cutoff_order_errors+=1
        if frame in (0,383,384,767,768,1151,1152,1535): section_at.append((frame,mem[labels['MB_Section']]))
        # Execute the actual same-frame visual chain. Every visual consumer sees
        # one immutable BeatEnv value; BeatEnvDecay advances it exactly once last.
        beat_cyc,_=call(labels['BeatRasterTick'])
        star_cyc,_=call(labels['StarTick'],max_steps=50000)
        pre_sprite=cyc+beat_cyc+star_cyc
        max_pre_sprite_cycles=max(max_pre_sprite_cycles,pre_sprite)
        vu_cyc,_=call(labels['VuBarsTick'],max_steps=50000)
        decay_cyc,_=call(labels['BeatEnvDecay'])
        scroll_cyc,_=call(labels['Scroller_Tick'],max_steps=50000)
        top_core=pre_sprite+vu_cyc+decay_cyc
        max_full_vblank_cycles=max(max_full_vblank_cycles,top_core+scroll_cyc)
        total_top_core_cycles+=top_core
        max_top_core_cycles=max(max_top_core_cycles,top_core)
        if mem[0x0e]==0: calm_frames+=1
        req(all(mem[labels['MB_VDur']+i] != 0 for i in range(3)),f'zero duration survived frame {frame}')
    req(not bad_sid,f'out-of-range SID writes: {bad_sid[:3]}')
    req(sid24_tick_writes==0,f'MusicTick wrote $d418 {sid24_tick_writes} times')
    req(cutoff_order_errors==0,f'cutoff low/high write order failed on {cutoff_order_errors} frames')
    req(max_cycles<4000,f'MusicTick worst-case {max_cycles} cycles exceeds 4000-cycle budget')
    req(max_pre_sprite_cycles<3300,f'pre-sprite update path {max_pre_sprite_cycles} cycles risks first sprite DMA')
    req(max_top_core_cycles<9000,f'top-frame visual core worst-case {max_top_core_cycles} cycles risks raster $d2 split')
    req(max_full_vblank_cycles<10000,f'full raster-0 work {max_full_vblank_cycles} cycles risks raster $d2 split')
    conservative_vic_steal_allowance=1500
    req(max_full_vblank_cycles+conservative_vic_steal_allowance<12000,
        f'full raster-0 work plus VIC steal allowance risks split: {max_full_vblank_cycles}+{conservative_vic_steal_allowance}')
    req(calm_frames>=300,f'BeatEnv produced too few calm frames: {calm_frames}/1536')
    req(mem[labels['MB_Section']]==3,f'last frame of four-section cycle should remain section 3: {mem[labels["MB_Section"]]}')
    req(mem[labels['MB_Frame']]==0,f'1536-frame run did not wrap MB_Frame: {mem[labels["MB_Frame"]]}')
    close_cycles,close_writes=call(labels['MusicTick'])
    req(mem[labels['MB_Section']]==0,f'next frame did not close macro cycle to section 0: {mem[labels["MB_Section"]]}')
    req(mem[labels['MB_Frame']]==1,f'closure frame did not advance MB_Frame to 1: {mem[labels["MB_Frame"]]}')
    close_beat,_=call(labels['BeatRasterTick']); close_star,_=call(labels['StarTick'],max_steps=50000); close_vu,_=call(labels['VuBarsTick'],max_steps=50000); close_decay,_=call(labels['BeatEnvDecay']); close_scroll,_=call(labels['Scroller_Tick'],max_steps=50000)
    max_cycles=max(max_cycles,close_cycles)
    max_pre_sprite_cycles=max(max_pre_sprite_cycles,close_cycles+close_beat+close_star)
    max_top_core_cycles=max(max_top_core_cycles,close_cycles+close_beat+close_star+close_vu+close_decay)
    max_full_vblank_cycles=max(max_full_vblank_cycles,close_cycles+close_beat+close_star+close_vu+close_decay+close_scroll)

    # Execute all four independent row-speed/offset authorities together.
    rows=(0x4c00+40*21,0x4c00+40*22,0x4c00+40*23,0x4c00+40*24)
    expected_speeds=(3,4,5,6)  # quarter pixels per frame, rows 1..4
    expected_fines=(7,5,3,1)
    speed_results=[]; all_scroll_cycles=[]; scroll_clear_cycles=0
    req(tuple(mem[labels['ScrollerSpeedQ2']+i] for i in range(4))==expected_speeds,
        'runtime row speed table differs from 3,4,5,6 Q2')
    clear_cyc,_=call(labels['Scroller_Clear'],max_steps=50000)
    scroll_clear_cycles=clear_cyc
    mem[0x05]=expected_fines[0]  # zpScrollFine1
    mem[0x18]=0                  # zpScrollFrac1
    mem[0x19]=0                  # zpScrollFrac2
    mem[0x1a]=0                  # zpScrollFrac3
    mem[0x1b]=0                  # zpScrollFrac4
    mem[0x1c]=expected_fines[1]  # zpScrollFine2
    mem[0x1d]=expected_fines[2]  # zpScrollFine3
    mem[0x1e]=expected_fines[3]  # zpScrollFine4
    mem[0x1f]=0                  # zpScrollSteps
    previous=[bytes(mem[a:a+40]) for a in rows]
    row_shifts=[0,0,0,0]; max_simultaneous=0
    for frame in range(32):
        cyc,_=call(labels['Scroller_Tick'],max_steps=50000)
        all_scroll_cycles.append(cyc)
        current=[bytes(mem[a:a+40]) for a in rows]
        changed=[i for i in range(4) if current[i]!=previous[i]]
        max_simultaneous=max(max_simultaneous,len(changed))
        for i in changed: row_shifts[i]+=1
        previous=current
    req(tuple(row_shifts)==expected_speeds,
        f'independent row shifts={tuple(row_shifts)}, expected {expected_speeds} over 32 frames')
    req(tuple(mem[a] for a in (0x05,0x1c,0x1d,0x1e))==expected_fines,
        f'row fine phases did not close: {tuple(mem[a] for a in (0x05,0x1c,0x1d,0x1e))}')
    req(tuple(mem[a] for a in (0x18,0x19,0x1a,0x1b))==(0,0,0,0),
        f'row fractional phases did not close: {tuple(mem[a] for a in (0x18,0x19,0x1a,0x1b))}')
    req(max_simultaneous<=2,f'more than two rows shifted in one frame: {max_simultaneous}')
    speed_results=[(i+1,expected_speeds[i]/4,row_shifts[i]) for i in range(4)]
    # Initial color rows are deliberately non-uniform and remain legal VIC colors.
    call(labels['Scroller_Clear'],max_steps=50000)
    for row_addr in rows:
        colors=list(mem[0xd800+(row_addr-0x4c00):0xd800+(row_addr-0x4c00)+40])
        req(len(set(colors))>=6,f'rainbow row has too little color variety: {colors}')
        req(all(1<=c<=15 for c in colors),f'rainbow row contains black/invalid color: {colors}')
    req(max(all_scroll_cycles)<3000,
        f'scroller worst-case {max(all_scroll_cycles)} cycles exceeds 3000-cycle lower-border budget')

    # Dedicated text screen must never touch the bitmap screen sprite pointers.
    call(labels['InstallStarSprites'],max_steps=50000)
    sprite_ptr_before=bytes(mem[0x47f8:0x4800])
    req(sprite_ptr_before==bytes([0xfe,0xfe,0xfe,0xfe,0xff,0xff,0xff,0xff]),
        f'sprite pointers not initialized as expected: {sprite_ptr_before.hex()}')
    call(labels['Scroller_Clear'],max_steps=50000)
    for _ in range(512): call(labels['Scroller_Tick'],max_steps=50000)
    req(bytes(mem[0x47f8:0x4800])==sprite_ptr_before,
        'text scroller corrupted bitmap screen sprite pointers at $47f8-$47ff')

    # Long-run proof: exercise several complete 360-character message loops.
    # This catches the historical +40 wrap bug and rainbow phase discontinuity.
    call(labels['Scroller_Clear'],max_steps=50000)
    mem[0x05]=expected_fines[0]
    for a in (0x18,0x19,0x1a,0x1b): mem[a]=0
    mem[0x1c]=expected_fines[1]; mem[0x1d]=expected_fines[2]; mem[0x1e]=expected_fines[3]
    mem[0x1f]=0
    previous=[bytes(mem[a:a+40]) for a in rows]
    long_shifts=[0,0,0,0]; long_max_simultaneous=0; long_max_cycles=0
    for frame in range(4096):
        cyc,_=call(labels['Scroller_Tick'],max_steps=50000)
        long_max_cycles=max(long_max_cycles,cyc)
        current=[bytes(mem[a:a+40]) for a in rows]
        changed=[i for i in range(4) if current[i]!=previous[i]]
        long_max_simultaneous=max(long_max_simultaneous,len(changed))
        for i in changed: long_shifts[i]+=1
        previous=current
    expected_long=tuple(s*4096//32 for s in expected_speeds)
    req(tuple(long_shifts)==expected_long,
        f'long-run row shifts={tuple(long_shifts)}, expected {expected_long}')
    req(long_max_simultaneous<=2,
        f'long-run phase schedule shifted {long_max_simultaneous} rows in one frame')
    req(long_max_cycles<3000,
        f'long-run scroller worst-case {long_max_cycles} cycles exceeds budget')
    ptr_zp=((0x10,0x11),(0x12,0x13),(0x14,0x15),(0x16,0x17))
    message_pairs=(('MessageFeatures','MessageFeaturesEnd'),('MessageEngine','MessageEngineEnd'),('MessageFunction','MessageFunctionEnd'),('MessageModes','MessageModesEnd'))
    for i,((lo,hi),(start,end)) in enumerate(zip(ptr_zp,message_pairs)):
        length=labels[end]-labels[start]
        req(length==360,f'{start} runtime length {length} != 360')
        got=mem[lo] | mem[hi]<<8
        expected=labels[start]+((40+long_shifts[i])%length)
        req(got==expected,f'{start} pointer ${got:04x}, expected ${expected:04x} after full loops')
        expected_color=(8+long_shifts[i])&0x0f
        req(mem[0x20+i]==expected_color,
            f'row {i+1} rainbow phase {mem[0x20+i]}, expected {expected_color}')
except Exception as exc:
    errors.append(f'6502 execution failed: {exc}')
    asset_install_cycles=init_cycles=max_cycles=total_cycles=max_top_core_cycles=total_top_core_cycles=max_pre_sprite_cycles=max_full_vblank_cycles=calm_frames=0; section_at=[]; all_scroll_cycles=[]; speed_results=[]; scroll_clear_cycles=0

if errors:
    print('FAIL: executable 6502 music runtime audit')
    for e in errors: print(' -',e)
    sys.exit(1)
print('PASS: executable 6502 music runtime audit')
print(f'asset_install_cycles={asset_install_cycles} init_cycles={init_cycles} sprite_init_cycles={sprite_init_cycles} frames=1536 max_music_cycles={max_cycles} avg_music_cycles={total_cycles/1536:.1f} max_pre_sprite_cycles={max_pre_sprite_cycles} max_top_core_cycles={max_top_core_cycles} avg_top_core_cycles={total_top_core_cycles/1536:.1f} max_full_vblank_cycles={max_full_vblank_cycles} vic_steal_allowance=1500 calm_frames={calm_frames}')
print('section_samples='+','.join(f'{f}:{s}' for f,s in section_at))
print('sid_d418_tick_writes=0 cutoff_order=low_then_high stack_balance=PASS')
print(f'scroller_cycles_clear={scroll_clear_cycles} max_tick={max(all_scroll_cycles) if all_scroll_cycles else 0} speed_results={speed_results} long_run_frames=4096')

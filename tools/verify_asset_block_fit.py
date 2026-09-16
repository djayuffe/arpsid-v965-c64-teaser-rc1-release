#!/usr/bin/env python3
from pathlib import Path
import re, sys

ROOT = Path(__file__).resolve().parents[1]
ASM = ROOT / "src" / "uber_intro.asm"
s = ASM.read_text()
errors = []

def require(cond, msg):
    if not cond:
        errors.append(msg)

def count_asset_bytes():
    require("* = ASSET_ADDR" in s, "ASSET_ADDR block missing")
    if "* = ASSET_ADDR" not in s:
        return 0, []
    asset = s.split("* = ASSET_ADDR", 1)[1]
    total = 0
    details = []
    for line in asset.splitlines():
        code = line.split(";", 1)[0].strip()
        if not code:
            continue
        if code.startswith("!bin"):
            m = re.search(r'!bin\s+"([^"]+)"', code)
            if m:
                p = ROOT / m.group(1)
                require(p.exists(), f"missing binary asset {m.group(1)}")
                sz = p.stat().st_size if p.exists() else 0
                total += sz
                details.append((m.group(1), sz))
        if "!byte" in code:
            part = code.split("!byte", 1)[1]
            n = len([x for x in part.split(",") if x.strip()])
            total += n
    return total, details

total, details = count_asset_bytes()
m_addr = re.search(r"(?m)^ASSET_ADDR\s*=\s*\$([0-9a-fA-F]+)", s)
require(m_addr is not None, "ASSET_ADDR constant missing")
asset_addr = int(m_addr.group(1), 16) if m_addr else 0
limit_end = 0xc000
limit = limit_end - asset_addr
headroom = limit - total
require(asset_addr >= 0x8000, f"asset source must remain above live VIC bank 1: ${asset_addr:04x}")
require(total < limit, f"asset block estimate crosses $c000: bytes={total} limit={limit}")
require(headroom >= 256, f"asset block headroom too small: {headroom} bytes")
require('!error "Asset block crossed $c000."' in s, "ACME asset boundary guard missing")


require('MEGABLAST_MUSIC_UTILIZE_ACTIVE' in s, 'MEGABLAST_MUSIC_UTILIZE marker missing')

if errors:
    print('FAIL: asset block fit')
    for e in errors:
        print(' -', e)
    print(f'asset_start=${asset_addr:04x} asset_bytes={total} limit={limit} headroom={headroom}')
    sys.exit(1)
print('PASS: asset block fit')
print(f'asset_start=${asset_addr:04x} asset_bytes={total} limit={limit} headroom={headroom}')
for name, size in details:
    print(f'{name}={size}')

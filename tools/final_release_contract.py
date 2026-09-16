#!/usr/bin/env python3
from pathlib import Path
import hashlib, sys
ROOT=Path(__file__).resolve().parents[1]
required=[
    'README.md','RELEASE_NOTES_ARPSID_V965_TEASER.md','ARPSID_TEASER_AUDIT.md',
    'BUILD_STATUS.txt','RELEASE_SHA256.txt','SHA256SUMS.txt',
    'ARPSID_TEASER_PREVIEW.png','ARPSID_V965_TEASER_RC1.prg',
    'build/uber_sound_solution.prg','build/uber_sound_solution.lbl',
    'src/uber_intro.asm','docs/AI2AI_ARPSID_V965_LOWLEVEL_HANDOFF.md',
    'docs/ARPSID_TEASER_FEATURE_MAP.md','docs/MEGABLAST_MUSIC_AUDIT.md',
    'tools/verify_vic_screen_isolation.py','tools/verify_builder_assertions.py'
]
errors=[]
for rel in required:
    if not (ROOT/rel).is_file(): errors.append(f'missing release file {rel}')
if (ROOT/'src/uber_intro_full.asm').exists(): errors.append('duplicate production ASM source remains')
status={}
if (ROOT/'BUILD_STATUS.txt').exists():
    for line in (ROOT/'BUILD_STATUS.txt').read_text().splitlines():
        if '=' in line:
            k,v=line.split('=',1);status[k]=v
expected={
    'release':'ARPSID_V965_C64_TEASER_RC1',
    'verify':'PASS',
    'active_marker':'ARPSID_V965_TEASER_RELEASE_ACTIVE',
    'background_marker':'ORIGINAL_UBER_BACKGROUND_RESTORED_ACTIVE',
    'single_vic_bank_marker':'SINGLE_VIC_BANK1_DISPLAY_ACTIVE',
    'raster_bank_switch_marker':'RASTER_BANK_SWITCH_REMOVED_ACTIVE',
    'unified_beat_marker':'UNIFIED_BEAT_FRAME_AUTHORITY_ACTIVE',
    'sprite_deadline_marker':'SPRITE_PREVISIBLE_UPDATE_ORDER_ACTIVE',
    'cia2_authority_marker':'CIA2_SINGLE_WRITE_AUTHORITY_ACTIVE',
    'builder_assertion_marker':'BUILDER_ASSERTION_ENFORCEMENT_ACTIVE',
    'sid_cutoff_low_marker':'SID_CUTOFF_LOW_BITS_CLEAN_ACTIVE',
    'screen_isolation_marker':'SEPARATE_TEXT_SCREEN_SPRITE_POINTER_FIX_ACTIVE',
    'mode_handoff_marker':'BITMAP_TO_TEXT_LAST_SCANLINE_HANDOFF_ACTIVE',
    'asset_layout_marker':'COMPACT_ASSET_SOURCE_LAYOUT_ACTIVE',
    'binary_math_marker':'BINARY_ARITHMETIC_STARTUP_GUARD_ACTIVE',
    'page_copy_marker':'PAGE_COPY_STARTUP_OPTIMIZATION_ACTIVE',
    'text_bank_marker':'VIC_VISIBLE_TEXT_BANK_FIX_ACTIVE',
    'scroller_marker':'VBLANK_SYNCED_SMOOTH_SCROLLER_ACTIVE',
    'scroller_vblank_marker':'VBLANK_TOP_SCROLLER_AUTHORITY_ACTIVE',
    'scroller_full_loop_marker':'FULL_MESSAGE_LOOP_AND_COLOR_PHASE_FIX_ACTIVE',
    'player':'3_voice_tracker',
    'frame_authority':'IrqTop_raster0',
    'vic_bank':'1',
    'cia2_dd00_writes':'1',
    'bitmap_screen':'$4400',
    'text_screen':'$4c00',
    'bitmap':'$6000',
    'text_vic_bank':'1',
    'text_charset':'$5000',
    'text_d018':'$34',
    'text_vic_visibility':'ROM_free_bank1_RAM',
    'sprite_pointer_range':'$47f8-$47ff',
    'sprite_pointer_isolation':'PASS',
    'split_cia2_bank_writes':'0',
    'scroller':'four_row_vic2_independent_x_speed_glyph_edge_clean_full_loop',
    'scroller_update_authority':'IrqTop_raster0_after_visuals',
    'bottom_irq_authority':'lightweight_vector_reset_no_jsr',
    'scroller_edge_mode':'38_column_hidden_fetch_edges',
    'scroller_row_handoff':'right_border_final_scanline',
    'scroller_pixels_per_frame':'0.75,1.00,1.25,1.50',
    'scroller_character_wrap':'full_360_character_stream',
    'scroller_runtime':'PASS',
    'runtime_asset_copy':'PASS',
    'startup_decimal_mode':'forced_binary_cld',
    'startup_nmi_vector':'installed_before_asset_copy',
    'nmi_stub':'preserve_A_ack_CIA2',
    'startup_vic_irq_clear':'all_flags_then_raster_only',
    'fallback_builder_assertions':'PASS',
    'sid_cutoff_low_bits':'masked_0_2',
    'beat_authority':'immutable_per_frame_then_BeatEnvDecay',
    'sid_policy':'static_d418_no_pumping',
    'source_authority':'single_canonical_asm',
    'reproducible_build':'PASS',
    'manifest_coverage':'complete',
    'scroller_initial_fine_offsets':'7,5,3,1',
    'scroller_max_simultaneous_row_shifts':'2',
    'scroller_long_run_frames':'4096',
    'runtime_max_music_cycles':'1808',
    'runtime_max_pre_sprite_cycles':'3044',
    'runtime_max_top_core_cycles':'4830',
    'runtime_max_full_vblank_cycles':'6545',
    'runtime_vic_steal_allowance':'1500',
    'asset_start':'$8000',
    'asset_end':'$b5a8',
    'code_end':'$1b60',
    'prg_end':'$b5a8',
    'prg_size_bytes':'44457',
}
for k,v in expected.items():
    if status.get(k)!=v: errors.append(f'BUILD_STATUS {k}={status.get(k)!r}, expected {v!r}')
readme=(ROOT/'README.md').read_text() if (ROOT/'README.md').exists() else ''
for token in (
    'ArpSID v965','Release Candidate 1','0.75 pixel/frame','1.50 pixels/frame',
    '7/5/3/1','4096-frame','360-character','continuous rainbow','1536-frame',
    '13736 / 16384','SINGLE_VIC_BANK1_DISPLAY_ACTIVE','VBLANK_TOP_SCROLLER_AUTHORITY_ACTIVE',
    'UNIFIED_BEAT_FRAME_AUTHORITY_ACTIVE','SPRITE_PREVISIBLE_UPDATE_ORDER_ACTIVE',
    'BUILDER_ASSERTION_ENFORCEMENT_ACTIVE','38-column','right border','UBER SOUND SOLUTION',
    '$4400','$4c00','$5000','$6000','VIC bank 1','$d2','sprite pointers','CLD',
    '195254 cycles','44457 bytes','3044','6545','1500-cycle VIC steal allowance'
):
    if token not in readme: errors.append(f'README missing current fact: {token}')
if (ROOT/'ARPSID_V965_TEASER_RC1.prg').exists() and (ROOT/'build/uber_sound_solution.prg').exists():
    if (ROOT/'ARPSID_V965_TEASER_RC1.prg').read_bytes()!=(ROOT/'build/uber_sound_solution.prg').read_bytes():
        errors.append('top-level teaser PRG diverges from verified build PRG')
release_sha=ROOT/'RELEASE_SHA256.txt'
if release_sha.is_file() and (ROOT/'build/uber_sound_solution.prg').is_file():
    lines=[line.split(None,1) for line in release_sha.read_text().splitlines() if line.strip()]
    found={rel.strip():sha for sha,rel in lines if len(sha)==64}
    expected_sha=hashlib.sha256((ROOT/'build/uber_sound_solution.prg').read_bytes()).hexdigest()
    for rel in ('build/uber_sound_solution.prg','ARPSID_V965_TEASER_RC1.prg'):
        if found.get(rel)!=expected_sha: errors.append(f'RELEASE_SHA256 missing/current hash mismatch for {rel}')
if errors:
    print('FAIL: final release contract')
    for e in errors: print(' -',e)
    sys.exit(1)
print('PASS: final release contract')
print('identity=ARPSID_V965_C64_TEASER_RC1 artifacts=present status=coherent')

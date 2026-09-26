; =============================================================================
; Copyright (C) 2026 Ulf Bertilsson
; SPDX-License-Identifier: GPL-3.0-or-later
; ARPSID V965 — canonical render pipeline teaser for C64
; ARPSID_V965_TEASER_RELEASE_ACTIVE
; VBLANK_SYNCED_SMOOTH_SCROLLER_ACTIVE
; VBLANK_TOP_SCROLLER_AUTHORITY_ACTIVE
; VARIABLE_SPEED_RAINBOW_SCROLLER_ACTIVE
; INDEPENDENT_ROW_OFFSET_SPEED_SCROLLER_ACTIVE
; GLYPH_EDGE_CLEAN_SCROLL_ACTIVE
; RIGHT_BORDER_D016_HANDOFF_ACTIVE
; TEXT_38_COLUMN_EDGE_GUARD_ACTIVE
; FULL_MESSAGE_LOOP_AND_COLOR_PHASE_FIX_ACTIVE
; SEPARATE_TEXT_SCREEN_SPRITE_POINTER_FIX_ACTIVE
; BITMAP_TO_TEXT_LAST_SCANLINE_HANDOFF_ACTIVE
; COMPACT_ASSET_SOURCE_LAYOUT_ACTIVE
; BINARY_ARITHMETIC_STARTUP_GUARD_ACTIVE
; PAGE_COPY_STARTUP_OPTIMIZATION_ACTIVE
; VIC_VISIBLE_TEXT_BANK_FIX_ACTIVE
; SINGLE_VIC_BANK1_DISPLAY_ACTIVE
; RASTER_BANK_SWITCH_REMOVED_ACTIVE
; UNIFIED_BEAT_FRAME_AUTHORITY_ACTIVE
; SPRITE_PREVISIBLE_UPDATE_ORDER_ACTIVE
; CIA2_SINGLE_WRITE_AUTHORITY_ACTIVE
; BUILDER_ASSERTION_ENFORCEMENT_ACTIVE
; SID_CUTOFF_LOW_BITS_CLEAN_ACTIVE
; ORIGINAL_UBER_BACKGROUND_RESTORED_ACTIVE
; BASIC: 10 SYS4096
; =============================================================================

!cpu 6510

* = $0801
!byte $0b,$08,$0a,$00,$9e,$34,$30,$39,$36,$00,$00,$00 ; 10 SYS4096

BITMAP_ADDR   = $6000      ; VIC bank 1 bitmap at bank offset $2000
SCREEN_ADDR   = $4400      ; VIC bank 1 bitmap screen and sprite-pointer authority
TEXT_SCREEN_ADDR = $4c00   ; VIC bank 1 dedicated text screen at offset $0c00
COLOR_RAM     = $d800
CHARSET_ADDR  = $5000      ; VIC bank 1 RAM charset at offset $1000
ASSET_ADDR    = $8000      ; source block above the live VIC bank; RAM under BASIC is visible
SPLIT_LINE    = $d2        ; final scanline of bitmap row 19; switch in right border
TEXT_ROW2_LINE = $e2
TEXT_ROW3_LINE = $ea
TEXT_ROW4_LINE = $f2
BOTTOM_LINE   = $fb
SCROLL_FINE_ROW1_START = $07
SCROLL_FINE_ROW2_START = $05
SCROLL_FINE_ROW3_START = $03
SCROLL_FINE_ROW4_START = $01
SCROLL_FINE_WRAP = $07
SPRITE_BASE   = $7f80      ; two sprite images after the bank-1 bitmap payload

zpSrcLo       = $fb
zpSrcHi       = $fc
zpDstLo       = $fd
zpDstHi       = $fe
zpCntLo       = $02
zpCntHi       = $03
zpMsgPtr1Lo   = $10
zpMsgPtr1Hi   = $11
zpMsgPtr2Lo   = $12
zpMsgPtr2Hi   = $13
zpMsgPtr3Lo   = $14
zpMsgPtr3Hi   = $15
zpMsgPtr4Lo   = $16
zpMsgPtr4Hi   = $17
zpScrollFine1 = $05
zpScrollFrac1 = $18
zpScrollFrac2 = $19
zpScrollFrac3 = $1a
zpScrollFrac4 = $1b
zpScrollFine2 = $1c
zpScrollFine3 = $1d
zpScrollFine4 = $1e
zpScrollSteps = $1f
zpColorPhase1 = $20
zpColorPhase2 = $21
zpColorPhase3 = $22
zpColorPhase4 = $23
MusicStep     = $08
BeatEnv       = $0e
StarFrame     = $0f

* = $1000
Start:
        sei
        cld                     ; all ADC/SBC music and scroll math is binary
        ldx #$ff
        txs
        lda #$2f
        sta $00
        lda #$35
        sta $01

        ; With HIRAM off, hardware vectors come from RAM. Install the NMI
        ; vector before the long asset-copy phase so an external NMI can never
        ; jump through uninitialized $fffa/$fffb.
        lda #<NmiStub
        sta $fffa
        lda #>NmiStub
        sta $fffb

        lda #$7f
        sta $dc0d
        sta $dd0d
        lda $dc0d
        lda $dd0d

        lda $dd02
        ora #%00000011
        sta $dd02

        lda $dd00
        and #%11111100
        ora #%00000010          ; CIA2 inverted select: %10 = VIC bank 1 ($4000-$7fff)
        sta $dd00               ; one VIC bank owns bitmap, text, charset and sprites

        lda #$00
        sta $d015
        sta $d020
        sta $d021
        lda #$0b              ; display off while copying assets
        sta $d011

        jsr InstallAssets
        jsr InstallStarSprites
        jsr SID_Init
        jsr Scroller_Clear

        lda #SCROLL_FINE_ROW1_START
        sta zpScrollFine1
        lda #SCROLL_FINE_ROW2_START
        sta zpScrollFine2
        lda #SCROLL_FINE_ROW3_START
        sta zpScrollFine3
        lda #SCROLL_FINE_ROW4_START
        sta zpScrollFine4
        lda #0
        sta zpScrollFrac1
        sta zpScrollFrac2
        sta zpScrollFrac3
        sta zpScrollFrac4
        sta zpScrollSteps
        jsr Scroller_InitPointers
        lda #0
        sta MusicStep
        sta BeatEnv
        sta StarFrame
        ; The active Megablast player initializes its own sequence pointers.

        lda #<IrqTop
        sta $fffe
        lda #>IrqTop
        sta $ffff
        lda #$0f
        sta $d019               ; clear all pending VIC-II IRQ flags
        lda #$01
        sta $d01a               ; enable raster IRQ only
        lda #$00
        sta $d012
        lda $d011
        and #$7f
        sta $d011
        cli
Main:
        jmp Main

InstallAssets:
        lda #<uber_bitmap_src
        sta zpSrcLo
        lda #>uber_bitmap_src
        sta zpSrcHi
        lda #<BITMAP_ADDR
        sta zpDstLo
        lda #>BITMAP_ADDR
        sta zpDstHi
        lda #<8000
        sta zpCntLo
        lda #>8000
        sta zpCntHi
        jsr CopyCount

        lda #<uber_screen_src
        sta zpSrcLo
        lda #>uber_screen_src
        sta zpSrcHi
        lda #<SCREEN_ADDR
        sta zpDstLo
        lda #>SCREEN_ADDR
        sta zpDstHi
        lda #<1000
        sta zpCntLo
        lda #>1000
        sta zpCntHi
        jsr CopyCount

        lda #<uber_color_src
        sta zpSrcLo
        lda #>uber_color_src
        sta zpSrcHi
        lda #<COLOR_RAM
        sta zpDstLo
        lda #>COLOR_RAM
        sta zpDstHi
        lda #<1000
        sta zpCntLo
        lda #>1000
        sta zpCntHi
        jsr CopyCount

        lda #<uber_charset_src
        sta zpSrcLo
        lda #>uber_charset_src
        sta zpSrcHi
        lda #<CHARSET_ADDR
        sta zpDstLo
        lda #>CHARSET_ADDR
        sta zpDstHi
        lda #<2048
        sta zpCntLo
        lda #>2048
        sta zpCntHi
        jsr CopyCount
        rts

CopyCount:
        ; Copy whole 256-byte pages first.  Indexed-indirect addressing handles
        ; arbitrary low-byte alignment; advancing the pointer high byte after
        ; Y wraps advances exactly one page.
        ldx zpCntHi
        beq CopyCount_tail
CopyCount_page:
        ldy #0
CopyCount_page_loop:
        lda (zpSrcLo),y
        sta (zpDstLo),y
        iny
        bne CopyCount_page_loop
        inc zpSrcHi
        inc zpDstHi
        dex
        bne CopyCount_page
CopyCount_tail:
        ldx zpCntLo
        beq CopyCount_done
        ldy #0
CopyCount_tail_loop:
        lda (zpSrcLo),y
        sta (zpDstLo),y
        iny
        dex
        bne CopyCount_tail_loop
CopyCount_done:
        rts


; -----------------------------------------------------------------------------
; Star sprites from uploaded previous starfield idea, implemented safely over bitmap.
; Sprite data sits at $7f80/$7fc0 in VIC bank 1, after the bitmap payload.
; -----------------------------------------------------------------------------
InstallStarSprites:
        lda #<StarSpriteData
        sta zpSrcLo
        lda #>StarSpriteData
        sta zpSrcHi
        lda #<SPRITE_BASE
        sta zpDstLo
        lda #>SPRITE_BASE
        sta zpDstHi
        lda #<128
        sta zpCntLo
        lda #>128
        sta zpCntHi
        jsr CopyCount

        lda #$fe
        ldx #0
InstallStarSprites_ptrs:
        sta SCREEN_ADDR+$03f8,x
        inx
        cpx #4
        bne InstallStarSprites_ptrs
        lda #$ff
InstallStarSprites_ptrs2:
        sta SCREEN_ADDR+$03f8,x
        inx
        cpx #8
        bne InstallStarSprites_ptrs2

        lda #$ff
        sta $d015               ; enable all 8 sprites
        lda #$00
        sta $d010               ; all X < 256
        sta $d017               ; no Y expansion
        sta $d01d               ; no X expansion
        sta $d01b               ; sprites in front
        sta $d01c               ; mono sprites
        ldx #0                  ; sprite index 0..7
        ldy #0                  ; VIC position register offset 0,2,..14
InstallStarSprites_initpos:
        lda StarXInit,x
        sta $d000,y
        lda StarYInit,x
        sta $d001,y
        iny
        iny
        inx
        cpx #8
        bne InstallStarSprites_initpos
        ldx #0
InstallStarSprites_initcol:
        lda StarColorInit,x
        sta $d027,x
        inx
        cpx #8
        bne InstallStarSprites_initcol
        rts

; RELEASE_LOCK: logo fly-off sprites stay top-panel only.
; RELEASE_LOCK: depth orbit keeps sprite logic simple.
StarTick:
        inc StarFrame

        ; Beat-aware sprite pop. BeatEnv is immutable for all visual consumers
        ; in this frame and decays once in BeatEnvDecay after Star/VU processing.
        lda BeatEnv
        beq StarTick_no_beat_exp
        cmp #$0c              ; BeatEnv peaks at $0f: strong first frames, then small pop
        bcc StarTick_small_pop
        lda #$ff              ; big kick/clap pop: all sprites react
        bne StarTick_pop_ready
StarTick_small_pop:
        lda #$55              ; smaller beat: alternating sprites
StarTick_pop_ready:
        sta $d01d
        sta $d017
        jmp StarTick_beat_exp_done
StarTick_no_beat_exp:
        lda #$00
        sta $d01d
        sta $d017
StarTick_beat_exp_done:

        ; Logo sparkle: on beat, alternate star/note sprite shapes across logo highlights.
        lda BeatEnv
        beq LogoSparkle_NoShapeFlip
        ldx #0
LogoSparkle_ShapeLoop:
        lda LogoSparklePtr,x
        sta SCREEN_ADDR+$03f8,x
        inx
        cpx #8
        bne LogoSparkle_ShapeLoop
        jmp LogoSparkle_ShapeDone
LogoSparkle_NoShapeFlip:
        ldx #0
LogoSparkle_ResetShapeLoop:
        lda LogoSparklePtrIdle,x
        sta SCREEN_ADDR+$03f8,x
        inx
        cpx #8
        bne LogoSparkle_ResetShapeLoop
LogoSparkle_ShapeDone:

        ldx #0
StarTick_loop:
        lda $d000,x
        clc
        adc StarSpeedByReg,x
        ldy BeatEnv
        beq StarTick_no_beat_speed
        clc                     ; beat boost is exactly +7, independent of prior X overflow
        adc #$07              ; FLYOFF: sprites shoot off logo faster while beat envelope is alive
StarTick_no_beat_speed:
        cmp #$e2              ; FLYOFF: earlier wrap keeps sprites cleanly inside top/logo panel
        bcc StarTick_xok
        lda StarXReset,x
StarTick_xok:
        sta $d000,x

        ; FLYOFF: apply a beat offset, but always restore the exact baseline afterward.
        txa
        lsr
        tay
        lda StarYInit,y
        pha
        lda BeatEnv
        beq StarTick_y_baseline
        pla
        clc
        adc StarFlyY,y
        jmp StarTick_y_store
StarTick_y_baseline:
        pla
StarTick_y_store:
        sta $d001,x
        txa
        lsr
        tay
        lda StarFrame
        and #$0f
        clc
        adc StarTwinkleOff,y
        and #$0f
        tay
        lda BeatEnv
        beq StarTick_normal_color
        lda StarBeatColors,y
        bne StarTick_color_ready
StarTick_normal_color:
        lda StarTwinkleColors,y
StarTick_color_ready:
        txa
        lsr
        tax
        sta $d027,x
        txa
        asl
        tax
        inx
        inx
        cpx #16
        bne StarTick_loop
        rts

; Single beat-envelope authority: all same-frame consumers observe one value,
; then the envelope advances exactly once at the frame boundary.
BeatEnvDecay:
        lda BeatEnv
        beq BeatEnvDecay_done
        cmp #3
        bcc BeatEnvDecay_clear
        sec
        sbc #2                  ; 15->13->...->1->0, leaving calm frames before next bass
        sta BeatEnv
        rts
BeatEnvDecay_clear:
        lda #0
        sta BeatEnv
BeatEnvDecay_done:
        rts


; -----------------------------------------------------------------------------
; Active music: Megablast three-voice tracker.
; Previous experimental players are not assembled or referenced by this release.
; -----------------------------------------------------------------------------
; MEGABLAST_MUSIC_UTILIZE_ACTIVE
; Source: uploaded megablast-c64-cracktro-v3.zip / src/cracktro.asm
; The demo uses the uploaded Megablast three-voice tracker at one PAL-frame tick.
; Loop commands are $fe,
; rests $ff, instrument commands $80..$83, note+duration pairs otherwise.
; MEGABLAST_CONTINUE_PLUS_ACTIVE: fixed gate-off, section-aware filter/PWM
; groove overlay, longer evolving polyrhythm without $d418 pumping.
; MEGABLAST_DEEP_AUDIT_FIX_ACTIVE: guarded stream/frequency timing, live slow-wah
; composition, synchronized visual clock, exact PWM clamps and clean source tree.
; -----------------------------------------------------------------------------
SID = $d400
MBPtrLo = $fb
MBPtrHi = $fc
MBArpLo = $fd
MBArpHi = $fe

SID_Init:
        ldx #$18
        lda #0
MB_InitSidClear:
        sta SID,x
        dex
        bpl MB_InitSidClear

        ldx #2
MB_InitVoiceLoop:
        lda MB_StartLo,x
        sta MB_VPtrLo,x
        lda MB_StartHi,x
        sta MB_VPtrHi,x
        lda #1
        sta MB_VDur,x
        lda #0
        sta MB_VNote,x
        sta MB_VArpIdx,x
        sta MB_VInst,x
        dex
        bpl MB_InitVoiceLoop

        lda #$00
        sta SID+16
        lda #$08
        sta SID+17
        lda #$00
        sta SID+21
        lda #$40
        sta SID+22
        lda #$a4              ; resonance + voice 3 routed, as uploaded source
        sta SID+23
        lda #$1f              ; static full volume, no $d418 pumping
        sta SID+24
        lda #0
        sta MB_PWMlo
        lda #$08
        sta MB_PWMhi
        lda #$01
        sta MB_PWMdir
        lda #$40
        sta MB_FiltVal
        lda #$01
        sta MB_FiltStep
        lda #0
        sta MB_Frame
        sta MB_Section
        sta BeatEnv
        rts

MusicTick:
        ldx #0
        jsr MB_VoiceUpdate
        ldx #1
        jsr MB_VoiceUpdate
        ldx #2
        jsr MB_VoiceUpdate
        jsr MB_PWMUpdate
        jsr MB_FiltUpdate
        jsr MB_GrooveOverlay
        rts

MB_VoiceUpdate:
        lda MB_VPtrLo,x
        sta MBPtrLo
        lda MB_VPtrHi,x
        sta MBPtrHi
        lda MB_VDur,x
        sec
        sbc #1
        sta MB_VDur,x
        beq MB_VoiceFetch
        jmp MB_Effects

MB_VoiceFetch:
        ldy #0
MB_StreamLoop:
        lda (MBPtrLo),y
        cmp #$fe
        beq MB_LoopCommand
        cmp #$ff
        beq MB_RestCommand
        cmp #$80
        bcs MB_InstCommand
        sta MB_VNote,x
        iny
        lda (MBPtrLo),y
        bne MB_NoteDurationOk
        lda #1                  ; malformed zero duration must not underflow to 255 frames
MB_NoteDurationOk:
        sta MB_VDur,x
        iny
        lda #0
        sta MB_VArpIdx,x
        jsr MB_TriggerNote
        jmp MB_StorePointer

MB_InstCommand:
        and #$7f
        cmp #4
        bcc MB_InstValid
        lda #0                  ; clamp malformed instrument commands to safe lead instrument
MB_InstValid:
        sta MB_VInst,x
        iny
        jmp MB_StreamLoop

MB_RestCommand:
        iny
        lda (MBPtrLo),y
        bne MB_RestDurationOk
        lda #1                  ; malformed zero rest cannot create a 255-frame stall
MB_RestDurationOk:
        sta MB_VDur,x
        iny
        jsr MB_GateOff
        jmp MB_StorePointer

MB_LoopCommand:
        cpx #1
        bne MB_LoopNoSectionTick
        inc MB_Section
        lda MB_Section
        and #$03
        sta MB_Section
MB_LoopNoSectionTick:
        lda MB_StartLo,x
        sta MBPtrLo
        lda MB_StartHi,x
        sta MBPtrHi
        ldy #0
        jmp MB_StreamLoop

MB_StorePointer:
        tya
        clc
        adc MBPtrLo
        sta MB_VPtrLo,x
        lda MBPtrHi
        adc #0
        sta MB_VPtrHi,x
        jmp MB_Effects

MB_Effects:
        lda MB_VInst,x
        tay
        lda MB_InstArpLo,y
        sta MBArpLo
        lda MB_InstArpHi,y
        sta MBArpHi
        lda MBArpLo
        ora MBArpHi
        beq MB_EffectsNoArp
        lda MB_VArpIdx,x
        tay
        lda (MBArpLo),y
        cmp #$80
        bne MB_EffectsHaveOffset
        ldy #0
        tya
        sta MB_VArpIdx,x
        lda (MBArpLo),y
MB_EffectsHaveOffset:
        pha
        lda MB_VArpIdx,x
        clc
        adc #1
        sta MB_VArpIdx,x
        pla
        clc
        adc MB_VNote,x
        jmp MB_EffectsWriteFreq
MB_EffectsNoArp:
        lda MB_VNote,x
MB_EffectsWriteFreq:
        jsr MB_CalcFreq
        lda MB_SidOff,x
        tay
        lda MB_FreqLo
        sta SID+0,y
        lda MB_FreqHi
        sta SID+1,y
        rts

MB_TriggerNote:
        tya
        sta MB_SavedY
        lda MB_VInst,x
        tay
        txa
        pha
        lda MB_SidOff,x
        tax
        cpx #7
        bne MB_TriggerNoBassFlash
        lda #$0f              ; drive existing visual beat envelope from uploaded bass voice
        sta BeatEnv
MB_TriggerNoBassFlash:
        cpx #14
        beq MB_TriggerSkipPW
        lda MB_InstPWlo,y
        sta SID+2,x
        lda MB_InstPWhi,y
        sta SID+3,x
MB_TriggerSkipPW:
        lda MB_InstAD,y
        sta SID+5,x
        lda MB_InstSR,y
        sta SID+6,x
        lda MB_InstWave,y
        and #$fe
        sta SID+4,x
        ora #$01
        sta SID+4,x
        pla
        tax
        ldy MB_SavedY
        rts

MB_GateOff:
        tya
        sta MB_SavedY
        lda MB_VInst,x
        tay
        lda MB_InstWave,y
        and #$fe
        pha
        lda MB_SidOff,x
        tay
        pla
        sta SID+4,y
        ldy MB_SavedY
        rts

MB_CalcFreq:
        cmp #84
        bcc MB_CalcFreqInRange
        lda #83                 ; table supports note numbers 0..83
MB_CalcFreqInRange:
        ldy #6
MB_CalcDivLoop:
        cmp #12
        bcc MB_CalcGotSemi
        sec
        sbc #12
        dey
        jmp MB_CalcDivLoop
MB_CalcGotSemi:
        pha
        tya
        sta MB_Shift
        pla
        tay
        lda MB_BaseLo,y
        sta MB_FreqLo
        lda MB_BaseHi,y
        sta MB_FreqHi
        ldy MB_Shift
        beq MB_CalcDone
MB_CalcShiftLoop:
        lsr MB_FreqHi
        ror MB_FreqLo
        dey
        bne MB_CalcShiftLoop
MB_CalcDone:
        rts

MB_PWMUpdate:
        lda MB_PWMdir
        bmi MB_PWMDown
MB_PWMUp:
        lda MB_PWMlo
        clc
        adc #4
        sta MB_PWMlo
        lda MB_PWMhi
        adc #0
        and #$0f
        sta MB_PWMhi
        cmp #$0e
        bcc MB_PWMWrite
        lda #$ff
        sta MB_PWMlo
        lda #$0d               ; exact upper clamp: $dff, never near-full $e00+
        sta MB_PWMhi
        lda #$ff
        sta MB_PWMdir
        jmp MB_PWMWrite
MB_PWMDown:
        lda MB_PWMlo
        sec
        sbc #4
        sta MB_PWMlo
        lda MB_PWMhi
        sbc #0
        and #$0f
        sta MB_PWMhi
        cmp #$02
        bcs MB_PWMWrite
        lda #$00
        sta MB_PWMlo
        lda #$02               ; exact lower clamp: $200
        sta MB_PWMhi
        lda #$01
        sta MB_PWMdir
MB_PWMWrite:
        lda MB_PWMlo
        sta SID+16
        lda MB_PWMhi
        sta SID+17
        rts

MB_FiltUpdate:
        lda MB_FiltStep
        bmi MB_FiltDown
MB_FiltUp:
        lda MB_FiltVal
        clc
        adc #1
        cmp #$d0
        bcc MB_FiltStoreUp
        lda #$cf
        sta MB_FiltVal
        lda #$ff
        sta MB_FiltStep
        rts
MB_FiltStoreUp:
        sta MB_FiltVal
        rts
MB_FiltDown:
        lda MB_FiltVal
        sec
        sbc #1
        cmp #$20
        bcs MB_FiltStoreDown
        lda #$20
        sta MB_FiltVal
        lda #$01
        sta MB_FiltStep
        rts
MB_FiltStoreDown:
        sta MB_FiltVal
        rts

; MEGABLAST_CONTINUE_PLUS_ACTIVE: bounded groove overlay after base PWM/filter.
; It writes cutoff/PW/filter-route only, never $d418, so crackle-safe volume policy remains.
MB_GrooveOverlay:
        inc MB_Frame
        lda MB_Frame
        sta MusicStep            ; visuals follow the active Megablast frame clock

        ; Build cutoff from the live slow wah, section bias, rhythmic accent and beat.
        lda MB_Section
        and #$03
        tax
        lda MB_FiltVal
        clc
        adc MB_SectionBias,x
        bcc MB_GrooveSectionOk
        lda #$cf
MB_GrooveSectionOk:
        cmp #$d0
        bcc MB_GrooveSectionStore
        lda #$cf
MB_GrooveSectionStore:
        sta MB_CutWork

        lda MB_Frame
        and #$0f
        tax
        lda MB_CutAccent,x
        clc
        adc MB_CutWork
        bcc MB_GrooveAccentOk
        lda #$cf
MB_GrooveAccentOk:
        clc
        adc BeatEnv
        bcc MB_GrooveCutOk
        lda #$cf
MB_GrooveCutOk:
        cmp #$d0
        bcc MB_GrooveCutStore
        lda #$cf
MB_GrooveCutStore:
        sta MB_CutWork
        lda MB_CutLo,x           ; SID cutoff-low exposes only bits 0..2
        and #$07
        sta SID+21               ; low bits first, then high bits: coherent cutoff update
        lda MB_CutWork
        sta SID+22

        lda MB_Section
        and #$03
        tax
        lda MB_RouteTab,x
        sta SID+23

        lda MB_Frame
        and #$0f
        tax
        lda MB_PWHiV3,x
        sta SID+17
        lda MB_PWHiV1,x
        sta SID+3
        rts

MB_BaseLo:
        !byte $9c,$c0,$23,$c9,$b5,$ec,$73,$4e,$82,$12,$08,$68
MB_BaseHi:
        !byte $45,$49,$4e,$52,$57,$5c,$62,$68,$6e,$75,$7c,$83
MB_SidOff:
        !byte 0,7,14

; Instruments from uploaded Megablast source:
; 0 = lead pulse, 1 = bass saw, 2 = major arp pulse, 3 = minor arp pulse.
MB_InstWave:
        !byte $40,$20,$40,$40
MB_InstAD:
        !byte $0a,$08,$06,$06
MB_InstSR:
        !byte $c9,$68,$a6,$a6
MB_InstPWlo:
        !byte $00,$00,$00,$00
MB_InstPWhi:
        !byte $08,$08,$04,$04
MB_ArpMajTab:
        !byte 0,4,7,$80
MB_ArpMinTab:
        !byte 0,3,7,$80
MB_InstArpLo:
        !byte $00,$00,<MB_ArpMajTab,<MB_ArpMinTab
MB_InstArpHi:
        !byte $00,$00,>MB_ArpMajTab,>MB_ArpMinTab

MB_ChordData:
        !byte $83,57,48
        !byte $82,53,48
        !byte $82,48,48
        !byte $82,55,48
        !byte $fe
MB_BassData:
        !byte $81
        ; Source 16-step bass, doubled with answer notes for longer drive.
        !byte 33,12, 33,12, 28,12, 33,12
        !byte 29,12, 29,12, 36,12, 29,12
        !byte 36,12, 36,12, 31,12, 36,12
        !byte 31,12, 31,12, 38,12, 31,12
        !byte 33,12, 40,12, 28,12, 33,12
        !byte 29,12, 36,12, 41,12, 36,12
        !byte 36,12, 43,12, 31,12, 36,12
        !byte 31,12, 38,12, 43,12, 38,12
        !byte $fe
MB_LeadData:
        !byte $80
        ; Source lead plus octave/answer continuation; no rests/silent bars.
        !byte 64,12, 69,12, 72,12, 71,12
        !byte 65,12, 69,12, 72,12, 69,12
        !byte 64,12, 67,12, 72,12, 67,12
        !byte 62,12, 67,12, 71,12, 74,12
        !byte 76,12, 72,12, 69,12, 72,12
        !byte 77,12, 74,12, 72,12, 69,12
        !byte 76,12, 79,12, 72,12, 76,12
        !byte 74,12, 71,12, 67,12, 71,12
        !byte $fe
MB_StartLo:
        !byte <MB_ChordData,<MB_BassData,<MB_LeadData
MB_StartHi:
        !byte >MB_ChordData,>MB_BassData,>MB_LeadData

MB_VPtrLo:   !byte 0,0,0
MB_VPtrHi:   !byte 0,0,0
MB_VDur:     !byte 0,0,0
MB_VNote:    !byte 0,0,0
MB_VInst:    !byte 0,0,0
MB_VArpIdx:  !byte 0,0,0
MB_Shift:    !byte 0
MB_FreqLo:   !byte 0
MB_FreqHi:   !byte 0
MB_SavedY:   !byte 0
MB_PWMlo:    !byte 0
MB_PWMhi:    !byte $08
MB_PWMdir:   !byte 1
MB_FiltVal:  !byte $40
MB_FiltStep: !byte 1
MB_Frame:    !byte 0
MB_Section:  !byte 0
MB_CutWork:  !byte $40

MB_SectionBias:
        !byte $00,$08,$18,$00
MB_CutAccent:
        !byte $00,$04,$08,$14,$0c,$04,$10,$18,$06,$0a,$16,$20,$10,$08,$18,$24
MB_CutLo:
        !byte $00,$03,$07,$03,$07,$01,$05,$01,$02,$06,$02,$06,$04,$00,$04,$00
MB_RouteTab:
        !byte $53,$63,$73,$43
MB_PWHiV3:
        !byte $04,$05,$06,$07,$08,$09,$0a,$09,$08,$07,$06,$05,$04,$05,$06,$07
MB_PWHiV1:
        !byte $07,$08,$09,$0a,$09,$08,$07,$06,$07,$09,$0b,$0a,$08,$07,$06,$08

NmiStub:
        ; Preserve A and clear a possible CIA2 FLAG source (for example RESTORE).
        ; CIA2 masks are disabled at startup, but acknowledging here prevents a
        ; stale source from retriggering if a loader/cartridge asserted NMI.
        pha
        lda $dd0d
        pla
        rti

; RELEASE_LOCK: top/logo panel only for beat visuals and sprites.
IrqTop:
        pha
        txa
        pha
        tya
        pha
        lda #$01
        sta $d019

        lda #$00
        sta $d020
        sta $d021
        ; CIA2 bank 1 was selected once during Start. No per-frame $dd00 write:
        ; this avoids clobbering unrelated CIA2/user-port output bits.
        lda #$18
        sta $d016
        lda #$18              ; bank 1: screen=$4400, bitmap=$6000
        sta $d018
        lda #$3b
        sta $d011
        lda #$ff              ; sprites only active in top/logo panel
        sta $d015

        jsr MusicTick            ; establish one beat value for the whole frame
        jsr BeatRasterTick
        jsr StarTick             ; finish sprite writes before the first sprite DMA line
        jsr VuBarsTick           ; rows 17-19 are fetched much later, so this may run last
        jsr BeatEnvDecay         ; one frame boundary owns beat-envelope advancement
        jsr Scroller_Tick        ; VSync authority: text RAM is not visible until raster $d3

        lda #<IrqSplit
        sta $fffe
        lda #>IrqSplit
        sta $ffff
        lda #SPLIT_LINE
        sta $d012
        lda $d011
        and #$7f
        sta $d011

        pla
        tay
        pla
        tax
        pla
        rti

; RELEASE_LOCK: text panel isolation begins here.
IrqSplit:
        pha
        txa
        pha
        tya
        pha
        lda #$01
        sta $d019

        ; Preserve all eight scanlines of bitmap row 19.  The split IRQ fires
        ; on raster $d2, then waits until the right border before selecting
        ; text mode/screen for the row-20 badline at $d3.
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        ; Bitmap and text now share ROM-free VIC bank 1. No CIA2 bank switch is
        ; performed in this timing-critical handoff; only mode/pointer registers change.
        lda zpScrollFine1     ; set fine-X on $d2, before the next badline
        sta $d016
        lda #$34              ; bank 1: screen=$4c00, charset=$5000
        sta $d018
        lda #$1b
        sta $d011
        lda #$00
        sta $d020
        sta $d021
        sta $d015

        lda #<IrqTextRow2
        sta $fffe
        lda #>IrqTextRow2
        sta $ffff
        lda #TEXT_ROW2_LINE
        sta $d012
        lda $d011
        and #$7f
        sta $d011

        pla
        tay
        pla
        tax
        pla
        rti

; Row-specific VIC-II X-scroll writes happen in the right border of the
; final scanline of the preceding glyph row. This preserves all eight glyph
; scanlines, while the next row still receives its independent fine-X phase.
IrqTextRow2:
        pha
        txa
        pha
        tya
        pha
        lda #$01
        sta $d019

        ; Delay the $d016 write until the right border. Writing earlier would
        ; alter the final visible scanline of the preceding 8x8 glyph row.
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        lda zpScrollFine2    ; guaranteed 0..7: 38-column hires text
        sta $d016

        lda #<IrqTextRow3
        sta $fffe
        lda #>IrqTextRow3
        sta $ffff
        lda #TEXT_ROW3_LINE
        sta $d012
        pla
        tay
        pla
        tax
        pla
        rti
IrqTextRow3:
        pha
        txa
        pha
        tya
        pha
        lda #$01
        sta $d019

        ; Delay the $d016 write until the right border. Writing earlier would
        ; alter the final visible scanline of the preceding 8x8 glyph row.
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        lda zpScrollFine3    ; guaranteed 0..7: 38-column hires text
        sta $d016

        lda #<IrqTextRow4
        sta $fffe
        lda #>IrqTextRow4
        sta $ffff
        lda #TEXT_ROW4_LINE
        sta $d012
        pla
        tay
        pla
        tax
        pla
        rti
IrqTextRow4:
        pha
        txa
        pha
        tya
        pha
        lda #$01
        sta $d019

        ; Delay the $d016 write until the right border. Writing earlier would
        ; alter the final visible scanline of the preceding 8x8 glyph row.
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        lda zpScrollFine4    ; guaranteed 0..7: 38-column hires text
        sta $d016

        lda #<IrqBottom
        sta $fffe
        lda #>IrqBottom
        sta $ffff
        lda #BOTTOM_LINE
        sta $d012
        pla
        tay
        pla
        tax
        pla
        rti


; Lightweight frame-tail IRQ. Scroller_Tick runs once at raster 0 after
; pre-visible sprite work; text RAM remains isolated from bitmap sprite pointers.
IrqBottom:
        pha
        txa
        pha
        tya
        pha
        lda #$01
        sta $d019

        ; Keep the frame-tail IRQ minimal. This remains safe even on shorter
        ; raster standards; all heavy scrolling already ran at VBlank raster 0.
        lda #<IrqTop
        sta $fffe
        lda #>IrqTop
        sta $ffff
        lda #$00
        sta $d012
        lda $d011
        and #$7f
        sta $d011

        pla
        tay
        pla
        tax
        pla
        rti


; RELEASE_LOCK: sound/eyecandy polish is top-panel only.
BeatRasterTick:
        ; Sound-reactive MC/background only. Border is always black.
        lda #$00
        sta $d020
        lda BeatEnv
        beq BeatRasterTick_calm
        and #$0f
        tax
        lda BeatRasterBack,x
        sta $d021
        ; Final visible MC1 is beat/frame coupled.
        txa
        eor MusicStep
        and #$0f
        tax
        lda BeatRasterMC1,x
        sta $d022
        ; Final visible MC2 is a slower star-frame shimmer.
        lda StarFrame
        and #$0f
        tax
        lda BeatRasterMC2,x
        sta $d023
        rts
BeatRasterTick_calm:
        lda #$00
        sta $d020
        sta $d021
        lda MusicStep
        and #$0f
        tax
        lda CalmRasterMC1,x
        sta $d022
        lda CalmRasterMC2,x
        sta $d023
        rts

; RELEASE_LOCK: middle VU/raster bars stay above text rows only.
VuBarsTick:
        ; VU bars are in bitmap/color rows 17-19, safely above text rows 21-24.
        ; They react to BeatEnv/MusicStep but never touch $d020 and never run in text split.
        lda BeatEnv
        lsr
        lsr
        and #$07
        tax
        lda VuBarColorA,x
        sta VuBarColorTempA
        lda MusicStep
        eor BeatEnv
        and #$07
        tax
        lda VuBarColorB,x
        sta VuBarColorTempB

        ldx #0
VuBarsTick_loop:
        txa
        and #$07
        tay
        lda VuBarMask,y
        bit BeatEnv
        beq VuBarsTick_dim
        lda VuBarColorTempA
        bne VuBarsTick_store
VuBarsTick_dim:
        lda VuBarColorTempB
VuBarsTick_store:
        sta COLOR_RAM+40*17,x
        sta COLOR_RAM+40*18,x
        sta COLOR_RAM+40*19,x
        inx
        cpx #40
        bne VuBarsTick_loop
        rts

; ARPSID V965: four independently phased/speeded smooth-scroll lanes.
; Speeds are permanently distinct: 0.75 / 1.00 / 1.25 / 1.50 px/frame.
; Initial fine-X offsets are 7 / 5 / 3 / 1 pixels. The phases are staggered
; so at most two character rows shift in one lower-border update.
Scroller_Tick:
        jsr Scroller_UpdateRow1
        jsr Scroller_UpdateRow2
        jsr Scroller_UpdateRow3
        jsr Scroller_UpdateRow4
        rts

Scroller_UpdateRow1:
        lda zpScrollFrac1
        clc
        adc ScrollerSpeedQ2+0
        sta zpScrollFrac1
        lsr
        lsr
        sta zpScrollSteps
        lda zpScrollFrac1
        and #$03
        sta zpScrollFrac1
Scroller_UpdateRow1_loop:
        lda zpScrollSteps
        beq Scroller_UpdateRow1_done
        jsr Scroller_StepPixel1
        dec zpScrollSteps
        jmp Scroller_UpdateRow1_loop
Scroller_UpdateRow1_done:
        rts

Scroller_UpdateRow2:
        lda zpScrollFrac2
        clc
        adc ScrollerSpeedQ2+1
        sta zpScrollFrac2
        lsr
        lsr
        sta zpScrollSteps
        lda zpScrollFrac2
        and #$03
        sta zpScrollFrac2
Scroller_UpdateRow2_loop:
        lda zpScrollSteps
        beq Scroller_UpdateRow2_done
        jsr Scroller_StepPixel2
        dec zpScrollSteps
        jmp Scroller_UpdateRow2_loop
Scroller_UpdateRow2_done:
        rts

Scroller_UpdateRow3:
        lda zpScrollFrac3
        clc
        adc ScrollerSpeedQ2+2
        sta zpScrollFrac3
        lsr
        lsr
        sta zpScrollSteps
        lda zpScrollFrac3
        and #$03
        sta zpScrollFrac3
Scroller_UpdateRow3_loop:
        lda zpScrollSteps
        beq Scroller_UpdateRow3_done
        jsr Scroller_StepPixel3
        dec zpScrollSteps
        jmp Scroller_UpdateRow3_loop
Scroller_UpdateRow3_done:
        rts

Scroller_UpdateRow4:
        lda zpScrollFrac4
        clc
        adc ScrollerSpeedQ2+3
        sta zpScrollFrac4
        lsr
        lsr
        sta zpScrollSteps
        lda zpScrollFrac4
        and #$03
        sta zpScrollFrac4
Scroller_UpdateRow4_loop:
        lda zpScrollSteps
        beq Scroller_UpdateRow4_done
        jsr Scroller_StepPixel4
        dec zpScrollSteps
        jmp Scroller_UpdateRow4_loop
Scroller_UpdateRow4_done:
        rts

Scroller_StepPixel1:
        lda zpScrollFine1
        beq Scroller_StepPixel1_wrap
        dec zpScrollFine1
        rts
Scroller_StepPixel1_wrap:
        lda #SCROLL_FINE_WRAP
        sta zpScrollFine1
        ldx #0
Scroller_StepPixel1_shift:
        lda TEXT_SCREEN_ADDR+40*21+1,x
        sta TEXT_SCREEN_ADDR+40*21+0,x
        lda COLOR_RAM+40*21+1,x
        sta COLOR_RAM+40*21+0,x
        inx
        cpx #39
        bcc Scroller_StepPixel1_shift
        ldy #0
        lda (zpMsgPtr1Lo),y
        sta TEXT_SCREEN_ADDR+40*21+39
        ldx zpColorPhase1
        lda ScrollColorRow1,x
        sta COLOR_RAM+40*21+39
        inc zpColorPhase1
        lda zpColorPhase1
        and #$0f
        sta zpColorPhase1
        jsr Scroller_AdvancePtr1
        rts

Scroller_StepPixel2:
        lda zpScrollFine2
        beq Scroller_StepPixel2_wrap
        dec zpScrollFine2
        rts
Scroller_StepPixel2_wrap:
        lda #SCROLL_FINE_WRAP
        sta zpScrollFine2
        ldx #0
Scroller_StepPixel2_shift:
        lda TEXT_SCREEN_ADDR+40*22+1,x
        sta TEXT_SCREEN_ADDR+40*22+0,x
        lda COLOR_RAM+40*22+1,x
        sta COLOR_RAM+40*22+0,x
        inx
        cpx #39
        bcc Scroller_StepPixel2_shift
        ldy #0
        lda (zpMsgPtr2Lo),y
        sta TEXT_SCREEN_ADDR+40*22+39
        ldx zpColorPhase2
        lda ScrollColorRow2,x
        sta COLOR_RAM+40*22+39
        inc zpColorPhase2
        lda zpColorPhase2
        and #$0f
        sta zpColorPhase2
        jsr Scroller_AdvancePtr2
        rts

Scroller_StepPixel3:
        lda zpScrollFine3
        beq Scroller_StepPixel3_wrap
        dec zpScrollFine3
        rts
Scroller_StepPixel3_wrap:
        lda #SCROLL_FINE_WRAP
        sta zpScrollFine3
        ldx #0
Scroller_StepPixel3_shift:
        lda TEXT_SCREEN_ADDR+40*23+1,x
        sta TEXT_SCREEN_ADDR+40*23+0,x
        lda COLOR_RAM+40*23+1,x
        sta COLOR_RAM+40*23+0,x
        inx
        cpx #39
        bcc Scroller_StepPixel3_shift
        ldy #0
        lda (zpMsgPtr3Lo),y
        sta TEXT_SCREEN_ADDR+40*23+39
        ldx zpColorPhase3
        lda ScrollColorRow3,x
        sta COLOR_RAM+40*23+39
        inc zpColorPhase3
        lda zpColorPhase3
        and #$0f
        sta zpColorPhase3
        jsr Scroller_AdvancePtr3
        rts

Scroller_StepPixel4:
        lda zpScrollFine4
        beq Scroller_StepPixel4_wrap
        dec zpScrollFine4
        rts
Scroller_StepPixel4_wrap:
        lda #SCROLL_FINE_WRAP
        sta zpScrollFine4
        ldx #0
Scroller_StepPixel4_shift:
        lda TEXT_SCREEN_ADDR+40*24+1,x
        sta TEXT_SCREEN_ADDR+40*24+0,x
        lda COLOR_RAM+40*24+1,x
        sta COLOR_RAM+40*24+0,x
        inx
        cpx #39
        bcc Scroller_StepPixel4_shift
        ldy #0
        lda (zpMsgPtr4Lo),y
        sta TEXT_SCREEN_ADDR+40*24+39
        ldx zpColorPhase4
        lda ScrollColorRow4,x
        sta COLOR_RAM+40*24+39
        inc zpColorPhase4
        lda zpColorPhase4
        and #$0f
        sta zpColorPhase4
        jsr Scroller_AdvancePtr4
        rts

Scroller_AdvancePtr1:
        inc zpMsgPtr1Lo
        bne Scroller_AdvancePtr1_Chk
        inc zpMsgPtr1Hi
Scroller_AdvancePtr1_Chk:
        lda zpMsgPtr1Lo
        cmp #<MessageFeaturesEnd
        bne Scroller_AdvancePtr1_Done
        lda zpMsgPtr1Hi
        cmp #>MessageFeaturesEnd
        bne Scroller_AdvancePtr1_Done
        lda #<MessageFeatures
        sta zpMsgPtr1Lo
        lda #>MessageFeatures
        sta zpMsgPtr1Hi
Scroller_AdvancePtr1_Done:
        rts

Scroller_AdvancePtr2:
        inc zpMsgPtr2Lo
        bne Scroller_AdvancePtr2_Chk
        inc zpMsgPtr2Hi
Scroller_AdvancePtr2_Chk:
        lda zpMsgPtr2Lo
        cmp #<MessageEngineEnd
        bne Scroller_AdvancePtr2_Done
        lda zpMsgPtr2Hi
        cmp #>MessageEngineEnd
        bne Scroller_AdvancePtr2_Done
        lda #<MessageEngine
        sta zpMsgPtr2Lo
        lda #>MessageEngine
        sta zpMsgPtr2Hi
Scroller_AdvancePtr2_Done:
        rts

Scroller_AdvancePtr3:
        inc zpMsgPtr3Lo
        bne Scroller_AdvancePtr3_Chk
        inc zpMsgPtr3Hi
Scroller_AdvancePtr3_Chk:
        lda zpMsgPtr3Lo
        cmp #<MessageFunctionEnd
        bne Scroller_AdvancePtr3_Done
        lda zpMsgPtr3Hi
        cmp #>MessageFunctionEnd
        bne Scroller_AdvancePtr3_Done
        lda #<MessageFunction
        sta zpMsgPtr3Lo
        lda #>MessageFunction
        sta zpMsgPtr3Hi
Scroller_AdvancePtr3_Done:
        rts

Scroller_AdvancePtr4:
        inc zpMsgPtr4Lo
        bne Scroller_AdvancePtr4_Chk
        inc zpMsgPtr4Hi
Scroller_AdvancePtr4_Chk:
        lda zpMsgPtr4Lo
        cmp #<MessageModesEnd
        bne Scroller_AdvancePtr4_Done
        lda zpMsgPtr4Hi
        cmp #>MessageModesEnd
        bne Scroller_AdvancePtr4_Done
        lda #<MessageModes
        sta zpMsgPtr4Lo
        lda #>MessageModes
        sta zpMsgPtr4Hi
Scroller_AdvancePtr4_Done:
        rts

Scroller_InitPointers:
        lda #<(MessageFeatures+40)
        sta zpMsgPtr1Lo
        lda #>(MessageFeatures+40)
        sta zpMsgPtr1Hi
        lda #<(MessageEngine+40)
        sta zpMsgPtr2Lo
        lda #>(MessageEngine+40)
        sta zpMsgPtr2Hi
        lda #<(MessageFunction+40)
        sta zpMsgPtr3Lo
        lda #>(MessageFunction+40)
        sta zpMsgPtr3Hi
        lda #<(MessageModes+40)
        sta zpMsgPtr4Lo
        lda #>(MessageModes+40)
        sta zpMsgPtr4Hi
        lda #$08              ; seeded columns 0..39 continue at rainbow phase 8
        sta zpColorPhase1
        sta zpColorPhase2
        sta zpColorPhase3
        sta zpColorPhase4
        rts

Scroller_Clear:
        ldx #0
Scroller_Clear_seed:
        lda #$00
        sta TEXT_SCREEN_ADDR+40*20,x
        lda MessageFeatures,x
        sta TEXT_SCREEN_ADDR+40*21,x
        lda MessageEngine,x
        sta TEXT_SCREEN_ADDR+40*22,x
        lda MessageFunction,x
        sta TEXT_SCREEN_ADDR+40*23,x
        lda MessageModes,x
        sta TEXT_SCREEN_ADDR+40*24,x
        txa
        and #$0f
        tay
        lda #$0e
        sta COLOR_RAM+40*20,x
        lda ScrollColorRow1,y
        sta COLOR_RAM+40*21,x
        lda ScrollColorRow2,y
        sta COLOR_RAM+40*22,x
        lda ScrollColorRow3,y
        sta COLOR_RAM+40*23,x
        lda ScrollColorRow4,y
        sta COLOR_RAM+40*24,x
        inx
        cpx #40
        bne Scroller_Clear_seed
        jsr Scroller_InitPointers
        rts

; Q2 pixels/frame for text rows 1..4.
ScrollerSpeedQ2:
        !byte 3,4,5,6
; Carefully chosen VIC-II palettes: bright, readable, and no black glyphs.
ScrollColorRow1:
        !byte $03,$0e,$01,$0f,$0d,$07,$0a,$04,$03,$0e,$01,$0f,$0d,$07,$0a,$04
ScrollColorRow2:
        !byte $04,$0a,$01,$07,$0f,$0e,$03,$0d,$04,$0a,$01,$07,$0f,$0e,$03,$0d
ScrollColorRow3:
        !byte $05,$0d,$07,$01,$0e,$03,$0f,$0a,$05,$0d,$07,$01,$0e,$03,$0f,$0a
ScrollColorRow4:
        !byte $08,$07,$01,$0a,$0f,$04,$0e,$0d,$08,$07,$01,$0a,$0f,$04,$0e,$0d

VuBarColorTempA:
        !byte $01
VuBarColorTempB:
        !byte $00
VuBarColorA:
        !byte $01,$0f,$07,$0e,$0a,$0d,$03,$01
VuBarColorB:
        !byte $00,$00,$06,$00,$00,$06,$00,$00
VuBarMask:
        !byte $01,$02,$04,$08,$10,$20,$40,$80

BeatRasterBack:
        !byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$06,$00,$00,$00,$00,$06,$00
; RELEASE_LOCK: wow pass keeps text stable and asset-fit.
BeatRasterMC1:
        !byte $08,$0f,$01,$07,$0e,$03,$0d,$01,$0f,$07,$0a,$01,$0e,$03,$07,$01
BeatRasterMC2:
        !byte $0b,$09,$01,$0f,$0e,$03,$0d,$01,$07,$0f,$0a,$01,$0e,$07,$0a,$01
CalmRasterMC1:
        !byte $08,$09,$0a,$0b,$0b,$0a,$09,$08,$08,$07,$06,$05,$05,$06,$07,$08
CalmRasterMC2:
        !byte $0b,$0a,$09,$08,$07,$06,$05,$06,$07,$08,$09,$0a,$0b,$0a,$09,$08




code_end:
!if code_end > $4000 {
        !error "Code grew into VIC bank 1 display memory at $4000."
}


; Active Megablast music is inline; no inactive stream block is assembled.

* = ASSET_ADDR
asset_start:
uber_bitmap_src:
        !bin "assets/uber_bitmap.bin"
uber_screen_src:
        !bin "assets/uber_screen.bin"
uber_color_src:
        !bin "assets/uber_color.bin"
uber_charset_src:
        !bin "assets/uber_custom_font.bin"

; -----------------------------------------------------------------------------
; Sprite / music data
; Logo sparkle sprites: beat-aware star/note highlights over uploaded logo.
; -----------------------------------------------------------------------------
StarSpriteData:
        ; sprite $fe: small plus/star
        !byte $00,$00,$00,$00,$18,$00,$00,$18,$00,$00,$7e,$00,$00,$18,$00,$00
        !byte $18,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
        !byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
        !byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
        ; sprite $ff: music note / sparkle
        !byte $00,$00,$00,$00,$0e,$00,$00,$0a,$00,$00,$0a,$00,$00,$0a,$00,$00
        !byte $3a,$00,$00,$7e,$00,$00,$24,$00,$00,$24,$00,$00,$00,$00,$00,$00
        !byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
        !byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00

; FLYOFF: sprites shoot off logo anchors on beat.
StarXInit:        !byte $34,$4a,$60,$76,$8c,$a2,$b8,$ce
StarYInit:        !byte $38,$40,$48,$50,$58,$60,$68,$70
; RELEASE_LOCK: polish compact keeps data size stable.
StarSpeedByReg:   !byte 5,0,7,0,6,0,7,0,5,0,7,0,6,0,7,0
StarXReset:       !byte $34,0,$4a,0,$60,0,$76,0,$8c,0,$a2,0,$b8,0,$ce,0
StarColorInit:    !byte $01,$0f,$07,$01,$0e,$0d,$01,$0a
StarTwinkleOff:   !byte 0,2,4,6,8,10,12,14
StarFlyY:         !byte $f6,$f8,$fb,$fd,$03,$06,$08,$0a
StarTwinkleColors:
        !byte $01,$0f,$07,$01,$0e,$01,$0a,$0f,$01,$0d,$07,$01,$0e,$0f,$0a,$01
StarBeatColors:
        !byte $01,$0f,$01,$07,$0f,$01,$0e,$01,$0f,$01,$0a,$0d,$0f,$01,$07,$01
LogoSparklePtrIdle:
        !byte $fe,$fe,$fe,$fe,$ff,$ff,$ff,$ff
LogoSparklePtr:
        !byte $ff,$ff,$fe,$ff,$ff,$fe,$ff,$fe

; ARPSID v965 handoff-derived four-line teaser payload.
; ROW21 FEATURES / ROW22 ENGINE / ROW23 FUNCTION / ROW24 MODES.
MessageFeatures:
        !byte $01,$12,$10,$13,$09,$04,$00,$16,$29,$26,$25,$00,$00,$03,$01,$0e
        !byte $0f,$0e,$09,$03,$01,$0c,$00,$12,$05,$0e,$04,$05,$12,$00,$10,$09
        !byte $10,$05,$0c,$09,$0e,$05,$00,$00,$0f,$0e,$05,$00,$03,$01,$0e,$0f
        !byte $0e,$09,$03,$01,$0c,$00,$14,$09,$0d,$05,$04,$00,$05,$16,$05,$0e
        !byte $14,$00,$0f,$12,$04,$05,$12,$00,$00,$00,$00,$00,$00,$00,$00,$00
        !byte $0e,$0f,$14,$05,$00,$0f,$06,$06,$00,$10,$01,$0e,$09,$03,$00,$13
        !byte $15,$12,$16,$09,$16,$05,$00,$11,$15,$05,$15,$05,$00,$10,$12,$05
        !byte $13,$13,$15,$12,$05,$00,$00,$00,$0e,$0f,$00,$0f,$15,$14,$10,$15
        !byte $14,$00,$13,$14,$09,$0c,$0c,$00,$12,$15,$0e,$13,$00,$14,$08,$05
        !byte $00,$06,$15,$0c,$0c,$00,$10,$09,$10,$05,$0c,$09,$0e,$05,$00,$00
        !byte $13,$14,$01,$14,$05,$00,$12,$0f,$0f,$14,$13,$00,$13,$17,$01,$10
        !byte $00,$17,$09,$14,$08,$0f,$15,$14,$00,$01,$15,$04,$09,$0f,$00,$0c
        !byte $0f,$03,$0b,$13,$00,$00,$00,$00,$14,$05,$0c,$05,$0d,$05,$14,$12
        !byte $19,$00,$10,$15,$02,$0c,$09,$13,$08,$05,$13,$00,$03,$0f,$08,$05
        !byte $12,$05,$0e,$14,$00,$06,$12,$01,$0d,$05,$13,$00,$00,$00,$00,$00
        !byte $13,$14,$12,$15,$03,$14,$15,$12,$01,$0c,$00,$03,$08,$01,$0e,$07
        !byte $05,$13,$00,$0f,$17,$0e,$00,$13,$01,$0d,$10,$0c,$05,$00,$02,$0f
        !byte $15,$0e,$04,$01,$12,$09,$05,$13,$12,$05,$01,$0c,$14,$09,$0d,$05
        !byte $00,$10,$01,$14,$08,$13,$00,$13,$14,$01,$19,$00,$02,$0f,$15,$0e
        !byte $04,$05,$04,$00,$01,$0e,$04,$00,$03,$0c,$05,$01,$0e,$00,$00,$00
        !byte $01,$12,$10,$13,$09,$04,$00,$16,$29,$26,$25,$00,$00,$14,$09,$0d
        !byte $09,$0e,$07,$00,$14,$12,$15,$14,$08,$00,$09,$0e,$00,$0d,$0f,$14
        !byte $09,$0f,$0e,$00,$00,$00,$00,$00
MessageFeaturesEnd:

MessageEngine:
        !byte $05,$0e,$07,$09,$0e,$05,$13,$00,$00,$02,$09,$14,$10,$05,$12,$06
        !byte $05,$03,$14,$00,$04,$12,$13,$09,$04,$00,$13,$09,$04,$28,$20,$28
        !byte $00,$04,$09,$07,$09,$00,$00,$00,$02,$09,$14,$10,$05,$12,$06,$05
        !byte $03,$14,$00,$03,$0c,$01,$13,$13,$09,$03,$00,$13,$09,$04,$00,$13
        !byte $19,$0e,$14,$08,$05,$13,$09,$13,$00,$00,$00,$00,$00,$00,$00,$00
        !byte $13,$09,$04,$00,$12,$05,$07,$09,$13,$14,$05,$12,$00,$0d,$0f,$04
        !byte $05,$00,$17,$09,$14,$08,$00,$16,$0f,$09,$03,$05,$00,$14,$0f,$0b
        !byte $05,$0e,$13,$00,$00,$00,$00,$00,$04,$12,$13,$09,$04,$00,$04,$12
        !byte $15,$0d,$00,$05,$0e,$07,$09,$0e,$05,$00,$01,$0e,$04,$00,$06,$01
        !byte $03,$14,$0f,$12,$19,$00,$0b,$09,$14,$13,$00,$00,$00,$00,$00,$00
        !byte $13,$09,$04,$28,$20,$28,$00,$0b,$09,$03,$0b,$00,$14,$0f,$0d,$00
        !byte $08,$01,$14,$00,$03,$0c,$01,$10,$00,$03,$0f,$17,$02,$05,$0c,$0c
        !byte $00,$00,$00,$00,$00,$00,$00,$00,$04,$09,$07,$09,$00,$13,$01,$0d
        !byte $10,$0c,$05,$12,$00,$01,$0e,$04,$00,$01,$15,$14,$08,$05,$0e,$14
        !byte $09,$03,$00,$04,$24,$21,$28,$00,$00,$00,$00,$00,$00,$00,$00,$00
        !byte $03,$26,$24,$00,$10,$13,$09,$04,$00,$12,$13,$09,$04,$00,$10,$0c
        !byte $01,$19,$05,$12,$00,$17,$09,$14,$08,$00,$10,$08,$09,$22,$00,$00
        !byte $00,$00,$00,$00,$00,$00,$00,$00,$0d,$15,$0c,$14,$09,$00,$13,$09
        !byte $04,$00,$0d,$0f,$04,$05,$0c,$00,$03,$0c,$0f,$03,$0b,$00,$01,$0e
        !byte $04,$00,$12,$0f,$15,$14,$09,$0e,$07,$00,$00,$00,$00,$00,$00,$00
        !byte $01,$12,$10,$13,$09,$04,$00,$05,$0e,$07,$09,$0e,$05,$00,$06,$01
        !byte $0d,$09,$0c,$19,$00,$00,$0f,$0e,$05,$00,$03,$0f,$12,$05,$00,$00
        !byte $00,$00,$00,$00,$00,$00,$00,$00
MessageEngineEnd:

MessageFunction:
        !byte $14,$09,$0d,$09,$0e,$07,$00,$00,$13,$01,$0d,$10,$0c,$05,$00,$03
        !byte $19,$03,$0c,$05,$00,$13,$15,$02,$10,$08,$01,$13,$05,$00,$01,$15
        !byte $14,$08,$0f,$12,$09,$14,$19,$00,$01,$12,$10,$00,$07,$01,$14,$05
        !byte $13,$00,$0c,$01,$0e,$04,$00,$01,$14,$00,$05,$18,$01,$03,$14,$00
        !byte $13,$01,$0d,$10,$0c,$05,$00,$0f,$06,$06,$13,$05,$14,$13,$00,$00
        !byte $13,$05,$11,$15,$05,$0e,$03,$05,$12,$00,$0b,$09,$14,$00,$04,$09
        !byte $07,$09,$00,$13,$08,$01,$12,$05,$00,$02,$0f,$15,$0e,$04,$01,$12
        !byte $09,$05,$13,$00,$00,$00,$00,$00,$10,$0f,$13,$14,$00,$06,$18,$00
        !byte $13,$14,$01,$12,$14,$13,$00,$05,$18,$01,$03,$14,$0c,$19,$00,$01
        !byte $14,$00,$05,$16,$05,$0e,$14,$00,$14,$09,$0d,$05,$00,$00,$00,$00
        !byte $10,$01,$0c,$00,$0e,$14,$13,$03,$00,$03,$0c,$0f,$03,$0b,$00,$03
        !byte $08,$01,$0e,$07,$05,$13,$00,$13,$14,$01,$19,$00,$01,$14,$0f,$0d
        !byte $09,$03,$00,$00,$00,$00,$00,$00,$03,$19,$03,$0c,$05,$00,$13,$14
        !byte $01,$0d,$10,$05,$04,$00,$13,$09,$04,$00,$17,$12,$09,$14,$05,$13
        !byte $00,$0b,$05,$05,$10,$00,$0f,$12,$04,$05,$12,$00,$00,$00,$00,$00
        !byte $12,$0f,$0c,$0c,$02,$01,$03,$0b,$00,$0d,$01,$0b,$05,$13,$00,$03
        !byte $26,$24,$00,$13,$05,$12,$16,$09,$03,$05,$00,$01,$14,$0f,$0d,$09
        !byte $03,$00,$00,$00,$00,$00,$00,$00,$02,$0c,$0f,$03,$0b,$00,$13,$10
        !byte $0c,$09,$14,$13,$00,$03,$0f,$0e,$13,$05,$12,$16,$05,$00,$10,$08
        !byte $19,$13,$09,$03,$01,$0c,$00,$14,$09,$0d,$05,$00,$00,$00,$00,$00
        !byte $01,$12,$10,$13,$09,$04,$00,$16,$29,$26,$25,$00,$00,$0e,$0f,$00
        !byte $13,$05,$03,$0f,$0e,$04,$00,$08,$09,$04,$04,$05,$0e,$00,$03,$0c
        !byte $0f,$03,$0b,$00,$00,$00,$00,$00
MessageFunctionEnd:

MessageModes:
        !byte $08,$0f,$13,$14,$13,$00,$00,$01,$15,$22,$00,$01,$15,$23,$00,$16
        !byte $13,$14,$23,$00,$03,$26,$24,$00,$10,$13,$09,$04,$00,$12,$13,$09
        !byte $04,$00,$00,$00,$00,$00,$00,$00,$01,$15,$00,$0e,$0f,$00,$0f,$15
        !byte $14,$10,$15,$14,$00,$01,$04,$16,$01,$0e,$03,$05,$13,$00,$04,$13
        !byte $10,$00,$06,$18,$00,$14,$05,$0c,$05,$0d,$05,$14,$12,$19,$00,$00
        !byte $16,$13,$14,$23,$00,$15,$13,$05,$13,$00,$14,$08,$05,$00,$03,$01
        !byte $0e,$0f,$0e,$09,$03,$01,$0c,$00,$12,$05,$0e,$04,$05,$12,$00,$03
        !byte $0f,$12,$05,$00,$00,$00,$00,$00,$07,$15,$09,$00,$12,$05,$01,$04
        !byte $13,$00,$09,$0d,$0d,$15,$14,$01,$02,$0c,$05,$00,$13,$0e,$01,$10
        !byte $13,$08,$0f,$14,$13,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
        !byte $03,$26,$24,$00,$13,$14,$12,$09,$03,$14,$00,$0f,$12,$00,$03,$0f
        !byte $0d,$10,$01,$14,$09,$02,$0c,$05,$00,$09,$13,$00,$05,$18,$10,$0c
        !byte $09,$03,$09,$14,$00,$00,$00,$00,$10,$12,$05,$13,$05,$14,$13,$00
        !byte $0b,$09,$14,$13,$00,$04,$09,$07,$09,$00,$01,$0e,$04,$00,$13,$14
        !byte $01,$14,$05,$00,$12,$0f,$0f,$14,$13,$00,$00,$00,$00,$00,$00,$00
        !byte $10,$01,$0e,$09,$03,$00,$12,$05,$17,$09,$0e,$04,$00,$13,$14,$0f
        !byte $10,$00,$13,$14,$01,$12,$14,$00,$13,$14,$01,$19,$00,$03,$0c,$05
        !byte $01,$0e,$00,$00,$00,$00,$00,$00,$10,$01,$0c,$00,$0e,$14,$13,$03
        !byte $00,$0d,$15,$0c,$14,$09,$00,$13,$09,$04,$00,$0c,$09,$16,$05,$00
        !byte $14,$05,$0c,$05,$0d,$05,$14,$12,$19,$00,$00,$00,$00,$00,$00,$00
        !byte $01,$12,$10,$13,$09,$04,$00,$16,$29,$26,$25,$00,$00,$02,$15,$09
        !byte $0c,$14,$00,$06,$0f,$12,$00,$12,$05,$01,$0c,$14,$09,$0d,$05,$00
        !byte $01,$15,$04,$09,$0f,$00,$00,$00
MessageModesEnd:








; Active release contains no stale or inactive music runtime tables.

asset_end:
!if asset_end > $c000 {
        !error "Asset block crossed $c000."
}

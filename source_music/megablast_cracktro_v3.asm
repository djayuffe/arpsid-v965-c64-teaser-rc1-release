; =============================================================================
;  P U L S E   C R E W   -   C R A C K T R O   " M E G A B L A S T "
; =============================================================================
;  Title........: Megablast
;  Type.........: 1x1-speed SID cracktro, PAL 50 Hz
;  Effects......: split hardware scroller, long-message 16-bit scroller,
;                 bass flash, title shimmer, lower-border raster bars,
;                 triangle PWM, clamped filter wah
;  Group........: The Pulse Crew
;  Machine......: Commodore 64 PAL, 6581/8580 SID
;  Assembler....: ACME 0.96+
;
;  Build:
;       acme -f cbm -o build/megablast.prg src/cracktro.asm
;
;  Run:
;       SYS 2062
; =============================================================================

        !cpu 6510

; =============================================================================
;  CONSTANTS
; =============================================================================

zpPtr           = $fb
zpArp           = $fd

SID             = $d400
SCR             = $0400
COL             = $d800
SCROLLER_ROW    = $07c0              ; screen row 24 = $0400 + 24*40
SCROLLER_COL    = $dbc0              ; colour row 24

; =============================================================================
;  BASIC STUB: 10 SYS 2062
; =============================================================================

        * = $0801
        !byte $0c,$08,$0a,$00,$9e,$20,$32,$30,$36,$32,$00,$00,$00

; =============================================================================
;  MAIN
; =============================================================================

start:
        sei

        jsr initScreen
        jsr initSID
        jsr initVars

        ; Disable CIA IRQs and acknowledge pending CIA latches.
        lda #$7f
        sta $dc0d
        sta $dd0d
        lda $dc0d
        lda $dd0d

        ; Enable only VIC-II raster IRQ.
        lda #$01
        sta $d01a

        ; Screen on, 25 rows, raster high bit clear.
        lda #$1b
        sta $d011

        ; Stable top-screen default: 40-column, fine scroll 0.
        lda #$08
        sta $d016

        ; Top IRQ starts at raster 0 through the KERNAL IRQ vector.
        lda #0
        sta $d012
        lda #<irqTop
        sta $0314
        lda #>irqTop
        sta $0315

        ; Ack pending VIC sources.
        lda #$0f
        sta $d019

        cli

mainLoop:
        jmp mainLoop

; =============================================================================
;  IRQ MULTIPLEXER
; =============================================================================

irqTop:
        lda #$01
        sta $d019

        ; Top/title area locked: no wobble from bottom hardware scroller.
        lda #$08
        sta $d016

        ; Music first so bass-triggered flash is visible on the same frame.
        jsr playMusic
        jsr flashUpdate
        jsr titleShimmer
        jsr scrollerColorPulse

        ; Schedule bottom split just before the scroller row.
        lda #238
        sta $d012
        lda #<irqBottom
        sta $0314
        lda #>irqBottom
        sta $0315

        jmp $ea81

irqBottom:
        lda #$01
        sta $d019

        ; Apply fine scroll only for lower screen/scroller region.
        jsr scrollUpdate

irqBottom_waitLowerBorder:
        lda $d012
        cmp #250
        bcc irqBottom_waitLowerBorder

        jsr rasterBars

        ; Return to top split.
        lda #0
        sta $d012
        lda #<irqTop
        sta $0314
        lda #>irqTop
        sta $0315

        jmp $ea81

; =============================================================================
;  MUSIC PLAYER
; =============================================================================

playMusic:
        ldx #0
        jsr voiceUpdate

        ldx #1
        jsr voiceUpdate

        ldx #2
        jsr voiceUpdate

        jsr pwmUpdate
        jsr filtUpdate
        rts

; -----------------------------------------------------------------------------
;  voiceUpdate
;  X = voice index 0..2
; -----------------------------------------------------------------------------

voiceUpdate:
        lda v_ptrLo,x
        sta zpPtr
        lda v_ptrHi,x
        sta zpPtr+1

        lda v_dur,x
        sec
        sbc #1
        sta v_dur,x
        beq voiceUpdate_fetch

        jmp effects

voiceUpdate_fetch:
        ldy #0

voiceUpdate_streamLoop:
        lda (zpPtr),y
        cmp #$fe
        beq voiceUpdate_loopCommand
        cmp #$ff
        beq voiceUpdate_restCommand
        cmp #$80
        bcs voiceUpdate_instCommand

        ; Note byte, followed by duration.
        sta v_note,x
        iny

        lda (zpPtr),y
        sta v_dur,x
        iny

        lda #1
        sta v_gate,x

        lda #0
        sta v_arpIdx,x

        jsr triggerNote
        jmp voiceUpdate_storePointer

voiceUpdate_instCommand:
        and #$7f
        sta v_inst,x
        iny
        jmp voiceUpdate_streamLoop

voiceUpdate_restCommand:
        iny
        lda (zpPtr),y
        sta v_dur,x
        iny

        lda #0
        sta v_gate,x
        jsr gateOff
        jmp voiceUpdate_storePointer

voiceUpdate_loopCommand:
        lda v_startLo,x
        sta zpPtr
        lda v_startHi,x
        sta zpPtr+1
        ldy #0
        jmp voiceUpdate_streamLoop

voiceUpdate_storePointer:
        tya
        clc
        adc zpPtr
        sta v_ptrLo,x
        lda zpPtr+1
        adc #0
        sta v_ptrHi,x

        jmp effects

; -----------------------------------------------------------------------------
;  effects
;  X = voice index 0..2
; -----------------------------------------------------------------------------

effects:
        ldy v_inst,x

        lda instArpLo,y
        sta zpArp
        lda instArpHi,y
        sta zpArp+1

        lda zpArp
        ora zpArp+1
        beq effects_noArp

        ldy v_arpIdx,x
        lda (zpArp),y
        cmp #$80
        bne effects_haveOffset

        ldy #0
        tya
        sta v_arpIdx,x
        lda (zpArp),y

effects_haveOffset:
        pha

        lda v_arpIdx,x
        clc
        adc #1
        sta v_arpIdx,x

        pla
        clc
        adc v_note,x
        jmp effects_writeFreq

effects_noArp:
        lda v_note,x

effects_writeFreq:
        jsr calcFreq

        ldy sidOff,x
        lda zpFreqLo
        sta SID+0,y
        lda zpFreqHi
        sta SID+1,y
        rts

; -----------------------------------------------------------------------------
;  triggerNote
;  X = voice index 0..2
; -----------------------------------------------------------------------------

triggerNote:
        sty savedY
        ldy v_inst,x

        txa
        pha

        lda sidOff,x
        tax                         ; X = SID voice register offset: 0,7,14

        ; Bass note trigger -> visual flash.
        cpx #7
        bne triggerNote_noBassFlash
        lda #8
        sta flashActive

triggerNote_noBassFlash:
        ; Voice 3 has live PWM. Do not overwrite PW on note trigger.
        cpx #14
        beq triggerNote_skipPW

        lda instPWlo,y
        sta SID+2,x
        lda instPWhi,y
        sta SID+3,x

triggerNote_skipPW:
        lda instAD,y
        sta SID+5,x
        lda instSR,y
        sta SID+6,x

        ; Force clean 0 -> 1 gate edge.
        lda instWave,y
        and #$fe
        sta SID+4,x
        ora #$01
        sta SID+4,x

        pla
        tax
        ldy savedY
        rts

; -----------------------------------------------------------------------------
;  gateOff
;  X = voice index 0..2
; -----------------------------------------------------------------------------

gateOff:
        sty savedY
        ldy v_inst,x
        lda instWave,y
        and #$fe
        ldy sidOff,x
        sta SID+4,y
        ldy savedY
        rts

; -----------------------------------------------------------------------------
;  calcFreq
;  A = note number 0..83
;  Output: zpFreqLo/zpFreqHi
; -----------------------------------------------------------------------------

calcFreq:
        ldy #6

calcFreq_divLoop:
        cmp #12
        bcc calcFreq_gotSemi
        sec
        sbc #12
        dey
        jmp calcFreq_divLoop

calcFreq_gotSemi:
        sty zpShift
        tay
        lda baseLo,y
        sta zpFreqLo
        lda baseHi,y
        sta zpFreqHi

        ldy zpShift
        beq calcFreq_done

calcFreq_shiftLoop:
        lsr zpFreqHi
        ror zpFreqLo
        dey
        bne calcFreq_shiftLoop

calcFreq_done:
        rts

; -----------------------------------------------------------------------------
;  pwmUpdate
;  Triangle PWM for Voice 3. Clamped away from near-zero/near-full widths.
; -----------------------------------------------------------------------------

pwmUpdate:
        lda pwmDir
        bmi pwmUpdate_down

pwmUpdate_up:
        lda pwmLo
        clc
        adc #4
        sta pwmLo
        lda pwmHi
        adc #0
        and #$0f
        sta pwmHi
        cmp #$0e
        bcc pwmUpdate_write
        lda #$ff
        sta pwmDir
        jmp pwmUpdate_write

pwmUpdate_down:
        lda pwmLo
        sec
        sbc #4
        sta pwmLo
        lda pwmHi
        sbc #0
        and #$0f
        sta pwmHi
        cmp #$02
        bcs pwmUpdate_write
        lda #$01
        sta pwmDir

pwmUpdate_write:
        lda pwmLo
        sta SID+16
        lda pwmHi
        sta SID+17
        rts

; -----------------------------------------------------------------------------
;  filtUpdate
;  Clamped triangle filter sweep. Never writes below $20 or above $cf.
; -----------------------------------------------------------------------------

filtUpdate:
        lda filtStep
        bmi filtUpdate_down

filtUpdate_up:
        lda filtVal
        clc
        adc #1
        cmp #$d0
        bcc filtUpdate_storeUp
        lda #$cf
        sta filtVal
        lda #$ff
        sta filtStep
        jmp filtUpdate_write

filtUpdate_storeUp:
        sta filtVal
        jmp filtUpdate_write

filtUpdate_down:
        lda filtVal
        sec
        sbc #1
        cmp #$20
        bcs filtUpdate_storeDown
        lda #$20
        sta filtVal
        lda #$01
        sta filtStep
        jmp filtUpdate_write

filtUpdate_storeDown:
        sta filtVal

filtUpdate_write:
        lda filtVal
        sta SID+22
        rts

; =============================================================================
;  VISUAL EFFECTS
; =============================================================================

; -----------------------------------------------------------------------------
;  flashUpdate
;  Bass-triggered background pulse with colour decay.
; -----------------------------------------------------------------------------

flashUpdate:
        lda flashActive
        beq flashUpdate_black
        tax
        lda flashTab,x
        sta $d021
        dex
        stx flashActive
        rts

flashUpdate_black:
        lda #0
        sta $d021
        rts

; -----------------------------------------------------------------------------
;  titleShimmer
;  Cheap colour-RAM shimmer on the four static title lines.
; -----------------------------------------------------------------------------

titleShimmer:
        lda titleDelay
        sec
        sbc #1
        sta titleDelay
        beq titleShimmer_advance
        rts

titleShimmer_advance:
        lda #3
        sta titleDelay

        lda titlePhase
        clc
        adc #1
        and #15
        sta titlePhase

        tax
        lda titleColors,x
        sta $d920               ; row 7 colour start
        sta $d974               ; row 9 colour start
        sta $d9c4               ; row 11 colour start
        sta $da14               ; row 13 colour start

        inx
        txa
        and #15
        tax
        lda titleColors,x
        sta $d921
        sta $d975
        sta $d9c5
        sta $da15
        rts

; -----------------------------------------------------------------------------
;  scrollerColorPulse
;  Slow colour wobble for the scroller row. Keeps row readable.
; -----------------------------------------------------------------------------

scrollerColorPulse:
        lda scrollColorDelay
        sec
        sbc #1
        sta scrollColorDelay
        beq scrollerColorPulse_advance
        rts

scrollerColorPulse_advance:
        lda #4
        sta scrollColorDelay

        lda scrollColorPhase
        clc
        adc #1
        and #7
        sta scrollColorPhase
        tax
        lda scrollColors,x
        sta scrollerCurrentColor

        ldx #0
scrollerColorPulse_loop:
        lda scrollerCurrentColor
        sta SCROLLER_COL,x
        inx
        cpx #40
        bne scrollerColorPulse_loop
        rts

; -----------------------------------------------------------------------------
;  rasterBars
;  Bottom-border rolling raster bars.
; -----------------------------------------------------------------------------

rasterBars:
        ldx barOffset
        ldy #14

rasterBars_loop:
        lda barColors,x
        sta $d020

        ; Wait for next raster line.
        lda $d012
rasterBars_wait:
        cmp $d012
        beq rasterBars_wait

        txa
        clc
        adc #1
        and #15
        tax

        dey
        bne rasterBars_loop

        lda #0
        sta $d020

        lda barDelay
        sec
        sbc #1
        sta barDelay
        bne rasterBars_done

        lda #2
        sta barDelay
        lda barOffset
        clc
        adc #1
        and #15
        sta barOffset

rasterBars_done:
        rts

; =============================================================================
;  SMOOTH HARDWARE SCROLLER
; =============================================================================

scrollUpdate:
        lda xscroll
        sec
        sbc #1
        and #7
        sta xscroll

        ; 38-column mode plus fine scroll. Bit 3 remains clear.
        sta $d016

        cmp #7
        beq scrollUpdate_shift
        rts

scrollUpdate_shift:
        ldx #0

scrollUpdate_copy:
        lda SCROLLER_ROW+1,x
        sta SCROLLER_ROW,x
        inx
        cpx #39
        bne scrollUpdate_copy

        ; 16-bit message pointer. The text is longer than 255 bytes, so a
        ; single Y index would silently truncate the message on real 6502.
        lda scrollPtrLo
        sta zpPtr
        lda scrollPtrHi
        sta zpPtr+1
        ldy #0
        lda (zpPtr),y
        cmp #$ff
        bne scrollUpdate_put

        lda #<scrollText
        sta scrollPtrLo
        sta zpPtr
        lda #>scrollText
        sta scrollPtrHi
        sta zpPtr+1
        ldy #0
        lda (zpPtr),y

scrollUpdate_put:
        sta SCROLLER_ROW+39

        lda scrollPtrLo
        clc
        adc #1
        sta scrollPtrLo
        lda scrollPtrHi
        adc #0
        sta scrollPtrHi
        rts

; =============================================================================
;  INITIALISATION
; =============================================================================

initSID:
        ldx #$18
        lda #0

initSID_clearLoop:
        sta SID,x
        dex
        bpl initSID_clearLoop

        ; Voice 3 starts at safe midpoint pulse width.
        lda #$00
        sta SID+16
        lda #$08
        sta SID+17

        ; Filter: cutoff low 0, cutoff high start, resonance, voice 3 routed.
        lda #$00
        sta SID+21
        lda #$40
        sta SID+22
        lda #$a4
        sta SID+23
        lda #$1f
        sta SID+24
        rts

initScreen:
        lda #0
        sta $d020
        sta $d021

        ldx #0

initScreen_clearLoop:
        lda #$20
        sta $0400,x
        sta $0500,x
        sta $0600,x
        sta $0700,x

        lda #$0e
        sta $d800,x
        sta $d900,x
        sta $da00,x
        sta $db00,x

        inx
        bne initScreen_clearLoop

        ldx #0

initScreen_scrollerColorLoop:
        lda #$01
        sta SCROLLER_COL,x
        inx
        cpx #40
        bne initScreen_scrollerColorLoop

        jsr drawTitle
        rts

drawTitle:
        ldx #0

drawTitle_t1Loop:
        lda t1,x
        cmp #$ff
        beq drawTitle_t2
        sta $0520,x
        inx
        bne drawTitle_t1Loop

drawTitle_t2:
        ldx #0

drawTitle_t2Loop:
        lda t2,x
        cmp #$ff
        beq drawTitle_t3
        sta $0574,x
        inx
        bne drawTitle_t2Loop

drawTitle_t3:
        ldx #0

drawTitle_t3Loop:
        lda t3,x
        cmp #$ff
        beq drawTitle_t4
        sta $05c4,x
        inx
        bne drawTitle_t3Loop

drawTitle_t4:
        ldx #0

drawTitle_t4Loop:
        lda t4,x
        cmp #$ff
        beq drawTitle_done
        sta $0614,x
        inx
        bne drawTitle_t4Loop

drawTitle_done:
        rts

initVars:
        ldx #2

initVars_voiceLoop:
        lda v_startLo,x
        sta v_ptrLo,x
        lda v_startHi,x
        sta v_ptrHi,x

        lda #1
        sta v_dur,x

        lda #0
        sta v_note,x
        sta v_gate,x
        sta v_arpIdx,x
        sta v_inst,x

        dex
        bpl initVars_voiceLoop

        lda #7
        sta xscroll

        lda #$00
        sta pwmLo
        lda #$08
        sta pwmHi
        lda #$01
        sta pwmDir

        lda #$40
        sta filtVal
        lda #$01
        sta filtStep

        lda #0
        sta flashActive
        sta barOffset
        sta titlePhase
        sta scrollColorPhase

        lda #<scrollText
        sta scrollPtrLo
        lda #>scrollText
        sta scrollPtrHi

        lda #1
        sta barDelay
        lda #3
        sta titleDelay
        lda #4
        sta scrollColorDelay
        lda #1
        sta scrollerCurrentColor
        rts

; =============================================================================
;  MUSIC DATA
; =============================================================================

baseLo:
        !byte $9c,$c0,$23,$c9,$b5,$ec,$73,$4e,$82,$12,$08,$68
baseHi:
        !byte $45,$49,$4e,$52,$57,$5c,$62,$68,$6e,$75,$7c,$83

sidOff:
        !byte 0,7,14

; Instruments:
; 0 = lead pulse
; 1 = bass saw
; 2 = major arp pulse
; 3 = minor arp pulse
instWave:
        !byte $40,$20,$40,$40
instAD:
        !byte $0a,$08,$06,$06
instSR:
        !byte $c9,$68,$a6,$a6
instPWlo:
        !byte $00,$00,$00,$00
instPWhi:
        !byte $08,$08,$04,$04
instArpLo:
        !byte $00,$00,<arpMajTab,<arpMinTab
instArpHi:
        !byte $00,$00,>arpMajTab,>arpMinTab

arpMajTab:
        !byte 0,4,7,$80
arpMinTab:
        !byte 0,3,7,$80

chordData:
        !byte $83,57,48
        !byte $82,53,48
        !byte $82,48,48
        !byte $82,55,48
        !byte $fe

bassData:
        !byte $81
        !byte 33,12, 33,12, 28,12, 33,12
        !byte 29,12, 29,12, 36,12, 29,12
        !byte 36,12, 36,12, 31,12, 36,12
        !byte 31,12, 31,12, 38,12, 31,12
        !byte $fe

leadData:
        !byte $80
        !byte 64,12, 69,12, 72,12, 71,12
        !byte 65,12, 69,12, 72,12, 69,12
        !byte 64,12, 67,12, 72,12, 67,12
        !byte 62,12, 67,12, 71,12, 74,12
        !byte $fe

v_startLo:
        !byte <chordData,<bassData,<leadData
v_startHi:
        !byte >chordData,>bassData,>leadData

; =============================================================================
;  VISUAL DATA
; =============================================================================

flashTab:
        !byte $00,$06,$0e,$03,$01,$01,$03,$0e,$06

barColors:
        !byte $06,$06,$0e,$0e,$03,$03,$01,$01
        !byte $03,$03,$0e,$0e,$06,$06,$00,$00

titleColors:
        !byte $06,$0e,$03,$01,$03,$0e,$06,$04
        !byte $02,$0a,$07,$01,$07,$0a,$02,$04

scrollColors:
        !byte $01,$0e,$03,$0d,$01,$0d,$03,$0e

t1:
        !scr "the pulse crew"
        !byte $ff

t2:
        !scr "proudly presents"
        !byte $ff

t3:
        !scr "== megablast 2026 =="
        !byte $ff

t4:
        !scr "100 percent working"
        !byte $ff

scrollText:
        !scr "     the pulse crew is back with another 100 percent fix ....   "
        !scr "greetings fly out to all the old school crackers and swappers still "
        !scr "keeping the scene alive in 2026 !!!    "
        !scr "music and code hammered out in one sitting on a real breadbin ... "
        !scr "3 sid voices, hardware scroller, triangle pwm, shimmer text, "
        !scr "and a low pass filter doing the wah wah.        wrap it again ....          "
        !byte $ff

; =============================================================================
;  VARIABLES
; =============================================================================

v_ptrLo:
        !byte 0,0,0
v_ptrHi:
        !byte 0,0,0
v_dur:
        !byte 0,0,0
v_note:
        !byte 0,0,0
v_inst:
        !byte 0,0,0
v_gate:
        !byte 0,0,0
v_arpIdx:
        !byte 0,0,0

zpShift:
        !byte 0
zpFreqLo:
        !byte 0
zpFreqHi:
        !byte 0
savedY:
        !byte 0

xscroll:
        !byte 7
scrollPtrLo:
        !byte <scrollText
scrollPtrHi:
        !byte >scrollText

pwmLo:
        !byte 0
pwmHi:
        !byte $08
pwmDir:
        !byte 1

filtVal:
        !byte $40
filtStep:
        !byte 1

flashActive:
        !byte 0
barOffset:
        !byte 0
barDelay:
        !byte 1

titlePhase:
        !byte 0
titleDelay:
        !byte 3
scrollColorPhase:
        !byte 0
scrollColorDelay:
        !byte 4
scrollerCurrentColor:
        !byte 1

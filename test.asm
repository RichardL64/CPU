;
; Test.asm
;
;	Generic source code to test the assembler
;
;	R.Lincoln		January 2024
;

				isa				microcode
				org				$100

chrin 	= $ffcf
chrout	=	$ffd2
eof			= 'x'

start
.1 			dc.b 	12,"te st", 0x50, %1010, 70, $8, $10, "A", eof
.2
.s			dc.w	start
.m			dc.w	middle
.e			word	end
.3
				ds.b	1
				ds.w	1
				dword	$1 << 31, %11 << 29, %11 << 27

				nop
				nop

				ld	t,$d800							;	comment
.4 			ld	t,chrout						;	comment
				ld	t,#eof

				jsr	($fffe)

				jsr	chrout
				jsr	chrin

.fwd		jsr	middle
.back1	beq	.4
				jsr	.e
.back2	bne	start
				tx	t,a

;				*	=	$500

middle
.1			lda ($100),y
				lda ($50,x)
end

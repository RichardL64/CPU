;
;	Microcode source
;
;	Defines the microcode control word, microcoded instructions
;	Generates microcode and opcode labels for use by the assembler
;
;	R.Lincoln			Feb 2024
;
;

;
;	Control word definition
;
;	_r		reads from the device onto the bus
;	_w		writes to the device from the bus
;

;	1 bit last microcode cycle for this instruction
mc_end				= %1 << 31

;	1 bit pre fetch next instruction (address bus is free)
mc_fetch			= %1 << 30

;	2 bits write memory: 1 of 3
mc_mem_w_nop	= %00	<< 28
mc_word_w			= %01 << 28										; word
mc_byte_w			= %10 << 28										; low byte
mc_addr_w			= %11 << 28

;	2 bits read memory: 1 of 3
mc_mem_r_nop	= %00	<< 26
mc_word_r			= %01	<< 26
mc_byte_r			= %10	<< 26
mc_addr_r			=	%11 << 26

;	4 bits source register: 1 of 15
mc_r_nop			= $0 << 22
mc_a_r				= $1 << 22
mc_b_r				= $2 << 22
mc_t_r				= $3 << 22
mc_r_r				= $4 << 22
mc_o_r				= $5 << 22
mc_pc_r				= $6 << 22
mc_sp_r				= $7 << 22
mc_rsp_r			= $8 << 22
mc_alu_r			= $9 << 22
;							= $a
mc_flags_r		= $b << 22
;							= $b
;							= $c
mc_ws_r				= $d << 22										; read w swapped bytes
mc_w_r				= $e << 22										; read w normal bytes
mc_n_r				= $f << 22

; 4 bits destination register: 1 of 15
mc_w_nop			= $0 << 18
mc_a_w				= $1 << 18
mc_b_w				= $2 << 18
mc_t_w				= $3 << 18
mc_r_w				= $4 << 18
mc_o_w				= $5 << 18
mc_pc_w				= $6 << 18
mc_sp_w				= $7 << 18
mc_rsp_w			= $8 << 18
mc_alu1_w			= $9 << 18
mc_alu2_w			= $a << 18
mc_flags_w		= $b << 18
;							= $c
;							= $d
mc_w_w				= $e << 18
mc_n_w				= $f << 18

; 3 bits counters: 1 of 7										? - make this a pre-post increment/decrement on all registers
mc_c_nop			= $0 << 15
mc_sp_minus2	= $1 << 15
mc_sp_plus2		= $2 << 15
mc_rsp_minus2	= $3 << 15
mc_rsp_plus2	= $4 << 15
mc_pc_plus1		= $5 << 15
mc_pc_plus2		= $6 << 15
;							= $7 << 15

; 8 bits set/clear/use flag in microcode address
mc_flag_set		= %10000000 << 7
mc_flag_clear	= %01000000 << 7
mc_flag_i			= %00100000 << 7						; interrupt mask
mc_flag_b			= %00010000 << 7						; byte/word mode
mc_flag_n			= %00001000 << 7						; negative
mc_flag_v			=	%00000100 << 7						; overflow
mc_flag_z			= %00000010 << 7						; zero
mc_flag_c			= %00000001 << 7						; carry

; 4 bits alu operation: 1 of 15
mc_alu_nop		= $0 << 3

mc_alu_add		= $1 << 3
mc_alu_sub		= $2 << 3

mc_alu_and		= $3 << 3
mc_alu_or			= $4 << 3
mc_alu_xor		= $5 << 3

mc_alu_asl		= $6 << 3
mc_alu_asr		= $7 << 3
mc_alu_lsl		= $8 << 3
mc_alu_lsr		= $9 << 3

mc_alu_rol		= $a << 3
mc_alu_ror		= $b << 3

mc_alu_plus1	= $c << 3
mc_alu_plus2	= $d << 3
mc_alu_minus1	= $e << 3
mc_alu_minus2 = $f << 3

;	3 bits unused


;	non-conditional:	8 cycles per instruction
;	conditional:			4 cycles per flag state, flag appears in 4 bit
;
mc_inst				=	8																				; %nnnnn000
mc_flagclear	=	8																				; %nnnnn000
mc_flagset		=	4																				; %nnnnn100

;	mch		alignment, operand bytes
;	mc		32 bit microcode instruction
;
nop			mch			mc_inst, 0
				mc			mc_fetch | mc_end

jmp			mch			mc_inst, 2
				mc			mc_pc_r			| mc_addr_w
				mc			mc_word_r		| mc_pc_w		| mc_end

jtr			mch			mc_inst, 2															; jump and link in r
				mc   		mc_pc_r			| mc_r_w 		| mc_addr_w			; pc -> r & addr
				mc   		mc_word_r		| mc_pc_w 	| mc_end				; (pc) -> pc

rtr			mch			mc_inst, 0															; return to r
				mc   		mc_r_r			| mc_pc_w
				mc   		mc_pc_plus2	| mc_fetch	| mc_end

rtn			mch			mc_inst, 0															; return and next
				mc   		mc_r_r			| mc_addr_w									; r -> addr
				mc   		mc_word_r		| mc_pc_w										; (r) -> pc
				mc   		mc_pc_plus2 |	mc_fetch | mc_end					; pc+2

jsr			mch			mc_inst, 2
				mc			mc_sp_minus2
				mc			mc_sp_r | mc_addr_w											; sp -> addr
				mc			mc_pc_r | mc_word_w											; pc -> stack
				mc			mc_addr_w
				mc			mc_word_r | mc_pc_w | mc_end						; (pc) -> pc

jsr.(		mch			mc_inst, 2
				mc			mc_sp_minus2
				mc			mc_sp_r | mc_addr_w
				mc			mc_pc_r | mc_word_w											; pc -> (sp)
				mc			mc_addr_w
				mc			mc_word_r | mc_addr_w										; (pc) -> addr
				mc			mc_word_r | mc_pc_w | mc_end						; word -> pc

rts			mch			mc_inst, 0
				mc			mc_sp_r | mc_addr_w
				mc			mc_sp_plus2 | mc_word_r | mc_pc_w				; (sp) -> pc
				mc			mc_pc_plus2 | mc_fetch | mc_end					; pc+2


ld.t#		mch			mc_inst, 2
				mc			mc_pc_r | mc_addr_w
				mc			mc_word_r | mc_t_w | mc_end

tx.ta		mch			mc_inst, 0
				mc			mc_a_r | mc_w_w													; a -> w
				mc			mc_t_r | mc_a_w													; t -> a
				mc			mc_w_r | mc_t_w | mc_fetch | mc_end			; w -> t

lda.(y	mch			mc_inst, 2
				mc			mc_end

lda.(x)	mch			mc_inst, 2
				mc			mc_end


seb			mch			mc_inst, 0															; byte mode
				mc   		mc_flag_set | mc_flag_b | mc_fetch | mc_end

sew			mch			mc_inst, 0															; word mode
				mc   		mc_flag_clear | mc_flag_b | mc_fetch | mc_end

sec			mch			mc_inst, 0
				mc   		mc_flag_set | mc_flag_c | mc_fetch | mc_end

clc			mch			mc_inst, 0
				mc   		mc_flag_clear | mc_flag_c | mc_fetch | mc_end

phf			mch			mc_inst, 0
				mc			mc_sp_minus2
				mc			mc_sp_r 		| mc_addr_w
				mc			mc_flags_r 	| mc_byte_w | mc_end

plf			mch			mc_inst, 0
				mc			mc_sp_r				| mc_addr_w
				mc			mc_byte_r			| mc_flags_w	| mc_sp_plus2	| mc_end

pht			mch			mc_inst, 0
				mc			mc_sp_minus2
				mc			mc_sp_r | mc_addr_w
				mc			mc_t_r	| mc_word_w | mc_end

plt			mch			mc_inst, 0
				mc			mc_sp_r		| mc_addr_w
				mc			mc_word_r	| mc_t_w		| mc_sp_plus2	| mc_end

push.t	mch			mc_inst, 0
				mc			mc_sp_minus2
				mc			mc_sp_r	| mc_addr_w
				mc			mc_n_r	| mc_word_w												; n -> (sp)
				mc			mc_t_r	| mc_n_w		| mc_fetch	| mc_end	; t -> n

pop.t		mch			mc_inst, 0
				mc			mc_n_r		| mc_t_w												; n -> t
				mc			mc_sp_r		| mc_addr_w
				mc			mc_word_r	| mc_n_w 		| mc_sp_plus2	| mc_end

sp.a.b	mch			mc_inst, 0
				mc			mc_a_r | mc_w_w
				mc			mc_b_r | mc_a_w	| mc_fetch
				mc			mc_w_r | mc_b_w | mc_end

sp.t		mch			mc_inst, 0																; byte swap
				mc			mc_t_r | mc_w_w
				mc			mc_ws_r | mc_t_w | mc_fetch | mc_end

beq			mch			mc_flagclear, 2														; z=0
				mc   		mc_flag_z	| mc_pc_plus2	| mc_fetch	| mc_end

				align		mc_flagset																; z=1
				mc   		mc_flag_z | mc_pc_r 	| mc_addr_w
				mc   		mc_flag_z | mc_word_r	| mc_pc_w 	| mc_end

bne			mch			mc_flagclear, 2														; z=0
				mc   		mc_flag_z | mc_pc_r		| mc_addr_w
				mc   		mc_flag_z | mc_word_r	| mc_pc_w		| mc_end

				align		mc_flagset																; z=1
				mc   		mc_flag_z	| mc_pc_plus2	| mc_fetch	| mc_end

ld.t		mch			mc_flagclear, 2														; 16 bit mode
				mc			mc_flag_b	|	mc_pc_r	| mc_addr_w
				mc			mc_flag_b	|	mc_word_r | mc_addr_w
				mc			mc_flag_b	|	mc_word_r | mc_t_w | mc_end

				mch			mc_flagset, 2															; 8 bit mode
				mc			mc_flag_b	|	mc_pc_r	| mc_addr_w
				mc			mc_flag_b	|	mc_word_r | mc_addr_w
				mc			mc_flag_b	|	mc_byte_r | mc_t_w | mc_end

ld.#.t	mch			mc_flagclear,2														; 16 bit mode
				mc			mc_flag_b	| mc_pc_r	| mc_addr_w
				mc			mc_flag_b	| mc_word_r | mc_t_w | mc_end

				align		mc_flagset																; 8 bit mode
				mc			mc_flag_b	| mc_pc_r		| mc_addr_w
				mc			mc_flag_b	| mc_byte_r	| mc_t_w | mc_end

old.#.t	mch			mc_inst, 2																; (o + #) -> t
				mc			mc_o_r 		| mc_alu1_w											; o -> alu1
				mc			mc_pc_r 	| mc_addr_w
				mc			mc_word_r | mc_alu2_w											; (pc) -> alu2
 				mc			mc_flag_clear | mc_flag_c | mc_alu_add		; +
				mc			mc_alu_r 	| mc_addr_w
				mc			mc_word_r | mc_t_w 				| mc_end				; (alur) -> t

ost.#.t	mch			mc_inst, 2																; t -> (o + #)
				mc			mc_o_r				| mc_alu1_w									; o -> alu1
				mc			mc_pc_r 			| mc_addr_w
				mc			mc_word_r 		| mc_alu2_w									; (pc) -> alu2
				mc			mc_flag_clear | mc_flag_c | mc_alu_add		; +
				mc			mc_alu_r 			| mc_addr_w
				mc			mc_t_r				| mc_word_w	| mc_end				; t -> (alur)

ojp.#		mch			mc_inst, 2																; (o + #) -> pc
				mc			mc_o_r				| mc_alu1_w									; o -> alu1
				mc			mc_pc_r 			| mc_addr_w
				mc			mc_word_r 		| mc_alu2_w									; (pc) -> alu2
				mc			mc_flag_clear | mc_flag_c | mc_alu_add		; +
				mc			mc_alu_r	| mc_pc_w				| mc_end				; alur -> pc

t.sp.o	mch			mc_inst, 0																; sp -> o
				mc			mc_sp_r		| mc_o_w	| mc_fetch | mc_end






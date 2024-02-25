"""

Simulator

R.Lincoln		February 2024

Simulate the processor at execution of microcode level

"""

#	32 bit wide microcode memory
#
microcode = [
]

#	8 bit wide ram
#
ram = [
]
rAddr = 0


#	Registers
#
rA = 0
rB = 0
rX = 0
rY = 0

rT = 0
rR = 0
rO = 0

rSP = 0
rRSP = 0

# Internal implicitly accessed registers
#
rPC = 0
rW = 0

rFlags = 0

rALU1 = 0
rALU2 = 0
rALUR = 0

#	Microcode pointer
#
rMCP = 0

#	The data bus
BUS = 0


#	Initialise ram etc
#
def init():
	for i in range(0, 2048):				# 2k x 32 bits
		microcode.append(0x00000000)

	for i in range(0, 65536):				# 64k x 8 bits
		ram.append(0x00)

	rPC = 0

	return

#
#	Return the instruction at the PC
#
def fetch():
	global BUS, rPC

	BUS = ram[rPC]
	rPC += 1

	print(rPC)
	return


#
#	Generate the MCPC from the opcode on the bus
#
def decode():
	global rMCP, BUS, rFlags

	rMCP = BUS << 3												# 3 bits for microcode line

	mc = microcode[rMCP]
	f = mc_flag_i or mc_flag_b or mc_flag_n or mc_flag_v or mc_flag_z or mc_flag_c

	if mc & f:														# ? selected in the instruction
		if rFlags | f:											# ? set in the flags register
			rMCP |= 4													# => set in the counter

	return


#
#	Sequence through microcode from MCPC
#	write to the bus on rising edge
#	read from the bus on falling edge
#
def execute():
	global rMCP

	while True:
		mc = microcode[rMCP]								# next microcode line
		rMCP += 1

		if mc & mc_end:
			break															# --->

		execRising(mc)											# clock rising edge
		execFalling(mc)											# clock falling edge

	return


#
#	Rising edge read from devices to the bus and/or start activity
#	Device => Bus
#
def execRising(mc):
	global BUS, rAddr, rA, rB, rX, rY

	if mc & mc_fetch:										# prefetch
		rAddr = rPC												# models a direct PC to Addr path

	if mc & mc_word_r:									# RAM
		BUS = ram[rAddr] + ram[rAddr +1] << 8
	if mc & mc_byte_r:
		BUS = ram[rAddr]
	if mc & mc_addr_r:
		BUS = rAddr

	if mc & mc_a_r:	BUS = rA						# registers
	if mc & mc_b_r:	BUS = rB
	if mc & mc_x_r:	BUS = rX
	if mc & mc_y_r:	BUS = rY

	if mc & mc_t_r:	BUS = rT
	if mc & mc_n_r:	BUS = rN
	if mc & mc_r_r:	BUS = rR
	if mc & mc_o_r:	BUS = rO

	if mc & mc_sp_r:	BUS = rSP
	if mc & mc_rsp_r:	BUS = rRSP

	if mc & mc_pc_r:	BUS = rPC
	if mc & mc_w_r:		BUS = rW
	if mc & mc_ws_r:	BUS = (rW & 255) << 8 | (rw >> 8)

	if mc & mc_f_r:		BUS = rFlags

	if mc & mc_alu1_r:	BUS = rALU1
	if mc & mc_alu2_r:	BUS = rALU2
	if mc & mc_alur_r:	BUS = rALUR

	if mc & mc_sp_minus2:								# counters pre decrement
		rSP -= 2
	if mc & mc_rsp_minus2:
		rRSP -= 2

	if mc & mc_flag_set:								# flags
		f = mc_flag_i or mc_flag_b or mc_flag_n or mc_flag_v or mc_flag_z or mc_flag_c
		rFlags |= f
	if mc & mc_flag_clear:
		f = 0xff ^ (mc_flag_i or mc_flag_b or mc_flag_n or mc_flag_v or mc_flag_z or mc_flag_c)
		rFlags &= f
	if mc_flag_set == 0 & mc_flag_clear == 0:
		BUS = mc_flag_i or mc_flag_b or mc_flag_n or mc_flag_v or mc_flag_z or mc_flag_c

	if mc & mc_alu_add:									# ALU
		rALUR = ALU1 + ALU2
		if rALUR == 0:										# <-- factor out flag setting
			rFlags |= zero
		else
			rFlags &= 0xff ^ zero
		if rALUR > 0xffff:
			rFlags |= carry
		else
			rFlags &= 0xff ^ carry

		rFlags |= rALUR | 0x8000 | negative
		rALUR &= 0xffff

	if mc & mc_alu_sub:
		rALUR = ALU1 - ALU2
	if mc & mc_alu_and:
		rALUR = ALU1 and ALU2
	if mc & mc_alu_or:
		rALUR = ALU1 or ALU2
	if mc & mc_alu_xor:
		rALUR = ALU1 ^ ALU2

#asl
#asr
	if mc & mc_alu_inc:
		ALU1 += 1
	if mc & mc_alu_dec:
		ALU1 -= 1
#rol
#ror
#cmp
	if mc & mc_alu_lsl:
		ALU1 << 1
	if mc & mc_alu_lsr:
		ALU1 >> 1

	return


#
#	Falling edge - write to devices from the bus
#	Device <= Bus
#
def execFalling(mc):

	if mc & mc_fetch:
		rAddr = rPC												# models a direct PC to Addr path
		rPC += 1

	if mc & mc_word_w:									# write memory
		ram[rAddr]		= BUS & 0xff
		ram[rAddr+1]	= BUS >> 8
	if mc & mc_byte_w:
		ram[rAddr] 		= BUS & 0xff
	if mc & mc_addr_w:
		rAddr = BUS

	if mc & mc_a_w:	rA = BUS
	if mc & mc_b_w:	rB = BUS
	if mc & mc_x_w:	rX = BUS
	if mc & mc_y_w:	rY = BUS

	if mc & mc_t_w:	rT = BUS
	if mc & mc_n_w:	rN = BUS
	if mc & mc_r_w:	rR = BUS
	if mc & mc_o_w:	rO = BUS

	if mc & mc_sp_w:	rSP = BUS
	if mc & mc_rsp_w:	rRSP = BUS

	if mc & mc_pc_w:	rPC = BUS
	if mc & mc_w_w:		rW = BUS

	if mc & mc_f_w:		rFlags = BUS

	if mc & mc_alu1_w:	rALU1 = BUS
	if mc & mc_alu2_w:	rALU2 = BUS
	if mc & mc_alur_w:	rALUR = BUS

	if mc & mc_sp_plus2:								# counters post increment
		rSP += 2
	if mc & mc_rsp_plus2:
		rRSP += 2
	if mc & mc_pc_plus1:
		rPC += 1
	if mc & mc_pc_plus2:
		rPC += 2

	return


#
#
#
init()
fetch()
decode()
execute()



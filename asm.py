"""

Assembler
Nominally understands 6502 syle opcode/addressing mode source formats
Table driven instructions derived from assembling the cpu's own microcode

i.e.
	asm microcode.asm -> microcode.obj
	microcode.obj -> asm source.asm -> source.obj


R.Lincoln		February 2024

Programming model
	8 bit instructions
	8-32 bit operands
	Table driven registers & instructions

Syntax

	[label | .label]   mnemonic   [operand,[operand]...]   [; comment]


"""

import sys
import srec
import ihex

#
#	Register list
# Added to instructions for a unique key
#
registers = [
	"a", "b",
	"x", "y", "x)",
	"t", "n"
]

#
#	Label values dictionary simple name/value pairs
#	Updated as defined, kept between passes
#
labels = {
}

LABEL_SCOPE = "."									# scope label for . locals

#
#	Instruction reference generated from the microcode assembly listing
#
#	Opcode 	+ve		Instruction to be assembled with operands
#					-1		Directive	- no opcode, no operands		eg. align, org
#					-2							-	no opcode, with operands 	eg. dc.b dc.w
#					-3							- one address per operand 	eg. microcode with 4 byte operands at each address
#
INS_OPCODE						=	0					# -1 = no opcode
INS_OPER_BYTES				= 1					# bytes in each operand

INS_OPCODE_NONE				= -1				# no opcode or operands
INS_OPCODE_OPS				= -2				# only operands
INS_OPCODE_MC					= -3				# one address per operand

instructions = {
	#
	#	Internal directives
	#
	"":				[-1, 0],
	"isa":		[-1, 0],
	"org":		[-1, 2],
	"=":			[-1, 2],
	"align":	[-1, 1],

	"dc.b":		[-2, 1],							# initialised space
	"dc.w":		[-2, 2],

	"byte":		[-2, 1],
	"word":		[-2, 2],

	"dword":	[-2, 4],

	"ds.b":		[-1, 1],							# reserve uninitialised space
	"ds.w":		[-1, 1],
	"bytes":	[-1, 1],
	"words":	[-1, 1],

	"mch":		[-1, 1],							# microcode header to generate .opcode and .opbytes labels
	"mc":			[-3, 4],							# microcode memory 32 bit words at each address

	#
	#	Machine instructions (read from the microcode.obj file)
	#
#	"nop":		[0, 0],								# test data
#	"ld.t":		[1, 2],
#	"ld.t#":	[2, 2],
#	"jsr":		[3, 2],
#	"beq":		[4, 2],
#	"bne":		[5, 2],
#	"tx.ta":	[6, 0],
#	"jsr.(":	[7, 2],
#	"lda.(y":	[8, 1],
#	"lda.(x)":[9, 1]
}

#
#	Source line list structure & indexes
#
LINE_NUMBER		=	0
LINE_LABEL 		= 1
LINE_INSTR 		= 2
LINE_OPERS		= 3										# list of operands

LINE_ADDRESS 				= 4
LINE_INS						= 5							# copy of this line's instruction record
LINE_BYTES 					= 6							# list of bytes representing this line



#
#	Find any quote delimited strings and replace with a list of character byte values
#
def expandStrings(s):

	s = s.replace("'", "\"")													# normalise to double quotes

	i = 0
	j = 0
	while True:																				# until we run out of strings
		i = s.find("\"", j)															# opening quote
		if i == -1: break																# -->

		j = s.find("\"",i +1)														# closing quote
		if j == -1: j = len(s)													# ...or end of line

		# ord(char) for each letter then combine into a comma delimited string
		chars = ", ".join([str(ord(c)) for c in s[i+1:j]])

		s = s[:i] + " " + chars + s[j +1:]							# replace the quoted string with the char list

	return s


#
#	Parse one line of source to split out component fields
#
def parseLine(source):
	label = ""
	instr = ""
	opers = []

	source = source.rstrip(" \t\n")									# discard carriage control
	source = expandStrings(source)									# convert quoted strings to lists of chars
	source = source.partition(";")[0]								# discard comments
	source = source.replace("\t", " ")							# remove tabs to simplify later finds

	#	First word on the line is a label
	#
	i = source.find(" ")														# ? label - word at the beginning of the line
	if i == -1: i = len(source)
	if i>0:
		label = source[0:i]

		if label[0].startswith("."):									# ? .local label
			label = labels[LABEL_SCOPE] + "_" + label[1:]
		else:																					# else normal label
			labels[LABEL_SCOPE] = label									# save for the next local definition

	#	Second word is an instruction
	#
	source = source[i:].strip()											# remove leading whitespace
	j = source.find(" ")
	if j == -1: j = len(source)
	instr = source[:j]

	# Third onwards are operands
	#
	source = source[j:].strip()
	if source == "":
		opers = []
	else:
		opers = source.split(",")											# separate operands, leaves [''] if given an empty string
		opers = [o.strip() for o in opers]

	# Create the line structure
	line = [
		0,																						# source fields
		label,
		instr,
		opers,

		0,																						# assembled fields
		[0, 0, 0],
		[]
	]

	return line


#
#	Execute internal directives
#
def runDirectives(line):

	label		= line[LINE_LABEL]
	inst 		= line[LINE_INSTR]
	try:		op0 = line[LINE_OPERS][0]
	except: op0 = ""

	if inst == "org":																# org address
		op0 = max(0, op0)
		labels["*"] = op0
		line[LINE_ADDRESS] = labels["*"]

	elif inst == "isa":															# instruction set architecture, import file
		op0 = op0.partition(".")[0] + ".obj"
		importInstructions(op0)

	elif inst == "ds.b" or inst == "bytes":					# reserve uninitialised bytes
		labels["*"] += max(0, op0)

	elif inst == "ds.w" or inst == "words":					# reserve uninitialised words
		labels["*"] += max(0, op0) *2

	elif inst == "align":														# align <byte multiplier>
		op0 = max(1, op0)
		labels["*"] = -labels["*"] // op0 * -op0			# -ve // modulus to ceiling the divided number
		line[LINE_ADDRESS] = labels["*"]

	elif inst == "mch":															# microcode header: align, oper size
		op0 = max(1, op0)
		labels["*"] = -labels["*"] // op0 * -op0			# -ve // modulus to ceiling the divided number
		line[LINE_ADDRESS] = labels["*"]
		if label:
			labels[label +".instr"] = labels["*"] >> 3				# labels used to populate the instructions table
			labels[label +".obytes"] = line[LINE_OPERS][1]		# operands total bytes

	#	labels are either the line address or an explicit = declaration
	#
	if inst == "=":																	# ? label = value declaration
		labels[label] = op0
	elif label != "":																# default to the line address
		labels[label] = line[LINE_ADDRESS]

	return


#
#	Create a unique instruction key from its mnemonic & operand types
#
def instrKey(line):

	if line[LINE_INSTR] == "":																		# no instruction
		return

	key = line[LINE_INSTR] + "."
	for o in line[LINE_OPERS]:
		o0 = str(o)[0]

		if o in registers				: key += o
		if key == "mc"					:	key += "mc"
		if o0 == "#"						:	key += "#"
		if o0 == "("						: key += "("

	line[LINE_INSTR] = key.strip(".")

	return


#
#	Format operators for python eval
# 	()#$ to 0x 0b
#		. - to _					Eval interprets . as method call, - as operator
#
def formatOper(o):

	o = o.replace("#","").replace("(","").replace(")","")
	o = o.replace("$","0x").replace("%","0b")
	o = o.replace(".","_").replace("-","_")

	return o


#
#	Numbers formatted, local labels formatted, registers & references resolved
#
def resolveOpers(line):

	for i in range(0, len(line[LINE_OPERS])):
		o = line[LINE_OPERS][i]

		if o in registers:														# ? registers
			o = ""																			# ignored

		elif o.startswith("."):												# ? local
			o = labels[LABEL_SCOPE] + "_" + o[1:]				# .prefix with last label to localise

		if o != "":
			try:																				# lookup labels, evaluate  << >> && etc
				o = eval(formatOper(o), {}, labels)
			except Exception as err:										# will fail in pass 1 on forward references
				pass

		line[LINE_OPERS][i] = o
																									# remove empty strings
	line[LINE_OPERS] = [o for o in line[LINE_OPERS] if o != ""]

	return


#
#	Process passed input source file
#
#	Pass 1 - resolve label addresses
# Pass 2 - generate assembly and listing
#
def asmFile(name, p):

	errors = 0
	ln = 0																					# line number
	labels["*"] = 0																	# assembly address
	labels[LABEL_SCOPE] = ""												# label used to expand locals
	fout = 0																				# output object file, only on pass 2

	# If pass 2 open the output object file
	#
	if p == 2:
		fOut = open(name.partition(".")[0] + ".obj", "w")


	#	Read the input file line by line and parse into components
	#
	name = name.partition(".")[0] + ".asm"					# force .asm suffix
	f = open(name)
	for source in f:

		line = parseLine(source)											# parse

		ln += 1																				# line number
		line[LINE_NUMBER] = ln
		line[LINE_ADDRESS] = labels["*"]

		instrKey(line)																# generate instruction lookup key
		resolveOpers(line)														# operand lookup
		runDirectives(line)														# internal assembler directives & assignments

		# Lookup the instruction details
		#
		i = line[LINE_INSTR]
		if i in instructions:
			ins = instructions[i]
		else:
			errors += 1
			print("Unknown instruction: '{}' on line {}".format(i, ln))
			ins = instructions[""]											# process as null instruction
		line[LINE_INS] = ins													# take a copy into the line for reference

		# Increment address pointer for instruction and operands depending on type
		#
		op = ins[INS_OPCODE]
		if op >= 0:																		# ? opcode
			labels["*"] += 1

		if op >= 0 or op == -2:												# ? opcode or directive with operands to assemble
			labels["*"] += ins[INS_OPER_BYTES] * len(line[LINE_OPERS])

		if op == -3:																	# ? one address per operand, wide words for MC etc
			labels["*"] += len(line[LINE_OPERS])


		#	Pass 1 ends - Forward references will not be resolved yet
		#
		if p == 1:																		# ? pass 1
			continue																		# <-----------


		#	Pass 2 - Assemble machine code
		#
		assembleLine(line, fOut)
		listLine(line)


	#	Tidy up
	#
	f.close()
	if p == 2:
		writeLabels(fOut)
		fOut.close()

	print("\nPass {}: {} errors found".format(p, errors))

	return

#
#	Generate the lines byte array & output to its object file
#
def assembleLine(line, oFile):

	opers = line[LINE_OPERS]
	bytes = line[LINE_BYTES]

	ins = line[LINE_INS]
	op = ins[INS_OPCODE]
	operBytes = ins[INS_OPER_BYTES]

	if op >= 0:
		bytes.append(op)														# opcode

	if op >= 0 or op == -2 or op == -3:
		for i in range(len(opers)):									# little endian byte list
			op = opers[i]
			if operBytes >= 1:												# $xxxxxxff
				bytes.append(op & 0xff)
			if operBytes >= 2:												# $xxxxffxx
				op >>= 8
				bytes.append(op & 0xff)
			if operBytes >= 4:												# $ffffxxxx
				op >>= 8
				bytes.append(op & 0xff)
				op >>= 8
				bytes.append(op & 0xff)

	if len(line[LINE_BYTES]):											# if there are any bytes -> object file
		oFile.write(srec.srec(line[LINE_ADDRESS], bytes))
		oFile.write("\n")

	return

#
#	Generate line listing
#
def listLine(line):

	opers = line[LINE_OPERS]
	bytes = line[LINE_BYTES]
	operBytes = line[LINE_INS][INS_OPER_BYTES]

	outo = ""																			# format operands
	for oper in opers:
		of = oper																		# posit register name string
		if isinstance(oper, int):										# ? number
			if	 operBytes == 1: of = "${:02x}".format(oper)
			elif operBytes == 2: of = "${:04x}".format(oper)
			else:								 of = "${:08x}".format(oper)
		outo += ", " + of

	outb = ""																			# format byte list
	for b in bytes:
		outb += "{:02x} ".format(b)

	#	Assembly listing
	#
	print("{:4} {:04x} {:20} {:16} {:10} {}".format(
		line[LINE_NUMBER],
		line[LINE_ADDRESS],
		outb[:20],
		line[LINE_LABEL],
		line[LINE_INSTR],
		outo[1:])
	)

	return

#
# label dictionary output cross reference in alphabetical order
#
def listLabels():

	print()
	for l, v in sorted(labels.items()):
		if isinstance(v, int):
			v="${:04X}".format(v)
		print("{:20} = {:>10}".format(l, v))

	return

#
#	label dictionary output in object file format
#
def writeLabels(oFile):

	for l, v in labels.items():
		if isinstance(v, int):
			oFile.write(srec.srecL(v, l))
			oFile.write("\n")

	return

#
#	read instruction information from microcode.obj labels
#		label.instr			opcode
#		label.obytes		bytes per operand
#
#
def importInstructions(name):

	iCount = 0
	try:
		f = open(name)																# ? .obj file
	except:
		print("\n{} instructions {} file not found".format(name))
		return																				# ------>

	for line in f:
		if line.startswith("S"):											# srec format
			addr, label = srec.parse(line)
		elif line.startswidth(":")	:									# ihex format
			addr, label = ihex.parse(line)

		if not isinstance(label ,str):								# ? label
			continue																		# <-------

		if label.endswith(".instr"):									# labels created by mch in runDirectives
			instr = addr
		elif label.endswith(".obytes"):
			instructions.update({label[0:-7]: [instr, addr]})
			iCount += 1

	f.close()

	print("\n{} instructions loaded from {}".format(iCount, name))

	return


#
#
#
file = sys.argv[1]
asmFile(file, 1)																	# pass 1
asmFile(file, 2)																	# pass 2
listLabels()

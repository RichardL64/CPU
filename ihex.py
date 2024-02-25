"""

Intel Hex file support
https://en.wikipedia.org/wiki/Intel_HEX

R.Lincoln			February 2024

"""


#
#	Return type 0/6 address/bytes list record
#
def ihex(addr, bytes, type = 0):

	if not isinstance(addr, int): return ""				# ? numeric address
	if addr > 0xffff: return ""										# ? 32 bit address

	n = len(bytes)
	if n > 0xff: return ""												# ? to long

	a = "{:04x}".format(addr)											# posit 16 bit address
	ac = (addr & 255) + (addr >> 8 & 255)					# checksum

	b = "".join("{:02x}".format(x) for x in bytes)

	c = n + ac + type + sum(bytes) & 0xff
	c = (c ^ 255) +1															# 2's complement?  TBC

	return	":{:02x}{}{:02x}{}{:02x}".format(n, a, type, b, c)


#
#	Return non standard address/label record
#
def ihexL(addr, label):

	bytes = [ord(c) for c in list(label)]					# string to list of character byte values
	rec = ihex(addr, bytes, 10)

	return rec


#
#	Return type 1 EOF record
#
def ihexEOF():

	return ":00000001FF"


#
#	Return an address and list of bytes or label from an srec
#	addr, [byte,...]
#
def parse(line):

	num = int(line[1:3], 16) *2
	addr = int(line[3:7], 16)
	type = int(line[7:9], 16)
	b1 = 9																				# first data byte

	bytes = []
	for i in range(b1, b1 + num, 2):							# hex char pairs
		bytes.append(int(line[i:i +2], 16))					# to decimal bytes

	if type == 10:																# types from ihexL, return as a label name
		bytes = "".join(chr(x) for x in bytes)

	return addr, bytes

"""

SREC file support
https://en.wikipedia.org/wiki/SREC_(file_format)

R.Lincoln			February 2024

"""


#
#	Return S1/S3/S4/S6 address/bytes list record
# Automatically generate an S3/S6 32 bit address record as required
# S4/S6 records same layout as S1/S3 but return the byte array as a text label
#
def srec(addr, bytes, type = 1):

	if not isinstance(addr, int): return ""				# ? numeric address

	a = "{:04x}".format(addr)											# posit 16 bit address
	ac = (addr & 255) + (addr >> 8 & 255)					# checksum
	n = len(bytes) +3															# record length

	if addr > 0xffff:															# ? 32 bit address
		type += 2
		a = "{:08x}".format(addr)
		ac += (addr >> 16 & 255) + (addr >> 24 & 255)
		n += 2

	if n > 0xff: return ""												# ? too long

	b = "".join("{:02x}".format(x) for x in bytes)
	c = 0xff - (n + ac + sum(bytes) & 0xff)

	rec = "S{}{:02x}{}{}{:02x}".format(type, n, a, b, c)

	return rec


#
#	Return S4/6 non standard address/label record
#
def srecL(addr, label):

	bytes = [ord(x) for x in list(label)]					# string to list of character byte values
	rec = srec(addr, bytes, 4)

	return rec


#
#	Return an address and list of bytes or label from an srec
#	addr, [byte,...]
#
def parse(line):

	type = int(line[1:2], 16)
	if type == 1 or type == 4:										# ? 16 bit address
		num = (int(line[2:4], 16) -3) *2
		addr = int(line[4:8], 16)
		b1 = 8																			# first data byte

	elif type == 3 or type == 6:									# ? 32 bit address
		num = (int(line[2:4], 16) -5) *2
		addr = int(line[4:12], 16)
		b1 = 12																			# first date byte

	bytes = []
	for i in range(b1, b1 + num, 2):							# hex char pairs
		bytes.append(int(line[i:i +2], 16))					# to decimal bytes

	if type == 4 or type == 6:										# type 4 from srecL, return as a label name
		bytes = "".join(chr(x) for x in bytes)

	return addr, bytes

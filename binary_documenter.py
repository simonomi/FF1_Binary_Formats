from io import BytesIO
from sys import argv

class Box:
	CORNER_TL = "╭"
	CORNER_TR = "╮"
	CORNER_BL = "╰"
	CORNER_BR = "╯"
	EDGE_H = "─"
	EDGE_V = "│"
	T_T = "┬"
	T_L = "├"
	T_R = "┤"
	T_B = "┴"
	CROSS = "┼"
	END = "╴"

# dear future simon: if you ever have to come back and debug this, good luck
def create_table(indexes, table, trailing_chunks):
	column_widths = []
	for column in range(len(table[0])):
		column_widths.append(max([len(x[column]) for x in table]))
	
	trailing_chunk_widths = []
	for chunk in trailing_chunks:
		trailing_chunk_widths.append(len(chunk))
	
	horizontal_divider = []
	for column_width in column_widths:
		horizontal_divider.append(Box.EDGE_H * (column_width + 2))
	horizontal_divider = Box.CROSS.join(horizontal_divider)
	
	tailing_chunk_divider = [""]
	for chunk_width in trailing_chunk_widths:
		tailing_chunk_divider.append(Box.EDGE_H * (chunk_width + 2))
	top_chunk_divider = Box.T_T.join(tailing_chunk_divider)
	bottom_chunk_divider = Box.T_B.join(tailing_chunk_divider)
	
	if len(indexes) >= len(table[0]):
		top_chunk_divider = Box.CROSS + top_chunk_divider[1:]
	
	tailing_chunk_divider = []
	for chunk_width in trailing_chunk_widths:
		tailing_chunk_divider.append(" " * (chunk_width + 2))
	tailing_chunk_divider.append("")
	middle_chunk_divider = Box.EDGE_V.join(tailing_chunk_divider)
	
	output = ""
	
	header = "   "
	for index, width in zip(indexes, column_widths):
		header += " " * (width - 1)
		header += index
	output += header + "\n"
	
	output += Box.CORNER_TL + horizontal_divider + top_chunk_divider + Box.CORNER_TR + "\n"
	
	row_divider = "\n" + Box.T_L + horizontal_divider + Box.T_R + middle_chunk_divider + "\n"
	
	rows = []
	for index, row in enumerate(table):
		line = []
		for label, width in zip(row, column_widths):
			line.append(f"{Box.EDGE_V} {label.ljust(width)} ")
		
		for chunk, width in zip(trailing_chunks, trailing_chunk_widths):
			if index == 1:
				line.append(f"{Box.EDGE_V} {chunk.ljust(width)} ")
			else:
				line.append(f"{Box.EDGE_V} {''.ljust(width)} ")
		
		rows.append("".join(line) + Box.EDGE_V)
	output += row_divider.join(rows)
	
	output += "\n" + Box.CORNER_BL + horizontal_divider + bottom_chunk_divider + Box.CORNER_BR + "\n"
	
	column_widths.pop()
	while column_widths:
		label_line = " "
		for width in column_widths:
			label_line += " " * (width + 2) + Box.EDGE_V
		label_line = label_line[:-1]
		label_line += Box.CORNER_BL + Box.END
		output += label_line + "\n"
		
		column_widths.pop()
	
	return output

def inte(_bytes):
	return int.from_bytes(_bytes, "little")

def swap_endianness(hex):
	hex = hex.replace(" ", "")
	
	if len(hex) == 2:
		return hex
	if len(hex) == 4:
		return hex[2:] + hex[:2]
	else:
		assert(len(hex) % 8 == 0)
		
		output = ""
		for i in range(0, len(hex), 8):
			output += hex[i + 6:i + 8]
			output += hex[i + 4:i + 6]
			output += hex[i + 2:i + 4]
			output += hex[i + 0:i + 2]
		
		return output

def insert_spaces(string):
	return " ".join([string[i:i + 2] for i in range(0, len(string), 2)])

if len(argv) < 3:
	print("usage:   binary_documentor.py <little endian input> <breaks> [trailing chunks]")
	print('example: binary_documentor.py "0052414D 0000051C"   "0 4 8"  "MCM File Lists", "MCM Files"')
	exit()
else:
	input_little_e = argv[1]
	input_breaks = argv[2].split()
	trailing_chunks = argv[3:]

input_bytes = bytes.fromhex(swap_endianness(input_little_e))
input_breaks = [int(x, 16) for x in input_breaks]

if 0 not in [x % 0x20 for x in input_breaks]:
	input_breaks.insert(0, 0)

breaks = []
for offset in input_breaks:
	breaks.append(offset - sum(breaks))

chunks = []
with BytesIO(input_bytes) as stream:
	while breaks:
		chunks.append(stream.read(breaks.pop(0) % 0x10))
	chunks.append(stream.read())
chunks = [x for x in chunks if x]

indexes = [f"0x{x:02X}" for x in input_breaks]

table = [
	["Raw"], 
	["Little-endian"], 
	["Formatted"],
	["utf-8"]
]
table[0] += [insert_spaces(x.hex().upper()) for x in chunks]
table[1] += [swap_endianness(x.hex()).upper() for x in chunks]
table[2] += [f"{inte(x):,}" for x in chunks]
for chunk in chunks:
	try:
		label = chunk.decode().replace("\x00", "")
		if not label.isprintable():
			label = ""
		
		table[3].append('"' + label + '"')
	except UnicodeDecodeError:
		table[3].append('""')

trailing_chunks = [x + "..." for x in trailing_chunks]

print(create_table(indexes, table, trailing_chunks))

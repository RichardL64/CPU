# CPU
Homebrew CPU - assembler etc
Probably forth based, a possible past where 6502 assembly had more support for a stack machine
16 bit


Names
  Histocially always used 'Lo4'    - Lincoln Object Forth
  Recently prefer 'Throf'          - Forth kindof backwards, i.e. like the word defining, lack of syntax, perhaps remove the reverse polish

Status
  Assembler basically working, no friendly error messages - drops to python
  Can sucessfully assemble microcode and the resulting assembler instructions defined by it


Lo4.numbers     OSX Numbers file playing with ISAs instruction set implmentation etc.

asm.py          Assembler instructions driven from microcode assembly
                Generates SREC format object files including some non standard label lines

microcode.asm   Example microcode file defining the control word and instructions
                Assembling the microcode produces a .obj file which the assembler can consule

test.asm        Assemlber test file, checking syntax and basic assembler functionality


sim.py          Not working yet - embryonic microcode level simulation

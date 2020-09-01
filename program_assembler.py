#!/usr/bin/env python

# Copyright (C) 2020 Caian Benedicto <caianbene@gmail.com>
#
# This software is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

##########################################

alu_ops = {
    "OR" : 0b10010000,
    "AND": 0b10100000,
    "XOR": 0b10110000,
    "ADD": 0b11000000,
    "LSH": 0b11010000,
    "RSH": 0b11100000,
    "NOT": 0b11110000,
}

mem_ops = {
    "SLO": 0b00000000,
    "SHI": 0b01000000,
}

prt_ops = {
    "PTR": 0b10000000,
}

jmp_ops = {
    "SKP": 0b10000001,
    "JMP": 0b10000010,
}

##########################################

tags = {}
program = []
retry = []

##########################################

def mktag(tag):
    if tag is None:
        return
    tags[tag] = len(program)

def mkinstr(instr):
    instr = instr[2:]
    instr = '0' * (2 - len(instr)) + instr
    program.append(instr)

def mkretry(funct, *args):
    pos = len(program)
    def wrapper():
        original = program.copy()
        program.clear()
        funct(*args)
        original[pos:pos+len(program)] = program
        program.clear()
        for i in original:
            program.append(i)
    retry.append(wrapper)

def mkaop(op, rd, rr, tag=None):
    mktag(tag)
    mkinstr(hex(alu_ops[op] | (rd << 2) | rr))

def mkllmop(r, v, tag=None):
    mktag(tag)
    mkinstr(hex(mem_ops["SLO"] | (r << 4) | (v & 0xF)))

def mklmop(r, v, tag=None):
    mktag(tag)
    if type(v) == str and len(v) == 1:
        return mklmop(r, ord(v[0]))
    mkllmop(r, v)

def mkhhmop(r, v, tag=None):
    mktag(tag)
    mkinstr(hex(mem_ops["SHI"] | (r << 4) | (v & 0xF)))

def mkhmop(r, v, tag=None):
    mktag(tag)
    if type(v) == str and len(v) == 1:
        return mkhmop(r, ord(v[0]))
    mkhhmop(r, v >> 4)

def mkmop(r, v, tag=None):
    mktag(tag)
    mklmop(r, v)
    mkhmop(r, v)

def mkpop(r, tag=None):
    mktag(tag)
    mkinstr(hex(prt_ops["PTR"] | (r << 2)))

def mkjmp(r, tag=None):
    mktag(tag)
    mkinstr(hex(jmp_ops["JMP"] | (r << 2)))

def mkjmpdest(r, jtag, tag=None):
    mktag(tag)
    addr = tags.get(jtag, None)
    if addr is None:
        addr = 255
        mkretry(mkjmpdest, r, jtag)
    mklmop(r, addr)
    mkhmop(r, addr)

def mkskp(r, tag=None):
    mktag(tag)
    mkinstr(hex(jmp_ops["SKP"] | (r << 2)))

##########################################

mkmop(3, 4)
mkmop(0, 0b0111)
mkaop('LSH', 0, 3)
mkmop(2, 0b11100000)
mkaop('AND', 0, 2)
mkaop('NOT', 1, 0)
mkaop('OR', 1, 0)
mkmop(2, 1)
mkaop('RSH', 1, 2)

mkmop(3, 254, 'BEGIN')

mkllmop(0, 0b1110, 'LOOP')
mkpop(0)
mkllmop(0, 0b1111)
mkpop(0)
mkllmop(0, 0b1011)
mkpop(0)
mkllmop(1, 0b0101)
mkpop(1)
mkllmop(0, 0b0100)
mkpop(0)
mkllmop(0, 0b1111)
mkpop(0)
mkaop('XOR', 2, 2)
mkhhmop(2, 0b0010)
mkpop(2)
mkllmop(0, 0b0011)
mkpop(0)
mkllmop(1, 0b0101)
mkpop(1)
mkllmop(1, 0b0010)
mkpop(1)
mkllmop(0, 0b1001)
mkpop(0)
mkllmop(0, 0b1111)
mkpop(0)
mkllmop(1, 0b0011)
mkpop(1)
mkllmop(0, 0b1111)
mkpop(0)

mkmop(2, 1)
mkaop('ADD', 3, 2)

mkjmpdest(2, 'END')
mkskp(3)
mkjmp(2)

mkmop(2, ' ')
mkpop(2)

mkjmpdest(2, 'LOOP')
mkjmp(2)

mkmop(2, '\n', 'END')
mkpop(2)

mkjmpdest(2, 'BEGIN')
mkjmp(2)

retry_copy = retry.copy()
retry.clear()

for r in retry_copy:
    r()

print('Program size: %d bytes' % len(program))
print('Program:')

n = 7
for i in range(0, len(program), n):
    instructions = program[i:i+n]
    print(' '.join(instructions))

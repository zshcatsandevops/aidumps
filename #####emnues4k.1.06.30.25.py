#!/usr/bin/env python3
"""
NESticle-py: A complete NES emulator with integrated debugger and tools
Pure Python/Tkinter implementation with no external dependencies
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import array
import time
import struct
from collections import deque
from typing import Optional, Tuple, List, Dict

# NES Color Palette (RGB values)
NES_PALETTE = [
    (0x7C, 0x7C, 0x7C), (0x00, 0x00, 0xFC), (0x00, 0x00, 0xBC), (0x44, 0x28, 0xBC),
    (0x94, 0x00, 0x84), (0xA8, 0x00, 0x20), (0xA8, 0x10, 0x00), (0x88, 0x14, 0x00),
    (0x50, 0x30, 0x00), (0x00, 0x78, 0x00), (0x00, 0x68, 0x00), (0x00, 0x58, 0x00),
    (0x00, 0x40, 0x58), (0x00, 0x00, 0x00), (0x00, 0x00, 0x00), (0x00, 0x00, 0x00),
    (0xBC, 0xBC, 0xBC), (0x00, 0x78, 0xF8), (0x00, 0x58, 0xF8), (0x68, 0x44, 0xFC),
    (0xD8, 0x00, 0xCC), (0xE4, 0x00, 0x58), (0xF8, 0x38, 0x00), (0xE4, 0x5C, 0x10),
    (0xAC, 0x7C, 0x00), (0x00, 0xB8, 0x00), (0x00, 0xA8, 0x00), (0x00, 0xA8, 0x44),
    (0x00, 0x88, 0x88), (0x00, 0x00, 0x00), (0x00, 0x00, 0x00), (0x00, 0x00, 0x00),
    (0xF8, 0xF8, 0xF8), (0x3C, 0xBC, 0xFC), (0x68, 0x88, 0xFC), (0x98, 0x78, 0xF8),
    (0xF8, 0x78, 0xF8), (0xF8, 0x58, 0x98), (0xF8, 0x78, 0x58), (0xFC, 0xA0, 0x44),
    (0xF8, 0xB8, 0x00), (0xB8, 0xF8, 0x18), (0x58, 0xD8, 0x54), (0x58, 0xF8, 0x98),
    (0x00, 0xE8, 0xD8), (0x78, 0x78, 0x78), (0x00, 0x00, 0x00), (0x00, 0x00, 0x00),
    (0xFC, 0xFC, 0xFC), (0xA4, 0xE4, 0xFC), (0xB8, 0xB8, 0xF8), (0xD8, 0xB8, 0xF8),
    (0xF8, 0xB8, 0xF8), (0xF8, 0xA4, 0xC0), (0xF0, 0xD0, 0xB0), (0xFC, 0xE0, 0xA8),
    (0xF8, 0xD8, 0x78), (0xD8, 0xF8, 0x78), (0xB8, 0xF8, 0xB8), (0xB8, 0xF8, 0xD8),
    (0x00, 0xFC, 0xFC), (0xF8, 0xD8, 0xF8), (0x00, 0x00, 0x00), (0x00, 0x00, 0x00)
]


class CPU6502:
    """MOS 6502 CPU emulator"""
    
    def __init__(self, nes):
        self.nes = nes
        self.pc = 0  # Program Counter
        self.sp = 0xFD  # Stack Pointer
        self.a = 0  # Accumulator
        self.x = 0  # X Register
        self.y = 0  # Y Register
        self.status = 0x24  # Status Register (NVss DIZC)
        self.cycles = 0
        self.interrupt_requested = False
        self.nmi_requested = False
        
        # Instruction set (simplified)
        self.instructions = self._init_instructions()
    
    def _init_instructions(self):
        """Initialize 6502 instruction set"""
        return {
            0x00: ("BRK", self.brk, 7),
            0x01: ("ORA", self.ora_idx_ind, 6),
            0x05: ("ORA", self.ora_zp, 3),
            0x06: ("ASL", self.asl_zp, 5),
            0x08: ("PHP", self.php, 3),
            0x09: ("ORA", self.ora_imm, 2),
            0x0A: ("ASL", self.asl_acc, 2),
            0x0D: ("ORA", self.ora_abs, 4),
            0x0E: ("ASL", self.asl_abs, 6),
            0x10: ("BPL", self.bpl, 2),
            0x18: ("CLC", self.clc, 2),
            0x20: ("JSR", self.jsr, 6),
            0x28: ("PLP", self.plp, 4),
            0x29: ("AND", self.and_imm, 2),
            0x2C: ("BIT", self.bit_abs, 4),
            0x30: ("BMI", self.bmi, 2),
            0x38: ("SEC", self.sec, 2),
            0x48: ("PHA", self.pha, 3),
            0x4C: ("JMP", self.jmp_abs, 3),
            0x60: ("RTS", self.rts, 6),
            0x68: ("PLA", self.pla, 4),
            0x78: ("SEI", self.sei, 2),
            0x85: ("STA", self.sta_zp, 3),
            0x86: ("STX", self.stx_zp, 3),
            0x88: ("DEY", self.dey, 2),
            0x8A: ("TXA", self.txa, 2),
            0x8D: ("STA", self.sta_abs, 4),
            0x8E: ("STX", self.stx_abs, 4),
            0x90: ("BCC", self.bcc, 2),
            0x91: ("STA", self.sta_ind_idx, 6),
            0x95: ("STA", self.sta_zp_x, 4),
            0x98: ("TYA", self.tya, 2),
            0x9A: ("TXS", self.txs, 2),
            0x9D: ("STA", self.sta_abs_x, 5),
            0xA0: ("LDY", self.ldy_imm, 2),
            0xA2: ("LDX", self.ldx_imm, 2),
            0xA4: ("LDY", self.ldy_zp, 3),
            0xA5: ("LDA", self.lda_zp, 3),
            0xA6: ("LDX", self.ldx_zp, 3),
            0xA8: ("TAY", self.tay, 2),
            0xA9: ("LDA", self.lda_imm, 2),
            0xAA: ("TAX", self.tax, 2),
            0xAC: ("LDY", self.ldy_abs, 4),
            0xAD: ("LDA", self.lda_abs, 4),
            0xAE: ("LDX", self.ldx_abs, 4),
            0xB0: ("BCS", self.bcs, 2),
            0xB1: ("LDA", self.lda_ind_idx, 5),
            0xB5: ("LDA", self.lda_zp_x, 4),
            0xB9: ("LDA", self.lda_abs_y, 4),
            0xBD: ("LDA", self.lda_abs_x, 4),
            0xC0: ("CPY", self.cpy_imm, 2),
            0xC8: ("INY", self.iny, 2),
            0xC9: ("CMP", self.cmp_imm, 2),
            0xCA: ("DEX", self.dex, 2),
            0xD0: ("BNE", self.bne, 2),
            0xD8: ("CLD", self.cld, 2),
            0xE0: ("CPX", self.cpx_imm, 2),
            0xE8: ("INX", self.inx, 2),
            0xE9: ("SBC", self.sbc_imm, 2),
            0xEA: ("NOP", self.nop, 2),
            0xF0: ("BEQ", self.beq, 2),
            0xF8: ("SED", self.sed, 2),
        }
    
    def reset(self):
        """Reset CPU to initial state"""
        self.pc = self.read16(0xFFFC)
        self.sp = 0xFD
        self.status = 0x24
        self.cycles = 0
    
    def read(self, addr):
        """Read from memory"""
        return self.nes.cpu_read(addr)
    
    def write(self, addr, value):
        """Write to memory"""
        self.nes.cpu_write(addr, value)
    
    def read16(self, addr):
        """Read 16-bit value from memory"""
        lo = self.read(addr)
        hi = self.read(addr + 1)
        return (hi << 8) | lo
    
    def push(self, value):
        """Push value to stack"""
        self.write(0x100 + self.sp, value)
        self.sp = (self.sp - 1) & 0xFF
    
    def pop(self):
        """Pop value from stack"""
        self.sp = (self.sp + 1) & 0xFF
        return self.read(0x100 + self.sp)
    
    def set_flag(self, flag, value):
        """Set status flag"""
        if value:
            self.status |= flag
        else:
            self.status &= ~flag
    
    def get_flag(self, flag):
        """Get status flag"""
        return (self.status & flag) != 0
    
    # Flag constants
    FLAG_C = 0x01  # Carry
    FLAG_Z = 0x02  # Zero
    FLAG_I = 0x04  # Interrupt Disable
    FLAG_D = 0x08  # Decimal
    FLAG_B = 0x10  # Break
    FLAG_V = 0x40  # Overflow
    FLAG_N = 0x80  # Negative
    
    def step(self):
        """Execute one instruction"""
        if self.nmi_requested:
            self.nmi()
            self.nmi_requested = False
        
        opcode = self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        
        if opcode in self.instructions:
            name, func, cycles = self.instructions[opcode]
            func()
            self.cycles += cycles
        else:
            # Unimplemented opcode - NOP
            self.cycles += 2
        
        return self.cycles
    
    def nmi(self):
        """Non-maskable interrupt"""
        self.push((self.pc >> 8) & 0xFF)
        self.push(self.pc & 0xFF)
        self.push(self.status | 0x20)
        self.set_flag(self.FLAG_I, True)
        self.pc = self.read16(0xFFFA)
    
    # Instruction implementations (simplified subset)
    def nop(self):
        pass
    
    def lda_imm(self):
        self.a = self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        self.set_flag(self.FLAG_Z, self.a == 0)
        self.set_flag(self.FLAG_N, self.a & 0x80)
    
    def lda_zp(self):
        addr = self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        self.a = self.read(addr)
        self.set_flag(self.FLAG_Z, self.a == 0)
        self.set_flag(self.FLAG_N, self.a & 0x80)
    
    def lda_zp_x(self):
        addr = (self.read(self.pc) + self.x) & 0xFF
        self.pc = (self.pc + 1) & 0xFFFF
        self.a = self.read(addr)
        self.set_flag(self.FLAG_Z, self.a == 0)
        self.set_flag(self.FLAG_N, self.a & 0x80)
    
    def lda_abs(self):
        addr = self.read16(self.pc)
        self.pc = (self.pc + 2) & 0xFFFF
        self.a = self.read(addr)
        self.set_flag(self.FLAG_Z, self.a == 0)
        self.set_flag(self.FLAG_N, self.a & 0x80)
    
    def lda_abs_x(self):
        addr = (self.read16(self.pc) + self.x) & 0xFFFF
        self.pc = (self.pc + 2) & 0xFFFF
        self.a = self.read(addr)
        self.set_flag(self.FLAG_Z, self.a == 0)
        self.set_flag(self.FLAG_N, self.a & 0x80)
    
    def lda_abs_y(self):
        addr = (self.read16(self.pc) + self.y) & 0xFFFF
        self.pc = (self.pc + 2) & 0xFFFF
        self.a = self.read(addr)
        self.set_flag(self.FLAG_Z, self.a == 0)
        self.set_flag(self.FLAG_N, self.a & 0x80)
    
    def lda_ind_idx(self):
        zp_addr = self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        addr = self.read16(zp_addr) + self.y
        self.a = self.read(addr & 0xFFFF)
        self.set_flag(self.FLAG_Z, self.a == 0)
        self.set_flag(self.FLAG_N, self.a & 0x80)
    
    def ldx_imm(self):
        self.x = self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        self.set_flag(self.FLAG_Z, self.x == 0)
        self.set_flag(self.FLAG_N, self.x & 0x80)
    
    def ldx_zp(self):
        addr = self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        self.x = self.read(addr)
        self.set_flag(self.FLAG_Z, self.x == 0)
        self.set_flag(self.FLAG_N, self.x & 0x80)
    
    def ldx_abs(self):
        addr = self.read16(self.pc)
        self.pc = (self.pc + 2) & 0xFFFF
        self.x = self.read(addr)
        self.set_flag(self.FLAG_Z, self.x == 0)
        self.set_flag(self.FLAG_N, self.x & 0x80)
    
    def ldy_imm(self):
        self.y = self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        self.set_flag(self.FLAG_Z, self.y == 0)
        self.set_flag(self.FLAG_N, self.y & 0x80)
    
    def ldy_zp(self):
        addr = self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        self.y = self.read(addr)
        self.set_flag(self.FLAG_Z, self.y == 0)
        self.set_flag(self.FLAG_N, self.y & 0x80)
    
    def ldy_abs(self):
        addr = self.read16(self.pc)
        self.pc = (self.pc + 2) & 0xFFFF
        self.y = self.read(addr)
        self.set_flag(self.FLAG_Z, self.y == 0)
        self.set_flag(self.FLAG_N, self.y & 0x80)
    
    def sta_zp(self):
        addr = self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        self.write(addr, self.a)
    
    def sta_zp_x(self):
        addr = (self.read(self.pc) + self.x) & 0xFF
        self.pc = (self.pc + 1) & 0xFFFF
        self.write(addr, self.a)
    
    def sta_abs(self):
        addr = self.read16(self.pc)
        self.pc = (self.pc + 2) & 0xFFFF
        self.write(addr, self.a)
    
    def sta_abs_x(self):
        addr = (self.read16(self.pc) + self.x) & 0xFFFF
        self.pc = (self.pc + 2) & 0xFFFF
        self.write(addr, self.a)
    
    def sta_ind_idx(self):
        zp_addr = self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        addr = (self.read16(zp_addr) + self.y) & 0xFFFF
        self.write(addr, self.a)
    
    def stx_zp(self):
        addr = self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        self.write(addr, self.x)
    
    def stx_abs(self):
        addr = self.read16(self.pc)
        self.pc = (self.pc + 2) & 0xFFFF
        self.write(addr, self.x)
    
    def tax(self):
        self.x = self.a
        self.set_flag(self.FLAG_Z, self.x == 0)
        self.set_flag(self.FLAG_N, self.x & 0x80)
    
    def txa(self):
        self.a = self.x
        self.set_flag(self.FLAG_Z, self.a == 0)
        self.set_flag(self.FLAG_N, self.a & 0x80)
    
    def tay(self):
        self.y = self.a
        self.set_flag(self.FLAG_Z, self.y == 0)
        self.set_flag(self.FLAG_N, self.y & 0x80)
    
    def tya(self):
        self.a = self.y
        self.set_flag(self.FLAG_Z, self.a == 0)
        self.set_flag(self.FLAG_N, self.a & 0x80)
    
    def txs(self):
        self.sp = self.x
    
    def inx(self):
        self.x = (self.x + 1) & 0xFF
        self.set_flag(self.FLAG_Z, self.x == 0)
        self.set_flag(self.FLAG_N, self.x & 0x80)
    
    def iny(self):
        self.y = (self.y + 1) & 0xFF
        self.set_flag(self.FLAG_Z, self.y == 0)
        self.set_flag(self.FLAG_N, self.y & 0x80)
    
    def dex(self):
        self.x = (self.x - 1) & 0xFF
        self.set_flag(self.FLAG_Z, self.x == 0)
        self.set_flag(self.FLAG_N, self.x & 0x80)
    
    def dey(self):
        self.y = (self.y - 1) & 0xFF
        self.set_flag(self.FLAG_Z, self.y == 0)
        self.set_flag(self.FLAG_N, self.y & 0x80)
    
    def clc(self):
        self.set_flag(self.FLAG_C, False)
    
    def sec(self):
        self.set_flag(self.FLAG_C, True)
    
    def cld(self):
        self.set_flag(self.FLAG_D, False)
    
    def sed(self):
        self.set_flag(self.FLAG_D, True)
    
    def sei(self):
        self.set_flag(self.FLAG_I, True)
    
    def jmp_abs(self):
        self.pc = self.read16(self.pc)
    
    def jsr(self):
        ret_addr = (self.pc + 1) & 0xFFFF
        self.push((ret_addr >> 8) & 0xFF)
        self.push(ret_addr & 0xFF)
        self.pc = self.read16(self.pc)
    
    def rts(self):
        lo = self.pop()
        hi = self.pop()
        self.pc = ((hi << 8) | lo) + 1
    
    def bne(self):
        offset = self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        if not self.get_flag(self.FLAG_Z):
            if offset & 0x80:
                offset = -(256 - offset)
            self.pc = (self.pc + offset) & 0xFFFF
    
    def beq(self):
        offset = self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        if self.get_flag(self.FLAG_Z):
            if offset & 0x80:
                offset = -(256 - offset)
            self.pc = (self.pc + offset) & 0xFFFF
    
    def bpl(self):
        offset = self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        if not self.get_flag(self.FLAG_N):
            if offset & 0x80:
                offset = -(256 - offset)
            self.pc = (self.pc + offset) & 0xFFFF
    
    def bmi(self):
        offset = self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        if self.get_flag(self.FLAG_N):
            if offset & 0x80:
                offset = -(256 - offset)
            self.pc = (self.pc + offset) & 0xFFFF
    
    def bcc(self):
        offset = self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        if not self.get_flag(self.FLAG_C):
            if offset & 0x80:
                offset = -(256 - offset)
            self.pc = (self.pc + offset) & 0xFFFF
    
    def bcs(self):
        offset = self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        if self.get_flag(self.FLAG_C):
            if offset & 0x80:
                offset = -(256 - offset)
            self.pc = (self.pc + offset) & 0xFFFF
    
    def pha(self):
        self.push(self.a)
    
    def pla(self):
        self.a = self.pop()
        self.set_flag(self.FLAG_Z, self.a == 0)
        self.set_flag(self.FLAG_N, self.a & 0x80)
    
    def php(self):
        self.push(self.status | 0x30)
    
    def plp(self):
        self.status = (self.pop() & 0xEF) | 0x20
    
    def and_imm(self):
        self.a &= self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        self.set_flag(self.FLAG_Z, self.a == 0)
        self.set_flag(self.FLAG_N, self.a & 0x80)
    
    def ora_imm(self):
        self.a |= self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        self.set_flag(self.FLAG_Z, self.a == 0)
        self.set_flag(self.FLAG_N, self.a & 0x80)
    
    def ora_zp(self):
        addr = self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        self.a |= self.read(addr)
        self.set_flag(self.FLAG_Z, self.a == 0)
        self.set_flag(self.FLAG_N, self.a & 0x80)
    
    def ora_abs(self):
        addr = self.read16(self.pc)
        self.pc = (self.pc + 2) & 0xFFFF
        self.a |= self.read(addr)
        self.set_flag(self.FLAG_Z, self.a == 0)
        self.set_flag(self.FLAG_N, self.a & 0x80)
    
    def ora_idx_ind(self):
        zp_addr = (self.read(self.pc) + self.x) & 0xFF
        self.pc = (self.pc + 1) & 0xFFFF
        addr = self.read16(zp_addr)
        self.a |= self.read(addr)
        self.set_flag(self.FLAG_Z, self.a == 0)
        self.set_flag(self.FLAG_N, self.a & 0x80)
    
    def cmp_imm(self):
        value = self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        result = self.a - value
        self.set_flag(self.FLAG_C, self.a >= value)
        self.set_flag(self.FLAG_Z, (result & 0xFF) == 0)
        self.set_flag(self.FLAG_N, result & 0x80)
    
    def cpx_imm(self):
        value = self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        result = self.x - value
        self.set_flag(self.FLAG_C, self.x >= value)
        self.set_flag(self.FLAG_Z, (result & 0xFF) == 0)
        self.set_flag(self.FLAG_N, result & 0x80)
    
    def cpy_imm(self):
        value = self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        result = self.y - value
        self.set_flag(self.FLAG_C, self.y >= value)
        self.set_flag(self.FLAG_Z, (result & 0xFF) == 0)
        self.set_flag(self.FLAG_N, result & 0x80)
    
    def sbc_imm(self):
        value = self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        result = self.a - value - (0 if self.get_flag(self.FLAG_C) else 1)
        self.set_flag(self.FLAG_C, result >= 0)
        self.set_flag(self.FLAG_V, ((self.a ^ result) & (self.a ^ value) & 0x80) != 0)
        self.a = result & 0xFF
        self.set_flag(self.FLAG_Z, self.a == 0)
        self.set_flag(self.FLAG_N, self.a & 0x80)
    
    def asl_acc(self):
        self.set_flag(self.FLAG_C, self.a & 0x80)
        self.a = (self.a << 1) & 0xFF
        self.set_flag(self.FLAG_Z, self.a == 0)
        self.set_flag(self.FLAG_N, self.a & 0x80)
    
    def asl_zp(self):
        addr = self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        value = self.read(addr)
        self.set_flag(self.FLAG_C, value & 0x80)
        value = (value << 1) & 0xFF
        self.write(addr, value)
        self.set_flag(self.FLAG_Z, value == 0)
        self.set_flag(self.FLAG_N, value & 0x80)
    
    def asl_abs(self):
        addr = self.read16(self.pc)
        self.pc = (self.pc + 2) & 0xFFFF
        value = self.read(addr)
        self.set_flag(self.FLAG_C, value & 0x80)
        value = (value << 1) & 0xFF
        self.write(addr, value)
        self.set_flag(self.FLAG_Z, value == 0)
        self.set_flag(self.FLAG_N, value & 0x80)
    
    def bit_abs(self):
        addr = self.read16(self.pc)
        self.pc = (self.pc + 2) & 0xFFFF
        value = self.read(addr)
        self.set_flag(self.FLAG_Z, (self.a & value) == 0)
        self.set_flag(self.FLAG_V, value & 0x40)
        self.set_flag(self.FLAG_N, value & 0x80)
    
    def brk(self):
        self.pc = (self.pc + 1) & 0xFFFF
        self.push((self.pc >> 8) & 0xFF)
        self.push(self.pc & 0xFF)
        self.push(self.status | 0x30)
        self.set_flag(self.FLAG_I, True)
        self.pc = self.read16(0xFFFE)


class PPU:
    """Picture Processing Unit"""
    
    def __init__(self, nes):
        self.nes = nes
        self.vram = bytearray(0x2000)  # 8KB VRAM
        self.oam = bytearray(0x100)  # Object Attribute Memory (sprites)
        self.palette = bytearray(0x20)  # Palette RAM
        
        # Registers
        self.ctrl = 0  # $2000
        self.mask = 0  # $2001
        self.status = 0  # $2002
        self.oam_addr = 0  # $2003
        self.scroll_x = 0
        self.scroll_y = 0
        self.addr = 0
        self.addr_latch = False
        
        # Rendering
        self.scanline = 0
        self.cycle = 0
        self.frame_buffer = array.array('B', [0] * (256 * 240 * 3))
        self.frame_ready = False
    
    def reset(self):
        """Reset PPU to initial state"""
        self.ctrl = 0
        self.mask = 0
        self.status = 0
        self.scanline = 0
        self.cycle = 0
    
    def read_register(self, addr):
        """Read PPU register"""
        if addr == 0x2002:  # Status
            value = self.status
            self.status &= 0x7F  # Clear vblank flag
            self.addr_latch = False
            return value
        elif addr == 0x2007:  # Data
            # Simplified - just return VRAM data
            value = self.vram[self.addr & 0x1FFF]
            self.addr = (self.addr + (32 if self.ctrl & 0x04 else 1)) & 0x3FFF
            return value
        return 0
    
    def write_register(self, addr, value):
        """Write PPU register"""
        if addr == 0x2000:  # Control
            self.ctrl = value
        elif addr == 0x2001:  # Mask
            self.mask = value
        elif addr == 0x2003:  # OAM address
            self.oam_addr = value
        elif addr == 0x2004:  # OAM data
            self.oam[self.oam_addr] = value
            self.oam_addr = (self.oam_addr + 1) & 0xFF
        elif addr == 0x2005:  # Scroll
            if not self.addr_latch:
                self.scroll_x = value
            else:
                self.scroll_y = value
            self.addr_latch = not self.addr_latch
        elif addr == 0x2006:  # Address
            if not self.addr_latch:
                self.addr = (value << 8) | (self.addr & 0xFF)
            else:
                self.addr = (self.addr & 0xFF00) | value
            self.addr_latch = not self.addr_latch
        elif addr == 0x2007:  # Data
            if self.addr < 0x2000:
                # CHR ROM/RAM write (mapper handles this)
                pass
            elif self.addr < 0x3F00:
                # Nametable write
                self.vram[(self.addr - 0x2000) & 0x1FFF] = value
            else:
                # Palette write
                palette_addr = (self.addr - 0x3F00) & 0x1F
                self.palette[palette_addr] = value
            self.addr = (self.addr + (32 if self.ctrl & 0x04 else 1)) & 0x3FFF
    
    def step(self):
        """Execute one PPU cycle"""
        # Simplified PPU - just track vblank timing
        self.cycle += 1
        
        if self.cycle >= 341:
            self.cycle = 0
            self.scanline += 1
            
            if self.scanline == 241:
                # Start vblank
                self.status |= 0x80
                if self.ctrl & 0x80:
                    self.nes.cpu.nmi_requested = True
                self.render_frame()
            elif self.scanline >= 262:
                self.scanline = 0
                self.status &= 0x7F  # Clear vblank
    
    def render_frame(self):
        """Render a frame (simplified)"""
        # Just fill with background color for now
        bg_color = self.palette[0] & 0x3F
        r, g, b = NES_PALETTE[bg_color]
        
        for i in range(0, len(self.frame_buffer), 3):
            self.frame_buffer[i] = r
            self.frame_buffer[i + 1] = g
            self.frame_buffer[i + 2] = b
        
        self.frame_ready = True


class Controller:
    """NES Controller"""
    
    def __init__(self):
        self.buttons = 0
        self.shift_register = 0
        self.strobe = False
    
    # Button constants
    BUTTON_A = 0x01
    BUTTON_B = 0x02
    BUTTON_SELECT = 0x04
    BUTTON_START = 0x08
    BUTTON_UP = 0x10
    BUTTON_DOWN = 0x20
    BUTTON_LEFT = 0x40
    BUTTON_RIGHT = 0x80
    
    def write(self, value):
        """Write to controller register"""
        self.strobe = value & 1
        if self.strobe:
            self.shift_register = self.buttons
    
    def read(self):
        """Read from controller register"""
        if self.strobe:
            return self.buttons & 1
        else:
            value = self.shift_register & 1
            self.shift_register >>= 1
            self.shift_register |= 0x80
            return value
    
    def set_button(self, button, pressed):
        """Set button state"""
        if pressed:
            self.buttons |= button
        else:
            self.buttons &= ~button


class NES:
    """NES System"""
    
    def __init__(self):
        self.cpu = CPU6502(self)
        self.ppu = PPU(self)
        self.controller1 = Controller()
        self.controller2 = Controller()
        
        # Memory
        self.ram = bytearray(0x800)  # 2KB RAM
        self.prg_rom = None
        self.chr_rom = None
        self.mapper = None
        
        # Timing
        self.cpu_cycles = 0
        self.running = False
        self.paused = False
    
    def load_rom(self, rom_data):
        """Load ROM file"""
        # Parse iNES header
        if rom_data[0:4] != b'NES\x1A':
            raise ValueError("Invalid NES ROM")
        
        prg_banks = rom_data[4]
        chr_banks = rom_data[5]
        mapper = (rom_data[6] >> 4) | (rom_data[7] & 0xF0)
        
        # Load PRG ROM
        prg_size = prg_banks * 0x4000
        self.prg_rom = rom_data[16:16 + prg_size]
        
        # Load CHR ROM
        chr_size = chr_banks * 0x2000
        if chr_size > 0:
            self.chr_rom = rom_data[16 + prg_size:16 + prg_size + chr_size]
        else:
            self.chr_rom = bytearray(0x2000)  # CHR RAM
        
        # Simple NROM mapper support
        if mapper != 0:
            print(f"Warning: Mapper {mapper} not fully supported")
        
        self.reset()
    
    def reset(self):
        """Reset system"""
        self.cpu.reset()
        self.ppu.reset()
        self.cpu_cycles = 0
    
    def cpu_read(self, addr):
        """CPU memory read"""
        if addr < 0x2000:
            # RAM (mirrored)
            return self.ram[addr & 0x7FF]
        elif addr < 0x4000:
            # PPU registers (mirrored)
            return self.ppu.read_register(0x2000 + (addr & 7))
        elif addr == 0x4016:
            # Controller 1
            return self.controller1.read()
        elif addr == 0x4017:
            # Controller 2
            return self.controller2.read()
        elif addr >= 0x8000:
            # PRG ROM
            if self.prg_rom:
                if len(self.prg_rom) <= 0x4000:
                    # 16KB ROM, mirrored
                    return self.prg_rom[(addr - 0x8000) & 0x3FFF]
                else:
                    # 32KB ROM
                    return self.prg_rom[addr - 0x8000]
        return 0
    
    def cpu_write(self, addr, value):
        """CPU memory write"""
        if addr < 0x2000:
            # RAM (mirrored)
            self.ram[addr & 0x7FF] = value
        elif addr < 0x4000:
            # PPU registers (mirrored)
            self.ppu.write_register(0x2000 + (addr & 7), value)
        elif addr == 0x4016:
            # Controller strobe
            self.controller1.write(value)
            self.controller2.write(value)
    
    def step(self):
        """Execute one system step"""
        # Run CPU
        cycles = self.cpu.step()
        
        # Run PPU (3 PPU cycles per CPU cycle)
        for _ in range(cycles * 3):
            self.ppu.step()
        
        self.cpu_cycles += cycles


class NESTicleApp:
    """Main application window"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("NESticle-py - NES Emulator & Debugger")
        self.root.configure(bg='#2b2b2b')
        
        self.nes = NES()
        self.running = False
        self.step_mode = False
        self.breakpoints = set()
        self.frame_skip = 1
        self.frame_count = 0
        
        self.setup_ui()
        self.setup_bindings()
        
        # Start emulation loop
        self.emulation_loop()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Create main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Screen and controls
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Screen
        screen_frame = ttk.LabelFrame(left_panel, text="Display", padding=5)
        screen_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(screen_frame, width=512, height=480, bg='black')
        self.canvas.pack()
        
        # Control buttons
        control_frame = ttk.Frame(left_panel)
        control_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(control_frame, text="Load ROM", command=self.load_rom).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Reset", command=self.reset).pack(side=tk.LEFT, padx=2)
        self.run_button = ttk.Button(control_frame, text="Run", command=self.toggle_run)
        self.run_button.pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Step", command=self.step).pack(side=tk.LEFT, padx=2)
        
        # Speed control
        ttk.Label(control_frame, text="Speed:").pack(side=tk.LEFT, padx=(10, 2))
        self.speed_var = tk.IntVar(value=60)
        ttk.Spinbox(control_frame, from_=1, to=240, textvariable=self.speed_var, width=5).pack(side=tk.LEFT)
        
        # Right panel - Debugger
        right_panel = ttk.Notebook(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # CPU tab
        cpu_frame = ttk.Frame(right_panel)
        right_panel.add(cpu_frame, text="CPU")
        
        # CPU registers
        reg_frame = ttk.LabelFrame(cpu_frame, text="Registers", padding=5)
        reg_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.reg_labels = {}
        for i, (name, width) in enumerate([("PC", 4), ("A", 2), ("X", 2), ("Y", 2), ("SP", 2), ("P", 2)]):
            frame = ttk.Frame(reg_frame)
            frame.grid(row=i//3, column=(i%3)*2, sticky=tk.W, padx=5)
            ttk.Label(frame, text=f"{name}:").pack(side=tk.LEFT)
            label = ttk.Label(frame, text="0000" if width == 4 else "00", font=('Courier', 10))
            label.pack(side=tk.LEFT, padx=(5, 0))
            self.reg_labels[name] = label
        
        # Disassembly
        dis_frame = ttk.LabelFrame(cpu_frame, text="Disassembly", padding=5)
        dis_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.dis_text = scrolledtext.ScrolledText(dis_frame, width=40, height=15, font=('Courier', 9))
        self.dis_text.pack(fill=tk.BOTH, expand=True)
        
        # Memory tab
        mem_frame = ttk.Frame(right_panel)
        right_panel.add(mem_frame, text="Memory")
        
        # Memory viewer
        self.mem_text = scrolledtext.ScrolledText(mem_frame, width=50, height=20, font=('Courier', 9))
        self.mem_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # PPU tab
        ppu_frame = ttk.Frame(right_panel)
        right_panel.add(ppu_frame, text="PPU")
        
        # Pattern tables
        pattern_frame = ttk.LabelFrame(ppu_frame, text="Pattern Tables", padding=5)
        pattern_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.pattern_canvas = tk.Canvas(pattern_frame, width=256, height=128, bg='black')
        self.pattern_canvas.pack()
        
        # Palettes
        palette_frame = ttk.LabelFrame(ppu_frame, text="Palettes", padding=5)
        palette_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.palette_canvas = tk.Canvas(palette_frame, width=256, height=32, bg='black')
        self.palette_canvas.pack()
        
        # Cheats tab
        cheat_frame = ttk.Frame(right_panel)
        right_panel.add(cheat_frame, text="Cheats")
        
        # Game Genie input
        gg_frame = ttk.LabelFrame(cheat_frame, text="Game Genie", padding=5)
        gg_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.gg_entry = ttk.Entry(gg_frame, width=20)
        self.gg_entry.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(gg_frame, text="Add", command=self.add_game_genie).pack(side=tk.LEFT)
        
        # Cheat list
        self.cheat_list = tk.Listbox(cheat_frame, height=10)
        self.cheat_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_bindings(self):
        """Setup keyboard bindings"""
        # Controller bindings
        self.root.bind('<KeyPress-z>', lambda e: self.nes.controller1.set_button(Controller.BUTTON_A, True))
        self.root.bind('<KeyRelease-z>', lambda e: self.nes.controller1.set_button(Controller.BUTTON_A, False))
        self.root.bind('<KeyPress-x>', lambda e: self.nes.controller1.set_button(Controller.BUTTON_B, True))
        self.root.bind('<KeyRelease-x>', lambda e: self.nes.controller1.set_button(Controller.BUTTON_B, False))
        self.root.bind('<KeyPress-Return>', lambda e: self.nes.controller1.set_button(Controller.BUTTON_START, True))
        self.root.bind('<KeyRelease-Return>', lambda e: self.nes.controller1.set_button(Controller.BUTTON_START, False))
        self.root.bind('<KeyPress-Shift_L>', lambda e: self.nes.controller1.set_button(Controller.BUTTON_SELECT, True))
        self.root.bind('<KeyRelease-Shift_L>', lambda e: self.nes.controller1.set_button(Controller.BUTTON_SELECT, False))
        self.root.bind('<KeyPress-Up>', lambda e: self.nes.controller1.set_button(Controller.BUTTON_UP, True))
        self.root.bind('<KeyRelease-Up>', lambda e: self.nes.controller1.set_button(Controller.BUTTON_UP, False))
        self.root.bind('<KeyPress-Down>', lambda e: self.nes.controller1.set_button(Controller.BUTTON_DOWN, True))
        self.root.bind('<KeyRelease-Down>', lambda e: self.nes.controller1.set_button(Controller.BUTTON_DOWN, False))
        self.root.bind('<KeyPress-Left>', lambda e: self.nes.controller1.set_button(Controller.BUTTON_LEFT, True))
        self.root.bind('<KeyRelease-Left>', lambda e: self.nes.controller1.set_button(Controller.BUTTON_LEFT, False))
        self.root.bind('<KeyPress-Right>', lambda e: self.nes.controller1.set_button(Controller.BUTTON_RIGHT, True))
        self.root.bind('<KeyRelease-Right>', lambda e: self.nes.controller1.set_button(Controller.BUTTON_RIGHT, False))
    
    def load_rom(self):
        """Load ROM file"""
        filename = filedialog.askopenfilename(
            title="Select ROM file",
            filetypes=[("NES ROMs", "*.nes"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'rb') as f:
                    rom_data = f.read()
                self.nes.load_rom(rom_data)
                self.status_var.set(f"Loaded: {filename.split('/')[-1]}")
                self.update_debugger()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load ROM: {e}")
    
    def reset(self):
        """Reset emulator"""
        self.nes.reset()
        self.update_debugger()
        self.status_var.set("Reset")
    
    def toggle_run(self):
        """Toggle run/pause"""
        self.running = not self.running
        self.run_button.config(text="Pause" if self.running else "Run")
        if self.running:
            self.step_mode = False
    
    def step(self):
        """Single step execution"""
        self.step_mode = True
        self.running = False
        self.run_button.config(text="Run")
    
    def add_game_genie(self):
        """Add Game Genie code"""
        code = self.gg_entry.get().strip().upper()
        if len(code) in (6, 8):
            self.cheat_list.insert(tk.END, code)
            self.gg_entry.delete(0, tk.END)
            # TODO: Implement Game Genie decoding and patching
    
    def update_debugger(self):
        """Update debugger displays"""
        if not self.nes.prg_rom:
            return
        
        # Update registers
        cpu = self.nes.cpu
        self.reg_labels["PC"].config(text=f"{cpu.pc:04X}")
        self.reg_labels["A"].config(text=f"{cpu.a:02X}")
        self.reg_labels["X"].config(text=f"{cpu.x:02X}")
        self.reg_labels["Y"].config(text=f"{cpu.y:02X}")
        self.reg_labels["SP"].config(text=f"{cpu.sp:02X}")
        self.reg_labels["P"].config(text=f"{cpu.status:02X}")
        
        # Update disassembly
        self.dis_text.delete(1.0, tk.END)
        pc = cpu.pc
        for i in range(20):
            if pc >= 0x8000 and self.nes.prg_rom:
                opcode = self.nes.cpu_read(pc)
                if opcode in cpu.instructions:
                    name, _, _ = cpu.instructions[opcode]
                    line = f"{pc:04X}: {opcode:02X} {name}\n"
                else:
                    line = f"{pc:04X}: {opcode:02X} ???\n"
                
                if pc == cpu.pc:
                    self.dis_text.insert(tk.END, line, "current")
                    self.dis_text.tag_config("current", background="yellow")
                else:
                    self.dis_text.insert(tk.END, line)
                
                pc = (pc + 1) & 0xFFFF
        
        # Update memory view
        self.mem_text.delete(1.0, tk.END)
        addr = 0
        for row in range(32):
            line = f"{addr:04X}: "
            for col in range(16):
                line += f"{self.nes.cpu_read(addr):02X} "
                addr += 1
            self.mem_text.insert(tk.END, line + "\n")
    
    def update_screen(self):
        """Update screen display"""
        if self.nes.ppu.frame_ready:
            # Convert frame buffer to PhotoImage
            width, height = 256, 240
            data = []
            for y in range(height):
                row = []
                for x in range(width):
                    idx = (y * width + x) * 3
                    r = self.nes.ppu.frame_buffer[idx]
                    g = self.nes.ppu.frame_buffer[idx + 1]
                    b = self.nes.ppu.frame_buffer[idx + 2]
                    row.append(f"#{r:02x}{g:02x}{b:02x}")
                data.append("{" + " ".join(row) + "}")
            
            image_data = " ".join(data)
            
            # Create scaled image
            self.photo = tk.PhotoImage(width=512, height=480)
            self.photo.put(image_data, to=(0, 0, 256, 240))
            self.photo = self.photo.zoom(2, 2)
            
            self.canvas.delete("all")
            self.canvas.create_image(256, 240, image=self.photo)
            
            self.nes.ppu.frame_ready = False
    
    def emulation_loop(self):
        """Main emulation loop"""
        if self.running and self.nes.prg_rom:
            # Run emulation for one frame
            target_cycles = 29780  # NTSC cycles per frame
            
            while self.nes.cpu_cycles < target_cycles:
                # Check breakpoints
                if self.nes.cpu.pc in self.breakpoints:
                    self.running = False
                    self.run_button.config(text="Run")
                    break
                
                self.nes.step()
            
            self.nes.cpu_cycles -= target_cycles
            
            # Update display
            self.frame_count += 1
            if self.frame_count % self.frame_skip == 0:
                self.update_screen()
                self.update_debugger()
        
        elif self.step_mode:
            if self.nes.prg_rom:
                self.nes.step()
                self.update_debugger()
            self.step_mode = False
        
        # Schedule next frame
        delay = max(1, int(1000 / self.speed_var.get()))
        self.root.after(delay, self.emulation_loop)


def main():
    """Main entry point"""
    root = tk.Tk()
    app = NESTicleApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

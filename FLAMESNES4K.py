import tkinter as tk
from tkinter import filedialog, messagebox
import os
import pygame
import sys
import pickle
import zlib
import numpy as np
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageTk
from functools import lru_cache

# NES Constants
SCREEN_WIDTH = 256
SCREEN_HEIGHT = 240
NES_PPU_ADDRESS = 0x2000
NES_RAM_SIZE = 0x0800  # 2KB internal RAM
NES_PRG_ROM_OFFSET = 0x8000

class MOS6502:
    """Simulates the MOS 6502 CPU used in the NES."""
    def __init__(self):
        self.a = 0  # Accumulator
        self.x = 0  # X Register
        self.y = 0  # Y Register
        self.pc = 0  # Program Counter
        self.sp = 0xFD  # Stack Pointer
        self.status = 0x24  # Status flags (NV-BDIZC)
        self.memory = bytearray(0x10000)  # 64KB address space
        self.cycles = 0
        self.sram = bytearray(0x2000)  # 8KB SRAM
        self.interrupt = None  # NMI, IRQ, or None
        self.mapper = None
        self.ppu = None
        self.controller = None

    def load_program(self, rom_data):
        """Load the NES ROM into memory with mapper support."""
        try:
            header = rom_data[:16]
            if header[:4] != b'NES\x1A':
                raise ValueError("Invalid NES file format.")
            prg_rom_size = header[4] * 0x4000  # 16KB units
            chr_rom_size = header[5] * 0x2000  # 8KB units
            self.mirroring = header[6] & 0x01  # 0: Horizontal, 1: Vertical
            self.battery = header[6] & 0x02
            mapper_id = (header[6] >> 4) | (header[7] & 0xF0)

            prg_offset = 16
            self.prg_data = rom_data[prg_offset:prg_offset + prg_rom_size]
            chr_offset = prg_offset + prg_rom_size
            self.chr_data = rom_data[chr_offset:chr_offset + chr_rom_size] if chr_rom_size else bytearray(0x2000)

            self.mapper = Mapper.create(mapper_id, self.prg_data, self.chr_data, self.battery)
            self.mapper.load(self.memory, self.sram)
            self.pc = self.read_word(0xFFFC)
            print(f"Loaded ROM, Mapper {mapper_id}, PC set to 0x{self.pc:04X}")
        except Exception as e:
            raise ValueError(f"Failed to parse ROM: {str(e)}")

    def reset(self):
        """Reset CPU state."""
        self.a = 0
        self.x = 0
        self.y = 0
        self.sp = 0xFD
        self.status = 0x24
        self.pc = self.read_word(0xFFFC)
        self.cycles = 0
        self.interrupt = None

    def read_byte(self, addr):
        addr &= 0xFFFF
        if addr < 0x2000:
            return self.memory[addr & 0x07FF]
        elif addr < 0x4000:
            return self.ppu.read_register(addr)
        elif addr == 0x4016:
            return self.controller.read()
        elif 0x6000 <= addr < 0x8000 and self.battery:
            return self.sram[addr - 0x6000]
        return self.mapper.read(addr)

    def write_byte(self, addr, value):
        addr &= 0xFFFF
        value &= 0xFF
        if addr < 0x2000:
            self.memory[addr & 0x07FF] = value
        elif addr < 0x4000:
            self.ppu.write_register(addr, value)
        elif addr == 0x4014:
            start_addr = value << 8
            for i in range(256):
                self.ppu.oam[i] = self.read_byte(start_addr + i)
            self.cycles += 513
        elif addr == 0x4016:
            self.controller.write(value)
        elif 0x6000 <= addr < 0x8000 and self.battery:
            self.sram[addr - 0x6000] = value
        else:
            self.mapper.write(addr, value)

    def read_word(self, addr):
        lo = self.read_byte(addr)
        hi = self.read_byte(addr + 1)
        return (hi << 8) | lo

    def set_flag(self, flag, value):
        if value:
            self.status |= (1 << flag)
        else:
            self.status &= ~(1 << flag)

    def get_flag(self, flag):
        return (self.status >> flag) & 1

    def push_byte(self, value):
        self.write_byte(0x0100 | self.sp, value)
        self.sp = (self.sp - 1) & 0xFF

    def pop_byte(self):
        self.sp = (self.sp + 1) & 0xFF
        return self.read_byte(0x0100 | self.sp)

    @lru_cache(maxsize=1024)
    def execute_instruction(self, opcode):
        """Execute a single 6502 instruction with caching."""
        cycles = 2
        addr_modes = {
            'imm': lambda: (self.pc, 1, 0),
            'abs': lambda: (self.read_word(self.pc), 2, 0),
            'abs_x': lambda: (
                base := self.read_word(self.pc),
                addr := (base + self.x) & 0xFFFF,
                (addr, 2, 1 if (base & 0xFF00) != (addr & 0xFF00) else 0)
            ),
            'abs_y': lambda: (
                base := self.read_word(self.pc),
                addr := (base + self.y) & 0xFFFF,
                (addr, 2, 1 if (base & 0xFF00) != (addr & 0xFF00) else 0)
            ),
            'zp': lambda: (self.read_byte(self.pc), 1, 0),
            'zp_x': lambda: ((self.read_byte(self.pc) + self.x) & 0xFF, 1, 0),
            'zp_y': lambda: ((self.read_byte(self.pc) + self.y) & 0xFF, 1, 0),
            'ind': lambda: (self.read_word(self.read_word(self.pc)), 2, 0),
            'ind_x': lambda: (self.read_word((self.read_byte(self.pc) + self.x) & 0xFF), 1, 0),
            'ind_y': lambda: (
                base := self.read_word(self.read_byte(self.pc)),
                addr := (base + self.y) & 0xFFFF,
                (addr, 1, 1 if (base & 0xFF00) != (addr & 0xFF00) else 0)
            ),
        }

        def adc(value):
            result = self.a + value + self.get_flag(0)
            self.set_flag(0, result > 0xFF)
            self.set_flag(7, result & 0x80)
            self.set_flag(6, ((self.a ^ result) & (value ^ result) & 0x80) != 0)
            self.a = result & 0xFF
            self.set_flag(1, self.a == 0)

        def sbc(value):
            value = value ^ 0xFF
            result = self.a + value + self.get_flag(0)
            self.set_flag(0, result > 0xFF)
            self.set_flag(7, result & 0x80)
            self.set_flag(6, ((self.a ^ result) & (value ^ result) & 0x80) != 0)
            self.a = result & 0xFF
            self.set_flag(1, self.a == 0)

        if self.interrupt == 'NMI':
            self.push_byte((self.pc >> 8) & 0xFF)
            self.push_byte(self.pc & 0xFF)
            self.push_byte(self.status)
            self.set_flag(2, 1)
            self.pc = self.read_word(0xFFFA)
            self.cycles += 7
            self.interrupt = None
            return 7

        instructions = {
            0x00: ('BRK', None, lambda: (self.pc := self.read_word(0xFFFE), self.push_byte((self.pc >> 8) & 0xFF), self.push_byte(self.pc & 0xFF), self.push_byte(self.status | 0x10), self.set_flag(2, 1), 7)),
            0x01: ('ORA', 'ind_x', lambda addr: (self.a |= self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 6)),
            0x05: ('ORA', 'zp', lambda addr: (self.a |= self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 3)),
            0x06: ('ASL', 'zp', lambda addr: (value := self.read_byte(addr), temp := value << 1, self.set_flag(0, temp & 0x100), value := temp & 0xFF, self.write_byte(addr, value), self.set_flag(7, value & 0x80), self.set_flag(1, value == 0), 5)),
            0x08: ('PHP', None, lambda: (self.push_byte(self.status), 3)),
            0x09: ('ORA', 'imm', lambda addr: (self.a |= self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 2)),
            0x0A: ('ASL', None, lambda: (temp := self.a << 1, self.set_flag(0, temp & 0x100), self.a := temp & 0xFF, self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 2)),
            0x0D: ('ORA', 'abs', lambda addr: (self.a |= self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 4)),
            0x0E: ('ASL', 'abs', lambda addr: (value := self.read_byte(addr), temp := value << 1, self.set_flag(0, temp & 0x100), value := temp & 0xFF, self.write_byte(addr, value), self.set_flag(7, value & 0x80), self.set_flag(1, value == 0), 6)),
            0x10: ('BPL', 'imm', lambda addr: (offset := self.read_byte(addr), taken := not self.get_flag(7), base_pc := self.pc, new_pc := (base_pc + (offset - 256 if offset >= 128 else offset)) & 0xFFFF if taken else base_pc, page_cross := (base_pc & 0xFF00) != (new_pc & 0xFF00) if taken else False, self.pc := new_pc, 2 + (1 if taken else 0) + (1 if page_cross else 0))),
            0x11: ('ORA', 'ind_y', lambda addr: (self.a |= self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 5)),
            0x15: ('ORA', 'zp_x', lambda addr: (self.a |= self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 4)),
            0x16: ('ASL', 'zp_x', lambda addr: (value := self.read_byte(addr), temp := value << 1, self.set_flag(0, temp & 0x100), value := temp & 0xFF, self.write_byte(addr, value), self.set_flag(7, value & 0x80), self.set_flag(1, value == 0), 6)),
            0x18: ('CLC', None, lambda: (self.set_flag(0, 0), 2)),
            0x19: ('ORA', 'abs_y', lambda addr: (self.a |= self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 4)),
            0x1D: ('ORA', 'abs_x', lambda addr: (self.a |= self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 4)),
            0x1E: ('ASL', 'abs_x', lambda addr: (value := self.read_byte(addr), temp := value << 1, self.set_flag(0, temp & 0x100), value := temp & 0xFF, self.write_byte(addr, value), self.set_flag(7, value & 0x80), self.set_flag(1, value == 0), 7)),
            0x20: ('JSR', 'abs', lambda addr: (self.push_byte((self.pc + 1) >> 8), self.push_byte((self.pc + 1) & 0xFF), self.pc := addr, 6)),
            0x21: ('AND', 'ind_x', lambda addr: (self.a &= self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 6)),
            0x24: ('BIT', 'zp', lambda addr: (value := self.read_byte(addr), self.set_flag(7, value & 0x80), self.set_flag(6, value & 0x40), self.set_flag(1, (self.a & value) == 0), 3)),
            0x25: ('AND', 'zp', lambda addr: (self.a &= self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 3)),
            0x26: ('ROL', 'zp', lambda addr: (value := self.read_byte(addr), carry := self.get_flag(0), self.set_flag(0, value & 0x80), value := ((value << 1) | carry) & 0xFF, self.write_byte(addr, value), self.set_flag(7, value & 0x80), self.set_flag(1, value == 0), 5)),
            0x28: ('PLP', None, lambda: (self.status := self.pop_byte() & ~0x10, 4)),
            0x29: ('AND', 'imm', lambda addr: (self.a &= self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 2)),
            0x2A: ('ROL', None, lambda: (carry := self.get_flag(0), self.set_flag(0, self.a & 0x80), self.a := ((self.a << 1) | carry) & 0xFF, self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 2)),
            0x2C: ('BIT', 'abs', lambda addr: (value := self.read_byte(addr), self.set_flag(7, value & 0x80), self.set_flag(6, value & 0x40), self.set_flag(1, (self.a & value) == 0), 4)),
            0x2D: ('AND', 'abs', lambda addr: (self.a &= self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 4)),
            0x2E: ('ROL', 'abs', lambda addr: (value := self.read_byte(addr), carry := self.get_flag(0), self.set_flag(0, value & 0x80), value := ((value << 1) | carry) & 0xFF, self.write_byte(addr, value), self.set_flag(7, value & 0x80), self.set_flag(1, value == 0), 6)),
            0x30: ('BMI', 'imm', lambda addr: (offset := self.read_byte(addr), taken := self.get_flag(7), base_pc := self.pc, new_pc := (base_pc + (offset - 256 if offset >= 128 else offset)) & 0xFFFF if taken else base_pc, page_cross := (base_pc & 0xFF00) != (new_pc & 0xFF00) if taken else False, self.pc := new_pc, 2 + (1 if taken else 0) + (1 if page_cross else 0))),
            0x31: ('AND', 'ind_y', lambda addr: (self.a &= self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 5)),
            0x35: ('AND', 'zp_x', lambda addr: (self.a &= self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 4)),
            0x36: ('ROL', 'zp_x', lambda addr: (value := self.read_byte(addr), carry := self.get_flag(0), self.set_flag(0, value & 0x80), value := ((value << 1) | carry) & 0xFF, self.write_byte(addr, value), self.set_flag(7, value & 0x80), self.set_flag(1, value == 0), 6)),
            0x38: ('SEC', None, lambda: (self.set_flag(0, 1), 2)),
            0x39: ('AND', 'abs_y', lambda addr: (self.a &= self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 4)),
            0x3D: ('AND', 'abs_x', lambda addr: (self.a &= self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 4)),
            0x3E: ('ROL', 'abs_x', lambda addr: (value := self.read_byte(addr), carry := self.get_flag(0), self.set_flag(0, value & 0x80), value := ((value << 1) | carry) & 0xFF, self.write_byte(addr, value), self.set_flag(7, value & 0x80), self.set_flag(1, value == 0), 7)),
            0x40: ('RTI', None, lambda: (self.status := self.pop_byte() & ~0x10, lo := self.pop_byte(), hi := self.pop_byte(), self.pc := (hi << 8) | lo, 6)),
            0x41: ('EOR', 'ind_x', lambda addr: (self.a ^= self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 6)),
            0x45: ('EOR', 'zp', lambda addr: (self.a ^= self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 3)),
            0x46: ('LSR', 'zp', lambda addr: (value := self.read_byte(addr), self.set_flag(0, value & 0x01), value := value >> 1, self.write_byte(addr, value), self.set_flag(7, value & 0x80), self.set_flag(1, value == 0), 5)),
            0x48: ('PHA', None, lambda: (self.push_byte(self.a), 3)),
            0x49: ('EOR', 'imm', lambda addr: (self.a ^= self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 2)),
            0x4A: ('LSR', None, lambda: (self.set_flag(0, self.a & 0x01), self.a := self.a >> 1, self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 2)),
            0x4C: ('JMP', 'abs', lambda addr: (self.pc := addr, 3)),
            0x4D: ('EOR', 'abs', lambda addr: (self.a ^= self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 4)),
            0x4E: ('LSR', 'abs', lambda addr: (value := self.read_byte(addr), self.set_flag(0, value & 0x01), value := value >> 1, self.write_byte(addr, value), self.set_flag(7, value & 0x80), self.set_flag(1, value == 0), 6)),
            0x50: ('BVC', 'imm', lambda addr: (offset := self.read_byte(addr), taken := not self.get_flag(6), base_pc := self.pc, new_pc := (base_pc + (offset - 256 if offset >= 128 else offset)) & 0xFFFF if taken else base_pc, page_cross := (base_pc & 0xFF00) != (new_pc & 0xFF00) if taken else False, self.pc := new_pc, 2 + (1 if taken else 0) + (1 if page_cross else 0))),
            0x51: ('EOR', 'ind_y', lambda addr: (self.a ^= self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 5)),
            0x55: ('EOR', 'zp_x', lambda addr: (self.a ^= self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 4)),
            0x56: ('LSR', 'zp_x', lambda addr: (value := self.read_byte(addr), self.set_flag(0, value & 0x01), value := value >> 1, self.write_byte(addr, value), self.set_flag(7, value & 0x80), self.set_flag(1, value == 0), 6)),
            0x58: ('CLI', None, lambda: (self.set_flag(2, 0), 2)),
            0x59: ('EOR', 'abs_y', lambda addr: (self.a ^= self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 4)),
            0x5D: ('EOR', 'abs_x', lambda addr: (self.a ^= self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 4)),
            0x5E: ('LSR', 'abs_x', lambda addr: (value := self.read_byte(addr), self.set_flag(0, value & 0x01), value := value >> 1, self.write_byte(addr, value), self.set_flag(7, value & 0x80), self.set_flag(1, value == 0), 7)),
            0x60: ('RTS', None, lambda: (lo := self.pop_byte(), hi := self.pop_byte(), self.pc := ((hi << 8) | lo) + 1, 6)),
            0x61: ('ADC', 'ind_x', lambda addr: (adc(self.read_byte(addr)), 6)),
            0x65: ('ADC', 'zp', lambda addr: (adc(self.read_byte(addr)), 3)),
            0x66: ('ROR', 'zp', lambda addr: (value := self.read_byte(addr), carry := self.get_flag(0), self.set_flag(0, value & 0x01), value := (value >> 1) | (carry << 7), self.write_byte(addr, value), self.set_flag(7, value & 0x80), self.set_flag(1, value == 0), 5)),
            0x68: ('PLA', None, lambda: (self.a := self.pop_byte(), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 4)),
            0x69: ('ADC', 'imm', lambda addr: (adc(self.read_byte(addr)), 2)),
            0x6A: ('ROR', None, lambda: (carry := self.get_flag(0), self.set_flag(0, self.a & 0x01), self.a := (self.a >> 1) | (carry << 7), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 2)),
            0x6C: ('JMP', 'abs', lambda addr: (lo := self.read_byte(addr), hi := self.read_byte((addr & 0xFF00) | ((addr + 1) & 0x00FF)), self.pc := (hi << 8) | lo, 5)),
            0x6D: ('ADC', 'abs', lambda addr: (adc(self.read_byte(addr)), 4)),
            0x6E: ('ROR', 'abs', lambda addr: (value := self.read_byte(addr), carry := self.get_flag(0), self.set_flag(0, value & 0x01), value := (value >> 1) | (carry << 7), self.write_byte(addr, value), self.set_flag(7, value & 0x80), self.set_flag(1, value == 0), 6)),
            0x70: ('BVS', 'imm', lambda addr: (offset := self.read_byte(addr), taken := self.get_flag(6), base_pc := self.pc, new_pc := (base_pc + (offset - 256 if offset >= 128 else offset)) & 0xFFFF if taken else base_pc, page_cross := (base_pc & 0xFF00) != (new_pc & 0xFF00) if taken else False, self.pc := new_pc, 2 + (1 if taken else 0) + (1 if page_cross else 0))),
            0x71: ('ADC', 'ind_y', lambda addr: (adc(self.read_byte(addr)), 5)),
            0x75: ('ADC', 'zp_x', lambda addr: (adc(self.read_byte(addr)), 4)),
            0x76: ('ROR', 'zp_x', lambda addr: (value := self.read_byte(addr), carry := self.get_flag(0), self.set_flag(0, value & 0x01), value := (value >> 1) | (carry << 7), self.write_byte(addr, value), self.set_flag(7, value & 0x80), self.set_flag(1, value == 0), 6)),
            0x78: ('SEI', None, lambda: (self.set_flag(2, 1), 2)),
            0x79: ('ADC', 'abs_y', lambda addr: (adc(self.read_byte(addr)), 4)),
            0x7D: ('ADC', 'abs_x', lambda addr: (adc(self.read_byte(addr)), 4)),
            0x7E: ('ROR', 'abs_x', lambda addr: (value := self.read_byte(addr), carry := self.get_flag(0), self.set_flag(0, value & 0x01), value := (value >> 1) | (carry << 7), self.write_byte(addr, value), self.set_flag(7, value & 0x80), self.set_flag(1, value == 0), 7)),
            0x81: ('STA', 'ind_x', lambda addr: (self.write_byte(addr, self.a), 6)),
            0x85: ('STA', 'zp', lambda addr: (self.write_byte(addr, self.a), 3)),
            0x86: ('STX', 'zp', lambda addr: (self.write_byte(addr, self.x), 3)),
            0x88: ('DEY', None, lambda: (self.y := (self.y - 1) & 0xFF, self.set_flag(7, self.y & 0x80), self.set_flag(1, self.y == 0), 2)),
            0x8A: ('TXA', None, lambda: (self.a := self.x, self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 2)),
            0x8C: ('STY', 'abs', lambda addr: (self.write_byte(addr, self.y), 4)),
            0x8D: ('STA', 'abs', lambda addr: (self.write_byte(addr, self.a), 4)),
            0x8E: ('STX', 'abs', lambda addr: (self.write_byte(addr, self.x), 4)),
            0x90: ('BCC', 'imm', lambda addr: (offset := self.read_byte(addr), taken := not self.get_flag(0), base_pc := self.pc, new_pc := (base_pc + (offset - 256 if offset >= 128 else offset)) & 0xFFFF if taken else base_pc, page_cross := (base_pc & 0xFF00) != (new_pc & 0xFF00) if taken else False, self.pc := new_pc, 2 + (1 if taken else 0) + (1 if page_cross else 0))),
            0x91: ('STA', 'ind_y', lambda addr: (self.write_byte(addr, self.a), 6)),
            0x94: ('STY', 'zp_x', lambda addr: (self.write_byte(addr, self.y), 4)),
            0x95: ('STA', 'zp_x', lambda addr: (self.write_byte(addr, self.a), 4)),
            0x96: ('STX', 'zp_y', lambda addr: (self.write_byte(addr, self.x), 4)),
            0x98: ('TYA', None, lambda: (self.a := self.y, self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 2)),
            0x99: ('STA', 'abs_y', lambda addr: (self.write_byte(addr, self.a), 5)),
            0x9A: ('TXS', None, lambda: (self.sp := self.x, 2)),
            0x9D: ('STA', 'abs_x', lambda addr: (self.write_byte(addr, self.a), 5)),
            0xA0: ('LDY', 'imm', lambda addr: (self.y := self.read_byte(addr), self.set_flag(7, self.y & 0x80), self.set_flag(1, self.y == 0), 2)),
            0xA1: ('LDA', 'ind_x', lambda addr: (self.a := self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 6)),
            0xA2: ('LDX', 'imm', lambda addr: (self.x := self.read_byte(addr), self.set_flag(7, self.x & 0x80), self.set_flag(1, self.x == 0), 2)),
            0xA4: ('LDY', 'zp', lambda addr: (self.y := self.read_byte(addr), self.set_flag(7, self.y & 0x80), self.set_flag(1, self.y == 0), 3)),
            0xA5: ('LDA', 'zp', lambda addr: (self.a := self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 3)),
            0xA6: ('LDX', 'zp', lambda addr: (self.x := self.read_byte(addr), self.set_flag(7, self.x & 0x80), self.set_flag(1, self.x == 0), 3)),
            0xA8: ('TAY', None, lambda: (self.y := self.a, self.set_flag(7, self.y & 0x80), self.set_flag(1, self.y == 0), 2)),
            0xA9: ('LDA', 'imm', lambda addr: (self.a := self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 2)),
            0xAA: ('TAX', None, lambda: (self.x := self.a, self.set_flag(7, self.x & 0x80), self.set_flag(1, self.x == 0), 2)),
            0xAC: ('LDY', 'abs', lambda addr: (self.y := self.read_byte(addr), self.set_flag(7, self.y & 0x80), self.set_flag(1, self.y == 0), 4)),
            0xAD: ('LDA', 'abs', lambda addr: (self.a := self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 4)),
            0xAE: ('LDX', 'abs', lambda addr: (self.x := self.read_byte(addr), self.set_flag(7, self.x & 0x80), self.set_flag(1, self.x == 0), 4)),
            0xB0: ('BCS', 'imm', lambda addr: (offset := self.read_byte(addr), taken := self.get_flag(0), base_pc := self.pc, new_pc := (base_pc + (offset - 256 if offset >= 128 else offset)) & 0xFFFF if taken else base_pc, page_cross := (base_pc & 0xFF00) != (new_pc & 0xFF00) if taken else False, self.pc := new_pc, 2 + (1 if taken else 0) + (1 if page_cross else 0))),
            0xB1: ('LDA', 'ind_y', lambda addr: (self.a := self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 5)),
            0xB4: ('LDY', 'zp_x', lambda addr: (self.y := self.read_byte(addr), self.set_flag(7, self.y & 0x80), self.set_flag(1, self.y == 0), 4)),
            0xB5: ('LDA', 'zp_x', lambda addr: (self.a := self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 4)),
            0xB6: ('LDX', 'zp_y', lambda addr: (self.x := self.read_byte(addr), self.set_flag(7, self.x & 0x80), self.set_flag(1, self.x == 0), 4)),
            0xB8: ('CLV', None, lambda: (self.set_flag(6, 0), 2)),
            0xB9: ('LDA', 'abs_y', lambda addr: (self.a := self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 4)),
            0xBA: ('TSX', None, lambda: (self.x := self.sp, self.set_flag(7, self.x & 0x80), self.set_flag(1, self.x == 0), 2)),
            0xBC: ('LDY', 'abs_x', lambda addr: (self.y := self.read_byte(addr), self.set_flag(7, self.y & 0x80), self.set_flag(1, self.y == 0), 4)),
            0xBD: ('LDA', 'abs_x', lambda addr: (self.a := self.read_byte(addr), self.set_flag(7, self.a & 0x80), self.set_flag(1, self.a == 0), 4)),
            0xBE: ('LDX', 'abs_y', lambda addr: (self.x := self.read_byte(addr), self.set_flag(7, self.x & 0x80), self.set_flag(1, self.x == 0), 4)),
            0xC0: ('CPY', 'imm', lambda addr: (result := (self.y - self.read_byte(addr)) & 0xFF, self.set_flag(7, result & 0x80), self.set_flag(1, result == 0), self.set_flag(0, self.y >= self.read_byte(addr)), 2)),
            0xC1: ('CMP', 'ind_x', lambda addr: (result := (self.a - self.read_byte(addr)) & 0xFF, self.set_flag(7, result & 0x80), self.set_flag(1, result == 0), self.set_flag(0, self.a >= self.read_byte(addr)), 6)),
            0xC4: ('CPY', 'zp', lambda addr: (result := (self.y - self.read_byte(addr)) & 0xFF, self.set_flag(7, result & 0x80), self.set_flag(1, result == 0), self.set_flag(0, self.y >= self.read_byte(addr)), 3)),
            0xC5: ('CMP', 'zp', lambda addr: (result := (self.a - self.read_byte(addr)) & 0xFF, self.set_flag(7, result & 0x80), self.set_flag(1, result == 0), self.set_flag(0, self.a >= self.read_byte(addr)), 3)),
            0xC6: ('DEC', 'zp', lambda addr: (value := (self.read_byte(addr) - 1) & 0xFF, self.write_byte(addr, value), self.set_flag(7, value & 0x80), self.set_flag(1, value == 0), 5)),
            0xC8: ('INY', None, lambda: (self.y := (self.y + 1) & 0xFF, self.set_flag(7, self.y & 0x80), self.set_flag(1, self.y == 0), 2)),
            0xC9: ('CMP', 'imm', lambda addr: (result := (self.a - self.read_byte(addr)) & 0xFF, self.set_flag(7, result & 0x80), self.set_flag(1, result == 0), self.set_flag(0, self.a >= self.read_byte(addr)), 2)),
            0xCA: ('DEX', None, lambda: (self.x := (self.x - 1) & 0xFF, self.set_flag(7, self.x & 0x80), self.set_flag(1, self.x == 0), 2)),
            0xCC: ('CPY', 'abs', lambda addr: (result := (self.y - self.read_byte(addr)) & 0xFF, self.set_flag(7, result & 0x80), self.set_flag(1, result == 0), self.set_flag(0, self.y >= self.read_byte(addr)), 4)),
            0xCD: ('CMP', 'abs', lambda addr: (result := (self.a - self.read_byte(addr)) & 0xFF, self.set_flag(7, self.a & 0x80), self.set_flag(1, result == 0), self.set_flag(0, self.a >= self.read_byte(addr)), 4)),
            0xCE: ('DEC', 'abs', lambda addr: (value := (self.read_byte(addr) - 1) & 0xFF, self.write_byte(addr, value), self.set_flag(7, value & 0x80), self.set_flag(1, value == 0), 6)),
            0xD0: ('BNE', 'imm', lambda addr: (offset := self.read_byte(addr), taken := not self.get_flag(1), base_pc := self.pc, new_pc := (base_pc + (offset - 256 if offset >= 128 else offset)) & 0xFFFF if taken else base_pc, page_cross := (base_pc & 0xFF00) != (new_pc & 0xFF00) if taken else False, self.pc := new_pc, 2 + (1 if taken else 0) + (1 if page_cross else 0))),
            0xD1: ('CMP', 'ind_y', lambda addr: (result := (self.a - self.read_byte(addr)) & 0xFF, self.set_flag(7, result & 0x80), self.set_flag(1, result == 0), self.set_flag(0, self.a >= self.read_byte(addr)), 5)),
            0xD5: ('CMP', 'zp_x', lambda addr: (result := (self.a - self.read_byte(addr)) & 0xFF, self.set_flag(7, result & 0x80), self.set_flag(1, result == 0), self.set_flag(0, self.a >= self.read_byte(addr)), 4)),
            0xD6: ('DEC', 'zp_x', lambda addr: (value := (self.read_byte(addr) - 1) & 0xFF, self.write_byte(addr, value), self.set_flag(7, value & 0x80), self.set_flag(1, value == 0), 6)),
            0xD8: ('CLD', None, lambda: (self.set_flag(3, 0), 2)),
            0xD9: ('CMP', 'abs_y', lambda addr: (result := (self.a - self.read_byte(addr)) & 0xFF, self.set_flag(7, result & 0x80), self.set_flag(1, result == 0), self.set_flag(0, self.a >= self.read_byte(addr)), 4)),
            0xDD: ('CMP', 'abs_x', lambda addr: (result := (self.a - self.read_byte(addr)) & 0xFF, self.set_flag(7, result & 0x80), self.set_flag(1, result == 0), self.set_flag(0, self.a >= self.read_byte(addr)), 4)),
            0xDE: ('DEC', 'abs_x', lambda addr: (value := (self.read_byte(addr) - 1) & 0xFF, self.write_byte(addr, value), self.set_flag(7, value & 0x80), self.set_flag(1, value == 0), 7)),
            0xE0: ('CPX', 'imm', lambda addr: (result := (self.x - self.read_byte(addr)) & 0xFF, self.set_flag(7, result & 0x80), self.set_flag(1, result == 0), self.set_flag(0, self.x >= self.read_byte(addr)), 2)),
            0xE1: ('SBC', 'ind_x', lambda addr: (sbc(self.read_byte(addr)), 6)),
            0xE4: ('CPX', 'zp', lambda addr: (result := (self.x - self.read_byte(addr)) & 0xFF, self.set_flag(7, result & 0x80), self.set_flag(1, result == 0), self.set_flag(0, self.x >= self.read_byte(addr)), 3)),
            0xE5: ('SBC', 'zp', lambda addr: (sbc(self.read_byte(addr)), 3)),
            0xE6: ('INC', 'zp', lambda addr: (value := (self.read_byte(addr) + 1) & 0xFF, self.write_byte(addr, value), self.set_flag(7, value & 0x80), self.set_flag(1, value == 0), 5)),
            0xE8: ('INX', None, lambda: (self.x := (self.x + 1) & 0xFF, self.set_flag(7, self.x & 0x80), self.set_flag(1, self.x == 0), 2)),
            0xE9: ('SBC', 'imm', lambda addr: (sbc(self.read_byte(addr)), 2)),
            0xEA: ('NOP', None, lambda: (2,)),
            0xEC: ('CPX', 'abs', lambda addr: (result := (self.x - self.read_byte(addr)) & 0xFF, self.set_flag(7, result & 0x80), self.set_flag(1, result == 0), self.set_flag(0, self.x >= self.read_byte(addr)), 4)),
            0xED: ('SBC', 'abs', lambda addr: (sbc(self.read_byte(addr)), 4)),
            0xEE: ('INC', 'abs', lambda addr: (value := (self.read_byte(addr) + 1) & 0xFF, self.write_byte(addr, value), self.set_flag(7, value & 0x80), self.set_flag(1, value == 0), 6)),
            0xF0: ('BEQ', 'imm', lambda addr: (offset := self.read_byte(addr), taken := self.get_flag(1), base_pc := self.pc, new_pc := (base_pc + (offset - 256 if offset >= 128 else offset)) & 0xFFFF if taken else base_pc, page_cross := (base_pc & 0xFF00) != (new_pc & 0xFF00) if taken else False, self.pc := new_pc, 2 + (1 if taken else 0) + (1 if page_cross else 0))),
            0xF1: ('SBC', 'ind_y', lambda addr: (sbc(self.read_byte(addr)), 5)),
            0xF5: ('SBC', 'zp_x', lambda addr: (sbc(self.read_byte(addr)), 4)),
            0xF6: ('INC', 'zp_x', lambda addr: (value := (self.read_byte(addr) + 1) & 0xFF, self.write_byte(addr, value), self.set_flag(7, value & 0x80), self.set_flag(1, value == 0), 6)),
            0xF8: ('SED', None, lambda: (self.set_flag(3, 1), 2)),
            0xF9: ('SBC', 'abs_y', lambda addr: (sbc(self.read_byte(addr)), 4)),
            0xFD: ('SBC', 'abs_x', lambda addr: (sbc(self.read_byte(addr)), 4)),
            0xFE: ('INC', 'abs_x', lambda addr: (value := (self.read_byte(addr) + 1) & 0xFF, self.write_byte(addr, value), self.set_flag(7, value & 0x80), self.set_flag(1, value == 0), 7)),
        }

        if opcode not in instructions:
            print(f"Unsupported opcode: 0x{opcode:02X} at PC=0x{self.pc-1:04X}")
            self.cycles += 2
            return 2

        name, addr_mode, func = instructions[opcode]
        if addr_mode:
            addr, pc_inc, extra_cycle = addr_modes[addr_mode]()
            self.pc += pc_inc
            _, base_cycles = func(addr)
            cycles = base_cycles + extra_cycle
        else:
            result = func()
            cycles = result[0] if isinstance(result, tuple) else result
        self.cycles += cycles
        return cycles

    def step(self):
        self.pc += 1
        return self.execute_instruction(self.read_byte(self.pc - 1))

class Mapper:
    """Base class for iNES mappers."""
    def __init__(self, prg_data, chr_data, battery):
        self.prg_data = prg_data
        self.chr_data = chr_data
        self.battery = battery

    def load(self, memory, sram):
        pass

    def read(self, addr):
        return 0

    def write(self, addr, value):
        pass

    def ppu_read(self, addr):
        return 0

    @staticmethod
    def create(mapper_id, prg_data, chr_data, battery):
        if mapper_id == 0:
            return NROM(prg_data, chr_data, battery)
        elif mapper_id == 1:
            return MMC1(prg_data, chr_data, battery)
        elif mapper_id == 3:
            return CNROM(prg_data, chr_data, battery)
        else:
            raise ValueError(f"Unsupported mapper: {mapper_id}")

class NROM(Mapper):
    """Mapper 0: NROM - No bank switching."""
    def load(self, memory, sram):
        if len(self.prg_data) == 0x4000:
            memory[0x8000:0xC000] = self.prg_data
            memory[0xC000:0x10000] = self.prg_data  # Mirror if 16KB
        else:
            memory[0x8000:0x10000] = self.prg_data

    def read(self, addr):
        if 0x8000 <= addr < 0x10000:
            return self.prg_data[addr - 0x8000] if addr - 0x8000 < len(self.prg_data) else 0
        return 0

    def ppu_read(self, addr):
        """Read CHR data directly (no bank switching)."""
        addr &= 0x1FFF
        return self.chr_data[addr] if addr < len(self.chr_data) else 0

class MMC1(Mapper):
    """Mapper 1: MMC1 - Supports PRG and CHR bank switching."""
    def __init__(self, prg_data, chr_data, battery):
        super().__init__(prg_data, chr_data, battery)
        self.shift_reg = 0
        self.shift_count = 0
        self.control = 0x0C  # Default: 8KB CHR, 16KB PRG at 0xC000
        self.chr_bank0 = 0
        self.chr_bank1 = 0
        self.prg_bank = 0
        self.prg_mode = 3
        self.chr_mode = 0

    def load(self, memory, sram):
        if len(self.prg_data) >= 0x4000:
            memory[0x8000:0xC000] = self.prg_data[0:0x4000]  # First bank
            last_bank_offset = (len(self.prg_data) // 0x4000 - 1) * 0x4000
            memory[0xC000:0x10000] = self.prg_data[last_bank_offset:last_bank_offset + 0x4000]  # Last bank
        else:
            memory[0x8000:0x10000] = self.prg_data + self.prg_data[:0x8000 - len(self.prg_data)]

    def read(self, addr):
        if 0x8000 <= addr < 0x10000:
            if self.prg_mode == 3:  # 16KB PRG at 0xC000
                if addr < 0xC000:
                    bank = 0
                else:
                    bank = self.prg_bank * 0x4000
            else:  # 32KB PRG
                bank = (self.prg_bank >> 1) * 0x8000
            offset = addr & 0x3FFF if self.prg_mode == 3 else addr & 0x7FFF
            index = bank + offset
            return self.prg_data[index] if index < len(self.prg_data) else 0
        return 0

    def write(self, addr, value):
        if addr < 0x8000:
            return
        if value & 0x80:  # Reset
            self.shift_reg = 0
            self.shift_count = 0
            self.control |= 0x0C
        else:
            self.shift_reg |= (value & 0x01) << self.shift_count
            self.shift_count += 1
            if self.shift_count == 5:
                reg = (addr >> 13) & 0x03
                if reg == 0:
                    self.control = self.shift_reg & 0x1F
                    self.prg_mode = (self.control >> 2) & 0x03
                    self.chr_mode = (self.control >> 4) & 0x01
                elif reg == 1:
                    self.chr_bank0 = self.shift_reg & 0x1F
                elif reg == 2:
                    self.chr_bank1 = self.shift_reg & 0x1F
                elif reg == 3:
                    self.prg_bank = self.shift_reg & 0x0F
                self.shift_reg = 0
                self.shift_count = 0

    def ppu_read(self, addr):
        """Read CHR data with bank switching."""
        addr &= 0x1FFF
        if self.chr_mode == 0:  # 8KB CHR mode
            bank = (self.chr_bank0 >> 1) * 0x2000
            return self.chr_data[bank + addr] if bank + addr < len(self.chr_data) else 0
        else:  # 4KB CHR mode
            if addr < 0x1000:
                bank = self.chr_bank0 * 0x1000
                return self.chr_data[bank + addr] if bank + addr < len(self.chr_data) else 0
            else:
                bank = self.chr_bank1 * 0x1000
                return self.chr_data[bank + (addr - 0x1000)] if bank + (addr - 0x1000) < len(self.chr_data) else 0

class CNROM(Mapper):
    """Mapper 3: CNROM - CHR bank switching."""
    def __init__(self, prg_data, chr_data, battery):
        super().__init__(prg_data, chr_data, battery)
        self.chr_bank = 0

    def load(self, memory, sram):
        memory[0x8000:0x10000] = self.prg_data + self.prg_data[:0x8000 - len(self.prg_data)] if len(self.prg_data) < 0x8000 else self.prg_data[:0x8000]

    def read(self, addr):
        if 0x8000 <= addr < 0x10000:
            return self.prg_data[addr - 0x8000] if addr - 0x8000 < len(self.prg_data) else 0
        return 0

    def write(self, addr, value):
        if 0x8000 <= addr < 0x10000:
            self.chr_bank = value & 0x03

    def ppu_read(self, addr):
        """Read CHR data with 8KB bank switching."""
        addr &= 0x1FFF
        bank_offset = self.chr_bank * 0x2000
        return self.chr_data[bank_offset + addr] if bank_offset + addr < len(self.chr_data) else 0

class PPU:
    """Simulates the NES Picture Processing Unit (PPU)."""
    def __init__(self, cpu):
        self.cpu = cpu
        self.vram = bytearray(0x4000)
        self.oam = bytearray(0x100)
        self.framebuffer = [(0, 0, 0)] * (SCREEN_WIDTH * SCREEN_HEIGHT)
        self.scanline = 0
        self.cycle = 0
        self.ctrl = 0
        self.mask = 0
        self.status = 0
        self.addr = 0
        self.data_buffer = 0
        self.nametable_base = 0x2000
        self.pattern_table_base = 0
        self.palette = [
            (84, 84, 84), (0, 30, 116), (8, 16, 144), (48, 0, 136),
            (68, 0, 100), (92, 0, 48), (84, 4, 0), (60, 24, 0),
            (32, 42, 0), (8, 58, 0), (0, 64, 0), (0, 60, 0),
            (0, 50, 60), (0, 0, 0), (0, 0, 0), (0, 0, 0),
            (152, 150, 152), (8, 76, 196), (48, 50, 236), (92, 30, 228),
            (136, 20, 176), (160, 20, 100), (152, 34, 32), (120, 60, 0),
            (84, 90, 0), (40, 114, 0), (8, 124, 0), (0, 118, 40),
            (0, 102, 120), (0, 0, 0), (0, 0, 0), (0, 0, 0),
            (236, 238, 236), (76, 154, 236), (120, 124, 236), (176, 98, 236),
            (228, 84, 236), (236, 88, 180), (236, 106, 100), (212, 136, 32),
            (160, 170, 0), (116, 196, 0), (76, 208, 32), (56, 204, 108),
            (56, 180, 204), (60, 60, 60), (0, 0, 0), (0, 0, 0),
            (236, 238, 236), (168, 204, 236), (188, 188, 236), (212, 178, 236),
            (236, 174, 236), (236, 174, 212), (236, 180, 176), (228, 196, 144),
            (204, 210, 120), (180, 222, 120), (168, 226, 144), (152, 226, 180),
            (160, 214, 228), (160, 162, 160), (0, 0, 0), (0, 0, 0)
        ]

    def reset(self):
        """Reset PPU state."""
        self.framebuffer = [(0, 0, 0)] * (SCREEN_WIDTH * SCREEN_HEIGHT)
        self.scanline = 0
        self.cycle = 0
        self.ctrl = 0
        self.mask = 0
        self.status = 0
        self.addr = 0
        self.data_buffer = 0
        self.nametable_base = 0x2000
        self.pattern_table_base = 0

    def map_address(self, addr):
        """Map PPU address space with mirroring."""
        if 0x2000 <= addr < 0x3000:
            nt_addr = addr & 0x3FF
            nt = (addr >> 10) & 3
            if self.cpu.mirroring == 0:  # Horizontal
                if nt == 2:
                    nt = 0
                elif nt == 3:
                    nt = 1
            elif self.cpu.mirroring == 1:  # Vertical
                if nt == 1:
                    nt = 0
                elif nt == 3:
                    nt = 2
            return 0x2000 + (nt * 0x400) + nt_addr
        elif 0x3F00 <= addr < 0x4000:
            addr = 0x3F00 + (addr & 0x1F)
            if addr in [0x3F10, 0x3F14, 0x3F18, 0x3F1C]:
                addr -= 0x10
            return addr
        return addr & 0x3FFF

    def read_register(self, addr):
        addr &= 0x2007
        if addr == 0x2002:
            value = self.status
            self.status &= ~0x80  # Clear VBlank flag
            return value
        elif addr == 0x2007:
            if 0x3F00 <= self.addr < 0x4000:
                value = self.vram[self.map_address(self.addr)]
            else:
                value = self.data_buffer
                self.data_buffer = self.vram[self.map_address(self.addr)]
            self.addr = (self.addr + (32 if self.ctrl & 0x04 else 1)) & 0x3FFF
            return value
        return 0

    def write_register(self, addr, value):
        addr &= 0x2007
        value &= 0xFF
        if addr == 0x2000:
            self.ctrl = value
            self.nametable_base = 0x2000 + (value & 0x03) * 0x400
            self.pattern_table_base = (value & 0x10) << 8  # 0x0000 or 0x1000
        elif addr == 0x2001:
            self.mask = value
        elif addr == 0x2006:
            self.addr = (self.addr << 8) | value
            self.addr &= 0x3FFF
        elif addr == 0x2007:
            self.vram[self.map_address(self.addr)] = value
            self.addr = (self.addr + (32 if self.ctrl & 0x04 else 1)) & 0x3FFF

    def render_frame(self):
        """Render a frame using mapper for CHR data."""
        if not (self.mask & 0x18):  # Rendering disabled
            self.framebuffer = [(0, 0, 0)] * (SCREEN_WIDTH * SCREEN_HEIGHT)
            return
        for tile_y in range(30):
            for tile_x in range(32):
                tile_idx = tile_y * 32 + tile_x
                tile_addr = self.map_address(self.nametable_base + tile_idx)
                tile_num = self.vram[tile_addr]
                attr_addr = self.map_address(self.nametable_base + 0x3C0 + (tile_y // 4) * 8 + (tile_x // 4))
                attr = self.vram[attr_addr]
                palette_idx = (attr >> ((tile_y % 4 // 2) * 4 + (tile_x % 4 // 2) * 2)) & 0x03
                tile_addr = self.pattern_table_base + tile_num * 16
                for y in range(8):
                    byte1 = self.cpu.mapper.ppu_read(tile_addr + y)
                    byte2 = self.cpu.mapper.ppu_read(tile_addr + y + 8)
                    for x in range(8):
                        pixel_x = tile_x * 8 + x
                        pixel_y = tile_y * 8 + y
                        if pixel_x >= SCREEN_WIDTH or pixel_y >= SCREEN_HEIGHT:
                            continue
                        bit1 = (byte1 >> (7 - x)) & 1
                        bit2 = (byte2 >> (7 - x)) & 1
                        color_idx = (bit2 << 1) | bit1
                        if color_idx:
                            color_idx = self.vram[self.map_address(0x3F00 + palette_idx * 4 + color_idx)] & 0x3F
                        else:
                            color_idx = self.vram[self.map_address(0x3F00)] & 0x3F
                        self.framebuffer[pixel_y * SCREEN_WIDTH + pixel_x] = self.palette[color_idx]
        if self.ctrl & 0x80:  # NMI enabled
            self.cpu.interrupt = 'NMI'

class APU:
    """Simulates the NES Audio Processing Unit (APU)."""
    def __init__(self):
        self.pulse1 = {'enable': False, 'freq': 440, 'volume': 0, 'sweep': 0, 'duty': 0}
        self.pulse2 = {'enable': False, 'freq': 440, 'volume': 0, 'sweep': 0, 'duty': 0}
        pygame.mixer.init(44100, -16, 2)
        self.channel1 = pygame.mixer.Channel(0)
        self.channel2 = pygame.mixer.Channel(1)

    def write_register(self, addr, value):
        if addr == 0x4000:
            self.pulse1['duty'] = (value >> 6) & 0x03
            self.pulse1['volume'] = value & 0x0F
            self.pulse1['enable'] = bool(value & 0x10)
        elif addr == 0x4001:
            self.pulse1['sweep'] = value
        elif addr == 0x4002:
            self.pulse1['freq'] = (self.pulse1['freq'] & 0xFF00) | value
        elif addr == 0x4003:
            self.pulse1['freq'] = (self.pulse1['freq'] & 0xFF) | ((value & 0x07) << 8)
        elif addr == 0x4004:
            self.pulse2['duty'] = (value >> 6) & 0x03
            self.pulse2['volume'] = value & 0x0F
            self.pulse2['enable'] = bool(value & 0x10)
        elif addr == 0x4005:
            self.pulse2['sweep'] = value
        elif addr == 0x4006:
            self.pulse2['freq'] = (self.pulse2['freq'] & 0xFF00) | value
        elif addr == 0x4007:
            self.pulse2['freq'] = (self.pulse2['freq'] & 0xFF) | ((value & 0x07) << 8)
        elif addr == 0x4015:
            self.pulse1['enable'] = bool(value & 0x01)
            self.pulse2['enable'] = bool(value & 0x02)

    def update(self):
        duty_cycles = [0.125, 0.25, 0.5, 0.75]  # NES duty cycles
        if self.pulse1['enable']:
            freq = max(100, min(2000, self.pulse1['freq'] + (self.pulse1['sweep'] & 0x07) * 10))
            duty = duty_cycles[self.pulse1['duty']]
            t = np.arange(44100) / 44100 * freq
            square_wave = (t % 1 < duty).astype(np.int16) * 2 - 1
            sound_array = (square_wave * 1000 * (self.pulse1['volume'] / 15)).astype(np.int16)
            sound = pygame.mixer.Sound(sound_array)
            self.channel1.play(sound, loops=-1)
        else:
            self.channel1.stop()

        if self.pulse2['enable']:
            freq = max(100, min(2000, self.pulse2['freq'] + (self.pulse2['sweep'] & 0x07) * 10))
            duty = duty_cycles[self.pulse2['duty']]
            t = np.arange(44100) / 44100 * freq
            square_wave = (t % 1 < duty).astype(np.int16) * 2 - 1
            sound_array = (square_wave * 1000 * (self.pulse2['volume'] / 15)).astype(np.int16)
            sound = pygame.mixer.Sound(sound_array)
            self.channel2.play(sound, loops=-1)
        else:
            self.channel2.stop()

class Controller:
    """Simulates NES controller input."""
    def __init__(self):
        self.buttons = [False] * 8  # A, B, Select, Start, Up, Down, Left, Right
        self.index = 0
        self.strobe = False

    def write(self, value):
        self.strobe = bool(value & 0x01)
        if self.strobe:
            self.index = 0

    def read(self):
        if self.strobe:
            return int(self.buttons[0])
        if self.index < 8:
            value = int(self.buttons[self.index])
            self.index += 1
            return value
        return 0

class NESEmulator:
    """The NES Emulator core."""
    def __init__(self):
        self.cpu = MOS6502()
        self.ppu = PPU(self.cpu)
        self.apu = APU()
        self.controller = Controller()
        self.loaded_rom = None
        self.cheats = {}
        self.save_states = []
        self.cpu.ppu = self.ppu
        self.cpu.controller = self.controller

    def load_rom(self, rom_path):
        with open(rom_path, 'rb') as f:
            self.loaded_rom = f.read()
        self.cpu.load_program(self.loaded_rom)
        self.cpu.reset()
        self.ppu.reset()
        if self.cpu.battery and os.path.exists(f"{rom_path}.sav"):
            with open(f"{rom_path}.sav", 'rb') as f:
                self.cpu.sram = bytearray(f.read())

    def step_frame(self):
        cycles_per_frame = 29780  # Approximate NTSC cycles per frame
        while self.cpu.cycles < cycles_per_frame:
            cycles = self.cpu.step()
            self.ppu.cycle += cycles * 3
            if self.ppu.cycle >= 341:
                self.ppu.cycle -= 341
                self.ppu.scanline += 1
                if self.ppu.scanline == 241:
                    self.ppu.status |= 0x80  # Set VBlank flag
                    self.ppu.render_frame()
                if self.ppu.scanline >= 262:
                    self.ppu.scanline = 0
                    self.ppu.status &= ~0x80  # Clear VBlank flag
                    self.cpu.cycles = 0
                    break
        self.apu.update()
        for addr, value in self.cheats.items():
            self.cpu.write_byte(addr, value)

    def save_state(self):
        state = {
            'cpu': pickle.dumps(self.cpu.__dict__),
            'ppu': pickle.dumps(self.ppu.__dict__),
            'apu': pickle.dumps(self.apu.__dict__),
            'controller': pickle.dumps(self.controller.__dict__)
        }
        compressed_state = zlib.compress(pickle.dumps(state))
        self.save_states.append(compressed_state)
        return len(self.save_states) - 1

    def load_state(self, slot):
        if 0 <= slot < len(self.save_states):
            state = pickle.loads(zlib.decompress(self.save_states[slot]))
            self.cpu.__dict__.update(pickle.loads(state['cpu']))
            self.ppu.__dict__.update(pickle.loads(state['ppu']))
            self.apu.__dict__.update(pickle.loads(state['apu']))
            self.controller.__dict__.update(pickle.loads(state['controller']))

class NESEmulatorApp:
    """Tkinter-based GUI for the NES Emulator."""
    def __init__(self, root):
        self.root = root
        self.root.title("NES Emulator")
        self.emulator = NESEmulator()
        self.canvas = tk.Canvas(root, width=SCREEN_WIDTH*2, height=SCREEN_HEIGHT*2)
        self.canvas.pack()
        self.speed = 1.0
        self.fast_forward = False
        self.key_map = {'z': 0, 'x': 1, 'a': 2, 's': 3, 'Up': 4, 'Down': 5, 'Left': 6, 'Right': 7}
        self.setup_menu()
        self.setup_keybindings()
        self.update_frame()

    def setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load ROM", command=self.load_rom)
        file_menu.add_command(label="Save State", command=lambda: self.emulator.save_state())
        file_menu.add_command(label="Load State", command=lambda: self.emulator.load_state(0))
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.quit)
        options_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Options", menu=options_menu)
        options_menu.add_command(label="Configure Input", command=self.configure_input)
        options_menu.add_command(label="Apply Cheat", command=self.apply_cheat)

    def setup_keybindings(self):
        for key in self.key_map:
            self.root.bind(f"<KeyPress-{key}>", self.key_press)
            self.root.bind(f"<KeyRelease-{key}>", self.key_release)
        self.root.bind("<F5>", lambda e: self.emulator.save_state())
        self.root.bind("<F7>", lambda e: self.emulator.load_state(0))
        self.root.bind("<F11>", lambda e: self.toggle_fullscreen())
        self.root.bind("<Shift_L>", lambda e: setattr(self, 'fast_forward', True))
        self.root.bind("<KeyRelease-Shift_L>", lambda e: setattr(self, 'fast_forward', False))
        self.root.bind("<space>", lambda e: setattr(self, 'speed', 2.0 if self.speed == 1.0 else 1.0))

    def load_rom(self):
        rom_path = filedialog.askopenfilename(filetypes=[("NES files", "*.nes")])
        if rom_path:
            self.emulator.load_rom(rom_path)

    def key_press(self, event):
        if event.keysym in self.key_map:
            self.emulator.controller.buttons[self.key_map[event.keysym]] = True

    def key_release(self, event):
        if event.keysym in self.key_map:
            self.emulator.controller.buttons[self.key_map[event.keysym]] = False

    def toggle_fullscreen(self):
        self.root.attributes('-fullscreen', not self.root.attributes('-fullscreen'))

    def configure_input(self):
        config_window = tk.Toplevel(self.root)
        config_window.title("Configure Input")
        labels = ['A', 'B', 'Select', 'Start', 'Up', 'Down', 'Left', 'Right']
        for i, label in enumerate(labels):
            tk.Label(config_window, text=f"{label}:").grid(row=i, column=0)
            entry = tk.Entry(config_window)
            entry.grid(row=i, column=1)
            entry.insert(0, [k for k, v in self.key_map.items() if v == i][0])
            entry.bind("<KeyPress>", lambda e, idx=i, ent=entry: self.update_keymap(idx, e.keysym, ent))

    def update_keymap(self, button_idx, new_key, entry):
        if new_key:
            old_key = [k for k, v in self.key_map.items() if v == button_idx][0]
            self.root.unbind(f"<KeyPress-{old_key}>")
            self.root.unbind(f"<KeyRelease-{old_key}>")
            self.key_map[new_key] = self.key_map.pop(old_key)
            self.root.bind(f"<KeyPress-{new_key}>", self.key_press)
            self.root.bind(f"<KeyRelease-{new_key}>", self.key_release)
            entry.delete(0, tk.END)
            entry.insert(0, new_key)

    def apply_cheat(self):
        cheat = tk.simpledialog.askstring("Cheat", "Enter Game Genie code (e.g., AAAAAAAA):")
        if cheat and len(cheat) == 8:
            gg_map = 'APZLGITYEOXUKSVN'
            value = 0
            for c in cheat.upper():
                value = (value << 4) | gg_map.index(c)
            addr = ((value >> 8) & 0x7FFF) | 0x8000
            data = value & 0xFF
            self.emulator.cheats[addr] = data
            messagebox.showinfo("Cheat", f"Applied cheat at 0x{addr:04X}: 0x{data:02X}")

    def update_frame(self):
        if self.emulator.loaded_rom:
            self.emulator.step_frame()
            surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            for i, (r, g, b) in enumerate(self.emulator.ppu.framebuffer):
                x, y = i % SCREEN_WIDTH, i // SCREEN_WIDTH
                surface.set_at((x, y), (r, g, b))
            img = Image.frombytes('RGB', (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.image.tostring(surface, 'RGB'))
            img = img.resize((SCREEN_WIDTH*2, SCREEN_HEIGHT*2), Image.NEAREST)
            self.photo = ImageTk.PhotoImage(img)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        delay = int(16 / (self.speed * (2.0 if self.fast_forward else 1.0)))
        self.root.after(delay, self.update_frame)

    def quit(self):
        if self.emulator.loaded_rom and self.emulator.cpu.battery:
            rom_path = filedialog.askopenfilename(filetypes=[("NES files", "*.nes")])
            if rom_path:
                with open(f"{rom_path}.sav", 'wb') as f:
                    f.write(self.emulator.cpu.sram)
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = NESEmulatorApp(root)
    root.mainloop()

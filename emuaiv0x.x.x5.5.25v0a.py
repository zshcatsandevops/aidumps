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
import time
import struct
import array
import math
import random

# NES Constants
SCREEN_WIDTH = 256
SCREEN_HEIGHT = 240
NES_PPU_ADDR = 0x2000
NES_RAM_SIZE = 0x0800
NES_PRG_ROM_OFFSET = 0x8000
NES_APU_REGISTERS = 0x4000
NES_CONTROLLER_REGISTERS = 0x4016
NES_FRAME_RATE = 60
NES_CPU_CLOCK = 1789773
NES_PPU_CLOCK = 5369318
NES_APU_FRAME_COUNTER = 240

class MOS6502:
    """Simulates the MOS 6502 CPU with NES-specific features"""
    def __init__(self):
        self.a = 0
        self.x = 0
        self.y = 0
        self.pc = 0
        self.sp = 0xFD
        self.status = 0x24
        self.memory = bytearray(0x10000)
        self.cycle = 0
        self.ram = bytearray(0x800)
        self.interrupt = None
        self.nmi_pending = False
        self.irq_pending = False
        self.stall = 0
        # NES-specific
        self.ppu = None
        self.apu = None
        self.mapper = None
        self.controllers = [Controller(), Controller()]
        self.dma_cycle = 0
        self.dma_page = 0
        self.dma_addr = 0
        self.dma_data = 0
        self.dma_dummy = True
        self.odd_cycle = False
        self.cycle_steal = 0
        self.cycle_steal_cycle = 0

    def reset(self):
        self.a = 0
        self.x = 0
        self.y = 0
        self.pc = 0
        self.sp = 0xFD
        self.status = 0x24
        self.cycle = 0
        self.interrupt = None
        self.nmi_pending = False
        self.irq_pending = False
        self.stall = 0
        self.dma_cycle = 0
        self.dma_page = 0
        self.dma_addr = 0
        self.dma_data = 0
        self.dma_dummy = True
        self.odd_cycle = False
        self.cycle_steal = 0
        self.cycle_steal_cycle = 0
        self.pc = self.read_word(0xFFFC)

    def load_rom(self, rom_data):
        try:
            if len(rom_data) < 16 or rom_data[0:4] != b'NES\x1a':
                raise ValueError("Invalid NES file format")
            
            prg_rom_size = rom_data[4] * 0x4000
            chr_rom_size = rom_data[5] * 0x2000
            flags6 = rom_rom_data[6]
            flags7 = rom_rom_data[7]
            mapper = ((flags7 & 0xF0) << 4) | (flags6 >> 4)
            mirroring = flags6 & 0x1
            battery = (flags6 & 0x2) != 0
            trainer = (flags6 & 0x4) != 0
            four_screen = (flags6 & 0x8) != 0
            
            prg_start = 16 + (512 if trainer else 0)
            chr_start = prg_start + prg_rom_size
            
            self.mapper = Mapper.create(mapper, rom_data[prg_start:prg_start+prg_rom_size], 
                                      rom_data[chr_start:chr_start+chr_rom_size] if chr_rom_size > 0 else None, 
                                      battery, mirroring, four_screen)
            self.mapper.load(self.memory, self.ram)
            self.pc = self.read_word(0xFFFC)
        except Exception as e:
            raise ValueError(f"Failed to load ROM: {str(e)}")

    def read_byte(self, addr):
        if addr < 0x2000:
            return self.ram[addr % 0x800]
        elif 0x2000 <= addr < 0x4000:
            return self.ppu.read_register(addr % 8)
        elif addr == 0x4016:
            return self.controllers[0].read()
        elif addr == 0x4017:
            return self.controllers[1].read()
        elif 0x4000 <= addr < 0x4018:
            return self.apu.read_register(addr)
        elif 0x4018 <= addr < 0x4020:
            return 0  # Test mode registers
        elif 0x4020 <= addr < 0x6000:
            return 0  # Expansion ROM
        elif 0x6000 <= addr < 0x8000:
            return self.mapper.read_ram(addr)
        else:
            return self.mapper.read_prg(addr)

    def write_byte(self, addr, value):
        if addr < 0x2000:
            self.ram[addr % 0x800] = value
        elif 0x2000 <= addr < 0x4000:
            self.ppu.write_register(addr % 8, value)
        elif addr == 0x4014:
            self.dma_page = value
            self.dma_addr = 0
            self.dma_cycle = 0
            self.dma_dummy = True
            self.stall = 513
        elif addr == 0x4016:
            self.controllers[0].write(value)
            self.controllers[1].write(value)
        elif 0x4000 <= addr < 0x4018:
            self.apu.write_register(addr, value)
        elif 0x4018 <= addr < 0x4020:
            pass  # Test mode registers
        elif 0x4020 <= addr < 0x6000:
            pass  # Expansion ROM
        elif 0x6000 <= addr < 0x8000:
            self.mapper.write_ram(addr, value)
        else:
            self.mapper.write_prg(addr, value)

    def read_word(self, addr):
        return self.read_byte(addr) | (self.read_byte(addr + 1) << 8)

    def push_byte(self, value):
        self.write_byte(0x100 + self.sp, value)
        self.sp = (self.sp - 1) & 0xFF

    def pop_byte(self):
        self.sp = (self.sp + 1) & 0xFF
        return self.read_byte(0x100 + self.sp)

    def set_flag(self, flag, value):
        if value:
            self.status |= (1 << flag)
        else:
            self.status &= ~(1 << flag)

    def get_flag(self, flag):
        return (self.status >> flag) & 1

    def handle_nmi(self):
        self.push_byte((self.pc >> 8) & 0xFF)
        self.push_byte(self.pc & 0xFF)
        self.push_byte(self.status | 0x20)
        self.set_flag(3, False)
        self.pc = self.read_word(0xFFFA)
        self.cycle += 7

    def handle_irq(self):
        self.push_byte((self.pc >>

import tkinter as tk
from tkinter import filedialog, messagebox, font as tkFont
import os
import time
import numpy as np
from PIL import Image, ImageTk
import threading

# Constants for NES hardware
NES_WIDTH = 256
NES_HEIGHT = 240
CPU_CLOCK_SPEED = 1789773  # ~1.79 MHz
FRAME_RATE = 60.0
CPU_CYCLES_PER_FRAME = CPU_CLOCK_SPEED // FRAME_RATE

# Memory Map Constants
RAM_SIZE = 0x800               # 2KB internal RAM
VRAM_SIZE = 0x1000             # 4KB Video RAM
OAM_SIZE = 0x100               # 256 bytes Object Attribute Memory
CPU_RAM_START = 0x0000
CPU_RAM_MIRROR_END = 0x1FFF
PPU_REGISTERS_START = 0x2000
PPU_REGISTERS_MIRROR_END = 0x3FFF
APU_IO_REGISTERS_START = 0x4000
APU_IO_REGISTERS_END = 0x4017
CARTRIDGE_SPACE_START = 0x4020
CARTRIDGE_SPACE_END = 0xFFFF

# PPU Memory Map Constants
PATTERN_TABLES_START = 0x0000
PATTERN_TABLES_END = 0x1FFF
NAMETABLES_START = 0x2000
NAMETABLES_END = 0x3EFF
PALETTES_START = 0x3F00
PALETTES_END = 0x3FFF

# iNES Header Constants
INES_HEADER_SIZE = 16
PRG_ROM_PAGE_SIZE = 16384     # 16KB
CHR_ROM_PAGE_SIZE = 8192      # 8KB

# Color palette for NES (simplified to RGB values)
NES_PALETTE = [
    (84, 84, 84), (0, 30, 116), (8, 16, 144), (48, 0, 136), (68, 0, 100), (92, 0, 48), (84, 4, 0), (60, 24, 0),
    (32, 42, 0), (8, 58, 0), (0, 64, 0), (0, 60, 0), (0, 50, 60), (0, 0, 0), (0, 0, 0), (0, 0, 0),
    (152, 150, 152), (8, 76, 196), (48, 50, 236), (92, 30, 228), (136, 20, 176), (160, 20, 100), (152, 34, 32), (120, 60, 0),
    (84, 90, 0), (40, 114, 0), (8, 124, 0), (0, 118, 40), (0, 102, 120), (0, 0, 0), (0, 0, 0), (0, 0, 0),
    (236, 238, 236), (76, 154, 236), (120, 124, 236), (176, 98, 236), (228, 84, 236), (236, 88, 180), (236, 106, 100), (212, 136, 32),
    (160, 170, 0), (116, 196, 0), (76, 208, 32), (56, 204, 108), (56, 180, 204), (60, 60, 60), (0, 0, 0), (0, 0, 0),
    (236, 238, 236), (168, 204, 236), (188, 188, 236), (212, 178, 236), (236, 174, 236), (236, 174, 212), (236, 180, 176), (228, 196, 144),
    (204, 210, 120), (180, 222, 120), (168, 226, 144), (152, 226, 180), (160, 214, 228), (160, 162, 160), (0, 0, 0), (0, 0, 0)
]

class CPURegisters:
    """Represents the 6502 CPU registers used in the NES."""
    def __init__(self):
        self.A = 0x00         # Accumulator
        self.X = 0x00         # X Index
        self.Y = 0x00         # Y Index
        self.SP = 0xFD        # Stack Pointer (starts at 0xFD on power-up)
        self.PC = 0x0000      # Program Counter
        
        # Status Register flags (as individual booleans for clarity)
        self.C = False  # Carry Flag
        self.Z = False  # Zero Flag
        self.I = True   # Interrupt Disable (starts as True on power-up)
        self.D = False  # Decimal Mode (not used in NES, but part of 6502)
        self.B = False  # Break Command
        self.V = False  # Overflow Flag
        self.N = False  # Negative Flag
        
    def get_status(self):
        """Returns the status register as a byte."""
        status = 0
        if self.C: status |= 0x01
        if self.Z: status |= 0x02
        if self.I: status |= 0x04
        if self.D: status |= 0x08
        if self.B: status |= 0x10
        status |= 0x20  # Unused bit, always 1
        if self.V: status |= 0x40
        if self.N: status |= 0x80
        return status
    
    def set_status(self, value):
        """Sets the status register from a byte."""
        self.C = bool(value & 0x01)
        self.Z = bool(value & 0x02)
        self.I = bool(value & 0x04)
        self.D = bool(value & 0x08)
        self.B = bool(value & 0x10)
        # Bit 5 is unused
        self.V = bool(value & 0x40)
        self.N = bool(value & 0x80)

class Mapper:
    """Base class for NES cartridge mappers."""
    def __init__(self, rom_data, prg_rom_size, chr_rom_size):
        self.rom_data = rom_data
        self.prg_rom_size = prg_rom_size
        self.chr_rom_size = chr_rom_size
        self.prg_rom = rom_data[INES_HEADER_SIZE:INES_HEADER_SIZE+prg_rom_size]
        
        # If CHR ROM exists, extract it, otherwise create CHR RAM
        if chr_rom_size > 0:
            self.chr_rom = rom_data[INES_HEADER_SIZE+prg_rom_size:INES_HEADER_SIZE+prg_rom_size+chr_rom_size]
            self.uses_chr_ram = False
        else:
            self.chr_rom = bytearray(8192)  # 8KB of CHR RAM
            self.uses_chr_ram = True
            
    def read_prg_rom(self, address):
        """Read from PRG ROM space, implementing mapper-specific behavior."""
        # Default implementation: mirror if needed (for smaller ROMs)
        addr = address % self.prg_rom_size
        return self.prg_rom[addr]
    
    def write_prg_rom(self, address, value):
        """Write to PRG ROM space, implementing mapper-specific behavior."""
        # By default, PRG ROM is read-only. Mappers can override this.
        pass
    
    def read_chr(self, address):
        """Read from CHR ROM/RAM, implementing mapper-specific behavior."""
        addr = address % (len(self.chr_rom))
        return self.chr_rom[addr]
    
    def write_chr(self, address, value):
        """Write to CHR ROM/RAM, implementing mapper-specific behavior."""
        # Only allow writing if using CHR RAM
        if self.uses_chr_ram:
            addr = address % (len(self.chr_rom))
            self.chr_rom[addr] = value

class Mapper0(Mapper):
    """NROM Mapper (0): No memory mapping, just direct access."""
    def __init__(self, rom_data, prg_rom_size, chr_rom_size):
        super().__init__(rom_data, prg_rom_size, chr_rom_size)
    
    def read_prg_rom(self, address):
        # Map 0x8000-0xFFFF to PRG ROM, mirroring if necessary
        addr = (address - 0x8000) % self.prg_rom_size
        return self.prg_rom[addr]

class Memory:
    """Emulates the NES memory system including RAM, ROM, and memory-mapped registers."""
    def __init__(self, nes_system):
        self.nes_system = nes_system
        self.ram = bytearray(RAM_SIZE)  # 2KB internal RAM
        self.mapper = None  # Set by NESSystem when ROM is loaded
    
    def read(self, address):
        """Read a byte from memory at the specified address."""
        # Internal RAM (0x0000-0x1FFF), mirrored every 0x800 bytes
        if address <= CPU_RAM_MIRROR_END:
            return self.ram[address % RAM_SIZE]
        
        # PPU registers (0x2000-0x3FFF), mirrored every 8 bytes
        elif address <= PPU_REGISTERS_MIRROR_END:
            return self.nes_system.ppu.read_register((address - 0x2000) % 8 + 0x2000)
        
        # APU and I/O registers (0x4000-0x4017)
        elif address <= APU_IO_REGISTERS_END:
            # APU registers
            if address <= 0x4013 or address == 0x4015:
                return self.nes_system.apu.read_register(address)
            # Controller 1 and 2 (0x4016-0x4017)
            elif address in (0x4016, 0x4017):
                return self.nes_system.read_controller(address - 0x4016)
            else:
                return 0
        
        # Cartridge space
        elif address >= 0x4020 and address <= 0xFFFF:
            if self.mapper:
                return self.mapper.read_prg_rom(address)
            return 0
            
        # Unmapped space
        return 0
    
    def write(self, address, value):
        """Write a byte to memory at the specified address."""
        # Ensure value is a byte
        value = value & 0xFF
        
        # Internal RAM (0x0000-0x1FFF), mirrored every 0x800 bytes
        if address <= CPU_RAM_MIRROR_END:
            self.ram[address % RAM_SIZE] = value
        
        # PPU registers (0x2000-0x3FFF), mirrored every 8 bytes
        elif address <= PPU_REGISTERS_MIRROR_END:
            self.nes_system.ppu.write_register((address - 0x2000) % 8 + 0x2000, value)
        
        # APU and I/O registers (0x4000-0x4017)
        elif address <= APU_IO_REGISTERS_END:
            # APU registers
            if address <= 0x4013 or address == 0x4015:
                self.nes_system.apu.write_register(address, value)
            # OAM DMA (0x4014)
            elif address == 0x4014:
                self.nes_system.ppu.do_oam_dma(value)
            # Controller 1 and 2 (0x4016-0x4017)
            elif address == 0x4016:
                self.nes_system.write_controller_strobe(value)
        
        # Cartridge space
        elif address >= 0x4020 and address <= 0xFFFF:
            if self.mapper:
                self.mapper.write_prg_rom(address, value)

class CPU:
    """Emulates the NES 6502 CPU."""
    def __init__(self, nes_system):
        self.nes_system = nes_system
        self.registers = CPURegisters()
        self.cycles = 0  # Track CPU cycles for timing
        
        # CPU instruction lookup tables
        self.opcodes = self._build_opcode_table()
        self.addressing_modes = self._build_addressing_mode_table()
        
        self.nmi_pending = False
        self.irq_pending = False
        self.stall_cycles = 0  # For DMA and other operations that stall the CPU
        
    def _build_opcode_table(self):
        """Build the opcode table mapping instruction codes to implementations."""
        opcodes = {}
        
        # LDA (Load Accumulator)
        opcodes[0xA9] = (self._LDA, "immediate", 2)  # Immediate
        opcodes[0xA5] = (self._LDA, "zeropage", 3)   # Zero Page
        opcodes[0xB5] = (self._LDA, "zeropage_x", 4) # Zero Page,X
        opcodes[0xAD] = (self._LDA, "absolute", 4)   # Absolute
        opcodes[0xBD] = (self._LDA, "absolute_x", 4) # Absolute,X (+1 if page crossed)
        opcodes[0xB9] = (self._LDA, "absolute_y", 4) # Absolute,Y (+1 if page crossed)
        opcodes[0xA1] = (self._LDA, "indirect_x", 6) # (Indirect,X)
        opcodes[0xB1] = (self._LDA, "indirect_y", 5) # (Indirect),Y (+1 if page crossed)
        
        # LDX (Load X Register)
        opcodes[0xA2] = (self._LDX, "immediate", 2)  # Immediate
        opcodes[0xA6] = (self._LDX, "zeropage", 3)   # Zero Page
        opcodes[0xB6] = (self._LDX, "zeropage_y", 4) # Zero Page,Y
        opcodes[0xAE] = (self._LDX, "absolute", 4)   # Absolute
        opcodes[0xBE] = (self._LDX, "absolute_y", 4) # Absolute,Y (+1 if page crossed)
        
        # LDY (Load Y Register)
        opcodes[0xA0] = (self._LDY, "immediate", 2)  # Immediate
        opcodes[0xA4] = (self._LDY, "zeropage", 3)   # Zero Page
        opcodes[0xB4] = (self._LDY, "zeropage_x", 4) # Zero Page,X
        opcodes[0xAC] = (self._LDY, "absolute", 4)   # Absolute
        opcodes[0xBC] = (self._LDY, "absolute_x", 4) # Absolute,X (+1 if page crossed)
        
        # STA (Store Accumulator)
        opcodes[0x85] = (self._STA, "zeropage", 3)   # Zero Page
        opcodes[0x95] = (self._STA, "zeropage_x", 4) # Zero Page,X
        opcodes[0x8D] = (self._STA, "absolute", 4)   # Absolute
        opcodes[0x9D] = (self._STA, "absolute_x", 5) # Absolute,X
        opcodes[0x99] = (self._STA, "absolute_y", 5) # Absolute,Y
        opcodes[0x81] = (self._STA, "indirect_x", 6) # (Indirect,X)
        opcodes[0x91] = (self._STA, "indirect_y", 6) # (Indirect),Y
        
        # STX (Store X Register)
        opcodes[0x86] = (self._STX, "zeropage", 3)   # Zero Page
        opcodes[0x96] = (self._STX, "zeropage_y", 4) # Zero Page,Y
        opcodes[0x8E] = (self._STX, "absolute", 4)   # Absolute
        
        # STY (Store Y Register)
        opcodes[0x84] = (self._STY, "zeropage", 3)   # Zero Page
        opcodes[0x94] = (self._STY, "zeropage_x", 4) # Zero Page,X
        opcodes[0x8C] = (self._STY, "absolute", 4)   # Absolute
        
        # JMP (Jump)
        opcodes[0x4C] = (self._JMP, "absolute", 3)   # Absolute
        opcodes[0x6C] = (self._JMP, "indirect", 5)   # Indirect
        
        # JSR (Jump to Subroutine)
        opcodes[0x20] = (self._JSR, "absolute", 6)   # Absolute
        
        # RTS (Return from Subroutine)
        opcodes[0x60] = (self._RTS, "implied", 6)    # Implied
        
        # Branches
        opcodes[0x90] = (self._BCC, "relative", 2)   # BCC (Branch if Carry Clear)
        opcodes[0xB0] = (self._BCS, "relative", 2)   # BCS (Branch if Carry Set)
        opcodes[0xF0] = (self._BEQ, "relative", 2)   # BEQ (Branch if Equal)
        opcodes[0x30] = (self._BMI, "relative", 2)   # BMI (Branch if Minus)
        opcodes[0xD0] = (self._BNE, "relative", 2)   # BNE (Branch if Not Equal)
        opcodes[0x10] = (self._BPL, "relative", 2)   # BPL (Branch if Plus)
        opcodes[0x50] = (self._BVC, "relative", 2)   # BVC (Branch if Overflow Clear)
        opcodes[0x70] = (self._BVS, "relative", 2)   # BVS (Branch if Overflow Set)
        
        # Status Register Operations
        opcodes[0x18] = (self._CLC, "implied", 2)    # CLC (Clear Carry Flag)
        opcodes[0xD8] = (self._CLD, "implied", 2)    # CLD (Clear Decimal Mode)
        opcodes[0x58] = (self._CLI, "implied", 2)    # CLI (Clear Interrupt Disable)
        opcodes[0xB8] = (self._CLV, "implied", 2)    # CLV (Clear Overflow Flag)
        opcodes[0x38] = (self._SEC, "implied", 2)    # SEC (Set Carry Flag)
        opcodes[0xF8] = (self._SED, "implied", 2)    # SED (Set Decimal Flag)
        opcodes[0x78] = (self._SEI, "implied", 2)    # SEI (Set Interrupt Disable)
        
        # Stack Operations
        opcodes[0x9A] = (self._TXS, "implied", 2)    # TXS (Transfer X to Stack Pointer)
        opcodes[0xBA] = (self._TSX, "implied", 2)    # TSX (Transfer Stack Pointer to X)
        opcodes[0x48] = (self._PHA, "implied", 3)    # PHA (Push Accumulator)
        opcodes[0x68] = (self._PLA, "implied", 4)    # PLA (Pull Accumulator)
        opcodes[0x08] = (self._PHP, "implied", 3)    # PHP (Push Processor Status)
        opcodes[0x28] = (self._PLP, "implied", 4)    # PLP (Pull Processor Status)
        
        # Register Transfers
        opcodes[0xAA] = (self._TAX, "implied", 2)    # TAX (Transfer A to X)
        opcodes[0x8A] = (self._TXA, "implied", 2)    # TXA (Transfer X to A)
        opcodes[0xA8] = (self._TAY, "implied", 2)    # TAY (Transfer A to Y)
        opcodes[0x98] = (self._TYA, "implied", 2)    # TYA (Transfer Y to A)
        
        # Arithmetic Operations
        opcodes[0x69] = (self._ADC, "immediate", 2)  # ADC (Add with Carry) - Immediate
        opcodes[0x65] = (self._ADC, "zeropage", 3)   # Zero Page
        opcodes[0x75] = (self._ADC, "zeropage_x", 4) # Zero Page,X
        opcodes[0x6D] = (self._ADC, "absolute", 4)   # Absolute
        opcodes[0x7D] = (self._ADC, "absolute_x", 4) # Absolute,X (+1 if page crossed)
        opcodes[0x79] = (self._ADC, "absolute_y", 4) # Absolute,Y (+1 if page crossed)
        opcodes[0x61] = (self._ADC, "indirect_x", 6) # (Indirect,X)
        opcodes[0x71] = (self._ADC, "indirect_y", 5) # (Indirect),Y (+1 if page crossed)
        
        opcodes[0xE9] = (self._SBC, "immediate", 2)  # SBC (Subtract with Carry) - Immediate
        opcodes[0xE5] = (self._SBC, "zeropage", 3)   # Zero Page
        opcodes[0xF5] = (self._SBC, "zeropage_x", 4) # Zero Page,X
        opcodes[0xED] = (self._SBC, "absolute", 4)   # Absolute
        opcodes[0xFD] = (self._SBC, "absolute_x", 4) # Absolute,X (+1 if page crossed)
        opcodes[0xF9] = (self._SBC, "absolute_y", 4) # Absolute,Y (+1 if page crossed)
        opcodes[0xE1] = (self._SBC, "indirect_x", 6) # (Indirect,X)
        opcodes[0xF1] = (self._SBC, "indirect_y", 5) # (Indirect),Y (+1 if page crossed)
        
        # Bitwise Operations
        opcodes[0x29] = (self._AND, "immediate", 2)  # AND - Immediate
        opcodes[0x25] = (self._AND, "zeropage", 3)   # Zero Page
        opcodes[0x35] = (self._AND, "zeropage_x", 4) # Zero Page,X
        opcodes[0x2D] = (self._AND, "absolute", 4)   # Absolute
        opcodes[0x3D] = (self._AND, "absolute_x", 4) # Absolute,X (+1 if page crossed)
        opcodes[0x39] = (self._AND, "absolute_y", 4) # Absolute,Y (+1 if page crossed)
        opcodes[0x21] = (self._AND, "indirect_x", 6) # (Indirect,X)
        opcodes[0x31] = (self._AND, "indirect_y", 5) # (Indirect),Y (+1 if page crossed)
        
        opcodes[0x09] = (self._ORA, "immediate", 2)  # ORA - Immediate
        opcodes[0x05] = (self._ORA, "zeropage", 3)   # Zero Page
        opcodes[0x15] = (self._ORA, "zeropage_x", 4) # Zero Page,X
        opcodes[0x0D] = (self._ORA, "absolute", 4)   # Absolute
        opcodes[0x1D] = (self._ORA, "absolute_x", 4) # Absolute,X (+1 if page crossed)
        opcodes[0x19] = (self._ORA, "absolute_y", 4) # Absolute,Y (+1 if page crossed)
        opcodes[0x01] = (self._ORA, "indirect_x", 6) # (Indirect,X)
        opcodes[0x11] = (self._ORA, "indirect_y", 5) # (Indirect),Y (+1 if page crossed)
        
        opcodes[0x49] = (self._EOR, "immediate", 2)  # EOR - Immediate
        opcodes[0x45] = (self._EOR, "zeropage", 3)   # Zero Page
        opcodes[0x55] = (self._EOR, "zeropage_x", 4) # Zero Page,X
        opcodes[0x4D] = (self._EOR, "absolute", 4)   # Absolute
        opcodes[0x5D] = (self._EOR, "absolute_x", 4) # Absolute,X (+1 if page crossed)
        opcodes[0x59] = (self._EOR, "absolute_y", 4) # Absolute,Y (+1 if page crossed)
        opcodes[0x41] = (self._EOR, "indirect_x", 6) # (Indirect,X)
        opcodes[0x51] = (self._EOR, "indirect_y", 5) # (Indirect),Y (+1 if page crossed)
        
        # Bit Test
        opcodes[0x24] = (self._BIT, "zeropage", 3)   # BIT - Zero Page
        opcodes[0x2C] = (self._BIT, "absolute", 4)   # Absolute
        
        # Compare Operations
        opcodes[0xC9] = (self._CMP, "immediate", 2)  # CMP - Immediate
        opcodes[0xC5] = (self._CMP, "zeropage", 3)   # Zero Page
        opcodes[0xD5] = (self._CMP, "zeropage_x", 4) # Zero Page,X
        opcodes[0xCD] = (self._CMP, "absolute", 4)   # Absolute
        opcodes[0xDD] = (self._CMP, "absolute_x", 4) # Absolute,X (+1 if page crossed)
        opcodes[0xD9] = (self._CMP, "absolute_y", 4) # Absolute,Y (+1 if page crossed)
        opcodes[0xC1] = (self._CMP, "indirect_x", 6) # (Indirect,X)
        opcodes[0xD1] = (self._CMP, "indirect_y", 5) # (Indirect),Y (+1 if page crossed)
        
        opcodes[0xE0] = (self._CPX, "immediate", 2)  # CPX - Immediate
        opcodes[0xE4] = (self._CPX, "zeropage", 3)   # Zero Page
        opcodes[0xEC] = (self._CPX, "absolute", 4)   # Absolute
        
        opcodes[0xC0] = (self._CPY, "immediate", 2)  # CPY - Immediate
        opcodes[0xC4] = (self._CPY, "zeropage", 3)   # Zero Page
        opcodes[0xCC] = (self._CPY, "absolute", 4)   # Absolute
        
        # Increment/Decrement Operations
        opcodes[0xE6] = (self._INC, "zeropage", 5)   # INC - Zero Page
        opcodes[0xF6] = (self._INC, "zeropage_x", 6) # Zero Page,X
        opcodes[0xEE] = (self._INC, "absolute", 6)   # Absolute
        opcodes[0xFE] = (self._INC, "absolute_x", 7) # Absolute,X
        
        opcodes[0xC6] = (self._DEC, "zeropage", 5)   # DEC - Zero Page
        opcodes[0xD6] = (self._DEC, "zeropage_x", 6) # Zero Page,X
        opcodes[0xCE] = (self._DEC, "absolute", 6)   # Absolute
        opcodes[0xDE] = (self._DEC, "absolute_x", 7) # Absolute,X
        
        opcodes[0xE8] = (self._INX, "implied", 2)    # INX - Implied
        opcodes[0xC8] = (self._INY, "implied", 2)    # INY - Implied
        opcodes[0xCA] = (self._DEX, "implied", 2)    # DEX - Implied
        opcodes[0x88] = (self._DEY, "implied", 2)    # DEY - Implied
        
        # Shift and Rotate Operations
        opcodes[0x0A] = (self._ASL_acc, "accumulator", 2) # ASL - Accumulator
        opcodes[0x06] = (self._ASL, "zeropage", 5)   # Zero Page
        opcodes[0x16] = (self._ASL, "zeropage_x", 6) # Zero Page,X
        opcodes[0x0E] = (self._ASL, "absolute", 6)   # Absolute
        opcodes[0x1E] = (self._ASL, "absolute_x", 7) # Absolute,X
        
        opcodes[0x4A] = (self._LSR_acc, "accumulator", 2) # LSR - Accumulator
        opcodes[0x46] = (self._LSR, "zeropage", 5)   # Zero Page
        opcodes[0x56] = (self._LSR, "zeropage_x", 6) # Zero Page,X
        opcodes[0x4E] = (self._LSR, "absolute", 6)   # Absolute
        opcodes[0x5E] = (self._LSR, "absolute_x", 7) # Absolute,X
        
        opcodes[0x2A] = (self._ROL_acc, "accumulator", 2) # ROL - Accumulator
        opcodes[0x26] = (self._ROL, "zeropage", 5)   # Zero Page
        opcodes[0x36] = (self._ROL, "zeropage_x", 6) # Zero Page,X
        opcodes[0x2E] = (self._ROL, "absolute", 6)   # Absolute
        opcodes[0x3E] = (self._ROL, "absolute_x", 7) # Absolute,X
        
        opcodes[0x6A] = (self._ROR_acc, "accumulator", 2) # ROR - Accumulator
        opcodes[0x66] = (self._ROR, "zeropage", 5)   # Zero Page
        opcodes[0x76] = (self._ROR, "zeropage_x", 6) # Zero Page,X
        opcodes[0x6E] = (self._ROR, "absolute", 6)   # Absolute
        opcodes[0x7E] = (self._ROR, "absolute_x", 7) # Absolute,X
        
        # System Operations
        opcodes[0x00] = (self._BRK, "implied", 7)    # BRK (Force Interrupt)
        opcodes[0x40] = (self._RTI, "implied", 6)    # RTI (Return from Interrupt)
        opcodes[0xEA] = (self._NOP, "implied", 2)    # NOP (No Operation)
        
        # Undocumented/Illegal opcodes often found in real NES games
        # Implementing the most common ones used in games
        opcodes[0x1A] = (self._NOP, "implied", 2)    # NOP (undocumented)
        opcodes[0x3A] = (self._NOP, "implied", 2)    # NOP (undocumented)
        opcodes[0x5A] = (self._NOP, "implied", 2)    # NOP (undocumented)
        opcodes[0x7A] = (self._NOP, "implied", 2)    # NOP (undocumented)
        opcodes[0xDA] = (self._NOP, "implied", 2)    # NOP (undocumented)
        opcodes[0xFA] = (self._NOP, "implied", 2)    # NOP (undocumented)
        
        return opcodes
        
    def _build_addressing_mode_table(self):
        """Build the table of addressing mode implementations."""
        modes = {
            "implied": self._addr_implied,
            "accumulator": self._addr_accumulator,
            "immediate": self._addr_immediate,
            "zeropage": self._addr_zeropage,
            "zeropage_x": self._addr_zeropage_x,
            "zeropage_y": self._addr_zeropage_y,
            "relative": self._addr_relative,
            "absolute": self._addr_absolute,
            "absolute_x": self._addr_absolute_x,
            "absolute_y": self._addr_absolute_y,
            "indirect": self._addr_indirect,
            "indirect_x": self._addr_indirect_x,
            "indirect_y": self._addr_indirect_y
        }
        return modes
    
    # Addressing Modes
    def _addr_implied(self):
        """Implied addressing mode."""
        return None, 0
    
    def _addr_accumulator(self):
        """Accumulator addressing mode."""
        return None, 0
    
    def _addr_immediate(self):
        """Immediate addressing mode."""
        address = self.registers.PC
        self.registers.PC += 1
        return address, 0
    
    def _addr_zeropage(self):
        """Zero page addressing mode."""
        address = self.read_memory(self.registers.PC)
        self.registers.PC += 1
        return address, 0
    
    def _addr_zeropage_x(self):
        """Zero page with X offset addressing mode."""
        address = (self.read_memory(self.registers.PC) + self.registers.X) & 0xFF
        self.registers.PC += 1
        return address, 0
    
    def _addr_zeropage_y(self):
        """Zero page with Y offset addressing mode."""
        address = (self.read_memory(self.registers.PC) + self.registers.Y) & 0xFF
        self.registers.PC += 1
        return address, 0
    
    def _addr_relative(self):
        """Relative addressing mode."""
        offset = self.read_memory(self.registers.PC)
        self.registers.PC += 1
        
        # Handle two's complement for negative offsets
        if offset < 0x80:
            return self.registers.PC + offset, 0
        else:
            return self.registers.PC + offset - 0x100, 0
    
    def _addr_absolute(self):
        """Absolute addressing mode."""
        low_byte = self.read_memory(self.registers.PC)
        self.registers.PC += 1
        high_byte = self.read_memory(self.registers.PC)
        self.registers.PC += 1
        address = (high_byte << 8) | low_byte
        return address, 0
    
    def _addr_absolute_x(self):
        """Absolute with X offset addressing mode."""
        low_byte = self.read_memory(self.registers.PC)
        self.registers.PC += 1
        high_byte = self.read_memory(self.registers.PC)
        self.registers.PC += 1
        
        base_address = (high_byte << 8) | low_byte
        address = (base_address + self.registers.X) & 0xFFFF
        
        # Return extra cycle cost if page boundary crossed
        page_crossed = (base_address & 0xFF00) != (address & 0xFF00)
        return address, 1 if page_crossed else 0
    
    def _addr_absolute_y(self):
        """Absolute with Y offset addressing mode."""
        low_byte = self.read_memory(self.registers.PC)
        self.registers.PC += 1
        high_byte = self.read_memory(self.registers.PC)
        self.registers.PC += 1
        
        base_address = (high_byte << 8) | low_byte
        address = (base_address + self.registers.Y) & 0xFFFF
        
        # Return extra cycle cost if page boundary crossed
        page_crossed = (base_address & 0xFF00) != (address & 0xFF00)
        return address, 1 if page_crossed else 0
    
    def _addr_indirect(self):
        """Indirect addressing mode."""
        low_byte = self.read_memory(self.registers.PC)
        self.registers.PC += 1
        high_byte = self.read_memory(self.registers.PC)
        self.registers.PC += 1
        
        ptr_address = (high_byte << 8) | low_byte
        
        # Simulate 6502 bug: if pointer is at the end of a page, high byte wraps within the same page
        if low_byte == 0xFF:
            # Page boundary bug: High byte comes from same page, not next page
            address = (self.read_memory((ptr_address & 0xFF00) | 0x00) << 8) | self.read_memory(ptr_address)
        else:
            address = (self.read_memory(ptr_address + 1) << 8) | self.read_memory(ptr_address)
            
        return address, 0
    
    def _addr_indirect_x(self):
        """Indirect with X offset addressing mode, aka (Indirect,X)."""
        zero_addr = self.read_memory(self.registers.PC)
        self.registers.PC += 1
        
        # Add X to zero page address (wrapping in zero page)
        ptr_address = (zero_addr + self.registers.X) & 0xFF
        
        # Read effective address from consecutive zero page addresses (with wrap-around)
        low_byte = self.read_memory(ptr_address)
        high_byte = self.read_memory((ptr_address + 1) & 0xFF)
        
        address = (high_byte << 8) | low_byte
        return address, 0
    
    def _addr_indirect_y(self):
        """Indirect with Y offset addressing mode, aka (Indirect),Y."""
        zero_addr = self.read_memory(self.registers.PC)
        self.registers.PC += 1
        
        # Read effective address from consecutive zero page addresses (with wrap-around)
        low_byte = self.read_memory(zero_addr)
        high_byte = self.read_memory((zero_addr + 1) & 0xFF)
        
        base_address = (high_byte << 8) | low_byte
        address = (base_address + self.registers.Y) & 0xFFFF
        
        # Return extra cycle cost if page boundary crossed
        page_crossed = (base_address & 0xFF00) != (address & 0xFF00)
        return address, 1 if page_crossed else 0
    
    # Instruction Implementations
    def _LDA(self, address):
        """Load Accumulator."""
        self.registers.A = self.read_memory(address)
        self.registers.Z = (self.registers.A == 0)
        self.registers.N = ((self.registers.A & 0x80) != 0)
    
    def _LDX(self, address):
        """Load X Register."""
        self.registers.X = self.read_memory(address)
        self.registers.Z = (self.registers.X == 0)
        self.registers.N = ((self.registers.X & 0x80) != 0)
    
    def _LDY(self, address):
        """Load Y Register."""
        self.registers.Y = self.read_memory(address)
        self.registers.Z = (self.registers.Y == 0)
        self.registers.N = ((self.registers.Y & 0x80) != 0)
    
    def _STA(self, address):
        """Store Accumulator."""
        self.write_memory(address, self.registers.A)
    
    def _STX(self, address):
        """Store X Register."""
        self.write_memory(address, self.registers.X)
    
    def _STY(self, address):
        """Store Y Register."""
        self.write_memory(address, self.registers.Y)
    
    def _TAX(self, _):
        """Transfer Accumulator to X."""
        self.registers.X = self.registers.A
        self.registers.Z = (self.registers.X == 0)
        self.registers.N = ((self.registers.X & 0x80) != 0)
    
    def _TAY(self, _):
        """Transfer Accumulator to Y."""
        self.registers.Y = self.registers.A
        self.registers.Z = (self.registers.Y == 0)
        self.registers.N = ((self.registers.Y & 0x80) != 0)
    
    def _TSX(self, _):
        """Transfer Stack Pointer to X."""
        self.registers.X = self.registers.SP
        self.registers.Z = (self.registers.X == 0)
        self.registers.N = ((self.registers.X & 0x80) != 0)
    
    def _TXA(self, _):
        """Transfer X to Accumulator."""
        self.registers.A = self.registers.X
        self.registers.Z = (self.registers.A == 0)
        self.registers.N = ((self.registers.A & 0x80) != 0)
    
    def _TXS(self, _):
        """Transfer X to Stack Pointer."""
        self.registers.SP = self.registers.X
        # Note: Does not affect status flags
    
    def _TYA(self, _):
        """Transfer Y to Accumulator."""
        self.registers.A = self.registers.Y
        self.registers.Z = (self.registers.A == 0)
        self.registers.N = ((self.registers.A & 0x80) != 0)
    
    def _ADC(self, address):
        """Add with Carry."""
        value = self.read_memory(address)
        result = self.registers.A + value + (1 if self.registers.C else 0)
        
        # Set carry flag if result overflows
        self.registers.C = (result > 0xFF)
        
        # Set overflow flag if the sign of result is different from both operands
        self.registers.V = ((self.registers.A ^ result) & (value ^ result) & 0x80) != 0
        
        self.registers.A = result & 0xFF
        self.registers.Z = (self.registers.A == 0)
        self.registers.N = ((self.registers.A & 0x80) != 0)
    
    def _AND(self, address):
        """Logical AND."""
        self.registers.A &= self.read_memory(address)
        self.registers.Z = (self.registers.A == 0)
        self.registers.N = ((self.registers.A & 0x80) != 0)
    
    def _ASL(self, address):
        """Arithmetic Shift Left (memory)."""
        value = self.read_memory(address)
        self.registers.C = ((value & 0x80) != 0)
        result = (value << 1) & 0xFF
        self.write_memory(address, result)
        self.registers.Z = (result == 0)
        self.registers.N = ((result & 0x80) != 0)
    
    def _ASL_acc(self, _):
        """Arithmetic Shift Left (accumulator)."""
        self.registers.C = ((self.registers.A & 0x80) != 0)
        self.registers.A = (self.registers.A << 1) & 0xFF
        self.registers.Z = (self.registers.A == 0)
        self.registers.N = ((self.registers.A & 0x80) != 0)
    
    def _BCC(self, address):
        """Branch if Carry Clear."""
        if not self.registers.C:
            old_pc = self.registers.PC
            self.registers.PC = address
            
            # Add 1 cycle if branch taken, add another if page boundary crossed
            return 1 + (1 if (old_pc & 0xFF00) != (address & 0xFF00) else 0)
        return 0
    
    def _BCS(self, address):
        """Branch if Carry Set."""
        if self.registers.C:
            old_pc = self.registers.PC
            self.registers.PC = address
            
            # Add 1 cycle if branch taken, add another if page boundary crossed
            return 1 + (1 if (old_pc & 0xFF00) != (address & 0xFF00) else 0)
        return 0
    
    def _BEQ(self, address):
        """Branch if Equal (Zero Set)."""
        if self.registers.Z:
            old_pc = self.registers.PC
            self.registers.PC = address
            
            # Add 1 cycle if branch taken, add another if page boundary crossed
            return 1 + (1 if (old_pc & 0xFF00) != (address & 0xFF00) else 0)
        return 0
    
    def _BIT(self, address):
        """Bit Test."""
        value = self.read_memory(address)
        result = self.registers.A & value
        
        self.registers.Z = (result == 0)
        self.registers.V = ((value & 0x40) != 0)
        self.registers.N = ((value & 0x80) != 0)
    
    def _BMI(self, address):
        """Branch if Minus (Negative Set)."""
        if self.registers.N:
            old_pc = self.registers.PC
            self.registers.PC = address
            
            # Add 1 cycle if branch taken, add another if page boundary crossed
            return 1 + (1 if (old_pc & 0xFF00) != (address & 0xFF00) else 0)
        return 0
    
    def _BNE(self, address):
        """Branch if Not Equal (Zero Clear)."""
        if not self.registers.Z:
            old_pc = self.registers.PC
            self.registers.PC = address
            
            # Add 1 cycle if branch taken, add another if page boundary crossed
            return 1 + (1 if (old_pc & 0xFF00) != (address & 0xFF00) else 0)
        return 0
    
    def _BPL(self, address):
        """Branch if Plus (Negative Clear)."""
        if not self.registers.N:
            old_pc = self.registers.PC
            self.registers.PC = address
            
            # Add 1 cycle if branch taken, add another if page boundary crossed
            return 1 + (1 if (old_pc & 0xFF00) != (address & 0xFF00) else 0)
        return 0
    
    def _BRK(self, _):
        """Force Interrupt (Break)."""
        # Increment PC before push (BRK is a 2-byte instruction though only 1 byte is encoded)
        self.registers.PC += 1
        
        # Push PC and status register to stack
        self.push_word(self.registers.PC)
        
        # Set break flag before pushing status
        self.registers.B = True
        self.push_byte(self.registers.get_status())
        self.registers.B = False  # Clear B flag after pushing
        
        # Set interrupt disable flag
        self.registers.I = True
        
        # Load interrupt vector
        self.registers.PC = self.read_word(0xFFFE)
    
    def _BVC(self, address):
        """Branch if Overflow Clear."""
        if not self.registers.V:
            old_pc = self.registers.PC
            self.registers.PC = address
            
            # Add 1 cycle if branch taken, add another if page boundary crossed
            return 1 + (1 if (old_pc & 0xFF00) != (address & 0xFF00) else 0)
        return 0
    
    def _BVS(self, address):
        """Branch if Overflow Set."""
        if self.registers.V:
            old_pc = self.registers.PC
            self.registers.PC = address
            
            # Add 1 cycle if branch taken, add another if page boundary crossed
            return 1 + (1 if (old_pc & 0xFF00) != (address & 0xFF00) else 0)
        return 0
    
    def _CLC(self, _):
        """Clear Carry Flag."""
        self.registers.C = False
    
    def _CLD(self, _):
        """Clear Decimal Mode Flag."""
        self.registers.D = False
    
    def _CLI(self, _):
        """Clear Interrupt Disable Flag."""
        self.registers.I = False
    
    def _CLV(self, _):
        """Clear Overflow Flag."""
        self.registers.V = False
    
    def _CMP(self, address):
        """Compare Accumulator."""
        value = self.read_memory(address)
        result = (self.registers.A - value) & 0xFF
        
        self.registers.C = (self.registers.A >= value)
        self.registers.Z = (result == 0)
        self.registers.N = ((result & 0x80) != 0)
    
    def _CPX(self, address):
        """Compare X Register."""
        value = self.read_memory(address)
        result = (self.registers.X - value) & 0xFF
        
        self.registers.C = (self.registers.X >= value)
        self.registers.Z = (result == 0)
        self.registers.N = ((result & 0x80) != 0)
    
    def _CPY(self, address):
        """Compare Y Register."""
        value = self.read_memory(address)
        result = (self.registers.Y - value) & 0xFF
        
        self.registers.C = (self.registers.Y >= value)
        self.registers.Z = (result == 0)
        self.registers.N = ((result & 0x80) != 0)
    
    def _DEC(self, address):
        """Decrement Memory."""
        value = (self.read_memory(address) - 1) & 0xFF
        self.write_memory(address, value)
        
        self.registers.Z = (value == 0)
        self.registers.N = ((value & 0x80) != 0)
    
    def _DEX(self, _):
        """Decrement X Register."""
        self.registers.X = (self.registers.X - 1) & 0xFF
        
        self.registers.Z = (self.registers.X == 0)
        self.registers.N = ((self.registers.X & 0x80) != 0)
    
    def _DEY(self, _):
        """Decrement Y Register."""
        self.registers.Y = (self.registers.Y - 1) & 0xFF
        
        self.registers.Z = (self.registers.Y == 0)
        self.registers.N = ((self.registers.Y & 0x80) != 0)
    
    def _EOR(self, address):
        """Exclusive OR."""
        self.registers.A ^= self.read_memory(address)
        
        self.registers.Z = (self.registers.A == 0)
        self.registers.N = ((self.registers.A & 0x80) != 0)
    
    def _INC(self, address):
        """Increment Memory."""
        value = (self.read_memory(address) + 1) & 0xFF
        self.write_memory(address, value)
        
        self.registers.Z = (value == 0)
        self.registers.N = ((value & 0x80) != 0)
    
    def _INX(self, _):
        """Increment X Register."""
        self.registers.X = (self.registers.X + 1) & 0xFF
        
        self.registers.Z = (self.registers.X == 0)
        self.registers.N = ((self.registers.X & 0x80) != 0)
    
    def _INY(self, _):
        """Increment Y Register."""
        self.registers.Y = (self.registers.Y + 1) & 0xFF
        
        self.registers.Z = (self.registers.Y == 0)
        self.registers.N = ((self.registers.Y & 0x80) != 0)
    
    def _JMP(self, address):
        """Jump to Address."""
        self.registers.PC = address
    
    def _JSR(self, address):
        """Jump to Subroutine."""
        # Push the address of the next instruction - 1 (return address)
        return_addr = self.registers.PC - 1
        self.push_word(return_addr)
        
        # Jump to subroutine
        self.registers.PC = address
    
    def _LSR(self, address):
        """Logical Shift Right (memory)."""
        value = self.read_memory(address)
        self.registers.C = ((value & 0x01) != 0)
        result = value >> 1
        self.write_memory(address, result)
        
        self.registers.Z = (result == 0)
        self.registers.N = False  # Bit 7 is always cleared
    
    def _LSR_acc(self, _):
        """Logical Shift Right (accumulator)."""
        self.registers.C = ((self.registers.A & 0x01) != 0)
        self.registers.A >>= 1
        
        self.registers.Z = (self.registers.A == 0)
        self.registers.N = False  # Bit 7 is always cleared
    
    def _NOP(self, _):
        """No Operation."""
        pass  # This instruction does nothing
    
    def _ORA(self, address):
        """Logical Inclusive OR."""
        self.registers.A |= self.read_memory(address)
        
        self.registers.Z = (self.registers.A == 0)
        self.registers.N = ((self.registers.A & 0x80) != 0)
    
    def _PHA(self, _):
        """Push Accumulator."""
        self.push_byte(self.registers.A)
    
    def _PHP(self, _):
        """Push Processor Status."""
        # Set Break flag before pushing
        self.registers.B = True
        self.push_byte(self.registers.get_status())
        self.registers.B = False  # Clear it after pushing
    
    def _PLA(self, _):
        """Pull Accumulator."""
        self.registers.A = self.pull_byte()
        
        self.registers.Z = (self.registers.A == 0)
        self.registers.N = ((self.registers.A & 0x80) != 0)
    
    def _PLP(self, _):
        """Pull Processor Status."""
        status = self.pull_byte()
        self.registers.set_status(status)
        # The B flag is not actually stored in the processor status register
        self.registers.B = False
    
    def _ROL(self, address):
        """Rotate Left (memory)."""
        value = self.read_memory(address)
        old_carry = 1 if self.registers.C else 0
        
        self.registers.C = ((value & 0x80) != 0)
        result = ((value << 1) | old_carry) & 0xFF
        self.write_memory(address, result)
        
        self.registers.Z = (result == 0)
        self.registers.N = ((result & 0x80) != 0)
    
    def _ROL_acc(self, _):
        """Rotate Left (accumulator)."""
        old_carry = 1 if self.registers.C else 0
        
        self.registers.C = ((self.registers.A & 0x80) != 0)
        self.registers.A = ((self.registers.A << 1) | old_carry) & 0xFF
        
        self.registers.Z = (self.registers.A == 0)
        self.registers.N = ((self.registers.A & 0x80) != 0)
    
    def _ROR(self, address):
        """Rotate Right (memory)."""
        value = self.read_memory(address)
        old_carry = 0x80 if self.registers.C else 0
        
        self.registers.C = ((value & 0x01) != 0)
        result = (value >> 1) | old_carry
        self.write_memory(address, result)
        
        self.registers.Z = (result == 0)
        self.registers.N = ((result & 0x80) != 0)
    
    def _ROR_acc(self, _):
        """Rotate Right (accumulator)."""
        old_carry = 0x80 if self.registers.C else 0
        
        self.registers.C = ((self.registers.A & 0x01) != 0)
        self.registers.A = (self.registers.A >> 1) | old_carry
        
        self.registers.Z = (self.registers.A == 0)
        self.registers.N = ((self.registers.A & 0x80) != 0)
    
    def _RTI(self, _):
        """Return from Interrupt."""
        # Pull status register and PC from stack
        status = self.pull_byte()
        self.registers.set_status(status)
        self.registers.B = False  # B is always cleared
        self.registers.PC = self.pull_word()
    
    def _RTS(self, _):
        """Return from Subroutine."""
        # Pull return address from stack and add 1
        self.registers.PC = self.pull_word() + 1
    
    def _SBC(self, address):
        """Subtract with Carry."""
        value = self.read_memory(address)
        
        # SBC is equivalent to ADC with inverted operand
        result = self.registers.A - value - (0 if self.registers.C else 1)
        
        # Set carry flag (inverted borrow)
        self.registers.C = (result >= 0)
        
        # Set overflow flag
        self.registers.V = (((self.registers.A ^ value) & (self.registers.A ^ (result & 0xFF)) & 0x80) != 0)
        
        self.registers.A = result & 0xFF
        self.registers.Z = (self.registers.A == 0)
        self.registers.N = ((self.registers.A & 0x80) != 0)
    
    def _SEC(self, _):
        """Set Carry Flag."""
        self.registers.C = True
    
    def _SED(self, _):
        """Set Decimal Flag."""
        self.registers.D = True
    
    def _SEI(self, _):
        """Set Interrupt Disable Flag."""
        self.registers.I = True
    
    # Stack operations
    def push_byte(self, value):
        """Push a byte onto the stack."""
        self.write_memory(0x0100 | self.registers.SP, value)
        self.registers.SP = (self.registers.SP - 1) & 0xFF
    
    def pull_byte(self):
        """Pull a byte from the stack."""
        self.registers.SP = (self.registers.SP + 1) & 0xFF
        return self.read_memory(0x0100 | self.registers.SP)
    
    def push_word(self, value):
        """Push a 16-bit word onto the stack (big-endian)."""
        high = (value >> 8) & 0xFF
        low = value & 0xFF
        self.push_byte(high)
        self.push_byte(low)
    
    def pull_word(self):
        """Pull a 16-bit word from the stack (big-endian)."""
        low = self.pull_byte()
        high = self.pull_byte()
        return (high << 8) | low
    
    # Memory access methods
    def read_memory(self, address):
        """Read a byte from memory."""
        return self.nes_system.memory.read(address)
    
    def write_memory(self, address, value):
        """Write a byte to memory."""
        self.nes_system.memory.write(address, value)
    
    def read_word(self, address):
        """Read a 16-bit word from memory (little-endian)."""
        low = self.read_memory(address)
        high = self.read_memory((address + 1) & 0xFFFF)
        return (high << 8) | low
    
    def step(self):
        """Execute one CPU instruction."""
        # Check for interrupts
        if self.nmi_pending:
            self._handle_nmi()
            self.nmi_pending = False
            return 7  # NMI takes 7 cycles
        
        if self.irq_pending and not self.registers.I:
            self._handle_irq()
            self.irq_pending = False
            return 7  # IRQ takes 7 cycles
        
        # Handle stall cycles (e.g., from DMA)
        if self.stall_cycles > 0:
            self.stall_cycles -= 1
            return 1
        
        # Fetch opcode
        opcode = self.read_memory(self.registers.PC)
        self.registers.PC += 1
        
        if opcode in self.opcodes:
            # Get instruction info
            instruction, addr_mode, cycles = self.opcodes[opcode]
            
            # Calculate effective address using addressing mode
            address_func = self.addressing_modes[addr_mode]
            address, page_cross_cycles = address_func()
            
            # Execute instruction
            extra_cycles = instruction(address) or 0
            
            # Return total cycles
            return cycles + page_cross_cycles + extra_cycles
        else:
            # Unknown opcode, skip
            print(f"Unknown opcode: ${opcode:02X} at PC=${self.registers.PC-1:04X}")
            return 2  # Default to 2 cycles
    
    def _handle_nmi(self):
        """Handle Non-Maskable Interrupt."""
        # Push PC and status to stack
        self.push_word(self.registers.PC)
        
        # Push status with B clear
        self.registers.B = False
        self.push_byte(self.registers.get_status())
        
        # Set interrupt disable
        self.registers.I = True
        
        # Load NMI vector
        self.registers.PC = self.read_word(0xFFFA)
    
    def _handle_irq(self):
        """Handle Interrupt Request."""
        # Push PC and status to stack
        self.push_word(self.registers.PC)
        
        # Push status with B clear
        self.registers.B = False
        self.push_byte(self.registers.get_status())
        
        # Set interrupt disable
        self.registers.I = True
        
        # Load IRQ vector
        self.registers.PC = self.read_word(0xFFFE)

class PPU:
    """Emulates the NES Picture Processing Unit (PPU)."""
    def __init__(self, nes_system):
        self.nes_system = nes_system
        
        # PPU memory
        self.vram = bytearray(VRAM_SIZE)         # 2KB VRAM (nametables)
        self.palette_ram = bytearray(32)         # 32 bytes of palette RAM
        self.oam = bytearray(OAM_SIZE)           # 256 bytes of Object Attribute Memory
        self.oam_addr = 0                        # OAM address
        
        # PPU registers
        self.ppuctrl = 0        # $2000 Control
        self.ppumask = 0        # $2001 Mask
        self.ppustatus = 0      # $2002 Status
        self.oamaddr = 0        # $2003 OAM Address
        self.ppuscroll_x = 0    # X scroll position
        self.ppuscroll_y = 0    # Y scroll position
        self.ppuaddr = 0        # $2006 VRAM Address
        self.ppudata = 0        # $2007 VRAM Data
        
        # PPU internal registers
        self.v = 0              # Current VRAM address (15 bits)
        self.t = 0              # Temporary VRAM address (15 bits)
        self.x = 0              # Fine X scroll (3 bits)
        self.w = 0              # Write toggle (1 bit)
        
        # Frame state
        self.scanline = 0       # Current scanline (0-261)
        self.cycle = 0          # Current cycle (0-340)
        self.frame_complete = False  # Flag for when a frame is complete
        self.odd_frame = False  # Flag for odd frames
        
        # NMI state
        self.nmi_output = False  # NMI output level
        self.nmi_occurred = False  # NMI occurred flag
        
        # Sprite evaluation state
        self.sprite_count = 0
        self.sprite_patterns = [0] * 8
        self.sprite_positions = [0] * 8
        self.sprite_priorities = [0] * 8
        self.sprite_indexes = [0] * 8
        
        # Background state
        self.bg_next_tile_id = 0
        self.bg_next_tile_attr = 0
        self.bg_next_tile_lsb = 0
        self.bg_next_tile_msb = 0
        self.bg_shifter_pattern_lo = 0
        self.bg_shifter_pattern_hi = 0
        self.bg_shifter_attrib_lo = 0
        self.bg_shifter_attrib_hi = 0
        
        # Frame buffer for rendering
        self.frame_buffer = np.zeros((NES_HEIGHT, NES_WIDTH, 3), dtype=np.uint8)
        
        # Mirroring type (set by mapper)
        self.mirroring = 0  # 0 = horizontal, 1 = vertical
    
    def tick(self):
        """Advance one PPU clock cycle."""
        # Pre-render scanline (261)
        if self.scanline == 261:
            # Clear VBLANK and Sprite 0 hit flags at start of pre-render scanline
            if self.cycle == 1:
                self.ppustatus &= ~0x80  # Clear VBLANK flag
                self.ppustatus &= ~0x40  # Clear Sprite 0 hit flag
                self.ppustatus &= ~0x20  # Clear Sprite overflow flag
            
            # Copy vertical scroll bits at end of pre-render scanline
            if self.cycle >= 280 and self.cycle <= 304 and (self.ppumask & 0x18):
                # Copy vertical bits from t to v
                self.v = (self.v & 0x841F) | (self.t & 0x7BE0)
        
        # Visible scanlines (0-239)
        if self.scanline < 240 and (self.ppumask & 0x18):  # Rendering enabled
            # Background processing
            if (self.cycle >= 1 and self.cycle <= 256) or (self.cycle >= 321 and self.cycle <= 336):
                self._update_shifters()
                
                # Determine which memory access to perform based on cycle
                cycle_mod_8 = self.cycle % 8
                
                if cycle_mod_8 == 1:
                    # Fetch nametable byte
                    addr = 0x2000 | (self.v & 0x0FFF)
                    self.bg_next_tile_id = self.read_ppu_memory(addr)
                
                elif cycle_mod_8 == 3:
                    # Fetch attribute byte
                    addr = 0x23C0 | (self.v & 0x0C00) | ((self.v >> 4) & 0x38) | ((self.v >> 2) & 0x07)
                    self.bg_next_tile_attr = self.read_ppu_memory(addr)
                    
                    # Determine which attribute bits to use based on tile position
                    if (self.v & 0x02) != 0:  # Right half of the 32x32 attribute area
                        self.bg_next_tile_attr >>= 2
                    if (self.v & 0x40) != 0:  # Bottom half of the 32x32 attribute area
                        self.bg_next_tile_attr >>= 4
                    
                    self.bg_next_tile_attr &= 0x03  # Only use the two bits we need
                
                elif cycle_mod_8 == 5:
                    # Fetch tile low byte
                    pattern_table = 0x1000 if (self.ppuctrl & 0x10) else 0x0000
                    addr = pattern_table + (self.bg_next_tile_id * 16) + ((self.v >> 12) & 0x07)
                    self.bg_next_tile_lsb = self.read_ppu_memory(addr)
                
                elif cycle_mod_8 == 7:
                    # Fetch tile high byte
                    pattern_table = 0x1000 if (self.ppuctrl & 0x10) else 0x0000
                    addr = pattern_table + (self.bg_next_tile_id * 16) + ((self.v >> 12) & 0x07) + 8
                    self.bg_next_tile_msb = self.read_ppu_memory(addr)
                
                elif cycle_mod_8 == 0:
                    # Load fetched data into shifters
                    for i in range(8):
                        bit_mask = 0x80 >> i
                        pattern_bit_lo = 1 if (self.bg_next_tile_lsb & bit_mask) else 0
                        pattern_bit_hi = 1 if (self.bg_next_tile_msb & bit_mask) else 0
                        pattern_bits = (pattern_bit_hi << 1) | pattern_bit_lo
                        
                        self.bg_shifter_pattern_lo |= pattern_bit_lo << (8 + i)
                        self.bg_shifter_pattern_hi |= pattern_bit_hi << (8 + i)
                        
                        attrib_bit_lo = 1 if (self.bg_next_tile_attr & 0x01) else 0
                        attrib_bit_hi = 1 if (self.bg_next_tile_attr & 0x02) else 0
                        
                        self.bg_shifter_attrib_lo |= attrib_bit_lo << (8 + i)
                        self.bg_shifter_attrib_hi |= attrib_bit_hi << (8 + i)
                    
                    # Increment horizontal position
                    if self.cycle == 256:
                        self._increment_scroll_y()
                    else:
                        self._increment_scroll_x()
            
            # At the end of visible scanline data fetch, copy horizontal position from t to v
            if self.cycle == 257 and (self.ppumask & 0x18):
                # Copy horizontal bits from t to v
                self.v = (self.v & 0xFBE0) | (self.t & 0x041F)
            
            # Sprite evaluation for next scanline
            if self.cycle == 257:
                self._evaluate_sprites()
            
            # Render current pixel
            if self.cycle < 256 and self.scanline < 240:
                self._render_pixel()
        
        # VBLANK starts at scanline 241
        if self.scanline == 241 and self.cycle == 1:
            self.ppustatus |= 0x80  # Set VBLANK flag
            self.nmi_occurred = True
            
            # Generate NMI if enabled
            if self.ppuctrl & 0x80:  # VBLANK NMI enabled
                self.nmi_output = True
                self.nes_system.cpu.nmi_pending = True
            
            # Frame is complete
            self.frame_complete = True
        
        # Advance PPU state
        self.cycle += 1
        if self.cycle > 340:
            self.cycle = 0
            self.scanline += 1
            if self.scanline > 261:
                self.scanline = 0
                self.odd_frame = not self.odd_frame
        
        # Return whether a frame was completed
        return self.frame_complete
    
    def _update_shifters(self):
        """Update PPU background shifters."""
        if self.ppumask & 0x08:  # Background rendering enabled
            # Shift background registers
            self.bg_shifter_pattern_lo >>= 1
            self.bg_shifter_pattern_hi >>= 1
            self.bg_shifter_attrib_lo >>= 1
            self.bg_shifter_attrib_hi >>= 1
    
    def _increment_scroll_x(self):
        """Increment horizontal scroll position."""
        # Increment coarse X
        if (self.v & 0x001F) == 31:
            # Reset coarse X to 0 and flip nametable bit
            self.v &= ~0x001F
            self.v ^= 0x0400
        else:
            self.v += 1
    
    def _increment_scroll_y(self):
        """Increment vertical scroll position."""
        # Increment fine Y
        if (self.v & 0x7000) != 0x7000:
            self.v += 0x1000
        else:
            # Reset fine Y to 0
            self.v &= ~0x7000
            
            # Increment coarse Y
            coarse_y = (self.v & 0x03E0) >> 5
            if coarse_y == 29:
                coarse_y = 0
                self.v ^= 0x0800  # Flip vertical nametable bit
            elif coarse_y == 31:
                coarse_y = 0
            else:
                coarse_y += 1
            
            # Put coarse Y back into v
            self.v = (self.v & ~0x03E0) | (coarse_y << 5)
    
    def _evaluate_sprites(self):
        """Evaluate sprites for the next scanline."""
        self.sprite_count = 0
        
        for i in range(64):  # Check all 64 sprites
            # OAM structure: 4 bytes per sprite
            # Byte 0: Y position
            # Byte 1: Tile index
            # Byte 2: Attributes (palette, priority, flip)
            # Byte 3: X position
            
            y_pos = self.oam[i * 4]
            tile_idx = self.oam[i * 4 + 1]
            attributes = self.oam[i * 4 + 2]
            x_pos = self.oam[i * 4 + 3]
            
            sprite_height = 16 if (self.ppuctrl & 0x20) else 8
            
            # Check if sprite is on next scanline
            if self.scanline >= y_pos and self.scanline < y_pos + sprite_height:
                if self.sprite_count < 8:  # We can only show 8 sprites per line
                    self.sprite_positions[self.sprite_count] = x_pos
                    self.sprite_priorities[self.sprite_count] = (attributes & 0x20) != 0
                    self.sprite_indexes[self.sprite_count] = i
                    
                    # Get pattern data
                    row = self.scanline - y_pos
                    
                    # Flip vertically if needed
                    if attributes & 0x80:
                        row = sprite_height - 1 - row
                    
                    # Fetch the pattern data
                    pattern_table = 0
                    tile_idx_use = tile_idx
                    
                    if sprite_height == 16:
                        # 8x16 sprites
                        pattern_table = (tile_idx & 0x01) * 0x1000
                        tile_idx_use = tile_idx & 0xFE
                        
                        if row >= 8:
                            tile_idx_use += 1
                            row -= 8
                    else:
                        # 8x8 sprites
                        pattern_table = (self.ppuctrl & 0x08) * 0x1000
                    
                    # Get pattern address
                    addr = pattern_table + tile_idx_use * 16 + row
                    pattern_low = self.read_ppu_memory(addr)
                    pattern_high = self.read_ppu_memory(addr + 8)
                    
                    # Flip horizontally if needed
                    if attributes & 0x40:
                        pattern_low = self._flip_byte(pattern_low)
                        pattern_high = self._flip_byte(pattern_high)
                    
                    # Store pattern data
                    palette_shift = (attributes & 0x03) << 2  # Sprite palette starts at 0x10
                    self.sprite_patterns[self.sprite_count] = (palette_shift << 16) | (pattern_high << 8) | pattern_low
                    
                    self.sprite_count += 1
                else:
                    # Sprite overflow
                    self.ppustatus |= 0x20
                    break
    
    def _flip_byte(self, b):
        """Flip a byte for horizontal sprite flipping."""
        result = 0
        for i in range(8):
            if b & (1 << i):
                result |= (1 << (7 - i))
        return result
    
    def _render_pixel(self):
        """Render the current pixel to the frame buffer."""
        x = self.cycle - 1  # Cycle 1-256 -> X coordinate 0-255
        y = self.scanline
        
        if x < 0 or x >= NES_WIDTH or y < 0 or y >= NES_HEIGHT:
            return
        
        # Default color is background color (0)
        palette_idx = 0
        pixel_color = self._get_color_from_palette(palette_idx)
        
        # Background rendering
        bg_pixel = 0
        bg_palette = 0
        
        # Determine pixel visibility
        render_bg = (self.ppumask & 0x08) != 0
        render_sprites = (self.ppumask & 0x10) != 0
        
        # Left edge mask
        bg_left_mask = (self.ppumask & 0x02) != 0
        sprite_left_mask = (self.ppumask & 0x04) != 0
        
        # Check if background is visible at this pixel
        if render_bg and (bg_left_mask or x >= 8):
            # Get pixel from shifter
            bit_mux = 0x8000 >> self.x
            
            # Get pixel color
            p0 = 1 if (self.bg_shifter_pattern_lo & bit_mux) else 0
            p1 = 1 if (self.bg_shifter_pattern_hi & bit_mux) else 0
            
            bg_pixel = (p1 << 1) | p0
            
            # Get palette
            bg_pal0 = 1 if (self.bg_shifter_attrib_lo & bit_mux) else 0
            bg_pal1 = 1 if (self.bg_shifter_attrib_hi & bit_mux) else 0
            
            bg_palette = (bg_pal1 << 1) | bg_pal0
        
        # Sprite rendering
        sprite_pixel = 0
        sprite_palette = 0
        sprite_priority = false
        sprite_zero_hit = false
        
        if render_sprites and (sprite_left_mask or x >= 8):
            for i in range(self.sprite_count):
                sprite_x = self.sprite_positions[i]
                if sprite_x <= x and sprite_x + 8 > x:
                    # This sprite is visible at this position
                    offset = x - sprite_x
                    
                    pattern_data = self.sprite_patterns[i]
                    pattern_low = (pattern_data & 0xFF)
                    pattern_high = ((pattern_data >> 8) & 0xFF)
                    palette_bits = ((pattern_data >> 16) & 0xFF)
                    
                    p0 = (pattern_low >> (7 - offset)) & 0x01
                    p1 = (pattern_high >> (7 - offset)) & 0x01
                    
                    pixel = (p1 << 1) | p0
                    
                    if pixel != 0:  # If not transparent
                        # Check for Sprite 0 hit
                        if self.sprite_indexes[i] == 0 and bg_pixel != 0:
                            self.ppustatus |= 0x40  # Set Sprite 0 hit flag
                        
                        sprite_pixel = pixel
                        sprite_palette = palette_bits | 0x10  # Sprite palettes start at 4
                        sprite_priority = self.sprite_priorities[i]
                        break  # First matching sprite wins
        
        # Final pixel selection
        if bg_pixel == 0 and sprite_pixel == 0:
            # Both transparent, use background color
            palette_idx = 0
        elif bg_pixel == 0 and sprite_pixel > 0:
            # Background transparent, sprite visible
            palette_idx = sprite_palette | sprite_pixel
        elif bg_pixel > 0 and sprite_pixel == 0:
            # Background visible, sprite transparent
            palette_idx = bg_palette | bg_pixel
        else:
            # Both visible, check priority
            if sprite_priority:
                # Sprite is behind background
                palette_idx = bg_palette | bg_pixel
            else:
                # Sprite is in front of background
                palette_idx = sprite_palette | sprite_pixel
        
        # Get the actual RGB color for this frame buffer pixel
        color = self._get_color_from_palette(palette_idx)
        r, g, b = color
        
        # Set the frame buffer pixel
        self.frame_buffer[y, x] = [r, g, b]
    
    def _get_color_from_palette(self, palette_idx):
        """Get the RGB color from the palette index."""
        # Read the color index from the palette RAM
        color_idx = self.read_palette(palette_idx) & 0x3F
        
        # Convert to RGB using the NES palette
        return NES_PALETTE[color_idx]
    
    def read_register(self, address):
        """Read from a PPU register."""
        # Map address to 0-7 range (PPU registers are mirrored)
        reg = address & 0x07
        
        if reg == 0x00:  # PPUCTRL ($2000)
            return 0  # Write-only
        
        elif reg == 0x01:  # PPUMASK ($2001)
            return 0  # Write-only
        
        elif reg == 0x02:  # PPUSTATUS ($2002)
            # Reading status resets write latch
            self.w = 0
            
            # Get the status register with VBLANK flag
            result = self.ppustatus
            
            # Clear VBLANK flag after read
            self.ppustatus &= ~0x80
            self.nmi_occurred = False
            
            return result
        
        elif reg == 0x03:  # OAMADDR ($2003)
            return 0  # Write-only
        
        elif reg == 0x04:  # OAMDATA ($2004)
            return self.oam[self.oamaddr]
        
        elif reg == 0x05:  # PPUSCROLL ($2005)
            return 0  # Write-only
        
        elif reg == 0x06:  # PPUADDR ($2006)
            return 0  # Write-only
        
        elif reg == 0x07:  # PPUDATA ($2007)
            # Get data from current VRAM address
            result = self.ppudata  # Return buffered data
            
            # Read from current VRAM address
            self.ppudata = self.read_ppu_memory(self.v)
            
            # Special case for palette memory: no buffering
            if (self.v & 0x3F00) == 0x3F00:
                result = self.ppudata
            
            # Increment VRAM address
            self.v += 32 if (self.ppuctrl & 0x04) else 1
            self.v &= 0x7FFF  # Keep within 15 bits
            
            return result
        
        return 0
    
    def write_register(self, address, value):
        """Write to a PPU register."""
        # Map address to 0-7 range (PPU registers are mirrored)
        reg = address & 0x07
        
        if reg == 0x00:  # PPUCTRL ($2000)
            self.ppuctrl = value
            
            # Update base nametable in t
            self.t = (self.t & 0xF3FF) | ((value & 0x03) << 10)
            
            # Update NMI output
            if (self.ppuctrl & 0x80) and self.nmi_occurred:
                self.nmi_output = True
                self.nes_system.cpu.nmi_pending = True
        
        elif reg == 0x01:  # PPUMASK ($2001)
            self.ppumask = value
        
        elif reg == 0x02:  # PPUSTATUS ($2002)
            # Write-only, does nothing
            pass
        
        elif reg == 0x03:  # OAMADDR ($2003)
            self.oamaddr = value
        
        elif reg == 0x04:  # OAMDATA ($2004)
            self.oam[self.oamaddr] = value
            self.oamaddr = (self.oamaddr + 1) & 0xFF
        
        elif reg == 0x05:  # PPUSCROLL ($2005)
            if self.w == 0:
                # First write: X scroll
                self.ppuscroll_x = value
                self.t = (self.t & 0xFFE0) | (value >> 3)  # Coarse X
                self.x = value & 0x07  # Fine X
                self.w = 1
            else:
                # Second write: Y scroll
                self.ppuscroll_y = value
                self.t = (self.t & 0x8C1F) | ((value & 0xF8) << 2)  # Coarse Y
                self.t = (self.t & 0xFC1F) | ((value & 0x07) << 12)  # Fine Y
                self.w = 0
        
        elif reg == 0x06:  # PPUADDR ($2006)
            if self.w == 0:
                # First write: high byte
                self.t = (self.t & 0x00FF) | ((value & 0x3F) << 8)  # High bits go into t
                self.w = 1
            else:
                # Second write: low byte
                self.t = (self.t & 0xFF00) | value  # Low bits go into t
                self.v = self.t  # Copy t to v
                self.w = 0
        
        elif reg == 0x07:  # PPUDATA ($2007)
            # Write to VRAM at the current address
            self.write_ppu_memory(self.v, value)
            
            # Increment address
            self.v += 32 if (self.ppuctrl & 0x04) else 1
            self.v &= 0x7FFF  # Keep within 15 bits
    
    def read_ppu_memory(self, address):
        """Read a byte from the PPU address space."""
        addr = address & 0x3FFF  # Mirror down to 0x0000-0x3FFF
        
        # Pattern tables (0x0000-0x1FFF) from CHR ROM/RAM
        if addr <= 0x1FFF:
            return self.nes_system.mapper.read_chr(addr)
        
        # Nametables (0x2000-0x3EFF)
        elif addr <= 0x3EFF:
            # Mirror down to the 4 nametables and apply mirroring mode
            addr = self.apply_nametable_mirroring(addr)
            return self.vram[addr & 0x07FF]
        
        # Palette RAM (0x3F00-0x3FFF)
        else:
            return self.read_palette(addr & 0x1F)
    
    def write_ppu_memory(self, address, value):
        """Write a byte to the PPU address space."""
        addr = address & 0x3FFF  # Mirror down to 0x0000-0x3FFF
        
        # Pattern tables (0x0000-0x1FFF) from CHR ROM/RAM
        if addr <= 0x1FFF:
            self.nes_system.mapper.write_chr(addr, value)
        
        # Nametables (0x2000-0x3EFF)
        elif addr <= 0x3EFF:
            # Mirror down to the 4 nametables and apply mirroring mode
            addr = self.apply_nametable_mirroring(addr)
            self.vram[addr & 0x07FF] = value
        
        # Palette RAM (0x3F00-0x3FFF)
        else:
            self.write_palette(addr & 0x1F, value)
    
    def read_palette(self, palette_addr):
        """Read from palette RAM with appropriate mirroring."""

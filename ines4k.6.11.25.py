import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
import time

##############################################################################
#  HARDWARE SIMULATION: BUS, CARTRIDGE, CPU, PPU
##############################################################################

class Bus:
    """The main bus connecting all hardware components."""
    def __init__(self):
        # Full 64KB address space, only 2KB is RAM, the rest is mirrored.
        self.cpu_ram = np.zeros(2048, dtype=np.uint8)
        self.cpu = CPU6502()
        self.cpu.connect_bus(self)
        self.ppu = PPU()
        self.cartridge = None
        self.system_clock_counter = 0

    def cpu_write(self, addr, data):
        """Route CPU write requests to the correct component."""
        if self.cartridge and self.cartridge.cpu_write(addr, data):
            return
        if 0x0000 <= addr <= 0x1FFF: # System RAM
            self.cpu_ram[addr & 0x07FF] = data
        elif 0x2000 <= addr <= 0x3FFF: # PPU Registers
            self.ppu.cpu_write(addr & 0x0007, data)
        # [FIX 8] Removed redundant cycle addition. Stall is handled in the main clock.
        elif addr == 0x4014: # OAM DMA
            self.ppu.oam_dma_page = data
            self.ppu.oam_dma_transfer = True
            self.ppu.oam_dma_addr = 0x00


    def cpu_read(self, addr, read_only=False):
        """Route CPU read requests to the correct component."""
        cart_data = self.cartridge.cpu_read(addr) if self.cartridge else None
        if cart_data is not None:
            return cart_data
        if 0x0000 <= addr <= 0x1FFF: # System RAM
            return self.cpu_ram[addr & 0x07FF]
        elif 0x2000 <= addr <= 0x3FFF: # PPU Registers
            return self.ppu.cpu_read(addr & 0x0007, read_only)
        return 0x00

    def insert_cartridge(self, cartridge):
        """Load a cartridge into the system."""
        self.cartridge = cartridge
        self.ppu.connect_cartridge(cartridge)

    def reset(self):
        """Reset the entire system."""
        self.cpu.reset()
        self.ppu.reset()
        self.system_clock_counter = 0

    def clock(self):
        """Perform one system clock cycle."""
        self.ppu.clock()
        # CPU runs at 1/3 the speed of the PPU
        if self.system_clock_counter % 3 == 0:
            # Stall CPU during DMA transfer
            if self.ppu.oam_dma_transfer:
                self.ppu.oam_dma_clock(self.system_clock_counter, self)
            else:
                self.cpu.clock()

        if self.ppu.nmi:
            self.ppu.nmi = False
            self.cpu.nmi()

        self.system_clock_counter += 1


class Cartridge:
    """A class to parse and hold data from an iNES ROM file."""
    def __init__(self, file_path):
        with open(file_path, 'rb') as f:
            header = f.read(16)
            
            if header[0:4] != b'NES\x1a':
                raise ValueError("Not a valid iNES file.")
            
            self.prg_rom_chunks = header[4]
            self.chr_rom_chunks = header[5]
            
            flags6 = header[6]
            flags7 = header[7]

            self.mapper_id = (flags7 & 0xF0) | (flags6 >> 4)
            # 1: VERTICAL, 0: HORIZONTAL
            self.mirror = 1 if flags6 & 0x01 else 0

            # Skip trainer if present
            if flags6 & 0x04:
                f.seek(512, 1)

            prg_rom_size = self.prg_rom_chunks * 16384
            self.prg_memory = np.frombuffer(f.read(prg_rom_size), dtype=np.uint8)

            chr_rom_size = self.chr_rom_chunks * 8192
            if chr_rom_size == 0:
                # Create CHR RAM if no CHR ROM is present
                self.chr_memory = np.zeros(8192, dtype=np.uint8)
            else:
                self.chr_memory = np.frombuffer(f.read(chr_rom_size), dtype=np.uint8)
        
        if self.mapper_id != 0:
            print(f"Warning: Mapper {self.mapper_id} not fully supported. Treating as NROM.")

    def cpu_read(self, addr):
        # Mapper 0 (NROM) logic
        if 0x8000 <= addr <= 0xFFFF:
            # If only one PRG chunk (16KB), mirror 0x8000-0xBFFF at 0xC000-0xFFFF
            map_addr = addr & (0x7FFF if self.prg_rom_chunks > 1 else 0x3FFF)
            return self.prg_memory[map_addr]
        return None

    def cpu_write(self, addr, data):
        return False

    def ppu_read(self, addr):
        if 0x0000 <= addr <= 0x1FFF:
            return self.chr_memory[addr]
        return None

    def ppu_write(self, addr, data):
        # Writing to CHR-RAM for games that support it
        if 0x0000 <= addr <= 0x1FFF and self.chr_rom_chunks == 0:
            self.chr_memory[addr] = data
            return True
        return False


class PPU:
    """Picture Processing Unit simulation."""
    def __init__(self):
        self.cartridge = None
        self.tbl_name = np.zeros((2, 1024), dtype=np.uint8)
        self.tbl_palette = np.zeros(32, dtype=np.uint8)
        self.oam = np.zeros(256, dtype=np.uint8)

        self.colors = np.array([
            (84, 84, 84), (0, 30, 116), (8, 16, 144), (48, 0, 136), (68, 0, 100), (92, 0, 48), (84, 4, 0), (60, 24, 0),
            (32, 42, 0), (8, 58, 0), (0, 64, 0), (0, 60, 0), (0, 50, 60), (0, 0, 0), (0, 0, 0), (0, 0, 0),
            (152, 150, 152), (8, 76, 196), (48, 50, 236), (92, 30, 228), (136, 20, 176), (160, 20, 100), (152, 34, 32), (120, 60, 0),
            (84, 90, 0), (40, 114, 0), (8, 124, 0), (0, 118, 40), (0, 102, 120), (0, 0, 0), (0, 0, 0), (0, 0, 0),
            (236, 238, 236), (76, 154, 236), (120, 124, 236), (176, 98, 236), (228, 84, 236), (236, 88, 180), (236, 106, 100), (212, 136, 32),
            (160, 170, 0), (116, 196, 0), (76, 208, 32), (56, 204, 108), (56, 180, 204), (60, 60, 60), (0, 0, 0), (0, 0, 0),
            (236, 238, 236), (168, 204, 236), (188, 188, 236), (212, 178, 236), (236, 174, 236), (236, 174, 212), (236, 180, 176), (228, 196, 144),
            (204, 210, 120), (180, 222, 120), (168, 226, 144), (152, 226, 180), (160, 214, 228), (160, 162, 160), (0, 0, 0), (0, 0, 0)
        ], dtype=np.uint8)
        
        self.screen = np.zeros((240, 256, 3), dtype=np.uint8)
        self.reset()

    def reset(self):
        self.ppuctrl = 0x00; self.ppumask = 0x00; self.ppustatus = 0x00
        self.oamaddr = 0x00; self.ppuscroll = 0x00; self.ppuaddr = 0x00
        self.ppudata = 0x00; self.vram_addr = 0x0000; self.tram_addr = 0x0000
        self.fine_x = 0x00; self.address_latch = 0x00; self.ppu_data_buffer = 0x00
        self.scanline = 0; self.cycle = 0; self.frame_complete = False
        self.nmi = False; self.oam_dma_page = 0x00; self.oam_dma_addr = 0x00
        self.oam_dma_transfer = False
        # [FIX 7] Added member variable to hold DMA data between cycles
        self.oam_dma_data = 0x00
        
        # Rendering state
        self.bg_next_tile_id = 0x00
        self.bg_next_tile_attrib = 0x00
        self.bg_next_tile_lsb = 0x00
        self.bg_next_tile_msb = 0x00
        self.bg_shifter_pattern_lo = 0x0000
        self.bg_shifter_pattern_hi = 0x0000
        self.bg_shifter_attrib_lo = 0x0000
        self.bg_shifter_attrib_hi = 0x0000
        
        # [FIX 10] Simplified mirroring lookup
        self.mirror_lookup = [
            [0, 0, 1, 1], # Horizontal
            [0, 1, 0, 1]  # Vertical
        ]


    def connect_cartridge(self, cartridge):
        self.cartridge = cartridge

    def cpu_read(self, addr, read_only=False):
        data = 0x00
        if addr == 0x0002:  # PPUSTATUS
            data = (self.ppustatus & 0xE0) | (self.ppu_data_buffer & 0x1F)
            self.ppustatus &= ~0x80  # Clear vblank flag
            # [FIX 6] Correctly reset address latch on status read
            self.address_latch = 0
        elif addr == 0x0004:  # OAMDATA
            data = self.oam[self.oamaddr]
        elif addr == 0x0007:  # PPUDATA
            data = self.ppu_data_buffer
            self.ppu_data_buffer = self.ppu_read(self.vram_addr)
            if self.vram_addr >= 0x3F00: data = self.ppu_data_buffer
            self.vram_addr = (self.vram_addr + (32 if self.ppuctrl & 0x04 else 1)) & 0x3FFF
        return data

    def cpu_write(self, addr, data):
        if addr == 0x0000:  # PPUCTRL
            self.ppuctrl = data
            self.tram_addr = (self.tram_addr & 0xF3FF) | ((data & 0x03) << 10)
        elif addr == 0x0001:  # PPUMASK
            self.ppumask = data
        elif addr == 0x0003:  # OAMADDR
            self.oamaddr = data
        elif addr == 0x0004:  # OAMDATA
            self.oam[self.oamaddr] = data
            self.oamaddr = (self.oamaddr + 1) & 0xFF
        elif addr == 0x0005:  # PPUSCROLL
            if self.address_latch == 0:
                self.fine_x = data & 0x07
                self.tram_addr = (self.tram_addr & 0xFFE0) | (data >> 3)
                self.address_latch = 1
            else:
                self.tram_addr = (self.tram_addr & 0x8C1F) | ((data & 0xF8) << 2) | ((data & 0x07) << 12)
                self.address_latch = 0
        elif addr == 0x0006:  # PPUADDR
            if self.address_latch == 0:
                self.tram_addr = (self.tram_addr & 0x00FF) | ((data & 0x3F) << 8)
                self.address_latch = 1
            else:
                self.tram_addr = (self.tram_addr & 0xFF00) | data
                self.vram_addr = self.tram_addr
                self.address_latch = 0
        elif addr == 0x0007:  # PPUDATA
            self.ppu_write(self.vram_addr, data)
            self.vram_addr = (self.vram_addr + (32 if self.ppuctrl & 0x04 else 1)) & 0x3FFF

    def ppu_read(self, addr):
        addr &= 0x3FFF
        # [FIX 11] Added check to prevent crash if no ROM is loaded
        if not self.cartridge: return 0

        if 0x0000 <= addr <= 0x1FFF: return self.cartridge.ppu_read(addr)
        elif 0x2000 <= addr <= 0x3EFF:
            addr &= 0x0FFF
            mirror_mode = self.cartridge.mirror
            table_idx = self.mirror_lookup[mirror_mode][addr // 0x400]
            return self.tbl_name[table_idx][addr & 0x03FF]
        elif 0x3F00 <= addr <= 0x3FFF:
            addr &= 0x001F
            if addr in [0x0010, 0x0014, 0x0018, 0x001C]: addr &= 0x000F
            return self.tbl_palette[addr]
        return 0

    def ppu_write(self, addr, data):
        addr &= 0x3FFF
        if not self.cartridge: return

        if 0x0000 <= addr <= 0x1FFF: self.cartridge.ppu_write(addr, data)
        elif 0x2000 <= addr <= 0x3EFF:
            addr &= 0x0FFF
            mirror_mode = self.cartridge.mirror
            table_idx = self.mirror_lookup[mirror_mode][addr // 0x400]
            self.tbl_name[table_idx][addr & 0x03FF] = data
        elif 0x3F00 <= addr <= 0x3FFF:
            addr &= 0x001F
            if addr in [0x0010, 0x0014, 0x0018, 0x001C]: addr &= 0x000F
            self.tbl_palette[addr] = data

    def _load_bg_shifters(self):
        self.bg_shifter_pattern_lo = (self.bg_shifter_pattern_lo & 0xFF00) | self.bg_next_tile_lsb
        self.bg_shifter_pattern_hi = (self.bg_shifter_pattern_hi & 0xFF00) | self.bg_next_tile_msb
        self.bg_shifter_attrib_lo  = (self.bg_shifter_attrib_lo & 0xFF00) | (0xFF if self.bg_next_tile_attrib & 0b01 else 0x00)
        self.bg_shifter_attrib_hi  = (self.bg_shifter_attrib_hi & 0xFF00) | (0xFF if self.bg_next_tile_attrib & 0b10 else 0x00)

    def _update_shifters(self):
        if self.ppumask & 0x08:
            self.bg_shifter_pattern_lo <<= 1
            self.bg_shifter_pattern_hi <<= 1
            self.bg_shifter_attrib_lo <<= 1
            self.bg_shifter_attrib_hi <<= 1

    def clock(self):
        # [FIX 1 & 5] Complete PPU rendering and scrolling logic
        rendering_enabled = (self.ppumask & 0x08) or (self.ppumask & 0x10)

        if self.scanline >= -1 and self.scanline < 240:
            if self.scanline == -1 and self.cycle == 1:
                self.ppustatus &= ~(0x80 | 0x40) # Clear VBlank and sprite 0 hit
            
            if (2 <= self.cycle <= 257) or (321 <= self.cycle <= 337):
                self._update_shifters()
                
                # Fetching logic
                if self.cycle % 8 == 1:
                    self._load_bg_shifters()
                    self.bg_next_tile_id = self.ppu_read(0x2000 | (self.vram_addr & 0x0FFF))
                elif self.cycle % 8 == 3:
                    self.bg_next_tile_attrib = self.ppu_read(0x23C0 | (self.vram_addr & 0x0C00) | ((self.vram_addr >> 4) & 0x38) | ((self.vram_addr >> 2) & 0x07))
                    if (self.vram_addr >> 1) & 1: self.bg_next_tile_attrib >>= 2 # correct 2x2 tile area
                    if (self.vram_addr >> 6) & 1: self.bg_next_tile_attrib >>= 4 # correct 4x4 tile area
                    self.bg_next_tile_attrib &= 0x03
                elif self.cycle % 8 == 5:
                    pattern_addr = ((self.ppuctrl & 0x10) << 8) + (self.bg_next_tile_id << 4) + ((self.vram_addr >> 12) & 0x07)
                    self.bg_next_tile_lsb = self.ppu_read(pattern_addr)
                elif self.cycle % 8 == 7:
                    pattern_addr = ((self.ppuctrl & 0x10) << 8) + (self.bg_next_tile_id << 4) + ((self.vram_addr >> 12) & 0x07) + 8
                    self.bg_next_tile_msb = self.ppu_read(pattern_addr)
            
            if rendering_enabled and self.cycle == 256: # End of scanline, increment Y
                if (self.vram_addr & 0x7000) != 0x7000:
                    self.vram_addr += 0x1000
                else:
                    self.vram_addr &= ~0x7000
                    y = (self.vram_addr & 0x03E0) >> 5
                    if y == 29:
                        y = 0
                        self.vram_addr ^= 0x0800
                    elif y == 31:
                        y = 0
                    else:
                        y += 1
                    self.vram_addr = (self.vram_addr & ~0x03E0) | (y << 5)

            if rendering_enabled and self.cycle == 257: # Reset X
                self._load_bg_shifters()
                self.vram_addr = (self.vram_addr & ~0x041F) | (self.tram_addr & 0x041F)

            if self.scanline == -1 and 280 <= self.cycle <= 304: # Reset Y
                if rendering_enabled:
                    self.vram_addr = (self.vram_addr & ~0x7BE0) | (self.tram_addr & 0x7BE0)

        # V-Blank period
        if self.scanline == 241 and self.cycle == 1:
            self.ppustatus |= 0x80 # Set VBlank
            if self.ppuctrl & 0x80:
                self.nmi = True
            self.frame_complete = True
        
        # Render a pixel
        bg_pixel, bg_palette = 0, 0
        if (self.ppumask & 0x08) and (1 <= self.cycle <= 256) and (0 <= self.scanline < 240):
            bit_mux = 0x8000 >> self.fine_x
            p0 = 1 if self.bg_shifter_pattern_lo & bit_mux else 0
            p1 = 1 if self.bg_shifter_pattern_hi & bit_mux else 0
            bg_pixel = (p1 << 1) | p0
            
            pal0 = 1 if self.bg_shifter_attrib_lo & bit_mux else 0
            pal1 = 1 if self.bg_shifter_attrib_hi & bit_mux else 0
            bg_palette = (pal1 << 1) | pal0

            # Draw pixel
            color_idx = self.ppu_read(0x3F00 + (bg_palette << 2) + bg_pixel)
            self.screen[self.scanline, self.cycle - 1] = self.colors[color_idx & 0x3F]
        
        # Increment PPU counters
        self.cycle += 1
        if self.cycle >= 341:
            self.cycle = 0
            self.scanline += 1
            if self.scanline >= 261:
                self.scanline = -1
                
        # Handle X increment for rendering
        if rendering_enabled and (2 <= self.cycle <= 257) and (self.cycle % 8 == 0):
            if (self.vram_addr & 0x001F) == 31:
                self.vram_addr &= ~0x001F
                self.vram_addr ^= 0x0400
            else:
                self.vram_addr += 1

    def oam_dma_clock(self, clock_counter, bus):
        if clock_counter % 2 == 0: # Even cycle: read from CPU bus
            self.oam_dma_data = bus.cpu_read(self.oam_dma_page * 256 + self.oam_dma_addr)
        else: # Odd cycle: write to PPU OAM
            self.oam[self.oam_dma_addr] = self.oam_dma_data
            self.oam_dma_addr = (self.oam_dma_addr + 1) & 0xFF
            if self.oam_dma_addr == 0:
                self.oam_dma_transfer = False


class CPU6502:
    """6502 CPU simulation."""
    def __init__(self):
        self.a = 0x00; self.x = 0x00; self.y = 0x00
        self.sp = 0xFD; self.pc = 0x0000; self.status = 0x00
        
        self.fetched = 0x00; self.addr_abs = 0x0000; self.addr_rel = 0x00
        self.opcode = 0x00; self.cycles = 0; self.clock_count = 0
        
        self.bus = None
        
        self.lookup = {
            0x00: ("BRK", self.BRK, self.IMP, 7), 0x01: ("ORA", self.ORA, self.IZX, 6),
            0x05: ("ORA", self.ORA, self.ZP0, 3), 0x06: ("ASL", self.ASL, self.ZP0, 5),
            0x08: ("PHP", self.PHP, self.IMP, 3), 0x09: ("ORA", self.ORA, self.IMM, 2),
            0x0A: ("ASL", self.ASL, self.IMP, 2), 0x0D: ("ORA", self.ORA, self.ABS, 4),
            0x0E: ("ASL", self.ASL, self.ABS, 6), 0x10: ("BPL", self.BPL, self.REL, 2),
            0x11: ("ORA", self.ORA, self.IZY, 5), 0x15: ("ORA", self.ORA, self.ZPX, 4),
            0x16: ("ASL", self.ASL, self.ZPX, 6), 0x18: ("CLC", self.CLC, self.IMP, 2),
            0x19: ("ORA", self.ORA, self.ABY, 4), 0x1D: ("ORA", self.ORA, self.ABX, 4),
            0x1E: ("ASL", self.ASL, self.ABX, 7), 0x20: ("JSR", self.JSR, self.ABS, 6),
            0x21: ("AND", self.AND, self.IZX, 6), 0x24: ("BIT", self.BIT, self.ZP0, 3),
            0x25: ("AND", self.AND, self.ZP0, 3), 0x26: ("ROL", self.ROL, self.ZP0, 5),
            0x28: ("PLP", self.PLP, self.IMP, 4), 0x29: ("AND", self.AND, self.IMM, 2),
            0x2A: ("ROL", self.ROL, self.IMP, 2), 0x2C: ("BIT", self.BIT, self.ABS, 4),
            0x2D: ("AND", self.AND, self.ABS, 4), 0x2E: ("ROL", self.ROL, self.ABS, 6),
            0x30: ("BMI", self.BMI, self.REL, 2), 0x31: ("AND", self.AND, self.IZY, 5),
            0x35: ("AND", self.AND, self.ZPX, 4), 0x36: ("ROL", self.ROL, self.ZPX, 6),
            0x38: ("SEC", self.SEC, self.IMP, 2), 0x39: ("AND", self.AND, self.ABY, 4),
            0x3D: ("AND", self.AND, self.ABX, 4), 0x3E: ("ROL", self.ROL, self.ABX, 7),
            0x40: ("RTI", self.RTI, self.IMP, 6), 0x41: ("EOR", self.EOR, self.IZX, 6),
            0x45: ("EOR", self.EOR, self.ZP0, 3), 0x46: ("LSR", self.LSR, self.ZP0, 5),
            0x48: ("PHA", self.PHA, self.IMP, 3), 0x49: ("EOR", self.EOR, self.IMM, 2),
            0x4A: ("LSR", self.LSR, self.IMP, 2), 0x4C: ("JMP", self.JMP, self.ABS, 3),
            0x4D: ("EOR", self.EOR, self.ABS, 4), 0x4E: ("LSR", self.LSR, self.ABS, 6),
            0x50: ("BVC", self.BVC, self.REL, 2), 0x51: ("EOR", self.EOR, self.IZY, 5),
            0x55: ("EOR", self.EOR, self.ZPX, 4), 0x56: ("LSR", self.LSR, self.ZPX, 6),
            0x58: ("CLI", self.CLI, self.IMP, 2), 0x59: ("EOR", self.EOR, self.ABY, 4),
            0x5D: ("EOR", self.EOR, self.ABX, 4), 0x5E: ("LSR", self.LSR, self.ABX, 7),
            0x60: ("RTS", self.RTS, self.IMP, 6), 0x61: ("ADC", self.ADC, self.IZX, 6),
            0x65: ("ADC", self.ADC, self.ZP0, 3), 0x66: ("ROR", self.ROR, self.ZP0, 5),
            0x68: ("PLA", self.PLA, self.IMP, 4), 0x69: ("ADC", self.ADC, self.IMM, 2),
            0x6A: ("ROR", self.ROR, self.IMP, 2), 0x6C: ("JMP", self.JMP, self.IND, 5),
            0x6D: ("ADC", self.ADC, self.ABS, 4), 0x6E: ("ROR", self.ROR, self.ABS, 6),
            0x70: ("BVS", self.BVS, self.REL, 2), 0x71: ("ADC", self.ADC, self.IZY, 5),
            0x75: ("ADC", self.ADC, self.ZPX, 4), 0x76: ("ROR", self.ROR, self.ZPX, 6),
            0x78: ("SEI", self.SEI, self.IMP, 2), 0x79: ("ADC", self.ADC, self.ABY, 4),
            0x7D: ("ADC", self.ADC, self.ABX, 4), 0x7E: ("ROR", self.ROR, self.ABX, 7),
            0x81: ("STA", self.STA, self.IZX, 6), 0x84: ("STY", self.STY, self.ZP0, 3),
            0x85: ("STA", self.STA, self.ZP0, 3), 0x86: ("STX", self.STX, self.ZP0, 3),
            0x88: ("DEY", self.DEY, self.IMP, 2), 0x8A: ("TXA", self.TXA, self.IMP, 2),
            0x8C: ("STY", self.STY, self.ABS, 4), 0x8D: ("STA", self.STA, self.ABS, 4),
            0x8E: ("STX", self.STX, self.ABS, 4), 0x90: ("BCC", self.BCC, self.REL, 2),
            0x91: ("STA", self.STA, self.IZY, 6), 0x94: ("STY", self.STY, self.ZPX, 4),
            0x95: ("STA", self.STA, self.ZPX, 4), 0x96: ("STX", self.STX, self.ZPY, 4),
            0x98: ("TYA", self.TYA, self.IMP, 2), 0x99: ("STA", self.STA, self.ABY, 5),
            0x9A: ("TXS", self.TXS, self.IMP, 2), 0x9D: ("STA", self.STA, self.ABX, 5),
            0xA0: ("LDY", self.LDY, self.IMM, 2), 0xA1: ("LDA", self.LDA, self.IZX, 6),
            0xA2: ("LDX", self.LDX, self.IMM, 2), 0xA4: ("LDY", self.LDY, self.ZP0, 3),
            0xA5: ("LDA", self.LDA, self.ZP0, 3), 0xA6: ("LDX", self.LDX, self.ZP0, 3),
            0xA8: ("TAY", self.TAY, self.IMP, 2), 0xA9: ("LDA", self.LDA, self.IMM, 2),
            0xAA: ("TAX", self.TAX, self.IMP, 2), 0xAC: ("LDY", self.LDY, self.ABS, 4),
            0xAD: ("LDA", self.LDA, self.ABS, 4), 0xAE: ("LDX", self.LDX, self.ABS, 4),
            0xB0: ("BCS", self.BCS, self.REL, 2), 0xB1: ("LDA", self.LDA, self.IZY, 5),
            0xB4: ("LDY", self.LDY, self.ZPX, 4), 0xB5: ("LDA", self.LDA, self.ZPX, 4),
            0xB6: ("LDX", self.LDX, self.ZPY, 4), 0xB8: ("CLV", self.CLV, self.IMP, 2),
            0xB9: ("LDA", self.LDA, self.ABY, 4), 0xBA: ("TSX", self.TSX, self.IMP, 2),
            0xBC: ("LDY", self.LDY, self.ABX, 4), 0xBD: ("LDA", self.LDA, self.ABX, 4),
            0xBE: ("LDX", self.LDX, self.ABY, 4), 0xC0: ("CPY", self.CPY, self.IMM, 2),
            0xC1: ("CMP", self.CMP, self.IZX, 6), 0xC4: ("CPY", self.CPY, self.ZP0, 3),
            0xC5: ("CMP", self.CMP, self.ZP0, 3), 0xC6: ("DEC", self.DEC, self.ZP0, 5),
            0xC8: ("INY", self.INY, self.IMP, 2), 0xC9: ("CMP", self.CMP, self.IMM, 2),
            0xCA: ("DEX", self.DEX, self.IMP, 2), 0xCC: ("CPY", self.CPY, self.ABS, 4),
            0xCD: ("CMP", self.CMP, self.ABS, 4), 0xCE: ("DEC", self.DEC, self.ABS, 6),
            0xD0: ("BNE", self.BNE, self.REL, 2), 0xD1: ("CMP", self.CMP, self.IZY, 5),
            0xD5: ("CMP", self.CMP, self.ZPX, 4), 0xD6: ("DEC", self.DEC, self.ZPX, 6),
            0xD8: ("CLD", self.CLD, self.IMP, 2), 0xD9: ("CMP", self.CMP, self.ABY, 4),
            0xDD: ("CMP", self.CMP, self.ABX, 4), 0xDE: ("DEC", self.DEC, self.ABX, 7),
            0xE0: ("CPX", self.CPX, self.IMM, 2), 0xE1: ("SBC", self.SBC, self.IZX, 6),
            0xE4: ("CPX", self.CPX, self.ZP0, 3), 0xE5: ("SBC", self.SBC, self.ZP0, 3),
            0xE6: ("INC", self.INC, self.ZP0, 5), 0xE8: ("INX", self.INX, self.IMP, 2),
            0xE9: ("SBC", self.SBC, self.IMM, 2), 0xEA: ("NOP", self.NOP, self.IMP, 2),
            0xEC: ("CPX", self.CPX, self.ABS, 4), 0xED: ("SBC", self.SBC, self.ABS, 4),
            0xEE: ("INC", self.INC, self.ABS, 6), 0xF0: ("BEQ", self.BEQ, self.REL, 2),
            0xF1: ("SBC", self.SBC, self.IZY, 5), 0xF5: ("SBC", self.SBC, self.ZPX, 4),
            0xF6: ("INC", self.INC, self.ZPX, 6), 0xF8: ("SED", self.SED, self.IMP, 2),
            0xF9: ("SBC", self.SBC, self.ABY, 4), 0xFD: ("SBC", self.SBC, self.ABX, 4),
            0xFE: ("INC", self.INC, self.ABX, 7),
        }

    def connect_bus(self, bus): self.bus = bus
    def write(self, addr, data): self.bus.cpu_write(addr, data)
    def read(self, addr, read_only=False): return self.bus.cpu_read(addr, read_only)

    def get_flag(self, flag): return (self.status >> list(CPU6502.FLAGS.keys()).index(flag)) & 1
    def set_flag(self, flag, value):
        if value: self.status |= CPU6502.FLAGS[flag]
        else: self.status &= ~CPU6502.FLAGS[flag]

    FLAGS = {'C': 1<<0, 'Z': 1<<1, 'I': 1<<2, 'D': 1<<3, 'B': 1<<4, 'U': 1<<5, 'V': 1<<6, 'N': 1<<7}

    def reset(self):
        self.a = 0; self.x = 0; self.y = 0; self.sp = 0xFD; self.status = 0x00 | self.FLAGS['U']
        self.addr_abs = 0xFFFC
        self.pc = (self.read(self.addr_abs + 1) << 8) | self.read(self.addr_abs)
        self.addr_rel = 0x00; self.addr_abs = 0x0000; self.fetched = 0x00
        self.cycles = 8

    def _push_stack(self, data):
        self.write(0x0100 + self.sp, data)
        # [FIX 2] Correct stack pointer wrapping
        self.sp = (self.sp - 1) & 0xFF
    
    def _pop_stack(self):
        self.sp = (self.sp + 1) & 0xFF
        return self.read(0x0100 + self.sp)

    def irq(self):
        if self.get_flag('I') == 0:
            self._push_stack((self.pc >> 8) & 0xFF)
            self._push_stack(self.pc & 0xFF)
            self.set_flag('B', 0); self.set_flag('U', 1); self.set_flag('I', 1)
            self._push_stack(self.status)
            self.addr_abs = 0xFFFE
            self.pc = (self.read(self.addr_abs + 1) << 8) | self.read(self.addr_abs)
            self.cycles = 7

    def nmi(self):
        self._push_stack((self.pc >> 8) & 0xFF)
        self._push_stack(self.pc & 0xFF)
        self.set_flag('B', 0); self.set_flag('U', 1); self.set_flag('I', 1)
        self._push_stack(self.status)
        self.addr_abs = 0xFFFA
        self.pc = (self.read(self.addr_abs + 1) << 8) | self.read(self.addr_abs)
        self.cycles = 8

    def clock(self):
        if self.cycles == 0:
            self.opcode = self.read(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            self.set_flag('U', 1)
            
            if self.opcode in self.lookup:
                name, op, addr, cyc = self.lookup[self.opcode]
                self.cycles = cyc
                add_cycle1 = addr()
                add_cycle2 = op()
                # [FIX 3] Use bitwise OR for correct cycle counting
                self.cycles += (add_cycle1 | add_cycle2)
            else: # Handle illegal opcodes as NOPs
                self.cycles = 2

            self.set_flag('U', 1)
        
        self.cycles -= 1
        self.clock_count += 1

    def fetch(self):
        if self.lookup[self.opcode][2] != self.IMP:
            self.fetched = self.read(self.addr_abs)
        return self.fetched

    # Addressing modes
    def IMP(self): self.fetched = self.a; return 0
    def IMM(self): self.addr_abs = self.pc; self.pc = (self.pc + 1) & 0xFFFF; return 0
    def ZP0(self): self.addr_abs = self.read(self.pc); self.pc = (self.pc + 1) & 0xFFFF; return 0
    def ZPX(self): self.addr_abs = (self.read(self.pc) + self.x) & 0xFF; self.pc = (self.pc + 1) & 0xFFFF; return 0
    def ZPY(self): self.addr_abs = (self.read(self.pc) + self.y) & 0xFF; self.pc = (self.pc + 1) & 0xFFFF; return 0
    def ABS(self): lo = self.read(self.pc); self.pc = (self.pc+1)&0xFFFF; hi = self.read(self.pc); self.pc = (self.pc+1)&0xFFFF; self.addr_abs = (hi << 8) | lo; return 0
    def ABX(self): lo=self.read(self.pc); self.pc=(self.pc+1)&0xFFFF; hi=self.read(self.pc); self.pc=(self.pc+1)&0xFFFF; base_addr=(hi<<8)|lo; self.addr_abs=base_addr+self.x; return 1 if (self.addr_abs & 0xFF00) != (base_addr & 0xFF00) else 0
    def ABY(self): lo=self.read(self.pc); self.pc=(self.pc+1)&0xFFFF; hi=self.read(self.pc); self.pc=(self.pc+1)&0xFFFF; base_addr=(hi<<8)|lo; self.addr_abs=base_addr+self.y; return 1 if (self.addr_abs & 0xFF00) != (base_addr & 0xFF00) else 0
    # [FIX 4] Correctly implement the JMP ($xxFF) hardware bug
    def IND(self):
        ptr_lo = self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        ptr_hi = self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        ptr = (ptr_hi << 8) | ptr_lo
        if ptr_lo == 0xFF:
            self.addr_abs = (self.read(ptr & 0xFF00) << 8) | self.read(ptr)
        else:
            self.addr_abs = (self.read(ptr + 1) << 8) | self.read(ptr)
        return 0
    def IZX(self): t=self.read(self.pc); self.pc=(self.pc+1)&0xFFFF; lo=self.read((t+self.x)&0xFF); hi=self.read((t+self.x+1)&0xFF); self.addr_abs=(hi<<8)|lo; return 0
    def IZY(self): t=self.read(self.pc); self.pc=(self.pc+1)&0xFFFF; lo=self.read(t); hi=self.read((t+1)&0xFF); base=(hi<<8)|lo; self.addr_abs=base+self.y; return 1 if (self.addr_abs&0xFF00)!=(base&0xFF00) else 0
    def REL(self): self.addr_rel = self.read(self.pc); self.pc = (self.pc + 1) & 0xFFFF; return 0

    # Instructions
    def ADC(self): self.fetch(); temp=self.a+self.fetched+self.get_flag('C'); self.set_flag('C', temp > 255); self.set_flag('Z', (temp&0xFF)==0); self.set_flag('V', (~(self.a^self.fetched)&(self.a^temp))&0x80); self.set_flag('N',temp&0x80); self.a=temp&0xFF; return 1
    def AND(self): self.fetch(); self.a &= self.fetched; self.set_flag('Z', self.a==0); self.set_flag('N', self.a&0x80); return 1
    def ASL(self): self.fetch(); temp=self.fetched<<1; self.set_flag('C', temp&0x100); self.set_flag('Z', (temp&0xFF)==0); self.set_flag('N',temp&0x80); (self.write(self.addr_abs, temp&0xFF) if self.lookup[self.opcode][2]!=self.IMP else setattr(self, 'a', temp&0xFF)); return 0
    def _branch(self, cond):
        if cond:
            self.cycles += 1
            self.addr_abs = self.pc + (np.int16(self.addr_rel) if self.addr_rel & 0x80 else self.addr_rel)
            if (self.addr_abs & 0xFF00) != (self.pc & 0xFF00):
                self.cycles += 1
            self.pc = self.addr_abs
        return 0
    def BCC(self): return self._branch(self.get_flag('C') == 0)
    def BCS(self): return self._branch(self.get_flag('C') == 1)
    def BEQ(self): return self._branch(self.get_flag('Z') == 1)
    def BIT(self): self.fetch(); self.set_flag('Z', (self.a&self.fetched)==0); self.set_flag('N', self.fetched&0x80); self.set_flag('V', self.fetched&0x40); return 0
    def BMI(self): return self._branch(self.get_flag('N') == 1)
    def BNE(self): return self._branch(self.get_flag('Z') == 0)
    def BPL(self): return self._branch(self.get_flag('N') == 0)
    def BRK(self): self.pc+=1; self.set_flag('I',1); self._push_stack((self.pc>>8)&0xFF); self._push_stack(self.pc&0xFF); self.set_flag('B',1); self._push_stack(self.status); self.set_flag('B',0); self.pc=self.read(0xFFFE)|(self.read(0xFFFF)<<8); return 0
    def BVC(self): return self._branch(self.get_flag('V') == 0)
    def BVS(self): return self._branch(self.get_flag('V') == 1)
    def CLC(self): self.set_flag('C', 0); return 0
    def CLD(self): self.set_flag('D', 0); return 0
    def CLI(self): self.set_flag('I', 0); return 0
    def CLV(self): self.set_flag('V', 0); return 0
    def CMP(self): self.fetch(); temp=self.a-self.fetched; self.set_flag('C',self.a>=self.fetched); self.set_flag('Z',(temp&0xFF)==0); self.set_flag('N',temp&0x80); return 1
    def CPX(self): self.fetch(); temp=self.x-self.fetched; self.set_flag('C',self.x>=self.fetched); self.set_flag('Z',(temp&0xFF)==0); self.set_flag('N',temp&0x80); return 0
    def CPY(self): self.fetch(); temp=self.y-self.fetched; self.set_flag('C',self.y>=self.fetched); self.set_flag('Z',(temp&0xFF)==0); self.set_flag('N',temp&0x80); return 0
    def DEC(self): self.fetch(); temp=(self.fetched-1)&0xFF; self.write(self.addr_abs, temp); self.set_flag('Z',temp==0); self.set_flag('N',temp&0x80); return 0
    def DEX(self): self.x=(self.x-1)&0xFF; self.set_flag('Z',self.x==0); self.set_flag('N',self.x&0x80); return 0
    def DEY(self): self.y=(self.y-1)&0xFF; self.set_flag('Z',self.y==0); self.set_flag('N',self.y&0x80); return 0
    def EOR(self): self.fetch(); self.a^=self.fetched; self.set_flag('Z',self.a==0); self.set_flag('N',self.a&0x80); return 1
    def INC(self): self.fetch(); temp=(self.fetched+1)&0xFF; self.write(self.addr_abs,temp); self.set_flag('Z',temp==0); self.set_flag('N',temp&0x80); return 0
    def INX(self): self.x=(self.x+1)&0xFF; self.set_flag('Z',self.x==0); self.set_flag('N',self.x&0x80); return 0
    def INY(self): self.y=(self.y+1)&0xFF; self.set_flag('Z',self.y==0); self.set_flag('N',self.y&0x80); return 0
    def JMP(self): self.pc = self.addr_abs; return 0
    def JSR(self): self.pc-=1; self._push_stack((self.pc>>8)&0xFF); self._push_stack(self.pc&0xFF); self.pc=self.addr_abs; return 0
    def LDA(self): self.fetch(); self.a=self.fetched; self.set_flag('Z',self.a==0); self.set_flag('N',self.a&0x80); return 1
    def LDX(self): self.fetch(); self.x=self.fetched; self.set_flag('Z',self.x==0); self.set_flag('N',self.x&0x80); return 1
    def LDY(self): self.fetch(); self.y=self.fetched; self.set_flag('Z',self.y==0); self.set_flag('N',self.y&0x80); return 1
    def LSR(self): self.fetch(); self.set_flag('C',self.fetched&1); temp=self.fetched>>1; self.set_flag('Z',temp==0); self.set_flag('N',0); (self.write(self.addr_abs,temp) if self.lookup[self.opcode][2]!=self.IMP else setattr(self,'a',temp)); return 0
    def NOP(self): return 0
    def ORA(self): self.fetch(); self.a|=self.fetched; self.set_flag('Z',self.a==0); self.set_flag('N',self.a&0x80); return 1
    def PHA(self): self._push_stack(self.a); return 0
    def PHP(self): self._push_stack(self.status|self.FLAGS['B']|self.FLAGS['U']); self.set_flag('B',0); self.set_flag('U',0); return 0
    def PLA(self): self.a=self._pop_stack(); self.set_flag('Z',self.a==0); self.set_flag('N',self.a&0x80); return 0
    def PLP(self): self.status=self._pop_stack(); self.set_flag('U',1); return 0
    def ROL(self): self.fetch(); temp=(self.fetched<<1)|self.get_flag('C'); self.set_flag('C',temp&0x100); self.set_flag('Z',(temp&0xFF)==0); self.set_flag('N',temp&0x80); (self.write(self.addr_abs,temp&0xFF) if self.lookup[self.opcode][2]!=self.IMP else setattr(self,'a',temp&0xFF)); return 0
    def ROR(self): self.fetch(); temp=(self.get_flag('C')<<7)|(self.fetched>>1); self.set_flag('C',self.fetched&1); self.set_flag('Z',(temp&0xFF)==0); self.set_flag('N',temp&0x80); (self.write(self.addr_abs,temp&0xFF) if self.lookup[self.opcode][2]!=self.IMP else setattr(self,'a',temp&0xFF)); return 0
    def RTI(self): self.status=self._pop_stack(); self.status&=~self.FLAGS['B']; self.status&=~self.FLAGS['U']; lo=self._pop_stack(); hi=self._pop_stack(); self.pc=(hi<<8)|lo; return 0
    def RTS(self): lo=self._pop_stack(); hi=self._pop_stack(); self.pc=((hi<<8)|lo)+1; return 0
    def SBC(self): self.fetch(); value=self.fetched^0xFF; temp=self.a+value+self.get_flag('C'); self.set_flag('C',temp&0x100); self.set_flag('Z',(temp&0xFF)==0); self.set_flag('V',((temp^self.a)&(temp^value))&0x80); self.set_flag('N',temp&0x80); self.a=temp&0xFF; return 1
    def SEC(self): self.set_flag('C', 1); return 0
    def SED(self): self.set_flag('D', 1); return 0
    def SEI(self): self.set_flag('I', 1); return 0
    def STA(self): self.write(self.addr_abs, self.a); return 0
    def STX(self): self.write(self.addr_abs, self.x); return 0
    def STY(self): self.write(self.addr_abs, self.y); return 0
    def TAX(self): self.x=self.a; self.set_flag('Z',self.x==0); self.set_flag('N',self.x&0x80); return 0
    def TAY(self): self.y=self.a; self.set_flag('Z',self.y==0); self.set_flag('N',self.y&0x80); return 0
    def TSX(self): self.x=self.sp; self.set_flag('Z',self.x==0); self.set_flag('N',self.x&0x80); return 0
    def TXA(self): self.a=self.x; self.set_flag('Z',self.a==0); self.set_flag('N',self.a&0x80); return 0
    def TXS(self): self.sp = self.x; return 0
    def TYA(self): self.a=self.y; self.set_flag('Z',self.a==0); self.set_flag('N',self.a&0x80); return 0


class NESEmulator:
    def __init__(self, root):
        self.root = root
        self.root.title("NES Emulator")
        
        self.nes = Bus()
        
        menubar = tk.Menu(root)
        root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open ROM...", command=self.load_rom)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=root.quit)
        
        self.canvas = tk.Canvas(root, width=256*2, height=240*2, bg='black')
        self.canvas.pack()
        
        control_frame = tk.Frame(root)
        control_frame.pack(pady=5)
        
        self.run_button = tk.Button(control_frame, text="Run", command=self.toggle_run, width=10)
        self.run_button.pack(side=tk.LEFT, padx=5)
        
        self.reset_button = tk.Button(control_frame, text="Reset", command=self.reset, width=10)
        self.reset_button.pack(side=tk.LEFT, padx=5)
        
        self.status_var = tk.StringVar()
        self.status_var.set("No ROM loaded. Go to File > Open ROM...")
        self.status_label = tk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor='w')
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM, ipady=2)
        
        self.running = False
        self.rom_loaded = False
        self.photo = None
        
    def load_rom(self):
        filename = filedialog.askopenfilename(
            title="Open NES ROM",
            filetypes=[("NES ROM files", "*.nes"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.running = False
                self.run_button.config(text="Run")
                cartridge = Cartridge(filename)
                self.nes.insert_cartridge(cartridge)
                self.nes.reset()
                self.rom_loaded = True
                self.status_var.set(f"Loaded: {filename.split('/')[-1]}")
                self.update_display()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load ROM: {str(e)}")
    
    def toggle_run(self):
        if self.rom_loaded:
            self.running = not self.running
            if self.running:
                self.run_button.config(text="Pause")
                self.run_emulation()
            else:
                self.run_button.config(text="Run")
    
    def reset(self):
        if self.rom_loaded:
            self.running = False
            self.run_button.config(text="Run")
            self.nes.reset()
            self.update_display()
    
    def run_emulation(self):
        if self.running:
            # Execute clocks until one full frame is rendered
            while not self.nes.ppu.frame_complete:
                self.nes.clock()
            self.nes.ppu.frame_complete = False
            
            self.update_display()
            
            # [FIX 9] Schedule next frame using root.after for stable 60 FPS
            self.root.after(16, self.run_emulation)
    
    def update_display(self):
        img = Image.fromarray(self.nes.ppu.screen, 'RGB')
        img = img.resize((256*2, 240*2), Image.Resampling.NEAREST)
        self.photo = ImageTk.PhotoImage(image=img)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)


if __name__ == "__main__":
    root = tk.Tk()
    emulator = NESEmulator(root)
    root.mainloop()

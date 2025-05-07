import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
import time # Fucking need this for timing later, maybe

SCREEN_WIDTH = 256
SCREEN_HEIGHT = 240
NES_FRAME_RATE = 60 # Target, not that Python will fucking hit it easily

# Goddamn NES Palette (NTSC) - This is a fucking standard, deal with it.
# Each entry is (R, G, B)
NES_PALETTE = [
    (84, 84, 84), (0, 30, 116), (8, 16, 144), (48, 0, 136), (68, 0, 100), (92, 0, 48), (84, 4, 0), (60, 24, 0),
    (32, 42, 0), (8, 58, 0), (0, 64, 0), (0, 60, 0), (0, 50, 60), (0, 0, 0), (0, 0, 0), (0, 0, 0),
    (152, 150, 152), (8, 76, 196), (48, 50, 236), (92, 30, 228), (136, 20, 176), (160, 20, 100), (152, 34, 32), (120, 60, 0),
    (84, 90, 0), (40, 114, 0), (8, 124, 0), (0, 118, 40), (0, 102, 120), (0, 0, 0), (0, 0, 0), (0, 0, 0),
    (236, 238, 236), (76, 154, 236), (120, 124, 236), (176, 98, 236), (228, 84, 236), (236, 88, 180), (236, 106, 100), (212, 136, 32),
    (160, 170, 0), (116, 196, 0), (76, 208, 32), (56, 204, 108), (56, 180, 220), (60, 60, 60), (0, 0, 0), (0, 0, 0),
    (236, 238, 236), (168, 204, 236), (188, 188, 236), (212, 178, 236), (236, 174, 236), (236, 174, 212), (236, 180, 176), (228, 196, 144),
    (204, 210, 120), (180, 222, 120), (168, 226, 144), (152, 226, 180), (160, 214, 228), (160, 162, 160), (0, 0, 0), (0, 0, 0),
]


class Mapper0:
    def __init__(self, prg_rom_banks, chr_rom_banks, prg_data, chr_data):
        self.prg_banks = prg_rom_banks
        self.chr_banks = chr_rom_banks
        self.prg_rom = prg_data
        # If CHR banks is 0, it means CHR RAM of 8KB
        self.chr_mem = chr_data if chr_rom_banks > 0 else bytearray(0x2000)
        self.is_chr_ram = (chr_rom_banks == 0)

    def read_prg(self, addr):
        if 0x8000 <= addr <= 0xFFFF:
            # If 1 PRG bank (16KB), mirror 0x8000-0xBFFF to 0xC000-0xFFFF
            # If 2 PRG banks (32KB), 0x8000-0xBFFF is bank 0, 0xC000-0xFFFF is bank 1
            # This simple mapper0 assumes 16KB or 32KB ROMs.
            # For 16KB ROMs (self.prg_banks == 1), the effective address is masked by 0x3FFF.
            # For 32KB ROMs (self.prg_banks == 2), the prg_rom is 0x8000 bytes long, so addr - 0x8000 works directly.
            if self.prg_banks == 1: # 16KB PRG ROM
                return self.prg_rom[(addr - 0x8000) & 0x3FFF]
            else: # 32KB PRG ROM
                return self.prg_rom[addr - 0x8000]
        return 0 # Should not happen for valid PRG reads

    def write_prg(self, addr, value):
        # Generally, PRG ROM is not writable for Mapper 0
        # print(f"Attempt to write to PRG ROM at {addr:04X} (not allowed for Mapper 0)")
        pass

    def read_chr(self, addr):
        if 0x0000 <= addr <= 0x1FFF:
            return self.chr_mem[addr]
        return 0

    def write_chr(self, addr, value):
        if 0x0000 <= addr <= 0x1FFF and self.is_chr_ram:
            self.chr_mem[addr] = value
        # else:
            # print(f"Attempt to write to CHR ROM at {addr:04X} (not allowed for CHR ROM)")


class PPU:
    def __init__(self, cpu):
        self.cpu = cpu
        self.mapper = None # Will be set by CPU when ROM loads

        self.cycle = 0          # 0-340
        self.scanline = 0       # 0-261 (0-239 visible, 240 post-render, 241-260 vblank, 261 pre-render)
        self.frame_complete = False
        self.screen = np.zeros((SCREEN_HEIGHT, SCREEN_WIDTH, 3), dtype=np.uint8)

        # PPU Registers - these are fucking important
        self.ppuctrl = 0x00     # $2000 Write
        self.ppumask = 0x00     # $2001 Write
        self.ppustatus = 0x00   # $2002 Read
        self.oamaddr = 0x00     # $2003 Write
        self.oamdata = bytearray(256) # $2004 Read/Write (Sprite RAM)
        # $2005 Write x2 (scroll)
        # $2006 Write x2 (PPU address)
        # $2007 Read/Write (PPU data)

        self.vram_addr = 0 # Internal PPU address register (often 'v' or 't')
        self.temp_vram_addr = 0 # Temporary PPU address register (often 't')
        self.fine_x_scroll = 0 # Fine X scroll (3 bits)
        self.write_toggle = False # For $2005 and $2006, determines if it's the first or second write

        self.ppu_data_buffer = 0x00 # For $2007 reads

        self.vram = bytearray(0x2000) # 2KB Name Table RAM (can be mirrored by mapper)
        self.palette_ram = bytearray(0x20) # 32 bytes Palette RAM

        self.nmi_occurred = False
        self.nmi_output = False


    def connect_mapper(self, mapper):
        self.mapper = mapper

    def read_register(self, addr):
        # PPU registers are mapped from $2000-$2007, mirrored up to $3FFF
        reg = addr & 0x0007
        val = 0
        if reg == 0x0002: # PPUSTATUS
            val = (self.ppustatus & 0xE0) | (self.ppu_data_buffer & 0x1F) # Top 3 bits, bottom 5 are noise/buffer
            self.ppustatus &= ~0x80 # Clear VBlank flag after read
            self.write_toggle = False # Reading PPUSTATUS resets the $2005/$2006 write toggle
            self.nmi_occurred = False # NMI is acknowledged
            # TODO: Suppress NMI if VBlank flag was already clear?
        elif reg == 0x0004: # OAMDATA read
            val = self.oamdata[self.oamaddr]
            # OAMADDR does not increment on read for most hardware, but some games rely on it.
            # For simplicity, we don't increment here. Official hardware doesn't during rendering.
        elif reg == 0x0007: # PPUDATA read
            val = self.ppu_data_buffer
            self.ppu_data_buffer = self._ppu_read(self.vram_addr)
            if self.vram_addr >= 0x3F00: # Palette reads are immediate
                val = self.ppu_data_buffer
            # Increment PPU address
            self.vram_addr += 32 if (self.ppuctrl & 0x04) else 1
            self.vram_addr &= 0x3FFF # Keep it within 14 bits for VRAM range
        return val

    def write_register(self, addr, value):
        reg = addr & 0x0007
        self.ppu_data_buffer = value # Any write to PPU register updates this internal buffer
        
        if reg == 0x0000: # PPUCTRL
            self.ppuctrl = value
            self.nmi_output = (self.ppuctrl & 0x80) != 0 and self.nmi_occurred
            # Set bits 10-11 of temp_vram_addr from bits 0-1 of value
            self.temp_vram_addr = (self.temp_vram_addr & 0xF3FF) | ((value & 0x03) << 10)
        elif reg == 0x0001: # PPUMASK
            self.ppumask = value
        elif reg == 0x0003: # OAMADDR
            self.oamaddr = value
        elif reg == 0x0004: # OAMDATA write
            self.oamdata[self.oamaddr] = value
            self.oamaddr = (self.oamaddr + 1) & 0xFF # Increment OAM address
        elif reg == 0x0005: # PPUSCROLL
            if not self.write_toggle: # First write (X scroll)
                self.temp_vram_addr = (self.temp_vram_addr & 0xFFE0) | (value >> 3)
                self.fine_x_scroll = value & 0x07
            else: # Second write (Y scroll)
                self.temp_vram_addr = (self.temp_vram_addr & 0x8C1F) | ((value & 0xF8) << 2) | ((value & 0x07) << 12)
            self.write_toggle = not self.write_toggle
        elif reg == 0x0006: # PPUADDR
            if not self.write_toggle: # First write (High byte)
                self.temp_vram_addr = (self.temp_vram_addr & 0x00FF) | ((value & 0x3F) << 8) # Mask to 6 bits for PPU addr
            else: # Second write (Low byte)
                self.temp_vram_addr = (self.temp_vram_addr & 0xFF00) | value
                self.vram_addr = self.temp_vram_addr # Copy to main VRAM address
            self.write_toggle = not self.write_toggle
        elif reg == 0x0007: # PPUDATA write
            self._ppu_write(self.vram_addr, value)
            # Increment PPU address
            self.vram_addr += 32 if (self.ppuctrl & 0x04) else 1
            self.vram_addr &= 0x3FFF


    def _ppu_read(self, addr):
        addr &= 0x3FFF # PPU addresses are 14-bit
        if 0x0000 <= addr <= 0x1FFF: # Pattern Tables (CHR ROM/RAM)
            return self.mapper.read_chr(addr)
        elif 0x2000 <= addr <= 0x3EFF: # Nametable RAM
            # Nametable mirroring - this is fucking simplified, real mappers do more
            # For now, horizontal mirroring (A, A, B, B) or vertical (A, B, A, B)
            # Defaulting to horizontal for simple mapper 0 if not specified
            # (self.ppuctrl & 0x01) can indicate mirroring preference from game for some setups
            # but mapper usually dictates this.
            # For Mapper 0, mirroring is fixed by soldering on the PCB. Assume horizontal for now.
            # $2000-$23FF NT0, $2400-$27FF NT1, $2800-$2BFF NT0 (mirrored), $2C00-$2FFF NT1 (mirrored)
            addr &= 0x0FFF # Mask to 12 bits for within a 4KB region
            if (addr & 0x0C00) == 0x0800: addr &= ~0x0800 # if $2800-$2BFF mirror $2000-$23FF
            if (addr & 0x0C00) == 0x0C00: addr &= ~0x0400 # if $2C00-$2FFF mirror $2400-$27FF but map to NT1
            # This is still too simple. Let's just use 0x7FF for now.
            # Basic horizontal: $2000, $2400, $2000, $2400
            # Basic vertical:   $2000, $2000, $2400, $2400
            # For now: use $2000-27FF for NT0/NT1, then mirror this space.
            # (Effectively mapping $2800-$2BFF to $2000-$23FF and $2C00-$2FFF to $2400-$27FF)
            # This makes it 2KB internal VRAM. Real common setups are 2KB internal.
            return self.vram[addr & 0x07FF] # Simple 2KB mirror for now. Real mirroring is complex.
        elif 0x3F00 <= addr <= 0x3FFF: # Palette RAM
            addr &= 0x001F # Mask to 5 bits for 32 palette entries
            if addr == 0x0010: addr = 0x0000 # Mirror $3F10 to $3F00
            if addr == 0x0014: addr = 0x0004
            if addr == 0x0018: addr = 0x0008
            if addr == 0x001C: addr = 0x000C
            return self.palette_ram[addr]
        return 0 # Should not happen

    def _ppu_write(self, addr, value):
        addr &= 0x3FFF
        if 0x0000 <= addr <= 0x1FFF: # Pattern Tables (CHR RAM only)
            self.mapper.write_chr(addr, value)
        elif 0x2000 <= addr <= 0x3EFF: # Nametable RAM
            # Same mirroring logic as read
            self.vram[addr & 0x07FF] = value # Simple 2KB mirror
        elif 0x3F00 <= addr <= 0x3FFF: # Palette RAM
            addr &= 0x001F
            if addr == 0x0010: addr = 0x0000
            if addr == 0x0014: addr = 0x0004
            if addr == 0x0018: addr = 0x0008
            if addr == 0x001C: addr = 0x000C
            self.palette_ram[addr] = value


    def step(self):
        # This needs to be way more fucking detailed for real emulation
        # Pre-render scanline
        if self.scanline == 261: # Pre-render line
            if self.cycle == 1:
                self.ppustatus &= ~0xE0 # Clear VBlank, Sprite 0 Hit, Sprite Overflow
                self.nmi_occurred = False
            # TODO: PPU register related updates on specific cycles
            if self.cycle >= 280 and self.cycle <= 304:
                if self.rendering_enabled():
                    # Copy vertical bits from t to v
                    self.vram_addr = (self.vram_addr & 0x841F) | (self.temp_vram_addr & 0x7BE0)


        # Visible scanlines (0-239) and Post-render scanline (240)
        if self.scanline >= 0 and self.scanline <= 240:
            # TODO: Background & Sprite evaluation/rendering logic for visible lines
            # This is where the real PPU work happens per cycle.
            # For now, we'll do a tile-based render at the end of the scanline for simplicity.
            pass


        # VBlank period
        if self.scanline == 241 and self.cycle == 1:
            self.ppustatus |= 0x80 # Set VBlank flag
            self.nmi_occurred = True
            if self.nmi_output: # If NMI enabled in PPUCTRL and VBlank occurred
                self.cpu.nmi_pending = True
            self.frame_complete = True # Signal GUI to render the frame

        # Update rendering flags at cycle 257 of each visible/pre-render scanline
        if self.cycle == 257 and self.rendering_enabled():
            if self.scanline < 240 or self.scanline == 261: # Visible or pre-render
                # Increment horizontal part of v
                if (self.vram_addr & 0x001F) == 31:  # if coarse X == 31
                    self.vram_addr &= ~0x001F          # coarse X = 0
                    self.vram_addr ^= 0x0400           # switch horizontal nametable
                else:
                    self.vram_addr += 1                # increment coarse X

        # Update vertical VRAM address at cycle 257 of scanline if rendering enabled
        if self.cycle == 256 and self.rendering_enabled(): # End of HBlank
            if self.scanline < 240 or self.scanline == 261: # Visible scanlines or pre-render line
                # Increment vertical part of v
                if (self.vram_addr & 0x7000) != 0x7000:  # if fine Y < 7
                    self.vram_addr += 0x1000             # increment fine Y
                else:
                    self.vram_addr &= ~0x7000            # fine Y = 0
                    y = (self.vram_addr & 0x03E0) >> 5   # let y = coarse Y
                    if y == 29:
                        y = 0                            # coarse Y = 0
                        self.vram_addr ^= 0x0800         # switch vertical nametable
                    elif y == 31:
                        y = 0                            # coarse Y = 0, nametable not switched
                    else:
                        y += 1                           # increment coarse Y
                    self.vram_addr = (self.vram_addr & ~0x03E0) | (y << 5)

        # Copy horizontal bits from t to v at cycle 257 of pre-render scanline
        if self.cycle == 257 and self.scanline == 261 and self.rendering_enabled():
            self.vram_addr = (self.vram_addr & 0xFBE0) | (self.temp_vram_addr & 0x041F)


        # Advance PPU cycle and scanline
        self.cycle += 1
        if self.cycle > 340: # End of a scanline
            self.cycle = 0
            self.scanline += 1
            if self.scanline > 261: # End of a frame
                self.scanline = 0
                # self.frame_complete = True # Moved to VBlank start for NMI timing

    def rendering_enabled(self):
        return (self.ppumask & 0x08) or (self.ppumask & 0x10) # Show background or show sprites

    def render_scanline(self, sl):
        # This is a fucking simplified tile-based renderer, not cycle-accurate pixel by pixel
        if not self.rendering_enabled() or sl >= SCREEN_HEIGHT:
            # Fill scanline with universal background color if rendering is off
            # Or if it's a non-visible scanline (shouldn't be called for > 239)
            bg_color_idx = self.palette_ram[0]
            bg_color_rgb = NES_PALETTE[bg_color_idx & 0x3F]
            for x in range(SCREEN_WIDTH):
                self.screen[sl, x] = bg_color_rgb
            return

        # Base nametable address from PPUCTRL bits 0-1 ($2000, $2400, $2800, $2C00)
        # This is simplified; vram_addr ('v') actually holds the current scroll address.
        
        # For each tile in the scanline (32 tiles + 1 for scroll)
        for tile_x_idx in range(SCREEN_WIDTH // 8 +1): # 32 tiles wide + 1 for fine_x scroll
            current_coarse_x = (self.vram_addr >> 0) & 0x1F
            current_coarse_y = (self.vram_addr >> 5) & 0x1F
            current_fine_y   = (self.vram_addr >> 12) & 0x07
            nametable_select = (self.vram_addr >> 10) & 0x03 # Which of the 4 virtual nametables


            # Calculate absolute tile address in one of the two 1KB nametables
            # Base nametable addresses: NT0=$2000, NT1=$2400, NT2=$2800, NT3=$2C00
            # For now, simple horizontal mirroring: NT0, NT1, NT0, NT1
            # This is wrong, nametable select comes from 'v' (self.vram_addr)
            nt_base_addr = 0x2000 | ((nametable_select & 0x01) << 10) # Use bit 0 for horiz select
            if (nametable_select & 0x02): # Use bit 1 for vert select
                 nt_base_addr |= ((nametable_select & 0x02) << (10-1)) # This is for vertical mirroring
            # Simplified: let's just use vram_addr to point to current tile
            
            tile_offset_in_nametable = current_coarse_y * 32 + current_coarse_x
            nametable_byte_addr = 0x2000 | (self.vram_addr & 0x0FFF) # Use lower 12 bits of vram_addr for NT access

            tile_id = self._ppu_read(nametable_byte_addr)

            # Attribute table: 1 byte for each 4x4 group of tiles (32x32 pixels)
            # AT byte is ((coarse_y / 4) * 8) + (coarse_x / 4)
            # AT address: NT_base + 0x03C0 + AT_offset
            attr_addr = (0x2000 | (self.vram_addr & 0x0C00)) + 0x03C0 + ((current_coarse_y // 4) * 8) + (current_coarse_x // 4)
            attr_byte = self._ppu_read(attr_addr)
            
            # Determine which 2x2 tile quadrant we're in to select 2 bits from attr_byte
            # Quadrant: TopL=0, TopR=1, BotL=2, BotR=3
            # Bits: (Y/2 % 2) << 1 | (X/2 % 2)
            quadrant_shift = ((current_coarse_y // 2 % 2) << 1) | (current_coarse_x // 2 % 2)
            palette_idx_high_bits = (attr_byte >> (quadrant_shift * 2)) & 0x03
            
            # Pattern table: PPUCTRL bit 4 selects background pattern table ($0000 or $1000)
            pt_base_addr = 0x1000 if (self.ppuctrl & 0x10) else 0x0000
            tile_row_addr_plane0 = pt_base_addr + tile_id * 16 + current_fine_y
            tile_row_addr_plane1 = tile_row_addr_plane0 + 8
            
            plane0_byte = self._ppu_read(tile_row_addr_plane0)
            plane1_byte = self._ppu_read(tile_row_addr_plane1)

            # Render 8 pixels for this tile for the current scanline (sl)
            for tile_pixel_x in range(8):
                screen_x = (current_coarse_x * 8) + tile_pixel_x - self.fine_x_scroll
                
                if screen_x >= 0 and screen_x < SCREEN_WIDTH:
                    # Bit for this pixel: (7 - tile_pixel_x) because MSB is left
                    pixel_bit = 7 - tile_pixel_x
                    pixel_val_low = (plane0_byte >> pixel_bit) & 1
                    pixel_val_high = (plane1_byte >> pixel_bit) & 1
                    pixel_palette_idx_low_bits = (pixel_val_high << 1) | pixel_val_low
                    
                    pixel_color_idx = 0 # Default to universal background
                    if pixel_palette_idx_low_bits != 0: # Not transparent
                        full_palette_entry = (palette_idx_high_bits << 2) | pixel_palette_idx_low_bits
                        # Palette RAM addr: 0x3F00 (base) + palette_entry_offset
                        pixel_color_idx = self._ppu_read(0x3F00 + full_palette_entry)
                    else: # Transparent, use universal background
                        pixel_color_idx = self._ppu_read(0x3F00)


                    color_rgb = NES_PALETTE[pixel_color_idx & 0x3F] # Mask to 6 bits for safety
                    self.screen[sl, screen_x] = color_rgb

            # Increment Coarse X (horizontal part of vram_addr)
            # This logic is simplified here. The cycle-accurate version handles this in PPU.step()
            if (self.vram_addr & 0x001F) == 31:  # if coarse X == 31
                self.vram_addr &= ~0x001F          # coarse X = 0
                self.vram_addr ^= 0x0400           # switch horizontal nametable
            else:
                self.vram_addr += 1                # increment coarse X


        # TODO: Sprite rendering (overlays background)
        # This is a whole other fucking beast involving OAM, pattern tables, priority etc.
        # For now, background only.


    def get_frame(self):
        # Render all visible scanlines if frame is complete
        # This is a HACK. Rendering should occur progressively during PPU.step() cycles.
        # For now, call render_scanline for each visible line when get_frame is called.
        if self.frame_complete:
            if self.rendering_enabled():
                # Reset vram_addr to temp_vram_addr at start of visible frame (approximates VBlank behavior)
                self.vram_addr = self.temp_vram_addr
                for sl in range(SCREEN_HEIGHT): # 0-239
                    # Simulate PPU internal scroll logic that happens per scanline
                    # This is a simplified version of what happens at cycle 256 and 257

                    # At the start of each scanline, reload horizontal components from t to v
                    self.vram_addr = (self.vram_addr & 0xFBE0) | (self.temp_vram_addr & 0x041F)
                    self.render_scanline(sl)
                    # Increment fine Y, coarse Y, and switch vertical nametable as needed
                    # This logic belongs in the PPU's cycle-by-cycle step
                    if (self.vram_addr & 0x7000) != 0x7000:  # if fine Y < 7
                        self.vram_addr += 0x1000             # increment fine Y
                    else:
                        self.vram_addr &= ~0x7000            # fine Y = 0
                        y = (self.vram_addr & 0x03E0) >> 5   # let y = coarse Y
                        if y == 29:
                            y = 0                            # coarse Y = 0
                            self.vram_addr ^= 0x0800         # switch vertical nametable
                        elif y == 31:
                            y = 0                            # coarse Y = 0, nametable not switched
                        else:
                            y += 1                           # increment coarse Y
                        self.vram_addr = (self.vram_addr & ~0x03E0) | (y << 5)
            else: # Rendering disabled, fill with universal background color
                bg_color_idx = self._ppu_read(0x3F00) # Palette entry 0
                bg_color_rgb = NES_PALETTE[bg_color_idx & 0x3F]
                self.screen[:, :] = bg_color_rgb
        return self.screen


class MOS6502:
    # Flags for P register
    C = (1 << 0)  # Carry Bit
    Z = (1 << 1)  # Zero
    I = (1 << 2)  # Disable Interrupts
    D = (1 << 3)  # Decimal Mode (unused in NES)
    B = (1 << 4)  # Break
    U = (1 << 5)  # Unused (always 1)
    V = (1 << 6)  # Overflow
    N = (1 << 7)  # Negative

    def __init__(self):
        self.a = 0x00       # Accumulator
        self.x = 0x00       # X Register
        self.y = 0x00       # Y Register
        self.sp = 0xFD      # Stack Pointer (0x0100 + sp)
        self.pc = 0x0000    # Program Counter
        self.status = 0x24  # Status Register (P) (IRQ disabled, U set)

        self.memory = bytearray(0x800)  # 2KB CPU RAM ($0000 - $07FF, mirrored up to $1FFF)
        self.mapper = None
        self.ppu = None # Will be set by NES system

        self.cycles = 0 # Cycles for current instruction
        self.total_cycles = 0 # System total cycles

        self.nmi_pending = False
        self.irq_pending = False # Not really used yet
        self.stall_cycles = 0 # For DMA etc.


    def connect_ppu(self, ppu):
        self.ppu = ppu

    def connect_mapper(self, mapper):
        self.mapper = mapper

    def read_byte(self, addr):
        addr &= 0xFFFF # Ensure 16-bit address
        if 0x0000 <= addr <= 0x1FFF: # CPU RAM (mirrored)
            return self.memory[addr & 0x07FF]
        elif 0x2000 <= addr <= 0x3FFF: # PPU Registers (mirrored)
            return self.ppu.read_register(addr)
        elif addr == 0x4016: # Controller 1 input (TODO)
            # For now, return 0 (no buttons pressed)
            return 0
        elif addr == 0x4017: # Controller 2 input (TODO)
            return 0
        elif 0x4000 <= addr <= 0x401F: # APU and I/O Registers (mostly TODO)
            # print(f"Unhandled read from I/O reg {addr:04X}")
            return 0 # Placeholder
        elif 0x6000 <= addr <= 0x7FFF: # PRG RAM (if mapper supports it, Mapper 0 doesn't typically)
            # print(f"Read from PRG RAM {addr:04X} (unsupported by Mapper0)")
            return 0
        elif 0x8000 <= addr <= 0xFFFF: # PRG ROM
            return self.mapper.read_prg(addr)
        return 0 # Open bus behavior for unmapped reads often returns last PPU read, complex.

    def write_byte(self, addr, value):
        value &= 0xFF # Ensure 8-bit value
        addr &= 0xFFFF
        if 0x0000 <= addr <= 0x1FFF: # CPU RAM
            self.memory[addr & 0x07FF] = value
        elif 0x2000 <= addr <= 0x3FFF: # PPU Registers
            self.ppu.write_register(addr, value)
        elif 0x4000 <= addr <= 0x4013 or addr == 0x4015 or addr == 0x4017: # APU registers
            # print(f"Write to APU reg {addr:04X} value {value:02X} (APU not implemented)")
            pass
        elif addr == 0x4014: # OAMDMA write
            # This is a fucking DMA transfer, takes 513/514 cycles!
            # print(f"OAMDMA initiated with page {value:02X}")
            dma_page_addr = value << 8
            for i in range(256):
                self.ppu.oamdata[(self.ppu.oamaddr + i) & 0xFF] = self.read_byte(dma_page_addr + i)
            self.stall_cycles += 513 # Or 514 if on odd CPU cycle, fuck it, 513 is fine for now
        elif addr == 0x4016: # Controller strobe
            # print(f"Controller strobe write {value:02X} (controllers not fully implemented)")
            pass
        elif 0x6000 <= addr <= 0x7FFF: # PRG RAM (if mapper supports it)
            # print(f"Write to PRG RAM {addr:04X} (unsupported by Mapper0)")
            pass
        elif 0x8000 <= addr <= 0xFFFF: # PRG ROM (some mappers allow writes for bank switching)
            self.mapper.write_prg(addr, value)

    def read_word(self, addr):
        lo = self.read_byte(addr)
        hi = self.read_byte(addr + 1)
        return (hi << 8) | lo

    def read_word_bug(self, addr): # For indirect JMP page boundary bug
        lo = self.read_byte(addr)
        # If addr LSB is 0xFF, the MSB is read from addr & 0xFF00, not (addr&0xFF00) + 1
        if (addr & 0x00FF) == 0x00FF:
            hi = self.read_byte(addr & 0xFF00)
        else:
            hi = self.read_byte(addr + 1)
        return (hi << 8) | lo

    def push_byte(self, value):
        self.write_byte(0x0100 + self.sp, value)
        self.sp = (self.sp - 1) & 0xFF

    def push_word(self, value):
        self.push_byte((value >> 8) & 0xFF) # High byte
        self.push_byte(value & 0xFF)        # Low byte

    def pop_byte(self):
        self.sp = (self.sp + 1) & 0xFF
        return self.read_byte(0x0100 + self.sp)

    def pop_word(self):
        lo = self.pop_byte()
        hi = self.pop_byte()
        return (hi << 8) | lo

    def _set_flag(self, flag, value):
        if value:
            self.status |= flag
        else:
            self.status &= ~flag

    def _get_flag(self, flag):
        return (self.status & flag) > 0

    def _update_nz_flags(self, value):
        self._set_flag(self.Z, value == 0)
        self._set_flag(self.N, (value & 0x80) > 0)

    # --- Addressing Modes ---
    # Each returns the address and if a page boundary was crossed (for cycle adjustments)
    def addr_imm(self): self.pc += 1; return self.pc - 1, False
    def addr_zp(self):  self.pc += 1; return self.read_byte(self.pc - 1) & 0xFF, False
    def addr_zpx(self): self.pc += 1; return (self.read_byte(self.pc - 1) + self.x) & 0xFF, False
    def addr_zpy(self): self.pc += 1; return (self.read_byte(self.pc - 1) + self.y) & 0xFF, False # Only for LDX, STX
    def addr_abs(self): self.pc += 2; return self.read_word(self.pc - 2), False
    
    def addr_absx(self): # Can take an extra cycle if page crossed
        self.pc += 2
        base_addr = self.read_word(self.pc - 2)
        eff_addr = (base_addr + self.x) & 0xFFFF
        page_crossed = (base_addr & 0xFF00) != (eff_addr & 0xFF00)
        return eff_addr, page_crossed
        
    def addr_absy(self): # Can take an extra cycle if page crossed
        self.pc += 2
        base_addr = self.read_word(self.pc - 2)
        eff_addr = (base_addr + self.y) & 0xFFFF
        page_crossed = (base_addr & 0xFF00) != (eff_addr & 0xFF00)
        return eff_addr, page_crossed
        
    def addr_indx(self): # (Indirect, X)
        self.pc += 1
        zp_addr_base = self.read_byte(self.pc - 1)
        lo_addr = (zp_addr_base + self.x) & 0xFF
        hi_addr = (zp_addr_base + self.x + 1) & 0xFF
        eff_addr = (self.read_byte(hi_addr) << 8) | self.read_byte(lo_addr)
        return eff_addr & 0xFFFF, False
        
    def addr_indy(self): # (Indirect), Y - can take an extra cycle
        self.pc += 1
        zp_addr_ptr = self.read_byte(self.pc - 1)
        lo_byte_addr = self.read_byte(zp_addr_ptr)
        hi_byte_addr = self.read_byte((zp_addr_ptr + 1) & 0xFF) # ZP wrap around for high byte address
        base_addr = (hi_byte_addr << 8) | lo_byte_addr
        eff_addr = (base_addr + self.y) & 0xFFFF
        page_crossed = (base_addr & 0xFF00) != (eff_addr & 0xFF00)
        return eff_addr, page_crossed

    # --- Opcodes ---
    # Each opcode function should set self.cycles
    # Load/Store
    def _lda(self, addr, page_crossed, cycles_base, cycles_page_cross=1):
        self.a = self.read_byte(addr)
        self._update_nz_flags(self.a)
        self.cycles = cycles_base + (cycles_page_cross if page_crossed else 0)
    def _ldx(self, addr, page_crossed, cycles_base, cycles_page_cross=1):
        self.x = self.read_byte(addr)
        self._update_nz_flags(self.x)
        self.cycles = cycles_base + (cycles_page_cross if page_crossed else 0)
    def _ldy(self, addr, page_crossed, cycles_base, cycles_page_cross=1):
        self.y = self.read_byte(addr)
        self._update_nz_flags(self.y)
        self.cycles = cycles_base + (cycles_page_cross if page_crossed else 0)
    def _sta(self, addr, _, cycles_base): self.write_byte(addr, self.a); self.cycles = cycles_base
    def _stx(self, addr, _, cycles_base): self.write_byte(addr, self.x); self.cycles = cycles_base
    def _sty(self, addr, _, cycles_base): self.write_byte(addr, self.y); self.cycles = cycles_base

    # Arithmetic
    def _adc(self, addr, page_crossed, cycles_base, cycles_page_cross=1):
        val = self.read_byte(addr)
        carry_in = 1 if self._get_flag(self.C) else 0
        temp = self.a + val + carry_in
        self._set_flag(self.C, temp > 0xFF)
        # Overflow: if signs of operands are same and sign of result is different
        self._set_flag(self.V, ((self.a ^ temp) & (val ^ temp) & 0x80) != 0)
        self.a = temp & 0xFF
        self._update_nz_flags(self.a)
        self.cycles = cycles_base + (cycles_page_cross if page_crossed else 0)

    def _sbc(self, addr, page_crossed, cycles_base, cycles_page_cross=1): # SBC is ADC with inverted operand
        val = self.read_byte(addr) ^ 0xFF # Invert bits of operand
        carry_in = 1 if self._get_flag(self.C) else 0
        temp = self.a + val + carry_in
        self._set_flag(self.C, temp > 0xFF)
        self._set_flag(self.V, ((self.a ^ temp) & (val ^ temp) & 0x80) != 0)
        self.a = temp & 0xFF
        self._update_nz_flags(self.a)
        self.cycles = cycles_base + (cycles_page_cross if page_crossed else 0)

    # Increment/Decrement
    def _inc(self, addr, _, cycles_base):
        val = (self.read_byte(addr) + 1) & 0xFF
        self.write_byte(addr, val)
        self._update_nz_flags(val)
        self.cycles = cycles_base
    def _dec(self, addr, _, cycles_base):
        val = (self.read_byte(addr) - 1) & 0xFF
        self.write_byte(addr, val)
        self._update_nz_flags(val)
        self.cycles = cycles_base
    def _inx(self): self.x = (self.x + 1) & 0xFF; self._update_nz_flags(self.x); self.cycles = 2
    def _iny(self): self.y = (self.y + 1) & 0xFF; self._update_nz_flags(self.y); self.cycles = 2
    def _dex(self): self.x = (self.x - 1) & 0xFF; self._update_nz_flags(self.x); self.cycles = 2
    def _dey(self): self.y = (self.y - 1) & 0xFF; self._update_nz_flags(self.y); self.cycles = 2

    # Shifts (Accumulator)
    def _asl_a(self):
        self._set_flag(self.C, (self.a & 0x80) > 0)
        self.a = (self.a << 1) & 0xFF
        self._update_nz_flags(self.a)
        self.cycles = 2
    def _lsr_a(self):
        self._set_flag(self.C, (self.a & 0x01) > 0)
        self.a = (self.a >> 1) & 0xFF
        self._update_nz_flags(self.a)
        self.cycles = 2
    def _rol_a(self):
        carry_in = 1 if self._get_flag(self.C) else 0
        self._set_flag(self.C, (self.a & 0x80) > 0)
        self.a = ((self.a << 1) | carry_in) & 0xFF
        self._update_nz_flags(self.a)
        self.cycles = 2
    def _ror_a(self):
        carry_in = 0x80 if self._get_flag(self.C) else 0
        self._set_flag(self.C, (self.a & 0x01) > 0)
        self.a = ((self.a >> 1) | carry_in) & 0xFF
        self._update_nz_flags(self.a)
        self.cycles = 2
    
    # Shifts (Memory)
    def _asl_m(self, addr, _, cycles_base):
        val = self.read_byte(addr)
        self._set_flag(self.C, (val & 0x80) > 0)
        val = (val << 1) & 0xFF
        self.write_byte(addr, val)
        self._update_nz_flags(val)
        self.cycles = cycles_base
    def _lsr_m(self, addr, _, cycles_base):
        val = self.read_byte(addr)
        self._set_flag(self.C, (val & 0x01) > 0)
        val = (val >> 1) & 0xFF
        self.write_byte(addr, val)
        self._update_nz_flags(val)
        self.cycles = cycles_base
    def _rol_m(self, addr, _, cycles_base):
        val = self.read_byte(addr)
        carry_in = 1 if self._get_flag(self.C) else 0
        self._set_flag(self.C, (val & 0x80) > 0)
        val = ((val << 1) | carry_in) & 0xFF
        self.write_byte(addr, val)
        self._update_nz_flags(val)
        self.cycles = cycles_base
    def _ror_m(self, addr, _, cycles_base):
        val = self.read_byte(addr)
        carry_in = 0x80 if self._get_flag(self.C) else 0
        self._set_flag(self.C, (val & 0x01) > 0)
        val = ((val >> 1) | carry_in) & 0xFF
        self.write_byte(addr, val)
        self._update_nz_flags(val)
        self.cycles = cycles_base

    # Logical
    def _and(self, addr, page_crossed, cycles_base, cycles_page_cross=1):
        self.a &= self.read_byte(addr)
        self._update_nz_flags(self.a)
        self.cycles = cycles_base + (cycles_page_cross if page_crossed else 0)
    def _eor(self, addr, page_crossed, cycles_base, cycles_page_cross=1):
        self.a ^= self.read_byte(addr)
        self._update_nz_flags(self.a)
        self.cycles = cycles_base + (cycles_page_cross if page_crossed else 0)
    def _ora(self, addr, page_crossed, cycles_base, cycles_page_cross=1):
        self.a |= self.read_byte(addr)
        self._update_nz_flags(self.a)
        self.cycles = cycles_base + (cycles_page_cross if page_crossed else 0)
    def _bit(self, addr, _, cycles_base):
        val = self.read_byte(addr)
        self._set_flag(self.Z, (self.a & val) == 0)
        self._set_flag(self.N, (val & 0x80) > 0)
        self._set_flag(self.V, (val & 0x40) > 0)
        self.cycles = cycles_base

    # Compare
    def _compare(self, reg_val, mem_val):
        res = (reg_val - mem_val) & 0xFF # Perform subtraction to set flags
        self._set_flag(self.C, reg_val >= mem_val)
        self._update_nz_flags(res)

    def _cmp(self, addr, page_crossed, cycles_base, cycles_page_cross=1):
        val = self.read_byte(addr)
        self._compare(self.a, val)
        self.cycles = cycles_base + (cycles_page_cross if page_crossed else 0)
    def _cpx(self, addr, _, cycles_base): # Immediate and ZP only for CPX, no page cross penalty
        val = self.read_byte(addr)
        self._compare(self.x, val)
        self.cycles = cycles_base
    def _cpy(self, addr, _, cycles_base): # Immediate and ZP only for CPY, no page cross penalty
        val = self.read_byte(addr)
        self._compare(self.y, val)
        self.cycles = cycles_base

    # Branch
    def _branch(self, condition, relative_offset):
        self.cycles = 2 # Base cycles for branch
        if condition:
            self.cycles += 1 # Extra cycle if branch taken
            target_addr = (self.pc + relative_offset) & 0xFFFF
            if (self.pc & 0xFF00) != (target_addr & 0xFF00): # Page crossed
                self.cycles += 1 # Extra cycle if page boundary crossed
            self.pc = target_addr
            
    def _bpl(self): addr_rel, _ = self.addr_imm(); offset = np.int8(addr_rel); self._branch(not self._get_flag(self.N), offset)
    def _bmi(self): addr_rel, _ = self.addr_imm(); offset = np.int8(addr_rel); self._branch(self._get_flag(self.N), offset)
    def _bvc(self): addr_rel, _ = self.addr_imm(); offset = np.int8(addr_rel); self._branch(not self._get_flag(self.V), offset)
    def _bvs(self): addr_rel, _ = self.addr_imm(); offset = np.int8(addr_rel); self._branch(self._get_flag(self.V), offset)
    def _bcc(self): addr_rel, _ = self.addr_imm(); offset = np.int8(addr_rel); self._branch(not self._get_flag(self.C), offset)
    def _bcs(self): addr_rel, _ = self.addr_imm(); offset = np.int8(addr_rel); self._branch(self._get_flag(self.C), offset)
    def _bne(self): addr_rel, _ = self.addr_imm(); offset = np.int8(addr_rel); self._branch(not self._get_flag(self.Z), offset)
    def _beq(self): addr_rel, _ = self.addr_imm(); offset = np.int8(addr_rel); self._branch(self._get_flag(self.Z), offset)

    # Jumps & Subroutines
    def _jmp_abs(self): addr, _ = self.addr_abs(); self.pc = addr; self.cycles = 3
    def _jmp_ind(self): # Indirect JMP has a famous bug
        ptr_addr, _ = self.addr_abs()
        self.pc = self.read_word_bug(ptr_addr) # Use bugged read for page boundary
        self.cycles = 5
    def _jsr(self):
        addr, _ = self.addr_abs()
        self.push_word(self.pc - 1) # JSR pushes PC of *last byte of JSR instruction*
        self.pc = addr
        self.cycles = 6
    def _rts(self): self.pc = self.pop_word() + 1; self.cycles = 6
    def _rti(self):
        self.status = (self.pop_byte() & ~self.B) | self.U # B flag cleared, U flag set
        self.pc = self.pop_word()
        self.cycles = 6

    # Stack
    def _pha(self): self.push_byte(self.a); self.cycles = 3
    def _php(self): self.push_byte(self.status | self.B | self.U); self.cycles = 3 # B and U are set when PHP pushes
    def _pla(self): self.a = self.pop_byte(); self._update_nz_flags(self.a); self.cycles = 4
    def _plp(self): self.status = (self.pop_byte() & ~self.B) | self.U; self.cycles = 4 # B flag cleared, U flag set

    # Transfers
    def _tax(self): self.x = self.a; self._update_nz_flags(self.x); self.cycles = 2
    def _tay(self): self.y = self.a; self._update_nz_flags(self.y); self.cycles = 2
    def _txa(self): self.a = self.x; self._update_nz_flags(self.a); self.cycles = 2
    def _tya(self): self.a = self.y; self._update_nz_flags(self.a); self.cycles = 2
    def _tsx(self): self.x = self.sp; self._update_nz_flags(self.x); self.cycles = 2
    def _txs(self): self.sp = self.x; self.cycles = 2 # Does not affect flags

    # Status Flag Clears/Sets
    def _clc(self): self._set_flag(self.C, False); self.cycles = 2
    def _cld(self): self._set_flag(self.D, False); self.cycles = 2 # Decimal mode not used in NES
    def _cli(self): self._set_flag(self.I, False); self.cycles = 2
    def _clv(self): self._set_flag(self.V, False); self.cycles = 2
    def _sec(self): self._set_flag(self.C, True); self.cycles = 2
    def _sed(self): self._set_flag(self.D, True); self.cycles = 2
    def _sei(self): self._set_flag(self.I, True); self.cycles = 2
    
    # No Operation
    def _nop(self): self.cycles = 2 # Official NOP
    def _nop_unofficial(self, cycles=2, addr_mode=None, read=False): # For unofficial NOPs
        # Some unofficial NOPs read memory, which can take extra cycles on page cross
        if addr_mode:
            addr, page_crossed = addr_mode()
            if read:
                self.read_byte(addr) # Dummy read
            self.cycles = cycles + (1 if page_crossed and read else 0)
        else:
            self.cycles = cycles


    def _brk(self):
        self.pc += 1 # BRK is 2 bytes, but treated as 1 for interrupt handling pc push
        self.push_word(self.pc)
        self.push_byte(self.status | self.B | self.U) # B and U flags set on push
        self._set_flag(self.I, True) # Disable further IRQs
        self.pc = self.read_word(0xFFFE) # IRQ/BRK vector
        self.cycles = 7

    def reset(self):
        self.pc = self.read_word(0xFFFC)
        self.sp = 0xFD
        self.status = 0x24 # IRQ disabled, U set
        self.a = self.x = self.y = 0
        self.cycles = 8 # Reset takes 8 cycles
        self.total_cycles = 0
        self.nmi_pending = False
        self.irq_pending = False # Not fully implemented
        self.stall_cycles = 0

    def _nmi(self):
        self.push_word(self.pc)
        self.push_byte(self.status & ~self.B | self.U) # B flag not set by NMI/IRQ, U set
        self._set_flag(self.I, True) # Disable further IRQs
        self.pc = self.read_word(0xFFFA) # NMI vector
        self.nmi_pending = False
        self.cycles = 7

    def _irq(self):
        if self._get_flag(self.I): return # IRQ disabled
        self.push_word(self.pc)
        self.push_byte(self.status & ~self.B | self.U)
        self._set_flag(self.I, True)
        self.pc = self.read_word(0xFFFE)
        self.irq_pending = False
        self.cycles = 7

    def load_rom(self, rom_data):
        if rom_data[0:4] != b'NES\x1a':
            raise ValueError("Fucking invalid iNES header, you idiot!")
        
        prg_rom_banks = rom_data[4] # Num of 16KB PRG ROM banks
        chr_rom_banks = rom_data[5] # Num of 8KB CHR ROM banks
        flags6 = rom_data[6]
        flags7 = rom_data[7]
        # TODO: Parse flags 6 and 7 for mapper number, mirroring, etc.
        mapper_num = ((flags6 >> 4) & 0x0F) | (flags7 & 0xF0)
        
        if mapper_num != 0:
            raise NotImplementedError(f"Goddamn it, Mapper {mapper_num} is not fucking implemented! Only Mapper 0, you pleb.")

        has_trainer = (flags6 & 0x04) > 0
        prg_ram_size = rom_data[8] # Usually 0 for mapper 0, can be 8KB for others

        header_size = 16
        trainer_size = 512 if has_trainer else 0
        
        prg_rom_start = header_size + trainer_size
        prg_rom_size = prg_rom_banks * 0x4000 # 16KB per bank
        prg_data = rom_data[prg_rom_start : prg_rom_start + prg_rom_size]
        
        chr_rom_start = prg_rom_start + prg_rom_size
        chr_rom_size = chr_rom_banks * 0x2000 # 8KB per bank
        chr_data = rom_data[chr_rom_start : chr_rom_start + chr_rom_size] if chr_rom_banks > 0 else bytearray()

        self.mapper = Mapper0(prg_rom_banks, chr_rom_banks, prg_data, chr_data)
        if self.ppu:
            self.ppu.connect_mapper(self.mapper)
        
        self.reset()
        print(f"ROM loaded: {prg_rom_banks} PRG banks, {chr_rom_banks} CHR banks. Mapper 0. Fucking finally.")


    def step(self): # This is the fucking main CPU execution loop part
        if self.stall_cycles > 0:
            self.stall_cycles -=1
            self.cycles = 1 # Stall takes 1 CPU cycle of doing nothing
            return self.cycles

        if self.nmi_pending:
            self._nmi()
            self.total_cycles += self.cycles
            return self.cycles
        
        # IRQ handling (rudimentary)
        # if self.irq_pending and not self._get_flag(self.I):
        #     self._irq()
        #     self.total_cycles += self.cycles
        #     return self.cycles

        opcode = self.read_byte(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        self.cycles = 0 # Reset cycles for this instruction

        # --- Opcode Dispatch --- This is gonna be a long fucking list ---
        # LDA
        if opcode == 0xA9: addr, pc = self.addr_imm(); self._lda(addr, pc, 2)
        elif opcode == 0xA5: addr, pc = self.addr_zp(); self._lda(addr, pc, 3)
        elif opcode == 0xB5: addr, pc = self.addr_zpx(); self._lda(addr, pc, 4)
        elif opcode == 0xAD: addr, pc = self.addr_abs(); self._lda(addr, pc, 4)
        elif opcode == 0xBD: addr, pc = self.addr_absx(); self._lda(addr, pc, 4, 1)
        elif opcode == 0xB9: addr, pc = self.addr_absy(); self._lda(addr, pc, 4, 1)
        elif opcode == 0xA1: addr, pc = self.addr_indx(); self._lda(addr, pc, 6)
        elif opcode == 0xB1: addr, pc = self.addr_indy(); self._lda(addr, pc, 5, 1)
        # LDX
        elif opcode == 0xA2: addr, pc = self.addr_imm(); self._ldx(addr, pc, 2)
        elif opcode == 0xA6: addr, pc = self.addr_zp(); self._ldx(addr, pc, 3)
        elif opcode == 0xB6: addr, pc = self.addr_zpy(); self._ldx(addr, pc, 4) # Uses Y
        elif opcode == 0xAE: addr, pc = self.addr_abs(); self._ldx(addr, pc, 4)
        elif opcode == 0xBE: addr, pc = self.addr_absy(); self._ldx(addr, pc, 4, 1) # Uses Y
        # LDY
        elif opcode == 0xA0: addr, pc = self.addr_imm(); self._ldy(addr, pc, 2)
        elif opcode == 0xA4: addr, pc = self.addr_zp(); self._ldy(addr, pc, 3)
        elif opcode == 0xB4: addr, pc = self.addr_zpx(); self._ldy(addr, pc, 4) # Uses X
        elif opcode == 0xAC: addr, pc = self.addr_abs(); self._ldy(addr, pc, 4)
        elif opcode == 0xBC: addr, pc = self.addr_absx(); self._ldy(addr, pc, 4, 1) # Uses X
        # STA
        elif opcode == 0x85: addr, pc = self.addr_zp(); self._sta(addr, pc, 3)
        elif opcode == 0x95: addr, pc = self.addr_zpx(); self._sta(addr, pc, 4)
        elif opcode == 0x8D: addr, pc = self.addr_abs(); self._sta(addr, pc, 4)
        elif opcode == 0x9D: addr, pc = self.addr_absx(); self._sta(addr, pc, 5) # No page cross penalty for STA AbsX/AbsY
        elif opcode == 0x99: addr, pc = self.addr_absy(); self._sta(addr, pc, 5)
        elif opcode == 0x81: addr, pc = self.addr_indx(); self._sta(addr, pc, 6)
        elif opcode == 0x91: addr, pc = self.addr_indy(); self._sta(addr, pc, 6) # No page cross for STA Indy
        # STX
        elif opcode == 0x86: addr, pc = self.addr_zp(); self._stx(addr, pc, 3)
        elif opcode == 0x96: addr, pc = self.addr_zpy(); self._stx(addr, pc, 4) # Uses Y
        elif opcode == 0x8E: addr, pc = self.addr_abs(); self._stx(addr, pc, 4)
        # STY
        elif opcode == 0x84: addr, pc = self.addr_zp(); self._sty(addr, pc, 3)
        elif opcode == 0x94: addr, pc = self.addr_zpx(); self._sty(addr, pc, 4) # Uses X
        elif opcode == 0x8C: addr, pc = self.addr_abs(); self._sty(addr, pc, 4)
        # Jumps
        elif opcode == 0x4C: self._jmp_abs()
        elif opcode == 0x6C: self._jmp_ind()
        # Subroutines
        elif opcode == 0x20: self._jsr()
        elif opcode == 0x60: self._rts()
        elif opcode == 0x40: self._rti()
        # Stack
        elif opcode == 0x48: self._pha()
        elif opcode == 0x08: self._php()
        elif opcode == 0x68: self._pla()
        elif opcode == 0x28: self._plp()
        # Transfers
        elif opcode == 0xAA: self._tax()
        elif opcode == 0xA8: self._tay()
        elif opcode == 0x8A: self._txa()
        elif opcode == 0x98: self._tya()
        elif opcode == 0xBA: self._tsx()
        elif opcode == 0x9A: self._txs()
        # Increments / Decrements
        elif opcode == 0xE6: addr, pc = self.addr_zp(); self._inc(addr, pc, 5)
        elif opcode == 0xF6: addr, pc = self.addr_zpx(); self._inc(addr, pc, 6)
        elif opcode == 0xEE: addr, pc = self.addr_abs(); self._inc(addr, pc, 6)
        elif opcode == 0xFE: addr, pc = self.addr_absx(); self._inc(addr, pc, 7)
        elif opcode == 0xC6: addr, pc = self.addr_zp(); self._dec(addr, pc, 5)
        elif opcode == 0xD6: addr, pc = self.addr_zpx(); self._dec(addr, pc, 6)
        elif opcode == 0xCE: addr, pc = self.addr_abs(); self._dec(addr, pc, 6)
        elif opcode == 0xDE: addr, pc = self.addr_absx(); self._dec(addr, pc, 7)
        elif opcode == 0xE8: self._inx()
        elif opcode == 0xC8: self._iny()
        elif opcode == 0xCA: self._dex()
        elif opcode == 0x88: self._dey()
        # Comparisons
        elif opcode == 0xC9: addr, pc = self.addr_imm(); self._cmp(addr, pc, 2)
        elif opcode == 0xC5: addr, pc = self.addr_zp(); self._cmp(addr, pc, 3)
        elif opcode == 0xD5: addr, pc = self.addr_zpx(); self._cmp(addr, pc, 4)
        elif opcode == 0xCD: addr, pc = self.addr_abs(); self._cmp(addr, pc, 4)
        elif opcode == 0xDD: addr, pc = self.addr_absx(); self._cmp(addr, pc, 4, 1)
        elif opcode == 0xD9: addr, pc = self.addr_absy(); self._cmp(addr, pc, 4, 1)
        elif opcode == 0xC1: addr, pc = self.addr_indx(); self._cmp(addr, pc, 6)
        elif opcode == 0xD1: addr, pc = self.addr_indy(); self._cmp(addr, pc, 5, 1)
        elif opcode == 0xE0: addr, _ = self.addr_imm(); self._cpx(addr, _, 2) # CPX Imm
        elif opcode == 0xE4: addr, _ = self.addr_zp(); self._cpx(addr, _, 3)   # CPX ZP
        elif opcode == 0xEC: addr, _ = self.addr_abs(); self._cpx(addr, _, 4)  # CPX Abs
        elif opcode == 0xC0: addr, _ = self.addr_imm(); self._cpy(addr, _, 2) # CPY Imm
        elif opcode == 0xC4: addr, _ = self.addr_zp(); self._cpy(addr, _, 3)   # CPY ZP
        elif opcode == 0xCC: addr, _ = self.addr_abs(); self._cpy(addr, _, 4)  # CPY Abs
        # Branching
        elif opcode == 0x10: self._bpl() # Relative addr mode handled inside branch
        elif opcode == 0x30: self._bmi()
        elif opcode == 0x50: self._bvc()
        elif opcode == 0x70: self._bvs()
        elif opcode == 0x90: self._bcc()
        elif opcode == 0xB0: self._bcs()
        elif opcode == 0xD0: self._bne()
        elif opcode == 0xF0: self._beq()
        # Arithmetic
        elif opcode == 0x69: addr, pc = self.addr_imm(); self._adc(addr, pc, 2)
        elif opcode == 0x65: addr, pc = self.addr_zp(); self._adc(addr, pc, 3)
        elif opcode == 0x75: addr, pc = self.addr_zpx(); self._adc(addr, pc, 4)
        elif opcode == 0x6D: addr, pc = self.addr_abs(); self._adc(addr, pc, 4)
        elif opcode == 0x7D: addr, pc = self.addr_absx(); self._adc(addr, pc, 4, 1)
        elif opcode == 0x79: addr, pc = self.addr_absy(); self._adc(addr, pc, 4, 1)
        elif opcode == 0x61: addr, pc = self.addr_indx(); self._adc(addr, pc, 6)
        elif opcode == 0x71: addr, pc = self.addr_indy(); self._adc(addr, pc, 5, 1)
        elif opcode == 0xE9: addr, pc = self.addr_imm(); self._sbc(addr, pc, 2)
        elif opcode == 0xE5: addr, pc = self.addr_zp(); self._sbc(addr, pc, 3)
        elif opcode == 0xF5: addr, pc = self.addr_zpx(); self._sbc(addr, pc, 4)
        elif opcode == 0xED: addr, pc = self.addr_abs(); self._sbc(addr, pc, 4)
        elif opcode == 0xFD: addr, pc = self.addr_absx(); self._sbc(addr, pc, 4, 1)
        elif opcode == 0xF9: addr, pc = self.addr_absy(); self._sbc(addr, pc, 4, 1)
        elif opcode == 0xE1: addr, pc = self.addr_indx(); self._sbc(addr, pc, 6)
        elif opcode == 0xF1: addr, pc = self.addr_indy(); self._sbc(addr, pc, 5, 1)
        # Logical
        elif opcode == 0x29: addr, pc = self.addr_imm(); self._and(addr, pc, 2)
        elif opcode == 0x25: addr, pc = self.addr_zp(); self._and(addr, pc, 3)
        elif opcode == 0x35: addr, pc = self.addr_zpx(); self._and(addr, pc, 4)
        elif opcode == 0x2D: addr, pc = self.addr_abs(); self._and(addr, pc, 4)
        elif opcode == 0x3D: addr, pc = self.addr_absx(); self._and(addr, pc, 4, 1)
        elif opcode == 0x39: addr, pc = self.addr_absy(); self._and(addr, pc, 4, 1)
        elif opcode == 0x21: addr, pc = self.addr_indx(); self._and(addr, pc, 6)
        elif opcode == 0x31: addr, pc = self.addr_indy(); self._and(addr, pc, 5, 1)
        elif opcode == 0x09: addr, pc = self.addr_imm(); self._ora(addr, pc, 2)
        elif opcode == 0x05: addr, pc = self.addr_zp(); self._ora(addr, pc, 3)
        elif opcode == 0x15: addr, pc = self.addr_zpx(); self._ora(addr, pc, 4)
        elif opcode == 0x0D: addr, pc = self.addr_abs(); self._ora(addr, pc, 4)
        elif opcode == 0x1D: addr, pc = self.addr_absx(); self._ora(addr, pc, 4, 1)
        elif opcode == 0x19: addr, pc = self.addr_absy(); self._ora(addr, pc, 4, 1)
        elif opcode == 0x01: addr, pc = self.addr_indx(); self._ora(addr, pc, 6)
        elif opcode == 0x11: addr, pc = self.addr_indy(); self._ora(addr, pc, 5, 1)
        elif opcode == 0x49: addr, pc = self.addr_imm(); self._eor(addr, pc, 2)
        elif opcode == 0x45: addr, pc = self.addr_zp(); self._eor(addr, pc, 3)
        elif opcode == 0x55: addr, pc = self.addr_zpx(); self._eor(addr, pc, 4)
        elif opcode == 0x4D: addr, pc = self.addr_abs(); self._eor(addr, pc, 4)
        elif opcode == 0x5D: addr, pc = self.addr_absx(); self._eor(addr, pc, 4, 1)
        elif opcode == 0x59: addr, pc = self.addr_absy(); self._eor(addr, pc, 4, 1)
        elif opcode == 0x41: addr, pc = self.addr_indx(); self._eor(addr, pc, 6)
        elif opcode == 0x51: addr, pc = self.addr_indy(); self._eor(addr, pc, 5, 1)
        elif opcode == 0x24: addr, pc = self.addr_zp(); self._bit(addr, pc, 3)
        elif opcode == 0x2C: addr, pc = self.addr_abs(); self._bit(addr, pc, 4)
        # Shifts
        elif opcode == 0x0A: self._asl_a()
        elif opcode == 0x06: addr, pc = self.addr_zp(); self._asl_m(addr, pc, 5)
        elif opcode == 0x16: addr, pc = self.addr_zpx(); self._asl_m(addr, pc, 6)
        elif opcode == 0x0E: addr, pc = self.addr_abs(); self._asl_m(addr, pc, 6)
        elif opcode == 0x1E: addr, pc = self.addr_absx(); self._asl_m(addr, pc, 7)
        elif opcode == 0x4A: self._lsr_a()
        elif opcode == 0x46: addr, pc = self.addr_zp(); self._lsr_m(addr, pc, 5)
        elif opcode == 0x56: addr, pc = self.addr_zpx(); self._lsr_m(addr, pc, 6)
        elif opcode == 0x4E: addr, pc = self.addr_abs(); self._lsr_m(addr, pc, 6)
        elif opcode == 0x5E: addr, pc = self.addr_absx(); self._lsr_m(addr, pc, 7)
        elif opcode == 0x2A: self._rol_a()
        elif opcode == 0x26: addr, pc = self.addr_zp(); self._rol_m(addr, pc, 5)
        elif opcode == 0x36: addr, pc = self.addr_zpx(); self._rol_m(addr, pc, 6)
        elif opcode == 0x2E: addr, pc = self.addr_abs(); self._rol_m(addr, pc, 6)
        elif opcode == 0x3E: addr, pc = self.addr_absx(); self._rol_m(addr, pc, 7)
        elif opcode == 0x6A: self._ror_a()
        elif opcode == 0x66: addr, pc = self.addr_zp(); self._ror_m(addr, pc, 5)
        elif opcode == 0x76: addr, pc = self.addr_zpx(); self._ror_m(addr, pc, 6)
        elif opcode == 0x6E: addr, pc = self.addr_abs(); self._ror_m(addr, pc, 6)
        elif opcode == 0x7E: addr, pc = self.addr_absx(); self._ror_m(addr, pc, 7)
        # Flag clear/set
        elif opcode == 0x18: self._clc()
        elif opcode == 0xD8: self._cld()
        elif opcode == 0x58: self._cli()
        elif opcode == 0xB8: self._clv()
        elif opcode == 0x38: self._sec()
        elif opcode == 0xF8: self._sed()
        elif opcode == 0x78: self._sei()
        # BRK
        elif opcode == 0x00: self._brk()
        # NOP
        elif opcode == 0xEA: self._nop()
        # Unofficial NOPs (many variants, this is a sample)
        elif opcode in [0x1A, 0x3A, 0x5A, 0x7A, 0xDA, 0xFA]: self._nop_unofficial(cycles=2) # 1-byte NOPs
        elif opcode in [0x80, 0x82, 0x89, 0xC2, 0xE2]: # 2-byte NOPs (imm)
            self.pc +=1; self._nop_unofficial(cycles=2)
        elif opcode in [0x04, 0x44, 0x64]: # ZP NOPs
            self.pc +=1; self._nop_unofficial(cycles=3, addr_mode=self.addr_zp, read=True)
        elif opcode in [0x0C]: # ABS NOP
            self.pc +=2; self._nop_unofficial(cycles=4, addr_mode=self.addr_abs, read=True)
        # More unofficial opcodes (LAX, SAX, SLO, RLA, SRE, RRA, DCP, ISB/ISC) would go here... FUCK that for now.
        
        else:
            print(f"Unfuckingimplemented Opcode: {opcode:02X} at PC: {self.pc-1:04X}. System Halted. You suck.")
            # You'd probably want a more graceful halt or error state.
            # For now, just stop by returning a huge cycle count to break the loop.
            return 99999999 

        self.total_cycles += self.cycles
        return self.cycles

class NESGUI:
    def __init__(self, root, cpu, ppu):
        self.root = root
        self.root.title("Fucking NES Emulator Thing")
        self.root.configure(bg='#1e1e1e') # Dark theme, 'cause we're edgy
        self.cpu = cpu
        self.ppu = ppu
        self.cpu.connect_ppu(self.ppu) # Crucial link, motherfucker
        self.ppu.cpu = self.cpu # And the other way around, because they're lovers

        self.running = False
        self.tk_image = None
        self.last_frame_time = 0
        self.rom_loaded = False

        self._create_menu()
        self._create_display()
        self._create_controls()
        self._create_statusbar()
        self.root.minsize(SCREEN_WIDTH + 40, SCREEN_HEIGHT + 100)

    def _create_menu(self):
        menubar = tk.Menu(self.root, bg="#3c3c3c", fg="white", activebackground="#5c5c5c", activeforeground="white")
        file_menu = tk.Menu(menubar, tearoff=0, bg="#3c3c3c", fg="white")
        file_menu.add_command(label="Load Fucking ROM…", command=self.load_rom, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Exit This Shitshow", command=self.root.quit, accelerator="Alt+F4")
        menubar.add_cascade(label="File", menu=file_menu)
        help_menu = tk.Menu(menubar, tearoff=0, bg="#3c3c3c", fg="white")
        help_menu.add_command(label="About This Abomination", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.root.config(menu=menubar)
        self.root.bind("<Control-o>", lambda e: self.load_rom())

    def _create_display(self):
        self.canvas = tk.Canvas(self.root, width=SCREEN_WIDTH, height=SCREEN_HEIGHT, bg='black', highlightthickness=1, highlightbackground="#555")
        self.canvas.pack(pady=10, padx=10)
        # Initial blank image
        blank = Image.new('RGB', (SCREEN_WIDTH, SCREEN_HEIGHT), color='black')
        self.blank_image = ImageTk.PhotoImage(blank)
        self.canvas_image = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.blank_image)

    def _create_controls(self):
        frame = tk.Frame(self.root, bg='#1e1e1e')
        frame.pack(pady=5)
        btn_style = {"bg": "#4a4a4a", "fg": "white", "activebackground": "#5a5a5a", "activeforeground": "white", "relief": tk.RAISED, "bd": 2, "padx":5, "pady":2}
        
        self.load_btn = tk.Button(frame, text="📁 Load ROM", width=12, command=self.load_rom, **btn_style)
        self.start_btn = tk.Button(frame, text="▶️ Start", width=12, command=self.start_emulation, **btn_style, state=tk.DISABLED)
        self.pause_btn = tk.Button(frame, text="⏸️ Pause", width=12, command=self.pause_emulation, **btn_style, state=tk.DISABLED)
        # self.reset_btn = tk.Button(frame, text="🔄 Reset", width=12, command=self.reset_emulation, **btn_style, state=tk.DISABLED) # TODO

        for btn in (self.load_btn, self.start_btn, self.pause_btn): # self.reset_btn
            btn.pack(side=tk.LEFT, padx=5)

    def _create_statusbar(self):
        self.status_var = tk.StringVar()
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W, bg='#101010', fg='lightgrey', padx=5)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.update_status("Ready to load some goddamn ROMs.")

    def update_status(self, msg):
        self.status_var.set(f"Fucking Status: {msg}")
        # self.root.update_idletasks() # Might not be needed if mainloop is running

    def load_rom(self):
        if self.running: self.pause_emulation()
        fname = filedialog.askopenfilename(title="Select a Fucking NES ROM", filetypes=[("NES ROMs", "*.nes"), ("All files", "*.*")])
        if not fname:
            self.update_status("No ROM selected, you coward.")
            return
        try:
            with open(fname, 'rb') as f:
                rom_data = bytearray(f.read())
            self.cpu.load_rom(rom_data) # This also connects mapper to CPU and PPU
            self.ppu.frame_complete = False # Reset PPU frame state
            self.update_status(f"Loaded: {os.path.basename(fname)}. Now what, asshole?")
            self.rom_loaded = True
            self.start_btn.config(state=tk.NORMAL)
            # self.reset_btn.config(state=tk.NORMAL)
            # Clear screen to black or universal background color
            bg_color_idx = self.ppu._ppu_read(0x3F00)
            bg_rgb = NES_PALETTE[bg_color_idx & 0x3F]
            img = Image.new('RGB', (SCREEN_WIDTH, SCREEN_HEIGHT), color=bg_rgb)
            self.tk_image = ImageTk.PhotoImage(img)
            self.canvas.itemconfig(self.canvas_image, image=self.tk_image)

        except Exception as e:
            messagebox.showerror("ROM Load Error - You Fucked Up!", f"Failed to load ROM: {e}\nAre you sure it's a real NES ROM, genius?")
            self.update_status(f"Error loading ROM: {e}")
            self.rom_loaded = False
            self.start_btn.config(state=tk.DISABLED)
            # self.reset_btn.config(state=tk.DISABLED)


    def start_emulation(self):
        if not self.rom_loaded:
            self.update_status("Load a fucking ROM first, numbnuts!")
            messagebox.showwarning("Hold Up", "You need to load a ROM before you can start this shit.")
            return
        if not self.running:
            self.running = True
            self.start_btn.config(state=tk.DISABLED, text="Running...")
            self.pause_btn.config(state=tk.NORMAL)
            self.load_btn.config(state=tk.DISABLED) # Don't load while running
            self.update_status("Emulation running! Try not to break everything.")
            self.last_frame_time = time.perf_counter()
            self._update_loop()

    def pause_emulation(self):
        if self.running:
            self.running = False
            self.start_btn.config(state=tk.NORMAL, text="▶️ Resume")
            self.pause_btn.config(state=tk.DISABLED)
            self.load_btn.config(state=tk.NORMAL)
            self.update_status("Emulation paused. Taking a fucking break, are we?")

    # def reset_emulation(self):
    #     if self.rom_loaded:
    #         self.pause_emulation() # Ensure it's paused
    #         self.cpu.reset()
    #         self.ppu.scanline = 0 # Reset PPU state as well
    #         self.ppu.cycle = 0
    #         self.ppu.frame_complete = False
    #         self.ppu.ppustatus = 0 # Clear VBlank etc.
    #         self.ppu.vram_addr = 0 # Reset PPU scroll/address registers
    #         self.ppu.temp_vram_addr = 0
    #         self.ppu.write_toggle = False
    #         # Clear screen
    #         bg_color_idx = self.ppu._ppu_read(0x3F00)
    #         bg_rgb = NES_PALETTE[bg_color_idx & 0x3F]
    #         img = Image.new('RGB', (SCREEN_WIDTH, SCREEN_HEIGHT), color=bg_rgb)
    #         self.tk_image = ImageTk.PhotoImage(img)
    #         self.canvas.itemconfig(self.canvas_image, image=self.tk_image)
    #         self.update_status("System reset. Hope you didn't fuck it up again.")
    #         self.start_btn.config(text="▶️ Start") # Reset start button text
    #     else:
    #         self.update_status("Can't reset if no ROM is loaded, dumbass.")


    def _update_loop(self):
        if not self.running:
            return

        # Rough timing for ~60FPS
        # NES CPU runs at ~1.79 MHz. PPU runs 3x faster.
        # Cycles per frame: ~29780.5 CPU cycles ( (341 PPU clocks/scanline * 262 scanlines/frame) / 3 PPU/CPU )
        CYCLES_PER_FRAME = 29781 # Close enough, fucker

        cycles_this_frame = 0
        while cycles_this_frame < CYCLES_PER_FRAME:
            if not self.running: break # Check if paused mid-frame
            
            cpu_cycles = self.cpu.step()
            if cpu_cycles > 999999: # Halting condition from CPU
                self.pause_emulation()
                self.update_status(f"CPU Halted at PC:{self.cpu.pc-1:04X}. Probably your shitty ROM.")
                messagebox.showerror("CPU HALT", f"CPU encountered an unimplemented opcode or error and has halted.\nOpcode: {self.cpu.read_byte(self.cpu.pc-1):02X} at PC: {self.cpu.pc-1:04X}")
                return

            cycles_this_frame += cpu_cycles
            
            # PPU runs 3 times for every CPU cycle
            for _ in range(cpu_cycles * 3):
                self.ppu.step()
            
            # If PPU signalled frame completion (due to VBlank NMI logic), break to render
            if self.ppu.frame_complete:
                break
        
        # If loop exited due to cycle count rather than PPU frame_complete, force it for rendering
        if not self.ppu.frame_complete and self.running :
             self.ppu.frame_complete = True # Ensure we render something

        if self.ppu.frame_complete:
            rendered_frame = self.ppu.get_frame() # This now does the full frame render
            img = Image.fromarray(rendered_frame, 'RGB')
            self.tk_image = ImageTk.PhotoImage(img)
            self.canvas.itemconfig(self.canvas_image, image=self.tk_image)
            self.ppu.frame_complete = False # Reset for next frame

        # Frame rate limiting (very fucking basic)
        target_delay = 1.0 / NES_FRAME_RATE
        current_time = time.perf_counter()
        elapsed_time = current_time - self.last_frame_time
        wait_time = target_delay - elapsed_time
        
        if wait_time < 0: wait_time = 0 # Don't wait if we're already late, obviously
        
        self.last_frame_time = current_time + wait_time # Adjust for next frame target

        self.root.after(int(wait_time * 1000) if wait_time > 0.001 else 1, self._update_loop)


    def show_about(self):
        messagebox.showinfo("About This Fucking Thing",
                            "NES Emulator - Python Abomination\n"
                            "Version: Good enough for government work (Beta as fuck)\n\n"
                            "Crafted by CATSDK, because you asked for it, you sick puppy.\n"
                            "Don't expect miracles. It's Python, for Christ's sake.")

def main():
    root = tk.Tk()
    cpu = MOS6502()
    ppu = PPU(cpu) # Pass CPU to PPU constructor
    app = NESGUI(root, cpu, ppu)
    root.mainloop()

if __name__ == "__main__":
    main()

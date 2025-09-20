a#!/usr/bin/env python3
"""
SamsoftEmu NES 0.1
A simplified NES emulator for Samsoft OS
Just for the giggles!
"""

import sys
import struct
import pygame
import numpy as np
from enum import IntEnum
import tkinter as tk
from tkinter import filedialog
import os

# Hide tkinter root window
root = tk.Tk()
root.withdraw()

class SamsoftEmuNES:
    def __init__(self):
        self.version = "0.1"
        self.window_width = 600
        self.window_height = 400
        self.scale = 2
        self.nes_width = 256
        self.nes_height = 240
        
        # Initialize Pygame
        pygame.init()
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption(f"SamsoftEmu NES {self.version}")
        self.clock = pygame.time.Clock()
        
        # NES Components
        self.cpu = CPU6502(self)
        self.ppu = PPU(self)
        self.rom = None
        self.running = False
        
        # Create display surface for NES output
        self.nes_surface = pygame.Surface((self.nes_width, self.nes_height))
        
        # Color palette (simplified NES palette)
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
        
    def load_rom(self, filename=None):
        """Load an iNES format ROM"""
        if not filename:
            filename = filedialog.askopenfilename(
                title="Select NES ROM (iNES format)",
                filetypes=[("NES ROMs", "*.nes"), ("All files", "*.*")]
            )
        
        if not filename:
            return False
            
        try:
            with open(filename, 'rb') as f:
                # Read iNES header
                header = f.read(16)
                if header[:4] != b'NES\x1a':
                    print("[ERROR] Not a valid iNES file")
                    return False
                
                prg_rom_size = header[4] * 16384  # 16KB units
                chr_rom_size = header[5] * 8192   # 8KB units
                
                # Read PRG-ROM and CHR-ROM
                prg_rom = f.read(prg_rom_size)
                chr_rom = f.read(chr_rom_size) if chr_rom_size > 0 else bytes(8192)
                
                self.rom = {
                    'prg': prg_rom,
                    'chr': chr_rom,
                    'mapper': (header[7] & 0xF0) | (header[6] >> 4),
                    'filename': os.path.basename(filename)
                }
                
                # Load ROM into CPU memory
                self.cpu.load_prg(prg_rom)
                self.ppu.load_chr(chr_rom)
                
                print(f"[LOADED] {self.rom['filename']}")
                print(f"[INFO] PRG-ROM: {prg_rom_size} bytes, CHR-ROM: {chr_rom_size} bytes")
                print(f"[INFO] Mapper: {self.rom['mapper']}")
                return True
                
        except Exception as e:
            print(f"[ERROR] Failed to load ROM: {e}")
            return False
    
    def reset(self):
        """Reset the emulator"""
        self.cpu.reset()
        self.ppu.reset()
        print("[SYSTEM] Emulator reset")
    
    def run(self):
        """Main emulation loop"""
        self.running = True
        print(f"[SYSTEM] SamsoftEmu NES {self.version} started")
        print("[SYSTEM] Press SPACE to load ROM, ESC to exit")
        
        # Demo pattern if no ROM loaded
        demo_offset = 0
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_SPACE:
                        if self.load_rom():
                            self.reset()
                    elif event.key == pygame.K_r:
                        self.reset()
            
            # Clear screen
            self.screen.fill((20, 20, 40))
            
            if self.rom:
                # Run emulation (simplified)
                try:
                    # Execute some CPU cycles
                    for _ in range(100):
                        self.cpu.step()
                    # Update PPU
                    self.ppu.render_frame()
                except:
                    pass  # Simplified error handling
            else:
                # Show demo pattern when no ROM is loaded
                self.show_demo_pattern(demo_offset)
                demo_offset = (demo_offset + 1) % 256
            
            # Scale and center the NES display
            scaled_surface = pygame.transform.scale(
                self.nes_surface, 
                (self.nes_width * self.scale, self.nes_height * self.scale)
            )
            x = (self.window_width - self.nes_width * self.scale) // 2
            y = (self.window_height - self.nes_height * self.scale) // 2
            self.screen.blit(scaled_surface, (x, y))
            
            # Draw UI
            self.draw_ui()
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        print("[SYSTEM] SamsoftEmu NES terminated")
    
    def show_demo_pattern(self, offset):
        """Show a demo pattern when no ROM is loaded"""
        pixels = pygame.PixelArray(self.nes_surface)
        for y in range(self.nes_height):
            for x in range(self.nes_width):
                color_idx = ((x + offset) ^ y) & 0x3F
                color = self.palette[color_idx]
                pixels[x, y] = color
        del pixels
    
    def draw_ui(self):
        """Draw the UI overlay"""
        font = pygame.font.Font(None, 24)
        
        # Title
        title = font.render(f"SamsoftEmu NES {self.version}", True, (255, 255, 255))
        self.screen.blit(title, (10, 10))
        
        # Status
        if self.rom:
            status = f"ROM: {self.rom['filename']}"
        else:
            status = "No ROM loaded (Press SPACE to load)"
        
        status_text = font.render(status, True, (200, 200, 200))
        self.screen.blit(status_text, (10, self.window_height - 30))
        
        # Controls
        controls = font.render("[SPACE: Load ROM] [R: Reset] [ESC: Exit]", True, (150, 150, 150))
        self.screen.blit(controls, (10, 40))


class CPU6502:
    """Simplified 6502 CPU emulator"""
    def __init__(self, nes):
        self.nes = nes
        self.memory = bytearray(0x10000)  # 64KB address space
        self.pc = 0x8000  # Program counter
        self.sp = 0xFD    # Stack pointer
        self.a = 0        # Accumulator
        self.x = 0        # X register
        self.y = 0        # Y register
        self.status = 0x24  # Status register
        self.cycles = 0
        
    def load_prg(self, prg_rom):
        """Load PRG-ROM into CPU memory"""
        # Simplified: Mirror PRG-ROM at 0x8000 and 0xC000
        if len(prg_rom) == 16384:  # 16KB
            self.memory[0x8000:0xC000] = prg_rom
            self.memory[0xC000:0x10000] = prg_rom
        else:  # 32KB
            self.memory[0x8000:0x10000] = prg_rom[:32768]
        
        # Set reset vector
        self.pc = self.read_word(0xFFFC)
    
    def reset(self):
        """Reset CPU state"""
        self.pc = self.read_word(0xFFFC) if self.memory[0xFFFC] else 0x8000
        self.sp = 0xFD
        self.a = 0
        self.x = 0
        self.y = 0
        self.status = 0x24
        self.cycles = 0
    
    def read_byte(self, address):
        """Read a byte from memory"""
        return self.memory[address & 0xFFFF]
    
    def read_word(self, address):
        """Read a word from memory"""
        low = self.read_byte(address)
        high = self.read_byte(address + 1)
        return (high << 8) | low
    
    def write_byte(self, address, value):
        """Write a byte to memory"""
        self.memory[address & 0xFFFF] = value & 0xFF
    
    def step(self):
        """Execute one instruction (simplified)"""
        # Very simplified CPU execution for demo
        opcode = self.read_byte(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        
        # Just increment PC for now (simplified)
        # A real implementation would decode and execute instructions
        self.cycles += 2


class PPU:
    """Simplified Picture Processing Unit"""
    def __init__(self, nes):
        self.nes = nes
        self.vram = bytearray(0x4000)  # 16KB VRAM
        self.oam = bytearray(256)      # Object Attribute Memory
        self.chr_rom = None
        self.scanline = 0
        self.cycle = 0
        
    def load_chr(self, chr_rom):
        """Load CHR-ROM data"""
        self.chr_rom = chr_rom
        if chr_rom:
            self.vram[:len(chr_rom)] = chr_rom
    
    def reset(self):
        """Reset PPU state"""
        self.scanline = 0
        self.cycle = 0
    
    def render_frame(self):
        """Render a frame (simplified)"""
        # Very simplified rendering - just show pattern from CHR-ROM
        if not self.chr_rom:
            return
        
        pixels = pygame.PixelArray(self.nes.nes_surface)
        
        # Simple pattern rendering for demo
        for y in range(240):
            for x in range(256):
                # Generate some pattern from CHR data
                tile_x = x // 8
                tile_y = y // 8
                tile_idx = (tile_y * 32 + tile_x) & 0xFF
                
                # Use tile index to pick a color
                color_idx = (self.chr_rom[tile_idx] if tile_idx < len(self.chr_rom) else 0) & 0x3F
                color = self.nes.palette[color_idx]
                pixels[x, y] = color
        
        del pixels


# Main entry point
if __name__ == "__main__":
    print("=" * 60)
    print("SAMSOFT OS - NES EMULATOR MODULE")
    print("=" * 60)
    print("[INITIALIZING] SamsoftEmu NES 0.1")
    print("[STATUS] Just for the giggles!")
    print("=" * 60)
    
    emulator = SamsoftEmuNES()
    emulator.run()

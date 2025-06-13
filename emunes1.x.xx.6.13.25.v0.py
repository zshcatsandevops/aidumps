# nesticle_blueprint.py - The architectural blueprint for a real emulator.
# Loads and parses a .nes ROM file and renders its raw character data.
# Run with: python nesticle_blueprint.py <your_rom>.nes

import time
import sys
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
from PIL import Image, ImageTk
import pygame

# --- THE BLUEPRINT FOR A REAL EMULATOR ---

class Cartridge:
    """ Parses an iNES ROM file and holds its data. """
    def __init__(self, rom_path):
        self.prg_rom = None  # Program code
        self.chr_rom = None  # Character (graphics) data
        self.mapper_id = 0
        self.prg_banks = 0
        self.chr_banks = 0

        with open(rom_path, 'rb') as f:
            header = f.read(16)
            # Check for the "NES" magic number
            if header[0:4] != b'NES\x1a':
                raise IOError("Not a valid iNES ROM file.")
            
            self.prg_banks = header[4]
            self.chr_banks = header[5]
            
            # Extract mapper ID from flags 6 and 7
            self.mapper_id = (header[6] >> 4) | (header[7] & 0xF0)
            
            print(f"ROM Loaded: Mapper {self.mapper_id}, PRG Banks: {self.prg_banks}, CHR Banks: {self.chr_banks}")

            # Skip trainer if present
            if header[6] & 0b100:
                f.seek(512, 1)

            # Read PRG and CHR data
            prg_size = self.prg_banks * 16384  # 16KB per bank
            chr_size = self.chr_banks * 8192   # 8KB per bank
            self.prg_rom = f.read(prg_size)
            self.chr_rom = f.read(chr_size) if chr_size > 0 else b'\x00' * 8192

class CPUSim:
    """ Blueprint for a 6502 CPU. Execution logic is needed here. """
    def __init__(self):
        # Registers
        self.a, self.x, self.y, self.st, self.sp = 0, 0, 0, 0, 0
        self.pc = 0 # Program Counter

    def step(self):
        # IN A REAL EMULATOR:
        # 1. Read opcode at self.pc from the BUS
        # 2. Decode and execute the opcode
        # 3. Update registers and flags
        # 4. Increment PC
        self.pc = (self.pc + 1) & 0xFFFF

class PPUSim:
    """ Blueprint for a 2C02 PPU. Rendering logic is needed here. """
    def __init__(self, cartridge):
        self.cart = cartridge
        self.frame_buffer = np.zeros((240, 256, 3), dtype=np.uint8)
        self.palette = np.array([ # A basic, hardcoded color palette
            [84, 84, 84], [0, 30, 116], [8, 16, 144], [48, 0, 136],
            [68, 0, 100], [92, 0, 48], [84, 4, 0], [60, 24, 0],
            [32, 42, 0], [8, 58, 0], [0, 64, 0], [0, 60, 0],
            [0, 50, 60], [0, 0, 0]], dtype=np.uint8)

    def step(self):
        # THIS IS THE NEW RENDERER. It proves the ROM is loaded.
        # It renders the first 128 tiles from CHR ROM directly to the screen.
        self.frame_buffer.fill(0) # Clear screen
        
        for tile_idx in range(128):
            tile_x = (tile_idx % 16) * 8
            tile_y = (tile_idx // 16) * 8
            
            # Each tile is 16 bytes in CHR ROM
            tile_start = tile_idx * 16
            tile_data = self.cart.chr_rom[tile_start : tile_start + 16]

            for y in range(8):
                # Get the two bit-planes for the current row
                plane1 = tile_data[y]
                plane2 = tile_data[y + 8]
                for x in range(8):
                    # Combine the planes to get a 2-bit color index (0-3)
                    bit1 = (plane1 >> (7 - x)) & 1
                    bit2 = (plane2 >> (7 - x)) & 1
                    color_idx = (bit2 << 1) | bit1
                    
                    # Draw pixel if not transparent (color 0)
                    if color_idx != 0:
                        px, py = tile_x + x, tile_y + y
                        if px < 256 and py < 240:
                            self.frame_buffer[py, px] = self.palette[color_idx]

class CustomNES:
    """ The central BUS, connecting all components. """
    def __init__(self, rom_path):
        self.cartridge = Cartridge(rom_path)
        self.cpu = CPUSim()
        self.ppu = PPUSim(self.cartridge)
        self.obs = self.ppu.frame_buffer
        print("Nesticle Blueprint Initialized. ROM parsed and loaded.")

    def step(self, action):
        # In a real emulator, this would be a complex loop of CPU and PPU steps
        self.cpu.step()
        # For this blueprint, we only step the PPU once to render the static CHR data.
        if not hasattr(self, 'rendered_once'):
             self.ppu.step()
             self.rendered_once = True
        return self.obs, 0, False, False, {}
    
    def reset(self):
        return self.obs, {}
    def close(self): pass

# --- UI AND WRAPPER (Modified to handle ROM loading) ---

class Emulator:
    def __init__(self, rom_path):
        self.env = CustomNES(rom_path)
        self.obs, _ = self.env.reset()
        self.running = True

    def step(self):
        self.obs, _, term, trunc, _ = self.env.step([0,0])
        return term or trunc
    def close(self): self.env.close()

class UI(tk.Tk):
    def __init__(self, rom_path):
        super().__init__()
        self.title(f"NESTICLE-BLUEPRINT ✒️ – {os.path.basename(rom_path)}")
        self.configure(bg="black")
        
        self.emu = Emulator(rom_path)
        
        self.canvas = tk.Canvas(self, width=512, height=480, bg="black", highlightthickness=0)
        self.canvas.pack()
        self.img_ref = None

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.after_idle(self.draw, self.emu.obs) # Draw the static frame once
        messagebox.showinfo("Nesticle Blueprint", "ROM file has been loaded and parsed.\n\nThe screen displays the raw character (tile) data from the game cartridge to prove it was loaded correctly. Full game emulation requires implementing the CPU and PPU logic.")

    def draw(self, frame):
        img = Image.fromarray(frame.astype(np.uint8), "RGB").resize((512, 480), Image.NEAREST)
        tk_img = ImageTk.PhotoImage(img)
        self.img_ref = tk_img
        self.canvas.create_image(0, 0, image=tk_img, anchor=tk.NW)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        messagebox.showerror("Error", "Usage: python nesticle_blueprint.py <your_rom>.nes")
        sys.exit(1)
    
    rom_file = sys.argv[1]
    if not os.path.exists(rom_file):
        messagebox.showerror("Error", f"ROM file not found: {rom_file}")
        sys.exit(1)
        
    app = UI(rom_file)
    app.mainloop()

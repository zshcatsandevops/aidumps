# nesticle_gui.py - A true GUI application.
# Boots to an interface and loads ROMs on command.
# Run with: python nesticle_gui.py

import time
import sys
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
from PIL import Image, ImageTk
import pygame

# --- CORE EMULATOR BLUEPRINT (Unchanged from nesticle_blueprint.py) ---

class Cartridge:
    def __init__(self, rom_path):
        self.prg_rom, self.chr_rom = None, None
        self.mapper_id, self.prg_banks, self.chr_banks = 0, 0, 0
        with open(rom_path, 'rb') as f:
            header = f.read(16)
            if header[0:4] != b'NES\x1a': raise IOError("Invalid iNES ROM.")
            self.prg_banks, self.chr_banks = header[4], header[5]
            self.mapper_id = (header[6] >> 4) | (header[7] & 0xF0)
            if header[6] & 0b100: f.seek(512, 1)
            prg_size, chr_size = self.prg_banks * 16384, self.chr_banks * 8192
            self.prg_rom = f.read(prg_size)
            self.chr_rom = f.read(chr_size) if chr_size > 0 else b'\x00' * 8192

class PPUSim:
    def __init__(self, cartridge):
        self.cart = cartridge
        self.frame_buffer = np.zeros((240, 256, 3), dtype=np.uint8)
        self.palette = np.array([[84, 84, 84], [0, 30, 116], [8, 16, 144], [48, 0, 136]], dtype=np.uint8)

    def render_chr_data(self):
        self.frame_buffer.fill(20) # Dark gray background
        for tile_idx in range(min(512, self.cart.chr_banks * 512)):
            tile_x, tile_y = (tile_idx % 32) * 8, (tile_idx // 32) * 8
            if tile_y >= 240: break
            tile_start = tile_idx * 16
            tile_data = self.cart.chr_rom[tile_start : tile_start + 16]
            for y in range(8):
                plane1, plane2 = tile_data[y], tile_data[y + 8]
                for x in range(8):
                    bit1, bit2 = (plane1 >> (7 - x)) & 1, (plane2 >> (7 - x)) & 1
                    color_idx = (bit2 << 1) | bit1
                    if color_idx != 0:
                        self.frame_buffer[tile_y + y, tile_x + x] = self.palette[color_idx]

class CustomNES:
    def __init__(self, rom_path):
        self.cartridge = Cartridge(rom_path)
        self.ppu = PPUSim(self.cartridge)
        self.obs = self.ppu.frame_buffer
        self.ppu.render_chr_data() # Render the static frame once on load

    def step(self, action): return self.obs, 0, False, False, {}
    def reset(self): return self.obs, {}
    def close(self): pass

# --- RE-ARCHITECTED GUI AND APPLICATION LOGIC ---

class Emulator:
    """ Manages the environment, which can be loaded and closed. """
    def __init__(self):
        self.env = None

    @property
    def is_loaded(self):
        return self.env is not None

    def load_rom(self, rom_path):
        try:
            if self.is_loaded: self.env.close()
            self.env = CustomNES(rom_path)
            return self.env.obs, None
        except Exception as e:
            return None, e

    def close(self):
        if self.is_loaded: self.env.close()
        self.env = None

class UI(tk.Tk):
    """ A true GUI-first application. """
    def __init__(self):
        super().__init__()
        self.title("NESTICLE")
        self.resizable(False, False)
        
        self.emu = Emulator()
        
        # Create a black frame to hold the canvas
        canvas_frame = tk.Frame(self, bg="black", padx=2, pady=2)
        canvas_frame.pack()
        self.canvas = tk.Canvas(canvas_frame, width=512, height=480, bg="black", highlightthickness=0)
        self.canvas.pack()
        
        self.img_ref = None # GC protection
        self.after_id = None
        
        self._create_menu()
        self.show_splash_screen()
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def show_splash_screen(self):
        self.canvas.delete("all")
        self.canvas.config(bg="black")
        self.canvas.create_text(256, 180, text="NESTICLE", fill="#B0B0B0", font=("TkFixedFont", 48, "bold"))
        self.canvas.create_text(256, 260, text="File -> Open ROM...", fill="#808080", font=("TkFixedFont", 14))
        self.title("NESTICLE")

    def open_rom_dialog(self):
        rom_path = filedialog.askopenfilename(
            title="Open NES/Famicom ROM",
            filetypes=(("NES ROMs", "*.nes"), ("Famicom ROMs", "*.fam"), ("All Files", "*.*"))
        )
        if not rom_path:
            return

        initial_obs, error = self.emu.load_rom(rom_path)
        
        if error:
            messagebox.showerror("ROM Error", f"Failed to load ROM:\n{error}")
            self.emu.close()
            return
        
        self.title(f"NESTICLE - {os.path.basename(rom_path)}")
        self.menu_bar.entryconfigure("File", state="normal") # Enable menu
        self.draw_frame(initial_obs)

    def draw_frame(self, frame_data):
        img = Image.fromarray(frame_data.astype(np.uint8), "RGB").resize((512, 480), Image.NEAREST)
        tk_img = ImageTk.PhotoImage(img)
        self.img_ref = tk_img
        self.canvas.create_image(0, 0, image=tk_img, anchor=tk.NW)

    def _create_menu(self):
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)
        
        # File Menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Open ROM...", command=self.open_rom_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

    def on_close(self):
        self.emu.close()
        self.destroy()

if __name__ == "__main__":
    # Initialize Pygame for potential future audio use, but don't let it fail the app
    try:
        pygame.mixer.init()
    except Exception as e:
        print(f"Could not initialize pygame.mixer: {e}")
        
    app = UI()
    app.mainloop()

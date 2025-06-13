# nesticle_inspector.py - The final blueprint. A GUI that loads and inspects any .nes file.
# Run with: python nesticle_inspector.py

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
from PIL import Image, ImageTk

# --- CORE EMULATOR BLUEPRINT ---

class Cartridge:
    """ Parses an iNES ROM file and holds its data. """
    def __init__(self, rom_path):
        with open(rom_path, 'rb') as f:
            header = f.read(16)
            if header[0:4] != b'NES\x1a': raise IOError("Invalid iNES ROM.")
            self.prg_banks = header[4]
            self.chr_banks = header[5]
            self.mapper_id = (header[6] >> 4) | (header[7] & 0xF0)
            self.mirroring = 1 if header[6] & 1 else 0 # 0=Horiz, 1=Vert
            
            # Skip trainer if present
            if header[6] & 0b100: f.seek(512, 1)

            prg_size = self.prg_banks * 16384
            chr_size = self.chr_banks * 8192
            self.prg_rom = f.read(prg_size)
            self.chr_rom = f.read(chr_size) if chr_size > 0 else b'\x00' * 8192

class PPUBlueprint:
    """ Renders the raw graphics data from a loaded cartridge. """
    def __init__(self, cartridge):
        self.cart = cartridge
        self.frame_buffer = np.zeros((240, 256, 3), dtype=np.uint8)
        self.palette = np.array([
            [124,124,124], [0,0,252], [0,0,188], [68,40,188], [148,0,132], 
            [168,0,32], [168,16,0], [136,20,0], [80,48,0], [0,120,0], 
            [0,104,0], [0,88,0], [0,64,88], [0,0,0]], dtype=np.uint8)

    def render_chr_data(self):
        """ Renders the entire CHR-ROM contents to the framebuffer. """
        self.frame_buffer.fill(20)
        total_tiles = len(self.cart.chr_rom) // 16
        for tile_idx in range(total_tiles):
            tile_x = (tile_idx % 32) * 8
            tile_y = (tile_idx // 32) * 8
            if tile_y >= 240: break
            
            tile_data = self.cart.chr_rom[tile_idx*16 : tile_idx*16 + 16]
            for y in range(8):
                plane1, plane2 = tile_data[y], tile_data[y + 8]
                for x in range(8):
                    color_idx = ((plane1 >> (7 - x)) & 1) | (((plane2 >> (7 - x)) & 1) << 1)
                    if color_idx != 0:
                        self.frame_buffer[tile_y + y, tile_x + x] = self.palette[color_idx]

class CustomNESBlueprint:
    """ A blueprint that holds the loaded cartridge and its components. """
    def __init__(self, rom_path):
        self.cartridge = Cartridge(rom_path)
        self.ppu = PPUBlueprint(self.cartridge)
        self.ppu.render_chr_data()
        self.obs = self.ppu.frame_buffer

# --- RE-ARCHITECTED GUI: THE ROM INSPECTOR ---

class UI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NESTICLE INSPECTOR")
        self.resizable(False, False)
        
        self.cart_data = {}

        # --- Main Layout ---
        main_frame = tk.Frame(self, bg="#3c3c3c")
        main_frame.pack()
        
        # --- Canvas for game output ---
        canvas_frame = tk.Frame(main_frame, bg="black", padx=2, pady=2)
        canvas_frame.grid(row=0, column=0, padx=5, pady=5)
        self.canvas = tk.Canvas(canvas_frame, width=512, height=480, bg="black", highlightthickness=0)
        self.canvas.pack()
        
        # --- Info panel for iNES data ---
        info_frame = tk.Frame(main_frame, bg="#3c3c3c")
        info_frame.grid(row=0, column=1, sticky="nw", padx=5, pady=5)
        tk.Label(info_frame, text="iNES ROM DATA", font=("TkFixedFont", 14, "bold"), fg="white", bg="#3c3c3c").pack(anchor="w")
        
        self.info_labels = {}
        for info_key in ["Mapper ID", "PRG Banks", "CHR Banks", "Mirroring"]:
            frame = tk.Frame(info_frame, bg="#3c3c3c")
            frame.pack(fill="x", pady=2)
            tk.Label(frame, text=f"{info_key}:", font=("TkFixedFont", 10), fg="#a0a0a0", bg="#3c3c3c").pack(side="left")
            val_label = tk.Label(frame, text="--", font=("TkFixedFont", 10, "bold"), fg="white", bg="#3c3c3c")
            val_label.pack(side="right")
            self.info_labels[info_key] = val_label

        self.img_ref = None
        self._create_menu()
        self.show_splash_screen()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def show_splash_screen(self):
        self.canvas.delete("all")
        self.canvas.create_text(256, 240, text="File -> Open ROM...", fill="#808080", font=("TkFixedFont", 14))
        for key, label in self.info_labels.items():
            label.config(text="--")

    def open_rom_dialog(self):
        rom_path = filedialog.askopenfilename(filetypes=(("NES ROMs", "*.nes"), ("All Files", "*.*")))
        if not rom_path: return

        try:
            # Load the blueprint and extract data
            blueprint = CustomNESBlueprint(rom_path)
            cart = blueprint.cartridge
            
            # Update GUI with parsed iNES header data
            self.title(f"INSPECTOR - {os.path.basename(rom_path)}")
            self.info_labels["Mapper ID"].config(text=str(cart.mapper_id))
            self.info_labels["PRG Banks"].config(text=str(cart.prg_banks))
            self.info_labels["CHR Banks"].config(text=str(cart.chr_banks))
            self.info_labels["Mirroring"].config(text="Vertical" if cart.mirroring == 1 else "Horizontal")
            
            # Draw the CHR-ROM data to the screen
            self.draw_frame(blueprint.obs)

        except Exception as e:
            messagebox.showerror("ROM Error", f"Failed to load ROM:\n{e}")
            self.show_splash_screen()

    def draw_frame(self, frame_data):
        img = Image.fromarray(frame_data.astype(np.uint8), "RGB").resize((512, 480), Image.NEAREST)
        tk_img = ImageTk.PhotoImage(img)
        self.img_ref = tk_img
        self.canvas.create_image(0, 0, image=tk_img, anchor=tk.NW)

    def _create_menu(self):
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Open ROM...", command=self.open_rom_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

if __name__ == "__main__":
    app = UI()
    app.mainloop()

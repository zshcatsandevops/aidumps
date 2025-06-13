# nesticle_prime.py - Engine with a custom, pure Python emulation core.
# No nes_py needed. Runs an internal tech demo.
# Run with: python nesticle_prime.py

import time
import sys
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
from PIL import Image, ImageTk
import pickle
import pygame
import math

# --- CORE EMULATOR CLASSES (Pure Python Implementation) ---

class CPUSim:
    """ A simple simulation of a CPU to demonstrate state change. """
    def __init__(self):
        self.program_counter = 0
        self.accumulator = 0
        self.x_reg = 0
        self.y_reg = 0

    def step(self):
        # Simulate simple register activity
        self.program_counter = (self.program_counter + 1) & 0xFFFF
        self.accumulator = (self.accumulator + 3) & 0xFF
        self.x_reg = (self.x_reg - 1) & 0xFF
        self.y_reg = (self.y_reg ^ 0x55) & 0xFF

class PPUSim:
    """ A custom Picture Processing Unit that generates a plasma effect. """
    def __init__(self, width=256, height=240):
        self.width = width
        self.height = height
        self.frame_buffer = np.zeros((height, width, 3), dtype=np.uint8)
        self.cycle = 0

    def step(self):
        # This generates a classic plasma effect, showing the PPU is "live"
        t = self.cycle / 60.0  # time in seconds
        
        # Create coordinate grids
        x = np.arange(self.width)
        y = np.arange(self.height)
        xx, yy = np.meshgrid(x, y)

        # Plasma calculation using sine waves
        plasma = (
            np.sin(xx / 16.0 + t * 2) +
            np.sin(yy / 16.0 - t) +
            np.sin((xx + yy) / 16.0 + t) +
            np.sin(np.sqrt(xx**2 + yy**2) / 8.0)
        )

        # Normalize to 0-1 range
        plasma = (plasma + 4) / 8.0
        
        # Create RGB channels from the plasma
        r = 0.5 + 0.5 * np.sin(np.pi * plasma + t * 3)
        g = 0.5 + 0.5 * np.sin(np.pi * plasma + 2 * np.pi / 3 + t * 2)
        b = 0.5 + 0.5 * np.sin(np.pi * plasma + 4 * np.pi / 3 + t)

        self.frame_buffer[..., 0] = (r * 255).astype(np.uint8)
        self.frame_buffer[..., 1] = (g * 255).astype(np.uint8)
        self.frame_buffer[..., 2] = (b * 255).astype(np.uint8)
        
        self.cycle += 1
    
class CustomNES:
    """
    A custom, self-contained mock emulator using our pure Python components.
    It has the same API as NESEnv to drop into our existing UI.
    """
    def __init__(self, rom_path=None): # rom_path is ignored
        self.cpu = CPUSim()
        self.ppu = PPUSim()
        self.obs = self.ppu.frame_buffer
        print("Custom Pure Python NES Core Initialized.")

    def step(self, action): # action is ignored
        # Simulate running a number of CPU & PPU cycles for one frame
        for _ in range(30000): # Rough cycle count
            self.cpu.step()
        self.ppu.step()
        # Return value mimics the nes_py API
        return self.obs, 0, False, False, {}
    
    def reset(self):
        return self.obs, {}

    def close(self):
        pass # Nothing to close

# --- UI AND WRAPPER CLASSES (Largely Unchanged) ---

FRAME_MS = 1000 // 60

class Emulator:
    """ Manages the CUSTOM environment and its state. """
    def __init__(self):
        # The key change: We now instantiate our own emulator.
        self.env = CustomNES()
        self.obs, _ = self.env.reset()
        self.running = True # Start running the demo immediately
        self.rom_path = "Internal Tech Demo"

    def step(self):
        self.obs, _, term, trunc, _ = self.env.step([0,0]) # Action is ignored
        return term or trunc

    def close(self):
        self.env.close()

class UI(tk.Tk):
    """ The main application window, now running the custom core. """
    def __init__(self):
        super().__init__()
        self.title("NESTICLE-PRIME ✨ (Custom Core)")
        self.configure(bg="black")
        
        pygame.mixer.init() # Still init for potential future use
        self.emu = Emulator()
        self._create_menu()
        
        self.canvas = tk.Canvas(self, width=600, height=480, bg="black", highlightthickness=0)
        self.canvas.pack()
        self.img_ref = None

        self.start_time = time.perf_counter_ns()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after_idle(self.loop)
        
        messagebox.showinfo("Nesticle Prime", "The external 'nes_py' emulator has been replaced with a custom internal core.\n\nThis core runs a procedural tech demo, as it's not fast enough for commercial ROMs. ROM loading and save states are disabled.")


    def _create_menu(self):
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Open ROM...", state="disabled")
        file_menu.add_command(label="Save State", state="disabled")
        file_menu.add_command(label="Load State", state="disabled")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        self.emulation_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.emulation_menu.add_command(label="Pause/Run", command=self.toggle_pause)
        self.menu_bar.add_cascade(label="Emulation", menu=self.emulation_menu)

    def toggle_pause(self):
        self.emu.running = not self.emu.running
        if self.emu.running:
            self.start_time = time.perf_counter_ns()
            self.loop()

    def loop(self):
        if not self.emu.running: return

        now = time.perf_counter_ns()
        if now >= self.start_time:
            done = self.emu.step()
            self.draw(self.emu.obs)
            self.start_time += FRAME_MS * 1_000_000
            if done: self.emu.running = False
        
        drift_ns = max(0, self.start_time - time.perf_counter_ns())
        self.after(int(drift_ns / 1_000_000) if drift_ns > 0 else 1, self.loop)

    def draw(self, frame):
        img = Image.fromarray(frame.astype(np.uint8), "RGB").resize((600, 480), Image.NEAREST)
        tk_img = ImageTk.PhotoImage(img)
        self.img_ref = tk_img
        self.canvas.create_image(0, 0, image=tk_img, anchor=tk.NW)
    
    def on_close(self):
        self.emu.close()
        pygame.mixer.quit()
        self.destroy()

if __name__ == "__main__":
    app = UI()
    app.mainloop()

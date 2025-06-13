# nesticle_600x400.py – 60‑FPS‑safe rewrite with 600x400 pixelated display and nes_py fallback
# Run with: python nesticle_600x400.py <your_rom>.nes

import time
import sys
import os
import tkinter as tk
from tkinter import messagebox
import numpy as np
from PIL import Image, ImageTk

# Attempt to import nes_py; if unavailable, use mock NESEnv
try:
    from nes_py import NESEnv  # official nes‑py base class
except ImportError:
    class NESEnv:
        def __init__(self, rom_path):
            self.rom_path = rom_path
            # standard NES frame dimensions
            self.frame = np.zeros((240, 256, 3), dtype=np.uint8)
        def reset(self):
            return self.frame, {}
        def step(self, action):
            # Return (obs, reward, terminated, truncated, info)
            return self.frame, 0, False, False, {}
        def close(self):
            pass

FRAME_MS = 1000 // 60  # ~16 ms = 60 FPS target

class Emulator:
    def __init__(self, rom):
        self.env = NESEnv(rom)
        self.obs, _ = self.env.reset()
        self.running = False

    def step(self, act=0):
        self.obs, _, term, trunc, _ = self.env.step(act)
        return term or trunc  # “done” flag

    def close(self):
        self.env.close()

class UI(tk.Tk):
    def __init__(self, rom):
        super().__init__()
        self.title(f"NESTICLE-TK 600x400 ✨ – {os.path.basename(rom)}")
        # Window size
        self.window_width = 600
        self.window_height = 400
        self.canvas = tk.Canvas(self, width=self.window_width, height=self.window_height, bg="black")
        self.canvas.pack()
        self.img_ref = None  # protect against GC
        self.emu = Emulator(rom)
        self.start_time = 0
        self.bind("<space>", self.toggle)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after_idle(self.loop)

    def toggle(self, _evt=None):
        self.emu.running = not self.emu.running
        self.start_time = time.perf_counter_ns()

    def loop(self):
        tgt = self.start_time + FRAME_MS * 1_000_000
        now = time.perf_counter_ns()
        if self.emu.running and now >= tgt:
            done = self.emu.step()
            self.draw(self.emu.obs)
            self.start_time = now
            if done:
                self.emu.running = False
        drift = max(0, FRAME_MS - (time.perf_counter_ns() - now) // 1_000_000)
        self.after(drift, self.loop)

    def draw(self, frame):
        img = Image.fromarray(frame.astype(np.uint8), "RGB")
        # Resize with nearest-neighbor for a pixelated look
        img = img.resize((self.window_width, self.window_height), Image.NEAREST)
        tk_img = ImageTk.PhotoImage(img)
        self.img_ref = tk_img
        self.canvas.create_image(0, 0, image=tk_img, anchor=tk.NW)

    def on_close(self):
        self.emu.close()
        self.destroy()

if __name__ == "__main__":
    if len(sys.argv) != 2 or not sys.argv[1].endswith(".nes"):
        print("Usage: python nesticle_600x400.py <rom>.nes")
        sys.exit(1)
    UI(sys.argv[1]).mainloop()

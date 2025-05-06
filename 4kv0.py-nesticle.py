import tkinter as tk
from tkinter import filedialog, messagebox
import pygame
import numpy as np
import os

# iNES HEADER PARSER (WITH MAPPER SUPPORT) [[7]][[9]]
class ROM:
    def __init__(self, path):
        with open(path, "rb") as f:
            self.data = bytearray(f.read())

        # Parse iNES header (16-byte header + trainer)
        self.header = self.data[:16]
        if self.header[:4] != b"NES\x1a":
            raise ValueError("Invalid iNES file - missing header")

        self.prg_banks = self.header[4]
        self.chr_banks = self.header[5]
        self.mapper = (self.header[6] >> 4) | (self.header[7] & 0xF0)
        self.mirroring = self.header[6] & 0x01
        self.battery = bool(self.header[6] & 0x02)
        self.trainer = self.data[16:528] if self.header[6] & 0x04 else None

        prg_start = 16 + (512 if self.trainer else 0)
        self.prg_rom = self.data[prg_start: prg_start + 16384 * self.prg_banks]
        self.chr_rom = self.data[prg_start + 16384 * self.prg_banks:] if self.chr_banks > 0 else bytearray(8192)

# 6502 CPU EMULATION (MINIMAL OPCODE IMPLEMENTATION)
class CPU:
    def __init__(self, rom):
        self.rom = rom
        self.reset()

    def reset(self):
        self.pc = 0xFFFC  # Reset vector
        self.sp = 0xFD
        self.acc = 0x00
        self.x = 0x00
        self.y = 0x00
        self.status = 0x24  # Default flags

    def step(self):
        opcode = self.read(self.pc)
        self.pc += 1
        # Simplified opcode dispatch (add full implementation later)
        if opcode == 0xA9:  # LDA Immediate
            self.acc = self.read(self.pc)
            self.pc += 1
        elif opcode == 0x4C:  # JMP Absolute
            self.pc = self.read_word(self.pc)
        return opcode

    def read(self, addr):
        if 0x8000 <= addr < 0xC000 and len(self.rom.prg_rom) == 0x4000:
            return self.rom.prg_rom[addr - 0x8000]
        elif 0xC000 <= addr < 0x10000:
            return self.rom.prg_rom[addr - 0xC000 if len(self.rom.prg_rom) == 0x4000 else addr - 0x8000]
        return 0x00

    def read_word(self, addr):
        return self.read(addr) | (self.read(addr + 1) << 8)

# PPU EMULATION (TILE-BASED RENDERING)
class PPU:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((256, 240))
        self.clock = pygame.time.Clock()
        self.framebuffer = pygame.Surface((256, 240))

    def render_frame(self, chr_rom, palette):
        self.framebuffer.fill((0, 0, 0))
        # Render background tiles (simplified)
        for tile_y in range(30):  # 30 rows
            for tile_x in range(32):  # 32 columns
                tile_index = tile_y * 32 + tile_x
                if tile_index < len(chr_rom) // 16:
                    self.draw_tile(chr_rom, tile_x * 8, tile_y * 8, tile_index, palette)
        self.screen.blit(self.framebuffer, (0, 0))
        pygame.display.flip()
        self.clock.tick(60)

    def draw_tile(self, chr_rom, x, y, index, palette):
        tile_data = chr_rom[index * 16:(index + 1) * 16]
        for row in range(8):
            lsb = tile_data[row]
            msb = tile_data[row + 8]
            for bit in range(8):
                color_bit = ((lsb >> (7 - bit)) & 1) | (((msb >> (7 - bit)) & 1) << 1)
                color = palette[color_bit]
                self.framebuffer.set_at((x + bit, y + row), color)

# APU EMULATION (BASIC SQUARE WAVE)
class APU:
    def __init__(self):
        pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)

    def generate_square(self, frequency=440, duration=0.1):
        t = np.linspace(0, duration, int(44100 * duration), endpoint=False)
        wave = np.where(np.sin(2 * np.pi * frequency * t) > 0, 32767, -32768)
        sound = pygame.sndarray.make_sound(wave.astype(np.int16))
        sound.play()

# NES EMULATOR KERNEL
class NES:
    def __init__(self, rom_path):
        self.rom = ROM(rom_path)
        self.cpu = CPU(self.rom)
        self.ppu = PPU()
        self.apu = APU()
        # Standard NTSC palette (simplified)
        self.palette = [(0, 0, 0), (255, 0, 0), (0, 255, 0), (255, 255, 255)]

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            # Emulate one frame
            for _ in range(29780):  # ~60 FPS (approximate CPU cycles per frame)
                self.cpu.step()
            self.ppu.render_frame(self.rom.chr_rom, self.palette)
            self.apu.generate_square(440, 0.01)

# FULL GUI + EMULATOR INTEGRATION
class NESticleGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("NESticle - NES Emulator")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        self.root.configure(bg="#000080")

        # GUI COMPONENTS
        self.title_label = tk.Label(root, text="NESticle v0.1", font=("Courier New", 18, "bold"), fg="white", bg="#000080")
        self.title_label.pack(pady=10)

        self.rom_frame = tk.Frame(root, bg="#000080")
        self.rom_frame.pack(pady=5)

        self.rom_listbox = tk.Listbox(self.rom_frame, width=60, height=10, font=("Courier New", 10), bg="#000000", fg="lime")
        self.rom_listbox.pack(side="left", fill="both")

        self.scrollbar = tk.Scrollbar(self.rom_frame, orient="vertical", command=self.rom_listbox.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.rom_listbox.config(yscrollcommand=self.scrollbar.set)

        self.button_frame = tk.Frame(root, bg="#000080")
        self.button_frame.pack(pady=10)

        self.load_button = tk.Button(self.button_frame, text="Load ROM", width=12, bg="#C0C0C0", fg="black", command=self.load_rom)
        self.load_button.grid(row=0, column=0, padx=5)

        self.play_button = tk.Button(self.button_frame, text="Play", width=12, bg="#C0C0C0", fg="black", command=self.play_game)
        self.play_button.grid(row=0, column=1, padx=5)

        self.exit_button = tk.Button(self.button_frame, text="Exit", width=12, bg="#C0C0C0", fg="black", command=root.quit)
        self.exit_button.grid(row=0, column=2, padx=5)

    def load_rom(self):
        file_path = filedialog.askopenfilename(title="Select NES ROM", filetypes=[("NES Files", "*.nes")])
        if file_path:
            self.rom_listbox.delete(0, tk.END)
            self.rom_listbox.insert(tk.END, file_path)  # Store full path

    def play_game(self):
        selected = self.rom_listbox.curselection()
        if selected:
            rom_path = self.rom_listbox.get(selected)
            if not os.path.isfile(rom_path):
                messagebox.showerror("File Not Found", f"The ROM file was not found:\n{rom_path}")
                return
            self.root.withdraw()  # Hide Tkinter window
            try:
                nes = NES(rom_path)
                nes.run()
            except ValueError as e:
                messagebox.showerror("Invalid ROM", str(e))
            except Exception as e:
                messagebox.showerror("Emulation Error", str(e))
            finally:
                self.root.deiconify()
        else:
            messagebox.showwarning("No Selection", "Please select a ROM first!")

if __name__ == "__main__":
    root = tk.Tk()
    app = NESticleGUI(root)
    root.mainloop()

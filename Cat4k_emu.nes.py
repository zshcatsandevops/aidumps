import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np

SCREEN_WIDTH = 256
SCREEN_HEIGHT = 240
NES_FRAME_RATE = 60

class Mapper0:
    def __init__(self, prg_rom, chr_rom):
        self.prg_rom = prg_rom
        self.chr_rom = chr_rom if chr_rom else bytearray(0x2000)  # 8KB CHR RAM if no CHR ROM

    def read_prg(self, addr):
        if 0x8000 <= addr <= 0xFFFF:
            return self.prg_rom[addr - 0x8000 & 0x3FFF]  # 16KB mirrored
        return 0

    def write_prg(self, addr, value):
        pass  # NROM is read-only

    def read_chr(self, addr):
        return self.chr_rom[addr & 0x1FFF]

    def write_chr(self, addr, value):
        pass

class PPU:
    def __init__(self, cpu):
        self.cpu = cpu
        self.cycle = 0
        self.frame_complete = False
        self.screen = np.zeros((SCREEN_HEIGHT, SCREEN_WIDTH, 3), dtype=np.uint8)

    def step(self):
        self.cycle += 1
        if self.cycle >= 89342:  # PPU cycles per frame (341 * 262)
            self.frame_complete = True
            self.cycle = 0
            if self.cycle == 1 and self.cpu.scanline == 241:  # VBlank NMI
                self.cpu.nmi_pending = True

    def render(self):
        return self.screen

class MOS6502:
    def __init__(self):
        self.pc = 0
        self.sp = 0xFD
        self.a = self.x = self.y = 0
        self.cycle = 0
        self.flags = 0x24  # Interrupt disable set
        self.memory = bytearray(0x800)  # 2KB RAM
        self.mapper = None
        self.ppu = None
        self.nmi_pending = False
        self.irq_pending = False
        self.stall = 0

    def reset(self):
        self.pc = self.read_word(0xFFFC)
        self.sp = 0xFD
        self.flags = 0x24
        self.a = self.x = self.y = 0
        self.cycle = 0

    def read_byte(self, addr):
        if addr < 0x2000:
            return self.memory[addr & 0x7FF]
        elif addr >= 0x8000:
            return self.mapper.read_prg(addr)
        return 0

    def read_word(self, addr):
        lo = self.read_byte(addr)
        hi = self.read_byte(addr + 1)
        return (hi << 8) | lo

    def write_byte(self, addr, value):
        if addr < 0x2000:
            self.memory[addr & 0x7FF] = value & 0xFF

    def load_rom(self, rom):
        if rom[0:4] != b'NES\x1a':
            raise ValueError("Invalid iNES header")
        prg_banks = rom[4]
        chr_banks = rom[5]
        header_size = 16
        prg_size = prg_banks * 0x4000
        chr_size = chr_banks * 0x2000
        prg_rom = rom[header_size:header_size + prg_size]
        chr_rom = rom[header_size + prg_size:header_size + prg_size + chr_size] if chr_banks else None
        self.mapper = Mapper0(prg_rom, chr_rom)
        self.reset()

    def step(self):
        if self.stall > 0:
            self.stall -= 1
            return 1
        if self.nmi_pending:
            self.handle_nmi()
            return 7
        elif self.irq_pending and not (self.flags & 0x04):
            self.handle_irq()
            return 7
        opcode = self.read_byte(self.pc)
        self.pc += 1
        if opcode == 0x4C:  # JMP Absolute
            addr = self.read_word(self.pc)
            self.pc = addr
            return 3
        else:
            raise NotImplementedError(f"Opcode {opcode:02X} not implemented")

    def handle_nmi(self):
        self.push_word(self.pc)
        self.push_byte(self.flags | 0x20)
        self.pc = self.read_word(0xFFFA)
        self.flags |= 0x04
        self.nmi_pending = False

    def handle_irq(self):
        self.push_word(self.pc)
        self.push_byte(self.flags | 0x20)
        self.pc = self.read_word(0xFFFE)
        self.flags |= 0x04
        self.irq_pending = False

    def push_byte(self, value):
        self.write_byte(0x100 + self.sp, value)
        self.sp = (self.sp - 1) & 0xFF

    def push_word(self, value):
        self.push_byte(value >> 8)
        self.push_byte(value & 0xFF)

class NESGUI:
    def __init__(self, root, cpu):
        self.root = root
        self.root.title("NES Emulator")
        self.root.configure(bg='#2c2c2c')
        self.cpu = cpu
        self.cpu.ppu = PPU(self.cpu)
        self.running = False
        self.tk_image = None
        self._create_menu()
        self._create_display()
        self._create_controls()
        self._create_statusbar()
        self.root.minsize(SCREEN_WIDTH + 20, SCREEN_HEIGHT + 80)

    def _create_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Load ROM…", command=self.load_rom, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Alt+F4")
        menubar.add_cascade(label="File", menu=file_menu)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.root.config(menu=menubar)
        self.root.bind("<Control-o>", lambda e: self.load_rom())

    def _create_display(self):
        self.canvas = tk.Canvas(self.root, width=SCREEN_WIDTH, height=SCREEN_HEIGHT, bg='black', highlightthickness=0)
        self.canvas.pack(pady=5)
        blank = Image.new('RGB', (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.blank_image = ImageTk.PhotoImage(blank)
        self.canvas_image = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.blank_image)

    def _create_controls(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=5)
        self.load_btn = tk.Button(frame, text="📁 Load ROM", width=12, command=self.load_rom, bg="#4CAF50", fg="white")
        self.start_btn = tk.Button(frame, text="▶️ Start", width=12, command=self.start_emulation, bg="#2196F3", fg="white")
        self.pause_btn = tk.Button(frame, text="⏸️ Pause", width=12, command=self.pause_emulation, bg="#FF9800", fg="white")
        for btn in (self.load_btn, self.start_btn, self.pause_btn):
            btn.pack(side=tk.LEFT, padx=5)

    def _create_statusbar(self):
        self.status_var = tk.StringVar()
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W, bg='#1e1e1e', fg='white')
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.update_status("Ready")

    def update_status(self, msg):
        self.status_var.set(f"Status: {msg}")
        self.root.update_idletasks()

    def load_rom(self):
        fname = filedialog.askopenfilename(title="Select NES ROM", filetypes=[("NES ROMs", "*.nes"), ("All files", "*.*")])
        if not fname:
            return
        try:
            with open(fname, 'rb') as f:
                rom = bytearray(f.read())
            self.cpu.load_rom(rom)
            self.update_status(f"Loaded: {os.path.basename(fname)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load ROM: {e}")

    def start_emulation(self):
        if not self.running:
            self.running = True
            self.update_status("Emulation running")
            self._update_loop()

    def pause_emulation(self):
        self.running = False
        self.update_status("Emulation paused")

    def _update_loop(self):
        if not self.running:
            return
        while not self.cpu.ppu.frame_complete:
            instruction_cycles = self.cpu.step()
            for _ in range(instruction_cycles * 3):
                self.cpu.ppu.step()
        self.cpu.ppu.frame_complete = False
        buf = self.cpu.ppu.render()
        img = Image.fromarray(buf)
        self.tk_image = ImageTk.PhotoImage(img)
        self.canvas.itemconfig(self.canvas_image, image=self.tk_image)
        self.root.after(1000 // NES_FRAME_RATE, self._update_loop)

    def show_about(self):
        messagebox.showinfo("About", "NES Emulator\nVersion 1.0\n\nA simple NES emulator in Python")

def main():
    root = tk.Tk()
    cpu = MOS6502()
    app = NESGUI(root, cpu)
    root.mainloop()

if __name__ == "__main__":
    main()

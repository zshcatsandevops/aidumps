import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
import time

SCREEN_WIDTH = 256
SCREEN_HEIGHT = 240
NES_FRAME_RATE = 60  # Target frame rate

# NES Palette (NTSC) - Standard RGB values
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
        self.chr_mem = chr_data if chr_rom_banks > 0 else bytearray(0x2000)  # 8KB CHR RAM if no ROM
        self.is_chr_ram = (chr_rom_banks == 0)

    def read_prg(self, addr):
        if 0x8000 <= addr <= 0xFFFF:
            return self.prg_rom[(addr - 0x8000) & 0x3FFF] if self.prg_banks == 1 else self.prg_rom[addr - 0x8000]
        return 0

    def write_prg(self, addr, value):
        pass  # Mapper 0 does not support PRG writes

    def read_chr(self, addr):
        return self.chr_mem[addr] if 0x0000 <= addr <= 0x1FFF else 0

    def write_chr(self, addr, value):
        if 0x0000 <= addr <= 0x1FFF and self.is_chr_ram:
            self.chr_mem[addr] = value

class PPU:
    def __init__(self, cpu):
        self.cpu = cpu
        self.mapper = None
        self.cycle = 0
        self.scanline = 0
        self.frame_complete = False
        self.screen = np.zeros((SCREEN_HEIGHT, SCREEN_WIDTH, 3), dtype=np.uint8)

        # PPU Registers
        self.ppuctrl = 0x00
        self.ppumask = 0x00
        self.ppustatus = 0x00
        self.oamaddr = 0x00
        self.oamdata = bytearray(256)
        self.vram_addr = 0
        self.temp_vram_addr = 0
        self.fine_x_scroll = 0
        self.write_toggle = False
        self.ppu_data_buffer = 0x00
        self.vram = bytearray(0x2000)  # 2KB Nametable RAM
        self.palette_ram = bytearray(0x20)  # 32 bytes Palette RAM
        self.nmi_occurred = False
        self.nmi_output = False

    def connect_mapper(self, mapper):
        self.mapper = mapper

    def read_register(self, addr):
        reg = addr & 0x0007
        if reg == 0x0002:  # PPUSTATUS
            val = (self.ppustatus & 0xE0) | (self.ppu_data_buffer & 0x1F)
            self.ppustatus &= ~0x80
            self.write_toggle = False
            self.nmi_occurred = False
            return val
        elif reg == 0x0004:  # OAMDATA
            return self.oamdata[self.oamaddr]
        elif reg == 0x0007:  # PPUDATA
            val = self.ppu_data_buffer
            self.ppu_data_buffer = self._ppu_read(self.vram_addr)
            if self.vram_addr >= 0x3F00:
                val = self.ppu_data_buffer
            self.vram_addr = (self.vram_addr + (32 if self.ppuctrl & 0x04 else 1)) & 0x3FFF
            return val
        return 0

    def write_register(self, addr, value):
        reg = addr & 0x0007
        self.ppu_data_buffer = value
        if reg == 0x0000:  # PPUCTRL
            self.ppuctrl = value
            self.nmi_output = (self.ppuctrl & 0x80) != 0 and self.nmi_occurred
            self.temp_vram_addr = (self.temp_vram_addr & 0xF3FF) | ((value & 0x03) << 10)
        elif reg == 0x0001:  # PPUMASK
            self.ppumask = value
        elif reg == 0x0003:  # OAMADDR
            self.oamaddr = value
        elif reg == 0x0004:  # OAMDATA
            self.oamdata[self.oamaddr] = value
            self.oamaddr = (self.oamaddr + 1) & 0xFF
        elif reg == 0x0005:  # PPUSCROLL
            if not self.write_toggle:
                self.temp_vram_addr = (self.temp_vram_addr & 0xFFE0) | (value >> 3)
                self.fine_x_scroll = value & 0x07
            else:
                self.temp_vram_addr = (self.temp_vram_addr & 0x8C1F) | ((value & 0xF8) << 2) | ((value & 0x07) << 12)
            self.write_toggle = not self.write_toggle
        elif reg == 0x0006:  # PPUADDR
            if not self.write_toggle:
                self.temp_vram_addr = (self.temp_vram_addr & 0x00FF) | ((value & 0x3F) << 8)
            else:
                self.temp_vram_addr = (self.temp_vram_addr & 0xFF00) | value
                self.vram_addr = self.temp_vram_addr
            self.write_toggle = not self.write_toggle
        elif reg == 0x0007:  # PPUDATA
            self._ppu_write(self.vram_addr, value)
            self.vram_addr = (self.vram_addr + (32 if self.ppuctrl & 0x04 else 1)) & 0x3FFF

    def _ppu_read(self, addr):
        addr &= 0x3FFF
        if 0x0000 <= addr <= 0x1FFF:
            return self.mapper.read_chr(addr)
        elif 0x2000 <= addr <= 0x3EFF:
            return self.vram[addr & 0x07FF]  # Simplified 2KB mirror
        elif 0x3F00 <= addr <= 0x3FFF:
            addr &= 0x001F
            if addr in (0x0010, 0x0014, 0x0018, 0x001C):
                addr &= 0x000F
            return self.palette_ram[addr]
        return 0

    def _ppu_write(self, addr, value):
        addr &= 0x3FFF
        if 0x0000 <= addr <= 0x1FFF:
            self.mapper.write_chr(addr, value)
        elif 0x2000 <= addr <= 0x3EFF:
            self.vram[addr & 0x07FF] = value
        elif 0x3F00 <= addr <= 0x3FFF:
            addr &= 0x001F
            if addr in (0x0010, 0x0014, 0x0018, 0x001C):
                addr &= 0x000F
            self.palette_ram[addr] = value

    def step(self):
        if self.scanline == 261 and self.cycle == 1:
            self.ppustatus &= ~0xE0
            self.nmi_occurred = False
        elif self.scanline == 241 and self.cycle == 1:
            self.ppustatus |= 0x80
            self.nmi_occurred = True
            if self.nmi_output:
                self.cpu.nmi_pending = True
            self.frame_complete = True

        if self.rendering_enabled():
            if self.cycle == 257 and self.scanline <= 239 or self.scanline == 261:
                if (self.vram_addr & 0x001F) == 31:
                    self.vram_addr = (self.vram_addr & ~0x001F) ^ 0x0400
                else:
                    self.vram_addr += 1
            if self.cycle == 256 and self.scanline <= 239 or self.scanline == 261:
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

        self.cycle += 1
        if self.cycle > 340:
            self.cycle = 0
            self.scanline = (self.scanline + 1) % 262

    def rendering_enabled(self):
        return (self.ppumask & 0x08) or (self.ppumask & 0x10)

    def get_bg_palettes_rgb(self):
        universal_bg_idx = self._ppu_read(0x3F00) & 0x3F
        bg_palettes = [
            [universal_bg_idx, self._ppu_read(0x3F01) & 0x3F, self._ppu_read(0x3F02) & 0x3F, self._ppu_read(0x3F03) & 0x3F],
            [universal_bg_idx, self._ppu_read(0x3F05) & 0x3F, self._ppu_read(0x3F06) & 0x3F, self._ppu_read(0x3F07) & 0x3F],
            [universal_bg_idx, self._ppu_read(0x3F09) & 0x3F, self._ppu_read(0x3F0A) & 0x3F, self._ppu_read(0x3F0B) & 0x3F],
            [universal_bg_idx, self._ppu_read(0x3F0D) & 0x3F, self._ppu_read(0x3F0E) & 0x3F, self._ppu_read(0x3F0F) & 0x3F],
        ]
        return [[NES_PALETTE[idx] for idx in palette] for palette in bg_palettes]

    def render_scanline(self, sl, bg_palettes_rgb):
        scanline_buffer = np.zeros((264, 3), dtype=np.uint8)  # 33 tiles * 8 pixels
        for tile_x_idx in range(33):
            coarse_x = self.vram_addr & 0x001F
            coarse_y = (self.vram_addr >> 5) & 0x001F
            fine_y = (self.vram_addr >> 12) & 0x07
            nametable_select = (self.vram_addr >> 10) & 0x03
            nt_base = 0x2000 | (nametable_select << 10)
            nt_addr = nt_base + (coarse_y * 32) + coarse_x
            tile_id = self._ppu_read(nt_addr)
            attr_addr = nt_base + 0x03C0 + ((coarse_y // 4) * 8) + (coarse_x // 4)
            attr_byte = self._ppu_read(attr_addr)
            quadrant = ((coarse_y % 4) // 2) * 2 + ((coarse_x % 4) // 2)
            palette_idx_high_bits = (attr_byte >> (quadrant * 2)) & 0x03
            pt_base = 0x1000 if (self.ppuctrl & 0x10) else 0x0000
            tile_addr = pt_base + tile_id * 16 + fine_y
            plane0 = self._ppu_read(tile_addr)
            plane1 = self._ppu_read(tile_addr + 8)
            palette_rgb = bg_palettes_rgb[palette_idx_high_bits]
            for px in range(8):
                bit = 7 - px
                color_idx = ((plane1 >> bit) & 1) << 1 | ((plane0 >> bit) & 1)
                scanline_buffer[tile_x_idx * 8 + px] = palette_rgb[color_idx]
            if (self.vram_addr & 0x001F) == 31:
                self.vram_addr = (self.vram_addr & ~0x001F) ^ 0x0400
            else:
                self.vram_addr += 1
        start_x = self.fine_x_scroll
        visible_pixels = scanline_buffer[start_x:start_x + SCREEN_WIDTH]
        if len(visible_pixels) < SCREEN_WIDTH:
            visible_pixels = np.concatenate((visible_pixels, np.tile(bg_palettes_rgb[0][0], (SCREEN_WIDTH - len(visible_pixels), 1))))
        return visible_pixels

    def get_frame(self):
        if self.frame_complete:
            if self.rendering_enabled():
                bg_palettes_rgb = self.get_bg_palettes_rgb()
                self.vram_addr = self.temp_vram_addr
                for sl in range(SCREEN_HEIGHT):
                    self.screen[sl] = self.render_scanline(sl, bg_palettes_rgb)
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
            else:
                self.screen[:] = NES_PALETTE[self._ppu_read(0x3F00) & 0x3F]
            self.frame_complete = False
        return self.screen

class MOS6502:
    # Flags for P register
    C, Z, I, D, B, U, V, N = [1 << i for i in range(8)]

    def __init__(self):
        self.a = self.x = self.y = 0
        self.sp = 0xFD
        self.pc = 0x0000
        self.status = 0x24  # IRQ disabled, U set
        self.memory = bytearray(0x800)
        self.mapper = self.ppu = None
        self.cycles = self.total_cycles = 0
        self.nmi_pending = self.irq_pending = False
        self.stall_cycles = 0

    def connect_ppu(self, ppu):
        self.ppu = ppu

    def connect_mapper(self, mapper):
        self.mapper = mapper

    def read_byte(self, addr):
        addr &= 0xFFFF
        if addr <= 0x1FFF:
            return self.memory[addr & 0x07FF]
        elif 0x2000 <= addr <= 0x3FFF:
            return self.ppu.read_register(addr)
        elif addr in (0x4016, 0x4017):
            return 0  # Placeholder for controllers
        elif 0x8000 <= addr <= 0xFFFF:
            return self.mapper.read_prg(addr)
        return 0

    def write_byte(self, addr, value):
        addr &= 0xFFFF
        value &= 0xFF
        if addr <= 0x1FFF:
            self.memory[addr & 0x07FF] = value
        elif 0x2000 <= addr <= 0x3FFF:
            self.ppu.write_register(addr, value)
        elif addr == 0x4014:  # OAMDMA
            dma_addr = value << 8
            for i in range(256):
                self.ppu.oamdata[i] = self.read_byte(dma_addr + i)
            self.stall_cycles += 513

    def read_word(self, addr):
        return self.read_byte(addr) | (self.read_byte(addr + 1) << 8)

    def push_byte(self, value):
        self.write_byte(0x0100 + self.sp, value)
        self.sp = (self.sp - 1) & 0xFF

    def push_word(self, value):
        self.push_byte(value >> 8)
        self.push_byte(value & 0xFF)

    def pop_byte(self):
        self.sp = (self.sp + 1) & 0xFF
        return self.read_byte(0x0100 + self.sp)

    def pop_word(self):
        return self.pop_byte() | (self.pop_byte() << 8)

    def _set_flag(self, flag, value):
        self.status = (self.status | flag) if value else (self.status & ~flag)

    def _get_flag(self, flag):
        return (self.status & flag) > 0

    def _update_nz_flags(self, value):
        self._set_flag(self.Z, value == 0)
        self._set_flag(self.N, value & 0x80)

    def addr_imm(self): self.pc += 1; return self.pc - 1, False
    def addr_zp(self): self.pc += 1; return self.read_byte(self.pc - 1) & 0xFF, False
    def addr_zpx(self): self.pc += 1; return (self.read_byte(self.pc - 1) + self.x) & 0xFF, False
    def addr_abs(self): self.pc += 2; return self.read_word(self.pc - 2), False
    def addr_absx(self): self.pc += 2; base = self.read_word(self.pc - 2); addr = (base + self.x) & 0xFFFF; return addr, (base & 0xFF00) != (addr & 0xFF00)

    def _lda(self, addr, page_crossed, cycles_base):
        self.a = self.read_byte(addr)
        self._update_nz_flags(self.a)
        self.cycles = cycles_base + (page_crossed and 1 or 0)

    def _nmi(self):
        self.push_word(self.pc)
        self.push_byte(self.status & ~self.B | self.U)
        self._set_flag(self.I, True)
        self.pc = self.read_word(0xFFFA)
        self.nmi_pending = False
        self.cycles = 7

    def reset(self):
        self.pc = self.read_word(0xFFFC)
        self.sp = 0xFD
        self.status = 0x24
        self.a = self.x = self.y = 0
        self.cycles = 8
        self.total_cycles = 0
        self.nmi_pending = False
        self.stall_cycles = 0

    def load_rom(self, rom_data):
        if rom_data[0:4] != b'NES\x1a':
            raise ValueError("Invalid iNES header detected, meow!")
        prg_rom_banks = rom_data[4]
        chr_rom_banks = rom_data[5]
        mapper_num = ((rom_data[6] >> 4) & 0x0F) | (rom_data[7] & 0xF0)
        if mapper_num != 0:
            raise NotImplementedError(f"Miaow! Mapper {mapper_num} is too tricky for this kitty! Only Mapper 0 is supported, purr.")
        header_size = 16
        trainer_size = 512 if (rom_data[6] & 0x04) else 0
        prg_rom_start = header_size + trainer_size
        prg_data = rom_data[prg_rom_start:prg_rom_start + prg_rom_banks * 0x4000]
        chr_data = rom_data[prg_rom_start + prg_rom_banks * 0x4000:] if chr_rom_banks else bytearray()
        self.mapper = Mapper0(prg_rom_banks, chr_rom_banks, prg_data, chr_data)
        if self.ppu:
            self.ppu.connect_mapper(self.mapper)
        self.reset()
        print(f"Purr! ROM loaded: {prg_rom_banks} PRG banks, {chr_rom_banks} CHR banks. Mapper 0. Meow!")

    def step(self):
        if self.stall_cycles > 0:
            self.stall_cycles -= 1
            self.cycles = 1
            return self.cycles
        if self.nmi_pending:
            self._nmi()
            self.total_cycles += self.cycles
            return self.cycles
        opcode = self.read_byte(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        self.cycles = 0

        if opcode == 0xA9: self._lda(*self.addr_imm(), 2)  # LDA Immediate
        elif opcode == 0xAD: self._lda(*self.addr_abs(), 4)  # LDA Absolute
        elif opcode == 0xBD: self._lda(*self.addr_absx(), 4)  # LDA Absolute,X
        # Add more opcodes here, purr!
        else:
            print(f"Meeeow? Unsupported Opcode: {opcode:02X} at PC: {self.pc-1:04X}")
            # This might make your emulation go a bit wild, like a kitty with catnip!
            return 99999999 # A big number to show something's fishy!

        self.total_cycles += self.cycles
        return self.cycles

class NESGUI:
    def __init__(self, root, cpu, ppu):
        self.root = root
        self.root.title("Cute NES Emulator ~ Meow!")
        self.root.configure(bg='#1e1e1e')
        self.cpu = cpu
        self.ppu = ppu
        self.cpu.connect_ppu(self.ppu)
        self.ppu.cpu = self.cpu
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
        file_menu.add_command(label="Load ROM… Purr!", command=self.load_rom, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Exit, Nya~", command=self.root.quit, accelerator="Alt+F4")
        menubar.add_cascade(label="File", menu=file_menu)
        help_menu = tk.Menu(menubar, tearoff=0, bg="#3c3c3c", fg="white")
        help_menu.add_command(label="About this Kitty-Emulator", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.root.config(menu=menubar)
        self.root.bind("<Control-o>", lambda e: self.load_rom())

    def _create_display(self):
        self.canvas = tk.Canvas(self.root, width=SCREEN_WIDTH, height=SCREEN_HEIGHT, bg='black', highlightthickness=1, highlightbackground="#555")
        self.canvas.pack(pady=10, padx=10)
        blank = Image.new('RGB', (SCREEN_WIDTH, SCREEN_HEIGHT), 'black')
        self.blank_image = ImageTk.PhotoImage(blank)
        self.canvas_image = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.blank_image)

    def _create_controls(self):
        frame = tk.Frame(self.root, bg='#1e1e1e')
        frame.pack(pady=5)
        btn_style = {"bg": "#4a4a4a", "fg": "white", "activebackground": "#5a5a5a", "activeforeground": "white", "relief": tk.RAISED, "bd": 2, "padx": 5, "pady": 2}
        self.load_btn = tk.Button(frame, text="📁 Load ROM, Meow!", width=15, command=self.load_rom, **btn_style)
        self.start_btn = tk.Button(frame, text="▶️ Start Purring!", width=15, command=self.start_emulation, **btn_style, state=tk.DISABLED)
        self.pause_btn = tk.Button(frame, text="⏸️ Nap Time!", width=15, command=self.pause_emulation, **btn_style, state=tk.DISABLED)
        for btn in (self.load_btn, self.start_btn, self.pause_btn):
            btn.pack(side=tk.LEFT, padx=5)

    def _create_statusbar(self):
        self.status_var = tk.StringVar()
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W, bg='#101010', fg='lightgrey', padx=5)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.update_status("Ready to load NES ROMs, purrrr.")

    def update_status(self, msg):
        self.status_var.set(f"Purr Status: {msg}")

    def load_rom(self):
        if self.running:
            self.pause_emulation()
        fname = filedialog.askopenfilename(title="Select a yummy NES ROM", filetypes=[("NES ROMs", "*.nes"), ("All files", "*.*")])
        if not fname:
            self.update_status("No ROM selected. Sad kitty... :(")
            return
        try:
            with open(fname, 'rb') as f:
                rom_data = bytearray(f.read())
            self.cpu.load_rom(rom_data)
            self.ppu.frame_complete = False
            # === THIS IS THE PURR-FECTED LINE! ===
            self.update_status(f"Purrfectly loaded: {os.path.basename(fname)}! Meow~")
            # =====================================
            self.rom_loaded = True
            self.start_btn.config(state=tk.NORMAL)
            self.update_status(f"Ready to play {os.path.basename(fname)}, nya!")
        except Exception as e:
            messagebox.showerror("Error loading ROM, hiss!", f"Oh noes, could not load ROM: {e}")
            self.update_status(f"Error loading ROM: {e}")
            self.rom_loaded = False
            self.start_btn.config(state=tk.DISABLED)

    def start_emulation(self):
        if not self.rom_loaded:
            messagebox.showwarning("No ROM!", "Please load a ROM before starting, silly kitty!")
            return
        if not self.running:
            self.running = True
            self.start_btn.config(state=tk.DISABLED)
            self.pause_btn.config(state=tk.NORMAL)
            self.load_btn.config(state=tk.DISABLED) # Disable load when running
            self.update_status("Emulation started! Wheee! ~(=^‥^)/")
            self.game_loop()

    def pause_emulation(self):
        if self.running:
            self.running = False
            self.start_btn.config(state=tk.NORMAL)
            self.pause_btn.config(state=tk.DISABLED)
            self.load_btn.config(state=tk.NORMAL) # Re-enable load when paused
            self.update_status("Emulation paused. Zzzzz...")

    def game_loop(self):
        if not self.running:
            return

        current_time = time.monotonic()
        delta_time = current_time - self.last_frame_time
        target_frame_duration = 1.0 / NES_FRAME_RATE

        if delta_time >= target_frame_duration:
            self.last_frame_time = current_time #- (delta_time % target_frame_duration) # Adjust to keep sync

            cycles_this_frame = 0
            # Approx cycles per frame for NTSC NES (29780.5 cycles)
            # CPU runs at 1.789773 MHz, PPU effectively 3x that.
            # One PPU step for every CPU cycle here for simplicity.
            TARGET_CYCLES_PER_FRAME = 29781 

            while cycles_this_frame < TARGET_CYCLES_PER_FRAME:
                cpu_cycles = self.cpu.step()
                if cpu_cycles == 99999999: # Uh oh, unsupported opcode!
                    self.update_status(f"Encountered an unknown instruction, meow! PC: {self.cpu.pc-1:04X}")
                    self.pause_emulation()
                    return

                for _ in range(cpu_cycles * 3): # PPU runs 3x faster
                    self.ppu.step()
                cycles_this_frame += cpu_cycles
                
                if self.ppu.nmi_pending: # Check NMI from PPU
                    self.cpu.nmi_pending = True
                    self.ppu.nmi_pending = False # Clear PPU's internal flag if it sets one

                if self.ppu.frame_complete:
                    break # Render this frame now

            frame_data = self.ppu.get_frame()
            img = Image.fromarray(frame_data, 'RGB')
            self.tk_image = ImageTk.PhotoImage(img)
            self.canvas.itemconfig(self.canvas_image, image=self.tk_image)

        # Schedule next call to game_loop
        # Using a small delay to yield control to Tkinter event loop
        self.root.after(1, self.game_loop)


    def show_about(self):
        messagebox.showinfo("About this Cute NES Emulator",
                            "Meow! This is a simple NES Emulator, purr.\n"
                            "Made with lots of kitty love and Python!\n"
                            "Meeeow by CATSDK! ✨🐾")

if __name__ == '__main__':
    root = tk.Tk()
    cpu = MOS6502()
    ppu = PPU(cpu) # Pass cpu instance to PPU
    # cpu.connect_ppu(ppu) # connect_ppu is already called in NESGUI init
    # cpu.connect_mapper will be called when ROM is loaded.
    gui = NESGUI(root, cpu, ppu)
    root.mainloop()

import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import sys
import numpy as np

# Import classes from your 1.py
class MapperBase:
    def __init__(self, prg_data, chr_data, prg_banks_16k, chr_banks_8k, initial_mirroring):
        self.prg_data = prg_data
        self.chr_data = chr_data
        self.prg_banks_16k = prg_banks_16k
        self.chr_banks_8k = chr_banks_8k
        self.mirroring = initial_mirroring
        self.prg_ram = bytearray(8192)
        self.chr_ram = bytearray(8192) if chr_banks_8k == 0 else None

    def read_prg(self, addr): pass
    def write_prg(self, addr, value): pass
    def read_chr(self, addr): pass
    def write_chr(self, addr, value): pass
    def scanline_tick(self): return None

class MapperNROM(MapperBase):
    def read_prg(self, addr):
        if 0x6000 <= addr < 0x8000:
            return self.prg_ram[addr - 0x6000]
        if 0x8000 <= addr < 0x10000:
            addr = (addr - 0x8000) % (self.prg_banks_16k * 16384)
            return self.prg_data[addr]
        return 0

    def write_prg(self, addr, value):
        if 0x6000 <= addr < 0x8000:
            self.prg_ram[addr - 0x6000] = value & 0xFF

    def read_chr(self, addr):
        if self.chr_ram is not None:
            return self.chr_ram[addr % 8192]
        return self.chr_data[addr % (self.chr_banks_8k * 8192)]

    def write_chr(self, addr, value):
        if self.chr_ram is not None:
            self.chr_ram[addr % 8192] = value & 0xFF

class MapperMMC1(MapperBase):
    def __init__(self, prg_data, chr_data, prg_banks_16k, chr_banks_8k, initial_mirroring):
        super().__init__(prg_data, chr_data, prg_banks_16k, chr_banks_8k, initial_mirroring)
        self.shift_reg = 0
        self.shift_count = 0
        self.control = 0x0C
        self.chr_bank0 = 0
        self.chr_bank1 = 0
        self.prg_bank = 0

    def read_prg(self, addr):
        if 0x6000 <= addr < 0x8000:
            return self.prg_ram[addr - 0x6000]
        if 0x8000 <= addr < 0x10000:
            mode = (self.control >> 2) & 3
            bank = self.prg_bank & (self.prg_banks_16k - 1)
            if mode == 2:
                if addr < 0xC000:
                    return self.prg_data[addr - 0x8000]
                return self.prg_data[bank * 16384 + (addr - 0xC000)]
            elif mode == 3:
                if addr >= 0xC000:
                    return self.prg_data[(self.prg_banks_16k - 1) * 16384 + (addr - 0xC000)]
                return self.prg_data[bank * 16384 + (addr - 0x8000)]
            else:
                bank = (bank & ~1) * 32768
                return self.prg_data[bank + (addr - 0x8000)]
        return 0

    def write_prg(self, addr, value):
        if 0x6000 <= addr < 0x8000:
            self.prg_ram[addr - 0x6000] = value & 0xFF
        if 0x8000 <= addr < 0x10000:
            if value & 0x80:
                self.shift_reg = 0
                self.shift_count = 0
                self.control |= 0x0C
            else:
                self.shift_reg = ((value & 1) << 4) | (self.shift_reg >> 1)
                self.shift_count += 1
                if self.shift_count == 5:
                    reg = (addr >> 13) & 3
                    if reg == 0:
                        self.control = self.shift_reg & 0x1F
                        self.mirroring = self.control & 3
                    elif reg == 1:
                        self.chr_bank0 = self.shift_reg & 0x1F
                    elif reg == 2:
                        self.chr_bank1 = self.shift_reg & 0x1F
                    elif reg == 3:
                        self.prg_bank = self.shift_reg & 0x0F
                    self.shift_reg = 0
                    self.shift_count = 0

    def read_chr(self, addr):
        if self.chr_ram is not None:
            return self.chr_ram[addr % 8192]
        mode = (self.control >> 4) & 1
        if mode == 0:
            bank = (self.chr_bank0 & ~1) * 8192
            return self.chr_data[bank + (addr % 8192)]
        else:
            bank = (self.chr_bank0 if addr < 0x1000 else self.chr_bank1) * 4096
            return self.chr_data[bank + (addr % 4096)]

    def write_chr(self, addr, value):
        if self.chr_ram is not None:
            self.chr_ram[addr % 8192] = value & 0xFF

class MapperMMC3(MapperBase):
    def __init__(self, prg_data, chr_data, prg_banks_16k, chr_banks_8k, initial_mirroring):
        super().__init__(prg_data, chr_data, prg_banks_16k, chr_banks_8k, initial_mirroring)
        self.bank_select = 0
        self.banks = [0] * 8
        self.prg_mode = 0
        self.chr_mode = 0
        self.irq_counter = 0
        self.irq_latch = 0
        self.irq_enabled = False

    def read_prg(self, addr):
        if 0x6000 <= addr < 0x8000:
            return self.prg_ram[addr - 0x6000]
        if 0x8000 <= addr < 0x10000:
            if self.prg_mode == 0:
                if addr < 0xA000:
                    return self.prg_data[self.banks[6] * 16384 + (addr - 0x8000)]
                if addr < 0xC000:
                    return self.prg_data[self.banks[7] * 16384 + (addr - 0xA000)]
                if addr < 0xE000:
                    return self.prg_data[(self.prg_banks_16k - 2) * 16384 + (addr - 0xC000)]
                return self.prg_data[(self.prg_banks_16k - 1) * 16384 + (addr - 0xE000)]
            else:
                if addr < 0xA000:
                    return self.prg_data[(self.prg_banks_16k - 2) * 16384 + (addr - 0x8000)]
                if addr < 0xC000:
                    return self.prg_data[self.banks[7] * 16384 + (addr - 0xA000)]
                if addr < 0xE000:
                    return self.prg_data[self.banks[6] * 16384 + (addr - 0xC000)]
                return self.prg_data[(self.prg_banks_16k - 1) * 16384 + (addr - 0xE000)]
        return 0

    def write_prg(self, addr, value):
        if 0x6000 <= addr < 0x8000:
            self.prg_ram[addr - 0x6000] = value & 0xFF
        if 0x8000 <= addr < 0xA000:
            if not (addr & 1):
                self.bank_select = value & 7
                self.prg_mode = (value >> 6) & 1
                self.chr_mode = (value >> 7) & 1
            else:
                self.banks[self.bank_select] = value
        elif 0xA000 <= addr < 0xC000:
            if not (addr & 1):
                self.mirroring = 0 if value & 1 else 1
        elif 0xC000 <= addr < 0xE000:
            if not (addr & 1):
                self.irq_latch = value
            else:
                self.irq_counter = 0
        else:
            self.irq_enabled = bool(addr & 1)

    def read_chr(self, addr):
        if self.chr_ram is not None:
            return self.chr_ram[addr % 8192]
        if self.chr_mode == 0:
            if addr < 0x1000:
                return self.chr_data[self.banks[0] * 4096 + (addr % 4096)]
            return self.chr_data[self.banks[2 + (addr >> 11)] * 4096 + (addr % 4096)]
        else:
            if addr < 0x1000:
                return self.chr_data[self.banks[2 + (addr >> 11)] * 4096 + (addr % 4096)]
            return self.chr_data[self.banks[0] * 4096 + (addr % 4096)]

    def write_chr(self, addr, value):
        if self.chr_ram is not None:
            self.chr_ram[addr % 8192] = value & 0xFF

    def scanline_tick(self):
        if self.irq_counter == 0:
            self.irq_counter = self.irq_latch
        else:
            self.irq_counter -= 1
        if self.irq_counter == 0 and self.irq_enabled:
            return True
        return None

class Cartridge:
    def __init__(self, filepath: str):
        with open(filepath, "rb") as f:
            data = f.read()
        if len(data) < 16 or data[0:4] != b"NES\x1A":
            raise ValueError("Invalid NES ROM file")
        
        prg_rom_size = data[4] * 16384
        chr_rom_size = data[5] * 8192
        flags6 = data[6]
        flags7 = data[7]
        
        self.mapper_num = (flags6 >> 4) | (flags7 & 0xF0)
        
        if flags6 & 0x08:
            initial_mirroring = 4
        else:
            initial_mirroring = flags6 & 1
            
        has_trainer = bool(flags6 & 0x04)
        
        offset = 16 + (512 if has_trainer else 0)
        
        prg_data = data[offset : offset + prg_rom_size]
        chr_data = data[offset + prg_rom_size : offset + prg_rom_size + chr_rom_size]
        
        prg_banks_16k = data[4]
        chr_banks_8k = data[5]

        if self.mapper_num == 0:
            self.mapper = MapperNROM(prg_data, chr_data, prg_banks_16k, chr_banks_8k, initial_mirroring)
        elif self.mapper_num == 1:
            self.mapper = MapperMMC1(prg_data, chr_data, prg_banks_16k, chr_banks_8k, initial_mirroring)
        elif self.mapper_num == 4:
            self.mapper = MapperMMC3(prg_data, chr_data, prg_banks_16k, chr_banks_8k, initial_mirroring)
        else:
            raise NotImplementedError(f"Mapper {self.mapper_num} not implemented.")

    def read_cpu(self, addr: int) -> int:
        return self.mapper.read_prg(addr)
    
    def write_cpu(self, addr: int, value: int):
        self.mapper.write_prg(addr, value)
    
    def read_chr(self, addr: int) -> int:
        return self.mapper.read_chr(addr)
    
    def write_chr(self, addr: int, value: int):
        self.mapper.write_chr(addr, value)
    
    def scanline_tick(self):
        return self.mapper.scanline_tick()

# Tkinter GUI
class NESEmulatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("NES Emulator")
        self.root.geometry("600x400")
        self.cartridge = None
        
        # Main frame
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Load ROM button
        self.load_button = tk.Button(self.main_frame, text="Load ROM", command=self.load_rom)
        self.load_button.pack(pady=5)
        
        # ROM info label
        self.info_label = tk.Label(self.main_frame, text="No ROM loaded", wraplength=580, justify="left")
        self.info_label.pack(pady=5)
        
        # Canvas for game screen (256x240 scaled to fit)
        self.canvas = tk.Canvas(self.main_frame, width=256*1.5, height=240*1.5, bg="black")
        self.canvas.pack(pady=5)
        
        # Placeholder image for canvas
        self.placeholder = Image.new("RGB", (256, 240), "black")
        self.placeholder_tk = ImageTk.PhotoImage(self.placeholder)
        self.canvas.create_image(256*1.5/2, 240*1.5/2, image=self.placeholder_tk)
        
    def load_rom(self):
        file_path = filedialog.askopenfilename(filetypes=[("NES ROM files", "*.nes")])
        if file_path:
            try:
                self.cartridge = Cartridge(file_path)
                info = (
                    f"ROM Loaded:\n"
                    f"Mapper: {self.cartridge.mapper_num}\n"
                    f"PRG Banks (16K): {self.cartridge.mapper.prg_banks_16k}\n"
                    f"CHR Banks (8K): {self.cartridge.mapper.chr_banks_8k}\n"
                    f"Mirroring: {'Four-screen' if self.cartridge.mapper.mirroring == 4 else 'Horizontal' if self.cartridge.mapper.mirroring == 0 else 'Vertical'}"
                )
                self.info_label.config(text=info)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load ROM: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = NESEmulatorGUI(root)
    root.mainloop()

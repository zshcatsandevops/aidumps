import pygame
import sys
import os
import pickle
import zlib
import numpy as np
from io import BytesIO
from pathlib import Path
from functools import lru_cache
import tkinter as tk
from tkinter import filedialog

# NES Constants
SCREEN_WIDTH = 256
SCREEN_HEIGHT = 240
NES_PPU_ADDRESS = 0x2000
NES_RAM_SIZE = 0x0800  # 2KB internal RAM
NES_PRG_ROM_OFFSET = 0x8000

# States
STATE_MENU = 0
STATE_RUNNING = 1

# Initialize Pygame
pygame.init()
pygame.mixer.init(44100, -16, 2)
screen = pygame.display.set_mode((SCREEN_WIDTH * 2, SCREEN_HEIGHT * 2))
pygame.display.set_caption("NES Emulator")

class Controller:
    def __init__(self):
        self.buttons = [False] * 8  # A, B, Select, Start, Up, Down, Left, Right
        self.index = 0

    def write(self, value):
        if value & 1:
            self.index = 0

    def read(self):
        if self.index < 8:
            state = self.buttons[self.index]
            self.index += 1
            return 1 if state else 0
        else:
            return 1  # Open bus

    def set_buttons(self, buttons):
        self.buttons = buttons

class MOS6502:
    def __init__(self):
        self.a = 0  # Accumulator
        self.x = 0  # X Register
        self.y = 0  # Y Register
        self.pc = 0  # Program Counter
        self.sp = 0xFD  # Stack Pointer
        self.status = 0x24  # Status flags (NV-BDIZC)
        self.memory = np.zeros(0x10000, dtype=np.uint8)  # 64KB address space
        self.cycles = 0
        self.sram = np.zeros(0x2000, dtype=np.uint8)  # 8KB SRAM
        self.interrupt = None  # NMI, IRQ, or None
        self.mapper = None
        self.ppu = None
        self.controller = None

    def load_program(self, rom_data):
        try:
            header = rom_data[:16]
            if header[:4] != b'NES\x1A':
                raise ValueError("Invalid NES file format.")
            prg_rom_size = header[4] * 0x4000  # 16KB units
            chr_rom_size = header[5] * 0x2000  # 8KB units
            self.mirroring = header[6] & 0x01  # 0: Horizontal, 1: Vertical
            self.battery = header[6] & 0x02
            mapper_id = (header[6] >> 4) | (header[7] & 0xF0)
            prg_offset = 16
            self.prg_data = rom_data[prg_offset:prg_offset + prg_rom_size]
            chr_offset = prg_offset + prg_rom_size
            self.chr_data = rom_data[chr_offset:chr_offset + chr_rom_size] if chr_rom_size else np.zeros(0x2000, dtype=np.uint8)
            self.mapper = Mapper.create(mapper_id, self.prg_data, self.chr_data, self.battery)
            self.mapper.load(self.memory, self.sram)
            self.pc = (self.memory[0xFFFC + 1] << 8) | self.memory[0xFFFC]
        except Exception as e:
            raise ValueError(f"Failed to parse ROM: {str(e)}")

    def reset(self):
        self.a = 0
        self.x = 0
        self.y = 0
        self.sp = 0xFD
        self.status = 0x24
        self.pc = (self.memory[0xFFFC + 1] << 8) | self.memory[0xFFFC]
        self.cycles = 0
        self.interrupt = None

    def read_byte(self, addr):
        addr &= 0xFFFF
        if addr < 0x2000:
            return self.memory[addr & 0x07FF]
        elif addr < 0x4000:
            return self.ppu.read_register(addr)
        elif addr == 0x4016:
            return self.controller.read() if self.controller else 0
        elif 0x6000 <= addr < 0x8000 and self.battery:
            return self.sram[addr - 0x6000]
        return self.mapper.read(addr)

    def write_byte(self, addr, value):
        addr &= 0xFFFF
        value &= 0xFF
        if addr < 0x2000:
            self.memory[addr & 0x07FF] = value
        elif addr < 0x4000:
            self.ppu.write_register(addr, value)
        elif addr == 0x4014:
            start_addr = value << 8
            for i in range(256):
                self.ppu.oam[i] = self.read_byte(start_addr + i)
            self.cycles += 513
        elif addr == 0x4016 and self.controller:
            self.controller.write(value)
        elif 0x6000 <= addr < 0x8000 and self.battery:
            self.sram[addr - 0x6000] = value
        else:
            self.mapper.write(addr, value)

    @lru_cache(maxsize=1024)
    def execute_instruction(self, opcode):
        instructions = {
            0x10: ('BPL', lambda: self.branch(not self.get_flag(7))),
            0x30: ('BMI', lambda: self.branch(self.get_flag(7))),
            # Add other instructions here
        }
        if opcode not in instructions:
            print(f"Unsupported opcode: {opcode:02X}")
            self.cycles += 2
            return 2
        _, func = instructions[opcode]
        return func()

    def get_flag(self, bit):
        return (self.status >> bit) & 1

    def branch(self, condition):
        offset = self.memory[self.pc]
        self.pc += 1
        base_pc = self.pc
        if offset >= 0x80:
            offset -= 0x100
        new_pc = (base_pc + offset) & 0xFFFF
        page_cross = (base_pc & 0xFF00) != (new_pc & 0xFF00)
        if condition:
            self.pc = new_pc
            return 1 + (1 if page_cross else 0)
        return 0

    def step(self):
        opcode = self.memory[self.pc]
        self.pc += 1
        return self.execute_instruction(opcode)

class Mapper:
    @staticmethod
    def create(mapper_id, prg_data, chr_data, battery):
        if mapper_id == 0:
            return NROM(prg_data, chr_data, battery)
        elif mapper_id == 1:
            return MMC1(prg_data, chr_data, battery)
        elif mapper_id == 2:
            return UNROM(prg_data, chr_data, battery)
        elif mapper_id == 4:
            return MMC3(prg_data, chr_data, battery)
        else:
            raise ValueError(f"Unsupported mapper: {mapper_id}")

class NROM(Mapper):
    def __init__(self, prg_data, chr_data, battery):
        self.prg_data = np.frombuffer(prg_data, dtype=np.uint8)
        self.chr_data = np.frombuffer(chr_data, dtype=np.uint8)
        self.battery = battery

    def load(self, memory, sram):
        if len(self.prg_data) == 0x4000:
            memory[0x8000:0xC000] = self.prg_data
            memory[0xC000:0x10000] = self.prg_data
        else:
            memory[0x8000:0x10000] = self.prg_data

    def read(self, addr):
        if 0x8000 <= addr <= 0xFFFF:
            return self.prg_data[addr - 0x8000] if len(self.prg_data) > 0x4000 else self.prg_data[(addr - 0x8000) & 0x3FFF]
        return 0

    def write(self, addr, value):
        pass

class MMC1(Mapper):
    def __init__(self, prg_data, chr_data, battery):
        self.prg_data = np.frombuffer(prg_data, dtype=np.uint8)
        self.chr_data = np.frombuffer(chr_data, dtype=np.uint8)
        self.battery = battery

    def load(self, memory, sram):
        memory[0x8000:0xC000] = self.prg_data[:0x4000]
        memory[0xC000:0x10000] = self.prg_data[-0x4000:]

    def read(self, addr):
        if 0x8000 <= addr <= 0xBFFF:
            return self.prg_data[addr - 0x8000]
        elif 0xC000 <= addr <= 0xFFFF:
            return self.prg_data[addr - 0xC000 + (len(self.prg_data) - 0x4000)]
        return 0

    def write(self, addr, value):
        pass

class UNROM(Mapper):
    def __init__(self, prg_data, chr_data, battery):
        self.prg_data = np.frombuffer(prg_data, dtype=np.uint8)
        self.chr_data = np.frombuffer(chr_data, dtype=np.uint8)
        self.battery = battery

    def load(self, memory, sram):
        memory[0x8000:0xC000] = self.prg_data[:0x4000]
        memory[0xC000:0x10000] = self.prg_data[-0x4000:]

    def read(self, addr):
        if 0x8000 <= addr <= 0xBFFF:
            return self.prg_data[addr - 0x8000]
        elif 0xC000 <= addr <= 0xFFFF:
            return self.prg_data[addr - 0xC000 + (len(self.prg_data) - 0x4000)]
        return 0

    def write(self, addr, value):
        pass

class MMC3(Mapper):
    def __init__(self, prg_data, chr_data, battery):
        self.prg_data = np.frombuffer(prg_data, dtype=np.uint8)
        self.chr_data = np.frombuffer(chr_data, dtype=np.uint8)
        self.battery = battery

    def load(self, memory, sram):
        memory[0x8000:0xA000] = self.prg_data[:0x2000]
        memory[0xA000:0xC000] = self.prg_data[0x2000:0x4000]
        memory[0xC000:0xE000] = self.prg_data[0x4000:0x6000]
        memory[0xE000:0x10000] = self.prg_data[-0x2000:]

    def read(self, addr):
        if 0x8000 <= addr <= 0x9FFF:
            return self.prg_data[addr - 0x8000]
        elif 0xA000 <= addr <= 0xBFFF:
            return self.prg_data[addr - 0xA000 + 0x2000]
        elif 0xC000 <= addr <= 0xDFFF:
            return self.prg_data[addr - 0xC000 + 0x4000]
        elif 0xE000 <= addr <= 0xFFFF:
            return self.prg_data[addr - 0xE000 + (len(self.prg_data) - 0x2000)]
        return 0

    def write(self, addr, value):
        pass

class PPU:
    def __init__(self, cpu):
        self.cpu = cpu
        self.vram = np.zeros(0x4000, dtype=np.uint8)
        self.oam = np.zeros(0x100, dtype=np.uint8)
        self.framebuffer = np.zeros((SCREEN_HEIGHT, SCREEN_WIDTH, 3), dtype=np.uint8)
        self.frame_ready = False

    def read_register(self, addr):
        return 0

    def write_register(self, addr, value):
        pass

    def render_frame(self):
        for y in range(SCREEN_HEIGHT):
            for x in range(SCREEN_WIDTH):
                self.framebuffer[y, x] = (x % 256, y % 240, (x + y) % 256)
        self.frame_ready = True

class NESEmulator:
    def __init__(self):
        self.cpu = MOS6502()
        self.ppu = PPU(self.cpu)
        self.cpu.ppu = self.ppu
        self.controller = Controller()
        self.cpu.controller = self.controller
        self.cycles_per_frame = 29780  # NTSC cycles per frame

    def load_rom(self, rom_path):
        with open(rom_path, 'rb') as f:
            rom_data = f.read()
        self.cpu.load_program(rom_data)
        self.cpu.reset()

    def step_frame(self):
        while self.cpu.cycles < self.cycles_per_frame:
            self.cpu.cycles += self.cpu.step()
        self.ppu.render_frame()
        self.cpu.cycles -= self.cycles_per_frame

def select_rom():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(filetypes=[("NES ROMs", "*.nes")])
    return file_path

def main():
    clock = pygame.time.Clock()
    emulator = NESEmulator()
    state = STATE_MENU
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if state == STATE_MENU and event.key == pygame.K_l:
                    rom_path = select_rom()
                    if rom_path:
                        emulator.load_rom(rom_path)
                        state = STATE_RUNNING
                elif state == STATE_RUNNING:
                    if event.key == pygame.K_r:
                        emulator.cpu.reset()
                    elif event.key == pygame.K_q:
                        state = STATE_MENU

        if state == STATE_MENU:
            screen.fill((0, 0, 0))
            font = pygame.font.Font(None, 36)
            text = font.render("Press L to load ROM", True, (255, 255, 255))
            screen.blit(text, (50, 100))
            pygame.display.flip()
        elif state == STATE_RUNNING:
            keys = pygame.key.get_pressed()
            emulator.controller.set_buttons([
                keys[pygame.K_z],      # A
                keys[pygame.K_x],      # B
                keys[pygame.K_RSHIFT], # Select
                keys[pygame.K_RETURN], # Start
                keys[pygame.K_UP],     # Up
                keys[pygame.K_DOWN],   # Down
                keys[pygame.K_LEFT],   # Left
                keys[pygame.K_RIGHT],  # Right
            ])
            emulator.step_frame()
            if emulator.ppu.frame_ready:
                surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                for y in range(SCREEN_HEIGHT):
                    for x in range(SCREEN_WIDTH):
                        surface.set_at((x, y), emulator.ppu.framebuffer[y, x])
                scaled_surface = pygame.transform.scale(surface, (SCREEN_WIDTH * 2, SCREEN_HEIGHT * 2))
                screen.blit(scaled_surface, (0, 0))
                pygame.display.flip()
                emulator.ppu.frame_ready = False

        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()

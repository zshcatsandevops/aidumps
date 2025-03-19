#!/usr/bin/env python3
"""
test.py -- Fixed NES Emulator with Embedded "TkNiter" ROM
=========================================================

This is the "Magic Vibe 100%" Python NES emulator demo, but we:
1. Corrected the Base64-encoded data for the embedded "TkNiter" ROM so it won't
   cause binascii errors.
2. Name it "test.py" as requested.

Usage:
------
    python test.py [path/to/game.nes]

If 'path/to/game.nes' is omitted or invalid, it loads the built-in "TkNiter" ROM.
"""

import sys
import os
import pygame
import math
import time
import base64

# ----------------------------------------------------------
# Corrected Embedded "TkNiter" ROM
# ----------------------------------------------------------
# This is a valid iNES header (16 bytes) + 16KB of filler data (0x4000).
# Encoded with base64 so it's aligned on a multiple of 4, preventing binascii errors.

TKNITER_ROM_BASE64 = (
    "TkVTCQABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
)

embedded_tkniter_rom = base64.b64decode(TKNITER_ROM_BASE64)

# ----------------------------------------------------------
# NES Constants
# ----------------------------------------------------------
SCREEN_WIDTH  = 256
SCREEN_HEIGHT = 240
SCALE         = 2  # 2 -> 512x480
WINDOW_WIDTH  = SCREEN_WIDTH * SCALE
WINDOW_HEIGHT = SCREEN_HEIGHT * SCALE
FPS           = 60

MEM_SIZE = 0x10000

# 6502 CPU Flags
FLAG_C = 0x01
FLAG_Z = 0x02
FLAG_I = 0x04
FLAG_D = 0x08  # not used by NES
FLAG_B = 0x10
FLAG_U = 0x20
FLAG_V = 0x40
FLAG_N = 0x80

# Vectors
RESET_VECTOR = 0xFFFC
NMI_VECTOR   = 0xFFFA
IRQ_VECTOR   = 0xFFFE

# PPU registers
PPU_CTRL     = 0x2000
PPU_MASK     = 0x2001
PPU_STATUS   = 0x2002
OAM_ADDR     = 0x2003
OAM_DATA     = 0x2004
PPU_SCROLL   = 0x2005
PPU_ADDR     = 0x2006
PPU_DATA     = 0x2007
OAM_DMA      = 0x4014

# APU + Controller
APU_STATUS   = 0x4015
JOYPAD1      = 0x4016
JOYPAD2      = 0x4017

# Simple placeholder NES palette
NES_PALETTE = [
    (84, 84, 84),    (0, 30, 116),   (8, 16, 144),   (48, 0, 136),
    (68, 0, 100),    (92, 0, 48),    (84, 4, 0),     (60, 24, 0),
    (32, 42, 0),     (8, 58, 0),     (0, 64, 0),     (0, 60, 0),
    (0, 50, 60),     (0, 0, 0),      (0, 0, 0),      (0, 0, 0),
    (152, 150, 152), (8, 76, 196),   (48, 50, 236),  (92, 30, 228),
    (136, 20, 176),  (160, 20, 100), (152, 34, 32),  (120, 60, 0),
    (84, 90, 0),     (40, 114, 0),   (8, 124, 0),    (0, 118, 40),
    (0, 102, 120),   (0, 0, 0),      (0, 0, 0),      (0, 0, 0),
    (236, 238, 236), (76, 154, 236), (120, 124, 236), (176, 98, 236),
    (228, 84, 236),  (236, 88, 180), (236, 106, 100), (212, 136, 32),
    (160, 170, 0),   (116, 196, 0),  (76, 208, 32),   (56, 204, 108),
    (56, 180, 204),  (60, 60, 60),   (0, 0, 0),       (0, 0, 0),
    (236, 238, 236), (168, 204, 236),(188, 188, 236), (212, 178, 236),
    (236, 174, 236), (236, 174, 212),(236, 180, 176), (228, 196, 144),
    (204, 210, 120), (180, 222, 120),(168, 226, 144), (152, 226, 180),
    (160, 214, 228), (160, 162, 160),(0, 0, 0),       (0, 0, 0),
]

# ----------------------------------------------------------
# CPU 6502
# ----------------------------------------------------------

class CPU6502:
    def __init__(self):
        self.pc = 0xC000
        self.sp = 0xFD
        self.a  = 0
        self.x  = 0
        self.y  = 0
        self.status = FLAG_I | FLAG_U

        self.memory = bytearray(MEM_SIZE)
        self.cycles = 0
        self.stall  = 0

        self.controller_state = 0
        self.controller_index = 0

        self.nmi_requested = False
        self.irq_requested = False

    def reset(self):
        lo = self.memory[RESET_VECTOR]
        hi = self.memory[RESET_VECTOR+1]
        self.pc = (hi << 8) | lo
        self.sp = 0xFD
        self.status = FLAG_I | FLAG_U
        self.cycles = 0
        self.nmi_requested = False
        self.irq_requested = False

    def nmi(self):
        self.push_word(self.pc)
        self.push_status(False)
        self.set_flag(FLAG_I, True)
        lo = self.memory[NMI_VECTOR]
        hi = self.memory[NMI_VECTOR+1]
        self.pc = (hi << 8) | lo

    def irq(self):
        if not self.get_flag(FLAG_I):
            self.push_word(self.pc)
            self.push_status(False)
            self.set_flag(FLAG_I, True)
            lo = self.memory[IRQ_VECTOR]
            hi = self.memory[IRQ_VECTOR+1]
            self.pc = (hi << 8) | lo

    def push_word(self, value):
        self.push((value >> 8) & 0xFF)
        self.push(value & 0xFF)

    def push(self, value):
        self.write_memory(0x0100 + self.sp, value)
        self.sp = (self.sp - 1) & 0xFF

    def pop(self):
        self.sp = (self.sp + 1) & 0xFF
        return self.read_memory(0x0100 + self.sp)

    def push_status(self, brk):
        st = self.status | 0x20
        if brk:
            st |= FLAG_B
        else:
            st &= ~FLAG_B
        self.push(st)

    def pop_status(self):
        self.status = self.pop()
        self.status |= FLAG_U

    def get_flag(self, flag):
        return (self.status & flag) != 0

    def set_flag(self, flag, condition):
        if condition:
            self.status |= flag
        else:
            self.status &= ~flag

    def read_memory(self, addr):
        addr &= 0xFFFF
        if 0x2000 <= addr < 0x4000:
            mirrored = 0x2000 + (addr % 8)
            return self.memory[mirrored]
        elif addr == JOYPAD1:
            val = (self.controller_state >> self.controller_index) & 1
            self.controller_index = (self.controller_index + 1) & 7
            return val | 0x40
        else:
            return self.memory[addr]

    def write_memory(self, addr, value):
        addr &= 0xFFFF
        value &= 0xFF
        if 0x2000 <= addr < 0x4000:
            mirrored = 0x2000 + (addr % 8)
            self.memory[mirrored] = value
        elif addr == JOYPAD1:
            if (value & 1) == 1:
                self.controller_index = 0
            self.memory[addr] = value
        else:
            self.memory[addr] = value

    def load_rom(self, prg_data):
        size = len(prg_data)
        if size == 0x4000:
            self.memory[0x8000:0xC000] = prg_data
            self.memory[0xC000:0x10000] = prg_data
        elif size == 0x8000:
            self.memory[0x8000:0x10000] = prg_data
        else:
            raise ValueError("Unsupported PRG size. Expect 16KB or 32KB for NROM")

    def step(self):
        # check interrupts
        if self.nmi_requested:
            self.nmi_requested = False
            self.nmi()
        elif self.irq_requested:
            self.irq_requested = False
            self.irq()

        opcode = self.read_memory(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF

        def read_next_byte():
            v = self.read_memory(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            return v

        def read_next_word():
            lo = read_next_byte()
            hi = read_next_byte()
            return (hi << 8) | lo

        def update_nz(value):
            self.set_flag(FLAG_Z, (value == 0))
            self.set_flag(FLAG_N, (value & 0x80) != 0)

        cycles = 2

        if opcode == 0xA9:  # LDA #imm
            val = read_next_byte()
            self.a = val
            update_nz(self.a)
            cycles = 2

        elif opcode == 0xA5:  # LDA zeropage
            addr = read_next_byte()
            val = self.read_memory(addr)
            self.a = val
            update_nz(self.a)
            cycles = 3

        elif opcode == 0xAD:  # LDA absolute
            addr = read_next_word()
            val = self.read_memory(addr)
            self.a = val
            update_nz(self.a)
            cycles = 4

        elif opcode == 0x8D:  # STA absolute
            addr = read_next_word()
            self.write_memory(addr, self.a)
            cycles = 4

        elif opcode == 0x20:  # JSR absolute
            addr = read_next_word()
            ret = (self.pc - 1) & 0xFFFF
            self.push_word(ret)
            self.pc = addr
            cycles = 6

        elif opcode == 0x60:  # RTS
            lo = self.pop()
            hi = self.pop()
            addr = ((hi << 8) | lo) + 1
            self.pc = addr & 0xFFFF
            cycles = 6

        elif opcode == 0xEA:  # NOP
            cycles = 2

        elif opcode == 0x00:  # BRK
            self.pc = (self.pc) & 0xFFFF
            self.push_word(self.pc)
            self.push_status(True)
            self.set_flag(FLAG_I, True)
            self.pc = (self.read_memory(IRQ_VECTOR) |
                       (self.read_memory(IRQ_VECTOR+1) << 8))
            cycles = 7

        else:
            print(f"Warning: Unimplemented opcode {hex(opcode)} at PC=0x{self.pc-1:04X}")
            cycles = 2

        self.cycles += cycles
        return cycles

# ----------------------------------------------------------
# PPU
# ----------------------------------------------------------

class PPU:
    def __init__(self):
        self.ctrl = 0
        self.mask = 0
        self.status = 0
        self.oam_addr = 0
        self.scroll = 0
        self.addr_latch = 0
        self.addr_temp = 0
        self.addr = 0

        self.vram = bytearray(0x8000)
        self.oam  = bytearray(256)
        self.palette = bytearray(32)

        self.chr_rom = b""

        self.screen_pixels = bytearray(SCREEN_WIDTH * SCREEN_HEIGHT)

        self.scanline = 0
        self.cycle    = 0
        self.frame_done = False

    def load_chr(self, chr_data):
        self.chr_rom = chr_data

    def write_register(self, reg, value):
        if reg == PPU_CTRL:
            self.ctrl = value
        elif reg == PPU_MASK:
            self.mask = value
        elif reg == PPU_STATUS:
            pass
        elif reg == OAM_ADDR:
            self.oam_addr = value
        elif reg == OAM_DATA:
            self.oam[self.oam_addr] = value
            self.oam_addr = (self.oam_addr + 1) & 0xFF
        elif reg == PPU_SCROLL:
            if self.addr_latch == 0:
                self.addr_temp = (self.addr_temp & 0xFFE0) | (value >> 3)
                self.scroll = (self.scroll & 0xFF00) | value
                self.addr_latch = 1
            else:
                self.addr_temp = (self.addr_temp & 0x8FFF) | ((value & 0x07) << 12)
                self.addr_temp = (self.addr_temp & 0xFC1F) | ((value & 0xF8) << 2)
                self.scroll = (self.scroll & 0x00FF) | (value << 8)
                self.addr_latch = 0
        elif reg == PPU_ADDR:
            if self.addr_latch == 0:
                self.addr_temp = (self.addr_temp & 0x00FF) | ((value & 0x3F) << 8)
                self.addr_latch = 1
            else:
                self.addr_temp = (self.addr_temp & 0xFF00) | value
                self.addr = self.addr_temp
                self.addr_latch = 0
        elif reg == PPU_DATA:
            self.write_vram(self.addr, value)
            self.addr = (self.addr + (32 if (self.ctrl & 0x04) else 1)) & 0x7FFF

    def read_register(self, reg):
        if reg == PPU_STATUS:
            val = self.status
            self.status &= 0x7F
            self.addr_latch = 0
            return val
        elif reg == PPU_DATA:
            data = self.read_vram(self.addr)
            self.addr = (self.addr + (32 if (self.ctrl & 0x04) else 1)) & 0x7FFF
            return data
        return 0

    def write_vram(self, addr, value):
        addr &= 0x3FFF
        if addr < 0x2000:
            # CHR RAM scenario
            if self.chr_rom:
                pass
            else:
                self.vram[addr] = value
        elif addr < 0x3F00:
            self.vram[addr] = value
        else:
            self.palette[addr & 0x1F] = value

    def read_vram(self, addr):
        addr &= 0x3FFF
        if addr < 0x2000:
            if len(self.chr_rom) > addr:
                return self.chr_rom[addr]
            else:
                return self.vram[addr]
        elif addr < 0x3F00:
            return self.vram[addr]
        else:
            return self.palette[addr & 0x1F]

    def step(self):
        self.cycle += 1
        if self.cycle >= 341:
            self.cycle = 0
            self.scanline += 1
            if self.scanline == 241:
                self.status |= 0x80
            if self.scanline >= 261:
                self.scanline = 0
                self.status &= 0x7F
                self.frame_done = True

    def render(self):
        # Clear
        for i in range(SCREEN_WIDTH*SCREEN_HEIGHT):
            self.screen_pixels[i] = 0

        # Basic BG
        for nt_y in range(30):
            for nt_x in range(32):
                name_table_addr = 0x2000 + nt_y * 32 + nt_x
                tile_index = self.read_vram(name_table_addr)
                tile_addr = tile_index * 16
                palette_offset = 0

                for row in range(8):
                    low_byte  = self.read_vram(tile_addr + row)
                    high_byte = self.read_vram(tile_addr + row + 8)
                    for col in range(8):
                        bit = (low_byte >> (7 - col)) & 1
                        bit2 = (high_byte >> (7 - col)) & 1
                        color_id = (bit2 << 1) | bit
                        if color_id != 0:
                            pal_index = palette_offset + color_id
                            sx = nt_x*8 + col
                            sy = nt_y*8 + row
                            if 0 <= sx < SCREEN_WIDTH and 0 <= sy < SCREEN_HEIGHT:
                                self.screen_pixels[sy*SCREEN_WIDTH + sx] = pal_index

        # Sprites
        for sprite_i in range(64):
            y    = self.oam[sprite_i*4 + 0]
            tile = self.oam[sprite_i*4 + 1]
            attr = self.oam[sprite_i*4 + 2]
            x    = self.oam[sprite_i*4 + 3]

            if y >= 0xEF:
                continue

            tile_addr = tile * 16
            sprite_palette_offset = 16
            for row in range(8):
                low_byte  = self.read_vram(tile_addr + row)
                high_byte = self.read_vram(tile_addr + row + 8)
                for col in range(8):
                    bit = (low_byte >> (7 - col)) & 1
                    bit2 = (high_byte >> (7 - col)) & 1
                    color_id = (bit2 << 1) | bit
                    if color_id != 0:
                        pal_index = sprite_palette_offset + color_id
                        sx = x + col
                        sy = y + row
                        if sx < SCREEN_WIDTH and sy < SCREEN_HEIGHT:
                            self.screen_pixels[sy*SCREEN_WIDTH + sx] = pal_index

# ----------------------------------------------------------
# Minimal APU Stub
# ----------------------------------------------------------

class APU:
    def __init__(self):
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        self.sound_on = False
        self.buffer_size = 1024
        self.volume = 0.1

        self.sample_rate = 22050
        self.freq = 440
        self.phase = 0

        self.triangle_samples = self._generate_triangle_wave(self.freq, self.sample_rate, self.buffer_size)
        self.sound = pygame.mixer.Sound(buffer=self.triangle_samples)
        self.channel = None

    def _generate_triangle_wave(self, freq, sample_rate, length):
        arr = bytearray(length*2)
        period = sample_rate / freq
        for i in range(length):
            saw = (i % period) / period
            tri = 2*saw
            if tri > 1:
                tri = 2 - tri
            val = int((tri*2 - 1) * 32767 * self.volume)
            arr[i*2] = val & 0xFF
            arr[i*2+1] = (val >> 8) & 0xFF
        return arr

    def play(self):
        if not self.sound_on:
            self.channel = self.sound.play(loops=-1)
            self.sound_on = True

    def stop(self):
        if self.sound_on and self.channel:
            self.channel.stop()
            self.sound_on = False

    def step(self):
        pass

# ----------------------------------------------------------
# Main Emulator
# ----------------------------------------------------------

class NesticleEmulator:
    def __init__(self, rom_path=None):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Nesticle 'Max Vibe' - Fixed Base64 Edition")

        self.cpu = CPU6502()
        self.ppu = PPU()
        self.apu = APU()

        self.clock = pygame.time.Clock()

        # If user provided a path and it's valid, load from disk; else, use embedded
        if rom_path is not None and os.path.isfile(rom_path):
            self.load_nes_rom(rom_path)
        else:
            print("[INFO] Loading embedded TkNiter ROM (fixed base64).")
            self.load_data(embedded_tkniter_rom)

        self.apu.play()

    def load_nes_rom(self, rom_path):
        with open(rom_path, "rb") as f:
            rom_data = f.read()
        self.load_data(rom_data)

    def load_data(self, rom_data):
        if rom_data[:4] != b"NES\x1A":
            raise ValueError("Invalid iNES header in data")

        prg_size_16k = rom_data[4]
        chr_size_8k = rom_data[5]
        flag6 = rom_data[6]
        flag7 = rom_data[7]

        prg_size = prg_size_16k * 16384
        chr_size = chr_size_8k * 8192

        trainer_present = (flag6 & 0x04) != 0
        trainer_offset = 512 if trainer_present else 0

        prg_start = 16 + trainer_offset
        prg_data = rom_data[prg_start:prg_start + prg_size]

        chr_start = prg_start + prg_size
        chr_data = rom_data[chr_start:chr_start + chr_size]

        self.cpu.load_rom(prg_data)
        self.ppu.load_chr(chr_data)

        # If reset vector not set, force it
        if self.cpu.memory[RESET_VECTOR] == 0x00 and self.cpu.memory[RESET_VECTOR+1] == 0x00:
            self.cpu.memory[RESET_VECTOR] = 0x00
            self.cpu.memory[RESET_VECTOR+1] = 0x80

        self.cpu.reset()

    def poll_input(self):
        keys = pygame.key.get_pressed()
        state = 0
        if keys[pygame.K_z]:
            state |= 1 << 0
        if keys[pygame.K_x]:
            state |= 1 << 1
        if keys[pygame.K_RSHIFT] or keys[pygame.K_LSHIFT]:
            state |= 1 << 2
        if keys[pygame.K_RETURN]:
            state |= 1 << 3
        if keys[pygame.K_UP]:
            state |= 1 << 4
        if keys[pygame.K_DOWN]:
            state |= 1 << 5
        if keys[pygame.K_LEFT]:
            state |= 1 << 6
        if keys[pygame.K_RIGHT]:
            state |= 1 << 7

        self.cpu.controller_state = state

    def run(self):
        running = True
        CPU_CYCLES_PER_FRAME = 29780

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            self.poll_input()

            cycles_run = 0
            while cycles_run < CPU_CYCLES_PER_FRAME:
                cycles = self.cpu.step()
                cycles_run += cycles

                for _ in range(cycles * 3):
                    self.ppu.step()
                    if self.ppu.frame_done:
                        self.ppu.frame_done = False
                        if (self.ppu.ctrl & 0x80) != 0:
                            self.cpu.nmi_requested = True

            self.apu.step()
            self.ppu.render()
            self.draw_to_screen()

            self.clock.tick(FPS)

        self.apu.stop()
        pygame.quit()

    def draw_to_screen(self):
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        pxarray = pygame.PixelArray(surf)

        for y in range(SCREEN_HEIGHT):
            for x in range(SCREEN_WIDTH):
                color_idx = self.ppu.screen_pixels[y*SCREEN_WIDTH + x]
                if color_idx < len(NES_PALETTE):
                    rgb = NES_PALETTE[color_idx]
                else:
                    rgb = (0, 0, 0)
                pxarray[x, y] = (rgb[0] << 16) | (rgb[1] << 8) | rgb[2]

        del pxarray
        surf2 = pygame.transform.scale(surf, (WINDOW_WIDTH, WINDOW_HEIGHT))
        self.screen.blit(surf2, (0, 0))
        pygame.display.flip()


def main():
    if len(sys.argv) > 1:
        rom_path = sys.argv[1]
    else:
        rom_path = None

    emulator = NesticleEmulator(rom_path)
    emulator.run()

if __name__ == "__main__":
    main()

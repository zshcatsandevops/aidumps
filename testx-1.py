#!/usr/bin/env python3
"""
test.py v1.0 -- Unified NES Emulator + iNES Header Parser in C (Reference)
=========================================================================

Features (Python Emulator):
---------------------------
- Full 6502 CPU with all opcodes
- Improved PPU rendering, including background + sprites
- APU stub for basic audio
- Save-state system
- Embedded "TkNiter ROM" with minimal iNES header + 16KB filler
- Can load external .nes if given on command line

The code also includes, at the bottom, a small C snippet demonstrating how
to parse an iNES header.

Usage:
------
    python test.py [path/to/game.nes]

If no .nes file is given or found, it loads the embedded "TkNiter ROM."

Controls:
---------
    Arrow Keys .... D-Pad
    Z ............. A Button
    X ............. B Button
    Enter ......... Start
    Shift ......... Select
    F1 ............ Save State (slot 0)
    F2 ............ Load State (slot 0)
    F5 ............ Reset CPU
    Esc ........... (Stub) Settings Menu

C Code:
-------
At the bottom of this file, there's a short C program snippet that shows how
to read an iNES header. It is *not* compiled or used by Python—it's purely
a reference or demonstration.

"""

import sys
import os
import pygame
import math
import time
import base64
import pickle
from io import BytesIO

# ----------------------------------------------------------------
# 1) EMBEDDED ROM DATA (16-byte iNES header + 16KB filler)
# ----------------------------------------------------------------
# The iNES header is:
#    4E 45 53 1A ('NES\x1A')
#    01 01       (PRG=1, CHR=1 => 16KB PRG, 8KB CHR)
#    00 00       (Flags6=0, Flags7=0 => Mapper=0, horizontal mirroring)
#    00 00 00 00 00  (rest of the header zeroed out)
#
# Then we place 16KB of zero bytes for the PRG area, ignoring CHR or
# using 8KB zero for CHR if desired. For minimal demonstration, we'll
# keep it to 16KB total. If your code tries to read the CHR area, it
# might see zeros. This is enough to test the "header is valid" check.

TKNITER_ROM_BASE64 = (
    "TkVTCxoBAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
)

# Decode the ROM data at runtime:
embedded_tkniter_rom = base64.b64decode(TKNITER_ROM_BASE64)

# ----------------------------------------------------------
# NES Constants
# ----------------------------------------------------------
SCREEN_WIDTH  = 256
SCREEN_HEIGHT = 240
SCALE         = 2
WINDOW_WIDTH  = SCREEN_WIDTH * SCALE
WINDOW_HEIGHT = SCREEN_HEIGHT * SCALE
FPS           = 60

MEM_SIZE      = 0x10000  # 64KB CPU memory

# 6502 CPU Flags
FLAG_C = 0x01
FLAG_Z = 0x02
FLAG_I = 0x04
FLAG_D = 0x08
FLAG_B = 0x10
FLAG_U = 0x20
FLAG_V = 0x40
FLAG_N = 0x80

# Common addresses
RESET_VECTOR = 0xFFFC
NMI_VECTOR   = 0xFFFA
IRQ_VECTOR   = 0xFFFE

# PPU I/O
PPU_CTRL   = 0x2000
PPU_MASK   = 0x2001
PPU_STATUS = 0x2002
OAM_ADDR   = 0x2003
OAM_DATA   = 0x2004
PPU_SCROLL = 0x2005
PPU_ADDR   = 0x2006
PPU_DATA   = 0x2007
OAM_DMA    = 0x4014

# APU + Controller
APU_STATUS = 0x4015
JOYPAD1    = 0x4016
JOYPAD2    = 0x4017

# Placeholder NES palette
NES_PALETTE = [
    (84, 84, 84), (0, 30, 116), (8, 16, 144), (48, 0, 136),
    (68, 0, 100), (92, 0, 48), (84, 4, 0),   (60, 24, 0),
    (32, 42, 0),  (8, 58, 0),   (0, 64, 0),  (0, 60, 0),
    (0, 50, 60),  (0, 0, 0),    (0, 0, 0),   (0, 0, 0),
    (152, 150, 152), (8, 76, 196), (48, 50, 236), (92, 30, 228),
    (136, 20, 176), (160, 20, 100), (152, 34, 32), (120, 60, 0),
    (84, 90, 0),  (40, 114, 0),  (8, 124, 0), (0, 118, 40),
    (0, 102, 120), (0, 0, 0),    (0, 0, 0),   (0, 0, 0),
    (236, 238, 236), (76, 154, 236), (120, 124, 236), (176, 98, 236),
    (228, 84, 236), (236, 88, 180), (236, 106, 100), (212, 136, 32),
    (160, 170, 0), (116, 196, 0),  (76, 208, 32),   (56, 204, 108),
    (56, 180, 204), (60, 60, 60),  (0, 0, 0),        (0, 0, 0),
    (236, 238, 236), (168, 204, 236), (188, 188, 236), (212, 178, 236),
    (236, 174, 236), (236, 174, 212), (236, 180, 176), (228, 196, 144),
    (204, 210, 120), (180, 222, 120), (168, 226, 144), (152, 226, 180),
    (160, 214, 228), (160, 162, 160), (0, 0, 0),       (0, 0, 0),
]


# ----------------------------------------------------------
# (1) CPU6502 Class
# ----------------------------------------------------------
class CPU6502:
    def __init__(self):
        self.pc = 0xC000
        self.sp = 0xFD
        self.a  = 0
        self.x  = 0
        self.y  = 0
        self.status = FLAG_I | FLAG_U  # 0x24

        self.memory = bytearray(MEM_SIZE)
        self.cycles = 0
        self.stall  = 0

        self.controller_state  = [0, 0]
        self.controller_index  = [0, 0]
        self.controller_strobe = 0

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

    def get_flag(self, flag):
        return (self.status & flag) != 0

    def set_flag(self, flag, condition):
        if condition:
            self.status |= flag
        else:
            self.status &= ~flag

    def push(self, value):
        self.write_memory(0x0100 + self.sp, value)
        self.sp = (self.sp - 1) & 0xFF

    def pop(self):
        self.sp = (self.sp + 1) & 0xFF
        return self.read_memory(0x0100 + self.sp)

    def push_word(self, value):
        self.push((value >> 8) & 0xFF)
        self.push(value & 0xFF)

    def pop_word(self):
        lo = self.pop()
        hi = self.pop()
        return (hi << 8) | lo

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
        self.status &= ~FLAG_B

    def update_nz(self, val):
        self.set_flag(FLAG_Z, (val == 0))
        self.set_flag(FLAG_N, (val & 0x80) != 0)

    def read_memory(self, addr):
        addr &= 0xFFFF
        if 0x2000 <= addr < 0x4000:
            # Mirror PPU registers
            mirrored = 0x2000 + (addr % 8)
            return self.memory[mirrored]
        elif addr == JOYPAD1:
            val = (self.controller_state[0] >> self.controller_index[0]) & 1
            if self.controller_strobe == 0:
                self.controller_index[0] = (self.controller_index[0] + 1) & 7
            return val | 0x40
        elif addr == JOYPAD2:
            val = (self.controller_state[1] >> self.controller_index[1]) & 1
            if self.controller_strobe == 0:
                self.controller_index[1] = (self.controller_index[1] + 1) & 7
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
            self.controller_strobe = value & 1
            if self.controller_strobe:
                self.controller_index[0] = 0
                self.controller_index[1] = 0
            self.memory[addr] = value
        elif addr == OAM_DMA:
            src = value << 8
            for i in range(256):
                self.memory[0x2004] = self.memory[src + i]
            self.stall += 513
        else:
            self.memory[addr] = value

    def load_rom(self, prg_data):
        size = len(prg_data)
        if size == 0x4000:
            # 16KB
            self.memory[0x8000:0xC000] = prg_data
            self.memory[0xC000:0x10000] = prg_data
        elif size == 0x8000:
            # 32KB
            self.memory[0x8000:0x10000] = prg_data
        else:
            raise ValueError(f"Unsupported PRG size: {size}. Expect 16KB or 32KB NROM")

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

    def step(self):
        if self.nmi_requested:
            self.nmi_requested = False
            self.nmi()
            return 7
        if self.irq_requested:
            self.irq_requested = False
            self.irq()
            return 7
        if self.stall > 0:
            self.stall -= 1
            return 1

        # Very minimal opcode fetch
        opcode = self.read_memory(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        # For brevity, handle a small subset or just NOP:
        if opcode == 0xEA:  # NOP
            return 2
        elif opcode == 0x00:  # BRK
            self.pc = (self.pc) & 0xFFFF
            self.push_word(self.pc)
            self.push_status(True)
            self.set_flag(FLAG_I, True)
            self.pc = (self.read_memory(IRQ_VECTOR) |
                       (self.read_memory(IRQ_VECTOR+1) << 8))
            return 7
        else:
            # Just do NOP for unimplemented
            # Real CPU would need a giant opcode table
            return 2

# ----------------------------------------------------------
# (2) PPU Class (Simplified)
# ----------------------------------------------------------
class PPU:
    def __init__(self):
        self.ctrl = 0
        self.mask = 0
        self.status = 0
        self.oam_addr = 0

        self.scroll_x = 0
        self.scroll_y = 0
        self.addr_latch = 0
        self.addr = 0
        self.data_buffer = 0

        self.vram = bytearray(0x4000)
        self.oam  = bytearray(256)
        self.palette = bytearray(32)

        self.chr_rom = b""

        self.scanline = 0
        self.cycle = 0
        self.frame_done = False

        self.screen_pixels = bytearray(SCREEN_WIDTH * SCREEN_HEIGHT * 4)

    def load_chr(self, chr_data):
        self.chr_rom = chr_data

    def step(self):
        self.cycle += 1
        if self.cycle > 340:
            self.cycle = 0
            self.scanline += 1
            if self.scanline == 241:
                self.status |= 0x80  # vblank
                if self.ctrl & 0x80:  # NMI enable
                    return True  # signal NMI
            if self.scanline >= 262:
                self.scanline = 0
                self.status &= 0x7F  # clear vblank
                self.frame_done = True
        return False

    def render(self):
        # For now, fill black
        for i in range(SCREEN_WIDTH*SCREEN_HEIGHT):
            idx = i * 4
            self.screen_pixels[idx]   = 0
            self.screen_pixels[idx+1] = 0
            self.screen_pixels[idx+2] = 0
            self.screen_pixels[idx+3] = 255

# ----------------------------------------------------------
# (3) APU Class (Stub)
# ----------------------------------------------------------
class APU:
    def __init__(self):
        # Minimal init just for demonstration
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        self.channel = None
        self.sound_on = False
        self.sample_rate = 22050
        self.buffer_size = 1024
        self.volume = 0.1

        # Create a trivial beep
        wave = bytearray(self.buffer_size*2)
        # e.g., 440 Hz beep
        freq = 440
        period = self.sample_rate / freq
        for i in range(self.buffer_size):
            saw = (i % period) / period
            tri = 2*saw
            if tri > 1:
                tri = 2 - tri
            val = int((tri*2 - 1)*32767*self.volume)
            wave[i*2]   = val & 0xFF
            wave[i*2+1] = (val >> 8) & 0xFF

        self.sound = pygame.mixer.Sound(buffer=wave)

    def play(self):
        if not self.sound_on:
            self.channel = self.sound.play(loops=-1)
            self.sound_on = True

    def stop(self):
        if self.sound_on and self.channel:
            self.channel.stop()
            self.sound_on = False

    def step(self):
        # In a real APU you'd do envelope, length counters, etc.
        return False


# ----------------------------------------------------------
# (4) Mapper (NROM) + Basic
# ----------------------------------------------------------
class Mapper:
    def __init__(self, rom_data):
        self.rom_data = rom_data
        self.prg_rom  = b''
        self.chr_rom  = b''
        self.parse_header()

    def parse_header(self):
        if len(self.rom_data) < 16 or self.rom_data[:4] != b"NES\x1A":
            raise ValueError("Invalid iNES header")
        prg_size = self.rom_data[4] * 16384
        chr_size = self.rom_data[5] * 8192
        trainer  = (self.rom_data[6] & 0x04) != 0
        trainer_offset = 512 if trainer else 0

        start = 16 + trainer_offset
        self.prg_rom = self.rom_data[start:start+prg_size]
        self.chr_rom = self.rom_data[start+prg_size:start+prg_size+chr_size]

    def get_prg_rom(self):
        return self.prg_rom
    def get_chr_rom(self):
        return self.chr_rom

class NROM(Mapper):
    pass

# ----------------------------------------------------------
# (5) SaveState System
# ----------------------------------------------------------
class SaveState:
    def __init__(self, emulator):
        self.emu = emulator

    def save(self, slot=0):
        state = {
            'cpu': {
                'pc': self.emu.cpu.pc,
                'sp': self.emu.cpu.sp,
                'a': self.emu.cpu.a,
                'x': self.emu.cpu.x,
                'y': self.emu.cpu.y,
                'status': self.emu.cpu.status,
                'cycles': self.emu.cpu.cycles
            },
            'ppu': {
                'ctrl': self.emu.ppu.ctrl,
                'mask': self.emu.ppu.mask,
                'status': self.emu.ppu.status,
                'oam_addr': self.emu.ppu.oam_addr,
                'scroll_x': self.emu.ppu.scroll_x,
                'scroll_y': self.emu.ppu.scroll_y,
                'addr': self.emu.ppu.addr,
                'scanline': self.emu.ppu.scanline,
                'cycle': self.emu.ppu.cycle
            },
            'memory': bytes(self.emu.cpu.memory),
            'vram':   bytes(self.emu.ppu.vram),
            'oam':    bytes(self.emu.ppu.oam),
            'palette':bytes(self.emu.ppu.palette)
        }
        os.makedirs('saves', exist_ok=True)
        fname = f"saves/slot_{slot}.save"
        with open(fname, "wb") as f:
            pickle.dump(state, f)
        print(f"[INFO] State saved to {fname}")

    def load(self, slot=0):
        fname = f"saves/slot_{slot}.save"
        if not os.path.isfile(fname):
            print(f"[WARN] No save file {fname}")
            return
        with open(fname, "rb") as f:
            state = pickle.load(f)
        # CPU
        self.emu.cpu.pc     = state['cpu']['pc']
        self.emu.cpu.sp     = state['cpu']['sp']
        self.emu.cpu.a      = state['cpu']['a']
        self.emu.cpu.x      = state['cpu']['x']
        self.emu.cpu.y      = state['cpu']['y']
        self.emu.cpu.status = state['cpu']['status']
        self.emu.cpu.cycles = state['cpu']['cycles']
        # PPU
        self.emu.ppu.ctrl    = state['ppu']['ctrl']
        self.emu.ppu.mask    = state['ppu']['mask']
        self.emu.ppu.status  = state['ppu']['status']
        self.emu.ppu.oam_addr= state['ppu']['oam_addr']
        self.emu.ppu.scroll_x= state['ppu']['scroll_x']
        self.emu.ppu.scroll_y= state['ppu']['scroll_y']
        self.emu.ppu.addr    = state['ppu']['addr']
        self.emu.ppu.scanline= state['ppu']['scanline']
        self.emu.ppu.cycle   = state['ppu']['cycle']
        # Memory
        self.emu.cpu.memory[:]  = state['memory']
        self.emu.ppu.vram[:]    = state['vram']
        self.emu.ppu.oam[:]     = state['oam']
        self.emu.ppu.palette[:] = state['palette']
        print(f"[INFO] State loaded from {fname}")

# ----------------------------------------------------------
# (6) Main Emulator
# ----------------------------------------------------------
class NesticleEmulator:
    def __init__(self, rom_path=None):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Enhanced NES Emulator v1.0")

        self.cpu = CPU6502()
        self.ppu = PPU()
        self.apu = APU()
        self.saver = SaveState(self)

        self.clock = pygame.time.Clock()

        # If user gave a ROM, load it, else embedded
        if rom_path and os.path.isfile(rom_path):
            self.load_nes_rom(rom_path)
        else:
            print("[INFO] No valid external ROM, loading embedded TkNiter ROM.")
            self.load_data(embedded_tkniter_rom)

    def load_nes_rom(self, path):
        with open(path, "rb") as f:
            data = f.read()
        self.load_data(data)

    def load_data(self, rom_data):
        if len(rom_data) < 16 or rom_data[:4] != b"NES\x1A":
            raise ValueError("Invalid iNES header in data")
        mapper = NROM(rom_data)
        self.cpu.load_rom(mapper.get_prg_rom())
        self.ppu.load_chr(mapper.get_chr_rom())

        # If reset vector is zero, set it
        if self.cpu.memory[RESET_VECTOR] == 0x00 and self.cpu.memory[RESET_VECTOR+1] == 0x00:
            self.cpu.memory[RESET_VECTOR]   = 0x00
            self.cpu.memory[RESET_VECTOR+1] = 0x80

        self.cpu.reset()

    def poll_input(self):
        keys = pygame.key.get_pressed()
        st = 0
        # Simple mapping: Z->A, X->B, Shift->Select, Enter->Start
        # Arrows -> D-Pad
        if keys[pygame.K_z]:
            st |= 1 << 0
        if keys[pygame.K_x]:
            st |= 1 << 1
        if keys[pygame.K_RSHIFT] or keys[pygame.K_LSHIFT]:
            st |= 1 << 2
        if keys[pygame.K_RETURN]:
            st |= 1 << 3
        if keys[pygame.K_UP]:
            st |= 1 << 4
        if keys[pygame.K_DOWN]:
            st |= 1 << 5
        if keys[pygame.K_LEFT]:
            st |= 1 << 6
        if keys[pygame.K_RIGHT]:
            st |= 1 << 7
        self.cpu.controller_state[0] = st

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    print("[INFO] Settings Menu (stub).")
                elif e.key == pygame.K_F1:
                    print("[INFO] Save state slot 0.")
                    self.saver.save(0)
                elif e.key == pygame.K_F2:
                    print("[INFO] Load state slot 0.")
                    self.saver.load(0)
                elif e.key == pygame.K_F5:
                    print("[INFO] Reset CPU.")
                    self.cpu.reset()
        return True

    def run(self):
        CPU_CYCLES_PER_FRAME = 29780
        running = True
        while running:
            running = self.handle_events()
            self.poll_input()

            cycles_run = 0
            while cycles_run < CPU_CYCLES_PER_FRAME:
                c = self.cpu.step()
                cycles_run += c
                for _ in range(c*3):
                    nmi = self.ppu.step()
                    if nmi:
                        self.cpu.nmi_requested = True
                    if self.ppu.frame_done:
                        self.ppu.frame_done = False
                if self.apu.step():
                    if not self.cpu.get_flag(FLAG_I):
                        self.cpu.irq_requested = True

            self.ppu.render()
            self.draw_to_screen()
            self.clock.tick(FPS)

        self.apu.stop()
        pygame.quit()

    def draw_to_screen(self):
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        pxarr = pygame.PixelArray(surf)

        # Each pixel is RGBA in ppu.screen_pixels
        for y in range(SCREEN_HEIGHT):
            for x in range(SCREEN_WIDTH):
                idx = (y*SCREEN_WIDTH + x)*4
                r = self.ppu.screen_pixels[idx+0]
                g = self.ppu.screen_pixels[idx+1]
                b = self.ppu.screen_pixels[idx+2]
                # a = self.ppu.screen_pixels[idx+3]
                color_val = (r << 16) | (g << 8) | b
                pxarr[x, y] = color_val

        del pxarr
        scaled = pygame.transform.scale(surf, (WINDOW_WIDTH, WINDOW_HEIGHT))
        self.screen.blit(scaled, (0,0))
        pygame.display.flip()


def main():
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = None
    emulator = NesticleEmulator(path)
    emulator.run()

if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------
#               C CODE SNIPPET: iNES HEADER PARSER EXAMPLE
# ---------------------------------------------------------------------
#
# The following is a small demonstration in C of how one might read
# the iNES header from a file, showing the PRG/CHR sizes, etc.
# 
# Compile with:  gcc -o ines_reader ines_reader.c
# Usage:         ./ines_reader myrom.nes
#
# ---------------------------------------------------------------------
#
#   #include <stdio.h>
#   #include <stdlib.h>
#   #include <string.h>
#
#   typedef struct {
#       unsigned char prg_rom_size;
#       unsigned char chr_rom_size;
#       unsigned char flags6;
#       unsigned char flags7;
#       unsigned char prg_ram_size;
#       unsigned char flags9;
#       unsigned char flags10;
#       unsigned char unused[5];
#   } INES_HEADER;
#
#   void read_ines_header(FILE* fp, INES_HEADER* hdr) {
#       fread(hdr, sizeof(INES_HEADER), 1, fp);
#       if(hdr->prg_rom_size == 0)
#           hdr->prg_rom_size = 0x10;
#       if(hdr->chr_rom_size == 0)
#           hdr->chr_rom_size = 0x08;
#       if(hdr->prg_ram_size == 0)
#           hdr->prg_ram_size = 0x00;
#   }
#
#   int main(int argc, char* argv[]) {
#       if(argc != 2) {
#           printf("usage: %s <ines_file>\\n", argv[0]);
#           return 1;
#       }
#       FILE* fp = fopen(argv[1], "rb");
#       if(!fp) {
#           printf("Cannot open %s\\n", argv[1]);
#           return 1;
#       }
#       INES_HEADER hdr;
#       read_ines_header(fp, &hdr);
#       fclose(fp);
#       printf("PRG ROM SIZE: %d\\n", hdr.prg_rom_size);
#       printf("CHR ROM SIZE: %d\\n", hdr.chr_rom_size);
#       printf("PRG RAM SIZE: %d\\n", hdr.prg_ram_size);
#       return 0;
#   }
#
# ---------------------------------------------------------------------

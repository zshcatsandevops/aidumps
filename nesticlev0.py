import asyncio
import platform
import pygame
import numpy as np

# NES Constants
SCREEN_WIDTH = 256
SCREEN_HEIGHT = 240
NES_PPU_ADDRESS = 0x2000
NES_RAM_SIZE = 0x0800  # 2KB internal RAM
NES_PRG_ROM_OFFSET = 0x8000
FPS = 60
CYCLES_PER_FRAME = 29780  # NTSC approximate CPU cycles per frame

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH * 2, SCREEN_HEIGHT * 2))
pygame.display.set_caption("NES Emulator")

class Controller:
    def __init__(self):
        self.buttons = [False] * 8
        self.index = 0

    def write(self, value):
        if value & 1:
            self.index = 0

    def read(self):
        if self.index < 8:
            state = self.buttons[self.index]
            self.index += 1
            return 1 if state else 0
        return 1

class Mapper:
    def __init__(self, prg_rom, chr_rom):
        self.prg_rom = prg_rom
        self.chr_rom = chr_rom

    def read(self, addr):
        addr &= 0x7FFF
        if len(self.prg_rom) == 0x4000:
            return self.prg_rom[addr % 0x4000]
        return self.prg_rom[addr]

    def chr_read(self, addr):
        return self.chr_rom[addr % len(self.chr_rom)]

class PPU:
    def __init__(self, cpu):
        self.cpu = cpu
        self.vram = np.zeros(0x800, dtype=np.uint8)
        self.palette_ram = np.zeros(32, dtype=np.uint8)
        self.oam = np.zeros(0x100, dtype=np.uint8)
        self.framebuffer = np.zeros((SCREEN_HEIGHT, SCREEN_WIDTH, 3), dtype=np.uint8)
        self.ppu_ctrl = 0
        self.ppu_mask = 0
        self.ppu_status = 0x80
        self.ppu_scroll = [0, 0]
        self.ppu_addr = 0
        self.first_write = True
        self.ppu_data_buffer = 0

        # Expanded NES palette (64 colors)
        self.palette = [
            (84, 84, 84), (0, 30, 116), (8, 16, 144), (48, 0, 136),
            (68, 0, 100), (92, 0, 48), (84, 4, 0), (60, 24, 0),
            (32, 42, 0), (8, 58, 0), (0, 64, 0), (0, 60, 0),
            (0, 50, 60), (0, 0, 0), (0, 0, 0), (0, 0, 0),
            (152, 150, 152), (8, 76, 196), (48, 50, 236), (92, 30, 228),
            (136, 20, 176), (160, 20, 100), (152, 34, 32), (120, 60, 0),
            (84, 90, 0), (40, 114, 0), (8, 124, 0), (0, 118, 40),
            (0, 102, 120), (0, 0, 0), (0, 0, 0), (0, 0, 0),
            (236, 238, 236), (76, 154, 236), (120, 124, 236), (176, 98, 236),
            (228, 84, 236), (236, 88, 180), (236, 106, 100), (212, 136, 32),
            (160, 170, 0), (116, 196, 0), (76, 208, 32), (56, 204, 108),
            (56, 180, 204), (60, 60, 60), (0, 0, 0), (0, 0, 0),
            (236, 238, 236), (168, 204, 236), (188, 188, 236), (212, 178, 236),
            (236, 174, 236), (236, 174, 212), (236, 180, 176), (228, 196, 144),
            (204, 210, 120), (180, 222, 120), (168, 226, 144), (152, 226, 180),
            (160, 214, 228), (160, 162, 160), (0, 0, 0), (0, 0, 0)
        ] * 4  # Repeat to ensure index safety

    def ppu_read(self, addr):
        addr &= 0x3FFF
        if addr < 0x2000:
            return self.cpu.mapper.chr_read(addr)
        elif addr < 0x3F00:
            return self.vram[addr & 0x07FF]
        elif addr < 0x4000:
            return self.palette_ram[addr & 0x1F]
        return 0

    def ppu_write(self, addr, value):
        addr &= 0x3FFF
        if addr < 0x2000:
            pass
        elif addr < 0x3F00:
            self.vram[addr & 0x07FF] = value
        elif addr < 0x4000:
            self.palette_ram[addr & 0x1F] = value

    def write_register(self, addr, value):
        reg = (addr - 0x2000) % 8
        if reg == 0:
            self.ppu_ctrl = value
        elif reg == 1:
            self.ppu_mask = value
        elif reg == 5:
            if self.first_write:
                self.ppu_scroll[0] = value
            else:
                self.ppu_scroll[1] = value
            self.first_write = not self.first_write
        elif reg == 6:
            if self.first_write:
                self.ppu_addr = (value << 8) | (self.ppu_addr & 0xFF)
            else:
                self.ppu_addr = (self.ppu_addr & 0xFF00) | value
            self.first_write = not self.first_write
        elif reg == 7:
            self.ppu_write(self.ppu_addr, value)
            self.ppu_addr += 1 if (self.ppu_ctrl & 0x04) == 0 else 32

    def read_register(self, addr):
        reg = (addr - 0x2000) % 8
        if reg == 2:
            status = self.ppu_status
            self.ppu_status &= 0x7F
            self.first_write = True
            return status
        elif reg == 7:
            value = self.ppu_data_buffer
            self.ppu_data_buffer = self.ppu_read(self.ppu_addr)
            self.ppu_addr += 1 if (self.ppu_ctrl & 0x04) == 0 else 32
            return value
        return 0

    def render_frame(self):
        # Directly fill framebuffer with blue
        self.framebuffer[:, :] = self.palette[1]
        pygame.event.pump()  # Keep window responsive

class MOS6502:
    def __init__(self, mapper):
        self.a = self.x = self.y = 0
        self.sp = 0xFD
        self.pc = 0x8000
        self.status = 0x24
        self.memory = np.zeros(0x10000, dtype=np.uint8)
        self.ram = self.memory[:NES_RAM_SIZE]
        self.cycles = 0
        self.interrupt = None
        self.mapper = mapper
        self.ppu = PPU(self)
        self.controller = Controller()

class Emulator:
    def __init__(self):
        prg_rom = np.zeros(0x8000, dtype=np.uint8)
        chr_rom = np.zeros(0x2000, dtype=np.uint8)
        self.cpu = MOS6502(Mapper(prg_rom, chr_rom))
        self.cpu.ppu.palette_ram[0] = 0x01  # Set to blue

    def step_frame(self):
        self.cpu.ppu.render_frame()

    def update_display(self):
        surface = pygame.surfarray.make_surface(self.cpu.ppu.framebuffer)
        scaled = pygame.transform.scale(surface, (SCREEN_WIDTH * 2, SCREEN_HEIGHT * 2))
        screen.blit(scaled, (0, 0))
        pygame.display.flip()

async def main():
    emulator = Emulator()
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
        emulator.step_frame()
        emulator.update_display()
        await asyncio.sleep(1/60)

if __name__ == "__main__":
    asyncio.run(main())

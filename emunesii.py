#!/usr/bin/env python3
"""
Extended 'Nesticle' Emulator in Python -- Educational Demo
==========================================================

Disclaimer:
-----------
- This example is *still* incomplete but more advanced than the ultra-simplified skeleton.
- It adds more 6502 opcodes, naive memory mirroring, partial controller input, etc.
- True NES emulation requires cycle accuracy, a wide variety of mappers, correct PPU
  register interactions, correct APU emulation, etc.
- Use for educational or experimental fun only!

Usage:
------
    python test.py path/to/rom.nes

Recommended:
------------
    - Try this with simpler homebrew or test ROMs that use Mapper 0 (NROM).
    - For more complex games, expect breakage or missing features!

“Vibe Magic Coding” ~ :-)
"""

import sys
import pygame

# -----------------------------------------------------------
# Constants
# -----------------------------------------------------------

WINDOW_WIDTH  = 600
WINDOW_HEIGHT = 400
FPS           = 60

# 6502 CPU runs ~1.79 MHz on NES, but we won't be cycle-accurate
CPU_CLOCK = 1789773

# Memory layout
MEM_SIZE = 0x10000  # 64KB 6502 address space

# Controller bits
# Standard NES controller layout in bits:
#   0: A
#   1: B
#   2: Select
#   3: Start
#   4: Up
#   5: Down
#   6: Left
#   7: Right

# -----------------------------------------------------------
# CPU (6502) Partial Emulation
# -----------------------------------------------------------

class CPU6502:
    def __init__(self):
        # Registers
        self.pc = 0xC000  # Program Counter
        self.sp = 0xFD   # Stack Pointer
        self.a  = 0      # Accumulator
        self.x  = 0      # X Register
        self.y  = 0      # Y Register

        # Status Flags (P register)
        # Bits: N V - B D I Z C
        # We'll store them in one byte for simplicity
        self.status = 0x24  # Typical initial status

        # Memory
        self.memory = bytearray(MEM_SIZE)

        # Internal
        self.cycles = 0

        # For naive controller reading
        self.controller_state = 0
        self.controller_index = 0

    def read_memory(self, addr):
        """
        Read a byte from CPU memory. This includes naive I/O mirroring for PPU
        and a naive read from a single controller port at 0x4016.
        """
        addr &= 0xFFFF

        # Naive memory-mapped I/O:
        # 0x2000-0x2007 are PPU registers, typically mirrored every 8 bytes up to 0x3FFF
        # 0x4016 -> Controller #1 read
        if 0x2000 <= addr <= 0x3FFF:
            # Mirror down to 0x2000-0x2007
            reg = 0x2000 + (addr % 8)
            # We'll pretend any PPU register read returns 0 for now
            return 0

        elif addr == 0x4016:
            # Reading the controller shift register
            # Return the next bit from the controller state
            value = (self.controller_state >> self.controller_index) & 1
            self.controller_index = (self.controller_index + 1) & 7
            return value

        return self.memory[addr]

    def write_memory(self, addr, value):
        """
        Write a byte to CPU memory, with naive handling for PPU register mirroring,
        controller strobe (0x4016), etc.
        """
        addr &= 0xFFFF
        value &= 0xFF

        if 0x2000 <= addr <= 0x3FFF:
            # PPU registers, mirrored
            reg = 0x2000 + (addr % 8)
            # We won't actually implement them, just store in memory for demonstration
            self.memory[reg] = value

        elif addr == 0x4016:
            # Controller strobe
            # If the LSB is 1 -> reset the controller shift register index
            if value & 1:
                self.controller_index = 0
            # We store the value anyway
            self.memory[addr] = value

        else:
            self.memory[addr] = value

    def load_rom(self, prg_data, load_address=0x8000):
        """
        Load PRG data into memory. For NROM, it's typically loaded at 0x8000,
        and mirrored at 0xC000 if it's 16KB total. In some cases, 0xC000 is used too.
        """
        end = load_address + len(prg_data)
        if end > MEM_SIZE:
            raise ValueError("ROM too large to fit in CPU memory at given load address.")

        # Load at 0x8000
        self.memory[load_address:end] = prg_data

        # If PRG is 16KB, mirror it at 0xC000:
        if len(prg_data) == 0x4000:
            self.memory[0xC000:0x10000] = prg_data

    def reset(self):
        """
        Reset the CPU to a known state, reading the reset vector at 0xFFFC/0xFFFD.
        """
        lo = self.memory[0xFFFC]
        hi = self.memory[0xFFFD]
        self.pc = (hi << 8) | lo

        self.sp = 0xFD
        self.status = 0x24
        self.a = 0
        self.x = 0
        self.y = 0
        self.cycles = 0

    def step(self):
        """
        Execute a single 6502 instruction. Return (approx) cycles consumed.
        This is still incomplete, but covers some common opcodes + addressing modes.
        """
        pc_before = self.pc
        opcode = self.read_memory(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF

        # A helper to fetch next byte
        def fetch():
            val = self.read_memory(self.pc)
            self.pc = (self.pc + 1) & 0xFFFF
            return val

        # Addressing modes (only a few for example)
        def immediate():
            return fetch()

        def zeropage():
            return self.read_memory(fetch() & 0xFF)

        def zeropage_addr():
            return fetch() & 0xFF

        def absolute_addr():
            lo = fetch()
            hi = fetch()
            return (hi << 8) | lo

        def absolute():
            addr = absolute_addr()
            return self.read_memory(addr)

        def absolute_x():
            addr = absolute_addr()
            return self.read_memory((addr + self.x) & 0xFFFF)

        def absolute_y():
            addr = absolute_addr()
            return self.read_memory((addr + self.y) & 0xFFFF)

        def zeropage_x_addr():
            base = (fetch() + self.x) & 0xFF
            return base

        def zeropage_y_addr():
            base = (fetch() + self.y) & 0xFF
            return base

        # Flag helpers
        def set_flag(flag, condition):
            if condition:
                self.status |= flag
            else:
                self.status &= ~flag

        def get_flag(flag):
            return (self.status & flag) != 0

        def update_nz(value):
            set_flag(0x02, (value == 0))        # Z
            set_flag(0x80, ((value & 0x80) != 0))  # N

        # Write helpers
        def write_zeropage(addr, val):
            self.write_memory(addr, val)

        def write_absolute(addr, val):
            self.write_memory(addr, val)

        # 6502 opcode cases (a subset)
        if opcode == 0xA9:  # LDA #Immediate
            v = immediate()
            self.a = v
            update_nz(self.a)
            cycles = 2

        elif opcode == 0xA5:  # LDA Zeropage
            zp = zeropage_addr()
            self.a = self.read_memory(zp)
            update_nz(self.a)
            cycles = 3

        elif opcode == 0xB5:  # LDA Zeropage,X
            zp = (fetch() + self.x) & 0xFF
            self.a = self.read_memory(zp)
            update_nz(self.a)
            cycles = 4

        elif opcode == 0xAD:  # LDA Absolute
            addr = absolute_addr()
            self.a = self.read_memory(addr)
            update_nz(self.a)
            cycles = 4

        elif opcode == 0xBD:  # LDA Absolute,X
            addr = absolute_addr()
            self.a = self.read_memory((addr + self.x) & 0xFFFF)
            update_nz(self.a)
            cycles = 4  # +1 if page boundary crossed

        elif opcode == 0xB9:  # LDA Absolute,Y
            addr = absolute_addr()
            self.a = self.read_memory((addr + self.y) & 0xFFFF)
            update_nz(self.a)
            cycles = 4  # +1 if page boundary crossed

        elif opcode == 0xAA:  # TAX
            self.x = self.a
            update_nz(self.x)
            cycles = 2

        elif opcode == 0x8A:  # TXA
            self.a = self.x
            update_nz(self.a)
            cycles = 2

        elif opcode == 0xA2:  # LDX #Immediate
            v = immediate()
            self.x = v
            update_nz(self.x)
            cycles = 2

        elif opcode == 0xE8:  # INX
            self.x = (self.x + 1) & 0xFF
            update_nz(self.x)
            cycles = 2

        elif opcode == 0x00:  # BRK
            print("BRK encountered at PC=0x{:04X}, halting for demo.".format(pc_before))
            cycles = 7

        else:
            print(f"Unimplemented opcode: {hex(opcode)} at PC=0x{pc_before:04X}")
            cycles = 2

        self.cycles += cycles
        return cycles


# -----------------------------------------------------------
# PPU (Picture Processing Unit) -- Very Simplified
# -----------------------------------------------------------

class PPU:
    def __init__(self, screen):
        self.screen = screen
        self.cycle_count = 0
        # We might store CHR data here if we want to do a naive tile fetch

    def load_chr(self, chr_data):
        """
        Load CHR data (8KB or more) for naive usage. We won't do full tile rendering yet.
        """
        self.chr_data = chr_data

    def render_frame(self, memory):
        """
        Render a placeholder background and a simple 'red square'
        so we have something to look at. Real NES PPU is far more complex.
        """
        # Fill screen with a dark blue
        self.screen.fill((0, 0, 80))

        # Example: draw a red square
        pygame.draw.rect(self.screen, (255, 0, 0), (50, 50, 100, 100))

        # Flip buffer
        pygame.display.flip()

# -----------------------------------------------------------
# Main NesticleEmulator
# -----------------------------------------------------------

class NesticleEmulator:
    def __init__(self, rom_path):
        pygame.init()
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Nesticle Emulator Python - Extended Demo")

        # Create CPU and PPU
        self.cpu = CPU6502()
        self.ppu = PPU(self.screen)

        # Load the ROM
        self.load_nes_rom(rom_path)

    def load_nes_rom(self, rom_path):
        with open(rom_path, "rb") as f:
            rom_data = f.read()

        # Parse iNES header (16 bytes)
        if rom_data[0:4] != b"NES\x1A":
            raise ValueError("Invalid iNES ROM header.")

        prg_size_16k = rom_data[4]
        chr_size_8k = rom_data[5]
        flag6 = rom_data[6]
        flag7 = rom_data[7]
        # For simplicity, ignore advanced mapper checks

        prg_size = prg_size_16k * 16384
        chr_size = chr_size_8k * 8192

        # Skip trainer if present (flag6 bit2)
        has_trainer = (flag6 & 0x04) != 0
        trainer_offset = 512 if has_trainer else 0

        # PRG data starts after header + trainer
        prg_start = 16 + trainer_offset
        prg_data = rom_data[prg_start : prg_start + prg_size]

        # CHR data
        chr_start = prg_start + prg_size
        chr_data = rom_data[chr_start : chr_start + chr_size]

        # Load PRG into CPU memory. For mapper 0, typically at 0x8000
        self.cpu.load_rom(prg_data, 0x8000)

        # If no CHR data, some games can run with CHR RAM
        self.ppu.load_chr(chr_data)

        # Set up reset vector if not set
        # If the ROM sets 0xFFFC/0xFFFD, that’s used automatically, else we point to 0x8000
        if self.cpu.memory[0xFFFC] == 0x00 and self.cpu.memory[0xFFFD] == 0x00:
            self.cpu.memory[0xFFFC] = 0x00
            self.cpu.memory[0xFFFD] = 0x80

        self.cpu.reset()

    def poll_input(self):
        """
        Convert Pygame key events to a single-byte NES controller state.
        Bits: 0=A,1=B,2=Select,3=Start,4=Up,5=Down,6=Left,7=Right
        """
        keys = pygame.key.get_pressed()
        state = 0

        # We’ll map: Z -> A, X -> B, Shift -> Select, Enter -> Start
        # Arrow keys -> Up/Down/Left/Right
        if keys[pygame.K_z]:
            state |= (1 << 0)  # A
        if keys[pygame.K_x]:
            state |= (1 << 1)  # B
        if keys[pygame.K_RSHIFT] or keys[pygame.K_LSHIFT]:
            state |= (1 << 2)  # Select
        if keys[pygame.K_RETURN]:
            state |= (1 << 3)  # Start
        if keys[pygame.K_UP]:
            state |= (1 << 4)  # Up
        if keys[pygame.K_DOWN]:
            state |= (1 << 5)  # Down
        if keys[pygame.K_LEFT]:
            state |= (1 << 6)  # Left
        if keys[pygame.K_RIGHT]:
            state |= (1 << 7)  # Right

        # Store in CPU so reads from 0x4016 can return bits
        self.cpu.controller_state = state

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Poll keyboard, update controller state
            self.poll_input()

            # Run enough CPU steps for one "frame" (highly approximate)
            # Real NES does ~29780 CPU cycles per frame (NTSC ~ 60 Hz),
            # but we’ll just do a chunk of instructions.
            for _ in range(1000):
                self.cpu.step()

            # Render
            self.ppu.render_frame(self.cpu.memory)

            # 60 FPS limit
            self.clock.tick(FPS)

        pygame.quit()

# -----------------------------------------------------------
# Entry Point
# -----------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python test.py path/to/rom.nes")
        sys.exit(1)

    rom_path = sys.argv[1]
    emulator = NesticleEmulator(rom_path)
    emulator.run()

if __name__ == "__main__":
    main()

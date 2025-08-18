# nds_emulator_enhanced.py
# Enhanced Educational Nintendo DS emulator shell in Python + Tkinter.
# - NDS header parsing + NitroFS browsing
# - Cartridge mapping (ARM9/ARM7 segments -> main RAM)
# - Memory bus for RAM/VRAM/IO/Cart
# - Tiny ARM/Thumb interpreter subset (ADD/SUB/MOV/ORR/AND/CMP + LDR/STR + B/BL + LDR literal)
# - Cheats (apply each step), Debugger, Memory Viewer, Dual-screen Canvas (lightweight)
# - Keyboard -> DS buttons (active-low) mapped into KEYINPUT/KEYXY IO regs
# LEGAL: No BIOS/firmware/ROMs included. Use homebrew or your own dumps.

from __future__ import annotations
import os
import struct
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# Tkinter UI (lazy import for headless envs)
try:
    import tkinter as tk
    from tkinter import filedialog, ttk, messagebox, simpledialog
except Exception:  # pragma: no cover
    tk = None
    filedialog = None
    ttk = None
    messagebox = None
    simpledialog = None


# ------------------------ Cartridge Header ------------------------

@dataclass
class NDSHeader:
    game_title: str
    game_code: str
    maker_code: str
    unit_code: int
    device_capacity: int
    rom_version: int
    autostart: int
    arm9_rom_offset: int
    arm9_entry_address: int
    arm9_ram_address: int
    arm9_size: int
    arm7_rom_offset: int
    arm7_entry_address: int
    arm7_ram_address: int
    arm7_size: int
    fnt_offset: int
    fnt_size: int
    fat_offset: int
    fat_size: int
    icon_title_offset: int
    total_used_rom_size: int
    header_size: int

    @classmethod
    def parse(cls, header: bytes) -> "NDSHeader":
        if len(header) < 0x170:
            raise ValueError("Header too short")
        game_title = header[0x000:0x00C].decode("ascii", errors="ignore").rstrip("\0")
        game_code = header[0x00C:0x010].decode("ascii", errors="ignore")
        maker_code = header[0x010:0x012].decode("ascii", errors="ignore")
        unit_code = header[0x012]
        device_capacity = header[0x014]
        rom_version = header[0x01E]
        autostart = header[0x01F]
        (arm9_rom_offset,
         arm9_entry_address,
         arm9_ram_address,
         arm9_size,
         arm7_rom_offset,
         arm7_entry_address,
         arm7_ram_address,
         arm7_size) = struct.unpack_from("<8I", header, 0x020)
        (fnt_offset, fnt_size, fat_offset, fat_size) = struct.unpack_from("<4I", header, 0x040)
        icon_title_offset = struct.unpack_from("<I", header, 0x068)[0]
        total_used_rom_size = struct.unpack_from("<I", header, 0x080)[0]
        header_size = struct.unpack_from("<I", header, 0x084)[0]
        return cls(
            game_title, game_code, maker_code, unit_code, device_capacity, rom_version, autostart,
            arm9_rom_offset, arm9_entry_address, arm9_ram_address, arm9_size,
            arm7_rom_offset, arm7_entry_address, arm7_ram_address, arm7_size,
            fnt_offset, fnt_size, fat_offset, fat_size,
            icon_title_offset, total_used_rom_size, header_size,
        )

    @property
    def rom_capacity_bytes(self) -> int:
        # capacity = 128KB << device_capacity
        return 128 * 1024 << self.device_capacity


# ------------------------ NitroFS (FNT/FAT) ------------------------

@dataclass
class FATEntry:
    start: int
    end: int
    @property
    def size(self) -> int:
        return max(0, self.end - self.start)


class NitroFS:
    """Minimal NitroFS reader (read-only, in-memory)."""
    def __init__(self, rom_bytes: bytes, fnt_offset: int, fnt_size: int, fat_offset: int, fat_size: int):
        self.rom = rom_bytes
        self.fnt = rom_bytes[fnt_offset:fnt_offset + fnt_size]
        self.fat = rom_bytes[fat_offset:fat_offset + fat_size]
        self.main_table: Dict[int, Tuple[int, int, int]] = {}
        self.files: Dict[str, FATEntry] = {}
        self._parse_main_table()
        self._build_tree()

    def _u16(self, d: bytes, off: int) -> int:
        return struct.unpack_from("<H", d, off)[0]
    def _u32(self, d: bytes, off: int) -> int:
        return struct.unpack_from("<I", d, off)[0]

    def _parse_main_table(self) -> None:
        if len(self.fnt) < 8:
            return
        root_sub = self._u32(self.fnt, 0x00)
        first_file_id = self._u16(self.fnt, 0x04)
        total_dirs = self._u16(self.fnt, 0x06)
        self.main_table[0xF000] = (root_sub, first_file_id, total_dirs)
        for i in range(1, total_dirs):
            base = i * 8
            if base + 8 > len(self.fnt):
                break
            sub_off = self._u32(self.fnt, base + 0x00)
            first_id = self._u16(self.fnt, base + 0x04)
            parent = self._u16(self.fnt, base + 0x06)
            self.main_table[0xF000 + i] = (sub_off, first_id, parent)

        self.fat_entries: List[FATEntry] = []
        for i in range(0, len(self.fat), 8):
            start = self._u32(self.fat, i + 0)
            end = self._u32(self.fat, i + 4)
            self.fat_entries.append(FATEntry(start, end))

    def _build_tree(self) -> None:
        def walk_dir(dir_id: int, path: str) -> None:
            if dir_id not in self.main_table:
                return
            sub_off, first_file_id, _parent = self.main_table[dir_id]
            p = sub_off
            cur_id = first_file_id
            while 0 <= p < len(self.fnt):
                type_len = self.fnt[p]; p += 1
                if type_len == 0x00:
                    break
                is_dir = (type_len & 0x80) != 0
                name_len = (type_len & 0x7F)
                name = self.fnt[p:p + name_len].decode("ascii", errors="ignore"); p += name_len
                if is_dir:
                    if p + 2 > len(self.fnt): break
                    subdir_id = self._u16(self.fnt, p); p += 2
                    if subdir_id < 0xF001: subdir_id |= 0xF000
                    walk_dir(subdir_id, f"{path}/{name}" if path else name)
                else:
                    fid = cur_id; cur_id += 1
                    if 0 <= fid < len(self.fat_entries):
                        entry = self.fat_entries[fid]
                        self.files[f"{path}/{name}" if path else name] = entry
        walk_dir(0xF000, "")

    def list(self) -> List[Tuple[str, int]]:
        return sorted([(p, e.size) for p, e in self.files.items()])

    def read(self, path: str) -> bytes:
        e = self.files[path]
        return self.rom[e.start:e.end]


# ------------------------ Cheats ------------------------

class CheatEngine:
    """Action Replay–style minimalist parser (AAAAAAA VVVVVVVV)."""
    def __init__(self) -> None:
        self.codes: List[Tuple[int, int]] = []  # (addr, value)
    def clear(self) -> None:
        self.codes.clear()
    def load_from_text(self, text: str) -> int:
        count = 0
        for raw in text.splitlines():
            line = raw.strip().replace("_", " ").replace(":", " ")
            if not line or line.startswith(("#", "//", ";")):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            try:
                addr = int(parts[0], 16)
                value = int(parts[1], 16)
            except ValueError:
                continue
            self.codes.append((addr & 0xFFFFFFFF, value & 0xFFFFFFFF))
            count += 1
        return count
    def apply_all(self, bus: "MemoryBus") -> None:
        for addr, val in self.codes:
            if val <= 0xFF:
                bus.write8(addr, val)
            elif val <= 0xFFFF:
                bus.write16(addr, val)
            else:
                bus.write32(addr, val)


# ------------------------ Memory Bus ------------------------

class MemoryBus:
    MAIN_RAM_BASE = 0x02000000
    MAIN_RAM_SIZE = 4 * 1024 * 1024  # 4 MiB
    CART_BASE     = 0x08000000       # Cartridge ROM (read-only)
    VRAM_BASE     = 0x06000000       # VRAM stub
    VRAM_SIZE     = 512 * 1024
    IO_BASE       = 0x04000000       # IO stub
    IO_SIZE       = 0x1000

    KEYINPUT_ADDR = IO_BASE + 0x0130  # 0x04000130 (16-bit)
    KEYCNT_ADDR   = IO_BASE + 0x0132  # (unused here)
    KEYXY_ADDR    = IO_BASE + 0x0136  # 0x04000136 (X/Y and others)

    # KEYINPUT bits (active low): 0:A,1:B,2:Select,3:Start,4:Right,5:Left,6:Up,7:Down,8:R,9:L
    # KEYXY bits (active low; we'll use 0:X,1:Y)
    BTN_BITS = {
        "A":0, "B":1, "SELECT":2, "START":3, "RIGHT":4, "LEFT":5, "UP":6, "DOWN":7, "R":8, "L":9
    }
    BTN_XY_BITS = {"X":0, "Y":1}

    def __init__(self, rom: bytes):
        self.rom = rom
        self.main_ram = bytearray(self.MAIN_RAM_SIZE)
        self.vram = bytearray(self.VRAM_SIZE)
        self.io = bytearray(self.IO_SIZE)
        # Active-low: 1=not pressed, 0=pressed
        self._keyinput = 0x03FF  # 10 bits used
        self._keyxy = 0x00FF     # we use lower bits 0..1 (X,Y)
        self._sync_key_regs()

    def _sync_key_regs(self) -> None:
        # Write KEYINPUT / KEYXY into the IO mirror (little-endian)
        off_ki = self.KEYINPUT_ADDR - self.IO_BASE
        off_xy = self.KEYXY_ADDR - self.IO_BASE
        if 0 <= off_ki <= self.IO_SIZE - 2:
            self.io[off_ki+0] = self._keyinput & 0xFF
            self.io[off_ki+1] = (self._keyinput >> 8) & 0xFF
        if 0 <= off_xy <= self.IO_SIZE - 2:
            self.io[off_xy+0] = self._keyxy & 0xFF
            self.io[off_xy+1] = (self._keyxy >> 8) & 0xFF

    # Button API (used by UI)
    def set_button(self, name: str, pressed: bool) -> None:
        if name in self.BTN_BITS:
            bit = self.BTN_BITS[name]
            if pressed:
                self._keyinput &= ~(1 << bit)
            else:
                self._keyinput |= (1 << bit)
            self._sync_key_regs()
        elif name in self.BTN_XY_BITS:
            bit = self.BTN_XY_BITS[name]
            if pressed:
                self._keyxy &= ~(1 << bit)
            else:
                self._keyxy |= (1 << bit)
            self._sync_key_regs()

    # Region helpers
    def _in_main_ram(self, addr: int) -> bool:
        return self.MAIN_RAM_BASE <= addr < self.MAIN_RAM_BASE + self.MAIN_RAM_SIZE
    def _in_vram(self, addr: int) -> bool:
        return self.VRAM_BASE <= addr < self.VRAM_BASE + self.VRAM_SIZE
    def _in_io(self, addr: int) -> bool:
        return self.IO_BASE <= addr < self.IO_BASE + self.IO_SIZE
    def _in_cart(self, addr: int) -> bool:
        off = addr - self.CART_BASE
        return 0 <= off < len(self.rom)

    # Bulk copy
    def copy_from_rom_to_ram(self, rom_off: int, ram_addr: int, size: int) -> int:
        if size <= 0 or not self._in_main_ram(ram_addr):
            return 0
        end_addr = ram_addr + size
        if end_addr > self.MAIN_RAM_BASE + self.MAIN_RAM_SIZE:
            size = (self.MAIN_RAM_BASE + self.MAIN_RAM_SIZE) - ram_addr
        if size <= 0:
            return 0
        src_end = min(len(self.rom), rom_off + size)
        size = max(0, src_end - rom_off)
        if size <= 0:
            return 0
        dst_off = ram_addr - self.MAIN_RAM_BASE
        self.main_ram[dst_off:dst_off + size] = self.rom[rom_off:rom_off + size]
        return size

    # Primitive reads/writes (little-endian)
    def read8(self, addr: int) -> int:
        if self._in_main_ram(addr):
            return self.main_ram[addr - self.MAIN_RAM_BASE]
        if self._in_vram(addr):
            return self.vram[addr - self.VRAM_BASE]
        if self._in_io(addr):
            off = addr - self.IO_BASE
            return self.io[off]
        if self._in_cart(addr):
            return self.rom[addr - self.CART_BASE]
        return 0

    def read16(self, addr: int) -> int:
        return self.read8(addr) | (self.read8(addr + 1) << 8)

    def read32(self, addr: int) -> int:
        return (self.read8(addr)
                | (self.read8(addr + 1) << 8)
                | (self.read8(addr + 2) << 16)
                | (self.read8(addr + 3) << 24))

    def write8(self, addr: int, value: int) -> None:
        v = value & 0xFF
        if self._in_main_ram(addr):
            self.main_ram[addr - self.MAIN_RAM_BASE] = v
        elif self._in_vram(addr):
            self.vram[addr - self.VRAM_BASE] = v
        elif self._in_io(addr):
            # Writes to key regs are ignored (read-only in HW); we allow others to be stored
            if addr in (self.KEYINPUT_ADDR, self.KEYINPUT_ADDR+1, self.KEYXY_ADDR, self.KEYXY_ADDR+1):
                return
            self.io[addr - self.IO_BASE] = v
        # cart writes ignored

    def write16(self, addr: int, value: int) -> None:
        self.write8(addr, value & 0xFF)
        self.write8(addr + 1, (value >> 8) & 0xFF)

    def write32(self, addr: int, value: int) -> None:
        self.write8(addr, value & 0xFF)
        self.write8(addr + 1, (value >> 8) & 0xFF)
        self.write8(addr + 2, (value >> 16) & 0xFF)
        self.write8(addr + 3, (value >> 24) & 0xFF)


# ------------------------ ARM/Thumb Core (subset) ------------------------

class ARMCore:
    """Tiny ARM9/ARM7 core subset: DP ops, LDR/STR (imm), B/BL, Thumb basic ops + LDR literal."""
    def __init__(self, name: str, entry: int, bus: MemoryBus):
        self.name = name
        self.bus = bus
        self.regs = [0] * 16  # R0..R15 (R15=PC)
        self.cpsr = 0x0000001F  # System mode, ARM state (bit5=0)
        self.breakpoints: set[int] = set()
        self.set_pc(entry)
        self.running = False

    # --- PC helpers
    @property
    def pc(self) -> int:
        return self.regs[15]
    def set_pc(self, value: int) -> None:
        self.regs[15] = value & 0xFFFFFFFF

    # --- CPSR flags
    def _set_nz(self, result: int) -> None:
        if result & 0x80000000: self.cpsr |= (1 << 31)
        else: self.cpsr &= ~(1 << 31)
        if (result & 0xFFFFFFFF) == 0: self.cpsr |= (1 << 30)
        else: self.cpsr &= ~(1 << 30)
    def _set_c(self, c: bool) -> None:
        if c: self.cpsr |= (1 << 29)
        else: self.cpsr &= ~(1 << 29)
    def _set_v(self, v: bool) -> None:
        if v: self.cpsr |= (1 << 28)
        else: self.cpsr &= ~(1 << 28)

    # --- Conditions
    def _flag(self, bit: int) -> int:
        return (self.cpsr >> bit) & 1
    def check_condition(self, cond: int) -> bool:
        Z = self._flag(30); C = self._flag(29); N = self._flag(31); V = self._flag(28)
        if cond == 0x0: return Z == 1         # EQ
        if cond == 0x1: return Z == 0         # NE
        if cond == 0x2: return C == 1         # CS/HS
        if cond == 0x3: return C == 0         # CC/LO
        if cond == 0x4: return N == 1         # MI
        if cond == 0x5: return N == 0         # PL
        if cond == 0x6: return V == 1         # VS
        if cond == 0x7: return V == 0         # VC
        if cond == 0x8: return (C == 1 and Z == 0)   # HI
        if cond == 0x9: return (C == 0 or Z == 1)    # LS
        if cond == 0xA: return N == V         # GE
        if cond == 0xB: return N != V         # LT
        if cond == 0xC: return (Z == 0 and N == V)   # GT
        if cond == 0xD: return (Z == 1 or N != V)    # LE
        if cond == 0xE: return True           # AL
        return False                          # NV

    # --- Shifter
    def _ror32(self, val: int, amt: int) -> int:
        amt = amt & 31
        return ((val >> amt) | ((val << (32 - amt)) & 0xFFFFFFFF)) & 0xFFFFFFFF

    def get_operand(self, opcode: int) -> Tuple[int, Optional[bool]]:
        """Return (operand2, carry_out?) for ARM DP ops."""
        if opcode & (1 << 25):  # immediate (rotated)
            rot = ((opcode >> 8) & 0xF) * 2
            imm = opcode & 0xFF
            val = self._ror32(imm, rot)
            # For immediates, carry is unaffected in most cases; return None
            return val, None
        else:
            rm = opcode & 0xF
            shift = (opcode >> 5) & 0x3
            by_reg = (opcode >> 4) & 1
            if by_reg:
                rs = (opcode >> 8) & 0xF
                amount = self.regs[rs] & 0xFF
            else:
                amount = (opcode >> 7) & 0x1F
            val = self.regs[rm] & 0xFFFFFFFF
            c_out = None
            if shift == 0:  # LSL
                if amount == 0:
                    pass
                elif amount < 32:
                    c_out = (val >> (32 - amount)) & 1
                    val = (val << amount) & 0xFFFFFFFF
                elif amount == 32:
                    c_out = val & 1
                    val = 0
                else:
                    c_out = 0
                    val = 0
            elif shift == 1:  # LSR
                if amount == 0 or amount == 32:
                    c_out = (val >> 31) & 1
                    val = 0
                elif amount < 32:
                    c_out = (val >> (amount - 1)) & 1
                    val = (val >> amount) & 0xFFFFFFFF
                else:
                    c_out = 0
                    val = 0
            elif shift == 2:  # ASR
                if amount == 0 or amount >= 32:
                    c_out = (val >> 31) & 1
                    val = 0xFFFFFFFF if (val & 0x80000000) else 0
                else:
                    c_out = (val >> (amount - 1)) & 1
                    if val & 0x80000000:
                        val = ((val >> amount) | (0xFFFFFFFF << (32 - amount))) & 0xFFFFFFFF
                    else:
                        val = (val >> amount) & 0xFFFFFFFF
            else:  # ROR
                if amount == 0:
                    # RRX would use carry; we ignore carry propagation for simplicity
                    amount = 1
                amount &= 31
                val = self._ror32(val, amount)
                c_out = (val >> 31) & 1
            return val, c_out

    # --- Arithmetic helpers
    def _add(self, a: int, b: int) -> Tuple[int, bool, bool]:
        res = (a + b) & 0xFFFFFFFF
        c = (a + b) > 0xFFFFFFFF
        va = (a ^ b) & 0x80000000 == 0 and (a ^ res) & 0x80000000 != 0
        return res, c, va
    def _sub(self, a: int, b: int) -> Tuple[int, bool, bool]:
        res = (a - b) & 0xFFFFFFFF
        c = a >= b
        v = (a ^ b) & 0x80000000 != 0 and (a ^ res) & 0x80000000 != 0
        return res, c, v

    # --- Step
    def step(self) -> None:
        thumb = (self.cpsr >> 5) & 1
        if thumb:
            opcode = self.bus.read16(self.pc)
            self.set_pc(self.pc + 2)
            self.execute_thumb(opcode)
        else:
            opcode = self.bus.read32(self.pc)
            self.set_pc(self.pc + 4)
            cond = opcode >> 28
            if self.check_condition(cond):
                self.execute_arm(opcode)

    # --- ARM decode/execute (subset)
    def execute_arm(self, opcode: int) -> None:
        top = (opcode >> 25) & 0x7

        # Branch (B/BL)
        if top == 0b101:
            L = (opcode >> 24) & 1
            imm24 = opcode & 0x00FFFFFF
            if imm24 & 0x00800000:
                imm24 |= 0xFF000000  # sign-extend
            offset = (imm24 << 2) & 0xFFFFFFFF
            next_pc = self.pc  # already advanced
            if L:
                self.regs[14] = next_pc
            self.set_pc((next_pc + offset) & 0xFFFFFFFF)
            return

        # Single data transfer (LDR/STR, immediate offset only)
        if ((opcode >> 26) & 0b11) == 0b01:
            I = (opcode >> 25) & 1
            P = (opcode >> 24) & 1
            U = (opcode >> 23) & 1
            B = (opcode >> 22) & 1
            W = (opcode >> 21) & 1
            L = (opcode >> 20) & 1
            Rn = (opcode >> 16) & 0xF
            Rd = (opcode >> 12) & 0xF
            base = self.regs[Rn]
            if I == 0:
                offset = opcode & 0xFFF
            else:
                # register offset path (simple): use rm value (no shift)
                rm = opcode & 0xF
                offset = self.regs[rm] & 0xFFFFFFFF
            if U == 0:
                offset = (-offset) & 0xFFFFFFFF
            addr = base
            if P:
                addr = (base + offset) & 0xFFFFFFFF
                if W:
                    self.regs[Rn] = addr
            else:
                # post-index
                eff = (base + offset) & 0xFFFFFFFF
                if L:
                    addr = eff
                else:
                    addr = base
                self.regs[Rn] = eff
            if L:
                if B:
                    self.regs[Rd] = self.bus.read8(addr)
                else:
                    self.regs[Rd] = self.bus.read32(addr)
            else:
                if B:
                    self.bus.write8(addr, self.regs[Rd])
                else:
                    self.bus.write32(addr, self.regs[Rd])
            return

        # Data-processing / multiply region (we handle DP only)
        if top in (0b000, 0b001):
            op = (opcode >> 21) & 0xF
            S = (opcode >> 20) & 1
            Rn = (opcode >> 16) & 0xF
            Rd = (opcode >> 12) & 0xF
            operand2, c_out = self.get_operand(opcode)
            rn_val = self.regs[Rn] & 0xFFFFFFFF

            def write_rd(val: int):
                self.regs[Rd] = val & 0xFFFFFFFF
                if S:
                    self._set_nz(self.regs[Rd])
                    if c_out is not None and op in (0x0,0x1,0xC,0xD,0xE,0xF):  # AND/EOR/ORR/MOV/BIC/MVN style
                        self._set_c(bool(c_out))

            if op == 0x0:  # AND
                write_rd(rn_val & operand2)
            elif op == 0xC:  # ORR
                write_rd(rn_val | operand2)
            elif op == 0xE:  # BIC
                write_rd(rn_val & (~operand2 & 0xFFFFFFFF))
            elif op == 0xD:  # MOV
                write_rd(operand2)
            elif op == 0x2:  # SUB
                res, c, v = self._sub(rn_val, operand2)
                self.regs[Rd] = res
                if S:
                    self._set_nz(res); self._set_c(c); self._set_v(v)
            elif op == 0x4:  # ADD
                res, c, v = self._add(rn_val, operand2)
                self.regs[Rd] = res
                if S:
                    self._set_nz(res); self._set_c(c); self._set_v(v)
            elif op == 0xA:  # CMP (sets flags only)
                res, c, v = self._sub(rn_val, operand2)
                self._set_nz(res); self._set_c(c); self._set_v(v)
            else:
                # Unimplemented DP ops are treated as NOP for this shell
                pass
            return

        # SWI/CoPro/etc ignored in this shell

    # --- Thumb decode/execute (subset)
    def execute_thumb(self, op: int) -> None:
        top = (op >> 13) & 0x7

        # Move shifted register (LSL/LSR/ASR)
        if top == 0b000:
            sub = (op >> 11) & 0x3
            imm5 = (op >> 6) & 0x1F
            rs = (op >> 3) & 0x7
            rd = op & 0x7
            val = self.regs[rs] & 0xFFFFFFFF
            if sub == 0:  # LSL
                res = (val << imm5) & 0xFFFFFFFF
            elif sub == 1:  # LSR
                if imm5 == 0: imm5 = 32
                res = (val >> imm5) & 0xFFFFFFFF
            else:  # ASR
                if imm5 == 0: imm5 = 32
                if val & 0x80000000:
                    res = ((val >> imm5) | (0xFFFFFFFF << (32 - imm5))) & 0xFFFFFFFF
                else:
                    res = (val >> imm5) & 0xFFFFFFFF
            self.regs[rd] = res
            self._set_nz(res)
            return

        # Add/subtract immediate
        if top == 0b001:
            subop = (op >> 11) & 0x3
            rd = (op >> 8) & 0x7
            imm8 = op & 0xFF
            if subop == 0b000:  # MOV Rd, #imm8
                self.regs[rd] = imm8
                self._set_nz(self.regs[rd])
            elif subop == 0b001:  # CMP Rd, #imm8
                res, c, v = self._sub(self.regs[rd], imm8)
                self._set_nz(res); self._set_c(c); self._set_v(v)
            elif subop == 0b010:  # ADD Rd, #imm8
                res, c, v = self._add(self.regs[rd], imm8)
                self.regs[rd] = res; self._set_nz(res); self._set_c(c); self._set_v(v)
            elif subop == 0b011:  # SUB Rd, #imm8
                res, c, v = self._sub(self.regs[rd], imm8)
                self.regs[rd] = res; self._set_nz(res); self._set_c(c); self._set_v(v)
            return

        # ALU operations (register)
        if top == 0b010 and ((op >> 10) & 0x3) == 0b00:
            alu = (op >> 6) & 0xF
            rs = (op >> 3) & 0x7
            rd = op & 0x7
            a = self.regs[rd]; b = self.regs[rs]
            if alu == 0x0:  # AND
                self.regs[rd] = a & b; self._set_nz(self.regs[rd])
            elif alu == 0xC:  # ORR
                self.regs[rd] = a | b; self._set_nz(self.regs[rd])
            elif alu == 0x2:  # LSL (by reg, simplified)
                amt = b & 0xFF; self.regs[rd] = (a << amt) & 0xFFFFFFFF; self._set_nz(self.regs[rd])
            elif alu == 0x4:  # LSR (by reg)
                amt = b & 0xFF; self.regs[rd] = (a >> amt) & 0xFFFFFFFF; self._set_nz(self.regs[rd])
            elif alu == 0x5:  # ASR (by reg)
                amt = b & 0xFF
                if a & 0x80000000:
                    self.regs[rd] = ((a >> amt) | (0xFFFFFFFF << (32 - amt))) & 0xFFFFFFFF
                else:
                    self.regs[rd] = (a >> amt) & 0xFFFFFFFF
                self._set_nz(self.regs[rd])
            elif alu == 0xA:  # CMP
                res, c, v = self._sub(a, b); self._set_nz(res); self._set_c(c); self._set_v(v)
            elif alu == 0xD:  # MOV (register)
                self.regs[rd] = b; self._set_nz(self.regs[rd])
            elif alu == 0x8:  # TST
                self._set_nz(a & b)
            elif alu == 0x1:  # EOR
                self.regs[rd] = a ^ b; self._set_nz(self.regs[rd])
            elif alu == 0xC:  # ORR already handled above
                pass
            else:
                pass
            return

        # LDR literal: LDR Rd, [PC, #imm*4]
        if (op & 0xF800) == 0x4800:
            rd = (op >> 8) & 0x7
            imm = (op & 0xFF) << 2
            # In real ARM, PC is aligned to next instruction + 4; we'll approximate with current PC
            addr = (self.pc & 0xFFFFFFFC) + imm
            self.regs[rd] = self.bus.read32(addr)
            self._set_nz(self.regs[rd])
            return

        # STR/ LDR (register offset, word) simplified
        if (op & 0xF200) == 0x5000:
            L = (op >> 11) & 1
            rb = (op >> 3) & 0x7
            ro = (op >> 6) & 0x7
            rd = (op >> 0) & 0x7
            addr = (self.regs[rb] + self.regs[ro]) & 0xFFFFFFFF
            if L:
                self.regs[rd] = self.bus.read32(addr)
            else:
                self.bus.write32(addr, self.regs[rd])
            return

        # STR/ LDR (immediate, word)
        if (op & 0xE000) == 0x6000:
            L = (op >> 11) & 1
            rb = (op >> 3) & 0x7
            rd = (op >> 0) & 0x7
            imm5 = (op >> 6) & 0x1F
            addr = (self.regs[rb] + (imm5 << 2)) & 0xFFFFFFFF
            if L:
                self.regs[rd] = self.bus.read32(addr)
            else:
                self.bus.write32(addr, self.regs[rd])
            return

        # Conditional branch (B<cond>)
        if (op & 0xF000) == 0xD000 and (op & 0x0F00) != 0x0F00:
            cond = (op >> 8) & 0xF
            imm8 = op & 0xFF
            if imm8 & 0x80: imm8 -= 0x100
            if self.check_condition(cond):
                self.set_pc((self.pc + (imm8 << 1)) & 0xFFFFFFFF)
            return

        # Unconditional branch
        if (op & 0xF800) == 0xE000:
            imm11 = op & 0x7FF
            if imm11 & 0x400: imm11 -= 0x800
            self.set_pc((self.pc + (imm11 << 1)) & 0xFFFFFFFF)
            return

        # Others: NOP in this shell


# ------------------------ Emulator Orchestrator ------------------------

class Emulator:
    GRID_W = 16  # 16x12 cells per screen (lightweight renderer)
    GRID_H = 12

    def __init__(self, rom_bytes: bytes):
        self.rom = rom_bytes
        self.header = NDSHeader.parse(rom_bytes[:0x400])
        self.nitrofs = NitroFS(rom_bytes, self.header.fnt_offset, self.header.fnt_size,
                               self.header.fat_offset, self.header.fat_size)
        self.bus = MemoryBus(rom_bytes)
        self.cheats = CheatEngine()
        self._load_segments()
        self.arm9 = ARMCore("ARM9", self.header.arm9_entry_address, self.bus)
        self.arm7 = ARMCore("ARM7", self.header.arm7_entry_address, self.bus)
        self.canvas: Optional[tk.Canvas] = None
        self._grid_ids_top: List[int] = []
        self._grid_ids_bot: List[int] = []

    def _load_segments(self) -> None:
        self.bus.copy_from_rom_to_ram(self.header.arm9_rom_offset, self.header.arm9_ram_address, self.header.arm9_size)
        self.bus.copy_from_rom_to_ram(self.header.arm7_rom_offset, self.header.arm7_ram_address, self.header.arm7_size)

    def load_cheats_text(self, text: str) -> int:
        return self.cheats.load_from_text(text)

    def attach_canvas(self, canvas: tk.Canvas) -> None:
        self.canvas = canvas
        self._setup_grid()

    def _setup_grid(self) -> None:
        if not self.canvas:
            return
        self.canvas.delete("all")
        cell_w = 256 // self.GRID_W
        cell_h = 192 // self.GRID_H
        # Top screen grid
        self._grid_ids_top.clear()
        for r in range(self.GRID_H):
            for c in range(self.GRID_W):
                x0 = c * cell_w
                y0 = r * cell_h
                x1 = x0 + cell_w
                y1 = y0 + cell_h
                rid = self.canvas.create_rectangle(x0, y0, x1, y1, outline="", fill="#000000")
                self._grid_ids_top.append(rid)
        # Bottom screen grid (offset by 192 px)
        self._grid_ids_bot.clear()
        for r in range(self.GRID_H):
            for c in range(self.GRID_W):
                x0 = c * cell_w
                y0 = 192 + r * cell_h
                x1 = x0 + cell_w
                y1 = y0 + cell_h
                rid = self.canvas.create_rectangle(x0, y0, x1, y1, outline="", fill="#000000")
                self._grid_ids_bot.append(rid)

    def step(self, cycles_per_core: int = 1) -> None:
        for _ in range(cycles_per_core):
            self.arm9.step()
            self.arm7.step()
        self.cheats.apply_all(self.bus)

    @staticmethod
    def _bgr555_to_hex(c15: int) -> str:
        # Treat VRAM as 15-bit BGR (simplified). Many homebrew write RGB555; this is "close enough" for a stub.
        r = (c15 & 0x1F) * 8
        g = ((c15 >> 5) & 0x1F) * 8
        b = ((c15 >> 10) & 0x1F) * 8
        return f"#{r:02x}{g:02x}{b:02x}"

    def render_screen(self) -> None:
        if not self.canvas:
            return
        # Sample VRAM into GRID_W x GRID_H cells per screen
        cell_w = 256 // self.GRID_W
        cell_h = 192 // self.GRID_H

        # Top screen starts at VRAM_BASE + 0
        for r in range(self.GRID_H):
            for c in range(self.GRID_W):
                sx = c * cell_w + cell_w // 2
                sy = r * cell_h + cell_h // 2
                off = (sy * 256 + sx) * 2
                if off + 1 < self.bus.VRAM_SIZE:
                    c15 = self.bus.vram[off] | (self.bus.vram[off + 1] << 8)
                    color = self._bgr555_to_hex(c15)
                else:
                    color = "#000000"
                rid = self._grid_ids_top[r * self.GRID_W + c]
                self.canvas.itemconfig(rid, fill=color)

        # Bottom screen placed right after top (assumption for shell)
        base = 256 * 192 * 2
        for r in range(self.GRID_H):
            for c in range(self.GRID_W):
                sx = c * cell_w + cell_w // 2
                sy = r * cell_h + cell_h // 2
                off = base + (sy * 256 + sx) * 2
                if off + 1 < len(self.bus.vram):
                    c15 = self.bus.vram[off] | (self.bus.vram[off + 1] << 8)
                    color = self._bgr555_to_hex(c15)
                else:
                    color = "#000000"
                rid = self._grid_ids_bot[r * self.GRID_W + c]
                self.canvas.itemconfig(rid, fill=color)


# ------------------------ UI: Debugger, Memory Viewer, NitroFS Browser ------------------------

class DebuggerWin:
    def __init__(self, app: "App"):
        self.app = app
        self.emu = app.emu
        self.root = tk.Toplevel(app.root)
        self.root.title("Debugger")
        self.root.geometry("640x460")

        self.arm_choice = tk.StringVar(value="ARM9")
        tk.Radiobutton(self.root, text="ARM9", variable=self.arm_choice, value="ARM9", command=self.refresh).pack(anchor="w")
        tk.Radiobutton(self.root, text="ARM7", variable=self.arm_choice, value="ARM7", command=self.refresh).pack(anchor="w")

        self.regs_text = tk.Text(self.root, width=80, height=18, state="disabled")
        self.regs_text.pack(fill="x", padx=6, pady=6)

        btns = tk.Frame(self.root); btns.pack(fill="x")
        tk.Button(btns, text="Step", command=self.do_step).pack(side="left", padx=2)
        tk.Button(btns, text="Run", command=self.do_run).pack(side="left", padx=2)
        tk.Button(btns, text="Stop", command=self.do_stop).pack(side="left", padx=2)
        tk.Button(btns, text="Add Breakpoint @PC", command=self.add_bp_pc).pack(side="left", padx=8)
        tk.Button(btns, text="Clear Breakpoints", command=self.clear_bps).pack(side="left", padx=2)

        self.status = tk.StringVar(value="")
        tk.Label(self.root, textvariable=self.status).pack(anchor="w", padx=6)

        self.running = False
        self.refresh()

    def core(self) -> ARMCore:
        return self.emu.arm9 if self.arm_choice.get() == "ARM9" else self.emu.arm7

    def refresh(self) -> None:
        c = self.core()
        rs = c.regs
        txt = []
        for i in range(0, 13, 4):
            row = " ".join(f"R{j:02d}={rs[j]:08X}" for j in range(i, min(i+4, 13)))
            txt.append(row)
        txt.append(f"SP(R13)={rs[13]:08X}  LR(R14)={rs[14]:08X}  PC(R15)={rs[15]:08X}")
        txt.append(f"CPSR={c.cpsr:08X}  (N={c._flag(31)} Z={c._flag(30)} C={c._flag(29)} V={c._flag(28)})")
        txt.append(f"Breakpoints: {', '.join(f'{x:08X}' for x in sorted(c.breakpoints)) or '—'}")
        # Peek 5 words at PC
        base = c.pc
        dis = []
        for k in range(5):
            addr = (base + 4*k) & 0xFFFFFFFF
            op = self.emu.bus.read32(addr)
            dis.append(f"{addr:08X}: {op:08X}  ; raw")
        txt.append("\nDisassembly (raw 32-bit words):\n" + "\n".join(dis))

        self.regs_text.config(state="normal")
        self.regs_text.delete("1.0", "end")
        self.regs_text.insert("end", "\n".join(txt))
        self.regs_text.config(state="disabled")

    def add_bp_pc(self) -> None:
        c = self.core()
        c.breakpoints.add(c.pc & 0xFFFFFFFF)
        self.refresh()

    def clear_bps(self) -> None:
        c = self.core()
        c.breakpoints.clear()
        self.refresh()

    def do_step(self) -> None:
        self.emu.step(1)
        self.refresh()
        self.app.render_once()

    def do_run(self) -> None:
        if self.running:
            return
        self.running = True
        self.status.set("Running…")
        self._tick()

    def _tick(self) -> None:
        if not self.running:
            return
        hit_bp = False
        for _ in range(500):
            self.emu.step(1)
            if (self.emu.arm9.pc in self.emu.arm9.breakpoints) or (self.emu.arm7.pc in self.emu.arm7.breakpoints):
                hit_bp = True
                break
        self.refresh()
        self.app.render_once()
        if hit_bp:
            self.status.set("Hit breakpoint.")
            self.running = False
            return
        self.root.after(1, self._tick)

    def do_stop(self) -> None:
        self.running = False
        self.status.set("Stopped.")


class MemoryViewerWin:
    def __init__(self, app: "App"):
        self.app = app
        self.emu = app.emu
        self.root = tk.Toplevel(app.root)
        self.root.title("Memory Viewer")
        self.root.geometry("760x560")

        top = tk.Frame(self.root); top.pack(fill="x", padx=6, pady=4)
        tk.Label(top, text="Address (hex):").pack(side="left")
        self.addr_var = tk.StringVar(value="02000000")
        tk.Entry(top, textvariable=self.addr_var, width=12).pack(side="left", padx=4)
        tk.Button(top, text="Go", command=self.refresh).pack(side="left", padx=4)
        tk.Button(top, text="Write…", command=self.write_value).pack(side="left", padx=8)

        self.text = tk.Text(self.root, width=100, height=32, state="disabled")
        self.text.pack(fill="both", expand=True, padx=6, pady=6)

        self.refresh()

    def refresh(self) -> None:
        try:
            addr = int(self.addr_var.get(), 16) & 0xFFFFFFFF
        except ValueError:
            addr = 0x02000000
            self.addr_var.set(f"{addr:08X}")
        lines = []
        span = 0x200  # 512 bytes
        for base in range(addr, addr + span, 16):
            bytes16 = [self.emu.bus.read8(base + i) for i in range(16)]
            hexpart = " ".join(f"{b:02X}" for b in bytes16[:8]) + "  " + " ".join(f"{b:02X}" for b in bytes16[8:])
            ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in bytes16)
            lines.append(f"{base:08X}  {hexpart}  {ascii_part}")
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("end", "\n".join(lines))
        self.text.config(state="disabled")

    def write_value(self) -> None:
        addr_s = simpledialog.askstring("Write", "Address (hex):", initialvalue=self.addr_var.get())
        if not addr_s:
            return
        val_s = simpledialog.askstring("Write", "Value (hex):", initialvalue="00000000")
        if not val_s:
            return
        width_s = simpledialog.askstring("Write", "Width: 8/16/32", initialvalue="32")
        try:
            addr = int(addr_s, 16) & 0xFFFFFFFF
            val = int(val_s, 16) & 0xFFFFFFFF
            width = int(width_s)
        except Exception:
            return
        if width == 8:
            self.emu.bus.write8(addr, val)
        elif width == 16:
            self.emu.bus.write16(addr, val)
        else:
            self.emu.bus.write32(addr, val)
        self.addr_var.set(f"{addr & 0xFFFFFFF0:08X}")
        self.refresh()


class NitroBrowserWin:
    def __init__(self, app: "App"):
        self.app = app
        self.emu = app.emu
        self.root = tk.Toplevel(app.root)
        self.root.title("NitroFS Browser")
        self.root.geometry("600x420")
        tree = ttk.Treeview(self.root, columns=("size",), displaycolumns=("size",))
        tree.heading("#0", text="Path")
        tree.heading("size", text="Size (bytes)")
        tree.pack(fill="both", expand=True)

        paths = self.emu.nitrofs.list()
        node_map: Dict[str, str] = {"": ""}

        def ensure_node(path: str) -> str:
            if path in node_map:
                return node_map[path]
            parent = os.path.dirname(path)
            node_parent = ensure_node(parent) if parent else ""
            text = os.path.basename(path)
            node_id = tree.insert(node_parent, "end", text=text, values=("—",))
            node_map[path] = node_id
            return node_id

        for path, size in paths:
            folder = os.path.dirname(path)
            base = os.path.basename(path)
            node_parent = ensure_node(folder) if folder else ""
            tree.insert(node_parent, "end", text=base, values=(size,))

        def on_open(_event):
            item = tree.focus()
            if not item: return
            parts = []
            cur = item
            while cur:
                parts.append(tree.item(cur, "text"))
                cur = tree.parent(cur)
            full = "/".join(reversed([p for p in parts if p]))
            if full in dict(paths):
                data = self.emu.nitrofs.read(full)
                if len(data) <= 64 * 1024:
                    preview = tk.Toplevel(self.root)
                    preview.title(full)
                    txt = tk.Text(preview, width=100, height=30)
                    txt.pack(fill="both", expand=True)
                    try:
                        txt.insert("end", data.decode("utf-8"))
                    except UnicodeDecodeError:
                        hexlines = []
                        for i in range(0, len(data), 16):
                            chunk = data[i:i+16]
                            hexpart = " ".join(f"{b:02X}" for b in chunk)
                            asc = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
                            hexlines.append(f"{i:08X}  {hexpart:<47}  {asc}")
                        txt.insert("end", "\n".join(hexlines))
                else:
                    messagebox.showinfo("NitroFS", "File too large to preview (> 64 KiB).")
        tree.bind("<Double-1>", on_open)


# ------------------------ App ------------------------

class App:
    KEYMAP_DOWN = {
        "z": "A",
        "x": "B",
        "a": "Y",
        "s": "X",
        "Return": "START",
        "Shift_L": "SELECT",
        "Shift_R": "SELECT",
        "q": "L",
        "w": "R",
        "Up": "UP",
        "Down": "DOWN",
        "Left": "LEFT",
        "Right": "RIGHT",
    }
    # release mapping is identical
    KEYMAP_UP = KEYMAP_DOWN

    def __init__(self, root: "tk.Tk"):
        self.root = root
        self.root.title("NDS Emulator Enhanced (Educational Shell)")
        self.emu: Optional[Emulator] = None
        self._running = False
        self._frame_timer_active = False

        # Menus
        menubar = tk.Menu(root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open ROM (.nds)", command=self.open_rom)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        emu_menu = tk.Menu(menubar, tearoff=0)
        emu_menu.add_command(label="Run", command=self.run_nonblocking, state="disabled")
        emu_menu.add_command(label="Pause", command=self.pause_run, state="disabled")
        emu_menu.add_command(label="Step", command=self.step_once, state="disabled")
        emu_menu.add_command(label="Reset PCs to Entry", command=self.reset_pcs, state="disabled")
        menubar.add_cascade(label="Emulation", menu=emu_menu)

        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Debugger…", command=self.open_debugger, state="disabled")
        tools_menu.add_command(label="Memory Viewer…", command=self.open_memview, state="disabled")
        tools_menu.add_command(label="Browse NitroFS…", command=self.open_nitro_browser, state="disabled")
        menubar.add_cascade(label="Tools", menu=tools_menu)

        cheats_menu = tk.Menu(menubar, tearoff=0)
        cheats_menu.add_command(label="Load Cheats from Text…", command=self.load_cheats, state="disabled")
        cheats_menu.add_command(label="Clear Cheats", command=self.clear_cheats, state="disabled")
        menubar.add_cascade(label="Cheats", menu=cheats_menu)

        self.root.config(menu=menubar)
        self._menus = {"emu": emu_menu, "tools": tools_menu, "cheats": cheats_menu}

        # Top info box
        self.info = tk.Text(root, width=100, height=10, state="disabled")
        self.info.pack(fill="x")

        # Dual-screen canvas: 256x192 (top) + 256x192 (bottom)
        self.canvas = tk.Canvas(root, width=256, height=384, bg="#000000", highlightthickness=0)
        self.canvas.pack(padx=6, pady=6)

        # Bind keys
        root.bind("<KeyPress>", self._on_key_down)
        root.bind("<KeyRelease>", self._on_key_up)

    # ----- File / ROM -----
    def open_rom(self) -> None:
        if filedialog is None:
            print("No Tk environment.")
            return
        path = filedialog.askopenfilename(filetypes=[("Nintendo DS ROM", "*.nds"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, "rb") as f:
                data = f.read()
            self.emu = Emulator(data)
            self.emu.attach_canvas(self.canvas)
            self.render_header()
            # Enable menus
            self._menus["cheats"].entryconfig(0, state="normal")
            self._menus["cheats"].entryconfig(1, state="normal")
            self._menus["emu"].entryconfig(0, state="normal")
            self._menus["emu"].entryconfig(1, state="normal")
            self._menus["emu"].entryconfig(2, state="normal")
            self._menus["emu"].entryconfig(3, state="normal")
            self._menus["tools"].entryconfig(0, state="normal")
            self._menus["tools"].entryconfig(1, state="normal")
            self._menus["tools"].entryconfig(2, state="normal")
            # Start a lightweight frame timer for rendering even when paused
            if not self._frame_timer_active:
                self._frame_timer_active = True
                self.root.after(33, self._frame_tick)
        except Exception as e:
            if messagebox:
                messagebox.showerror("Error", f"Failed to open ROM: {e}")
            else:
                print("Error:", e)

    def render_header(self) -> None:
        if not self.emu:
            return
        h = self.emu.header
        self.info.config(state="normal")
        self.info.delete("1.0", "end")
        self.info.insert("end", f"Title: {h.game_title}\n")
        self.info.insert("end", f"Game Code: {h.game_code}   Maker: {h.maker_code}\n")
        self.info.insert("end", f"Unit: {h.unit_code:#04x}   ROM version: {h.rom_version}\n")
        self.info.insert("end", f"Capacity: {h.rom_capacity_bytes/1024/1024:.1f} MiB   Header size: {h.header_size:#x}\n")
        self.info.insert("end", "\nARM9:\n")
        self.info.insert("end", f"  ROM off: {h.arm9_rom_offset:#x}  Entry: {h.arm9_entry_address:#x}  RAM: {h.arm9_ram_address:#x}  Size: {h.arm9_size:#x}\n")
        self.info.insert("end", "ARM7:\n")
        self.info.insert("end", f"  ROM off: {h.arm7_rom_offset:#x}  Entry: {h.arm7_entry_address:#x}  RAM: {h.arm7_ram_address:#x}  Size: {h.arm7_size:#x}\n")
        self.info.insert("end", "\nNitroFS:\n")
        self.info.insert("end", f"  FNT: off {h.fnt_offset:#x}, size {h.fnt_size:#x}   FAT: off {h.fat_offset:#x}, size {h.fat_size:#x}\n")
        self.info.insert("end", f"Icon/Title off: {h.icon_title_offset:#x}  Total Used ROM: {h.total_used_rom_size:#x}\n")
        self.info.insert("end", "\nDisclaimer: This is an educational shell, not a full emulator.\n")
        self.info.config(state="disabled")

    # ----- Emulation control -----
    def step_once(self) -> None:
        if not self.emu:
            return
        self.emu.step(1)
        self.render_once()

    def run_nonblocking(self) -> None:
        if not self.emu or self._running:
            return
        self._running = True
        self.root.after(1, self._run_tick)

    def pause_run(self) -> None:
        self._running = False

    def _run_tick(self) -> None:
        if not self._running or not self.emu:
            return
        hit_bp = False
        for _ in range(1000):
            self.emu.step(1)
            if (self.emu.arm9.pc in self.emu.arm9.breakpoints) or (self.emu.arm7.pc in self.emu.arm7.breakpoints):
                hit_bp = True
                break
        if hit_bp and messagebox:
            messagebox.showinfo("Break", "Hit breakpoint.")
            self._running = False
        self.render_once()
        if self._running:
            self.root.after(1, self._run_tick)

    def reset_pcs(self) -> None:
        if not self.emu:
            return
        self.emu.arm9.set_pc(self.emu.header.arm9_entry_address)
        self.emu.arm7.set_pc(self.emu.header.arm7_entry_address)
        if messagebox:
            messagebox.showinfo("Reset", "PCs reset to entry addresses.")

    # ----- Tools -----
    def open_debugger(self) -> None:
        if self.emu:
            DebuggerWin(self)

    def open_memview(self) -> None:
        if self.emu:
            MemoryViewerWin(self)

    def open_nitro_browser(self) -> None:
        if self.emu:
            NitroBrowserWin(self)

    # ----- Cheats -----
    def load_cheats(self) -> None:
        if self.emu is None:
            return
        top = tk.Toplevel(self.root)
        top.title("Load Cheats")
        tk.Label(top, text="Paste Action Replay–style codes:\n(Format: AAAAAAAA VVVVVVVV per line)").pack()
        txt = tk.Text(top, width=80, height=20)
        txt.pack(fill="both", expand=True)
        status = tk.StringVar(value="")
        tk.Label(top, textvariable=status).pack()

        def do_load():
            count = self.emu.load_cheats_text(txt.get("1.0", "end"))
            status.set(f"Loaded {count} entries. (Applied each step)")
        tk.Button(top, text="Load", command=do_load).pack(pady=6)

    def clear_cheats(self) -> None:
        if self.emu:
            self.emu.cheats.clear()
            if messagebox:
                messagebox.showinfo("Cheats", "Cleared cheats.")

    # ----- Rendering -----
    def render_once(self) -> None:
        if self.emu:
            self.emu.render_screen()

    def _frame_tick(self) -> None:
        # Keep screens alive/redrawn ~30 FPS even when paused
        self.render_once()
        if self._frame_timer_active:
            self.root.after(33, self._frame_tick)

    # ----- Input -----
    def _on_key_down(self, event) -> None:
        if not self.emu:
            return
        key = event.keysym
        btn = self.KEYMAP_DOWN.get(key)
        if btn:
            self.emu.bus.set_button(btn, True)

    def _on_key_up(self, event) -> None:
        if not self.emu:
            return
        key = event.keysym
        btn = self.KEYMAP_UP.get(key)
        if btn:
            self.emu.bus.set_button(btn, False)


# ------------------------ Main ------------------------

def main() -> None:
    if tk is None:
        print("Tkinter not available in this environment.")
        return
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()

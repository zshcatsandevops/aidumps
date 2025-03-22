# flame64.py

import struct

# 4MB RDRAM
RDRAM_SIZE = 0x400000
rdram = bytearray(RDRAM_SIZE)

# Load ROM
def load_rom(path):
    with open(path, 'rb') as f:
        data = f.read()
        print(f"ROM loaded: {len(data)} bytes")

        # Detect and fix byte order
        if data[0:4] == b'\x80\x37\x12\x40':  # .z64 (big endian)
            rom_data = data
        elif data[0:4] == b'\x37\x80\x40\x12':  # .v64 (byte-swapped)
            rom_data = bytearray()
            for i in range(0, len(data), 2):
                rom_data += data[i+1:i+2] + data[i:i+1]
        elif data[0:4] == b'\x40\x12\x37\x80':  # .n64 (little endian)
            rom_data = bytearray()
            for i in range(0, len(data), 4):
                rom_data += data[i+3:i+4] + data[i+2:i+3] + data[i+1:i+2] + data[i:i+1]
        else:
            raise Exception("Unknown or unsupported ROM format.")

        print("ROM byte order normalized.")
        return rom_data

# Test ROM load
if __name__ == '__main__':
    rom = load_rom('super_mario_64.z64')

import pygame
import sys

# Hex data provided by the user - The "ripped" essence, meow!
# This is raw data, probably from something like a ROM, nya~
# My HQRIPPER 7.1 chewed this up, purrrr.
HEX_DATA = (
    "2e0000ea24ffae51699aa2213d84820a"
    "84e409ad11248b98c0817f21a352be19"
    "9309ce2010464a4af82731ec58c7e833"
    "82e3cebf85f4df94ce4b09c194568ac0"
    "1372a7fc9f844d73a3ca9a615897a327"
    "fc039876231dc7610304ae56bf388400"
    "40a70efdff52fe036f9530f197fbc085"
    "60d68025a963be03014e38e2f9a234ff"
    "bb3e0344780090cb88113a9465c07c63"
    "87f03cafd625e48b380aac7221d4f807"
    "5355504552204d4152494f4241413245"  # "SUPER MARIOBAA2E" - Oh, a clue, nya!
    "303196000000000000000000008e0000"
    "1200a0e300f029e128d09fe51f00a0e3"
    "00f029e118d09fe598119fe518008fe2"
    "000081e590119fe50fe0a0e111ff2fe1"
    "f2ffffea007e0003807f000301c3a0e3"
    "023c8ce2002093e5221802e00020a0e3"
    "020a11e27c014315feffff1a042082e2"
    "010011e2b8004c112200001a042082e2"
    "800011e21f00001a042082e2400011e2"
    "1c00001a042082e2020011e21900001a"
    "042082e2040011e21600001a042082e2"
    "080011e21300001a042082e2100011e2"
    "1000001a042082e2200011e20d00001a"
    "042082e2010c11e20a00001a042082e2"
    "020c11e20700001a042082e2010b11e2"
    "0400001a042082e2020b11e20100001a"
    "042082e2010a11e2b200c3e1bc109fe5"
    "021081e0000091e510ff2fe101c3a0e3"
    "023c8ce2002093e5221802e00020a0e3"
    "020a11e27c014315feffff1a042082e2"
    "010011e2b8004c111900001a042082e2"
    "800011e21600001a042082e2400011e2"
    "1300001a042082e2020011e21000001a"
    "042082e2040011e20d00001a042082e2"
    "010c11e20a00001a042082e2020c11e2"
    "0700001a042082e2010b11e20400001a"
    "042082e2020b11e20100001a042082e2"
    "010a11e2b200c3e114109fe5021081e0"
    "000091e510ff2fe1fc7f00034d040008"
    "007a0003007a000370b5114d11496818"
    "048801f02ff9104aa918002008700f48"
    "29186f2008700e496e18307800285dd0"
    "201c82f0bdff012c16d0082c00d088e0"
    "3078022828d197f003fe064aa81815e0"
    "4023000356080000b2560000b3560000"
    "830800009c5500001a4c1b4960180078"
    "022811d197f0ecfd184aa01802681849"
    "5018007803210840002805d015495018"
    "0178f022114001700e4b0f4a99180020"
    "08700e481b1819680f4a89180878ef22"
    "1040087019680c480918087820221043"
    "08707ff083f814209bf0b4fa80209bf0"
    "21fb3ee040230003830800009c550000"
    "3f040000430400002e0400001a4b1b49"
    "581800681a4908401a4988421fd10820"
    "204000281bd0184a9918012008701748"
    "1b181968164a89180878102210430870"
    "19681348091808782022104308707ff0"
    "4df814209bf07efa32209bf0ebfa0d49"
    "05480d4a801800788000401800689ef0"
    "35f870bc01bc004740230003b8560000"
    "00ffff0000010200830800009c550000"
    "2e04000058400d08b956000000b50649"
)

# Screen and grid settings, purrr
# Total bytes = 768. 768 / 3 bytes per color = 256 colors.
# A 16x16 grid has 256 cells. Perfect match, meow!
GRID_WIDTH = 16
GRID_HEIGHT = 16
BLOCK_SIZE = 30  # Size of each colored block in pixels, nya~
SCREEN_WIDTH = GRID_WIDTH * BLOCK_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * BLOCK_SIZE
FPS = 60

# Colors
BLACK = (0, 0, 0)
DEFAULT_COLOR = (50, 50, 50) # Fallback if data runs out early, nya

def hex_to_bytes(hex_string):
    """Converts a string of hex characters into a list of byte values (0-255), purrr."""
    # Remove any spaces or newlines just in case, nya~
    hex_string = "".join(hex_string.split())
    if len(hex_string) % 2 != 0:
        print("Warning: Hex string has an odd number of characters! Truncating last char, meow.")
        hex_string = hex_string[:-1]
    
    byte_values = []
    for i in range(0, len(hex_string), 2):
        byte = hex_string[i:i+2]
        try:
            byte_values.append(int(byte, 16))
        except ValueError:
            print(f"Warning: Could not convert '{byte}' to int. Using 0 instead, meow.")
            byte_values.append(0) # Default to 0 if a byte is weird
    return byte_values

def main():
    """Meow! This is the main function, where all the Pygame magic happens!"""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("CATSDK's Super Fucking Hex Ripper Visualizer DX - Meooow!")
    clock = pygame.time.Clock()

    byte_data = hex_to_bytes(HEX_DATA)
    print(f"Nyah! Converted hex to {len(byte_data)} bytes of raw fucking data!")

    # Pre-calculate colors to avoid doing it in the loop, purrr...
    colors = []
    byte_idx = 0
    num_expected_colors = GRID_WIDTH * GRID_HEIGHT
    
    # Let's skip the initial hash-like data and the "SUPER MARIO" string for coloring.
    # The "SUPER MARIOBAA2E" string is 16 bytes. The initial hashes are 10 lines * 16 bytes/line = 160 bytes.
    # "5355504552204d4152494f4241413245" starts at index 10*16 = 160
    # Let's start data processing for colors after "SUPER MARIOBAA2E" and the next line.
    # Offset = (10 lines hashes + 1 line SUPERMARIO + 1 line "3031...") * 16 bytes/line
    # Offset = (10 + 1 + 1) * 16 = 12 * 16 = 192 bytes from the start of total hex.
    # The full HEX_DATA string has all lines concatenated.
    # Each line is 32 hex chars = 16 bytes.
    # "2e00..." is line 0
    # ...
    # "87f0..." is line 9
    # "5355..." is line 10 (SUPER MARIOBAA2E)
    # "3031..." is line 11
    # Data for drawing starts from line 12: "1200a0e3..."
    
    start_byte_for_drawing = 12 * 16 # Start after the first 12 lines (0-11) of 16 bytes each
    
    if len(byte_data) < start_byte_for_drawing + num_expected_colors * 3:
        print("Warning: Not enough fucking byte data for all cells after offset! Some cells might use default color, nya.")

    for i in range(num_expected_colors):
        color_byte_idx = start_byte_for_drawing + (i * 3)
        if color_byte_idx + 2 < len(byte_data):
            r = byte_data[color_byte_idx]
            g = byte_data[color_byte_idx + 1]
            b = byte_data[color_byte_idx + 2]
            colors.append((r, g, b))
        else:
            colors.append(DEFAULT_COLOR) # Not enough data, use a default purr

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        screen.fill(BLACK) # Black background, like the void, meow

        # Draw the grid of colored blocks
        color_idx = 0
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if color_idx < len(colors):
                    color = colors[color_idx]
                else:
                    color = DEFAULT_COLOR # Should not happen if pre-calculation is correct
                
                rect = pygame.Rect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
                pygame.draw.rect(screen, color, rect)
                # Optional: draw a border for each block
                # pygame.draw.rect(screen, (50,50,50), rect, 1) 
                color_idx += 1
        
        pygame.display.flip() # Update the full screen, nya~
        clock.tick(FPS) # Keep it smooth, purrrr

    pygame.quit()
    print("Nyah! Pygame quit. Hope you enjoyed the fucking show, bastard!")
    sys.exit()

if __name__ == '__main__':
    main()

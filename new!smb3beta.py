import pygame
import platform
import asyncio

# Hex data from the ROM
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
    "5355504552204d4152494f4241413245"
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

# Screen and grid settings
GRID_WIDTH = 16
GRID_HEIGHT = 16
BLOCK_SIZE = 30
SCREEN_WIDTH = GRID_WIDTH * BLOCK_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * BLOCK_SIZE
FPS = 60

# Colors
BLACK = (0, 0, 0)
DEFAULT_COLOR = (50, 50, 50)

# Player settings
PLAYER_WIDTH = 20
PLAYER_HEIGHT = 20
GRAVITY = 1
JUMP_STRENGTH = -15
MOVE_SPEED = 5

# Global variables
screen = None
clock = None
byte_data = None
colors = []
level_grid = []
player_x = 0
player_y = 0
player_vx = 0
player_vy = 0
is_on_ground = False
running = True

def hex_to_bytes(hex_string):
    hex_string = "".join(hex_string.split())
    if len(hex_string) % 2 != 0:
        print("Warning: Hex string has an odd number of characters! Truncating last char.")
        hex_string = hex_string[:-1]
    byte_values = []
    for i in range(0, len(hex_string), 2):
        byte = hex_string[i:i+2]
        try:
            byte_values.append(int(byte, 16))
        except ValueError:
            print(f"Warning: Could not convert '{byte}' to int. Using 0 instead.")
            byte_values.append(0)
    return byte_values

def setup():
    global screen, clock, byte_data, colors, level_grid, player_x, player_y
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Hex Data Platformer Game")
    clock = pygame.time.Clock()

    byte_data = hex_to_bytes(HEX_DATA)
    print(f"Converted hex to {len(byte_data)} bytes of data.")

    start_byte_for_drawing = 12 * 16
    for i in range(GRID_WIDTH * GRID_HEIGHT):
        color_byte_idx = start_byte_for_drawing + (i * 3)
        if color_byte_idx + 2 < len(byte_data):
            r = byte_data[color_byte_idx]
            g = byte_data[color_byte_idx + 1]
            b = byte_data[color_byte_idx + 2]
            colors.append((r, g, b))
        else:
            colors.append(DEFAULT_COLOR)

    level_grid = [[False for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            color = colors[y * GRID_WIDTH + x]
            if color[0] > 100:
                level_grid[y][x] = True

    player_x = 0
    player_y = 0

def get_intersecting_blocks(x, y, width, height):
    intersecting = []
    left = int(x // BLOCK_SIZE)
    right = int((x + width - 1) // BLOCK_SIZE)
    top = int(y // BLOCK_SIZE)
    bottom = int((y + height - 1) // BLOCK_SIZE)
    for gy in range(top, bottom + 1):
        for gx in range(left, right + 1):
            if 0 <= gx < GRID_WIDTH and 0 <= gy < GRID_HEIGHT:
                if level_grid[gy][gx]:
                    intersecting.append((gx, gy))
    return intersecting

def update_loop():
    global player_x, player_y, player_vx, player_vy, is_on_ground, running
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        player_vx = -MOVE_SPEED
    elif keys[pygame.K_RIGHT]:
        player_vx = MOVE_SPEED
    else:
        player_vx = 0
    if keys[pygame.K_SPACE] and is_on_ground:
        player_vy = JUMP_STRENGTH
        is_on_ground = False

    player_vy += GRAVITY

    player_x += player_vx
    intersecting_blocks = get_intersecting_blocks(player_x, player_y, PLAYER_WIDTH, PLAYER_HEIGHT)
    for block in intersecting_blocks:
        block_rect = pygame.Rect(block[0] * BLOCK_SIZE, block[1] * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
        player_rect = pygame.Rect(player_x, player_y, PLAYER_WIDTH, PLAYER_HEIGHT)
        if player_vx > 0:
            overlap = player_rect.right - block_rect.left
            if overlap > 0:
                player_x -= overlap
        elif player_vx < 0:
            overlap = block_rect.right - player_rect.left
            if overlap > 0:
                player_x += overlap

    player_y += player_vy
    intersecting_blocks = get_intersecting_blocks(player_x, player_y, PLAYER_WIDTH, PLAYER_HEIGHT)
    for block in intersecting_blocks:
        block_rect = pygame.Rect(block[0] * BLOCK_SIZE, block[1] * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
        player_rect = pygame.Rect(player_x, player_y, PLAYER_WIDTH, PLAYER_HEIGHT)
        if player_vy > 0:
            overlap = player_rect.bottom - block_rect.top
            if overlap > 0:
                player_y -= overlap
                player_vy = 0
                is_on_ground = True
        elif player_vy < 0:
            overlap = block_rect.bottom - player_rect.top
            if overlap > 0:
                player_y += overlap
                player_vy = 0

    if player_x < 0:
        player_x = 0
    elif player_x > SCREEN_WIDTH - PLAYER_WIDTH:
        player_x = SCREEN_WIDTH - PLAYER_WIDTH
    if player_y < 0:
        player_y = 0
    elif player_y > SCREEN_HEIGHT - PLAYER_HEIGHT:
        player_y = SCREEN_HEIGHT - PLAYER_HEIGHT
        player_vy = 0
        is_on_ground = True

    screen.fill(BLACK)
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            color = colors[y * GRID_WIDTH + x]
            rect = pygame.Rect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
            pygame.draw.rect(screen, color, rect)
    player_rect = pygame.Rect(player_x, player_y, PLAYER_WIDTH, PLAYER_HEIGHT)
    pygame.draw.rect(screen, (255, 255, 255), player_rect)
    pygame.display.flip()
    clock.tick(FPS)

async def main():
    setup()
    while running:
        update_loop()
        await asyncio.sleep(1.0 / FPS)

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())

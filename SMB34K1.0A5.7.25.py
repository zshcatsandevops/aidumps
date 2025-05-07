import pygame
import numpy as np
import random
import asyncio
import platform

# Initialize Pygame
pygame.init()

# --- Game Constants ---
WIDTH, HEIGHT = 800, 600
FPS = 60
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ROM-Data Platformer Adventure, Meow!")
CLOCK = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PINK_PLAYER = (255, 105, 180)  # Cute pink for the player
GREEN_PLATFORM = (0, 200, 0)
BLUE_SKY = (135, 206, 235)

# Player properties
PLAYER_ACC = 0.7
PLAYER_FRICTION = -0.12
PLAYER_GRAVITY = 0.7
PLAYER_JUMP_STRENGTH = -15  # Negative because Pygame Y-axis is inverted

# Tile properties for level generation
TILE_SIZE = 32
LEVEL_CHUNK_WIDTH_TILES = 100  # How many tiles wide is a chunk of our level from ROM
LEVEL_CHUNK_HEIGHT_TILES = 20  # How many tiles high

# --- Simulate ROM data (16MB, typical GBA ROM size) ---
ROM_SIZE = 16 * 1024 * 1024  # 16MB in bytes
probability_platform = 0.2
rom_data_list = []
for _ in range(ROM_SIZE):
    if random.random() < probability_platform:
        rom_data_list.append(1)  # Platform byte
    else:
        rom_data_list.append(0)  # Empty space byte
rom_data = np.array(rom_data_list, dtype=np.uint8)

# --- Player Class ---
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.surf = pygame.Surface((TILE_SIZE // 2 + 10, TILE_SIZE + 10))
        self.surf.fill(PINK_PLAYER)
        self.rect = self.surf.get_rect(midbottom=(WIDTH / 4, HEIGHT - TILE_SIZE))
        self.pos = pygame.math.Vector2(self.rect.midbottom)
        self.vel = pygame.math.Vector2(0, 0)
        self.acc = pygame.math.Vector2(0, 0)
        self.on_ground = False
        self.jumps_made = 0
        self.max_jumps = 2  # Allow double jump

    def move(self):
        self.acc = pygame.math.Vector2(0, PLAYER_GRAVITY)  # Apply gravity

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.acc.x = -PLAYER_ACC
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.acc.x = PLAYER_ACC

        # Apply friction
        self.acc.x += self.vel.x * PLAYER_FRICTION
        # Update velocity
        self.vel += self.acc
        # Cap horizontal speed
        if abs(self.vel.x) > 7:
            self.vel.x = 7 if self.vel.x > 0 else -7
        if abs(self.vel.x) < 0.1:
            self.vel.x = 0

        self.pos += self.vel + 0.5 * self.acc  # Update position
        self.rect.midbottom = (self.pos.x, self.pos.y)  # Update rect

    def jump(self):
        if self.on_ground or self.jumps_made < self.max_jumps:
            self.vel.y = PLAYER_JUMP_STRENGTH
            self.on_ground = False
            self.jumps_made += 1

    def draw(self, surface, camera_offset_x):
        draw_rect = self.rect.copy()
        draw_rect.x -= camera_offset_x
        surface.blit(self.surf, draw_rect)

# --- Platform Class ---
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.surf = pygame.Surface((w, h))
        self.surf.fill(GREEN_PLATFORM)
        self.rect = self.surf.get_rect(topleft=(x, y))

    def draw(self, surface, camera_offset_x):
        draw_rect = self.rect.copy()
        draw_rect.x -= camera_offset_x
        if draw_rect.right > 0 and draw_rect.left < WIDTH:
            surface.blit(self.surf, draw_rect)

# --- Level Generation from ROM data ---
def generate_level_from_rom(rom_slice, tile_size, chunk_width_tiles, chunk_height_tiles):
    platforms = pygame.sprite.Group()
    print(f"Purr... Interpreting {len(rom_slice)} bytes for a {chunk_width_tiles}x{chunk_height_tiles} tile level, meow!")
    for y_tile in range(chunk_height_tiles):
        for x_tile in range(chunk_width_tiles):
            rom_idx = y_tile * chunk_width_tiles + x_tile
            if rom_idx < len(rom_slice):
                byte_val = rom_slice[rom_idx]
                if byte_val == 1:  # Platform tile
                    plat_x = x_tile * tile_size
                    plat_y = y_tile * tile_size
                    platform = Platform(plat_x, plat_y, tile_size, tile_size)
                    platforms.add(platform)
            else:
                print(f"Meow! Ran out of ROM data at tile ({x_tile}, {y_tile})")
                return platforms
    print(f"Purr! Generated {len(platforms)} platforms, amazing, nyah!")
    return platforms

# --- Game Setup ---
def setup():
    global player, all_sprites, level_platforms, camera_offset_x
    player = Player()
    all_sprites = pygame.sprite.Group()
    all_sprites.add(player)

    rom_slice_size = LEVEL_CHUNK_WIDTH_TILES * LEVEL_CHUNK_HEIGHT_TILES
    if rom_slice_size > ROM_SIZE:
        print(f"Meow! Warning! Requested ROM slice ({rom_slice_size} bytes) is bigger than total ROM size ({ROM_SIZE} bytes).")
        rom_slice_size = ROM_SIZE

    current_rom_offset = 0
    level_platforms = generate_level_from_rom(rom_data[current_rom_offset: current_rom_offset + rom_slice_size],
                                              TILE_SIZE,
                                              LEVEL_CHUNK_WIDTH_TILES,
                                              LEVEL_CHUNK_HEIGHT_TILES)
    all_sprites.add(level_platforms)
    camera_offset_x = 0

# --- Update Loop ---
def update_loop():
    global running, camera_offset_x # Added running to global for modification in event loop

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            # nonlocal running # 'running' is global, not nonlocal here
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_SPACE, pygame.K_UP, pygame.K_w]:
                player.jump()
            if event.key == pygame.K_ESCAPE:
                # nonlocal running # 'running' is global, not nonlocal here
                running = False

    # Update player movement
    player.move()

    # Horizontal collision
    player.rect.x += round(player.vel.x) # Use round for potentially fractional velocities before collision check
    horizontal_hits = pygame.sprite.spritecollide(player, level_platforms, False)
    for hit in horizontal_hits:
        if player.vel.x > 0:
            player.rect.right = hit.rect.left
        elif player.vel.x < 0:
            player.rect.left = hit.rect.right
        player.pos.x = player.rect.midbottom[0] # Update pos.x from rect.midbottom[0] or rect.centerx
        player.vel.x = 0

    # Vertical collision
    player.rect.y += round(player.vel.y) # Use round for potentially fractional velocities
    player.on_ground = False # Assume not on ground until collision proves otherwise
    vertical_hits = pygame.sprite.spritecollide(player, level_platforms, False)
    for hit in vertical_hits:
        if player.vel.y > 0: # Moving down
            player.rect.bottom = hit.rect.top
            player.on_ground = True
            player.jumps_made = 0
            player.vel.y = 0
        elif player.vel.y < 0: # Moving up
            player.rect.top = hit.rect.bottom
            player.vel.y = 0
        # Update player.pos.y based on collision corrected rect.bottom
        # This ensures pos vector is in sync with the rect after collision
        player.pos.y = player.rect.bottom


    # Update camera
    target_camera_x = player.pos.x - WIDTH / 3
    # Smooth camera movement
    camera_offset_x += (target_camera_x - camera_offset_x) * 0.1 # Adjust 0.1 for different smoothing
    # Clamp camera
    if camera_offset_x < 0:
        camera_offset_x = 0
    level_pixel_width = LEVEL_CHUNK_WIDTH_TILES * TILE_SIZE
    if camera_offset_x > level_pixel_width - WIDTH:
        camera_offset_x = max(0, level_pixel_width - WIDTH) # Ensure not negative if level is smaller than screen

    # Render
    SCREEN.fill(BLUE_SKY)
    for plat in level_platforms:
        plat.draw(SCREEN, camera_offset_x)
    player.draw(SCREEN, camera_offset_x)
    pygame.display.flip()
    CLOCK.tick(FPS) # Ensure clock ticks in the update loop

# --- Main Async Loop for Pyodide Compatibility ---
async def main():
    setup()
    global running # Declare running as global to be used in update_loop
    running = True
    while running:
        update_loop()
        #CLOCK.tick(FPS) # Moved CLOCK.tick to update_loop
        await asyncio.sleep(0) # Use asyncio.sleep(0) for pyodide to yield control

if platform.system() == "Emscripten":
    asyncio.run(main()) # For Pyodide, ensure_future might be better if main is already an async task
else:
    if __name__ == "__main__":
        # For desktop, Pygame's own loop management is usually sufficient without asyncio
        # but to keep the async structure for compatibility:
        setup()
        running = True
        while running:
            update_loop()
            # If not using asyncio.sleep in update_loop for desktop, ensure events are processed
            # and game doesn't run too fast (CLOCK.tick handles this)

        pygame.quit() # Quit pygame when loop finishes
        print("Meow! Game Over, you rockstar! Hope you enjoyed this ROM-fueled adventure, nyah!")

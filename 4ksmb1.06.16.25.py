import asyncio
import platform
import pygame
from pygame.locals import *

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 16
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Super Mario Bros")

# Colors
BACKGROUND_COLOR = (135, 206, 235)  # Light blue
MARIO_COLOR = (255, 0, 0)  # Red

# Tile color mappings
TILE_COLORS = {
    'X': (0, 255, 0),  # Solid ground (green)
    '?': (255, 255, 0),  # Question block (yellow)
    'B': (165, 42, 42),  # Brick (brown)
    'P': (0, 128, 0),  # Pipe (dark green)
    'F': (255, 255, 255),  # Flagpole (white)
    '-': BACKGROUND_COLOR  # Empty space
}

# Frame rate
FPS = 60

# Load level from text file
def load_level(file_path):
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        level = [list(line.strip()) for line in lines if line.strip()]
        return level
    except:
        # Fallback level if file not found
        return [
            list('-' * 50),
            list('-' * 50),
            list('-' * 50),
            list('-' * 50),
            list('-' * 50),
            list('-' * 50),
            list('-' * 50),
            list('-' * 50),
            list('-' * 50),
            list('-' * 50),
            list('-' * 50),
            list('-' * 50),
            list('M' + '-' * 49),
            list('X' * 50),
            list('X' * 50)
        ]

# Mario class
class Mario(pygame.sprite.Sprite):
    def __init__(self, x, y, platforms):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill(MARIO_COLOR)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.platforms = platforms

    def update(self):
        # Apply gravity
        self.vy += 0.5
        # Horizontal movement
        self.rect.x += self.vx
        for platform in self.platforms:
            if self.rect.colliderect(platform.rect):
                if self.vx > 0:
                    self.rect.right = platform.rect.left
                elif self.vx < 0:
                    self.rect.left = platform.rect.right
        # Vertical movement
        previous_bottom = self.rect.bottom
        self.rect.y += self.vy
        self.on_ground = False
        for platform in self.platforms:
            if self.rect.colliderect(platform.rect):
                if self.vy > 0 and previous_bottom <= platform.rect.top:
                    self.rect.bottom = platform.rect.top
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:
                    self.rect.top = platform.rect.bottom
                    self.vy = 0
        # Keep Mario within screen bounds horizontally
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

# Platform class
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, tile_type):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(TILE_COLORS.get(tile_type, (0, 0, 0)))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

# Setup function to initialize the game
def setup(level_number):
    global platforms, mario, all_sprites, level_width
    # Load level
    level_file = f"level{(level_number // 4) + 1}-{(level_number % 4) + 1}.txt"
    level = load_level(level_file)
    platforms = pygame.sprite.Group()
    mario = None
    # Parse level grid
    for y in range(len(level)):
        for x in range(len(level[y])):
            char = level[y][x]
            if char == 'M':
                mario = Mario(x * TILE_SIZE, y * TILE_SIZE, platforms)
            elif char in TILE_COLORS and char != '-':
                platform = Platform(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE, char)
                platforms.add(platform)
    # Default Mario position if not found
    if mario is None:
        mario = Mario(100, 560, platforms)
    # All sprites group
    all_sprites = pygame.sprite.Group()
    all_sprites.add(mario)
    all_sprites.add(platforms)
    # Calculate level width
    level_width = len(level[0]) * TILE_SIZE

# Update loop for game logic
def update_loop():
    global camera_x
    for event in pygame.event.get():
        if event.type == QUIT:
            if platform.system() != "Emscripten":
                pygame.quit()
                exit()
        elif event.type == KEYDOWN:
            if event.key == K_SPACE and mario.on_ground:
                mario.vy = -15  # Jump
    # Handle horizontal movement
    keys = pygame.key.get_pressed()
    if keys[K_LEFT]:
        mario.vx = -5
    elif keys[K_RIGHT]:
        mario.vx = 5
    else:
        mario.vx = 0
    # Update all sprites
    all_sprites.update()
    # Update camera
    camera_x = max(0, min(mario.rect.x - SCREEN_WIDTH // 2, level_width - SCREEN_WIDTH))
    # Draw
    screen.fill(BACKGROUND_COLOR)
    for sprite in all_sprites:
        screen.blit(sprite.image, (sprite.rect.x - camera_x, sprite.rect.y))
    pygame.display.flip()

# Main async function for Pyodide compatibility
async def main():
    setup(0)  # Start with level 1-1
    while True:
        update_loop()
        await asyncio.sleep(1.0 / FPS)

# Run the game based on platform
if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())

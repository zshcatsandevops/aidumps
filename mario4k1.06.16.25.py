import asyncio
import platform
import pygame
from pygame.locals import *

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Super Mario Bros")

# Colors
BACKGROUND_COLOR = (135, 206, 235)  # Light blue
MARIO_COLOR = (255, 0, 0)  # Red
PLATFORM_COLOR = (0, 255, 0)  # Green

# Frame rate
FPS = 60

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
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(PLATFORM_COLOR)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self):
        pass  # Platforms don't move

# Setup function to initialize the game
def setup():
    global platforms, mario, all_sprites
    # Create platforms
    platforms = pygame.sprite.Group()
    ground = Platform(0, 580, 800, 20)
    platform1 = Platform(200, 400, 100, 20)
    platform2 = Platform(500, 300, 100, 20)
    platforms.add(ground, platform1, platform2)

    # Create Mario
    mario = Mario(100, 560, platforms)

    # All sprites group
    all_sprites = pygame.sprite.Group()
    all_sprites.add(mario)
    all_sprites.add(platforms)

# Update loop for game logic
def update_loop():
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

    # Draw
    screen.fill(BACKGROUND_COLOR)
    all_sprites.draw(screen)
    pygame.display.flip()

# Main async function for Pyodide compatibility
async def main():
    setup()
    while True:
        update_loop()
        await asyncio.sleep(1.0 / FPS)

# Run the game based on platform
if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())

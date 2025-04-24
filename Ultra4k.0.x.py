import pygame
import asyncio
import platform

# Initialize Pygame
pygame.init()

# Set up the display (NES resolution: 256x240)
SCREEN_WIDTH = 256
SCREEN_HEIGHT = 240
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("NES Assembly to Pygame Platformer")

# Colors
SKY_BLUE = (135, 206, 235)
RED = (255, 0, 0)
GROUND_COLOR = (139, 69, 19)  # Brown for ground tiles
BLOCK_COLOR = (128, 128, 128)  # Gray for block tiles
ENEMY_COLOR = (165, 42, 42)  # Dark red for enemies

# Game constants
TILE_SIZE = 16
PLAYER_SIZE = 16
ENEMY_SIZE = 16
GRAVITY = 0.2
JUMP_VELOCITY = -5
MOVE_SPEED = 2
FPS = 60

# Simple tilemap (0 = empty, 1 = ground, 2 = block)
tilemap = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],  # Ground
]

# Player class
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vy = 0
        self.on_ground = False

    def update(self, keys):
        # Horizontal movement
        if keys[pygame.K_LEFT]:
            self.x -= MOVE_SPEED
        if keys[pygame.K_RIGHT]:
            self.x += MOVE_SPEED

        # Jumping
        if keys[pygame.K_UP] and self.on_ground:
            self.vy = JUMP_VELOCITY
            self.on_ground = False

        # Apply gravity
        self.vy += GRAVITY
        self.y += self.vy

        # Collision detection with tiles
        self.check_collisions()

        # Keep player within screen bounds
        if self.x < 0:
            self.x = 0
        if self.x > SCREEN_WIDTH - PLAYER_SIZE:
            self.x = SCREEN_WIDTH - PLAYER_SIZE

    def check_collisions(self):
        player_rect = pygame.Rect(self.x, self.y, PLAYER_SIZE, PLAYER_SIZE)
        for y in range(len(tilemap)):
            for x in range(len(tilemap[y])):
                if tilemap[y][x] in [1, 2]:  # Solid tiles
                    tile_rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    if player_rect.colliderect(tile_rect):
                        # Collision from below (landing)
                        if self.vy > 0 and player_rect.bottom > tile_rect.top:
                            self.y = tile_rect.top - PLAYER_SIZE
                            self.vy = 0
                            self.on_ground = True
                        # Collision from above (hitting head)
                        elif self.vy < 0 and player_rect.top < tile_rect.bottom:
                            self.y = tile_rect.bottom
                            self.vy = 0

    def draw(self):
        pygame.draw.rect(screen, RED, (self.x, self.y, PLAYER_SIZE, PLAYER_SIZE))

# Enemy class
class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 1  # Move right initially

    def update(self):
        self.x += self.vx
        # Reverse direction at screen edges
        if self.x < 0 or self.x > SCREEN_WIDTH - ENEMY_SIZE:
            self.vx = -self.vx

    def draw(self):
        # Draw enemy body as a circle
        pygame.draw.circle(screen, ENEMY_COLOR, (int(self.x + ENEMY_SIZE / 2), int(self.y + ENEMY_SIZE / 2)), ENEMY_SIZE // 2)
        # Add eyes
        eye_color = (255, 255, 255)  # White
        pupil_color = (0, 0, 0)  # Black
        eye_radius = 3
        pupil_radius = 1
        # Left eye
        left_eye_x = int(self.x + ENEMY_SIZE / 4)
        left_eye_y = int(self.y + ENEMY_SIZE / 3)
        pygame.draw.circle(screen, eye_color, (left_eye_x, left_eye_y), eye_radius)
        pygame.draw.circle(screen, pupil_color, (left_eye_x, left_eye_y), pupil_radius)
        # Right eye
        right_eye_x = int(self.x + 3 * ENEMY_SIZE / 4)
        right_eye_y = int(self.y + ENEMY_SIZE / 3)
        pygame.draw.circle(screen, eye_color, (right_eye_x, right_eye_y), eye_radius)
        pygame.draw.circle(screen, pupil_color, (right_eye_x, right_eye_y), pupil_radius)

# Function to draw tiles with patterns
def draw_tile(x, y, tile_type):
    if tile_type == 1:  # Ground
        # Draw brown rectangle
        pygame.draw.rect(screen, GROUND_COLOR, (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        # Add grass on top
        grass_color = (0, 255, 0)  # Green
        for i in range(0, TILE_SIZE, 2):
            pygame.draw.line(screen, grass_color, (x * TILE_SIZE + i, y * TILE_SIZE), (x * TILE_SIZE + i, y * TILE_SIZE + 2))
    elif tile_type == 2:  # Block
        # Draw gray rectangle
        pygame.draw.rect(screen, BLOCK_COLOR, (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        # Add brick pattern
        line_color = (100, 100, 100)  # Darker gray
        # Draw horizontal line at y=8
        pygame.draw.line(screen, line_color, (x * TILE_SIZE, y * TILE_SIZE + 8), (x * TILE_SIZE + TILE_SIZE, y * TILE_SIZE + 8))
        # Draw vertical lines at x=4 and x=12
        pygame.draw.line(screen, line_color, (x * TILE_SIZE + 4, y * TILE_SIZE), (x * TILE_SIZE + 4, y * TILE_SIZE + TILE_SIZE))
        pygame.draw.line(screen, line_color, (x * TILE_SIZE + 12, y * TILE_SIZE), (x * TILE_SIZE + 12, y * TILE_SIZE + TILE_SIZE))

# Initialize game objects
player = Player(100, 100)
enemies = [Enemy(150, 200), Enemy(200, 200)]

# Game loop functions
def setup():
    pass  # Initialization already done above

async def update_loop():
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False

    # Get keyboard input
    keys = pygame.key.get_pressed()

    # Update game state
    player.update(keys)
    for enemy in enemies:
        enemy.update()

    # Draw everything
    screen.fill(SKY_BLUE)  # Fill with sky blue background

    # Draw tilemap with patterns
    for y in range(len(tilemap)):
        for x in range(len(tilemap[y])):
            if tilemap[y][x] != 0:
                draw_tile(x, y, tilemap[y][x])

    # Draw player and enemies
    player.draw()
    for enemy in enemies:
        enemy.draw()

    # Update display
    pygame.display.flip()
    return True

# Main async loop for Pyodide compatibility
async def main():
    setup()
    running = True
    while running:
        running = await update_loop()
        await asyncio.sleep(1.0 / FPS)  # Control frame rate

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())

import pygame

# Initialize Pygame
pygame.init()

# Set up the display (NES resolution: 256x240)
SCREEN_WIDTH = 256
SCREEN_HEIGHT = 240
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("NES Assembly to Pygame Platformer")

# Colors
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BROWN = (139, 69, 19)
GRAY = (128, 128, 128)

# Game constants
TILE_SIZE = 16
PLAYER_SIZE = 16
ENEMY_SIZE = 16
GRAVITY = 0.2
JUMP_VELOCITY = -5
MOVE_SPEED = 2

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
        pygame.draw.rect(screen, BROWN, (self.x, self.y, ENEMY_SIZE, ENEMY_SIZE))

# Initialize game objects
player = Player(100, 100)
enemies = [Enemy(150, 200), Enemy(200, 200)]

# Clock for 60 FPS
clock = pygame.time.Clock()

# Main game loop
running = True
while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Get keyboard input
    keys = pygame.key.get_pressed()

    # Update game state
    player.update(keys)
    for enemy in enemies:
        enemy.update()

    # Draw everything
    screen.fill(BLACK)  # Clear screen with black background

    # Draw tilemap
    for y in range(len(tilemap)):
        for x in range(len(tilemap[y])):
            if tilemap[y][x] == 1:  # Ground
                pygame.draw.rect(screen, GRAY, (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
            elif tilemap[y][x] == 2:  # Block
                pygame.draw.rect(screen, GRAY, (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))

    # Draw player and enemies
    player.draw()
    for enemy in enemies:
        enemy.draw()

    # Update display
    pygame.display.flip()

    # Cap frame rate at 60 FPS
    clock.tick(60)

# Quit Pygame
pygame.quit()

import pygame
import asyncio
import platform

# Initialize Pygame
pygame.init()

# Colors
BLACK = (0, 0, 0)      # Background
BLUE = (0, 0, 255)     # Platforms
RED = (255, 0, 0)      # Player (Mario)
BROWN = (139, 69, 19)  # Enemies (Goombas)
GREEN = (0, 255, 0)    # Power-ups (Mushrooms)
YELLOW = (255, 255, 0) # Coins
LIGHT_BLUE = (173, 216, 230)  # Menu/Control background
WHITE = (255, 255, 255)  # Text

# Window and level size (DS-like: 256x192 per screen)
WINDOW_WIDTH = 256
WINDOW_HEIGHT = 384  # 192 top + 192 bottom
LEVEL_WIDTH = 1600
LEVEL_HEIGHT = 192
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("NSMB DS-Inspired Pygame Tech Demo")

# Player constants
PLAYER_WIDTH = 16
PLAYER_HEIGHT = 16
PLAYER_GRAVITY = 0.35
PLAYER_JUMP = 10
PLAYER_ACCEL = 0.5
PLAYER_FRICTION = 0.2
PLAYER_WALK_SPEED = 3
PLAYER_RUN_SPEED = 5

# Enemy constants
ENEMY_WIDTH = 16
ENEMY_HEIGHT = 16
ENEMY_SPEED = 1

# Power-up and coin constants
ITEM_WIDTH = 16
ITEM_HEIGHT = 16

# Block constants
BLOCK_SIZE = 16

# Classes
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.size = 1  # 1 = small, 2 = super
        self.on_ground = False

    def update(self, keys):
        # Running or walking
        max_speed = PLAYER_RUN_SPEED if keys[pygame.K_LSHIFT] else PLAYER_WALK_SPEED
        if keys[pygame.K_LEFT]:
            self.vx = max(self.vx - PLAYER_ACCEL, -max_speed)
        elif keys[pygame.K_RIGHT]:
            self.vx = min(self.vx + PLAYER_ACCEL, max_speed)
        else:
            if self.vx > 0:
                self.vx = max(self.vx - PLAYER_FRICTION, 0)
            elif self.vx < 0:
                self.vx = min(self.vx + PLAYER_FRICTION, 0)

        # Apply gravity
        if not self.on_ground:
            self.vy += PLAYER_GRAVITY

        # Update position
        self.x += self.vx
        self.y += self.vy

        # Boundaries
        w = PLAYER_WIDTH * self.size
        if self.x < 0:
            self.x = 0
            self.vx = 0
        elif self.x > LEVEL_WIDTH - w:
            self.x = LEVEL_WIDTH - w
            self.vx = 0

    def get_rect(self):
        return pygame.Rect(self.x, self.y, PLAYER_WIDTH * self.size, PLAYER_HEIGHT * self.size)

    def draw(self, screen, offset):
        w = PLAYER_WIDTH * self.size
        h = PLAYER_HEIGHT * self.size
        pygame.draw.rect(screen, RED, (self.x - offset, self.y, w, h))

class Enemy:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.direction = direction

    def update(self):
        self.x += ENEMY_SPEED * self.direction
        if self.x <= 0 or self.x >= LEVEL_WIDTH - ENEMY_WIDTH:
            self.direction *= -1

    def get_rect(self):
        return pygame.Rect(self.x, self.y, ENEMY_WIDTH, ENEMY_HEIGHT)

    def draw(self, screen, offset):
        x = self.x - offset
        if 0 <= x <= WINDOW_WIDTH:
            pygame.draw.rect(screen, BROWN, (x, self.y, ENEMY_WIDTH, ENEMY_HEIGHT))

class Block:
    def __init__(self, x, y, type, item=None):
        self.x = x
        self.y = y
        self.type = type  # "question" or "brick"
        self.item = item  # "mushroom" or "coin" or None
        self.hit = False

    def get_rect(self):
        return pygame.Rect(self.x, self.y, BLOCK_SIZE, BLOCK_SIZE)

    def draw(self, screen, offset):
        x = self.x - offset
        if 0 <= x <= WINDOW_WIDTH:
            color = YELLOW if self.type == "question" else BROWN
            pygame.draw.rect(screen, color, (x, self.y, BLOCK_SIZE, BLOCK_SIZE))

# Level data (inspired by NSMB World 1-1)
platforms = [
    pygame.Rect(0, 172, LEVEL_WIDTH, 20),         # Ground
    pygame.Rect(200, 120, 100, 8),                # Platform 1
    pygame.Rect(400, 80, 150, 8),                 # Platform 2
    pygame.Rect(700, 100, 100, 8),                # Platform 3
    pygame.Rect(1000, 60, 200, 8),                # High platform
]

blocks = [
    Block(250, 80, "question", "mushroom"),       # Mushroom block
    Block(450, 40, "question", "coin"),           # Coin block
    Block(750, 60, "brick"),                      # Brick block
]

enemies = [
    Enemy(300, 172 - ENEMY_HEIGHT, 1),           # Goomba 1
    Enemy(800, 172 - ENEMY_HEIGHT, -1),           # Goomba 2
]

items = []  # Dynamic items from blocks

# Game state
player = Player(100, 172 - PLAYER_HEIGHT)
camera_offset = 0
state = "menu"
score = 0
coins = 0

# Menu and HUD
font = pygame.font.SysFont("Arial", 16)
title_text = font.render("NSMB Pygame Demo", True, BLACK)
start_text = font.render("Start", True, BLACK)
jump_text = font.render("Jump", True, WHITE)
button_rect = pygame.Rect(78, 100, 100, 40)
jump_button_rect = pygame.Rect(50, 250, 156, 60)

def setup():
    global player, enemies, items, blocks, camera_offset, state, score, coins
    player = Player(100, 172 - PLAYER_HEIGHT)
    enemies = [
        Enemy(300, 172 - ENEMY_HEIGHT, 1),
        Enemy(800, 172 - ENEMY_HEIGHT, -1)
    ]
    items = []
    blocks = [
        Block(250, 80, "question", "mushroom"),
        Block(450, 40, "question", "coin"),
        Block(750, 60, "brick")
    ]

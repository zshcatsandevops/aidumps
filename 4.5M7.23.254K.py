import pygame
import sys
import random

# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
LEVEL_WIDTH = 5000
FPS = 60

GRAVITY = 0.8
JUMP_POWER = -16
PLAYER_ACCELERATION = 1.2
PLAYER_FRICTION = -0.12

# Colors
SKY_COLOR = (107, 140, 255)
GROUND_COLOR = (96, 56, 19)
COIN_COLOR = (255, 223, 0)
PLAYER_COLOR = (255, 50, 50)
ENEMY_COLOR = (255, 128, 0)

# Setup screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("New Super Mario Bros U Deluxe - Python Edition")
clock = pygame.time.Clock()

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((40, 60))
        self.image.fill(PLAYER_COLOR)
        self.rect = self.image.get_rect()
        self.pos = pygame.math.Vector2(100, SCREEN_HEIGHT - 300)
        self.vel = pygame.math.Vector2(0, 0)
        self.acc = pygame.math.Vector2(0, 0)
        self.on_ground = False

    def update(self):
        self.acc = pygame.math.Vector2(0, GRAVITY)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.acc.x = -PLAYER_ACCELERATION
        if keys[pygame.K_RIGHT]:
            self.acc.x = PLAYER_ACCELERATION
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vel.y = JUMP_POWER

        # Apply friction
        self.acc.x += self.vel.x * PLAYER_FRICTION
        self.vel += self.acc
        self.pos += self.vel + 0.5 * self.acc

        self.rect.midbottom = self.pos

# Platform class
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(GROUND_COLOR)
        self.rect = self.image.get_rect(topleft=(x, y))

# Level setup
platforms = pygame.sprite.Group()
platforms.add(Platform(0, SCREEN_HEIGHT - 50, LEVEL_WIDTH, 50))
for i in range(10):
    x = random.randint(200, LEVEL_WIDTH - 200)
    y = random.randint(300, SCREEN_HEIGHT - 150)
    platforms.add(Platform(x, y, 200, 30))

# Sprite groups
player = Player()
player_group = pygame.sprite.Group(player)

camera_offset = 0

# Main loop
running = True
while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    player.update()

    # Check collisions
    hits = pygame.sprite.spritecollide(player, platforms, False)
    if hits:
        player.pos.y = hits[0].rect.top + 1
        player.vel.y = 0
        player.on_ground = True
    else:
        player.on_ground = False

    # Camera follows player
    camera_offset = max(0, min(player.rect.centerx - SCREEN_WIDTH // 2, LEVEL_WIDTH - SCREEN_WIDTH))

    # Drawing
    screen.fill(SKY_COLOR)

    for platform in platforms:
        screen.blit(platform.image, (platform.rect.x - camera_offset, platform.rect.y))

    screen.blit(player.image, (player.rect.x - camera_offset, player.rect.y))

    pygame.display.flip()

pygame.quit()
sys.exit()

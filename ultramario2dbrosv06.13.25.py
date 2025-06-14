import asyncio
import platform
import pygame
import random

# Constants
WIDTH = 800
HEIGHT = 600
FPS = 60
PLAYER_SIZE = 30
PLATFORM_HEIGHT = 20
BG_COLOR = (135, 206, 250)  # Sky blue
PLAYER_COLOR = (255, 255, 0)  # Yellow
PLATFORM_COLOR = (0, 255, 0)  # Green
BASE_PLATFORM_COLOR = (255, 0, 0)  # Red

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Super Mario 2D World")
clock = pygame.time.Clock()

# Player setup
player = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE))
player.fill(PLAYER_COLOR)
player_rect = player.get_rect(center=(WIDTH // 2, HEIGHT - 50))
player_speed = 5
player_jump = -15
player_gravity = 0.8
player_velocity_y = 0
on_ground = False

# Platforms
platforms = []
base_platform = pygame.Surface((WIDTH, PLATFORM_HEIGHT))
base_platform.fill(BASE_PLATFORM_COLOR)
base_rect = base_platform.get_rect(bottom=HEIGHT)
platforms.append(base_rect)

# Game state
current_level = 1
running = True

def setup():
    global platforms, player_rect, player_velocity_y, on_ground
    # Reset player
    player_rect.center = (WIDTH // 2, HEIGHT - 50)
    player_velocity_y = 0
    on_ground = False
    # Define platforms for current level (example for level 1)
    platforms.clear()
    platforms.append(base_rect)
    # Add more platforms (example)
    plat1 = pygame.Surface((100, PLATFORM_HEIGHT))
    plat1.fill(PLATFORM_COLOR)
    plat1_rect = plat1.get_rect(topleft=(200, HEIGHT - 200))
    platforms.append(plat1_rect)

def update_loop():
    global running, player_rect, player_velocity_y, on_ground, current_level
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Player movement
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] and player_rect.left > 0:
        player_rect.x -= player_speed
    if keys[pygame.K_RIGHT] and player_rect.right < WIDTH:
        player_rect.x += player_speed
    if keys[pygame.K_SPACE] and on_ground:
        player_velocity_y = player_jump
        on_ground = False

    # Apply gravity
    player_velocity_y += player_gravity
    player_rect.y += player_velocity_y

    # Collision detection
    on_ground = False
    for plat in platforms:
        if player_rect.colliderect(plat) and player_velocity_y >= 0:
            if player_rect.bottom <= plat.bottom:
                player_rect.bottom = plat.top
                player_velocity_y = 0
                on_ground = True

    # Check if player falls off
    if player_rect.top > HEIGHT:
        setup()  # Reset level

    # Draw everything
    screen.fill(BG_COLOR)
    screen.blit(player, player_rect)
    screen.blit(base_platform, base_rect)
    for plat in platforms[1:]:
        plat_surf = pygame.Surface((plat.width, plat.height))
        plat_surf.fill(PLATFORM_COLOR)
        screen.blit(plat_surf, plat)

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

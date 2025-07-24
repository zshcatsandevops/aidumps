import pygame
import sys
import math

# Initialize Pygame
pygame.init()

# Atari-inspired palette
BLACK   = (  0,   0,   0)
WHITE   = (255, 255, 255)
RED     = (224,   0,   0)
GREEN   = (  0, 224,   0)
BLUE    = (  0,   0, 224)
YELLOW  = (224, 224,   0)
ORANGE  = (224, 112,   0)
GRAY    = (112, 112, 112)
DARKGRN = (  0, 112,   0)

# Screen settings
LOGICAL_W, LOGICAL_H = 160, 120
SCALE = 4
SCREEN = pygame.display.set_mode((LOGICAL_W * SCALE, LOGICAL_H * SCALE))
pygame.display.set_caption("GTA4 Vibes - Atari Edition")

# Map grid (20 x 15): 0=grass, 1=road
GRID_W, GRID_H = LOGICAL_W // 8, LOGICAL_H // 8
MAP = [[0]*GRID_W for _ in range(GRID_H)]
# Draw horizontal road across middle
for x in range(GRID_W): MAP[GRID_H//2][x] = 1
# Draw vertical road down center
for y in range(GRID_H): MAP[y][GRID_W//2] = 1

# Car parameters
tile = 8  # 8x8 pixels
car_surf = pygame.Surface((tile, tile))
car_surf.fill(RED)

car_x = LOGICAL_W//2
car_y = LOGICAL_H//2
angle = 0
speed = 0
max_speed = 2
accel = 0.05
friction = 0.02

clock = pygame.time.Clock()

# Main loop
while True:
    dt = clock.tick(60) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()
    # Steering
    if keys[pygame.K_LEFT]:
        angle += 100 * dt
    if keys[pygame.K_RIGHT]:
        angle -= 100 * dt
    # Acceleration
    if keys[pygame.K_UP]:
        speed = min(max_speed, speed + accel)
    elif keys[pygame.K_DOWN]:
        speed = max(-max_speed/2, speed - accel)
    else:
        # Apply friction
        if speed > 0:
            speed = max(0, speed - friction)
        elif speed < 0:
            speed = min(0, speed + friction)

    # Update car position
    rad = math.radians(angle)
    car_x += math.cos(rad) * speed
    car_y -= math.sin(rad) * speed
    # Boundaries
    car_x = max(0, min(LOGICAL_W - tile, car_x))
    car_y = max(0, min(LOGICAL_H - tile, car_y))

    # Draw scene to logical surface
    surf = pygame.Surface((LOGICAL_W, LOGICAL_H))
    # Draw map
    for y in range(GRID_H):
        for x in range(GRID_W):
            rect = pygame.Rect(x*tile, y*tile, tile, tile)
            if MAP[y][x] == 1:
                pygame.draw.rect(surf, GRAY, rect)
            else:
                pygame.draw.rect(surf, DARKGRN, rect)
    # Draw car
    rotated = pygame.transform.rotate(car_surf, angle)
    rrect = rotated.get_rect(center=(car_x + tile/2, car_y + tile/2))
    surf.blit(rotated, rrect)

    # Draw HUD (mini-map)
    hud = pygame.transform.scale(surf.subsurface((0,0,GRID_W*2,GRID_H*2)), (GRID_W*2, GRID_H*2))
    hud_rect = hud.get_rect(bottomright=(LOGICAL_W-2, LOGICAL_H-2))
    pygame.draw.rect(surf, BLACK, hud_rect.inflate(2,2))
    surf.blit(hud, hud_rect)

    # Scale up and blit to screen
    screen_scaled = pygame.transform.scale(surf, (LOGICAL_W * SCALE, LOGICAL_H * SCALE))
    SCREEN.blit(screen_scaled, (0,0))
    pygame.display.flip()

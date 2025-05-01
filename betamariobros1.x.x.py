import asyncio
import platform
import pygame

# Constants
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400
TILE_SIZE = 26
FPS = 60

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Super Mario Bros 1x")
clock = pygame.time.Clock()

# Level configuration
level_height = 15
level_width = 50
level = [[0]*level_width for _ in range(level_height - 1)] + [[1]*level_width]

# Add platforms and features
for i in range(10, 16):
    level[10][i] = 1
for i in range(20, 26):
    level[8][i] = 1
level[10][5] = 2  # Question block
level[8][15] = 2  # Question block

# Add a pit
for i in range(30, 35):
    level[level_height - 1][i] = 0

# Tile images setup
ground_img = pygame.Surface((TILE_SIZE, TILE_SIZE))
ground_img.fill((139, 69, 19))  # Brown color for ground
question_img = pygame.Surface((TILE_SIZE, TILE_SIZE))
question_img.fill((255, 255, 0))  # Yellow for question blocks
tile_images = {0: None, 1: ground_img, 2: question_img}

# Mario setup
mario_img = pygame.Surface((TILE_SIZE, TILE_SIZE))
mario_img.fill((255, 0, 0))  # Red color placeholder
mario_x = TILE_SIZE * 1
mario_y = (level_height - 2) * TILE_SIZE
vx, vy = 0, 0
on_ground = True
mario_rect = pygame.Rect(mario_x, mario_y, TILE_SIZE, TILE_SIZE)

# Enemies setup
goomba_img = pygame.Surface((TILE_SIZE, TILE_SIZE))
goomba_img.fill((165, 42, 42))  # Dark brown for Goombas
enemies = [
    {'x': 200, 'y': (level_height - 2) * TILE_SIZE, 'vx': -2, 'vy': 0,
     'on_ground': False, 'alive': True, 
     'rect': pygame.Rect(200, (level_height - 2) * TILE_SIZE, TILE_SIZE, TILE_SIZE)},
    {'x': 300, 'y': (level_height - 2) * TILE_SIZE, 'vx': -2, 'vy': 0,
     'on_ground': False, 'alive': True,
     'rect': pygame.Rect(300, (level_height - 2) * TILE_SIZE, TILE_SIZE, TILE_SIZE)}
]

# Camera setup
camera_x = 0

def get_nearby_tiles(rect):
    nearby = []
    left = max(0, int(rect.left // TILE_SIZE) - 1)
    right = min(level_width, int(rect.right // TILE_SIZE) + 2)
    top = max(0, int(rect.top // TILE_SIZE) - 1)
    bottom = min(level_height, int(rect.bottom // TILE_SIZE) + 2)
    
    for j in range(top, bottom):
        for i in range(left, right):
            if level[j][i] in [1, 2]:
                tile_rect = pygame.Rect(i * TILE_SIZE, j * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                nearby.append(tile_rect)
    return nearby

def update_loop():
    global mario_x, mario_y, vx, vy, on_ground, camera_x
    
    # Handle input
    keys = pygame.key.get_pressed()
    vx = 0
    if keys[pygame.K_LEFT]:
        vx = -5
    elif keys[pygame.K_RIGHT]:
        vx = 5
    if keys[pygame.K_SPACE] and on_ground:
        vy = -10
        on_ground = False

    # Apply physics
    vy += 0.5
    mario_x += vx
    mario_rect.x = int(mario_x)
    
    # Horizontal collisions
    nearby_tiles = get_nearby_tiles(mario_rect)
    for tile in nearby_tiles:
        if mario_rect.colliderect(tile):
            if vx > 0:
                mario_x = tile.left - mario_rect.width
            elif vx < 0:
                mario_x = tile.right
            mario_rect.x = int(mario_x)
            vx = 0

    # Vertical movement
    mario_y += vy
    mario_rect.y = int(mario_y)
    on_ground = False
    for tile in nearby_tiles:
        if mario_rect.colliderect(tile):
            if vy > 0:
                mario_y = tile.top - mario_rect.height
                on_ground = True
                vy = 0
            elif vy < 0:
                mario_y = tile.bottom
                vy = 0
            mario_rect.y = int(mario_y)

    # Enemy AI
    for enemy in enemies[:]:  # Iterate over a copy to allow removal
        if not enemy['alive']:
            continue
            
        enemy['vy'] += 0.5
        enemy['x'] += enemy['vx']
        enemy['rect'].x = int(enemy['x'])
        
        # Horizontal collisions
        nearby_enemy_tiles = get_nearby_tiles(enemy['rect'])
        for tile in nearby_enemy_tiles:
            if enemy['rect'].colliderect(tile):
                enemy['vx'] *= -1
                enemy['x'] += enemy['vx'] * 2
                enemy['rect'].x = int(enemy['x'])
                break
                
        # Vertical collisions
        enemy['y'] += enemy['vy']
        enemy['rect'].y = int(enemy['y'])
        enemy['on_ground'] = False
        for tile in nearby_enemy_tiles:
            if enemy['rect'].colliderect(tile):
                if enemy['vy'] > 0:
                    enemy['y'] = tile.top - enemy['rect'].height
                    enemy['on_ground'] = True
                    enemy['vy'] = 0
                elif enemy['vy'] < 0:
                    enemy['y'] = tile.bottom
                    enemy['vy'] = 0
                enemy['rect'].y = int(enemy['y'])
                break
                
        # Mario collision
        if enemy['alive'] and mario_rect.colliderect(enemy['rect']):
            if mario_rect.bottom <= enemy['rect'].top + 5:
                enemy['alive'] = False
                vy = -10
            else:
                mario_x, mario_y = TILE_SIZE, (level_height - 2) * TILE_SIZE
                vx = vy = 0
                mario_rect.topleft = (mario_x, mario_y)

    # Update camera
    camera_x = max(0, min(mario_x - SCREEN_WIDTH/2, level_width*TILE_SIZE - SCREEN_WIDTH))

    # Optimized rendering - only draw visible tiles
    screen.fill((135, 206, 235))
    start_x = max(0, int(camera_x // TILE_SIZE))
    end_x = min(level_width, int((camera_x + SCREEN_WIDTH) // TILE_SIZE) + 1)
    for j in range(level_height):
        for i in range(start_x, end_x):
            tile_type = level[j][i]
            if tile_type:
                screen.blit(tile_images[tile_type], 
                           (i * TILE_SIZE - camera_x, j * TILE_SIZE))
    
    # Draw entities
    for enemy in enemies:
        if enemy['alive']:
            screen.blit(goomba_img, (enemy['x'] - camera_x, enemy['y']))
    screen.blit(mario_img, (mario_x - camera_x, mario_y))
    pygame.display.flip()

async def async_main():
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        update_loop()
        clock.tick(FPS)
        await asyncio.sleep(0)

if platform.system() == "Emscripten":
    asyncio.ensure_future(async_main())
else:
    # Standard Pygame loop for non-Emscripten platforms
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        update_loop()
        clock.tick(FPS)
    pygame.quit()

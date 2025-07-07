import pygame, sys, math, random
pygame.init()

###############################################################################
# CONSTANTS & GLOBAL STATE
###############################################################################
FPS          = 60
TILE         = 32
W, H         = 20*TILE, 15*TILE
GRAVITY_AIR  = 0.75
GRAVITY_GND  = 2
MARIO_ACCEL  = 1.2
MARIO_FRIC_G = 0.84
MARIO_FRIC_A = 0.94
MARIO_JUMP_V = -13.5
BLOCK_SIZE   = 16
ITEM_SIZE    = 16

screen = pygame.display.set_mode((W, H))
clock  = pygame.time.Clock()

# ───────────────── Level layout (0 = air, 1 = solid) ────────────────────────
level = [[0]*20 for _ in range(15)]
for x in range(20):                                   # floor
    level[13][x] = 1
for x in range(5, 10):                                # mid-air platform
    level[10][x] = 1
for x in range(12, 17):                               # second platform
    level[8][x] = 1

# Grab-block platform (row 12, cols 7-14)
grab_blocks = []
for col in range(7, 15):
    grab_blocks.append({
        'x': col*TILE + (TILE-BLOCK_SIZE)//2,
        'y': 12*TILE + (TILE-BLOCK_SIZE)//2,
        'vx': 0.0, 'vy': 0.0,
        'grabbed': False
    })

# Item spawns (coins, mushrooms, fire flowers)
items = []
item_spawn_timer = 0
ITEM_SPAWN_INTERVAL = 180  # frames (~3 seconds)

# ────────────────── Mario state ──────────────────────────────────────────────
mario = {
    'x': 2*TILE, 'y': 11*TILE,
    'vx': 0.0,    'vy': 0.0,
    'w': 24,      'h': 32,
    'on_ground': False,
    'face': 1,    # 1 = right, –1 = left
    'carrying': None,
    'power': 'small'  # small, super, fire
}

# ────────────────── Big Boo state ────────────────────────────────────────────
boo = {
    'x': 14*TILE, 'y': 8.5*TILE,
    'vx': 0.0,    'w': 48,  'h': 48,
    'float_t': 0.0,
    'health': 5,  # Increased for longer fight
    'alpha': 255,
    'state': 'chase',  # chase, teleport, vulnerable
    'state_timer': 0,
    'teleport_x': 0,
    'teleport_y': 0
}

###############################################################################
# UTILITY HELPERS
###############################################################################
def tile_rect(i, j): return pygame.Rect(i*TILE, j*TILE, TILE, TILE)
def mario_rect():     return pygame.Rect(int(mario['x']), int(mario['y']), mario['w'], mario['h'])
def boo_rect():       return pygame.Rect(int(boo['x']),  int(boo['y']),  boo['w'],   boo['h'])
def block_rect(b):    return pygame.Rect(int(b['x']),   int(b['y']),    BLOCK_SIZE, BLOCK_SIZE)
def item_rect(i):     return pygame.Rect(int(i['x']),   int(i['y']),    ITEM_SIZE, ITEM_SIZE)

def solid_at(px, py):
    i, j = int(px)//TILE, int(py)//TILE
    return 0 <= i < 20 and 0 <= j < 15 and level[j][i] == 1

def collide_tile(px, py, w, h):
    for i in range(int(px)//TILE, int(px+w-1)//TILE+1):
        for j in range(int(py)//TILE, int(py+h-1)//TILE+1):
            if 0 <= i < 20 and 0 <= j < 15 and level[j][i]:
                return True
    return False

def spawn_item():
    x = random.randint(4, 16) * TILE
    y = random.randint(6, 10) * TILE
    if collide_tile(x, y, ITEM_SIZE, ITEM_SIZE):
        return
    item_type = random.choice(['coin', 'mushroom', 'fire_flower'])
    items.append({
        'x': x, 'y': y,
        'type': item_type
    })

###############################################################################
# DRAWING
###############################################################################
def draw_level():
    for j, row in enumerate(level):
        for i, t in enumerate(row):
            if t:
                pygame.draw.rect(screen, (70,180,255), tile_rect(i,j))

def draw_grab_blocks():
    for b in grab_blocks:
        if b['grabbed']: continue
        pygame.draw.rect(screen, (180,120,30), block_rect(b))
        pygame.draw.rect(screen, (230,180,80), block_rect(b), 2)

def draw_items():
    for item in items:
        if item['type'] == 'coin':
            pygame.draw.circle(screen, (255,215,0), (int(item['x'])+8, int(item['y'])+8), 8)
        elif item['type'] == 'mushroom':
            pygame.draw.rect(screen, (139,69,19), (int(item['x'])+2, int(item['y'])+8, 12, 8))
            pygame.draw.ellipse(screen, (255,0,0), (int(item['x']), int(item['y']), 16, 12))
        elif item['type'] == 'fire_flower':
            pygame.draw.circle(screen, (255,165,0), (int(item['x'])+8, int(item['y'])+8, 8))
            pygame.draw.circle(screen, (255,0,0), (int(item['x'])+8, int(item['y'])+8, 6))

def draw_mario():
    x, y = int(mario['x']), int(mario['y'])
    h = 48 if mario['power'] != 'small' else 32
    mario['h'] = h
    # body
    color = (60,80,200) if mario['power'] != 'fire' else (255,165,0)
    pygame.draw.rect(screen, color, (x+6,y+h-16,12,16), border_radius=5)
    # face
    pygame.draw.ellipse(screen, (255,226,185), (x+4,y+4,16,14))
    # hat
    hat_color = (220,0,0) if mario['power'] != 'fire' else (255,255,255)
    pygame.draw.ellipse(screen, hat_color, (x+5,y-4,14,8))
    # eyes
    pygame.draw.ellipse(screen, (0,0,0), (x+8,y+10,2,5))
    pygame.draw.ellipse(screen, (0,0,0), (x+14,y+10,2,5))
    # arms
    pygame.draw.rect(screen, (255,226,185), (x,y+h-14,5,12), border_radius=3)
    pygame.draw.rect(screen, (255,226,185), (x+19,y+h-14,5,12), border_radius=3)
    # shoes
    pygame.draw.rect(screen, (120,60,20), (x+5,y+h,6,6), border_radius=2)
    pygame.draw.rect(screen, (120,60,20), (x+13,y+h,6,6), border_radius=2)
    # carried block
    if mario['carrying'] is not None:
        bx = x + mario['w']//2 - BLOCK_SIZE//2
        by = y - BLOCK_SIZE - 2
        pygame.draw.rect(screen, (180,120,30), (bx,by,BLOCK_SIZE,BLOCK_SIZE))
        pygame.draw.rect(screen, (230,180,80), (bx,by,BLOCK_SIZE,BLOCK_SIZE),2)

def draw_big_boo():
    surf = pygame.Surface((boo['w'],boo['h']), pygame.SRCALPHA)
    center = boo['w']//2, boo['h']//2
    pygame.draw.circle(surf, (200,220,255,boo['alpha']), center, 24)
    pygame.draw.circle(surf, (90,130,255,boo['alpha']), center, 24, 4)
    pygame.draw.ellipse(surf, (255,255,255,boo['alpha']), (boo['w']//2-18, boo['h']//2-15, 36, 28))
    pygame.draw.arc(surf, (0,0,255,boo['alpha']), (boo['w']//2-22, boo['h']//2-18, 44, 32), 3.7, 2.7, 4)
    pygame.draw.ellipse(surf, (0,0,180,boo['alpha']), (boo['w']//2-10, boo['h']//2-8, 7, 12))
    pygame.draw.ellipse(surf, (0,0,180,boo['alpha']), (boo['w']//2+3, boo['h']//2-8, 7, 12))
    pygame.draw.ellipse(surf, (255,80,80,boo['alpha']), (boo['w']//2-7, boo['h']//2+6, 14, 8))
    pygame.draw.rect(surf, (255,255,255,boo['alpha']), (boo['w']//2-4, boo['h']//2+10,3,5))
    pygame.draw.rect(surf, (255,255,255,boo['alpha']), (boo['w']//2+1, boo['h']//2+10,3,5))
    pygame.draw.polygon(surf, (255,240,80,boo['alpha']), [(boo['w']//2-5,boo['h']//2-25),
                                                         (boo['w']//2+5,boo['h']//2-25),
                                                         (boo['w']//2,boo['h']//2-32)])
    pygame.draw.circle(surf, (255,80,80,boo['alpha']), (boo['w']//2, boo['h']//2-30), 2)
    screen.blit(surf, (int(boo['x']), int(boo['y'])))

###############################################################################
# GAMEPLAY LOGIC
###############################################################################
def move_mario():
    keys = pygame.key.get_pressed()
    mario['vx'] *= MARIO_FRIC_G if mario['on_ground'] else MARIO_FRIC_A
    if keys[pygame.K_LEFT]:  mario['vx'] -= MARIO_ACCEL
    if keys[pygame.K_RIGHT]: mario['vx'] += MARIO_ACCEL
    mario['vx'] = max(-5, min(5, mario['vx']))
    if mario['vx'] > 0: mario['face'] = 1
    elif mario['vx'] < 0: mario['face'] = -1
    if (keys[pygame.K_z] or keys[pygame.K_SPACE]) and mario['on_ground']:
        mario['vy'] = MARIO_JUMP_V
        mario['on_ground'] = False
    mario['vy'] += GRAVITY_GND if mario['on_ground'] else GRAVITY_AIR
    mario['vy'] = min(12, mario['vy'])
    nx = mario['x'] + mario['vx']
    if not collide_tile(nx, mario['y'], mario['w'], mario['h']):
        mario['x'] = nx
    else:
        step = 1 if mario['vx'] > 0 else -1
        while not collide_tile(mario['x']+step, mario['y'], mario['w'], mario['h']):
            mario['x'] += step
        mario['vx'] = 0
    ny = mario['y'] + mario['vy']
    mario['on_ground'] = False
    if not collide_tile(mario['x'], ny, mario['w'], mario['h']):
        mario['y'] = ny
    else:
        step = 1 if mario['vy'] > 0 else -1
        while not collide_tile(mario['x'], mario['y']+step, mario['w'], mario['h']):
            mario['y'] += step
        mario['vy'] = 0
        mario['on_ground'] = step == 1

def update_items():
    global item_spawn_timer
    item_spawn_timer += 1
    if item_spawn_timer >= ITEM_SPAWN_INTERVAL:
        spawn_item()
        item_spawn_timer = 0
    for item in items[:]:
        if mario_rect().colliderect(item_rect(item)):
            if item['type'] == 'coin':
                items.remove(item)
            elif item['type'] == 'mushroom':
                mario['power'] = 'super'
                items.remove(item)
            elif item['type'] == 'fire_flower':
                mario['power'] = 'fire'
                items.remove(item)

def update_grab_blocks():
    keys = pygame.key.get_pressed()
    carrying = mario['carrying']
    if keys[pygame.K_x]:
        if carrying is None:
            for i, b in enumerate(grab_blocks):
                if not b['grabbed'] and mario_rect().colliderect(block_rect(b)):
                    mario['carrying'] = i
                    b['grabbed'] = True
                    b['vx'] = b['vy'] = 0
                    break
    else:
        if carrying is not None:
            b = grab_blocks[carrying]
            dir = mario['face']
            b['grabbed'] = False
            b['x'] = mario['x'] + mario['w']//2 - BLOCK_SIZE//2 + dir*20
            b['y'] = mario['y'] + mario['h']//2 - BLOCK_SIZE//2
            b['vx'] = dir*6
            b['vy'] = -4
            mario['carrying'] = None
    for b in grab_blocks:
        if b['grabbed']:
            b['x'] = mario['x'] + mario['w']//2 - BLOCK_SIZE//2
            b['y'] = mario['y'] - BLOCK_SIZE - 2
            continue
        b['vy'] += GRAVITY_AIR
        b['vy'] = min(b['vy'], 12)
        b['x'] += b['vx']
        b['y'] += b['vy']
        if collide_tile(b['x'], b['y']+BLOCK_SIZE, BLOCK_SIZE, 1):
            b['vy'] = -b['vy']*0.3
            b['vx'] *= 0.5
            while collide_tile(b['x'], b['y']+BLOCK_SIZE, BLOCK_SIZE,1):
                b['y'] -= 1
            if abs(b['vy']) < 1: b['vy'] = 0
        if collide_tile(b['x'], b['y'], BLOCK_SIZE, BLOCK_SIZE):
            b['vx'] = -b['vx']*0.3
        if boo_rect().colliderect(block_rect(b)) and boo['state'] == 'vulnerable':
            b['vx'] = b['vy'] = 0
            boo['health'] -= 1
            boo['alpha'] = 255
            boo['x'] += 10 if b['x'] < boo['x'] else -10
            b['x'] = b['y'] = -1000

def move_big_boo():
    m_center_x = mario['x'] + mario['w']//2
    boo_center_x = boo['x'] + boo['w']//2
    mario_looking_at_boo = ((boo_center_x - m_center_x) * mario['face']) > 0
    boo['float_t'] += 0.03
    boo['state_timer'] += 1

    if boo['state'] == 'chase':
        boo['y'] = 8.5*TILE + 16*math.sin(boo['float_t'])
        if mario_looking_at_boo:
            boo['vx'] = 0
            boo['alpha'] = max(80, boo['alpha'] - 15)
        else:
            boo['alpha'] = min(255, boo['alpha'] + 25)
            speed = 2.0
            boo['vx'] = speed if boo_center_x < m_center_x else -speed
        if boo['state_timer'] > 180:
            boo['state'] = 'teleport'
            boo['state_timer'] = 0
            boo['alpha'] = 50
            boo['teleport_x'] = random.randint(4, 16) * TILE
            boo['teleport_y'] = random.randint(6, 10) * TILE
    elif boo['state'] == 'teleport':
        if boo['state_timer'] > 60:
            boo['x'] = boo['teleport_x']
            boo['y'] = boo['teleport_y']
            boo['state'] = 'vulnerable'
            boo['state_timer'] = 0
            boo['alpha'] = 255
    elif boo['state'] == 'vulnerable':
        boo['y'] = boo['teleport_y'] + 16*math.sin(boo['float_t'])
        boo['vx'] = 0
        if boo['state_timer'] > 120:
            boo['state'] = 'chase'
            boo['state_timer'] = 0

    boo['x'] += boo['vx']
    boo['x'] = max(4*TILE, min(boo['x'], 17*TILE))

def reset_and_quit(msg):
    print(msg)
    pygame.time.wait(1200)
    pygame.quit()
    sys.exit()

###############################################################################
# MAIN LOOP
###############################################################################
while True:
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            reset_and_quit("Quit")

    # Update
    move_mario()
    update_items()
    update_grab_blocks()
    move_big_boo()

    # Check loss
    if mario_rect().colliderect(boo_rect()):
        reset_and_quit("Haunted! Try again…")

    # Check win
    if boo['health'] <= 0:
        reset_and_quit("Big Boo defeated! Nice job!")

    # Draw
    screen.fill((150,220,255))
    draw_level()
    draw_items()
    draw_grab_blocks()
    draw_mario()
    draw_big_boo()

    pygame.display.flip()
    clock.tick(FPS)

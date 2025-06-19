"""
Snake — Pygame, no external assets
60 × 40 grid, 20 px tiles, WASD controls, pure‑Python beep SFX
"""

import pygame, sys, random, numpy as np

# ─── Configuration ──────────────────────────────────────────────────────────────
WIDTH, HEIGHT   = 600, 400
TILE            = 20
COLS, ROWS      = WIDTH // TILE, HEIGHT // TILE
FPS             = 10

# ─── Palette ────────────────────────────────────────────────────────────────────
BG      = (15, 15, 20)
GRID    = (40, 40, 60)
SNAKE   = (40, 220, 40)
HEAD    = (30, 240, 60)
FOOD    = (255, 70, 70)
TEXT    = (255, 240, 120)

# ─── Initialisation ─────────────────────────────────────────────────────────────
pygame.init()
pygame.mixer.init(frequency=22_050, size=-16, channels=1, buffer=256)
screen      = pygame.display.set_mode((WIDTH, HEIGHT))
clock       = pygame.time.Clock()
font_big    = pygame.font.SysFont("Arial", 32)
font_small  = pygame.font.SysFont("Arial", 22)
pygame.display.set_caption("Snake — WASD Atari Style")

# ─── Simple tone generator (pure NumPy → Pygame sound) ─────────────────────────
def tone(freq=440, ms=120, vol=0.25):
    sr = 22_050
    ns = int(sr * ms / 1_000)
    t  = np.linspace(0, ms / 1_000, ns, False)
    wave = np.sin(freq * 2*np.pi * t)
    return pygame.sndarray.make_sound((wave * (2**15-1) * vol).astype(np.int16))

SFX_FOOD, SFX_DEAD = tone(920, 90, .22), tone(220, 360, .22)

# ─── Helper ─────────────────────────────────────────────────────────────────────
def free_cell(snake):
    while True:
        p = random.randrange(COLS), random.randrange(ROWS)
        if p not in snake: return p

# ─── Draw routines ──────────────────────────────────────────────────────────────
def draw_grid():
    for x in range(0, WIDTH, TILE):
        pygame.draw.line(screen, GRID, (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, TILE):
        pygame.draw.line(screen, GRID, (0, y), (WIDTH, y))

def draw_game(snake, food, score):
    screen.fill(BG); draw_grid()
    # food
    pygame.draw.rect(screen, FOOD,
                     (food[0]*TILE, food[1]*TILE, TILE, TILE))
    # snake
    for i, (cx, cy) in enumerate(snake):
        pygame.draw.rect(screen, HEAD if i==0 else SNAKE,
                         (cx*TILE, cy*TILE, TILE, TILE))
    # score
    screen.blit(font_big.render(f"Score: {score}", True, TEXT), (10, 5))

def draw_center(msg, dy=0, f=font_big):
    s = f.render(msg, True, TEXT)
    screen.blit(s, (WIDTH//2 - s.get_width()//2,
                    HEIGHT//2 - s.get_height()//2 + dy))

def draw_menu():
    screen.fill(BG)
    draw_center("SNAKE")
    draw_center("Press SPACE to start", 50, font_small)
    draw_center("Use W A S D to move", 80, font_small)

def draw_game_over(score):
    draw_game(snake, food, score)          # show final board dimmed
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0,0,0,180)); screen.blit(overlay, (0,0))
    draw_center("GAME OVER!")
    draw_center(f"Score: {score}", 40)
    draw_center("R = Restart   ESC = Menu", 80, font_small)

# ─── Game loop ──────────────────────────────────────────────────────────────────
MENU, PLAY, DEAD = range(3)
state           = MENU
snake           = [(COLS//2, ROWS//2)]
direction       = (1,0)
pending         = direction
food            = free_cell(snake)
score           = 0

while True:
    # ── Input ──
    for e in pygame.event.get():
        if e.type == pygame.QUIT: pygame.quit(); sys.exit()
        if e.type != pygame.KEYDOWN: continue
        # --- Menu ---
        if state == MENU and e.key == pygame.K_SPACE:
            state = PLAY; snake = [(COLS//2, ROWS//2)]
            direction = pending = (1,0); food = free_cell(snake); score = 0
        # --- Play ---
        elif state == PLAY:
            if   e.key == pygame.K_w and direction!=(0,1):  pending = (0,-1)
            elif e.key == pygame.K_s and direction!=(0,-1): pending = (0, 1)
            elif e.key == pygame.K_a and direction!=(1,0):  pending = (-1,0)
            elif e.key == pygame.K_d and direction!=(-1,0): pending = (1, 0)
        # --- Dead ---
        elif state == DEAD:
            if e.key == pygame.K_r:
                state = PLAY; snake = [(COLS//2, ROWS//2)]
                direction = pending = (1,0); food = free_cell(snake); score = 0
            elif e.key == pygame.K_ESCAPE:
                state = MENU

    # ── Update ──
    if state == PLAY:
        direction = pending
        head = (snake[0][0] + direction[0],
                snake[0][1] + direction[1])
        hit_wall  = not (0 <= head[0] < COLS and 0 <= head[1] < ROWS)
        hit_self  = head in snake
        if hit_wall or hit_self:
            state = DEAD; SFX_DEAD.play()
        else:
            snake.insert(0, head)
            if head == food:
                food = free_cell(snake); score += 1; SFX_FOOD.play()
            else:
                snake.pop()

    # ── Render ──
    if   state == MENU: draw_menu()
    elif state == PLAY: draw_game(snake, food, score)
    else:               draw_game_over(score)

    pygame.display.flip()
    clock.tick(FPS)

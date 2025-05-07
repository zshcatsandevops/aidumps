"""
fixed_platformer.py – simple 16×16 platformer whose tiles are
generated from a chunk of ROM data.
"""
import pygame, platform, sys
from pathlib import Path

# --- CONSTANTS --------------------------------------------------------------
HEX_DATA = (
    "2e0000ea24ffae51699aa2213d84820a"
    "84e409ad11248b98c0817f21a352be19"
    "9309ce2010464a4af82731ec58c7e833"
    "82e3cebf85f4df94ce4b09c194568ac0"
    "1372a7fc9f844d73a3ca9a615897a327"
    "fc039876231dc7610304ae56bf388400"
    "40a70efdff52fe036f9530f197fbc085"
    "60d68025a963be03014e38e2f9a234ff"
    "bb3e0344780090cb88113a9465c07c63"
    "87f03cafd625e48b380aac7221d4f807"
    "5355504552204d4152494f4241413245"
    "303196000000000000000000008e0000"
    "1200a0e300f029e128d09fe51f00a0e3"
    "00f029e118d09fe598119fe518008fe2"
)  # truncated for readability – keep full string in real code

GRID_W, GRID_H   = 16, 16
TILE             = 30
SCREEN_W, SCREEN_H = GRID_W*TILE, GRID_H*TILE
FPS              = 60
GRAVITY          = 1200         # px / s²
JUMP_VY          = -450         # px / s
MOVE_SPEED       = 200          # px / s
MAX_FALL_SPEED   = 900

COLLIDABLE_R_MIN = 100          # byte-R threshold to mark a solid tile

BLACK            = (0,0,0)
PLAYER_CLR       = (255,255,255)
DEFAULT_CLR      = (40,40,40)

# --- LEVEL DATA -------------------------------------------------------------
raw_bytes = bytes.fromhex(HEX_DATA)           # built-in, fast & safe
palette   = []
start     = 12*16                             # skip header bytes
for i in range(GRID_W*GRID_H):
    idx = start + i*3
    if idx+2 < len(raw_bytes):
        palette.append(tuple(raw_bytes[idx:idx+3]))
    else:
        palette.append(DEFAULT_CLR)

solids = [
    [ palette[y*GRID_W+x][0] > COLLIDABLE_R_MIN
      for x in range(GRID_W) ]
    for y in range(GRID_H)
]

# --- INITIALISE PYGAME ------------------------------------------------------
pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Hex Data Platformer")
clock  = pygame.time.Clock()

player = pygame.Rect(0, 0, 22, 22)
vel_x  = vel_y = 0.0
on_ground = False

# --- HELPERS ---------------------------------------------------------------
def tiles_touching(rect: pygame.Rect):
    """Yield (gx, gy) of any solid tiles overlapped by rect."""
    left   = max(0, rect.left  // TILE)
    right  = min(GRID_W-1, rect.right  // TILE)
    top    = max(0, rect.top   // TILE)
    bottom = min(GRID_H-1, rect.bottom // TILE)
    for gy in range(top, bottom+1):
        for gx in range(left, right+1):
            if solids[gy][gx]:
                yield gx, gy

# --- MAIN LOOP -------------------------------------------------------------
running = True
while running:
    dt = clock.tick(FPS) / 1000          # seconds since last frame

    # -- events
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
            break
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            running = False
            break

    keys = pygame.key.get_pressed()
    vel_x = ( -MOVE_SPEED if keys[pygame.K_LEFT]
              else MOVE_SPEED if keys[pygame.K_RIGHT] else 0 )

    # jump only when key *just* pressed and standing
    if keys[pygame.K_SPACE] and on_ground:
        vel_y = JUMP_VY
        on_ground = False

    # -- physics: horizontal
    player.x += vel_x * dt
    for gx,gy in tiles_touching(player):
        tile_rect = pygame.Rect(gx*TILE, gy*TILE, TILE, TILE)
        if player.colliderect(tile_rect):
            if vel_x > 0:
                player.right = tile_rect.left
            elif vel_x < 0:
                player.left  = tile_rect.right

    # -- physics: vertical
    vel_y = min(vel_y + GRAVITY*dt, MAX_FALL_SPEED)
    player.y += vel_y * dt
    on_ground = False
    for gx,gy in tiles_touching(player):
        tile_rect = pygame.Rect(gx*TILE, gy*TILE, TILE, TILE)
        if player.colliderect(tile_rect):
            if vel_y > 0:                   # falling
                player.bottom = tile_rect.top
                on_ground = True
            elif vel_y < 0:                 # rising
                player.top = tile_rect.bottom
            vel_y = 0

    # -- screen-edge clamp
    player.clamp_ip(screen.get_rect())

    # -- draw
    screen.fill(BLACK)
    for y in range(GRID_H):
        for x in range(GRID_W):
            pygame.draw.rect(
                screen, palette[y*GRID_W+x],
                pygame.Rect(x*TILE, y*TILE, TILE, TILE)
            )
    pygame.draw.rect(screen, PLAYER_CLR, player)
    pygame.display.flip()

# --- CLEAN UP --------------------------------------------------------------
pygame.quit()
sys.exit()

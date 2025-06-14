###############################################################################
# Super‑Simple Maria 32‑Level Demo — single‑file, 0‑asset, 60 FPS
# Inspired by open‑source Mario clones (MIT licences) and level‑data research.
# Author: ChatGPT (OpenAI o3) — June 2025
###############################################################################
import sys, random, math, pygame
pygame.init()

# ------------------------------------------------------------
# Global constants
# ------------------------------------------------------------
SCREEN_W, SCREEN_H   = 512, 480
TILE                = 16
GRAVITY             = 0.35
MAX_FALL_SPEED      = 8
FPS                 = 60
WHITE, SKY, GROUND  = (255,255,255), (112,176,255), (188,124,68)

# Palette variations for procedural worlds (8 worlds × 4 areas)
WORLD_SKIES = [
    (112,176,255), (96,96,96), (16,16,48), (40,160,200),
    (200,64,64),   (32,128,0), (240,240,240), (32,32,32)
]

# ------------------------------------------------------------
# Tile definitions:
# ' ' empty, '#' ground, '?' coin box, 'X' solid block, 'F' flag pole
# ------------------------------------------------------------
LEVEL_TEMPLATE = [
    "                                                                                                ",
    "                                                                                                ",
    "                                                                                                ",
    "                                                                                                ",
    "                                                                                                ",
    "                                                                                                ",
    "                       ?                                                                         ",
    "                 X                                                                              ",
    "        ?               XXX                                                                     ",
    "                       #####                                                                    ",
    "                                                                                                ",
    "###############################   ##############################################################",
]

LEVEL_WIDTH   = len(LEVEL_TEMPLATE[0])
LEVEL_HEIGHT  = len(LEVEL_TEMPLATE)

# ------------------------------------------------------------
# Helper: build 32 deterministic variations
# ------------------------------------------------------------
def build_levels():
    levels = []
    rng = random.Random(20250614)      # fixed seed for reproducibility
    for world in range(8):
        for area in range(4):
            mod = []
            sky = WORLD_SKIES[world]
            for row in LEVEL_TEMPLATE:
                # Mutate: every 25% chance flip '?' -> 'X' to vary rewards
                new_row = ''.join(
                    ('X' if ch == '?' and rng.random() < 0.25 else ch)
                    for ch in row
                )
                # Occasionally grow hills
                if rng.random() < 0.10:
                    hill_h = rng.randint(1,3)
                    hill_x = rng.randint(5, LEVEL_WIDTH-10)
                    for h in range(hill_h):
                        idx = -h-2
                        new_row = new_row[:hill_x] + "#"*8 + new_row[hill_x+8:]
                mod.append(new_row)
            levels.append({'tiles': mod, 'sky': sky})
    return levels

LEVELS = build_levels()

# ------------------------------------------------------------
# Entity classes
# ------------------------------------------------------------
class Player(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((TILE,TILE*2))
        self.image.fill((255,0,0))
        self.rect = self.image.get_rect(topleft=pos)
        self.vel = pygame.Vector2(0,0)
        self.on_ground = False
    
    def update(self, tiles, keys):
        accel = 0.4
        max_speed = 3
        if keys[pygame.K_LEFT]:  self.vel.x = max(self.vel.x-accel, -max_speed)
        elif keys[pygame.K_RIGHT]: self.vel.x = min(self.vel.x+accel,  max_speed)
        else: self.vel.x *= 0.8

        if self.on_ground and keys[pygame.K_z]:
            self.vel.y = -6
            self.on_ground = False
        self.vel.y = min(self.vel.y + GRAVITY, MAX_FALL_SPEED)

        # Horizontal collision
        self.rect.x += int(self.vel.x)
        self.collide(tiles, dx=True)
        # Vertical collision
        self.rect.y += int(self.vel.y)
        self.collide(tiles, dy=True)
    
    def collide(self, tiles, dx=False, dy=False):
        for tile in tiles:
            if self.rect.colliderect(tile):
                if dx:
                    if self.vel.x > 0: self.rect.right = tile.left
                    elif self.vel.x < 0: self.rect.left = tile.right
                    self.vel.x = 0
                if dy:
                    if self.vel.y > 0: 
                        self.rect.bottom = tile.top
                        self.on_ground = True
                    elif self.vel.y < 0:
                        self.rect.top = tile.bottom
                    self.vel.y = 0

# ------------------------------------------------------------
# Level renderer
# ------------------------------------------------------------
def gather_solid_tiles(level, cam_x):
    solid = []
    for y, row in enumerate(level['tiles']):
        for x, ch in enumerate(row):
            if ch in "#X":
                solid.append(
                    pygame.Rect(x*TILE - cam_x, y*TILE, TILE, TILE)
                )
    return solid

def draw_level(screen, level, cam_x):
    # Sky
    screen.fill(level['sky'])
    # Tiles
    for y, row in enumerate(level['tiles']):
        for x, ch in enumerate(row):
            px = x*TILE - cam_x
            py = y*TILE
            if ch == '#':
                pygame.draw.rect(screen, GROUND, (px,py,TILE,TILE))
            elif ch == 'X':
                pygame.draw.rect(screen, (200,200,0), (px,py,TILE,TILE))
            elif ch == '?':
                pygame.draw.rect(screen, (255,215,0), (px,py,TILE,TILE))
            elif ch == 'F':
                pygame.draw.line(screen, WHITE, (px+TILE//2,0), (px+TILE//2, py+TILE*2), 2)

# ------------------------------------------------------------
# Game loop
# ------------------------------------------------------------
def run():
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock  = pygame.time.Clock()
    level_id = 0
    player = Player((TILE*2, SCREEN_H - TILE*3))
    font = pygame.font.SysFont("monospace", 14, bold=True)

    while True:
        level = LEVELS[level_id]
        # --- Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: sys.exit()

        keys = pygame.key.get_pressed()
        player.update(gather_solid_tiles(level, 0), keys)

        # Camera follows player
        cam_x = max(0, player.rect.centerx - SCREEN_W//2)
        # Win condition → next level
        if player.rect.left > LEVEL_WIDTH*TILE:
            level_id = (level_id + 1) % 32
            # Respawn player & vibes
            player.rect.topleft = (TILE*2, SCREEN_H - TILE*3)
            print(f'🌟  World‑{level_id//4+1}-{level_id%4+1} vibes ON!  🌟')

        # Draw
        draw_level(screen, level, cam_x)
        screen.blit(player.image, (player.rect.x - cam_x, player.rect.y))
        # HUD
        hud = font.render(f"W-{level_id//4+1}-{level_id%4+1}", True, WHITE)
        screen.blit(hud, (8,8))
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    run()

# test.py  – run with:  python test.py
import pygame, sys, math

# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS          = 60
TILESIZE     = 32
LEVEL_ROWS   = SCREEN_HEIGHT // TILESIZE

PALETTE = [                       # index in hex = colour
    (255,255,255),(220,220,220),(192,192,192),(160,160,160),
    (128,128,128),( 96, 96, 96),( 64, 64, 64),( 32, 32, 32),
    (140,200,255),(100,180,255),(255,200,100),(200,100, 50),
    (100,200,100),(255,100,100),(200,150,100),( 50,150, 50)
]

# ---------------------------------------------------------------------
# LEVEL DATA  (30×20 – last two rows ground)
# ---------------------------------------------------------------------
LEVEL_DATA = {
    "w1_1": [
        "000000000000000000000000000000",
        "000000000000000000000000000000",
        "000000000000000000000000000000",
        "000001100000000000000000000000",
        "000001100000000000000000000000",
        "000000000000000000000000000000",
        "000000000000000000000000000000",
        "000000000001111100000000000000",
        "000000000001000100000000000000",
        "000000000001111100000000000000",
        "000000000000000000000000000000",
        "000000000000000000000000000000",
        "000000000000000000000000000000",
        "000000000000000000000000000000",
        "000000000000000000000000000000",
        "EEEEEEEEEEEEEEEEEEEEEEEEEEEEEE",
        "EEEEEEEEEEEEEEEEEEEEEEEEEEEEEE",
        "EEEEEEEEEEEEEEEEEEEEEEEEEEEEEE",
        "EEEEEEEEEEEEEEEEEEEEEEEEEEEEEE",
        "EEEEEEEEEEEEEEEEEEEEEEEEEEEEEE",
    ]
}
LEVEL_ORDER = ["w1_1"]  # wrap to itself until you create more maps


# ---------------------------------------------------------------------
# 16×16 PATTERNS  (hex chars map to PALETTE index)
# ---------------------------------------------------------------------
TILES = {
    1: [                       # “brick”
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
        "BBBBBBBBBBBBBBBB",
    ],
    0xE: [                     # “ground”
        "EEEEEEEEEEEEEEEE",
        "EEEEEEEEEEEEEEEE",
        "EEEEEEEEEEEEEEEE",
        "EEEEEEEEEEEEEEEE",
        "EEEEEEEEEEEEEEEE",
        "EEEEEEEEEEEEEEEE",
        "EEEEEEEEEEEEEEEE",
        "EEEEEEEEEEEEEEEE",
        "EEEEEEEEEEEEEEEE",
        "EEEEEEEEEEEEEEEE",
        "EEEEEEEEEEEEEEEE",
        "EEEEEEEEEEEEEEEE",
        "EEEEEEEEEEEEEEEE",
        "EEEEEEEEEEEEEEEE",
        "EEEEEEEEEEEEEEEE",
        "EEEEEEEEEEEEEEEE",
    ],
}

MARIO_SMALL = [
    "000D0D000",
    "00DDD0DDD",
    "0DDBBDDDB",
    "0DDBBDDDB",
    "0DDD0DDDD",
    "0000D0000",
    "000D0D000",
    "00D000D00",
]

MARIO_BIG = [
    "0000DDDD0000",
    "000DDDDDD000",
    "00DDBBBBDD00",
    "00DDBBBBDD00",
    "00DDDDDDDD00",
    "0000DDDD0000",
    "000DD00DD000",
    "000D0000D000",
    "00D0000000D0",
    "00D0000000D0",
    "000000000000",
    "000000000000",
]

CLOUD = [
    "0009999000",
    "0999999990",
    "9999999999",
    " 099999990",
    "  0999990 ",
]

# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------
def paint_pattern(surf, pattern, x, y, scale=2):
    """Draw any 2‑D pattern (list[str]) onto surface at pixel (x,y)."""
    for row, line in enumerate(pattern):
        for col, ch in enumerate(line):
            if ch != " " and ch != "0":
                colour = PALETTE[int(ch, 16)]
                pygame.draw.rect(
                    surf,
                    colour,
                    (x + col * scale, y + row * scale, scale, scale)
                )

class TileCache:
    def __init__(self):
        self._cache = {}

    def get(self, tid: int) -> pygame.Surface | None:
        if tid not in self._cache:
            # draw pattern if we have one, else solid colour
            surf = pygame.Surface((TILESIZE, TILESIZE), pygame.SRCALPHA)
            if tid in TILES:
                paint_pattern(surf, TILES[tid], 0, 0, TILESIZE // 16)
            else:
                surf.fill(PALETTE[tid % len(PALETTE)])
            self._cache[tid] = surf
        return self._cache[tid]


class LevelLoader:
    @staticmethod
    def load(key: str) -> list[list[int]]:
        raw = LEVEL_DATA.get(key, [])
        return [[int(c, 16) for c in row] for row in raw] if raw else [[]]


# ---------------------------------------------------------------------
# PARTICLES
# ---------------------------------------------------------------------
class Particle:
    def __init__(self, x, y, vx, vy, colour, life=30):
        self.x, self.y, self.vx, self.vy, self.life = x, y, vx, vy, life
        self.colour = colour

    def update(self) -> bool:
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.3
        self.life -= 1
        return self.life > 0

    def draw(self, surf, cam_x):
        if self.life <= 0:
            return
        alpha = self.life / 30
        size = max(1, int(4 * alpha))
        pygame.draw.circle(
            surf,
            self.colour,
            (int(self.x - cam_x), int(self.y)),
            size,
        )


# ---------------------------------------------------------------------
# MARIO
# ---------------------------------------------------------------------
class Mario:
    MOVE_SPEED = 3.5
    JUMP_SPEED = -10.5
    GRAVITY    = 0.45
    MAX_FALL   = 15

    def __init__(self):
        self.w = self.h = TILESIZE
        self.x, self.y = 3 * TILESIZE, (LEVEL_ROWS - 4) * TILESIZE
        self.vx = self.vy = 0
        self.facing_right = True
        self.on_ground  = False
        self.is_big     = False
        self.anim_frame = self.anim_timer = 0
        self.particles  = []

    # ---------------------------------------------------------
    # COLLISION (optimised: only tiles around the player)
    # ---------------------------------------------------------
    def _collision_rects(self, level):
        if not level or not level[0]:
            return []

        cols, rows = len(level[0]), len(level)
        min_tx = max(0, int(self.x          // TILESIZE) - 1)
        max_tx = min(cols-1, int((self.x+self.w-1) // TILESIZE) + 1)
        min_ty = max(0, int(self.y          // TILESIZE) - 1)
        max_ty = min(rows-1, int((self.y+self.h-1) // TILESIZE) + 1)

        rects = []
        for ty in range(min_ty, max_ty+1):
            for tx in range(min_tx, max_tx+1):
                if level[ty][tx]:
                    rects.append((tx, ty,
                                  pygame.Rect(tx*TILESIZE,
                                              ty*TILESIZE,
                                              TILESIZE, TILESIZE)))
        return rects

    def _collide(self, x, y, level):
        test_rect = pygame.Rect(x, y, self.w, self.h)
        for tx, ty, rect in self._collision_rects(level):
            if test_rect.colliderect(rect):
                return tx, ty
        return None

    # ---------------------------------------------------------
    # UPDATE
    # ---------------------------------------------------------
    def update(self, keys, level):
        # Horizontal intent
        if keys[pygame.K_LEFT]:
            self.vx = -self.MOVE_SPEED
            self.facing_right = False
        elif keys[pygame.K_RIGHT]:
            self.vx =  self.MOVE_SPEED
            self.facing_right = True
        else:
            self.vx *= 0.85

        # Jump
        if (keys[pygame.K_z] or keys[pygame.K_x] or keys[pygame.K_SPACE]) and self.on_ground:
            self.vy = self.JUMP_SPEED
            self.on_ground = False
            for i in range(5):
                self.particles.append(
                    Particle(self.x + self.w//2 + (i-2)*3,
                             self.y + self.h,
                             (i-2)*0.5, 2,
                             PALETTE[6], 20)
                )

        # Gravity
        self.vy = min(self.vy + self.GRAVITY, self.MAX_FALL)

        # --- HORIZONTAL ---
        nx = self.x + self.vx
        if not self._collide(nx, self.y, level):
            self.x = nx
        else:
            self.vx = 0

        # --- VERTICAL ---
        ny = self.y + self.vy
        col = self._collide(self.x, ny, level)
        if col:
            tx, ty = col
            if self.vy > 0:      # falling – land on top
                self.y = ty*TILESIZE - self.h
                self.on_ground = True
            else:                # hitting ceiling
                self.y = (ty+1)*TILESIZE
            self.vy = 0
        else:
            self.y = ny
            self.on_ground = False

        # animation state
        if abs(self.vx) > 0.5:
            self.anim_timer = (self.anim_timer + 1) % 6
            if self.anim_timer == 0:
                self.anim_frame ^= 1
        else:
            self.anim_frame = 0

        # particles
        self.particles[:] = [p for p in self.particles if p.update()]

    # ---------------------------------------------------------
    # DRAW
    # ---------------------------------------------------------
    def draw(self, surf, cam_x):
        pattern = MARIO_BIG if self.is_big else MARIO_SMALL
        if not self.facing_right:
            pattern = [line[::-1] for line in pattern]

        paint_pattern(surf, pattern, self.x - cam_x, self.y, 2)
        for p in self.particles:
            p.draw(surf, cam_x)


# ---------------------------------------------------------------------
# BACKGROUND (simple gradient + scrolling ASCII clouds)
# ---------------------------------------------------------------------
class Background:
    def __init__(self, map_width_px):
        self.clouds = [{"x": i*200 + (i*57)%90,
                        "y": 50 + (i*31)%60,
                        "speed": 0.2 + (i%3)*0.1}
                       for i in range(20)]
        self.map_width_px = map_width_px

    def update(self):
        for c in self.clouds:
            c["x"] -= c["speed"]
            if c["x"] < -200:
                c["x"] = self.map_width_px

    def draw(self, surf, cam_x):
        # sky gradient
        for y in range(SCREEN_HEIGHT//3):
            ratio = y / (SCREEN_HEIGHT//3)
            colour = (140+int(ratio*60), 200+int(ratio*30), 255)
            pygame.draw.line(surf, colour, (0,y), (SCREEN_WIDTH,y))

        # clouds
        for c in self.clouds:
            if -200 < c["x"]-cam_x < SCREEN_WIDTH+200:
                paint_pattern(surf, CLOUD,
                              int(c["x"] - cam_x*0.3), c["y"], 2)


# ---------------------------------------------------------------------
# GAME LOOP
# ---------------------------------------------------------------------
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Super Mario Land – ASCII edition (60 fps)")
        self.clock       = pygame.time.Clock()
        self.tile_cache  = TileCache()
        self.level_index = 0
        self.level       = LevelLoader.load(LEVEL_ORDER[self.level_index])
        self.player      = Mario()
        self.camera_x    = 0
        self.camera_smooth = 0.1
        self.background  = Background(len(self.level[0])*TILESIZE)

    # --------------------
    def advance_level(self):
        self.level_index = (self.level_index + 1) % len(LEVEL_ORDER)
        self.level       = LevelLoader.load(LEVEL_ORDER[self.level_index])
        self.player.x, self.player.y = 3*TILESIZE, (len(self.level)-4)*TILESIZE
        self.camera_x   = 0
        self.background = Background(len(self.level[0])*TILESIZE)

    # --------------------
    def run(self):
        running = True
        while running:
            self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:           running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE,
                                     pygame.K_q):        running = False
                    elif event.key == pygame.K_b:        self.player.is_big ^= True

            keys = pygame.key.get_pressed()
            self.player.update(keys, self.level)
            self.background.update()

            # camera follows Mario (clamped)
            map_w_px = len(self.level[0])*TILESIZE
            target_x = max(0, min(self.player.x - SCREEN_WIDTH//2,
                                  map_w_px - SCREEN_WIDTH))
            self.camera_x += (target_x - self.camera_x)*self.camera_smooth

            # draw world
            self.draw()

            # go to next level when Mario reaches far right
            if self.player.x >= (map_w_px - self.player.w):
                self.advance_level()

        pygame.quit()
        sys.exit()

    # --------------------
    def draw(self):
        self.screen.fill(PALETTE[8])              # clear
        self.background.draw(self.screen, self.camera_x)

        first = int(self.camera_x // TILESIZE)
        last  = first + SCREEN_WIDTH//TILESIZE + 2
        for ty, row in enumerate(self.level):
            for tx in range(first, min(last, len(row))):
                tid = row[tx]
                if tid:
                    surf = self.tile_cache.get(tid)
                    self.screen.blit(
                        surf, (tx*TILESIZE - self.camera_x, ty*TILESIZE)
                    )

        self.player.draw(self.screen, self.camera_x)

        # overlay FPS
        fps_text = pygame.font.Font(None, 24).render(
            f"{int(self.clock.get_fps()):>3} FPS", True, PALETTE[0])
        self.screen.blit(fps_text, (10, 10))

        pygame.display.flip()


# ---------------------------------------------------------------------
if __name__ == "__main__":
    Game().run()

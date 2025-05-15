import pygame, random

# --- CORE CONSTANTS ---
WIDTH, HEIGHT = 640, 400
TILE = 32
FPS = 60

# --- COLORS ---
COL = dict(
    white=(255,255,255), black=(0,0,0), red=(220,50,50), green=(60,220,60), blue=(50,90,220), yellow=(240,220,70),
    brown=(170,100,40), sky=(110,180,240), gray=(120,120,120), gold=(240,220,70), orange=(220,120,30),
    darkgreen=(20,100,20), darkred=(150,20,30), purple=(120,60,180)
)

# --- SMW-STYLE MAP & LEVEL DATA ---
SMW_MAP = [
    # World 1: Yoshi's Island
    {
        "name": "Yoshi's Island",
        "nodes": [
            {"pos": (80, 220), "level": (1,1)},
            {"pos": (180, 200), "level": (1,2)},
            {"pos": (300, 220), "level": (1,3)},
            {"pos": (420, 200), "level": (1,4)},
            {"pos": (540, 220), "level": (1,5)},
        ]
    },
    # World 2: Donut Plains
    {
        "name": "Donut Plains",
        "nodes": [
            {"pos": (80, 100), "level": (2,1)},
            {"pos": (180, 120), "level": (2,2)},
            {"pos": (300, 90),  "level": (2,3)},
            {"pos": (420, 110), "level": (2,4)},
            {"pos": (540, 100), "level": (2,5)},
        ]
    },
]

SMW_LEVELS = {
    (1,1): {
        "platforms": [
            (0, HEIGHT-40, WIDTH, 12), (120, 220, 80, 12), (320, 170, 80, 12)
        ],
        "enemies": [(260, HEIGHT-72, "goomba")],
        "items": [(160, 160, "coin"), (190, 160, "powerup")],
        "flag": (580, HEIGHT-72),
        "pipes": [(300, HEIGHT-72, True)],
        "switches": [(220, HEIGHT-52, "blue")],
        "powerups": [(192, 156, "mushroom")],
        "yoshi": (90, HEIGHT-72)
    },
    (1,2): {
        "platforms": [
            (0, HEIGHT-40, WIDTH, 12), (200, 160, 100, 12)
        ],
        "enemies": [(350, HEIGHT-72, "goomba"), (400, 140, "koopa")],
        "items": [(240, 120, "coin")],
        "flag": (580, HEIGHT-72),
        "pipes": [],
        "switches": [],
        "powerups": [],
        "yoshi": None
    },
    (1,3): {
        "platforms": [
            (0, HEIGHT-40, WIDTH, 12), (300, 120, 120, 12), (500, 70, 80, 12)
        ],
        "enemies": [(400, HEIGHT-72, "koopa")],
        "items": [(320, 100, "powerup")],
        "flag": (580, HEIGHT-72),
        "pipes": [],
        "switches": [],
        "powerups": [(325, 90, "mushroom")],
        "yoshi": None
    },
    (1,4): {
        "platforms": [
            (0, HEIGHT-40, WIDTH, 12), (220, 190, 80, 12), (400, 110, 70, 12)
        ],
        "enemies": [(420, HEIGHT-72, "goomba")],
        "items": [(270, 170, "coin")],
        "flag": (580, HEIGHT-72),
        "pipes": [],
        "switches": [],
        "powerups": [],
        "yoshi": (100, HEIGHT-72)
    },
    (1,5): {
        "platforms": [
            (0, HEIGHT-40, WIDTH, 12)
        ],
        "enemies": [(450, HEIGHT-72, "koopa")],
        "items": [],
        "flag": (580, HEIGHT-72),
        "pipes": [],
        "switches": [],
        "powerups": [],
        "yoshi": None
    },
    (2,1): {
        "platforms": [
            (0, HEIGHT-40, WIDTH, 12), (200, 130, 100, 12), (400, 80, 80, 12)
        ],
        "enemies": [(280, HEIGHT-72, "goomba")],
        "items": [(210, 110, "coin")],
        "flag": (580, HEIGHT-72),
        "pipes": [],
        "switches": [],
        "powerups": [],
        "yoshi": None
    },
    (2,2): {
        "platforms": [
            (0, HEIGHT-40, WIDTH, 12)
        ],
        "enemies": [(360, HEIGHT-72, "koopa")],
        "items": [(230, 130, "coin")],
        "flag": (580, HEIGHT-72),
        "pipes": [],
        "switches": [],
        "powerups": [],
        "yoshi": (100, HEIGHT-72)
    },
    (2,3): {
        "platforms": [
            (0, HEIGHT-40, WIDTH, 12), (400, 60, 100, 12)
        ],
        "enemies": [(420, 38, "goomba")],
        "items": [],
        "flag": (580, HEIGHT-72),
        "pipes": [],
        "switches": [],
        "powerups": [],
        "yoshi": None
    },
    (2,4): {
        "platforms": [
            (0, HEIGHT-40, WIDTH, 12), (150, 110, 200, 12)
        ],
        "enemies": [],
        "items": [(180, 90, "powerup")],
        "flag": (580, HEIGHT-72),
        "pipes": [],
        "switches": [(200, HEIGHT-52, "purple")],
        "powerups": [],
        "yoshi": None
    },
    (2,5): {
        "platforms": [
            (0, HEIGHT-40, WIDTH, 12)
        ],
        "enemies": [(560, HEIGHT-72, "koopa")],
        "items": [],
        "flag": (580, HEIGHT-72),
        "pipes": [],
        "switches": [],
        "powerups": [],
        "yoshi": (90, HEIGHT-72)
    },
}

# --- CORE ENGINE CLASSES ---
class Entity:
    def __init__(self, x, y, w, h, color):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.vx, self.vy = 0, 0
        self.color = color
        self.on_ground = False
        self.active = True
    def rect(self): return pygame.Rect(int(self.x), int(self.y), int(self.w), int(self.h))
    def update(self, state): pass
    def draw(self, surf): pygame.draw.rect(surf, self.color, self.rect())

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 24, 32, COL["red"])
        self.power = "small"
        self.lives, self.score, self.coins = 5, 0, 0
        self.yoshi = None
        self.state = "idle"
        self.invincible = 0
        self.carrying = None
        self.keys = []
        self.accel = 0.18
        self.max_speed = 2.4
        self.friction = 0.12
        self.jump_power = -7
        self.gravity = 0.27
    def handle_input(self, keys):
        if keys[pygame.K_LEFT]: self.vx -= self.accel
        elif keys[pygame.K_RIGHT]: self.vx += self.accel
        else:
            if self.vx > 0:
                self.vx -= self.friction
                if self.vx < 0: self.vx = 0
            elif self.vx < 0:
                self.vx += self.friction
                if self.vx > 0: self.vx = 0
        if self.vx > self.max_speed: self.vx = self.max_speed
        if self.vx < -self.max_speed: self.vx = -self.max_speed
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vy = self.jump_power
        if keys[pygame.K_LSHIFT]:
            self.state = "spin"
    def update(self, state):
        self.vy += self.gravity
        self.x += self.vx
        self.y += self.vy
        if self.x < 0: self.x = 0
        if self.x > WIDTH-self.w: self.x = WIDTH-self.w
        self.on_ground = False
        rect = self.rect()
        for plat in state.level.platforms:
            if rect.colliderect(plat.rect()):
                if self.vy > 0 and rect.bottom - plat.rect().top < 12:
                    self.y = plat.rect().top - self.h
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:
                    self.vy = 0
        if self.yoshi: self.yoshi.x, self.yoshi.y = self.x, self.y+24

class Yoshi(Entity):
    def __init__(self, x, y): super().__init__(x, y, 36, 28, COL["green"])
    def update(self, state): pass

class Enemy(Entity):
    def __init__(self, x, y, kind="goomba"):
        color = COL["brown"] if kind=="goomba" else COL["green"]
        super().__init__(x, y, 24, 24, color)
        self.kind = kind
    def update(self, state):
        self.x += (-1 if self.kind=="goomba" else 1)

class Platform(Entity):
    def __init__(self, x, y, w, h): super().__init__(x, y, w, h, COL["brown"])
    def update(self, state): pass

class Block(Entity):
    def __init__(self, x, y, block_type="coin"):
        color = COL["gold"] if block_type=="coin" else COL["gray"]
        super().__init__(x, y, TILE, TILE, color)
        self.block_type = block_type
    def update(self, state): pass

class Pipe(Entity):
    def __init__(self, x, y, vert=True): super().__init__(x, y, TILE, TILE*2 if vert else TILE, COL["green"])
    def update(self, state): pass

class Switch(Entity):
    def __init__(self, x, y, color): super().__init__(x, y, TILE, TILE/2, COL[color])
    def update(self, state): pass

class PowerUp(Entity):
    def __init__(self, x, y, ptype): super().__init__(x, y, 20, 20, COL["orange"])
    def update(self, state): pass

class Flag(Entity):
    def __init__(self, x, y): super().__init__(x, y, 16, 32, COL["yellow"])
    def update(self, state): pass

# --- OVERWORLD ---
class Overworld:
    def __init__(self, smw_map):
        self.smw_map = smw_map
        self.world = 0
        self.node = 0
        self.move_delay = 0
        self.move_cooldown = 0.15
    def draw(self, surf, font):
        nodes = self.smw_map[self.world]["nodes"]
        for i, node in enumerate(nodes):
            pygame.draw.circle(surf, COL["green"], node["pos"], 16)
            if i > 0:
                pygame.draw.line(surf, COL["gray"], nodes[i-1]["pos"], node["pos"], 5)
        pygame.draw.circle(surf, COL["red"], nodes[self.node]["pos"], 12)
        txt = font.render(self.smw_map[self.world]["name"], True, COL["black"])
        surf.blit(txt, (WIDTH//2-80, 20))
    def move(self, d, dt):
        if self.move_delay <= 0:
            nodes = self.smw_map[self.world]["nodes"]
            self.node = max(0, min(len(nodes)-1, self.node+d))
            self.move_delay = self.move_cooldown
    def switch_world(self, d):
        w = self.world + d
        if 0 <= w < len(self.smw_map):
            self.world = w
            self.node = 0

# --- LEVEL LOADER ---
class Level:
    def __init__(self, world, level):
        data = SMW_LEVELS.get((world+1, level+1), None)
        if not data: data = list(SMW_LEVELS.values())[0]
        self.platforms = [Platform(*p) for p in data["platforms"]]
        self.enemies = [Enemy(*e) for e in data["enemies"]]
        self.items = [Block(*i) for i in data["items"]]
        self.flag = Flag(*data["flag"])
        self.pipes = [Pipe(*p) for p in data["pipes"]]
        self.switches = [Switch(*s) for s in data["switches"]]
        self.powerups = [PowerUp(*pu) for pu in data["powerups"]]
        self.yoshi = Yoshi(*data["yoshi"]) if data["yoshi"] else None
    def draw(self, surf):
        for p in self.platforms: p.draw(surf)
        for e in self.enemies: e.draw(surf)
        for i in self.items: i.draw(surf)
        for pi in self.pipes: pi.draw(surf)
        for s in self.switches: s.draw(surf)
        for pu in self.powerups: pu.draw(surf)
        if self.yoshi: self.yoshi.draw(surf)
        self.flag.draw(surf)

# --- GAME STATE ---
class GameState:
    def __init__(self):
        self.scene = "overworld"
        self.overworld = Overworld(SMW_MAP)
        self.player = Player(60, HEIGHT-72)
        self.level = None
        self.world = 0
        self.level_num = 0
    def switch_level(self):
        self.world = self.overworld.world
        self.level_num = self.overworld.node
        self.level = Level(self.world, self.level_num)
        self.player.x, self.player.y = 60, HEIGHT-72
        self.scene = "level"
    def back_to_overworld(self):
        self.scene = "overworld"

# --- GAME LOOP ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)
    state = GameState()
    running = True
    while running:
        dt = clock.tick(FPS)/1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        keys = pygame.key.get_pressed()
        # --- Overworld move cooldown ---
        if state.scene == "overworld":
            if hasattr(state.overworld, "move_delay"):
                if state.overworld.move_delay > 0:
                    state.overworld.move_delay -= dt
                else:
                    state.overworld.move_delay = 0
        # --- SCENE SWITCH ---
        if state.scene == "overworld":
            if keys[pygame.K_UP]: state.overworld.switch_world(-1)
            if keys[pygame.K_DOWN]: state.overworld.switch_world(1)
            if keys[pygame.K_RIGHT]: state.overworld.move(1, dt)
            if keys[pygame.K_LEFT]: state.overworld.move(-1, dt)
            if keys[pygame.K_RETURN]: state.switch_level()
        elif state.scene == "level":
            state.player.handle_input(keys)
            state.player.update(state)
            for e in state.level.enemies: e.update(state)
            if state.level.yoshi: state.level.yoshi.update(state)
            if state.player.rect().colliderect(state.level.flag.rect()):
                state.back_to_overworld()
            if state.player.y > HEIGHT:
                state.player.lives -= 1
                if state.player.lives <= 0: state.player.lives = 5
                state.player.x, state.player.y = 60, HEIGHT-72
        # --- DRAW ---
        screen.fill(COL["sky"])
        if state.scene == "overworld":
            state.overworld.draw(screen, font)
            txt = font.render("World: ↑/↓ Node: ←/→ Enter=Play", True, COL["black"])
            screen.blit(txt, (10, 10))
        elif state.scene == "level":
            state.level.draw(screen)
            state.player.draw(screen)
            txt = font.render(f"Lives: {state.player.lives} Coins: {state.player.coins} Power: {state.player.power}", True, COL["black"])
            screen.blit(txt, (10, 10))
        pygame.display.flip()
    pygame.quit()

if __name__ == "__main__":
    main()

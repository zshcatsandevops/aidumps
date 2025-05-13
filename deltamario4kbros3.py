import pygame, sys, math, os
from pytmx import load_pygame
from enum import Enum, auto

# CONFIG
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
TILE = 32
VIBE_SPEED = 0.5
NUM_WORLDS = 8
LEVELS_PER_WORLD = 4
MAP_DIR = 'levels'
SOLID_LAYER_NAME = 'Solid'

# HSV to RGB Helper
def hsv_to_rgb(h, s, v):
    h = h % 360
    h60 = h / 60.0
    i = int(h60) % 6
    f = h60 - int(h60)
    p, q, t = v*(1-s), v*(1-f*s), v*(1-(1-f)*s)
    if i == 0: r,g,b = v,t,p
    elif i == 1: r,g,b = q,v,p
    elif i == 2: r,g,b = p,v,t
    elif i == 3: r,g,b = p,q,v
    elif i == 4: r,g,b = t,p,v
    else: r,g,b = v,p,q
    return int(r*255), int(g*255), int(b*255)

# Game States
class SceneID(Enum):
    TITLE = auto()
    WORLDMAP = auto()
    LEVELSELECT = auto()
    GAMEPLAY = auto()

# Player Class
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TILE, TILE*1.5), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (255, 255, 255), (0, 0, TILE, TILE*1.5), 2)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel = pygame.Vector2(0, 0)
        self.on_ground = False
        self.speed = 5
        self.jump_v = -15
        self.gravity = 0.8
        self.max_fall = 20

    def update(self, dt, solids):
        keys = pygame.key.get_pressed()
        self.vel.x = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * self.speed
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vel.y = self.jump_v
        self.vel.y = min(self.vel.y + self.gravity, self.max_fall)
        self.rect.x += self.vel.x
        self._collide(solids, self.vel.x, 0)
        self.rect.y += self.vel.y
        self.on_ground = False
        self._collide(solids, 0, self.vel.y)

    def _collide(self, solids, dx, dy):
        for tile in solids:
            if self.rect.colliderect(tile):
                if dx > 0: self.rect.right = tile.left
                if dx < 0: self.rect.left = tile.right
                if dy > 0:
                    self.rect.bottom = tile.top
                    self.vel.y = 0; self.on_ground = True
                if dy < 0:
                    self.rect.top = tile.bottom
                    self.vel.y = 0

# Game Core
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('Vibe Mario 3 — Zero-Shot Vibes')
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)
        self.bigfont = pygame.font.SysFont(None, 72)
        self.current = SceneID.TITLE
        self.world = 1
        self.level = 1
        self.tmx_cache = {}

    def switch(self, scene):
        self.current = scene
        if scene == SceneID.WORLDMAP:
            self.sel_world = 1
        if scene == SceneID.LEVELSELECT:
            self.sel_level = 1
        if scene == SceneID.GAMEPLAY:
            self.enter_gameplay()

    def run(self):
        t = 0.0
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            t += dt * VIBE_SPEED
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                self.handle_event(e)
            self.update(dt)
            self.draw(t)
            pygame.display.flip()

    def handle_event(self, e):
        handler = getattr(self, f'handle_{self.current.name.lower()}')
        handler(e)

    def update(self, dt):
        updater = getattr(self, f'update_{self.current.name.lower()}')
        updater(dt)

    def draw(self, t):
        drawer = getattr(self, f'draw_{self.current.name.lower()}')
        drawer(t)

    # TITLE Scene
    def handle_title(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
            self.switch(SceneID.WORLDMAP)
    def update_title(self, dt): pass
    def draw_title(self, t):
        self.screen.fill(hsv_to_rgb(math.sin(t)*180+180, 0.6, 0.8))
        txt = self.bigfont.render('Vibe Mario 3', True, (255,255,255))
        self.screen.blit(txt, (SCREEN_WIDTH//2-txt.get_width()//2, SCREEN_HEIGHT//2-40))
        sub = self.font.render('Press Enter', True, (255,255,255))
        self.screen.blit(sub, (SCREEN_WIDTH//2-sub.get_width()//2, SCREEN_HEIGHT//2+40))

    # WORLDMAP Scene
    def handle_worldmap(self, e):
        if e.type != pygame.KEYDOWN: return
        if e.key in (pygame.K_RIGHT, pygame.K_LEFT, pygame.K_DOWN, pygame.K_UP):
            delta = {pygame.K_RIGHT:1, pygame.K_LEFT:-1, pygame.K_DOWN:4, pygame.K_UP:-4}[e.key]
            self.sel_world = (self.sel_world + delta - 1) % NUM_WORLDS + 1
        elif e.key == pygame.K_RETURN:
            self.world = self.sel_world
            self.switch(SceneID.LEVELSELECT)
    def update_worldmap(self, dt): pass
    def draw_worldmap(self, t):
        self.screen.fill(hsv_to_rgb(math.sin(t)*180+180, 0.6, 0.8))
        txt = self.bigfont.render(f'World {self.sel_world}', True, (255,255,255))
        self.screen.blit(txt, (SCREEN_WIDTH//2-txt.get_width()//2, SCREEN_HEIGHT//2-40))
        hint = self.font.render('←/→/↑/↓ + Enter', True, (255,255,255))
        self.screen.blit(hint, (SCREEN_WIDTH//2-hint.get_width()//2, SCREEN_HEIGHT-60))

    # LEVELSELECT Scene
    def handle_levelselect(self, e):
        if e.type != pygame.KEYDOWN: return
        if e.key == pygame.K_LEFT:
            self.sel_level = (self.sel_level - 2) % LEVELS_PER_WORLD + 1
        elif e.key == pygame.K_RIGHT:
            self.sel_level = self.sel_level % LEVELS_PER_WORLD + 1
        elif e.key == pygame.K_RETURN:
            self.level = self.sel_level
            self.switch(SceneID.GAMEPLAY)
        elif e.key == pygame.K_ESCAPE:
            self.switch(SceneID.WORLDMAP)
    def update_levelselect(self, dt): pass
    def draw_levelselect(self, t):
        self.screen.fill(hsv_to_rgb(math.sin(t)*180+180, 0.6, 0.8))
        txt = self.bigfont.render(f'World {self.world} – Level {self.sel_level}', True, (255,255,255))
        self.screen.blit(txt, (SCREEN_WIDTH//2-txt.get_width()//2, SCREEN_HEIGHT//2-40))
        hint = self.font.render('←/→ to change, Enter to play', True, (255,255,255))
        self.screen.blit(hint, (SCREEN_WIDTH//2-hint.get_width()//2, SCREEN_HEIGHT-60))

    # GAMEPLAY Scene
    def load_tmx_or_generate(self, world, level):
        path = os.path.join(MAP_DIR, f'world{world}', f'level{level}.tmx')
        if os.path.isfile(path) and path not in self.tmx_cache:
            self.tmx_cache[path] = load_pygame(path)
            return self.tmx_cache[path]
        elif path in self.tmx_cache:
            return self.tmx_cache[path]
        else:
            class FakeTMX:
                width, height = 40, 20
                class Layer:
                    def __init__(self, name): self.name = name
                    def tiles(self):
                        if self.name == SOLID_LAYER_NAME:
                            for i in range(40):
                                yield (i, 19, 1)  # Ground
                            yield (5, 15, 1); yield (6, 15, 1)
                            yield (10, 12, 1); yield (11, 12, 1)
                visible_layers = [Layer('Background'), Layer(SOLID_LAYER_NAME)]
                def get_tile_image_by_gid(self, gid):
                    return None
            return FakeTMX()

    def enter_gameplay(self):
        self.tmx = self.load_tmx_or_generate(self.world, self.level)
        self.solids = []
        for layer in self.tmx.visible_layers:
            if hasattr(layer, 'tiles') and layer.name == SOLID_LAYER_NAME:
                for x, y, gid in layer.tiles():
                    rect = pygame.Rect(x*TILE, y*TILE, TILE, TILE)
                    self.solids.append(rect)
        self.player = Player(64, SCREEN_HEIGHT-200)
        self.cam_x = 0

    def handle_gameplay(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.switch(SceneID.LEVELSELECT)
    def update_gameplay(self, dt):
        self.player.update(dt, self.solids)
        self.cam_x = max(0, self.player.rect.centerx - SCREEN_WIDTH//3)
    def draw_gameplay(self, t):
        self.screen.fill((0, 0, 0))  # Clear with black to let tiles stand out
        for layer in self.tmx.visible_layers:
            if hasattr(layer, 'tiles'):
                is_solid = layer.name == SOLID_LAYER_NAME
                for x, y, gid in layer.tiles():
                    img = self.tmx.get_tile_image_by_gid(gid) if hasattr(self.tmx, 'get_tile_image_by_gid') else None
                    if img:
                        self.screen.blit(img, (x * TILE - self.cam_x, y * TILE))
                    else:
                        hue = (math.sin(t + x*0.1 + y*0.1)*180 + 180) % 360
                        color = hsv_to_rgb(hue, 0.7 if is_solid else 0.5, 0.8)
                        rect = pygame.Rect(x*TILE - self.cam_x, y*TILE, TILE, TILE)
                        pygame.draw.rect(self.screen, color, rect)
                        pygame.draw.rect(self.screen, (255,255,255), rect, 1)
        # Draw player
        self.player.image.fill((0,0,0,0))
        player_hue = (math.sin(t)*180 + 180) % 360
        pygame.draw.rect(self.player.image, hsv_to_rgb(player_hue, 0.6, 1.0), (0, 0, TILE, TILE*1.5), 2)
        self.screen.blit(self.player.image, (self.player.rect.x - self.cam_x, self.player.rect.y))
        # Vibe overlay
        vibe_color = hsv_to_rgb(math.sin(t)*180+180, 0.6, 0.8)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((*vibe_color, 50))  # Alpha 50 for subtle effect
        self.screen.blit(overlay, (0, 0))
        # HUD
        hud = self.font.render(f'W{self.world}-L{self.level}', True, (255,255,255))
        self.screen.blit(hud, (10, 10))

# Startup
if __name__ == '__main__':
    Game().run()

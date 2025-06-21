"""
Legend of Zelda‑style 2‑D prototype
-----------------------------------
• Zero external assets: every sprite/animation is procedurally generated.
• Tkinter front‑end → launches or restarts the Pygame window.
• Clean OOP structure ready for expansion: Player, Enemy, Sword, TileMap.
Tested on Python 3.13‑dev (works on 3.11+ as well).
"""

# ─────────────────────────── imports ────────────────────────────
import sys
import random
import threading
import tkinter as tk
from dataclasses import dataclass

import pygame as pg

# ────────────────────────── constants ───────────────────────────
TILE      = 32                        # logical tile size (px)
MAP_W, MAP_H = 20, 15                 # logical map dimensions (tiles)
SCREEN_W, SCREEN_H = MAP_W*TILE, MAP_H*TILE
FPS       = 60
PLAYER_SPEED = 3                      # px per frame
ENEMY_SPEED  = 2
ATTACK_CD    = 300                    # sword cooldown in ms
SWORD_LEN    = 16                     # sword reach

# palette
GREEN  = ( 48,182, 65)
DARK_G = ( 22, 92, 33)
RED    = (205,  60, 45)
YELLOW = (252, 232,132)
GRAY   = (120,120,120)
BLACK  = (  0,  0,  0)

# ────────────────────────── helpers ─────────────────────────────
def load_map():
    """Generate a simple random walkable/blocked map (0=walkable,1=wall)."""
    grid = [[0 for _ in range(MAP_W)] for _ in range(MAP_H)]
    # border walls
    for x in range(MAP_W):
        grid[0][x] = grid[MAP_H-1][x] = 1
    for y in range(MAP_H):
        grid[y][0] = grid[y][MAP_W-1] = 1
    # random obstacles
    for _ in range(int(MAP_W*MAP_H*0.10)):
        x, y = random.randrange(1, MAP_W-1), random.randrange(1, MAP_H-1)
        grid[y][x] = 1
    return grid

def rect_from_tile(tx, ty):
    """Return Pygame Rect for given tile coords."""
    return pg.Rect(tx*TILE, ty*TILE, TILE, TILE)

# ───────────────────────── game objects ─────────────────────────
@dataclass
class Entity:
    x: float
    y: float
    size: int
    color: tuple

    @property
    def rect(self):
        return pg.Rect(int(self.x), int(self.y), self.size, self.size)

    def draw(self, surf):
        pg.draw.rect(surf, self.color, self.rect)

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, TILE//2, GREEN)
        self.last_attack = -ATTACK_CD
        self.facing = pg.Vector2(0, -1)

    def handle_input(self, keys):
        vel = pg.Vector2(0, 0)
        if keys[pg.K_LEFT] or keys[pg.K_a]:
            vel.x = -PLAYER_SPEED
            self.facing = pg.Vector2(-1, 0)
        if keys[pg.K_RIGHT] or keys[pg.K_d]:
            vel.x = PLAYER_SPEED
            self.facing = pg.Vector2(1, 0)
        if keys[pg.K_UP] or keys[pg.K_w]:
            vel.y = -PLAYER_SPEED
            self.facing = pg.Vector2(0, -1)
        if keys[pg.K_DOWN] or keys[pg.K_s]:
            vel.y = PLAYER_SPEED
            self.facing = pg.Vector2(0, 1)
        return vel

class Enemy(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, TILE//2, RED)
        self.direction = pg.Vector2(random.choice([-1,1]), 0).normalize()

    def update(self, walls):
        # simple bounce AI
        move = self.direction * ENEMY_SPEED
        next_rect = self.rect.move(move)
        if any(next_rect.colliderect(w) for w in walls):
            self.direction = -self.direction
        else:
            self.x += move.x
            self.y += move.y

class Sword:
    """Transient hitbox in front of the player."""
    def __init__(self, player):
        self.player = player
        self.dir = player.facing
        self.rect = pg.Rect(0, 0, SWORD_LEN, SWORD_LEN)
        self.position()

    def position(self):
        # place in front of player
        p = self.player.rect.center
        offset = self.dir * (self.player.size//2 + SWORD_LEN//2)
        self.rect.center = (p[0]+offset.x, p[1]+offset.y)

    def draw(self, surf):
        pg.draw.rect(surf, YELLOW, self.rect)

# ─────────────────────────── engine ─────────────────────────────
class ZeldaLike:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((SCREEN_W, SCREEN_H))
        pg.display.set_caption("Zelda‑Like Prototype (no assets)")
        self.clock = pg.time.Clock()
        self.map = load_map()
        self.player = Player(TILE*2, TILE*2)
        self.enemies = [Enemy(TILE*random.randrange(3,MAP_W-3),
                              TILE*random.randrange(3,MAP_H-3))
                        for _ in range(5)]
        self.walls = [rect_from_tile(x, y)
                      for y,row in enumerate(self.map)
                      for x,val in enumerate(row) if val == 1]
        self.sword = None
        self.running = True

    # ─────────── game loop ────────────
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS)
            self.handle_events()
            self.update(dt)
            self.draw()
        pg.quit()

    def handle_events(self):
        for ev in pg.event.get():
            if ev.type == pg.QUIT:
                self.running = False
            elif ev.type == pg.KEYDOWN and ev.key == pg.K_SPACE:
                # attack if cooldown elapsed
                now = pg.time.get_ticks()
                if now - self.player.last_attack >= ATTACK_CD:
                    self.sword = Sword(self.player)
                    self.player.last_attack = now

    def update(self, dt):
        keys = pg.key.get_pressed()
        vel = self.player.handle_input(keys)
        self._move_entity(self.player, vel)

        for e in self.enemies:
            e.update(self.walls)

        # sword lifetime 100 ms
        if self.sword and pg.time.get_ticks() - self.player.last_attack > 100:
            self.sword = None
        elif self.sword:
            self.sword.position()
            # enemy collision
            for e in self.enemies[:]:
                if self.sword.rect.colliderect(e.rect):
                    self.enemies.remove(e)

    def _move_entity(self, ent, vel):
        # naive axis‑separated movement
        for axis in (0, 1):
            move = [0,0]
            move[axis] = vel[axis]
            next_rect = ent.rect.move(*move)
            if any(next_rect.colliderect(w) for w in self.walls):
                continue
            if axis == 0:
                ent.x += vel.x
            else:
                ent.y += vel.y

    # ─────────── rendering ────────────
    def draw(self):
        self.screen.fill(DARK_G)
        # draw tiles
        for y,row in enumerate(self.map):
            for x,val in enumerate(row):
                if val == 1:
                    pg.draw.rect(self.screen, GRAY,
                                 rect_from_tile(x, y))
        # draw entities
        self.player.draw(self.screen)
        for e in self.enemies:
            e.draw(self.screen)
        if self.sword: self.sword.draw(self.screen)

        # HUD
        txt = f"Enemies left: {len(self.enemies)} | SPACE=Attack"
        self._blit_text(txt, 5, 5)
        pg.display.flip()

    def _blit_text(self, text, x, y):
        font = pg.font.SysFont("consolas", 16, bold=True)
        surf = font.render(text, True, (255,255,255))
        self.screen.blit(surf, (x, y))

# ─────────────────────────── tkinter ────────────────────────────
def launch_game():
    root.destroy()
    game = ZeldaLike()
    game.run()

root = tk.Tk()
root.title("Zelda‑Like Launcher")
tk.Label(root, text="Legend‑of‑Zelda‑Style Prototype",
         font=("Consolas", 14, "bold")).pack(padx=20, pady=10)
tk.Button(root, text="Start Game", width=20, command=launch_game).pack(pady=10)
tk.Button(root, text="Quit", width=20, command=root.destroy).pack(pady=5)

# run Tkinter in the main thread; Pygame after root.destroy()
root.mainloop()

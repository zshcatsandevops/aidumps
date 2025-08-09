#!/usr/bin/env python3
# Super Mario Bros Forever - Files-Off Edition
# SMB1 physics, SMB3 Boom Boom bosses, NSMB Wii castle themes
# 6 worlds, deterministic procedural generation, 60 FPS
#
# Controls:
#   TITLE:  Type a seed code, Enter = start, Tab = randomize
#   MAP:    Arrows/WASD select world/stage, Enter = play, Esc = title
#   LEVEL:  Arrows/A/D move, Space/Up/W jump, Shift = run, P = pause
#           R = restart level, F8 = unlock all, F9 = relock
# 
# (c) 2025 Mushroom Kingdom Vibes. Files-off, pure Python/Pygame.

import os, sys, math, random, time, colorsys
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
from array import array

# ----------------------------- constants -------------------------------------
SCREEN_W, SCREEN_H = 960, 540   # 16:9 but SMB1 feel
TILE = 32
FPS = 60
DT = 1 / FPS

# SMB1 physics
GRAVITY = 0.50
JUMP_VEL = -11.5
JUMP_VEL_RUNNING = -12.8
MAX_WALK_SPEED = 3.5
MAX_RUN_SPEED = 6.5
ACCEL = 0.35
RUN_ACCEL = 0.5
FRICTION = 0.89
SKID_FRICTION = 0.95

WORLD_COUNT = 6
STAGES_PER_WORLD = 4  # 3 levels + castle boss
CASTLE_STAGE_INDEX = 3

DEFAULT_SEED = "MUSHROOM-KINGDOM-1985"

# SMB1 color palettes per world
WORLD_PALETTES = [
    # World 1 (Grassland)
    {"sky": (107, 140, 255), "ground": (228, 92, 16), "pipe": (0, 168, 0), "block": (255, 144, 0)},
    # World 2 (Desert) 
    {"sky": (255, 219, 140), "ground": (204, 96, 12), "pipe": (168, 145, 60), "block": (255, 168, 68)},
    # World 3 (Ocean/Beach)
    {"sky": (32, 192, 255), "ground": (255, 206, 84), "pipe": (0, 147, 156), "block": (144, 252, 252)},
    # World 4 (Giant Land)
    {"sky": (168, 255, 168), "ground": (139, 69, 19), "pipe": (34, 139, 34), "block": (144, 238, 144)},
    # World 5 (Sky)
    {"sky": (224, 248, 255), "ground": (255, 255, 255), "pipe": (135, 206, 235), "block": (255, 182, 193)},
    # World 6 (Lava/Castle)
    {"sky": (48, 0, 48), "ground": (139, 0, 0), "pipe": (105, 105, 105), "block": (178, 34, 34)},
]

# ----------------------------- util ------------------------------------------
def seed_from_string(s: str) -> int:
    val = 0x9E3779B97F4A7C15
    for i, ch in enumerate(s.strip().upper()):
        v = (ord(ch) * (i + 1)) & 0xFFFFFFFF
        val ^= (v + 0x9E3779B97F4A7C15 + ((val << 6) & 0xFFFFFFFF) + (val >> 2))
        val &= 0x7FFFFFFF
    return val if val else 0xC0FFEE

def clamp(v, lo, hi): return max(lo, min(hi, v))
def lerp(a, b, t): return a + (b - a) * t

# ----------------------------- audio (procedural) ----------------------------
class AudioEngine:
    def __init__(self):
        self.ok = False
        try:
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
            self.ok = True
        except:
            self.ok = False
        self.cache = {}

    def square_wave(self, freq=440, ms=100, volume=0.3):
        if not self.ok: return None
        key = ('square', freq, ms, volume)
        if key in self.cache: return self.cache[key]
        
        samples = int(22050 * ms / 1000)
        buf = array('h', [0] * samples)
        period = 22050 / freq
        
        for i in range(samples):
            # Envelope
            env = 1.0
            if i < samples * 0.1:  # Attack
                env = i / (samples * 0.1)
            elif i > samples * 0.8:  # Release
                env = (samples - i) / (samples * 0.2)
            
            # Square wave
            val = 1.0 if (i % period) < (period / 2) else -1.0
            buf[i] = int(val * env * volume * 32767)
        
        snd = pygame.mixer.Sound(buffer=buf)
        self.cache[key] = snd
        return snd

    def play_jump(self):
        if s := self.square_wave(400, 200, 0.25):
            s.play()

    def play_coin(self):
        if s := self.square_wave(988, 150, 0.2):
            s.play()

    def play_stomp(self):
        if s := self.square_wave(200, 100, 0.3):
            s.play()

    def play_powerup(self):
        if s := self.square_wave(600, 400, 0.25):
            s.play()

    def play_pipe(self):
        if s := self.square_wave(300, 300, 0.2):
            s.play()

    def play_death(self):
        if s := self.square_wave(150, 500, 0.3):
            s.play()

# ----------------------------- sprites (procedural) --------------------------
def draw_mario(surf, x, y, small=True, facing_right=True, frame=0):
    """Draw SMB1-style Mario sprite procedurally"""
    if small:
        # Small Mario (16x16)
        # Hat
        pygame.draw.rect(surf, (228, 92, 16), (x+2, y, 12, 4))
        # Face
        pygame.draw.rect(surf, (255, 206, 150), (x+3, y+4, 10, 6))
        # Shirt
        pygame.draw.rect(surf, (228, 92, 16), (x+2, y+10, 12, 4))
        # Overalls
        pygame.draw.rect(surf, (0, 0, 255), (x+2, y+14, 12, 2))
        # Eyes
        if facing_right:
            pygame.draw.rect(surf, (0, 0, 0), (x+9, y+5, 2, 2))
        else:
            pygame.draw.rect(surf, (0, 0, 0), (x+5, y+5, 2, 2))
    else:
        # Big Mario (16x32)
        # Hat
        pygame.draw.rect(surf, (228, 92, 16), (x+2, y, 12, 6))
        # Face
        pygame.draw.rect(surf, (255, 206, 150), (x+3, y+6, 10, 8))
        # Shirt
        pygame.draw.rect(surf, (228, 92, 16), (x+2, y+14, 12, 8))
        # Overalls
        pygame.draw.rect(surf, (0, 0, 255), (x+2, y+22, 12, 10))
        # Eyes
        if facing_right:
            pygame.draw.rect(surf, (0, 0, 0), (x+9, y+8, 2, 2))
        else:
            pygame.draw.rect(surf, (0, 0, 0), (x+5, y+8, 2, 2))

def draw_goomba(surf, x, y, squished=False, frame=0):
    """Draw SMB1-style Goomba sprite"""
    if squished:
        pygame.draw.rect(surf, (139, 69, 19), (x, y+12, 16, 4))
    else:
        # Body
        pygame.draw.ellipse(surf, (139, 69, 19), (x, y, 16, 14))
        # Feet (animated walk)
        foot_offset = 2 if (frame // 8) % 2 == 0 else -2
        pygame.draw.rect(surf, (0, 0, 0), (x+2+foot_offset, y+12, 4, 4))
        pygame.draw.rect(surf, (0, 0, 0), (x+10-foot_offset, y+12, 4, 4))
        # Eyes
        pygame.draw.rect(surf, (0, 0, 0), (x+4, y+4, 2, 4))
        pygame.draw.rect(surf, (0, 0, 0), (x+10, y+4, 2, 4))

def draw_koopa(surf, x, y, color=(0, 168, 0), frame=0):
    """Draw SMB1-style Koopa Troopa sprite"""
    # Shell
    pygame.draw.ellipse(surf, color, (x+2, y+4, 12, 10))
    # Head
    pygame.draw.ellipse(surf, (255, 206, 150), (x, y, 8, 8))
    # Feet
    foot_offset = 1 if (frame // 10) % 2 == 0 else -1
    pygame.draw.rect(surf, (255, 144, 0), (x+3+foot_offset, y+14, 3, 2))
    pygame.draw.rect(surf, (255, 144, 0), (x+10-foot_offset, y+14, 3, 2))

def draw_boom_boom(surf, x, y, frame=0, hurt=False):
    """Draw SMB3-style Boom Boom boss"""
    # Main body (larger Koopa-like)
    body_color = (255, 255, 255) if hurt else (168, 145, 60)
    # Shell/body
    pygame.draw.ellipse(surf, body_color, (x, y+8, 32, 24))
    # Spikes on shell
    if not hurt:
        for i in range(3):
            spike_x = x + 6 + i * 10
            pygame.draw.polygon(surf, (255, 255, 255), [
                (spike_x, y+12),
                (spike_x-3, y+18),
                (spike_x+3, y+18)
            ])
    # Head
    pygame.draw.ellipse(surf, (255, 206, 150), (x+8, y, 16, 16))
    # Arms (swinging animation)
    arm_angle = math.sin(frame * 0.15) * 0.3
    pygame.draw.ellipse(surf, body_color, (x-4 + math.cos(arm_angle)*4, y+10, 8, 12))
    pygame.draw.ellipse(surf, body_color, (x+28 - math.cos(arm_angle)*4, y+10, 8, 12))
    # Eyes
    pygame.draw.rect(surf, (255, 0, 0) if hurt else (0, 0, 0), (x+10, y+4, 3, 3))
    pygame.draw.rect(surf, (255, 0, 0) if hurt else (0, 0, 0), (x+19, y+4, 3, 3))
    # Feet
    foot_offset = 2 if (frame // 6) % 2 == 0 else -2
    pygame.draw.rect(surf, (255, 144, 0), (x+6+foot_offset, y+30, 6, 4))
    pygame.draw.rect(surf, (255, 144, 0), (x+20-foot_offset, y+30, 6, 4))

def draw_pipe(surf, x, y, height, color):
    """Draw SMB1-style pipe"""
    # Pipe body
    pygame.draw.rect(surf, color, (x+4, y+TILE, TILE-8, height-TILE))
    pygame.draw.rect(surf, tuple(int(c*0.7) for c in color), (x+4, y+TILE, 4, height-TILE))
    # Pipe top
    pygame.draw.rect(surf, color, (x, y, TILE, TILE))
    pygame.draw.rect(surf, tuple(int(c*0.7) for c in color), (x, y, 4, TILE))
    pygame.draw.rect(surf, tuple(int(c*1.2) for c in color[:3]) if max(color)*1.2 <= 255 else (255,255,255), 
                     (x+TILE-4, y+4, 4, TILE-8))

def draw_castle_block(surf, x, y, dark=False):
    """Draw NSMB Wii-style castle block"""
    base = (64, 64, 64) if dark else (128, 128, 128)
    highlight = (96, 96, 96) if dark else (160, 160, 160)
    shadow = (32, 32, 32) if dark else (96, 96, 96)
    
    pygame.draw.rect(surf, base, (x, y, TILE, TILE))
    pygame.draw.rect(surf, highlight, (x, y, TILE-2, 2))
    pygame.draw.rect(surf, highlight, (x, y, 2, TILE-2))
    pygame.draw.rect(surf, shadow, (x+2, y+TILE-2, TILE-2, 2))
    pygame.draw.rect(surf, shadow, (x+TILE-2, y+2, 2, TILE-2))

# ----------------------------- entities --------------------------------------
class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 14, 14)  # Small Mario size
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.facing_right = True
        self.running = False
        self.big = False
        self.invincible = 0
        self.coins = 0
        self.lives = 3
        self.anim_frame = 0

    def update_input(self, keys):
        # Running
        self.running = keys[pygame.K_LSHIFT] or keys[pygame.K_x]
        
        # Movement
        max_speed = MAX_RUN_SPEED if self.running else MAX_WALK_SPEED
        accel = RUN_ACCEL if self.running else ACCEL
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx -= accel
            self.facing_right = False
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx += accel
            self.facing_right = True
        else:
            self.vx *= FRICTION
        
        # Clamp speed
        self.vx = clamp(self.vx, -max_speed, max_speed)
        
        # Jump
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.vy = JUMP_VEL_RUNNING if self.running else JUMP_VEL
            self.on_ground = False

    def apply_physics(self):
        self.vy += GRAVITY
        if self.vy > 15: self.vy = 15
        if self.invincible > 0: self.invincible -= 1
        if abs(self.vx) > 0.1: self.anim_frame += 1

    def move_and_collide(self, level):
        # Horizontal movement
        self.rect.x += int(self.vx)
        for tile in level.get_solid_tiles_near(self.rect):
            if self.rect.colliderect(tile):
                if self.vx > 0: 
                    self.rect.right = tile.left
                else: 
                    self.rect.left = tile.right
                self.vx = 0

        # Vertical movement
        self.rect.y += int(self.vy)
        self.on_ground = False
        for tile in level.get_solid_tiles_near(self.rect):
            if self.rect.colliderect(tile):
                if self.vy > 0:
                    self.rect.bottom = tile.top
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:
                    self.rect.top = tile.bottom
                    self.vy = 0

    def get_hurt(self):
        if self.invincible > 0: return False
        if self.big:
            self.big = False
            self.rect.h = 14
            self.invincible = 90
            return False
        return True  # Dead

    def draw(self, surf, cam_x, frame):
        if self.invincible > 0 and frame % 4 < 2:
            return  # Flashing
        x = self.rect.x - cam_x
        y = self.rect.y
        draw_mario(surf, x, y, not self.big, self.facing_right, self.anim_frame)

class Goomba:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 16, 16)
        self.vx = -1.0
        self.vy = 0
        self.alive = True
        self.squish_timer = 0

    def update(self, level):
        if not self.alive:
            self.squish_timer -= 1
            return
        
        # Apply gravity
        self.vy += GRAVITY
        if self.vy > 10: self.vy = 10
        
        # Move horizontally
        self.rect.x += int(self.vx)
        for tile in level.get_solid_tiles_near(self.rect):
            if self.rect.colliderect(tile):
                self.vx *= -1
                if self.vx > 0:
                    self.rect.right = tile.left
                else:
                    self.rect.left = tile.right
        
        # Move vertically
        self.rect.y += int(self.vy)
        for tile in level.get_solid_tiles_near(self.rect):
            if self.rect.colliderect(tile) and self.vy > 0:
                self.rect.bottom = tile.top
                self.vy = 0

    def stomp(self):
        self.alive = False
        self.squish_timer = 30

    def draw(self, surf, cam_x, frame):
        if self.squish_timer <= 0 and not self.alive: return
        x = self.rect.x - cam_x
        y = self.rect.y
        draw_goomba(surf, x, y, not self.alive, frame)

class KoopaTroopa:
    def __init__(self, x, y, color=(0, 168, 0)):
        self.rect = pygame.Rect(x, y, 16, 20)
        self.vx = -1.0
        self.vy = 0
        self.color = color
        self.shell_mode = False
        self.shell_moving = False

    def update(self, level):
        # Apply gravity
        self.vy += GRAVITY
        if self.vy > 10: self.vy = 10
        
        # Move horizontally
        if self.shell_mode and not self.shell_moving:
            self.vx = 0
        elif self.shell_mode and self.shell_moving:
            self.vx = clamp(self.vx, -8, 8)
        
        self.rect.x += int(self.vx)
        for tile in level.get_solid_tiles_near(self.rect):
            if self.rect.colliderect(tile):
                if not self.shell_mode or self.shell_moving:
                    self.vx *= -1
                if self.vx > 0:
                    self.rect.right = tile.left
                else:
                    self.rect.left = tile.right
        
        # Move vertically
        self.rect.y += int(self.vy)
        for tile in level.get_solid_tiles_near(self.rect):
            if self.rect.colliderect(tile) and self.vy > 0:
                self.rect.bottom = tile.top
                self.vy = 0

    def stomp(self):
        if not self.shell_mode:
            self.shell_mode = True
            self.shell_moving = False
            self.rect.h = 16
        elif not self.shell_moving:
            self.shell_moving = True
            self.vx = 7.0

    def draw(self, surf, cam_x, frame):
        x = self.rect.x - cam_x
        y = self.rect.y
        if self.shell_mode:
            pygame.draw.ellipse(surf, self.color, (x, y+4, 16, 12))
        else:
            draw_koopa(surf, x, y, self.color, frame)

class BoomBoom:
    def __init__(self, arena_center):
        self.rect = pygame.Rect(arena_center[0], arena_center[1], 32, 34)
        self.vx = 0
        self.vy = 0
        self.hp = 3
        self.state = "idle"  # idle, jumping, hurt, defeated
        self.state_timer = 0
        self.invincible = 0
        self.jump_cooldown = 0
        self.arena_center = arena_center
        self.facing_right = True

    def update(self, level, player, audio):
        # Physics
        self.vy += GRAVITY * 0.8
        if self.vy > 12: self.vy = 12
        
        # State machine
        if self.state == "defeated":
            self.vy += GRAVITY
            self.rect.y += int(self.vy)
            return
        
        if self.invincible > 0:
            self.invincible -= 1
        
        if self.state == "hurt":
            self.state_timer -= 1
            if self.state_timer <= 0:
                self.state = "idle"
        
        # AI behavior
        if self.state == "idle":
            # Face player
            self.facing_right = player.rect.centerx > self.rect.centerx
            
            # Jump toward player
            if self.jump_cooldown <= 0:
                dx = player.rect.centerx - self.rect.centerx
                if abs(dx) < 300:
                    self.state = "jumping"
                    self.vy = -10
                    self.vx = clamp(dx / 40, -4, 4)
                    self.jump_cooldown = 60
        
        if self.jump_cooldown > 0:
            self.jump_cooldown -= 1
        
        # Movement
        self.rect.x += int(self.vx)
        for tile in level.get_solid_tiles_near(self.rect):
            if self.rect.colliderect(tile):
                if self.vx > 0:
                    self.rect.right = tile.left
                else:
                    self.rect.left = tile.right
                self.vx = 0
        
        self.rect.y += int(self.vy)
        on_ground = False
        for tile in level.get_solid_tiles_near(self.rect):
            if self.rect.colliderect(tile):
                if self.vy > 0:
                    self.rect.bottom = tile.top
                    self.vy = 0
                    on_ground = True
                    if self.state == "jumping":
                        self.state = "idle"
                        self.vx *= 0.5
                elif self.vy < 0:
                    self.rect.top = tile.bottom
                    self.vy = 0
        
        # Check stomp
        if self.rect.colliderect(player.rect) and self.invincible == 0:
            if player.vy > 0 and player.rect.bottom < self.rect.centery:
                # Stomped
                self.hp -= 1
                self.invincible = 60
                self.state = "hurt"
                self.state_timer = 30
                player.vy = JUMP_VEL * 0.8
                
                if audio:
                    audio.play_stomp()
                
                if self.hp <= 0:
                    self.state = "defeated"
                    self.vy = -8
                    if audio:
                        audio.play_powerup()
            else:
                # Hurt player
                return True
        
        return False

    def draw(self, surf, cam_x, frame):
        if self.invincible > 0 and frame % 4 < 2:
            return
        x = self.rect.x - cam_x
        y = self.rect.y
        hurt = self.state == "hurt"
        draw_boom_boom(surf, x, y, frame, hurt)

# ----------------------------- level -----------------------------------------
class Level:
    def __init__(self, seed, world_idx, stage_idx):
        self.rng = random.Random(seed)
        self.world_idx = world_idx
        self.stage_idx = stage_idx
        self.is_castle = (stage_idx == CASTLE_STAGE_INDEX)
        
        self.width = 30 if self.is_castle else 200
        self.height = 17
        self.tiles = {}  # (x, y): tile_type
        self.spawn = (2 * TILE, 10 * TILE)
        self.goal = None
        self.enemies = []
        self.boss = None
        
        self.generate()

    def generate(self):
        if self.is_castle:
            self.generate_castle()
        else:
            self.generate_overworld()

    def generate_overworld(self):
        """Generate SMB1-style overworld level"""
        ground_y = 13
        
        # Base ground
        for x in range(self.width):
            for y in range(ground_y, self.height):
                self.tiles[(x, y)] = 'ground'
        
        # Add features
        x = 5
        while x < self.width - 10:
            feature = self.rng.choice(['gap', 'pipe', 'blocks', 'stairs', 'enemies'])
            
            if feature == 'gap':
                gap_width = self.rng.randint(2, 4)
                for gx in range(x, min(x + gap_width, self.width)):
                    for y in range(ground_y, self.height):
                        if (gx, y) in self.tiles:
                            del self.tiles[(gx, y)]
                x += gap_width + 2
                
            elif feature == 'pipe':
                pipe_height = self.rng.randint(2, 5)
                for py in range(ground_y - pipe_height, ground_y):
                    self.tiles[(x, py)] = 'pipe'
                x += 3
                
            elif feature == 'blocks':
                block_y = ground_y - self.rng.randint(3, 6)
                block_width = self.rng.randint(3, 8)
                for bx in range(block_width):
                    if self.rng.random() < 0.7:
                        self.tiles[(x + bx, block_y)] = 'brick'
                x += block_width + 2
                
            elif feature == 'stairs':
                stair_height = self.rng.randint(2, 4)
                for i in range(stair_height):
                    for sy in range(ground_y - i - 1, ground_y):
                        self.tiles[(x + i, sy)] = 'brick'
                for i in range(stair_height):
                    for sy in range(ground_y - stair_height + i + 1, ground_y):
                        self.tiles[(x + stair_height + i, sy)] = 'brick'
                x += stair_height * 2 + 2
                
            elif feature == 'enemies':
                # Place enemies
                for i in range(self.rng.randint(1, 3)):
                    enemy_x = (x + i * 2) * TILE
                    enemy_y = (ground_y - 1) * TILE
                    if self.rng.random() < 0.6:
                        self.enemies.append(Goomba(enemy_x, enemy_y))
                    else:
                        color = (0, 168, 0) if self.world_idx < 3 else (255, 0, 0)
                        self.enemies.append(KoopaTroopa(enemy_x, enemy_y, color))
                x += 6
        
        # Goal flag/castle
        self.goal = pygame.Rect((self.width - 5) * TILE, (ground_y - 10) * TILE, TILE, 10 * TILE)

    def generate_castle(self):
        """Generate NSMB Wii-style castle level with Boom Boom arena"""
        # Castle walls
        for y in range(self.height):
            self.tiles[(0, y)] = 'castle_wall'
            self.tiles[(self.width - 1, y)] = 'castle_wall'
        
        # Castle floor with lava gaps
        floor_y = 13
        for x in range(self.width):
            if x < 8 or x > self.width - 8:  # Solid floor at edges
                for y in range(floor_y, self.height):
                    self.tiles[(x, y)] = 'castle_floor'
            elif self.rng.random() < 0.7:  # Random lava gaps
                for y in range(floor_y, self.height):
                    self.tiles[(x, y)] = 'castle_floor'
        
        # Platforms for boss fight
        platform_positions = [
            (5, 9), (10, 7), (15, 9), (20, 7), (25, 9)
        ]
        for px, py in platform_positions:
            if px < self.width - 3:
                for i in range(3):
                    self.tiles[(px + i, py)] = 'castle_platform'
        
        # Moving platforms (static for simplicity)
        for i in range(2):
            px = 8 + i * 12
            py = 10 - i * 2
            for j in range(4):
                self.tiles[(px + j, py)] = 'castle_platform'
        
        # Boss
        arena_center = (self.width * TILE // 2, floor_y * TILE - 100)
        self.boss = BoomBoom(arena_center)
        
        # Spawn point
        self.spawn = (3 * TILE, (floor_y - 2) * TILE)

    def get_solid_tiles_near(self, rect):
        """Get solid tiles near a rect for collision"""
        tiles = []
        x0 = max(0, rect.left // TILE - 1)
        x1 = min(self.width, rect.right // TILE + 2)
        y0 = max(0, rect.top // TILE - 1)
        y1 = min(self.height, rect.bottom // TILE + 2)
        
        for y in range(y0, y1):
            for x in range(x0, x1):
                if (x, y) in self.tiles:
                    tiles.append(pygame.Rect(x * TILE, y * TILE, TILE, TILE))
        return tiles

    def update(self, player, audio):
        # Update enemies
        for enemy in self.enemies:
            enemy.update(self)
            
            # Check collision with player
            if enemy.rect.colliderect(player.rect):
                if isinstance(enemy, Goomba) and enemy.alive:
                    if player.vy > 0 and player.rect.bottom < enemy.rect.centery:
                        enemy.stomp()
                        player.vy = JUMP_VEL * 0.5
                        player.coins += 1
                        if audio: audio.play_stomp()
                    elif player.get_hurt():
                        return "dead"
                        
                elif isinstance(enemy, KoopaTroopa):
                    if player.vy > 0 and player.rect.bottom < enemy.rect.centery:
                        enemy.stomp()
                        player.vy = JUMP_VEL * 0.5
                        if audio: audio.play_stomp()
                    elif enemy.shell_moving and player.get_hurt():
                        return "dead"
                    elif not enemy.shell_mode and player.get_hurt():
                        return "dead"
        
        # Update boss
        if self.boss:
            if self.boss.update(self, player, audio):
                if player.get_hurt():
                    return "dead"
            if self.boss.state == "defeated" and self.boss.rect.y > SCREEN_H:
                return "complete"
        
        # Check goal
        if self.goal and player.rect.colliderect(self.goal):
            return "complete"
        
        # Check fall death
        if player.rect.y > self.height * TILE:
            return "dead"
        
        return None

    def draw(self, surf, cam_x, world_idx):
        palette = WORLD_PALETTES[world_idx]
        
        # Background
        surf.fill(palette["sky"])
        
        # Draw tiles
        for (x, y), tile_type in self.tiles.items():
            draw_x = x * TILE - cam_x
            if draw_x < -TILE or draw_x > SCREEN_W:
                continue
            
            draw_y = y * TILE
            
            if tile_type == 'ground':
                pygame.draw.rect(surf, palette["ground"], (draw_x, draw_y, TILE, TILE))
                # Brick pattern
                pygame.draw.rect(surf, (0, 0, 0), (draw_x, draw_y, TILE, 1))
                pygame.draw.rect(surf, (0, 0, 0), (draw_x + TILE//2, draw_y, 1, TILE//2))
                pygame.draw.rect(surf, (0, 0, 0), (draw_x, draw_y + TILE//2, TILE, 1))
                
            elif tile_type == 'brick':
                pygame.draw.rect(surf, palette["block"], (draw_x, draw_y, TILE, TILE))
                # Brick lines
                for i in range(4):
                    pygame.draw.rect(surf, (0, 0, 0), (draw_x, draw_y + i * 8, TILE, 1))
                    pygame.draw.rect(surf, (0, 0, 0), (draw_x + (i % 2) * 16, draw_y, 1, TILE))
                    
            elif tile_type == 'pipe':
                draw_pipe(surf, draw_x, draw_y, TILE * 2, palette["pipe"])
                
            elif tile_type.startswith('castle'):
                draw_castle_block(surf, draw_x, draw_y, tile_type == 'castle_wall')
        
        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(surf, cam_x, self.world_idx * 10)
        
        # Draw boss
        if self.boss:
            self.boss.draw(surf, cam_x, self.world_idx * 10)
        
        # Draw goal
        if self.goal:
            # Flag pole
            pygame.draw.rect(surf, (0, 168, 0), 
                            (self.goal.x - cam_x, self.goal.y, 4, self.goal.h))
            # Flag
            pygame.draw.polygon(surf, (255, 255, 255),
                               [(self.goal.x - cam_x + 4, self.goal.y),
                                (self.goal.x - cam_x + 24, self.goal.y + 10),
                                (self.goal.x - cam_x + 4, self.goal.y + 20)])

# ----------------------------- game states ------------------------------------
class WorldMapState:
    def __init__(self, seed):
        self.seed = seed
        self.cursor = [0, 0]  # world, stage
        self.unlocked = {(0, 0)}  # Start with 1-1 unlocked
        self.completed = set()

    def unlock_next(self, world, stage):
        if stage < STAGES_PER_WORLD - 1:
            self.unlocked.add((world, stage + 1))
        elif world < WORLD_COUNT - 1:
            self.unlocked.add((world + 1, 0))

    def draw(self, surf):
        surf.fill((107, 140, 255))
        
        # Title
        font = pygame.font.Font(None, 48)
        title = font.render("SUPER MARIO BROS FOREVER", True, (255, 255, 255))
        surf.blit(title, (SCREEN_W//2 - title.get_width()//2, 30))
        
        # World paths
        for w in range(WORLD_COUNT):
            y = 120 + w * 70
            
            # World name
            font = pygame.font.Font(None, 32)
            world_names = ["GRASS LAND", "DESERT LAND", "WATER LAND", 
                          "GIANT LAND", "SKY LAND", "DARK LAND"]
            name = font.render(f"WORLD {w+1} - {world_names[w]}", True, (255, 255, 255))
            surf.blit(name, (50, y))
            
            # Stage nodes
            for s in range(STAGES_PER_WORLD):
                x = 350 + s * 150
                
                # Node
                if (w, s) in self.completed:
                    color = (0, 255, 0)
                elif (w, s) in self.unlocked:
                    color = (255, 255, 255)
                else:
                    color = (128, 128, 128)
                
                pygame.draw.circle(surf, color, (x, y + 20), 20)
                
                # Stage number
                font = pygame.font.Font(None, 24)
                if s == CASTLE_STAGE_INDEX:
                    text = font.render("🏰", True, (0, 0, 0))
                else:
                    text = font.render(f"{s+1}", True, (0, 0, 0))
                surf.blit(text, (x - 8, y + 12))
                
                # Path
                if s < STAGES_PER_WORLD - 1:
                    pygame.draw.line(surf, (255, 255, 255), (x + 20, y + 20), (x + 130, y + 20), 3)
        
        # Cursor
        w, s = self.cursor
        x = 350 + s * 150
        y = 120 + w * 70 + 20
        pygame.draw.circle(surf, (255, 255, 0), (x, y), 25, 3)
        
        # Instructions
        font = pygame.font.Font(None, 24)
        inst = font.render("ARROW KEYS: Select   ENTER: Play   ESC: Title", True, (255, 255, 255))
        surf.blit(inst, (SCREEN_W//2 - inst.get_width()//2, SCREEN_H - 30))

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Super Mario Bros Forever - Files-Off Edition")
        self.clock = pygame.time.Clock()
        self.audio = AudioEngine()
        
        self.seed_code = DEFAULT_SEED
        self.base_seed = seed_from_string(self.seed_code)
        
        self.state = "title"
        self.world_map = WorldMapState(self.base_seed)
        self.level = None
        self.player = None
        self.camera_x = 0
        self.frame = 0
        
        # Title screen
        self.title_input = list(self.seed_code)

    def start_level(self, world, stage):
        level_seed = self.base_seed ^ (world * 1000) ^ (stage * 100)
        self.level = Level(level_seed, world, stage)
        self.player = Player(*self.level.spawn)
        self.camera_x = 0
        self.state = "playing"

    def run(self):
        running = True
        while running:
            # Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    
                elif event.type == pygame.KEYDOWN:
                    if self.state == "title":
                        if event.key == pygame.K_RETURN:
                            self.seed_code = "".join(self.title_input) or DEFAULT_SEED
                            self.base_seed = seed_from_string(self.seed_code)
                            self.world_map = WorldMapState(self.base_seed)
                            self.state = "map"
                        elif event.key == pygame.K_BACKSPACE and self.title_input:
                            self.title_input.pop()
                        elif event.key == pygame.K_TAB:
                            # Random seed
                            import string
                            chars = string.ascii_uppercase + string.digits
                            self.title_input = list("".join(random.choices(chars, k=16)))
                        elif event.key == pygame.K_F8:
                            # Unlock all
                            for w in range(WORLD_COUNT):
                                for s in range(STAGES_PER_WORLD):
                                    self.world_map.unlocked.add((w, s))
                            
                    elif self.state == "map":
                        if event.key == pygame.K_ESCAPE:
                            self.state = "title"
                        elif event.key == pygame.K_RETURN:
                            w, s = self.world_map.cursor
                            if (w, s) in self.world_map.unlocked:
                                self.start_level(w, s)
                        elif event.key == pygame.K_LEFT:
                            self.world_map.cursor[1] = max(0, self.world_map.cursor[1] - 1)
                        elif event.key == pygame.K_RIGHT:
                            self.world_map.cursor[1] = min(STAGES_PER_WORLD - 1, self.world_map.cursor[1] + 1)
                        elif event.key == pygame.K_UP:
                            self.world_map.cursor[0] = max(0, self.world_map.cursor[0] - 1)
                        elif event.key == pygame.K_DOWN:
                            self.world_map.cursor[0] = min(WORLD_COUNT - 1, self.world_map.cursor[0] + 1)
                        elif event.key == pygame.K_F8:
                            # Unlock all
                            for w in range(WORLD_COUNT):
                                for s in range(STAGES_PER_WORLD):
                                    self.world_map.unlocked.add((w, s))
                        elif event.key == pygame.K_F9:
                            # Reset progress
                            self.world_map.unlocked = {(0, 0)}
                            self.world_map.completed = set()
                            
                    elif self.state == "playing":
                        if event.key == pygame.K_ESCAPE:
                            self.state = "map"
                        elif event.key == pygame.K_r:
                            w, s = self.world_map.cursor
                            self.start_level(w, s)
                        elif event.key == pygame.K_p:
                            self.state = "paused"
                            
                    elif self.state == "paused":
                        if event.key == pygame.K_p:
                            self.state = "playing"
                            
                elif event.type == pygame.TEXTINPUT and self.state == "title":
                    if len(self.title_input) < 32:
                        self.title_input.extend(list(event.text.upper()))
            
            # Update
            if self.state == "playing":
                keys = pygame.key.get_pressed()
                self.player.update_input(keys)
                self.player.apply_physics()
                self.player.move_and_collide(self.level)
                
                # Update camera
                target_x = self.player.rect.centerx - SCREEN_W // 3
                self.camera_x = clamp(target_x, 0, self.level.width * TILE - SCREEN_W)
                
                # Update level
                result = self.level.update(self.player, self.audio)
                if result == "complete":
                    w, s = self.world_map.cursor
                    self.world_map.completed.add((w, s))
                    self.world_map.unlock_next(w, s)
                    self.state = "map"
                    if self.audio: self.audio.play_powerup()
                elif result == "dead":
                    self.player.lives -= 1
                    if self.player.lives <= 0:
                        self.state = "gameover"
                    else:
                        w, s = self.world_map.cursor
                        self.start_level(w, s)
                    if self.audio: self.audio.play_death()
            
            # Draw
            if self.state == "title":
                self.screen.fill((107, 140, 255))
                
                # Title
                font = pygame.font.Font(None, 64)
                title1 = font.render("SUPER MARIO BROS", True, (255, 255, 255))
                title2 = font.render("FOREVER", True, (255, 255, 255))
                self.screen.blit(title1, (SCREEN_W//2 - title1.get_width()//2, 100))
                self.screen.blit(title2, (SCREEN_W//2 - title2.get_width()//2, 170))
                
                # Subtitle
                font = pygame.font.Font(None, 32)
                sub = font.render("Files-Off Edition", True, (255, 206, 150))
                self.screen.blit(sub, (SCREEN_W//2 - sub.get_width()//2, 230))
                
                # Seed input
                font = pygame.font.Font(None, 28)
                seed_text = "".join(self.title_input) + "_"
                seed_surf = font.render(f"SEED: {seed_text}", True, (255, 255, 255))
                self.screen.blit(seed_surf, (SCREEN_W//2 - seed_surf.get_width()//2, 320))
                
                # Instructions
                font = pygame.font.Font(None, 24)
                inst1 = font.render("Type seed code or TAB for random", True, (255, 255, 255))
                inst2 = font.render("ENTER to start | F8 unlock all", True, (255, 255, 255))
                self.screen.blit(inst1, (SCREEN_W//2 - inst1.get_width()//2, 400))
                self.screen.blit(inst2, (SCREEN_W//2 - inst2.get_width()//2, 430))
                
            elif self.state == "map":
                self.world_map.draw(self.screen)
                
            elif self.state == "playing" or self.state == "paused":
                # Draw level
                w = self.world_map.cursor[0]
                self.level.draw(self.screen, self.camera_x, w)
                
                # Draw player
                self.player.draw(self.screen, self.camera_x, self.frame)
                
                # HUD
                font = pygame.font.Font(None, 28)
                hud_y = 10
                
                # Score/coins
                coins_text = font.render(f"COINS: {self.player.coins:03d}", True, (255, 255, 255))
                self.screen.blit(coins_text, (10, hud_y))
                
                # World/stage
                w, s = self.world_map.cursor
                world_text = font.render(f"WORLD {w+1}-{s+1}", True, (255, 255, 255))
                self.screen.blit(world_text, (SCREEN_W//2 - world_text.get_width()//2, hud_y))
                
                # Lives
                lives_text = font.render(f"LIVES: {self.player.lives}", True, (255, 255, 255))
                self.screen.blit(lives_text, (SCREEN_W - lives_text.get_width() - 10, hud_y))
                
                # Paused overlay
                if self.state == "paused":
                    overlay = pygame.Surface((SCREEN_W, SCREEN_H))
                    overlay.set_alpha(128)
                    overlay.fill((0, 0, 0))
                    self.screen.blit(overlay, (0, 0))
                    
                    font = pygame.font.Font(None, 64)
                    pause_text = font.render("PAUSED", True, (255, 255, 255))
                    self.screen.blit(pause_text, (SCREEN_W//2 - pause_text.get_width()//2, SCREEN_H//2 - 32))
                    
            elif self.state == "gameover":
                self.screen.fill((0, 0, 0))
                font = pygame.font.Font(None, 64)
                go_text = font.render("GAME OVER", True, (255, 255, 255))
                self.screen.blit(go_text, (SCREEN_W//2 - go_text.get_width()//2, SCREEN_H//2 - 32))
                
                font = pygame.font.Font(None, 32)
                cont = font.render("Press ESC to return to title", True, (255, 255, 255))
                self.screen.blit(cont, (SCREEN_W//2 - cont.get_width()//2, SCREEN_H//2 + 40))
                
                keys = pygame.key.get_pressed()
                if keys[pygame.K_ESCAPE]:
                    self.state = "title"
            
            self.frame += 1
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()

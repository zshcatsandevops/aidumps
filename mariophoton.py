#!/usr/bin/env python3
"""
Super Mario World - Complete Game
Haltmann OS CatKernel Photon-Compiled Edition
Single File Implementation
"""

import pygame
import sys
import random
import math
import json
import os

# ============================================================================
# CONSTANTS
# ============================================================================

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
SKY_BLUE = (135, 206, 235)
BROWN = (139, 69, 19)
DARK_GREEN = (0, 128, 0)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)

# Tile sizes
TILE_SIZE = 32
HALF_TILE = TILE_SIZE // 2

# Physics
GRAVITY = 980
MAX_FALL_SPEED = 600
JUMP_POWER = -450
RUN_SPEED = 200
WALK_SPEED = 120
MAX_SPEED = 300
ACCELERATION = 800
FRICTION = 600
AIR_RESISTANCE = 400

# Player states
STATE_SMALL = 0
STATE_SUPER = 1
STATE_FIRE = 2
STATE_CAPE = 3

# Game states
GAME_STATE_MENU = 0
GAME_STATE_OVERWORLD = 1
GAME_STATE_LEVEL = 2
GAME_STATE_PAUSE = 3
GAME_STATE_GAMEOVER = 4
GAME_STATE_WIN = 5

# Tile types
TILE_EMPTY = 0
TILE_GROUND = 1
TILE_BRICK = 2
TILE_QUESTION = 3
TILE_PIPE = 4
TILE_COIN = 5
TILE_SPIKE = 6
TILE_CLOUD = 7
TILE_BUSH = 8
TILE_CASTLE = 9
TILE_FLAG = 10

# Enemy types
ENEMY_GOOMBA = 0
ENEMY_KOOPA = 1
ENEMY_PIRANHA = 2
ENEMY_BULLET_BILL = 3
ENEMY_LAKITU = 4
ENEMY_HAMMER_BRO = 5
ENEMY_BOWSER = 6

# Item types
ITEM_MUSHROOM = 0
ITEM_FIRE_FLOWER = 1
ITEM_STAR = 2
ITEM_CAPE_FEATHER = 3
ITEM_1UP = 4
ITEM_COIN = 5
ITEM_P_SWITCH = 6

# Level themes
THEME_OVERWORLD = 0
THEME_UNDERGROUND = 1
THEME_UNDERWATER = 2
THEME_CASTLE = 3
THEME_GHOST_HOUSE = 4
THEME_AIRSHIP = 5

# ============================================================================
# BASE CLASSES
# ============================================================================

class Entity:
    """Base class for all game entities"""
    
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)
        self.active = True
        self.visible = True
    
    def update(self, dt):
        """Update entity"""
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
    
    def draw(self, screen, camera_x=0, camera_y=0):
        """Draw entity"""
        if self.visible:
            pygame.draw.rect(screen, (255, 255, 255), 
                           (self.x - camera_x, self.y - camera_y, self.width, self.height))
    
    def collides_with(self, other):
        """Check collision with another entity"""
        return self.rect.colliderect(other.rect)
    
    def distance_to(self, other):
        """Calculate distance to another entity"""
        dx = self.x - other.x
        dy = self.y - other.y
        return (dx * dx + dy * dy) ** 0.5
    
    def destroy(self):
        """Destroy this entity"""
        self.active = False
        self.visible = False

# ============================================================================
# SOUND MANAGER
# ============================================================================

class SoundManager:
    """Manages game audio"""
    
    def __init__(self):
        self.music_volume = 0.7
        self.sfx_volume = 0.8
        self.current_music = None
        self.sounds = {}
    
    def play_music(self, track_name):
        """Play background music"""
        self.current_music = track_name
        # Would load and play music file here
    
    def stop_music(self):
        """Stop background music"""
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
    
    def pause_music(self):
        """Pause music"""
        pygame.mixer.music.pause()
    
    def resume_music(self):
        """Resume music"""
        pygame.mixer.music.unpause()
    
    def play_sfx(self, sound_name):
        """Play sound effect"""
        # Would play sound effect here
        pass
    
    def update(self):
        """Update sound system"""
        pass

# ============================================================================
# PARTICLE SYSTEM
# ============================================================================

class ParticleSystem:
    """Manages particle effects"""
    
    def __init__(self):
        self.particles = []
    
    def create_particle(self, x, y, particle_type, color=WHITE):
        """Create a particle"""
        particle = {
            'x': x,
            'y': y,
            'vx': random.randint(-100, 100),
            'vy': random.randint(-200, -50),
            'type': particle_type,
            'color': color,
            'lifetime': 1.0,
            'size': random.randint(2, 6)
        }
        self.particles.append(particle)
    
    def update(self, dt):
        """Update all particles"""
        for particle in self.particles[:]:
            particle['x'] += particle['vx'] * dt
            particle['y'] += particle['vy'] * dt
            particle['vy'] += 300 * dt  # Gravity
            particle['lifetime'] -= dt
            
            if particle['lifetime'] <= 0:
                self.particles.remove(particle)
    
    def draw(self, screen):
        """Draw all particles"""
        for particle in self.particles:
            alpha = particle['lifetime']
            size = int(particle['size'] * alpha)
            if size > 0:
                pygame.draw.circle(screen, particle['color'],
                                 (int(particle['x']), int(particle['y'])), size)

# ============================================================================
# SAVE SYSTEM
# ============================================================================

class SaveSystem:
    """Handles saving and loading game data"""
    
    def __init__(self):
        self.save_file = 'mario_save.json'
        self.high_score_file = 'high_score.json'
    
    def save(self, data):
        """Save game data"""
        try:
            with open(self.save_file, 'w') as f:
                json.dump(data, f)
            return True
        except:
            return False
    
    def load(self):
        """Load game data"""
        try:
            with open(self.save_file, 'r') as f:
                return json.load(f)
        except:
            return None
    
    def has_save(self):
        """Check if save file exists"""
        return os.path.exists(self.save_file)
    
    def get_high_score(self):
        """Get high score"""
        try:
            with open(self.high_score_file, 'r') as f:
                data = json.load(f)
                return data.get('high_score', 0)
        except:
            return 0
    
    def save_high_score(self, score):
        """Save high score"""
        try:
            with open(self.high_score_file, 'w') as f:
                json.dump({'high_score': score}, f)
            return True
        except:
            return False

# ============================================================================
# PLAYER
# ============================================================================

class Player(Entity):
    """Player character with all Mario mechanics"""
    
    def __init__(self, x, y):
        super().__init__(x, y, 16, 32)
        
        # Movement
        self.vel_x = 0
        self.vel_y = 0
        self.facing_right = True
        self.on_ground = False
        self.jumping = False
        self.running = False
        self.ducking = False
        self.can_jump = True
        
        # Power state
        self.power_state = STATE_SMALL
        self.invincible = False
        self.invincible_timer = 0
        self.star_power = False
        self.star_timer = 0
        
        # Cape/Flying
        self.has_cape = False
        self.flying = False
        self.flight_meter = 0
        self.gliding = False
        
        # Animation
        self.animation_timer = 0
        self.current_frame = 0
        
        # Sound timers
        self.jump_sound_timer = 0
        self.powerup_animation = False
        self.powerup_timer = 0
        
        # Physics modifiers
        self.water_physics = False
        self.ice_physics = False
        
        # Combo/Score
        self.enemy_combo = 0
        self.coin_combo = 0
    
    def update(self, dt, level):
        """Update player physics and state"""
        # Handle invincibility
        if self.invincible:
            self.invincible_timer -= dt
            if self.invincible_timer <= 0:
                self.invincible = False
        
        # Handle star power
        if self.star_power:
            self.star_timer -= dt
            if self.star_timer <= 0:
                self.star_power = False
        
        # Handle powerup animation
        if self.powerup_animation:
            self.powerup_timer -= dt
            if self.powerup_timer <= 0:
                self.powerup_animation = False
        
        # Apply physics
        self.apply_physics(dt, level)
        
        # Update animation
        self.animation_timer += dt
        
        # Check boundaries
        self.check_boundaries()
    
    def apply_physics(self, dt, level):
        """Apply physics to player"""
        # Gravity
        if not self.on_ground:
            if self.gliding and self.vel_y > 0:
                self.vel_y += GRAVITY * 0.3 * dt
            else:
                self.vel_y += GRAVITY * dt
            
            if self.vel_y > MAX_FALL_SPEED:
                self.vel_y = MAX_FALL_SPEED
        
        # Horizontal movement
        if self.ice_physics:
            if abs(self.vel_x) > 0:
                self.vel_x -= math.copysign(FRICTION * 0.2 * dt, self.vel_x)
        else:
            if abs(self.vel_x) > 0 and not self.running:
                self.vel_x -= math.copysign(FRICTION * dt, self.vel_x)
        
        # Water physics
        if self.water_physics:
            self.vel_x *= 0.8
            self.vel_y *= 0.8
        
        # Update position
        self.x += self.vel_x * dt
        self.y += self.vel_y * dt
        
        # Check collisions with level
        self.check_collisions(level)
    
    def check_collisions(self, level):
        """Check and resolve collisions with level"""
        if self.y + self.rect.height >= SCREEN_HEIGHT - 64:
            self.y = SCREEN_HEIGHT - 64 - self.rect.height
            self.vel_y = 0
            self.on_ground = True
        else:
            self.on_ground = False
        
        if self.x < 0:
            self.x = 0
            self.vel_x = 0
        elif hasattr(level, 'width'):
            max_x = level.width * TILE_SIZE
            if self.x + self.rect.width > max_x:
                self.x = max_x - self.rect.width
                self.vel_x = 0
    
    def handle_input(self, keys):
        """Handle player input"""
        if keys[pygame.K_LEFT]:
            self.move_left()
        elif keys[pygame.K_RIGHT]:
            self.move_right()
        else:
            self.vel_x *= 0.9
        
        self.running = keys[pygame.K_LSHIFT] or keys[pygame.K_x]
        
        if keys[pygame.K_SPACE] or keys[pygame.K_z]:
            self.jump()
        else:
            self.can_jump = True
            if self.vel_y < 0:
                self.vel_y *= 0.5
        
        self.ducking = keys[pygame.K_DOWN] and self.on_ground and self.power_state != STATE_SMALL
        
        if keys[pygame.K_LCTRL] or keys[pygame.K_c]:
            self.special_action()
    
    def move_left(self):
        """Move player left"""
        self.facing_right = False
        max_speed = RUN_SPEED if self.running else WALK_SPEED
        
        if self.vel_x > -max_speed:
            self.vel_x -= ACCELERATION * 0.016
            if self.vel_x < -max_speed:
                self.vel_x = -max_speed
    
    def move_right(self):
        """Move player right"""
        self.facing_right = True
        max_speed = RUN_SPEED if self.running else WALK_SPEED
        
        if self.vel_x < max_speed:
            self.vel_x += ACCELERATION * 0.016
            if self.vel_x > max_speed:
                self.vel_x = max_speed
    
    def jump(self):
        """Make player jump"""
        if self.on_ground and self.can_jump:
            self.vel_y = JUMP_POWER
            self.on_ground = False
            self.jumping = True
            self.can_jump = False
            self.jump_sound_timer = 0.2
        elif self.water_physics:
            self.vel_y = JUMP_POWER * 0.6
    
    def special_action(self):
        """Perform special action based on power state"""
        if self.power_state == STATE_FIRE:
            pass  # Throw fireball
        elif self.power_state == STATE_CAPE:
            if self.on_ground:
                pass  # Cape spin
            elif self.vel_y > 0:
                self.gliding = True
    
    def power_up(self, power_type):
        """Apply power-up to player"""
        if power_type == ITEM_MUSHROOM:
            if self.power_state == STATE_SMALL:
                self.power_state = STATE_SUPER
                self.rect.height = 32
                self.powerup_animation = True
                self.powerup_timer = 1.0
        elif power_type == ITEM_FIRE_FLOWER:
            self.power_state = STATE_FIRE
            self.rect.height = 32
        elif power_type == ITEM_CAPE_FEATHER:
            self.power_state = STATE_CAPE
            self.has_cape = True
            self.rect.height = 32
        elif power_type == ITEM_STAR:
            self.star_power = True
            self.star_timer = 10.0
            self.invincible = True
            self.invincible_timer = 10.0
    
    def take_damage(self):
        """Handle player taking damage"""
        if self.invincible or self.star_power:
            return False
        
        if self.power_state == STATE_CAPE:
            self.power_state = STATE_SUPER
            self.has_cape = False
        elif self.power_state == STATE_FIRE:
            self.power_state = STATE_SUPER
        elif self.power_state == STATE_SUPER:
            self.power_state = STATE_SMALL
            self.rect.height = 16
        elif self.power_state == STATE_SMALL:
            return True
        
        self.invincible = True
        self.invincible_timer = 2.0
        return False
    
    def draw(self, screen, camera_x=0, camera_y=0):
        """Draw player"""
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        
        if self.invincible and int(self.invincible_timer * 10) % 2 == 0:
            return
        
        color = RED
        if self.power_state == STATE_FIRE:
            color = ORANGE
        elif self.power_state == STATE_CAPE:
            color = YELLOW
        
        if self.star_power:
            t = pygame.time.get_ticks() / 100
            color = [RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE][int(t) % 6]
        
        height = 16 if self.power_state == STATE_SMALL else 32
        pygame.draw.rect(screen, color, (draw_x, draw_y, self.rect.width, height))
        
        # Eyes
        eye_color = WHITE
        if self.facing_right:
            pygame.draw.circle(screen, eye_color, (int(draw_x + 12), int(draw_y + 5)), 2)
        else:
            pygame.draw.circle(screen, eye_color, (int(draw_x + 4), int(draw_y + 5)), 2)
    
    def check_boundaries(self):
        """Check level boundaries"""
        if self.y > SCREEN_HEIGHT + 100:
            self.take_damage()
            self.take_damage()
    
    def reset(self):
        """Reset player to default state"""
        self.x = 100
        self.y = 100
        self.vel_x = 0
        self.vel_y = 0
        self.power_state = STATE_SMALL
        self.rect.height = 16
        self.invincible = False
        self.star_power = False
        self.has_cape = False
        self.on_ground = False

# ============================================================================
# ENEMIES
# ============================================================================

class Enemy(Entity):
    """Base enemy class"""
    
    def __init__(self, x, y, width, height, enemy_type):
        super().__init__(x, y, width, height)
        self.enemy_type = enemy_type
        self.vel_x = 0
        self.vel_y = 0
        self.health = 1
        self.damage = 1
        self.points = 100
        self.direction = -1
        self.on_ground = False
        self.can_be_stomped = True
        self.can_be_fire_killed = True
        self.animation_timer = 0
        self.current_frame = 0
    
    def update(self, dt, level, player):
        """Update enemy"""
        super().update(dt)
        self.apply_physics(dt, level)
        self.update_ai(dt, player)
        self.animation_timer += dt
    
    def apply_physics(self, dt, level):
        """Apply physics"""
        if not self.on_ground:
            self.vel_y += GRAVITY * dt
            if self.vel_y > MAX_FALL_SPEED:
                self.vel_y = MAX_FALL_SPEED
        
        self.x += self.vel_x * dt
        self.y += self.vel_y * dt
        
        if self.y + self.height >= SCREEN_HEIGHT - 64:
            self.y = SCREEN_HEIGHT - 64 - self.height
            self.vel_y = 0
            self.on_ground = True
        else:
            self.on_ground = False
    
    def update_ai(self, dt, player):
        """Update AI behavior"""
        pass
    
    def take_damage(self, amount=1, source=None):
        """Take damage"""
        self.health -= amount
        if self.health <= 0:
            self.die()
            return True
        return False
    
    def die(self):
        """Enemy death"""
        self.active = False
    
    def draw(self, screen, camera_x=0, camera_y=0):
        """Draw enemy"""
        if not self.visible:
            return
        
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        
        color = self.get_color()
        pygame.draw.rect(screen, color, (draw_x, draw_y, self.width, self.height))
        
        eye_color = WHITE
        eye_size = 3
        if self.direction > 0:
            pygame.draw.circle(screen, eye_color, 
                             (int(draw_x + self.width - 5), int(draw_y + 5)), eye_size)
        else:
            pygame.draw.circle(screen, eye_color,
                             (int(draw_x + 5), int(draw_y + 5)), eye_size)
    
    def get_color(self):
        """Get enemy color based on type"""
        return (100, 100, 100)

class Goomba(Enemy):
    """Goomba enemy"""
    
    def __init__(self, x, y):
        super().__init__(x, y, 24, 24, ENEMY_GOOMBA)
        self.vel_x = -50
        self.points = 100
    
    def update_ai(self, dt, player):
        """Goomba AI"""
        self.vel_x = 50 * self.direction
        if random.random() < 0.01:
            self.direction *= -1
    
    def get_color(self):
        return BROWN

class Koopa(Enemy):
    """Koopa Troopa"""
    
    def __init__(self, x, y, color='green'):
        super().__init__(x, y, 24, 32, ENEMY_KOOPA)
        self.color = color
        self.vel_x = -40
        self.in_shell = False
        self.shell_spinning = False
        self.shell_timer = 0
        self.points = 200
    
    def update_ai(self, dt, player):
        """Koopa AI"""
        if not self.in_shell:
            self.vel_x = 40 * self.direction
        elif self.shell_spinning:
            self.vel_x = 300 * self.direction
        else:
            self.vel_x = 0
        
        if self.in_shell:
            self.shell_timer += dt
            if self.shell_timer > 5.0 and not self.shell_spinning:
                self.in_shell = False
                self.shell_timer = 0
                self.height = 32
    
    def take_damage(self, amount=1, source=None):
        """Take damage"""
        if not self.in_shell:
            self.in_shell = True
            self.shell_spinning = False
            self.height = 24
            self.shell_timer = 0
            self.vel_x = 0
            return False
        elif not self.shell_spinning:
            self.shell_spinning = True
            self.direction = 1 if source and source.x < self.x else -1
            return False
        else:
            self.shell_spinning = False
            self.vel_x = 0
            return False
    
    def get_color(self):
        return RED if self.color == 'red' else GREEN

def create_enemy(enemy_type, x, y):
    """Factory function to create enemies"""
    if enemy_type == ENEMY_GOOMBA:
        return Goomba(x, y)
    elif enemy_type == ENEMY_KOOPA:
        return Koopa(x, y)
    else:
        return Enemy(x, y, 24, 24, enemy_type)

# ============================================================================
# ITEMS
# ============================================================================

class Item(Entity):
    """Base item class"""
    
    def __init__(self, x, y, width, height, item_type):
        super().__init__(x, y, width, height)
        self.item_type = item_type
        self.vel_x = 0
        self.vel_y = 0
        self.collected = False
        self.emerge_timer = 0.5
        self.emerging = True
        self.start_y = y
        self.points = 100
    
    def update(self, dt, level):
        """Update item"""
        super().update(dt)
        
        if self.emerging:
            self.emerge_timer -= dt
            progress = 1.0 - (self.emerge_timer / 0.5)
            self.y = self.start_y - (16 * progress)
            if self.emerge_timer <= 0:
                self.emerging = False
                self.y = self.start_y - 16
        else:
            self.apply_physics(dt, level)
    
    def apply_physics(self, dt, level):
        """Apply physics to item"""
        if self.item_type not in [ITEM_COIN, ITEM_STAR]:
            self.vel_y += GRAVITY * dt
            if self.vel_y > MAX_FALL_SPEED:
                self.vel_y = MAX_FALL_SPEED
        
        self.x += self.vel_x * dt
        self.y += self.vel_y * dt
        
        if self.y + self.height >= SCREEN_HEIGHT - 64:
            self.y = SCREEN_HEIGHT - 64 - self.height
            self.vel_y = 0
    
    def collect(self, player):
        """Item collected by player"""
        self.collected = True
        self.active = False
    
    def draw(self, screen, camera_x=0, camera_y=0):
        """Draw item"""
        if not self.visible:
            return
        
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        
        color = self.get_color()
        pygame.draw.rect(screen, color, (draw_x, draw_y, self.width, self.height))
    
    def get_color(self):
        """Get item color"""
        return WHITE

class Mushroom(Item):
    """Super Mushroom"""
    
    def __init__(self, x, y):
        super().__init__(x, y, 24, 24, ITEM_MUSHROOM)
        self.vel_x = 50
        self.points = 1000
    
    def collect(self, player):
        """Give player mushroom power"""
        super().collect(player)
        player.power_up(ITEM_MUSHROOM)
    
    def get_color(self):
        return RED

class Coin(Item):
    """Coin"""
    
    def __init__(self, x, y):
        super().__init__(x, y, 16, 16, ITEM_COIN)
        self.vel_x = 0
        self.vel_y = -200
        self.lifetime = 1.0
        self.points = 200
        self.animation_timer = 0
    
    def update(self, dt, level):
        """Update coin"""
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.active = False
        
        self.vel_y += GRAVITY * 0.5 * dt
        self.y += self.vel_y * dt
        
        self.animation_timer += dt
    
    def draw(self, screen, camera_x=0, camera_y=0):
        """Draw spinning coin"""
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        
        width = abs(math.cos(self.animation_timer * 5)) * self.width
        
        if width > 2:
            pygame.draw.ellipse(screen, YELLOW,
                              (draw_x + (self.width - width) // 2, draw_y,
                               width, self.height))

def create_item(item_type, x, y):
    """Factory function to create items"""
    if item_type == ITEM_MUSHROOM:
        return Mushroom(x, y)
    elif item_type == ITEM_COIN:
        return Coin(x, y)
    else:
        return Item(x, y, 16, 16, item_type)

# ============================================================================
# LEVEL
# ============================================================================

class Tile:
    """Individual tile in the level"""
    
    def __init__(self, tile_type, x, y):
        self.type = tile_type
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        self.solid = tile_type in [TILE_GROUND, TILE_BRICK, TILE_PIPE, TILE_QUESTION]
        self.breakable = tile_type == TILE_BRICK
        self.contents = None
        self.hit = False
    
    def draw(self, screen, camera_x, camera_y):
        """Draw the tile"""
        draw_x = self.rect.x - camera_x
        draw_y = self.rect.y - camera_y
        
        if draw_x < -TILE_SIZE or draw_x > SCREEN_WIDTH:
            return
        
        color = self.get_color()
        if color:
            pygame.draw.rect(screen, color, (draw_x, draw_y, TILE_SIZE, TILE_SIZE))
            
            if self.type in [TILE_GROUND, TILE_BRICK, TILE_QUESTION]:
                pygame.draw.rect(screen, BLACK, (draw_x, draw_y, TILE_SIZE, TILE_SIZE), 1)
    
    def get_color(self):
        """Get tile color based on type"""
        colors = {
            TILE_GROUND: BROWN,
            TILE_BRICK: (150, 75, 0),
            TILE_QUESTION: YELLOW if not self.hit else DARK_GRAY,
            TILE_PIPE: GREEN,
            TILE_COIN: YELLOW,
            TILE_SPIKE: DARK_GRAY,
            TILE_CLOUD: WHITE,
            TILE_BUSH: DARK_GREEN,
            TILE_CASTLE: DARK_GRAY,
            TILE_FLAG: WHITE
        }
        return colors.get(self.type, None)

class Level:
    """Level class managing tiles, enemies, and items"""
    
    def __init__(self, width, height, theme=THEME_OVERWORLD):
        self.width = width
        self.height = height
        self.theme = theme
        self.tiles = [[None for _ in range(width)] for _ in range(height)]
        self.enemies = []
        self.items = []
        self.particles = []
        self.camera_x = 0
        self.camera_y = 0
        self.background_color = self.get_background_color()
        
        self.start_x = 2 * TILE_SIZE
        self.start_y = 10 * TILE_SIZE
        self.goal_x = (width - 3) * TILE_SIZE
        self.goal_y = 10 * TILE_SIZE
        self.time_limit = 300
        
        self.generate()
    
    def get_background_color(self):
        """Get background color based on theme"""
        theme_colors = {
            THEME_OVERWORLD: SKY_BLUE,
            THEME_UNDERGROUND: BLACK,
            THEME_UNDERWATER: (0, 100, 150),
            THEME_CASTLE: (50, 50, 50)
        }
        return theme_colors.get(self.theme, SKY_BLUE)
    
    def generate(self):
        """Generate level layout"""
        # Create ground
        ground_height = self.height - 3
        for x in range(self.width):
            if x > 10 and random.random() < 0.1:
                ground_height += random.choice([-1, 0, 1])
                ground_height = max(self.height - 5, min(self.height - 2, ground_height))
            
            for y in range(ground_height, self.height):
                self.tiles[y][x] = Tile(TILE_GROUND, x, y)
        
        # Add platforms
        for _ in range(5):
            x = random.randint(5, self.width - 10)
            y = random.randint(5, self.height - 6)
            width = random.randint(3, 8)
            
            for i in range(width):
                if x + i < self.width:
                    self.tiles[y][x + i] = Tile(TILE_GROUND, x + i, y)
        
        # Add question blocks
        for _ in range(10):
            x = random.randint(2, self.width - 2)
            y = random.randint(3, self.height - 6)
            if not self.tiles[y][x]:
                tile = Tile(TILE_QUESTION, x, y)
                tile.contents = random.choice([ITEM_COIN, ITEM_MUSHROOM])
                self.tiles[y][x] = tile
        
        # Add enemies
        for _ in range(5):
            x = random.randint(5, self.width - 5) * TILE_SIZE
            y = random.randint(3, self.height - 4) * TILE_SIZE
            enemy_type = random.choice([ENEMY_GOOMBA, ENEMY_KOOPA])
            self.enemies.append(create_enemy(enemy_type, x, y))
        
        # Add goal flag
        for i in range(10):
            if ground_height - i - 1 >= 0:
                self.tiles[ground_height - i - 1][self.width - 3] = Tile(TILE_FLAG, self.width - 3, ground_height - i - 1)
    
    def get_tile_at(self, x, y):
        """Get tile at world coordinates"""
        tile_x = int(x // TILE_SIZE)
        tile_y = int(y // TILE_SIZE)
        
        if 0 <= tile_x < self.width and 0 <= tile_y < self.height:
            return self.tiles[tile_y][tile_x]
        return None
    
    def break_tile(self, tile):
        """Break a breakable tile"""
        if tile and tile.breakable and not tile.hit:
            tile_y = tile.y
            tile_x = tile.x
            self.tiles[tile_y][tile_x] = None
            return True
        return False
    
    def hit_block(self, tile, player):
        """Hit a question block"""
        if tile and tile.type == TILE_QUESTION and not tile.hit:
            tile.hit = True
            if tile.contents:
                item_x = tile.x * TILE_SIZE
                item_y = (tile.y - 1) * TILE_SIZE
                self.items.append(create_item(tile.contents, item_x, item_y))
                return True
        return False
    
    def update(self, dt, player):
        """Update level elements"""
        for enemy in self.enemies[:]:
            if enemy.active:
                enemy.update(dt, self, player)
                
                if enemy.collides_with(player):
                    if player.vel_y > 0 and player.y < enemy.y:
                        if enemy.can_be_stomped:
                            enemy.take_damage(1, player)
                            player.vel_y = JUMP_POWER * 0.5
                            player.enemy_combo += 1
                    else:
                        player.take_damage()
            else:
                self.enemies.remove(enemy)
        
        for item in self.items[:]:
            if item.active:
                item.update(dt, self)
                
                if item.collides_with(player):
                    item.collect(player)
                    self.items.remove(item)
            else:
                self.items.remove(item)
        
        self.update_camera(player)
    
    def update_camera(self, player):
        """Update camera position"""
        target_x = player.x - SCREEN_WIDTH // 2
        self.camera_x = max(0, min(target_x, self.width * TILE_SIZE - SCREEN_WIDTH))
        
        target_y = player.y - SCREEN_HEIGHT // 2
        self.camera_y = max(0, min(target_y, self.height * TILE_SIZE - SCREEN_HEIGHT))
    
    def draw(self, screen):
        """Draw the level"""
        screen.fill(self.background_color)
        
        if self.theme == THEME_OVERWORLD:
            # Draw hills
            hill_color = (34, 139, 34)
            for i in range(3):
                x = (i * 300 - self.camera_x * 0.3) % (SCREEN_WIDTH + 200) - 100
                pygame.draw.ellipse(screen, hill_color,
                                  (x, SCREEN_HEIGHT - 150, 200, 150))
        
        # Draw tiles
        start_x = max(0, int(self.camera_x // TILE_SIZE))
        end_x = min(self.width, start_x + (SCREEN_WIDTH // TILE_SIZE) + 2)
        start_y = max(0, int(self.camera_y // TILE_SIZE))
        end_y = min(self.height, start_y + (SCREEN_HEIGHT // TILE_SIZE) + 2)
        
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                if self.tiles[y][x]:
                    self.tiles[y][x].draw(screen, self.camera_x, self.camera_y)
        
        for item in self.items:
            item.draw(screen, self.camera_x, self.camera_y)
        
        for enemy in self.enemies:
            enemy.draw(screen, self.camera_x, self.camera_y)

# ============================================================================
# GAME STATES
# ============================================================================

class WorldNode:
    """Node on the world map"""
    
    def __init__(self, x, y, node_type='level', level_id=None):
        self.x = x
        self.y = y
        self.node_type = node_type
        self.level_id = level_id
        self.completed = False
        self.unlocked = False
        self.connections = []
    
    def connect_to(self, other_node):
        """Connect this node to another"""
        if other_node not in self.connections:
            self.connections.append(other_node)
            other_node.connections.append(self)
    
    def draw(self, screen, selected=False):
        """Draw the node"""
        if self.node_type == 'castle':
            color = DARK_GRAY
            size = 30
        else:
            color = RED if not self.completed else GREEN
            size = 20
        
        if not self.unlocked:
            color = DARK_GRAY
        
        for connected in self.connections:
            if connected.unlocked or self.unlocked:
                pygame.draw.line(screen, BROWN, 
                               (self.x, self.y), 
                               (connected.x, connected.y), 3)
        
        pygame.draw.circle(screen, color, (self.x, self.y), size)
        
        if selected:
            pygame.draw.circle(screen, WHITE, (self.x, self.y), size + 5, 3)
        
        if self.completed:
            pygame.draw.circle(screen, WHITE, (self.x, self.y), 5)

class MenuState:
    """Main menu state"""
    
    def __init__(self, game):
        self.game = game
        self.options = ['Start Game', 'Continue', 'Quit']
        self.selected = 0
        self.title_font = pygame.font.Font(None, 72)
        self.menu_font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 24)
        self.animation_timer = 0
    
    def enter(self):
        """Enter menu state"""
        self.game.sound_manager.play_music('menu')
    
    def exit(self):
        """Exit menu state"""
        self.game.sound_manager.stop_music()
    
    def handle_event(self, event):
        """Handle menu input"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                self.select_option()
    
    def select_option(self):
        """Execute selected menu option"""
        if self.selected == 0:  # Start Game
            self.game.reset()
            self.game.change_state(GAME_STATE_OVERWORLD)
        elif self.selected == 1:  # Continue
            if self.game.save_system.has_save():
                self.game.load_game()
                self.game.change_state(GAME_STATE_OVERWORLD)
        elif self.selected == 2:  # Quit
            pygame.quit()
            sys.exit()
    
    def update(self, dt):
        """Update menu animation"""
        self.animation_timer += dt
    
    def draw(self, screen):
        """Draw menu"""
        screen.fill(SKY_BLUE)
        
        # Title
        title = self.title_font.render("SUPER MARIO WORLD", True, YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        screen.blit(title, title_rect)
        
        # Subtitle
        subtitle = self.small_font.render("Haltmann OS Edition", True, WHITE)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 150))
        screen.blit(subtitle, subtitle_rect)
        
        # Menu options
        for i, option in enumerate(self.options):
            color = YELLOW if i == self.selected else WHITE
            
            if i == 1 and not self.game.save_system.has_save():
                color = DARK_GRAY
            
            text = self.menu_font.render(option, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 250 + i * 60))
            
            if i == self.selected:
                arrow_x = text_rect.x - 40
                arrow_y = text_rect.centery
                points = [
                    (arrow_x, arrow_y),
                    (arrow_x - 20, arrow_y - 10),
                    (arrow_x - 20, arrow_y + 10)
                ]
                pygame.draw.polygon(screen, YELLOW, points)
            
            screen.blit(text, text_rect)
        
        # Ground
        pygame.draw.rect(screen, BROWN, (0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50))

class OverworldState:
    """Overworld map state"""
    
    def __init__(self, game):
        self.game = game
        self.nodes = []
        self.current_node = None
        self.player_x = 0
        self.player_y = 0
        self.animation_timer = 0
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.unlocked_levels = []
        
        self.create_world_map()
    
    def create_world_map(self):
        """Create the world map nodes"""
        world1_nodes = [
            WorldNode(100, 300, 'level', '1-1'),
            WorldNode(200, 280, 'level', '1-2'),
            WorldNode(300, 260, 'level', '1-3'),
            WorldNode(400, 280, 'level', '1-4'),
            WorldNode(500, 250, 'castle', '1-castle'),
        ]
        
        for i in range(len(world1_nodes) - 1):
            world1_nodes[i].connect_to(world1_nodes[i + 1])
        
        self.nodes = world1_nodes
        
        self.nodes[0].unlocked = True
        self.current_node = self.nodes[0]
        self.player_x = self.current_node.x
        self.player_y = self.current_node.y
    
    def enter(self):
        """Enter overworld state"""
        self.game.sound_manager.play_music('overworld')
        
        for node in self.nodes:
            if node.level_id in self.unlocked_levels:
                node.unlocked = True
    
    def exit(self):
        """Exit overworld state"""
        pass
    
    def handle_event(self, event):
        """Handle overworld input"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.move_to_connected_node(-1, 0)
            elif event.key == pygame.K_RIGHT:
                self.move_to_connected_node(1, 0)
            elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                self.enter_level()
            elif event.key == pygame.K_ESCAPE:
                self.game.change_state(GAME_STATE_MENU)
    
    def move_to_connected_node(self, dx, dy):
        """Move to a connected node"""
        if not self.current_node:
            return
        
        best_node = None
        for node in self.current_node.connections:
            if not node.unlocked:
                continue
            
            if dx > 0 and node.x > self.current_node.x:
                best_node = node
                break
            elif dx < 0 and node.x < self.current_node.x:
                best_node = node
                break
        
        if best_node:
            self.current_node = best_node
            self.player_x = best_node.x
            self.player_y = best_node.y
    
    def enter_level(self):
        """Enter the selected level"""
        if self.current_node and self.current_node.unlocked:
            self.game.current_level_id = self.current_node.level_id
            self.game.current_level_type = self.current_node.node_type
            self.game.change_state(GAME_STATE_LEVEL)
    
    def complete_level(self, level_id):
        """Mark a level as completed"""
        for node in self.nodes:
            if node.level_id == level_id:
                node.completed = True
                
                for connected in node.connections:
                    connected.unlocked = True
                    if connected.level_id not in self.unlocked_levels:
                        self.unlocked_levels.append(connected.level_id)
                break
    
    def update(self, dt):
        """Update overworld"""
        self.animation_timer += dt
        
        if self.current_node:
            dx = self.current_node.x - self.player_x
            dy = self.current_node.y - self.player_y
            self.player_x += dx * 0.2
            self.player_y += dy * 0.2
    
    def draw(self, screen):
        """Draw overworld map"""
        screen.fill(SKY_BLUE)
        
        # Draw land
        pygame.draw.ellipse(screen, (34, 139, 34), (50, 250, 500, 200))
        
        # Draw nodes
        for node in self.nodes:
            node.draw(screen, node == self.current_node)
        
        # Draw player
        pygame.draw.rect(screen, RED,
                        (int(self.player_x) - 8, int(self.player_y) - 16, 16, 16))
        
        # HUD
        if self.current_node:
            level_text = self.font.render(f"World {self.current_node.level_id}", True, WHITE)
            screen.blit(level_text, (10, 10))
        
        lives_text = self.small_font.render(f"Lives: {self.game.lives}", True, WHITE)
        screen.blit(lives_text, (10, 50))

class LevelState:
    """Level gameplay state"""
    
    def __init__(self, game):
        self.game = game
        self.level = None
        self.player = None
        self.time_left = 300
        self.level_complete = False
        self.death_timer = 0
        self.transition_timer = 0
        self.font = pygame.font.Font(None, 48)
    
    def enter(self):
        """Enter level state"""
        theme = THEME_OVERWORLD
        if 'castle' in getattr(self.game, 'current_level_id', ''):
            theme = THEME_CASTLE
        
        self.level = Level(50, 20, theme)
        
        self.player = self.game.player
        self.player.x = self.level.start_x
        self.player.y = self.level.start_y
        self.player.vel_x = 0
        self.player.vel_y = 0
        
        self.time_left = self.level.time_limit
        self.level_complete = False
        self.death_timer = 0
        self.transition_timer = 0
        
        self.game.sound_manager.play_music('level')
    
    def exit(self):
        """Exit level state"""
        self.game.sound_manager.stop_music()
    
    def handle_event(self, event):
        """Handle level input"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(GAME_STATE_PAUSE)
    
    def update(self, dt):
        """Update level gameplay"""
        if self.level_complete:
            self.handle_level_complete(dt)
            return
        
        if self.death_timer > 0:
            self.handle_death(dt)
            return
        
        self.time_left -= dt
        if self.time_left <= 0:
            self.player_death()
            return
        
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)
        
        self.player.update(dt, self.level)
        
        if self.player.y > SCREEN_HEIGHT + 100:
            self.player_death()
            return
        
        self.level.update(dt, self.player)
        
        if self.check_level_complete():
            self.complete_level()
        
        for item in self.level.items[:]:
            if self.player.collides_with(item):
                if item.item_type == ITEM_COIN:
                    self.game.add_coin()
                elif item.item_type == ITEM_1UP:
                    self.game.add_life()
                item.collect(self.player)
                self.game.add_score(item.points)
        
        self.check_tile_collisions()
    
    def check_tile_collisions(self):
        """Check player collisions with tiles"""
        if self.player.vel_y < 0:
            head_x = self.player.x + self.player.rect.width // 2
            head_y = self.player.y
            tile = self.level.get_tile_at(head_x, head_y)
            
            if tile and tile.solid:
                if tile.type == TILE_BRICK and self.player.power_state != STATE_SMALL:
                    if self.level.break_tile(tile):
                        self.game.add_score(50)
                elif tile.type == TILE_QUESTION:
                    if self.level.hit_block(tile, self.player):
                        self.game.add_score(200)
    
    def check_level_complete(self):
        """Check if level is complete"""
        if abs(self.player.x - self.level.goal_x) < TILE_SIZE:
            return True
        
        if 'castle' in getattr(self.game, 'current_level_id', ''):
            return len(self.level.enemies) == 0
        
        return False
    
    def complete_level(self):
        """Handle level completion"""
        self.level_complete = True
        self.transition_timer = 3.0
        
        time_bonus = int(self.time_left) * 10
        self.game.add_score(time_bonus)
    
    def player_death(self):
        """Handle player death"""
        self.death_timer = 3.0
        self.player.vel_x = 0
        self.player.vel_y = -300
    
    def handle_death(self, dt):
        """Handle death animation"""
        self.death_timer -= dt
        
        self.player.vel_y += GRAVITY * dt
        self.player.y += self.player.vel_y * dt
        
        if self.death_timer <= 0:
            self.game.lose_life()
    
    def handle_level_complete(self, dt):
        """Handle level complete transition"""
        self.transition_timer -= dt
        
        if self.transition_timer <= 0:
            level_id = getattr(self.game, 'current_level_id', '1-1')
            self.game.states[GAME_STATE_OVERWORLD].complete_level(level_id)
            self.game.change_state(GAME_STATE_OVERWORLD)
    
    def draw(self, screen):
        """Draw level"""
        self.level.draw(screen)
        self.player.draw(screen, self.level.camera_x, self.level.camera_y)
        
        if self.level_complete:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(128)
            overlay.fill(BLACK)
            screen.blit(overlay, (0, 0))
            
            complete_text = self.font.render("LEVEL COMPLETE!", True, YELLOW)
            complete_rect = complete_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(complete_text, complete_rect)

class PauseState:
    """Pause menu state"""
    
    def __init__(self, game):
        self.game = game
        self.options = ['Resume', 'Return to Map', 'Main Menu']
        self.selected = 0
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 36)
    
    def enter(self):
        """Enter pause state"""
        self.selected = 0
    
    def exit(self):
        """Exit pause state"""
        pass
    
    def handle_event(self, event):
        """Handle pause menu input"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                self.select_option()
            elif event.key == pygame.K_ESCAPE:
                self.game.return_to_previous_state()
    
    def select_option(self):
        """Execute selected option"""
        if self.selected == 0:  # Resume
            self.game.return_to_previous_state()
        elif self.selected == 1:  # Return to Map
            self.game.change_state(GAME_STATE_OVERWORLD)
        elif self.selected == 2:  # Main Menu
            self.game.change_state(GAME_STATE_MENU)
    
    def update(self, dt):
        """Update pause state"""
        pass
    
    def draw(self, screen):
        """Draw pause menu"""
        if self.game.previous_state in self.game.states:
            self.game.states[self.game.previous_state].draw(screen)
        
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        
        title_text = self.font.render("PAUSED", True, YELLOW)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 150))
        screen.blit(title_text, title_rect)
        
        for i, option in enumerate(self.options):
            color = YELLOW if i == self.selected else WHITE
            text = self.small_font.render(option, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 250 + i * 50))
            screen.blit(text, text_rect)

class GameOverState:
    """Game over screen state"""
    
    def __init__(self, game):
        self.game = game
        self.options = ['Continue', 'Main Menu']
        self.selected = 0
        self.font = pygame.font.Font(None, 72)
        self.small_font = pygame.font.Font(None, 36)
    
    def enter(self):
        """Enter game over state"""
        self.selected = 0
    
    def exit(self):
        """Exit game over state"""
        pass
    
    def handle_event(self, event):
        """Handle game over input"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                self.select_option()
    
    def select_option(self):
        """Execute selected option"""
        if self.selected == 0:  # Continue
            self.game.lives = 3
            self.game.change_state(GAME_STATE_OVERWORLD)
        elif self.selected == 1:  # Main Menu
            self.game.reset()
            self.game.change_state(GAME_STATE_MENU)
    
    def update(self, dt):
        """Update game over"""
        pass
    
    def draw(self, screen):
        """Draw game over screen"""
        screen.fill(BLACK)
        
        game_over_text = self.font.render("GAME OVER", True, RED)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, 150))
        screen.blit(game_over_text, game_over_rect)
        
        score_text = self.small_font.render(f"Final Score: {self.game.score:08d}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 250))
        screen.blit(score_text, score_rect)
        
        for i, option in enumerate(self.options):
            color = YELLOW if i == self.selected else WHITE
            text = self.small_font.render(option, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 400 + i * 50))
            screen.blit(text, text_rect)

# ============================================================================
# MAIN GAME CLASS
# ============================================================================

class Game:
    """Main game controller"""
    
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        
        self.sound_manager = SoundManager()
        self.particle_system = ParticleSystem()
        self.save_system = SaveSystem()
        
        self.lives = 3
        self.coins = 0
        self.score = 0
        self.world = 1
        self.level = 1
        self.time_limit = 300
        
        self.player = Player(100, 100)
        
        self.states = {
            GAME_STATE_MENU: MenuState(self),
            GAME_STATE_OVERWORLD: OverworldState(self),
            GAME_STATE_LEVEL: LevelState(self),
            GAME_STATE_PAUSE: PauseState(self),
            GAME_STATE_GAMEOVER: GameOverState(self)
        }
        
        self.current_state = GAME_STATE_MENU
        self.previous_state = None
        
        self.load_game()
    
    def change_state(self, new_state):
        """Change game state"""
        if new_state in self.states:
            if self.current_state in self.states:
                self.states[self.current_state].exit()
            
            self.previous_state = self.current_state
            self.current_state = new_state
            self.states[new_state].enter()
    
    def return_to_previous_state(self):
        """Return to previous state"""
        if self.previous_state is not None:
            self.change_state(self.previous_state)
    
    def handle_event(self, event):
        """Handle pygame events"""
        if self.current_state in self.states:
            self.states[self.current_state].handle_event(event)
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F5:
                self.save_game()
            elif event.key == pygame.K_F9:
                self.load_game()
    
    def update(self, dt):
        """Update game logic"""
        if self.current_state in self.states:
            self.states[self.current_state].update(dt)
        
        self.particle_system.update(dt)
        self.sound_manager.update()
    
    def draw(self, screen):
        """Draw everything"""
        if self.current_state in self.states:
            self.states[self.current_state].draw(screen)
        
        self.particle_system.draw(screen)
        self.draw_hud(screen)
    
    def draw_hud(self, screen):
        """Draw HUD elements"""
        if self.current_state == GAME_STATE_LEVEL:
            font = pygame.font.Font(None, 36)
            
            score_text = font.render(f"SCORE: {self.score:08d}", True, WHITE)
            screen.blit(score_text, (10, 10))
            
            coin_text = font.render(f"COINS: {self.coins:02d}", True, YELLOW)
            screen.blit(coin_text, (10, 50))
            
            lives_text = font.render(f"LIVES: {self.lives}", True, WHITE)
            screen.blit(lives_text, (SCREEN_WIDTH - 150, 10))
            
            if hasattr(self.states[GAME_STATE_LEVEL], 'time_left'):
                time_text = font.render(f"TIME: {int(self.states[GAME_STATE_LEVEL].time_left)}", True, WHITE)
                screen.blit(time_text, (SCREEN_WIDTH // 2 - 50, 10))
    
    def add_score(self, points):
        """Add to score"""
        self.score += points
        if self.score >= 1000000:
            self.score = 999999
    
    def add_coin(self):
        """Add a coin"""
        self.coins += 1
        self.sound_manager.play_sfx('coin')
        if self.coins >= 100:
            self.coins = 0
            self.add_life()
    
    def add_life(self):
        """Add an extra life"""
        if self.lives < 99:
            self.lives += 1
            self.sound_manager.play_sfx('1up')
    
    def lose_life(self):
        """Lose a life"""
        self.lives -= 1
        if self.lives <= 0:
            self.change_state(GAME_STATE_GAMEOVER)
        else:
            self.player.reset()
            self.change_state(GAME_STATE_OVERWORLD)
    
    def save_game(self):
        """Save game progress"""
        save_data = {
            'lives': self.lives,
            'coins': self.coins,
            'score': self.score,
            'world': self.world,
            'level': self.level,
            'player_state': self.player.power_state,
            'unlocked_levels': getattr(self.states[GAME_STATE_OVERWORLD], 'unlocked_levels', [])
        }
        self.save_system.save(save_data)
    
    def load_game(self):
        """Load saved game"""
        save_data = self.save_system.load()
        if save_data:
            self.lives = save_data.get('lives', 3)
            self.coins = save_data.get('coins', 0)
            self.score = save_data.get('score', 0)
            self.world = save_data.get('world', 1)
            self.level = save_data.get('level', 1)
            self.player.power_state = save_data.get('player_state', STATE_SMALL)
            if GAME_STATE_OVERWORLD in self.states:
                self.states[GAME_STATE_OVERWORLD].unlocked_levels = save_data.get('unlocked_levels', [])
    
    def reset(self):
        """Reset game to initial state"""
        self.lives = 3
        self.coins = 0
        self.score = 0
        self.world = 1
        self.level = 1
        self.player.reset()
        self.change_state(GAME_STATE_MENU)

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Initialize and run the game"""
    pygame.init()
    pygame.mixer.init()
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Super Mario World - Haltmann Edition")
    
    try:
        icon = pygame.Surface((32, 32))
        icon.fill(RED)
        pygame.display.set_icon(icon)
    except:
        pass
    
    game = Game(screen)
    
    clock = pygame.time.Clock()
    running = True
    
    while running:
        dt = clock.tick(FPS) / 1000.0
        
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            game.handle_event(event)
        
        game.update(dt)
        
        game.draw(screen)
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

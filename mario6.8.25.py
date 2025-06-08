import asyncio
import platform
import pygame
import random
import math

# --- Initialization ---
pygame.init()

# --- Screen and Game Settings ---
WIDTH, HEIGHT = 800, 600
TILE_SIZE = 40
FPS = 60
FONT = pygame.font.Font(None, 30)
BIG_FONT = pygame.font.Font(None, 60)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Super Mario Bros - 5 Worlds")

# --- Colors ---
SKY_BLUE = (107, 140, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BROWN = (139, 69, 19)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_BLUE = (173, 216, 230)
PINK = (255, 192, 203)
DARK_GREEN = (0, 100, 0)
GOLD = (255, 215, 0)
FLESH = (255, 220, 177)

# World-specific colors
WORLD_THEMES = {
    1: {"bg": SKY_BLUE, "ground": (181, 101, 29), "brick": (200, 76, 12)},
    2: {"bg": (20, 20, 40), "ground": (80, 80, 120), "brick": (100, 100, 140)},
    3: {"bg": (0, 150, 136), "ground": (244, 164, 96), "brick": (205, 133, 63)},
    4: {"bg": (255, 140, 0), "ground": (139, 90, 43), "brick": (160, 82, 45)},
    5: {"bg": (25, 25, 112), "ground": (70, 130, 180), "brick": (100, 149, 237)},
}

# --- Physics and Player Constants ---
GRAVITY = 0.8
JUMP_SPEED = -15
MOVE_SPEED = 5
MAX_FALL_SPEED = 12
SPRINT_SPEED = 8
FIREBALL_SPEED = 10

# --- Helper Functions for Drawing ---
def draw_mario(surface, x, y, size=30, is_big=False, is_fire=False):
    """Draw Mario sprite"""
    scale = 1.5 if is_big else 1
    # Hat color based on power-up
    hat_color = WHITE if is_fire else RED
    shirt_color = RED if is_fire else RED
    
    # Hat
    pygame.draw.rect(surface, hat_color, (x+5*scale, y, 20*scale, 8*scale))
    # Face
    pygame.draw.rect(surface, FLESH, (x+5*scale, y+8*scale, 20*scale, 10*scale))
    # Eyes
    pygame.draw.rect(surface, BLACK, (x+8*scale, y+10*scale, 3*scale, 3*scale))
    pygame.draw.rect(surface, BLACK, (x+18*scale, y+10*scale, 3*scale, 3*scale))
    # Mustache
    pygame.draw.rect(surface, BLACK, (x+7*scale, y+14*scale, 16*scale, 2*scale))
    # Shirt
    pygame.draw.rect(surface, shirt_color, (x+3*scale, y+18*scale, 24*scale, 12*scale))
    # Overalls
    pygame.draw.rect(surface, (0, 0, 255), (x+3*scale, y+20*scale, 24*scale, 10*scale if not is_big else 20*scale))
    # Arms
    pygame.draw.rect(surface, FLESH, (x, y+20*scale, 3*scale, 8*scale))
    pygame.draw.rect(surface, FLESH, (x+27*scale, y+20*scale, 3*scale, 8*scale))

def draw_goomba(surface, x, y):
    """Draw Goomba sprite"""
    # Body
    pygame.draw.ellipse(surface, BROWN, (x, y+10, 30, 20))
    # Head
    pygame.draw.ellipse(surface, BROWN, (x+2, y, 26, 18))
    # Eyes
    pygame.draw.ellipse(surface, WHITE, (x+6, y+5, 6, 8))
    pygame.draw.ellipse(surface, WHITE, (x+18, y+5, 6, 8))
    pygame.draw.ellipse(surface, BLACK, (x+7, y+7, 3, 4))
    pygame.draw.ellipse(surface, BLACK, (x+19, y+7, 3, 4))
    # Feet
    pygame.draw.ellipse(surface, DARK_GRAY, (x+3, y+25, 10, 8))
    pygame.draw.ellipse(surface, DARK_GRAY, (x+17, y+25, 10, 8))

def draw_koopa(surface, x, y):
    """Draw Koopa Troopa sprite"""
    # Shell
    pygame.draw.ellipse(surface, GREEN, (x+2, y+10, 26, 20))
    # Shell pattern
    pygame.draw.arc(surface, DARK_GREEN, (x+2, y+10, 26, 20), 0, math.pi, 3)
    # Head
    pygame.draw.ellipse(surface, YELLOW, (x+20, y+5, 12, 12))
    # Eye
    pygame.draw.circle(surface, BLACK, (x+26, y+9), 2)
    # Feet
    pygame.draw.ellipse(surface, ORANGE, (x+5, y+27, 8, 6))
    pygame.draw.ellipse(surface, ORANGE, (x+17, y+27, 8, 6))

def draw_mushroom(surface, x, y, is_fire=False):
    """Draw mushroom power-up"""
    cap_color = RED if not is_fire else ORANGE
    # Stem
    pygame.draw.rect(surface, WHITE, (x+7, y+10, 16, 10))
    # Cap
    pygame.draw.ellipse(surface, cap_color, (x, y, 30, 20))
    # Spots
    pygame.draw.circle(surface, WHITE, (x+8, y+8), 4)
    pygame.draw.circle(surface, WHITE, (x+22, y+8), 4)
    pygame.draw.circle(surface, WHITE, (x+15, y+5), 3)

def draw_coin(surface, x, y, frame):
    """Draw spinning coin"""
    width = abs(math.sin(frame * 0.1) * 20) + 5
    pygame.draw.ellipse(surface, GOLD, (x+15-width//2, y+5, width, 20))
    if width > 15:
        pygame.draw.ellipse(surface, YELLOW, (x+15-width//2+3, y+8, width-6, 14))

def draw_fireball(surface, x, y, frame):
    """Draw fireball"""
    size = 8 + abs(math.sin(frame * 0.3) * 3)
    pygame.draw.circle(surface, ORANGE, (x+10, y+10), size)
    pygame.draw.circle(surface, YELLOW, (x+10, y+10), size-3)

def draw_boom_boom(surface, x, y, frame):
    """Draw Boom Boom boss"""
    # Body
    pygame.draw.ellipse(surface, GRAY, (x+10, y+20, 60, 40))
    # Shell spikes
    for i in range(4):
        spike_x = x + 20 + i * 12
        spike_y = y + 25 + abs(math.sin(i + frame * 0.1)) * 5
        pygame.draw.polygon(surface, DARK_GRAY, [
            (spike_x, spike_y),
            (spike_x-5, spike_y+10),
            (spike_x+5, spike_y+10)
        ])
    # Arms
    arm_swing = math.sin(frame * 0.1) * 10
    pygame.draw.ellipse(surface, GRAY, (x-5+arm_swing, y+30, 20, 15))
    pygame.draw.ellipse(surface, GRAY, (x+65-arm_swing, y+30, 20, 15))
    # Head
    pygame.draw.ellipse(surface, GRAY, (x+20, y, 40, 35))
    # Eyes
    pygame.draw.ellipse(surface, RED, (x+25, y+10, 10, 8))
    pygame.draw.ellipse(surface, RED, (x+45, y+10, 10, 8))
    # Mouth
    pygame.draw.arc(surface, BLACK, (x+30, y+20, 20, 10), 0, math.pi, 2)
    # Feet
    pygame.draw.ellipse(surface, DARK_GRAY, (x+15, y+55, 20, 15))
    pygame.draw.ellipse(surface, DARK_GRAY, (x+45, y+55, 20, 15))

def draw_pipe(surface, x, y, height=80):
    """Draw warp pipe"""
    # Pipe body
    pygame.draw.rect(surface, DARK_GREEN, (x+5, y+20, 70, height))
    pygame.draw.rect(surface, GREEN, (x+10, y+20, 60, height))
    # Pipe top
    pygame.draw.rect(surface, DARK_GREEN, (x, y, 80, 30))
    pygame.draw.rect(surface, GREEN, (x+5, y+5, 70, 20))

def draw_flag(surface, x, y):
    """Draw end flag"""
    # Pole
    pygame.draw.rect(surface, WHITE, (x+38, y, 4, 120))
    pygame.draw.circle(surface, GOLD, (x+40, y), 8)
    # Flag
    pygame.draw.polygon(surface, GREEN, [
        (x+42, y+10),
        (x+80, y+25),
        (x+42, y+40)
    ])

def draw_castle(surface, x, y):
    """Draw castle"""
    # Main structure
    pygame.draw.rect(surface, GRAY, (x, y+40, 120, 80))
    # Towers
    pygame.draw.rect(surface, DARK_GRAY, (x-10, y+20, 30, 100))
    pygame.draw.rect(surface, DARK_GRAY, (x+100, y+20, 30, 100))
    # Door
    pygame.draw.rect(surface, BLACK, (x+45, y+70, 30, 50))
    # Windows
    pygame.draw.rect(surface, BLACK, (x+20, y+50, 15, 15))
    pygame.draw.rect(surface, BLACK, (x+85, y+50, 15, 15))
    # Flag
    pygame.draw.rect(surface, WHITE, (x+58, y, 4, 40))
    pygame.draw.polygon(surface, RED, [
        (x+62, y+5),
        (x+80, y+15),
        (x+62, y+25)
    ])

# --- Classes ---
class Player(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        super().__init__()
        self.game = game
        self.state = "small"  # small, big, fire
        self.update_image()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.velocity = pygame.math.Vector2(0, 0)
        self.on_ground = False
        self.facing_right = True
        self.invincible = 0
        self.lives = 3

    def update_image(self):
        height = 45 if self.state != "small" else 30
        self.image = pygame.Surface((30, height), pygame.SRCALPHA)
        draw_mario(self.image, 0, 0, 30, self.state != "small", self.state == "fire")

    def update(self):
        self.apply_input()
        self.apply_gravity()
        
        # Horizontal movement and collision
        self.rect.x += self.velocity.x
        self.check_collision('horizontal')

        # Vertical movement and collision
        self.rect.y += self.velocity.y
        self.on_ground = False
        self.check_collision('vertical')
        
        # Update invincibility
        if self.invincible > 0:
            self.invincible -= 1
        
        # Death check
        if self.rect.top > HEIGHT:
            self.die()

    def apply_input(self):
        keys = pygame.key.get_pressed()
        self.velocity.x = 0
        
        sprint = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        speed = SPRINT_SPEED if sprint else MOVE_SPEED
        
        if keys[pygame.K_LEFT]:
            self.velocity.x = -speed
            self.facing_right = False
        if keys[pygame.K_RIGHT]:
            self.velocity.x = speed
            self.facing_right = True
        if keys[pygame.K_SPACE] and self.on_ground:
            self.velocity.y = JUMP_SPEED
        if keys[pygame.K_z] and self.state == "fire":
            self.shoot_fireball()

    def shoot_fireball(self):
        if len([f for f in self.game.fireballs if f.alive()]) < 2:
            direction = 1 if self.facing_right else -1
            fireball = Fireball(self.rect.centerx, self.rect.centery, direction)
            self.game.fireballs.add(fireball)
            self.game.all_sprites.add(fireball)

    def apply_gravity(self):
        self.velocity.y += GRAVITY
        if self.velocity.y > MAX_FALL_SPEED:
            self.velocity.y = MAX_FALL_SPEED

    def check_collision(self, direction):
        if direction == 'horizontal':
            for sprite in self.game.platforms:
                if sprite.rect.colliderect(self.rect):
                    if self.velocity.x > 0: 
                        self.rect.right = sprite.rect.left
                    if self.velocity.x < 0: 
                        self.rect.left = sprite.rect.right
        
        if direction == 'vertical':
            for sprite in self.game.platforms:
                if sprite.rect.colliderect(self.rect):
                    if self.velocity.y > 0:
                        self.rect.bottom = sprite.rect.top
                        self.velocity.y = 0
                        self.on_ground = True
                    if self.velocity.y < 0:
                        self.rect.top = sprite.rect.bottom
                        self.velocity.y = 0

    def power_up(self, power_type):
        if power_type == "mushroom":
            if self.state == "small":
                self.state = "big"
                self.update_image()
                old_bottom = self.rect.bottom
                self.rect = self.image.get_rect()
                self.rect.bottom = old_bottom
        elif power_type == "fire_flower":
            self.state = "fire"
            self.update_image()
            if self.state == "small":
                old_bottom = self.rect.bottom
                self.rect = self.image.get_rect()
                self.rect.bottom = old_bottom

    def take_damage(self):
        if self.invincible > 0:
            return
            
        if self.state == "fire":
            self.state = "big"
        elif self.state == "big":
            self.state = "small"
        else:
            self.die()
        
        self.update_image()
        self.invincible = 120  # 2 seconds at 60 FPS

    def die(self):
        self.lives -= 1
        if self.lives <= 0:
            self.game.game_over()
        else:
            self.game.reset_level()

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, size, color):
        super().__init__()
        self.image = pygame.Surface(size)
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))

class Brick(pygame.sprite.Sprite):
    def __init__(self, x, y, color):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(color)
        # Add brick pattern
        pygame.draw.line(self.image, BLACK, (0, TILE_SIZE//2), (TILE_SIZE, TILE_SIZE//2), 2)
        pygame.draw.line(self.image, BLACK, (TILE_SIZE//2, 0), (TILE_SIZE//2, TILE_SIZE//2), 2)
        pygame.draw.line(self.image, BLACK, (0, TILE_SIZE//2), (0, TILE_SIZE), 2)
        pygame.draw.line(self.image, BLACK, (TILE_SIZE-1, TILE_SIZE//2), (TILE_SIZE-1, TILE_SIZE), 2)
        self.rect = self.image.get_rect(topleft=(x, y))

class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.frame = 0

    def update(self):
        self.frame += 1
        self.image.fill((0, 0, 0, 0))
        draw_coin(self.image, 0, 0, self.frame)

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, enemy_type="goomba"):
        super().__init__()
        self.enemy_type = enemy_type
        self.image = pygame.Surface((30, 35), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.velocity_x = 2
        self.update_image()

    def update_image(self):
        self.image.fill((0, 0, 0, 0))
        if self.enemy_type == "goomba":
            draw_goomba(self.image, 0, 0)
        elif self.enemy_type == "koopa":
            draw_koopa(self.image, 0, 0)

    def update(self):
        self.rect.x += self.velocity_x
        # Check platform edges
        check_rect = self.rect.copy()
        check_rect.x += self.velocity_x * 10
        check_rect.y += 5
        colliding = False
        for platform in self.game.platforms:
            if check_rect.colliderect(platform.rect):
                colliding = True
                break
        if not colliding:
            self.velocity_x *= -1

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, power_type="mushroom"):
        super().__init__()
        self.power_type = power_type
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.velocity = pygame.math.Vector2(2, 0)
        self.update_image()

    def update_image(self):
        self.image.fill((0, 0, 0, 0))
        draw_mushroom(self.image, 0, 5, self.power_type == "fire_flower")

    def update(self):
        # Movement
        self.rect.x += self.velocity.x
        self.rect.y += self.velocity.y
        
        # Gravity
        self.velocity.y += GRAVITY * 0.5
        if self.velocity.y > MAX_FALL_SPEED:
            self.velocity.y = MAX_FALL_SPEED
        
        # Platform collision
        for platform in self.game.platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity.y > 0:
                    self.rect.bottom = platform.rect.top
                    self.velocity.y = 0
                elif self.velocity.x != 0:
                    self.velocity.x *= -1

class Fireball(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__()
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self.velocity = pygame.math.Vector2(FIREBALL_SPEED * direction, 0)
        self.bounce_count = 0
        self.frame = 0

    def update(self):
        self.frame += 1
        self.image.fill((0, 0, 0, 0))
        draw_fireball(self.image, 0, 0, self.frame)
        
        # Movement
        self.rect.x += self.velocity.x
        self.rect.y += self.velocity.y
        
        # Gravity
        self.velocity.y += GRAVITY * 0.5
        
        # Bounce on ground
        for platform in self.game.platforms:
            if self.rect.colliderect(platform.rect) and self.velocity.y > 0:
                self.rect.bottom = platform.rect.top
                self.velocity.y = -8
                self.bounce_count += 1
        
        # Remove after bounces or off screen
        if self.bounce_count > 3 or self.rect.right < 0 or self.rect.left > WIDTH:
            self.kill()

class Goal(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((80, 120), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(x, y-80))
        draw_flag(self.image, 0, 0)

class Castle(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((120, 120), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(x, y-80))
        draw_castle(self.image, 0, 0)

class BoomBoom(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((80, 70), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.velocity = pygame.math.Vector2(3, 0)
        self.health = 3
        self.jump_timer = 0
        self.frame = 0

    def update(self):
        self.frame += 1
        self.image.fill((0, 0, 0, 0))
        draw_boom_boom(self.image, 0, 0, self.frame)
        
        # Movement
        self.rect.x += self.velocity.x
        
        # Jump occasionally
        self.jump_timer -= 1
        if self.jump_timer <= 0 and random.random() < 0.02:
            self.velocity.y = -10
            self.jump_timer = 60
        
        # Gravity
        self.velocity.y += GRAVITY
        if self.velocity.y > MAX_FALL_SPEED:
            self.velocity.y = MAX_FALL_SPEED
        
        self.rect.y += self.velocity.y
        
        # Platform collision
        for platform in self.game.platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity.y > 0:
                    self.rect.bottom = platform.rect.top
                    self.velocity.y = 0
                else:
                    # Reverse direction when hitting walls
                    self.velocity.x *= -1

    def take_damage(self):
        self.health -= 1
        if self.health <= 0:
            self.kill()
            # Victory!
            self.game.boss_defeated()
        else:
            # Speed up when damaged
            self.velocity.x = self.velocity.x * 1.5

class Game:
    def __init__(self):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.running = True
        self.camera_offset = pygame.math.Vector2(0, 0)
        self.current_world = 1
        self.current_level = 1
        self.score = 0
        self.coins = 0
        self.state = "playing"  # playing, world_complete, game_over, victory
        
    def generate_level(self, world, level):
        """Generate level layout based on world and level number"""
        theme = WORLD_THEMES[world]
        is_castle = level == 4  # Castle level
        
        # Create base layout
        width = 60 if not is_castle else 40
        height = 15
        layout = [" " * width for _ in range(height)]
        
        # Convert to list of lists for easier manipulation
        layout = [list(row) for row in layout]
        
        # Add ground
        for x in range(width):
            layout[-2][x] = 'P'
            layout[-1][x] = 'P'
        
        if is_castle:
            # Castle level with Boom Boom
            # Platforms
            for x in range(5, 15):
                layout[7][x] = 'B'
            for x in range(25, 35):
                layout[7][x] = 'B'
            for x in range(10, 30):
                layout[10][x] = 'B'
            
            # Boss
            layout[5][20] = 'X'  # Boom Boom
            
            # Castle at end
            layout[8][35] = 'K'
        else:
            # Regular level
            # Add platforms and obstacles
            for i in range(3, width - 5, 8):
                # Platform structures
                if random.random() < 0.7:
                    height_var = random.randint(5, 9)
                    for j in range(3):
                        layout[height_var][i+j] = 'B'
                    
                    # Add coins above platforms
                    if random.random() < 0.5:
                        for j in range(3):
                            layout[height_var-3][i+j] = 'C'
                
                # Add enemies
                if random.random() < 0.4:
                    enemy_type = 'E' if world < 3 else 'K'  # Koopas in later worlds
                    layout[10][i+2] = enemy_type
            
            # Add pipes
            for i in range(10, width - 10, 15):
                if random.random() < 0.3:
                    layout[9][i] = 'W'  # Pipe
                    layout[10][i] = 'W'
            
            # Add power-ups
            if level == 1:
                layout[6][15] = '?'  # Question block with mushroom
            elif level == 2:
                layout[5][20] = 'F'  # Fire flower
            
            # Goal
            layout[8][width-5] = 'G'
        
        # Convert back to strings
        return {
            "layout": ["".join(row) for row in layout],
            "background": theme["bg"],
            "ground_color": theme["ground"],
            "brick_color": theme["brick"],
        }

    def load_level(self):
        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.bricks = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.fireballs = pygame.sprite.Group()
        self.goal = pygame.sprite.GroupSingle()
        self.boss = pygame.sprite.GroupSingle()

        level_data = self.generate_level(self.current_world, self.current_level)
        self.background_color = level_data["background"]
        self.ground_color = level_data["ground_color"]
        self.brick_color = level_data["brick_color"]

        # Set references for sprites that need game access
        Enemy.game = self
        PowerUp.game = self
        Fireball.game = self
        BoomBoom.game = self

        layout = level_data["layout"]
        for row_index, row in enumerate(layout):
            for col_index, tile in enumerate(row):
                x, y = col_index * TILE_SIZE, row_index * TILE_SIZE
                
                if tile == 'P':  # Platform/Ground
                    p = Platform(x, y, (TILE_SIZE, TILE_SIZE), self.ground_color)
                    self.platforms.add(p)
                    self.all_sprites.add(p)
                    
                elif tile == 'B':  # Brick
                    b = Brick(x, y, self.brick_color)
                    self.platforms.add(b)
                    self.bricks.add(b)
                    self.all_sprites.add(b)
                    
                elif tile == 'C':  # Coin
                    c = Coin(x, y)
                    self.coins.add(c)
                    self.all_sprites.add(c)
                    
                elif tile == 'E':  # Enemy (Goomba)
                    e = Enemy(x, y + TILE_SIZE - 35, "goomba")
                    self.enemies.add(e)
                    self.all_sprites.add(e)
                    
                elif tile == 'K':  # Koopa
                    k = Enemy(x, y + TILE_SIZE - 35, "koopa")
                    self.enemies.add(k)
                    self.all_sprites.add(k)
                    
                elif tile == '?':  # Mushroom
                    m = PowerUp(x, y, "mushroom")
                    self.powerups.add(m)
                    self.all_sprites.add(m)
                    
                elif tile == 'F':  # Fire Flower
                    f = PowerUp(x, y, "fire_flower")
                    self.powerups.add(f)
                    self.all_sprites.add(f)
                    
                elif tile == 'G':  # Goal
                    g = Goal(x, y)
                    self.goal.add(g)
                    self.all_sprites.add(g)
                    
                elif tile == 'X':  # Boom Boom
                    bb = BoomBoom(x, y)
                    self.boss.add(bb)
                    self.enemies.add(bb)
                    self.all_sprites.add(bb)
                    
                elif tile == 'K':  # Castle
                    castle = Castle(x, y)
                    self.goal.add(castle)
                    self.all_sprites.add(castle)

        # Create player
        self.player = Player(self, 100, 100)
        self.all_sprites.add(self.player)

    def reset_level(self):
        self.load_level()
        
    def next_level(self):
        self.current_level += 1
        if self.current_level > 3:
            # Go to castle level
            self.current_level = 4
            self.load_level()
        else:
            self.load_level()
    
    def boss_defeated(self):
        # Complete the world
        self.state = "world_complete"
        self.world_complete_timer = 180  # 3 seconds
    
    def next_world(self):
        self.current_world += 1
        self.current_level = 1
        if self.current_world > 5:
            self.victory()
        else:
            self.load_level()
            self.state = "playing"
    
    def victory(self):
        self.state = "victory"
    
    def game_over(self):
        self.state = "game_over"

    def update(self):
        if self.state == "playing":
            self.all_sprites.update()
            self.scroll_camera()

            # Coin collision
            coin_hits = pygame.sprite.spritecollide(self.player, self.coins, True)
            for coin in coin_hits:
                self.score += 10
                self.coins += 1

            # Power-up collision
            powerup_hits = pygame.sprite.spritecollide(self.player, self.powerups, True)
            for powerup in powerup_hits:
                self.player.power_up(powerup.power_type)
                self.score += 100

            # Enemy collision
            enemy_hits = pygame.sprite.spritecollide(self.player, self.enemies, False)
            for enemy in enemy_hits:
                if isinstance(enemy, BoomBoom):
                    # Boss collision - always take damage
                    self.player.take_damage()
                else:
                    # Regular enemy
                    if self.player.velocity.y > 0 and self.player.rect.bottom < enemy.rect.centery + 10:
                        enemy.kill()
                        self.player.velocity.y = JUMP_SPEED * 0.5
                        self.score += 50
                    else:
                        self.player.take_damage()
            
            # Fireball vs enemy collision
            for fireball in self.fireballs:
                hit_enemies = pygame.sprite.spritecollide(fireball, self.enemies, False)
                for enemy in hit_enemies:
                    if isinstance(enemy, BoomBoom):
                        enemy.take_damage()
                    else:
                        enemy.kill()
                    fireball.kill()
                    self.score += 25
            
            # Goal collision
            if pygame.sprite.spritecollide(self.player, self.goal, False):
                if self.current_level == 4:
                    # Castle level complete (shouldn't reach here normally)
                    self.boss_defeated()
                else:
                    self.next_level()
                    
        elif self.state == "world_complete":
            self.world_complete_timer -= 1
            if self.world_complete_timer <= 0:
                self.next_world()

    def draw(self):
        self.screen.fill(self.background_color)
        
        if self.state == "playing":
            # Draw sprites
            for sprite in self.all_sprites:
                # Flicker effect for invincible player
                if sprite == self.player and self.player.invincible > 0 and self.player.invincible % 10 < 5:
                    continue
                self.screen.blit(sprite.image, sprite.rect.topleft - self.camera_offset)
            
            # HUD
            self.draw_hud()
            
        elif self.state == "world_complete":
            text = BIG_FONT.render(f"World {self.current_world} Complete!", True, WHITE)
            text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2))
            self.screen.blit(text, text_rect)
            
        elif self.state == "victory":
            text = BIG_FONT.render("Victory! You saved the kingdom!", True, GOLD)
            text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
            self.screen.blit(text, text_rect)
            
            score_text = FONT.render(f"Final Score: {self.score}", True, WHITE)
            score_rect = score_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 20))
            self.screen.blit(score_text, score_rect)
            
        elif self.state == "game_over":
            text = BIG_FONT.render("Game Over", True, RED)
            text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2))
            self.screen.blit(text, text_rect)

        pygame.display.flip()

    def draw_hud(self):
        # Score
        score_text = FONT.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        
        # Coins
        coin_text = FONT.render(f"Coins: {self.coins}", True, GOLD)
        self.screen.blit(coin_text, (10, 45))
        
        # Lives
        lives_text = FONT.render(f"Lives: {self.player.lives}", True, WHITE)
        self.screen.blit(lives_text, (10, 80))
        
        # World and Level
        level_text = FONT.render(f"World {self.current_world}-{self.current_level}", True, WHITE)
        self.screen.blit(level_text, (WIDTH - 150, 10))
        
        # Power state
        power_text = FONT.render(f"Power: {self.player.state.title()}", True, WHITE)
        self.screen.blit(power_text, (WIDTH - 150, 45))

    def scroll_camera(self):
        # Follow player with camera
        self.camera_offset.x = self.player.rect.centerx - WIDTH / 2
        self.camera_offset.y = 0
        
        # Get level width
        level_layout = self.generate_level(self.current_world, self.current_level)["layout"]
        level_width = len(level_layout[0]) * TILE_SIZE
        
        # Clamp camera
        if self.camera_offset.x < 0: 
            self.camera_offset.x = 0
        if self.camera_offset.x > level_width - WIDTH: 
            self.camera_offset.x = level_width - WIDTH

    async def run(self):
        self.load_level()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and self.state == "game_over":
                        # Restart game
                        self.__init__()
                        self.load_level()

            self.update()
            self.draw()
            self.clock.tick(FPS)
            await asyncio.sleep(0)
        
        pygame.quit()

async def main():
    game = Game()
    await game.run()

if __name__ == "__main__":
    if platform.system() == "Emscripten":
        asyncio.run(main())
    else:
        game = Game()
        asyncio.run(game.run())

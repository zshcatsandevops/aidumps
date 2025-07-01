import pygame
import sys
import math
import random
from pygame.locals import *

# Constants
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 540
TILE_SIZE = 32
FPS = 60

# Physics constants (based on Mario Forever 2001)
GRAVITY = 0.6
MAX_X_SPEED = 6.0
MAX_Y_SPEED = 12.0
ACCELERATION = 0.5
DECELERATION = 0.3
JUMP_FORCE = -11.0
SKID_THRESHOLD = 0.5
JUMP_BUFFER_FRAMES = 5
COYOTE_TIME = 5

# Colors (NSMB2 style)
NSMB2_YELLOW = (255, 204, 0)
NSMB2_GOLD = (255, 187, 0)
NSMB2_RED = (231, 62, 1)
NSMB2_BLUE = (0, 128, 255)
NSMB2_GREEN = (0, 184, 0)
NSMB2_BROWN = (150, 75, 0)
NSMB2_SKY = (135, 206, 235)
NSMB2_CLOUD = (245, 245, 245)

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # Player state
        self.state = "small"  # small, big, fire
        self.facing_right = True
        self.on_ground = False
        self.is_jumping = False
        self.is_crouching = False
        self.is_shooting = False
        self.invincible = False
        self.invincible_timer = 0
        
        # Physics
        self.velocity = pygame.math.Vector2(0, 0)
        self.position = pygame.math.Vector2(x, y)
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.hitbox = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.jump_buffer = 0
        self.coyote_time = 0
        
        # Animation
        self.animation_frame = 0
        self.animation_timer = 0
        
        # Create placeholder graphics
        self.create_graphics()
        
    def create_graphics(self):
        self.frames = {
            "small": {
                "idle": [self.create_small_frame(0)],
                "run": [self.create_small_frame(i) for i in range(3)],
                "jump": [self.create_small_frame(3)],
                "crouch": [self.create_small_frame(4)],
                "shoot": [self.create_small_frame(5)],
            },
            "big": {
                "idle": [self.create_big_frame(0)],
                "run": [self.create_big_frame(i) for i in range(3)],
                "jump": [self.create_big_frame(3)],
                "crouch": [self.create_big_frame(4)],
                "shoot": [self.create_big_frame(5)],
            },
            "fire": {
                "idle": [self.create_fire_frame(0)],
                "run": [self.create_fire_frame(i) for i in range(3)],
                "jump": [self.create_fire_frame(3)],
                "crouch": [self.create_fire_frame(4)],
                "shoot": [self.create_fire_frame(5)],
            }
        }
        
        self.image = self.frames["small"]["idle"][0]
        self.rect = self.image.get_rect(topleft=(self.position.x, self.position.y))
        
    def create_small_frame(self, frame_type):
        # Placeholder for small Mario
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        
        # Body
        pygame.draw.rect(surf, NSMB2_RED, (8, 16, 16, 16))
        
        # Head
        pygame.draw.circle(surf, (255, 200, 150), (16, 12), 8)
        
        # Hat
        pygame.draw.rect(surf, NSMB2_RED, (8, 6, 16, 6))
        pygame.draw.circle(surf, NSMB2_RED, (16, 6), 8)
        
        # Animation variations
        if frame_type == 1:  # Running frame 1
            pygame.draw.line(surf, (0, 0, 0), (10, 32), (14, 32), 2)
            pygame.draw.line(surf, (0, 0, 0), (18, 32), (22, 32), 2)
        elif frame_type == 2:  # Running frame 2
            pygame.draw.line(surf, (0, 0, 0), (8, 32), (12, 32), 2)
            pygame.draw.line(surf, (0, 0, 0), (20, 32), (24, 32), 2)
        elif frame_type == 3:  # Jumping
            pygame.draw.line(surf, (0, 0, 0), (12, 32), (20, 32), 2)
        elif frame_type == 4:  # Crouching
            pygame.draw.rect(surf, NSMB2_RED, (8, 20, 16, 12))
            pygame.draw.circle(surf, (255, 200, 150), (16, 18), 8)
        elif frame_type == 5:  # Shooting
            pygame.draw.rect(surf, NSMB2_RED, (8, 16, 16, 16))
            pygame.draw.circle(surf, (255, 200, 150), (16, 12), 8)
            pygame.draw.circle(surf, (255, 255, 0), (24, 16), 6)  # Fireball
            
        return surf
    
    def create_big_frame(self, frame_type):
        # Placeholder for big Mario
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE*1.5), pygame.SRCALPHA)
        
        # Body
        pygame.draw.rect(surf, NSMB2_RED, (8, 24, 16, 24))
        
        # Head
        pygame.draw.circle(surf, (255, 200, 150), (16, 16), 8)
        
        # Hat
        pygame.draw.rect(surf, NSMB2_RED, (8, 10, 16, 6))
        pygame.draw.circle(surf, NSMB2_RED, (16, 10), 8)
        
        # Animation variations
        if frame_type == 1:  # Running frame 1
            pygame.draw.line(surf, (0, 0, 0), (10, 48), (14, 48), 2)
            pygame.draw.line(surf, (0, 0, 0), (18, 48), (22, 48), 2)
        elif frame_type == 2:  # Running frame 2
            pygame.draw.line(surf, (0, 0, 0), (8, 48), (12, 48), 2)
            pygame.draw.line(surf, (0, 0, 0), (20, 48), (24, 48), 2)
        elif frame_type == 3:  # Jumping
            pygame.draw.line(surf, (0, 0, 0), (12, 48), (20, 48), 2)
        elif frame_type == 4:  # Crouching
            pygame.draw.rect(surf, NSMB2_RED, (8, 32, 16, 16))
            pygame.draw.circle(surf, (255, 200, 150), (16, 28), 8)
        elif frame_type == 5:  # Shooting
            pygame.draw.rect(surf, NSMB2_RED, (8, 24, 16, 24))
            pygame.draw.circle(surf, (255, 200, 150), (16, 16), 8)
            pygame.draw.circle(surf, (255, 255, 0), (24, 24), 6)  # Fireball
            
        return surf
    
    def create_fire_frame(self, frame_type):
        # Placeholder for fire Mario
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE*1.5), pygame.SRCALPHA)
        
        # Body
        pygame.draw.rect(surf, NSMB2_RED, (8, 24, 16, 24))
        
        # Head
        pygame.draw.circle(surf, (255, 200, 150), (16, 16), 8)
        
        # Hat
        pygame.draw.rect(surf, NSMB2_RED, (8, 10, 16, 6))
        pygame.draw.circle(surf, NSMB2_RED, (16, 10), 8)
        
        # Fire suit details
        pygame.draw.rect(surf, NSMB2_YELLOW, (8, 30, 16, 8))
        pygame.draw.circle(surf, NSMB2_YELLOW, (16, 30), 8)
        
        # Animation variations
        if frame_type == 5:  # Shooting
            pygame.draw.circle(surf, (255, 255, 0), (24, 24), 6)  # Fireball
            
        return surf
    
    def update(self, keys, dt):
        # Handle horizontal movement
        self.handle_horizontal_movement(keys)
        
        # Apply gravity
        self.velocity.y = min(self.velocity.y + GRAVITY, MAX_Y_SPEED)
        
        # Handle jumping
        self.handle_jumping(keys)
        
        # Update position
        self.position.x += self.velocity.x * dt
        self.position.y += self.velocity.y * dt
        
        # Update rect and hitbox
        if self.state == "small":
            self.rect = pygame.Rect(self.position.x, self.position.y, TILE_SIZE, TILE_SIZE)
            self.hitbox = pygame.Rect(self.position.x + 4, self.position.y + 4, TILE_SIZE - 8, TILE_SIZE - 8)
        else:
            self.rect = pygame.Rect(self.position.x, self.position.y, TILE_SIZE, TILE_SIZE * 1.5)
            self.hitbox = pygame.Rect(self.position.x + 4, self.position.y + 4, TILE_SIZE - 8, TILE_SIZE * 1.5 - 8)
        
        # Update animation
        self.update_animation(keys)
        
        # Handle invincibility
        if self.invincible:
            self.invincible_timer -= dt
            if self.invincible_timer <= 0:
                self.invincible = False
    
    def handle_horizontal_movement(self, keys):
        # Handle left/right movement with acceleration/deceleration
        if keys[K_RIGHT]:
            if self.velocity.x < 0:  # Turning around
                self.velocity.x += ACCELERATION * 2  # Skid
            else:
                self.velocity.x += ACCELERATION
            self.facing_right = True
        elif keys[K_LEFT]:
            if self.velocity.x > 0:  # Turning around
                self.velocity.x -= ACCELERATION * 2  # Skid
            else:
                self.velocity.x -= ACCELERATION
            self.facing_right = False
        else:
            # Decelerate when no keys are pressed
            if self.velocity.x > 0:
                self.velocity.x = max(0, self.velocity.x - DECELERATION)
            elif self.velocity.x < 0:
                self.velocity.x = min(0, self.velocity.x + DECELERATION)
        
        # Cap the speed
        self.velocity.x = max(-MAX_X_SPEED, min(MAX_X_SPEED, self.velocity.x))
    
    def handle_jumping(self, keys):
        # Jump buffering
        if keys[K_z]:
            self.jump_buffer = JUMP_BUFFER_FRAMES
        
        # Coyote time
        if self.on_ground:
            self.coyote_time = COYOTE_TIME
        else:
            self.coyote_time = max(0, self.coyote_time - 1)
        
        # Jump if conditions are met
        if (self.jump_buffer > 0 and (self.on_ground or self.coyote_time > 0)) and not self.is_jumping:
            self.velocity.y = JUMP_FORCE
            self.on_ground = False
            self.is_jumping = True
            self.jump_buffer = 0
            self.coyote_time = 0
        
        # Variable jump height
        if not keys[K_z] and self.velocity.y < -3:
            self.velocity.y = -3
        
        # Reset jump buffer
        if self.jump_buffer > 0:
            self.jump_buffer -= 1
    
    def update_animation(self, keys):
        # Determine animation state
        state = "idle"
        if not self.on_ground:
            state = "jump"
        elif keys[K_DOWN] and self.state != "small":
            state = "crouch"
            self.is_crouching = True
        elif abs(self.velocity.x) > 0.1:
            state = "run"
        elif self.is_shooting:
            state = "shoot"
        
        # Update animation frame
        self.animation_timer += 1
        if state == "run" and self.animation_timer >= 5:
            self.animation_frame = (self.animation_frame + 1) % len(self.frames[self.state]["run"])
            self.animation_timer = 0
        
        # Get current frame
        frames = self.frames[self.state][state]
        self.image = frames[self.animation_frame % len(frames)]
        
        # Flip image if facing left
        if not self.facing_right:
            self.image = pygame.transform.flip(self.image, True, False)
    
    def get_hit(self):
        if self.invincible:
            return False
            
        if self.state == "fire":
            self.state = "big"
            self.invincible = True
            self.invincible_timer = 60
            return False
        elif self.state == "big":
            self.state = "small"
            self.invincible = True
            self.invincible_timer = 60
            return False
        else:
            return True  # Player died
    
    def grow(self):
        if self.state == "small":
            self.state = "big"
            self.invincible = True
            self.invincible_timer = 60
            return True
        return False
    
    def become_fire(self):
        if self.state == "big":
            self.state = "fire"
            self.invincible = True
            self.invincible_timer = 60
            return True
        return False

class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y, tile_type):
        super().__init__()
        self.type = tile_type
        self.position = pygame.math.Vector2(x, y)
        
        # Create placeholder graphics
        self.create_graphics()
        
        # Set collision properties
        self.solid = True
        self.bumpable = False
        self.breakable = False
        self.coin = False
        
        if tile_type == "?":
            self.bumpable = True
        elif tile_type == "B":
            self.breakable = True
        elif tile_type == "C":
            self.coin = True
            self.solid = False
        elif tile_type == " ":
            self.solid = False
    
    def create_graphics(self):
        # Create different tile types with NSMB2 style
        if self.type == "G":  # Ground
            self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.image.fill(NSMB2_BROWN)
            pygame.draw.rect(self.image, (100, 50, 0), (0, 0, TILE_SIZE, TILE_SIZE), 2)
            pygame.draw.rect(self.image, (180, 130, 70), (0, 0, TILE_SIZE, 4))
        elif self.type == "D":  # Dirt
            self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.image.fill((110, 70, 40))
            for _ in range(10):
                x = random.randint(2, TILE_SIZE - 4)
                y = random.randint(2, TILE_SIZE - 4)
                pygame.draw.rect(self.image, (90, 50, 20), (x, y, 2, 2))
        elif self.type == "?":  # Question block
            self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.image.fill(NSMB2_YELLOW)
            pygame.draw.rect(self.image, NSMB2_GOLD, (0, 0, TILE_SIZE, TILE_SIZE), 3)
            pygame.draw.rect(self.image, (220, 170, 0), (4, 4, TILE_SIZE-8, TILE_SIZE-8))
            pygame.draw.rect(self.image, (255, 230, 100), (8, 8, TILE_SIZE-16, TILE_SIZE-16))
            pygame.draw.rect(self.image, (255, 255, 0), (12, 12, 8, 8))
        elif self.type == "B":  # Brick
            self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.image.fill(NSMB2_RED)
            pygame.draw.rect(self.image, (200, 50, 0), (0, 0, TILE_SIZE, TILE_SIZE), 2)
            for i in range(3):
                pygame.draw.line(self.image, (200, 50, 0), (0, i*8+4), (TILE_SIZE, i*8+4), 1)
        elif self.type == "C":  # Coin
            self.image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(self.image, NSMB2_YELLOW, (TILE_SIZE//2, TILE_SIZE//2), 8)
            pygame.draw.circle(self.image, (255, 255, 0), (TILE_SIZE//2, TILE_SIZE//2), 6)
        elif self.type == "P":  # Pipe
            self.image = pygame.Surface((TILE_SIZE, TILE_SIZE*2))
            self.image.fill(NSMB2_GREEN)
            pygame.draw.rect(self.image, (0, 150, 0), (0, 0, TILE_SIZE, TILE_SIZE*2), 2)
            pygame.draw.rect(self.image, (0, 100, 0), (4, 4, TILE_SIZE-8, TILE_SIZE-8))
        else:  # Empty
            self.image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        
        self.rect = self.image.get_rect(topleft=(self.position.x, self.position.y))
    
    def bump(self):
        if self.type == "?":
            # Turn into used block
            self.type = "U"
            self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.image.fill((150, 150, 150))
            pygame.draw.rect(self.image, (100, 100, 100), (0, 0, TILE_SIZE, TILE_SIZE), 2)
            self.bumpable = False
            return True
        return False

class Goomba(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.position = pygame.math.Vector2(x, y)
        self.velocity = pygame.math.Vector2(-1, 0)
        self.direction = -1
        self.on_ground = False
        
        # Create placeholder graphics
        self.create_graphics()
        
        self.rect = self.image.get_rect(topleft=(self.position.x, self.position.y))
        self.hitbox = pygame.Rect(x+4, y+4, TILE_SIZE-8, TILE_SIZE-8)
        
        # Animation
        self.animation_frame = 0
        self.animation_timer = 0
    
    def create_graphics(self):
        self.frames = []
        for i in range(2):
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            
            # Body
            pygame.draw.ellipse(surf, (180, 100, 40), (4, 8, TILE_SIZE-8, TILE_SIZE-8))
            
            # Head
            pygame.draw.ellipse(surf, (180, 100, 40), (8, 4, TILE_SIZE-16, 12))
            
            # Eyes
            eye_x = 12 if i == 0 else 16
            pygame.draw.circle(surf, (0, 0, 0), (eye_x, 10), 2)
            pygame.draw.circle(surf, (0, 0, 0), (TILE_SIZE - eye_x, 10), 2)
            
            # Feet
            pygame.draw.ellipse(surf, (120, 60, 20), (6, TILE_SIZE-6, 8, 4))
            pygame.draw.ellipse(surf, (120, 60, 20), (TILE_SIZE-14, TILE_SIZE-6, 8, 4))
            
            self.frames.append(surf)
        
        self.image = self.frames[0]
    
    def update(self, dt, tiles):
        # Apply gravity
        self.velocity.y = min(self.velocity.y + GRAVITY, MAX_Y_SPEED)
        
        # Move horizontally
        self.position.x += self.velocity.x * dt
        self.rect.x = self.position.x
        
        # Check for collisions with tiles
        for tile in tiles:
            if tile.solid and self.rect.colliderect(tile.rect):
                if self.velocity.x > 0:  # Moving right
                    self.rect.right = tile.rect.left
                    self.direction *= -1
                    self.velocity.x *= -1
                elif self.velocity.x < 0:  # Moving left
                    self.rect.left = tile.rect.right
                    self.direction *= -1
                    self.velocity.x *= -1
                self.position.x = self.rect.x
        
        # Move vertically
        self.position.y += self.velocity.y * dt
        self.rect.y = self.position.y
        self.on_ground = False
        
        for tile in tiles:
            if tile.solid and self.rect.colliderect(tile.rect):
                if self.velocity.y > 0:  # Falling
                    self.rect.bottom = tile.rect.top
                    self.on_ground = True
                    self.velocity.y = 0
                elif self.velocity.y < 0:  # Jumping
                    self.rect.top = tile.rect.bottom
                    self.velocity.y = 0
                self.position.y = self.rect.y
        
        # Update hitbox
        self.hitbox = pygame.Rect(self.rect.x+4, self.rect.y+4, TILE_SIZE-8, TILE_SIZE-8)
        
        # Update animation
        self.animation_timer += 1
        if self.animation_timer >= 10:
            self.animation_frame = (self.animation_frame + 1) % len(self.frames)
            self.animation_timer = 0
        
        self.image = self.frames[self.animation_frame]
        
        # Flip if moving left
        if self.velocity.x < 0:
            self.image = pygame.transform.flip(self.image, True, False)

class Camera:
    def __init__(self, width, height):
        self.rect = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.offset_x = 0
    
    def update(self, target, level_width):
        # Center the camera on the target
        x = target.rect.centerx - self.width // 2
        y = 0  # Only horizontal scrolling
        
        # Limit scrolling to map boundaries
        x = max(0, min(x, level_width * TILE_SIZE - self.width))
        
        self.offset_x = x
        self.rect.x = x
    
    def apply(self, entity):
        # Return the position adjusted for the camera
        return entity.rect.move(-self.offset_x, 0)

class Particle:
    def __init__(self, x, y, color, velocity, lifetime):
        self.position = pygame.math.Vector2(x, y)
        self.velocity = pygame.math.Vector2(velocity[0], velocity[1])
        self.color = color
        self.lifetime = lifetime
        self.size = random.randint(2, 6)
        self.alpha = 255
    
    def update(self, dt):
        self.position.x += self.velocity.x * dt
        self.position.y += self.velocity.y * dt
        self.velocity.y += 0.1
        self.lifetime -= dt
        self.alpha = max(0, min(255, int(255 * self.lifetime / 30)))
    
    def draw(self, screen, camera_offset):
        x = self.position.x - camera_offset
        y = self.position.y
        
        if 0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT:
            color_with_alpha = (*self.color, self.alpha)
            surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            pygame.draw.circle(surf, color_with_alpha, (self.size//2, self.size//2), self.size//2)
            screen.blit(surf, (x, y))

class CoinParticle(Particle):
    def __init__(self, x, y):
        super().__init__(x, y, (255, 223, 0), (random.uniform(-1, 1), random.uniform(-3, -1)), 30)
        self.size = random.randint(3, 5)
    
    def draw(self, screen, camera_offset):
        x = self.position.x - camera_offset
        y = self.position.y
        
        if 0 <= x < SCREEN_WIDTH and 0 <= y < SCREEN_HEIGHT:
            color = (255, 223, int(50 * (1 - self.lifetime/30)))
            pygame.draw.circle(screen, color, (int(x), int(y)), self.size)
            pygame.draw.circle(screen, (255, 255, 200), (int(x), int(y)), self.size-2)

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Mario Forever 2001 Prototype Remake - NSMB2 Graphics - World 1-1")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 24)
        
        # Game state
        self.score = 0
        self.coins = 0
        self.lives = 3
        self.time = 400
        self.world = "1-1"
        self.game_state = "playing"  # playing, paused, game_over, level_complete
        
        # Create level
        self.level_width = 0
        self.level_height = 0
        self.create_level()
        
        # Create player
        self.player = Player(64, SCREEN_HEIGHT - TILE_SIZE * 5)
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # Groups
        self.all_sprites = pygame.sprite.Group()
        self.tiles = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.particles = []
        
        # Add tiles to groups
        for row in self.level_data:
            for tile in row:
                if tile:
                    self.all_sprites.add(tile)
                    self.tiles.add(tile)
        
        # Add player
        self.all_sprites.add(self.player)
        
        # Add enemies
        self.add_enemies()
        
        # Create HUD
        self.create_hud()
        
        # Timer
        self.last_time_update = pygame.time.get_ticks()
    
    def create_level(self):
        # World 1-1 level design based on Mario Forever 2001 prototype
        level_str = """
        ....................................................................................................
        ....................................................................................................
        ....................................................................................................
        ....................................................................................................
        ....................................................................................................
        ....................................................................................................
        ....................................................................................................
        ....................................................................................................
        ......................................?B?............................................................
        .......................................G.............................................................
        ....................................................................................................
        ....................................................................................................
        ....................................................................................................
        ....................................................................................................
        ...............GGG.................GGG...........................................GGG................
        ...............GGG.................GGG...........................................GGG................
        GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG
        DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
        """
        
        # Process level string
        rows = [line.strip() for line in level_str.strip().splitlines()]
        self.level_width = len(rows[0])
        self.level_height = len(rows)
        
        self.level_data = []
        for y, row in enumerate(rows):
            tile_row = []
            for x, char in enumerate(row):
                if char == "G":
                    tile = Tile(x * TILE_SIZE, y * TILE_SIZE, "G")
                elif char == "D":
                    tile = Tile(x * TILE_SIZE, y * TILE_SIZE, "D")
                elif char == "?":
                    tile = Tile(x * TILE_SIZE, y * TILE_SIZE, "?")
                elif char == "B":
                    tile = Tile(x * TILE_SIZE, y * TILE_SIZE, "B")
                elif char == "C":
                    tile = Tile(x * TILE_SIZE, y * TILE_SIZE, "C")
                elif char == "P":
                    tile = Tile(x * TILE_SIZE, y * TILE_SIZE, "P")
                else:
                    tile = None
                tile_row.append(tile)
            self.level_data.append(tile_row)
    
    def add_enemies(self):
        # Add Goombas at strategic positions
        goomba1 = Goomba(300, SCREEN_HEIGHT - TILE_SIZE * 3)
        goomba2 = Goomba(500, SCREEN_HEIGHT - TILE_SIZE * 3)
        goomba3 = Goomba(700, SCREEN_HEIGHT - TILE_SIZE * 3)
        goomba4 = Goomba(900, SCREEN_HEIGHT - TILE_SIZE * 3)
        
        self.enemies.add(goomba1, goomba2, goomba3, goomba4)
        self.all_sprites.add(goomba1, goomba2, goomba3, goomba4)
    
    def create_hud(self):
        # Create HUD elements in NSMB2 style
        self.hud_surface = pygame.Surface((SCREEN_WIDTH, 32))
        self.hud_surface.fill((40, 40, 120))
        
        # Draw coins area
        pygame.draw.rect(self.hud_surface, (60, 60, 140), (10, 4, 80, 24))
        pygame.draw.rect(self.hud_surface, NSMB2_YELLOW, (15, 8, 16, 16))
        self.coin_text = self.font.render(f"x{self.coins:02d}", True, (255, 255, 255))
        
        # Draw score area
        pygame.draw.rect(self.hud_surface, (60, 60, 140), (100, 4, 180, 24))
        self.score_text = self.font.render(f"SCORE {self.score:06d}", True, (255, 255, 255))
        
        # Draw world area
        pygame.draw.rect(self.hud_surface, (60, 60, 140), (290, 4, 100, 24))
        self.world_text = self.font.render(f"WORLD {self.world}", True, (255, 255, 255))
        
        # Draw time area
        pygame.draw.rect(self.hud_surface, (60, 60, 140), (400, 4, 80, 24))
        self.time_text = self.font.render(f"TIME {self.time}", True, (255, 255, 255))
        
        # Draw lives area
        pygame.draw.rect(self.hud_surface, (60, 60, 140), (490, 4, 100, 24))
        self.lives_text = self.font.render(f"LIVES x{self.lives}", True, (255, 255, 255))
    
    def update_hud(self):
        # Update HUD elements
        self.hud_surface.fill((40, 40, 120))
        
        # Coins
        pygame.draw.rect(self.hud_surface, (60, 60, 140), (10, 4, 80, 24))
        pygame.draw.rect(self.hud_surface, NSMB2_YELLOW, (15, 8, 16, 16))
        self.coin_text = self.font.render(f"x{self.coins:02d}", True, (255, 255, 255))
        self.hud_surface.blit(self.coin_text, (35, 8))
        
        # Score
        pygame.draw.rect(self.hud_surface, (60, 60, 140), (100, 4, 180, 24))
        self.score_text = self.font.render(f"SCORE {self.score:06d}", True, (255, 255, 255))
        self.hud_surface.blit(self.score_text, (110, 8))
        
        # World
        pygame.draw.rect(self.hud_surface, (60, 60, 140), (290, 4, 100, 24))
        self.world_text = self.font.render(f"WORLD {self.world}", True, (255, 255, 255))
        self.hud_surface.blit(self.world_text, (300, 8))
        
        # Time
        pygame.draw.rect(self.hud_surface, (60, 60, 140), (400, 4, 80, 24))
        self.time_text = self.font.render(f"TIME {self.time}", True, (255, 255, 255))
        self.hud_surface.blit(self.time_text, (410, 8))
        
        # Lives
        pygame.draw.rect(self.hud_surface, (60, 60, 140), (490, 4, 100, 24))
        self.lives_text = self.font.render(f"LIVES x{self.lives}", True, (255, 255, 255))
        self.hud_surface.blit(self.lives_text, (500, 8))
    
    def draw_parallax(self):
        # Draw NSMB2-style parallax background
        self.screen.fill(NSMB2_SKY)
        
        # Distant mountains
        for i in range(5):
            x = (i * 400 - self.camera.offset_x * 0.1) % (SCREEN_WIDTH + 400) - 200
            pygame.draw.polygon(self.screen, (80, 120, 80), [
                (x, SCREEN_HEIGHT - 100),
                (x + 200, SCREEN_HEIGHT - 100),
                (x + 100, SCREEN_HEIGHT - 200)
            ])
        
        # Medium hills
        for i in range(7):
            x = (i * 300 - self.camera.offset_x * 0.3) % (SCREEN_WIDTH + 300) - 150
            pygame.draw.polygon(self.screen, (60, 180, 60), [
                (x, SCREEN_HEIGHT - 50),
                (x + 150, SCREEN_HEIGHT - 50),
                (x + 75, SCREEN_HEIGHT - 120)
            ])
        
        # Clouds
        for i in range(8):
            x = (i * 250 - self.camera.offset_x * 0.2) % (SCREEN_WIDTH + 250) - 125
            y = 50 + (i % 3) * 40
            pygame.draw.ellipse(self.screen, NSMB2_CLOUD, (x, y, 120, 40))
            pygame.draw.ellipse(self.screen, NSMB2_CLOUD, (x + 30, y - 20, 100, 50))
            pygame.draw.ellipse(self.screen, NSMB2_CLOUD, (x + 70, y + 10, 80, 40))
    
    def handle_collisions(self):
        # Player collisions with tiles
        for tile in pygame.sprite.spritecollide(self.player, self.tiles, False):
            if tile.rect.colliderect(self.player.rect):
                # Horizontal collision
                if self.player.velocity.x > 0:  # Moving right
                    self.player.rect.right = tile.rect.left
                elif self.player.velocity.x < 0:  # Moving left
                    self.player.rect.left = tile.rect.right
                
                # Vertical collision
                if self.player.velocity.y > 0:  # Falling
                    self.player.rect.bottom = tile.rect.top
                    self.player.on_ground = True
                    self.player.velocity.y = 0
                    
                    # Check if hitting a block from below
                    if tile.bumpable and self.player.rect.top < tile.rect.bottom:
                        if tile.bump():
                            self.add_particles(tile.rect.centerx, tile.rect.top, 10)
                            self.score += 100
                            self.coins += 1
                elif self.player.velocity.y < 0:  # Jumping
                    self.player.rect.top = tile.rect.bottom
                    self.player.velocity.y = 0
        
        # Player collisions with enemies
        for enemy in pygame.sprite.spritecollide(self.player, self.enemies, False):
            if self.player.hitbox.colliderect(enemy.hitbox):
                # Player jumping on enemy
                if self.player.velocity.y > 0 and self.player.rect.bottom < enemy.rect.centery:
                    enemy.kill()
                    self.player.velocity.y = -4
                    self.score += 100
                    self.add_particles(enemy.rect.centerx, enemy.rect.centery, 8)
                # Player hit by enemy
                elif not self.player.invincible:
                    if self.player.get_hit():
                        self.lives -= 1
                        if self.lives <= 0:
                            self.game_state = "game_over"
                        else:
                            self.player.position = pygame.math.Vector2(64, SCREEN_HEIGHT - TILE_SIZE * 4)
                            self.player.velocity = pygame.math.Vector2(0, 0)
    
    def add_particles(self, x, y, count):
        for _ in range(count):
            self.particles.append(CoinParticle(x, y))
    
    def update_particles(self, dt):
        for particle in self.particles[:]:
            particle.update(dt)
            if particle.lifetime <= 0:
                self.particles.remove(particle)
    
    def run(self):
        running = True
        while running:
            # Calculate delta time for frame-rate independent movement
            dt = self.clock.tick(FPS) / 16.67  # Normalize to ~60 FPS
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.game_state = "paused" if self.game_state == "playing" else "playing"
                    elif event.key == pygame.K_r:
                        self.__init__()  # Reset game
            
            # Update game state
            if self.game_state == "playing":
                # Update timer
                current_time = pygame.time.get_ticks()
                if current_time - self.last_time_update > 1000:  # Every second
                    self.time -= 1
                    self.last_time_update = current_time
                    if self.time <= 0:
                        self.player.get_hit()  # Time ran out
                
                # Update player
                keys = pygame.key.get_pressed()
                self.player.update(keys, dt)
                
                # Update enemies
                for enemy in self.enemies:
                    enemy.update(dt, self.tiles)
                
                # Update camera
                self.camera.update(self.player, self.level_width)
                
                # Handle collisions
                self.handle_collisions()
                
                # Update particles
                self.update_particles(dt)
                
                # Update HUD
                self.update_hud()
            
            # Draw everything
            self.draw_parallax()
            
            # Draw tiles
            for tile in self.tiles:
                screen_pos = self.camera.apply(tile)
                if -TILE_SIZE <= screen_pos.x <= SCREEN_WIDTH and -TILE_SIZE <= screen_pos.y <= SCREEN_HEIGHT:
                    self.screen.blit(tile.image, screen_pos)
            
            # Draw enemies
            for enemy in self.enemies:
                screen_pos = self.camera.apply(enemy)
                if -TILE_SIZE <= screen_pos.x <= SCREEN_WIDTH and -TILE_SIZE <= screen_pos.y <= SCREEN_HEIGHT:
                    self.screen.blit(enemy.image, screen_pos)
            
            # Draw player
            player_pos = self.camera.apply(self.player)
            self.screen.blit(self.player.image, player_pos)
            
            # Draw particles
            for particle in self.particles:
                particle.draw(self.screen, self.camera.offset_x)
            
            # Draw HUD
            self.screen.blit(self.hud_surface, (0, 0))
            
            # Draw game state overlays
            if self.game_state == "paused":
                self.draw_pause_screen()
            elif self.game_state == "game_over":
                self.draw_game_over_screen()
            
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()
    
    def draw_pause_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))
        
        font_large = pygame.font.SysFont(None, 48)
        text = font_large.render("PAUSED", True, NSMB2_YELLOW)
        text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 30))
        self.screen.blit(text, text_rect)
        
        text_small = pygame.font.SysFont(None, 32)
        text = text_small.render("Press ESC to resume", True, (255, 255, 255))
        text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 30))
        self.screen.blit(text, text_rect)
    
    def draw_game_over_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 192))
        self.screen.blit(overlay, (0, 0))
        
        font_large = pygame.font.SysFont(None, 64)
        text = font_large.render("GAME OVER", True, NSMB2_RED)
        text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
        self.screen.blit(text, text_rect)
        
        font_med = pygame.font.SysFont(None, 36)
        text = font_med.render(f"Final Score: {self.score}", True, (255, 255, 255))
        text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20))
        self.screen.blit(text, text_rect)
        
        text = font_med.render("Press R to restart", True, NSMB2_YELLOW)
        text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 70))
        self.screen.blit(text, text_rect)

if __name__ == "__main__":
    game = Game()
    game.run()

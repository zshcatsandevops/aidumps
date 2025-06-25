import pygame
import math
import random
import json
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60
GRAVITY = 0.5
JUMP_STRENGTH = -12
MOVE_SPEED = 5
TILE_SIZE = 32

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
BROWN = (139, 69, 19)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_BLUE = (173, 216, 230)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
PINK = (255, 192, 203)
CYAN = (0, 255, 255)
DARK_GREEN = (0, 100, 0)
LAVA_RED = (255, 69, 0)
CRYSTAL_BLUE = (100, 149, 237)
GOLD = (255, 215, 0)

class PowerUpType(Enum):
    NONE = 0
    SUPER = 1
    FIRE = 2
    ICE = 3
    METAL = 4

class EnemyType(Enum):
    GOOMBA = 0
    KOOPA = 1
    PIRANHA = 2
    BLOOPER = 3
    BOO = 4
    HAMMER_BRO = 5
    FIRE_SNAKE = 6
    CRYSTAL_GOLEM = 7
    MECHA_BOWSER = 8

@dataclass
class Platform:
    x: float
    y: float
    width: float
    height: float
    color: Tuple[int, int, int]
    moving: bool = False
    move_range: float = 0
    move_speed: float = 0
    disappearing: bool = False
    disappear_time: float = 0
    solid: bool = True
    hazard: bool = False
    
class Entity:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.rect = pygame.Rect(x, y, width, height)
        
    def update_rect(self):
        self.rect.x = self.x
        self.rect.y = self.y
        
    def apply_gravity(self):
        if not self.on_ground:
            self.vy += GRAVITY
            self.vy = min(self.vy, 15)  # Terminal velocity
            
    def check_collision(self, platforms):
        self.on_ground = False
        self.x += self.vx
        self.update_rect()
        
        for platform in platforms:
            if platform.solid and self.rect.colliderect(pygame.Rect(platform.x, platform.y, platform.width, platform.height)):
                if self.vx > 0:  # Moving right
                    self.rect.right = platform.x
                    self.x = self.rect.x
                elif self.vx < 0:  # Moving left
                    self.rect.left = platform.x + platform.width
                    self.x = self.rect.x
                    
        self.y += self.vy
        self.update_rect()
        
        for platform in platforms:
            if platform.solid and self.rect.colliderect(pygame.Rect(platform.x, platform.y, platform.width, platform.height)):
                if self.vy > 0:  # Falling
                    self.rect.bottom = platform.y
                    self.y = self.rect.y
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:  # Jumping
                    self.rect.top = platform.y + platform.height
                    self.y = self.rect.y
                    self.vy = 0

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 24, 32)
        self.power_up = PowerUpType.NONE
        self.lives = 3
        self.coins = 0
        self.invulnerable_timer = 0
        self.fire_cooldown = 0
        self.facing_right = True
        
    def jump(self):
        if self.on_ground:
            self.vy = JUMP_STRENGTH
            
    def move_left(self):
        self.vx = -MOVE_SPEED
        self.facing_right = False
        
    def move_right(self):
        self.vx = MOVE_SPEED
        self.facing_right = True
        
    def stop(self):
        self.vx = 0
        
    def take_damage(self):
        if self.invulnerable_timer <= 0:
            if self.power_up != PowerUpType.NONE:
                self.power_up = PowerUpType.NONE
                self.invulnerable_timer = 120
            else:
                self.lives -= 1
                self.invulnerable_timer = 180
                
    def draw(self, screen, camera_x, camera_y):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        
        if self.invulnerable_timer > 0 and self.invulnerable_timer % 10 < 5:
            return
            
        # Draw body
        color = RED
        if self.power_up == PowerUpType.FIRE:
            color = ORANGE
        elif self.power_up == PowerUpType.ICE:
            color = LIGHT_BLUE
        elif self.power_up == PowerUpType.METAL:
            color = GRAY
            
        pygame.draw.rect(screen, color, (draw_x, draw_y + 12, self.width, 20))
        
        # Draw head
        pygame.draw.circle(screen, PINK, (int(draw_x + self.width/2), int(draw_y + 8)), 8)
        
        # Draw cap
        pygame.draw.arc(screen, RED, (draw_x + 2, draw_y, self.width - 4, 16), 0, math.pi, 3)
        
        # Draw eyes
        eye_offset = 3 if self.facing_right else -3
        pygame.draw.circle(screen, BLACK, (int(draw_x + self.width/2 + eye_offset), int(draw_y + 8)), 2)

class Enemy(Entity):
    def __init__(self, x, y, enemy_type):
        self.enemy_type = enemy_type
        if enemy_type == EnemyType.GOOMBA:
            super().__init__(x, y, 24, 24)
            self.color = BROWN
            self.speed = 1
        elif enemy_type == EnemyType.KOOPA:
            super().__init__(x, y, 28, 36)
            self.color = GREEN
            self.speed = 1.5
        elif enemy_type == EnemyType.PIRANHA:
            super().__init__(x, y, 32, 48)
            self.color = GREEN
            self.speed = 0
        elif enemy_type == EnemyType.BOO:
            super().__init__(x, y, 32, 32)
            self.color = WHITE
            self.speed = 2
        else:
            super().__init__(x, y, 32, 32)
            self.color = RED
            self.speed = 1
            
        self.direction = 1
        self.alive = True
        self.patrol_start = x
        self.patrol_range = 100
        
    def update(self, platforms, player):
        if not self.alive:
            return
            
        if self.enemy_type == EnemyType.GOOMBA or self.enemy_type == EnemyType.KOOPA:
            # Basic patrol movement
            self.vx = self.speed * self.direction
            
            # Change direction at patrol boundaries or edges
            if abs(self.x - self.patrol_start) > self.patrol_range:
                self.direction *= -1
                
            self.apply_gravity()
            old_x = self.x
            self.check_collision(platforms)
            
            # If hit a wall, turn around
            if self.x == old_x and self.vx != 0:
                self.direction *= -1
                
        elif self.enemy_type == EnemyType.BOO:
            # Boo follows player when back is turned
            if player.facing_right and self.x < player.x or not player.facing_right and self.x > player.x:
                # Move toward player
                if self.x < player.x:
                    self.vx = self.speed
                else:
                    self.vx = -self.speed
                if self.y < player.y:
                    self.vy = self.speed
                else:
                    self.vy = -self.speed
            else:
                self.vx = 0
                self.vy = 0
                
            self.x += self.vx
            self.y += self.vy
            self.update_rect()
            
    def draw(self, screen, camera_x, camera_y):
        if not self.alive:
            return
            
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        
        if self.enemy_type == EnemyType.GOOMBA:
            # Draw body
            pygame.draw.rect(screen, self.color, (draw_x, draw_y + 8, self.width, 16))
            # Draw head
            pygame.draw.ellipse(screen, self.color, (draw_x - 4, draw_y, self.width + 8, 16))
            # Draw feet
            pygame.draw.circle(screen, BLACK, (int(draw_x + 6), int(draw_y + 22)), 4)
            pygame.draw.circle(screen, BLACK, (int(draw_x + 18), int(draw_y + 22)), 4)
            
        elif self.enemy_type == EnemyType.KOOPA:
            # Draw shell
            pygame.draw.ellipse(screen, self.color, (draw_x, draw_y + 12, self.width, 20))
            # Draw head
            pygame.draw.circle(screen, DARK_GREEN, (int(draw_x + self.width/2), int(draw_y + 8)), 6)
            
        elif self.enemy_type == EnemyType.BOO:
            # Draw ghost body
            pygame.draw.circle(screen, self.color, (int(draw_x + self.width/2), int(draw_y + self.height/2)), 16)
            # Draw eyes
            pygame.draw.circle(screen, BLACK, (int(draw_x + 8), int(draw_y + 12)), 3)
            pygame.draw.circle(screen, BLACK, (int(draw_x + 24), int(draw_y + 12)), 3)
            # Draw mouth
            pygame.draw.arc(screen, BLACK, (draw_x + 8, draw_y + 16, 16, 8), 0, math.pi, 2)
            
        else:
            # Generic enemy
            pygame.draw.rect(screen, self.color, (draw_x, draw_y, self.width, self.height))

class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 12
        self.collected = False
        self.animation = 0
        
    def update(self):
        self.animation += 0.1
        
    def draw(self, screen, camera_x, camera_y):
        if self.collected:
            return
            
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y + math.sin(self.animation) * 3
        
        pygame.draw.circle(screen, GOLD, (int(draw_x), int(draw_y)), self.radius)
        pygame.draw.circle(screen, YELLOW, (int(draw_x), int(draw_y)), self.radius - 2)

class PowerUp:
    def __init__(self, x, y, power_type):
        self.x = x
        self.y = y
        self.width = 24
        self.height = 24
        self.power_type = power_type
        self.collected = False
        
    def draw(self, screen, camera_x, camera_y):
        if self.collected:
            return
            
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        
        if self.power_type == PowerUpType.SUPER:
            # Mushroom
            pygame.draw.rect(screen, BROWN, (draw_x + 8, draw_y + 12, 8, 12))
            pygame.draw.circle(screen, RED, (int(draw_x + 12), int(draw_y + 8)), 10)
            pygame.draw.circle(screen, WHITE, (int(draw_x + 8), int(draw_y + 8)), 3)
            pygame.draw.circle(screen, WHITE, (int(draw_x + 16), int(draw_y + 8)), 3)
            
        elif self.power_type == PowerUpType.FIRE:
            # Fire Flower
            pygame.draw.rect(screen, GREEN, (draw_x + 10, draw_y + 16, 4, 8))
            for i in range(5):
                angle = (i * 72 + 36) * math.pi / 180
                petal_x = draw_x + 12 + math.cos(angle) * 8
                petal_y = draw_y + 10 + math.sin(angle) * 8
                pygame.draw.circle(screen, ORANGE, (int(petal_x), int(petal_y)), 4)
            pygame.draw.circle(screen, YELLOW, (int(draw_x + 12), int(draw_y + 10)), 4)
            
        elif self.power_type == PowerUpType.ICE:
            # Ice Flower
            pygame.draw.rect(screen, GREEN, (draw_x + 10, draw_y + 16, 4, 8))
            for i in range(6):
                angle = i * 60 * math.pi / 180
                crystal_x = draw_x + 12 + math.cos(angle) * 8
                crystal_y = draw_y + 10 + math.sin(angle) * 8
                pygame.draw.circle(screen, LIGHT_BLUE, (int(crystal_x), int(crystal_y)), 3)
            pygame.draw.circle(screen, WHITE, (int(draw_x + 12), int(draw_y + 10)), 4)

class Level:
    def __init__(self, world_num, level_num):
        self.world_num = world_num
        self.level_num = level_num
        self.platforms = []
        self.enemies = []
        self.coins = []
        self.power_ups = []
        self.start_x = 100
        self.start_y = 400
        self.goal_x = 0
        self.goal_y = 0
        self.width = 0
        self.height = 600
        self.bg_color = BLACK
        
        self.generate_level()
        
    def generate_level(self):
        # Set theme colors based on world
        world_themes = {
            1: (LIGHT_BLUE, GREEN, BROWN),  # Mushroom Meadows
            2: (DARK_GRAY, CRYSTAL_BLUE, GRAY),  # Crystal Caves
            3: (CYAN, BLUE, YELLOW),  # Tropical Archipelago
            4: (GRAY, ORANGE, DARK_GRAY),  # Clockwork Factory
            5: (PURPLE, DARK_GREEN, PINK),  # Mystic Forest
            6: (BLACK, LAVA_RED, DARK_GRAY),  # Volcanic Fortress
            7: (WHITE, LIGHT_BLUE, GRAY),  # Sky Citadel
            8: (BLACK, PURPLE, RED)  # Nightmare Realm
        }
        
        self.bg_color, main_color, accent_color = world_themes.get(self.world_num, (BLACK, GRAY, WHITE))
        
        # Generate level based on world and level number
        if self.world_num == 1:
            self._generate_world_1()
        elif self.world_num == 2:
            self._generate_world_2()
        elif self.world_num == 3:
            self._generate_world_3()
        elif self.world_num == 4:
            self._generate_world_4()
        elif self.world_num == 5:
            self._generate_world_5()
        elif self.world_num == 6:
            self._generate_world_6()
        elif self.world_num == 7:
            self._generate_world_7()
        elif self.world_num == 8:
            self._generate_world_8()
            
    def _generate_world_1(self):
        # Mushroom Meadows - Classic Mario gameplay
        level_length = 2000 + self.level_num * 500
        self.width = level_length
        
        # Ground
        for i in range(0, level_length, TILE_SIZE):
            self.platforms.append(Platform(i, 500, TILE_SIZE, 100, BROWN))
            
        # Generate platforms and gaps
        x = 200
        while x < level_length - 400:
            if random.random() < 0.3:  # Gap
                gap_width = random.randint(2, 4) * TILE_SIZE
                x += gap_width
            else:  # Platform
                platform_width = random.randint(3, 8) * TILE_SIZE
                platform_height = 450 - random.randint(0, 3) * 50
                self.platforms.append(Platform(x, platform_height, platform_width, 20, GREEN))
                
                # Add coins above platform
                if random.random() < 0.6:
                    for i in range(3):
                        self.coins.append(Coin(x + platform_width/2 - 30 + i * 30, platform_height - 40))
                        
                # Add enemy on platform
                if random.random() < 0.4:
                    enemy_type = EnemyType.GOOMBA if self.level_num < 3 else random.choice([EnemyType.GOOMBA, EnemyType.KOOPA])
                    self.enemies.append(Enemy(x + platform_width/2, platform_height - 40, enemy_type))
                    
                x += platform_width + TILE_SIZE
                
        # Add power-ups
        if self.level_num == 1:
            self.power_ups.append(PowerUp(300, 400, PowerUpType.SUPER))
        elif self.level_num == 3:
            self.power_ups.append(PowerUp(500, 350, PowerUpType.FIRE))
            
        # Set goal
        self.goal_x = level_length - 100
        self.goal_y = 450
        
    def _generate_world_2(self):
        # Crystal Caves - Underground theme with minecarts
        level_length = 2500 + self.level_num * 400
        self.width = level_length
        
        # Cave ceiling and floor
        for i in range(0, level_length, TILE_SIZE):
            self.platforms.append(Platform(i, 0, TILE_SIZE, 50, DARK_GRAY))
            self.platforms.append(Platform(i, 550, TILE_SIZE, 50, DARK_GRAY))
            
        # Crystal formations and platforms
        x = 150
        while x < level_length - 400:
            if self.level_num == 2 and random.random() < 0.2:  # Minecart section
                # Rails
                rail_length = random.randint(200, 400)
                for i in range(0, rail_length, 20):
                    self.platforms.append(Platform(x + i, 450, 20, 5, GRAY))
                x += rail_length + 100
            else:
                # Crystal platform
                platform_width = random.randint(80, 150)
                platform_y = random.randint(250, 450)
                self.platforms.append(Platform(x, platform_y, platform_width, 20, CRYSTAL_BLUE))
                
                # Moving platform chance
                if self.level_num >= 3 and random.random() < 0.3:
                    self.platforms[-1].moving = True
                    self.platforms[-1].move_range = 100
                    self.platforms[-1].move_speed = 1
                    
                # Stalactites (hazards)
                if self.level_num >= 4 and random.random() < 0.3:
                    self.platforms.append(Platform(x + platform_width/2, 50, 20, 60, GRAY, hazard=True))
                    
                x += platform_width + random.randint(50, 150)
                
        # Ice flower in level 4
        if self.level_num == 4:
            self.power_ups.append(PowerUp(level_length/2, 300, PowerUpType.ICE))
            
        self.goal_x = level_length - 150
        self.goal_y = 480
        
    def _generate_world_3(self):
        # Tropical Archipelago - Water levels
        level_length = 2200 + self.level_num * 600
        self.width = level_length
        
        # Water line
        water_level = 400
        
        # Islands and underwater sections
        x = 0
        while x < level_length - 300:
            if random.random() < 0.4 and self.level_num >= 2:  # Underwater section
                # Water platforms
                section_length = random.randint(300, 500)
                for i in range(3):
                    platform_x = x + random.randint(50, section_length - 50)
                    platform_y = water_level + random.randint(50, 150)
                    self.platforms.append(Platform(platform_x, platform_y, 100, 20, BLUE))
                    
                # Add Bloopers
                if self.level_num >= 3:
                    self.enemies.append(Enemy(x + section_length/2, water_level + 100, EnemyType.BLOOPER))
                    
                x += section_length
            else:  # Island
                island_width = random.randint(200, 400)
                # Beach
                self.platforms.append(Platform(x, water_level + 50, island_width, 100, YELLOW))
                # Palm trees (decorative platforms)
                self.platforms.append(Platform(x + island_width/2, water_level - 50, 120, 20, GREEN))
                
                x += island_width + random.randint(100, 200)
                
        self.goal_x = level_length - 200
        self.goal_y = water_level
        
    def _generate_world_4(self):
        # Clockwork Factory - Mechanical obstacles
        level_length = 2800 + self.level_num * 500
        self.width = level_length
        
        # Factory floor
        for i in range(0, level_length, TILE_SIZE):
            self.platforms.append(Platform(i, 550, TILE_SIZE, 50, DARK_GRAY))
            
        # Conveyor belts, pistons, and gears
        x = 200
        while x < level_length - 400:
            obstacle_type = random.randint(1, 3)
            
            if obstacle_type == 1:  # Conveyor belt
                belt_width = random.randint(150, 300)
                self.platforms.append(Platform(x, 500, belt_width, 20, GRAY))
                # Moving platform to simulate conveyor
                if self.level_num >= 2:
                    self.platforms[-1].moving = True
                    self.platforms[-1].move_range = 0
                    self.platforms[-1].move_speed = 2 if random.random() < 0.5 else -2
                    
            elif obstacle_type == 2 and self.level_num >= 2:  # Pistons
                for i in range(3):
                    piston_x = x + i * 60
                    piston = Platform(piston_x, 350, 40, 150, ORANGE)
                    piston.moving = True
                    piston.move_range = 150
                    piston.move_speed = 3
                    self.platforms.append(piston)
                    
            elif obstacle_type == 3 and self.level_num >= 3:  # Rotating gears
                gear_y = random.randint(300, 450)
                self.platforms.append(Platform(x, gear_y, 100, 20, ORANGE))
                
            x += random.randint(200, 350)
            
        # Metal cap power-up in later levels
        if self.level_num >= 4:
            self.power_ups.append(PowerUp(level_length/2, 400, PowerUpType.METAL))
            
        self.goal_x = level_length - 250
        self.goal_y = 480
        
    def _generate_world_5(self):
        # Mystic Forest - Illusions and teleportation
        level_length = 2400 + self.level_num * 700
        self.width = level_length
        
        # Mystical ground
        for i in range(0, level_length, TILE_SIZE * 3):
            if random.random() > 0.3:  # Some gaps in ground
                self.platforms.append(Platform(i, 550, TILE_SIZE * 3, 50, DARK_GREEN))
                
        # Disappearing platforms and illusions
        x = 150
        while x < level_length - 400:
            if self.level_num >= 2 and random.random() < 0.4:  # Disappearing platform
                platform = Platform(x, random.randint(300, 450), 100, 20, PURPLE)
                platform.disappearing = True
                platform.disappear_time = 180  # 3 seconds
                self.platforms.append(platform)
                
            else:  # Regular mystical platform
                platform_y = random.randint(250, 450)
                platform_width = random.randint(80, 150)
                self.platforms.append(Platform(x, platform_y, platform_width, 20, PINK))
                
                # Add Boo enemies
                if self.level_num >= 3 and random.random() < 0.3:
                    self.enemies.append(Enemy(x + platform_width/2, platform_y - 50, EnemyType.BOO))
                    
            x += random.randint(150, 250)
            
        self.goal_x = level_length - 300
        self.goal_y = 480
        
    def _generate_world_6(self):
        # Volcanic Fortress - Lava and fire hazards
        level_length = 3000 + self.level_num * 600
        self.width = level_length
        
        # Lava at bottom
        for i in range(0, level_length, TILE_SIZE):
            self.platforms.append(Platform(i, 580, TILE_SIZE, 20, LAVA_RED, hazard=True))
            
        # Castle platforms and hazards
        x = 100
        while x < level_length - 400:
            # Safe platform
            platform_width = random.randint(100, 200)
            platform_y = random.randint(350, 500)
            self.platforms.append(Platform(x, platform_y, platform_width, 30, DARK_GRAY))
            
            # Lava hazards
            if self.level_num >= 2 and random.random() < 0.4:
                # Rising lava platform
                lava_platform = Platform(x + platform_width + 50, 550, 80, 20, LAVA_RED)
                lava_platform.moving = True
                lava_platform.move_range = 200
                lava_platform.move_speed = 2
                lava_platform.hazard = True
                self.platforms.append(lava_platform)
                
            # Fire Snake enemies
            if self.level_num >= 3 and random.random() < 0.3:
                self.enemies.append(Enemy(x + platform_width/2, platform_y - 40, EnemyType.FIRE_SNAKE))
                
            x += platform_width + random.randint(100, 200)
            
        self.goal_x = level_length - 350
        self.goal_y = 400
        
    def _generate_world_7(self):
        # Sky Citadel - Precision platforming
        level_length = 2600 + self.level_num * 800
        self.width = level_length
        
        # Cloud platforms
        x = 100
        y_base = 500
        while x < level_length - 400:
            # Ascending platforms
            for i in range(random.randint(3, 6)):
                platform_y = y_base - i * 80
                cloud_platform = Platform(x + i * 120, platform_y, 80, 20, WHITE)
                
                # Disappearing clouds in later levels
                if self.level_num >= 3 and random.random() < 0.4:
                    cloud_platform.disappearing = True
                    cloud_platform.disappear_time = 180
                    
                self.platforms.append(cloud_platform)
                
                # Coins in the sky
                if random.random() < 0.5:
                    self.coins.append(Coin(x + i * 120 + 40, platform_y - 40))
                    
            x += random.randint(600, 800)
            
        # Wind effects (implemented as moving platforms)
        if self.level_num >= 4:
            for i in range(5):
                wind_platform = Platform(
                    random.randint(200, level_length - 200),
                    random.randint(200, 400),
                    150, 20, LIGHT_BLUE
                )
                wind_platform.moving = True
                wind_platform.move_range = 200
                wind_platform.move_speed = random.choice([-3, 3])
                self.platforms.append(wind_platform)
                
        self.goal_x = level_length - 400
        self.goal_y = 200
        
    def _generate_world_8(self):
        # Nightmare Realm - Everything combined
        level_length = 3500 + self.level_num * 1000
        self.width = level_length
        
        # Chaotic generation combining all previous mechanics
        x = 100
        while x < level_length - 500:
            mechanic = random.randint(1, 7)
            
            if mechanic == 1:  # Gravity flip section
                for i in range(5):
                    y_pos = 100 if i % 2 == 0 else 500
                    self.platforms.append(Platform(x + i * 100, y_pos, 80, 20, PURPLE))
                    
            elif mechanic == 2:  # Disappearing maze
                for i in range(3):
                    for j in range(3):
                        if random.random() < 0.7:
                            platform = Platform(x + i * 80, 200 + j * 100, 60, 20, RED)
                            platform.disappearing = True
                            platform.disappear_time = random.randint(60, 180)
                            self.platforms.append(platform)
                            
            elif mechanic == 3:  # Enemy gauntlet
                platform = Platform(x, 450, 300, 30, BLACK)
                self.platforms.append(platform)
                for i in range(4):
                    enemy_type = random.choice(list(EnemyType))
                    self.enemies.append(Enemy(x + 50 + i * 60, 400, enemy_type))
                    
            elif mechanic == 4:  # Lava and ice
                self.platforms.append(Platform(x, 500, 100, 20, LAVA_RED, hazard=True))
                self.platforms.append(Platform(x + 120, 500, 100, 20, LIGHT_BLUE))
                
            else:  # Random chaos
                for i in range(random.randint(2, 5)):
                    platform = Platform(
                        x + random.randint(0, 200),
                        random.randint(200, 500),
                        random.randint(60, 120),
                        20,
                        random.choice([RED, PURPLE, BLACK, GRAY])
                    )
                    if random.random() < 0.5:
                        platform.moving = True
                        platform.move_range = random.randint(50, 150)
                        platform.move_speed = random.randint(-3, 3)
                    self.platforms.append(platform)
                    
            x += random.randint(300, 500)
            
        # Boss arena for level 5
        if self.level_num == 5:
            # Create boss arena
            for i in range(10):
                self.platforms.append(Platform(level_length - 600 + i * 60, 500, 60, 30, BLACK))
                
        self.goal_x = level_length - 200
        self.goal_y = 400
        
    def update(self, dt):
        # Update moving platforms
        for platform in self.platforms:
            if platform.moving:
                platform.x += platform.move_speed
                if abs(platform.x - platform.move_range) > platform.move_range:
                    platform.move_speed *= -1
                    
            # Update disappearing platforms
            if platform.disappearing:
                platform.disappear_time -= 1
                if platform.disappear_time <= 0:
                    platform.solid = False
                    
        # Update coins
        for coin in self.coins:
            coin.update()
            
    def draw_background(self, screen, camera_x):
        screen.fill(self.bg_color)
        
        # Draw parallax background elements based on world
        if self.world_num == 1:  # Mushroom Meadows
            # Hills
            for i in range(0, self.width, 400):
                hill_x = i - camera_x * 0.5
                pygame.draw.ellipse(screen, DARK_GREEN, (hill_x, 400, 300, 200))
                
        elif self.world_num == 2:  # Crystal Caves
            # Crystals
            for i in range(0, self.width, 200):
                crystal_x = i - camera_x * 0.7
                for j in range(3):
                    pygame.draw.polygon(screen, CRYSTAL_BLUE, [
                        (crystal_x + j * 50, 100),
                        (crystal_x + j * 50 - 10, 130),
                        (crystal_x + j * 50 + 10, 130)
                    ])
                    
        elif self.world_num == 6:  # Volcanic Fortress
            # Lava bubbles
            for i in range(0, self.width, 150):
                bubble_x = i - camera_x * 0.8
                bubble_y = 500 + math.sin(pygame.time.get_ticks() * 0.001 + i) * 20
                pygame.draw.circle(screen, ORANGE, (int(bubble_x), int(bubble_y)), 10)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Mario Forever - Community Edition")
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.current_world = 1
        self.current_level = 1
        self.level = None
        self.player = None
        self.camera_x = 0
        self.camera_y = 0
        
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        self.game_state = "MENU"
        self.level_complete = False
        self.game_over = False
        
        self.start_new_level()
        
    def start_new_level(self):
        self.level = Level(self.current_world, self.current_level)
        self.player = Player(self.level.start_x, self.level.start_y)
        self.camera_x = 0
        self.camera_y = 0
        self.level_complete = False
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            if event.type == pygame.KEYDOWN:
                if self.game_state == "MENU":
                    if event.key == pygame.K_SPACE:
                        self.game_state = "PLAYING"
                        self.start_new_level()
                        
                elif self.game_state == "PLAYING":
                    if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                        self.player.jump()
                    elif event.key == pygame.K_ESCAPE:
                        self.game_state = "MENU"
                        
                elif self.game_state == "LEVEL_COMPLETE":
                    if event.key == pygame.K_SPACE:
                        self.current_level += 1
                        if self.current_level > 5:
                            self.current_level = 1
                            self.current_world += 1
                            if self.current_world > 8:
                                self.game_state = "GAME_COMPLETE"
                            else:
                                self.start_new_level()
                                self.game_state = "PLAYING"
                        else:
                            self.start_new_level()
                            self.game_state = "PLAYING"
                            
                elif self.game_state == "GAME_OVER":
                    if event.key == pygame.K_SPACE:
                        self.current_world = 1
                        self.current_level = 1
                        self.game_state = "MENU"
                        
    def update(self):
        if self.game_state != "PLAYING":
            return
            
        # Handle input
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.player.move_left()
        elif keys[pygame.K_RIGHT]:
            self.player.move_right()
        else:
            self.player.stop()
            
        # Update player physics
        self.player.apply_gravity()
        self.player.check_collision(self.level.platforms)
        
        # Update invulnerability
        if self.player.invulnerable_timer > 0:
            self.player.invulnerable_timer -= 1
            
        # Check hazards
        for platform in self.level.platforms:
            if platform.hazard and self.player.rect.colliderect(pygame.Rect(platform.x, platform.y, platform.width, platform.height)):
                self.player.take_damage()
                
        # Update enemies
        for enemy in self.level.enemies:
            enemy.update(self.level.platforms, self.player)
            
            # Check enemy collision
            if enemy.alive and self.player.rect.colliderect(enemy.rect):
                if self.player.vy > 0 and self.player.y < enemy.y:
                    # Stomp enemy
                    enemy.alive = False
                    self.player.vy = -8
                else:
                    # Take damage
                    self.player.take_damage()
                    
        # Check coin collection
        for coin in self.level.coins:
            if not coin.collected:
                dist = math.sqrt((self.player.x + self.player.width/2 - coin.x)**2 + 
                               (self.player.y + self.player.height/2 - coin.y)**2)
                if dist < coin.radius + 12:
                    coin.collected = True
                    self.player.coins += 1
                    
        # Check power-up collection
        for power_up in self.level.power_ups:
            if not power_up.collected and self.player.rect.colliderect(
                pygame.Rect(power_up.x, power_up.y, power_up.width, power_up.height)):
                power_up.collected = True
                self.player.power_up = power_up.power_type
                
        # Check level completion
        if abs(self.player.x - self.level.goal_x) < 50 and abs(self.player.y - self.level.goal_y) < 50:
            self.level_complete = True
            self.game_state = "LEVEL_COMPLETE"
            
        # Check game over
        if self.player.lives <= 0 or self.player.y > self.level.height + 100:
            self.game_over = True
            self.game_state = "GAME_OVER"
            
        # Update camera to follow player
        self.camera_x = self.player.x - SCREEN_WIDTH // 2
        self.camera_x = max(0, min(self.camera_x, self.level.width - SCREEN_WIDTH))
        
        # Update level
        self.level.update(1/60)
        
    def draw(self):
        if self.game_state == "MENU":
            self.draw_menu()
        elif self.game_state == "PLAYING":
            self.draw_game()
        elif self.game_state == "LEVEL_COMPLETE":
            self.draw_level_complete()
        elif self.game_state == "GAME_OVER":
            self.draw_game_over()
        elif self.game_state == "GAME_COMPLETE":
            self.draw_game_complete()
            
    def draw_menu(self):
        self.screen.fill(BLACK)
        
        # Title
        title = self.font.render("MARIO FOREVER", True, RED)
        subtitle = self.font.render("COMMUNITY EDITION", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 200))
        self.screen.blit(subtitle, (SCREEN_WIDTH//2 - subtitle.get_width()//2, 250))
        
        # Instructions
        start_text = self.small_font.render("Press SPACE to Start", True, WHITE)
        self.screen.blit(start_text, (SCREEN_WIDTH//2 - start_text.get_width()//2, 400))
        
        controls = [
            "Arrow Keys - Move",
            "Space/Up - Jump",
            "ESC - Menu"
        ]
        
        y = 500
        for control in controls:
            text = self.small_font.render(control, True, GRAY)
            self.screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, y))
            y += 30
            
    def draw_game(self):
        # Draw background
        self.level.draw_background(self.screen, self.camera_x)
        
        # Draw platforms
        for platform in self.level.platforms:
            if platform.disappearing and platform.disappear_time <= 60:
                # Flashing effect for disappearing platforms
                if platform.disappear_time % 10 < 5:
                    continue
                    
            draw_x = platform.x - self.camera_x
            draw_y = platform.y - self.camera_y
            
            if -platform.width < draw_x < SCREEN_WIDTH and -platform.height < draw_y < SCREEN_HEIGHT:
                pygame.draw.rect(self.screen, platform.color, 
                               (draw_x, draw_y, platform.width, platform.height))
                
        # Draw goal flag
        goal_x = self.level.goal_x - self.camera_x
        goal_y = self.level.goal_y - self.camera_y
        pygame.draw.rect(self.screen, BROWN, (goal_x - 5, goal_y - 100, 10, 100))
        pygame.draw.polygon(self.screen, RED, [
            (goal_x, goal_y - 100),
            (goal_x + 50, goal_y - 75),
            (goal_x, goal_y - 50)
        ])
        
        # Draw coins
        for coin in self.level.coins:
            coin.draw(self.screen, self.camera_x, self.camera_y)
            
        # Draw power-ups
        for power_up in self.level.power_ups:
            power_up.draw(self.screen, self.camera_x, self.camera_y)
            
        # Draw enemies
        for enemy in self.level.enemies:
            enemy.draw(self.screen, self.camera_x, self.camera_y)
            
        # Draw player
        self.player.draw(self.screen, self.camera_x, self.camera_y)
        
        # Draw HUD
        self.draw_hud()
        
    def draw_hud(self):
        # Background for HUD
        pygame.draw.rect(self.screen, BLACK, (0, 0, SCREEN_WIDTH, 40))
        
        # Lives
        lives_text = self.small_font.render(f"Lives: {self.player.lives}", True, WHITE)
        self.screen.blit(lives_text, (10, 10))
        
        # Coins
        coins_text = self.small_font.render(f"Coins: {self.player.coins}", True, YELLOW)
        self.screen.blit(coins_text, (150, 10))
        
        # World and Level
        level_text = self.small_font.render(f"World {self.current_world}-{self.current_level}", True, WHITE)
        self.screen.blit(level_text, (SCREEN_WIDTH//2 - level_text.get_width()//2, 10))
        
        # Power-up status
        power_text = self.small_font.render(f"Power: {self.player.power_up.name}", True, WHITE)
        self.screen.blit(power_text, (SCREEN_WIDTH - 200, 10))
        
    def draw_level_complete(self):
        self.draw_game()  # Draw the game in background
        
        # Overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Text
        complete_text = self.font.render("LEVEL COMPLETE!", True, GREEN)
        self.screen.blit(complete_text, (SCREEN_WIDTH//2 - complete_text.get_width()//2, 300))
        
        continue_text = self.small_font.render("Press SPACE to continue", True, WHITE)
        self.screen.blit(continue_text, (SCREEN_WIDTH//2 - continue_text.get_width()//2, 400))
        
    def draw_game_over(self):
        self.screen.fill(BLACK)
        
        game_over_text = self.font.render("GAME OVER", True, RED)
        self.screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, 300))
        
        continue_text = self.small_font.render("Press SPACE to return to menu", True, WHITE)
        self.screen.blit(continue_text, (SCREEN_WIDTH//2 - continue_text.get_width()//2, 400))
        
    def draw_game_complete(self):
        self.screen.fill(BLACK)
        
        # Congratulations
        congrats = self.font.render("CONGRATULATIONS!", True, GOLD)
        self.screen.blit(congrats, (SCREEN_WIDTH//2 - congrats.get_width()//2, 200))
        
        complete = self.font.render("You've completed all 8 worlds!", True, WHITE)
        self.screen.blit(complete, (SCREEN_WIDTH//2 - complete.get_width()//2, 300))
        
        # Stats
        stats_text = self.small_font.render(f"Total Coins: {self.player.coins}", True, YELLOW)
        self.screen.blit(stats_text, (SCREEN_WIDTH//2 - stats_text.get_width()//2, 400))
        
        thanks = self.small_font.render("Thank you for playing Mario Forever - Community Edition!", True, WHITE)
        self.screen.blit(thanks, (SCREEN_WIDTH//2 - thanks.get_width()//2, 500))
        
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)
            
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()

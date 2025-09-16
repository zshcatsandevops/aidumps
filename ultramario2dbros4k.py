#!/usr/bin/env python3
"""
Super Mario Bros 2D - 5 Worlds Edition
A complete platformer engine with physics, enemies, and power-ups
"""

import pygame
import random
import math
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRAVITY = 0.8
JUMP_STRENGTH = -15
MOVE_SPEED = 5
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (135, 206, 235)
GREEN = (34, 139, 34)
RED = (220, 20, 60)
YELLOW = (255, 215, 0)
BROWN = (139, 69, 19)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)

class PowerUpType(Enum):
    NONE = 0
    MUSHROOM = 1
    FIRE_FLOWER = 2
    STAR = 3

class EnemyType(Enum):
    GOOMBA = 1
    KOOPA = 2
    PIRANHA = 3
    BULLET = 4
    HAMMER_BRO = 5

@dataclass
class WorldTheme:
    name: str
    bg_color: Tuple[int, int, int]
    platform_color: Tuple[int, int, int]
    accent_color: Tuple[int, int, int]

class GameObject(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vx = 0
        self.vy = 0

class Player(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, 32, 32, RED)
        self.power_up = PowerUpType.NONE
        self.invincible_timer = 0
        self.fire_cooldown = 0
        self.lives = 3
        self.coins = 0
        self.on_ground = False
        self.facing_right = True
        self.update_appearance()
    
    def update_appearance(self):
        if self.power_up == PowerUpType.MUSHROOM:
            self.image = pygame.Surface((32, 48))
            self.image.fill(RED)
            old_rect = self.rect
            self.rect = self.image.get_rect()
            self.rect.x = old_rect.x
            self.rect.bottom = old_rect.bottom
        elif self.power_up == PowerUpType.FIRE_FLOWER:
            self.image = pygame.Surface((32, 48))
            self.image.fill(WHITE)
            old_rect = self.rect
            self.rect = self.image.get_rect()
            self.rect.x = old_rect.x
            self.rect.bottom = old_rect.bottom
        elif self.power_up == PowerUpType.STAR:
            self.image.fill(YELLOW)
        else:
            self.image = pygame.Surface((32, 32))
            self.image.fill(RED)
            old_rect = self.rect
            self.rect = self.image.get_rect()
            self.rect.x = old_rect.x
            self.rect.bottom = old_rect.bottom
    
    def jump(self):
        if self.on_ground:
            self.vy = JUMP_STRENGTH
    
    def update(self):
        self.vy += GRAVITY
        self.rect.x += self.vx
        self.rect.y += self.vy
        
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
            if self.invincible_timer == 0 and self.power_up == PowerUpType.STAR:
                self.power_up = PowerUpType.NONE
                self.update_appearance()
        
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1

class Platform(GameObject):
    def __init__(self, x, y, width, height, color):
        super().__init__(x, y, width, height, color)
        self.is_moving = False
        self.move_range = 0
        self.move_speed = 0
        self.start_x = x
        self.direction = 1

class Enemy(GameObject):
    def __init__(self, x, y, enemy_type):
        self.enemy_type = enemy_type
        colors = {
            EnemyType.GOOMBA: BROWN,
            EnemyType.KOOPA: GREEN,
            EnemyType.PIRANHA: GREEN,
            EnemyType.BULLET: BLACK,
            EnemyType.HAMMER_BRO: GREEN
        }
        sizes = {
            EnemyType.GOOMBA: (30, 30),
            EnemyType.KOOPA: (32, 48),
            EnemyType.PIRANHA: (40, 60),
            EnemyType.BULLET: (24, 24),
            EnemyType.HAMMER_BRO: (40, 50)
        }
        size = sizes[enemy_type]
        super().__init__(x, y, size[0], size[1], colors[enemy_type])
        self.vx = random.choice([-2, 2])
        self.patrol_distance = 100
        self.start_x = x
        self.alive = True
        
    def update(self):
        if self.enemy_type == EnemyType.BULLET:
            self.rect.x += self.vx * 2
        elif self.enemy_type == EnemyType.PIRANHA:
            # Stationary enemy
            pass
        else:
            self.rect.x += self.vx
            if abs(self.rect.x - self.start_x) > self.patrol_distance:
                self.vx *= -1
        
        self.vy += GRAVITY
        self.rect.y += self.vy

class PowerUp(GameObject):
    def __init__(self, x, y, power_type):
        self.power_type = power_type
        colors = {
            PowerUpType.MUSHROOM: RED,
            PowerUpType.FIRE_FLOWER: ORANGE,
            PowerUpType.STAR: YELLOW
        }
        super().__init__(x, y, 24, 24, colors[power_type])
        self.collected = False

class Fireball(GameObject):
    def __init__(self, x, y, direction):
        super().__init__(x, y, 12, 12, ORANGE)
        self.vx = 8 * direction
        self.vy = -5
        self.bounces = 0
        self.max_bounces = 3
    
    def update(self):
        self.vy += GRAVITY * 0.5
        self.rect.x += self.vx
        self.rect.y += self.vy

class Coin(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, 20, 20, YELLOW)
        self.collected = False
        self.animation_offset = random.random() * math.pi * 2
    
    def update(self):
        # Floating animation
        self.rect.y += math.sin(pygame.time.get_ticks() * 0.003 + self.animation_offset) * 0.5

class Flag(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, 20, 200, GREEN)

class World:
    def __init__(self, world_num, theme):
        self.world_num = world_num
        self.theme = theme
        self.platforms = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.power_ups = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()
        self.fireballs = pygame.sprite.Group()
        self.flag = None
        self.spawn_point = (100, 400)
        self.camera_x = 0
        self.level_width = 3000
        self.generate_level()
    
    def generate_level(self):
        # Generate terrain
        for i in range(0, self.level_width, 100):
            if random.random() > 0.2 or i < 200:  # Always have ground at start
                height = random.randint(80, 150)
                platform = Platform(i, SCREEN_HEIGHT - height, 100, height, self.theme.platform_color)
                self.platforms.add(platform)
                
                # Add floating platforms
                if i > 300 and random.random() > 0.6:
                    float_y = SCREEN_HEIGHT - height - random.randint(150, 300)
                    float_platform = Platform(i + random.randint(-30, 30), float_y, 
                                            random.randint(60, 120), 20, self.theme.platform_color)
                    if random.random() > 0.7:  # Moving platform
                        float_platform.is_moving = True
                        float_platform.move_range = 100
                        float_platform.move_speed = 2
                    self.platforms.add(float_platform)
        
        # Add enemies based on world difficulty
        enemy_count = 5 + self.world_num * 3
        for _ in range(enemy_count):
            x = random.randint(300, self.level_width - 200)
            y = random.randint(100, 400)
            enemy_types = list(EnemyType)[:min(self.world_num + 1, len(EnemyType))]
            enemy_type = random.choice(enemy_types)
            enemy = Enemy(x, y, enemy_type)
            self.enemies.add(enemy)
        
        # Add power-ups
        power_count = 3 + self.world_num
        for _ in range(power_count):
            x = random.randint(400, self.level_width - 300)
            y = random.randint(200, 400)
            power_type = random.choice([PowerUpType.MUSHROOM, PowerUpType.FIRE_FLOWER, PowerUpType.STAR])
            power_up = PowerUp(x, y, power_type)
            self.power_ups.add(power_up)
        
        # Add coins
        coin_count = 20 + self.world_num * 5
        for _ in range(coin_count):
            x = random.randint(200, self.level_width - 100)
            y = random.randint(100, 450)
            coin = Coin(x, y)
            self.coins.add(coin)
        
        # Add flag at the end
        self.flag = Flag(self.level_width - 150, 200)
    
    def update_camera(self, player_x):
        self.camera_x = player_x - SCREEN_WIDTH // 2
        self.camera_x = max(0, min(self.camera_x, self.level_width - SCREEN_WIDTH))

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Super Mario Bros 2D - 5 Worlds")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        self.world_themes = [
            WorldTheme("Grassland", BLUE, GREEN, YELLOW),
            WorldTheme("Desert", (255, 228, 181), (194, 154, 108), ORANGE),
            WorldTheme("Ocean", (0, 119, 190), (0, 64, 128), (173, 216, 230)),
            WorldTheme("Mountain", (176, 196, 222), (105, 105, 105), WHITE),
            WorldTheme("Castle", (25, 25, 25), (139, 0, 0), PURPLE)
        ]
        
        self.current_world_index = 0
        self.world = None
        self.player = None
        self.game_state = "MENU"
        self.score = 0
        self.high_score = 0
        
    def start_world(self, world_index):
        self.current_world_index = world_index
        theme = self.world_themes[world_index]
        self.world = World(world_index + 1, theme)
        self.player = Player(*self.world.spawn_point)
    
    def handle_collisions(self):
        # Platform collisions
        self.player.on_ground = False
        for platform in self.world.platforms:
            if self.player.rect.colliderect(platform.rect):
                if self.player.vy > 0:  # Falling
                    self.player.rect.bottom = platform.rect.top
                    self.player.vy = 0
                    self.player.on_ground = True
                    
                    # Move with moving platform
                    if platform.is_moving:
                        self.player.rect.x += platform.move_speed * platform.direction
        
        # Update moving platforms
        for platform in self.world.platforms:
            if platform.is_moving:
                platform.rect.x += platform.move_speed * platform.direction
                if abs(platform.rect.x - platform.start_x) > platform.move_range:
                    platform.direction *= -1
        
        # Enemy collisions
        for enemy in self.world.enemies:
            if not enemy.alive:
                continue
                
            if self.player.rect.colliderect(enemy.rect):
                if self.player.vy > 0 and self.player.rect.bottom < enemy.rect.centery:
                    # Stomp enemy
                    enemy.alive = False
                    self.world.enemies.remove(enemy)
                    self.score += 100
                    self.player.vy = JUMP_STRENGTH // 2
                elif self.player.invincible_timer > 0:
                    # Invincible - destroy enemy
                    enemy.alive = False
                    self.world.enemies.remove(enemy)
                    self.score += 200
                else:
                    # Take damage
                    self.take_damage()
        
        # Power-up collisions
        for power_up in self.world.power_ups:
            if not power_up.collected and self.player.rect.colliderect(power_up.rect):
                power_up.collected = True
                self.world.power_ups.remove(power_up)
                
                if power_up.power_type == PowerUpType.STAR:
                    self.player.invincible_timer = 600  # 10 seconds
                
                self.player.power_up = power_up.power_type
                self.player.update_appearance()
                self.score += 500
        
        # Coin collisions
        for coin in self.world.coins:
            if not coin.collected and self.player.rect.colliderect(coin.rect):
                coin.collected = True
                self.world.coins.remove(coin)
                self.player.coins += 1
                self.score += 50
                
                if self.player.coins >= 100:
                    self.player.coins = 0
                    self.player.lives += 1
        
        # Fireball collisions
        for fireball in self.world.fireballs:
            # Check platform collisions
            for platform in self.world.platforms:
                if fireball.rect.colliderect(platform.rect):
                    fireball.vy = -8
                    fireball.bounces += 1
                    if fireball.bounces >= fireball.max_bounces:
                        self.world.fireballs.remove(fireball)
                        break
            
            # Check enemy collisions
            for enemy in self.world.enemies:
                if enemy.alive and fireball.rect.colliderect(enemy.rect):
                    enemy.alive = False
                    self.world.enemies.remove(enemy)
                    if fireball in self.world.fireballs:
                        self.world.fireballs.remove(fireball)
                    self.score += 150
        
        # Flag collision (level complete)
        if self.world.flag and self.player.rect.colliderect(self.world.flag.rect):
            self.complete_level()
    
    def take_damage(self):
        if self.player.power_up == PowerUpType.MUSHROOM or self.player.power_up == PowerUpType.FIRE_FLOWER:
            self.player.power_up = PowerUpType.NONE
            self.player.invincible_timer = 120  # 2 seconds of invincibility
            self.player.update_appearance()
        else:
            self.player.lives -= 1
            if self.player.lives <= 0:
                self.game_over()
            else:
                self.respawn()
    
    def respawn(self):
        self.player.rect.x, self.player.rect.y = self.world.spawn_point
        self.player.vx = 0
        self.player.vy = 0
        self.player.power_up = PowerUpType.NONE
        self.player.update_appearance()
        self.player.invincible_timer = 180  # 3 seconds of invincibility
    
    def complete_level(self):
        bonus_score = 1000 * (self.current_world_index + 1)
        self.score += bonus_score
        
        if self.current_world_index < len(self.world_themes) - 1:
            self.current_world_index += 1
            self.start_world(self.current_world_index)
        else:
            self.victory()
    
    def game_over(self):
        self.high_score = max(self.high_score, self.score)
        self.game_state = "GAME_OVER"
    
    def victory(self):
        self.high_score = max(self.high_score, self.score)
        self.game_state = "VICTORY"
    
    def shoot_fireball(self):
        if self.player.power_up == PowerUpType.FIRE_FLOWER and self.player.fire_cooldown == 0:
            direction = 1 if self.player.facing_right else -1
            fireball = Fireball(
                self.player.rect.centerx + direction * 20,
                self.player.rect.centery,
                direction
            )
            self.world.fireballs.add(fireball)
            self.player.fire_cooldown = 30
    
    def update(self):
        if self.game_state != "PLAYING":
            return
        
        # Update player
        self.player.update()
        
        # Update world objects
        for enemy in self.world.enemies:
            enemy.update()
        
        for coin in self.world.coins:
            coin.update()
        
        for fireball in self.world.fireballs:
            fireball.update()
            # Remove fireballs that go off screen
            if fireball.rect.x < 0 or fireball.rect.x > self.world.level_width:
                self.world.fireballs.remove(fireball)
        
        # Handle collisions
        self.handle_collisions()
        
        # Keep player in bounds
        self.player.rect.x = max(0, min(self.player.rect.x, self.world.level_width - self.player.rect.width))
        if self.player.rect.y > SCREEN_HEIGHT:
            self.take_damage()
        
        # Update camera
        self.world.update_camera(self.player.rect.centerx)
    
    def render_menu(self):
        self.screen.fill(BLUE)
        
        title_text = self.font.render("SUPER MARIO BROS 2D", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title_text, title_rect)
        
        subtitle_text = self.font.render("5 WORLDS EDITION", True, YELLOW)
        subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(subtitle_text, subtitle_rect)
        
        for i, theme in enumerate(self.world_themes):
            y = 250 + i * 50
            world_text = self.small_font.render(f"[{i+1}] World {i+1}: {theme.name}", True, WHITE)
            self.screen.blit(world_text, (SCREEN_WIDTH // 2 - 100, y))
        
        controls_text = self.small_font.render("Arrow Keys: Move | Space: Jump | X: Fire", True, WHITE)
        controls_rect = controls_text.get_rect(center=(SCREEN_WIDTH // 2, 550))
        self.screen.blit(controls_text, controls_rect)
        
        if self.high_score > 0:
            high_score_text = self.small_font.render(f"High Score: {self.high_score}", True, YELLOW)
            high_score_rect = high_score_text.get_rect(center=(SCREEN_WIDTH // 2, 520))
            self.screen.blit(high_score_text, high_score_rect)
    
    def render_game(self):
        # Draw background
        self.screen.fill(self.world.theme.bg_color)
        
        # Draw world objects with camera offset
        for platform in self.world.platforms:
            adjusted_rect = platform.rect.copy()
            adjusted_rect.x -= self.world.camera_x
            if -platform.rect.width < adjusted_rect.x < SCREEN_WIDTH:
                self.screen.blit(platform.image, adjusted_rect)
        
        for enemy in self.world.enemies:
            if enemy.alive:
                adjusted_rect = enemy.rect.copy()
                adjusted_rect.x -= self.world.camera_x
                if -enemy.rect.width < adjusted_rect.x < SCREEN_WIDTH:
                    self.screen.blit(enemy.image, adjusted_rect)
        
        for power_up in self.world.power_ups:
            if not power_up.collected:
                adjusted_rect = power_up.rect.copy()
                adjusted_rect.x -= self.world.camera_x
                if -power_up.rect.width < adjusted_rect.x < SCREEN_WIDTH:
                    self.screen.blit(power_up.image, adjusted_rect)
        
        for coin in self.world.coins:
            if not coin.collected:
                adjusted_rect = coin.rect.copy()
                adjusted_rect.x -= self.world.camera_x
                if -coin.rect.width < adjusted_rect.x < SCREEN_WIDTH:
                    self.screen.blit(coin.image, adjusted_rect)
        
        for fireball in self.world.fireballs:
            adjusted_rect = fireball.rect.copy()
            adjusted_rect.x -= self.world.camera_x
            if -fireball.rect.width < adjusted_rect.x < SCREEN_WIDTH:
                self.screen.blit(fireball.image, adjusted_rect)
        
        # Draw flag
        if self.world.flag:
            adjusted_rect = self.world.flag.rect.copy()
            adjusted_rect.x -= self.world.camera_x
            if -self.world.flag.rect.width < adjusted_rect.x < SCREEN_WIDTH:
                self.screen.blit(self.world.flag.image, adjusted_rect)
        
        # Draw player
        adjusted_rect = self.player.rect.copy()
        adjusted_rect.x -= self.world.camera_x
        
        # Flashing effect when invincible
        if self.player.invincible_timer == 0 or self.player.invincible_timer % 10 < 5:
            self.screen.blit(self.player.image, adjusted_rect)
        
        # Draw HUD
        self.render_hud()
    
    def render_hud(self):
        # Score
        score_text = self.small_font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        
        # Lives
        lives_text = self.small_font.render(f"Lives: {self.player.lives}", True, WHITE)
        self.screen.blit(lives_text, (10, 40))
        
        # Coins
        coins_text = self.small_font.render(f"Coins: {self.player.coins}", True, YELLOW)
        self.screen.blit(coins_text, (10, 70))
        
        # World
        world_text = self.small_font.render(f"World {self.current_world_index + 1}: {self.world.theme.name}", True, WHITE)
        self.screen.blit(world_text, (SCREEN_WIDTH - 200, 10))
        
        # Power-up
        power_text = ""
        if self.player.power_up == PowerUpType.MUSHROOM:
            power_text = "Super"
        elif self.player.power_up == PowerUpType.FIRE_FLOWER:
            power_text = "Fire"
        elif self.player.power_up == PowerUpType.STAR:
            power_text = "STAR!"
        
        if power_text:
            power_display = self.small_font.render(power_text, True, YELLOW)
            self.screen.blit(power_display, (SCREEN_WIDTH - 200, 40))
    
    def render_game_over(self):
        self.screen.fill(BLACK)
        
        game_over_text = self.font.render("GAME OVER", True, RED)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(game_over_text, game_over_rect)
        
        score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 300))
        self.screen.blit(score_text, score_rect)
        
        if self.score >= self.high_score:
            new_high_text = self.font.render("NEW HIGH SCORE!", True, YELLOW)
            new_high_rect = new_high_text.get_rect(center=(SCREEN_WIDTH // 2, 350))
            self.screen.blit(new_high_text, new_high_rect)
        
        restart_text = self.small_font.render("Press SPACE to return to menu", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, 450))
        self.screen.blit(restart_text, restart_rect)
    
    def render_victory(self):
        self.screen.fill(YELLOW)
        
        victory_text = self.font.render("VICTORY!", True, GREEN)
        victory_rect = victory_text.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(victory_text, victory_rect)
        
        congrats_text = self.font.render("All 5 Worlds Complete!", True, BLACK)
        congrats_rect = congrats_text.get_rect(center=(SCREEN_WIDTH // 2, 220))
        self.screen.blit(congrats_text, congrats_rect)
        
        score_text = self.font.render(f"Final Score: {self.score}", True, BLACK)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 300))
        self.screen.blit(score_text, score_rect)
        
        if self.score >= self.high_score:
            new_high_text = self.font.render("NEW HIGH SCORE!", True, RED)
            new_high_rect = new_high_text.get_rect(center=(SCREEN_WIDTH // 2, 350))
            self.screen.blit(new_high_text, new_high_rect)
        
        restart_text = self.small_font.render("Press SPACE to return to menu", True, BLACK)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, 450))
        self.screen.blit(restart_text, restart_rect)
    
    def render(self):
        if self.game_state == "MENU":
            self.render_menu()
        elif self.game_state == "PLAYING":
            self.render_game()
        elif self.game_state == "GAME_OVER":
            self.render_game_over()
        elif self.game_state == "VICTORY":
            self.render_victory()
        
        pygame.display.flip()
    
    def handle_input(self):
        keys = pygame.key.get_pressed()
        
        if self.game_state == "MENU":
            for i in range(1, 6):
                if keys[getattr(pygame, f'K_{i}')]:
                    if i - 1 < len(self.world_themes):
                        self.start_world(i - 1)
                        self.game_state = "PLAYING"
                        self.score = 0
                        break
        
        elif self.game_state == "PLAYING":
            # Movement
            self.player.vx = 0
            
            if keys[pygame.K_LEFT]:
                self.player.vx = -MOVE_SPEED
                self.player.facing_right = False
            if keys[pygame.K_RIGHT]:
                self.player.vx = MOVE_SPEED
                self.player.facing_right = True
            
            # Run faster with shift
            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                self.player.vx *= 1.5
            
            if keys[pygame.K_SPACE] or keys[pygame.K_UP]:
                self.player.jump()
            
            if keys[pygame.K_x]:
                self.shoot_fireball()
        
        elif self.game_state in ["GAME_OVER", "VICTORY"]:
            if keys[pygame.K_SPACE]:
                self.game_state = "MENU"
    
    def run(self):
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.game_state == "PLAYING":
                            self.game_state = "MENU"
                        else:
                            running = False
            
            self.handle_input()
            self.update()
            self.render()
            self.clock.tick(FPS)
        
        pygame.quit()

def main():
    game = Game()
    game.run()

if __name__ == "__main__":
    main()

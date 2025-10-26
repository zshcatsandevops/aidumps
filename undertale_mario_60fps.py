#!/usr/bin/env python3
"""
UNDERTALE × SUPER MARIO BROS ULTIMATE
Complete Integration - 60 FPS Game Boy Advance Performance Edition
"""

import pygame
import sys
import math
import random
from enum import Enum, auto

# Initialize Pygame
pygame.init()
pygame.mixer.pre_init(44100, -16, 2, 512)

# Constants
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
MARIO_RED = (200, 0, 0)
TOAD_WHITE = (255, 220, 200)
GOOMBA_BROWN = (139, 69, 19)
PIPE_GREEN = (0, 150, 0)

class GameMode(Enum):
    """Game modes"""
    MENU = auto()
    PLATFORMER = auto()
    BATTLE = auto()
    OVERWORLD = auto()

class UndertaleMarioGame:
    """Main integrated game class"""
    
    def __init__(self):
        # Display setup with hardware acceleration
        flags = pygame.DOUBLEBUF | pygame.HWSURFACE
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
        pygame.display.set_caption("Undertale × Super Mario Bros | 60 FPS")
        
        # Performance
        self.clock = pygame.time.Clock()
        self.dt = 0
        self.fps_font = pygame.font.Font(None, 20)
        self.show_fps = True
        
        # Game state
        self.mode = GameMode.PLATFORMER
        self.running = True
        
        # Player data (shared across modes)
        self.player_data = {
            'name': 'Mario',
            'hp': 20,
            'max_hp': 20,
            'level': 1,
            'exp': 0,
            'coins': 0,
            'lives': 3,
            'power_state': 'small',  # small, super, fire
            'mercy_points': 0,
            'spare_count': 0,
            'kill_count': 0,
            'determination': 100,
            'route': 'neutral'  # pacifist, neutral, genocide
        }
        
        # Initialize game modes
        self.platformer = PlatformerMode(self)
        self.battle = BattleMode(self)
        self.overworld = OverworldMode(self)
        
        print("=== UNDERTALE × SUPER MARIO BROS ULTIMATE ===")
        print("60 FPS Game Boy Advance Performance Edition")
        print("Controls:")
        print("  Arrow Keys - Move")
        print("  Z/Space - Jump/Confirm")
        print("  X/Shift - Run/Cancel")
        print("  C - ACT/Spare")
        print("  F1-F3 - Switch Modes")
        print("  F4 - Toggle FPS Display")
        print("============================================")
    
    def handle_events(self):
        """Handle global events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.KEYDOWN:
                # Mode switching
                if event.key == pygame.K_F1:
                    self.mode = GameMode.PLATFORMER
                    print("Switched to Platformer Mode")
                elif event.key == pygame.K_F2:
                    self.mode = GameMode.BATTLE
                    self.battle.start_battle()
                    print("Switched to Battle Mode")
                elif event.key == pygame.K_F3:
                    self.mode = GameMode.OVERWORLD
                    print("Switched to Overworld Mode")
                elif event.key == pygame.K_F4:
                    self.show_fps = not self.show_fps
            
            # Pass to current mode
            if self.mode == GameMode.PLATFORMER:
                self.platformer.handle_event(event)
            elif self.mode == GameMode.BATTLE:
                self.battle.handle_event(event)
            elif self.mode == GameMode.OVERWORLD:
                self.overworld.handle_event(event)
    
    def update(self):
        """Update current mode"""
        if self.mode == GameMode.PLATFORMER:
            next_mode = self.platformer.update(self.dt)
        elif self.mode == GameMode.BATTLE:
            next_mode = self.battle.update(self.dt)
        elif self.mode == GameMode.OVERWORLD:
            next_mode = self.overworld.update(self.dt)
        
        # Handle mode transitions
        if next_mode:
            self.mode = next_mode
    
    def draw(self):
        """Draw current mode"""
        self.screen.fill(BLACK)
        
        if self.mode == GameMode.PLATFORMER:
            self.platformer.draw(self.screen)
        elif self.mode == GameMode.BATTLE:
            self.battle.draw(self.screen)
        elif self.mode == GameMode.OVERWORLD:
            self.overworld.draw(self.screen)
        
        # Draw FPS
        if self.show_fps:
            fps_text = f"FPS: {int(self.clock.get_fps())}"
            text = self.fps_font.render(fps_text, True, YELLOW)
            self.screen.blit(text, (10, 10))
            
            # Draw route indicator
            route_color = {
                'pacifist': GREEN,
                'genocide': RED,
                'neutral': WHITE
            }.get(self.player_data['route'], WHITE)
            
            route_text = f"[{self.player_data['route'].upper()}]"
            text = self.fps_font.render(route_text, True, route_color)
            self.screen.blit(text, (10, 30))
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        while self.running:
            # Calculate delta time
            self.dt = self.clock.tick(FPS) / 1000.0
            if self.dt > 0.05:  # Cap dt to prevent large jumps
                self.dt = 0.05
            
            self.handle_events()
            self.update()
            self.draw()
        
        pygame.quit()
        sys.exit()

# === PLATFORMER MODE ===

class PlatformerMode:
    """Mario-style platforming with Undertale mechanics"""
    
    def __init__(self, game):
        self.game = game
        
        # Mario
        self.mario_x = 100
        self.mario_y = 300
        self.mario_vx = 0
        self.mario_vy = 0
        self.on_ground = False
        self.facing_right = True
        
        # Level
        self.camera_x = 0
        self.tiles = []
        self.enemies = []
        self.items = []
        
        # Initialize level
        self.generate_level()
    
    def generate_level(self):
        """Generate a simple level"""
        # Ground
        for x in range(0, 2000, 32):
            self.tiles.append({'x': x, 'y': 400, 'w': 32, 'h': 32, 'type': 'ground'})
        
        # Platforms
        platforms = [
            (300, 300), (400, 300), (500, 250), (600, 250),
            (800, 320), (900, 320), (1000, 320),
            (1200, 200), (1300, 200)
        ]
        for x, y in platforms:
            self.tiles.append({'x': x, 'y': y, 'w': 32, 'h': 32, 'type': 'brick'})
        
        # Enemies
        self.enemies = [
            {'x': 250, 'y': 368, 'type': 'goomba', 'vx': -1, 'spared': False, 'hp': 1},
            {'x': 450, 'y': 368, 'type': 'goomba', 'vx': -1, 'spared': False, 'hp': 1},
            {'x': 750, 'y': 368, 'type': 'koopa', 'vx': -1, 'spared': False, 'hp': 2},
            {'x': 1050, 'y': 368, 'type': 'goomba', 'vx': -1, 'spared': False, 'hp': 1},
        ]
        
        # Items (coins)
        self.items = [
            {'x': 320, 'y': 200, 'type': 'coin'},
            {'x': 350, 'y': 200, 'type': 'coin'},
            {'x': 520, 'y': 150, 'type': 'coin'},
            {'x': 550, 'y': 150, 'type': 'coin'},
            {'x': 820, 'y': 250, 'type': 'coin'},
            {'x': 920, 'y': 250, 'type': 'coin'},
        ]
    
    def handle_event(self, event):
        """Handle platformer input"""
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_z, pygame.K_SPACE]:
                if self.on_ground:
                    self.mario_vy = -15
            elif event.key == pygame.K_c:
                # Try to spare nearby enemy
                self.try_spare_enemy()
    
    def try_spare_enemy(self):
        """Attempt to spare a nearby enemy"""
        for enemy in self.enemies:
            if not enemy['spared'] and enemy['hp'] > 0:
                dist = abs(self.mario_x - enemy['x'])
                if dist < 50:
                    enemy['spared'] = True
                    self.game.player_data['spare_count'] += 1
                    self.game.player_data['mercy_points'] += 10
                    print(f"* You spared the {enemy['type']}!")
                    
                    # Update route
                    self.update_route()
    
    def update_route(self):
        """Update route based on player actions"""
        spare = self.game.player_data['spare_count']
        kill = self.game.player_data['kill_count']
        
        if kill == 0 and spare > 5:
            self.game.player_data['route'] = 'pacifist'
        elif spare == 0 and kill > 5:
            self.game.player_data['route'] = 'genocide'
        else:
            self.game.player_data['route'] = 'neutral'
    
    def update(self, dt):
        """Update platformer physics"""
        keys = pygame.key.get_pressed()
        
        # Horizontal movement
        self.mario_vx = 0
        if keys[pygame.K_LEFT]:
            self.mario_vx = -5 if keys[pygame.K_x] else -3
            self.facing_right = False
        elif keys[pygame.K_RIGHT]:
            self.mario_vx = 5 if keys[pygame.K_x] else 3
            self.facing_right = True
        
        # Apply gravity
        if not self.on_ground:
            self.mario_vy = min(self.mario_vy + 0.8, 12)
        
        # Move Mario
        self.mario_x += self.mario_vx
        self.mario_y += self.mario_vy
        
        # Check collisions
        self.on_ground = False
        mario_rect = pygame.Rect(self.mario_x - 12, self.mario_y - 16, 24, 32)
        
        for tile in self.tiles:
            tile_rect = pygame.Rect(tile['x'], tile['y'], tile['w'], tile['h'])
            if mario_rect.colliderect(tile_rect):
                if self.mario_vy > 0:  # Falling
                    self.mario_y = tile['y'] - 16
                    self.mario_vy = 0
                    self.on_ground = True
        
        # Update enemies
        for enemy in self.enemies[:]:
            if not enemy['spared'] and enemy['hp'] > 0:
                enemy['x'] += enemy['vx']
                
                # Bounce off edges
                if enemy['x'] < 0 or enemy['x'] > 2000:
                    enemy['vx'] *= -1
                
                # Check collision with Mario
                enemy_rect = pygame.Rect(enemy['x'] - 12, enemy['y'] - 12, 24, 24)
                if mario_rect.colliderect(enemy_rect):
                    if self.mario_vy > 0:  # Jumping on enemy
                        self.mario_vy = -10  # Bounce
                        enemy['hp'] -= 1
                        if enemy['hp'] <= 0:
                            self.game.player_data['kill_count'] += 1
                            self.update_route()
                    else:
                        # Take damage
                        self.game.player_data['hp'] -= 1
                        print(f"Ouch! HP: {self.game.player_data['hp']}")
        
        # Collect items
        for item in self.items[:]:
            item_rect = pygame.Rect(item['x'] - 8, item['y'] - 8, 16, 16)
            if mario_rect.colliderect(item_rect):
                if item['type'] == 'coin':
                    self.game.player_data['coins'] += 1
                self.items.remove(item)
        
        # Update camera
        self.camera_x = max(0, self.mario_x - SCREEN_WIDTH // 2)
        
        # Check for battle trigger
        if random.random() < 0.001:  # Random encounters
            return GameMode.BATTLE
        
        return None
    
    def draw(self, screen):
        """Draw platformer scene"""
        # Sky gradient
        for y in range(0, 400, 4):
            color = (100 + y // 4, 149 + y // 4, 237 - y // 3)
            pygame.draw.rect(screen, color, (0, y, SCREEN_WIDTH, 4))
        
        # Draw tiles
        for tile in self.tiles:
            x = tile['x'] - self.camera_x
            if -32 <= x <= SCREEN_WIDTH:
                if tile['type'] == 'ground':
                    color = (139, 69, 19)
                else:
                    color = (165, 42, 42)
                pygame.draw.rect(screen, color, (x, tile['y'], tile['w'], tile['h']))
        
        # Draw items
        for item in self.items:
            x = item['x'] - self.camera_x
            if -16 <= x <= SCREEN_WIDTH:
                pygame.draw.circle(screen, YELLOW, (x, item['y']), 8)
        
        # Draw enemies
        for enemy in self.enemies:
            if enemy['hp'] > 0:
                x = enemy['x'] - self.camera_x
                if -32 <= x <= SCREEN_WIDTH:
                    if enemy['spared']:
                        color = YELLOW  # Spared enemies turn yellow
                    elif enemy['type'] == 'goomba':
                        color = GOOMBA_BROWN
                    else:
                        color = GREEN
                    
                    pygame.draw.rect(screen, color, (x - 12, enemy['y'] - 12, 24, 24))
        
        # Draw Mario
        mario_screen_x = self.mario_x - self.camera_x
        
        # Body
        pygame.draw.rect(screen, MARIO_RED, 
                        (mario_screen_x - 12, self.mario_y - 16, 24, 32))
        # Cap
        pygame.draw.rect(screen, RED,
                        (mario_screen_x - 12, self.mario_y - 16, 24, 10))
        
        # HUD
        self.draw_hud(screen)
    
    def draw_hud(self, screen):
        """Draw HUD elements"""
        font = pygame.font.Font(None, 24)
        
        # Lives
        text = font.render(f"MARIO x{self.game.player_data['lives']}", True, WHITE)
        screen.blit(text, (10, 50))
        
        # Coins
        text = font.render(f"@ x{self.game.player_data['coins']:02d}", True, YELLOW)
        screen.blit(text, (150, 50))
        
        # HP Bar
        hp_ratio = self.game.player_data['hp'] / self.game.player_data['max_hp']
        pygame.draw.rect(screen, (100, 100, 100), (300, 50, 100, 20))
        pygame.draw.rect(screen, RED, (300, 50, int(100 * hp_ratio), 20))
        
        # Mercy Points
        if self.game.player_data['mercy_points'] > 0:
            text = font.render(f"MERCY: {self.game.player_data['mercy_points']}", True, YELLOW)
            screen.blit(text, (420, 50))

# === BATTLE MODE ===

class BattleMode:
    """Undertale-style battle system"""
    
    def __init__(self, game):
        self.game = game
        
        # Battle state
        self.state = 'menu'  # menu, dodge, dialogue, victory
        self.menu_index = 0
        self.menu_options = ['FIGHT', 'ACT', 'ITEM', 'MERCY']
        
        # Battle box
        self.box_x = 160
        self.box_y = 250
        self.box_w = 320
        self.box_h = 140
        
        # Soul (player heart)
        self.soul_x = self.box_x + self.box_w // 2
        self.soul_y = self.box_y + self.box_h // 2
        self.soul_size = 16
        
        # Enemy
        self.enemy_name = "Bowser"
        self.enemy_hp = 100
        self.enemy_max_hp = 100
        self.can_spare = False
        self.spare_progress = 0
        
        # Projectiles
        self.projectiles = []
        self.dodge_timer = 0
        
        # Dialogue
        self.dialogue = ""
        self.dialogue_timer = 0
    
    def start_battle(self):
        """Initialize a new battle"""
        self.state = 'menu'
        self.enemy_hp = 100
        self.can_spare = False
        self.spare_progress = 0
        self.projectiles = []
        self.dialogue = f"* {self.enemy_name} appears!"
        self.dialogue_timer = 120
    
    def handle_event(self, event):
        """Handle battle input"""
        if event.type == pygame.KEYDOWN:
            if self.state == 'menu':
                if event.key == pygame.K_LEFT:
                    self.menu_index = (self.menu_index - 1) % 4
                elif event.key == pygame.K_RIGHT:
                    self.menu_index = (self.menu_index + 1) % 4
                elif event.key in [pygame.K_z, pygame.K_SPACE]:
                    self.select_menu_option()
    
    def select_menu_option(self):
        """Execute menu selection"""
        option = self.menu_options[self.menu_index]
        
        if option == 'FIGHT':
            damage = random.randint(8, 12)
            self.enemy_hp -= damage
            self.dialogue = f"* You dealt {damage} damage!"
            self.dialogue_timer = 120
            
            if self.enemy_hp <= 0:
                self.state = 'victory'
                self.dialogue = "* You won!"
                self.game.player_data['exp'] += 50
                self.game.player_data['kill_count'] += 1
            else:
                self.state = 'dodge'
                self.dodge_timer = 300
        
        elif option == 'ACT':
            # Simplified ACT
            self.spare_progress += 25
            self.dialogue = f"* You reason with {self.enemy_name}!"
            
            if self.spare_progress >= 100:
                self.can_spare = True
                self.dialogue += "\n* Can now be spared!"
            
            self.dialogue_timer = 120
            self.state = 'dodge'
            self.dodge_timer = 300
        
        elif option == 'MERCY':
            if self.can_spare:
                self.state = 'victory'
                self.dialogue = f"* You spared {self.enemy_name}!"
                self.game.player_data['spare_count'] += 1
                self.game.player_data['mercy_points'] += 25
            else:
                self.dialogue = f"* {self.enemy_name} doesn't want mercy yet."
                self.dialogue_timer = 120
    
    def update(self, dt):
        """Update battle state"""
        if self.dialogue_timer > 0:
            self.dialogue_timer -= 1
        
        if self.state == 'dodge':
            # Move soul
            keys = pygame.key.get_pressed()
            speed = 3
            
            if keys[pygame.K_LEFT]:
                self.soul_x = max(self.box_x + 8, self.soul_x - speed)
            if keys[pygame.K_RIGHT]:
                self.soul_x = min(self.box_x + self.box_w - 8, self.soul_x + speed)
            if keys[pygame.K_UP]:
                self.soul_y = max(self.box_y + 8, self.soul_y - speed)
            if keys[pygame.K_DOWN]:
                self.soul_y = min(self.box_y + self.box_h - 8, self.soul_y + speed)
            
            # Spawn projectiles
            if self.dodge_timer % 30 == 0:
                # Fire pattern
                for i in range(3):
                    angle = (i - 1) * 0.5
                    self.projectiles.append({
                        'x': self.box_x + self.box_w // 2,
                        'y': self.box_y,
                        'vx': math.cos(angle) * 2,
                        'vy': 2,
                        'size': 8
                    })
            
            # Update projectiles
            for proj in self.projectiles[:]:
                proj['x'] += proj['vx']
                proj['y'] += proj['vy']
                
                # Check collision with soul
                dist = math.sqrt((proj['x'] - self.soul_x)**2 + (proj['y'] - self.soul_y)**2)
                if dist < self.soul_size // 2 + proj['size'] // 2:
                    self.game.player_data['hp'] -= 1
                    self.projectiles.remove(proj)
                
                # Remove if out of bounds
                if (proj['x'] < self.box_x or proj['x'] > self.box_x + self.box_w or
                    proj['y'] < self.box_y or proj['y'] > self.box_y + self.box_h):
                    if proj in self.projectiles:
                        self.projectiles.remove(proj)
            
            # End dodge phase
            self.dodge_timer -= 1
            if self.dodge_timer <= 0:
                self.state = 'menu'
                self.projectiles = []
        
        elif self.state == 'victory':
            if self.dialogue_timer <= 0:
                return GameMode.PLATFORMER
        
        return None
    
    def draw(self, screen):
        """Draw battle scene"""
        screen.fill(BLACK)
        
        # Draw enemy
        font = pygame.font.Font(None, 36)
        text = font.render(self.enemy_name, True, WHITE)
        screen.blit(text, (SCREEN_WIDTH // 2 - 50, 100))
        
        # Enemy HP bar
        if self.enemy_hp > 0:
            hp_ratio = self.enemy_hp / self.enemy_max_hp
            pygame.draw.rect(screen, (100, 100, 100), (220, 150, 200, 20))
            pygame.draw.rect(screen, GREEN if hp_ratio > 0.5 else RED, 
                           (220, 150, int(200 * hp_ratio), 20))
        
        # Draw battle box
        pygame.draw.rect(screen, WHITE, 
                        (self.box_x, self.box_y, self.box_w, self.box_h), 3)
        
        # Draw based on state
        if self.state == 'menu':
            # Draw menu options
            font = pygame.font.Font(None, 28)
            for i, option in enumerate(self.menu_options):
                color = YELLOW if i == self.menu_index else WHITE
                text = font.render(option, True, color)
                screen.blit(text, (100 + i * 120, 420))
        
        elif self.state == 'dodge':
            # Draw soul
            pygame.draw.circle(screen, RED, (int(self.soul_x), int(self.soul_y)), 
                             self.soul_size // 2)
            
            # Draw projectiles
            for proj in self.projectiles:
                pygame.draw.circle(screen, WHITE, 
                                 (int(proj['x']), int(proj['y'])), 
                                 proj['size'] // 2)
        
        # Draw dialogue
        if self.dialogue_timer > 0 and self.dialogue:
            font = pygame.font.Font(None, 20)
            lines = self.dialogue.split('\n')
            for i, line in enumerate(lines):
                text = font.render(line, True, WHITE)
                screen.blit(text, (self.box_x + 20, self.box_y + 20 + i * 25))
        
        # Draw player stats
        font = pygame.font.Font(None, 24)
        text = font.render(f"HP: {self.game.player_data['hp']}/{self.game.player_data['max_hp']}", 
                         True, WHITE)
        screen.blit(text, (50, 420))

# === OVERWORLD MODE ===

class OverworldMode:
    """Simple overworld exploration"""
    
    def __init__(self, game):
        self.game = game
        
        # Player position
        self.player_x = 320
        self.player_y = 240
        
        # NPCs
        self.npcs = [
            {'x': 200, 'y': 200, 'name': 'Toad', 'color': RED},
            {'x': 400, 'y': 300, 'name': 'Luigi', 'color': GREEN},
            {'x': 500, 'y': 150, 'name': 'Peach', 'color': (255, 192, 203)},
        ]
        
        # Save points
        self.save_points = [
            {'x': 100, 'y': 100},
            {'x': 500, 'y': 400},
        ]
    
    def handle_event(self, event):
        """Handle overworld input"""
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_z, pygame.K_SPACE]:
                # Check for interactions
                player_rect = pygame.Rect(self.player_x - 16, self.player_y - 16, 32, 32)
                
                # Check save points
                for save in self.save_points:
                    save_rect = pygame.Rect(save['x'] - 16, save['y'] - 16, 32, 32)
                    if player_rect.colliderect(save_rect):
                        print("* Game saved!")
                        print("* You are filled with DETERMINATION.")
                        self.game.player_data['hp'] = self.game.player_data['max_hp']
                
                # Check NPCs
                for npc in self.npcs:
                    npc_rect = pygame.Rect(npc['x'] - 16, npc['y'] - 16, 32, 32)
                    if player_rect.colliderect(npc_rect):
                        print(f"* {npc['name']}: Hello, Mario!")
    
    def update(self, dt):
        """Update overworld"""
        keys = pygame.key.get_pressed()
        
        # Player movement
        speed = 3
        if keys[pygame.K_LEFT]:
            self.player_x = max(20, self.player_x - speed)
        if keys[pygame.K_RIGHT]:
            self.player_x = min(SCREEN_WIDTH - 20, self.player_x + speed)
        if keys[pygame.K_UP]:
            self.player_y = max(20, self.player_y - speed)
        if keys[pygame.K_DOWN]:
            self.player_y = min(SCREEN_HEIGHT - 20, self.player_y + speed)
        
        return None
    
    def draw(self, screen):
        """Draw overworld"""
        # Background
        screen.fill((100, 149, 237))
        
        # Draw save points
        for save in self.save_points:
            # Star shape
            points = []
            for i in range(10):
                angle = math.pi * i / 5
                if i % 2 == 0:
                    r = 16
                else:
                    r = 8
                x = save['x'] + int(r * math.cos(angle - math.pi / 2))
                y = save['y'] + int(r * math.sin(angle - math.pi / 2))
                points.append((x, y))
            pygame.draw.polygon(screen, YELLOW, points)
        
        # Draw NPCs
        for npc in self.npcs:
            pygame.draw.rect(screen, npc['color'], 
                           (npc['x'] - 16, npc['y'] - 16, 32, 32))
            
            # Name
            font = pygame.font.Font(None, 16)
            text = font.render(npc['name'], True, WHITE)
            screen.blit(text, (npc['x'] - 20, npc['y'] - 30))
        
        # Draw player (Mario)
        pygame.draw.rect(screen, MARIO_RED, 
                        (self.player_x - 12, self.player_y - 12, 24, 24))
        pygame.draw.rect(screen, RED,
                        (self.player_x - 12, self.player_y - 12, 24, 8))
        
        # Instructions
        font = pygame.font.Font(None, 20)
        text = font.render("Arrow Keys: Move | Z: Interact | F1-F3: Switch Modes", 
                         True, WHITE)
        screen.blit(text, (10, SCREEN_HEIGHT - 30))

# === MAIN ===

def main():
    """Entry point"""
    game = UndertaleMarioGame()
    game.run()

if __name__ == "__main__":
    main()

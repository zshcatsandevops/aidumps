import pygame
import numpy as np
import platform
import asyncio
import math
from typing import List, Tuple, Dict

# Initialize Pygame
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# Constants
SCREEN_WIDTH = 256
SCREEN_HEIGHT = 240
TILE_SIZE = 16
FPS = 60
GRAVITY = 0.8
PLAYER_SPEED = 3
JUMP_FORCE = -12
WORLD_MAP_WIDTH = 10
WORLD_MAP_HEIGHT = 10

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BROWN = (139, 69, 19)
YELLOW = (255, 255, 0)

class GameState:
    def __init__(self):
        self.state = "title"
        self.current_world = 1
        self.current_level = 1
        self.lives = 3
        self.coins = 0
        self.score = 0
        self.save_slots = [{"world": 1, "level": 1, "lives": 3, "coins": 0, "score": 0} for _ in range(3)]
        self.selected_slot = 0
        self.world_map_pos = (0, 0)  # Player position on world map
        self.muted = False  # Audio mute toggle
        self.map_input_delay = 0  # Prevent rapid map movement

class Player:
    def __init__(self, x: int, y: int):
        self.powerup = "small"  # small, super, fire, raccoon
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE * (2 if self.powerup != "small" else 1))
        self.vx = 0
        self.vy = 0
        self.direction = "right"
        self.is_jumping = False
        self.is_grounded = False
        self.run_timer = 0
        self.jump_cooldown = 0  # Prevent rapid jump SFX
        self.invincible = False
        self.invincible_timer = 0

    def update(self, tiles: List[pygame.Rect]):
        if self.invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.invincible = False

        # Apply gravity
        self.vy += GRAVITY
        if self.vy > 15:  # Terminal velocity
            self.vy = 15
            
        # Update Y position
        self.rect.y += int(self.vy)
        
        # Check vertical collisions
        self.is_grounded = False
        for tile in tiles:
            if self.rect.colliderect(tile):
                if self.vy > 0:  # Falling
                    self.rect.bottom = tile.top
                    self.vy = 0
                    self.is_grounded = True
                elif self.vy < 0:  # Jumping
                    self.rect.top = tile.bottom
                    self.vy = 0
        
        # Update X position
        self.rect.x += int(self.vx)
        
        # Check horizontal collisions
        for tile in tiles:
            if self.rect.colliderect(tile):
                if self.vx > 0:
                    self.rect.right = tile.left
                elif self.vx < 0:
                    self.rect.left = tile.right
                self.vx = 0

        # Keep player on screen
        self.rect.x = max(0, min(self.rect.x, SCREEN_WIDTH - self.rect.width))
        
        if self.jump_cooldown > 0:
            self.jump_cooldown -= 1

class Enemy:
    def __init__(self, x: int, y: int, enemy_type: str):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.type = enemy_type
        self.vx = -1 if enemy_type == "goomba" else -2 if enemy_type == "koopa" else 0
        self.alive = True
        self.vy = 0

    def update(self, tiles: List[pygame.Rect]):
        if not self.alive:
            return
            
        # Apply gravity
        self.vy += GRAVITY
        self.rect.y += int(self.vy)
        
        # Check vertical collisions
        for tile in tiles:
            if self.rect.colliderect(tile):
                if self.vy > 0:
                    self.rect.bottom = tile.top
                    self.vy = 0
        
        # Move horizontally
        self.rect.x += int(self.vx)
        
        # Check horizontal collisions and reverse direction
        for tile in tiles:
            if self.rect.colliderect(tile):
                if self.vx > 0:
                    self.rect.right = tile.left
                    self.vx = -abs(self.vx)
                elif self.vx < 0:
                    self.rect.left = tile.right
                    self.vx = abs(self.vx)

class PowerUp:
    def __init__(self, x: int, y: int, powerup_type: str):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.type = powerup_type  # mushroom, fireflower, leaf

class Level:
    def __init__(self, world: int, level: int):
        self.tiles = []
        self.enemies = []
        self.powerups = []
        self.world = world
        self.level = level
        self.load_level()

    def load_level(self):
        # Sample level layout (World 1-1)
        if self.world == 1 and self.level == 1:
            # Ground
            for x in range(0, 30):
                self.tiles.append(pygame.Rect(x * TILE_SIZE, SCREEN_HEIGHT - TILE_SIZE, TILE_SIZE, TILE_SIZE))
            
            # Some platforms
            for x in range(5, 8):
                self.tiles.append(pygame.Rect(x * TILE_SIZE, SCREEN_HEIGHT - 4 * TILE_SIZE, TILE_SIZE, TILE_SIZE))
            
            # Enemies
            self.enemies.append(Enemy(5 * TILE_SIZE, SCREEN_HEIGHT - 2 * TILE_SIZE, "goomba"))
            self.enemies.append(Enemy(10 * TILE_SIZE, SCREEN_HEIGHT - 2 * TILE_SIZE, "koopa"))
            
            # Power-ups
            self.powerups.append(PowerUp(8 * TILE_SIZE, SCREEN_HEIGHT - 5 * TILE_SIZE, "mushroom"))

class AudioGenerator:
    def __init__(self):
        self.sample_rate = 22050  # Lower sample rate for better compatibility
        self.channels = 2  # Stereo

    def generate_square_wave(self, freq: float, duration: float, volume: float = 0.2) -> np.ndarray:
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        wave = volume * np.sign(np.sin(2 * np.pi * freq * t))
        stereo = np.vstack((wave, wave)).T  # 2D array for stereo
        return (stereo * 32767).astype(np.int16)

    def generate_jump_sfx(self) -> pygame.mixer.Sound:
        try:
            sound = self.generate_square_wave(440, 0.1, 0.15)
            return pygame.mixer.Sound(sound)
        except:
            return None

    def generate_powerup_sfx(self) -> pygame.mixer.Sound:
        try:
            sound = self.generate_square_wave(660, 0.15, 0.15)
            return pygame.mixer.Sound(sound)
        except:
            return None

    def generate_background_music(self) -> pygame.mixer.Sound:
        try:
            # Simple melody
            notes = [220, 440, 330, 550]
            duration_per_note = 0.25
            total_samples = int(self.sample_rate * duration_per_note * len(notes))
            wave = np.zeros(total_samples)
            
            for i, freq in enumerate(notes):
                start = int(i * self.sample_rate * duration_per_note)
                end = int((i + 1) * self.sample_rate * duration_per_note)
                t = np.linspace(0, duration_per_note, end - start, False)
                wave[start:end] = 0.1 * np.sign(np.sin(2 * np.pi * freq * t))
            
            stereo = np.vstack((wave, wave)).T
            return pygame.mixer.Sound((stereo * 32767).astype(np.int16))
        except:
            return None

class WorldMap:
    def __init__(self):
        self.map = [[0 for _ in range(WORLD_MAP_WIDTH)] for _ in range(WORLD_MAP_HEIGHT)]
        self.map[0][0] = 1  # Start position
        self.map[0][1] = 1  # Path
        self.map[0][2] = 2  # Level 1-1
        # Add more connected paths
        self.map[1][0] = 1
        self.map[1][1] = 1
        self.map[1][2] = 1

class GameEngine:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Super Mario Bros. 3")
        self.clock = pygame.time.Clock()
        self.game_state = GameState()
        self.player = Player(TILE_SIZE, SCREEN_HEIGHT - 3 * TILE_SIZE)
        self.level = Level(self.game_state.current_world, self.game_state.current_level)
        self.world_map = WorldMap()
        self.audio = AudioGenerator()
        
        # Initialize audio with error handling
        self.jump_sfx = self.audio.generate_jump_sfx()
        self.powerup_sfx = self.audio.generate_powerup_sfx()
        self.bg_music = self.audio.generate_background_music()
        
        if self.bg_music and pygame.mixer.get_init():
            self.bg_music_channel = pygame.mixer.Channel(0)
            self.bg_music_channel.play(self.bg_music, loops=-1)
        else:
            self.bg_music_channel = None
            
        self.font = pygame.font.Font(None, 24)
        self.mute_toggle_cooldown = 0

    def draw_pixel_sprite(self, surface: pygame.Surface, x: int, y: int, sprite_type: str):
        if sprite_type == "mario_small":
            pygame.draw.rect(surface, RED, (x, y, TILE_SIZE, TILE_SIZE))
        elif sprite_type == "mario_super":
            pygame.draw.rect(surface, RED, (x, y, TILE_SIZE, TILE_SIZE * 2))
        elif sprite_type == "goomba":
            pygame.draw.rect(surface, BROWN, (x, y + 4, TILE_SIZE, TILE_SIZE - 4))
            pygame.draw.rect(surface, BLACK, (x + 2, y + 8, 4, 2))  # Eyes
            pygame.draw.rect(surface, BLACK, (x + 10, y + 8, 4, 2))
        elif sprite_type == "koopa":
            pygame.draw.rect(surface, GREEN, (x, y, TILE_SIZE, TILE_SIZE))
        elif sprite_type == "tile":
            pygame.draw.rect(surface, BROWN, (x, y, TILE_SIZE, TILE_SIZE))
            pygame.draw.rect(surface, BLACK, (x, y, TILE_SIZE, TILE_SIZE), 1)  # Border
        elif sprite_type == "mushroom":
            pygame.draw.rect(surface, RED, (x + 2, y + 2, TILE_SIZE - 4, TILE_SIZE // 2))
            pygame.draw.rect(surface, YELLOW, (x + 4, y + TILE_SIZE // 2, TILE_SIZE - 8, TILE_SIZE // 2 - 2))
        elif sprite_type == "map_node":
            pygame.draw.circle(surface, WHITE, (x + TILE_SIZE // 4, y + TILE_SIZE // 4), TILE_SIZE // 4)

    def handle_input(self):
        keys = pygame.key.get_pressed()
        
        # Movement
        self.player.vx = 0
        if keys[pygame.K_LEFT]:
            self.player.vx = -PLAYER_SPEED
            self.player.direction = "left"
        if keys[pygame.K_RIGHT]:
            self.player.vx = PLAYER_SPEED
            self.player.direction = "right"
            
        # Jump
        if keys[pygame.K_SPACE] and self.player.is_grounded and self.player.jump_cooldown == 0:
            self.player.vy = JUMP_FORCE
            self.player.is_jumping = True
            if not self.game_state.muted and self.jump_sfx:
                self.jump_sfx.play()
            self.player.is_grounded = False
            self.player.jump_cooldown = 10
            
        # Mute toggle with cooldown
        if keys[pygame.K_m] and self.mute_toggle_cooldown == 0:
            self.game_state.muted = not self.game_state.muted
            if self.bg_music_channel:
                if self.game_state.muted:
                    self.bg_music_channel.stop()
                else:
                    self.bg_music_channel.play(self.bg_music, loops=-1)
            self.mute_toggle_cooldown = 20
            
        if self.mute_toggle_cooldown > 0:
            self.mute_toggle_cooldown -= 1

    def handle_world_map_input(self):
        if self.game_state.map_input_delay > 0:
            self.game_state.map_input_delay -= 1
            return
            
        keys = pygame.key.get_pressed()
        x, y = self.game_state.world_map_pos
        moved = False
        
        if keys[pygame.K_UP] and y > 0:
            if self.world_map.map[y-1][x] != 0:
                self.game_state.world_map_pos = (x, y-1)
                moved = True
        elif keys[pygame.K_DOWN] and y < WORLD_MAP_HEIGHT-1:
            if self.world_map.map[y+1][x] != 0:
                self.game_state.world_map_pos = (x, y+1)
                moved = True
        elif keys[pygame.K_LEFT] and x > 0:
            if self.world_map.map[y][x-1] != 0:
                self.game_state.world_map_pos = (x-1, y)
                moved = True
        elif keys[pygame.K_RIGHT] and x < WORLD_MAP_WIDTH-1:
            if self.world_map.map[y][x+1] != 0:
                self.game_state.world_map_pos = (x+1, y)
                moved = True
                
        if moved:
            self.game_state.map_input_delay = 10

    def check_collisions(self):
        # Player-PowerUp collisions
        for powerup in self.level.powerups[:]:
            if self.player.rect.colliderect(powerup.rect):
                if powerup.type == "mushroom" and self.player.powerup == "small":
                    self.player.powerup = "super"
                    self.player.rect.height = TILE_SIZE * 2
                    self.game_state.score += 1000
                    if not self.game_state.muted and self.powerup_sfx:
                        self.powerup_sfx.play()
                self.level.powerups.remove(powerup)
                
        # Player-Enemy collisions
        for enemy in self.level.enemies[:]:
            if self.player.rect.colliderect(enemy.rect) and enemy.alive:
                # Check if player is stomping
                if self.player.vy > 0 and self.player.rect.bottom <= enemy.rect.centery:
                    enemy.alive = False
                    self.game_state.score += 100
                    self.player.vy = JUMP_FORCE / 2  # Bounce
                elif not self.player.invincible:
                    # Take damage
                    if self.player.powerup == "super":
                        self.player.powerup = "small"
                        self.player.rect.height = TILE_SIZE
                        self.player.invincible = True
                        self.player.invincible_timer = 120
                    else:
                        self.game_state.lives -= 1
                        if self.game_state.lives <= 0:
                            self.game_state.state = "title"
                            self.reset_level()
                        else:
                            self.player.invincible = True
                            self.player.invincible_timer = 120

    def reset_level(self):
        self.player = Player(TILE_SIZE, SCREEN_HEIGHT - 3 * TILE_SIZE)
        self.level = Level(self.game_state.current_world, self.game_state.current_level)

    def draw_ui(self):
        score_text = self.font.render(f"Score: {self.game_state.score}", True, WHITE)
        lives_text = self.font.render(f"Lives: {self.game_state.lives}", True, WHITE)
        coins_text = self.font.render(f"Coins: {self.game_state.coins}", True, WHITE)
        world_text = self.font.render(f"World: {self.game_state.current_world}-{self.game_state.current_level}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        self.screen.blit(lives_text, (10, 30))
        self.screen.blit(coins_text, (10, 50))
        self.screen.blit(world_text, (SCREEN_WIDTH - 80, 10))
        
        if self.game_state.muted:
            mute_text = self.font.render("MUTED", True, RED)
            self.screen.blit(mute_text, (SCREEN_WIDTH - 60, 30))

    def save_game(self):
        self.game_state.save_slots[self.game_state.selected_slot] = {
            "world": self.game_state.current_world,
            "level": self.game_state.current_level,
            "lives": self.game_state.lives,
            "coins": self.game_state.coins,
            "score": self.game_state.score
        }

    def load_game(self):
        slot = self.game_state.save_slots[self.game_state.selected_slot]
        self.game_state.current_world = slot["world"]
        self.game_state.current_level = slot["level"]
        self.game_state.lives = slot["lives"]
        self.game_state.coins = slot["coins"]
        self.game_state.score = slot["score"]
        self.reset_level()

    def draw_world_map(self):
        # Draw map nodes
        for y in range(WORLD_MAP_HEIGHT):
            for x in range(WORLD_MAP_WIDTH):
                if self.world_map.map[y][x] != 0:
                    color = YELLOW if self.world_map.map[y][x] == 2 else WHITE
                    pygame.draw.circle(self.screen, color, 
                                     (x * TILE_SIZE * 2 + TILE_SIZE, y * TILE_SIZE * 2 + TILE_SIZE), 
                                     TILE_SIZE // 2)
                    
        # Draw player on map
        px, py = self.game_state.world_map_pos
        self.draw_pixel_sprite(self.screen, px * TILE_SIZE * 2, py * TILE_SIZE * 2, f"mario_{self.player.powerup}")

    async def main_loop(self):
        running = True
        input_cooldown = 0
        
        while running:
            if input_cooldown > 0:
                input_cooldown -= 1

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and input_cooldown == 0:
                    if self.game_state.state == "title" and event.key == pygame.K_RETURN:
                        self.game_state.state = "file_select"
                        input_cooldown = 10
                    elif self.game_state.state == "file_select":
                        if event.key == pygame.K_UP:
                            self.game_state.selected_slot = (self.game_state.selected_slot - 1) % 3
                        elif event.key == pygame.K_DOWN:
                            self.game_state.selected_slot = (self.game_state.selected_slot + 1) % 3
                        elif event.key == pygame.K_RETURN:
                            self.load_game()
                            self.game_state.state = "world_map"
                            input_cooldown = 10
                    elif self.game_state.state == "world_map" and event.key == pygame.K_RETURN:
                        x, y = self.game_state.world_map_pos
                        if self.world_map.map[y][x] == 2:  # Level node
                            self.game_state.state = "level"
                            input_cooldown = 10

            self.screen.fill(BLACK)

            if self.game_state.state == "title":
                title_text = self.font.render("Super Mario Bros. 3", True, WHITE)
                start_text = self.font.render("Press ENTER to Start", True, WHITE)
                self.screen.blit(title_text, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 - 20))
                self.screen.blit(start_text, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 + 20))
            elif self.game_state.state == "file_select":
                title = self.font.render("Select Save Slot", True, WHITE)
                self.screen.blit(title, (SCREEN_WIDTH // 2 - 60, 20))
                
                for i, slot in enumerate(self.game_state.save_slots):
                    slot_text = self.font.render(f"Slot {i+1}: World {slot['world']}-{slot['level']} Lives: {slot['lives']}", True, WHITE)
                    self.screen.blit(slot_text, (50, 60 + i * 40))
                    
                cursor_text = self.font.render(">", True, WHITE)
                self.screen.blit(cursor_text, (30, 60 + self.game_state.selected_slot * 40))
            elif self.game_state.state == "world_map":
                self.handle_world_map_input()
                self.draw_world_map()
                
                # Show instructions
                inst_text = self.font.render("Arrow keys to move, ENTER to enter level", True, WHITE)
                self.screen.blit(inst_text, (10, SCREEN_HEIGHT - 30))
            elif self.game_state.state == "level":
                self.handle_input()
                self.player.update(self.level.tiles)
                
                for enemy in self.level.enemies:
                    enemy.update(self.level.tiles)
                    
                self.check_collisions()

                # Draw tiles
                for tile in self.level.tiles:
                    self.draw_pixel_sprite(self.screen, tile.x, tile.y, "tile")
                    
                # Draw power-ups
                for powerup in self.level.powerups:
                    self.draw_pixel_sprite(self.screen, powerup.rect.x, powerup.rect.y, powerup.type)
                    
                # Draw enemies
                for enemy in self.level.enemies:
                    if enemy.alive:
                        self.draw_pixel_sprite(self.screen, enemy.rect.x, enemy.rect.y, enemy.type)
                        
                # Draw player (with flashing when invincible)
                if not self.player.invincible or (pygame.time.get_ticks() // 100) % 2:
                    self.draw_pixel_sprite(self.screen, self.player.rect.x, self.player.rect.y, f"mario_{self.player.powerup}")
                    
                self.draw_ui()

            pygame.display.flip()
            self.clock.tick(FPS)
            
            if platform.system() == "Emscripten":
                await asyncio.sleep(0)
            else:
                await asyncio.sleep(1.0 / FPS)

        pygame.quit()

# Run the game
if platform.system() == "Emscripten":
    asyncio.ensure_future(GameEngine().main_loop())
else:
    if __name__ == "__main__":
        asyncio.run(GameEngine().main_loop())

import pygame
import random
import asyncio
import platform
from enum import Enum, auto

# Constants
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400
FPS = 60
TILE_SIZE = 20

# Enums for game states and types
class GameMode(Enum):
    TITLE_SCREEN = auto()
    WORLD_MAP = auto()
    LEVEL = auto()
    GAME_OVER = auto()

class PowerUp(Enum):
    NONE = auto()
    MUSHROOM = auto()
    FIRE_FLOWER = auto()

class EnemyType(Enum):
    GOOMBA = auto()
    KOOPA = auto()

class TileType(Enum):
    EMPTY = auto()
    GROUND = auto()
    BRICK = auto()
    QUESTION_BLOCK = auto()
    USED_BLOCK = auto()
    PIPE_TOP_LEFT = auto()
    PIPE_TOP_RIGHT = auto()
    PIPE_BODY_LEFT = auto()
    PIPE_BODY_RIGHT = auto()

# Enemy class
class Enemy:
    def __init__(self, x, y, enemy_type):
        self.x = x
        self.y = y
        self.type = enemy_type
        self.width = 30
        self.height = 30
        self.alive = True
        self.direction = random.choice([-1, 1])

    def move(self):
        speed = 2 if self.type == EnemyType.GOOMBA else 1.5
        self.x += self.direction * speed
        if self.x < 50 or self.x > 550:
            self.direction *= -1

# Item (power-up) class
class Item:
    def __init__(self, x, y, powerup_type):
        self.x = x
        self.y = y
        self.type = powerup_type
        self.width = 20
        self.height = 20
        self.collected = False

# Main game class
class SMB3Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Super Mario Bros. 3")
        self.clock = pygame.time.Clock()

        # Game state
        self.mode = GameMode.TITLE_SCREEN
        self.player_x = 300
        self.player_y = 300
        self.player_vx = 0
        self.player_vy = 0
        self.max_speed = 5
        self.acceleration = 0.5
        self.deceleration = 0.3
        self.on_ground = True
        self.scroll_x = 0
        self.level_length = 3000
        self.coins = 0
        self.lives = 3
        self.world = 1
        self.level = 1
        self.powerup = PowerUp.NONE
        self.invincible = False
        self.invincible_timer = 0

        # Level objects
        self.enemies = []
        self.items = []
        self.flag_x = 2800

        # Tile map
        self.TILE_SIZE = TILE_SIZE
        self.level_data = []
        self.level_height = SCREEN_HEIGHT // self.TILE_SIZE
        self.level_width = self.level_length // self.TILE_SIZE

        # Colors
        self.colors = {
            'sky': (135, 206, 235),
            'ground': (139, 69, 19),
            'brick': (160, 82, 45),
            'coin': (255, 215, 0),
            'pipe': (0, 128, 0),
            'mario': (255, 0, 0),
            'mario_big': (255, 165, 0),
            'fire': (255, 255, 255),
            'goomba': (165, 42, 42),
            'koopa': (0, 128, 0),
            'mushroom': (255, 0, 0),
            'flower': (255, 165, 0),
            'flag': (255, 255, 255),
            'black': (0, 0, 0),
            'white': (255, 255, 255)
        }

        # Fonts
        self.big_font = pygame.font.SysFont('Helvetica', 36, bold=True)
        self.small_font = pygame.font.SysFont('Helvetica', 20)

    def start_level(self, world, level):
        self.world = world
        self.level = level
        self.player_x = 100
        self.player_y = 300
        self.player_vx = 0
        self.player_vy = 0
        self.scroll_x = 0
        self.on_ground = True
        self.powerup = PowerUp.NONE
        self.invincible = False
        self.invincible_timer = 0

        # Generate level data
        self.level_data = self.generate_level_data(world, level)

        # Enemies and items (customize per level)
        self.enemies = [
            Enemy(400, 350, EnemyType.GOOMBA),
            Enemy(700, 350, EnemyType.KOOPA),
        ]
        self.items = [
            Item(500, 250, PowerUp.MUSHROOM),
        ]
        self.flag_x = 2800

    def generate_level_data(self, world, level):
        level_data = [[TileType.EMPTY] * self.level_width for _ in range(self.level_height)]
        # Ground
        for x in range(self.level_width):
            level_data[15][x] = TileType.GROUND
        # Platforms
        if world == 1 and level == 1:
            for x in range(10, 16):
                level_data[10][x] = TileType.BRICK
        elif world == 1 and level == 2:
            for x in range(20, 26):
                level_data[8][x] = TileType.BRICK
        # Add more variations
        return level_data

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if self.mode == GameMode.GAME_OVER and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.lives = 3
                    self.coins = 0
                    self.level = 1
                    self.world = 1
                    self.mode = GameMode.TITLE_SCREEN
                elif self.mode == GameMode.TITLE_SCREEN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.mode = GameMode.WORLD_MAP
                elif self.mode == GameMode.WORLD_MAP and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.mode = GameMode.LEVEL
                    self.start_level(self.world, self.level)

    def handle_input(self):
        keys = pygame.key.get_pressed()
        if self.mode == GameMode.WORLD_MAP:
            if keys[pygame.K_RIGHT]: self.player_x = min(self.player_x + 3, 550)
            if keys[pygame.K_LEFT]: self.player_x = max(self.player_x - 3, 50)
            if keys[pygame.K_UP]: self.player_y = max(self.player_y - 3, 50)
            if keys[pygame.K_DOWN]: self.player_y = min(self.player_y + 3, 350)
        elif self.mode == GameMode.LEVEL:
            if keys[pygame.K_RIGHT]:
                self.player_vx = min(self.player_vx + self.acceleration, self.max_speed)
            elif keys[pygame.K_LEFT]:
                self.player_vx = max(self.player_vx - self.acceleration, -self.max_speed)
            else:
                if self.player_vx > 0:
                    self.player_vx = max(self.player_vx - self.deceleration, 0)
                elif self.player_vx < 0:
                    self.player_vx = min(self.player_vx + self.deceleration, 0)
            if keys[pygame.K_UP] and self.on_ground:
                self.player_vy = -10
                self.on_ground = False

    def update(self, dt):
        if self.mode == GameMode.LEVEL:
            # Move player horizontally
            self.player_x += self.player_vx
            # Handle scrolling
            if self.player_x > 300 and self.scroll_x < self.level_length - SCREEN_WIDTH:
                self.scroll_x += self.player_vx
                self.player_x = 300
            elif self.player_x < 100 and self.scroll_x > 0:
                self.scroll_x += self.player_vx
                self.player_x = 100

            # Apply gravity
            if not self.on_ground:
                self.player_vy += 0.5
                self.player_y += self.player_vy

            # Collision detection
            # Simplified: check if player is on ground
            player_tile_x = int((self.player_x + self.scroll_x) // self.TILE_SIZE)
            player_tile_y = int(self.player_y // self.TILE_SIZE)
            if player_tile_y + 1 < self.level_height and self.level_data[player_tile_y + 1][player_tile_x] in {TileType.GROUND, TileType.BRICK}:
                self.on_ground = True
                self.player_y = player_tile_y * self.TILE_SIZE
                self.player_vy = 0
            else:
                self.on_ground = False

            # Move enemies
            for enemy in self.enemies:
                if enemy.alive:
                    enemy.move()

            # Invincibility
            if self.invincible:
                self.invincible_timer -= dt
                if self.invincible_timer <= 0:
                    self.invincible = False

            # Enemy collisions
            for enemy in self.enemies:
                if enemy.alive and self.collision(
                    self.player_x, self.player_y, 30, 45,
                    enemy.x - self.scroll_x, enemy.y, enemy.width, enemy.height):
                    if self.invincible:
                        enemy.alive = False
                    elif self.player_vy > 0 and self.player_y < enemy.y:
                        enemy.alive = False
                        self.player_vy = -8
                    else:
                        if self.powerup != PowerUp.NONE:
                            self.powerup = PowerUp.NONE
                            self.invincible = True
                            self.invincible_timer = 2
                        else:
                            self.lives -= 1
                            if self.lives <= 0:
                                self.mode = GameMode.GAME_OVER
                            else:
                                self.start_level(self.world, self.level)
                            return

            # Item collisions
            for item in self.items:
                if not item.collected and self.collision(
                    self.player_x, self.player_y, 30, 45,
                    item.x - self.scroll_x, item.y, item.width, item.height):
                    item.collected = True
                    if item.type == PowerUp.MUSHROOM:
                        self.powerup = PowerUp.MUSHROOM
                    elif item.type == PowerUp.FIRE_FLOWER:
                        self.powerup = PowerUp.FIRE_FLOWER

            # Coin collection simulation
            for i in range(5):
                coin_x = 120 + i * 200 - self.scroll_x % 200
                if 0 < coin_x < SCREEN_WIDTH and abs(self.player_x - coin_x) < 20 and abs(self.player_y - 220) < 20:
                    self.coins += 1

            # Level end
            if self.player_x + self.scroll_x > self.flag_x:
                if self.level < 4:
                    self.level += 1
                else:
                    self.world += 1
                    self.level = 1
                self.mode = GameMode.WORLD_MAP

    def collision(self, x1, y1, w1, h1, x2, y2, w2, h2):
        return (x1 < x2 + w2 and x1 + w1 > x2 and
                y1 < y2 + h2 and y1 + h1 > y2)

    def render(self):
        # Clear screen
        if self.mode in (GameMode.TITLE_SCREEN, GameMode.GAME_OVER):
            self.screen.fill(self.colors['black'])
        else:
            self.screen.fill(self.colors['sky'])

        if self.mode == GameMode.TITLE_SCREEN:
            self.render_title_screen()
        elif self.mode == GameMode.WORLD_MAP:
            self.render_world_map()
        elif self.mode == GameMode.LEVEL:
            self.render_level()
        elif self.mode == GameMode.GAME_OVER:
            self.render_game_over()

        self.render_hud()

    def render_title_screen(self):
        title_surf = self.big_font.render("SUPER MARIO BROS. 3", True, self.colors['white'])
        prompt_surf = self.small_font.render("Press START", True, self.colors['white'])
        self.screen.blit(title_surf, (SCREEN_WIDTH//2 - title_surf.get_width()//2, 100))
        self.screen.blit(prompt_surf, (SCREEN_WIDTH//2 - prompt_surf.get_width()//2, 200))
        # Mario placeholder
        self.draw_mario(300, 250, 1)

    def render_world_map(self):
        self.screen.fill((173, 216, 230))  # lightblue
        for i in range(1, 9):
            x = 50 + i * 60
            y = 100 + (i % 3) * 100
            pygame.draw.circle(self.screen, (0, 255, 0), (x, y), 20)
            text_surf = self.small_font.render(str(i), True, self.colors['black'])
            self.screen.blit(text_surf, (x - text_surf.get_width()//2, y - text_surf.get_height()//2))
        self.draw_mario(self.player_x, self.player_y, 1)

    def render_level(self):
        # Render tiles
        start_x = self.scroll_x // self.TILE_SIZE
        end_x = start_x + (SCREEN_WIDTH // self.TILE_SIZE) + 1
        for y in range(self.level_height):
            for x in range(start_x, min(end_x, self.level_width)):
                tile = self.level_data[y][x]
                if tile != TileType.EMPTY:
                    tile_x = (x * self.TILE_SIZE) - self.scroll_x
                    tile_y = y * self.TILE_SIZE
                    if tile == TileType.GROUND:
                        pygame.draw.rect(self.screen, self.colors['ground'], (tile_x, tile_y, self.TILE_SIZE, self.TILE_SIZE))
                    elif tile == TileType.BRICK:
                        pygame.draw.rect(self.screen, self.colors['brick'], (tile_x, tile_y, self.TILE_SIZE, self.TILE_SIZE))
                    # Add more tile types

        # Render enemies
        for enemy in self.enemies:
            if enemy.alive:
                ex = enemy.x - self.scroll_x
                if 0 < ex < SCREEN_WIDTH:
                    if enemy.type == EnemyType.GOOMBA:
                        self.draw_goomba(ex, enemy.y)
                    elif enemy.type == EnemyType.KOOPA:
                        self.draw_koopa(ex, enemy.y)

        # Render items
        for item in self.items:
            if not item.collected:
                ix = item.x - self.scroll_x
                if 0 < ix < SCREEN_WIDTH:
                    if item.type == PowerUp.MUSHROOM:
                        self.draw_mushroom(ix, item.y)
                    elif item.type == PowerUp.FIRE_FLOWER:
                        self.draw_fire_flower(ix, item.y)

        # Render player
        self.draw_mario(self.player_x, self.player_y, 1 if self.powerup == PowerUp.NONE else 1.5)

    def render_game_over(self):
        over_surf = self.big_font.render("GAME OVER", True, self.colors['white'])
        prompt_surf = self.small_font.render("Press START to continue", True, self.colors['white'])
        self.screen.blit(over_surf, (SCREEN_WIDTH//2 - over_surf.get_width()//2, 200))
        self.screen.blit(prompt_surf, (SCREEN_WIDTH//2 - prompt_surf.get_width()//2, 250))

    def render_hud(self):
        pygame.draw.rect(self.screen, self.colors['black'], (0, 0, SCREEN_WIDTH, 30))
        coin_surf = self.small_font.render(f"COINS: {self.coins}", True, self.colors['white'])
        world_surf = self.small_font.render(f"WORLD {self.world}-{self.level}", True, self.colors['white'])
        lives_surf = self.small_font.render(f"LIVES: {self.lives}", True, self.colors['white'])
        self.screen.blit(coin_surf, (10, 5))
        self.screen.blit(world_surf, (SCREEN_WIDTH//2 - world_surf.get_width()//2, 5))
        self.screen.blit(lives_surf, (SCREEN_WIDTH - lives_surf.get_width() - 10, 5))
        if self.powerup == PowerUp.MUSHROOM:
            pu_surf = self.small_font.render("MUSHROOM", True, self.colors['mario_big'])
            self.screen.blit(pu_surf, (110, 5))
        elif self.powerup == PowerUp.FIRE_FLOWER:
            pu_surf = self.small_font.render("FIRE FLOWER", True, self.colors['fire'])
            self.screen.blit(pu_surf, (110, 5))

    # Asset drawing methods
    def draw_mario(self, x, y, size):
        # Simple Mario drawing
        # Head
        pygame.draw.circle(self.screen, self.colors['mario'], (int(x), int(y - 20 * size)), int(10 * size))
        # Body
        pygame.draw.rect(self.screen, self.colors['mario'], (int(x - 10 * size), int(y - 10 * size), int(20 * size), int(20 * size)))
        # Arms
        pygame.draw.line(self.screen, self.colors['mario'], (int(x - 15 * size), int(y - 5 * size)), (int(x - 10 * size), int(y - 5 * size)), int(5 * size))
        pygame.draw.line(self.screen, self.colors['mario'], (int(x + 10 * size), int(y - 5 * size)), (int(x + 15 * size), int(y - 5 * size)), int(5 * size))
        # Legs
        pygame.draw.line(self.screen, self.colors['mario'], (int(x - 5 * size), int(y + 10 * size)), (int(x - 5 * size), int(y + 15 * size)), int(5 * size))
        pygame.draw.line(self.screen, self.colors['mario'], (int(x + 5 * size), int(y + 10 * size)), (int(x + 5 * size), int(y + 15 * size)), int(5 * size))

    def draw_goomba(self, x, y):
        # Simple Goomba drawing
        pygame.draw.ellipse(self.screen, self.colors['goomba'], (int(x - 15), int(y - 15), 30, 30))
        pygame.draw.circle(self.screen, self.colors['white'], (int(x - 5), int(y - 5)), 5)
        pygame.draw.circle(self.screen, self.colors['white'], (int(x + 5), int(y - 5)), 5)
        pygame.draw.circle(self.screen, self.colors['black'], (int(x - 5), int(y - 5)), 2)
        pygame.draw.circle(self.screen, self.colors['black'], (int(x + 5), int(y - 5)), 2)

    def draw_koopa(self, x, y):
        # Simple Koopa drawing
        pygame.draw.rect(self.screen, self.colors['koopa'], (int(x - 15), int(y - 30), 30, 30))
        pygame.draw.circle(self.screen, self.colors['koopa'], (int(x), int(y - 35)), 10)

    def draw_mushroom(self, x, y):
        # Simple mushroom drawing
        pygame.draw.rect(self.screen, self.colors['white'], (int(x - 5), int(y - 10), 10, 20))
        pygame.draw.ellipse(self.screen, self.colors['mushroom'], (int(x - 15), int(y - 20), 30, 20))

    def draw_fire_flower(self, x, y):
        # Simple fire flower drawing
        pygame.draw.circle(self.screen, self.colors['flower'], (int(x), int(y)), 10)
        for angle in range(0, 360, 90):
            rad = angle * (3.14159 / 180)
            pygame.draw.line(self.screen, self.colors['flower'], (int(x), int(y)), (int(x + 15 * math.cos(rad)), int(y + 15 * math.sin(rad))), 5)

    async def run(self):
        game = SMB3Game()
        while True:
            game.handle_events()
            game.handle_input()
            game.update(1.0 / FPS)
            game.render()
            pygame.display.flip()
            await asyncio.sleep(1.0 / FPS)

async def main():
    game = SMB3Game()
    await game.run()

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        import math
        asyncio.run(main())

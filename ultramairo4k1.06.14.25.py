from __future__ import annotations

import sys
from typing import List, Tuple

import pygame

# ---------------------------------------------------------------------------
# Config & constants
# ---------------------------------------------------------------------------
WIDTH, HEIGHT = 800, 450      # viewport size
FPS = 60                      # frames per second
GRAVITY = 0.45                # pixels per frame²
PLAYER_SPEED = 4.5            # horizontal acceleration
PLAYER_JUMP = 12              # initial jump impulse
CAMERA_LAG = 0.15             # lower = snappier camera

BG_COLOR = (135, 206, 250)      # sky blue
PLATFORM_COLOR = (139, 69, 19)   # saddle brown
PLAYER_COLOR = (220, 20, 60)     # crimson
ENEMY_COLOR = (60, 179, 113)     # medium sea-green
FLAG_COLOR = (255, 223, 0)       # gold
BOSS_COLOR = (128, 0, 128)       # purple
TEXT_COLOR = (33, 33, 33)

# Logical (virtual) world width per level
LEVEL_WIDTH = 2400            # wide enough for side-scrolling
GROUND_Y = HEIGHT - 40
TOTAL_LEVELS = 32

pygame.init()
FONT = pygame.font.SysFont("consolas", 20)

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def draw_text(surface: pygame.Surface, text: str, pos: Tuple[int, int]) -> None:
    surface.blit(FONT.render(text, True, TEXT_COLOR), pos)

# ---------------------------------------------------------------------------
# Sprite classes
# ---------------------------------------------------------------------------

class Platform(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, w: int, h: int):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(PLATFORM_COLOR)
        self.rect = self.image.get_rect(topleft=(x, y))


class Enemy(pygame.sprite.Sprite):
    """Simple back-and-forth patroller that stays on its platform."""

    def __init__(self, x: int, y: int, platform: Platform, speed: int = 2):
        super().__init__()
        size = 28
        self.image = pygame.Surface((size, size))
        self.image.fill(ENEMY_COLOR)
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.platform = platform
        self.vx = speed

    def update(self) -> None:
        self.rect.x += self.vx
        if self.rect.right > self.platform.rect.right or self.rect.left < self.platform.rect.left:
            self.vx *= -1
            self.rect.x += self.vx


class Flag(pygame.sprite.Sprite):
    """Flag that triggers next level when reached."""
    def __init__(self, x: int, y: int):
        super().__init__()
        self.image = pygame.Surface((20, 40))
        self.image.fill(FLAG_COLOR)
        self.rect = self.image.get_rect(midbottom=(x, y))


class Boss(pygame.sprite.Sprite):
    """Final boss at castle level."""
    def __init__(self, x: int, y: int, health: int = 5):
        super().__init__()
        size = 60
        self.image = pygame.Surface((size, size))
        self.image.fill(BOSS_COLOR)
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.vx = 3
        self.health = health

    def update(self) -> None:
        # Patrol horizontally at top of play area
        self.rect.x += self.vx
        if self.rect.left < 0 or self.rect.right > LEVEL_WIDTH:
            self.vx *= -1

    def hit(self):
        self.health -= 1
        if self.health <= 0:
            self.kill()


class Player(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int):
        super().__init__()
        self.image = pygame.Surface((32, 45))
        self.image.fill(PLAYER_COLOR)
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.pos = pygame.Vector2(self.rect.topleft)
        self.vel = pygame.Vector2(0, 0)
        self.on_ground = False
        self.score = 0

    def handle_input(self, keys: pygame.key.ScancodeWrapper) -> None:
        if keys[pygame.K_LEFT]:
            self.vel.x = max(self.vel.x - PLAYER_SPEED * 0.4, -PLAYER_SPEED)
        elif keys[pygame.K_RIGHT]:
            self.vel.x = min(self.vel.x + PLAYER_SPEED * 0.4, PLAYER_SPEED)
        else:
            self.vel.x *= 0.8
            if abs(self.vel.x) < 0.1:
                self.vel.x = 0
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vel.y = -PLAYER_JUMP
            self.on_ground = False

    def apply_gravity(self) -> None:
        self.vel.y += GRAVITY
        if self.vel.y > 12:
            self.vel.y = 12

    def update(self, platforms: pygame.sprite.Group, enemies: pygame.sprite.Group, flags: pygame.sprite.Group, bosses: pygame.sprite.Group) -> None:
        self.apply_gravity()
        # Horizontal movement
        self.pos.x += self.vel.x
        self.rect.x = round(self.pos.x)
        self._horizontal_collisions(platforms)
        # Vertical movement
        self.pos.y += self.vel.y
        self.rect.y = round(self.pos.y)
        self._vertical_collisions(platforms)
        # Enemy interactions
        self._handle_enemies(enemies)
        # Flag interaction
        if pygame.sprite.spritecollideany(self, flags):
            raise LevelComplete
        # Boss interaction
        for boss in pygame.sprite.spritecollide(self, bosses, False):
            if self.vel.y > 0 and self.rect.bottom - boss.rect.top < 10:
                boss.hit()
                self.vel.y = -PLAYER_JUMP * 0.6
                if not boss.alive():
                    raise Victory
            else:
                raise GameOver

    def _horizontal_collisions(self, platforms: pygame.sprite.Group) -> None:
        for plat in pygame.sprite.spritecollide(self, platforms, False):
            if self.vel.x > 0:
                self.rect.right = plat.rect.left
            elif self.vel.x < 0:
                self.rect.left = plat.rect.right
            self.pos.x = self.rect.x
            self.vel.x = 0

    def _vertical_collisions(self, platforms: pygame.sprite.Group) -> None:
        self.on_ground = False
        for plat in pygame.sprite.spritecollide(self, platforms, False):
            if self.vel.y > 0:
                self.rect.bottom = plat.rect.top
                self.pos.y = self.rect.y
                self.vel.y = 0
                self.on_ground = True
            elif self.vel.y < 0:
                self.rect.top = plat.rect.bottom
                self.pos.y = self.rect.y
                self.vel.y = 0

    def _handle_enemies(self, enemies: pygame.sprite.Group) -> None:
        for enemy in pygame.sprite.spritecollide(self, enemies, False):
            if self.vel.y > 0 and self.rect.bottom - enemy.rect.top < 10:
                enemy.kill()
                self.vel.y = -PLAYER_JUMP * 0.6
                self.score += 100
            else:
                raise GameOver

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class GameOver(Exception): pass
class LevelComplete(Exception): pass
class Victory(Exception): pass

# ---------------------------------------------------------------------------
# Level data
# ---------------------------------------------------------------------------

# Base platform layout for levels
BASE_LAYOUT: List[Tuple[int,int,int,int]] = [
    (200, 340, 200, 14),
    (500, 275, 140, 14),
    (750, 210, 180, 14),
    (1100, 260, 200, 14),
    (1400, 320, 160, 14),
    (1750, 280, 220, 14),
]

# Generate 32 levels with identical layout (customize as needed)
LEVEL_LAYOUTS = [BASE_LAYOUT[:] for _ in range(TOTAL_LEVELS)]

# ---------------------------------------------------------------------------
# Build level contents
# ---------------------------------------------------------------------------
def build_level(level_index: int) -> Tuple[pygame.sprite.Group, pygame.sprite.Group, pygame.sprite.Group, pygame.sprite.Group]:
    platforms = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    flags = pygame.sprite.Group()
    bosses = pygame.sprite.Group()

    ground = Platform(0, GROUND_Y, LEVEL_WIDTH, HEIGHT - GROUND_Y)
    platforms.add(ground)

    layout = LEVEL_LAYOUTS[level_index]
    for x, y, w, h in layout:
        plat = Platform(x, y, w, h)
        platforms.add(plat)
        if w > 100 and level_index < TOTAL_LEVELS-1:
            enemy = Enemy(x + w//2, y, plat)
            enemies.add(enemy)

    # Add end-of-level flag
    flag_x = LEVEL_WIDTH - 100
    flag = Flag(flag_x, GROUND_Y)
    flags.add(flag)

    # If final level, add boss instead of regular enemies
    if level_index == TOTAL_LEVELS - 1:
        boss = Boss(LEVEL_WIDTH//2, GROUND_Y)
        bosses.add(boss)

    return platforms, enemies, flags, bosses

# ---------------------------------------------------------------------------
# Screens
# ---------------------------------------------------------------------------

def _overlay_text(screen: pygame.Surface, msg: str):
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0,0,0,200))
    screen.blit(overlay, (0,0))
    draw_text(screen, msg, (WIDTH//2 - len(msg)*5, HEIGHT//2))
    pygame.display.flip()

# ---------------------------------------------------------------------------
# Main game loop
# ---------------------------------------------------------------------------

def run() -> None:
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Super Mario Bros – Pure-Python Edition")
    clock = pygame.time.Clock()
    level = 0

    while True:
        try:
            platforms, enemies, flags, bosses = build_level(level)
            player = Player(100, GROUND_Y)
            cam_x = 0.0

            while True:
                clock.tick(FPS)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or (event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE):
                        pygame.quit(); sys.exit()
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                        raise GameOver

                keys = pygame.key.get_pressed()
                player.handle_input(keys)

                enemies.update()
                bosses.update()
                player.update(platforms, enemies, flags, bosses)

                cam_x += (player.rect.centerx - cam_x - WIDTH//2) * CAMERA_LAG
                cam_x = max(0, min(cam_x, LEVEL_WIDTH - WIDTH))

                screen.fill(BG_COLOR)
                for sprite in platforms: screen.blit(sprite.image, (sprite.rect.x-cam_x, sprite.rect.y))
                for sprite in enemies:   screen.blit(sprite.image, (sprite.rect.x-cam_x, sprite.rect.y))
                for sprite in flags:     screen.blit(sprite.image, (sprite.rect.x-cam_x, sprite.rect.y))
                for sprite in bosses:    screen.blit(sprite.image, (sprite.rect.x-cam_x, sprite.rect.y))
                screen.blit(player.image, (player.rect.x-cam_x, player.rect.y))
                draw_text(screen, f"Score: {player.score}", (10, 10))
                draw_text(screen, f"Level: {level+1}/{TOTAL_LEVELS}", (WIDTH-140, 10))
                pygame.display.flip()

                if player.rect.top > HEIGHT:
                    raise GameOver

        except GameOver:
            _overlay_text(screen, "Game Over – press R to restart")
            # restart same level
            continue
        except LevelComplete:
            level = min(level+1, TOTAL_LEVELS-1)
            continue
        except Victory:
            _overlay_text(screen, "You Defeated the Boss! You Win!")
            pygame.time.delay(3000)
            pygame.quit(); sys.exit()

if __name__ == "__main__":
    run()

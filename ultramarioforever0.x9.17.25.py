"""Samsoft Mario Forever: A Really Long Journey

An extended fan-style platformer inspired by Super Mario World aesthetics
and the clean information layout of the New Super Mario Bros. HUD.
Run this file directly to begin the adventure.
"""
import math
import random
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import pygame


# Screen and gameplay constants
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 600
GRAVITY = 0.6
PLAYER_SPEED = 4.4
PLAYER_JUMP = 12.5
MAX_FALL_SPEED = 15
FPS = 60


Color = Tuple[int, int, int]


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def lighten(color: Color, amount: float) -> Color:
    return tuple(int(clamp(c + amount, 0, 255)) for c in color)


def darken(color: Color, amount: float) -> Color:
    return tuple(int(clamp(c - amount, 0, 255)) for c in color)


def render_outlined_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    position: Tuple[int, int],
    text_color: Color,
    outline_color: Color,
    outline_size: int = 2,
) -> None:
    base = font.render(text, True, text_color)
    outline = font.render(text, True, outline_color)
    x, y = position
    for dx in range(-outline_size, outline_size + 1):
        for dy in range(-outline_size, outline_size + 1):
            if dx == 0 and dy == 0:
                continue
            surface.blit(outline, (x + dx, y + dy))
    surface.blit(base, position)


@dataclass
class Theme:
    name: str
    background: Color
    ground: Color
    accent: Color
    distant: Color


THEMES: Sequence[Theme] = (
    Theme("Grassland", (126, 196, 255), (124, 188, 92), (242, 212, 88), (112, 168, 84)),
    Theme("Underground", (70, 96, 134), (138, 122, 160), (196, 184, 220), (86, 72, 120)),
    Theme("Desert", (250, 218, 152), (214, 174, 118), (255, 234, 188), (180, 142, 88)),
    Theme("Snow", (178, 218, 255), (206, 238, 255), (246, 254, 255), (148, 198, 230)),
    Theme("Jungle", (120, 190, 148), (88, 150, 106), (212, 236, 180), (76, 130, 92)),
    Theme("Volcano", (176, 96, 70), (132, 70, 52), (242, 172, 112), (104, 54, 42)),
    Theme("Sky", (164, 220, 255), (206, 216, 234), (255, 255, 255), (150, 198, 228)),
    Theme("Star", (56, 42, 88), (102, 84, 140), (216, 194, 255), (70, 56, 102)),
)

CASTLE_THEME = Theme("Castle", (54, 62, 90), (134, 134, 168), (214, 136, 98), (92, 96, 132))


class Platform:
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        color: Color,
        *,
        style: str = "block",
    ) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.style = style

    def draw(self, surface: pygame.Surface, offset_x: float) -> None:
        draw_rect = self.rect.move(-offset_x, 0)
        if self.style == "ground":
            base_rect = draw_rect.copy()
            pygame.draw.rect(surface, darken(self.color, 18), base_rect)
            top_rect = pygame.Rect(base_rect.x, base_rect.y, base_rect.width, 28)
            pygame.draw.rect(surface, lighten(self.color, 34), top_rect)
            stripe_color = darken(self.color, 32)
            for x in range(base_rect.x, base_rect.right, 36):
                pygame.draw.line(
                    surface,
                    stripe_color,
                    (x, base_rect.bottom - 18),
                    (x + 22, base_rect.bottom - 8),
                    4,
                )
            pygame.draw.line(
                surface,
                darken(self.color, 50),
                (base_rect.left, base_rect.bottom - 2),
                (base_rect.right, base_rect.bottom - 2),
                4,
            )
        else:
            shadow = draw_rect.inflate(6, 6)
            shadow.y += 4
            pygame.draw.rect(surface, darken(self.color, 60), shadow, border_radius=10)
            pygame.draw.rect(surface, self.color, draw_rect, border_radius=10)
            highlight = pygame.Rect(draw_rect.x + 6, draw_rect.y + 4, draw_rect.width - 12, 10)
            pygame.draw.rect(surface, lighten(self.color, 40), highlight, border_radius=6)
            shade = pygame.Rect(draw_rect.x + 6, draw_rect.bottom - 14, draw_rect.width - 12, 10)
            pygame.draw.rect(surface, darken(self.color, 45), shade, border_radius=6)
            pygame.draw.rect(surface, darken(self.color, 70), draw_rect, 3, border_radius=10)


class Coin:
    def __init__(self, x: int, y: int) -> None:
        self.rect = pygame.Rect(x, y, 22, 28)
        self.collected = False
        self.float_phase = random.random() * math.tau

    def reset(self) -> None:
        self.collected = False
        self.float_phase = random.random() * math.tau

    def update(self) -> None:
        if self.collected:
            return
        self.float_phase += 0.08

    def draw(self, surface: pygame.Surface, offset_x: float) -> None:
        if self.collected:
            return
        offset = math.sin(self.float_phase) * 4
        draw_rect = self.rect.move(-offset_x, -offset)
        pygame.draw.ellipse(surface, (220, 170, 28), draw_rect)
        inner = draw_rect.inflate(-8, -6)
        if inner.width > 0 and inner.height > 0:
            pygame.draw.ellipse(surface, (252, 226, 128), inner)
            shine = pygame.Rect(0, 0, inner.width // 3, max(4, inner.height - 6))
            shine.center = (inner.centerx - 4, inner.centery)
            pygame.draw.ellipse(surface, (255, 238, 180), shine)
        pygame.draw.ellipse(surface, (168, 120, 26), draw_rect, 3)


class Enemy:
    def __init__(self, x: int, y: int, patrol_left: int, patrol_right: int, color: Color) -> None:
        self.rect = pygame.Rect(x, y, 40, 40)
        self.speed = 2
        self.direction = 1
        self.patrol_left = patrol_left
        self.patrol_right = patrol_right
        self.color = color
        self.alive = True

    def update(self) -> None:
        if not self.alive:
            return
        self.rect.x += self.speed * self.direction
        if self.rect.left <= self.patrol_left or self.rect.right >= self.patrol_right:
            self.direction *= -1
            self.rect.x += self.speed * self.direction

    def draw(self, surface: pygame.Surface, offset_x: float) -> None:
        if not self.alive:
            return
        draw_rect = self.rect.move(-offset_x, 0)
        shell = pygame.Rect(draw_rect.x, draw_rect.y + 14, draw_rect.width, draw_rect.height - 14)
        pygame.draw.rect(surface, darken(self.color, 50), shell.inflate(6, 6), border_radius=12)
        pygame.draw.rect(surface, self.color, shell, border_radius=12)
        head = pygame.Rect(draw_rect.x + 6, draw_rect.y, draw_rect.width - 12, 22)
        pygame.draw.rect(surface, (244, 228, 188), head, border_radius=8)
        eye_color = (24, 24, 32)
        pygame.draw.circle(surface, eye_color, (head.x + 8, head.y + 12), 4)
        pygame.draw.circle(surface, eye_color, (head.right - 8, head.y + 12), 4)
        foot_color = darken(self.color, 70)
        foot_left = pygame.Rect(draw_rect.x + 4, draw_rect.bottom - 8, 14, 6)
        foot_right = pygame.Rect(draw_rect.right - 18, draw_rect.bottom - 8, 14, 6)
        pygame.draw.rect(surface, foot_color, foot_left, border_radius=3)
        pygame.draw.rect(surface, foot_color, foot_right, border_radius=3)


class Projectile:
    def __init__(self, x: float, y: float, vx: float, vy: float, color: Color, gravity: float = 0.0) -> None:
        self.rect = pygame.Rect(int(x), int(y), 14, 14)
        self.velocity = pygame.Vector2(vx, vy)
        self.color = color
        self.gravity = gravity

    def update(self) -> None:
        self.rect.x += int(self.velocity.x)
        self.rect.y += int(self.velocity.y)
        self.velocity.y += self.gravity

    def draw(self, surface: pygame.Surface, offset_x: float) -> None:
        draw_rect = self.rect.move(-offset_x, 0)
        pygame.draw.rect(surface, self.color, draw_rect, border_radius=4)

    def off_limits(self, level_width: int) -> bool:
        return (
            self.rect.top > SCREEN_HEIGHT + 200
            or self.rect.right < -200
            or self.rect.left > level_width + 200
        )


class Boss:
    def __init__(self, boss_type: str, bounds: Tuple[int, int], floor_y: int) -> None:
        self.type = boss_type
        self.bounds = bounds
        self.floor_y = floor_y
        if boss_type == "kamek":
            self.rect = pygame.Rect((bounds[0] + bounds[1]) // 2, 280, 56, 64)
            self.health = 6
        else:
            self.rect = pygame.Rect((bounds[0] + bounds[1]) // 2, floor_y - 72, 72, 72)
            self.health = 10
        self.max_health = self.health
        self.direction = 1
        self.timer = 0
        self.float_phase = random.random() * math.tau
        self.velocity = pygame.Vector2(0, 0)
        self.defeated = False

    def update(self, player_rect: pygame.Rect, projectiles: List[Projectile]) -> None:
        if self.defeated:
            return
        if self.type == "kamek":
            self.float_phase += 0.04
            float_y = 300 + math.sin(self.float_phase) * 40
            self.rect.y = int(float_y)
            self.rect.x += int(2.5 * self.direction)
            if self.rect.left < self.bounds[0] or self.rect.right > self.bounds[1]:
                self.direction *= -1
                self.rect.x += int(2.5 * self.direction)
            self.timer += 1
            if self.timer >= 70:
                self.timer = 0
                dx = player_rect.centerx - self.rect.centerx
                vx = max(-3, min(3, dx / 40))
                projectile = Projectile(
                    self.rect.centerx,
                    self.rect.bottom - 10,
                    vx,
                    5,
                    (160, 90, 255),
                    gravity=0.15,
                )
                projectiles.append(projectile)
        else:  # Bowser Jr.
            self.velocity.y += GRAVITY
            self.rect.y += int(self.velocity.y)
            if self.rect.bottom >= self.floor_y:
                self.rect.bottom = self.floor_y
                self.velocity.y = 0
            self.rect.x += int(3.2 * self.direction)
            if self.rect.left < self.bounds[0] or self.rect.right > self.bounds[1]:
                self.direction *= -1
                self.rect.x += int(3.2 * self.direction)
            self.timer += 1
            if self.timer % 160 == 0 and self.rect.bottom >= self.floor_y:
                self.velocity.y = -13
            if self.timer % 90 == 0:
                dx = player_rect.centerx - self.rect.centerx
                dy = player_rect.centery - self.rect.centery
                distance = max(1.0, math.hypot(dx, dy))
                speed = 5.0
                vx = dx / distance * speed
                vy = dy / distance * speed
                projectile = Projectile(
                    self.rect.centerx,
                    self.rect.centery,
                    vx,
                    vy,
                    (255, 140, 60),
                )
                projectiles.append(projectile)

    def take_damage(self) -> None:
        if self.defeated:
            return
        self.health -= 1
        if self.health <= 0:
            self.defeated = True

    def draw(self, surface: pygame.Surface, offset_x: float) -> None:
        if self.defeated:
            return
        draw_rect = self.rect.move(-offset_x, 0)
        if self.type == "kamek":
            robe_rect = draw_rect.inflate(6, 6)
            pygame.draw.rect(surface, (116, 86, 202), robe_rect, border_radius=14)
            hat = pygame.Rect(draw_rect.x + 6, draw_rect.y - 20, draw_rect.width - 12, 28)
            pygame.draw.rect(surface, (210, 210, 255), hat, border_radius=8)
            pygame.draw.rect(surface, (48, 38, 110), robe_rect, 4, border_radius=14)
        else:
            shell = pygame.Rect(draw_rect.x, draw_rect.y + 18, draw_rect.width, draw_rect.height - 18)
            pygame.draw.rect(surface, (206, 110, 48), shell, border_radius=14)
            jaw = pygame.Rect(draw_rect.x + 8, draw_rect.centery + 4, draw_rect.width - 16, 18)
            pygame.draw.rect(surface, (248, 198, 120), jaw, border_radius=8)
            pygame.draw.circle(surface, (248, 198, 120), (draw_rect.centerx - 12, draw_rect.y + 26), 8)
            pygame.draw.circle(surface, (248, 198, 120), (draw_rect.centerx + 12, draw_rect.y + 26), 8)
            pygame.draw.rect(surface, (98, 42, 22), draw_rect, 4, border_radius=14)


class Player:
    def __init__(self, position: Tuple[int, int]) -> None:
        self.rect = pygame.Rect(position[0], position[1], 40, 54)
        self.velocity = pygame.Vector2(0, 0)
        self.on_ground = False
        self.lives = 5
        self.max_lives = 8
        self.invulnerable_timer = 0
        self.score = 0
        self.coins = 0

    def reset(self, position: Tuple[int, int]) -> None:
        self.rect.topleft = position
        self.velocity.update(0, 0)
        self.on_ground = False
        self.invulnerable_timer = 45

    def hurt(self) -> None:
        if self.invulnerable_timer > 0:
            return
        self.lives -= 1
        self.invulnerable_timer = 90

    def add_coin(self) -> None:
        self.coins += 1
        if self.coins >= 100:
            self.coins -= 100
            self.lives = min(self.max_lives, self.lives + 1)

    def update(self, keys: pygame.key.ScancodeWrapper, platforms: Sequence[Platform]) -> None:
        self.velocity.x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.velocity.x = -PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.velocity.x = PLAYER_SPEED

        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.velocity.y = -PLAYER_JUMP
            self.on_ground = False

        self.rect.x += int(self.velocity.x)
        self._resolve_horizontal_collisions(platforms)

        self.velocity.y += GRAVITY
        if self.velocity.y > MAX_FALL_SPEED:
            self.velocity.y = MAX_FALL_SPEED
        self.rect.y += int(self.velocity.y)
        self._resolve_vertical_collisions(platforms)

        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1

    def _resolve_horizontal_collisions(self, platforms: Sequence[Platform]) -> None:
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity.x > 0:
                    self.rect.right = platform.rect.left
                elif self.velocity.x < 0:
                    self.rect.left = platform.rect.right

    def _resolve_vertical_collisions(self, platforms: Sequence[Platform]) -> None:
        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.velocity.y > 0:
                    self.rect.bottom = platform.rect.top
                    self.velocity.y = 0
                    self.on_ground = True
                elif self.velocity.y < 0:
                    self.rect.top = platform.rect.bottom
                    self.velocity.y = 0

    def draw(self, surface: pygame.Surface, offset_x: float) -> None:
        draw_rect = self.rect.move(-offset_x, 0)
        body = pygame.Rect(draw_rect.x + 8, draw_rect.y + 24, draw_rect.width - 16, draw_rect.height - 24)
        overalls = pygame.Rect(draw_rect.x + 8, draw_rect.y + 26, draw_rect.width - 16, draw_rect.height - 30)
        shirt_color = (224, 56, 56)
        overall_color = (32, 72, 200)
        glove_color = (252, 252, 252)
        head_rect = pygame.Rect(draw_rect.x + 10, draw_rect.y + 4, draw_rect.width - 20, 26)
        face_color = (252, 214, 164)
        hat_rect = pygame.Rect(draw_rect.x + 6, draw_rect.y - 6, draw_rect.width - 12, 16)

        pygame.draw.rect(surface, darken(shirt_color, 60), body.inflate(6, 8), border_radius=12)
        pygame.draw.rect(surface, shirt_color, body, border_radius=10)
        pygame.draw.rect(surface, overall_color, overalls, border_radius=10)
        strap_left = pygame.Rect(overalls.x + 4, overalls.y - 6, 8, 18)
        strap_right = pygame.Rect(overalls.right - 12, overalls.y - 6, 8, 18)
        pygame.draw.rect(surface, overall_color, strap_left, border_radius=4)
        pygame.draw.rect(surface, overall_color, strap_right, border_radius=4)
        pygame.draw.circle(surface, (248, 232, 120), (strap_left.centerx, strap_left.y + 6), 4)
        pygame.draw.circle(surface, (248, 232, 120), (strap_right.centerx, strap_right.y + 6), 4)

        pygame.draw.rect(surface, face_color, head_rect, border_radius=10)
        moustache = pygame.Rect(head_rect.x + 4, head_rect.centery, head_rect.width - 8, 8)
        pygame.draw.rect(surface, (82, 52, 30), moustache, border_radius=6)
        eye_color = (24, 24, 32)
        pygame.draw.circle(surface, eye_color, (head_rect.x + 10, head_rect.y + 12), 4)
        pygame.draw.circle(surface, eye_color, (head_rect.right - 10, head_rect.y + 12), 4)

        hat_color = (206, 32, 48)
        pygame.draw.rect(surface, darken(hat_color, 50), hat_rect.inflate(6, 6), border_radius=10)
        pygame.draw.rect(surface, hat_color, hat_rect, border_radius=8)
        brim = pygame.Rect(hat_rect.x - 2, hat_rect.bottom - 4, hat_rect.width + 4, 8)
        pygame.draw.rect(surface, hat_color, brim, border_radius=6)
        pygame.draw.circle(surface, (255, 255, 255), (hat_rect.centerx, hat_rect.centery + 2), 6)
        pygame.draw.circle(surface, (220, 40, 40), (hat_rect.centerx, hat_rect.centery + 2), 4)

        glove_left = pygame.Rect(draw_rect.x + 2, draw_rect.y + 34, 12, 12)
        glove_right = pygame.Rect(draw_rect.right - 14, draw_rect.y + 34, 12, 12)
        pygame.draw.rect(surface, glove_color, glove_left, border_radius=6)
        pygame.draw.rect(surface, glove_color, glove_right, border_radius=6)

        shoe_left = pygame.Rect(draw_rect.x + 4, draw_rect.bottom - 10, 14, 10)
        shoe_right = pygame.Rect(draw_rect.right - 18, draw_rect.bottom - 10, 14, 10)
        shoe_color = (132, 78, 40)
        pygame.draw.rect(surface, shoe_color, shoe_left, border_radius=5)
        pygame.draw.rect(surface, shoe_color, shoe_right, border_radius=5)

        if self.invulnerable_timer > 0 and (self.invulnerable_timer // 4) % 2 == 0:
            flash_rect = draw_rect.inflate(6, 6)
            flash_surface = pygame.Surface(flash_rect.size, pygame.SRCALPHA)
            flash_surface.fill((255, 255, 255, 130))
            surface.blit(flash_surface, flash_rect)


class Level:
    def __init__(self, world: int, index: int) -> None:
        self.world = world
        self.index = index
        self.is_castle = index == 5
        self.theme = CASTLE_THEME if self.is_castle else THEMES[(world - 1) % len(THEMES)]
        self.width = 2200 if not self.is_castle else 2000
        self.platforms: List[Platform] = []
        self.enemies: List[Enemy] = []
        self.projectiles: List[Projectile] = []
        self.coins: List[Coin] = []
        self.boss: Optional[Boss] = None
        self.goal_rect = pygame.Rect(self.width - 90, 300, 40, 260)
        self.door_rect = pygame.Rect(self.width - 120, 320, 70, 200)
        self.spawn_point = (80, 460)
        self.title = f"World {world}-{index}"
        self.time_limit = 400 if not self.is_castle else 500
        self.clouds: List[Tuple[float, float, float]] = []
        self.hills: List[Tuple[float, float, float, float]] = []
        self.bushes: List[Tuple[float, float, float]] = []
        self.sky_gradient = self._create_sky_gradient()
        self._build()

    def _create_sky_gradient(self) -> pygame.Surface:
        top = lighten(self.theme.background, 18)
        bottom = darken(self.theme.background, 26)
        surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            color = pygame.Color(0)
            color.r = int(top[0] * (1 - t) + bottom[0] * t)
            color.g = int(top[1] * (1 - t) + bottom[1] * t)
            color.b = int(top[2] * (1 - t) + bottom[2] * t)
            color.a = 255
            pygame.draw.line(surface, color, (0, y), (SCREEN_WIDTH, y))
        return surface

    def _build(self) -> None:
        random.seed(self.world * 100 + self.index)
        ground = Platform(-600, 520, self.width + 1200, 120, self.theme.ground, style="ground")
        self.platforms.append(ground)
        accent_color = lighten(self.theme.accent, 4)

        if not self.is_castle:
            self.clouds = [
                (
                    random.uniform(-200, self.width + 400),
                    random.uniform(60, 180),
                    random.uniform(0.9, 1.35),
                )
                for _ in range(10)
            ]
            self.hills = [
                (
                    random.uniform(-300, self.width + 320),
                    random.uniform(160, 260),
                    random.uniform(0.7, 1.2),
                    random.uniform(0.2, 0.5),
                )
                for _ in range(14)
            ]
            self.bushes = [
                (
                    random.uniform(-200, self.width + 200),
                    random.uniform(SCREEN_HEIGHT - 180, SCREEN_HEIGHT - 140),
                    random.uniform(0.6, 1.1),
                )
                for _ in range(18)
            ]
        else:
            self.clouds = []
            self.hills = []
            self.bushes = []

        if not self.is_castle:
            platform_count = 6 + max(0, self.world // 2)
            x_cursor = 220
            for _ in range(platform_count):
                width = random.randint(160, 230)
                y = random.randint(260, 420)
                x = x_cursor + random.randint(-70, 70)
                platform = Platform(x, y, width, 24, accent_color)
                self.platforms.append(platform)
                coin_slots = random.randint(1, 3)
                start_x = x + 24
                for i in range(coin_slots):
                    coin_x = start_x + i * 36
                    if coin_x + 22 < x + width:
                        self.coins.append(Coin(coin_x, y - 36))
                if random.random() < 0.55:
                    patrol_left = x - 20
                    patrol_right = x + width + 20
                    enemy_x = random.randint(x + 10, x + width - 50)
                    enemy = Enemy(enemy_x, y - 40, patrol_left, patrol_right, (182, 122, 64))
                    self.enemies.append(enemy)
                x_cursor += random.randint(220, 320)
            finale_platform = Platform(self.goal_rect.x - 60, 420, 220, 22, accent_color)
            self.platforms.append(finale_platform)
            self.coins.extend(
                [
                    Coin(self.goal_rect.x - 40 + i * 32, 360)
                    for i in range(4)
                ]
            )
            self.title = f"World {self.world}-{self.index} ({self.theme.name})"
        else:
            self.goal_rect = pygame.Rect(self.width - 80, 260, 30, 260)
            self.spawn_point = (90, 460)
            castle_steps = [410, 310, 360, 270, 340]
            base_x = 280
            for i, height in enumerate(castle_steps):
                platform = Platform(
                    base_x + i * 240,
                    height,
                    170,
                    24,
                    lighten(self.theme.accent, 6),
                )
                self.platforms.append(platform)
                self.coins.append(Coin(base_x + i * 240 + 48, height - 38))
            right_platform = Platform(self.width - 360, 380, 200, 24, lighten(self.theme.accent, 6))
            self.platforms.append(right_platform)
            self.coins.append(Coin(self.width - 300, 340))
            boss_bounds = (self.width - 560, self.width - 80)
            boss_type = "bowser_jr" if self.world == 20 else "kamek"
            self.boss = Boss(boss_type, boss_bounds, 520)
            self.title = f"World {self.world} Castle - {'Final Showdown' if boss_type == 'bowser_jr' else 'Kamek'}"

    def reset_entities(self) -> None:
        for enemy in self.enemies:
            enemy.alive = True
        self.projectiles.clear()
        for coin in self.coins:
            coin.reset()
        if self.boss:
            self.boss.defeated = False
            self.boss.health = self.boss.max_health
            if self.boss.type == "bowser_jr":
                self.boss.rect.bottom = self.boss.floor_y
                self.boss.velocity.update(0, 0)
            else:
                self.boss.rect.y = 280

    def update(self, player_rect: pygame.Rect) -> None:
        for enemy in self.enemies:
            enemy.update()
        self.enemies = [enemy for enemy in self.enemies if enemy.alive]
        if self.boss:
            self.boss.update(player_rect, self.projectiles)
        for projectile in list(self.projectiles):
            projectile.update()
            if projectile.off_limits(self.width):
                self.projectiles.remove(projectile)
                continue
            for platform in self.platforms:
                if projectile.rect.colliderect(platform.rect):
                    if projectile in self.projectiles:
                        self.projectiles.remove(projectile)
                    break
        for coin in self.coins:
            coin.update()

    def draw_background(self, surface: pygame.Surface, offset_x: float) -> None:
        if self.is_castle:
            surface.fill(self.theme.background)
            for i in range(0, SCREEN_WIDTH + 120, 120):
                column_rect = pygame.Rect(i, 0, 80, SCREEN_HEIGHT)
                pygame.draw.rect(surface, darken(self.theme.background, 20), column_rect)
                brick_height = 36
                color_a = lighten(self.theme.background, 14)
                color_b = darken(self.theme.background, 10)
                for y in range(80, SCREEN_HEIGHT, brick_height):
                    target = pygame.Rect(i, y, 80, brick_height - 4)
                    pygame.draw.rect(surface, color_a if (y // brick_height) % 2 == 0 else color_b, target)
                    pygame.draw.rect(surface, darken(self.theme.background, 40), target, 2)
            return

        surface.blit(self.sky_gradient, (0, 0))

        for x, height, scale, speed in self.hills:
            hill_width = 260 * scale
            draw_x = (x - offset_x * speed) % (self.width + 520) - 260
            base_y = SCREEN_HEIGHT - 140
            hill_rect = pygame.Rect(int(draw_x), int(base_y - height), int(hill_width), int(height))
            hill_color = lighten(self.theme.distant, 18)
            pygame.draw.ellipse(surface, hill_color, hill_rect)
            pygame.draw.ellipse(surface, darken(hill_color, 40), hill_rect, 3)

        for bx, by, scale in self.bushes:
            draw_x = (bx - offset_x * 0.55) % (self.width + 360) - 180
            width = max(40, int(140 * scale))
            height = max(24, int(70 * scale))
            base = pygame.Rect(int(draw_x), int(by), width, height)
            color = lighten(self.theme.distant, 26)
            pygame.draw.ellipse(surface, color, base)
            pygame.draw.ellipse(surface, darken(color, 50), base, 3)
            top = base.inflate(-width // 4, -height // 3)
            if top.width > 0 and top.height > 0:
                pygame.draw.ellipse(surface, lighten(color, 18), top)

        for cx, cy, scale in self.clouds:
            draw_x = (cx - offset_x * 0.25) % (self.width + 400) - 200
            wobble = math.sin((offset_x + cx) * 0.004) * 6
            self._draw_cloud(surface, draw_x, cy + wobble, 140 * scale, 60 * scale)

    def _draw_cloud(self, surface: pygame.Surface, x: float, y: float, width: float, height: float) -> None:
        width = max(20, int(width))
        height = max(14, int(height))
        base = pygame.Rect(int(x), int(y), width, height)
        color = lighten(self.theme.accent, 20)
        pygame.draw.ellipse(surface, color, base)
        inner = base.inflate(-max(2, width // 4), -max(2, height // 3))
        if inner.width > 0 and inner.height > 0:
            pygame.draw.ellipse(surface, lighten(color, 20), inner)
        left = pygame.Rect(base.x - width // 3, base.y + height // 6, width // 2, int(height * 0.7))
        right = pygame.Rect(base.right - width // 2, base.y + height // 6, width // 2, int(height * 0.7))
        pygame.draw.ellipse(surface, color, left)
        pygame.draw.ellipse(surface, color, right)

    def draw(self, surface: pygame.Surface, offset_x: float) -> None:
        for platform in self.platforms:
            platform.draw(surface, offset_x)
        for coin in self.coins:
            coin.draw(surface, offset_x)
        for enemy in self.enemies:
            enemy.draw(surface, offset_x)
        for projectile in self.projectiles:
            projectile.draw(surface, offset_x)
        if self.boss:
            self.boss.draw(surface, offset_x)
        if not self.is_castle:
            flag_rect = self.goal_rect.move(-offset_x, 0)
            pole = pygame.Rect(flag_rect.right - 6, 170, 8, 360)
            pygame.draw.rect(surface, (240, 240, 240), pole)
            pygame.draw.circle(surface, (240, 240, 240), (pole.centerx, pole.top), 8)
            flag_top = flag_rect.top + 20
            flag_points = [
                (pole.x - 50, flag_top),
                (pole.x - 12, flag_top + 30),
                (pole.x - 50, flag_top + 60),
            ]
            pygame.draw.polygon(surface, (255, 64, 64), flag_points)
            pygame.draw.polygon(surface, (255, 255, 255), [
                (pole.x - 18, flag_top + 10),
                (pole.x - 10, flag_top + 30),
                (pole.x - 18, flag_top + 50),
            ])
        else:
            door_rect = self.door_rect.move(-offset_x, 0)
            color = (210, 110, 68) if self.boss and not self.boss.defeated else (90, 196, 120)
            frame = pygame.Rect(door_rect.x - 8, door_rect.y - 10, door_rect.width + 16, door_rect.height + 20)
            pygame.draw.rect(surface, darken(color, 60), frame, border_radius=16)
            pygame.draw.rect(surface, color, door_rect, border_radius=14)
            opening = door_rect.inflate(-34, -62)
            pygame.draw.rect(surface, (32, 32, 48), opening, border_radius=10)
            knob = pygame.Rect(door_rect.right - 34, door_rect.centery - 6, 12, 12)
            pygame.draw.ellipse(surface, (252, 220, 120), knob)

    def boss_alive(self) -> bool:
        return self.boss is not None and not self.boss.defeated


class JourneyGame:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Samsoft Mario Forever: A Really Long Journey")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 20)
        self.big_font = pygame.font.SysFont("arial", 42, bold=True)
        self.hud_font = pygame.font.SysFont("arial", 26, bold=True)
        self.hud_small_font = pygame.font.SysFont("arial", 18, bold=True)
        self.state = "title"
        self.world = 1
        self.level_index = 1
        self.level = Level(self.world, self.level_index)
        self.player = Player(self.level.spawn_point)
        self.message_timer = 0
        self.time_remaining = float(self.level.time_limit)
        self.hud_surface = self._create_hud_surface()
        self.player_icon = self._create_player_icon()
        self.coin_icon = self._create_coin_icon()

    def _create_hud_surface(self) -> pygame.Surface:
        height = 68
        surface = pygame.Surface((SCREEN_WIDTH, height), pygame.SRCALPHA)
        for y in range(height):
            t = y / max(1, height - 1)
            color = pygame.Color(0)
            color.r = int(66 + 38 * (1 - t))
            color.g = int(122 + 48 * (1 - t))
            color.b = int(198 + 26 * (1 - t))
            color.a = 225
            pygame.draw.line(surface, color, (0, y), (SCREEN_WIDTH, y))
        pygame.draw.rect(surface, (255, 255, 255, 200), surface.get_rect(), 2, border_radius=18)
        return surface

    def _create_player_icon(self) -> pygame.Surface:
        surface = pygame.Surface((44, 44), pygame.SRCALPHA)
        pygame.draw.circle(surface, (206, 38, 44), (22, 18), 14)
        pygame.draw.rect(surface, (206, 38, 44), (8, 16, 28, 10), border_radius=6)
        pygame.draw.circle(surface, (255, 255, 255), (22, 18), 6)
        pygame.draw.circle(surface, (226, 46, 46), (22, 18), 4)
        face_rect = pygame.Rect(12, 20, 20, 18)
        pygame.draw.rect(surface, (252, 214, 164), face_rect, border_radius=8)
        moustache = pygame.Rect(12, 30, 20, 6)
        pygame.draw.rect(surface, (82, 52, 30), moustache, border_radius=4)
        pygame.draw.circle(surface, (24, 24, 32), (16, 26), 3)
        pygame.draw.circle(surface, (24, 24, 32), (28, 26), 3)
        pygame.draw.rect(surface, (32, 72, 200), (10, 34, 24, 10), border_radius=4)
        return surface

    def _create_coin_icon(self) -> pygame.Surface:
        surface = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.ellipse(surface, (220, 170, 28), (6, 4, 20, 24))
        pygame.draw.ellipse(surface, (252, 226, 128), (9, 6, 14, 20))
        pygame.draw.ellipse(surface, (168, 120, 26), (6, 4, 20, 24), 3)
        return surface

    def start_new_game(self) -> None:
        self.world = 1
        self.level_index = 1
        self.level = Level(self.world, self.level_index)
        self.player = Player(self.level.spawn_point)
        self.state = "playing"
        self.message_timer = 180
        self.time_remaining = float(self.level.time_limit)

    def current_level_complete(self) -> None:
        self.player.score += int(self.time_remaining) * 50
        self.level_index += 1
        if self.level_index > 5:
            self.level_index = 1
            self.world += 1
            if self.world > 20:
                self.state = "victory"
                return
        self.level = Level(self.world, self.level_index)
        self.player.reset(self.level.spawn_point)
        self.message_timer = 150
        self.time_remaining = float(self.level.time_limit)

    def handle_player_hit(self) -> None:
        previous_lives = self.player.lives
        self.player.hurt()
        if self.player.lives < previous_lives:
            if self.player.lives <= 0:
                self.state = "game_over"
            else:
                self.level.reset_entities()
                self.player.reset(self.level.spawn_point)
                self.time_remaining = float(self.level.time_limit)

    def update_gameplay(self) -> None:
        keys = pygame.key.get_pressed()
        self.player.update(keys, self.level.platforms)
        if self.player.rect.top > SCREEN_HEIGHT + 200:
            self.handle_player_hit()
            return

        self.level.update(self.player.rect)
        self.time_remaining = max(0.0, self.time_remaining - 1 / FPS)
        if self.time_remaining <= 0:
            self.handle_player_hit()
            if self.state == "playing":
                self.time_remaining = float(self.level.time_limit)
            return

        for coin in self.level.coins:
            if not coin.collected and self.player.rect.colliderect(coin.rect):
                coin.collected = True
                self.player.add_coin()
                self.player.score += 100

        for enemy in list(self.level.enemies):
            if not enemy.alive:
                continue
            if self.player.rect.colliderect(enemy.rect):
                if self.player.velocity.y > 0 and self.player.rect.centery < enemy.rect.centery:
                    enemy.alive = False
                    self.player.velocity.y = -10
                    self.player.score += 100
                else:
                    self.handle_player_hit()
                    return

        if self.level.boss and not self.level.boss.defeated and self.player.rect.colliderect(self.level.boss.rect):
            if self.player.velocity.y > 0 and self.player.rect.centery < self.level.boss.rect.centery:
                self.level.boss.take_damage()
                self.player.velocity.y = -12
                self.player.score += 250
            else:
                self.handle_player_hit()
                return

        for projectile in list(self.level.projectiles):
            if projectile.rect.colliderect(self.player.rect):
                self.level.projectiles.remove(projectile)
                self.handle_player_hit()
                return

        if not self.level.is_castle and self.player.rect.colliderect(self.level.goal_rect):
            self.player.score += 500
            self.current_level_complete()
        elif self.level.is_castle and not self.level.boss_alive() and self.player.rect.colliderect(self.door_rect_world()):
            self.player.score += 750
            self.current_level_complete()

    def door_rect_world(self) -> pygame.Rect:
        return self.level.door_rect

    def draw_hud(self) -> None:
        self.screen.blit(self.hud_surface, (0, 0))
        render_outlined_text(
            self.screen,
            f"WORLD {self.world}-{self.level_index}",
            self.hud_font,
            (34, 14),
            (255, 255, 255),
            (16, 32, 80),
        )
        self.screen.blit(self.player_icon, (220, 10))
        render_outlined_text(
            self.screen,
            f"×{self.player.lives:02d}",
            self.hud_font,
            (268, 14),
            (255, 255, 255),
            (16, 32, 80),
        )
        self.screen.blit(self.coin_icon, (340, 14))
        render_outlined_text(
            self.screen,
            f"×{self.player.coins:02d}",
            self.hud_font,
            (380, 14),
            (255, 255, 255),
            (16, 32, 80),
        )
        render_outlined_text(
            self.screen,
            f"SCORE {self.player.score:07d}",
            self.hud_font,
            (500, 14),
            (255, 255, 255),
            (16, 32, 80),
        )
        time_value = max(0, int(self.time_remaining))
        render_outlined_text(
            self.screen,
            f"TIME {time_value:03d}",
            self.hud_font,
            (SCREEN_WIDTH - 190, 14),
            (255, 255, 255),
            (16, 32, 80),
        )

        if self.level.is_castle and self.level.boss:
            bar_width = 240
            bar_rect = pygame.Rect(SCREEN_WIDTH - bar_width - 40, 46, bar_width, 18)
            overlay_rect = bar_rect.inflate(12, 12)
            overlay = pygame.Surface(overlay_rect.size, pygame.SRCALPHA)
            overlay.fill((24, 24, 40, 160))
            self.screen.blit(overlay, overlay_rect.topleft)
            pygame.draw.rect(self.screen, (36, 36, 56), bar_rect, border_radius=10)
            if not self.level.boss.defeated:
                health_ratio = self.level.boss.health / self.level.boss.max_health
                inner_width = int((bar_rect.width - 6) * health_ratio)
                health_rect = pygame.Rect(bar_rect.x + 3, bar_rect.y + 3, inner_width, bar_rect.height - 6)
                pygame.draw.rect(self.screen, (232, 72, 72), health_rect, border_radius=8)
                label = "Bowser Jr." if self.level.boss.type == "bowser_jr" else "Kamek"
                render_outlined_text(
                    self.screen,
                    label,
                    self.hud_small_font,
                    (bar_rect.x + 8, bar_rect.y - 18),
                    (255, 255, 255),
                    (16, 32, 80),
                    outline_size=1,
                )

        if self.message_timer > 0:
            self.message_timer -= 1
            banner = self.big_font.render(self.level.title, True, (255, 255, 255))
            banner_rect = banner.get_rect(center=(SCREEN_WIDTH // 2, 110))
            bg_rect = banner_rect.inflate(30, 20)
            banner_bg = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
            banner_bg.fill((0, 0, 0, 160))
            self.screen.blit(banner_bg, bg_rect)
            self.screen.blit(banner, banner_rect)

    def draw_gameplay(self) -> None:
        offset_x = max(0, min(self.level.width - SCREEN_WIDTH, self.player.rect.centerx - SCREEN_WIDTH // 2))
        self.level.draw_background(self.screen, offset_x)
        self.level.draw(self.screen, offset_x)
        self.player.draw(self.screen, offset_x)
        self.draw_hud()

    def draw_title(self) -> None:
        self.level.draw_background(self.screen, 0)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))
        render_outlined_text(
            self.screen,
            "Samsoft Mario Forever",
            self.big_font,
            (SCREEN_WIDTH // 2 - 210, 180),
            (255, 255, 255),
            (16, 24, 72),
        )
        render_outlined_text(
            self.screen,
            "A Really Long Journey",
            self.hud_font,
            (SCREEN_WIDTH // 2 - 180, 240),
            (255, 240, 220),
            (16, 24, 72),
        )
        render_outlined_text(
            self.screen,
            "Press Enter to begin",
            self.hud_small_font,
            (SCREEN_WIDTH // 2 - 140, 320),
            (255, 255, 255),
            (16, 24, 72),
        )

    def draw_game_over(self) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((18, 18, 18))
        self.screen.blit(overlay, (0, 0))
        render_outlined_text(
            self.screen,
            "Game Over",
            self.big_font,
            (SCREEN_WIDTH // 2 - 110, 200),
            (240, 70, 70),
            (0, 0, 0),
        )
        render_outlined_text(
            self.screen,
            f"Score: {self.player.score}",
            self.hud_font,
            (SCREEN_WIDTH // 2 - 110, 260),
            (230, 230, 230),
            (0, 0, 0),
        )
        render_outlined_text(
            self.screen,
            "Press Enter to try again",
            self.hud_small_font,
            (SCREEN_WIDTH // 2 - 170, 320),
            (230, 230, 230),
            (0, 0, 0),
        )

    def draw_victory(self) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((30, 90, 40))
        self.screen.blit(overlay, (0, 0))
        render_outlined_text(
            self.screen,
            "You saved the Mushroom Kingdom!",
            self.big_font,
            (SCREEN_WIDTH // 2 - 280, 200),
            (255, 255, 255),
            (16, 48, 16),
        )
        render_outlined_text(
            self.screen,
            f"Final Score: {self.player.score}",
            self.hud_font,
            (SCREEN_WIDTH // 2 - 180, 260),
            (250, 250, 210),
            (16, 48, 16),
        )
        render_outlined_text(
            self.screen,
            "Press Enter to embark again",
            self.hud_small_font,
            (SCREEN_WIDTH // 2 - 190, 320),
            (240, 240, 240),
            (16, 48, 16),
        )

    def run(self) -> None:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_RETURN:
                        if self.state in {"title", "game_over", "victory"}:
                            self.start_new_game()
            if self.state == "playing":
                self.update_gameplay()
                self.draw_gameplay()
            elif self.state == "title":
                self.draw_title()
            elif self.state == "game_over":
                self.draw_game_over()
            elif self.state == "victory":
                self.draw_victory()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()


def main() -> None:
    JourneyGame().run()


if __name__ == "__main__":
    main()

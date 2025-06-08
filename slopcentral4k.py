# test.py
#
# A complete, runnable Pygame file demonstrating a player controller
# with physics and mechanics inspired by Super Mario Bros. 3, expanded to include
# game states, menus, a five-level structure, and a "romhack" system
# that allows for custom physics, levels, and color palettes.
# Enhanced with a "GIGA HACK" configuration inspired by SMW ROM hacks and Anikiti's Luigi's Adventure (2006).
#
# To run this, you need pygame: pip install pygame

import pygame
import sys
import textwrap

# --- Game Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# --- Base Game Configuration (Vanilla) ---
VANILLA_CONFIG = {
    "name": "Vanilla (The Original)",
    "description": "The way it was meant to be played.",
    "GRAVITY": 0.5,
    "MAX_FALL_SPEED": 10,
    "ACCELERATION": 0.3,
    "RUN_ACCELERATION": 0.5,
    "FRICTION": 0.25,
    "MAX_WALK_SPEED": 4,
    "MAX_RUN_SPEED": 7,
    "JUMP_FORCE": 11,
    "RUNNING_JUMP_BOOST": 2,
    "VARIABLE_JUMP_BOOST": 0.4,
    "JUMP_TIMER_DURATION": 18,
    "DEATH_Y_LEVEL": 600,
    "SKY_BLUE": (105, 185, 255),
    "WHITE": (255, 255, 255),
    "BLACK": (0, 0, 0),
    "MENU_GRAY": (50, 50, 50),
    "PLAYER_COLOR": "cyan",
    "PLAYER_RUN_COLOR": "red",
    "SOLID_COLOR": "darkgreen",
    "Q_BLOCK_COLOR": "orange",
    "Q_BLOCK_HIT_COLOR": "saddlebrown",
    "GOAL_COLOR": "gold",
    "LEVELS": [
        {"player_start": (100, 500), "solids": [{"x": 0, "y": 560, "w": 800, "h": 40}, {"x": 200, "y": 450, "w": 150, "h": 20}, {"x": 400, "y": 350, "w": 150, "h": 20}], "q_blocks": [{"x": 455, "y": 250}], "goal": {"x": 700, "y": 280, "w": 40, "h": 60}},
        {"player_start": (50, 500), "solids": [{"x": 0, "y": 560, "w": 300, "h": 40}, {"x": 450, "y": 560, "w": 350, "h": 40}, {"x": 350, "y": 450, "w": 80, "h": 20}, {"x": 100, "y": 350, "w": 80, "h": 20}, {"x": 300, "y": 250, "w": 80, "h": 20}], "q_blocks": [{"x": 500, "y": 450}, {"x": 540, "y": 450}], "goal": {"x": 750, "y": 490, "w": 40, "h": 60}},
        {"player_start": (40, 500), "solids": [{"x": 0, "y": 560, "w": 800, "h": 40}, {"x": 200, "y": 480, "w": 100, "h": 20}, {"x": 350, "y": 400, "w": 100, "h": 20}, {"x": 500, "y": 320, "w": 100, "h": 20}, {"x": 350, "y": 240, "w": 100, "h": 20}, {"x": 150, "y": 160, "w": 100, "h": 20}], "q_blocks": [{"x": 40, "y": 450}], "goal": {"x": 180, "y": 90, "w": 40, "h": 60}},
        {"player_start": (50, 200), "solids": [{"x": 0, "y": 270, "w": 250, "h": 20}, {"x": 450, "y": 270, "w": 350, "h": 20}, {"x": 0, "y": 560, "w": 800, "h": 40}, {"x": 760, "y": 400, "w": 40, "h": 160}], "q_blocks": [{"x": 600, "y": 150}, {"x": 640, "y": 150}, {"x": 680, "y": 150}], "goal": {"x": 50, "y": 490, "w": 40, "h": 60}},
        {"player_start": (50, 500), "solids": [{"x": 0, "y": 560, "w": 800, "h": 40}, {"x": 120, "y": 460, "w": 20, "h": 100}, {"x": 120, "y": 350, "w": 150, "h": 20}, {"x": 350, "y": 440, "w": 100, "h": 20}, {"x": 500, "y": 360, "w": 100, "h": 20}, {"x": 350, "y": 280, "w": 100, "h": 20}, {"x": 0, "y": 150, "w": 300, "h": 20}], "q_blocks": [{"x": 180, "y": 250}, {"x": 50, "y": 50}], "goal": {"x": 260, "y": 80, "w": 40, "h": 60}}
    ]
}

# --- Romhack Level Definitions ---
KAIZO_LEVELS = [
    {"player_start": (50, 200), "solids": [{"x": 0, "y": 270, "w": 100, "h": 20}, {"x": 350, "y": 270, "w": 40, "h": 20}, {"x": 550, "y": 250, "w": 40, "h": 20}, {"x": 650, "y": 450, "w": 150, "h": 20}, {"x": 0, "y": 580, "w": 800, "h": 20}], "q_blocks": [{"x": 350, "y": 180}], "goal": {"x": 750, "y": 380, "w": 40, "h": 60}},
    {"player_start": (30, 30), "solids": [{"x": 0, "y": 100, "w": 100, "h": 20}, {"x": 0, "y": 580, "w": 800, "h": 20}, {"x": 200, "y": 200, "w": 20, "h": 20}, {"x": 300, "y": 300, "w": 20, "h": 20}, {"x": 400, "y": 400, "w": 20, "h": 20}, {"x": 500, "y": 500, "w": 200, "h": 20}], "q_blocks": [], "goal": {"x": 650, "y": 430, "w": 40, "h": 60}},
]

INVERTED_LEVELS = [
    {"player_start": (100, 100), "solids": [{"x": 0, "y": 0, "w": 800, "h": 40}, {"x": 200, "y": 150, "w": 150, "h": 20}, {"x": 400, "y": 250, "w": 150, "h": 20}], "q_blocks": [{"x": 455, "y": 350}], "goal": {"x": 700, "y": 280, "w": 40, "h": 60}},
    {"player_start": (750, 100), "solids": [{"x": 0, "y": 0, "w": 800, "h": 40}, {"x": 0, "y": 580, "w": 800, "h": 20}, {"x": 600, "y": 150, "w": 80, "h": 20}, {"x": 450, "y": 250, "w": 80, "h": 20}, {"x": 250, "y": 350, "w": 80, "h": 20}], "q_blocks": [], "goal": {"x": 40, "y": 480, "w": 40, "h": 60}},
]

# --- New GIGA HACK Levels ---
# Inspired by SMW ROM hacks and Anikiti's Luigi's Adventure, with tight platforming and creative challenges
GIGA_HACK_LEVELS = [
    # Level 1: Kaizo Precision
    {
        "player_start": (50, 500),
        "solids": [
            {"x": 0, "y": 560, "w": 800, "h": 40},  # Ground
            {"x": 150, "y": 460, "w": 20, "h": 20},  # Small platform
            {"x": 250, "y": 400, "w": 20, "h": 20},  # Precision jump
            {"x": 350, "y": 340, "w": 20, "h": 20},  # Another small step
            {"x": 500, "y": 400, "w": 150, "h": 20},  # Safe landing
        ],
        "q_blocks": [{"x": 250, "y": 300}],
        "goal": {"x": 700, "y": 490, "w": 40, "h": 60},
    },
    # Level 2: Inverted Challenge
    {
        "player_start": (100, 100),
        "solids": [
            {"x": 0, "y": 0, "w": 800, "h": 40},  # Ceiling
            {"x": 200, "y": 200, "w": 80, "h": 20},
            {"x": 350, "y": 300, "w": 80, "h": 20},
            {"x": 500, "y": 400, "w": 80, "h": 20},
        ],
        "q_blocks": [{"x": 350, "y": 220}],
        "goal": {"x": 650, "y": 80, "w": 40, "h": 60},
    },
    # Level 3: Anikiti's Gauntlet
    {
        "player_start": (50, 500),
        "solids": [
            {"x": 0, "y": 560, "w": 300, "h": 40},  # Partial ground
            {"x": 400, "y": 560, "w": 400, "h": 40},  # Partial ground
            {"x": 300, "y": 450, "w": 20, "h": 20},  # Gap jump
            {"x": 400, "y": 350, "w": 20, "h": 20},  # High platform
            {"x": 500, "y": 250, "w": 20, "h": 20},  # Precision
            {"x": 600, "y": 150, "w": 20, "h": 20},  # Final leap
        ],
        "q_blocks": [{"x": 400, "y": 270}, {"x": 500, "y": 170}],
        "goal": {"x": 750, "y": 80, "w": 40, "h": 60},
    },
]

# --- Romhack Definitions ---
ROMHACKS = [
    {
        "name": "Kaizo: Beginner's Trap",
        "description": "A true test of platforming skill from the 2010s. Expect pixel-perfect jumps and devious traps.",
        "LEVELS": KAIZO_LEVELS,
        "JUMP_FORCE": 10.7,
        "ACCELERATION": 0.4,
    },
    {
        "name": "Low-G Adventure",
        "description": "Like bouncing on the moon! A relaxing trip through the original levels with floaty physics.",
        "GRAVITY": 0.2,
        "JUMP_FORCE": 12,
        "PLAYER_COLOR": "pink",
    },
    {
        "name": "Inverted Insanity",
        "description": "Fall is up, jump is down. Your world is turned upside down, literally. Navigate new, inverted levels.",
        "LEVELS": INVERTED_LEVELS,
        "GRAVITY": -0.5,
        "MAX_FALL_SPEED": -10,
        "DEATH_Y_LEVEL": -50,
    },
    {
        "name": "Retro NES Palette",
        "description": "Remember the 8-bit days? Experience the game with a classic, limited color palette.",
        "SKY_BLUE": (92, 148, 252),
        "PLAYER_COLOR": (252, 188, 176),
        "PLAYER_RUN_COLOR": (252, 88, 56),
        "SOLID_COLOR": (0, 168, 0),
        "Q_BLOCK_COLOR": (252, 120, 88),
        "Q_BLOCK_HIT_COLOR": (124, 60, 0),
    },
    # --- New GIGA HACK Configuration ---
    {
        "name": "GIGA HACK: Anikiti's Legacy",
        "description": "A tribute to SMW hacks and Anikiti's Luigi's Adventure. Tight platforming, inverted challenges, and epic gauntlets await!",
        "LEVELS": GIGA_HACK_LEVELS,
        "GRAVITY": 0.4,  # Slightly lower for precise control
        "JUMP_FORCE": 11.5,  # Balanced for Anikiti-style jumps
        "ACCELERATION": 0.35,  # Responsive but controlled
        "MAX_RUN_SPEED": 8,  # Faster for dynamic movement
        "PLAYER_COLOR": "limegreen",  # Thematic for Luigi
        "PLAYER_RUN_COLOR": "darkgreen",
        "SOLID_COLOR": "forestgreen",
        "Q_BLOCK_COLOR": "yellow",
        "Q_BLOCK_HIT_COLOR": "brown",
        "GOAL_COLOR": "silver",
    },
]

# --- Game Context Class ---
class GameContext:
    def __init__(self, hack_data=None):
        self.__dict__.update(VANILLA_CONFIG)
        if hack_data:
            self.__dict__.update(hack_data)

# --- Base Sprite Class ---
class MockSprite(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))

# --- Game Object Classes ---
class Solid(MockSprite):
    def __init__(self, x, y, width, height, context):
        super().__init__(x, y, width, height, context.SOLID_COLOR)

class QuestionBlock(MockSprite):
    def __init__(self, x, y, context):
        self.context = context
        super().__init__(x, y, 40, 40, self.context.Q_BLOCK_COLOR)
        self.original_y = y
        self.hit_timer = 0
        self.is_hit = False
        self._draw_initial_state()

    def _draw_initial_state(self):
        self.image.fill(self.context.Q_BLOCK_COLOR)
        font = pygame.font.SysFont("Consolas", 30, bold=True)
        text = font.render("?", True, self.context.BLACK)
        text_rect = text.get_rect(center=self.image.get_rect().center)
        self.image.blit(text, text_rect)

    def hit(self, player):
        if self.is_hit:
            return
        self.image.fill(self.context.Q_BLOCK_HIT_COLOR)
        self.hit_timer = 10
        self.is_hit = True

    def update(self, *args):
        if self.hit_timer > 0:
            self.hit_timer -= 1
            if self.hit_timer > 5:
                self.rect.y -= 2
            else:
                self.rect.y += 2
        elif self.rect.y != self.original_y:
            self.rect.y = self.original_y

class Goal(MockSprite):
    def __init__(self, x, y, width, height, context):
        super().__init__(x, y, width, height, context.GOAL_COLOR)
        font = pygame.font.SysFont("Consolas", height - 10, bold=True)
        text = font.render("★", True, context.BLACK)
        text_rect = text.get_rect(center=self.image.get_rect().center)
        self.image.blit(text, text_rect)

class Player(MockSprite):
    def __init__(self, x, y, context):
        self.context = context
        super().__init__(x, y, 30, 50, self.context.PLAYER_COLOR)
        self.velocity_x = 0
        self.velocity_y = 0
        self.on_ground = False
        self.running = False
        self.jump_held = False
        self.jump_timer = 0

    def update(self, keys, solids, blocks):
        self._handle_input(keys)
        self._apply_horizontal_movement()
        self._handle_horizontal_collisions(solids, blocks)
        self._apply_vertical_movement()
        self._handle_vertical_collisions(solids, blocks)
        self.image.fill(self.context.PLAYER_RUN_COLOR if self.running else self.context.PLAYER_COLOR)

    def _handle_input(self, keys):
        self.running = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        accel = self.context.RUN_ACCELERATION if self.running else self.context.ACCELERATION
        if keys[pygame.K_LEFT]:
            self.velocity_x -= accel
        if keys[pygame.K_RIGHT]:
            self.velocity_x += accel
        if not keys[pygame.K_LEFT] and not keys[pygame.K_RIGHT]:
            if self.velocity_x > self.context.FRICTION:
                self.velocity_x -= self.context.FRICTION
            elif self.velocity_x < -self.context.FRICTION:
                self.velocity_x += self.context.FRICTION
            else:
                self.velocity_x = 0
        max_speed = self.context.MAX_RUN_SPEED if self.running else self.context.MAX_WALK_SPEED
        self.velocity_x = max(-max_speed, min(max_speed, self.velocity_x))

    def _apply_horizontal_movement(self):
        self.rect.x += int(self.velocity_x)

    def _handle_horizontal_collisions(self, solids, blocks):
        for platform in solids.sprites() + blocks.sprites():
            if self.rect.colliderect(platform.rect):
                if self.velocity_x > 0:
                    self.rect.right = platform.rect.left
                elif self.velocity_x < 0:
                    self.rect.left = platform.rect.right
                self.velocity_x = 0

    def _apply_vertical_movement(self):
        self.velocity_y += self.context.GRAVITY
        if self.context.GRAVITY > 0:
            self.velocity_y = min(self.velocity_y, self.context.MAX_FALL_SPEED)
        else:
            self.velocity_y = max(self.velocity_y, self.context.MAX_FALL_SPEED)
        if self.jump_held and self.jump_timer > 0:
            self.velocity_y -= self.context.VARIABLE_JUMP_BOOST
            self.jump_timer -= 1
        self.rect.y += int(self.velocity_y)

    def _handle_vertical_collisions(self, solids, blocks):
        self.on_ground = False
        all_platforms = solids.sprites() + blocks.sprites()
        for platform in all_platforms:
            if self.rect.colliderect(platform.rect):
                is_ceiling_collision = (self.velocity_y < 0 and self.context.GRAVITY > 0) or (self.velocity_y > 0 and self.context.GRAVITY < 0)
                is_floor_collision = (self.velocity_y > 0 and self.context.GRAVITY > 0) or (self.velocity_y < 0 and self.context.GRAVITY < 0)
                if is_floor_collision:
                    self.rect.bottom = platform.rect.top
                    self.on_ground = True
                    self.velocity_y = 0
                    self.jump_timer = 0
                elif is_ceiling_collision:
                    self.rect.top = platform.rect.bottom
                    self.velocity_y = 0
                    self.jump_timer = 0
                    if hasattr(platform, 'hit'):
                        platform.hit(self)
                    if self.context.GRAVITY < 0:
                        self.on_ground = True

    def jump(self):
        if self.on_ground:
            jump_power = -self.context.JUMP_FORCE
            if self.running:
                jump_power -= self.context.RUNNING_JUMP_BOOST
            if self.context.GRAVITY < 0:
                jump_power *= -1
            self.velocity_y = jump_power
            self.jump_timer = self.context.JUMP_TIMER_DURATION
            self.on_ground = False

    def reset(self, x, y):
        self.rect.topleft = (x, y)
        self.velocity_x = 0
        self.velocity_y = 0
        self.on_ground = False

# --- Game Engine & State Management ---
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("SMW Central Fangame Mockup")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont("Consolas", 50, bold=True)
        self.font_small = pygame.font.SysFont("Consolas", 28)
        self.font_tiny = pygame.font.SysFont("Consolas", 18)
        self.state = "MAIN_MENU"
        self.context = None
        self.player = None
        self.save_file = None
        self.current_level_index = 0
        self.all_sprites = pygame.sprite.Group()
        self.solids = pygame.sprite.Group()
        self.blocks = pygame.sprite.Group()
        self.goals = pygame.sprite.Group()

    def run(self):
        while True:
            if self.state == "MAIN_MENU":
                self.main_menu_loop()
            elif self.state == "HACK_SELECT":
                self.hack_select_loop()
            elif self.state == "FILE_SELECT":
                self.file_select_loop()
            elif self.state == "GAMEPLAY":
                self.gameplay_loop()
            elif self.state == "LEVEL_COMPLETE":
                self.level_complete_loop()
            elif self.state == "GAME_COMPLETE":
                self.game_complete_loop()

    def _draw_text(self, text, font, color, x, y, center=True, wrap_width=0):
        if wrap_width > 0:
            lines = textwrap.wrap(text, width=wrap_width)
            for i, line in enumerate(lines):
                text_surf = font.render(line, True, color)
                text_rect = text_surf.get_rect()
                if center:
                    text_rect.center = (x, y + i * font.get_height())
                else:
                    text_rect.topleft = (x, y + i * font.get_height())
                self.screen.blit(text_surf, text_rect)
        else:
            text_surf = font.render(text, True, color)
            text_rect = text_surf.get_rect()
            if center:
                text_rect.center = (x, y)
            else:
                text_rect.topleft = (x, y)
            self.screen.blit(text_surf, text_rect)

    def _load_level(self, level_index):
        self.all_sprites.empty()
        self.solids.empty()
        self.blocks.empty()
        self.goals.empty()
        level_data = self.context.LEVELS[level_index]
        for s_data in level_data["solids"]:
            self.solids.add(Solid(s_data["x"], s_data["y"], s_data["w"], s_data["h"], self.context))
        for b_data in level_data.get("q_blocks", []):
            self.blocks.add(QuestionBlock(b_data["x"], b_data["y"], self.context))
        g_data = level_data["goal"]
        self.goals.add(Goal(g_data["x"], g_data["y"], g_data["w"], g_data["h"], self.context))
        player_start = level_data["player_start"]
        self.player.reset(player_start[0], player_start[1])
        self.all_sprites.add(self.player, self.solids, self.blocks, self.goals)

    def main_menu_loop(self):
        while self.state == "MAIN_MENU":
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    self.state = "HACK_SELECT"
            self.screen.fill(VANILLA_CONFIG["MENU_GRAY"])
            self._draw_text("Platformer Adventure!", self.font_large, VANILLA_CONFIG["WHITE"], SCREEN_WIDTH/2, SCREEN_HEIGHT/3)
            self._draw_text("Press ENTER to Start", self.font_small, VANILLA_CONFIG["WHITE"], SCREEN_WIDTH/2, SCREEN_HEIGHT/2)
            pygame.display.flip()
            self.clock.tick(FPS)

    def hack_select_loop(self):
        hack_list = [VANILLA_CONFIG] + ROMHACKS
        selected_index = 0
        while self.state == "HACK_SELECT":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.state = "MAIN_MENU"
                    if event.key == pygame.K_UP:
                        selected_index = (selected_index - 1) % len(hack_list)
                    if event.key == pygame.K_DOWN:
                        selected_index = (selected_index + 1) % len(hack_list)
                    if event.key == pygame.K_RETURN:
                        selected_hack_data = hack_list[selected_index] if selected_index > 0 else None
                        self.context = GameContext(selected_hack_data)
                        self.player = Player(0, 0, self.context)
                        self.player.kill()
                        self.state = "FILE_SELECT"
            self.screen.fill(VANILLA_CONFIG["MENU_GRAY"])
            self._draw_text("Select a Game / Mod", self.font_large, VANILLA_CONFIG["WHITE"], SCREEN_WIDTH/2, 60)
            for i, hack in enumerate(hack_list):
                color = "yellow" if i == selected_index else VANILLA_CONFIG["WHITE"]
                prefix = "> " if i == selected_index else "  "
                self._draw_text(f"{prefix}{hack['name']}", self.font_small, color, SCREEN_WIDTH/2 - 150, 150 + i * 50, center=False)
            desc_rect = pygame.Rect(50, 400, SCREEN_WIDTH - 100, 150)
            pygame.draw.rect(self.screen, (20, 20, 20), desc_rect)
            pygame.draw.rect(self.screen, VANILLA_CONFIG["WHITE"], desc_rect, 2)
            selected_hack_desc = hack_list[selected_index]['description']
            self._draw_text(selected_hack_desc, self.font_tiny, VANILLA_CONFIG["WHITE"], desc_rect.centerx, desc_rect.y + 20, center=True, wrap_width=60)
            pygame.display.flip()
            self.clock.tick(FPS)

    def file_select_loop(self):
        selected_file = 1
        while self.state == "FILE_SELECT":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.state = "HACK_SELECT"
                    if event.key == pygame.K_UP:
                        selected_file = max(1, selected_file - 1)
                    if event.key == pygame.K_DOWN:
                        selected_file = min(3, selected_file + 1)
                    if event.key == pygame.K_RETURN:
                        self.save_file = selected_file
                        self.current_level_index = 0
                        self._load_level(self.current_level_index)
                        self.state = "GAMEPLAY"
            self.screen.fill(self.context.MENU_GRAY)
            self._draw_text("Select a File", self.font_large, self.context.WHITE, SCREEN_WIDTH/2, 100)
            for i in range(1, 4):
                color = "yellow" if i == selected_file else self.context.WHITE
                self._draw_text(f"{'> ' if i == selected_file else '  '}File {i}", self.font_small, color, SCREEN_WIDTH/2, 200 + i * 60)
            self._draw_text("Press ESC to go back", self.font_small, self.context.WHITE, SCREEN_WIDTH/2, 500)
            pygame.display.flip()
            self.clock.tick(FPS)

    def gameplay_loop(self):
        running_level = True
        while running_level:
            keys = pygame.key.get_pressed()
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running_level = False
                    self.state = "MAIN_MENU"
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self.player.jump()
                    self.player.jump_held = True
                if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
                    self.player.jump_held = False
            if self.state != "GAMEPLAY":
                return
            self.player.update(keys, self.solids, self.blocks)
            self.blocks.update()
            death_condition = self.player.rect.top > self.context.DEATH_Y_LEVEL if self.context.GRAVITY > 0 else self.player.rect.bottom < self.context.DEATH_Y_LEVEL
            if death_condition:
                self._load_level(self.current_level_index)
            if pygame.sprite.spritecollide(self.player, self.goals, False):
                running_level = False
                self.current_level_index += 1
                if self.current_level_index >= len(self.context.LEVELS):
                    self.state = "GAME_COMPLETE"
                else:
                    self.state = "LEVEL_COMPLETE"
            self.screen.fill(self.context.SKY_BLUE)
            self.all_sprites.draw(self.screen)
            self._draw_text(f"Level: {self.current_level_index + 1}", self.font_small, self.context.BLACK, 10, 10, center=False)
            self._draw_text(f"Mod: {self.context.name}", self.font_tiny, self.context.BLACK, 10, 40, center=False)
            pygame.display.flip()
            self.clock.tick(FPS)

    def level_complete_loop(self):
        timer = FPS * 2
        while timer > 0:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            self.screen.fill(self.context.MENU_GRAY)
            self._draw_text("Level Complete!", self.font_large, self.context.WHITE, SCREEN_WIDTH/2, SCREEN_HEIGHT/2)
            pygame.display.flip()
            timer -= 1
            self.clock.tick(FPS)
        self._load_level(self.current_level_index)
        self.state = "GAMEPLAY"

    def game_complete_loop(self):
        while self.state == "GAME_COMPLETE":
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and (event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN)):
                    self.state = "MAIN_MENU"
            self.screen.fill(self.context.MENU_GRAY)
            self._draw_text("You Win!", self.font_large, self.context.GOAL_COLOR, SCREEN_WIDTH/2, SCREEN_HEIGHT/3)
            self._draw_text(f"Congratulations, File {self.save_file}!", self.font_small, self.context.WHITE, SCREEN_WIDTH/2, SCREEN_HEIGHT/2)
            self._draw_text("Press ENTER to return to Main Menu", self.font_small, self.context.WHITE, SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 50)
            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()

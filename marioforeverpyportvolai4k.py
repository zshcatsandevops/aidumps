import asyncio
import platform
import pygame
import sys
import math

# Constants
WIDTH, HEIGHT = 800, 600
FPS = 60
GRAVITY = 0.8
MARIO_WIDTH, MARIO_HEIGHT = 24, 32
BLOCK_SIZE = 32
COIN_SIZE = 20
ENEMY_WIDTH, ENEMY_HEIGHT = 32, 32
FLAGPOLE_WIDTH, FLAGPOLE_HEIGHT = 8, 320
PIPE_WIDTH, PIPE_HEIGHT = 64, 64
LEVEL_WIDTH = 1600

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
BROWN = (139, 69, 19)
DARK_RED = (139, 0, 0)
SKY_BLUE = (107, 136, 255)
LIGHT_BLUE = (156, 252, 240)
BRICK_RED = (181, 49, 32)
BRICK_DARK = (132, 36, 23)
GROUND_BROWN = (148, 77, 48)
GROUND_DARK = (107, 56, 35)
PIPE_GREEN = (0, 147, 0)
PIPE_DARK = (0, 98, 0)
COIN_YELLOW = (252, 216, 64)
COIN_DARK = (252, 152, 56)

# Game states
INTRO, MENU, PLAYING, GAME_OVER, VICTORY = 0, 1, 2, 3, 4

# Global variables
screen = None
font = None
big_font = None
small_font = None
mario = None
platforms = []
coins = []
enemies = []
pipes = []
flagpole = None
game_state = INTRO
coins_collected = 0
intro_timer = 0
clock = None
camera_x = 0
background = None

# Mario class with optimized sprite
class Mario:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = MARIO_WIDTH
        self.height = MARIO_HEIGHT
        self.vel_x = 0
        self.vel_y = 0
        self.jumping = False
        self.on_ground = False
        self.facing_right = True
        self.animation_frame = 0
        self.running = False

    def update(self):
        global game_state
        self.vel_y += GRAVITY
        self.y += self.vel_y
        self.x += self.vel_x
        if abs(self.vel_x) > 0:
            self.running = True
            self.animation_frame = (self.animation_frame + 0.2) % 3
        else:
            self.running = False
            self.animation_frame = 0
        if self.vel_x > 0:
            self.facing_right = True
        elif self.vel_x < 0:
            self.facing_right = False
        if self.x < 0:
            self.x = 0
        elif self.x + self.width > LEVEL_WIDTH:
            self.x = LEVEL_WIDTH - self.width
        if self.y > HEIGHT:
            game_state = GAME_OVER

    def draw(self, screen, camera_x):
        x_pos = self.x - camera_x
        # Simplified body and head
        pygame.draw.rect(screen, (255, 0, 0), (x_pos, self.y + 16, 24, 16))  # Shirt
        pygame.draw.rect(screen, (0, 0, 255), (x_pos, self.y + 24, 24, 8))   # Pants
        pygame.draw.rect(screen, (255, 220, 177), (x_pos + 4, self.y, 16, 16))  # Face
        pygame.draw.rect(screen, (255, 0, 0), (x_pos + 2, self.y - 4, 20, 6))   # Hat
        # Eye
        if self.facing_right:
            pygame.draw.rect(screen, BLACK, (x_pos + 14, self.y + 4, 2, 2))
        else:
            pygame.draw.rect(screen, BLACK, (x_pos + 8, self.y + 4, 2, 2))
        # Feet animation
        if self.running and int(self.animation_frame) == 1:
            pygame.draw.rect(screen, BROWN, (x_pos + 4, self.y + 28, 6, 4))
            pygame.draw.rect(screen, BROWN, (x_pos + 14, self.y + 28, 6, 4))
        else:
            pygame.draw.rect(screen, BROWN, (x_pos + 6, self.y + 28, 6, 4))
            pygame.draw.rect(screen, BROWN, (x_pos + 12, self.y + 28, 6, 4))

    def jump(self):
        if self.on_ground:
            self.vel_y = -15
            self.jumping = True
            self.on_ground = False

# Platform class with optimized textures
class Platform:
    def __init__(self, x, y, width, height, block_type="ground"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.block_type = block_type
        self.hit_from_below = False
        self.coin_given = False

    def draw(self, screen, camera_x):
        x_pos = self.x - camera_x
        if self.block_type == "ground":
            for bx in range(0, self.width, BLOCK_SIZE):
                self.draw_ground_block(screen, x_pos + bx, self.y)
        elif self.block_type == "brick":
            for bx in range(0, self.width, BLOCK_SIZE):
                self.draw_brick_block(screen, x_pos + bx, self.y)
        elif self.block_type == "question":
            self.draw_question_block(screen, x_pos, self.y)

    def draw_ground_block(self, screen, x, y):
        pygame.draw.rect(screen, GROUND_BROWN, (x, y, BLOCK_SIZE, BLOCK_SIZE))
        pygame.draw.line(screen, GROUND_DARK, (x, y), (x + BLOCK_SIZE, y))
        pygame.draw.line(screen, GROUND_DARK, (x, y + BLOCK_SIZE - 1), (x + BLOCK_SIZE, y + BLOCK_SIZE - 1))

    def draw_brick_block(self, screen, x, y):
        pygame.draw.rect(screen, BRICK_RED, (x, y, BLOCK_SIZE, BLOCK_SIZE))
        for i in range(0, BLOCK_SIZE, 8):
            pygame.draw.line(screen, BRICK_DARK, (x, y + i), (x + BLOCK_SIZE, y + i))

    def draw_question_block(self, screen, x, y):
        color = COIN_YELLOW if not self.hit_from_below else GROUND_BROWN
        pygame.draw.rect(screen, color, (x, y, BLOCK_SIZE, BLOCK_SIZE))
        pygame.draw.rect(screen, BLACK, (x, y, BLOCK_SIZE, BLOCK_SIZE), 2)
        if not self.hit_from_below:
            font = pygame.font.Font(None, 24)
            text = font.render("?", True, WHITE)
            screen.blit(text, (x + 11, y + 4))

    def hit(self):
        if self.block_type == "question" and not self.coin_given:
            self.coin_given = True
            self.hit_from_below = True
            coins.append(Coin(self.x + self.width // 2 - COIN_SIZE // 2, self.y - COIN_SIZE - 5))

# Coin class with static design
class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = COIN_SIZE
        self.collected = False

    def update(self):
        pass  # No animation needed

    def draw(self, screen, camera_x):
        if not self.collected:
            x_pos = self.x - camera_x
            pygame.draw.circle(screen, COIN_YELLOW, (x_pos + self.size // 2, self.y + self.size // 2), self.size // 2)
            pygame.draw.circle(screen, COIN_DARK, (x_pos + self.size // 2, self.y + self.size // 2), self.size // 2 - 2)

# Enemy class with simplified design
class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = ENEMY_WIDTH
        self.height = ENEMY_HEIGHT
        self.vel_x = -1
        self.alive = True

    def update(self):
        if self.alive:
            self.x += self.vel_x

    def draw(self, screen, camera_x):
        if self.alive:
            x_pos = self.x - camera_x
            pygame.draw.ellipse(screen, (139, 90, 43), (x_pos, self.y + 8, 32, 24))  # Body
            pygame.draw.ellipse(screen, WHITE, (x_pos + 8, self.y + 12, 6, 8))      # Eyes
            pygame.draw.ellipse(screen, WHITE, (x_pos + 18, self.y + 12, 6, 8))
            pygame.draw.ellipse(screen, BLACK, (x_pos + 10, self.y + 14, 3, 4))
            pygame.draw.ellipse(screen, BLACK, (x_pos + 19, self.y + 14, 3, 4))
            pygame.draw.ellipse(screen, BLACK, (x_pos + 4, self.y + 28, 8, 4))      # Feet
            pygame.draw.ellipse(screen, BLACK, (x_pos + 20, self.y + 28, 8, 4))

# Pipe class (unchanged)
class Pipe:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = PIPE_WIDTH
        self.height = PIPE_HEIGHT

    def draw(self, screen, camera_x):
        x_pos = self.x - camera_x
        pygame.draw.rect(screen, PIPE_GREEN, (x_pos + 4, self.y + 16, self.width - 8, self.height - 16))
        pygame.draw.rect(screen, PIPE_DARK, (x_pos + 4, self.y + 16, 4, self.height - 16))
        pygame.draw.rect(screen, PIPE_DARK, (x_pos + self.width - 8, self.y + 16, 4, self.height - 16))
        pygame.draw.rect(screen, PIPE_GREEN, (x_pos, self.y, self.width, 20))
        pygame.draw.rect(screen, PIPE_DARK, (x_pos, self.y, 4, 20))
        pygame.draw.rect(screen, PIPE_DARK, (x_pos + self.width - 4, self.y, 4, 20))
        pygame.draw.rect(screen, PIPE_DARK, (x_pos, self.y + 16, self.width, 4))

# Flagpole class (unchanged)
class Flagpole:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = FLAGPOLE_WIDTH
        self.height = FLAGPOLE_HEIGHT

    def draw(self, screen, camera_x):
        x_pos = self.x - camera_x
        pygame.draw.rect(screen, GREEN, (x_pos - 16, self.y + self.height - 32, 40, 32))
        pygame.draw.rect(screen, (0, 100, 0), (x_pos - 16, self.y + self.height - 32, 40, 4))
        pygame.draw.rect(screen, (200, 200, 200), (x_pos, self.y, self.width, self.height))
        pygame.draw.circle(screen, (255, 215, 0), (x_pos + self.width // 2, self.y), 8)
        pygame.draw.polygon(screen, GREEN, [
            (x_pos + self.width, self.y + 20),
            (x_pos + self.width + 40, self.y + 35),
            (x_pos + self.width, self.y + 50)
        ])

# Collision detection (unchanged)
def check_collisions():
    global coins_collected, game_state
    mario_rect = pygame.Rect(mario.x, mario.y, mario.width, mario.height)
    mario.on_ground = False
    for platform in platforms:
        platform_rect = pygame.Rect(platform.x, platform.y, platform.width, platform.height)
        if mario_rect.colliderect(platform_rect):
            if mario.vel_y > 0 and mario.y < platform.y:
                mario.y = platform.y - mario.height
                mario.vel_y = 0
                mario.on_ground = True
                mario.jumping = False
            elif mario.vel_y < 0 and mario.y > platform.y:
                mario.y = platform.y + platform.height
                mario.vel_y = 0
                platform.hit()
    for pipe in pipes:
        pipe_rect = pygame.Rect(pipe.x, pipe.y, pipe.width, pipe.height)
        if mario_rect.colliderect(pipe_rect):
            if mario.vel_x > 0 and mario.x < pipe.x:
                mario.x = pipe.x - mario.width
                mario.vel_x = 0
            elif mario.vel_x < 0 and mario.x > pipe.x:
                mario.x = pipe.x + pipe.width
                mario.vel_x = 0
            elif mario.vel_y > 0 and mario.y < pipe.y:
                mario.y = pipe.y - mario.height
                mario.vel_y = 0
                mario.on_ground = True
                mario.jumping = False
    for coin in coins[:]:
        if not coin.collected:
            coin_rect = pygame.Rect(coin.x, coin.y, coin.size, coin.size)
            if mario_rect.colliderect(coin_rect):
                coin.collected = True
                coins_collected += 1
    for enemy in enemies[:]:
        if enemy.alive:
            enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.width, enemy.height)
            if mario_rect.colliderect(enemy_rect):
                if mario.vel_y > 0 and mario.y < enemy.y:
                    enemy.alive = False
                    mario.vel_y = -10
                else:
                    game_state = GAME_OVER
    flagpole_rect = pygame.Rect(flagpole.x - 16, flagpole.y, flagpole.width + 32, flagpole.height)
    if mario_rect.colliderect(flagpole_rect):
        game_state = VICTORY

# Background creation
def create_background():
    bg = pygame.Surface((LEVEL_WIDTH, HEIGHT))
    for i in range(HEIGHT):
        color = (
            SKY_BLUE[0] + (LIGHT_BLUE[0] - SKY_BLUE[0]) * i // HEIGHT,
            SKY_BLUE[1] + (LIGHT_BLUE[1] - SKY_BLUE[1]) * i // HEIGHT,
            SKY_BLUE[2] + (LIGHT_BLUE[2] - SKY_BLUE[2]) * i // HEIGHT
        )
        pygame.draw.line(bg, color, (0, i), (LEVEL_WIDTH, i))
    for cloud_x in range(100, LEVEL_WIDTH, 300):
        draw_cloud(bg, cloud_x, 80)
        draw_cloud(bg, cloud_x + 150, 120)
    return bg

def draw_cloud(surface, x, y):
    pygame.draw.ellipse(surface, WHITE, (x, y, 60, 30))
    pygame.draw.ellipse(surface, WHITE, (x - 20, y + 5, 50, 25))
    pygame.draw.ellipse(surface, WHITE, (x + 30, y + 5, 50, 25))

# Setup function with background
def setup():
    global screen, font, big_font, small_font, mario, platforms, coins, enemies, pipes, flagpole, background
    global game_state, coins_collected, intro_timer, clock, camera_x
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Super Mario - Special 64 Edition")
    font = pygame.font.Font(None, 36)
    big_font = pygame.font.Font(None, 48)
    small_font = pygame.font.Font(None, 24)
    clock = pygame.time.Clock()
    game_state = INTRO
    coins_collected = 0
    intro_timer = 0
    camera_x = 0
    background = create_background()
    mario = Mario(50, 400)
    platforms = [
        Platform(0, 500, LEVEL_WIDTH, 100, "ground"),
        Platform(200, 400, 128, BLOCK_SIZE, "brick"),
        Platform(400, 300, 96, BLOCK_SIZE, "brick"),
        Platform(600, 350, 64, BLOCK_SIZE, "brick"),
        Platform(800, 250, 128, BLOCK_SIZE, "brick"),
        Platform(300, 350, BLOCK_SIZE, BLOCK_SIZE, "question"),
        Platform(500, 250, BLOCK_SIZE, BLOCK_SIZE, "question"),
        Platform(700, 300, BLOCK_SIZE, BLOCK_SIZE, "question"),
        Platform(900, 200, BLOCK_SIZE, BLOCK_SIZE, "question"),
        Platform(1000, 400, 96, BLOCK_SIZE, "brick"),
        Platform(1200, 300, 128, BLOCK_SIZE, "brick"),
        Platform(1400, 350, 96, BLOCK_SIZE, "brick"),
    ]
    coins = [
        Coin(250, 370),
        Coin(450, 270),
        Coin(650, 320),
        Coin(850, 220),
        Coin(1050, 370),
        Coin(1250, 270),
    ]
    enemies = [
        Enemy(300, 468),
        Enemy(500, 468),
        Enemy(700, 468),
        Enemy(1000, 468),
        Enemy(1300, 468),
    ]
    pipes = [
        Pipe(750, 436),
        Pipe(1100, 436),
    ]
    flagpole = Flagpole(1500, 180)

# Update loop with optimized drawing
def update_loop():
    global game_state, intro_timer, camera_x
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if game_state == INTRO and intro_timer > 60:
                game_state = MENU
            elif game_state == MENU and event.key == pygame.K_RETURN:
                game_state = PLAYING
            elif game_state == PLAYING and (event.key == pygame.K_SPACE or event.key == pygame.K_UP):
                mario.jump()
            elif game_state in [GAME_OVER, VICTORY] and event.key == pygame.K_r:
                setup()
                game_state = PLAYING
    if game_state == INTRO:
        intro_timer += 1
        if intro_timer > 180:
            game_state = MENU
    elif game_state == PLAYING:
        keys = pygame.key.get_pressed()
        mario.vel_x = -5 if keys[pygame.K_LEFT] else 5 if keys[pygame.K_RIGHT] else 0
        mario.update()
        for enemy in enemies:
            enemy.update()
        for coin in coins:
            coin.update()
        check_collisions()
        camera_x = max(0, min(mario.x - WIDTH // 2, LEVEL_WIDTH - WIDTH))
    
    # Drawing
    if game_state == INTRO:
        screen.fill(BLACK)
        red_alpha = int(128 + 127 * abs(math.sin(intro_timer * 0.05)))
        red_surface = pygame.Surface((WIDTH, HEIGHT))
        red_surface.set_alpha(red_alpha)
        red_surface.fill(DARK_RED)
        screen.blit(red_surface, (0, 0))
        text1 = big_font.render("TEAM SPECIALEMU AGI Division", True, WHITE)
        text2 = font.render("Presents", True, WHITE)
        special_text = small_font.render("Special 64 Emulator v1.0", True, RED)
        screen.blit(text1, (WIDTH // 2 - text1.get_width() // 2, HEIGHT // 2 - 50))
        screen.blit(text2, (WIDTH // 2 - text2.get_width() // 2, HEIGHT // 2 + 10))
        screen.blit(special_text, (WIDTH // 2 - special_text.get_width() // 2, HEIGHT - 50))
    else:
        screen.blit(background, (0, 0), (camera_x, 0, WIDTH, HEIGHT))
        if game_state == MENU:
            title_text = big_font.render("SUPER MARIO", True, RED)
            subtitle_text = font.render("Special 64 Edition", True, DARK_RED)
            start_text = font.render("Press ENTER to Start", True, BLACK)
            screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 2 - 100))
            screen.blit(subtitle_text, (WIDTH // 2 - subtitle_text.get_width() // 2, HEIGHT // 2 - 40))
            screen.blit(start_text, (WIDTH // 2 - start_text.get_width() // 2, HEIGHT // 2 + 50))
        elif game_state == PLAYING:
            for platform in platforms:
                if platform.x - camera_x < WIDTH and platform.x + platform.width - camera_x > 0:
                    platform.draw(screen, camera_x)
            for pipe in pipes:
                if pipe.x - camera_x < WIDTH and pipe.x + pipe.width - camera_x > 0:
                    pipe.draw(screen, camera_x)
            for coin in coins:
                if coin.x - camera_x < WIDTH and coin.x + coin.size - camera_x > 0:
                    coin.draw(screen, camera_x)
            for enemy in enemies:
                if enemy.x - camera_x < WIDTH and enemy.x + enemy.width - camera_x > 0:
                    enemy.draw(screen, camera_x)
            flagpole.draw(screen, camera_x)
            mario.draw(screen, camera_x)
            coin_text = font.render(f"Coins: {coins_collected}", True, BLACK)
            pygame.draw.rect(screen, WHITE, (8, 8, 140, 30))
            pygame.draw.rect(screen, BLACK, (8, 8, 140, 30), 2)
            screen.blit(coin_text, (15, 10))
        elif game_state == GAME_OVER:
            game_over_text = big_font.render("GAME OVER", True, RED)
            restart_text = font.render("Press R to Restart", True, BLACK)
            screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 50))
            screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 20))
        elif game_state == VICTORY:
            victory_text = big_font.render("VICTORY!", True, GREEN)
            score_text = font.render(f"Coins Collected: {coins_collected}", True, BLACK)
            restart_text = font.render("Press R to Play Again", True, BLACK)
            screen.blit(victory_text, (WIDTH // 2 - victory_text.get_width() // 2, HEIGHT // 2 - 80))
            screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2 - 20))
            screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 40))
    
    pygame.display.flip()
    if clock:
        clock.tick(FPS)

# Main async loop
async def main():
    setup()
    while True:
        update_loop()
        await asyncio.sleep(1.0 / FPS)

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        setup()
        while True:
            update_loop()

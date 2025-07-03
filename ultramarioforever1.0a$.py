import asyncio
import platform
import pygame
import sys

# Constants
WIDTH, HEIGHT = 800, 600
FPS = 60
GRAVITY = 0.5
MARIO_WIDTH, MARIO_HEIGHT = 20, 30
PLATFORM_HEIGHT = 20
COIN_SIZE = 10
ENEMY_WIDTH, ENEMY_HEIGHT = 20, 20
FLAGPOLE_WIDTH, FLAGPOLE_HEIGHT = 10, 100

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
BROWN = (139, 69, 19)

# Game states
MENU, PLAYING, GAME_OVER = 0, 1, 2

# Mario class
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

    def update(self):
        self.vel_y += GRAVITY
        self.y += self.vel_y
        self.x += self.vel_x
        if self.x < 0:
            self.x = 0
        elif self.x + self.width > WIDTH:
            self.x = WIDTH - self.width
        if self.y > HEIGHT:
            global game_state
            game_state = GAME_OVER

    def draw(self, screen):
        pygame.draw.rect(screen, RED, (self.x, self.y, self.width, self.height))

    def jump(self):
        if self.on_ground:
            self.vel_y = -10
            self.jumping = True
            self.on_ground = False

# Platform class
class Platform:
    def __init__(self, x, y, width, height, secret=False):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.secret = secret
        self.visible = not secret

    def draw(self, screen):
        if self.visible:
            pygame.draw.rect(screen, GREEN, (self.x, self.y, self.width, self.height))

    def hit(self):
        if self.secret:
            self.visible = True
            coins.append(Coin(self.x + self.width // 2 - COIN_SIZE // 2, self.y - COIN_SIZE - 5))

# Coin class
class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = COIN_SIZE

    def draw(self, screen):
        pygame.draw.circle(screen, YELLOW, (self.x + self.size // 2, self.y + self.size // 2), self.size // 2)

# Enemy class
class Enemy:
    def __init__(self, x, y, width, height, left_bound, right_bound):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.left_bound = left_bound
        self.right_bound = right_bound
        self.vel_x = 2

    def update(self):
        self.x += self.vel_x
        if self.x <= self.left_bound:
            self.x = self.left_bound
            self.vel_x = 2
        elif self.x + self.width >= self.right_bound:
            self.x = self.right_bound - self.width
            self.vel_x = -2

    def draw(self, screen):
        pygame.draw.rect(screen, BROWN, (self.x, self.y, self.width, self.height))

# Flagpole class
class Flagpole:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def draw(self, screen):
        pygame.draw.rect(screen, BLUE, (self.x, self.y, self.width, self.height))

# Collision detection
def check_collisions():
    global coins_collected
    mario_rect = pygame.Rect(mario.x, mario.y, mario.width, mario.height)
    for platform in platforms:
        platform_rect = pygame.Rect(platform.x, platform.y, platform.width, platform.height)
        if mario_rect.colliderect(platform_rect):
            if mario.vel_y > 0 and mario.y + mario.height - mario.vel_y <= platform.y:
                mario.y = platform.y - mario.height
                mario.vel_y = 0
                mario.on_ground = True
                mario.jumping = False
            elif mario.vel_y < 0 and mario.y - mario.vel_y >= platform.y + platform.height:
                mario.y = platform.y + platform.height
                mario.vel_y = 0
                if platform.secret:
                    platform.hit()
    for coin in coins[:]:
        coin_rect = pygame.Rect(coin.x, coin.y, coin.size, coin.size)
        if mario_rect.colliderect(coin_rect):
            coins.remove(coin)
            coins_collected += 1
    for enemy in enemies[:]:
        enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.width, enemy.height)
        if mario_rect.colliderect(enemy_rect):
            if mario.vel_y > 0 and mario.y + mario.height - mario.vel_y <= enemy.y:
                enemies.remove(enemy)
            else:
                global game_state
                game_state = GAME_OVER
    flagpole_rect = pygame.Rect(flagpole.x, flagpole.y, flagpole.width, flagpole.height)
    if mario_rect.colliderect(flagpole_rect):
        game_state = GAME_OVER  # Ends game for simplicity

# Setup function
def setup():
    global screen, font, mario, platforms, coins, enemies, flagpole, game_state, coins_collected
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    font = pygame.font.Font(None, 36)
    game_state = MENU
    coins_collected = 0
    mario = Mario(50, 470)
    platforms = [
        Platform(0, 500, 800, 100),
        Platform(200, 400, 100, PLATFORM_HEIGHT),
        Platform(400, 300, 100, PLATFORM_HEIGHT),
        Platform(600, 200, 100, PLATFORM_HEIGHT),
        Platform(300, 450, 50, PLATFORM_HEIGHT, secret=True),
    ]
    coins = [
        Coin(250, 380),
        Coin(450, 280),
        Coin(650, 180),
    ]
    enemies = [
        Enemy(300, 480, ENEMY_WIDTH, ENEMY_HEIGHT, 200, 400),
        Enemy(500, 280, ENEMY_WIDTH, ENEMY_HEIGHT, 400, 600),
    ]
    flagpole = Flagpole(750, 400, FLAGPOLE_WIDTH, FLAGPOLE_HEIGHT)

# Update loop
def update_loop():
    global game_state
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if game_state == MENU:
                if event.key == pygame.K_RETURN:
                    game_state = PLAYING
            elif game_state == PLAYING:
                if event.key == pygame.K_SPACE:
                    mario.jump()
            elif game_state == GAME_OVER:
                if event.key == pygame.K_r:
                    setup()
                    game_state = PLAYING
    if game_state == PLAYING:
        keys = pygame.key.get_pressed()
        mario.vel_x = -5 if keys[pygame.K_LEFT] else 5 if keys[pygame.K_RIGHT] else 0
        mario.update()
        for enemy in enemies:
            enemy.update()
        check_collisions()
    screen.fill(WHITE)
    if game_state == MENU:
        text = font.render("Press ENTER to Start", True, BLACK)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))
    elif game_state == PLAYING:
        for platform in platforms:
            platform.draw(screen)
        for coin in coins:
            coin.draw(screen)
        for enemy in enemies:
            enemy.draw(screen)
        flagpole.draw(screen)
        mario.draw(screen)
        text = font.render(f"Coins: {coins_collected}", True, BLACK)
        screen.blit(text, (10, 10))
    elif game_state == GAME_OVER:
        text = font.render("Game Over! Press R to Restart", True, BLACK)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))
    pygame.display.flip()

# Main async loop for Pyodide compatibility
async def main():
    setup()
    while True:
        update_loop()
        await asyncio.sleep(1.0 / FPS)

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())

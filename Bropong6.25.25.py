import asyncio
import platform
import pygame as pg
import random
import numpy as np

FPS = 60
WIDTH, HEIGHT = 800, 600
PADDLE_WIDTH, PADDLE_HEIGHT = 100, 10
BALL_RADIUS = 7
BRICK_WIDTH, BRICK_HEIGHT = 80, 30
BRICK_ROWS, BRICK_COLS = 5, 10
PADDLE_SPEED = 6
BALL_SPEED = 7

pg.init()
screen = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("Breakout with WASD")
clock = pg.time.Clock()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

# Sound generation (simple beep)
def generate_beep(frequency=440, duration=0.1):
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = np.sin(frequency * t * 2 * np.pi)
    tone = (tone * 32767).astype(np.int16)
    sound_array = np.column_stack((tone, tone))  # Stereo
    return pg.sndarray.make_sound(sound_array)

hit_sound = generate_beep(440, 0.1)
brick_sound = generate_beep(880, 0.1)

# Paddle
class Paddle:
    def __init__(self):
        self.rect = pg.Rect(WIDTH // 2 - PADDLE_WIDTH // 2, HEIGHT - 40, PADDLE_WIDTH, PADDLE_HEIGHT)
    
    def move(self, dx):
        self.rect.x += dx
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
    
    def draw(self, screen):
        pg.draw.rect(screen, BLUE, self.rect)

# Ball
class Ball:
    def __init__(self):
        self.rect = pg.Rect(WIDTH // 2, HEIGHT // 2, BALL_RADIUS * 2, BALL_RADIUS * 2)
        self.dx = BALL_SPEED * random.choice([-1, 1])
        self.dy = -BALL_SPEED
    
    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        if self.rect.left < 0 or self.rect.right > WIDTH:
            self.dx = -self.dx
            hit_sound.play()
        if self.rect.top < 0:
            self.dy = -self.dy
            hit_sound.play()
        return self.rect
    
    def draw(self, screen):
        pg.draw.circle(screen, RED, self.rect.center, BALL_RADIUS)

# Brick
class Brick:
    def __init__(self, x, y):
        self.rect = pg.Rect(x, y, BRICK_WIDTH, BRICK_HEIGHT)
    
    def draw(self, screen):
        pg.draw.rect(screen, GREEN, self.rect)

# Game setup
def setup():
    global paddle, ball, bricks, score, lives, game_over, game_won
    paddle = Paddle()
    ball = Ball()
    bricks = [Brick(col * (BRICK_WIDTH + 5) + 35, row * (BRICK_HEIGHT + 5) + 50)
              for row in range(BRICK_ROWS) for col in range(BRICK_COLS)]
    score = 0
    lives = 3
    game_over = False
    game_won = False

# Game loop
def update_loop():
    global score, lives, game_over, game_won
    for event in pg.event.get():
        if event.type == pg.QUIT:
            pg.quit()
            return False
        if event.type == pg.KEYDOWN and (game_over or game_won) and event.key == pg.K_0:
            setup()
    
    if not game_over and not game_won:
        keys = pg.key.get_pressed()
        dx = 0
        if keys[pg.K_a]:
            dx -= PADDLE_SPEED
        if keys[pg.K_d]:
            dx += PADDLE_SPEED
        paddle.move(dx)
        
        ball_rect = ball.update()
        if ball_rect.colliderect(paddle.rect):
            ball.dy = -ball.dy
            hit_sound.play()
        
        for brick in bricks[:]:
            if ball_rect.colliderect(brick.rect):
                ball.dy = -ball.dy
                bricks.remove(brick)
                score += 10
                brick_sound.play()
                break
        
        if ball_rect.bottom > HEIGHT:
            lives -= 1
            if lives == 0:
                game_over = True
            else:
                ball.rect.center = (WIDTH // 2, HEIGHT // 2)
                ball.dx = BALL_SPEED * random.choice([-1, 1])
                ball.dy = -BALL_SPEED
        
        if not bricks:
            game_won = True
    
    screen.fill(BLACK)
    paddle.draw(screen)
    ball.draw(screen)
    for brick in bricks:
        brick.draw(screen)
    
    font = pg.font.SysFont('Arial', 24)
    score_text = font.render(f'Score: {score}', True, WHITE)
    lives_text = font.render(f'Lives: {lives}', True, WHITE)
    screen.blit(score_text, (10, 10))
    screen.blit(lives_text, (WIDTH - 100, 10))
    
    if game_over:
        game_over_text = font.render('Game Over! Press 0 to Restart', True, WHITE)
        screen.blit(game_over_text, (WIDTH // 2 - 150, HEIGHT // 2))
    elif game_won:
        game_won_text = font.render('You Won! Press 0 to Restart', True, WHITE)
        screen.blit(game_won_text, (WIDTH // 2 - 150, HEIGHT // 2))
    
    pg.display.flip()
    clock.tick(FPS)
    return True

async def main():
    setup()
    while update_loop():
        await asyncio.sleep(1.0 / FPS)

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())

import asyncio
import platform
import pygame
import random

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
PADDLE_WIDTH, PADDLE_HEIGHT = 20, 100
BALL_SIZE = 20
PADDLE_SPEED = 5
AI_SPEED = 4
BALL_SPEED_X, BALL_SPEED_Y = 5, 5
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)

# Setup game window
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong Game")

# Initialize game objects
left_paddle = pygame.Rect(50, HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
right_paddle = pygame.Rect(WIDTH - 50 - PADDLE_WIDTH, HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
ball = pygame.Rect(WIDTH // 2 - BALL_SIZE // 2, HEIGHT // 2 - BALL_SIZE // 2, BALL_SIZE, BALL_SIZE)

# Game state
left_score = 0
right_score = 0
game_over = False

# Font setup
font = pygame.font.Font(None, 74)
small_font = pygame.font.Font(None, 36)

# Ball movement
ball_dx, ball_dy = random.choice([-1, 1]) * BALL_SPEED_X, random.choice([-1, 1]) * BALL_SPEED_Y

def reset_ball():
    ball.center = (WIDTH // 2, HEIGHT // 2)
    return random.choice([-1, 1]) * BALL_SPEED_X, random.choice([-1, 1]) * BALL_SPEED_Y

def draw():
    win.fill(BLACK)
    pygame.draw.rect(win, WHITE, left_paddle)
    pygame.draw.rect(win, WHITE, right_paddle)
    pygame.draw.ellipse(win, WHITE, ball)
    pygame.draw.aaline(win, WHITE, (WIDTH // 2, 0), (WIDTH // 2, HEIGHT))
    
    # Display scores
    left_text = font.render(str(left_score), True, WHITE)
    right_text = font.render(str(right_score), True, WHITE)
    win.blit(left_text, (WIDTH // 4, 20))
    win.blit(right_text, (3 * WIDTH // 4, 20))

def game_over_screen():
    win.fill(RED)
    game_over_text = font.render("Game Over!", True, WHITE)
    play_again_text = small_font.render("Play again? (Y/N)", True, WHITE)
    win.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 50))
    win.blit(play_again_text, (WIDTH // 2 - play_again_text.get_width() // 2, HEIGHT // 2 + 50))

def setup():
    global left_score, right_score, game_over, ball_dx, ball_dy
    left_score = 0
    right_score = 0
    game_over = False
    ball_dx, ball_dy = reset_ball()
    left_paddle.center = (50 + PADDLE_WIDTH // 2, HEIGHT // 2)
    right_paddle.center = (WIDTH - 50 - PADDLE_WIDTH // 2, HEIGHT // 2)
    ball.center = (WIDTH // 2, HEIGHT // 2)

def update_loop():
    global ball_dx, ball_dy, left_score, right_score, game_over
    
    if not game_over:
        # Player input
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] and left_paddle.top > 0:
            left_paddle.y -= PADDLE_SPEED
        if keys[pygame.K_s] and left_paddle.bottom < HEIGHT:
            left_paddle.y += PADDLE_SPEED

        # AI movement
        if ball.centery < right_paddle.centery and right_paddle.top > 0:
            right_paddle.y -= AI_SPEED
        if ball.centery > right_paddle.centery and right_paddle.bottom < HEIGHT:
            right_paddle.y += AI_SPEED

        # Ball movement
        ball.x += ball_dx
        ball.y += ball_dy

        # Ball collisions
        if ball.top <= 0 or ball.bottom >= HEIGHT:
            ball_dy *= -1
        if ball.colliderect(left_paddle) or ball.colliderect(right_paddle):
            ball_dx *= -1

        # Scoring
        if ball.left <= 0:
            right_score += 1
            ball_dx, ball_dy = reset_ball()
            pygame.time.delay(1000)
        elif ball.right >= WIDTH:
            left_score += 1
            ball_dx, ball_dy = reset_ball()
            pygame.time.delay(1000)

        # Check game over
        if left_score >= 5 or right_score >= 5:
            game_over = True

        draw()
    else:
        game_over_screen()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_y]:
            setup()
        elif keys[pygame.K_n]:
            pygame.quit()
            raise SystemExit

    pygame.display.flip()

async def main():
    setup()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
        update_loop()
        await asyncio.sleep(1.0 / FPS)

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())

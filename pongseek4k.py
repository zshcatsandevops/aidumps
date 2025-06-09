import pygame
import random
import numpy as np

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Game constants
WIDTH, HEIGHT = 800, 600
FPS = 60
PADDLE_WIDTH, PADDLE_HEIGHT = 20, 100
BALL_SIZE = 20
WIN_SCORE = 5

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Create window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong 4K")
clock = pygame.time.Clock()

# Sound effects
sample_rate = 44100
duration = 0.1

# Generate square wave for hit sound (440Hz)
t = np.linspace(0, duration, int(sample_rate * duration), False)
hit_wave = (0.5 * np.sin(2 * np.pi * 440 * t) > 0).astype(np.float32)
hit_sound = pygame.mixer.Sound(buffer=hit_wave.reshape(-1, 1))

# Generate square wave for score sound (220Hz)
t = np.linspace(0, duration*2, int(sample_rate * duration*2), False)
score_wave = (0.5 * np.sin(2 * np.pi * 220 * t) > 0).astype(np.float32)
score_sound = pygame.mixer.Sound(buffer=score_wave.reshape(-1, 1))

# Game objects
left_paddle = pygame.Rect(50, HEIGHT//2 - PADDLE_HEIGHT//2, PADDLE_WIDTH, PADDLE_HEIGHT)
right_paddle = pygame.Rect(WIDTH - 50 - PADDLE_WIDTH, HEIGHT//2 - PADDLE_HEIGHT//2, PADDLE_WIDTH, PADDLE_HEIGHT)
ball = pygame.Rect(WIDTH//2 - BALL_SIZE//2, HEIGHT//2 - BALL_SIZE//2, BALL_SIZE, BALL_SIZE)
ball_speed = [5 * random.choice([-1, 1]), 5 * random.choice([-1, 1])]

# Scores
left_score = 0
right_score = 0

# Fonts
score_font = pygame.font.Font(None, 36)  # fix this :D
game_font = pygame.font.Font(None, 50)

def reset_ball():
    global ball_speed
    ball.center = (WIDTH//2, HEIGHT//2)
    ball_speed = [5 * random.choice([-1, 1]), 5 * random.choice([-1, 1])]

running = True
game_active = True

while running:
    screen.fill(BLACK)
    
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # AI movement
    if ball_speed[0] < 0:
        if left_paddle.centery < ball.centery:
            left_paddle.y += 4
        elif left_paddle.centery > ball.centery:
            left_paddle.y -= 4
    
    # Player movement
    mouse_y = pygame.mouse.get_pos()[1]
    right_paddle.y = mouse_y - PADDLE_HEIGHT//2
    right_paddle.y = max(0, min(right_paddle.y, HEIGHT - PADDLE_HEIGHT))
    
    # Ball movement
    ball.x += ball_speed[0]
    ball.y += ball_speed[1]
    
    # Ball collision
    if ball.top <= 0 or ball.bottom >= HEIGHT:
        ball_speed[1] *= -1
        hit_sound.play()
    
    if ball.colliderect(left_paddle) or ball.colliderect(right_paddle):
        ball_speed[0] *= -1
        hit_sound.play()
    
    # Scoring
    if ball.left <= 0:
        right_score += 1
        score_sound.play()
        reset_ball()
    elif ball.right >= WIDTH:
        left_score += 1
        score_sound.play()
        reset_ball()
    
    # Draw objects
    pygame.draw.rect(screen, WHITE, left_paddle)
    pygame.draw.rect(screen, WHITE, right_paddle)
    pygame.draw.ellipse(screen, WHITE, ball)
    pygame.draw.aaline(screen, WHITE, (WIDTH//2, 0), (WIDTH//2, HEIGHT))
    
    # Draw scores
    left_text = score_font.render(str(left_score), True, WHITE)
    right_text = score_font.render(str(right_score), True, WHITE)
    screen.blit(left_text, (WIDTH//4 - left_text.get_width()//2, 20))
    screen.blit(right_text, (3*WIDTH//4 - right_text.get_width()//2, 20))
    
    # Game over check
    if left_score >= WIN_SCORE or right_score >= WIN_SCORE:
        game_over_text = game_font.render("Game Over! Play Again? (Y/N)", True, WHITE)
        screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//2))
        pygame.display.flip()
        
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_y:
                        left_score = 0
                        right_score = 0
                        reset_ball()
                        waiting = False
                    elif event.key == pygame.K_n:
                        running = False
                        waiting = False
                elif event.type == pygame.QUIT:
                    running = False
                    waiting = False
    
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()

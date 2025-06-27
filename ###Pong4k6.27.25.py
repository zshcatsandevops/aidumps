import pygame
import sys
import random
import numpy as np  # For sound generation [[4]]

# Initialize Pygame
pygame.mixer.pre_init(44100, -16, 2, 512)  # Audio settings [[4]]
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong with AI")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Game settings
PADDLE_WIDTH, PADDLE_HEIGHT = 10, 100
BALL_SIZE = 15
PADDLE_SPEED = 7
AI_SPEED = 5
BALL_SPEED_X, BALL_SPEED_Y = 5, 3

# Create game objects
left_paddle = pygame.Rect(50, HEIGHT//2 - PADDLE_HEIGHT//2, PADDLE_WIDTH, PADDLE_HEIGHT)
right_paddle = pygame.Rect(WIDTH - 60, HEIGHT//2 - PADDLE_HEIGHT//2, PADDLE_WIDTH, PADDLE_HEIGHT)
ball = pygame.Rect(WIDTH//2 - BALL_SIZE//2, HEIGHT//2 - BALL_SIZE//2, BALL_SIZE, BALL_SIZE)

# Score tracking
left_score = 0
right_score = 0
font = pygame.font.Font(None, 74)

# === Sound Generation ===
def make_square_wave(freq, duration, volume=0.5):
    """Generate Atari-style square wave sound"""
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    buf = np.zeros((n_samples, 2), dtype=np.int16)  # Stereo buffer
    
    for i in range(n_samples):
        t = i / sample_rate
        cycle = (freq * t) % 2
        sample = volume * 32767 if cycle < 1 else -volume * 32767
        buf[i] = [sample, sample]  # Left and right channels
    
    return pygame.sndarray.make_sound(buf)

# Create sound effects
paddle_hit = make_square_wave(freq=1000, duration=0.1, volume=0.5)  # High-pitched beep
score_sound = make_square_wave(freq=440, duration=0.3, volume=0.3)  # Lower boop

# Initial ball movement
ball_dx, ball_dy = BALL_SPEED_X, BALL_SPEED_Y

clock = pygame.time.Clock()

def reset_ball():
    ball.center = (WIDTH//2, HEIGHT//2)
    return [BALL_SPEED_X * (-1 if random.choice([0, 1]) else 1), BALL_SPEED_Y]

# === Main Menu ===
def show_main_menu():
    menu_font = pygame.font.Font(None, 36)
    menu_text = "PONG 1.0. By Qwen [C] @Team Flames 1.0"
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return  # Start the game

        screen.fill(BLACK)
        text_surface = menu_font.render(menu_text, True, WHITE)
        text_rect = text_surface.get_rect(center=(WIDTH//2, HEIGHT - 50))
        screen.blit(text_surface, text_rect)
        pygame.display.flip()
        clock.tick(30)

# Show main menu before starting game
show_main_menu()

# Reset ball after menu
ball_dx, ball_dy = reset_ball()

# === Game Over Screen ===
def show_game_over(winner):
    """Display game over screen and handle restart/quit"""
    game_over_font = pygame.font.Font(None, 48)
    prompt_font = pygame.font.Font(None, 36)
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_y, pygame.K_Y):  # Restart
                    return True
                if event.key in (pygame.K_n, pygame.K_N):  # Quit
                    pygame.quit()
                    sys.exit()

        # Render game over screen
        screen.fill(BLACK)
        game_over_text = game_over_font.render(f"{winner} WINS!", True, WHITE)
        prompt_text = prompt_font.render("Play again? (Y/N)", True, WHITE)
        
        # Center text on screen
        game_over_rect = game_over_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 30))
        prompt_rect = prompt_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 20))
        
        screen.blit(game_over_text, game_over_rect)
        screen.blit(prompt_text, prompt_rect)
        pygame.display.flip()
        clock.tick(30)

# === Game Loop ===
while True:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Left paddle - mouse control
    left_paddle.y = pygame.mouse.get_pos()[1] - PADDLE_HEIGHT//2
    left_paddle.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))  # Keep within bounds

    # Right paddle - AI control
    if right_paddle.centery < ball.y:
        right_paddle.y += AI_SPEED
    elif right_paddle.centery > ball.y:
        right_paddle.y -= AI_SPEED
    right_paddle.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))  # Keep within bounds

    # Ball movement
    ball.x += ball_dx
    ball.y += ball_dy

    # Ball collision with top/bottom
    if ball.top <= 0 or ball.bottom >= HEIGHT:
        ball_dy *= -1

    # Ball collision with paddles
    if ball.colliderect(left_paddle) or ball.colliderect(right_paddle):
        ball_dx *= -1.1  # Add acceleration
        ball.x += ball_dx  # Prevent sticking
        paddle_hit.play()  # Play beep [[4]]

    # Scoring
    if ball.left <= 0:
        right_score += 1
        score_sound.play()  # Play boop [[4]]
        if right_score >= 5:  # Check for game over
            if show_game_over("RIGHT"):  # Restart if Y pressed
                left_score = right_score = 0
                ball_dx, ball_dy = reset_ball()
                continue  # Skip rest of loop and restart
        ball_dx, ball_dy = reset_ball()
        
    elif ball.right >= WIDTH:
        left_score += 1
        score_sound.play()  # Play boop [[4]]
        if left_score >= 5:  # Check for game over
            if show_game_over("LEFT"):  # Restart if Y pressed
                left_score = right_score = 0
                ball_dx, ball_dy = reset_ball()
                continue  # Skip rest of loop and restart
        ball_dx, ball_dy = reset_ball()

    # Drawing
    screen.fill(BLACK)
    pygame.draw.rect(screen, WHITE, left_paddle)
    pygame.draw.rect(screen, WHITE, right_paddle)
    pygame.draw.ellipse(screen, WHITE, ball)
    pygame.draw.aaline(screen, WHITE, (WIDTH//2, 0), (WIDTH//2, HEIGHT))

    # Display scores
    left_text = font.render(f"{left_score}", True, WHITE)
    right_text = font.render(f"{right_score}", True, WHITE)
    screen.blit(left_text, (WIDTH//4, 20))
    screen.blit(right_text, (WIDTH*3//4, 20))

    pygame.display.flip()
    clock.tick(60)

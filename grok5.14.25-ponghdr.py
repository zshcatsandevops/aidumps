import asyncio
import platform
import pygame
import random
import numpy as np

# Initialize Pygame and Mixer
pygame.init()
pygame.mixer.init(frequency=44100)  # Set sample rate to 44100 Hz for sound

# Set up the window
WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Paddles and ball
left_paddle = pygame.Rect(50, HEIGHT // 2 - 50, 20, 100)
right_paddle = pygame.Rect(WIDTH - 70, HEIGHT // 2 - 50, 20, 100)
ball = pygame.Rect(WIDTH // 2 - 10, HEIGHT // 2 - 10, 20, 20)

# Initial velocities and speeds
ball_dx = 5
ball_dy = random.choice([-5, -4, -3, -2, -1, 1, 2, 3, 4, 5])
paddle_speed = 10
ai_paddle_speed = 5  # Slightly slower than player for balance

# Scores
left_score = 0
right_score = 0

# Font for scores
font = pygame.font.SysFont(None, 36)

# Ball reset control
can_move_ball = True
ball_reset_time = 0

# Sound effects (defined at module level)
hit_paddle_sound = None
hit_wall_sound = None
score_sound = None

FPS = 60

# Function to generate a simple sine wave sound for stereo
def generate_sound(freq, duration):
    sample_rate = 44100
    samples = int(sample_rate * duration)
    t = np.linspace(0, duration, samples, False)
    wave = 0.5 * np.sin(2 * np.pi * freq * t)
    wave_int = (wave * 32767).astype(np.int16)  # Convert to 16-bit integer
    # Create a 2D array for stereo: duplicate mono signal for both channels
    stereo_wave = np.column_stack((wave_int, wave_int))
    return pygame.sndarray.make_sound(stereo_wave)

def setup():
    global ball_dx, ball_dy, can_move_ball, ball_reset_time
    global hit_paddle_sound, hit_wall_sound, score_sound
    # Reset initial conditions
    ball.center = (WIDTH // 2, HEIGHT // 2)
    ball_dx = 5
    ball_dy = random.choice([-5, -4, -3, -2, -1, 1, 2, 3, 4, 5])
    can_move_ball = True
    ball_reset_time = 0
    # Initialize sound effects
    hit_paddle_sound = generate_sound(440, 0.1)  # 440 Hz tone for paddle hit
    hit_wall_sound = generate_sound(220, 0.1)    # 220 Hz tone for wall hit
    score_sound = generate_sound(660, 0.2)       # 660 Hz tone for scoring

def update_loop():
    global ball_dx, ball_dy, left_score, right_score, can_move_ball, ball_reset_time

    # Handle key presses for left paddle (player)
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        left_paddle.y -= paddle_speed
    if keys[pygame.K_s]:
        left_paddle.y += paddle_speed

    # AI control for right paddle
    if ball.y < right_paddle.centery:
        right_paddle.y -= ai_paddle_speed
    elif ball.y > right_paddle.centery:
        right_paddle.y += ai_paddle_speed

    # Clamp paddle positions
    left_paddle.y = max(0, min(left_paddle.y, HEIGHT - left_paddle.height))
    right_paddle.y = max(0, min(right_paddle.y, HEIGHT - right_paddle.height))

    # Update ball position if can_move_ball
    if can_move_ball:
        ball.x += ball_dx
        ball.y += ball_dy

        # Check for collisions with top and bottom
        if ball.top <= 0 or ball.bottom >= HEIGHT:
            ball_dy = -ball_dy
            hit_wall_sound.play()

        # Check for collisions with paddles
        if ball_dx < 0 and ball.colliderect(left_paddle):
            ball_dx = -ball_dx
            hit_paddle_sound.play()
        elif ball_dx > 0 and ball.colliderect(right_paddle):
            ball_dx = -ball_dx
            hit_paddle_sound.play()

        # Check for scoring
        if ball.left < 0:
            right_score += 1
            ball.center = (WIDTH // 2, HEIGHT // 2)
            ball_dx = -5  # towards left
            ball_dy = random.choice([-5, -4, -3, -2, -1, 1, 2, 3, 4, 5])
            can_move_ball = False
            ball_reset_time = pygame.time.get_ticks() + 1000
            score_sound.play()
        elif ball.right > WIDTH:
            left_score += 1
            ball.center = (WIDTH // 2, HEIGHT // 2)
            ball_dx = 5  # towards right
            ball_dy = random.choice([-5, -4, -3, -2, -1, 1, 2, 3, 4, 5])
            can_move_ball = False
            ball_reset_time = pygame.time.get_ticks() + 1000
            score_sound.play()
    else:
        # Check if reset time has passed
        if pygame.time.get_ticks() > ball_reset_time:
            can_move_ball = True

    # Draw everything
    screen.fill(BLACK)
    pygame.draw.rect(screen, WHITE, left_paddle)
    pygame.draw.rect(screen, WHITE, right_paddle)
    pygame.draw.rect(screen, WHITE, ball)

    # Draw scores
    left_score_text = font.render(str(left_score), True, WHITE)
    right_score_text = font.render(str(right_score), True, WHITE)
    screen.blit(left_score_text, (100, 50))
    screen.blit(right_score_text, (WIDTH - 100, 50))

    pygame.display.flip()

async def main():
    setup()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
        update_loop()
        await asyncio.sleep(1.0 / FPS)

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())

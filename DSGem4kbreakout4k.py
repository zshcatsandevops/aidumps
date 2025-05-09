import pygame
import random
import math
import numpy as np

# Initialize Pygame
pygame.init()

# Audio settings
SAMPLE_RATE = 44100  # Hz – must match mixer frequency below
pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512)

def generate_sound(frequency: float, duration: float, wave_type: str = "sine", volume: float = 0.5) -> pygame.mixer.Sound:
    """Generate a short procedural sound matching the current mixer settings.

    Args:
        frequency: Pitch in Hz.
        duration: Length of the sound in seconds.
        wave_type: 'sine' or 'square'.
        volume: 0‑1 linear volume multiplier.

    Returns:
        pygame.mixer.Sound object ready to play.
    """
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)

    if wave_type == "square":
        wave = np.where(np.sin(2 * np.pi * frequency * t) >= 0, 1.0, -1.0)
    else:  # default to sine
        wave = np.sin(2 * np.pi * frequency * t)

    wave *= volume
    samples = np.int16(wave * 32767)

    # Ensure the NumPy array shape matches the number of mixer channels
    mixer_settings = pygame.mixer.get_init()
    channels = mixer_settings[2] if mixer_settings else 1
    if channels == 2:
        samples = np.column_stack((samples, samples))  # duplicate mono signal into L/R

    return pygame.sndarray.make_sound(samples)

# Game sound effects
hit_paddle_sound = generate_sound(880, 0.1)
hit_brick_sound = generate_sound(440, 0.08, "square")
lose_life_sound = generate_sound(220, 0.3)
level_complete_sound = generate_sound(1760, 0.5)

# Game constants
WIDTH, HEIGHT = 800, 600
PADDLE_WIDTH, PADDLE_HEIGHT = 120, 20
BALL_SIZE = 15
BRICK_ROWS, BRICK_COLS = 6, 12
COLORS = [
    (255, 0, 0), (255, 165, 0), (255, 255, 0),
    (0, 255, 0), (0, 0, 255), (75, 0, 130)
]

# Setup display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SynthBreakout")
clock = pygame.time.Clock()

# Dynamic color system
def hue_shift(angle: float) -> tuple[int, int, int]:
    r = math.sin(angle) * 127 + 128
    g = math.sin(angle + 2) * 127 + 128
    b = math.sin(angle + 4) * 127 + 128
    return int(r), int(g), int(b)

# Game objects
class Paddle:
    def __init__(self):
        self.x = float(WIDTH // 2 - PADDLE_WIDTH // 2)
        self.rect = pygame.Rect(int(self.x), HEIGHT - 50, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.speed = 400
        self.color = (255, 255, 255)

class Ball:
    def __init__(self):
        self.rect = pygame.Rect(0, 0, BALL_SIZE, BALL_SIZE)
        self.base_speed = 300
        self.trail_points: list[tuple[tuple[int, int], float]] = []
        self.x = 0.0
        self.y = 0.0
        self.dx = 0.0
        self.dy = 0.0
        self.reset()

    def reset(self):
        self.x = float(WIDTH // 2 - BALL_SIZE // 2)
        self.y = float(HEIGHT // 2 - BALL_SIZE // 2)
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

        angle = random.uniform(math.pi * 0.25, math.pi * 0.75)
        self.dx = self.base_speed * math.cos(angle) * random.choice([-1, 1])
        self.dy = -self.base_speed * math.sin(angle)

class Brick:
    def __init__(self, x: int, y: int, color: tuple[int, int, int]):
        self.rect = pygame.Rect(x, y, 60, 25)
        self.color = color
        self.active = True

def create_bricks() -> list[Brick]:
    return [
        Brick(10 + col * 65, 50 + row * 30, COLORS[row % len(COLORS)])
        for row in range(BRICK_ROWS)
        for col in range(BRICK_COLS)
    ]

# Initialize game state
paddle = Paddle()
ball = Ball()
bricks = create_bricks()
hue_angle = 0.0
phase_shift = 0.0
score = 0
lives = 3

font = pygame.font.Font(None, 36)

# Main game loop
running = True
while running:
    dt = clock.tick(60) / 1000.0

    hue_angle += 0.02
    phase_shift += 0.1

    # Handle input
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        paddle.x = max(0.0, paddle.x - paddle.speed * dt)
    if keys[pygame.K_RIGHT]:
        paddle.x = min(WIDTH - PADDLE_WIDTH, paddle.x + paddle.speed * dt)
    paddle.rect.x = int(paddle.x)

    # Move ball
    ball.x += ball.dx * dt
    ball.y += ball.dy * dt
    ball.rect.x = int(ball.x)
    ball.rect.y = int(ball.y)

    # Trail effect
    ball.trail_points.insert(0, (ball.rect.center, phase_shift))
    if len(ball.trail_points) > 15:
        ball.trail_points.pop()

    # Wall collisions
    if ball.rect.left <= 0:
        ball.rect.left = 0
        ball.x = float(ball.rect.x)
        ball.dx *= -1
    elif ball.rect.right >= WIDTH:
        ball.rect.right = WIDTH
        ball.x = float(ball.rect.x)
        ball.dx *= -1
    if ball.rect.top <= 0:
        ball.rect.top = 0
        ball.y = float(ball.rect.y)
        ball.dy *= -1

    # Paddle collision
    if ball.rect.colliderect(paddle.rect) and ball.dy > 0:
        hit_paddle_sound.play()
        ball.y = float(paddle.rect.top - BALL_SIZE)
        ball.rect.y = int(ball.y)
        offset = (ball.rect.centerx - paddle.rect.centerx) / (PADDLE_WIDTH / 2.0)
        bounce = offset * (math.pi / 3.0)
        speed = math.hypot(ball.dx, ball.dy) or ball.base_speed
        ball.dx = speed * math.sin(bounce)
        ball.dy = -speed * math.cos(bounce)

    # Brick collisions
    for brick in bricks:
        if brick.active and ball.rect.colliderect(brick.rect):
            hit_brick_sound.play()
            brick.active = False
            score += 10
            # Determine collision side
            overlap_x = (
                ball.rect.right - brick.rect.left if ball.dx > 0 else brick.rect.right - ball.rect.left
            )
            overlap_y = (
                ball.rect.bottom - brick.rect.top if ball.dy > 0 else brick.rect.bottom - ball.rect.top
            )
            if abs(overlap_x) < abs(overlap_y):
                ball.dx *= -1
                ball.x = float(brick.rect.left - BALL_SIZE if ball.dx < 0 else brick.rect.right)
            else:
                ball.dy *= -1
                ball.y = float(brick.rect.top - BALL_SIZE if ball.dy < 0 else brick.rect.bottom)
            ball.rect.x, ball.rect.y = int(ball.x), int(ball.y)
            break

    # Bottom out
    if ball.rect.bottom > HEIGHT:
        lose_life_sound.play()
        lives -= 1
        if lives > 0:
            ball.reset()
        else:
            running = False

    # Level complete
    if lives > 0 and not any(b.active for b in bricks):
        level_complete_sound.play()
        ball.base_speed *= 1.1
        bricks = create_bricks()
        ball.reset()

    # Drawing
    screen.fill((0, 0, 0))

    # Draw trail
    for i, (pos, phase) in enumerate(ball.trail_points):
        alpha = max(0, 255 - i * 17)
        color = hue_shift(phase)
        radius = max(1, BALL_SIZE // 2 + i // 3)
        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*color, alpha), (radius, radius), radius)
        screen.blit(surf, (pos[0] - radius, pos[1] - radius))

    pygame.draw.rect(screen, hue_shift(phase_shift), paddle.rect.inflate(6, 6), 4)
    pygame.draw.rect(screen, paddle.color, paddle.rect)
    pygame.draw.ellipse(screen, hue_shift(-phase_shift), ball.rect)

    for brick in bricks:
        if brick.active:
            pygame.draw.rect(screen, brick.color, brick.rect)
            pygame.draw.rect(screen, (255, 255, 255), brick.rect.inflate(-2, -2), 2)

    # HUD
    screen.blit(font.render(f"Score: {score}", True, hue_shift(phase_shift + 1)), (10, 10))
    lives_surf = font.render(f"Lives: {lives}", True, hue_shift(phase_shift + 2))
    screen.blit(lives_surf, (WIDTH - lives_surf.get_width() - 10, 10))

    pygame.display.flip()

pygame.quit()

import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Game constants
WIDTH, HEIGHT = 800, 600
PADDLE_WIDTH, PADDLE_HEIGHT = 120, 20
BALL_SIZE = 15
BRICK_ROWS, BRICK_COLS = 6, 12
COLORS = [(255, 0, 0), (255, 165, 0), (255, 255, 0),
          (0, 255, 0), (0, 0, 255), (75, 0, 130)]

# Setup display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SynthBreakout")
clock = pygame.time.Clock()

# Dynamic color system
def hue_shift(angle):
    r = math.sin(angle) * 127 + 128
    g = math.sin(angle + 2) * 127 + 128
    b = math.sin(angle + 4) * 127 + 128
    return (int(r), int(g), int(b))

# Game objects
class Paddle:
    def __init__(self):
        self.x = float(WIDTH//2 - PADDLE_WIDTH//2)  # Float position
        self.rect = pygame.Rect(int(self.x), HEIGHT - 50,
                                PADDLE_WIDTH, PADDLE_HEIGHT)
        self.speed = 400  # Speed in pixels per second (e.g., 8 pixels/frame * 60fps-ish)
        self.color = (255, 255, 255)

class Ball:
    def __init__(self):
        self.rect = pygame.Rect(0, 0, BALL_SIZE, BALL_SIZE) # Create rect once
        self.base_speed = 300  # Speed in pixels per second (e.g., 5 pixels/frame * 60 fps)
        self.trail_points = []
        self.x = 0.0  # Float position for x
        self.y = 0.0  # Float position for y
        self.dx = 0.0 # Speed component for x (pixels/sec)
        self.dy = 0.0 # Speed component for y (pixels/sec)
        self.reset() # Call reset to initialize positions and speeds

    def reset(self):
        self.x = float(WIDTH//2 - BALL_SIZE//2)
        self.y = float(HEIGHT//2 - BALL_SIZE//2)
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        
        # dx and dy are now speeds in pixels/second
        angle = random.uniform(math.pi * 0.25, math.pi * 0.75) # Angle between 45 and 135 degrees
        self.dx = self.base_speed * math.cos(angle) * random.choice([-1,1])
        self.dy = -self.base_speed * math.sin(angle) # Initially upwards

class Brick:
    def __init__(self, x, y, color):
        self.rect = pygame.Rect(x, y, 60, 25)
        self.color = color
        self.active = True

def create_bricks():
    return [Brick(10 + col*65, 50 + row*30, COLORS[row % len(COLORS)])
            for row in range(BRICK_ROWS) 
            for col in range(BRICK_COLS)]

# Game initialization
paddle = Paddle()
ball = Ball()
bricks = create_bricks()
hue_angle = 0

# Game loop
running = True
score = 0
lives = 3
phase_shift = 0

while running:
    dt = clock.tick(60) / 1000
    hue_angle += 0.02
    phase_shift += 0.1
    
    # Handle input
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        paddle.x -= paddle.speed * dt
        if paddle.x < 0: paddle.x = 0.0
        paddle.rect.x = int(paddle.x)
    if keys[pygame.K_RIGHT]:
        paddle.x += paddle.speed * dt
        if paddle.x + PADDLE_WIDTH > WIDTH: paddle.x = float(WIDTH - PADDLE_WIDTH)
        paddle.rect.x = int(paddle.x)

    # Ball movement
    ball.x += ball.dx * dt
    ball.y += ball.dy * dt
    ball.rect.x = int(ball.x)
    ball.rect.y = int(ball.y)
    
    # Store trail points with dynamic alpha
    ball.trail_points.insert(0, (ball.rect.center, phase_shift))
    if len(ball.trail_points) > 15:
        ball.trail_points.pop()

    # Wall collisions
    if ball.rect.left <= 0 or ball.rect.right >= WIDTH:
        ball.dx *= -1
    if ball.rect.top <= 0:
        ball.dy *= -1
        
    # Paddle collision
    if ball.rect.colliderect(paddle.rect):
        ball.y = float(paddle.rect.top - BALL_SIZE) # Place ball on top of paddle
        ball.rect.y = int(ball.y)
        ball.dy = -abs(ball.dy) # Reverse vertical direction
        # More sophisticated bounce angle based on hit position
        offset = (ball.rect.centerx - paddle.rect.centerx) / (PADDLE_WIDTH / 2.0)
        # Max bounce angle of ~60 degrees (pi/3 radians)
        bounce_angle_rad = offset * (math.pi / 3.0) 
        # Maintain current speed magnitude
        current_speed_magnitude = math.sqrt(ball.dx**2 + ball.dy**2)
        if current_speed_magnitude == 0: # Avoid division by zero if ball somehow stopped
            current_speed_magnitude = ball.base_speed
        ball.dx = current_speed_magnitude * math.sin(bounce_angle_rad)
        ball.dy = -current_speed_magnitude * math.cos(bounce_angle_rad) # Negative because Y is downwards

    # Brick collisions
    for brick in bricks:
        if brick.active and ball.rect.colliderect(brick.rect):
            brick.active = False
            score += 10
            
            # Calculate collision side
            overlap_x = (ball.rect.right - brick.rect.left) if ball.dx > 0 else (brick.rect.right - ball.rect.left)
            overlap_y = (ball.rect.bottom - brick.rect.top) if ball.dy > 0 else (brick.rect.bottom - ball.rect.top)
            
            if abs(overlap_x) < abs(overlap_y):
                ball.dx *= -1
            else:
                ball.dy *= -1

    # Ball reset
    if ball.rect.bottom > HEIGHT:
        lives -= 1
        if lives > 0:
            ball.reset()
            # bricks = create_bricks()  # Removed: Do not reset bricks on life loss
        else:
            running = False

    # Level progression
    if not any(brick.active for brick in bricks):
        ball.base_speed *= 1.1
        bricks = create_bricks()
        ball.reset()

    # Dynamic drawing
    screen.fill((0, 0, 0))

    # Draw trail with proper alpha blending
    for i, (pos, phase) in enumerate(ball.trail_points):
        alpha = 255 - i*15
        trail_color = hue_shift(phase)
        radius = BALL_SIZE//2 + i//3
        trail_surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        pygame.draw.circle(trail_surf, (*trail_color, alpha), (radius, radius), radius)
        screen.blit(trail_surf, (pos[0]-radius, pos[1]-radius))

    # Draw paddle
    pygame.draw.rect(screen, hue_shift(phase_shift), paddle.rect.inflate(6, 6), 4)
    pygame.draw.rect(screen, paddle.color, paddle.rect)

    # Draw ball
    pygame.draw.ellipse(screen, hue_shift(-phase_shift), ball.rect)

    # Draw bricks
    for brick in bricks:
        if brick.active:
            pygame.draw.rect(screen, brick.color, brick.rect)
            pygame.draw.rect(screen, (255, 255, 255), brick.rect.inflate(-2, -2), 2)

    # UI Elements
    font = pygame.font.Font(None, 36)
    score_text = font.render(f"Score: {score}", True, hue_shift(phase_shift + 1))
    lives_text = font.render(f"Lives: {lives}", True, hue_shift(phase_shift + 2))
    screen.blit(score_text, (10, 10))
    screen.blit(lives_text, (WIDTH - 150, 10))

    pygame.display.flip()

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

pygame.quit()

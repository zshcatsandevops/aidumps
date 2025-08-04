 import tkinter as tk
import pygame
import random
import numpy as np

# Initialize Pygame for graphics and sound
pygame.init()
pygame.mixer.pre_init(44100, -16, 2, 128)  # Stereo, 44.1 kHz, 16-bit
pygame.mixer.init()

# Tkinter window setup
root = tk.Tk()
root.title("Breakout - PS3 Vibes Stereo Edition")a
canvas = tk.Canvas(root, width=800, height=600, bg="black")
canvas.pack()
pygame_surface = pygame.Surface((800, 600))
clock = pygame.time.Clock()

# PS3-inspired colors
BALL_COLOR = (255, 50, 50)  # Neon red
PADDLE_COLOR = (0, 255, 100)  # Electric green
BRICK_COLORS = [(255, 100, 100), (100, 255, 100), (100, 100, 255)]  # PS3 palette
BRICK_ROWS, BRICK_COLS = 5, 10
BRICK_WIDTH, BRICK_HEIGHT = 75, 30

# Game objects
paddle = pygame.Rect(350, 550, 100, 10)
ball = pygame.Rect(400, 300, 10, 10)
ball_speed = [5, -5]
bricks = [pygame.Rect(col * (BRICK_WIDTH + 5) + 25, row * (BRICK_HEIGHT + 5) + 50, BRICK_WIDTH, BRICK_HEIGHT)
          for row in range(BRICK_ROWS) for col in range(BRICK_COLS)]

# PS3-style stereo SFX
def create_ps3_sfx(freq: int, duration: float, sr: int = 44100) -> pygame.mixer.Sound:
    """Return a stereo square-wave sound of <duration> seconds at <freq> Hz."""
    samples = int(sr * duration)
    t = np.arange(samples, dtype=np.float32)
    mono_wave = (np.sign(np.sin(2 * np.pi * freq * t / sr)) * 12000).astype(np.int16)
    stereo_wave = np.repeat(mono_wave[:, None], 2, axis=1)  # Duplicate for L & R
    return pygame.sndarray.make_sound(stereo_wave)

hit_sfx = create_ps3_sfx(800, 0.1)  # Sharp paddle hit
brick_sfx = create_ps3_sfx(600, 0.15)  # Deeper brick break
wall_sfx = create_ps3_sfx(400, 0.1)  # Wall bounce

# Game loop
score = 0
running = True

def game_loop():
    global running, score, ball_speed
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Paddle movement
    mouse_x = root.winfo_pointerx() - root.winfo_rootx()
    paddle.x = max(0, min(mouse_x - 50, 700))

    # Ball movement
    ball.x += ball_speed[0]
    ball.y += ball_speed[1]

    # Collisions
    if ball.left <= 0 or ball.right >= 800:
        ball_speed[0] = -ball_speed[0]
        wall_sfx.play()
    if ball.top <= 0:
        ball_speed[1] = -ball_speed[1]
        wall_sfx.play()
    if ball.bottom >= 600:
        running = False  # Game over
    if ball.colliderect(paddle):
        ball_speed[1] = -ball_speed[1]
        ball_speed[0] += random.uniform(-1, 1)  # Add spin
        hit_sfx.play()

    # Brick collisions
    for brick in bricks[:]:
        if ball.colliderect(brick):
            bricks.remove(brick)
            ball_speed[1] = -ball_speed[1]
            score += 10
            brick_sfx.play()
            break

    # Draw
    pygame_surface.fill((0, 0, 0))  # Black background
    pygame.draw.rect(pygame_surface, PADDLE_COLOR, paddle)
    pygame.draw.circle(pygame_surface, BALL_COLOR, ball.center, 5)
    for i, brick in enumerate(bricks):
        pygame.draw.rect(pygame_surface, BRICK_COLORS[i % len(BRICK_COLORS)], brick)

    # Convert Pygame surface to Tkinter
    raw_data = pygame.image.tostring(pygame_surface, "RGB")
    img = tk.PhotoImage(data=raw_data)
    canvas.create_image(0, 0, image=img, anchor="nw")
    canvas.image = img  # Keep reference

    # Score display
    canvas.create_text(50, 20, text=f"Score: {score}", fill="white", font=("Arial", 14))

    if running:
        root.after(16, game_loop)  # ~60 FPS
    else:
        canvas.create_text(400, 300, text=f"Game Over! Score: {score}", fill="white", font=("Arial", 24))
    clock.tick(60)

# Start game
game_loop()
root.mainloop()
pygame.quit()

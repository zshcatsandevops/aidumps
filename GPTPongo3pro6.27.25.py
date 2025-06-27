#!/usr/bin/env python3
"""
test.py ― Classic Pong in one pure‑Python file using Pygame
----------------------------------------------------------

Rules implemented
* Left paddle: simple AI that tracks the ball with a max speed (not perfect)
* Right paddle: controlled only by the mouse Y position
* 60 FPS smooth play, Atari‑2600‑style black & white visuals
* Procedural “beep” (paddle hit) and “boop” (score) sounds generated in code
* First to 11 points wins

Run with:
    $ python test.py
"""

import math
import random
import struct
import sys
from array import array

import pygame

# --------------------------------------------------------------------------- #
# Configuration constants
# --------------------------------------------------------------------------- #
WIDTH, HEIGHT = 800, 600
FPS            = 60

PADDLE_W       = 10
PADDLE_H       = 80
PADDLE_MARGIN  = 30
AI_MAX_SPEED   = 6           # px per frame the AI can move

BALL_SIZE      = 12
BALL_SPEED     = 6           # initial speed (pixels / frame)

WIN_SCORE      = 11

BG_COLOR       = (0, 0, 0)   # black
FG_COLOR       = (255, 255, 255)  # white

SAMPLE_RATE    = 44100       # Hz
SOUND_VOL      = 0.4

# --------------------------------------------------------------------------- #
# Utility: Procedural sound synthesis
# --------------------------------------------------------------------------- #
def synth_tone(freq: float, ms: int = 120, volume: float = SOUND_VOL):
    """
    Generate a short square‑wave tone as a pygame.Sound object, no external files.
    """
    n_samples = int(SAMPLE_RATE * ms / 1000)
    buf = array("h")
    amplitude = int(volume * 32767)
    samples_per_cycle = SAMPLE_RATE / freq

    for i in range(n_samples):
        # Square wave: high half the cycle, low the other half
        if (i % samples_per_cycle) < (samples_per_cycle / 2):
            sample = amplitude
        else:
            sample = -amplitude
        buf.append(sample)

    return pygame.mixer.Sound(buffer=buf.tobytes())

# --------------------------------------------------------------------------- #
# Game objects
# --------------------------------------------------------------------------- #
class Paddle:
    def __init__(self, x, is_player: bool):
        self.x = x
        self.y = HEIGHT // 2 - PADDLE_H // 2
        self.is_player = is_player

    @property
    def rect(self):
        return pygame.Rect(self.x, int(self.y), PADDLE_W, PADDLE_H)

    def move_ai(self, target_y):
        center = self.y + PADDLE_H / 2
        if center < target_y - 5:
            self.y += min(AI_MAX_SPEED, target_y - center)
        elif center > target_y + 5:
            self.y -= min(AI_MAX_SPEED, center - target_y)
        # clamp to screen
        self.y = max(0, min(self.y, HEIGHT - PADDLE_H))

    def move_player(self, mouse_y):
        self.y = mouse_y - PADDLE_H / 2
        self.y = max(0, min(self.y, HEIGHT - PADDLE_H))

class Ball:
    def __init__(self):
        self.reset()

    def reset(self, direction=None):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        angle = random.uniform(-0.35, 0.35)  # radians off horizontal
        speed = BALL_SPEED
        # Choose direction: -1 = left, 1 = right
        dir_sign = random.choice([-1, 1]) if direction is None else direction
        self.vx = speed * math.cos(angle) * dir_sign
        self.vy = speed * math.sin(angle)

    @property
    def rect(self):
        return pygame.Rect(int(self.x - BALL_SIZE / 2),
                           int(self.y - BALL_SIZE / 2),
                           BALL_SIZE, BALL_SIZE)

    def update(self):
        self.x += self.vx
        self.y += self.vy

        # Top / bottom wall bounce
        if self.y < BALL_SIZE / 2:
            self.y = BALL_SIZE / 2
            self.vy *= -1
        elif self.y > HEIGHT - BALL_SIZE / 2:
            self.y = HEIGHT - BALL_SIZE / 2
            self.vy *= -1

# --------------------------------------------------------------------------- #
# Main game
# --------------------------------------------------------------------------- #
def main():
    # ‑‑ Pygame init ‑‑ #
    pygame.mixer.pre_init(SAMPLE_RATE, -16, 1, 512)
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Classic Pong")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 56)

    # Sounds
    beep = synth_tone(880, 80)   # paddle hit
    boop = synth_tone(220, 140)  # score

    # Game objects
    left_paddle  = Paddle(PADDLE_MARGIN, is_player=False)
    right_paddle = Paddle(WIDTH - PADDLE_MARGIN - PADDLE_W, is_player=True)
    ball = Ball()

    score_left  = 0
    score_right = 0
    running     = True
    game_over   = False

    # ‑‑ Main loop ‑‑ #
    while running:
        dt = clock.tick(FPS)

        # ----- Event handling ----- #
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Early exit once someone wins
        if game_over:
            draw_end_screen(screen, font, score_left, score_right)
            pygame.display.flip()
            continue  # skip updates

        # ----- Input ----- #
        _, mouse_y = pygame.mouse.get_pos()

        # ----- Update objects ----- #
        right_paddle.move_player(mouse_y)
        left_paddle.move_ai(ball.y)

        ball.update()

        # Paddle collisions
        if ball.rect.colliderect(left_paddle.rect):
            ball.x = left_paddle.rect.right + BALL_SIZE / 2
            ball.vx = abs(ball.vx)
            beep.play()
        elif ball.rect.colliderect(right_paddle.rect):
            ball.x = right_paddle.rect.left - BALL_SIZE / 2
            ball.vx = -abs(ball.vx)
            beep.play()

        # Scoring
        if ball.x < 0:
            score_right += 1
            boop.play()
            ball.reset(direction=-1)
        elif ball.x > WIDTH:
            score_left += 1
            boop.play()
            ball.reset(direction=1)

        # Check win
        if score_left >= WIN_SCORE or score_right >= WIN_SCORE:
            game_over = True

        # ----- Render ----- #
        screen.fill(BG_COLOR)

        # Center dotted net
        for y in range(0, HEIGHT, 30):
            pygame.draw.rect(screen, FG_COLOR,
                             (WIDTH // 2 - 2, y + 5, 4, 20))

        # Paddles & ball
        pygame.draw.rect(screen, FG_COLOR, left_paddle.rect)
        pygame.draw.rect(screen, FG_COLOR, right_paddle.rect)
        pygame.draw.ellipse(screen, FG_COLOR, ball.rect)

        # Score
        score_text = font.render(f"{score_left}   {score_right}", True, FG_COLOR)
        text_rect = score_text.get_rect(center=(WIDTH // 2, 50))
        screen.blit(score_text, text_rect)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def draw_end_screen(screen, font, left, right):
    screen.fill(BG_COLOR)
    winner = "AI WINS!" if left > right else "YOU WIN!"
    msg1 = font.render(winner, True, FG_COLOR)
    msg2 = font.render(f"Final Score {left}–{right}", True, FG_COLOR)
    rect1 = msg1.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40))
    rect2 = msg2.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
    screen.blit(msg1, rect1)
    screen.blit(msg2, rect2)

# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    main()

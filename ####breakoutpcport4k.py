#!/usr/bin/env python3
"""
Beep\u202Fn\u202FBoop\u202FBreakout\u00a0\u2013 Switch\u202F2 Mouse Vibes (Black & White Edition)
Author\u00a0: OpenAI\u00a0o3\nVersion : 1.0\u00a0(2025\u201106\u201130)

• Pointer\u2011style paddle: follow the mouse X like a Joy\u2011Con.
• Click to launch; play entire game with the mouse (P/Y/Q keys optional).
• Pure code\u2011drawn retro graphics (scan\u2011line CRT overlay toggleable with **C**).
• Built\u2011in \u201cbeep\u201d (paddle/\u200bwall) and \u201cboop\u201d (brick) SFX generated on the fly.
• 60\u00a0FPS, immediate start, quick restart (R\u2011click), graceful exit (Q/Esc).
(BLACK & WHITE PALETTE)
"""

import math
import random
import sys
from array import array
from typing import List

import pygame

# —— Static configuration ———————————————————
WIDTH, HEIGHT      = 640, 480
FPS                = 60

PADDLE_W, PADDLE_H = 80, 12
BALL_SZ            = 8

BRICK_COLS         = 10
BRICK_ROWS         = 6
BRICK_W            = WIDTH // BRICK_COLS
BRICK_H            = 18

LIVES              = 3

WHITE              = (245, 245, 245)
GRAY               = (50, 50, 50)
BLACK              = (0, 0, 0)
LIGHT_GRAY         = (180, 180, 180)
BG_COLOR           = (12, 12, 12)
FONT_NAME          = pygame.font.get_default_font()

# —— Helpers ———————————————————

def generate_tone(freq: int, ms: int, volume: float = 0.4, sr: int = 44100) -> pygame.mixer.Sound:
    """Generate a short sine\u2011wave tone without external libs."""
    samples = int(sr * ms / 1000)
    buf = array("h")
    amp = int(volume * 32767)
    for i in range(samples):
        v = int(math.sin(2 * math.pi * freq * (i / sr)) * amp)
        buf.append(v)
    return pygame.mixer.Sound(buffer=buf.tobytes())


def draw_center_text(surf: pygame.Surface, msg: str, size: int, y_offset: int = 0):
    font = pygame.font.Font(FONT_NAME, size)
    txt  = font.render(msg, True, WHITE)
    rect = txt.get_rect(center=(WIDTH // 2, HEIGHT // 2 + y_offset))
    surf.blit(txt, rect)


def new_ball_vel() -> List[int]:
    """Return a random initial velocity for a fresh serve."""
    angle = random.uniform(-math.pi / 4, math.pi / 4)  # \u00b145\u00b0
    speed = 5
    return [speed * math.cos(angle), -speed * math.sin(angle)]


def build_bricks() -> List[pygame.Rect]:
    bricks: List[pygame.Rect] = []
    for r in range(BRICK_ROWS):
        for c in range(BRICK_COLS):
            bricks.append(pygame.Rect(c * BRICK_W, 50 + r * BRICK_H, BRICK_W, BRICK_H))
    return bricks


def build_crt_mask() -> pygame.Surface:
    mask = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    mask.fill((0, 0, 0, 0))
    for y in range(0, HEIGHT, 4):
        pygame.draw.line(mask, (0, 0, 0, 50), (0, y), (WIDTH, y))
    return mask

# —— Main game ——————————————————

def main():
    pygame.init()
    try:
        pygame.mixer.init()
        beep = generate_tone(880, 60)
        boop = generate_tone(440, 80)
    except pygame.error:
        beep = boop = None  # Sound unavailable

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Beep n Boop Breakout – Switch\u202F2 Mouse Vibes (BW)")
    clock = pygame.time.Clock()
    crt_mask = build_crt_mask()
    crt_on   = True

    paddle = pygame.Rect(WIDTH // 2 - PADDLE_W // 2, HEIGHT - 40, PADDLE_W, PADDLE_H)
    ball   = pygame.Rect(0, 0, BALL_SZ, BALL_SZ)
    ball.center = paddle.centerx, paddle.top - BALL_SZ
    ball_vel = [0, 0]
    attached = True  # Ball stuck to paddle before launch

    bricks = build_bricks()
    lives  = LIVES
    paused = False
    game_over = False
    won   = False

    # —— Loop ——————————————————
    while True:
        clock.tick(FPS)

        # —— Events ————————————————
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    pygame.quit(); sys.exit()
                if event.key == pygame.K_p and not game_over:
                    paused = not paused
                if event.key == pygame.K_y:
                    # Hard reset
                    bricks = build_bricks()
                    lives  = LIVES
                    game_over = False
                    won = False
                    attached = True
                    paddle.centerx = WIDTH // 2
                    ball.center = paddle.centerx, paddle.top - BALL_SZ
                    ball_vel = [0, 0]
                    paused = False
                if event.key == pygame.K_c:
                    crt_on = not crt_on

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # L\u2011click \u2192 launch
                    if attached and not game_over and not paused:
                        ball_vel = new_ball_vel()
                        attached = False
                elif event.button == 3:  # R\u2011click quick restart (when over)
                    if game_over:
                        bricks = build_bricks()
                        lives  = LIVES
                        game_over = False
                        won = False
                        attached = True
                        paddle.centerx = WIDTH // 2
                        ball.center = paddle.centerx, paddle.top - BALL_SZ
                        ball_vel = [0, 0]

        # —— Update ————————————————
        if not paused and not game_over:
            mx, _ = pygame.mouse.get_pos()
            paddle.centerx = mx
            # Keep paddle inside bounds
            paddle.left = max(paddle.left, 0)
            paddle.right = min(paddle.right, WIDTH)

            if attached:
                ball.centerx = paddle.centerx
                ball.bottom = paddle.top
            else:
                # Move ball
                ball.x += int(ball_vel[0])
                ball.y += int(ball_vel[1])

                # Wall collisions
                if ball.left <= 0 or ball.right >= WIDTH:
                    ball_vel[0] *= -1
                    if beep: beep.play()
                if ball.top <= 0:
                    ball_vel[1] *= -1
                    if beep: beep.play()

                # Paddle collision
                if ball.colliderect(paddle) and ball_vel[1] > 0:
                    # Reflect based on hit position
                    offset = (ball.centerx - paddle.centerx) / (PADDLE_W / 2)
                    angle  = offset * (math.pi / 3)  # \u00b160\u00b0
                    speed  = math.hypot(*ball_vel)
                    ball_vel[0] = speed * math.sin(angle)
                    ball_vel[1] = -abs(speed * math.cos(angle))
                    if beep: beep.play()

                # Brick collisions
                hit_index = ball.collidelist(bricks)
                if hit_index != -1:
                    hit_brick = bricks.pop(hit_index)
                    # Determine bounce direction (simple)
                    if abs(ball.centerx - hit_brick.left) < 4 or abs(ball.centerx - hit_brick.right) < 4:
                        ball_vel[0] *= -1
                    else:
                        ball_vel[1] *= -1
                    if boop: boop.play()

                # Lose life
                if ball.top > HEIGHT:
                    lives -= 1
                    if lives > 0:
                        attached = True
                        ball.center = paddle.centerx, paddle.top - BALL_SZ
                        ball_vel = [0, 0]
                    else:
                        game_over = True
                        won = False

                # Win check
                if not bricks:
                    game_over = True
                    won = True

        # —— Draw ————————————————
        screen.fill(BG_COLOR)

        # Bricks
        for b in bricks:
            # Alternate two gray levels
            col = WHITE if (b.y // BRICK_H) % 2 == 0 else LIGHT_GRAY
            pygame.draw.rect(screen, col, b.inflate(-2, -2))

        # Paddle & ball
        pygame.draw.rect(screen, WHITE, paddle)
        pygame.draw.rect(screen, WHITE, ball)

        # HUD
        font = pygame.font.Font(FONT_NAME, 24)
        hud  = font.render(f"Lives: {lives}", True, WHITE)
        screen.blit(hud, (10, 10))

        # Pause overlay
        if paused:
            draw_center_text(screen, "PAUSED", 48)

        # Game\u2011over overlay
        if game_over:
            msg = "YOU WIN!" if won else "GAME OVER"
            draw_center_text(screen, msg, 48, -40)
            draw_center_text(screen, "Left\u2011click or Y to restart", 24, 20)
            draw_center_text(screen, "Q / Esc to quit", 24, 50)

        # CRT mask
        if crt_on:
            screen.blit(crt_mask, (0, 0))

        pygame.display.flip()

# —— Entrypoint ——————————————————
if __name__ == "__main__":
    main()

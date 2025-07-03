#!/usr/bin/env python3
"""
Minimal‑but‑groovy Snake for Pygame (with a tiny Tkinter pop‑up on game‑over).

• One file, no external images (“only vibes”).
• Fixed window: 600 × 400 px.
• “Vibe mode” = animated rainbow background + snake whose colour cycles.
"""

import sys, random, math, pygame
import tkinter as tk
from tkinter import messagebox

# ────────────────────────────────────────────────────────────
# CONFIGURATION
WIDTH, HEIGHT          = 600, 400
CELL                   = 20                           # size of each grid cell
FPS                    = 12                           # base speed
VIBE_MODE              = True                        # dynamic colours
# ────────────────────────────────────────────────────────────

GRID_W, GRID_H = WIDTH // CELL, HEIGHT // CELL

# Tkinter root kept hidden; we only need messagebox:
tk_root = tk.Tk()
tk_root.withdraw()

pygame.init()
screen  = pygame.display.set_mode((WIDTH, HEIGHT))
clock   = pygame.time.Clock()
font    = pygame.font.SysFont("consolas", 18)

def hsv2rgb(h, s, v):
    """NaN‑free HSV→RGB (floats 0‑1 → ints 0‑255)."""
    i   = int(h * 6); f = h * 6 - i
    p,q,t = v*(1-s), v*(1-f*s), v*(1-(1-f)*s)
    i%=6
    r,g,b = ((v,t,p),(q,v,p),(p,v,t),(p,q,v),(t,p,v),(v,p,q))[i]
    return int(r*255), int(g*255), int(b*255)

def draw_rect(pos, colour):
    x, y = pos
    pygame.draw.rect(screen, colour, (x*CELL, y*CELL, CELL, CELL))

def rand_cell():
    return random.randrange(GRID_W), random.randrange(GRID_H)

def game_over(score):
    messagebox.showinfo("Snake", f"Game over!\nScore: {score}")
    pygame.quit()
    sys.exit()

def main():
    snake = [(GRID_W//2, GRID_H//2)]
    direction = (1, 0)                     # start moving right
    apple = rand_cell()
    frame = 0                              # counts ticks for vibe maths

    while True:
        # ─── Event handling ──────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN:
                if   event.key in (pygame.K_w, pygame.K_UP)    and direction!=(0,1):  direction=(0,-1)
                elif event.key in (pygame.K_s, pygame.K_DOWN)  and direction!=(0,-1): direction=(0,1)
                elif event.key in (pygame.K_a, pygame.K_LEFT)  and direction!=(1,0):  direction=(-1,0)
                elif event.key in (pygame.K_d, pygame.K_RIGHT) and direction!=(-1,0): direction=(1,0)

        # ─── Move snake ──────────────────────────────────────────────────
        head_x, head_y = snake[0]
        dx, dy         = direction
        new_head       = ((head_x + dx) % GRID_W, (head_y + dy) % GRID_H)

        # Collision with self?
        if new_head in snake:
            game_over(len(snake) - 1)

        snake.insert(0, new_head)

        # Apple eaten?
        if new_head == apple:
            while apple in snake:          # place new apple on free cell
                apple = rand_cell()
        else:
            snake.pop()

        # ─── Drawing ─────────────────────────────────────────────────────
        if VIBE_MODE:
            # Background cycles through hues; speed tied to frame count.
            bg_colour = hsv2rgb((frame * 0.005) % 1.0, 0.6, 0.25)
            screen.fill(bg_colour)
        else:
            screen.fill((30, 30, 30))

        # Draw apple
        draw_rect(apple, (220, 50, 50))

        # Draw snake with colour gradient (head brighter)
        for idx, segment in enumerate(snake):
            if VIBE_MODE:
                hue = ((frame*0.02) + idx/len(snake)) % 1.0
                colour = hsv2rgb(hue, 0.8, 0.9 - idx*0.5/len(snake))
            else:
                shade = 200 - idx*5
                colour = (shade, shade, shade)
            draw_rect(segment, colour)

        # Score
        score_surf = font.render(f"Score: {len(snake) - 1}", True, (255, 255, 255))
        screen.blit(score_surf, (6, 6))

        pygame.display.flip()
        clock.tick(FPS + len(snake)//5)    # speed up as snake grows
        frame += 1

if __name__ == "__main__":
    main()

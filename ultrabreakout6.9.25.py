#!/usr/bin/env python3
"""
Simple Breakout clone in Tkinter – test.py

Controls
--------
Move the mouse left/right anywhere over the window to control the paddle.

Gameplay
--------
Clear all bricks to win. Ball speeds up slightly after each paddle hit.
A couple of basic "beeps" play when the ball hits the paddle or bricks
(using winsound on Windows or system bell fallback elsewhere).
"""

import sys
import random
import platform
import tkinter as tk
import math

# -----------------------------------------------------------------------------#
# Sound helpers – "beeps & boops" without external media
# -----------------------------------------------------------------------------#
def _beep(frequency=880, duration=80):
    """
    Cross‑platform best‑effort beep:
    * On Windows, use winsound.Beep for real tones.
    * Elsewhere, fallback to the terminal bell (prints '\a').
    """
    if platform.system() == "Windows":
        try:
            import winsound

            winsound.Beep(int(frequency), int(duration))
        except Exception:
            # Fallback to bell
            print("\a", end='', flush=True)
    else:
        # Tk has 'bell' but it is often silent; we try terminal bell first.
        print("\a", end='', flush=True)


def brick_beep():
    _beep(1046, 60)  # C6


def paddle_beep():
    _beep(880, 60)   # A5


# -----------------------------------------------------------------------------#
# Game constants
# -----------------------------------------------------------------------------#
CANVAS_W, CANVAS_H = 800, 600
PADDLE_W, PADDLE_H = 100, 15
PADDLE_Y_OFFSET = 40          # distance from bottom
BALL_SIZE = 14
BRICK_ROWS = 5
BRICK_COLS = 10
BRICK_GAP = 4
BRICK_TOP_OFFSET = 60
BALL_SPEED = 4.5              # initial pixels per frame
SPEEDUP_FACTOR = 1.05         # ball accelerates per paddle hit
FPS = 60                      # frames per second

# Colors reminiscent of the original cabinet palette
BRICK_COLORS = ["#ff595e", "#ffca3a", "#8ac926", "#1982c4", "#6a4c93"]


# -----------------------------------------------------------------------------#
# Game objects
# -----------------------------------------------------------------------------#
class Paddle:
    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas
        x0 = (CANVAS_W - PADDLE_W) / 2
        y0 = CANVAS_H - PADDLE_Y_OFFSET
        self.id = canvas.create_rectangle(
            x0, y0, x0 + PADDLE_W, y0 + PADDLE_H,
            fill="#eeeeee", outline="#cccccc"
        )

    def move_to(self, x):
        """Move paddle centre to given x, clamped to canvas edges."""
        half = PADDLE_W / 2
        x = max(half, min(CANVAS_W - half, x))
        coords = self.canvas.coords(self.id)
        current_x = (coords[0] + coords[2]) / 2
        dx = x - current_x
        self.canvas.move(self.id, dx, 0)

    def bbox(self):
        return self.canvas.bbox(self.id)


class Ball:
    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas
        x0 = CANVAS_W / 2 - BALL_SIZE / 2
        y0 = CANVAS_H / 2 - BALL_SIZE / 2
        self.id = canvas.create_oval(
            x0, y0, x0 + BALL_SIZE, y0 + BALL_SIZE,
            fill="#ffffff", outline="#dddddd"
        )
        angle = random.uniform(30, 150)
        self.vx = BALL_SPEED * random.choice([-1, 1]) * abs(math.cos(math.radians(angle)))
        self.vy = -BALL_SPEED  # start upwards

    def move(self):
        self.canvas.move(self.id, self.vx, self.vy)

    def coords(self):
        return self.canvas.coords(self.id)

    def bounce_x(self):
        self.vx = -self.vx

    def bounce_y(self):
        self.vy = -self.vy

    def speed_up(self):
        self.vx *= SPEEDUP_FACTOR
        self.vy *= SPEEDUP_FACTOR

    def centre(self):
        x0, y0, x1, y1 = self.coords()
        return (x0 + x1) / 2, (y0 + y1) / 2


class Brick:
    def __init__(self, canvas: tk.Canvas, row, col):
        self.canvas = canvas
        bw = (CANVAS_W - (BRICK_COLS + 1) * BRICK_GAP) / BRICK_COLS
        bh = 20
        x0 = BRICK_GAP + col * (bw + BRICK_GAP)
        y0 = BRICK_TOP_OFFSET + row * (bh + BRICK_GAP)
        x1, y1 = x0 + bw, y0 + bh
        color = BRICK_COLORS[row % len(BRICK_COLORS)]
        self.id = canvas.create_rectangle(
            x0, y0, x1, y1,
            fill=color, outline="#333333"
        )

    def bbox(self):
        return self.canvas.bbox(self.id)

    def destroy(self):
        self.canvas.delete(self.id)


# -----------------------------------------------------------------------------#
# Main Game class
# -----------------------------------------------------------------------------#
class Breakout:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.canvas = tk.Canvas(root, width=CANVAS_W, height=CANVAS_H, bg="#000000")
        self.canvas.pack()
        root.resizable(False, False)
        
        # Game state: 'menu', 'playing', 'game_over'
        self.game_state = 'menu'
        self.show_main_menu()

    def show_main_menu(self, event=None):
        """Displays the main menu screen."""
        self.running = False
        self.game_state = 'menu'
        self.canvas.delete("all")
        self.root.title("ULTRA!BREAKOUT")
        
        # Menu Texts
        self.canvas.create_text(
            CANVAS_W / 2, CANVAS_H / 3,
            fill="#ffca3a", font=("Terminal", 48, "bold"),
            text="ULTRA!BREAKOUT"
        )
        self.canvas.create_text(
            CANVAS_W / 2, CANVAS_H / 2 + 50,
            fill="#ffffff", font=("Helvetica", 16, "bold"),
            text="Press Enter to Start"
        )
        self.canvas.create_text(
            CANVAS_W / 2, CANVAS_H - 50,
            fill="#cccccc", font=("Courier", 12),
            text="[C] Team Flames 20XX"
        )
        self.canvas.create_text(
            CANVAS_W / 2, CANVAS_H - 30,
            fill="#cccccc", font=("Courier", 12),
            text="[C] Atari 199X"
        )
        
        # Bind enter key to start the game
        self.root.bind("<Return>", self.start_game)

    def start_game(self, event=None):
        """Initializes game elements and starts the game loop."""
        if self.game_state != 'playing':
            self.game_state = 'playing'
            self.root.unbind("<Return>") # Unbind to avoid restarts
            self.canvas.delete("all")
            self.root.title("Breakout in Tkinter – mouse to play")

            # Initialize objects
            self.paddle = Paddle(self.canvas)
            self.ball = Ball(self.canvas)
            self.bricks = []
            for r in range(BRICK_ROWS):
                for c in range(BRICK_COLS):
                    self.bricks.append(Brick(self.canvas, r, c))

            # HUD
            self.score = 0
            self.score_text = self.canvas.create_text(
                8, 8, anchor="nw", fill="#ffffff",
                font=("Helvetica", 14, "bold"),
                text=f"Score: {self.score}"
            )

            # Bind mouse motion
            self.canvas.bind("<Motion>", self.on_mouse)

            # Start game loop
            self.running = True
            self.loop()

    # ---------------------------------------------------------------------#
    # Event handlers
    # ---------------------------------------------------------------------#
    def on_mouse(self, event):
        self.paddle.move_to(event.x)

    # ---------------------------------------------------------------------#
    # Game loop
    # ---------------------------------------------------------------------#
    def loop(self):
        if self.running:
            self.update()
            self.root.after(int(1000 / FPS), self.loop)

    def update(self):
        """Advance one frame."""
        self.ball.move()
        self.handle_collisions()
        self.check_game_over()

    # ---------------------------------------------------------------------#
    # Collision detection
    # ---------------------------------------------------------------------#
    def handle_collisions(self):
        bx0, by0, bx1, by1 = self.ball.coords()

        # Wall collisions
        if bx0 <= 0 or bx1 >= CANVAS_W:
            self.ball.bounce_x()
        if by0 <= 0:
            self.ball.bounce_y()

        # Paddle collision
        if self._hit(self.paddle.bbox(), self.ball.coords()) and self.ball.vy > 0:
            self.ball.bounce_y()
            self.ball.speed_up()
            paddle_beep()

        # Brick collisions
        hit_brick = None
        for brick in self.bricks:
            if self._hit(brick.bbox(), self.ball.coords()):
                hit_brick = brick
                break
        if hit_brick:
            hit_brick.destroy()
            self.bricks.remove(hit_brick)
            self.ball.bounce_y()
            brick_beep()
            self.score += 100
            self.canvas.itemconfigure(self.score_text, text=f"Score: {self.score}")

        # Bottom (miss)
        if by1 >= CANVAS_H:
            self.game_over("Game Over!")

    @staticmethod
    def _hit(bbox1, bbox2):
        """Axis‑aligned rectangle collision."""
        if not bbox1 or not bbox2:
            return False
        x0, y0, x1, y1 = bbox1
        a0, b0, a1, b1 = bbox2
        return (x0 < a1 and x1 > a0 and y0 < b1 and y1 > b0)

    # ---------------------------------------------------------------------#
    # Game state checks
    # ---------------------------------------------------------------------#
    def check_game_over(self):
        if not self.bricks:
            self.game_over("YOU WIN!")

    def game_over(self, message):
        self.running = False
        self.game_state = 'game_over'
        self.canvas.create_text(
            CANVAS_W / 2, CANVAS_H / 2,
            fill="#ffffff", font=("Helvetica", 32, "bold"),
            text=message
        )
        self.canvas.create_text(
            CANVAS_W / 2, CANVAS_H / 2 + 40,
            fill="#999999", font=("Helvetica", 16),
            text="Press Enter to return to Menu."
        )
        _beep(659, 200)  # final tone
        # Bind enter to return to menu
        self.root.bind("<Return>", self.show_main_menu)


# -----------------------------------------------------------------------------#
# Entry point
# -----------------------------------------------------------------------------#
if __name__ == "__main__":
    root = tk.Tk()
    Breakout(root)
    root.mainloop()

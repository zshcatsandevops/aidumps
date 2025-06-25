import tkinter as tk
import random
import sys
import platform

if sys.platform == 'win32':
    import winsound
elif sys.platform == 'darwin':
    import os
else:
    import os
    import threading
    import time

FIELD_WIDTH = 600
FIELD_HEIGHT = 400
PADDLE_WIDTH = 80
PADDLE_HEIGHT = 16
BALL_SIZE = 12
BRICK_ROWS = 5
BRICKS_PER_ROW = 10
BRICK_WIDTH = 52
BRICK_HEIGHT = 20
BALL_SPEED = 5
MAX_LIVES = 3
FPS = 60

NEON_BLUE = '#00eaff'
NEON_PINK = '#ff39c9'
NEON_GREEN = '#48ff59'
NEON_YELLOW = '#fffb41'
NEON_ORANGE = '#ff912d'
BG_COLOR = '#16171d'

# ---- AUDIO ---
def play_beep(freq, dur):
    if sys.platform == 'win32':
        try:
            winsound.Beep(int(freq), int(dur*1000))
        except:
            pass
    elif sys.platform == 'darwin':
        # macOS: no beep by freq, use system beep (quick)
        os.system('afplay /System/Library/Sounds/Pop.aiff &')
    else:
        # Linux, try beep command if available (background)
        def linux_beep():
            try:
                os.system(f'beep -f {freq} -l {int(dur*1000)} 2>/dev/null')
            except:
                sys.stdout.write('\a')
                sys.stdout.flush()
        threading.Thread(target=linux_beep, daemon=True).start()

class BreakoutGame:
    def __init__(self, master):
        self.master = master
        self.master.title("Breakout – Tkinter Atari Edition")
        self.canvas = tk.Canvas(master, width=FIELD_WIDTH, height=FIELD_HEIGHT, bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack()
        self.running = False
        self.menu_mode = True
        self.lives = MAX_LIVES
        self.score = 0
        self.high_score = 0
        self.paddle = None
        self.ball = None
        self.ball_dx = 0
        self.ball_dy = 0
        self.bricks = []
        self.after_id = None

        master.bind('<Left>', lambda e: self.move_paddle(-1))
        master.bind('<Right>', lambda e: self.move_paddle(1))
        master.bind('a', lambda e: self.move_paddle(-1))
        master.bind('d', lambda e: self.move_paddle(1))
        master.bind('<space>', self.start_game)
        master.bind('q', lambda e: master.destroy())
        master.protocol("WM_DELETE_WINDOW", master.destroy)

        self.draw_menu()

    def draw_menu(self):
        self.menu_mode = True
        self.canvas.delete('all')
        self.canvas.create_text(FIELD_WIDTH//2, 90, text="BREAKOUT", font=("Consolas", 52, "bold"), fill=NEON_PINK)
        self.canvas.create_text(FIELD_WIDTH//2, 145, text="Atari TTY Edition (Tkinter)", font=("Consolas", 22), fill=NEON_BLUE)
        self.canvas.create_text(FIELD_WIDTH//2, 210, text="[SPACE] Start", font=("Consolas", 20), fill=NEON_GREEN)
        self.canvas.create_text(FIELD_WIDTH//2, 240, text="[Q] Quit", font=("Consolas", 20), fill=NEON_YELLOW)
        if self.high_score > 0:
            self.canvas.create_text(FIELD_WIDTH//2, 310, text=f"High Score: {self.high_score}", font=("Consolas", 18), fill=NEON_GREEN)

    def start_game(self, event=None):
        if not self.menu_mode:
            return
        self.menu_mode = False
        self.lives = MAX_LIVES
        self.score = 0
        self.setup_level()
        self.running = True
        self.game_loop()

    def setup_level(self):
        self.canvas.delete('all')
        self.paddle_x = FIELD_WIDTH//2 - PADDLE_WIDTH//2
        self.paddle = self.canvas.create_rectangle(
            self.paddle_x, FIELD_HEIGHT - 30,
            self.paddle_x + PADDLE_WIDTH, FIELD_HEIGHT - 30 + PADDLE_HEIGHT,
            fill=NEON_BLUE, outline=NEON_BLUE
        )
        self.ball_x = FIELD_WIDTH//2
        self.ball_y = FIELD_HEIGHT//2
        self.ball_dx = random.choice([-BALL_SPEED, BALL_SPEED])
        self.ball_dy = -BALL_SPEED
        self.ball = self.canvas.create_oval(
            self.ball_x, self.ball_y,
            self.ball_x + BALL_SIZE, self.ball_y + BALL_SIZE,
            fill=NEON_PINK, outline=NEON_PINK
        )
        self.bricks = []
        self.colors = [NEON_ORANGE, NEON_YELLOW, NEON_GREEN, NEON_PINK, NEON_BLUE]
        for row in range(BRICK_ROWS):
            for col in range(BRICKS_PER_ROW):
                x = 10 + col * (BRICK_WIDTH + 7)
                y = 25 + row * (BRICK_HEIGHT + 5)
                color = self.colors[row % len(self.colors)]
                brick = self.canvas.create_rectangle(
                    x, y, x + BRICK_WIDTH, y + BRICK_HEIGHT,
                    fill=color, outline=BG_COLOR
                )
                self.bricks.append((brick, x, y, x + BRICK_WIDTH, y + BRICK_HEIGHT, color, (BRICK_ROWS-row)*10))
        self.hud_text = self.canvas.create_text(10, FIELD_HEIGHT-5, anchor='sw',
            text=f"Score: {self.score}  Lives: {'♥'*self.lives}", font=("Consolas", 18), fill=NEON_GREEN)

    def move_paddle(self, direction):
        if not self.running:
            return
        dx = direction * 20
        new_x = self.paddle_x + dx
        if 0 <= new_x <= FIELD_WIDTH - PADDLE_WIDTH:
            self.paddle_x = new_x
            self.canvas.coords(
                self.paddle,
                self.paddle_x, FIELD_HEIGHT - 30,
                self.paddle_x + PADDLE_WIDTH, FIELD_HEIGHT - 30 + PADDLE_HEIGHT
            )

    def game_loop(self):
        if not self.running:
            return
        self.ball_x += self.ball_dx
        self.ball_y += self.ball_dy
        self.canvas.coords(
            self.ball,
            self.ball_x, self.ball_y,
            self.ball_x + BALL_SIZE, self.ball_y + BALL_SIZE
        )
        if self.ball_x <= 0 or self.ball_x + BALL_SIZE >= FIELD_WIDTH:
            self.ball_dx *= -1
            play_beep(600, 0.04)
        if self.ball_y <= 0:
            self.ball_dy *= -1
            play_beep(900, 0.03)
        paddle_top = FIELD_HEIGHT - 30
        if (self.ball_y + BALL_SIZE >= paddle_top and
            self.paddle_x <= self.ball_x + BALL_SIZE//2 <= self.paddle_x + PADDLE_WIDTH and
            self.ball_dy > 0):
            self.ball_dy *= -1
            hit_pos = (self.ball_x + BALL_SIZE//2 - self.paddle_x) / PADDLE_WIDTH
            self.ball_dx = BALL_SPEED * (2 * hit_pos - 1)
            play_beep(800, 0.05)
        for i, (brick, x1, y1, x2, y2, color, points) in enumerate(self.bricks):
            bx, by = self.ball_x + BALL_SIZE//2, self.ball_y + BALL_SIZE//2
            if x1 <= bx <= x2 and y1 <= by <= y2:
                self.canvas.delete(brick)
                self.ball_dy *= -1
                self.score += points
                play_beep(1200, 0.03)
                del self.bricks[i]
                break
        if self.ball_y > FIELD_HEIGHT:
            self.lives -= 1
            play_beep(300, 0.12)
            if self.lives > 0:
                self.ball_x = FIELD_WIDTH//2
                self.ball_y = FIELD_HEIGHT//2
                self.ball_dx = random.choice([-BALL_SPEED, BALL_SPEED])
                self.ball_dy = -BALL_SPEED
                self.canvas.coords(
                    self.ball,
                    self.ball_x, self.ball_y,
                    self.ball_x + BALL_SIZE, self.ball_y + BALL_SIZE
                )
            else:
                self.running = False
                self.high_score = max(self.score, self.high_score)
                self.draw_game_over()
                return
        if not self.bricks:
            self.running = False
            self.high_score = max(self.score, self.high_score)
            self.draw_victory()
            return
        self.canvas.itemconfig(self.hud_text,
            text=f"Score: {self.score}  Lives: {'♥'*self.lives}")
        self.after_id = self.master.after(int(1000/FPS), self.game_loop)

    def draw_game_over(self):
        self.canvas.create_rectangle(FIELD_WIDTH//2-130, FIELD_HEIGHT//2-70, FIELD_WIDTH//2+130, FIELD_HEIGHT//2+70,
            fill=BG_COLOR, outline=NEON_PINK, width=4)
        self.canvas.create_text(FIELD_WIDTH//2, FIELD_HEIGHT//2-40, text="GAME OVER", font=("Consolas", 36, "bold"), fill=NEON_PINK)
        self.canvas.create_text(FIELD_WIDTH//2, FIELD_HEIGHT//2, text=f"Score: {self.score}", font=("Consolas", 22), fill=NEON_GREEN)
        self.canvas.create_text(FIELD_WIDTH//2, FIELD_HEIGHT//2+38, text=f"[SPACE] Retry  [Q] Quit", font=("Consolas", 18), fill=NEON_YELLOW)
        self.menu_mode = True

    def draw_victory(self):
        self.canvas.create_rectangle(FIELD_WIDTH//2-130, FIELD_HEIGHT//2-70, FIELD_WIDTH//2+130, FIELD_HEIGHT//2+70,
            fill=BG_COLOR, outline=NEON_GREEN, width=4)
        self.canvas.create_text(FIELD_WIDTH//2, FIELD_HEIGHT//2-40, text="YOU WIN!", font=("Consolas", 36, "bold"), fill=NEON_GREEN)
        self.canvas.create_text(FIELD_WIDTH//2, FIELD_HEIGHT//2, text=f"Score: {self.score}", font=("Consolas", 22), fill=NEON_PINK)
        self.canvas.create_text(FIELD_WIDTH//2, FIELD_HEIGHT//2+38, text=f"[SPACE] Play Again  [Q] Quit", font=("Consolas", 18), fill=NEON_YELLOW)
        self.menu_mode = True

def main():
    root = tk.Tk()
    app = BreakoutGame(root)
    root.mainloop()

if __name__ == "__main__":
    main()

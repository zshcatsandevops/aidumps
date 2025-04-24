# 4k Tetris: Pure Python, no media, 60 FPS, single file
import tkinter as tk
import random
import time
import threading
import math
import sys
if sys.platform == 'win32':
    import winsound
else:
    import os

CELL = 20
COLS, ROWS = 10, 20
WIDTH, HEIGHT = COLS * CELL, ROWS * CELL
FPS = 60

# Tetromino shapes: (rotations)
TETROMINOS = {
    'I': [[(0,1),(1,1),(2,1),(3,1)], [(2,0),(2,1),(2,2),(2,3)]],
    'O': [[(1,0),(2,0),(1,1),(2,1)]],
    'T': [[(1,0),(0,1),(1,1),(2,1)], [(1,0),(1,1),(2,1),(1,2)], [(0,1),(1,1),(2,1),(1,2)], [(1,0),(0,1),(1,1),(1,2)]],
    'S': [[(1,0),(2,0),(0,1),(1,1)], [(1,0),(1,1),(2,1),(2,2)]],
    'Z': [[(0,0),(1,0),(1,1),(2,1)], [(2,0),(1,1),(2,1),(1,2)]],
    'J': [[(0,0),(0,1),(1,1),(2,1)], [(1,0),(2,0),(1,1),(1,2)], [(0,1),(1,1),(2,1),(2,2)], [(1,0),(1,1),(0,2),(1,2)]],
    'L': [[(2,0),(0,1),(1,1),(2,1)], [(1,0),(1,1),(1,2),(2,2)], [(0,1),(1,1),(2,1),(0,2)], [(0,0),(1,0),(1,1),(1,2)]]
}
COLORS = {'I':'#0ff','O':'#ff0','T':'#a0f','S':'#0f0','Z':'#f00','J':'#00f','L':'#fa0'}

try:
    import simpleaudio as sa
    SIMPLEAUDIO = True
except ImportError:
    SIMPLEAUDIO = False

class FamiSoundEngine:
    def __init__(self):
        self.sample_rate = 44100
        self.channels = 1
        self.lock = threading.Lock()

    def play_square(self, freq=440, duration=0.08, duty=0.5, vol=0.2):
        if SIMPLEAUDIO:
            t = np.linspace(0, duration, int(self.sample_rate * duration), False)
            wave = (np.sign(np.sin(2 * np.pi * freq * t)) * (t % (1/freq) < duty/freq)).astype(np.float32)
            audio = (wave * vol * 32767).astype(np.int16)
            sa.play_buffer(audio, 1, 2, self.sample_rate)
        elif sys.platform == 'win32':
            winsound.Beep(int(freq), int(duration*1000))

    def play_noise(self, duration=0.08, vol=0.2):
        if SIMPLEAUDIO:
            samples = np.random.uniform(-1, 1, int(self.sample_rate * duration))
            audio = (samples * vol * 32767).astype(np.int16)
            sa.play_buffer(audio, 1, 2, self.sample_rate)
        elif sys.platform == 'win32':
            winsound.Beep(37, int(duration*1000))

import numpy as np

class Tetris:
    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg='#111')
        self.canvas.pack()
        self.sound = FamiSoundEngine()
        self.reset()
        self.root.bind('<Key>', self.key)
        self.last_time = time.time()
        self.fall_delay = 0.5
        self.fall_timer = 0
        self.running = True
        self.loop()

    def reset(self):
        self.board = [[None]*COLS for _ in range(ROWS)]
        self.score = 0
        self.spawn()

    def spawn(self):
        self.type = random.choice(list(TETROMINOS))
        self.rot = 0
        self.x, self.y = 3, 0
        if self.collide(self.x, self.y, self.rot):
            self.running = False

    def collide(self, x, y, rot):
        for dx, dy in TETROMINOS[self.type][rot]:
            nx, ny = x+dx, y+dy
            if nx<0 or nx>=COLS or ny<0 or ny>=ROWS or (ny>=0 and self.board[ny][nx]):
                return True
        return False

    def freeze(self):
        for dx, dy in TETROMINOS[self.type][self.rot]:
            nx, ny = self.x+dx, self.y+dy
            if 0<=ny<ROWS and 0<=nx<COLS:
                self.board[ny][nx] = self.type
        self.sound.play_square(220, 0.06, 0.5, 0.2)  # NES-like lock sound
        self.clear_lines()
        self.spawn()

    def clear_lines(self):
        new_board = [row for row in self.board if any(cell is None for cell in row)]
        lines = ROWS - len(new_board)
        for _ in range(lines):
            new_board.insert(0, [None]*COLS)
        self.board = new_board
        if lines:
            self.sound.play_noise(0.12, 0.3)  # NES-like line clear
        self.score += lines*100

    def move(self, dx, dy, drot):
        nx, ny, nrot = self.x+dx, self.y+dy, (self.rot+drot)%len(TETROMINOS[self.type])
        if not self.collide(nx, ny, nrot):
            self.x, self.y, self.rot = nx, ny, nrot
            if dx or drot:
                self.sound.play_square(660, 0.02, 0.25, 0.1)  # NES-like move/rotate
            return True
        return False

    def drop(self):
        while self.move(0,1,0): pass
        self.sound.play_square(330, 0.05, 0.5, 0.2)  # NES-like hard drop
        self.freeze()

    def key(self, e):
        if not self.running: return
        k = e.keysym
        if k in ('Left','a'): self.move(-1,0,0)
        elif k in ('Right','d'): self.move(1,0,0)
        elif k in ('Down','s'): self.move(0,1,0)
        elif k in ('Up','w','x'): self.move(0,0,1)
        elif k in ('space','Return'): self.drop()
        elif k=='r': self.reset(); self.running=True

    def draw(self):
        self.canvas.delete('all')
        # Draw board
        for y in range(ROWS):
            for x in range(COLS):
                t = self.board[y][x]
                if t:
                    self.canvas.create_rectangle(x*CELL, y*CELL, (x+1)*CELL, (y+1)*CELL, fill=COLORS[t], outline='#222')
        # Draw current piece
        if self.running:
            for dx, dy in TETROMINOS[self.type][self.rot]:
                nx, ny = self.x+dx, self.y+dy
                if ny>=0:
                    self.canvas.create_rectangle(nx*CELL, ny*CELL, (nx+1)*CELL, (ny+1)*CELL, fill=COLORS[self.type], outline='#fff')
        # Draw grid
        for x in range(COLS+1):
            self.canvas.create_line(x*CELL,0,x*CELL,HEIGHT,fill='#333')
        for y in range(ROWS+1):
            self.canvas.create_line(0,y*CELL,WIDTH,y*CELL,fill='#333')
        # Draw score
        self.canvas.create_text(WIDTH-5,5,anchor='ne',text=f'Score: {self.score}',fill='#fff',font=('Consolas',12,'bold'))
        if not self.running:
            self.canvas.create_text(WIDTH//2,HEIGHT//2,text='GAME OVER',fill='#f44',font=('Consolas',24,'bold'))
            self.canvas.create_text(WIDTH//2,HEIGHT//2+30,text='Press R to restart',fill='#fff',font=('Consolas',12))

    def update(self, dt):
        if not self.running: return
        self.fall_timer += dt
        if self.fall_timer > self.fall_delay:
            if not self.move(0,1,0):
                self.freeze()
            self.fall_timer = 0

    def loop(self):
        now = time.time()
        dt = now - self.last_time
        self.last_time = now
        self.update(dt)
        self.draw()
        self.root.after(int(1000/FPS), self.loop)

if __name__=='__main__':
    root = tk.Tk()
    root.title('Tetris 4k')
    game = Tetris(root)
    root.mainloop()

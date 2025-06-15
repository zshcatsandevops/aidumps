import tkinter as tk
import random

CELL_SIZE = 20
MAZE = [
    "############################",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#G####.#####.##.#####.####G#",
    "#.####.#####.##.#####.####.#",
    "#..........................#",
    "#.####.##.########.##.####.#",
    "#.####.##.########.##.####.#",
    "#......##....##....##......#",
    "######.##### ## #####.######",
    "     #.##### ## #####.#     ",
    "     #.##          ##.#     ",
    "     #.## ###--### ##.#     ",
    "######.## #      # ##.######",
    "      .   #      #   .      ",
    "######.## #      # ##.######",
    "     #.## ######## ##.#     ",
    "     #.##          ##.#     ",
    "     #.## ######## ##.#     ",
    "######.## ######## ##.######",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#G..##................##..G#",
    "###.##.##.########.##.##.###",
    "###.##.##.########.##.##.###",
    "#......##....##....##......#",
    "#.##########.##.##########.#",
    "#..........................#",
    "############################"
]

class PacmanApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Pac-Man 4K")
        width = len(MAZE[0]) * CELL_SIZE
        height = len(MAZE) * CELL_SIZE
        self.canvas = tk.Canvas(self.root, width=width, height=height, bg="black")
        self.canvas.pack()
        self.state = 'start'
        self.score = 0
        self.lives = 3
        self.pacman = None
        self.ghosts = []
        self.pac_dir = (0,0)
        self.after_id = None
        self.root.bind('<Return>', self.start_game)
        self.root.bind('<KeyPress>', self.on_key)
        self.draw_start()
        self.root.mainloop()

    def draw_start(self):
        self.canvas.delete('all')
        self.canvas.create_text( self.canvas.winfo_reqwidth()/2, 100,
            text="PAC-MAN", fill="yellow", font=("Arial", 48, 'bold'))
        self.canvas.create_text( self.canvas.winfo_reqwidth()/2, 200,
            text="Press Enter to Start", fill="white", font=("Arial", 24))

    def start_game(self, event=None):
        if self.state != 'start': return
        self.state = 'playing'
        self.score = 0
        self.lives = 3
        self.init_game()
        self.game_loop()

    def init_game(self):
        self.canvas.delete('all')
        self.pellets = set()
        for y,row in enumerate(MAZE):
            for x,ch in enumerate(row):
                px,py = x*CELL_SIZE, y*CELL_SIZE
                if ch == '#':
                    self.canvas.create_rectangle(px,py,px+CELL_SIZE,py+CELL_SIZE,
                        fill='blue',width=0)
                elif ch == '.':
                    oval = self.canvas.create_oval(px+8,py+8,px+12,py+12,fill='white')
                    self.pellets.add((x,y))
                elif ch == 'G':
                    ghost = self.canvas.create_oval(px,py,px+CELL_SIZE,py+CELL_SIZE,
                        fill='red')
                    self.ghosts.append({'id':ghost,'pos':(x,y),'dir':random.choice([(1,0),(-1,0),(0,1),(0,-1)])})
        # Pac-Man initial
        self.px, self.py = 14, 23
        self.pacman = self.canvas.create_oval(self.px*CELL_SIZE,self.py*CELL_SIZE,
            self.px*CELL_SIZE+CELL_SIZE,self.py*CELL_SIZE+CELL_SIZE,fill='yellow')
        self.pac_dir = (0,-1)

    def on_key(self, event):
        if self.state!='playing': return
        dirs = {'Left':(-1,0),'Right':(1,0),'Up':(0,-1),'Down':(0,1)}
        if event.keysym in dirs:
            self.pac_dir = dirs[event.keysym]

    def move_pacman(self):
        nx,ny = self.px+self.pac_dir[0], self.py+self.pac_dir[1]
        if MAZE[ny][nx] != '#':
            self.px, self.py = nx, ny
            self.canvas.coords(self.pacman,
                nx*CELL_SIZE,ny*CELL_SIZE,
                nx*CELL_SIZE+CELL_SIZE,ny*CELL_SIZE+CELL_SIZE)
        if (self.px,self.py) in self.pellets:
            self.pellets.remove((self.px,self.py))
            self.score += 10
            self.canvas.delete('all')
            self.init_game()

    def move_ghosts(self):
        for g in self.ghosts:
            x,y = g['pos']
            dx,dy = g['dir']
            if random.random()<0.2 or MAZE[y+dy][x+dx]=='#':
                g['dir']=random.choice([(1,0),(-1,0),(0,1),(0,-1)])
                dx,dy = g['dir']
            nx,ny = x+dx,y+dy
            if MAZE[ny][nx] != '#':
                g['pos']=(nx,ny)
                self.canvas.coords(g['id'],
                    nx*CELL_SIZE,ny*CELL_SIZE,
                    nx*CELL_SIZE+CELL_SIZE,ny*CELL_SIZE+CELL_SIZE)

    def game_loop(self):
        if self.lives<=0 or not self.pellets:
            self.state='gameover'
            self.draw_gameover()
            return
        self.move_pacman()
        self.move_ghosts()
        for g in self.ghosts:
            if g['pos']==(self.px,self.py):
                self.lives-=1
                self.init_game()
                break
        self.canvas.after(150, self.game_loop)

    def draw_gameover(self):
        self.canvas.delete('all')
        self.canvas.create_text(self.canvas.winfo_width()/2,100,
            text="GAME OVER", fill="red", font=("Arial", 48, 'bold'))
        self.canvas.create_text(self.canvas.winfo_width()/2,200,
            text=f"Score: {self.score}", fill="white", font=("Arial", 24))
        self.canvas.create_text(self.canvas.winfo_width()/2,300,
            text="Press Enter to Restart", fill="white", font=("Arial", 16))
        self.root.bind('<Return>', self.restart)

    def restart(self, event=None):
        self.root.unbind('<Return>')
        self.start_game()

if __name__ == '__main__':
    PacmanApp()

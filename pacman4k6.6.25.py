import tkinter as tk
import math
import time
import random
from collections import deque

class SoundEngine:
    """NES-style sound engine using tkinter bell"""
    def __init__(self, root):
        self.root = root
        self.sound_queue = deque()
        self.last_sound = 0
        
    def play(self, sound_type):
        current_time = time.time()
        if current_time - self.last_sound > 0.1:  # Throttle sounds
            if sound_type == "chomp":
                self.root.bell()
            elif sound_type == "power":
                for _ in range(2):
                    self.root.bell()
            elif sound_type == "ghost":
                for _ in range(3):
                    self.root.bell()
            self.last_sound = current_time

class Game:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PAC-MAN")
        self.root.configure(bg='black')
        self.root.resizable(False, False)
        
        # Game constants
        self.TILE_SIZE = 20
        self.MAZE_WIDTH = 28
        self.MAZE_HEIGHT = 31
        self.WIDTH = self.MAZE_WIDTH * self.TILE_SIZE
        self.HEIGHT = self.MAZE_HEIGHT * self.TILE_SIZE
        self.FPS = 60
        self.FRAME_TIME = 1000 // self.FPS
        
        # Canvas
        self.canvas = tk.Canvas(self.root, width=self.WIDTH, height=self.HEIGHT, bg='black', highlightthickness=0)
        self.canvas.pack()
        
        # Sound engine
        self.sound = SoundEngine(self.root)
        
        # Game state
        self.score = 0
        self.lives = 3
        self.level = 1
        self.game_over = False
        self.power_mode = False
        self.power_timer = 0
        self.dots_eaten = 0
        self.frame_count = 0
        
        # Initialize maze (1 = wall, 0 = dot, 2 = power pellet, 3 = empty)
        self.init_maze()
        
        # Entities
        self.pacman = {
            'x': 14 * self.TILE_SIZE,
            'y': 23 * self.TILE_SIZE,
            'dx': 0,
            'dy': 0,
            'next_dx': 0,
            'next_dy': 0,
            'angle': 0,
            'mouth_open': True
        }
        
        # Ghosts with different AI behaviors
        self.ghosts = [
            {'x': 14 * self.TILE_SIZE, 'y': 11 * self.TILE_SIZE, 'dx': 1, 'dy': 0, 'color': '#ff0000', 'scared': False, 'mode': 'chase'},  # Blinky
            {'x': 12 * self.TILE_SIZE, 'y': 14 * self.TILE_SIZE, 'dx': 0, 'dy': -1, 'color': '#ffb8ff', 'scared': False, 'mode': 'ambush'},  # Pinky
            {'x': 14 * self.TILE_SIZE, 'y': 14 * self.TILE_SIZE, 'dx': -1, 'dy': 0, 'color': '#00ffff', 'scared': False, 'mode': 'patrol'},  # Inky
            {'x': 16 * self.TILE_SIZE, 'y': 14 * self.TILE_SIZE, 'dx': 0, 'dy': 1, 'color': '#ffb852', 'scared': False, 'mode': 'random'}   # Clyde
        ]
        
        # Controls
        self.root.bind('<KeyPress>', self.key_press)
        
        # Start game loop
        self.update()
        
    def init_maze(self):
        # Classic Pac-Man maze layout
        maze_template = [
            "1111111111111111111111111111",
            "1000000000000110000000000001",
            "1011110111110110111110111101",
            "1211110111110110111110111121",
            "1011110111110110111110111101",
            "1000000000000000000000000001",
            "1011110110111111110110111101",
            "1011110110111111110110111101",
            "1000000110000110000110000001",
            "1111110111110110111110111111",
            "1111110111110110111110111111",
            "1111110110333333330110111111",
            "1111110110111331110110111111",
            "1111110330111331110330111111",
            "3333330330111331110330333333",
            "1111110110111111110110111111",
            "1111110110333333330110111111",
            "1111110110111111110110111111",
            "1111110110111111110110111111",
            "1000000000000110000000000001",
            "1011110111110110111110111101",
            "1011110111110110111110111101",
            "1000110000000000000000110001",
            "1000110000000330000000110001", # <- FIX: Created path for Pac-Man spawn
            "1110110110111001110110110111", # <- FIX: Connected path downwards
            "1000000110000110000110000001",
            "1011111111110110111111111101",
            "1211111111110110111111111121",
            "1000000000000000000000000001",
            "1111111111111111111111111111",
            "3333333333333333333333333333"
        ]
        
        self.maze = []
        for y, row in enumerate(maze_template):
            maze_row = []
            for x, cell in enumerate(row):
                maze_row.append(int(cell))
            self.maze.append(maze_row)
            
        # Count total dots
        self.total_dots = sum(row.count(0) + row.count(2) for row in self.maze)
        
    def draw(self):
        self.canvas.delete("all")
        
        # Draw maze
        for y in range(self.MAZE_HEIGHT):
            for x in range(self.MAZE_WIDTH):
                cell = self.maze[y][x]
                px = x * self.TILE_SIZE
                py = y * self.TILE_SIZE
                
                if cell == 1:  # Wall
                    self.canvas.create_rectangle(px, py, px + self.TILE_SIZE, py + self.TILE_SIZE,
                                               fill='#0000ff', outline='#4040ff')
                elif cell == 0:  # Dot
                    cx = px + self.TILE_SIZE // 2
                    cy = py + self.TILE_SIZE // 2
                    self.canvas.create_oval(cx - 2, cy - 2, cx + 2, cy + 2, fill='white', outline='white')
                elif cell == 2:  # Power pellet
                    cx = px + self.TILE_SIZE // 2
                    cy = py + self.TILE_SIZE // 2
                    self.canvas.create_oval(cx - 6, cy - 6, cx + 6, cy + 6, fill='white', outline='white')
        
        # Draw Pac-Man
        px = self.pacman['x'] + self.TILE_SIZE // 2
        py = self.pacman['y'] + self.TILE_SIZE // 2
        
        if self.pacman['mouth_open']:
            # Calculate mouth angle based on direction
            if self.pacman['dx'] > 0:
                start_angle = 45
            elif self.pacman['dx'] < 0:
                start_angle = 225
            elif self.pacman['dy'] > 0:
                start_angle = 315
            elif self.pacman['dy'] < 0:
                start_angle = 135
            else:
                start_angle = 45
                
            self.canvas.create_arc(px - 10, py - 10, px + 10, py + 10,
                                  start=start_angle, extent=270,
                                  fill='yellow', outline='yellow')
        else:
            self.canvas.create_oval(px - 10, py - 10, px + 10, py + 10,
                                  fill='yellow', outline='yellow')
        
        # Draw ghosts
        for ghost in self.ghosts:
            gx = ghost['x'] + self.TILE_SIZE // 2
            gy = ghost['y'] + self.TILE_SIZE // 2
            
            color = '#0000ff' if ghost['scared'] else ghost['color']
            
            # Ghost body
            self.canvas.create_arc(gx - 10, gy - 10, gx + 10, gy + 5,
                                 start=0, extent=180, fill=color, outline=color)
            self.canvas.create_rectangle(gx - 10, gy - 2, gx + 10, gy + 5,
                                       fill=color, outline=color)
            
            # Ghost bottom wave
            for i in range(4):
                wx = gx - 7 + i * 5
                self.canvas.create_oval(wx - 2, gy + 3, wx + 2, gy + 7,
                                      fill=color, outline=color)
            
            # Eyes
            if not ghost['scared']:
                self.canvas.create_oval(gx - 6, gy - 6, gx - 2, gy - 2, fill='white', outline='white')
                self.canvas.create_oval(gx + 2, gy - 6, gx + 6, gy - 2, fill='white', outline='white')
                self.canvas.create_oval(gx - 5, gy - 5, gx - 3, gy - 3, fill='black', outline='black')
                self.canvas.create_oval(gx + 3, gy - 5, gx + 5, gy - 3, fill='black', outline='black')
        
        # Draw UI
        self.canvas.create_text(10, 10, text=f"SCORE: {self.score}", fill='white', font=('Arial', 14), anchor='nw')
        self.canvas.create_text(self.WIDTH - 10, 10, text=f"LIVES: {self.lives}", fill='white', font=('Arial', 14), anchor='ne')
        
        if self.game_over:
            self.canvas.create_text(self.WIDTH // 2, self.HEIGHT // 2, text="GAME OVER", 
                                  fill='red', font=('Arial', 30), anchor='center')
            self.canvas.create_text(self.WIDTH // 2, self.HEIGHT // 2 + 40, text=f"Final Score: {self.score}", 
                                  fill='white', font=('Arial', 20), anchor='center')
    
    def check_collision(self, x, y, dx, dy):
        # Check all four corners of the entity
        size = self.TILE_SIZE - 4
        corners = [
            (x + 2 + dx, y + 2 + dy),
            (x + size + dx, y + 2 + dy),
            (x + 2 + dx, y + size + dy),
            (x + size + dx, y + size + dy)
        ]
        
        for cx, cy in corners:
            grid_x = int(cx // self.TILE_SIZE)
            grid_y = int(cy // self.TILE_SIZE)
            
            if 0 <= grid_x < self.MAZE_WIDTH and 0 <= grid_y < self.MAZE_HEIGHT:
                if self.maze[grid_y][grid_x] == 1:
                    return True
        return False
    
    def move_pacman(self):
        # Try to change direction if requested
        if self.pacman['next_dx'] != 0 or self.pacman['next_dy'] != 0:
            if not self.check_collision(self.pacman['x'], self.pacman['y'], 
                                       self.pacman['next_dx'] * 4, self.pacman['next_dy'] * 4):
                self.pacman['dx'] = self.pacman['next_dx']
                self.pacman['dy'] = self.pacman['next_dy']
        
        # Move if possible
        if not self.check_collision(self.pacman['x'], self.pacman['y'], 
                                   self.pacman['dx'] * 4, self.pacman['dy'] * 4):
            self.pacman['x'] += self.pacman['dx'] * 4
            self.pacman['y'] += self.pacman['dy'] * 4
        
        # Tunnel wrapping
        if self.pacman['x'] < 0:
            self.pacman['x'] = self.WIDTH - self.TILE_SIZE
        elif self.pacman['x'] >= self.WIDTH:
            self.pacman['x'] = 0
        
        # Animate mouth
        if self.frame_count % 8 == 0:
            self.pacman['mouth_open'] = not self.pacman['mouth_open']
        
        # Check dot eating
        grid_x = int((self.pacman['x'] + self.TILE_SIZE // 2) // self.TILE_SIZE)
        grid_y = int((self.pacman['y'] + self.TILE_SIZE // 2) // self.TILE_SIZE)
        
        if 0 <= grid_x < self.MAZE_WIDTH and 0 <= grid_y < self.MAZE_HEIGHT:
            cell = self.maze[grid_y][grid_x]
            if cell == 0:  # Regular dot
                self.maze[grid_y][grid_x] = 3
                self.score += 10
                self.dots_eaten += 1
                self.sound.play("chomp")
            elif cell == 2:  # Power pellet
                self.maze[grid_y][grid_x] = 3
                self.score += 50
                self.dots_eaten += 1
                self.power_mode = True
                self.power_timer = 300  # 5 seconds at 60 FPS
                for ghost in self.ghosts:
                    ghost['scared'] = True
                self.sound.play("power")
    
    def move_ghosts(self):
        for i, ghost in enumerate(self.ghosts):
            # Different AI for each ghost
            if ghost['scared'] and self.power_mode:
                # Run away from Pac-Man
                dx = math.copysign(1, ghost['x'] - self.pacman['x'])
                dy = math.copysign(1, ghost['y'] - self.pacman['y'])
            else:
                if i == 0:  # Blinky - direct chase
                    dx = math.copysign(1, self.pacman['x'] - ghost['x'])
                    dy = math.copysign(1, self.pacman['y'] - ghost['y'])
                elif i == 1:  # Pinky - ambush
                    target_x = self.pacman['x'] + self.pacman['dx'] * 80
                    target_y = self.pacman['y'] + self.pacman['dy'] * 80
                    dx = math.copysign(1, target_x - ghost['x'])
                    dy = math.copysign(1, target_y - ghost['y'])
                elif i == 2:  # Inky - patrol corners
                    corner = ((self.frame_count // 240) % 4)
                    corners = [(0, 0), (self.WIDTH, 0), (self.WIDTH, self.HEIGHT), (0, self.HEIGHT)]
                    target = corners[corner]
                    dx = math.copysign(1, target[0] - ghost['x'])
                    dy = math.copysign(1, target[1] - ghost['y'])
                else:  # Clyde - random
                    if self.frame_count % 60 == 0:
                        ghost['dx'] = random.choice([-1, 0, 1])
                        ghost['dy'] = random.choice([-1, 0, 1]) if ghost['dx'] == 0 else 0
                    continue
            
            # Try to move in the desired direction
            speed = 2 if ghost['scared'] else 3
            
            # Prioritize one direction over the other
            if abs(dx) > abs(dy):
                if not self.check_collision(ghost['x'], ghost['y'], dx * speed, 0):
                    ghost['x'] += dx * speed
                    ghost['dy'] = 0
                    ghost['dx'] = dx
                elif not self.check_collision(ghost['x'], ghost['y'], 0, dy * speed):
                    ghost['y'] += dy * speed
                    ghost['dx'] = 0
                    ghost['dy'] = dy
            else:
                if not self.check_collision(ghost['x'], ghost['y'], 0, dy * speed):
                    ghost['y'] += dy * speed
                    ghost['dx'] = 0
                    ghost['dy'] = dy
                elif not self.check_collision(ghost['x'], ghost['y'], dx * speed, 0):
                    ghost['x'] += dx * speed
                    ghost['dy'] = 0
                    ghost['dx'] = dx
            
            # If stuck, try random direction
            if self.check_collision(ghost['x'], ghost['y'], ghost['dx'] * speed, ghost['dy'] * speed):
                directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                random.shuffle(directions)
                for dx, dy in directions:
                    if not self.check_collision(ghost['x'], ghost['y'], dx * speed, dy * speed):
                        ghost['dx'] = dx
                        ghost['dy'] = dy
                        break
            
            # Move ghost
            ghost['x'] += ghost['dx'] * speed
            ghost['y'] += ghost['dy'] * speed
            
            # Tunnel wrapping
            if ghost['x'] < 0:
                ghost['x'] = self.WIDTH - self.TILE_SIZE
            elif ghost['x'] >= self.WIDTH:
                ghost['x'] = 0
    
    def check_ghost_collision(self):
        px = self.pacman['x'] + self.TILE_SIZE // 2
        py = self.pacman['y'] + self.TILE_SIZE // 2
        
        for ghost in self.ghosts:
            gx = ghost['x'] + self.TILE_SIZE // 2
            gy = ghost['y'] + self.TILE_SIZE // 2
            
            distance = math.sqrt((px - gx) ** 2 + (py - gy) ** 2)
            
            if distance < 15:  # Collision threshold
                if ghost['scared']:
                    # Eat ghost
                    ghost['x'] = 14 * self.TILE_SIZE
                    ghost['y'] = 14 * self.TILE_SIZE
                    ghost['scared'] = False
                    self.score += 200
                    self.sound.play("ghost")
                else:
                    # Lose life
                    self.lives -= 1
                    if self.lives <= 0:
                        self.game_over = True
                    else:
                        # Reset positions
                        self.pacman['x'] = 14 * self.TILE_SIZE
                        self.pacman['y'] = 23 * self.TILE_SIZE
                        self.pacman['dx'] = 0
                        self.pacman['dy'] = 0
                        for i, ghost in enumerate(self.ghosts):
                            ghost['x'] = (12 + i * 2) * self.TILE_SIZE
                            ghost['y'] = 14 * self.TILE_SIZE
    
    def update(self):
        if not self.game_over:
            self.move_pacman()
            self.move_ghosts()
            self.check_ghost_collision()
            
            # Update power mode
            if self.power_mode:
                self.power_timer -= 1
                if self.power_timer <= 0:
                    self.power_mode = False
                    for ghost in self.ghosts:
                        ghost['scared'] = False
            
            # Check win condition
            if self.dots_eaten >= self.total_dots:
                self.level += 1
                self.init_maze()
                self.dots_eaten = 0
                self.pacman['x'] = 14 * self.TILE_SIZE
                self.pacman['y'] = 23 * self.TILE_SIZE
        
        self.draw()
        self.frame_count += 1
        
        # Schedule next frame
        self.root.after(self.FRAME_TIME, self.update)
    
    def key_press(self, event):
        if event.keysym == 'Up':
            self.pacman['next_dx'] = 0
            self.pacman['next_dy'] = -1
        elif event.keysym == 'Down':
            self.pacman['next_dx'] = 0
            self.pacman['next_dy'] = 1
        elif event.keysym == 'Left':
            self.pacman['next_dx'] = -1
            self.pacman['next_dy'] = 0
        elif event.keysym == 'Right':
            self.pacman['next_dx'] = 1
            self.pacman['next_dy'] = 0
    
    def run(self):
        self.root.mainloop()

# Start the game
if __name__ == "__main__":
    game = Game()
    game.run()

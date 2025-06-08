import tkinter as tk
import time
import random

class MarioGame:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Mario Forever Community Edition")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        self.canvas = tk.Canvas(self.root, width=600, height=400, bg='#5C94FC')
        self.canvas.pack()
        
        # Game state
        self.running = True
        self.current_level = 0
        self.lives = 3
        self.coins = 0
        self.score = 0
        self.game_over = False
        self.level_complete = False
        self.game_won = False
        
        # Physics
        self.gravity = 0.5
        self.jump_strength = -12
        self.move_speed = 4
        
        # Player
        self.player = {
            'x': 50, 'y': 300, 'vx': 0, 'vy': 0,
            'width': 20, 'height': 30,
            'on_ground': False, 'facing_right': True
        }
        
        # Camera
        self.camera_x = 0
        
        # Level definitions
        self.levels = [
            # Level 1
            {
                'platforms': [
                    {'x': 0, 'y': 350, 'width': 300, 'height': 50},
                    {'x': 350, 'y': 350, 'width': 200, 'height': 50},
                    {'x': 200, 'y': 280, 'width': 100, 'height': 20},
                    {'x': 400, 'y': 250, 'width': 80, 'height': 20},
                    {'x': 600, 'y': 350, 'width': 400, 'height': 50},
                    {'x': 750, 'y': 280, 'width': 100, 'height': 20},
                    {'x': 900, 'y': 220, 'width': 120, 'height': 20},
                    {'x': 1100, 'y': 350, 'width': 300, 'height': 50},
                ],
                'enemies': [
                    {'x': 400, 'y': 330, 'vx': -1, 'type': 'goomba'},
                    {'x': 700, 'y': 330, 'vx': 1, 'type': 'goomba'},
                    {'x': 950, 'y': 200, 'vx': -1, 'type': 'goomba'},
                ],
                'coins': [
                    {'x': 250, 'y': 250}, {'x': 440, 'y': 220},
                    {'x': 800, 'y': 250}, {'x': 960, 'y': 190},
                    {'x': 1200, 'y': 300}, {'x': 1250, 'y': 300},
                ],
                'goal': {'x': 1350, 'y': 300}
            },
            # Level 2
            {
                'platforms': [
                    {'x': 0, 'y': 350, 'width': 150, 'height': 50},
                    {'x': 200, 'y': 320, 'width': 80, 'height': 80},
                    {'x': 330, 'y': 290, 'width': 80, 'height': 110},
                    {'x': 460, 'y': 260, 'width': 80, 'height': 140},
                    {'x': 590, 'y': 350, 'width': 200, 'height': 50},
                    {'x': 840, 'y': 280, 'width': 100, 'height': 20},
                    {'x': 990, 'y': 220, 'width': 100, 'height': 20},
                    {'x': 1140, 'y': 160, 'width': 100, 'height': 20},
                    {'x': 1290, 'y': 350, 'width': 300, 'height': 50},
                ],
                'enemies': [
                    {'x': 650, 'y': 330, 'vx': -1, 'type': 'goomba'},
                    {'x': 890, 'y': 260, 'vx': 1, 'type': 'goomba'},
                    {'x': 1040, 'y': 200, 'vx': -1, 'type': 'goomba'},
                    {'x': 1400, 'y': 330, 'vx': 1, 'type': 'goomba'},
                ],
                'coins': [
                    {'x': 240, 'y': 290}, {'x': 370, 'y': 260},
                    {'x': 500, 'y': 230}, {'x': 690, 'y': 320},
                    {'x': 890, 'y': 250}, {'x': 1040, 'y': 190},
                    {'x': 1190, 'y': 130}, {'x': 1400, 'y': 320},
                ],
                'goal': {'x': 1500, 'y': 300}
            },
            # Level 3
            {
                'platforms': [
                    {'x': 0, 'y': 350, 'width': 100, 'height': 50},
                    {'x': 150, 'y': 300, 'width': 60, 'height': 20},
                    {'x': 260, 'y': 250, 'width': 60, 'height': 20},
                    {'x': 370, 'y': 200, 'width': 60, 'height': 20},
                    {'x': 480, 'y': 150, 'width': 100, 'height': 20},
                    {'x': 630, 'y': 200, 'width': 60, 'height': 20},
                    {'x': 740, 'y': 250, 'width': 60, 'height': 20},
                    {'x': 850, 'y': 300, 'width': 60, 'height': 20},
                    {'x': 960, 'y': 350, 'width': 200, 'height': 50},
                    {'x': 1210, 'y': 280, 'width': 150, 'height': 20},
                    {'x': 1410, 'y': 350, 'width': 200, 'height': 50},
                ],
                'enemies': [
                    {'x': 530, 'y': 130, 'vx': -1, 'type': 'goomba'},
                    {'x': 1050, 'y': 330, 'vx': 1, 'type': 'goomba'},
                    {'x': 1285, 'y': 260, 'vx': -1, 'type': 'goomba'},
                    {'x': 1500, 'y': 330, 'vx': 1, 'type': 'goomba'},
                ],
                'coins': [
                    {'x': 180, 'y': 270}, {'x': 290, 'y': 220},
                    {'x': 400, 'y': 170}, {'x': 530, 'y': 120},
                    {'x': 660, 'y': 170}, {'x': 770, 'y': 220},
                    {'x': 880, 'y': 270}, {'x': 1285, 'y': 250},
                ],
                'goal': {'x': 1550, 'y': 300}
            }
        ]
        
        # Initialize level
        self.load_level(0)
        
        # Controls
        self.keys = {'Left': False, 'Right': False, 'Up': False, 'space': False}
        self.root.bind('<KeyPress>', self.key_press)
        self.root.bind('<KeyRelease>', self.key_release)
        
        # UI elements
        self.create_ui()
        
        # Start game loop
        self.last_time = time.time()
        self.game_loop()
        
    def create_ui(self):
        self.score_text = self.canvas.create_text(10, 10, anchor='nw', 
            text=f'Score: {self.score}', fill='white', font=('Arial', 14, 'bold'))
        self.coins_text = self.canvas.create_text(10, 30, anchor='nw',
            text=f'Coins: {self.coins}', fill='yellow', font=('Arial', 14, 'bold'))
        self.lives_text = self.canvas.create_text(10, 50, anchor='nw',
            text=f'Lives: {self.lives}', fill='red', font=('Arial', 14, 'bold'))
        self.level_text = self.canvas.create_text(300, 10, anchor='n',
            text=f'Level {self.current_level + 1}', fill='white', font=('Arial', 16, 'bold'))
            
    def load_level(self, level_num):
        self.current_level = level_num
        level = self.levels[level_num]
        
        # Reset player position
        self.player['x'] = 50
        self.player['y'] = 300
        self.player['vx'] = 0
        self.player['vy'] = 0
        self.camera_x = 0
        
        # Copy level data
        self.platforms = [p.copy() for p in level['platforms']]
        self.enemies = [e.copy() for e in level['enemies']]
        self.coin_objects = [c.copy() for c in level['coins']]
        self.goal = level['goal'].copy()
        
        self.level_complete = False
        
    def key_press(self, event):
        if event.keysym in self.keys:
            self.keys[event.keysym] = True
            
    def key_release(self, event):
        if event.keysym in self.keys:
            self.keys[event.keysym] = False
            
    def update_player(self, dt):
        # Horizontal movement
        if self.keys['Left']:
            self.player['vx'] = -self.move_speed
            self.player['facing_right'] = False
        elif self.keys['Right']:
            self.player['vx'] = self.move_speed
            self.player['facing_right'] = True
        else:
            self.player['vx'] *= 0.8
            
        # Jump
        if self.keys['Up'] and self.player['on_ground']:
            self.player['vy'] = self.jump_strength
            
        # Apply gravity
        self.player['vy'] += self.gravity
        if self.player['vy'] > 15:
            self.player['vy'] = 15
            
        # Move player
        self.player['x'] += self.player['vx']
        self.player['y'] += self.player['vy']
        
        # Check platform collisions
        self.player['on_ground'] = False
        for platform in self.platforms:
            if self.check_collision(self.player, platform):
                # Top collision (landing)
                if self.player['vy'] > 0 and self.player['y'] < platform['y']:
                    self.player['y'] = platform['y'] - self.player['height']
                    self.player['vy'] = 0
                    self.player['on_ground'] = True
                # Bottom collision
                elif self.player['vy'] < 0 and self.player['y'] > platform['y']:
                    self.player['y'] = platform['y'] + platform['height']
                    self.player['vy'] = 0
                # Side collisions
                elif self.player['vx'] > 0:
                    self.player['x'] = platform['x'] - self.player['width']
                elif self.player['vx'] < 0:
                    self.player['x'] = platform['x'] + platform['width']
                    
        # Fall detection
        if self.player['y'] > 450:
            self.die()
            
        # Update camera
        self.camera_x = self.player['x'] - 300
        if self.camera_x < 0:
            self.camera_x = 0
            
    def check_collision(self, obj1, obj2):
        return (obj1['x'] < obj2['x'] + obj2['width'] and
                obj1['x'] + obj1['width'] > obj2['x'] and
                obj1['y'] < obj2['y'] + obj2['height'] and
                obj1['y'] + obj1['height'] > obj2['y'])
                
    def update_enemies(self, dt):
        for enemy in self.enemies[:]:
            # Move enemy
            enemy['x'] += enemy['vx']
            
            # Check platform edges
            on_platform = False
            for platform in self.platforms:
                if (enemy['x'] > platform['x'] and 
                    enemy['x'] + 20 < platform['x'] + platform['width'] and
                    enemy['y'] + 20 == platform['y']):
                    on_platform = True
                    break
                    
            # Reverse direction at edges
            if not on_platform:
                enemy['vx'] *= -1
            if enemy['x'] <= 0 or enemy['x'] >= 1800:
                enemy['vx'] *= -1
                
            # Check collision with player
            enemy_rect = {'x': enemy['x'], 'y': enemy['y'], 'width': 20, 'height': 20}
            if self.check_collision(self.player, enemy_rect):
                if self.player['vy'] > 0 and self.player['y'] < enemy['y']:
                    # Player jumped on enemy
                    self.enemies.remove(enemy)
                    self.score += 100
                    self.player['vy'] = self.jump_strength / 2
                else:
                    # Player hit by enemy
                    self.die()
                    
    def update_coins(self, dt):
        for coin in self.coin_objects[:]:
            coin_rect = {'x': coin['x'], 'y': coin['y'], 'width': 16, 'height': 16}
            if self.check_collision(self.player, coin_rect):
                self.coin_objects.remove(coin)
                self.coins += 1
                self.score += 10
                
    def check_goal(self):
        goal_rect = {'x': self.goal['x'], 'y': self.goal['y'], 'width': 40, 'height': 50}
        if self.check_collision(self.player, goal_rect):
            self.level_complete = True
            self.score += 1000
            
    def die(self):
        self.lives -= 1
        if self.lives <= 0:
            self.game_over = True
        else:
            self.load_level(self.current_level)
            
    def draw(self):
        self.canvas.delete('game')
        
        # Sky gradient
        for i in range(10):
            color = f'#{92-i*3:02x}{148-i*3:02x}{252-i*3:02x}'
            self.canvas.create_rectangle(0, i*40, 600, (i+1)*40, 
                fill=color, outline='', tags='game')
        
        # Clouds
        for i in range(3):
            x = (i * 200 - self.camera_x * 0.3) % 700 - 100
            y = 50 + i * 30
            self.canvas.create_oval(x, y, x+80, y+40, fill='white', 
                outline='', tags='game')
            self.canvas.create_oval(x+30, y-10, x+90, y+30, fill='white',
                outline='', tags='game')
                
        # Platforms
        for platform in self.platforms:
            x = platform['x'] - self.camera_x
            if -100 < x < 700:
                # Platform top
                self.canvas.create_rectangle(x, platform['y'], 
                    x + platform['width'], platform['y'] + platform['height'],
                    fill='#8B4513', outline='#654321', width=2, tags='game')
                # Grass on top
                self.canvas.create_rectangle(x, platform['y'],
                    x + platform['width'], platform['y'] + 5,
                    fill='#228B22', outline='', tags='game')
                    
        # Coins
        for coin in self.coin_objects:
            x = coin['x'] - self.camera_x
            if -50 < x < 650:
                self.canvas.create_oval(x, coin['y'], x+16, coin['y']+16,
                    fill='gold', outline='orange', width=2, tags='game')
                    
        # Enemies
        for enemy in self.enemies:
            x = enemy['x'] - self.camera_x
            if -50 < x < 650:
                # Goomba body
                self.canvas.create_oval(x, enemy['y'], x+20, enemy['y']+20,
                    fill='brown', outline='#654321', width=2, tags='game')
                # Eyes
                self.canvas.create_oval(x+3, enemy['y']+5, x+7, enemy['y']+9,
                    fill='white', outline='', tags='game')
                self.canvas.create_oval(x+13, enemy['y']+5, x+17, enemy['y']+9,
                    fill='white', outline='', tags='game')
                    
        # Goal flag
        x = self.goal['x'] - self.camera_x
        if -50 < x < 650:
            # Pole
            self.canvas.create_rectangle(x+18, self.goal['y']-50, x+22, self.goal['y']+50,
                fill='gray', outline='black', tags='game')
            # Flag
            self.canvas.create_polygon(x+22, self.goal['y']-50, x+60, self.goal['y']-30,
                x+22, self.goal['y']-10, fill='red', outline='darkred', width=2, tags='game')
                
        # Player
        x = self.player['x'] - self.camera_x
        # Body
        self.canvas.create_rectangle(x, self.player['y'],
            x + self.player['width'], self.player['y'] + self.player['height'],
            fill='red', outline='darkred', width=2, tags='game')
        # Head
        head_y = self.player['y'] - 15
        self.canvas.create_oval(x, head_y, x+20, head_y+20,
            fill='#FDBCB4', outline='black', tags='game')
        # Hat
        self.canvas.create_rectangle(x-3, head_y, x+23, head_y+8,
            fill='red', outline='darkred', tags='game')
        # Eye
        if self.player['facing_right']:
            self.canvas.create_oval(x+12, head_y+8, x+16, head_y+12,
                fill='black', tags='game')
        else:
            self.canvas.create_oval(x+4, head_y+8, x+8, head_y+12,
                fill='black', tags='game')
                
        # Update UI
        self.canvas.itemconfig(self.score_text, text=f'Score: {self.score}')
        self.canvas.itemconfig(self.coins_text, text=f'Coins: {self.coins}')
        self.canvas.itemconfig(self.lives_text, text=f'Lives: {self.lives}')
        self.canvas.itemconfig(self.level_text, text=f'Level {self.current_level + 1}')
        
        # Game over screen
        if self.game_over:
            self.canvas.create_rectangle(150, 100, 450, 300,
                fill='black', outline='white', width=4, tags='game')
            self.canvas.create_text(300, 150, text='GAME OVER',
                fill='red', font=('Arial', 32, 'bold'), tags='game')
            self.canvas.create_text(300, 200, text=f'Final Score: {self.score}',
                fill='white', font=('Arial', 20), tags='game')
            self.canvas.create_text(300, 250, text='Press ESC to exit',
                fill='yellow', font=('Arial', 16), tags='game')
                
        # Level complete screen
        elif self.level_complete:
            self.canvas.create_rectangle(150, 100, 450, 300,
                fill='black', outline='white', width=4, tags='game')
            self.canvas.create_text(300, 150, text='LEVEL COMPLETE!',
                fill='green', font=('Arial', 28, 'bold'), tags='game')
            self.canvas.create_text(300, 200, text=f'Score: {self.score}',
                fill='white', font=('Arial', 20), tags='game')
            self.canvas.create_text(300, 250, text='Press SPACE for next level',
                fill='yellow', font=('Arial', 16), tags='game')
                
        # Win screen
        elif self.game_won:
            self.canvas.create_rectangle(150, 100, 450, 300,
                fill='black', outline='white', width=4, tags='game')
            self.canvas.create_text(300, 150, text='CONGRATULATIONS!',
                fill='gold', font=('Arial', 28, 'bold'), tags='game')
            self.canvas.create_text(300, 200, text='You Won!',
                fill='white', font=('Arial', 32, 'bold'), tags='game')
            self.canvas.create_text(300, 250, text=f'Final Score: {self.score}',
                fill='gold', font=('Arial', 20), tags='game')
            self.canvas.create_text(300, 300, text='Press ESC to exit',
                fill='yellow', font=('Arial', 16), tags='game')
                
    def game_loop(self):
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time
        
        if not self.game_over and not self.level_complete and not self.game_won:
            self.update_player(dt)
            self.update_enemies(dt)
            self.update_coins(dt)
            self.check_goal()
            
        self.draw()
        
        # Handle level transitions
        if self.level_complete:
            self.root.bind('<KeyPress-space>', lambda e: self.next_level())
        if self.game_over or self.game_won:
            self.root.bind('<KeyPress-Escape>', lambda e: self.root.quit())
            
        # 60 FPS
        self.root.after(16, self.game_loop)
        
    def next_level(self):
        if self.current_level < len(self.levels) - 1:
            self.load_level(self.current_level + 1)
            self.level_complete = False
            self.root.unbind('<KeyPress-space>')
        else:
            # Game won!
            self.game_won = True
            
    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    game = MarioGame()
    game.run()

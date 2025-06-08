import tkinter as tk
import time
import random

class MarioGame:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Super Mario Bros. 3 Clone")
        self.root.geometry("800x600")
        self.root.resizable(False, False)
        
        self.canvas = tk.Canvas(self.root, width=800, height=600, bg='#5C94FC')
        self.canvas.pack()
        
        # Game state
        self.running = True
        self.world = 1
        self.level = 1
        self.lives = 3
        self.coins = 0
        self.score = 0
        self.game_over = False
        self.level_complete = False
        self.game_won = False
        self.mushrooms = 0
        self.fire_flowers = 0
        self.stars = 0
        
        # Physics
        self.gravity = 0.8
        self.jump_strength = -13
        self.move_speed = 4
        self.max_velocity = 8
        
        # Player
        self.player = {
            'x': 50, 'y': 300, 'vx': 0, 'vy': 0,
            'width': 20, 'height': 30,
            'on_ground': False, 'facing_right': True,
            'immune': False, 'immune_timer': 0, 'power_level': 0  # 0: small, 1: mushroom, 2: fire, 3: tanooki
        }
        
        # Game structure
        self.worlds = {
            1: {"name": "World 1", "levels": {1: self.create_ground_level(), 2: self.create_ground_level(), 3: self.create_ground_level()}},
            2: {"name": "World 2", "levels": {1: self.create_cloud_level(), 'airship': self.create_airship_level()}},
            3: {"name": "World 3", "levels": {1: self.create_desert_level(), 2: self.create_water_level(), 3: self.create_pipe_level()}},
            4: {"name": "World 4", "levels": {1: self.create_underground_level(), 'castle': self.create_castle_level()}},
            5: {"name": "World 5", "levels": {1: self.create_ground_level(), 2: self.create_underground_level(), 3: self.create_ground_level()}},
            6: {"name": "World 6", "levels": {1: self.create_cloud_level(), 'castle': self.create_castle_level()}},
            7: {"name": "World 7", "levels": {1: self.create_ground_level(), 2: self.create_cloud_level(), 'castle': self.create_castle_level()}},
            8: {"name": "World 8", "levels": {'castle': self.create_castle_level()}}
        }
        
        self.load_level(self.world, self.level)
        
        # Controls
        self.keys = {'Left': False, 'Right': False, 'Up': False, 'space': False}
        self.root.bind('<KeyPress>', self.key_press)
        self.root.bind('<KeyRelease>', self.key_release)
        
        # UI elements
        self.create_ui()
        
        # Start game loop
        self.last_time = time.time()
        self.game_loop()
        
    # Level creation functions
    def create_ground_level(self):
        return {
            'platforms': [
                {'x': 0, 'y': 450, 'width': 300, 'height': 50, 'type': 'ground'},
                {'x': 350, 'y': 450, 'width': 200, 'height': 50, 'type': 'ground'},
                {'x': 200, 'y': 380, 'width': 100, 'height': 20, 'type': 'block'},
                {'x': 400, 'y': 350, 'width': 80, 'height': 20, 'type': 'block'},
                {'x': 600, 'y': 450, 'width': 400, 'height': 50, 'type': 'ground'},
                {'x': 750, 'y': 380, 'width': 100, 'height': 20, 'type': 'block'},
                {'x': 900, 'y': 320, 'width': 120, 'height': 20, 'type': 'block'},
                {'x': 1100, 'y': 450, 'width': 300, 'height': 50, 'type': 'ground'},
            ],
            'enemies': [
                {'x': 400, 'y': 430, 'vx': -1, 'type': 'goomba'},
                {'x': 700, 'y': 430, 'vx': 1, 'type': 'goomba'},
                {'x': 950, 'y': 300, 'vx': -1, 'type': 'koopa'},
            ],
            'coins': [
                {'x': 250, 'y': 350}, {'x': 440, 'y': 320},
                {'x': 800, 'y': 350}, {'x': 960, 'y': 290},
                {'x': 1200, 'y': 400}, {'x': 1250, 'y': 400},
            ],
            'special_blocks': [
                {'x': 500, 'y': 350, 'type': 'coin_block'},
                {'x': 550, 'y': 350, 'type': 'mushroom_block'},
            ],
            'pipes': [
                {'x': 300, 'y': 380, 'width': 60, 'height': 120, 'type': 'green'},
                {'x': 650, 'y': 380, 'width': 60, 'height': 120, 'type': 'green'},
            ],
            'goal': {'x': 1350, 'y': 400, 'width': 40, 'height': 80},
            'background': 'ground',
            'music': 'overworld'
        }
        
    def create_castle_level(self):
        return {
            'platforms': [
                {'x': 0, 'y': 450, 'width': 800, 'height': 50, 'type': 'ground'},
                {'x': 300, 'y': 350, 'width': 100, 'height': 20, 'type': 'block'},
                {'x': 500, 'y': 300, 'width': 80, 'height': 20, 'type': 'block'},
            ],
            'enemies': [
                {'x': 400, 'y': 430, 'vx': -1, 'type': 'bowser'},
                {'x': 600, 'y': 430, 'vx': 1, 'type': 'goomba'},
            ],
            'coins': [
                {'x': 350, 'y': 320}, {'x': 400, 'y': 320},
                {'x': 550, 'y': 270}, {'x': 600, 'y': 270},
            ],
            'special_blocks': [
                {'x': 350, 'y': 320, 'type': 'coin_block'},
                {'x': 550, 'y': 270, 'type': 'mushroom_block'},
            ],
            'pipes': [],
            'goal': {'x': 700, 'y': 400, 'width': 60, 'height': 100},
            'background': 'castle',
            'music': 'castle'
        }
        
    def create_airship_level(self):
        return {
            'platforms': [
                {'x': 0, 'y': 450, 'width': 200, 'height': 50, 'type': 'ground'},
                {'x': 300, 'y': 400, 'width': 100, 'height': 20, 'type': 'block'},
                {'x': 500, 'y': 350, 'width': 80, 'height': 20, 'type': 'block'},
                {'x': 700, 'y': 450, 'width': 200, 'height': 50, 'type': 'ground'},
            ],
            'enemies': [
                {'x': 400, 'y': 380, 'vx': -1, 'type': 'koopa'},
                {'x': 600, 'y': 330, 'vx': 1, 'type': 'koopa'},
            ],
            'coins': [
                {'x': 350, 'y': 380}, {'x': 400, 'y': 380},
                {'x': 550, 'y': 330}, {'x': 600, 'y': 330},
            ],
            'special_blocks': [
                {'x': 350, 'y': 380, 'type': 'coin_block'},
                {'x': 550, 'y': 330, 'type': 'fire_block'},
            ],
            'pipes': [],
            'goal': {'x': 850, 'y': 400, 'width': 40, 'height': 80},
            'background': 'airship',
            'music': 'airship'
        }
        
    def create_cloud_level(self):
        return {
            'platforms': [
                {'x': 0, 'y': 450, 'width': 200, 'height': 50, 'type': 'ground'},
                {'x': 300, 'y': 350, 'width': 100, 'height': 20, 'type': 'block'},
                {'x': 500, 'y': 300, 'width': 80, 'height': 20, 'type': 'block'},
                {'x': 700, 'y': 350, 'width': 100, 'height': 20, 'type': 'block'},
                {'x': 900, 'y': 450, 'width': 200, 'height': 50, 'type': 'ground'},
            ],
            'enemies': [
                {'x': 400, 'y': 330, 'vx': -1, 'type': 'koopa'},
                {'x': 600, 'y': 280, 'vx': 1, 'type': 'koopa'},
            ],
            'coins': [
                {'x': 350, 'y': 320}, {'x': 400, 'y': 320},
                {'x': 550, 'y': 270}, {'x': 600, 'y': 270},
            ],
            'special_blocks': [
                {'x': 350, 'y': 320, 'type': 'coin_block'},
                {'x': 550, 'y': 270, 'type': 'fire_block'},
            ],
            'pipes': [
                {'x': 200, 'y': 380, 'width': 60, 'height': 120, 'type': 'green'},
            ],
            'goal': {'x': 1050, 'y': 400, 'width': 40, 'height': 80},
            'background': 'cloud',
            'music': 'cloud'
        }
        
    def create_desert_level(self):
        return {
            'platforms': [
                {'x': 0, 'y': 450, 'width': 300, 'height': 50, 'type': 'ground'},
                {'x': 350, 'y': 450, 'width': 200, 'height': 50, 'type': 'ground'},
                {'x': 200, 'y': 380, 'width': 100, 'height': 20, 'type': 'block'},
                {'x': 400, 'y': 350, 'width': 80, 'height': 20, 'type': 'block'},
                {'x': 600, 'y': 450, 'width': 400, 'height': 50, 'type': 'ground'},
                {'x': 750, 'y': 380, 'width': 100, 'height': 20, 'type': 'block'},
                {'x': 900, 'y': 320, 'width': 120, 'height': 20, 'type': 'block'},
                {'x': 1100, 'y': 450, 'width': 300, 'height': 50, 'type': 'ground'},
            ],
            'enemies': [
                {'x': 400, 'y': 430, 'vx': -1, 'type': 'goomba'},
                {'x': 700, 'y': 430, 'vx': 1, 'type': 'goomba'},
                {'x': 950, 'y': 300, 'vx': -1, 'type': 'piranha'},
            ],
            'coins': [
                {'x': 250, 'y': 350}, {'x': 440, 'y': 320},
                {'x': 800, 'y': 350}, {'x': 960, 'y': 290},
                {'x': 1200, 'y': 400}, {'x': 1250, 'y': 400},
            ],
            'special_blocks': [
                {'x': 500, 'y': 350, 'type': 'coin_block'},
                {'x': 550, 'y': 350, 'type': 'mushroom_block'},
            ],
            'pipes': [
                {'x': 300, 'y': 380, 'width': 60, 'height': 120, 'type': 'green'},
                {'x': 650, 'y': 380, 'width': 60, 'height': 120, 'type': 'green'},
            ],
            'goal': {'x': 1350, 'y': 400, 'width': 40, 'height': 80},
            'background': 'desert',
            'music': 'desert'
        }
        
    def create_water_level(self):
        return {
            'platforms': [
                {'x': 0, 'y': 450, 'width': 800, 'height': 50, 'type': 'ground'},
                {'x': 100, 'y': 350, 'width': 50, 'height': 20, 'type': 'block'},
                {'x': 300, 'y': 300, 'width': 50, 'height': 20, 'type': 'block'},
                {'x': 500, 'y': 350, 'width': 50, 'height': 20, 'type': 'block'},
                {'x': 700, 'y': 300, 'width': 50, 'height': 20, 'type': 'block'},
            ],
            'enemies': [
                {'x': 200, 'y': 330, 'vx': -1, 'type': 'fish'},
                {'x': 400, 'y': 280, 'vx': 1, 'type': 'fish'},
                {'x': 600, 'y': 330, 'vx': -1, 'type': 'fish'},
            ],
            'coins': [
                {'x': 150, 'y': 320}, {'x': 350, 'y': 270},
                {'x': 550, 'y': 320}, {'x': 750, 'y': 270},
            ],
            'special_blocks': [
                {'x': 150, 'y': 320, 'type': 'coin_block'},
                {'x': 350, 'y': 270, 'type': 'star_block'},
            ],
            'pipes': [
                {'x': 400, 'y': 380, 'width': 60, 'height': 120, 'type': 'green'},
            ],
            'goal': {'x': 800, 'y': 400, 'width': 40, 'height': 80},
            'background': 'water',
            'music': 'water'
        }
        
    def create_pipe_level(self):
        return {
            'platforms': [
                {'x': 0, 'y': 450, 'width': 200, 'height': 50, 'type': 'ground'},
                {'x': 300, 'y': 400, 'width': 100, 'height': 50, 'type': 'block'},
                {'x': 500, 'y': 350, 'width': 100, 'height': 50, 'type': 'block'},
                {'x': 700, 'y': 400, 'width': 100, 'height': 50, 'type': 'block'},
                {'x': 900, 'y': 450, 'width': 200, 'height': 50, 'type': 'ground'},
            ],
            'enemies': [
                {'x': 400, 'y': 380, 'vx': -1, 'type': 'goomba'},
                {'x': 600, 'y': 330, 'vx': 1, 'type': 'goomba'},
            ],
            'coins': [
                {'x': 350, 'y': 350}, {'x': 400, 'y': 350},
                {'x': 550, 'y': 300}, {'x': 600, 'y': 300},
            ],
            'special_blocks': [
                {'x': 350, 'y': 350, 'type': 'coin_block'},
                {'x': 550, 'y': 300, 'type': 'tanooki_block'},
            ],
            'pipes': [
                {'x': 250, 'y': 380, 'width': 60, 'height': 120, 'type': 'green'},
                {'x': 450, 'y': 330, 'width': 60, 'height': 120, 'type': 'green'},
                {'x': 650, 'y': 380, 'width': 60, 'height': 120, 'type': 'green'},
            ],
            'goal': {'x': 1000, 'y': 400, 'width': 40, 'height': 80},
            'background': 'pipe',
            'music': 'pipe'
        }
        
    def create_underground_level(self):
        return {
            'platforms': [
                {'x': 0, 'y': 450, 'width': 800, 'height': 50, 'type': 'ground'},
                {'x': 100, 'y': 400, 'width': 100, 'height': 20, 'type': 'block'},
                {'x': 300, 'y': 350, 'width': 100, 'height': 20, 'type': 'block'},
                {'x': 500, 'y': 400, 'width': 100, 'height': 20, 'type': 'block'},
                {'x': 700, 'y': 350, 'width': 100, 'height': 20, 'type': 'block'},
            ],
            'enemies': [
                {'x': 200, 'y': 380, 'vx': -1, 'type': 'koopa'},
                {'x': 400, 'y': 330, 'vx': 1, 'type': 'koopa'},
                {'x': 600, 'y': 380, 'vx': -1, 'type': 'koopa'},
            ],
            'coins': [
                {'x': 150, 'y': 370}, {'x': 350, 'y': 320},
                {'x': 550, 'y': 370}, {'x': 750, 'y': 320},
            ],
            'special_blocks': [
                {'x': 150, 'y': 370, 'type': 'coin_block'},
                {'x': 550, 'y': 370, 'type': 'fire_block'},
            ],
            'pipes': [
                {'x': 350, 'y': 380, 'width': 60, 'height': 120, 'type': 'green'},
            ],
            'goal': {'x': 800, 'y': 400, 'width': 40, 'height': 80},
            'background': 'underground',
            'music': 'underground'
        }
        
    def load_level(self, world_num, level_num):
        self.world = world_num
        self.level = level_num
        world = self.worlds[world_num]
        
        if isinstance(level_num, int):
            level = world['levels'][level_num]
        elif level_num == 'airship':
            level = world['levels']['airship']
        elif level_num == 'castle':
            level = world['levels']['castle']
        else:
            level = world['levels'][1]
            
        self.player['x'] = 50
        self.player['y'] = 300
        self.player['vx'] = 0
        self.player['vy'] = 0
        self.player['immune'] = False
        self.player['immune_timer'] = 0
        self.camera_x = 0
        
        # Copy level data
        self.platforms = [p.copy() for p in level['platforms']]
        self.enemies = [e.copy() for e in level['enemies']]
        self.coin_objects = [c.copy() for c in level['coins']]
        self.special_blocks = [s.copy() for s in level.get('special_blocks', [])]
        self.pipes = [p.copy() for p in level.get('pipes', [])]
        self.goal = level['goal'].copy()
        self.background = level['background']
        self.level_complete = False
        
    def create_ui(self):
        self.score_text = self.canvas.create_text(10, 10, anchor='nw', 
            text=f'Score: {self.score}', fill='white', font=('Arial', 14, 'bold'))
        self.coins_text = self.canvas.create_text(10, 30, anchor='nw',
            text=f'Coins: {self.coins}', fill='yellow', font=('Arial', 14, 'bold'))
        self.lives_text = self.canvas.create_text(10, 50, anchor='nw',
            text=f'Lives: {self.lives}', fill='red', font=('Arial', 14, 'bold'))
        self.power_text = self.canvas.create_text(10, 70, anchor='nw',
            text=f'Power: {"SMALL" if self.player["power_level"] == 0 else "MUSHROOM" if self.player["power_level"] == 1 else "FIRE" if self.player["power_level"] == 2 else "TANOOKI"}',
            fill='white', font=('Arial', 14, 'bold'))
        self.world_text = self.canvas.create_text(300, 10, anchor='n',
            text=f'World {self.world}-{self.level}', fill='white', font=('Arial', 16, 'bold'))
            
    def update_player(self, dt):
        # Apply gravity
        self.player['vy'] += self.gravity
        if self.player['vy'] > self.max_velocity:
            self.player['vy'] = self.max_velocity
            
        # Handle movement
        if self.keys['Left']:
            self.player['vx'] = -self.move_speed
            self.player['facing_right'] = False
        elif self.keys['Right']:
            self.player['vx'] = self.move_speed
            self.player['facing_right'] = True
        else:
            self.player['vx'] = 0
            
        # Handle jumping
        if self.keys['Up'] and self.player['on_ground']:
            self.player['vy'] = self.jump_strength
            self.player['on_ground'] = False
            
        # Update position
        self.player['x'] += self.player['vx']
        self.player['y'] += self.player['vy']
        
        # Reset ground state
        self.player['on_ground'] = False
        
        # Check collisions with platforms
        for platform in self.platforms:
            self.resolve_collision(platform)
            
        # Check collisions with pipes
        for pipe in self.pipes:
            self.resolve_collision(pipe)
            
        # Check collisions with special blocks
        for block in self.special_blocks:
            if self.check_collision(self.player, block):
                if self.player['vy'] < 0:  # Hitting from below
                    self.activate_block(block)
                    
        # Check if player fell off the screen
        if self.player['y'] > 600:
            self.die()
            
        # Update camera
        self.camera_x = self.player['x'] - 400
        if self.camera_x < 0:
            self.camera_x = 0
            
        # Update immunity timer
        if self.player['immune']:
            self.player['immune_timer'] += dt
            if self.player['immune_timer'] > 2.0:  # 2 seconds of immunity
                self.player['immune'] = False
                self.player['immune_timer'] = 0
    
    def resolve_collision(self, obj):
        if not self.check_collision(self.player, obj):
            return
            
        # Calculate collision depths
        dx1 = abs(self.player['x'] + self.player['width'] - obj['x'])
        dx2 = abs(obj['x'] + obj['width'] - self.player['x'])
        dy1 = abs(self.player['y'] + self.player['height'] - obj['y'])
        dy2 = abs(obj['y'] + obj['height'] - self.player['y'])
        
        # Find the minimum overlap
        min_overlap = min(dx1, dx2, dy1, dy2)
        
        # Resolve collision based on the minimum overlap
        if min_overlap == dy1:  # Hit from above (player on top of platform)
            self.player['y'] = obj['y'] - self.player['height']
            self.player['vy'] = 0
            self.player['on_ground'] = True
        elif min_overlap == dy2: # Hit from below
            self.player['y'] = obj['y'] + obj['height']
            self.player['vy'] = 0
        elif min_overlap == dx1: # Hit from the right
            self.player['x'] = obj['x'] - self.player['width']
        elif min_overlap == dx2: # Hit from the left
            self.player['x'] = obj['x'] + obj['width']
    
    def activate_block(self, block):
        if block['type'] == 'coin_block':
            self.coins += 1
            self.score += 10
            block['type'] = 'empty_block'
        elif block['type'] == 'mushroom_block':
            if self.player['power_level'] < 1:
                self.player['power_level'] = 1
            self.mushrooms += 1
            block['type'] = 'empty_block'
        elif block['type'] == 'fire_block':
            if self.player['power_level'] < 2:
                self.player['power_level'] = 2
            self.fire_flowers += 1
            block['type'] = 'empty_block'
        elif block['type'] == 'star_block':
            self.stars += 1
            self.player['immune'] = True
            block['type'] = 'empty_block'
        elif block['type'] == 'tanooki_block':
            if self.player['power_level'] < 3:
                self.player['power_level'] = 3
            block['type'] = 'empty_block'
    
    def draw(self):
        self.canvas.delete('game')
        
        # Draw background based on world
        if self.background == 'ground':
            # Draw sky gradient
            for i in range(10):
                color = f'#{92-i*3:02x}{148-i*3:02x}{252-i*3:02x}'
                self.canvas.create_rectangle(0, i*60, 800, (i+1)*60, 
                    fill=color, outline='', tags='game')
            
            # Draw clouds
            for i in range(5):
                x = (i * 300 - self.camera_x * 0.3) % 2000 - 100
                self.canvas.create_oval(x, 80 + i * 50, x+100, 130 + i * 50, 
                    fill='white', outline='', tags='game')
                
        elif self.background == 'cloud':
            # Draw cloud level background
            for i in range(5):
                color = f'#{100+i*20:02x}{180+i*10:02x}{255:02x}'
                self.canvas.create_rectangle(0, i*120, 800, (i+1)*120, 
                    fill=color, outline='', tags='game')
                    
        elif self.background == 'castle':
            # Draw castle background
            self.canvas.create_rectangle(0, 0, 800, 600, fill='#301934', outline='', tags='game')
                    
        elif self.background == 'airship':
            # Draw airship background
            self.canvas.create_rectangle(0, 0, 800, 600, fill='#202050', outline='', tags='game')
                    
        elif self.background == 'desert':
            # Draw desert background
            self.canvas.create_rectangle(0, 0, 800, 600, fill='#E0AC69', outline='', tags='game')
                    
        elif self.background == 'water':
            # Draw water background
            self.canvas.create_rectangle(0, 0, 800, 600, fill='#6495ED', outline='', tags='game')
                    
        elif self.background == 'pipe':
            # Draw pipe level background
            self.canvas.create_rectangle(0, 0, 800, 600, fill='#306082', outline='', tags='game')
                    
        elif self.background == 'underground':
            # Draw underground background
            self.canvas.create_rectangle(0, 0, 800, 600, fill='#303030', outline='', tags='game')
        
        # Draw platforms
        for platform in self.platforms:
            x = platform['x'] - self.camera_x
            if -100 < x < 900:
                if platform['type'] == 'block':
                    self.canvas.create_rectangle(x, platform['y'], 
                        x + platform['width'], platform['y'] + platform['height'],
                        fill='#8B4513', outline='#654321', width=2, tags='game')
                else:  # ground
                    self.canvas.create_rectangle(x, platform['y'], 
                        x + platform['width'], platform['y'] + platform['height'],
                        fill='#8B4513', outline='#654321', width=2, tags='game')
                    self.canvas.create_rectangle(x, platform['y'],
                        x + platform['width'], platform['y'] + 10,
                        fill='#228B22', outline='', tags='game')
                    
        # Draw pipes
        for pipe in self.pipes:
            x = pipe['x'] - self.camera_x
            if -100 < x < 900:
                # Pipe body
                self.canvas.create_rectangle(x, pipe['y'], 
                    x + pipe['width'], pipe['y'] + pipe['height'],
                    fill='#00AA00', outline='#008800', width=2, tags='game')
                
                # Pipe top
                self.canvas.create_rectangle(x-5, pipe['y']-10, 
                    x + pipe['width']+5, pipe['y'],
                    fill='#00AA00', outline='#008800', width=2, tags='game')
                    
        # Draw coins
        for coin in self.coin_objects:
            x = coin['x'] - self.camera_x
            if -50 < x < 850:
                self.canvas.create_oval(x, coin['y'], x+16, coin['y']+16,
                    fill='gold', outline='orange', width=2, tags='game')
                    
        # Draw special blocks
        for block in self.special_blocks:
            x = block['x'] - self.camera_x
            if -50 < x < 850:
                if block['type'] == 'coin_block':
                    fill_color = '#FFD700'
                elif block['type'] == 'mushroom_block':
                    fill_color = '#FF0000'
                elif block['type'] == 'fire_block':
                    fill_color = '#FF4500'
                elif block['type'] == 'star_block':
                    fill_color = '#FFFF00'
                elif block['type'] == 'tanooki_block':
                    fill_color = '#8B4513'
                else:  # empty block
                    fill_color = '#A9A9A9'
                    
                self.canvas.create_rectangle(x, block['y'], 
                    x + 30, block['y'] + 30,
                    fill=fill_color, outline='#654321', width=2, tags='game')
                    
        # Draw enemies
        for enemy in self.enemies:
            x = enemy['x'] - self.camera_x
            if -50 < x < 850:
                if enemy['type'] == 'goomba':
                    # Body
                    self.canvas.create_oval(x, enemy['y'], x+20, enemy['y']+15,
                        fill='#8B4513', outline='#654321', width=2, tags='game')
                    # Feet
                    self.canvas.create_oval(x+2, enemy['y']+12, x+8, enemy['y']+18,
                        fill='#8B4513', outline='#654321', width=1, tags='game')
                    self.canvas.create_oval(x+12, enemy['y']+12, x+18, enemy['y']+18,
                        fill='#8B4513', outline='#654321', width=1, tags='game')
                    # Eyes
                    self.canvas.create_oval(x+5, enemy['y']+4, x+8, enemy['y']+7,
                        fill='white', outline='', tags='game')
                    self.canvas.create_oval(x+12, enemy['y']+4, x+15, enemy['y']+7,
                        fill='white', outline='', tags='game')
                    
                elif enemy['type'] == 'koopa':
                    # Shell
                    self.canvas.create_oval(x, enemy['y'], x+22, enemy['y']+22,
                        fill='#00AA00', outline='#008800', width=2, tags='game')
                    # Head
                    self.canvas.create_rectangle(x+5, enemy['y']-5, x+17, enemy['y']+5,
                        fill='#00AA00', outline='#008800', width=2, tags='game')
                    # Eyes
                    self.canvas.create_oval(x+8, enemy['y']-2, x+10, enemy['y'],
                        fill='black', outline='', tags='game')
                    self.canvas.create_oval(x+12, enemy['y']-2, x+14, enemy['y'],
                        fill='black', outline='', tags='game')
                    
                elif enemy['type'] == 'fish':
                    self.canvas.create_oval(x, enemy['y'], x+20, enemy['y']+20,
                        fill='blue', outline='darkblue', width=2, tags='game')
                    self.canvas.create_oval(x+10, enemy['y']+8, x+15, enemy['y']+12,
                        fill='white', outline='', tags='game')
                    
                elif enemy['type'] == 'bowser':
                    # Body
                    self.canvas.create_rectangle(x, enemy['y'], x+40, enemy['y']+40,
                        fill='red', outline='darkred', width=2, tags='game')
                    # Head
                    self.canvas.create_rectangle(x+10, enemy['y']-10, x+30, enemy['y'],
                        fill='red', outline='darkred', width=2, tags='game')
                    # Eyes
                    self.canvas.create_oval(x+15, enemy['y']-5, x+20, enemy['y'],
                        fill='black', outline='', tags='game')
                    self.canvas.create_oval(x+20, enemy['y']-5, x+25, enemy['y'],
                        fill='black', outline='', tags='game')
                    # Spikes
                    for i in range(3):
                        self.canvas.create_polygon(
                            x+10+i*10, enemy['y']-10,
                            x+15+i*10, enemy['y']-20,
                            x+20+i*10, enemy['y']-10,
                            fill='red', outline='darkred', tags='game'
                        )
                        
                elif enemy['type'] == 'piranha':
                    # Stem
                    self.canvas.create_rectangle(x+7, enemy['y'], x+13, enemy['y']+20,
                        fill='green', outline='darkgreen', width=1, tags='game')
                    # Head
                    self.canvas.create_oval(x, enemy['y']-5, x+20, enemy['y']+15,
                        fill='green', outline='darkgreen', width=2, tags='game')
                    # Mouth
                    self.canvas.create_arc(x+2, enemy['y']+2, x+18, enemy['y']+13,
                        start=0, extent=180, fill='red', outline='darkred', tags='game')
                        
        # Draw goal
        x = self.goal['x'] - self.camera_x
        if -50 < x < 850:
            # Pole
            self.canvas.create_rectangle(x+18, self.goal['y'], x+22, self.goal['y']+self.goal['height'],
                fill='gray', outline='black', width=2, tags='game')
            # Flag
            self.canvas.create_polygon(x+22, self.goal['y'], x+60, self.goal['y']+20,
                x+22, self.goal['y']+40, fill='red', outline='darkred', width=2, tags='game')
                
        # Draw player
        x = self.player['x'] - self.camera_x
        player_color = 'red'
        if self.player['power_level'] == 1:
            player_color = '#00AA00'  # Green for mushroom
        elif self.player['power_level'] == 2:
            player_color = '#FF4500'  # Orange for fire
        elif self.player['power_level'] == 3:
            player_color = '#8B4513'  # Brown for tanooki
            
        # Draw Mario's body
        self.canvas.create_rectangle(x, self.player['y'],
            x + self.player['width'], self.player['y'] + self.player['height'],
            fill=player_color, outline='darkred', width=2, tags='game')
            
        # Draw Mario's head
        head_y = self.player['y'] - 15
        self.canvas.create_oval(x, head_y, x+20, head_y+20,
            fill='#FDBCB4', outline='black', tags='game')
            
        # Draw Mario's hat
        self.canvas.create_rectangle(x-3, head_y, x+23, head_y+8,
            fill=player_color, outline='darkred', tags='game')
            
        # Draw Mario's eye
        if self.player['facing_right']:
            self.canvas.create_oval(x+12, head_y+8, x+16, head_y+12,
                fill='black', tags='game')
        else:
            self.canvas.create_oval(x+4, head_y+8, x+8, head_y+12,
                fill='black', tags='game')
                
        # Draw mustache
        self.canvas.create_rectangle(x+4, head_y+13, x+16, head_y+15,
            fill='#663300', outline='', tags='game')
                
        # Update UI
        self.canvas.itemconfig(self.score_text, text=f'Score: {self.score}')
        self.canvas.itemconfig(self.coins_text, text=f'Coins: {self.coins}')
        self.canvas.itemconfig(self.lives_text, text=f'Lives: {self.lives}')
        self.canvas.itemconfig(self.power_text, 
            text=f'Power: {"SMALL" if self.player["power_level"] == 0 else "MUSHROOM" if self.player["power_level"] == 1 else "FIRE" if self.player["power_level"] == 2 else "TANOOKI"}')
        self.canvas.itemconfig(self.world_text, text=f'World {self.world}-{self.level}')
        
        # Game over and level complete screens
        if self.game_over:
            self.canvas.create_rectangle(150, 100, 650, 500,
                fill='black', outline='white', width=4, tags='game')
            self.canvas.create_text(400, 200, text='GAME OVER',
                fill='red', font=('Arial', 40, 'bold'), tags='game')
            self.canvas.create_text(400, 250, text=f'Final Score: {self.score}',
                fill='white', font=('Arial', 20), tags='game')
            self.canvas.create_text(400, 300, text='Press ESC to exit',
                fill='yellow', font=('Arial', 16), tags='game')
                
        elif self.level_complete:
            self.canvas.create_rectangle(150, 100, 650, 500,
                fill='black', outline='white', width=4, tags='game')
            self.canvas.create_text(400, 200, text='LEVEL COMPLETE!',
                fill='green', font=('Arial', 36, 'bold'), tags='game')
            self.canvas.create_text(400, 250, text=f'Score: {self.score}',
                fill='white', font=('Arial', 20), tags='game')
            self.canvas.create_text(400, 300, text='Press SPACE for next level',
                fill='yellow', font=('Arial', 16), tags='game')
                
        elif self.game_won:
            self.canvas.create_rectangle(150, 100, 650, 500,
                fill='black', outline='white', width=4, tags='game')
            self.canvas.create_text(400, 200, text='CONGRATULATIONS!',
                fill='gold', font=('Arial', 36, 'bold'), tags='game')
            self.canvas.create_text(400, 250, text='You Won!',
                fill='white', font=('Arial', 40, 'bold'), tags='game')
            self.canvas.create_text(400, 300, text=f'Final Score: {self.score}',
                fill='gold', font=('Arial', 20), tags='game')
            self.canvas.create_text(400, 350, text='Press ESC to exit',
                fill='yellow', font=('Arial', 16), tags='game')
                
    def check_collision(self, obj1, obj2):
        return (obj1['x'] < obj2['x'] + obj2.get('width', 30) and
                obj1['x'] + obj1['width'] > obj2['x'] and
                obj1['y'] < obj2['y'] + obj2.get('height', 30) and
                obj1['y'] + obj1['height'] > obj2['y'])
                
    def die(self):
        self.lives -= 1
        if self.lives <= 0:
            self.game_over = True
        else:
            self.load_level(self.world, self.level)
            
    def check_goal(self):
        if self.check_collision(self.player, self.goal):
            self.level_complete = True
            self.score += 1000
            
    def update_enemies(self, dt):
        for enemy in self.enemies[:]:
            # Move enemy
            enemy['x'] += enemy['vx']
            
            # Check if enemy should turn around
            on_platform = False
            for platform in self.platforms:
                if (enemy['x'] + 10 > platform['x'] and 
                    enemy['x'] + 10 < platform['x'] + platform['width'] and
                    abs(enemy['y'] + 20 - platform['y']) < 5):
                    on_platform = True
                    break
                    
            if not on_platform:
                enemy['vx'] *= -1
                
            # Check collision with player
            if self.check_collision(self.player, enemy):
                if self.player['vy'] > 0 and self.player['y'] < enemy['y']:
                    # Player jumped on enemy
                    self.enemies.remove(enemy)
                    self.score += 100
                    self.player['vy'] = self.jump_strength / 2
                else:
                    # Player hit by enemy
                    if not self.player['immune']:
                        if self.player['power_level'] > 0:
                            self.player['power_level'] = 0
                            self.player['immune'] = True
                        else:
                            self.die()
                        
    def update_coins(self, dt):
        for coin in self.coin_objects[:]:
            if self.check_collision(self.player, coin):
                self.coin_objects.remove(coin)
                self.coins += 1
                self.score += 10
                
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
        elif self.game_over or self.game_won:
            self.root.bind('<KeyPress-Escape>', lambda e: self.root.quit())
            
        self.root.after(16, self.game_loop)
        
    def next_level(self):
        self.root.unbind('<KeyPress-space>')
        if self.level == len(self.worlds[self.world]['levels']):
            if self.world < len(self.worlds):
                self.world += 1
                self.level = 1
            else:
                self.game_won = True
                return
        else:
            self.level += 1
            
        self.load_level(self.world, self.level)
        self.level_complete = False
                
    def key_press(self, event):
        if event.keysym in self.keys:
            self.keys[event.keysym] = True
            
    def key_release(self, event):
        if event.keysym in self.keys:
            self.keys[event.keysym] = False
            
    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    game = MarioGame()
    game.run()

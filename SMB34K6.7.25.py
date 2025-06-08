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
        self.gravity = 0.5
        self.jump_strength = -12
        self.move_speed = 4
        
        # Player
        self.player = {
            'x': 50, 'y': 300, 'vx': 0, 'vy': 0,
            'width': 20, 'height': 30,
            'on_ground': False, 'facing_right': True,
            'imune': False, 'power_level': 0  # 0: small, 1: mushroom, 2: fire, 3: tanooki
        }
        
        # Game structure - 8 worlds with multiple levels each
        self.worlds = {
            1: {
                "name": "World 1",
                "levels": {
                    1: self.create_world1_level1(),
                    2: self.create_world1_level2(),
                    3: self.create_world1_level3(),
                    'castle': self.create_castle_level()
                }
            },
            2: {
                "name": "World 2",
                "levels": {
                    1: self.create_world2_level1(),
                    'airship': self.create_airship_level(),
                    'castle': self.create_castle_level()
                }
            },
            3: {
                "name": "World 3",
                "levels": {
                    1: self.create_world3_level1(),
                    2: self.create_world3_level2(),
                    3: self.create_world3_level3(),
                    'castle': self.create_castle_level()
                }
            },
            4: {
                "name": "World 4",
                "levels": {
                    1: self.create_world4_level1(),
                    'airship': self.create_airship_level(),
                    'castle': self.create_castle_level()
                }
            },
            5: {
                "name": "World 5",
                "levels": {
                    1: self.create_world5_level1(),
                    2: self.create_world5_level2(),
                    3: self.create_world5_level3(),
                    'castle': self.create_castle_level()
                }
            },
            6: {
                "name": "World 6",
                "levels": {
                    1: self.create_world6_level1(),
                    'castle': self.create_castle_level()
                }
            },
            7: {
                "name": "World 7",
                "levels": {
                    1: self.create_world7_level1(),
                    2: self.create_world7_level2(),
                    'castle': self.create_castle_level()
                }
            },
            8: {
                "name": "World 8",
                "levels": {
                    1: self.create_world8_level1(),
                    'castle': self.create_castle_level()
                }
            }
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
    def create_world1_level1(self):
        return self.create_ground_level()
        
    def create_world1_level2(self):
        return self.create_ground_level()
        
    def create_world1_level3(self):
        return self.create_ground_level()
        
    def create_world2_level1(self):
        return self.create_cloud_level()
        
    def create_world3_level1(self):
        return self.create_desert_level()
        
    def create_world3_level2(self):
        return self.create_water_level()
        
    def create_world3_level3(self):
        return self.create_pipe_level()
        
    def create_world4_level1(self):
        return self.create_ground_level()
        
    def create_world5_level1(self):
        return self.create_ground_level()
        
    def create_world5_level2(self):
        return self.create_underground_level()
        
    def create_world5_level3(self):
        return self.create_ground_level()
        
    def create_world6_level1(self):
        return self.create_ground_level()
        
    def create_world7_level1(self):
        return self.create_ground_level()
        
    def create_world7_level2(self):
        return self.create_cloud_level()
        
    def create_world8_level1(self):
        return self.create_ground_level()
        
    def create_castle_level(self):
        return {
            'platforms': [
                {'x': 0, 'y': 350, 'width': 800, 'height': 50, 'type': 'ground'},
                {'x': 300, 'y': 250, 'width': 100, 'height': 20, 'type': 'block'},
                {'x': 500, 'y': 200, 'width': 80, 'height': 20, 'type': 'block'},
            ],
            'enemies': [
                {'x': 400, 'y': 330, 'vx': -1, 'type': 'bowser'},
                {'x': 600, 'y': 330, 'vx': 1, 'type': 'goomba'},
            ],
            'coins': [
                {'x': 350, 'y': 220}, {'x': 400, 'y': 220},
                {'x': 550, 'y': 170}, {'x': 600, 'y': 170},
            ],
            'special_blocks': [
                {'x': 350, 'y': 220, 'type': 'coin_block'},
                {'x': 550, 'y': 170, 'type': 'mushroom_block'},
            ],
            'goal': {'x': 700, 'y': 300},
            'background': 'castle',
            'music': 'castle'
        }
        
    def create_airship_level(self):
        return {
            'platforms': [
                {'x': 0, 'y': 350, 'width': 200, 'height': 50, 'type': 'ground'},
                {'x': 300, 'y': 300, 'width': 100, 'height': 20, 'type': 'block'},
                {'x': 500, 'y': 250, 'width': 80, 'height': 20, 'type': 'block'},
                {'x': 700, 'y': 350, 'width': 200, 'height': 50, 'type': 'ground'},
            ],
            'enemies': [
                {'x': 400, 'y': 280, 'vx': -1, 'type': 'koopa'},
                {'x': 600, 'y': 230, 'vx': 1, 'type': 'koopa'},
            ],
            'coins': [
                {'x': 350, 'y': 280}, {'x': 400, 'y': 280},
                {'x': 550, 'y': 230}, {'x': 600, 'y': 230},
            ],
            'special_blocks': [
                {'x': 350, 'y': 280, 'type': 'coin_block'},
                {'x': 550, 'y': 230, 'type': 'fire_block'},
            ],
            'goal': {'x': 850, 'y': 300},
            'background': 'airship',
            'music': 'airship'
        }
        
    def create_ground_level(self):
        return {
            'platforms': [
                {'x': 0, 'y': 350, 'width': 300, 'height': 50, 'type': 'ground'},
                {'x': 350, 'y': 350, 'width': 200, 'height': 50, 'type': 'ground'},
                {'x': 200, 'y': 280, 'width': 100, 'height': 20, 'type': 'block'},
                {'x': 400, 'y': 250, 'width': 80, 'height': 20, 'type': 'block'},
                {'x': 600, 'y': 350, 'width': 400, 'height': 50, 'type': 'ground'},
                {'x': 750, 'y': 280, 'width': 100, 'height': 20, 'type': 'block'},
                {'x': 900, 'y': 220, 'width': 120, 'height': 20, 'type': 'block'},
                {'x': 1100, 'y': 350, 'width': 300, 'height': 50, 'type': 'ground'},
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
            'special_blocks': [
                {'x': 500, 'y': 250, 'type': 'coin_block'},
                {'x': 550, 'y': 250, 'type': 'mushroom_block'},
            ],
            'goal': {'x': 1350, 'y': 300},
            'background': 'ground',
            'music': 'overworld'
        }
        
    def create_cloud_level(self):
        return {
            'platforms': [
                {'x': 0, 'y': 350, 'width': 200, 'height': 50, 'type': 'ground'},
                {'x': 300, 'y': 250, 'width': 100, 'height': 20, 'type': 'block'},
                {'x': 500, 'y': 200, 'width': 80, 'height': 20, 'type': 'block'},
                {'x': 700, 'y': 250, 'width': 100, 'height': 20, 'type': 'block'},
                {'x': 900, 'y': 350, 'width': 200, 'height': 50, 'type': 'ground'},
            ],
            'enemies': [
                {'x': 400, 'y': 230, 'vx': -1, 'type': 'koopa'},
                {'x': 600, 'y': 180, 'vx': 1, 'type': 'koopa'},
            ],
            'coins': [
                {'x': 350, 'y': 220}, {'x': 400, 'y': 220},
                {'x': 550, 'y': 170}, {'x': 600, 'y': 170},
            ],
            'special_blocks': [
                {'x': 350, 'y': 220, 'type': 'coin_block'},
                {'x': 550, 'y': 170, 'type': 'fire_block'},
            ],
            'goal': {'x': 1050, 'y': 300},
            'background': 'cloud',
            'music': 'cloud'
        }
        
    def create_desert_level(self):
        return {
            'platforms': [
                {'x': 0, 'y': 350, 'width': 300, 'height': 50, 'type': 'ground'},
                {'x': 350, 'y': 350, 'width': 200, 'height': 50, 'type': 'ground'},
                {'x': 200, 'y': 280, 'width': 100, 'height': 20, 'type': 'block'},
                {'x': 400, 'y': 250, 'width': 80, 'height': 20, 'type': 'block'},
                {'x': 600, 'y': 350, 'width': 400, 'height': 50, 'type': 'ground'},
                {'x': 750, 'y': 280, 'width': 100, 'height': 20, 'type': 'block'},
                {'x': 900, 'y': 220, 'width': 120, 'height': 20, 'type': 'block'},
                {'x': 1100, 'y': 350, 'width': 300, 'height': 50, 'type': 'ground'},
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
            'special_blocks': [
                {'x': 500, 'y': 250, 'type': 'coin_block'},
                {'x': 550, 'y': 250, 'type': 'mushroom_block'},
            ],
            'goal': {'x': 1350, 'y': 300},
            'background': 'desert',
            'music': 'desert'
        }
        
    def create_water_level(self):
        return {
            'platforms': [
                {'x': 0, 'y': 350, 'width': 800, 'height': 50, 'type': 'ground'},
                {'x': 100, 'y': 250, 'width': 50, 'height': 20, 'type': 'block'},
                {'x': 300, 'y': 200, 'width': 50, 'height': 20, 'type': 'block'},
                {'x': 500, 'y': 250, 'width': 50, 'height': 20, 'type': 'block'},
                {'x': 700, 'y': 200, 'width': 50, 'height': 20, 'type': 'block'},
            ],
            'enemies': [
                {'x': 200, 'y': 230, 'vx': -1, 'type': 'fish'},
                {'x': 400, 'y': 180, 'vx': 1, 'type': 'fish'},
                {'x': 600, 'y': 230, 'vx': -1, 'type': 'fish'},
            ],
            'coins': [
                {'x': 150, 'y': 220}, {'x': 350, 'y': 170},
                {'x': 550, 'y': 220}, {'x': 750, 'y': 170},
            ],
            'special_blocks': [
                {'x': 150, 'y': 220, 'type': 'coin_block'},
                {'x': 350, 'y': 170, 'type': 'star_block'},
            ],
            'goal': {'x': 800, 'y': 300},
            'background': 'water',
            'music': 'water'
        }
        
    def create_pipe_level(self):
        return {
            'platforms': [
                {'x': 0, 'y': 350, 'width': 200, 'height': 50, 'type': 'ground'},
                {'x': 300, 'y': 300, 'width': 100, 'height': 50, 'type': 'block'},
                {'x': 500, 'y': 250, 'width': 100, 'height': 50, 'type': 'block'},
                {'x': 700, 'y': 300, 'width': 100, 'height': 50, 'type': 'block'},
                {'x': 900, 'y': 350, 'width': 200, 'height': 50, 'type': 'ground'},
            ],
            'enemies': [
                {'x': 400, 'y': 280, 'vx': -1, 'type': 'goomba'},
                {'x': 600, 'y': 230, 'vx': 1, 'type': 'goomba'},
            ],
            'coins': [
                {'x': 350, 'y': 250}, {'x': 400, 'y': 250},
                {'x': 550, 'y': 200}, {'x': 600, 'y': 200},
            ],
            'special_blocks': [
                {'x': 350, 'y': 250, 'type': 'coin_block'},
                {'x': 550, 'y': 200, 'type': 'tanooki_block'},
            ],
            'goal': {'x': 1000, 'y': 300},
            'background': 'pipe',
            'music': 'pipe'
        }
        
    def create_underground_level(self):
        return {
            'platforms': [
                {'x': 0, 'y': 350, 'width': 800, 'height': 50, 'type': 'ground'},
                {'x': 100, 'y': 300, 'width': 100, 'height': 20, 'type': 'block'},
                {'x': 300, 'y': 250, 'width': 100, 'height': 20, 'type': 'block'},
                {'x': 500, 'y': 300, 'width': 100, 'height': 20, 'type': 'block'},
                {'x': 700, 'y': 250, 'width': 100, 'height': 20, 'type': 'block'},
            ],
            'enemies': [
                {'x': 200, 'y': 280, 'vx': -1, 'type': 'koopa'},
                {'x': 400, 'y': 230, 'vx': 1, 'type': 'koopa'},
                {'x': 600, 'y': 280, 'vx': -1, 'type': 'koopa'},
            ],
            'coins': [
                {'x': 150, 'y': 270}, {'x': 350, 'y': 220},
                {'x': 550, 'y': 270}, {'x': 750, 'y': 220},
            ],
            'special_blocks': [
                {'x': 150, 'y': 270, 'type': 'coin_block'},
                {'x': 550, 'y': 270, 'type': 'fire_block'},
            ],
            'goal': {'x': 800, 'y': 300},
            'background': 'underground',
            'music': 'underground'
        }
        
    def load_level(self, world_num, level_num):
        self.world = world_num
        self.level = level_num
        world = self.worlds[world_num]
        
        if level_num in world['levels']:
            level = world['levels'][level_num]
        elif level_num == 'airship':
            level = world['levels']['airship']
        else:
            level = world['levels']['castle']
            
        self.player['x'] = 50
        self.player['y'] = 300
        self.player['vx'] = 0
        self.player['vy'] = 0
        self.camera_x = 0
        
        # Copy level data
        self.platforms = [p.copy() for p in level['platforms']]
        self.enemies = [e.copy() for e in level['enemies']]
        self.coin_objects = [c.copy() for c in level['coins']]
        self.special_blocks = [s.copy() for s in level.get('special_blocks', [])]
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
        # Update movement and collision
        if self.keys['Left']:
            self.player['vx'] = -self.move_speed
            self.player['facing_right'] = False
        elif self.keys['Right']:
            self.player['vx'] = self.move_speed
            self.player['facing_right'] = True
        else:
            self.player['vx'] *= 0.8
            
        if self.keys['Up'] and self.player['on_ground']:
            self.player['vy'] = self.jump_strength
            
        self.player['vy'] += self.gravity
        if self.player['vy'] > 15:
            self.player['vy'] = 15
            
        self.player['x'] += self.player['vx']
        self.player['y'] += self.player['vy']
        
        # Update collisions
        self.player['on_ground'] = False
        for platform in self.platforms:
            if self.check_collision(self.player, platform):
                if platform['type'] == 'block':
                    self.handle_block_collision(platform)
                else:
                    self.handle_ground_collision(platform)
                    
        # Special stage mechanics
        if self.background == 'cloud':
            self.player['vy'] *= 0.9
            
        # Fall detection
        if self.player['y'] > 600:
            self.die()
            
        # Update camera
        self.camera_x = self.player['x'] - 400
        if self.camera_x < 0:
            self.camera_x = 0
            
    def handle_block_collision(self, block):
        if self.player['vy'] > 0:
            self.player['y'] = block['y'] - self.player['height']
            self.player['vy'] = 0
            self.player['on_ground'] = True
            if self.keys['Up']:
                self.activate_block(block)
                
    def activate_block(self, block):
        if block['type'] == 'coin_block':
            self.coins += 1
            self.score += 10
            block['type'] = 'empty_block'
        elif block['type'] == 'mushroom_block':
            self.mushrooms += 1
            block['type'] = 'empty_block'
        elif block['type'] == 'fire_block':
            self.fire_flowers += 1
            block['type'] = 'empty_block'
        elif block['type'] == 'star_block':
            self.stars += 1
            block['type'] = 'empty_block'
        elif block['type'] == 'tanooki_block':
            self.player['power_level'] = 3
            block['type'] = 'empty_block'
            
    def draw(self):
        self.canvas.delete('game')
        
        # Draw background based on world and level
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
                    
            # Draw floating platforms
            for platform in self.platforms:
                x = platform['x'] - self.camera_x
                if -100 < x < 900:
                    self.canvas.create_rectangle(x, platform['y'], 
                        x + platform['width'], platform['y'] + platform['height'],
                        fill='#8B4513', outline='#654321', width=2, tags='game')
                    self.canvas.create_rectangle(x, platform['y'],
                        x + platform['width'], platform['y'] + 5,
                        fill='#228B22', outline='', tags='game')
        
        elif self.background == 'castle':
            # Draw castle background
            for i in range(10):
                color = f'#{100-i*5:02x}{80-i*5:02x}{60-i*3:02x}'
                self.canvas.create_rectangle(0, i*60, 800, (i+1)*60, 
                    fill=color, outline='', tags='game')
                    
        # Draw platforms and special blocks
        for platform in self.platforms:
            x = platform['x'] - self.camera_x
            if -100 < x < 900:
                if platform['type'] == 'block':
                    self.canvas.create_rectangle(x, platform['y'], 
                        x + platform['width'], platform['y'] + platform['height'],
                        fill='#8B4513', outline='#654321', width=2, tags='game')
                else:
                    self.canvas.create_rectangle(x, platform['y'], 
                        x + platform['width'], platform['y'] + platform['height'],
                        fill='#8B4513', outline='#654321', width=2, tags='game')
                    self.canvas.create_rectangle(x, platform['y'],
                        x + platform['width'], platform['y'] + 5,
                        fill='#228B22', outline='', tags='game')
                    
        # Draw coins
        for coin in self.coin_objects:
            x = coin['x'] - self.camera_x
            if -50 < x < 850:
                self.canvas.create_oval(x, coin['y'], x+16, coin['y']+16,
                    fill='gold', outline='orange', width=2, tags='game')
                    
        # Draw enemies
        for enemy in self.enemies:
            x = enemy['x'] - self.camera_x
            if -50 < x < 850:
                if enemy['type'] == 'goomba':
                    self.canvas.create_oval(x, enemy['y'], x+20, enemy['y']+20,
                        fill='brown', outline='#654321', width=2, tags='game')
                    self.canvas.create_oval(x+3, enemy['y']+5, x+7, enemy['y']+9,
                        fill='white', outline='', tags='game')
                    self.canvas.create_oval(x+13, enemy['y']+5, x+17, enemy['y']+9,
                        fill='white', outline='', tags='game')
                elif enemy['type'] == 'koopa':
                    self.canvas.create_oval(x, enemy['y'], x+22, enemy['y']+22,
                        fill='green', outline='#654321', width=2, tags='game')
                    self.canvas.create_oval(x+5, enemy['y']+5, x+10, enemy['y']+10,
                        fill='black', outline='', tags='game')
                    self.canvas.create_oval(x+12, enemy['y']+5, x+17, enemy['y']+10,
                        fill='black', outline='', tags='game')
                elif enemy['type'] == 'fish':
                    self.canvas.create_oval(x, enemy['y'], x+20, enemy['y']+20,
                        fill='blue', outline='darkblue', width=2, tags='game')
                    self.canvas.create_oval(x+10, enemy['y']+8, x+15, enemy['y']+12,
                        fill='white', outline='', tags='game')
                elif enemy['type'] == 'bowser':
                    self.canvas.create_rectangle(x, enemy['y'], x+40, enemy['y']+40,
                        fill='red', outline='darkred', width=2, tags='game')
                    self.canvas.create_rectangle(x+10, enemy['y']-10, x+30, enemy['y'],
                        fill='red', outline='darkred', width=2, tags='game')
                    self.canvas.create_oval(x+15, enemy['y']-5, x+25, enemy['y']+5,
                        fill='black', outline='', tags='game')
                        
        # Draw goal
        x = self.goal['x'] - self.camera_x
        if -50 < x < 850:
            self.canvas.create_rectangle(x+18, self.goal['y']-50, x+22, self.goal['y']+50,
                fill='gray', outline='black', tags='game')
            self.canvas.create_polygon(x+22, self.goal['y']-50, x+60, self.goal['y']-30,
                x+22, self.goal['y']-10, fill='red', outline='darkred', width=2, tags='game')
                
        # Draw power-up meter
        self.canvas.delete(self.power_text)
        self.power_text = self.canvas.create_text(10, 70, anchor='nw',
            text=f'Power: {"SMALL" if self.player["power_level"] == 0 else "MUSHROOM" if self.player["power_level"] == 1 else "FIRE" if self.player["power_level"] == 2 else "TANOOKI"}',
            fill='white', font=('Arial', 14, 'bold'))
            
        # Draw player based on power level
        x = self.player['x'] - self.camera_x
        player_color = 'red'
        if self.player['power_level'] == 1:
            player_color = 'green'
        elif self.player['power_level'] == 2:
            player_color = 'orange'
        elif self.player['power_level'] == 3:
            player_color = 'brown'
            
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
                
        # Update UI
        self.canvas.itemconfig(self.score_text, text=f'Score: {self.score}')
        self.canvas.itemconfig(self.coins_text, text=f'Coins: {self.coins}')
        self.canvas.itemconfig(self.lives_text, text=f'Lives: {self.lives}')
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
        return (obj1['x'] < obj2['x'] + obj2['width'] and
                obj1['x'] + obj1['width'] > obj2['x'] and
                obj1['y'] < obj2['y'] + obj2['height'] and
                obj1['y'] + obj1['height'] > obj2['y'])
                
    def handle_ground_collision(self, platform):
        if self.player['vy'] > 0:
            self.player['y'] = platform['y'] - self.player['height']
            self.player['vy'] = 0
            self.player['on_ground'] = True
        elif self.player['vy'] < 0:
            self.player['y'] = platform['y'] + platform['height']
            self.player['vy'] = 0
        elif self.player['vx'] > 0:
            self.player['x'] = platform['x'] - self.player['width']
        elif self.player['vx'] < 0:
            self.player['x'] = platform['x'] + platform['width']
            
    def die(self):
        self.lives -= 1
        if self.lives <= 0:
            self.game_over = True
        else:
            self.load_level(self.world, self.level)
            
    def check_goal(self):
        goal_rect = {'x': self.goal['x'], 'y': self.goal['y'], 'width': 40, 'height': 50}
        if self.check_collision(self.player, goal_rect):
            self.level_complete = True
            self.score += 1000
            
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
                if enemy['type'] == 'koopa':
                    enemy['vx'] *= 0.5
                    
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
                    if not self.player['imune']:
                        self.die()
                        self.player['imune'] = True
                        self.root.after(2000, lambda: setattr(self.player, 'imune', False))
                        
    def update_coins(self, dt):
        for coin in self.coin_objects[:]:
            coin_rect = {'x': coin['x'], 'y': coin['y'], 'width': 16, 'height': 16}
            if self.check_collision(self.player, coin_rect):
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
        
        # Handle level transitions and game states
        if self.level_complete:
            if self.level == len(self.worlds[self.world]['levels']):
                # If last level in world, go to castle
                self.load_level(self.world, 'castle')
            else:
                self.root.bind('<KeyPress-space>', lambda e: self.next_level())
                
        if self.game_over or self.game_won:
            self.root.bind('<KeyPress-Escape>', lambda e: self.root.quit())
            
        self.root.after(16, self.game_loop)
        
    def next_level(self):
        if self.level < len(self.worlds[self.world]['levels']):
            self.load_level(self.world, self.level + 1)
            self.level_complete = False
            self.root.unbind('<KeyPress-space>')
        else:
            if self.world < len(self.worlds):
                self.load_level(self.world + 1, 1)
            else:
                self.game_won = True
                
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

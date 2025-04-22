import tkinter as tk
from tkinter import font as tkfont
from enum import Enum, auto
import random
import time

class GameMode(Enum):
    WORLD_MAP = auto()
    LEVEL = auto()
    BATTLE = auto()
    INVENTORY = auto()
    GAME_OVER = auto()
    TITLE_SCREEN = auto()

class PowerUp(Enum):
    NONE = auto()
    MUSHROOM = auto()
    FIRE_FLOWER = auto()

class EnemyType(Enum):
    GOOMBA = auto()
    KOOPA = auto()

class Enemy:
    def __init__(self, x, y, enemy_type):
        self.x = x
        self.y = y
        self.type = enemy_type
        self.width = 30
        self.height = 30
        self.alive = True
        self.direction = random.choice([-1, 1])

    def move(self):
        if self.type == EnemyType.GOOMBA:
            self.x += self.direction * 2
        elif self.type == EnemyType.KOOPA:
            self.x += self.direction * 1.5

        # Bounce off screen edges
        if self.x < 50 or self.x > 550:
            self.direction *= -1

class Item:
    def __init__(self, x, y, powerup_type):
        self.x = x
        self.y = y
        self.type = powerup_type
        self.width = 20
        self.height = 20
        self.collected = False

class SMB3Game:
    def __init__(self, root):
        self.root = root
        self.root.title("Super Mario Bros. 3")
        self.root.geometry("600x400")
        self.canvas = tk.Canvas(root, width=600, height=400, bg='skyblue')
        self.canvas.pack()

        # Game state
        self.mode = GameMode.TITLE_SCREEN
        self.player_x = 300
        self.player_y = 300
        self.player_vy = 0
        self.on_ground = True
        self.scroll_x = 0
        self.level_length = 3000
        self.coins = 0
        self.lives = 3
        self.world = 1
        self.level = 1
        self.powerup = PowerUp.NONE
        self.invincible = False
        self.invincible_timer = 0

        # Level objects
        self.enemies = []
        self.items = []
        self.flag_x = 2800

        # Colors
        self.colors = {
            'mario': 'red',
            'mario_big': 'orange',
            'fire': 'white',
            'ground': 'brown',
            'brick': 'sienna',
            'coin': 'gold',
            'pipe': 'green',
            'cloud': 'white',
            'bush': 'darkgreen',
            'goomba': 'brown',
            'koopa': 'green',
            'mushroom': 'red',
            'flower': 'orange',
            'flag': 'white'
        }

        # Set up fonts
        self.big_font = tkfont.Font(family='Helvetica', size=24, weight='bold')
        self.small_font = tkfont.Font(family='Helvetica', size=12)

        # Bind keys
        self.root.bind('<KeyPress>', self.key_pressed)
        self.root.bind('<KeyRelease>', self.key_released)
        self.keys_pressed = set()

        # Start game loop
        self.last_time = time.time()
        self.root.after(16, self.game_loop)

    def start_level(self):
        self.player_x = 100
        self.player_y = 300
        self.player_vy = 0
        self.scroll_x = 0
        self.on_ground = True
        self.powerup = PowerUp.NONE
        self.invincible = False
        self.invincible_timer = 0
        self.enemies = [
            Enemy(400, 350, EnemyType.GOOMBA),
            Enemy(700, 350, EnemyType.KOOPA),
            Enemy(1200, 350, EnemyType.GOOMBA),
            Enemy(1800, 350, EnemyType.KOOPA)
        ]
        self.items = [
            Item(500, 250, PowerUp.MUSHROOM),
            Item(1500, 250, PowerUp.FIRE_FLOWER)
        ]
        self.flag_x = 2800

    def game_loop(self):
        current_time = time.time()
        delta_time = current_time - self.last_time
        self.last_time = current_time

        self.handle_input()
        self.update(delta_time)
        self.render()

        self.root.after(16, self.game_loop)

    def handle_input(self):
        if self.mode == GameMode.TITLE_SCREEN:
            if any(key in self.keys_pressed for key in ['Return', 'space']):
                self.mode = GameMode.WORLD_MAP
        elif self.mode == GameMode.WORLD_MAP:
            if 'Right' in self.keys_pressed:
                self.player_x = min(self.player_x + 3, 550)
            if 'Left' in self.keys_pressed:
                self.player_x = max(self.player_x - 3, 50)
            if 'Up' in self.keys_pressed:
                self.player_y = max(self.player_y - 3, 50)
            if 'Down' in self.keys_pressed:
                self.player_y = min(self.player_y + 3, 350)
            if any(key in self.keys_pressed for key in ['Return', 'space']):
                self.mode = GameMode.LEVEL
                self.start_level()
        elif self.mode == GameMode.LEVEL:
            if 'Right' in self.keys_pressed:
                self.player_x = min(self.player_x + 5, 550)
                self.scroll_x = min(self.scroll_x + 5, self.level_length - 600)
            if 'Left' in self.keys_pressed:
                self.player_x = max(self.player_x - 5, 50)
                self.scroll_x = max(self.scroll_x - 5, 0)
            if 'Up' in self.keys_pressed and self.on_ground:
                self.player_vy = -12
                self.on_ground = False

    def update(self, delta_time):
        if self.mode == GameMode.LEVEL:
            # Gravity
            if not self.on_ground:
                self.player_vy += 0.7
                self.player_y += self.player_vy
                if self.player_y >= 350:
                    self.player_y = 350
                    self.player_vy = 0
                    self.on_ground = True

            # Move enemies
            for enemy in self.enemies:
                if enemy.alive:
                    enemy.move()

            # Invincibility timer
            if self.invincible:
                self.invincible_timer -= delta_time
                if self.invincible_timer <= 0:
                    self.invincible = False

            # Collision with enemies
            for enemy in self.enemies:
                if enemy.alive and self.collision(self.player_x, self.player_y, 30, 45,
                                                  enemy.x - self.scroll_x, enemy.y, enemy.width, enemy.height):
                    if self.invincible:
                        enemy.alive = False
                    elif self.player_vy > 0 and self.player_y < enemy.y:
                        # Stomp enemy
                        enemy.alive = False
                        self.player_vy = -8
                    else:
                        if self.powerup != PowerUp.NONE:
                            self.powerup = PowerUp.NONE
                            self.invincible = True
                            self.invincible_timer = 2
                        else:
                            self.lives -= 1
                            if self.lives <= 0:
                                self.mode = GameMode.GAME_OVER
                            else:
                                self.start_level()
                            return

            # Collision with items
            for item in self.items:
                if not item.collected and self.collision(self.player_x, self.player_y, 30, 45,
                                                         item.x - self.scroll_x, item.y, item.width, item.height):
                    item.collected = True
                    if item.type == PowerUp.MUSHROOM:
                        self.powerup = PowerUp.MUSHROOM
                    elif item.type == PowerUp.FIRE_FLOWER:
                        self.powerup = PowerUp.FIRE_FLOWER

            # Coin collection (simulate coins on platforms)
            for i in range(5):
                coin_x = 120 + i * 200 - self.scroll_x % 200
                if 0 < coin_x < 600 and abs(self.player_x - coin_x) < 20 and abs(self.player_y - 220) < 20:
                    self.coins += 1

            # Level end
            if self.player_x + self.scroll_x > self.flag_x:
                self.level += 1
                self.world += (self.level // 4)
                self.level = (self.level - 1) % 4 + 1
                self.mode = GameMode.WORLD_MAP

    def collision(self, x1, y1, w1, h1, x2, y2, w2, h2):
        return (x1 < x2 + w2 and x1 + w1 > x2 and
                y1 < y2 + h2 and y1 + h1 > y2)

    def render(self):
        self.canvas.delete('all')

        if self.mode == GameMode.TITLE_SCREEN:
            self.render_title_screen()
        elif self.mode == GameMode.WORLD_MAP:
            self.render_world_map()
        elif self.mode == GameMode.LEVEL:
            self.render_level()
        elif self.mode == GameMode.GAME_OVER:
            self.render_game_over()

        # Always show HUD
        self.render_hud()

    def render_title_screen(self):
        self.canvas.create_rectangle(0, 0, 600, 400, fill='black')
        self.canvas.create_text(300, 100, text="SUPER MARIO BROS. 3",
                               font=self.big_font, fill='white')
        self.canvas.create_text(300, 200, text="Press START",
                               font=self.small_font, fill='white')
        self.canvas.create_rectangle(280, 250, 320, 300, fill=self.colors['mario'])
        self.canvas.create_oval(270, 230, 330, 290, fill=self.colors['mario'])

    def render_world_map(self):
        self.canvas.create_rectangle(0, 0, 600, 400, fill='lightblue')
        for i in range(1, 9):
            x = 50 + i * 60
            y = 100 + (i % 3) * 100
            self.canvas.create_oval(x-20, y-20, x+20, y+20, fill='green')
            self.canvas.create_text(x, y, text=str(i), font=self.small_font)
        self.canvas.create_oval(self.player_x-15, self.player_y-15,
                               self.player_x+15, self.player_y+15,
                               fill=self.colors['mario'])

    def render_level(self):
        self.canvas.create_rectangle(0, 0, 600, 300, fill='skyblue')
        self.canvas.create_rectangle(0, 300, 600, 400, fill=self.colors['ground'])

        # Draw platforms
        for i in range(5):
            x = 100 + i * 200 - self.scroll_x % 200
            if x > -50 and x < 650:
                self.canvas.create_rectangle(x, 250, x+100, 260, fill=self.colors['brick'])
                # Draw coins on platforms
                self.canvas.create_oval(x+40, 220, x+60, 240, fill=self.colors['coin'])

        # Draw pipes
        for i in range(3):
            x = 300 + i * 300 - self.scroll_x % 300
            if x > -50 and x < 650:
                self.canvas.create_rectangle(x, 260, x+60, 300, fill=self.colors['pipe'])
                self.canvas.create_rectangle(x-10, 240, x+70, 260, fill=self.colors['pipe'])

        # Draw flag
        flag_x = self.flag_x - self.scroll_x
        if 0 < flag_x < 600:
            self.canvas.create_rectangle(flag_x, 200, flag_x+10, 300, fill='black')
            self.canvas.create_rectangle(flag_x+10, 200, flag_x+40, 230, fill=self.colors['flag'])

        # Draw items
        for item in self.items:
            if not item.collected:
                ix = item.x - self.scroll_x
                if 0 < ix < 600:
                    color = self.colors['mushroom'] if item.type == PowerUp.MUSHROOM else self.colors['flower']
                    self.canvas.create_oval(ix, item.y, ix+item.width, item.y+item.height, fill=color)

        # Draw enemies
        for enemy in self.enemies:
            if enemy.alive:
                ex = enemy.x - self.scroll_x
                if 0 < ex < 600:
                    color = self.colors['goomba'] if enemy.type == EnemyType.GOOMBA else self.colors['koopa']
                    self.canvas.create_oval(ex, enemy.y, ex+enemy.width, enemy.y+enemy.height, fill=color)

        # Draw player (Mario)
        if self.powerup == PowerUp.NONE:
            color = self.colors['mario']
            self.canvas.create_rectangle(self.player_x-15, self.player_y-30,
                                        self.player_x+15, self.player_y,
                                        fill=color)
            self.canvas.create_oval(self.player_x-15, self.player_y-45,
                                   self.player_x+15, self.player_y-15,
                                   fill=color)
        elif self.powerup == PowerUp.MUSHROOM:
            color = self.colors['mario_big']
            self.canvas.create_rectangle(self.player_x-15, self.player_y-45,
                                        self.player_x+15, self.player_y,
                                        fill=color)
            self.canvas.create_oval(self.player_x-15, self.player_y-65,
                                   self.player_x+15, self.player_y-35,
                                   fill=color)
        elif self.powerup == PowerUp.FIRE_FLOWER:
            color = self.colors['fire']
            self.canvas.create_rectangle(self.player_x-15, self.player_y-45,
                                        self.player_x+15, self.player_y,
                                        fill=color)
            self.canvas.create_oval(self.player_x-15, self.player_y-65,
                                   self.player_x+15, self.player_y-35,
                                   fill=color)

        # Invincibility effect
        if self.invincible and int(time.time() * 10) % 2 == 0:
            self.canvas.create_rectangle(self.player_x-20, self.player_y-50,
                                        self.player_x+20, self.player_y+5,
                                        outline='yellow', width=3)

    def render_game_over(self):
        self.canvas.create_rectangle(0, 0, 600, 400, fill='black')
        self.canvas.create_text(300, 200, text="GAME OVER",
                               font=self.big_font, fill='red')
        self.canvas.create_text(300, 250, text="Press START to continue",
                               font=self.small_font, fill='white')

    def render_hud(self):
        self.canvas.create_rectangle(0, 0, 600, 30, fill='black')
        self.canvas.create_text(50, 15, text=f"COINS: {self.coins}",
                               font=self.small_font, fill='white')
        self.canvas.create_text(300, 15, text=f"WORLD {self.world}-{self.level}",
                               font=self.small_font, fill='white')
        self.canvas.create_text(550, 15, text=f"LIVES: {self.lives}",
                               font=self.small_font, fill='white')
        if self.powerup == PowerUp.MUSHROOM:
            self.canvas.create_text(150, 15, text="MUSHROOM",
                                   font=self.small_font, fill='orange')
        elif self.powerup == PowerUp.FIRE_FLOWER:
            self.canvas.create_text(150, 15, text="FIRE FLOWER",
                                   font=self.small_font, fill='orange')

    def key_pressed(self, event):
        self.keys_pressed.add(event.keysym)
        if self.mode == GameMode.GAME_OVER and event.keysym in ['Return', 'space']:
            self.lives = 3
            self.coins = 0
            self.level = 1
            self.world = 1
            self.mode = GameMode.TITLE_SCREEN

    def key_released(self, event):
        if event.keysym in self.keys_pressed:
            self.keys_pressed.remove(event.keysym)

if __name__ == "__main__":
    root = tk.Tk()
    game = SMB3Game(root)
    root.mainloop()

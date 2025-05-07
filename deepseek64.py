from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random

app = Ursina()

# --- Helper Function ---
def distance_xz(a, b):
    return sqrt((a.x - b.x)**2 + (a.z - b.z)**2)

# --- Window and Application Settings ---
window.fps_counter.enabled = True
window.title = 'SM64-Inspired Game'
window.borderless = False
window.vsync = False  # Better for consistent FPS control
application.target_fps = 60  # Lock to 60 FPS

# --- Player Setup ---
player = FirstPersonController(
    collider='box',
    jump_height=2.0,
    gravity=0.6,
    speed=10,
    position=(0, 10, 0)
player.jump_key = None  # Disable default jump handling
player.cursor.visible = False
player.can_fly = False
player.jump_count = 0
player.is_swimming = False
player.coins = 0
player.max_health = 8
player.health = player.max_health
player.invincible_timer = 0
player.is_ground_pounding = False
player.is_diving = False
player.dive_timer = 0
player.original_gravity = player.gravity

# Add visible player model
player_model = Entity(
    parent=player,
    model='cube',
    color=color.azure,
    scale=(0.8, 1.8, 0.8),
    position=Vec3(0, -0.9, 0)
    
# --- UI Elements ---
health_text = Text(
    text='Health: 8/8',
    origin=(-0.95, 0.9),
    color=color.red,
    scale=1.5,
    background=True)
    
star_text = Text(
    text='Stars: 0/7',
    origin=(-0.95, 0.85),
    color=color.gold,
    scale=1.5,
    background=True)
    
coin_text = Text(
    text='Coins: 0',
    origin=(-0.95, 0.8),
    color=color.yellow,
    scale=1.5,
    background=True)
    
red_coin_text = Text(
    text='Red Coins: 0/8',
    origin=(-0.95, 0.75),
    color=color.orange,
    scale=1.5,
    background=True)

def update_health_ui():
    health_text.text = f'Health: {player.health}/{player.max_health}'
    health_text.color = color.gray if player.health <= 0 else color.red

def update_coin_ui():
    coin_text.text = f'Coins: {player.coins}'

# --- Terrains ---
ground = Entity(
    model='quad',
    color=color.lime,
    scale=300,
    rotation_x=90,
    collider='box')
    
water_area = Entity(
    model='cube',
    color=color.rgba(0, 100, 255, 128),
    position=(70, -5, 70),
    scale=(60, 10, 60),
    collider='box',
    alpha=0.5)
    
slope1 = Entity(
    model='cube',
    color=color.rgb(0,180,0),
    position=(0, 2.5, 40),
    scale=(20, 5, 20),
    rotation_x=20,
    collider='mesh')
    
slope2 = Entity(
    model='cube',
    color=color.rgb(0,170,0),
    position=(0, 2.5, -40),
    scale=(20, 5, 20),
    rotation_x=-20,
    collider='mesh')

# --- Wing Cap ---
class WingCap(Entity):
    def __init__(self, position):
        super().__init__(
            model='cube',
            color=color.red,
            position=position,
            collider='box',
            scale=1)
        self.rotation_speed = 50
        self.original_y = position.y
        self.bob_timer = 0

    def update(self):
        self.rotation_y += self.rotation_speed * time.dt
        self.bob_timer += time.dt
        self.y = self.original_y + sin(self.bob_timer * 3) * 0.2

        if self.enabled and self.intersects(player).hit and not player.can_fly:
            player.can_fly = True
            player.gravity = 0
            print_on_screen("Wing Cap Activated!", position=(-0.5, 0.4), scale=2, duration=3)
            invoke(self.remove_wing_cap, delay=20)
            self.disable()

    def remove_wing_cap(self):
        if player.can_fly:
            player.can_fly = False
            if not player.is_swimming:
                player.gravity = player.original_gravity
            print_on_screen("Wing Cap Wore Off!", position=(-0.5, 0.4), scale=2, duration=3)

wing_cap = WingCap(position=(10, 6, 10))

# --- Collectibles ---
TOTAL_STARS = 7
stars_collected = 0
stars_list = []

TOTAL_RED_COINS = 8
red_coins_collected = 0
red_coins_list = []

class Star(Entity):
    def __init__(self, position):
        super().__init__(
            model='sphere',
            color=color.yellow,
            scale=0.8,
            collider='sphere',
            position=position)
        self.rotation_speed = random.uniform(80, 120)
        self.original_y = position.y
        self.bob_timer = random.uniform(0, 5)
        stars_list.append(self)

    def update(self):
        self.rotation_y += self.rotation_speed * time.dt
        self.bob_timer += time.dt
        self.y = self.original_y + sin(self.bob_timer * 2) * 0.15

        if self.enabled and self.intersects(player).hit:
            global stars_collected
            stars_collected += 1
            stars_list.remove(self)
            self.disable()
            destroy(self)
            update_star_ui()

def update_star_ui():
    star_text.text = f'Stars: {stars_collected}/{TOTAL_STARS}'
    if stars_collected >= TOTAL_STARS:
        Text("All Stars Collected!", origin=(0,0), scale=3, color=color.cyan, background=True, duration=10)

class RedCoin(Entity):
    def __init__(self, position):
        super().__init__(
            model='sphere',
            color=color.red,
            scale=0.4,
            collider='sphere',
            position=position)
        self.rotation_speed = random.uniform(60, 100)
        self.original_y = position.y
        self.bob_timer = random.uniform(0,5)
        red_coins_list.append(self)

    def update(self):
        self.rotation_y += self.rotation_speed * time.dt
        self.bob_timer += time.dt
        self.y = self.original_y + sin(self.bob_timer * 2.5) * 0.1

        if self.enabled and self.intersects(player).hit:
            global red_coins_collected
            red_coins_collected += 1
            red_coins_list.remove(self)
            self.disable()
            destroy(self)
            update_red_coin_ui()
            if red_coins_collected >= TOTAL_RED_COINS:
                print_on_screen("Red Coin Star Appears!", position=(-0.5, 0.3), scale=2, duration=4)
                Star(position=player.position + Vec3(0,5,5))

def update_red_coin_ui():
    red_coin_text.text = f'Red Coins: {red_coins_collected}/{TOTAL_RED_COINS}'

# Populate collectibles
for _ in range(TOTAL_STARS):
    Star(position=(random.uniform(-70,70), random.uniform(5,20), random.uniform(-70,70)))

for _ in range(TOTAL_RED_COINS):
    RedCoin(position=(random.uniform(-60,60), random.uniform(3,15), random.uniform(-60,60)))

# --- Enemies ---
class Goomba(Entity):
    def __init__(self, position):
        super().__init__(
            model='cube',
            color=color.rgb(150,75,0),
            collider='box',
            position=position,
            scale=(1.5,1,1.5))
        self.speed = random.uniform(1,2.5)
        self.health = 1

    def update(self):
        if self.health <= 0 or not self.enabled:
            return
        if distance_xz(self, player) < 15:
            self.look_at_2d(player.position)
            self.position += self.forward * self.speed * time.dt

        if self.intersects(player):
            if player.is_ground_pounding:
                self.health = 0
            elif player.y > self.y + 1:
                self.health = 0
                player.velocity.y = 2
            else:
                take_player_damage(1)

for _ in range(10):
    Goomba(position=(random.uniform(-70,70), 0.5, random.uniform(-70,70)))

# --- Main Game Loop ---
def update():
    # Invincibility effects
    if player.invincible_timer > 0:
        player.invincible_timer -= time.dt
        player_model.visible = int(player.invincible_timer * 10) % 2 == 0
    else:
        player_model.visible = True

    # Water interaction
    player.is_swimming = water_area.intersects(player).hit and player.y < 0
    if player.is_swimming:
        player.gravity = 0.07
    elif player.can_fly:
        player.gravity = 0
    else:
        player.gravity = player.original_gravity

    # Fall damage
    if player.y < -50:
        take_player_damage(2)
        player.position = (0,10,0)

def input(key):
    # Jump handling
    if key == 'space':
        input.handled = True
        if player.grounded:
            player.jump()
        elif player.jump_count < 2:
            player.jump_count += 1
            player.jump()

    # Ground pound
    if key == 'c' and not player.grounded:
        player.is_ground_pounding = True
        player.velocity.y = -5

Sky()
app.run()

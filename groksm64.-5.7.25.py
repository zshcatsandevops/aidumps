from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random
import math

app = Ursina()

# --- Helper Function ---
def distance_xz(a, b):
    return math.sqrt((a.x - b.x)**2 + (a.z - b.z)**2)

# --- Window and Application Settings ---
window.fps_counter.enabled = True
window.title = 'SM64-Inspired Game'
window.borderless = False
window.vsync = True  # Enables smoother 60 FPS control
application.target_fps = 60  # Target 60 FPS

# --- Player Setup ---
player = FirstPersonController(
    collider='box',
    jump_height=2.0,
    gravity=0.6,
    speed=10,
    position=(0, 10, 0)
)
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
)

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

def update_star_ui():
    star_text.text = f'Stars: {stars_collected}/{TOTAL_STARS}'
    if stars_collected >= TOTAL_STARS:
        Text("All Stars Collected!", origin=(0,0), scale=3, color=color.cyan, background=True, duration=10)

def update_red_coin_ui():
    red_coin_text.text = f'Red Coins: {red_coins_collected}/{TOTAL_RED_COINS}'

# --- Terrains ---
ground = Entity(
    model='quad',
    color=color.lime,
    scale=300,
    rotation_x=90,
    collider='box')

water_area = Entity(
    model='cube',
    color=color.rgba(0, 100, 255, )

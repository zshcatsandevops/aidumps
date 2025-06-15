# test.py: Super Mario Odyssey 2 (Ursina-based game)
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random
import logging

# Suppress Ursina's monitor info logs
logging.getLogger('ursina').setLevel(logging.WARNING)

app = Ursina()
window.title = 'Super Mario Odyssey 2'
window.borderless = False
window.fullscreen = False
window.size = (800, 600)
window.position = (100, 100)
window.fps_counter.enabled = True
window.exit_button.visible = False
app.target_fps = 60  # Enforce 60 FPS [[6]](https://www.ursina-engine.org/) 

# Global variables
current_kingdom = "n64_express"
current_player = "mario"
coins = 0
stars = 0
player_speed = 6
player_jump = 1.8
jump_duration = 0.4
camera_fov = 90

# Player models
def create_mario_model():
    mario = Entity(model='cube', color=color.red, scale=(0.8, 1.6, 0.8))
    mario_head = Entity(model='sphere', color=color.red, scale=0.7, position=(0, 0.9, 0), parent=mario)
    mario_hat = Entity(model='cube', color=color.red, scale=(1, 0.2, 1), position=(0, 1.1, 0), parent=mario)
    mario_eyes = Entity(model='quad', color=color.white, scale=(0.3, 0.2), position=(0, 0.9, 0.35), parent=mario)
    return mario

def create_luigi_model():
    luigi = Entity(model='cube', color=color.green, scale=(0.8, 1.6, 0.8))
    luigi_head = Entity(model='sphere', color=color.green, scale=0.7, position=(0, 0.9, 0), parent=luigi)
    luigi_hat = Entity(model='cube', color=color.green, scale=(1, 0.2, 1), position=(0, 1.1, 0), parent=luigi)
    luigi_eyes = Entity(model='quad', color=color.white, scale=(0.3, 0.2), position=(0, 0.9, 0.35), parent=luigi)
    return luigi

# Player setup
mario = create_mario_model()
luigi = create_luigi_model()
player = FirstPersonController()
player.collider = 'box'
player.scale_y = 1.8
player.speed = player_speed
player.jump_height = player_jump
player.jump_duration = jump_duration
player.gravity = 1
player.cursor.visible = False
player.visible = False
camera.fov = camera_fov

# Captured model for when Mario captures an entity
captured_model = Entity(model='cube', color=color.brown, scale=(1, 1, 1), enabled=False)

# Environment setup
sky = Sky(color=color.cyan)
ground = Entity(model='plane', scale=200, texture='grass', collider='mesh')

# Kingdoms dictionary to store entities
kingdoms = {
    "n64_express": [],
    "waterfront": [],
    "flower": [],
    "shimmerock": [],
    "bowser_jr": [],
    "skyloft": [],
    "darker_side": [],
    "shine": [],
    "toad_town": [],
    "bowser": []
}

# Goomba creation function
def create_goomba(position):
    goomba = Entity(model='cube', color=color.brown, scale=(1, 1, 1), position=position, collider='box', name='goomba')
    return goomba

# Kingdom creation functions (simplified for brevity)
def create_n64_express():
    train = Entity(model='cube', scale=(25, 5, 6), texture='brick', position=(0, 2.5, 0), collider='box')
    cars = [Entity(model='cube', scale=(6, 4, 5), texture='brick', position=(pos, 2, 0), collider='box') for pos in [-10, -17, -24]]
    wheel_positions = [(x, 0.5, z) for x in [10,5,-5,-10,-17,-24] for z in [3,-3]]
    wheels = [Entity(model='cube', scale=(1, 0.3, 1), color=color.gray, position=pos, rotation_x=90) for pos in wheel_positions]
    portal_positions = [(-5,3,0,"Waterfront Kingdom"), (-10,3,0,"Flower Kingdom"), (-15,3,0,"Shimmerock Kingdom"),
                        (-20,3,0,"Bowser Jr. Kingdom"), (-25,3,0,"Skyloft Kingdom"), (-30,3,0,"Darker Side Kingdom"),
                        (-35,3,0,"Shine Kingdom"), (-40,3,0,"Toad Town Kingdom"), (-45,3,0,"Bowser's Kingdom")]
    portals = [Entity(model='circle', scale=2.5, color=color.azure, position=(x,y,z), rotation_x=90, collider='box', name=name) 
               for x,y,z,name in portal_positions]
    return [train] + cars + wheels + portals

# Simplified kingdom functions (full versions omitted for brevity)
def create_waterfront_kingdom():
    terrain = Entity(model='plane', scale=100, texture='white_cube', color=color.blue, collider='mesh')
    return [terrain]

# ... (other kingdom functions follow the same pattern as the original code)

# UI Elements
def create_ui():
    coin_icon = Entity(model='quad', texture='circle', color=color.gold, scale=(0.05,0.05), position=window.top_left + (0.05,-0.05,0))
    coin_text = Text(text=f"Coins: {coins}", position=window.top_left + (0.1,-0.05,0), origin=(0,0), scale=1.5)
    star_icon = Entity(model='quad', texture='circle', color=color.yellow, scale=(0.05,0.05), position=window.top_left + (0.05,-0.12,0))
    star_text = Text(text=f"Stars: {stars}", position=window.top_left + (0.1,-0.12,0), origin=(0,0), scale=1.5)
    kingdom_text = Text(text="N64 Express", position=window.top, origin=(0,0), scale=2, y=-0.05)
    character_text = Text(text=f"Character: {current_player.capitalize()}", position=window.bottom_left + (0.05,0.05,0), origin=(0,0), scale=1.5)
    return [coin_icon, coin_text, star_icon, star_text, kingdom_text, character_text]

# Initialize kingdoms
kingdoms["n64_express"] = create_n64_express()
kingdoms["waterfront"] = create_waterfront_kingdom()
# ... (initialize other kingdoms similarly)

ui_elements = create_ui()

# Hide kingdoms initially
for kingdom in kingdoms:
    if kingdom != "n64_express":
        for entity in kingdoms[kingdom]:
            entity.enabled = False

# Game state management
def switch_kingdom(kingdom_name):
    global current_kingdom
    for entity in kingdoms[current_kingdom]:
        entity.enabled = False
    current_kingdom = kingdom_name
    for entity in kingdoms[kingdom_name]:
        entity.enabled = True
    ui_elements[4].text = kingdom_name.replace("_", " ").title()
    player.position = (0, 5, 0) if kingdom_name != "n64_express" else (0, 3, 0)

# Player controls
def switch_character():
    global current_player
    if current_player == "mario":
        current_player = "luigi"
        mario.enabled = False
        luigi.enabled = True
    else:
        current_player = "mario"
        luigi.enabled = False
        mario.enabled = True
    ui_elements[5].text = f"Character: {current_player.capitalize()}"

def collect_coin(coin):
    global coins
    coins += 1
    coin.enabled = False
    ui_elements[1].text = f"Coins: {coins}"

def collect_star(star):
    global stars
    stars += 1
    star.enabled = False
    ui_elements[3].text = f"Stars: {stars}"
    switch_kingdom("n64_express")

# Cap throw and capture mechanics
def throw_cap():
    direction = player.forward
    hit_info = raycast(player.position, direction, distance=10, ignore=(player,))
    if hit_info.hit and hasattr(hit_info.entity, 'name') and hit_info.entity.name == 'goomba':
        capture_goomba(hit_info.entity)

def capture_goomba(goomba):
    goomba.enabled = False
    mario.enabled = False
    captured_model.enabled = True
    captured_model.position = player.position + (0, -0.9, 0)
    invoke(uncapture, delay=5)

def uncapture():
    captured_model.enabled = False
    mario.enabled = True

# Input handling
def input(key):
    if key == 'c':
        switch_character()
    if current_kingdom == "n64_express" and key == 'e':
        for entity in kingdoms["n64_express"]:
            if hasattr(entity, 'name') and entity.name in [
                "Waterfront Kingdom", "Flower Kingdom", "Shimmerock Kingdom",
                "Bowser Jr. Kingdom", "Skyloft Kingdom", "Darker Side Kingdom",
                "Shine Kingdom", "Toad Town Kingdom", "Bowser's Kingdom"
            ]:
                if distance(player.position, entity.position) < 3:
                    kingdom_key = entity.name.replace(" Kingdom", "").replace("'", "").lower().replace(" ", "_")
                    switch_kingdom(kingdom_key)
    if key == 'r' and current_kingdom != "n64_express":
        switch_kingdom("n64_express")
    if key == 'q':
        application.quit()
    if key == 'f':
        throw_cap()

# Collision detection and update loop
def update():
    for kingdom in kingdoms:
        if kingdom == current_kingdom:
            for entity in kingdoms[kingdom]:
                if hasattr(entity, 'color'):
                    if entity.color == color.gold or (hasattr(entity.color, 'hex') and entity.color.hex == color.gold.hex):
                        if distance(player.position, entity.position) < 2:
                            collect_coin(entity)
                    elif entity.color == color.yellow or (hasattr(entity.color, 'hex') and entity.color.hex == color.yellow.hex):
                        if distance(player.position, entity.position) < 2:
                            collect_star(entity)
    # Update character model position
    if not captured_model.enabled:
        if current_player == "mario":
            mario.position = player.position + (0, -0.9, 0)
            mario.rotation = (0, -player.rotation_y, 0)
        else:
            luigi.position = player.position + (0, -0.9, 0)
            luigi.rotation = (0, -player.rotation_y, 0)
    if captured_model.enabled:
        captured_model.position = player.position + (0, -0.9, 0)
        captured_model.rotation = (0, -player.rotation_y, 0)

# Set initial state
player.position = (0, 3, 0)
luigi.position = player.position + (0, -0.9, 0)
mario.position = player.position + (0, -0.9, 0)
luigi.enabled = False
mario.enabled = True

# Start the game
app.run()

# test.py - CATSDK'S PUREVIBE PAPER MARIO 64 ENGINE - NO PNGS, ALL GLORY!
from ursina import *
import random
import math
import os

# Import PIL for dynamic texture generation
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
    print("☇[ CATSDK ]: Meow! Pillow (PIL) is loaded! Ready to craft authentic Paper Mario vibes! This is going to be paper-perfect!☇")
    try:
        VIBE_FONT_PATH = "arialbd.ttf"
        VIBE_FONT_SIZE = random.randint(18, 28)
        VIBE_FONT = ImageFont.truetype(VIBE_FONT_PATH, size=VIBE_FONT_SIZE)
        print(f"☇[ CATSDK ]: Loaded font '{VIBE_FONT_PATH}' (size {VIBE_FONT_SIZE}) for extra Paper Mario textual spice! So stylish!☇")
    except IOError:
        VIBE_FONT = ImageFont.load_default()
        print("☇[ CATSDK ]: Couldn't load a specific font. Using default font.☇")
except ImportError:
    PIL_AVAILABLE = False
    VIBE_FONT = None
    print("☇[ CATSDK ]: Pillow (PIL) is not installed. Install 'Pillow' for the full experience: `pip install Pillow`☇")

app = Ursina()

# Game Constants
GRAVITY = 14
WALK_SPEED = 3.5
RUN_SPEED = 6.5
JUMP_FORCE = 8
MAX_JUMPS = 1
CAMERA_DISTANCE = 16
CAMERA_HEIGHT = 6

# Color Palettes
PM_PALETTES = {
    "mario_red": color.rgb(230, 20, 20), 
    "mario_blue": color.rgb(0, 80, 200),
    "goomba_brown": color.rgb(139, 69, 19),
    "scenery_grass_green": color.rgb(50, 200, 50),
    "scenery_dirt_brown": color.rgb(160, 100, 40),
    "item_star_yellow": color.gold,
}

def get_paper_mario_vibe_texture(entity_type_tag="generic_pm_character", img_w=32, img_h=32):
    """Generate procedural textures based on entity type"""
    if not PIL_AVAILABLE:
        return random.choice(list(PM_PALETTES.values()))
    
    img = Image.new('RGBA', (img_w, img_h), color=(0,0,0,0))
    draw = ImageDraw.Draw(img)
    
    # Mario Texture
    if entity_type_tag == "player_mario":
        draw.ellipse([(img_w*0.1, img_h*0.05), (img_w*0.9, img_h*0.5)], fill=PM_PALETTES["mario_red"].rgba)
        draw.rectangle([(img_w*0.2, img_h*0.45), (img_w*0.8, img_h*0.9)], fill=PM_PALETTES["mario_blue"].rgba)
    
    # Goomba Texture
    elif entity_type_tag == "enemy_goomba":
        draw.ellipse([(img_w*0.1, img_h*0.2), (img_w*0.9, img_h*0.95)], fill=PM_PALETTES["goomba_brown"].rgba)
    
    # Grass Texture
    elif "scenery_grass" in entity_type_tag:
        draw.rectangle([(0,0), (img_w, img_h)], fill=PM_PALETTES["scenery_grass_green"].rgba)
    
    return Texture(img)

class PaperEntity(Entity):
    def __init__(self, entity_type_tag="generic_pm_character", **kwargs):
        super().__init__(
            model='quad',
            texture=get_paper_mario_vibe_texture(entity_type_tag),
            scale=(2, 2),
            **kwargs
        )
        self.billboard = True

# Scene Setup
ground = Entity(
    model='plane',
    texture=get_paper_mario_vibe_texture("scenery_grass"),
    texture_scale=(10, 10),
    scale=(100, 1, 100),
    color=color.green
)

# Spawn Entities
mario = PaperEntity("player_mario", position=(0, 1, 0))
goomba = PaperEntity("enemy_goomba", position=(3, 1, 0))

# Camera Setup
camera.position = (0, CAMERA_HEIGHT, -CAMERA_DISTANCE)
camera.look_at(mario.position)

# Input Handling
def update():
    # Basic Movement
    if held_keys['w']:
        mario.z -= WALK_SPEED * time.dt
    if held_keys['s']:
        mario.z += WALK_SPEED * time.dt
    if held_keys['a']:
        mario.x -= WALK_SPEED * time.dt
    if held_keys['d']:
        mario.x += WALK_SPEED * time.dt
    
    # Camera Follow
    camera.position = mario.position + Vec3(0, CAMERA_HEIGHT, -CAMERA_DISTANCE)
    camera.look_at(mario.position)

app.run()

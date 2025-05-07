# test.py - CATSDK'S PUREVIBE PAPER MARIO 64 ENGINE - NO PNGS, ALL GLORY!
from ursina import *
import random
import math
import os  # For dummy sound file creation

# Attempt to import Pillow for dynamic texture generation
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
    print("☇[ CATSDK ]: Meow! Pillow (PIL) is loaded! Ready to craft authentic Paper Mario vibes! This is going to be paper-perfect!☇")
    try:
        # You might need to change 'arialbd.ttf' to a font you have
        VIBE_FONT_PATH = "arialbd.ttf"  # Arial Bold as a fallback
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

### Constants
GRAVITY = 14  # Adjusted for realistic feel
WALK_SPEED = 3.5
RUN_SPEED = 6.5
JUMP_FORCE = 8  # Adjusted for corrected gravity
MAX_JUMPS = 1
HAMMER_COOLDOWN = 0.7
CAMERA_DISTANCE = 16
CAMERA_HEIGHT = 6
CAMERA_ROTATION_SPEED = 80

### Game State
collected_star_points = 0
player_health = 10
player_fp = 10

### Texture Generation
PM_PALETTES = {
    "mario_red": color.rgb(230, 20, 20), "mario_blue": color.rgb(0, 80, 200), "mario_yellow_button": color.yellow, "mario_brown_shoe": color.brown, "mario_skin": color.rgb(255, 200, 150), "mario_white_glove": color.white,
    "goomba_brown": color.rgb(139, 69, 19), "goomba_beige": color.rgb(245, 222, 179), "goomba_eye_white": color.white, "goomba_pupil_black": color.black,
    "koopa_green_shell": color.rgb(0, 180, 50), "koopa_yellow_skin": color.rgb(255, 220, 50), "koopa_beak_orange": color.orange, "koopa_shoe_blue": color.blue,
    "scenery_grass_green": color.rgb(50, 200, 50), "scenery_dirt_brown": color.rgb(160, 100, 40), "scenery_wood_brown": color.sienna, "scenery_sky_blue": color.cyan, "scenery_rock_gray": color.gray,
    "item_star_yellow": color.gold, "item_coin_gold": color.gold, "item_heart_red": color.red, "item_flower_pink": color.pink,
    "effect_hit_spark_yellow": color.yellow, "effect_hit_spark_white": color.white, "effect_damage_flash_red": color.rgb(255, 80, 80),
    "ui_text_black": color.black, "ui_text_white": color.white, "ui_bg_dark": color.dark_gray, "ui_border_light": color.light_gray,
    "generic_outline_black": color.black,
}

def get_paper_mario_vibe_texture(entity_type_tag="generic_pm_character", specific_palette_keys=None, img_w=32, img_h=32):
    if not PIL_AVAILABLE:
        print("☇[ CATSDK ]: No Pillow! Using random color fallback.☇")
        return random.choice(list(PM_PALETTES.values()))

    print(f"☇[ CATSDK ]: Crafting a Paper Mario texture for '{entity_type_tag}' ({img_w}x{img_h})!☇")
    
    img = Image.new('RGBA', (img_w, img_h), color=(0,0,0,0))
    draw = ImageDraw.Draw(img)

    if entity_type_tag == "player_mario":
        draw.ellipse([(img_w*0.1, img_h*0.05), (img_w*0.9, img_h*0.5)], fill=PM_PALETTES["mario_red"].rgba)
        draw.ellipse([(img_w*0.3, img_h*0.01), (img_w*0.7, img_h*0.25)], fill=PM_PALETTES["mario_red"].rgba)
        draw.ellipse([(img_w*0.4, img_h*0.1), (img_w*0.6, img_h*0.3)], fill=PM_PALETTES["mario_white_glove"].rgba)
        if VIBE_FONT:
            m_font = VIBE_FONT.font_variant(size=int(img_h*0.18))
            try:
                draw.text((img_w*0.47, img_h*0.12), "M", font=m_font, fill=PM_PALETTES["mario_red"].rgba, anchor="mm")
            except AttributeError:
                try:
                    bbox = draw.textbbox((0,0), "M", font=m_font)
                    tw = bbox[2] - bbox[0]
                    th = bbox[3] - bbox[1]
                except:
                    tw, th = draw.textsize("M", font=m_font)
                draw.text((img_w*0.47 - tw/2, img_h*0.12 - th/2), "M", font=m_font, fill=PM_PALETTES["mario_red"].rgba)
        draw.rectangle([(img_w*0.2, img_h*0.45), (img_w*0.8, img_h*0.9)], fill=PM_PALETTES["mario_blue"].rgba)
        draw.ellipse([(img_w*0.25, img_h*0.4), (img_w*0.35, img_h*0.5)], fill=PM_PALETTES["mario_yellow_button"].rgba)
        draw.ellipse([(img_w*0.65, img_h*0.4), (img_w*0.75, img_h*0.5)], fill=PM_PALETTES["mario_yellow_button"].rgba)

    elif entity_type_tag == "enemy_goomba":
        draw.ellipse([(img_w*0.1, img_h*0.2), (img_w*0.9, img_h*0.95)], fill=PM_PALETTES["goomba_brown"].rgba)
        draw.ellipse([(img_w*0.2, img_h*0.8), (img_w*0.45, img_h*0.98)], fill=PM_PALETTES["goomba_beige"].rgba)
        draw.ellipse([(img_w*0.55, img_h*0.8), (img_w*0.8, img_h*0.98)], fill=PM_PALETTES["goomba_beige"].rgba)
        eye_y = img_h*0.4
        draw.ellipse([(img_w*0.25, eye_y - img_h*0.1), (img_w*0.45, eye_y + img_h*0.1)], fill=PM_PALETTES["goomba_eye_white"].rgba)
        draw.ellipse([(img_w*0.55, eye_y - img_h*0.1), (img_w*0.75, eye_y + img_h*0.1)], fill=PM_PALETTES["goomba_eye_white"].rgba)
        draw.ellipse([(img_w*0.35, eye_y - img_h*0.05), (img_w*0.42, eye_y + img_h*0.05)], fill=PM_PALETTES["goomba_pupil_black"].rgba)
        draw.ellipse([(img_w*0.65, eye_y - img_h*0.05), (img_w*0.72, eye_y + img_h*0.05)], fill=PM_PALETTES["goomba_pupil_black"].rgba)
        draw.polygon([(img_w*0.4, img_h*0.65), (img_w*0.45, img_h*0.75), (img_w*0.5, img_h*0.65)], fill=PM_PALETTES["goomba_eye_white"].rgba)

    elif entity_type_tag == "item_star":
        center_x, center_y = img_w / 2, img_h / 2
        radius = min(img_w, img_h) * 0.4
        draw.ellipse([(center_x - radius, center_y - radius), (center_x + radius, center_y + radius)], fill=PM_PALETTES["item_star_yellow"].rgba)
        for i in range(5):
            angle = i * (360/5) + random.uniform(-10,10)
            sparkle_dist = radius * random.uniform(0.7, 1.1)
            sx1 = center_x + math.cos(math.radians(angle)) * sparkle_dist
            sy1 = center_y + math.sin(math.radians(angle)) * sparkle_dist
            sx2 = center_x + math.cos(math.radians(angle)) * (sparkle_dist + radius*0.3)
            sy2 = center_y + math.sin(math.radians(angle)) * (sparkle_dist + radius*0.3)
            draw.line([(sx1,sy1),(sx2,sy2)], fill=PM_PALETTES["mario_white_glove"].rgba, width=max(1, int(img_w/16)))

    elif entity_type_tag == "item_hammer_head":
        draw.rectangle([(0,0), (img_w, img_h)], fill=PM_PALETTES["scenery_rock_gray"].rgba)
        draw.rectangle([(0,0), (img_w, img_h*0.2)], fill=color.tint(PM_PALETTES["scenery_rock_gray"], -0.2).rgba)
        draw.rectangle([(0,img_h*0.8), (img_w, img_h)], fill=color.tint(PM_PALETTES["scenery_rock_gray"], -0.2).rgba)
        draw.line([(img_w*0.2, img_h*0.3), (img_w*0.8, img_h*0.4)], fill=color.tint(PM_PALETTES["scenery_rock_gray"], 0.3).rgba, width=max(1, int(img_h/10)))

    elif "scenery_grass" in entity_type_tag:
        draw.rectangle([(0,0), (img_w, img_h)], fill=PM_PALETTES["scenery_grass_green"].rgba)
        for _ in range(int(img_w*img_h/50)):
            px, py = random.randint(0,img_w-1), random.randint(0,img_h-1)
            speckle_col = color.tint(PM_PALETTES["scenery_grass_green"], random.uniform(-0.2, -0.1)).rgba
            draw.point((px,py), fill=speckle_col)
    elif "scenery_dirt" in entity_type_tag:
        draw.rectangle([(0,0), (img_w, img_h)], fill=PM_PALETTES["scenery_dirt_brown"].rgba)
        for _ in range(int(img_w*img_h/60)):
            px, py = random.randint(0,img_w-1), random.randint(0,img_h-1)
            speckle_col = color.tint(PM_PALETTES["scenery_dirt_brown"], random.uniform(-0.1, 0.1)).rgba
            draw.point((px,py), fill=speckle_col)
    elif "scenery_wood" in entity_type_tag:
        draw.rectangle([(0,0), (img_w, img_h)], fill=PM_PALETTES["scenery_wood_brown"].rgba)
        for i in range(int(img_h / random.uniform(3,5))):
            y_pos = random.randint(0, img_h-1)
            line_col = color.tint(PM_PALETTES["scenery_wood_brown"], random.uniform(-0.3, -0.1)).rgba
            draw.line([(0, y_pos), (img_w, y_pos + random.randint(-int(img_h/10),int(img_h/10)))], fill=line_col, width=max(1, int(img_h/20)))
        for i in range(int(img_w / random.uniform(8,12))):
            kx, ky = random.randint(0, img_w-1), random.randint(0, img_h-1)
            k_rad_x = random.randint(int(img_w/20),int(img_w/10))
            k_rad_y = random.randint(int(img_h/20),int(img_h/10))
            knot_col = color.tint(PM_PALETTES["scenery_wood_brown"], random.uniform(-0.4, -0.2)).rgba
            draw.ellipse([(kx-k_rad_x, ky-k_rad_y), (kx+k_rad_x, ky+k_rad_y)], fill=knot_col)
    elif "scenery_rock" in entity_type_tag:
        draw.rectangle([(0,0), (img_w, img_h)], fill=PM_PALETTES["scenery_rock_gray"].rgba)
        for _ in range(int(img_w*img_h/random.uniform(70,90))):
            px, py = random.randint(0,img_w-1), random.randint(0,img_h-1)
            poly_points = []
            num_sides = random.randint(3,5)
            avg_radius = random.uniform(img_w*0.05, img_w*0.20)
            for i_side in range(num_sides):
                angle = (i_side / num_sides + random.uniform(-0.1, 0.1)) * 2 * math.pi
                dist = avg_radius * random.uniform(0.7, 1.3)
                poly_points.append( (min(img_w-1, max(0, px + math.cos(angle)*dist)), min(img_h-1, max(0, py + math.sin(angle)*dist))) )
            if len(poly_points) < 3: continue
            facet_col = color.tint(PM_PALETTES["scenery_rock_gray"], random.uniform(-0.25, 0.15)).rgba
            draw.polygon(poly_points, fill=facet_col)

    else:
        chosen_palette_key = random.choice(specific_palette_keys) if specific_palette_keys else random.choice(list(PM_PALETTES.keys()))
        fallback_color = PM_PALETTES.get(chosen_palette_key, color.pink)
        draw.rectangle([(0,0), (img_w, img_h)], fill=fallback_color.rgba)
        print(f"☇[ CATSDK ]: Texture for '{entity_type_tag}' used a fallback fill with {chosen_palette_key}!☇")

    print(f"☇[ CATSDK ]: Created a vibrant texture for '{entity_type_tag}'!☇")
    return Texture(img)

### Entity Classes
class PaperEntity(Entity):
    def __init__(self, entity_type_tag="generic_pm_character", specific_palette_keys=None, is_billboard=True, texture_size=(32,32), **kwargs):
        super().__init__(**kwargs)
        self.entity_type_tag = entity_type_tag
        self.specific_palette_keys = specific_palette_keys
        self.is_billboard = is_billboard
        self.texture_size_w, self.texture_size_h = texture_size
        if not hasattr(self, 'model'):
            self.model = 'quad' if self.is_billboard else 'cube'
        
        if self.is_billboard:
            self.double_sided = True
            self.unlit = True
        else:
            self.unlit = kwargs.get('unlit', False)

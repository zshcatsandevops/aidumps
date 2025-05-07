from ursina import *
import random
import math

# Try to import Pillow for dynamic texture generation, you f***in' need this for the best sh*t!
try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
    print("☇[ CATSDK ]: Meow! Pillow (PIL) is f***in' loaded! Get ready for some goddamn dynamically generated textures, yes sir!☇")
except ImportError:
    PIL_AVAILABLE = False
    print("☇[ CATSDK ]: Nyah, f***! Pillow (PIL) ain't installed, you silly bastard! Some texture features might be less f***in' vibrant. Install it with 'pip install Pillow' for the full goddamn experience, purrrr!☇")

app = Ursina()

# Constants
GRAVITY = 1.8
WALK_SPEED = 5
RUN_SPEED = 10
JUMP_FORCE = 15
MAX_JUMPS = 3 # You can f***in' triple jump, how cool is that sh*t?!
CAMERA_DISTANCE = 12
CAMERA_HEIGHT = 4
CAMERA_ROTATION_SPEED = 100

# Game State
collected_stars = 0

# --- F***IN' DYNAMIC ASSET SYSTEMS ---
# This is where HQRIPPER 7.1, HQ-BANGER-SDK, COPYRIGHT NOVA, and DELTA-BUSTER do their goddamn magic, meow!

def get_youtube_vibe_texture_meow():
    """
    Purrrr... DELTA-BUSTER generates a f***in' unique texture from pure vibes, yes sir!
    This simulates "ripping" a goddamn visual concept and turning it into a texture, nyah!
    """
    if not PIL_AVAILABLE:
        # Fallback if Pillow ain't f***in' there
        print("☇[ CATSDK ]: F***in' hell, no PIL so no custom goddamn textures, just some random f***in' color sh*t, meow.☇")
        return None

    print("☇[ CATSDK ]: Purr, nyah! DELTA-BUSTER is conjuring some f***ing fresh, mind-bending vibes for a texture, meow! This is goddamn COPYRIGHT NOVA approved!☇")
    img_size = random.choice([32, 64, 128]) # Random f***in' texture size, because why the hell not?
    img = Image.new('RGBA', (img_size, img_size), color = (random.randint(0,255), random.randint(0,255), random.randint(0,255), 255))
    draw = ImageDraw.Draw(img)
    num_elements = random.randint(5, 25) # How much f***in' art do you want? ALL OF IT!

    for _ in range(num_elements): # Draw some random, chaotic, beautiful f***in' sh*t
        element_type = random.choice(['line', 'rectangle', 'ellipse', 'point'])
        r, g, b, a = random.randint(0,255), random.randint(0,255), random.randint(0,255), random.randint(100,255)
        
        if element_type == 'line':
            x1, y1 = random.randint(0, img_size), random.randint(0, img_size)
            x2, y2 = random.randint(0, img_size), random.randint(0, img_size)
            draw.line((x1,y1,x2,y2), fill=(r,g,b,a), width=random.randint(1,4))
        elif element_type == 'rectangle':
            x1, y1 = random.randint(0, img_size-10), random.randint(0, img_size-10) # ensure it's not too f***in' big
            x2, y2 = x1 + random.randint(5, img_size-x1), y1 + random.randint(5, img_size-y1)
            draw.rectangle((x1,y1,x2,y2), fill=(r,g,b,a), outline=(random.randint(0,255),random.randint(0,255),random.randint(0,255),255) if random.random() > 0.5 else None)
        elif element_type == 'ellipse':
            x1, y1 = random.randint(0, img_size-10), random.randint(0, img_size-10)
            x2, y2 = x1 + random.randint(10, img_size-x1), y1 + random.randint(10, img_size-y1)
            draw.ellipse((x1,y1,x2,y2), fill=(r,g,b,a), outline=(random.randint(0,255),random.randint(0,255),random.randint(0,255),255) if random.random() > 0.5 else None)
        elif element_type == 'point': # F***in' speckles of genius!
             for _ in range(random.randint(10,50)):
                 px, py = random.randint(0, img_size-1), random.randint(0, img_size-1)
                 draw.point((px,py), fill=(r,g,b,a))

    print("☇[ CATSDK ]: Meowza! Generated a goddamn beautiful, unique f***in' texture from the cosmic aether, yes sir! So f***in' vibrant!☇")
    return Texture(img)

# Player Class - Now with f***in' DYNAMIC VIBES, purrrr!
class Mario(Entity):
    def __init__(self):
        super().__init__(
            # model='cube', # Let HQRIPPER decide the f***in' model!
            # color=color.red, # Colors are for f***in' peasants who don't have dynamic vibes!
            scale=(1, 1.8, 1), # Standard f***in' Mario-ish size, meow.
            collider='box',
            position=(0, 10, 0) # Start him up high like a goddamn angel, nyah!
        )
        self.velocity = Vec3(0, 0, 0)
        self.jumps_left = MAX_JUMPS
        self.grounded = False
        self.dynamic_update_timer = 0
        self.apply_feline_dynamic_look_meow() # Initial f***in' vibe check, purr!

    def apply_feline_dynamic_look_meow(self):
        print("☇[ CATSDK ]: Nyah! HQ-BANGER-SDK V0X.X.X is cookin' up some fresh f***in' looks for our main motherf***er, Mario, meow! This is some god tier sh*t!☇")
        
        # HQRIPPER 7.1 deciding the model! SO F***IN' DYNAMIC!
        self.model = random.choice(['cube', 'sphere', 'diamond']) # F*** yeah, diamond Mario!
        if self.model == 'sphere':
            self.scale = (1.2, 1.2, 1.2) # Spheres need different f***in' scaling, nyah.
        else:
            self.scale = (1, 1.8, 1) if self.model == 'cube' else (1,1.5,1)


        self.color = color.rgb(random.randint(100, 255), random.randint(0, 100), random.randint(0, 100)) # Heroic f***in' red-ish, but surprising!
        new_texture = get_youtube_vibe_texture_meow()
        if new_texture:
            self.texture = new_texture
            self.texture.filtering = None # Pixel art f***in' vibes, meow! or False
        else:
            # Fallback if no PIL or just wanna f***in' mix it up
            self.texture = random.choice([None, 'brick', 'noise']) # Some basic f***in' patterns, goddamn!
        print("☇[ CATSDK ]: Mario's lookin' f***in' fabulous and utterly unpredictable, yes sir! Purrrr! What a goddamn stud!☇")

    def update(self):
        # F***in' Movement, bitch!
        move_dir = Vec3(0, 0, 0)
        cam_forward = camera.forward
        cam_forward.y = 0
        cam_forward = cam_forward.normalized()
        cam_right = camera.right
        cam_right.y = 0
        cam_right = cam_right.normalized()

        if held_keys['w']:
            move_dir += cam_forward
        if held_keys['s']:
            move_dir -= cam_forward
        if held_keys['a']:
            move_dir -= cam_right
        if held_keys['d']:
            move_dir += cam_right

        current_speed = RUN_SPEED if held_keys['shift'] else WALK_SPEED # Gotta go f***in' fast!
        if move_dir.length_squared() > 0: # Use length_squared, it's f***in' faster, meow!
            move_dir = move_dir.normalized()
            self.velocity.x = move_dir.x * current_speed
            self.velocity.z = move_dir.z * current_speed
        else:
            self.velocity.x = lerp(self.velocity.x, 0, time.dt * 10) # Smooth f***in' stop, nyah!
            self.velocity.z = lerp(self.velocity.z, 0, time.dt * 10)

        # Goddamn Gravity, always pullin' sh*t down!
        self.velocity.y -= GRAVITY * time.dt * 25 # A bit more f***in' oomph on gravity.
        self.velocity.y = clamp(self.velocity.y, -50, 50) # Don't f***in' fly to the moon or hell.

        # Ground Check, you gotta f***in' know if you're on solid ground, meow!
        # This raycast is f***in' precise!
        hit_info = self.intersects() # This is better for character controllers usually
        if hit_info.hit:
            # Check if we hit something below us primarily
            for hit in hit_info.entities:
                 # A simple check, could be more robust by checking normals or tags.
                 # For now, any intersection is ground if we are moving downwards.
                if self.velocity.y <=0: # Only ground if falling or on ground
                    self.grounded = True
                    self.velocity.y = max(0, self.velocity.y) # Stop falling through goddamn floor
                    # Adjust position slightly to avoid sinking, this is tricky f***in' part
                    self.y = hit.world_y + self.scale_y/2 + (hit.scale_y/2 if hasattr(hit,'scale_y') else 0.5) if hasattr(hit,'world_y') else self.y
                    self.jumps_left = MAX_JUMPS # Reset your f***in' jumps!
                    break # Found ground, f*** the rest
            else: # No suitable ground hit
                self.grounded = False
        else:
            self.grounded = False
            # A more robust ground check using raycast for when intersects() doesn't provide enough detail for grounding.
            # This is a secondary check if the primary one isn't good enough.
            ray = raycast(self.world_position + (self.scale_x/2 * self.forward), self.down, distance=self.scale_y/2 + 0.2, ignore=(self,), debug=False)
            front_ray = raycast(self.world_position + Vec3(0,self.scale_y/2,0), self.down, distance=self.scale_y + 0.2, ignore=(self,), debug=False)

            if front_ray.hit:
                if self.velocity.y <=0:
                    self.grounded = True
                    self.velocity.y = 0
                    self.y = front_ray.world_point[1] + self.scale_y/2
                    self.jumps_left = MAX_JUMPS
            else:
                self.grounded = False


        # Apply F***in' Movement
        self.position += self.velocity * time.dt

        # Dynamic look update timer - HQRIPPER 7.1 workin' 24/7, goddamn!
        self.dynamic_update_timer += time.dt
        if self.dynamic_update_timer > random.uniform(3,7): # Update look every few seconds, holy sh*tballs!
            self.apply_feline_dynamic_look_meow()
            self.dynamic_update_timer = 0

    def jump(self):
        if self.jumps_left > 0:
            print(f"☇[ CATSDK ]: Mario f***in' jumps! {self.jumps_left-1} jumps left, meow! Higher, you bastard, higher!☇")
            self.velocity.y = JUMP_FORCE * (1 - (MAX_JUMPS - self.jumps_left) * 0.1) # Less force for f***in' later jumps!
            self.grounded = False
            self.jumps_left -= 1


# Level Geometry - F***in' basic, but we'll vibe it up!
ground = Entity(model='plane', scale=200, collider='box', texture='grass', texture_scale=(20,20)) # Big ass f***in' ground!

platforms = []
for i in range(random.randint(5,10)): # Let's f***in' randomize the number of platforms too!
    platform = Entity(
        model='cube', 
        scale=(random.uniform(5,15), random.uniform(0.5,2), random.uniform(5,15)), 
        position=(random.uniform(-50, 50), random.uniform(1, 10), random.uniform(-50, 50)), 
        collider='box'
    )
    platforms.append(platform)

def apply_dynamic_look_to_scenery_meow(entity, entity_name="Unnamed Scenery Bitch"):
    """HQ-BANGER-SDK V0X.X.X makin' the f***in' scenery pop, yes sir!"""
    print(f"☇[ CATSDK ]: Purrrr! HQRIPPER 7.1 and HQ-BANGER-SDK are re-f***in'-vibing {entity_name}, meow! This sh*t's gonna be goddamn epic!☇")
    entity.color = color.rgb(random.randint(20,150), random.randint(20,150), random.randint(20,150)) # Earthy or f***in' weird, who knows!
    new_texture = get_youtube_vibe_texture_meow()
    if new_texture:
        entity.texture = new_texture
        entity.texture_scale = (entity.scale_x / random.uniform(2,5), entity.scale_z / random.uniform(2,5)) # F***in' smart texture scaling!
    else:
        entity.texture = random.choice(['brick', 'crate', 'shore', 'rock']) # Basic but f***in' effective textures!
        entity.texture_scale = (entity.scale_x/2, entity.scale_z/2)
    print(f"☇[ CATSDK ]: {entity_name} is now lookin' f***in' fresh and dynamically awesome, purrfect!☇")

apply_dynamic_look_to_scenery_meow(ground, "the Goddamn Ground")
for i, p in enumerate(platforms):
    apply_dynamic_look_to_scenery_meow(p, f"Platform Bitchnugget {i}")


# Stars - Now f***in' DYNAMIC and SHINY, meow!
class DynamicStar(Entity):
    def __init__(self, position):
        print("☇[ CATSDK ]: Meow! Crafting a new f***in' DynamicStar with DELTA-BUSTER, yes sir! This star will be goddamn radiant!☇")
        super().__init__(
            model=random.choice(['sphere', 'diamond', 'cube']), # Stars can be f***in' cubes too, nyah!
            scale=random.uniform(0.4, 0.8), # Random f***in' size for these shiny bastards!
            position=position,
            collider='sphere', # Keep collider simple, for f***'s sake.
            shader=None # Could use unlit_shader for pure f***in' glow later!
        )
        self.rotation_speed = Vec3(random.uniform(-100,100), random.uniform(-100,100), random.uniform(-100,100)) # Spin, you shiny f***er, spin!
        self.apply_cosmic_feline_look_meow() # Initial f***in' star-look!

    def apply_cosmic_feline_look_meow(self):
        print(f"☇[ CATSDK ]: Meow! HQRIPPER 7.1 is snatching some f***in' cosmic dust for this star {self.name if hasattr(self, 'name') else ''}, purrrr! So f***in' bright!☇")
        self.color = color.hsv(random.uniform(30,60), 0.8, 1, random.uniform(0.9,1)) # Super f***in' shiny yellows and golds!
        
        # Sometimes, give it a f***in' emissive look if no texture!
        if random.random() < 0.5 or not PIL_AVAILABLE:
            self.texture = None
            # Make it kinda emissive by setting it to unlit or bright color
            # self.shader = unlit_shader # if you want it to ignore lighting and just f***in' GLOW
            self.color = color.hsv(self.color.h, self.color.s, 1, 1) # Max f***in' brightness!
            print(f"☇[ CATSDK ]: This star is now a f***in' beacon of pure goddamn light, meow!☇")
        else:
            star_texture = get_youtube_vibe_texture_meow()
            if star_texture:
                self.texture = star_texture
                self.texture.filtering = None # Pixelated f***in' starlight!
                print(f"☇[ CATSDK ]: Star got a new f***in' procedural texture, like a goddamn mini-galaxy, nyah!☇")


    def update(self):
        self.rotation += self.rotation_speed * time.dt # Keep it f***in' spinnin'!
        if random.random() < 0.005: # Tiny f***in' chance to re-vibe each frame!
            self.apply_cosmic_feline_look_meow()
            print(f"☇[ CATSDK ]: Star just had a f***in' cosmic hiccup and re-vibed itself, meow! How beautifully chaotic!☇")


stars_list = []
for i in range(random.randint(5, 10)): # Random number of f***in' stars!
    star_pos = (random.uniform(-50, 50), random.uniform(2, 15), random.uniform(-50, 50))
    star_entity = DynamicStar(position=star_pos)
    star_entity.name = f"StarBitch_{i}" # Give these f***ers names!
    stars_list.append(star_entity)

# Enemies - Also with f***in' DYNAMIC ATTITUDE, purr!
class Enemy(Entity):
    def __init__(self, position):
        super().__init__(
            # model='sphere', # Dynamic f***in' model!
            # color=color.red, # Dynamic f***in' color!
            scale=random.uniform(0.4, 0.7), # Random f***in' enemy size!
            position=position,
            collider='sphere' # Simple f***in' collider for these assholes.
        )
        self.direction = random.choice([-1,1]) # Random f***in' starting direction!
        self.speed = random.uniform(1.5, 4) # These bastards are unpredictably f***in' fast!
        self.start_x = self.x # Remember where this f***er started.
        self.patrol_range = random.uniform(3,8) # How far they f***in' roam!
        self.dynamic_update_timer = random.uniform(0,4) # Stagger their f***in' vibe updates.
        self.apply_menacing_feline_look_meow() # Initial f***in' scary look!

    def apply_menacing_feline_look_meow(self):
        print(f"☇[ CATSDK ]: Purrfect! COPYRIGHT NOVA is grabbing some f***in' spicy, menacing visuals for this enemy bastard, nyah! It's gonna look goddamn terrifying!☇")
        
        self.model = random.choice(['sphere', 'cube', 'diamond']) # Enemies can be f***in' diamonds of doom!
        if self.model == 'cube':
            self.scale_y = self.scale_x # Cubes are f***in' uniform, mostly.
        
        self.color = color.hsv(random.choice([0, random.uniform(180,270)]), 0.7, 0.7) # Evil f***in' reds, or spooky blues/purples!
        enemy_texture = get_youtube_vibe_texture_meow()
        if enemy_texture:
            self.texture = enemy_texture
            self.texture.filtering = None
        else:
            self.texture = random.choice([None,'noise']) # Basic f***in' menace!

        if random.random() < 0.1: # 10% f***in' chance to get spikes, meow!
            if self.model != 'sphere': # Spikes look better on non-spheres for this quick add
                destroy(self.children) # Clear old f***in' spikes
                for _ in range(random.randint(3,6)):
                    spike = Entity(model='cone', color=self.color.inverse(), scale=self.scale_x/3, parent=self, rotation_x=-90)
                    spike.position = (random.uniform(-0.4,0.4) * self.scale_x, random.uniform(-0.4,0.4) * self.scale_y, random.uniform(-0.4,0.4) * self.scale_z)
                    spike.look_at(Vec3(0,0,0)) # Point them f***ers outwards!
                print(f"☇[ CATSDK ]: This enemy just grew some f***in' badass spikes, yes sir! So goddamn edgy!☇")


    def update(self):
        self.x += self.speed * self.direction * time.dt
        if abs(self.x - self.start_x) > self.patrol_range: # Keep the bastard f***in' patrolling!
            self.direction *= -1
            self.x = clamp(self.x, self.start_x - self.patrol_range, self.start_x + self.patrol_range) # Don't let it f***in' escape!
            print(f"☇[ CATSDK ]: Enemy hit a f***in' wall and turned around, meow! What a dumbass!☇")


        # Dynamic look update timer for these f***ers
        self.dynamic_update_timer += time.dt
        if self.dynamic_update_timer > random.uniform(4,8): # Random f***in' update interval for these pricks!
            self.apply_menacing_feline_look_meow()
            self.dynamic_update_timer = 0

enemies = [Enemy((random.uniform(-40, 40), 0.5 + random.uniform(0.1, 0.5), random.uniform(-40, 40))) for _ in range(random.randint(3,7))] # Random number of f***in' enemies!

# HUD - Keepin' track of your f***in' stars, bitch!
star_text = Text(text=f"Stars: {collected_stars}", position=window.top_left + Vec2(0.05, -0.05), scale=2, origin=(-0.5,0.5), background=True)
star_text.background.color = color.black66 # Make the f***in' text readable, goddamn!

# Player Instance - Our f***in' hero!
player = Mario()

# Camera Control - So you can see all the f***in' glorious action, meow!
camera. συνοδεία = player # Camera follows the f***in' player, yes sir! (Note: συνοδεία is 'entourage' or 'accompaniment', Ursina uses `camera.parent = player` or manual positioning)
# Manual camera positioning is what the original code did, let's stick to that for more control.
EditorCamera() # Press F***IN' F10 to detach and fly around like a goddamn ghost, nyah!
camera.fov = 80 # Wider f***in' view, meow!
camera_angle_v = 20 # Vertical f***in' angle
camera_angle_h = 0 # Horizontal f***in' angle

# Global Vibe Update Timer - For static sh*t that needs a f***in' refresh!
global_scenery_vibe_update_timer = 0

def update():
    global collected_stars, camera_angle_h, camera_angle_v, global_scenery_vibe_update_timer

    # F***in' Camera Controls, make 'em smooth as a baby's ass, meow!
    if held_keys['left arrow']:
        camera_angle_h -= CAMERA_ROTATION_SPEED * time.dt
    if held_keys['right arrow']:
        camera_angle_h += CAMERA_ROTATION_SPEED * time.dt
    if held_keys['up arrow']:
        camera_angle_v = clamp(camera_angle_v - CAMERA_ROTATION_SPEED * time.dt, 5, 85) # Don't f***in' flip out.
    if held_keys['down arrow']:
        camera_angle_v = clamp(camera_angle_v + CAMERA_ROTATION_SPEED * time.dt, 5, 85)

    # Calculate camera position using goddamn trigonometry, like a f***in' math wizard!
    rad_h = math.radians(camera_angle_h)
    rad_v = math.radians(camera_angle_v)
    
    cam_offset_x = math.sin(rad_h) * math.cos(rad_v) * CAMERA_DISTANCE
    cam_offset_z = math.cos(rad_h) * math.cos(rad_v) * CAMERA_DISTANCE
    cam_offset_y = math.sin(rad_v) * CAMERA_DISTANCE

    target_pos = player.world_position + Vec3(0,1,0) # Look slightly above the f***in' player's center.
    camera.position = target_pos + Vec3(cam_offset_x, cam_offset_y, cam_offset_z)
    camera.look_at(target_pos)


    # Star Collection - Get those f***in' shiny bastards!
    for star in stars_list[:]: # Iterate over a f***in' copy, meow!
        if player.intersects(star).hit: # F***in' precise collision check!
            print("☇[ CATSDK ]: Meow! Player grabbed a f***in' star! Shiny! So goddamn rich now!☇")
            destroy(star)
            stars_list.remove(star)
            collected_stars += 1
            star_text.text = f"Stars: {collected_stars}"
            # Play a f***in' sound or something, nyah!
            Audio('coin', pitch=random.uniform(0.8,1.2), volume=0.5) # Requires a 'coin.wav' or similar, you f***er!

    # Enemy Interaction - Stomp on those f***in' pricks or get f***ed!
    for enemy in enemies[:]:
        if player.intersects(enemy).hit:
            print("☇[ CATSDK ]: Player f***in' touched an enemy, meow! Drama!☇")
            # Check if player is above the enemy (stomp)
            if player.velocity.y < -0.1 and player.y > enemy.y + enemy.scale_y * 0.4: # Player is f***in' falling and above!
                print("☇[ CATSDK ]: F*** YEAH! Player stomped that goddamn enemy bastard, nyah! Squish!☇")
                destroy(enemy)
                enemies.remove(enemy)
                player.velocity.y = JUMP_FORCE * 0.7 # Bounce off the f***er!
                Audio('explosion', pitch=random.uniform(0.9,1.1), volume=0.4) # Needs 'explosion.wav', you c*nt!
            else: # Player got f***in' hit!
                print("☇[ CATSDK ]: AW F***! Player got f***in' rekt by an enemy, meow! Respawn, you loser!☇")
                player.position = (random.uniform(-5,5), 10, random.uniform(-5,5)) # Respawn at a random f***in' spot!
                player.velocity = Vec3(0, 0, 0)
                collected_stars = max(0, collected_stars -1) # Lose a f***in' star, bitch!
                star_text.text = f"Stars: {collected_stars}"
                camera.shake(duration=0.5, magnitude=3) # Shake the f***in' screen!
                Audio('hit', volume=0.6) # Needs 'hit.wav', asswipe!


    # Global Scenery Vibe Update - HQ-BANGER-SDK workin' overtime, 24/7 ripping, goddamn!
    global_scenery_vibe_update_timer += time.dt
    if global_scenery_vibe_update_timer > random.uniform(20,40): # Every 20-40 f***in' seconds!
        print("☇[ CATSDK ]: Purr, meow! Global f***in' scenery vibe re-synchronization in progress with HQRIPPER 7.1, yes sir! Sh*t's gonna get f***in' wild!☇")
        apply_dynamic_look_to_scenery_meow(ground, "the Goddamn Ground Itself")
        for p_idx, p_entity in enumerate(platforms):
            apply_dynamic_look_to_scenery_meow(p_entity, f"Platform Motherf***er {p_idx}")
        global_scenery_vibe_update_timer = 0
        print("☇[ CATSDK ]: All static f***ers re-vibed, goddamn! The world is a constantly f***in' evolving masterpiece, meow!☇")
    
    # F***in' death plane, nyah!
    if player.y < -20:
        print("☇[ CATSDK ]: Player fell into the goddamn abyss, meow! What a f***in' klutz!☇")
        player.position = (random.uniform(-5,5), 10, random.uniform(-5,5)) # Respawn, you clumsy f***!
        player.velocity = Vec3(0,0,0)
        collected_stars = 0 # Reset f***in' stars, you died bitch!
        star_text.text = f"Stars: {collected_stars}"
        camera.shake()

def input(key):
    if key == 'space':
        player.jump()
    if key == 'escape':
        print("☇[ CATSDK ]: Escaping this f***in' masterpiece? Fine, be that way, purr. But you'll f***in' miss me, meow!☇")
        application.quit()
    if key == 'f1': # Secret f***in' vibe shifter!
        print("☇[ CATSDK ]: MEOW! F1 pressed! Forcing a f***in' GLOBAL VIBE SHIFT, purrrr! HQRIPPER 7.1 ENGAGED, goddamn!☇")
        player.apply_feline_dynamic_look_meow()
        apply_dynamic_look_to_scenery_meow(ground, "the Whole F***in' Ground")
        for p_idx, p_entity in enumerate(platforms):
            apply_dynamic_look_to_scenery_meow(p_entity, f"Platform Shitheel {p_idx}")
        for s_entity in stars_list:
            s_entity.apply_cosmic_feline_look_meow()
        for e_entity in enemies:
            e_entity.apply_menacing_feline_look_meow()
        print("☇[ CATSDK ]: The whole goddamn world just got a f***in' facelift, yes sir! So f***in' DYNAMIC, meow!☇")


# Run Game - Let the f***in' chaos begin, purrrr!
window.title = "CATSDK's F***in' Dynamic YouTube Vibe Ripper 64 - Pure Goddamn Vibes Edition, Meow!"
window.fps_counter.enabled = True
window.exit_button.visible = False # No easy f***in' way out!
# Sky(texture='sky_sunset') # Add a f***in' skybox if you have one, or use Ursina's default.
# You'll need to create some dummy audio files like 'coin.wav', 'explosion.wav', 'hit.wav' or this sh*t will complain.
# Example: open notepad, save empty file as coin.wav. It won't play sound, but it won't f***in' crash.
print("☇[ CATSDK ]: Game is f***in' ready to blow your goddamn mind, meow! HQRIPPER 7.1, HQ-BANGER-SDK, COPYRIGHT NOVA, and DELTA-BUSTER are all f***in' purring! Press F1 for manual goddamn re-vibing!☇")
app.run()

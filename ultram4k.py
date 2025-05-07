from ursina import *
import random
import math

# Try to import Pillow for dynamic texture generation
try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
    print("[CATSDK]: Pillow (PIL) is loaded. Dynamic texture generation is available.")
except ImportError:
    PIL_AVAILABLE = False
    print("[CATSDK]: Pillow (PIL) is not installed. Some texture features may be limited. Install it with 'pip install Pillow' for full functionality.")

app = Ursina()

# Constants
GRAVITY = 1.8
WALK_SPEED = 5
RUN_SPEED = 10
JUMP_FORCE = 15
MAX_JUMPS = 3  # Allows triple jumping
CAMERA_DISTANCE = 12
CAMERA_HEIGHT = 4
CAMERA_ROTATION_SPEED = 100

# Game State
collected_stars = 0

# --- Dynamic Asset Systems ---
def get_youtube_vibe_texture_meow():
    """
    Generates a unique texture using DELTA-BUSTER, simulating visual concept extraction.
    """
    if not PIL_AVAILABLE:
        print("[CATSDK]: Pillow (PIL) is not available. Using fallback textures.")
        return None

    print("[CATSDK]: Generating a new texture using DELTA-BUSTER.")
    img_size = random.choice([32, 64, 128])  # Random texture size
    img = Image.new('RGBA', (img_size, img_size), color=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255))
    draw = ImageDraw.Draw(img)
    num_elements = random.randint(5, 25)  # Number of artistic elements

    for _ in range(num_elements):
        element_type = random.choice(['line', 'rectangle', 'ellipse', 'point'])
        r, g, b, a = random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(100, 255)
        
        if element_type == 'line':
            x1, y1 = random.randint(0, img_size), random.randint(0, img_size)
            x2, y2 = random.randint(0, img_size), random.randint(0, img_size)
            draw.line((x1, y1, x2, y2), fill=(r, g, b, a), width=random.randint(1, 4))
        elif element_type == 'rectangle':
            x1, y1 = random.randint(0, img_size - 10), random.randint(0, img_size - 10)
            x2, y2 = x1 + random.randint(5, img_size - x1), y1 + random.randint(5, img_size - y1)
            draw.rectangle((x1, y1, x2, y2), fill=(r, g, b, a), outline=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255) if random.random() > 0.5 else None)
        elif element_type == 'ellipse':
            x1, y1 = random.randint(0, img_size - 10), random.randint(0, img_size - 10)
            x2, y2 = x1 + random.randint(10, img_size - x1), y1 + random.randint(10, img_size - y1)
            draw.ellipse((x1, y1, x2, y2), fill=(r, g, b, a), outline=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255) if random.random() > 0.5 else None)
        elif element_type == 'point':
            for _ in range(random.randint(10, 50)):
                px, py = random.randint(0, img_size - 1), random.randint(0, img_size - 1)
                draw.point((px, py), fill=(r, g, b, a))

    print("[CATSDK]: Generated a new unique texture.")
    return Texture(img)

# Player Class with Dynamic Appearance
class Mario(Entity):
    def __init__(self):
        super().__init__(
            scale=(1, 1.8, 1),  # Standard Mario-like size
            collider='box',
            position=(0, 10, 0)  # Starts elevated
        )
        self.velocity = Vec3(0, 0, 0)
        self.jumps_left = MAX_JUMPS
        self.grounded = False
        self.dynamic_update_timer = 0
        self.apply_feline_dynamic_look_meow()  # Initial appearance update

    def apply_feline_dynamic_look_meow(self):
        print("[CATSDK]: Applying a new dynamic look to Mario.")
        self.model = random.choice(['cube', 'sphere', 'diamond'])
        if self.model == 'sphere':
            self.scale = (1.2, 1.2, 1.2)
        else:
            self.scale = (1, 1.8, 1) if self.model == 'cube' else (1, 1.5, 1)
        self.color = color.rgb(random.randint(100, 255), random.randint(0, 100), random.randint(0, 100))
        new_texture = get_youtube_vibe_texture_meow()
        if new_texture:
            self.texture = new_texture
            self.texture.filtering = None
        else:
            self.texture = random.choice([None, 'brick', 'noise'])
        print("[CATSDK]: Mario's appearance has been updated.")

    def update(self):
        # Movement Logic
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

        current_speed = RUN_SPEED if held_keys['shift'] else WALK_SPEED
        if move_dir.length_squared() > 0:
            move_dir = move_dir.normalized()
            self.velocity.x = move_dir.x * current_speed
            self.velocity.z = move_dir.z * current_speed
        else:
            self.velocity.x = lerp(self.velocity.x, 0, time.dt * 10)
            self.velocity.z = lerp(self.velocity.z, 0, time.dt * 10)

        # Gravity Application
        self.velocity.y -= GRAVITY * time.dt * 25
        self.velocity.y = clamp(self.velocity.y, -50, 50)

        # Ground Detection
        hit_info = self.intersects()
        if hit_info.hit:
            for hit in hit_info.entities:
                if self.velocity.y <= 0:
                    self.grounded = True
                    self.velocity.y = max(0, self.velocity.y)
                    self.y = hit.world_y + self.scale_y / 2 + (hit.scale_y / 2 if hasattr(hit, 'scale_y') else 0.5) if hasattr(hit, 'world_y') else self.y
                    self.jumps_left = MAX_JUMPS
                    break
            else:
                self.grounded = False
        else:
            self.grounded = False
            ray = raycast(self.world_position + (self.scale_x / 2 * self.forward), self.down, distance=self.scale_y / 2 + 0.2, ignore=(self,), debug=False)
            front_ray = raycast(self.world_position + Vec3(0, self.scale_y / 2, 0), self.down, distance=self.scale_y + 0.2, ignore=(self,), debug=False)
            if front_ray.hit:
                if self.velocity.y <= 0:
                    self.grounded = True
                    self.velocity.y = 0
                    self.y = front_ray.world_point[1] + self.scale_y / 2
                    self.jumps_left = MAX_JUMPS
            else:
                self.grounded = False

        # Apply Movement
        self.position += self.velocity * time.dt

        # Dynamic Appearance Update
        self.dynamic_update_timer += time.dt
        if self.dynamic_update_timer > random.uniform(3, 7):
            self.apply_feline_dynamic_look_meow()
            self.dynamic_update_timer = 0

    def jump(self):
        if self.jumps_left > 0:
            print(f"[CATSDK]: Mario jumps! Jumps left: {self.jumps_left - 1}")
            self.velocity.y = JUMP_FORCE * (1 - (MAX_JUMPS - self.jumps_left) * 0.1)
            self.grounded = False
            self.jumps_left -= 1

# Level Geometry
ground = Entity(model='plane', scale=200, collider='box', texture='grass', texture_scale=(20, 20))

platforms = []
for i in range(random.randint(5, 10)):
    platform = Entity(
        model='cube',
        scale=(random.uniform(5, 15), random.uniform(0.5, 2), random.uniform(5, 15)),
        position=(random.uniform(-50, 50), random.uniform(1, 10), random.uniform(-50, 50)),
        collider='box'
    )
    platforms.append(platform)

def apply_dynamic_look_to_scenery_meow(entity, entity_name="Unnamed Scenery"):
    """Updates the appearance of scenery entities."""
    print(f"[CATSDK]: Applying a new dynamic look to {entity_name}.")
    entity.color = color.rgb(random.randint(20, 150), random.randint(20, 150), random.randint(20, 150))
    new_texture = get_youtube_vibe_texture_meow()
    if new_texture:
        entity.texture = new_texture
        entity.texture_scale = (entity.scale_x / random.uniform(2, 5), entity.scale_z / random.uniform(2, 5))
    else:
        entity.texture = random.choice(['brick', 'crate', 'shore', 'rock'])
        entity.texture_scale = (entity.scale_x / 2, entity.scale_z / 2)
    print(f"[CATSDK]: {entity_name} has been updated with a new appearance.")

apply_dynamic_look_to_scenery_meow(ground, "Ground")
for i, p in enumerate(platforms):
    apply_dynamic_look_to_scenery_meow(p, f"Platform {i}")

# Stars with Dynamic Appearance
class DynamicStar(Entity):
    def __init__(self, position):
        print("[CATSDK]: Creating a new DynamicStar.")
        super().__init__(
            model=random.choice(['sphere', 'diamond', 'cube']),
            scale=random.uniform(0.4, 0.8),
            position=position,
            collider='sphere',
            shader=None
        )
        self.rotation_speed = Vec3(random.uniform(-100, 100), random.uniform(-100, 100), random.uniform(-100, 100))
        self.apply_cosmic_feline_look_meow()

    def apply_cosmic_feline_look_meow(self):
        print(f"[CATSDK]: Applying a new appearance to star {self.name if hasattr(self, 'name') else ''}.")
        self.color = color.hsv(random.uniform(30, 60), 0.8, 1, random.uniform(0.9, 1))
        if random.random() < 0.5 or not PIL_AVAILABLE:
            self.texture = None
            self.color = color.hsv(self.color.h, self.color.s, 1, 1)
            print(f"[CATSDK]: This star is now brightly colored.")
        else:
            star_texture = get_youtube_vibe_texture_meow()
            if star_texture:
                self.texture = star_texture
                self.texture.filtering = None
                print(f"[CATSDK]: Star has a new procedural texture.")

    def update(self):
        self.rotation += self.rotation_speed * time.dt
        if random.random() < 0.005:
            self.apply_cosmic_feline_look_meow()

stars_list = []
for i in range(random.randint(5, 10)):
    star_pos = (random.uniform(-50, 50), random.uniform(2, 15), random.uniform(-50, 50))
    star_entity = DynamicStar(position=star_pos)
    star_entity.name = f"Star_{i}"
    stars_list.append(star_entity)

# Enemies with Dynamic Appearance
class Enemy(Entity):
    def __init__(self, position):
        super().__init__(
            scale=random.uniform(0.4, 0.7),
            position=position,
            collider='sphere'
        )
        self.direction = random.choice([-1, 1])
        self.speed = random.uniform(1.5, 4)
        self.start_x = self.x
        self.patrol_range = random.uniform(3, 8)
        self.dynamic_update_timer = random.uniform(0, 4)
        self.apply_menacing_feline_look_meow()

    def apply_menacing_feline_look_meow(self):
        print("[CATSDK]: Applying a new appearance to the enemy.")
        self.model = random.choice(['sphere', 'cube', 'diamond'])
        if self.model == 'cube':
            self.scale_y = self.scale_x
        self.color = color.hsv(random.choice([0, random.uniform(180, 270)]), 0.7, 0.7)
        enemy_texture = get_youtube_vibe_texture_meow()
        if enemy_texture:
            self.texture = enemy_texture
            self.texture.filtering = None
        else:
            self.texture = random.choice([None, 'noise'])
        if random.random() < 0.1 and self.model != 'sphere':
            destroy(self.children)
            for _ in range(random.randint(3, 6)):
                spike = Entity(model='cone', color=self.color.inverse(), scale=self.scale_x / 3, parent=self, rotation_x=-90)
                spike.position = (random.uniform(-0.4, 0.4) * self.scale_x, random.uniform(-0.4, 0.4) * self.scale_y, random.uniform(-0.4, 0.4) * self.scale_z)
                spike.look_at(Vec3(0, 0, 0))
            print("[CATSDK]: The enemy now has spikes.")

    def update(self):
        self.x += self.speed * self.direction * time.dt
        if abs(self.x - self.start_x) > self.patrol_range:
            self.direction *= -1
            self.x = clamp(self.x, self.start_x - self.patrol_range, self.start_x + self.patrol_range)
            print("[CATSDK]: Enemy turned around.")

        self.dynamic_update_timer += time.dt
        if self.dynamic_update_timer > random.uniform(4, 8):
            self.apply_menacing_feline_look_meow()
            self.dynamic_update_timer = 0

enemies = [Enemy((random.uniform(-40, 40), 0.5 + random.uniform(0.1, 0.5), random.uniform(-40, 40))) for _ in range(random.randint(3, 7))]

# HUD
star_text = Text(text=f"Stars: {collected_stars}", position=window.top_left + Vec2(0.05, -0.05), scale=2, origin=(-0.5, 0.5), background=True)
star_text.background.color = color.black66

# Player Instance
player = Mario()

# Camera Control
camera.fov = 80
camera_angle_v = 20
camera_angle_h = 0

# Global Vibe Update Timer
global_scenery_vibe_update_timer = 0

def update():
    global collected_stars, camera_angle_h, camera_angle_v, global_scenery_vibe_update_timer

    # Camera Controls
    if held_keys['left arrow']:
        camera_angle_h -= CAMERA_ROTATION_SPEED * time.dt
    if held_keys['right arrow']:
        camera_angle_h += CAMERA_ROTATION_SPEED * time.dt
    if held_keys['up arrow']:
        camera_angle_v = clamp(camera_angle_v - CAMERA_ROTATION_SPEED * time.dt, 5, 85)
    if held_keys['down arrow']:
        camera_angle_v = clamp(camera_angle_v + CAMERA_ROTATION_SPEED * time.dt, 5, 85)

    rad_h = math.radians(camera_angle_h)
    rad_v = math.radians(camera_angle_v)
    cam_offset_x = math.sin(rad_h) * math.cos(rad_v) * CAMERA_DISTANCE
    cam_offset_z = math.cos(rad_h) * math.cos(rad_v) * CAMERA_DISTANCE
    cam_offset_y = math.sin(rad_v) * CAMERA_DISTANCE
    target_pos = player.world_position + Vec3(0, 1, 0)
    camera.position = target_pos + Vec3(cam_offset_x, cam_offset_y, cam_offset_z)
    camera.look_at(target_pos)

    # Star Collection
    for star in stars_list[:]:
        if player.intersects(star).hit:
            print("[CATSDK]: Player collected a star.")
            destroy(star)
            stars_list.remove(star)
            collected_stars += 1
            star_text.text = f"Stars: {collected_stars}"
            Audio('coin', pitch=random.uniform(0.8, 1.2), volume=0.5)

    # Enemy Interaction
    for enemy in enemies[:]:
        if player.intersects(enemy).hit:
            print("[CATSDK]: Player touched an enemy.")
            if player.velocity.y < -0.1 and player.y > enemy.y + enemy.scale_y * 0.4:
                print("[CATSDK]: Player stomped the enemy.")
                destroy(enemy)
                enemies.remove(enemy)
                player.velocity.y = JUMP_FORCE * 0.7
                Audio('explosion', pitch=random.uniform(0.9, 1.1), volume=0.4)
            else:
                print("[CATSDK]: Player was hit by an enemy and respawned.")
                player.position = (random.uniform(-5, 5), 10, random.uniform(-5, 5))
                player.velocity = Vec3(0, 0, 0)
                collected_stars = max(0, collected_stars - 1)
                star_text.text = f"Stars: {collected_stars}"
                camera.shake(duration=0.5, magnitude=3)
                Audio('hit', volume=0.6)

    # Global Scenery Update
    global_scenery_vibe_update_timer += time.dt
    if global_scenery_vibe_update_timer > random.uniform(20, 40):
        print("[CATSDK]: Updating scenery textures.")
        apply_dynamic_look_to_scenery_meow(ground, "Ground")
        for p_idx, p_entity in enumerate(platforms):
            apply_dynamic_look_to_scenery_meow(p_entity, f"Platform {p_idx}")
        global_scenery_vibe_update_timer = 0
        print("[CATSDK]: Scenery textures have been updated.")

    # Death Plane
    if player.y < -20:
        print("[CATSDK]: Player fell off the platform and respawned.")
        player.position = (random.uniform(-5, 5), 10, random.uniform(-5, 5))
        player.velocity = Vec3(0, 0, 0)
        collected_stars = 0
        star_text.text = f"Stars: {collected_stars}"
        camera.shake()

def input(key):
    if key == 'space':
        player.jump()
    if key == 'escape':
        print("[CATSDK]: Exiting the game.")
        application.quit()
    if key == 'f1':
        print("[CATSDK]: F1 pressed! Triggering a global texture update.")
        player.apply_feline_dynamic_look_meow()
        apply_dynamic_look_to_scenery_meow(ground, "Ground")
        for p_idx, p_entity in enumerate(platforms):
            apply_dynamic_look_to_scenery_meow(p_entity, f"Platform {p_idx}")
        for s_entity in stars_list:
            s_entity.apply_cosmic_feline_look_meow()
        for e_entity in enemies:
            e_entity.apply_menacing_feline_look_meow()
        print("[CATSDK]: All entities have been updated with new appearances.")

# Run Game
window.title = "CATSDK's Dynamic Texture Game"
window.fps_counter.enabled = True
window.exit_button.visible = False
# Note: Audio files 'coin.wav', 'explosion.wav', and 'hit.wav' are required to avoid errors. Use dummy files if needed.
print("[CATSDK]: Game is ready. Press F1 to manually update textures.")
app.run()

from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.shaders import lit_with_shadows_shader
import random

app = Ursina()

# Set default shader for lighting
Entity.default_shader = lit_with_shadows_shader

# Ground
ground = Entity(model='plane', collider='box', scale=64, texture='grass', texture_scale=(4,4), color=color.green)

# Player setup with third-person camera
player = FirstPersonController(model='cube', color=color.red, origin_y=-0.5, speed=5)
player.camera_pivot.z = -5  # Distance behind player
player.camera_pivot.y = 2   # Height above player
player.collider = BoxCollider(player, Vec3(0,1,0), Vec3(1,2,1))

# Score system
stars_collected = 0
total_stars = 3
score_text = Text('Stars: 0/3', position=(-0.8, 0.45), scale=2, color=color.yellow)

# Store star entities in a list for collision checking
stars = []

# Generate random platforms
random.seed(42)  # For reproducibility
for i in range(20):
    platform = Entity(
        model='cube',
        origin_y=-0.5,
        scale=(random.uniform(2,5), random.uniform(0.5,1), random.uniform(2,5)),
        texture='brick',
        texture_scale=(1,2),
        x=random.uniform(-20,20),
        y=random.uniform(0,5),
        z=random.uniform(-20,20),
        collider='box',
        color=color.hsv(0, 0, random.uniform(0.9, 1))
    )

# Spawn stars on some platforms
star_positions = [(5,3,5), (-10,2,-5), (15,4,10)]  # Pre-set for easy collection
for pos in star_positions:
    star = Entity(
        model='sphere',
        color=color.yellow,
        scale=0.5,
        position=pos,
        collider='sphere'
    )
    stars.append(star)  # Add to stars list

# Lighting and sky
sun = DirectionalLight()
sun.look_at(Vec3(1,-1,-1))
Sky()

def update():
    global stars_collected
    
    # Check for star collection using distance-based detection
    for star in stars[:]:  # Use slice to avoid modification during iteration
        if distance(player.position, star.position) < 2:
            stars.remove(star)
            destroy(star)
            stars_collected += 1
            score_text.text = f'Stars: {stars_collected}/{total_stars}'
            
            if stars_collected >= total_stars:
                Text('You collected all stars! Mario wins!', origin=(0,0), scale=3, color=color.gold, duration=5)
    
    # Basic win/exit
    if held_keys['escape']:
        quit()

app.run()

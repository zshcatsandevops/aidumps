from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from math import sin, cos

# Initialize Ursina app with error handling
try:
    app = Ursina(
        title="Vibey Mario Odyssey",
        borderless=False,
        fullscreen=False,
        development_mode=True,
        size=(1280, 720)  # Explicit window size
    )
    app.target_fps = 60
except Exception as e:
    print(f"Ursina failed to start: {e}")
    exit(1)

# Create Sky (procedural, no texture)
sky = Sky(color=color.rgb(135, 206, 235))  # Vibey sky blue, no texture file

# Create player
try:
    player = FirstPersonController(
        position=(0, 2, 0),  # Slightly higher to avoid clipping
        gravity=1,
        jump_height=2,
        speed=5
    )
    player.cursor.visible = False
except Exception as e:
    print(f"Player creation failed: {e}")
    exit(1)

# Ground
ground = Entity(
    model='plane',
    scale=(100, 1, 100),
    color=color.green,  # Solid color, no texture
    collider='box'  # Simpler collider
)

# Create Peach's Castle and environment
def create_level():
    # Castle (blocky cube placeholder)
    castle = Entity(
        model='cube',
        position=(0, 0, 0),
        scale=(10, 10, 10),
        color=color.red,  # Vibrant red for castle vibes
        collider='box'
    )
    # Tree (cylinder for a funky trunk)
    tree = Entity(
        model='cylinder',
        scale=(1, 5, 1),
        position=(10, 0, 10),
        color=color.brown,  # Tree trunk color
        collider='box'
    )
    # Water (shimmering plane)
    water = Entity(
        model='plane',
        scale=(5, 0.1, 5),
        position=(-10, 0.1, -10),
        color=color.cyan,  # Bright water color
        collider='box'
    )
    # Monkey Slide (sloped plane)
    slide = Entity(
        model='plane',
        position=(20, 5, 20),
        scale=(5, 0.1, 10),
        rotation=(0, 0, -30),  # Slope for sliding
        color=color.yellow,  # Sunny slide color
        collider='box'
    )
    # Spinning Star collectible
    star = Entity(
        model='quad',
        color=color.gold,  # Shiny star color, no texture
        position=(22, 6, 22),
        scale=0.5,
        billboard=True,  # Faces player
        collider='box'
    )
    # Animate star rotation for vibes
    def spin_star():
        if star:  # Check if star exists
            star.rotation_y += time.dt * 100  # Spin speed
    star.update = spin_star
    return castle, slide, star, water

# Create level
try:
    castle, slide, star, water = create_level()
except Exception as e:
    print(f"Level creation failed: {e}")
    exit(1)

# Update function for gameplay mechanics
def update():
    try:
        # Sliding mechanic
        if player.intersects(slide).hit:
            # Calculate slide direction from rotation
            slide_angle = slide.rotation_z * (3.14159 / 180)  # Radians
            slide_direction = Vec3(0, -sin(slide_angle), -cos(slide_angle)).normalized()
            player.position += slide_direction * 10 * time.dt  # Smooth slide
            player.speed = 10  # Fast on slide
        else:
            player.speed = 5  # Normal speed

        # Star collection
        if player.intersects(star).hit:
            print("Star collected! 🌟")
            destroy(star)

        # Water interaction (bobbing effect)
        if player.intersects(water).hit:
            player.speed = 2  # Slow in water
            player.y += sin(time.time() * 5) * 0.02  # Gentle bob
    except Exception as e:
        print(f"Update failed: {e}")

# Input handling for jumping
def input(key):
    if key == 'space' and player.grounded:
        player.jump()

# Debug to confirm game is running
print("Game running! Use WASD to move, mouse to look, space to jump.")

# Run the game
try:
    app.run()
except Exception as e:
    print(f"Game loop failed: {e}")
    exit(1)

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

# Build Peach's Castle
def build_castle():
    # Main building
    Entity(model='cube', position=(0, 5, 0), scale=(20, 10, 20), color=color.white, collider='box')
    # Roof
    Entity(model='cube', position=(0, 10, 0), scale=(18, 2, 18), color=color.red)
    # Towers
    tower_positions = [(10, 7.5, 10), (10, 7.5, -10), (-10, 7.5, 10), (-10, 7.5, -10)]
    for pos in tower_positions:
        Entity(model='cylinder', position=pos, scale=(2, 15, 2), color=color.white, collider='box')
        # Tower roof
        Entity(model='cone', position=(pos[0], pos[1] + 7.5, pos[2]), scale=(3, 3, 3), color=color.red)
    # Door
    Entity(model='cube', position=(0, 2.5, 10), scale=(4, 5, 1), color=color.brown)
    # Windows
    window_positions = [(5, 5, 10), (-5, 5, 10), (5, 5, -10), (-5, 5, -10)]
    for pos in window_positions:
        Entity(model='cube', position=pos, scale=(2, 2, 0.5), color=color.blue)

# Create level
def create_level():
    build_castle()
    # Tree
    tree = Entity(
        model='cylinder',
        scale=(1, 5, 1),
        position=(15, 2.5, 15),  # Adjusted to avoid tower
        color=color.brown,
        collider='box'
    )
    # Water
    water = Entity(
        model='plane',
        scale=(5, 0.1, 5),
        position=(-10, 0.1, -10),
        color=color.cyan,
        collider='box'
    )
    # Slide
    slide = Entity(
        model='plane',
        position=(20, 5, 20),
        scale=(5, 0.1, 10),
        rotation=(0, 0, -30),
        color=color.yellow,
        collider='box'
    )
    # Star
    star = Entity(
        model='quad',
        color=color.gold,
        position=(22, 6, 22),
        scale=0.5,
        billboard=True,
        collider='box'
    )
    # Animate star
    def spin_star():
        if star:
            star.rotation_y += time.dt * 100
    star.update = spin_star
    return slide, star, water

# Create level
try:
    slide, star, water = create_level()
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

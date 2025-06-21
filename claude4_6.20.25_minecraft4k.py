# minecraft_cavegame_ursina.py
# Requirements: pip install ursina
from ursina import *
import math

# ---------------------------------------------------------------------------
# Window & basic scene
# ---------------------------------------------------------------------------
app = Ursina(title='Cave Game – Ursina', borderless=False)
window.size = (800, 600)
window.color = color.rgb(135, 206, 235)  # sky-blue background

# ---------------------------------------------------------------------------
# Camera & player controller (no textures, no models)
# ---------------------------------------------------------------------------
camera.fov = 90
mouse_sensitivity = Vec2(40, 40)
move_speed = 4
gravity = 9.81
jump_force = 5

player = Entity()
player.y = 5  # spawn height
velocity_y = 0

# Lock mouse to window for FPS controls
window.exit_button.visible = False
mouse.locked = True

def update():
    global velocity_y
    
    # 1. Mouse-look ----------------------------------------------------------
    if mouse.locked:
        camera.rotation_y += mouse.velocity[0] * mouse_sensitivity[0]
        camera.rotation_x -= mouse.velocity[1] * mouse_sensitivity[1]
        camera.rotation_x = max(min(camera.rotation_x, 90), -90)
    
    # 2. WASD movement -------------------------------------------------------
    # Calculate forward and right vectors based on camera yaw only
    yaw_rad = math.radians(camera.rotation_y)
    forward = Vec3(math.sin(yaw_rad), 0, math.cos(yaw_rad))
    right = Vec3(math.cos(yaw_rad), 0, -math.sin(yaw_rad))
    
    # Calculate movement vector
    move = Vec3(0, 0, 0)
    if held_keys['w']: move += forward
    if held_keys['s']: move -= forward
    if held_keys['d']: move += right
    if held_keys['a']: move -= right
    
    # Normalize and apply speed
    if move.length() > 0:
        move = move.normalized() * move_speed * time.dt
    
    # 3. Vertical motion & gravity -------------------------------------------
    # Check if on ground
    origin = player.world_position + Vec3(0, 0.1, 0)
    hit_info = raycast(origin, Vec3(0, -1, 0), distance=1.2, ignore=[player])
    on_ground = hit_info.hit
    
    if on_ground:
        velocity_y = 0
        if held_keys['space']:
            velocity_y = jump_force
    else:
        velocity_y -= gravity * time.dt
    
    # Apply movement
    player.position += move
    player.y += velocity_y * time.dt
    
    # Keep camera at player position
    camera.position = player.position + Vec3(0, 0.8, 0)  # Eye height

# ---------------------------------------------------------------------------
# Voxel logic
# ---------------------------------------------------------------------------
BLOCK_SIZE = 1
voxels = {}  # {(x,y,z): entity}

def add_block(position, colour):
    """Add a voxel block at the given position with the specified color."""
    pos_tuple = (int(position.x), int(position.y), int(position.z))
    
    # Check if block already exists
    if pos_tuple in voxels:
        return
    
    ent = Entity(
        model='cube',
        color=colour,
        texture='white_cube',  # Use built-in white texture for better visibility
        position=Vec3(*pos_tuple),
        scale=BLOCK_SIZE,
        collider='box',
    )
    voxels[pos_tuple] = ent

def remove_block(position):
    """Remove a voxel block at the given position."""
    pos_tuple = (int(position.x), int(position.y), int(position.z))
    if pos_tuple in voxels:
        destroy(voxels[pos_tuple])
        del voxels[pos_tuple]

def input(key):
    # Toggle mouse lock with ESC
    if key == 'escape':
        mouse.locked = not mouse.locked
        if not mouse.locked:
            window.exit_button.visible = True
        else:
            window.exit_button.visible = False
    
    # Left click to destroy blocks
    if key == 'left mouse down' and mouse.hovered_entity and mouse.locked:
        if hasattr(mouse.hovered_entity, 'position'):
            remove_block(mouse.hovered_entity.position)
    
    # Right click to place blocks
    if key == 'right mouse down' and mouse.hovered_entity and mouse.locked:
        if hasattr(mouse.hovered_entity, 'position') and mouse.normal:
            hit_pos = mouse.hovered_entity.position
            place_pos = hit_pos + mouse.normal
            add_block(place_pos, color.rgb(150, 111, 51))  # Brown dirt

# ---------------------------------------------------------------------------
# Create terrain
# ---------------------------------------------------------------------------
GROUND_SIZE = 20
GROUND_HEIGHT = 0

# Create flat ground with grass on top and dirt below
print("Generating terrain...")
for x in range(-GROUND_SIZE, GROUND_SIZE):
    for z in range(-GROUND_SIZE, GROUND_SIZE):
        # Grass layer
        add_block(Vec3(x, GROUND_HEIGHT, z), color.rgb(34, 139, 34))
        # Dirt layers
        for y in range(GROUND_HEIGHT - 3, GROUND_HEIGHT):
            add_block(Vec3(x, y, z), color.rgb(150, 111, 51))

# Add some hills for variety
for i in range(5):
    hill_x = random.randint(-GROUND_SIZE + 5, GROUND_SIZE - 5)
    hill_z = random.randint(-GROUND_SIZE + 5, GROUND_SIZE - 5)
    hill_height = random.randint(2, 5)
    hill_radius = random.randint(3, 6)
    
    for x in range(hill_x - hill_radius, hill_x + hill_radius):
        for z in range(hill_z - hill_radius, hill_z + hill_radius):
            dist = math.sqrt((x - hill_x)**2 + (z - hill_z)**2)
            if dist < hill_radius:
                height = int(hill_height * (1 - dist / hill_radius))
                for y in range(1, height + 1):
                    add_block(Vec3(x, GROUND_HEIGHT + y, z), color.rgb(100, 100, 100))  # Stone

print(f"Generated {len(voxels)} blocks")

# Instructions
instructions = Text(
    'WASD: Move | Mouse: Look | Space: Jump | Left Click: Break | Right Click: Place | ESC: Toggle Mouse Lock',
    position=(-0.9, 0.45),
    scale=0.8,
    background=True
)

# ---------------------------------------------------------------------------
# Run the game
# ---------------------------------------------------------------------------
app.run()

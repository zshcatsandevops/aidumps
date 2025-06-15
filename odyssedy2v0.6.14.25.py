from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

app = Ursina()

# Set target frame rate
app.target_fps = 60

# Create Sky
sky = Sky(texture='sky_default')

# Create player
player = FirstPersonController()
player.cursor.visible = False
player.gravity = 1
player.jumping = False
player.jump_height = 2

# Ground
ground = Entity(
    model='plane',
    scale=(100, 1, 100),
    texture='grass',
    collider='mesh'
)

# Simple test level
def create_level():
    # Platform 1
    Entity(
        model='cube',
        scale=(10, 1, 10),
        position=(0, 1, 0),
        texture='grass',
        collider='box'
    )
    
    # Platform 2
    Entity(
        model='cube',
        scale=(10, 1, 10),
        position=(15, 1, 0),
        texture='grass',
        collider='box'
    )
    
    # Platform 3 (higher)
    Entity(
        model='cube',
        scale=(10, 1, 10),
        position=(30, 5, 0),
        texture='grass',
        collider='box'
    )
    
    # Goal
    goal = Entity(
        model='cube',
        scale=(2, 10, 2),
        position=(30, 10, 0),
        texture='brick',
        collider='box'
    )
    return goal

goal = create_level()

def update():
    # Basic movement controls
    player.speed = 5
    
    # Jump
    if held_keys['space'] and not player.jumping:
        player.jumping = True
        player.animate_position(
            (player.x, player.y + player.jump_height, player.z),
            duration=0.5,
            curve=curve.out_quart
        )
        invoke(setattr, player, 'jumping', False, delay=1)

app.run()

from ursina import *

app = Ursina()
window.size = (600, 400)
window.borderless = False
window.title = "Super Mario 64 Inspired Game"

# Player setup
player = Entity(model='cube', color=color.red, scale=(1,1,1), position=(0,1,0))

# Level setup
ground = Entity(model='cube', scale=(10,1,10), position=(0,0,0), color=color.green, collider='box')
platform1 = Entity(model='cube', scale=(2,1,2), position=(3,1,3), color=color.blue, collider='box')
platform2 = Entity(model='cube', scale=(2,1,2), position=(-3,2,-3), color=color.blue, collider='box')

# Goal setup
goal = Entity(model='cube', scale=(1,1,1), position=(5,1,5), color=color.yellow)

# Lighting
light = DirectionalLight()
light.direction = (1, -1, -1)  # Corrected: use direction property instead of set_direction

# Camera setup
camera.position = (0,10,-10)
camera.rotation_x = 45

def update():
    # Player movement
    player.x += held_keys['d'] * time.dt * 5  # Move right
    player.x -= held_keys['a'] * time.dt * 5  # Move left
    player.z += held_keys['w'] * time.dt * 5  # Move forward
    player.z -= held_keys['s'] * time.dt * 5  # Move backward

    # Jumping
    if held_keys['space'] and player.y == 0:
        player.y += 1

    # Gravity
    if player.y > 0:
        player.y -= time.dt * 5

    # Collision detection with platforms
    hit_info = raycast(player.position, direction=(0,-1,0), distance=1)
    if hit_info.hit:
        player.y = hit_info.entity.position.y + hit_info.entity.scale_y / 2 + player.scale_y / 2

    # Check for goal
    if distance(player, goal) < 1:
        print("You win!")
        # Add additional win logic here if desired

app.run()

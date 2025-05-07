from ursina import *
from ursina.shaders import basic_lighting_shader

app = Ursina()

# Paper Mario style settings
window.color = color.rgb(135, 206, 235)  # Sky blue
window.borderless = False

# Isometric camera
camera.position = (10, 15, -20)
camera.rotation = (30, -45, 0)

# Paper-style player
player = Entity(
    model='cube',
    color=color.red,
    scale=(1, 2, 0.1),  # Flat paper look
    position=(0, 0.5, 0),
    shader=basic_lighting_shader
)

# Paper-style ground
ground = Entity(
    model='plane',
    texture='white_cube',
    texture_scale=(10, 10),
    color=color.green,
    scale=(20, 1, 20),
    collider='box'
)

# Paper-style obstacles
obstacles = []
for i in range(10):
    obstacle = Entity(
        model='cube',
        color=color.blue,
        scale=(1, 1, 0.1),  # Flat paper look
        position=(i * 2, 0.5, 0),
        collider='box'
    )
    obstacles.append(obstacle)

def update():
    # 3D movement with isometric controls
    player.x += (held_keys['d'] - held_keys['a']) * 5 * time.dt
    player.z += (held_keys['w'] - held_keys['s']) * 5 * time.dt
    
    # Paper-style jump
    if held_keys['space'] and player.y <= 0.5:
        player.y += 0.1
    elif player.y > 0.5:
        player.y -= 0.1 * time.dt
    
    # Paper-style collision
    for obstacle in obstacles[:]:
        if player.intersects(obstacle).hit:
            player.color = color.yellow  # Hit feedback
            destroy(obstacle)
            obstacles.remove(obstacle)
            break
        else:
            player.color = color.red

app.run()

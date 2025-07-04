from ursina import *

app = Ursina()
window.size = (600, 400)
window.title = 'Mario 64 Peach\'s Castle Demo'

# Create the ground
ground = Entity(model='plane', color=color.green, scale=(100,1,100))

# Create the castle as a cube
castle = Entity(model='cube', color=color.gray, scale=(10,10,10), position=(0,5,0))

# Create Mario as a sphere
mario = Entity(model='sphere', color=color.red, scale=1, position=(0,0.5,10))

# Update function to handle movement and camera
def update():
    new_x = mario.x
    new_z = mario.z
    
    # Movement controls
    if held_keys['left arrow']:
        new_x -= 0.1
    if held_keys['right arrow']:
        new_x += 0.1
    if held_keys['up arrow']:
        new_z -= 0.1
    if held_keys['down arrow']:
        new_z += 0.1
    
    # Simple collision detection with the castle
    if not (-5 < new_x < 5 and -5 < new_z < 5):
        mario.x = new_x
        mario.z = new_z
    
    # Third-person camera follows Mario
    camera.position = (mario.x, mario.y + 5, mario.z - 10)
    camera.look_at(mario)

app.run()

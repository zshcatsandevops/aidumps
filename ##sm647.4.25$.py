from ursina import *

app = Ursina()
window.size = (600, 400)
window.title = 'Mario 64 Peach\'s Castle Demo'

# Create the ground
ground = Entity(model='plane', color=color.green, scale=(100,1,100))

# Function to build the castle
def build_castle():
    castle_parent = Entity()
    # Main building
    main_building = Entity(parent=castle_parent, model='cube', color=color.white, scale=(20,10,20), position=(0,5,0))
    # Towers
    tower1 = Entity(parent=castle_parent, model='cube', color=color.light_gray, scale=(5,15,5), position=(10,7.5,10))
    tower2 = Entity(parent=castle_parent, model='cube', color=color.light_gray, scale=(5,15,5), position=(10,7.5,-10))
    tower3 = Entity(parent=castle_parent, model='cube', color=color.light_gray, scale=(5,15,5), position=(-10,7.5,10))
    tower4 = Entity(parent=castle_parent, model='cube', color=color.light_gray, scale=(5,15,5), position=(-10,7.5,-10))
    # Door
    door = Entity(parent=castle_parent, model='cube', color=color.brown, scale=(2,5,0.5), position=(0,2.5,10))
    return castle_parent

castle = build_castle()

# Create the path
path = Entity(model='plane', color=color.gray, scale=(5,1,10), position=(0,0.01,15))

# Function to build trees
def build_tree(position):
    tree = Entity()
    trunk = Entity(parent=tree, model='cube', color=color.brown, scale=(1,3,1), position=position)
    leaves = Entity(parent=tree, model='sphere', color=color.green, scale=3, position=(position[0], position[1]+2.5, position[2]))
    return tree

# Add trees around the castle
tree1 = build_tree((15,0,15))
tree2 = build_tree((15,0,-15))
tree3 = build_tree((-15,0,15))
tree4 = build_tree((-15,0,-15))

# Create Mario as a sphere
mario = Entity(model='sphere', color=color.red, scale=1, position=(0,0.5,20))

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
    
    # Simple collision detection with the castle area
    if not (-10 < new_x < 10 and -10 < new_z < 10):
        mario.x = new_x
        mario.z = new_z
    
    # Third-person camera follows Mario
    camera.position = (mario.x, mario.y + 5, mario.z - 10)
    camera.look_at(mario)

app.run()

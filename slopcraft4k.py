from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.shaders import lit_with_shadows_shader
import random

app = Ursina()
window.borderless = False
window.exit_button.visible = False
window.fps_counter.enabled = True

# Block types with textures
blocks = [
    ('stone', 'stone'),    # Stone
    ('dirt', 'dirt'),      # Dirt
    ('grass', 'grass'),    # Grass
    ('sand', 'brick'),     # Sand (using brick texture)
    ('gold', 'gold'),      # Gold
    ('iron', 'gray')       # Iron (using gray texture)
]

# Inventory
inventory = [0] * len(blocks)
selected_slot = 0
hotbar = Entity(parent=camera.ui, model='quad', texture='white_cube', scale=(.8, .1), position=(0, -.45))

# Block class
class Block(Button):
    def __init__(self, position=(0,0,0), block_type=0):
        super().__init__(
            parent=scene,
            position=position,
            model='cube',
            texture=blocks[block_type][1],
            color=color.white,
            highlight_color=color.lime,
            shader=lit_with_shadows_shader
        )
        self.block_type = block_type
        self.collider = 'box'

# Terrain generation
def generate_world():
    for z in range(-25, 25):
        for x in range(-25, 25):
            if random.random() > 0.6:
                height = random.randint(1, 3)
                for y in range(0, height):
                    Block(position=(x, y, z), block_type=random.choice([0,1,3]))
            else:
                Block(position=(x, 0, z), block_type=0)

# Player
player = FirstPersonController()
player.position = (0, 5, 0)

# UI
def update_inventory():
    hotbar.texture = load_texture('white_cube')
    for i in range(len(blocks)):
        button = Button(
            parent=hotbar,
            model='cube',
            texture=blocks[i][1],
            color=color.white,
            scale=(.09, .8),
            position=(-.3 + i * .1, 0),
            highlight_color=color.azure
        )
        button.tooltip = Tooltip(f'{blocks[i][0].capitalize()}: {inventory[i]}')
        button.on_click = Func(set_selected_slot, i)

def set_selected_slot(slot):
    global selected_slot
    selected_slot = slot

# Game logic
def input(key):
    global selected_slot
    
    if key == 'left mouse down':
        hit_info = raycast(camera.world_position, camera.forward, distance=5)
        if hit_info.hit and hasattr(hit_info.entity, 'block_type'):
            destroy(hit_info.entity)
            inventory[hit_info.entity.block_type] += 1
            update_inventory()
    
    if key == 'right mouse down':
        hit_info = raycast(camera.world_position, camera.forward, distance=5)
        if hit_info.hit and inventory[selected_slot] > 0:
            new_pos = hit_info.world_point + hit_info.normal
            Block(position=new_pos, block_type=selected_slot)
            inventory[selected_slot] -= 1
            update_inventory()
    
    if key in '123456789':
        selected_slot = int(key) - 1
    
    if key == 'e':
        camera_parent = player
        camera_parent.position = (0, 1.5, 0)

update_inventory()
generate_world()

# Lighting
AmbientLight(color=color.rgba(100, 100, 100, 1))
DirectionalLight(color=color.rgba(255, 255, 255, 0.5), direction=(1, 1, 1))

app.run()

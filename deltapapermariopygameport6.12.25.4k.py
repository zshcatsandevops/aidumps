# paper_mario64_ursina_demo.py
from ursina import *

app = Ursina(title='Paper Mario 64 – Ursina Tech Demo')

# ---------- CAMERA (diorama view) ----------
camera.orthographic = True               # flat projection 欄
camera.fov          = 16                 # visible units vertically :contentReference[oaicite:4]{index=4}
camera.position     = (0, 8, -20)
camera.rotation_x   = 25                 # gentle tilt

# ---------- WORLD ----------
ground = Entity(model='quad',
                scale=(64, 1, 1),
                rotation_x=-90,
                y=-.1,
                color=color.green,
                collider='box')

def paper_sprite(texture_name,
                 pos=(0, 0, 0),
                 scale=4):
    """Return a quad that always faces the camera."""
    e = Entity(model='quad',
               texture=texture_name,
               position=pos,
               scale=scale,
               double_sided=True,
               collider='box')

    def face_camera():
        e.look_at(camera, 'forward')     # look toward lens
        e.rotation_y += 180              # keep front forward

    e.update = face_camera
    return e

# ---------- PLAYER ----------
player          = paper_sprite('paper_mario_placeholder', pos=(0, 1, 0), scale=3)
player.grounded = True
MOVE_SPEED      = 4
GRAVITY         = 9

# ---------- UPDATE LOOP ----------
def update():
    player.x += (held_keys['d'] - held_keys['a']) * MOVE_SPEED * time.dt
    if held_keys['space'] and player.grounded:
        player.animate_y(player.y + 4, .3, curve.out_cubic)
        player.grounded = False

    if not player.grounded:
        player.y -= GRAVITY * time.dt
        if player.y <= 1:
            player.y       = 1
            player.grounded = True

    # soft follow
    camera.x = lerp(camera.x, player.x, 4 * time.dt)

# ---------- BATTLE MODE ----------
battle_mode = False
turn_text   = Text('', position=(-.7, .45), scale=2)

def input(key):
    global battle_mode
    if key == 'b':
        battle_mode = not battle_mode
        if battle_mode:
            enter_battle()
        else:
            exit_battle()

def enter_battle():
    camera.animate_position((player.x, 3, -10), .5)
    camera.animate_rotation((0, 0, 0), .5)
    camera.orthographic = False
    turn_text.text      = "Mario's Turn – Press Z!"

def exit_battle():
    camera.animate_position((player.x, 8, -20), .5)
    camera.animate_rotation((25, 0, 0), .5)
    invoke(setattr, camera, 'orthographic', True, delay=.5)
    turn_text.text = ''

def update_battle():
    if battle_mode and held_keys['z']:
        turn_text.text = "Nice!"
        invoke(exit_battle, delay=.8)

# Inject extra updater so both loops run.
Entity(update=update_battle, eternal=True)

app.run()

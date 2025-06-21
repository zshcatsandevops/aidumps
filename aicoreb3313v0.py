#!/usr/bin/env python3
# 1.py – a 600x400 Ursina micro‑platformer (no external PNGs needed)

from ursina import *
from random import uniform

# --- engine / window -----------------------------------------------------------------
window.title = 'B3313 Mini Quest'
window.size  = (600, 400)          # 600 × 400 as requested
window.borderless = False
window.exit_button.visible = True  # toggle off if you want a clean frame

app = Ursina()

# --- world ---------------------------------------------------------------------------
ground = Entity(model='plane', scale=(40, 1, 40),
                collider='box', color=color.green)

# scatter some simple columns / obstacles
for x in range(-18, 19, 6):
    for z in range(-18, 19, 6):
        if (x + z) % 12 == 0:
            Entity(model='cube', y=1, x=x, z=z,
                   scale_y=2, collider='box',
                   color=color.hsv(uniform(0, 1), 1, .9))

# --- player --------------------------------------------------------------------------
player = Entity(model='cube', color=color.orange,
                scale_y=1.8, y=2, collider='box')
player.speed       = 4
player.jump_height = 3
player.gravity     = 6
player.grounded    = False

camera.parent     = player
camera.position   = (0, 1.5, -6)
camera.rotation_x = 10

# --- collectibles --------------------------------------------------------------------
stars = []
for _ in range(10):
    stars.append(Entity(model='sphere', scale=.4,
                        color=color.yellow,
                        position=(uniform(-18, 18), 1, uniform(-18, 18)),
                        collider='box'))

score_text = Text(text='Stars: 0/10',
                  origin=(0, -.45), scale=2,
                  background=True)

# --- gameplay loop -------------------------------------------------------------------
def update():
    # horizontal movement
    player.x += (held_keys['d'] - held_keys['a']) * time.dt * player.speed
    player.z += (held_keys['w'] - held_keys['s']) * time.dt * player.speed

    # gravity & ground collision
    if not player.grounded:
        player.y -= player.gravity * time.dt
    if player.intersects(ground).hit:
        player.y = ground.world_y + .9   # half the scaled height
        player.grounded = True
    else:
        player.grounded = False

    # jump
    if held_keys['space'] and player.grounded:
        player.y += player.jump_height
        player.grounded = False

    # collectible check
    global stars
    for star in stars[:]:
        if player.intersects(star).hit:
            destroy(star)
            stars.remove(star)
            score = 10 - len(stars)
            score_text.text = f'Stars: {score}/10'
            if not stars:   # all collected?
                invoke(victory_banner, delay=.1)

def victory_banner():
    Text(text='ALL STARS COLLECTED!',
         origin=(0, 0), scale=3, color=color.azure)
    application.pause()

# --- run! ----------------------------------------------------------------------------
app.run()

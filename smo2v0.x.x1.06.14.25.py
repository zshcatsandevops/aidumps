"""
Super Mario Odyssey 2 (minimal, IP‑clean fan prototype)
Author: Cat‑sama & ChatGPT‑o3    Last update: 15 Jun 2025
Tested with Ursina v5.1.0 / Python 3.12
------------------------------------------------------
Controls
 • WASD / mouse      – move / look
 • Space             – jump
 • C                 – swap Mario ↔ Luigi
 • F                 – throw Cappy (capture Goomba)
 • E (near portal)   – enter kingdom
 • R                 – return to N64 Express
 • Q                 – quit
"""

from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random, logging

# ────────────────────────── Window & engine ──────────────────────────
logging.getLogger('ursina').setLevel(logging.WARNING)       # silence info spam :contentReference[oaicite:0]{index=0}
app = Ursina(borderless=False, development_mode=False)      # hide debug colliders :contentReference[oaicite:1]{index=1}
window.title      = 'Super Mario Odyssey 2 – prototype'
window.size       = (960, 600)
window.position   = (80, 60)
window.fps_counter.enabled = True
app.target_fps    = 60                                       # hard‑limit FPS :contentReference[oaicite:2]{index=2}
mouse.locked      = True

# ────────────────────────── Global state ──────────────────────────
current_kingdom   = "n64_express"
current_player    = "mario"
coins, stars      = 0, 0

# Tunables
PLAYER_SPEED      = 6
PLAYER_JUMP       = 1.8
JUMP_DURATION     = .4
CAMERA_FOV        = 90
COLLECT_RADIUS    = 1.8

# ────────────────────────── Helper factories ──────────────────────────
def make_coin(pos):
    return Entity(model='sphere', scale=.5, color=color.gold,    position=pos, collider='sphere')  # :contentReference[oaicite:3]{index=3}

def make_star(pos):
    return Entity(model='cube',  scale=.7, color=color.yellow,  position=pos, collider='box')

def make_goomba(pos):
    b = Entity(model='cube',  scale=.9, color=color.brown, position=pos, collider='box')
    b.name = 'goomba'
    return b

# ────────────────────────── Players & capture ──────────────────────────
def build_character(col):
    body  = Entity(model='cube',   scale=(.8,1.6,.8), color=col)
    head  = Entity(model='sphere', scale= .7, parent=body, y=.9, color=col)
    hat   = Entity(model='cube',   scale=(1,.2,1),  parent=body, y=1.1, color=col)
    eyes  = Entity(model='quad',   scale=(.3,.2),    parent=body, y=.9, z=.35, color=color.white)
    return body

mario = build_character(color.red)
luigi = build_character(color.green)
captured = Entity(model='cube',   scale=1,   color=color.brown, enabled=False)  # generic shell for captures

# ────────────────────────── First‑person controller ───────────────────
player = FirstPersonController(speed=PLAYER_SPEED,                # :contentReference[oaicite:4]{index=4}
                               jump_height=PLAYER_JUMP,
                               jump_duration=JUMP_DURATION,
                               gravity=1)
player.cursor.visible  = False
player.visible         = False
camera.fov             = CAMERA_FOV

# keep model glued to controller
def sync_avatar():
    host = captured if captured.enabled else (mario if current_player=="mario" else luigi)
    host.position = player.position + (0, -.9, 0)
    host.rotation = (0, -player.rotation_y, 0)

# ────────────────────────── UI / HUD ──────────────────────────
coin_txt   = Text(text='Coins: 0',  position=window.top_left + (0.06,-0.05), scale=1.5)  # :contentReference[oaicite:5]{index=5}
star_txt   = Text(text='Stars: 0', position=window.top_left + (0.06,-0.10), scale=1.5)
kingdom_lbl= Text(text='N64 Express', position=window.top, origin=(0,0), y=-.06, scale=2)
char_lbl   = Text(text='Character: Mario', position=window.bottom_left + (.06,.05), scale=1.5)

# ────────────────────────── Kingdom construction tools ────────────────
def flat_kingdom(size, texture, tint, height=0, spawn_coins=True, water=False):
    """Returns [terrain, *entities]."""
    terr = Entity(model='plane', texture=texture, color=tint,
                  scale=size, y=height, collider='mesh')         # :contentReference[oaicite:6]{index=6}
    entities = [terr]

    if spawn_coins:
        for _ in range(25):
            x = random.uniform(-size*4, size*4)
            z = random.uniform(-size*4, size*4)
            entities.append(make_coin((x, terr.y+1, z)))

    # guarantee at least one star per kingdom
    s_pos = (random.uniform(-size*3, size*3), terr.y+1, random.uniform(-size*3, size*3))
    entities.append(make_star(s_pos))

    # add a couple Goombas
    for _ in range(6):
        entities.append(make_goomba((random.uniform(-size*3, size*3), terr.y+1, random.uniform(-size*3, size*3))))
    return entities

# Each kingdom – minimalist layout
kingdoms = {
    "n64_express":  [],   # portals live here
    "waterfront":   flat_kingdom(100, 'white_cube', color.blue,   height=0, spawn_coins=True),
    "flower":       flat_kingdom(80,  'grass',      color.lime,   height=0),
    "shimmerock":   flat_kingdom(90,  'white_cube', color.light_gray, height=.5),
    "bowser_jr":    flat_kingdom(90,  'white_cube', color.orange, height=0),
    "skyloft":      flat_kingdom(60,  'grass',      color.cyan,   height=40),
    "darker_side":  flat_kingdom(100, 'white_cube', color.black66, height=0),
    "shine":        flat_kingdom(120, 'white_cube', color.yellow, height=0),
    "toad_town":    flat_kingdom(120, 'grass',      color.azure,  height=0),
    "bowser":       flat_kingdom(100, 'white_cube', color.dark_gray, height=0),
}

# build the express train & portals
def build_n64_express():
    entities = []
    # locomotive
    entities.append(Entity(model='cube', texture='brick', scale=(25,5,6), y=2.5, collider='box'))
    # cars
    for off in (-10,-17,-24):
        entities.append(Entity(model='cube', texture='brick', scale=(6,4,5), position=(off,2,0), collider='box'))
    # wheels
    for x in (10,5,-5,-10,-17,-24):
        for z in (3,-3):
            entities.append(Entity(model='cube', scale=(1,.3,1), color=color.gray, position=(x,.5,z), rotation_x=90))
    # portals – label becomes the kingdom key
    names = ["Waterfront","Flower","Shimmerock","Bowser Jr.","Skyloft",
             "Darker Side","Shine","Toad Town","Bowser"]
    for i,n in enumerate(names):
        ent = Entity(model='circle', color=color.azure, scale=2.5,
                     position=(-5-(i*5),3,0), rotation_x=90, collider='box')
        ent.name = f"{n} Kingdom"
        entities.append(ent)
    return entities
kingdoms["n64_express"] = build_n64_express()

# ────────────────────────── Kingdom switching ──────────────────────────
def switch_kingdom(name):
    global current_kingdom
    # hide old
    for e in kingdoms[current_kingdom]:
        e.enabled = False                                         # :contentReference[oaicite:7]{index=7}
    current_kingdom = name
    # show new
    for e in kingdoms[name]:
        e.enabled = True
    player.position = (0, 5 if name!="n64_express" else 3, 0)
    kingdom_lbl.text = name.replace("_"," ").title()

# disable all except express at start
for k, lst in kingdoms.items():
    if k != "n64_express":
        for e in lst: e.enabled = False

# ────────────────────────── Cap throw / capture ────────────────────────
def throw_cap():
    hit = raycast(player.position, player.forward, distance=6, ignore=(player,))  # :contentReference[oaicite:8]{index=8}
    if hit.hit and getattr(hit.entity, 'name', '') == 'goomba':
        capture_goomba(hit.entity)

def capture_goomba(g):
    g.enabled = False
    captured.enabled = True
    mario.enabled = luigi.enabled = False
    invoke(uncapture, delay=5)                                      # timed release :contentReference[oaicite:9]{index=9}

def uncapture():
    captured.enabled = False
    (mario if current_player=="mario" else luigi).enabled = True

# ────────────────────────── Input ──────────────────────────
def input(key):
    global current_player, coins, stars

    if key == 'c':
        current_player = 'luigi' if current_player=='mario' else 'mario'
        mario.enabled, luigi.enabled = current_player=='mario', current_player=='luigi'
        char_lbl.text = f"Character: {current_player.title()}"

    elif key == 'f':  throw_cap()

    elif key == 'e' and current_kingdom=='n64_express':
        for p in kingdoms['n64_express']:
            if distance(player.position, p.position) < 3 and hasattr(p,'name'):
                target = p.name.replace(" Kingdom","").replace(" ","_").replace("'","").lower()
                switch_kingdom(target)

    elif key == 'r' and current_kingdom!='n64_express':
        switch_kingdom('n64_express')

    elif key == 'q': application.quit()

# ────────────────────────── Main update loop ──────────────────────────
def update():
    global coins, stars
    sync_avatar()

    # pick‑ups
    for e in kingdoms[current_kingdom]:
        if not e.enabled: continue
        if distance(player.position, e.position) > COLLECT_RADIUS: continue

        if e.color == color.gold:               # coin
            coins += 1
            coin_txt.text = f"Coins: {coins}"
            e.enabled = False
        elif e.color == color.yellow:           # star
            stars += 1
            star_txt.text = f"Stars: {stars}"
            e.enabled = False
            switch_kingdom('n64_express')

# ────────────────────────── Scene init ──────────────────────────
player.position   = (0,3,0)
(camera.ui).enabled = True
sky  = Sky(color=color.cyan)                    # change tint here :contentReference[oaicite:10]{index=10}
mario.enabled     = True
luigi.enabled     = False

app.run()

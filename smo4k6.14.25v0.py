from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random, logging

# ────────────────────────── Window & Engine ──────────────────────────
logging.getLogger('ursina').setLevel(logging.WARNING)
app = Ursina(borderless=False, development_mode=False)
window.title = 'Super Mario Odyssey 2 – Prototype'
window.size = (960, 600)
window.position = (80, 60)
window.fps_counter.enabled = True
app.target_fps = 60
mouse.locked = True

# ────────────────────────── Global State ──────────────────────────
current_kingdom = "n64_express"
current_player = "mario"
coins, stars, moons, health = 0, 0, 0, 3
power_up = None  # None, 'fire', 'star'

# Tunables
PLAYER_SPEED = 6
PLAYER_JUMP = 1.8
JUMP_DURATION = 0.4
CAMERA_FOV = 90
COLLECT_RADIUS = 1.8
FIREBALL_SPEED = 10

# ────────────────────────── Helper Factories ──────────────────────────
def make_coin(pos):
    return Entity(model='sphere', scale=0.5, color=color.gold, position=pos, collider='sphere')

def make_star(pos):
    return Entity(model='cube', scale=0.7, color=color.yellow, position=pos, collider='box')

def make_moon(pos):
    return Entity(model='sphere', scale=0.6, color=color.silver, position=pos, collider='sphere')

def make_goomba(pos):
    b = Entity(model='cube', scale=0.9, color=color.brown, position=pos, collider='box')
    b.name = 'goomba'
    return b

def make_chain_chomp(pos):
    b = Entity(model='sphere', scale=1.2, color=color.gray, position=pos, collider='sphere')
    b.name = 'chain_chomp'
    return b

def make_cheep_cheep(pos):
    b = Entity(model='cube', scale=(0.8, 0.4, 0.8), color=color.red, position=pos, collider='box')
    b.name = 'cheep_cheep'
    return b

# ────────────────────────── Players & Capture ──────────────────────────
def build_character(col):
    body = Entity(model='cube', scale=(0.8, 1.6, 0.8), color=col)
    head = Entity(model='sphere', scale=0.7, parent=body, y=0.9, color=col)
    hat = Entity(model='cube', scale=(1, 0.2, 1), parent=body, y=1.1, color=col)
    eyes = Entity(model='quad', scale=(0.3, 0.2), parent=body, y=0.9, z=0.35, color=color.white)
    return body

mario = build_character(color.red)
luigi = build_character(color.green)
captured = Entity(model='cube', scale=1, color=color.brown, enabled=False)

# ────────────────────────── First-Person Controller ───────────────────
player = FirstPersonController(speed=PLAYER_SPEED, jump_height=PLAYER_JUMP, jump_duration=JUMP_DURATION, gravity=1)
player.cursor.visible = False
player.visible = False
camera.fov = CAMERA_FOV

def sync_avatar():
    host = captured if captured.enabled else (mario if current_player == "mario" else luigi)
    host.position = player.position + (0, -0.9, 0)
    host.rotation = (0, -player.rotation_y, 0)

# ────────────────────────── UI / HUD ──────────────────────────
coin_txt = Text(text='Coins: 0', position=window.top_left + (0.06, -0.05), scale=1.5)
star_txt = Text(text='Stars: 0', position=window.top_left + (0.06, -0.10), scale=1.5)
moon_txt = Text(text='Moons: 0', position=window.top_left + (0.06, -0.15), scale=1.5)
health_txt = Text(text='Health: 3', position=window.top_left + (0.06, -0.20), scale=1.5)
kingdom_lbl = Text(text='N64 Express', position=window.top, origin=(0, 0), y=-0.06, scale=2)
char_lbl = Text(text='Character: Mario', position=window.bottom_left + (0.06, 0.05), scale=1.5)
power_txt = Text(text='Power: None', position=window.bottom_left + (0.06, 0.10), scale=1.5)

# ────────────────────────── Kingdom Construction Tools ────────────────
def flat_kingdom(size, texture, tint, height=0, spawn_coins=True, water=False):
    terr = Entity(model='plane', texture=texture, color=tint, scale=size, y=height, collider='mesh')
    entities = [terr]
    if spawn_coins:
        for _ in range(20):
            x = random.uniform(-size * 4, size * 4)
            z = random.uniform(-size * 4, size * 4)
            entities.append(make_coin((x, terr.y + 1, z)))
    s_pos = (random.uniform(-size * 3, size * 3), terr.y + 1, random.uniform(-size * 3, size * 3))
    entities.append(make_star(s_pos))
    m_pos = (random.uniform(-size * 3, size * 3), terr.y + 1, random.uniform(-size * 3, size * 3))
    entities.append(make_moon(m_pos))
    for _ in range(5):
        entities.append(make_goomba((random.uniform(-size * 3, size * 3), terr.y + 1, random.uniform(-size * 3, size * 3))))
    for _ in range(3):
        entities.append(make_chain_chomp((random.uniform(-size * 3, size * 3), terr.y + 1, random.uniform(-size * 3, size * 3))))
    if water:
        for _ in range(4):
            entities.append(make_cheep_cheep((random.uniform(-size * 3, size * 3), terr.y + 0.5, random.uniform(-size * 3, size * 3))))
    return entities

def cloud_kingdom():
    entities = []
    base = Entity(model='plane', texture='white_cube', color=color.white, scale=50, y=50, collider='mesh')
    entities.append(base)
    for _ in range(10):
        x = random.uniform(-40, 40)
        z = random.uniform(-40, 40)
        y = random.uniform(51, 60)
        plat = Entity(model='cube', texture='white_cube', color=color.white, scale=(5, 0.5, 5), position=(x, y, z), collider='box')
        entities.append(plat)
        if random.random() < 0.5:
            entities.append(make_coin((x, y + 1, z)))
    entities.append(make_moon((0, 55, 0)))
    return entities

kingdoms = {
    "n64_express": [],
    "waterfront": flat_kingdom(100, 'white_cube', color.blue, height=0, spawn_coins=True, water=True),
    "flower": flat_kingdom(80, 'grass', color.lime, height=0),
    "shimmerock": flat_kingdom(90, 'white_cube', color.light_gray, height=0.5),
    "bowser_jr": flat_kingdom(90, 'white_cube', color.orange, height=0),
    "skyloft": flat_kingdom(60, 'grass', color.cyan, height=40),
    "darker_side": flat_kingdom(100, 'white_cube', color.black66, height=0),
    "shine": flat_kingdom(120, 'white_cube', color.yellow, height=0),
    "toad_town": flat_kingdom(120, 'grass', color.azure, height=0),
    "bowser": flat_kingdom(100, 'white_cube', color.dark_gray, height=0),
    "crystal": flat_kingdom(80, 'white_cube', color.white, height=0),
    "food": flat_kingdom(90, 'white_cube', color.pink, height=0),
    "cloud": cloud_kingdom(),
}

def build_n64_express():
    entities = []
    entities.append(Entity(model='cube', texture='brick', scale=(25, 5, 6), y=2.5, collider='box'))
    for off in (-10, -17, -24):
        entities.append(Entity(model='cube', texture='brick', scale=(6, 4, 5), position=(off, 2, 0), collider='box'))
    for x in (10, 5, -5, -10, -17, -24):
        for z in (3, -3):
            entities.append(Entity(model='cube', scale=(1, 0.3, 1), color=color.gray, position=(x, 0.5, z), rotation_x=90))
    names = ["Waterfront", "Flower", "Shimmerock", "Bowser Jr.", "Skyloft", "Darker Side", "Shine", "Toad Town", "Bowser", "Crystal", "Food", "Cloud"]
    for i, n in enumerate(names):
        ent = Entity(model='circle', color=color.azure, scale=2.5, position=(-5 - (i * 5), 3, 0), rotation_x=90, collider='box')
        ent.name = f"{n} Kingdom"
        entities.append(ent)
    return entities

kingdoms["n64_express"] = build_n64_express()

# ────────────────────────── Kingdom Switching ──────────────────────────
def switch_kingdom(name):
    global current_kingdom
    for e in kingdoms[current_kingdom]:
        e.enabled = False
    current_kingdom = name
    for e in kingdoms[name]:
        e.enabled = True
    player.position = (0, 5 if name != "n64_express" else 3, 0)
    kingdom_lbl.text = name.replace("_", " ").title()

for k, lst in kingdoms.items():
    if k != "n64_express":
        for e in lst:
            e.enabled = False

# ────────────────────────── Cap Throw / Capture ────────────────────────
def throw_cap():
    hit = raycast(player.position, player.forward, distance=6, ignore=(player,))
    if hit.hit and getattr(hit.entity, 'name', '') in ['goomba', 'chain_chomp', 'cheep_cheep']:
        capture_enemy(hit.entity)

def capture_enemy(enemy):
    enemy.enabled = False
    captured.enabled = True
    captured.name = enemy.name
    mario.enabled = luigi.enabled = False
    invoke(uncapture, delay=5)

def uncapture():
    captured.enabled = False
    captured.name = ''
    (mario if current_player == "mario" else luigi).enabled = True

# ────────────────────────── Power-Ups ──────────────────────────
def apply_power_up(power):
    global power_up
    power_up = power
    power_txt.text = f"Power: {power.title() if power else 'None'}"
    if power == 'star':
        invoke(clear_power_up, delay=10)

def clear_power_up():
    global power_up
    power_up = None
    power_txt.text = 'Power: None'

def shoot_fireball():
    if power_up == 'fire':
        fb = Entity(model='sphere', scale=0.3, color=color.orange, position=player.position + player.forward * 1, collider='sphere')
        fb.name = 'fireball'
        fb.velocity = player.forward * FIREBALL_SPEED
        invoke(destroy, fb, delay=3)

# ────────────────────────── Input ──────────────────────────
def input(key):
    global current_player, coins, stars, moons, health
    if key == 'c':
        current_player = 'luigi' if current_player == 'mario' else 'mario'
        mario.enabled, luigi.enabled = current_player == 'mario', current_player == 'luigi'
        char_lbl.text = f"Character: {current_player.title()}"
    elif key == 'f':
        throw_cap()
    elif key == 'g' and power_up == 'fire':
        shoot_fireball()
    elif key == 'e' and current_kingdom == 'n64_express':
        for p in kingdoms['n64_express']:
            if distance(player.position, p.position) < 3 and hasattr(p, 'name'):
                target = p.name.replace(" Kingdom", "").replace(" ", "_").replace(".", "").lower()
                switch_kingdom(target)
    elif key == 'r' and current_kingdom != 'n64_express':
        switch_kingdom('n64_express')
    elif key == 'q':
        application.quit()

# ────────────────────────── Main Update Loop ──────────────────────────
def update():
    global coins, stars, moons, health
    sync_avatar()
    for e in kingdoms[current_kingdom]:
        if not e.enabled:
            continue
        if distance(player.position, e.position) > COLLECT_RADIUS:
            continue
        if e.color == color.gold:
            coins += 1
            coin_txt.text = f"Coins: {coins}"
            e.enabled = False
        elif e.color == color.yellow:
            stars += 1
            star_txt.text = f"Stars: {stars}"
            e.enabled = False
            switch_kingdom('n64_express')
        elif e.color == color.silver:
            moons += 1
            moon_txt.text = f"Moons: {moons}"
            e.enabled = False
        elif e.name in ['goomba', 'chain_chomp', 'cheep_cheep'] and power_up != 'star':
            health -= 1
            health_txt.text = f"Health: {health}"
            e.enabled = False
            if health <= 0:
                switch_kingdom('n64_express')
                health = 3
                health_txt.text = f"Health: {health}"
    if captured.enabled and captured.name == 'chain_chomp':
        player.position += player.forward * 0.2
    for e in kingdoms[current_kingdom]:
        if not e.enabled or e.name != 'fireball':
            continue
        for enemy in kingdoms[current_kingdom]:
            if not enemy.enabled or enemy.name not in ['goomba', 'chain_chomp', 'cheep_cheep']:
                continue
            if distance(e.position, enemy.position) < 1:
                destroy(e)
                enemy.enabled = False

# ────────────────────────── Scene Init ──────────────────────────
player.position = (0, 3, 0)
(camera.ui).enabled = True
sky = Sky(color=color.cyan)
mario.enabled = True
luigi.enabled = False

app.run()from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random, logging

# ────────────────────────── Window & Engine ──────────────────────────
logging.getLogger('ursina').setLevel(logging.WARNING)
app = Ursina(borderless=False, development_mode=False)
window.title = 'Super Mario Odyssey 2 – Prototype'
window.size = (960, 600)
window.position = (80, 60)
window.fps_counter.enabled = True
app.target_fps = 60
mouse.locked = True

# ────────────────────────── Global State ──────────────────────────
current_kingdom = "n64_express"
current_player = "mario"
coins, stars, moons, health = 0, 0, 0, 3
power_up = None  # None, 'fire', 'star'

# Tunables
PLAYER_SPEED = 6
PLAYER_JUMP = 1.8
JUMP_DURATION = 0.4
CAMERA_FOV = 90
COLLECT_RADIUS = 1.8
FIREBALL_SPEED = 10

# ────────────────────────── Helper Factories ──────────────────────────
def make_coin(pos):
    return Entity(model='sphere', scale=0.5, color=color.gold, position=pos, collider='sphere')

def make_star(pos):
    return Entity(model='cube', scale=0.7, color=color.yellow, position=pos, collider='box')

def make_moon(pos):
    return Entity(model='sphere', scale=0.6, color=color.silver, position=pos, collider='sphere')

def make_goomba(pos):
    b = Entity(model='cube', scale=0.9, color=color.brown, position=pos, collider='box')
    b.name = 'goomba'
    return b

def make_chain_chomp(pos):
    b = Entity(model='sphere', scale=1.2, color=color.gray, position=pos, collider='sphere')
    b.name = 'chain_chomp'
    return b

def make_cheep_cheep(pos):
    b = Entity(model='cube', scale=(0.8, 0.4, 0.8), color=color.red, position=pos, collider='box')
    b.name = 'cheep_cheep'
    return b

# ────────────────────────── Players & Capture ──────────────────────────
def build_character(col):
    body = Entity(model='cube', scale=(0.8, 1.6, 0.8), color=col)
    head = Entity(model='sphere', scale=0.7, parent=body, y=0.9, color=col)
    hat = Entity(model='cube', scale=(1, 0.2, 1), parent=body, y=1.1, color=col)
    eyes = Entity(model='quad', scale=(0.3, 0.2), parent=body, y=0.9, z=0.35, color=color.white)
    return body

mario = build_character(color.red)
luigi = build_character(color.green)
captured = Entity(model='cube', scale=1, color=color.brown, enabled=False)

# ────────────────────────── First-Person Controller ───────────────────
player = FirstPersonController(speed=PLAYER_SPEED, jump_height=PLAYER_JUMP, jump_duration=JUMP_DURATION, gravity=1)
player.cursor.visible = False
player.visible = False
camera.fov = CAMERA_FOV

def sync_avatar():
    host = captured if captured.enabled else (mario if current_player == "mario" else luigi)
    host.position = player.position + (0, -0.9, 0)
    host.rotation = (0, -player.rotation_y, 0)

# ────────────────────────── UI / HUD ──────────────────────────
coin_txt = Text(text='Coins: 0', position=window.top_left + (0.06, -0.05), scale=1.5)
star_txt = Text(text='Stars: 0', position=window.top_left + (0.06, -0.10), scale=1.5)
moon_txt = Text(text='Moons: 0', position=window.top_left + (0.06, -0.15), scale=1.5)
health_txt = Text(text='Health: 3', position=window.top_left + (0.06, -0.20), scale=1.5)
kingdom_lbl = Text(text='N64 Express', position=window.top, origin=(0, 0), y=-0.06, scale=2)
char_lbl = Text(text='Character: Mario', position=window.bottom_left + (0.06, 0.05), scale=1.5)
power_txt = Text(text='Power: None', position=window.bottom_left + (0.06, 0.10), scale=1.5)

# ────────────────────────── Kingdom Construction Tools ────────────────
def flat_kingdom(size, texture, tint, height=0, spawn_coins=True, water=False):
    terr = Entity(model='plane', texture=texture, color=tint, scale=size, y=height, collider='mesh')
    entities = [terr]
    if spawn_coins:
        for _ in range(20):
            x = random.uniform(-size * 4, size * 4)
            z = random.uniform(-size * 4, size * 4)
            entities.append(make_coin((x, terr.y + 1, z)))
    s_pos = (random.uniform(-size * 3, size * 3), terr.y + 1, random.uniform(-size * 3, size * 3))
    entities.append(make_star(s_pos))
    m_pos = (random.uniform(-size * 3, size * 3), terr.y + 1, random.uniform(-size * 3, size * 3))
    entities.append(make_moon(m_pos))
    for _ in range(5):
        entities.append(make_goomba((random.uniform(-size * 3, size * 3), terr.y + 1, random.uniform(-size * 3, size * 3))))
    for _ in range(3):
        entities.append(make_chain_chomp((random.uniform(-size * 3, size * 3), terr.y + 1, random.uniform(-size * 3, size * 3))))
    if water:
        for _ in range(4):
            entities.append(make_cheep_cheep((random.uniform(-size * 3, size * 3), terr.y + 0.5, random.uniform(-size * 3, size * 3))))
    return entities

def cloud_kingdom():
    entities = []
    base = Entity(model='plane', texture='white_cube', color=color.white, scale=50, y=50, collider='mesh')
    entities.append(base)
    for _ in range(10):
        x = random.uniform(-40, 40)
        z = random.uniform(-40, 40)
        y = random.uniform(51, 60)
        plat = Entity(model='cube', texture='white_cube', color=color.white, scale=(5, 0.5, 5), position=(x, y, z), collider='box')
        entities.append(plat)
        if random.random() < 0.5:
            entities.append(make_coin((x, y + 1, z)))
    entities.append(make_moon((0, 55, 0)))
    return entities

kingdoms = {
    "n64_express": [],
    "waterfront": flat_kingdom(100, 'white_cube', color.blue, height=0, spawn_coins=True, water=True),
    "flower": flat_kingdom(80, 'grass', color.lime, height=0),
    "shimmerock": flat_kingdom(90, 'white_cube', color.light_gray, height=0.5),
    "bowser_jr": flat_kingdom(90, 'white_cube', color.orange, height=0),
    "skyloft": flat_kingdom(60, 'grass', color.cyan, height=40),
    "darker_side": flat_kingdom(100, 'white_cube', color.black66, height=0),
    "shine": flat_kingdom(120, 'white_cube', color.yellow, height=0),
    "toad_town": flat_kingdom(120, 'grass', color.azure, height=0),
    "bowser": flat_kingdom(100, 'white_cube', color.dark_gray, height=0),
    "crystal": flat_kingdom(80, 'white_cube', color.white, height=0),
    "food": flat_kingdom(90, 'white_cube', color.pink, height=0),
    "cloud": cloud_kingdom(),
}

def build_n64_express():
    entities = []
    entities.append(Entity(model='cube', texture='brick', scale=(25, 5, 6), y=2.5, collider='box'))
    for off in (-10, -17, -24):
        entities.append(Entity(model='cube', texture='brick', scale=(6, 4, 5), position=(off, 2, 0), collider='box'))
    for x in (10, 5, -5, -10, -17, -24):
        for z in (3, -3):
            entities.append(Entity(model='cube', scale=(1, 0.3, 1), color=color.gray, position=(x, 0.5, z), rotation_x=90))
    names = ["Waterfront", "Flower", "Shimmerock", "Bowser Jr.", "Skyloft", "Darker Side", "Shine", "Toad Town", "Bowser", "Crystal", "Food", "Cloud"]
    for i, n in enumerate(names):
        ent = Entity(model='circle', color=color.azure, scale=2.5, position=(-5 - (i * 5), 3, 0), rotation_x=90, collider='box')
        ent.name = f"{n} Kingdom"
        entities.append(ent)
    return entities

kingdoms["n64_express"] = build_n64_express()

# ────────────────────────── Kingdom Switching ──────────────────────────
def switch_kingdom(name):
    global current_kingdom
    for e in kingdoms[current_kingdom]:
        e.enabled = False
    current_kingdom = name
    for e in kingdoms[name]:
        e.enabled = True
    player.position = (0, 5 if name != "n64_express" else 3, 0)
    kingdom_lbl.text = name.replace("_", " ").title()

for k, lst in kingdoms.items():
    if k != "n64_express":
        for e in lst:
            e.enabled = False

# ────────────────────────── Cap Throw / Capture ────────────────────────
def throw_cap():
    hit = raycast(player.position, player.forward, distance=6, ignore=(player,))
    if hit.hit and getattr(hit.entity, 'name', '') in ['goomba', 'chain_chomp', 'cheep_cheep']:
        capture_enemy(hit.entity)

def capture_enemy(enemy):
    enemy.enabled = False
    captured.enabled = True
    captured.name = enemy.name
    mario.enabled = luigi.enabled = False
    invoke(uncapture, delay=5)

def uncapture():
    captured.enabled = False
    captured.name = ''
    (mario if current_player == "mario" else luigi).enabled = True

# ────────────────────────── Power-Ups ──────────────────────────
def apply_power_up(power):
    global power_up
    power_up = power
    power_txt.text = f"Power: {power.title() if power else 'None'}"
    if power == 'star':
        invoke(clear_power_up, delay=10)

def clear_power_up():
    global power_up
    power_up = None
    power_txt.text = 'Power: None'

def shoot_fireball():
    if power_up == 'fire':
        fb = Entity(model='sphere', scale=0.3, color=color.orange, position=player.position + player.forward * 1, collider='sphere')
        fb.name = 'fireball'
        fb.velocity = player.forward * FIREBALL_SPEED
        invoke(destroy, fb, delay=3)

# ────────────────────────── Input ──────────────────────────
def input(key):
    global current_player, coins, stars, moons, health
    if key == 'c':
        current_player = 'luigi' if current_player == 'mario' else 'mario'
        mario.enabled, luigi.enabled = current_player == 'mario', current_player == 'luigi'
        char_lbl.text = f"Character: {current_player.title()}"
    elif key == 'f':
        throw_cap()
    elif key == 'g' and power_up == 'fire':
        shoot_fireball()
    elif key == 'e' and current_kingdom == 'n64_express':
        for p in kingdoms['n64_express']:
            if distance(player.position, p.position) < 3 and hasattr(p, 'name'):
                target = p.name.replace(" Kingdom", "").replace(" ", "_").replace(".", "").lower()
                switch_kingdom(target)
    elif key == 'r' and current_kingdom != 'n64_express':
        switch_kingdom('n64_express')
    elif key == 'q':
        application.quit()

# ────────────────────────── Main Update Loop ──────────────────────────
def update():
    global coins, stars, moons, health
    sync_avatar()
    for e in kingdoms[current_kingdom]:
        if not e.enabled:
            continue
        if distance(player.position, e.position) > COLLECT_RADIUS:
            continue
        if e.color == color.gold:
            coins += 1
            coin_txt.text = f"Coins: {coins}"
            e.enabled = False
        elif e.color == color.yellow:
            stars += 1
            star_txt.text = f"Stars: {stars}"
            e.enabled = False
            switch_kingdom('n64_express')
        elif e.color == color.silver:
            moons += 1
            moon_txt.text = f"Moons: {moons}"
            e.enabled = False
        elif e.name in ['goomba', 'chain_chomp', 'cheep_cheep'] and power_up != 'star':
            health -= 1
            health_txt.text = f"Health: {health}"
            e.enabled = False
            if health <= 0:
                switch_kingdom('n64_express')
                health = 3
                health_txt.text = f"Health: {health}"
    if captured.enabled and captured.name == 'chain_chomp':
        player.position += player.forward * 0.2
    for e in kingdoms[current_kingdom]:
        if not e.enabled or e.name != 'fireball':
            continue
        for enemy in kingdoms[current_kingdom]:
            if not enemy.enabled or enemy.name not in ['goomba', 'chain_chomp', 'cheep_cheep']:
                continue
            if distance(e.position, enemy.position) < 1:
                destroy(e)
                enemy.enabled = False

# ────────────────────────── Scene Init ──────────────────────────
player.position = (0, 3, 0)
(camera.ui).enabled = True
sky = Sky(color=color.cyan)
mario.enabled = True
luigi.enabled = False

app.run()

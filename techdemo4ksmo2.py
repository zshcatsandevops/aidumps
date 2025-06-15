from ursina import *

# Constants
FIREBALL_SPEED = 10
COLLECT_RADIUS = 2

# Initialize Ursina app
app = Ursina()

# Define player entities
mario = Entity(model="cube", color=color.red, scale=1, position=(0, 0, 0))
luigi = Entity(model="cube", color=color.green, scale=1, position=(0, 0, 0))
captured = Entity(model=None, enabled=False)

# Set initial player state
current_player = "mario"
player = mario
mario.enabled = True
luigi.enabled = False

# Define kingdoms with entities
kingdoms = {
    "n64_express": [
        Entity(model="cube", color=color.yellow, position=(5, 0, 0), name="star", collider="box"),
        Entity(model="sphere", color=color.gold, position=(2, 0, 0), name="coin", collider="sphere"),
        Entity(model="sphere", color=color.gold, position=(-2, 0, 0), name="coin", collider="sphere"),
    ],
    "mushroom_kingdom": [
        Entity(model="cube", color=color.white, position=(0, 0, 5), name="moon", collider="box"),
        Entity(model="cube", color=color.brown, position=(3, 0, 3), name="goomba", collider="box"),
        Entity(model="cube", color=color.gray, position=(-3, 0, 3), name="chain_chomp", collider="box"),
    ],
}
current_kingdom = "mushroom_kingdom"

# UI elements
coin_txt = Text(text="Coins: 0", position=(-0.8, 0.45))
star_txt = Text(text="Stars: 0", position=(-0.8, 0.4))
moon_txt = Text(text="Moons: 0", position=(-0.8, 0.35))
health_txt = Text(text="Health: 3", position=(-0.8, 0.3))

# Game variables
coins = 0
stars = 0
moons = 0
health = 3
power_up = "fire"  # Set to "fire" for testing fireball functionality

# Function definitions
def shoot_fireball():
    global kingdoms
    if power_up != "fire":
        return
    fb = Entity(model="sphere", scale=0.3, color=color.orange, position=player.position + player.forward * 1.2, collider="sphere")
    fb.name = "fireball"
    fb.velocity = player.forward.normalized() * FIREBALL_SPEED
    kingdoms[current_kingdom].append(fb)
    def fb_update():
        fb.position += fb.velocity * time.dt
    fb.update = fb_update
    invoke(lambda: (kingdoms[current_kingdom].remove(fb), destroy(fb)), delay=3)

def capture_enemy(enemy: Entity):
    global player
    enemy.enabled = False
    captured.enabled = True
    captured.name = enemy.name
    mario.enabled = luigi.enabled = False
    captured.model = enemy.model
    captured.scale = enemy.scale
    captured.color = enemy.color
    captured.original_model = enemy.model
    captured.original_scale = enemy.scale
    captured.original_player = player
    player = captured  # Player controls the captured entity
    invoke(uncapture, delay=5)

def uncapture():
    global player
    player = captured.original_player  # Restore original player
    captured.enabled = False
    captured.name = ""
    captured.model = captured.original_model
    captured.scale = captured.original_scale
    (mario if current_player == "mario" else luigi).enabled = True

def switch_kingdom(new_kingdom):
    global current_kingdom
    current_kingdom = new_kingdom
    # Optionally, teleport player or reset entities here if needed

def update():
    global coins, stars, moons, health
    # Placeholder for sync_avatar() if defined elsewhere
    # sync_avatar()

    # Handle entity interactions
    for e in kingdoms[current_kingdom][:]:
        if not e.enabled or distance(player.position, e.position) > COLLECT_RADIUS:
            continue
        match e.name:
            case "coin":
                coins += 1
                coin_txt.text = f"Coins: {coins}"
                kingdoms[current_kingdom].remove(e)
                destroy(e)
            case "star":
                stars += 1
                star_txt.text = f"Stars: {stars}"
                kingdoms[current_kingdom].remove(e)
                destroy(e)
                switch_kingdom("n64_express")
            case "moon":
                moons += 1
                moon_txt.text = f"Moons: {moons}"
                kingdoms[current_kingdom].remove(e)
                destroy(e)
            case "goomba" | "chain_chomp" | "cheep_cheep":
                if power_up != "star":
                    health -= 1
                    health_txt.text = f"Health: {health}"
                kingdoms[current_kingdom].remove(e)
                destroy(e)
                if health <= 0:
                    switch_kingdom("n64_express")
                    health = 3
                    health_txt.text = f"Health: {health}"

    # Chain chomp movement when captured
    if captured.enabled and captured.name == "chain_chomp":
        player.position += player.forward * 0.2

    # Fireball-enemy collision
    for fb in [e for e in kingdoms[current_kingdom] if e.enabled and e.name == "fireball"]:
        for enemy in [en for en in kingdoms[current_kingdom] if en.enabled and en.name in ["goomba", "chain_chomp", "cheep_cheep"]]:
            if distance(fb.position, enemy.position) < 1:
                kingdoms[current_kingdom].remove(fb)
                destroy(fb)
                kingdoms[current_kingdom].remove(enemy)
                destroy(enemy)
                break  # Prevent list modification issues

    # Player movement
    if held_keys['w']:
        player.position += player.forward * time.dt * 5
    if held_keys['s']:
        player.position += player.back * time.dt * 5
    if held_keys['a']:
        player.position += player.left * time.dt * 5
    if held_keys['d']:
        player.position += player.right * time.dt * 5

    # Camera follow
    camera.position = player.position + Vec3(0, 10, -10)
    camera.look_at(player)

def input(key):
    if key == 'space':
        shoot_fireball()

# Set frame rate to 60 FPS
application.target_frame_rate = 60

# Run the game
app.run()

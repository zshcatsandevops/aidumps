from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random

app = Ursina()

# --- Window and Application Settings ---
window.fps_counter.enabled = True
window.title = 'SM64-Inspired Game'
window.borderless = False
window.vsync = True
application.development_mode = False # Set to True for more verbose error messages during development

# --- Player Setup ---
player = FirstPersonController(
    collider='box', # Using a box collider for FPC can sometimes be tricky with ground detection
    jump_height=2.0, # SM64 jumps are quite high
    gravity=0.6,    # Slightly lower gravity for more floaty jumps
    speed=10,
    position=(0, 10, 0)
)
player.cursor.visible = False
player.can_fly = False # Wing Cap status
player.jump_count = 0
player.is_swimming = False
player.coins = 0
player.max_health = 8
player.health = player.max_health
player.invincible_timer = 0 # Time for which player is invincible after taking damage
player.is_ground_pounding = False
player.is_diving = False
player.dive_timer = 0
player.original_gravity = player.gravity # Store original gravity

# --- UI Elements ---
health_text = Text(text=f'Health: {player.health}/{player.max_health}', origin=(0, -16), color=color.red, scale=1.5, background=True)
star_text = Text(text=f'Stars: 0/0', origin=(0, -18), color=color.gold, scale=1.5, background=True) # Initialized later
coin_text = Text(text=f'Coins: {player.coins}', origin=(0, -20), color=color.yellow, scale=1.5, background=True)
red_coin_text = Text(text=f'Red Coins: 0/0', origin=(0, -22), color=color.orange, scale=1.5, background=True) # Initialized later

def update_health_ui():
    health_text.text = f'Health: {player.health}/{player.max_health}'
    if player.health <= 0:
        health_text.color = color.gray
    else:
        health_text.color = color.red

def update_coin_ui():
    coin_text.text = f'Coins: {player.coins}'

# --- Terrains ---
ground = Entity(model='quad', color=color.lime, scale=300, rotation_x=90, collider='box', position=(0,0,0))
water_area = Entity(model='cube', color=color.rgba(0, 100, 255, 128), collider='box', position=(70, -5, 70), scale=(60, 10, 60), alpha=0.5)
snow_area = Entity(model='cube', color=color.white, collider='box', position=(-70, 5, -70), scale=(60, 1, 60))
# Add some slopes
slope1 = Entity(model='cube', color=color.rgb(0,180,0), collider='box', position=(0, 2.5, 40), scale=(20, 5, 20), rotation_x=20)
slope2 = Entity(model='cube', color=color.rgb(0,170,0), collider='box', position=(0, 2.5, -40), scale=(20, 5, 20), rotation_x=-20)


# --- Wing Cap ---
class WingCap(Entity):
    def __init__(self, position):
        super().__init__(model='cube', color=color.red, position=position, collider='box', scale=1)
        self.rotation_speed = 50
        self.original_y = position.y # To bob up and down
        self.bob_timer = 0

    def update(self):
        self.rotation_y += self.rotation_speed * time.dt
        self.bob_timer += time.dt
        self.y = self.original_y + sin(self.bob_timer * 3) * 0.2 # Bobbing effect

        if self.enabled and self.intersects(player).hit and not player.can_fly:
            player.can_fly = True
            player.gravity = 0 # Flying overrides gravity
            print_on_screen("Wing Cap Activated!", position=(-0.5, 0.4), scale=2, duration=3)
            invoke(self.remove_wing_cap, delay=20) # Wing cap lasts 20 seconds
            self.disable() # Disable the cap entity itself

    def remove_wing_cap(self):
        if player.can_fly: # Check if player is still flying (might have landed in water etc)
            player.can_fly = False
            if not player.is_swimming: # Only restore gravity if not in water
                 player.gravity = player.original_gravity
            print_on_screen("Wing Cap Wore Off!", position=(-0.5, 0.4), scale=2, duration=3)
            # Re-enable the cap or spawn a new one if desired
            # For now, it's a one-time use in this example
            # self.enable()
            # self.position = (random.uniform(-20,20), ground.y + 6, random.uniform(-20,20))


wing_cap = WingCap(position=(10, ground.y + 6, 10))

# --- Collectibles ---
TOTAL_STARS = 7
stars_collected = 0
stars_list = [] # To keep track of star objects

TOTAL_RED_COINS = 8
red_coins_collected = 0
red_coin_star_spawned = False
red_coins_list = []

coins_on_screen = [] # Keep track of regular coins


class Star(Entity):
    def __init__(self, position, is_red_coin_star=False):
        super().__init__(model='sphere', color=color.yellow, scale=0.8, collider='sphere', position=position,
                         texture='radial_gradient') # simple texture effect
        self.rotation_speed = random.uniform(80, 120)
        self.is_red_coin_star = is_red_coin_star
        self.original_y = position.y
        self.bob_timer = random.uniform(0, 5) # Randomize bob start
        stars_list.append(self)

    def update(self):
        self.rotation_y += self.rotation_speed * time.dt
        self.rotation_x += self.rotation_speed * 0.5 * time.dt
        self.bob_timer += time.dt
        self.y = self.original_y + sin(self.bob_timer * 2) * 0.15 # Bobbing effect

        if self.enabled and self.intersects(player).hit:
            global stars_collected
            stars_collected += 1
            update_star_ui()
            print_on_screen(f"Star Collected! ({stars_collected}/{TOTAL_STARS})", position=(-0.5, 0.4), scale=2, duration=3)
            self.disable()
            stars_list.remove(self)

def update_star_ui():
    star_text.text = f'Stars: {stars_collected}/{TOTAL_STARS}'
    if stars_collected >= TOTAL_STARS:
        Text("All main stars collected!", origin=(0, 0), scale=3, color=color.cyan, background=True, duration=10)

star_text.text = f'Stars: {stars_collected}/{TOTAL_STARS}' # Initial UI update

class RedCoin(Entity):
    def __init__(self, position):
        super().__init__(model='sphere', color=color.red, scale=0.4, collider='sphere', position=position,
                         texture='radial_gradient')
        self.rotation_speed = random.uniform(60, 100)
        self.original_y = position.y
        self.bob_timer = random.uniform(0,5)
        red_coins_list.append(self)

    def update(self):
        self.rotation_y += self.rotation_speed * time.dt
        self.bob_timer += time.dt
        self.y = self.original_y + sin(self.bob_timer * 2.5) * 0.1

        if self.enabled and self.intersects(player).hit:
            global red_coins_collected, red_coin_star_spawned, TOTAL_STARS
            if not self.is_red_coin_star: # Ensure it's not accidentally counting the reward star
                red_coins_collected += 1
                update_red_coin_ui()
                self.disable()
                red_coins_list.remove(self)
                if red_coins_collected >= TOTAL_RED_COINS and not red_coin_star_spawned:
                    print_on_screen("All Red Coins Collected! A Star Appears!", position=(-0.5, 0.3), scale=2, duration=4)
                    # Spawn a star, e.g., near the last collected red coin or a fixed spot
                    Star(position=player.position + Vec3(0, 5, 5), is_red_coin_star=True)
                    red_coin_star_spawned = True
                    TOTAL_STARS +=1 # Increment total stars if red coin star is a bonus
                    update_star_ui() # Update total in UI

def update_red_coin_ui():
    red_coin_text.text = f'Red Coins: {red_coins_collected}/{TOTAL_RED_COINS}'

red_coin_text.text = f'Red Coins: {red_coins_collected}/{TOTAL_RED_COINS}' # Initial UI update


class Coin(Entity):
    def __init__(self, position):
        super().__init__(model='sphere', color=color.gold, scale=0.3, collider='sphere', position=position)
        self.rotation_speed = random.uniform(50, 150)
        self.original_y = position.y
        self.bob_timer = random.uniform(0,5)
        coins_on_screen.append(self)

    def update(self):
        self.rotation_y += self.rotation_speed * time.dt
        self.bob_timer += time.dt
        self.y = self.original_y + sin(self.bob_timer * 3) * 0.05


        if self.enabled and self.intersects(player).hit:
            player.coins += 1
            update_coin_ui()
            # Small feedback for coin collection
            # Text("+1", position=self.screen_position + Vec2(0,0.05), origin=(0,0), color=color.yellow, scale=1, duration=0.5)
            self.disable()
            coins_on_screen.remove(self)
            if player.coins % 100 == 0: # SM64 1-UP at 50/100 coins, simplified here
                 print_on_screen("100 Coins! Extra Health!", position=(-0.5, 0.4), scale=2, duration=3)
                 player.health = min(player.max_health, player.health + 1) # SM64 gives a life, here +1 health
                 update_health_ui()


# --- Populate Collectibles ---
for i in range(TOTAL_STARS):
    Star(position=(random.uniform(-70, 70), random.uniform(5, 20), random.uniform(-70, 70)))

for i in range(TOTAL_RED_COINS):
    # Spread red coins a bit more intentionally if designing a level
    RedCoin(position=(random.uniform(-60, 60), random.uniform(3, 15), random.uniform(-60, 60)))

for _ in range(150):
    Coin(position=(random.uniform(-78, 78), random.uniform(2, 32), random.uniform(-78, 78)))


# --- Enemies ---
class Goomba(Entity):
    def __init__(self, position):
        super().__init__(model='cube', color=color.rgb(150, 75, 0), collider='box', position=position, scale=(1.5, 1, 1.5)) # More Goomba-like proportions
        self.speed = random.uniform(1, 2.5)
        self.turn_speed = random.uniform(60,120)
        self.view_distance = 15
        self.state = 'patrol' # patrol, chase
        self.patrol_target = self.position + Vec3(random.uniform(-5,5),0,random.uniform(-5,5))
        self.health = 1

    def update(self):
        if self.health <= 0 or not self.enabled:
            return

        dist_to_player = distance_xz(self, player)

        if self.state == 'patrol':
            if dist_to_player < self.view_distance:
                self.state = 'chase'
            else:
                if distance_xz(self.position, self.patrol_target) < 1:
                    self.patrol_target = self.world_position + Vec3(random.uniform(-10,10),0,random.uniform(-10,10))
                self.look_at_2d(self.patrol_target, 'y')
                self.position += self.forward * self.speed * time.dt * 0.5 # Slower when patrolling

        elif self.state == 'chase':
            if dist_to_player > self.view_distance * 1.5: # Lose interest
                self.state = 'patrol'
            else:
                self.look_at_2d(player.position, 'y')
                self.position += self.forward * self.speed * time.dt

        # Boundary checks
        if self.x > 95 or self.x < -95 or self.z > 95 or self.z < -95:
            self.look_at_2d(Vec3(0,0,0),'y') # Turn towards center if out of bounds
            if self.state == 'chase': self.state = 'patrol' # Reset state

        # Collision with player
        if self.intersects(player).hit:
            if player.is_ground_pounding and player.y > self.world_y + self.scale_y * 0.5:
                self.take_damage(10) # Ground pound insta-kills
                player.velocity.y = player.jump_height * 0.7 # Small bounce after ground pound
                player.is_ground_pounding = False # End ground pound on hit
                player.gravity = player.original_gravity
            elif player.y > self.world_y + self.scale_y * 0.7 and player.velocity.y < -0.1: # Stomp
                self.take_damage(1)
                # player.jump() # FPC jump is a bit much, let's do a smaller bounce
                player.velocity.y = player.jump_height * 0.6
            elif player.is_diving:
                self.take_damage(1)
                # Stop player's dive
                player.is_diving = False
                player.dive_timer = 0
                player.velocity = Vec3(0,0,0)
            elif player.invincible_timer <= 0: # Player not invincible
                take_player_damage(1)

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            print_on_screen("Goomba Defeated!", duration=1.5, position=self.screen_position)
            # Spawn a coin or effect
            Coin(self.position + Vec3(0,0.5,0))
            self.disable()
            # Could add a particle effect here

for _ in range(10):
    Goomba(position=(random.uniform(-70, 70), ground.y + 0.5, random.uniform(-70, 70)))

# --- NPC ---
class NPC(Entity):
    def __init__(self, position, message="Hello, adventurer! Find all the stars!"):
        super().__init__(model='cube', color=color.cyan, position=position, collider='box', scale=(1, 2, 1)) # Taller
        self.message = message
        self.talk_cooldown = 0
        self.original_y = position.y
        self.bob_timer = random.uniform(0,5)

    def update(self):
        self.bob_timer += time.dt
        self.y = self.original_y + sin(self.bob_timer * 1.5) * 0.1

        if self.talk_cooldown > 0:
            self.talk_cooldown -= time.dt
        if distance(self, player) < 4 and self.talk_cooldown <= 0:
            print_on_screen(self.message, position=(-0.6, 0.3), scale=1.5, duration=4, text_color=color.black, background=True)
            self.talk_cooldown = 5 # Can talk every 5 seconds

npc = NPC(position=(20, ground.y + 1, 20), message=f"Collect {TOTAL_STARS} Stars and {TOTAL_RED_COINS} Red Coins!")

# --- Player Damage and Death ---
def take_player_damage(amount):
    if player.invincible_timer > 0:
        return

    player.health -= amount
    update_health_ui()
    print_on_screen("Ouch!", position=(-0.5, 0.4), scale=2, duration=2, text_color=color.red)
    player.invincible_timer = 1.5 # 1.5 seconds of invincibility

    # Visual feedback for invincibility
    player.color = color.rgba(255,0,0,150)
    invoke(reset_player_color, delay=player.invincible_timer)


    if player.health <= 0:
        player_death()

def reset_player_color():
    player.color = color.white # Assuming FPC is white by default or has no specific color.
                               # FirstPersonController doesn't have a simple .color,
                               # this might need to affect its children if it has a model.
                               # For now, it's a conceptual reset.

def player_death():
    print_on_screen("Game Over!", origin=(0,0), scale=4, duration=5, text_color=color.black)
    player.health = player.max_health // 2 # Restart with half health
    player.position = (0, 10, 0) # Reset position
    player.coins = max(0, player.coins - 50) # Lose some coins
    update_health_ui()
    update_coin_ui()
    # Potentially reset some level elements or enemy positions if desired

# --- Main Update Loop ---
def update():
    # Invincibility timer
    if player.invincible_timer > 0:
        player.invincible_timer -= time.dt
        # Flicker effect for invincibility
        player.visible = not (int(player.invincible_timer * 10) % 2 == 0) # FPC visibility
    else:
        player.visible = True


    # Manage player states and gravity
    current_gravity = player.original_gravity

    if player.is_swimming:
        current_gravity = 0.07 # Less gravity in water
        player.velocity.y = clamp(player.velocity.y, -0.2, 0.2) # Clamp vertical speed in water
        if held_keys['space']:
            player.y += 3 * time.dt
        if held_keys['control'] or held_keys['c']: # Use 'left control' for consistency
            player.y -= 3 * time.dt
    elif player.can_fly:
        current_gravity = 0
        if held_keys['space']:
            player.y += 7 * time.dt
        if held_keys['control'] or held_keys['c']: # Use 'left control'
            player.y -= 7 * time.dt
    elif player.is_ground_pounding:
        current_gravity = 3.5 # Strong gravity for ground pound
    elif player.is_diving:
        current_gravity = player.original_gravity * 0.8 # Slight downward pull during dive, FPC handles most
        player.dive_timer -= time.dt
        if player.dive_timer <=0 or player.grounded: # End dive
            player.is_diving = False
            # Small skid/recovery? For now, just stops.

    player.gravity = current_gravity


    # Water interaction
    if water_area.intersects(player).hit:
        # Check if player is mostly submerged
        if player.y < water_area.y + water_area.scale_y / 2 - player.height/2:
            if not player.is_swimming:
                player.is_swimming = True
                print_on_screen("Entered water", duration=2)
        # If player is just above water surface but intersected, could make them "bob" or slightly sink
    else: # Not intersecting water_area
        if player.is_swimming:
            player.is_swimming = False
            player.gravity = player.original_gravity # Restore gravity when leaving water
            print_on_screen("Left water", duration=2)

    # Ground pound landing
    if player.is_ground_pounding and player.grounded:
        player.is_ground_pounding = False
        player.gravity = player.original_gravity
        # Create a small shockwave effect (visual only for now)
        shockwave = Entity(model='circle', color=color.rgba(200,200,200,150), scale=0.1, position=player.position - Vec3(0,player.height/2 -0.1,0) , rotation_x=90)
        shockwave.animate_scale(3, duration=0.3, curve=curve.linear)
        shockwave.animate_alpha(0, duration=0.35, curve=curve.linear)
        destroy(shockwave, delay=0.4)
        # print_on_screen("Ground Pound!", duration=1) # Optional feedback
        # Nearby enemies could react to this (e.g. get stunned or damaged)

    # Fall out of world
    if player.y < -50:
        print_on_screen("Fell out of the world!", duration=3)
        take_player_damage(2) # Take some damage
        player.position = (0, 10, 0) # Reset position

    # Simple check for player "grounded" status for multi-jumps if FPC's internal one isn't enough
    # FPC handles its own grounded state, so player.grounded should be reliable.

# --- Input Handling ---
def input(key):
    global TOTAL_STARS # Allow modification if a star is added (e.g. red coin star)

    # --- Player Actions ---
    if player.is_diving or player.is_ground_pounding: # Prevent other actions during these states
        return

    # Jump variations
    if key == 'space':
        if player.is_swimming or player.can_fly: # Space is for up movement in these states
            return

        if player.grounded:
            player.jump()
            player.jump_count = 1
        elif player.jump_count < 3: # Allow double and triple jump
            player.jump() # FPC jump handles the upward velocity
            player.jump_count += 1
            if player.jump_count == 2: # Double Jump
                player.velocity.y *= 1.1 # Make second jump slightly higher
                print_on_screen("Double Jump!", duration=0.7, scale=1.5)
            elif player.jump_count == 3: # Triple Jump
                player.velocity.y *= 1.3 # Make third jump even higher
                # Add some forward momentum to triple jump if moving
                if player.velocity.xz.length() > 1:
                    player.velocity += player.forward * player.speed * 0.2
                print_on_screen("Triple Jump!", duration=1, scale=1.8)

    # Long Jump (Shift + Space while running on ground)
    if key == 'space down' and held_keys['left shift'] and player.grounded and player.velocity.xz.length() > player.speed * 0.3:
        # Check if FPC is moving forward significantly enough
        if LVector3f(player.velocity).xz.length_squared() > 0.1 : # FPC velocity directly
            player.velocity = player.forward * player.speed * 1.3 + Vec3(0, player.jump_height * 0.7, 0)
            player.jump_count = 1 # Counts as a jump
            print_on_screen("Long Jump!", position=(-0.5, 0.4), scale=2, duration=1)

    # Ground Pound (Control/C while in air)
    if (key == 'left control down' or key == 'c down') and not player.grounded and not player.is_swimming and not player.can_fly:
        player.is_ground_pounding = True
        player.velocity.x = 0  # Stop horizontal movement
        player.velocity.z = 0
        # Gravity will be increased in update()
        print_on_screen("Ground Pounding!", duration=1)

    # Dive (Left Mouse Button while running on ground)
    if key == 'left mouse down' and player.grounded and not player.is_swimming:
        # Check if player is moving with significant speed
        if LVector3f(player.velocity).xz.length_squared() > (player.speed * 0.3)**2 :
            player.is_diving = True
            player.dive_timer = 0.6 # Duration of dive
            # Lunge forward: FPC applies its own movement, so we give an initial boost if needed
            # FPC's movement might override direct velocity settings quickly.
            # A common way to do a dive with character controllers is to trigger an animation
            # and let animation root motion handle the movement, or apply a temporary force.
            # For FPC, we can try to influence its velocity or temporarily change its state.
            player.velocity = player.forward * player.speed * 1.8 + Vec3(0, player.jump_height * 0.2, 0)
            print_on_screen("Dive!", duration=0.8)


    # --- Debug/Testing Keys ---
    if key == 'k': # Debug key to test damage
        take_player_damage(1)
    if key == 'l': # Debug key to get a star
        if stars_list:
            s = stars_list[0]
            s.intersect(player) # Force collection for test
    if key == 'r': # Debug key to collect a red coin
        if red_coins_list:
            rc = red_coins_list[0]
            rc.intersects(player) # Force collection
            rc.update() # Trigger its update logic


# --- Sky and Lighting ---
Sky() # Add a simple skybox
AmbientLight(color=color.rgba(100,100,100,0.1)) # Basic ambient light
DirectionalLight(color=color.rgba(150,150,100,0.2), direction=(1,1,1)) # A bit of directional light
DirectionalLight(color=color.rgba(150,150,100,0.2), direction=(-1,-1,-1)) # Light from other side


app.run()

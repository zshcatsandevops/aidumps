# main_game.py
from ursina import *
from ursina.shaders import basic_lighting_shader
import requests # For grabbing shit from GitHub
import os # For file paths and stuff, duh

# --- GitHub Asset Fetching Crap ---
# Put a goddamn direct raw image URL here, like for a Mario sprite!
# e.g., https://raw.githubusercontent.com/your_username/your_repo/main/mario_texture.png
# If it's not a real URL or fails, Mario will be a boring default color, boo hoo.
GITHUB_MARIO_TEXTURE_URL = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/25.png' # Pikachu, 'cause why the fuck not for a placeholder?
PLAYER_TEXTURE_FILENAME = 'downloaded_player_texture.png'

def fetch_github_asset_motherfucker(url, filename):
    """Tries to download an asset from GitHub. Returns True on success, False on fail, purr."""
    try:
        print(f"Nyah! Trying to snatch '{url}' like a fuckin' catnip toy...")
        response = requests.get(url, stream=True)
        response.raise_for_status() # Will raise an HTTPError if the HTTP request returned an unsuccessful status code
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Purrfect! Snatched it and saved as '{filename}'. Good kitty!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"ERRRROWR! Couldn't get the goddamn asset from '{url}'. Fuckin' error: {e}")
        return False

# --- Player Class: It's-a-me, Fucko! ---
class PaperPlayer(Entity):
    def __init__(self, texture_path=None, **kwargs):
        super().__init__(
            model='quad', # Using quad for a truly flat paper look, can also be 'cube' with tiny z-scale
            collider='box',
            scale=(1.5, 2, 1), # Adjust as needed for your sprite
            position=(0, 1, 0), # Start player a bit above ground
            shader=basic_lighting_shader, # Basic lighting so it's not totally flat color
            **kwargs
        )
        
        if texture_path and os.path.exists(texture_path):
            self.texture = load_texture(texture_path.split(os.sep)[-1], path=os.path.dirname(texture_path))
            self.color = color.white # Show texture clearly
            print(f"Meow! Player texture '{texture_path}' loaded! Lookin' sharp, asshole!")
        else:
            self.color = color.red # Fallback color if no texture
            print(f"Grrr! Player texture not found or failed to load. Using boring ass red.")

        # Movement and Jump Attributes, goddammit!
        self.speed = 5
        self.gravity_force = 0.4 # How hard this fucker falls
        self.jump_height = 0.3    # How high this little shit can jump
        self.jumping = False
        self.air_time = 0       # How long this asshole has been airborne
        self.grounded = False   # Is the player on solid fuckin' ground?

    def update(self):
        # Movement, you lazy bastard
        self.x += (held_keys['d'] - held_keys['a']) * self.speed * time.dt
        self.z += (held_keys['w'] - held_keys['s']) * self.speed * time.dt

        # Simple Billboard Effect - player always faces camera (ish) for paper effect
        # Only rotate around Y axis to keep it upright
        if camera.world_rotation_y != self.world_rotation_y :
            self.world_rotation_y = camera.world_rotation_y
        
        # --- Jumping like a scalded cat ---
        if self.grounded and held_keys['space']:
            self.jumping = True
            self.grounded = False
            self.air_time = 0
            # Initial upward velocity impulse
            self.y += self.jump_height 
            print("WHEEE, motherfucker! Jump!")

        if not self.grounded:
            self.y -= self.gravity_force * time.dt * 25 # Apply gravity, the 25 is a magic number, deal with it
            self.air_time += time.dt

            # Check for ground collision (very basic, assumes ground is at y=0 and player origin)
            # A better way is raycasting or checking intersection with ground entity
            ground_check = raycast(self.world_position, self.down, distance=self.scale_y/2 + 0.1, ignore=[self,])
            
            if ground_check.hit:
                if self.y <= ground_check.world_point[1] + self.scale_y/2: # Ensure we don't sink
                    self.y = ground_check.world_point[1] + self.scale_y/2
                    self.grounded = True
                    self.jumping = False
                    self.air_time = 0
                    # print("Landed, bitch!") # Can be spammy
            elif self.y < 0.5: # Fallback absolute minimum height if raycast fails for some reason
                self.y = 0.5
                self.grounded = True
                self.jumping = False
                self.air_time = 0
                # print("Landed by fallback, you clumsy fuck!")

        # Collision with shit (obstacles for now)
        hit_info = self.intersects()
        if hit_info.hit:
            if hit_info.entity in obstacles:
                print("BAM! Hit a fuckin' obstacle!")
                # A little bounce back or something, or just destroy it
                destroy(hit_info.entity)
                obstacles.remove(hit_info.entity)
                # Make player flash or some shit
                self.blink(color.orange, duration=0.2)
            elif hit_info.entity in coins:
                print("Cha-ching, you greedy bastard!")
                destroy(hit_info.entity)
                coins.remove(hit_info.entity)
                # Add score or some shit here
                # Could also make a sound: Audio('coin_sound.wav') if you have one


# --- Main App Setup: Let's get this shitshow on the road! ---
app = Ursina(development_mode=True)

# Paper Mario style settings, meow!
window.color = color.rgb(135, 206, 250) # Nice sky blue, fuck yeah
window.borderless = False
window.title = 'CATSDK\'s Fucking Paper Tech Demo'

# Isometric camera, because why the fuck not?
camera.orthographic = True # Orthographic for true paper feel
camera.fov = 20 # Zoom level for orthographic
camera.position = (15, 15, -15)
camera.look_at((0,0,0)) # Look at origin
camera.rotation = (30, -45, 0) # Standard isometric angles

# Try to fetch the player texture, goddammit
if fetch_github_asset_motherfucker(GITHUB_MARIO_TEXTURE_URL, PLAYER_TEXTURE_FILENAME):
    player = PaperPlayer(texture_path=PLAYER_TEXTURE_FILENAME)
else:
    print("MEOWR! Couldn't get the fancy texture from GitHub. Using default shitty player.")
    player = PaperPlayer() # Player will use default red color


# Paper-style ground, so you don't fall into the goddamn void
ground = Entity(
    model='plane',
    # texture='white_cube', # Let's make it grass or something
    texture='grass',
    texture_scale=(20, 20),
    color=color.rgb(100, 180, 100), # Greenish, bitch
    scale=(40, 1, 40),
    collider='box',
    shader=basic_lighting_shader # So it catches some light
)

# Paper-style obstacles: Goombas or some shit
obstacles = []
for i in range(-5, 5, 2):
    obstacle = Entity(
        model='cube', # Flat cube
        # texture='brick', # If you have a Goomba texture, use it!
        color=color.brown, # Goomba-ish color
        scale=(1, 1, 0.1),  # Flat paper look
        position=(i * 2, 0.5, random.randint(-5, 5)),
        collider='box',
        shader=basic_lighting_shader,
        rotation_y = random.randint(0,360) # Random rotation to look less uniform
    )
    obstacles.append(obstacle)

# Paper-style "Coins" to collect, 'cause everyone loves shiny shit
coins = []
for i in range(5):
    coin = Entity(
        model='sphere', # Could be a cylinder for coin shape or a quad with texture
        color=color.gold,
        scale=0.5,
        position=(random.uniform(-10, 10), 1, random.uniform(-10, 10)),
        collider='sphere',
        shader=basic_lighting_shader
    )
    # Make 'em spin, the bastards!
    coin.animate('rotation_y', coin.rotation_y + 360, duration=2, loop=True, curve=curve.linear)
    coins.append(coin)

# Simple lighting, 'cause darkness sucks balls
pivot = Entity() # For rotating the light
DirectionalLight(parent=pivot, y=2, z=3, shadows=True, rotation=(45, -45, 45))


# Optional: Sky
sky = Sky()

# Optional: Editor Camera for debugging this clusterfuck
# editor_camera = EditorCamera(enabled=False, ignore_paused=True)

# def input(key):
#     if key == 'tab': # Press Tab to toggle editor camera
#         editor_camera.enabled = not editor_camera.enabled

print("Purrrrr... Ursina app is ready to fuckin' run! Move with WASD, jump with SPACE. Don't fuck it up!")
app.run()

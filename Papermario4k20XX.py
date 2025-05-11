from ursina import *
from ursina.shaders import basic_lighting_shader
import requests  # For grabbing assets from GitHub
import os  # For file paths and handling

# --- GitHub Asset Fetching ---
# Provide a direct raw image URL here, like for a Mario sprite!
# e.g., https://raw.githubusercontent.com/your_username/your_repo/main/mario_texture.png
# If the URL is invalid or fails, Mario will use a default color.
GITHUB_MARIO_TEXTURE_URL = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/25.png'  # Pikachu as a placeholder
PLAYER_TEXTURE_FILENAME = 'downloaded_player_texture.png'

def fetch_github_asset(url, filename):
    """Tries to download an asset from GitHub. Returns True on success, False on fail."""
    try:
        print(f"Meow! Trying to grab '{url}' like a catnip toy...")
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raises an HTTPError for unsuccessful status codes
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Purr! Saved as '{filename}'. Nice catch!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Meowr! Couldn't grab the asset from '{url}'. Error: {e}")
        return False

# --- Player Class: It's-a-me, Mario! ---
class PaperPlayer(Entity):
    def __init__(self, texture_path=None, **kwargs):
        super().__init__(
            model='quad',  # Using quad for a truly flat paper look, can also be 'cube' with tiny z-scale
            collider='box',
            scale=(1.5, 2, 1),  # Adjust as needed for your sprite
            position=(0, 1, 0),  # Start player a bit above ground
            shader=basic_lighting_shader,  # Basic lighting so it's not totally flat color
            **kwargs
        )
        
        if texture_path and os.path.exists(texture_path):
            self.texture = load_texture(texture_path.split(os.sep)[-1], path=os.path.dirname(texture_path))
            self.color = color.white  # Show texture clearly
            print(f"Meow! Player texture '{texture_path}' loaded! Looking sharp!")
        else:
            self.color = color.red  # Fallback color if no texture
            print(f"Grr! Player texture not found or failed to load. Using plain red.")

        # Movement and Jump Attributes
        self.speed = 5
        self.gravity_force = 0.4  # How fast the player falls
        self.jump_height = 0.3    # How high the player can jump
        self.jumping = False
        self.air_time = 0         # How long the player has been airborne
        self.grounded = False     # Is the player on solid ground?

    def update(self):
        # Movement
        self.x += (held_keys['d'] - held_keys['a']) * self.speed * time.dt
        self.z += (held_keys['w'] - held_keys['s']) * self.speed * time.dt

        # Simple Billboard Effect - player always faces camera (ish) for paper effect
        # Only rotate around Y axis to keep it upright
        if camera.world_rotation_y != self.world_rotation_y:
            self.world_rotation_y = camera.world_rotation_y
        
        # --- Jumping ---
        if self.grounded and held_keys['space']:
            self.jumping = True
            self.grounded = False
            self.air_time = 0
            # Initial upward velocity impulse
            self.y += self.jump_height 
            print("Whee! Jump!")

        if not self.grounded:
            self.y -= self.gravity_force * time.dt * 25  # Apply gravity, the 25 is a magic number
            self.air_time += time.dt

            # Check for ground collision (basic, assumes ground is at y=0 and player origin)
            # A better way is raycasting or checking intersection with ground entity
            ground_check = raycast(self.world_position, self.down, distance=self.scale_y/2 + 0.1, ignore=[self,])
            
            if ground_check.hit:
                if self.y <= ground_check.world_point[1] + self.scale_y/2:  # Ensure we don't sink
                    self.y = ground_check.world_point[1] + self.scale_y/2
                    self.grounded = True
                    self.jumping = False
                    self.air_time = 0
                    # print("Landed!")  # Can be spammy
            elif self.y < 0.5:  # Fallback minimum height if raycast fails
                self.y = 0.5
                self.grounded = True
                self.jumping = False
                self.air_time = 0
                # print("Landed by fallback!")

        # Collision with obstacles or coins
        hit_info = self.intersects()
        if hit_info.hit:
            if hit_info.entity in obstacles:
                print("Bam! Hit an obstacle!")
                # Remove the obstacle
                destroy(hit_info.entity)
                obstacles.remove(hit_info.entity)
                # Visual feedback
                self.blink(color.orange, duration=0.2)
            elif hit_info.entity in coins:
                print("Cha-ching! Collected a coin!")
                destroy(hit_info.entity)
                coins.remove(hit_info.entity)
                # Add score or other effects here
                # Could play a sound: Audio('coin_sound.wav') if available

# --- Main App Setup: Let's get this show started! ---
app = Ursina(development_mode=True)

# Paper Mario style settings
window.color = color.rgb(135, 206, 250)  # Nice sky blue
window.borderless = False
window.title = 'CATSDK\'s Paper Tech Demo'

# Isometric camera for a paper-like view
camera.orthographic = True  # Orthographic for true paper feel
camera.fov = 20  # Zoom level for orthographic
camera.position = (15, 15, -15)
camera.look_at((0,0,0))  # Look at origin
camera.rotation = (30, -45, 0)  # Standard isometric angles

# Try to fetch the player texture
if fetch_github_asset(GITHUB_MARIO_TEXTURE_URL, PLAYER_TEXTURE_FILENAME):
    player = PaperPlayer(texture_path=PLAYER_TEXTURE_FILENAME)
else:
    print("Meowr! Couldn't fetch the texture from GitHub. Using default player.")
    player = PaperPlayer()  # Player will use default red color

# Paper-style ground to prevent falling into the void
ground = Entity(
    model='plane',
    texture='grass',
    texture_scale=(20, 20),
    color=color.rgb(100, 180, 100),  # Greenish color
    scale=(40, 1, 40),
    collider='box',
    shader=basic_lighting_shader  # So it catches some light
)

# Paper-style obstacles: Goombas or similar
obstacles = []
for i in range(-5, 5, 2):
    obstacle = Entity(
        model='cube',  # Flat cube
        color=color.brown,  # Goomba-ish color
        scale=(1, 1, 0.1),  # Flat paper look
        position=(i * 2, 0.5, random.randint(-5, 5)),
        collider='box',
        shader=basic_lighting_shader,
        rotation_y=random.randint(0, 360)  # Random rotation for variety
    )
    obstacles.append(obstacle)

# Paper-style "Coins" to collect
coins = []
for i in range(5):
    coin = Entity(
        model='sphere',  # Could be a cylinder for coin shape or a quad with texture
        color=color.gold,
        scale=0.5,
        position=(random.uniform(-10, 10), 1, random.uniform(-10, 10)),
        collider='sphere',
        shader=basic_lighting_shader
    )
    # Make them spin
    coin.animate('rotation_y', coin.rotation_y + 360, duration=2, loop=True, curve=curve.linear)
    coins.append(coin)

# Simple lighting for visibility
pivot = Entity()  # For rotating the light
DirectionalLight(parent=pivot, y=2, z=3, shadows=True, rotation=(45, -45, 45))

# Optional: Sky
sky = Sky()

# Optional: Editor Camera for debugging
# editor_camera = EditorCamera(enabled=False, ignore_paused=True)

# def input(key):
#     if key == 'tab':  # Press Tab to toggle editor camera
#         editor_camera.enabled = not editor_camera.enabled

print("Purr... Ursina app is ready to run! Move with WASD, jump with SPACE. Have fun!")
app.run()

from ursina import *
from ursina.shaders import basic_lighting_shader
import requests  # For downloading assets from GitHub
import os  # For handling file paths

# --- GitHub Asset Fetching ---
# Provide a direct raw image URL here, such as a character sprite.
# For example: https://raw.githubusercontent.com/your_username/your_repo/main/mario_texture.png
# If the URL is invalid or the download fails, the player will use a default color.
GITHUB_MARIO_TEXTURE_URL = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/25.png'  # Using Pikachu as a placeholder
PLAYER_TEXTURE_FILENAME = 'downloaded_player_texture.png'

def fetch_github_asset(url, filename):
    """Attempts to download an asset from GitHub. Returns True on success, False on failure."""
    try:
        print(f"Attempting to download '{url}'...")
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raises an HTTPError for unsuccessful status codes
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Successfully downloaded and saved as '{filename}'.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to download the asset from '{url}'. Error: {e}")
        return False

# --- Player Class ---
class PaperPlayer(Entity):
    def __init__(self, texture_path=None, **kwargs):
        super().__init__(
            model='quad',  # Using quad for a flat paper look; can also be 'cube' with tiny z-scale
            collider='box',
            scale=(1.5, 2, 1),  # Adjust as needed for your sprite
            position=(0, 1, 0),  # Start player slightly above ground
            shader=basic_lighting_shader,  # Basic lighting for visual depth
            **kwargs
        )
        
        if texture_path and os.path.exists(texture_path):
            self.texture = load_texture(texture_path.split(os.sep)[-1], path=os.path.dirname(texture_path))
            self.color = color.white  # Ensure texture displays clearly
            print(f"Player texture '{texture_path}' loaded successfully!")
        else:
            self.color = color.red  # Fallback color if no texture is available
            print(f"Player texture not found or failed to load. Using default red color.")

        # Movement and Jump Attributes
        self.speed = 5
        self.gravity_force = 0.4  # Strength of gravity
        self.jump_height = 0.3    # Maximum jump height
        self.jumping = False
        self.air_time = 0         # Duration in the air
        self.grounded = False     # Whether the player is on the ground

    def update(self):
        # Movement
        self.x += (held_keys['d'] - held_keys['a']) * self.speed * time.dt
        self.z += (held_keys['w'] - held_keys['s']) * self.speed * time.dt

        # Simple Billboard Effect - player faces camera approximately for paper effect
        # Only rotate around Y axis to keep it upright
        if camera.world_rotation_y != self.world_rotation_y:
            self.world_rotation_y = camera.world_rotation_y
        
        # Jumping
        if self.grounded and held_keys['space']:
            self.jumping = True
            self.grounded = False
            self.air_time = 0
            # Initial upward velocity impulse
            self.y += self.jump_height 
            print("Jump initiated!")

        if not self.grounded:
            self.y -= self.gravity_force * time.dt * 25  # Apply gravity, 25 is an arbitrary multiplier
            self.air_time += time.dt

            # Check for ground collision (basic, assumes ground at y=0)
            ground_check = raycast(self.world_position, self.down, distance=self.scale_y/2 + 0.1, ignore=[self,])
            
            if ground_check.hit:
                if self.y <= ground_check.world_point[1] + self.scale_y/2:  # Prevent sinking
                    self.y = ground_check.world_point[1] + self.scale_y/2
                    self.grounded = True
                    self.jumping = False
                    self.air_time = 0
                    # print("Landed!")  # Optional, can be spammy
            elif self.y < 0.5:  # Fallback minimum height if raycast fails
                self.y = 0.5
                self.grounded = True
                self.jumping = False
                self.air_time = 0
                # print("Landed by fallback!")  # Optional

        # Collision with obstacles and coins
        hit_info = self.intersects()
        if hit_info.hit:
            if hit_info.entity in obstacles:
                print("Collided with an obstacle!")
                destroy(hit_info.entity)
                obstacles.remove(hit_info.entity)
                # Visual feedback
                self.blink(color.orange, duration=0.2)
            elif hit_info.entity in coins:
                print("Collected a coin!")
                destroy(hit_info.entity)
                coins.remove(hit_info.entity)
                # Additional scoring logic can be added here

# --- Main App Setup ---
app = Ursina(development_mode=True)

# Paper Mario style settings
window.color = color.rgb(135, 206, 250)  # Sky blue background
window.borderless = False
window.title = 'Paper Tech Demo'

# Isometric camera setup
camera.orthographic = True  # Orthographic for a paper-like feel
camera.fov = 20  # Zoom level for orthographic view
camera.position = (15, 15, -15)
camera.look_at((0, 0, 0))  # Focus on origin
camera.rotation = (30, -45, 0)  # Standard isometric angles

# Attempt to fetch the player texture
if fetch_github_asset(GITHUB_MARIO_TEXTURE_URL, PLAYER_TEXTURE_FILENAME):
    player = PaperPlayer(texture_path=PLAYER_TEXTURE_FILENAME)
else:
    print("Failed to retrieve texture from GitHub. Using default player appearance.")
    player = PaperPlayer()  # Player will use default red color

# Paper-style ground
ground = Entity(
    model='plane',
    texture='grass',
    texture_scale=(20, 20),
    color=color.rgb(100, 180, 100),  # Greenish tint
    scale=(40, 1, 40),
    collider='box',
    shader=basic_lighting_shader  # Apply lighting
)

# Paper-style obstacles
obstacles = []
for i in range(-5, 5, 2):
    obstacle = Entity(
        model='cube',  # Flat cube for paper effect
        color=color.brown,  # Brown for obstacle color
        scale=(1, 1, 0.1),  # Flat appearance
        position=(i * 2, 0.5, random.randint(-5, 5)),
        collider='box',
        shader=basic_lighting_shader,
        rotation_y=random.randint(0, 360)  # Random rotation for variety
    )
    obstacles.append(obstacle)

# Paper-style coins to collect
coins = []
for i in range(5):
    coin = Entity(
        model='sphere',  # Sphere for coin shape
        color=color.gold,
        scale=0.5,
        position=(random.uniform(-10, 10), 1, random.uniform(-10, 10)),
        collider='sphere',
        shader=basic_lighting_shader
    )
    # Animate coin spinning
    coin.animate('rotation_y', coin.rotation_y + 360, duration=2, loop=True, curve=curve.linear)
    coins.append(coin)

# Simple lighting setup
pivot = Entity()  # For light rotation
DirectionalLight(parent=pivot, y=2, z=3, shadows=True, rotation=(45, -45, 45))

# Optional: Sky
sky = Sky()

# Optional: Editor Camera for debugging
# editor_camera = EditorCamera(enabled=False, ignore_paused=True)

# def input(key):
#     if key == 'tab':  # Press Tab to toggle editor camera
#         editor_camera.enabled = not editor_camera.enabled

print("Ursina app is ready to run! Move with WASD, jump with SPACE.")
app.run()

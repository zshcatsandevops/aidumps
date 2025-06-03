from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from math import sin, cos, pi, radians, acos, dot, cross
import random
import time

# --------------------------------------------------
# 🚀 Optimized Engine Bootstrap
# --------------------------------------------------
app = Ursina(
    vsync=False,
    development_mode=False,
    size=(640, 480)
window.title = "B3313 Engine - Comet Observatory"
window.borderless = False
window.fullscreen = False
window.color = color.rgb(8, 10, 22)

# --------------------------------------------------
# 🎯 Performance Configuration
# --------------------------------------------------
window.fps_counter.enabled = True
window.fps_counter.position = (0, .45)
window.fps_counter.scale *= 0.7

# --------------------------------------------------
# 🎨 Optimized Color Palette
# --------------------------------------------------
OBS_COLOR = color.rgba(210, 230, 255, 255)
ENGINE_COL = color.rgba(90, 90, 160, 240)
GLASS_COL = color.rgba(160, 220, 255, 120)
STAR_COLOR = color.yellow
DOME_RED = color.rgba(200, 50, 50)
DOME_GREEN = color.rgba(50, 150, 50)
METAL_COLOR = color.rgba(100, 100, 100)
ENERGY_COLOR = color.rgba(100, 150, 255)

# --------------------------------------------------
# 🌍 Fixed Spherical Gravity Controller
# --------------------------------------------------
GRAVITY_STRENGTH = 15
SURFACE_R = 32

class GalaxyPlayer(Entity):
    def __init__(self, **kwargs):
        super().__init__(
            model='sphere',
            color=color.azure,
            scale=0.8,
            collider='sphere',
            **kwargs
        )
        self.speed = 7
        self.jump_height = 4
        self.velocity = Vec3(0, 0, 0)
        self.cursor = Cursor()
        self.cursor.visible = False
        
        # Camera setup
        self.camera_pivot = Entity(parent=self)
        self.camera = Camera(parent=self.camera_pivot)
        self.camera.position = (0, 1.8, 0)
        self.camera.fov = 80
        self.camera_rotation_speed = 150
        self.min_camera_x = -80
        self.max_camera_x = 80
        
        # Player state
        self.grounded = False
        self.rotation_speed = 200

    def update(self):
        # Camera rotation with mouse
        self.camera_pivot.rotation_x -= mouse.velocity[1] * self.camera_rotation_speed * time.dt
        self.camera_pivot.rotation_x = clamp(self.camera_pivot.rotation_x, self.min_camera_x, self.max_camera_x)
        self.rotation_y += mouse.velocity[0] * self.camera_rotation_speed * time.dt

        # Movement direction relative to camera
        direction = Vec3(
            self.forward * (held_keys['w'] - held_keys['s']),
            0,
            self.right * (held_keys['d'] - held_keys['a'])
        ).normalized() * self.speed

        # Apply spherical gravity
        to_center = -self.position.normalized()
        gravity_force = to_center * GRAVITY_STRENGTH
        
        # Jumping
        if self.grounded and held_keys['space']:
            self.velocity += to_center * self.jump_height
        
        # Update velocity
        self.velocity += direction * time.dt + gravity_force * time.dt
        
        # Apply damping when grounded
        if self.grounded:
            self.velocity *= 0.85
        
        # Update position
        self.position += self.velocity * time.dt
        
        # Constrain to sphere surface
        distance = self.position.length()
        if distance > SURFACE_R - 0.1:
            self.position = self.position.normalized() * SURFACE_R
            surface_normal = self.position.normalized()
            self.grounded = distance < SURFACE_R + 0.2
            
            # Align player's up with surface normal using quaternion
            up = Vec3(0, 1, 0)
            dot_product = dot(up, surface_normal)
            if abs(dot_product) < 0.9999:  # Not parallel or exactly opposite
                axis = cross(up, surface_normal).normalized()
                angle = acos(dot_product)
                w = cos(angle / 2)
                v = axis * sin(angle / 2)
                q = Quat(w, v.x, v.y, v.z)
            else:
                if dot_product > 0:  # Parallel, no rotation needed
                    q = Quat()
                else:  # Opposite, 180-degree rotation around x-axis
                    q = Quat(0, 1, 0, 0)
            self.rotation = q
        else:
            self.grounded = False

# --------------------------------------------------
# 🌌 Optimized Starfield
# --------------------------------------------------
window.color = color.rgb(5, 5, 15)
star_positions = [Vec3(random.uniform(-100, 100), 
                  random.uniform(-100, 100), 
                  random.uniform(-100, 100)) for _ in range(100)]
star_entity = Entity(model=Mesh(vertices=star_positions, mode='point'), 
                     texture='white_cube', 
                     color=color.white, 
                     scale=1.2)

# --------------------------------------------------
# 🪐 Optimized Observatory Planetoid
# --------------------------------------------------
def create_lowpoly_sphere(segments=8):
    verts = []
    tris = []
    for i in range(segments + 1):
        lat = pi * i / segments
        for j in range(segments):
            lon = 2 * pi * j / segments
            x = sin(lat) * cos(lon)
            y = cos(lat)
            z = sin(lat) * sin(lon)
            verts.append(Vec3(x, y, z))
    for i in range(segments):
        for j in range(segments):
            a = i * (segments + 1) + j
            b = a + 1
            c = (i + 1) * (segments + 1) + j
            d = c + 1
            tris.extend([(a, c, b), (b, c, d)])
    return Mesh(vertices=verts, triangles=tris, mode='triangle')

lowpoly_sphere = create_lowpoly_sphere(segments=8)
main_floor = Entity(model=lowpoly_sphere, scale=SURFACE_R * 2, 
                    color=OBS_COLOR, texture='white_cube', 
                    double_sided=True)

# Decorative cubes
decor_cubes = []
for i in range(8):
    angle = i * (360 / 8)
    pos = Vec3(28 * cos(radians(angle)), 1.5, 28 * sin(radians(angle)))
    cube = Entity(model='cube', color=color.gray(0.3), 
                 scale=(1.5, 0.8, 1.5), position=pos, 
                 rotation=(0, angle, 0))
    decor_cubes.append(cube)

# --------------------------------------------------
# 🔴🟢🔵 Optimized Domes
# --------------------------------------------------
def create_dome(position, dome_color):
    return Entity(model=lowpoly_sphere, color=dome_color, 
                 scale=3, position=position, texture='white_cube')

dome_red = create_dome((16, 0, 0), DOME_RED)
dome_green = create_dome((-16, 0, 0), DOME_GREEN)
dome_cyan = create_dome((0, 0, 16), color.cyan)

# --------------------------------------------------
# ⚡ Optimized Warp Pads
# --------------------------------------------------
def create_warp_pad(position, glow_color):
    return Entity(model='cylinder', color=glow_color, 
                 scale=(1.8, 0.4, 1.8), position=position)

warp_red = create_warp_pad(dome_red.position + Vec3(0, 1, 0), DOME_RED)
warp_green = create_warp_pad(dome_green.position + Vec3(0, 1, 0), DOME_GREEN)
warp_cyan = create_warp_pad(dome_cyan.position + Vec3(0, 1, 0), color.cyan)

# --------------------------------------------------
# ⭐ Optimized Central Star
# --------------------------------------------------
star_npc = Entity(model=lowpoly_sphere, color=STAR_COLOR, 
                 scale=1, position=(0, 6, 0), texture='white_cube')

# --------------------------------------------------
# 🔧 Optimized Engine Room
# --------------------------------------------------
en_base = Entity(model='cylinder', color=ENGINE_COL, 
                scale=(7, 0.8, 7), position=(0, -2, -20))
en_core = Entity(model='cylinder', color=color.gray(0.3), 
                scale=(1.8, 5, 1.8), position=(0, 2, -20))

# Engine supports
engine_supports = []
for ang in range(0, 360, 60):
    pos = Vec3(0, 2, -20)
    rot = (0, ang, 0)
    scale = (0.3, 0.3, 6)
    support = Entity(model='cube', color=color.gray(0.25), 
                    scale=scale, position=pos, rotation=rot)
    engine_supports.append(support)

# Energy nodes
energy_nodes = []
for i in range(5):
    theta = i * (2 * pi / 5)
    x = 5 * cos(theta)
    z = -20 + 5 * sin(theta)
    node = Entity(model=lowpoly_sphere, color=ENERGY_COLOR, 
                 scale=0.4, position=(x, 2.7, z), texture='white_cube')
    energy_nodes.append(node)

# --------------------------------------------------
# 🎮 Player Setup
# --------------------------------------------------
player = GalaxyPlayer()
player.position = (0, SURFACE_R, 0)

# --------------------------------------------------
# 🌀 Optimized Animation System
# --------------------------------------------------
star_pulse = 0
node_pulses = [0] * len(energy_nodes)

def update():
    global star_pulse, node_pulses
    t = time.time()
    star_pulse = sin(t * 2) * 0.15
    star_npc.scale = 1 + star_pulse
    for i, node in enumerate(energy_nodes):
        node_pulses[i] = sin(t * 3 + i) * 0.08
        node.scale = 0.4 + node_pulses[i]

# --------------------------------------------------
# 💡 Optimized Lighting
# --------------------------------------------------
DirectionalLight(direction=(1, -2, -1), shadows=False)
AmbientLight(color=color.rgba(80, 80, 120, 100))

# --------------------------------------------------
# 🌐 Zone Management
# --------------------------------------------------
current_zone = "observatory"

def load_zone(zone: str):
    print(f"Loading zone: {zone}")
    # Zone loading logic would go here
    if zone == "engine_room":
        # Show engine room, hide observatory
        en_base.enabled = True
        en_core.enabled = True
        for support in engine_supports:
            support.enabled = True
        for node in energy_nodes:
            node.enabled = True
        
        main_floor.enabled = False
        for cube in decor_cubes:
            cube.enabled = False
        dome_red.enabled = False
        dome_green.enabled = False
        dome_cyan.enabled = False
        warp_red.enabled = False
        warp_green.enabled = False
        warp_cyan.enabled = False
        star_npc.enabled = False
        
    else:  # observatory
        # Show observatory, hide engine room
        main_floor.enabled = True
        for cube in decor_cubes:
            cube.enabled = True
        dome_red.enabled = True
        dome_green.enabled = True
        dome_cyan.enabled = True
        warp_red.enabled = True
        warp_green.enabled = True
        warp_cyan.enabled = True
        star_npc.enabled = True
        
        en_base.enabled = False
        en_core.enabled = False
        for support in engine_supports:
            support.enabled = False
        for node in energy_nodes:
            node.enabled = False

# --------------------------------------------------
# ⌨️ Input Handler
# --------------------------------------------------
def input(key):
    # Zone switching
    if key == '1':
        load_zone("observatory")
    elif key == '2':
        load_zone("engine_room")
    
    # Warp pad teleportation
    if key == 'e':
        for warp in [warp_red, warp_green, warp_cyan]:
            if distance(player.position, warp.position) < 3:
                if warp == warp_red:
                    player.position = Vec3(16, SURFACE_R, 0)
                elif warp == warp_green:
                    player.position = Vec3(-16, SURFACE_R, 0)
                elif warp == warp_cyan:
                    player.position = Vec3(0, SURFACE_R, 16)
                player.velocity = Vec3(0, 0, 0)
                break

# --------------------------------------------------
# 🚀 Launch Optimized Demo
# --------------------------------------------------
print("Controls:")
print("WASD - Move | Mouse - Look | SPACE - Jump")
print("1 - Observatory | 2 - Engine Room")
print("E - Use warp pads (stand near one and press E)")
print("Optimized for stable 60 FPS galaxy experience")

# Initial zone load
load_zone(current_zone)

app.run()

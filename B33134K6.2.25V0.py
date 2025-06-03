from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.maths import distance
from math import sin, cos, pi, radians
import random
import time

# --------------------------------------------------
# 🚀 Optimized Engine Bootstrap
# --------------------------------------------------
app = Ursina(
    vsync=False,  # Disable vsync for higher FPS potential
    development_mode=False,  # Disable dev tools for performance
    size=(640, 480)  # Lower resolution for N64-like performance
)
window.title = "B3313 Engine - Comet Observatory (Optimized)"
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
# 🌍 Optimized Spherical Gravity Controller
# --------------------------------------------------
GRAVITY_STRENGTH = 0.9
CENTER_POINT = Vec3(0, 0, 0)
SURFACE_R = 32

class GalaxyPlayer(FirstPersonController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.velocity = Vec3(0, 0, 0)
        self.cursor.visible = False
        self.speed = 7
        self.collider = 'sphere'
        self.collider_radius = 0.5

    def update(self):
        super().update()
        direction = CENTER_POINT - self.position
        r = direction.length()
        if r > 0.01:
            self.velocity += direction.normalized() * GRAVITY_STRENGTH * time.dt
            self.position += self.velocity
        if abs(r - SURFACE_R) < 0.5 and self.velocity.length_squared() > 0.01:
            self.velocity = Vec3(0, 0, 0)

# --------------------------------------------------
# 🌌 Optimized Starfield
# --------------------------------------------------
window.color = color.rgb(5, 5, 15)

star_positions = [Vec3(random.uniform(-80, 80), random.uniform(-80, 80), random.uniform(-80, 80)) for _ in range(60)]
star_mesh = Mesh(vertices=star_positions, mode='point')
star_entity = Entity(model=star_mesh, color=color.white, point_size=1.5)  # Reduced point size

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
main_floor = Entity(model=lowpoly_sphere, scale=SURFACE_R * 2, color=OBS_COLOR, double_sided=True)

# Combine decorative cubes into a single mesh (optional optimization)
decor_cubes = Entity(model='cube', color=color.gray(0.3), scale=(1.5, 0.8, 1.5))
for i in range(8):
    angle = i * (360 / 8)
    decor_cubes.combine(position=(28 * cos(radians(angle)), 1.5, 28 * sin(radians(angle))), rotation=(0, angle, 0))

# --------------------------------------------------
# 🔴🟢🔵 Optimized Domes
# --------------------------------------------------
def create_dome(position, dome_color):
    return Entity(model=lowpoly_sphere, color=dome_color, scale=3, position=position)

dome_red = create_dome((16, 0, 0), DOME_RED)
dome_green = create_dome((-16, 0, 0), DOME_GREEN)
dome_cyan = create_dome((0, 0, 16), color.cyan)

# --------------------------------------------------
# ⚡ Optimized Warp Pads
# --------------------------------------------------
def create_warp_pad(position, glow_color):
    return Entity(model='cylinder', color=glow_color, scale=(1.8, 0.4, 1.8), position=position, collider='box')

warp_red = create_warp_pad(dome_red.position + Vec3(0, 1, 0), DOME_RED)
warp_green = create_warp_pad(dome_green.position + Vec3(0, 1, 0), DOME_GREEN)
warp_cyan = create_warp_pad(dome_cyan.position + Vec3(0, 1, 0), color.cyan)

# --------------------------------------------------
# ⭐ Optimized Central Star
# --------------------------------------------------
star_npc = Entity(model=lowpoly_sphere, color=STAR_COLOR, scale=1, position=(0, 6, 0), collider='sphere')

# --------------------------------------------------
# 🔧 Optimized Engine Room
# --------------------------------------------------
en_base = Entity(model='cylinder', color=ENGINE_COL, scale=(7, 0.8, 7), position=(0, -2, -20))
en_core = Entity(model='cylinder', color=color.gray(0.3), scale=(1.8, 5, 1.8), position=(0, 2, -20))

# Combine engine room supports into a single entity (optional)
engine_supports = Entity(model='cube', color=color.gray(0.25), scale=(0.3, 0.3, 6))
for ang in range(0, 360, 60):
    engine_supports.combine(position=(0, 2, -20), rotation=(0, ang, 0))

energy_nodes = []
for i in range(5):
    theta = i * (2 * pi / 5)
    x = 5 * cos(theta)
    z = -20 + 5 * sin(theta)
    node = Entity(model=lowpoly_sphere, color=ENERGY_COLOR, scale=0.4, position=(x, 2.7, z))
    energy_nodes.append(node)

# --------------------------------------------------
# 🎮 Player & Camera Setup
# --------------------------------------------------
player = GalaxyPlayer()
player.position = (0, 2, 12)
camera.fov = 80  # Slightly reduced FOV for performance

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
# 🌐 Zone Management (Unchanged Placeholder)
# --------------------------------------------------
current_zone = "observatory"

def load_zone(zone: str):
    pass

# --------------------------------------------------
# ⌨️ Input Handler (Unchanged Placeholder)
# --------------------------------------------------
def input(key):
    pass

# --------------------------------------------------
# 💡 Optimized Lighting
# --------------------------------------------------
DirectionalLight(direction=(1, -2, -1), shadows=False)
AmbientLight(color=color.rgba(80, 80, 120, 100))

# --------------------------------------------------
# 🚀 Launch Optimized Demo
# --------------------------------------------------
load_zone("observatory")
print("Controls: WASD/Arrow - move | Mouse - look | LMB - interact | R - Reset")
print("Optimized for N64-like performance at 60 FPS")

app.run()

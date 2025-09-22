"""
UrsinaCraft (Minimal) — Minecraft‑like sandbox in Ursina 1.0
- Left click: place selected block
- Right click: remove block
- Scroll / 1..6: change block type
- WASD + Space/Shift: move/jump/sprint (FirstPersonController)

Notes:
- Uses only built‑in 'white_cube' texture + solid colors (no external assets).
- Pygame is optional and not used by default; imported safely if available.
"""

# Optional import requested by user. Safe fallback if not installed.
try:
    import pygame  # noqa: F401  (imported by request; not required for Ursina)
except Exception:
    pygame = None

from random import randint
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController


# ---------- App & Window ----------
app = Ursina()
window.title = 'UrsinaCraft (Minimal)'
window.borderless = False
window.fps_counter.enabled = True


# ---------- Block Catalog ----------
# Solid-color "textures" using the built-in white cube.
BLOCK_ORDER = ['grass', 'stone', 'dirt', 'wood', 'brick', 'glass']

BLOCK_COLOR = {
    'grass': color.rgb(106, 190, 48),       # greenish
    'stone': color.rgb(130, 130, 130),      # gray
    'dirt' : color.rgb(120, 72, 48),        # brown
    'wood' : color.rgb(166, 124, 82),       # tan
    'brick': color.rgb(178, 34, 34),        # red
    'glass': color.rgba(220, 240, 255, 110) # translucent
}

_current_block_index = 0
def current_block_name() -> str:
    return BLOCK_ORDER[_current_block_index]


# ---------- UI ----------
block_label = Text(
    text=f'Block: {current_block_name().upper()}  [Scroll or 1..6]',
    position=window.top_left + Vec2(0.02, -0.02),
    origin=(0, 0),
    scale=0.9,
    background=True
)

def _refresh_block_label():
    block_label.text = f'Block: {current_block_name().upper()}  [Scroll or 1..6]'


# ---------- Voxel ----------
class Voxel(Button):
    def __init__(self, position=(0, 0, 0), block_type: str = 'grass'):
        self.block_type = block_type

        # Color (with alpha for glass)
        col = BLOCK_COLOR.get(block_type, color.white)

        super().__init__(
            parent=scene,
            model='cube',
            texture='white_cube',
            color=col,
            position=position,
            origin_y=0.5,
            collider='box',
            highlight_color=color.white
        )

    def input(self, key):
        # Handle placing/removing when the cursor is hovering this voxel
        if self.hovered:
            if key == 'left mouse down':
                # Place a new block flush with the face you're pointing at
                Voxel(position=self.position + mouse.normal, block_type=current_block_name())
            elif key == 'right mouse down':
                # Remove this block
                destroy(self)


# ---------- World Generation ----------
def generate_chunk(size=16, max_h=3, seed=None):
    if seed is not None:
        random.seed(seed)

    half = size // 2
    for x in range(-half, half):
        for z in range(-half, half):
            h = randint(1, max_h)  # 1..max_h layers tall
            for y in range(h):
                top = (y == h - 1)
                bt = 'grass' if top else 'dirt'
                Voxel(position=(x, y, z), block_type=bt)


# ---------- Player, Sky ----------
Sky()  # built-in skybox
player = FirstPersonController(y=8, speed=6)  # spawn above ground
generate_chunk(size=24, max_h=3)


# ---------- Global Input ----------
def input(key):
    global _current_block_index

    # Number keys 1..6 select block type directly
    if key in ('1','2','3','4','5','6'):
        idx = int(key) - 1
        if 0 <= idx < len(BLOCK_ORDER):
            _current_block_index = idx
            _refresh_block_label()

    # Mouse wheel cycles block types
    if key == 'scroll up':
        _current_block_index = (_current_block_index - 1) % len(BLOCK_ORDER)
        _refresh_block_label()
    elif key == 'scroll down':
        _current_block_index = (_current_block_index + 1) % len(BLOCK_ORDER)
        _refresh_block_label()

    # Quick quit
    if key == 'escape':
        application.quit()


if __name__ == '__main__':
    app.run()

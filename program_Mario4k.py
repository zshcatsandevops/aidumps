#!/usr/bin/env python3
"""
sm64_vibe.py: Super Mario 64 Vibe in Python (no media assets, 60 FPS)
- Move with arrow keys/WASD, jump with Space.
- No external assets, all code in one file.
- All textures procedurally generated.
"""

import pygame
import numpy as np
import random
from ursina import Ursina, Entity, color, Vec3, window, application, Texture, held_keys, time
from ursina.shaders import lit_with_shadows_shader
from ursina import scene, camera

# --- Settings ---
SCREEN_SIZE = (640, 480)
FPS = 60

# --- Procedural Texture Generation ---
def create_texture(width, height, func):
    """Create a texture using a function that takes x,y coordinates and returns RGB."""
    pixels = np.zeros((height, width, 4), dtype=np.uint8)
    for y in range(height):
        for x in range(width):
            r, g, b, a = func(x/width, y/height)
            pixels[y, x] = [r, g, b, a]
    return Texture(pixels)

# --- Texture Generators ---
def mario_texture(x, y):
    """Generate Mario-like texture (red overall, blue pants, etc.)"""
    # Red overall
    r, g, b = 220, 40, 40
    a = 255
    
    # Blue pants (bottom third)
    if y > 0.6:
        r, g, b = 40, 40, 200
    
    # Face area (top part)
    if y < 0.3:
        # Skin tone
        r, g, b = 255, 200, 160
        
        # Eyes (two black dots)
        eye_size = 0.05
        if y < 0.2 and (0.3 < x < 0.3 + eye_size or 0.6 < x < 0.6 + eye_size):
            r, g, b = 0, 0, 0
            
        # Mustache (black rectangle)
        if 0.2 < y < 0.25 and 0.3 < x < 0.7:
            r, g, b = 0, 0, 0
            
    # Cap (red with M)
    if y < 0.1:
        r, g, b = 220, 40, 40
        # M on cap
        if 0.45 < x < 0.55 and y < 0.08:
            r, g, b = 255, 255, 255
    
    return r, g, b, a

def ground_texture(x, y):
    """Generate ground texture (grass-like)"""
    # Base green color
    r, g, b = 60, 180, 60
    a = 255
    
    # Add some variation
    noise = (np.sin(x*20) * np.cos(y*20) * 20) + (np.sin(x*5) * np.cos(y*5) * 10)
    g += int(noise)
    
    # Add some darker patches
    if (x*10 % 1 < 0.1) or (y*10 % 1 < 0.1):
        r -= 20
        g -= 20
        b -= 20
    
    return r, g, b, a

def brick_texture(x, y):
    """Generate brick texture"""
    # Base brick color
    r, g, b = 180, 100, 60
    a = 255
    
    # Brick pattern
    brick_w, brick_h = 0.2, 0.1
    mortar_w, mortar_h = 0.01, 0.01
    
    # Offset every other row
    row = int(y / (brick_h + mortar_h))
    offset = 0.5 * (row % 2)
    
    # Check if we're on mortar
    x_mod = (x + offset) % (brick_w + mortar_w)
    y_mod = y % (brick_h + mortar_h)
    
    if x_mod < mortar_w or y_mod < mortar_h:
        r, g, b = 150, 150, 150  # Mortar color
    
    return r, g, b, a

def question_block_texture(x, y):
    """Generate question block texture"""
    # Base yellow color
    r, g, b = 220, 220, 40
    a = 255
    
    # Border
    border = 0.1
    if x < border or x > 1-border or y < border or y > 1-border:
        r, g, b = 180, 100, 40  # Brown border
    
    # Question mark
    if 0.4 < x < 0.6 and 0.3 < y < 0.7:
        r, g, b = 180, 100, 40  # Brown question mark
    if 0.4 < x < 0.6 and 0.6 < y < 0.7:
        r, g, b = 180, 100, 40
    if 0.5 < x < 0.6 and 0.5 < y < 0.7:
        r, g, b = 180, 100, 40
    if 0.4 < x < 0.6 and 0.3 < y < 0.4:
        r, g, b = 180, 100, 40
    
    # Add some shine
    if 0.8 < x < 0.9 and 0.1 < y < 0.2:
        r, g, b = 255, 255, 255
    
    return r, g, b, a

def coin_texture(x, y):
    """Generate coin texture"""
    # Base gold color
    r, g, b = 255, 215, 0
    a = 255
    
    # Make it circular
    dx, dy = x - 0.5, y - 0.5
    dist = (dx*dx + dy*dy) ** 0.5
    
    if dist > 0.4:  # Outside the circle
        return 0, 0, 0, 0  # Transparent
    
    # Add some shine
    if dist < 0.3 and x > 0.5 and y < 0.5:
        r, g, b = 255, 255, 200
    
    return r, g, b, a

def sky_texture(x, y):
    """Generate sky texture with clouds"""
    # Base sky blue
    r, g, b = 135, 206, 235
    a = 255
    
    # Gradient (darker at top)
    b += int((1-y) * 20)
    
    # Clouds
    cloud_density = 0.3
    for i in range(5):  # 5 cloud centers
        cx, cy = (i*0.2 + 0.1) % 1, 0.2 + 0.1 * np.sin(i*2)
        dx, dy = x - cx, y - cy
        dist = (dx*dx*4 + dy*dy) ** 0.5  # Elliptical clouds
        
        if dist < 0.2:
            cloud_factor = 1 - dist/0.2
            cloud_factor *= cloud_density
            r = int(r * (1-cloud_factor) + 255 * cloud_factor)
            g = int(g * (1-cloud_factor) + 255 * cloud_factor)
            b = int(b * (1-cloud_factor) + 255 * cloud_factor)
    
    return r, g, b, a

def water_texture(x, y):
    """Generate water texture"""
    # Base water blue
    r, g, b = 64, 164, 223
    a = 200  # Semi-transparent
    
    # Add some wave patterns
    wave = np.sin(x*20 + y*10) * 20
    b += int(wave)
    g += int(wave * 0.5)
    
    return r, g, b, a

# --- Mario-like Player Entity ---
class Mario(Entity):
    def __init__(self, **kwargs):
        # Generate Mario texture
        mario_tex = create_texture(64, 64, mario_texture)
        
        super().__init__(
            model='cube',
            texture=mario_tex,
            scale=(0.8, 1.2, 0.8),
            position=(0, 2, 0),
            collider='box',
            shader=lit_with_shadows_shader,
            **kwargs
        )
        self.velocity = Vec3(0, 0, 0)
        self.speed = 5
        self.jump_power = 8
        self.grounded = False
        self.coins = 0
        self.facing = Vec3(0, 0, 1)  # Forward direction

    def update(self):
        # Simple gravity
        self.velocity.y -= 20 * time.dt
        
        # Movement direction
        move_dir = Vec3(
            held_keys['d'] - held_keys['a'],
            0,
            held_keys['w'] - held_keys['s']
        )
        
        # Only update facing if we're moving
        if move_dir.length() > 0.1:
            self.facing = move_dir.normalized()
            # Rotate to face movement direction
            target_angle = np.degrees(np.arctan2(self.facing.x, self.facing.z))
            self.rotation_y = target_angle
        
        # Apply movement
        move = self.facing * move_dir.length() * self.speed * time.dt
        self.position += move
        
        # Apply vertical velocity
        self.y += self.velocity.y * time.dt
        
        # Ground collision
        if self.y < 1:
            self.y = 1
            self.velocity.y = 0
            self.grounded = True
        else:
            self.grounded = False
            
        # Collect coins
        for coin in [e for e in scene.entities if hasattr(e, 'coin') and e.coin]:
            if (self.position - coin.position).length() < 1:
                self.coins += 1
                print(f"Coins: {self.coins}")
                coin.disable()

    def input(self, key):
        if key == 'space' and self.grounded:
            self.velocity.y = self.jump_power

# --- Coin Entity ---
class Coin(Entity):
    def __init__(self, position, **kwargs):
        coin_tex = create_texture(32, 32, coin_texture)
        super().__init__(
            model='quad',
            texture=coin_tex,
            position=position,
            scale=0.5,
            billboard=True,  # Always face camera
            shader=lit_with_shadows_shader,
            **kwargs
        )
        self.coin = True
        
        # Floating animation
        self.original_y = position.y
        self.spin_speed = 2
        
    def update(self):
        # Spin and bob
        self.rotation_y += 100 * time.dt
        self.y = self.original_y + np.sin(time.time() * self.spin_speed) * 0.1

# --- Question Block ---
class QuestionBlock(Entity):
    def __init__(self, position, **kwargs):
        question_tex = create_texture(32, 32, question_block_texture)
        super().__init__(
            model='cube',
            texture=question_tex,
            position=position,
            scale=1,
            collider='box',
            shader=lit_with_shadows_shader,
            **kwargs
        )
        self.hit = False
        self.original_y = position.y
        
    def update(self):
        # Bob slightly
        if not self.hit:
            self.y = self.original_y + np.sin(time.time() * 2) * 0.05
            
        # Check for collision with Mario from below
        mario = next((e for e in scene.entities if isinstance(e, Mario)), None)
        if mario and not self.hit:
            if (abs(mario.x - self.x) < 1 and 
                abs(mario.z - self.z) < 1 and
                0 < self.y - mario.y < 1.5 and
                mario.velocity.y > 0):
                self.hit = True
                self.texture = create_texture(32, 32, brick_texture)  # Change to brick texture
                # Spawn a coin
                Coin(position=Vec3(self.x, self.y + 1.5, self.z))

# --- Main ---
if __name__ == '__main__':
    # Pygame for input (optional, Ursina can handle input)
    pygame.init()
    pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption("SM64 Vibe Python")

    # Ursina app
    app = Ursina()
    window.title = "SM64 Vibe Python"
    window.borderless = False
    window.fps_counter.enabled = True
    window.size = SCREEN_SIZE

    # Sky
    sky = Entity(
        model='sphere',
        texture=create_texture(256, 256, sky_texture),
        scale=500,
        double_sided=True
    )

    # Ground
    ground = Entity(
        model='plane',
        texture=create_texture(128, 128, ground_texture),
        scale=(50, 1, 50),
        position=(0, 0, 0),
        collider='box',
        shader=lit_with_shadows_shader
    )
    
    # Water
    water = Entity(
        model='plane',
        texture=create_texture(128, 128, water_texture),
        scale=(100, 1, 100),
        position=(0, -0.5, 0),
        shader=lit_with_shadows_shader
    )

    # Create some blocks
    blocks = []
    for i in range(-5, 6, 2):
        for j in range(-5, 6, 2):
            if random.random() < 0.3:  # 30% chance of a block
                block = Entity(
                    model='cube',
                    texture=create_texture(32, 32, brick_texture),
                    position=(i, 0.5, j),
                    scale=1,
                    collider='box',
                    shader=lit_with_shadows_shader
                )
                blocks.append(block)
    
    # Question blocks
    for i in range(5):
        QuestionBlock(position=Vec3(i*2 - 4, 3, 0))
    
    # Coins
    for i in range(10):
        x = random.uniform(-10, 10)
        z = random.uniform(-10, 10)
        Coin(position=Vec3(x, 1, z))

    # Mario
    mario = Mario()

    # Camera
    camera.parent = mario
    camera.position = (0, 2, -5)
    camera.rotation_x = 10

    # Lighting
    from ursina.lights import DirectionalLight
    sun = DirectionalLight()
    sun.look_at(Vec3(1, -1, 1))
    
    # 60 FPS clock
    clock = pygame.time.Clock()

    # Ursina update loop
    @app.task
    def update_loop():
        dt = clock.tick(FPS) / 1000.0
        # Pygame event handling (for quit)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Instead of application.quit() (which can cause instant exit), set a flag
                global running_flag
                running_flag = False

    # Add a running flag to control the main loop
    global running_flag
    running_flag = True
    
    # Custom run loop to keep Ursina and Pygame alive until quit
    while running_flag:
        app.step()  # Advance Ursina one frame
    
    pygame.quit()

from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.shaders import lit_with_shadows_shader
import random
import json
import os
import math

# Initialize the game
app = Ursina()

# Game settings
window.title = "Yoshi's Story 3D - Enhanced Edition"
window.borderless = False
window.fullscreen = False
window.exit_button.visible = False
window.fps_counter.enabled = True

# Game state
game_state = "menu"
current_level = 0
score = 0
lives = 3
collected_fruits = 0
total_score = 0
combo_multiplier = 1
combo_timer = 0

# Create assets directory if it doesn't exist
if not os.path.exists('assets'):
    os.makedirs('assets')

# Colors
yoshi_green = color.rgb(102, 204, 0)
level_colors = [
    color.rgb(255, 153, 153),  # Level 1 - Pink
    color.rgb(153, 204, 255),  # Level 2 - Blue
    color.rgb(255, 204, 153),  # Level 3 - Orange
    color.rgb(204, 153, 255),  # Level 4 - Purple
    color.rgb(153, 255, 204),  # Level 5 - Green
]

# Game entities
yoshi = None
platforms = []
fruits = []
enemies = []
eggs = []
goal = None
moving_platforms = []
power_ups = []

# Sky
sky = Sky()

# Lighting
sun = DirectionalLight()
sun.look_at(Vec3(1, -1, -1))
ambient = AmbientLight(color=color.rgba(100, 100, 100, 0.2))

# UI elements
title_text = None
start_button = None
quit_button = None
score_text = None
lives_text = None
level_text = None
combo_text = None
game_over_text = None
restart_button = None
menu_button = None
win_text = None

# Sound effects (placeholder - you can add actual sound files)
def play_sound(sound_name):
    """Placeholder for sound effects"""
    print(f"Playing sound: {sound_name}")

# Level data with enhanced features
level_data = [
    {  # Level 1 - Introduction
        "platforms": [
            {"position": (0, 0, 0), "scale": (10, 1, 10), "color": level_colors[0]},
            {"position": (15, 2, 0), "scale": (5, 1, 5), "color": level_colors[0]},
            {"position": (25, 4, 0), "scale": (5, 1, 5), "color": level_colors[0]},
            {"position": (20, 1, 8), "scale": (4, 1, 4), "color": level_colors[0]},
        ],
        "moving_platforms": [
            {"position": (10, 3, 5), "scale": (3, 0.5, 3), "color": color.orange, "movement": "horizontal", "range": 5}
        ],
        "fruits": 12,
        "enemies": 2,
        "power_ups": 1,
        "goal": {"position": (28, 5, 0)}
    },
    {  # Level 2 - Vertical Challenge
        "platforms": [
            {"position": (0, 0, 0), "scale": (8, 1, 8), "color": level_colors[1]},
            {"position": (12, 2, 5), "scale": (6, 1, 6), "color": level_colors[1]},
            {"position": (5, 4, 12), "scale": (5, 1, 5), "color": level_colors[1]},
            {"position": (15, 6, 15), "scale": (7, 1, 7), "color": level_colors[1]},
            {"position": (-5, 8, 10), "scale": (4, 1, 4), "color": level_colors[1]},
        ],
        "moving_platforms": [
            {"position": (8, 5, 8), "scale": (3, 0.5, 3), "color": color.cyan, "movement": "vertical", "range": 3}
        ],
        "fruits": 18,
        "enemies": 4,
        "power_ups": 2,
        "goal": {"position": (18, 7, 15)}
    },
    {  # Level 3 - Spiral Tower
        "platforms": [
            {"position": (0, 0, 0), "scale": (10, 1, 10), "color": level_colors[2]},
            {"position": (0, 3, 15), "scale": (8, 1, 8), "color": level_colors[2]},
            {"position": (15, 6, 15), "scale": (6, 1, 6), "color": level_colors[2]},
            {"position": (15, 9, 0), "scale": (6, 1, 6), "color": level_colors[2]},
            {"position": (0, 12, 0), "scale": (8, 1, 8), "color": level_colors[2]},
            {"position": (0, 15, 15), "scale": (6, 1, 6), "color": level_colors[2]},
        ],
        "moving_platforms": [
            {"position": (7, 7, 7), "scale": (3, 0.5, 3), "color": color.yellow, "movement": "circular", "range": 5}
        ],
        "fruits": 25,
        "enemies": 5,
        "power_ups": 2,
        "goal": {"position": (0, 16, 15)}
    },
    {  # Level 4 - Platform Maze
        "platforms": [
            {"position": (0, 0, 0), "scale": (6, 1, 6), "color": level_colors[3]},
            {"position": (10, 3, 0), "scale": (5, 1, 5), "color": level_colors[3]},
            {"position": (0, 6, 10), "scale": (5, 1, 5), "color": level_colors[3]},
            {"position": (10, 9, 10), "scale": (5, 1, 5), "color": level_colors[3]},
            {"position": (0, 12, 20), "scale": (5, 1, 5), "color": level_colors[3]},
            {"position": (10, 15, 20), "scale": (5, 1, 5), "color": level_colors[3]},
            {"position": (5, 18, 25), "scale": (4, 1, 4), "color": level_colors[3]},
        ],
        "moving_platforms": [
            {"position": (5, 4, 5), "scale": (2.5, 0.5, 2.5), "color": color.pink, "movement": "horizontal", "range": 4},
            {"position": (5, 10, 15), "scale": (2.5, 0.5, 2.5), "color": color.pink, "movement": "vertical", "range": 3}
        ],
        "fruits": 30,
        "enemies": 6,
        "power_ups": 3,
        "goal": {"position": (5, 19, 25)}
    },
    {  # Level 5 - Final Challenge
        "platforms": [
            {"position": (0, 0, 0), "scale": (8, 1, 8), "color": level_colors[4]},
            {"position": (12, 4, 0), "scale": (6, 1, 6), "color": level_colors[4]},
            {"position": (0, 8, 12), "scale": (6, 1, 6), "color": level_colors[4]},
            {"position": (12, 12, 12), "scale": (5, 1, 5), "color": level_colors[4]},
            {"position": (0, 16, 24), "scale": (5, 1, 5), "color": level_colors[4]},
            {"position": (12, 20, 24), "scale": (5, 1, 5), "color": level_colors[4]},
            {"position": (0, 24, 36), "scale": (6, 1, 6), "color": level_colors[4]},
        ],
        "moving_platforms": [
            {"position": (6, 6, 6), "scale": (3, 0.5, 3), "color": color.lime, "movement": "circular", "range": 4},
            {"position": (6, 14, 18), "scale": (3, 0.5, 3), "color": color.lime, "movement": "horizontal", "range": 6},
            {"position": (6, 22, 30), "scale": (3, 0.5, 3), "color": color.lime, "movement": "vertical", "range": 4}
        ],
        "fruits": 40,
        "enemies": 8,
        "power_ups": 4,
        "goal": {"position": (0, 25, 36)}
    }
]

def create_yoshi():
    global yoshi
    
    # Destroy existing Yoshi if it exists
    if yoshi:
        destroy(yoshi)
    
    # Create a simple Yoshi character with enhanced features
    yoshi = FirstPersonController()
    yoshi.model = 'sphere'
    yoshi.color = yoshi_green
    yoshi.scale = (1, 1.5, 1)
    yoshi.position = (0, 2, 0)
    yoshi.speed = 8
    yoshi.jump_height = 4
    yoshi.jump_up_duration = 0.4
    yoshi.cursor.color = color.red
    yoshi.invincible = False
    yoshi.invincible_timer = 0
    yoshi.power_up_timer = 0
    yoshi.has_power_up = False
    
    # Adjust for third-person view
    yoshi.camera_pivot.y = 2  # Move camera higher
    yoshi.camera_pivot.z = -5  # Move camera behind (adjust as needed for view)
    
    # Add Yoshi's saddle (positioned slightly back)
    saddle = Entity(
        model='cube',
        color=color.red,
        scale=(0.8, 0.3, 0.8),
        position=(0, -0.2, -0.2),
        parent=yoshi
    )
    
    # Add Yoshi's boots (positioned at bottom)
    boot1 = Entity(
        model='sphere',
        color=color.brown,
        scale=(0.4, 0.3, 0.4),
        position=(-0.3, -0.8, 0),
        parent=yoshi
    )
    
    boot2 = Entity(
        model='sphere',
        color=color.brown,
        scale=(0.4, 0.3, 0.4),
        position=(0.3, -0.8, 0),
        parent=yoshi
    )
    
    # Add Yoshi's eyes (positioned in front)
    eye1 = Entity(
        model='sphere',
        color=color.black,
        scale=(0.1, 0.1, 0.1),
        position=(-0.2, 0.3, 0.4),
        parent=yoshi
    )
    
    eye2 = Entity(
        model='sphere',
        color=color.black,
        scale=(0.1, 0.1, 0.1),
        position=(0.2, 0.3, 0.4),
        parent=yoshi
    )

def create_main_menu():
    global title_text, start_button, quit_button
    
    # Title with animation
    title_text = Text(
        text="Yoshi's Story 3D\nEnhanced Edition",
        position=(0, 0.3),
        origin=(0, 0),
        scale=3,
        color=color.green
    )
    
    # Start button
    start_button = Button(
        text='Start Game',
        color=color.green,
        scale=(0.3, 0.1),
        position=(0, 0)
    )
    start_button.on_click = start_game
    
    # Quit button
    quit_button = Button(
        text='Quit',
        color=color.red,
        scale=(0.3, 0.1),
        position=(0, -0.15)
    )
    quit_button.on_click = application.quit

def create_game_ui():
    global score_text, lives_text, level_text, combo_text
    
    # Score display
    score_text = Text(
        text=f'Score: {score}',
        position=(-0.8, 0.45),
        scale=2,
        color=color.white
    )
    
    # Lives display
    lives_text = Text(
        text=f'Lives: {lives}',
        position=(-0.8, 0.4),
        scale=2,
        color=color.white
    )
    
    # Level display
    level_text = Text(
        text=f'Level: {current_level + 1}/5',
        position=(-0.8, 0.35),
        scale=2,
        color=color.white
    )
    
    # Combo display
    combo_text = Text(
        text=f'Combo: x{combo_multiplier}',
        position=(-0.8, 0.3),
        scale=2,
        color=color.yellow
    )

def create_game_over_ui():
    global game_over_text, restart_button, menu_button, win_text
    
    if lives > 0:
        # Victory screen
        win_text = Text(
            text=f"Congratulations!\nTotal Score: {total_score}",
            position=(0, 0.2),
            origin=(0, 0),
            scale=3,
            color=color.green
        )
    else:
        # Game over screen
        game_over_text = Text(
            text=f"Game Over\nFinal Score: {total_score}",
            position=(0, 0.2),
            origin=(0, 0),
            scale=3,
            color=color.red
        )
    
    # Restart button
    restart_button = Button(
        text='New Game',
        color=color.green,
        scale=(0.3, 0.1),
        position=(0, 0)
    )
    restart_button.on_click = restart_game
    
    # Menu button
    menu_button = Button(
        text='Main Menu',
        color=color.blue,
        scale=(0.3, 0.1),
        position=(0, -0.15)
    )
    menu_button.on_click = show_main_menu

def hide_main_menu():
    if title_text: destroy(title_text)
    if start_button: destroy(start_button)
    if quit_button: destroy(quit_button)

def hide_game_ui():
    if score_text: destroy(score_text)
    if lives_text: destroy(lives_text)
    if level_text: destroy(level_text)
    if combo_text: destroy(combo_text)

def hide_game_over_ui():
    if game_over_text: destroy(game_over_text)
    if win_text: destroy(win_text)
    if restart_button: destroy(restart_button)
    if menu_button: destroy(menu_button)

def start_game():
    global game_state, total_score, score, lives, current_level, collected_fruits
    hide_main_menu()
    game_state = "playing"
    score = 0
    total_score = 0
    lives = 3
    current_level = 0
    collected_fruits = 0
    create_yoshi()
    load_level(0)
    create_game_ui()

def restart_game():
    global game_state, score, total_score, lives, current_level, collected_fruits, combo_multiplier
    hide_game_over_ui()
    game_state = "playing"
    score = 0
    total_score = 0
    lives = 3
    current_level = 0
    collected_fruits = 0
    combo_multiplier = 1
    create_yoshi()
    load_level(0)
    create_game_ui()

def show_main_menu():
    global game_state, yoshi
    clear_level()
    if game_state == "game_over":
        hide_game_over_ui()
    else:
        hide_game_ui()
    game_state = "menu"
    
    # Destroy Yoshi if it exists
    if yoshi:
        destroy(yoshi)
        yoshi = None
        
    create_main_menu()

def game_over():
    global game_state
    game_state = "game_over"
    hide_game_ui()
    create_game_over_ui()

class MovingPlatform(Entity):
    def __init__(self, position, scale, color, movement, range, **kwargs):
        super().__init__(
            model='cube',
            color=color,
            scale=scale,
            position=position,
            collider='box',
            shader=lit_with_shadows_shader,
            **kwargs
        )
        self.movement = movement
        self.range = range
        self.initial_position = Vec3(*position)
        self.time = 0
        
    def update(self):
        if game_state == "playing":
            self.time += time.dt
            
            if self.movement == "horizontal":
                self.x = self.initial_position.x + math.sin(self.time) * self.range
            elif self.movement == "vertical":
                self.y = self.initial_position.y + math.sin(self.time) * self.range
            elif self.movement == "circular":
                self.x = self.initial_position.x + math.cos(self.time) * self.range
                self.z = self.initial_position.z + math.sin(self.time) * self.range

class Enemy(Entity):
    def __init__(self, position, platform, **kwargs):
        super().__init__(
            model='cube',
            color=color.red,
            scale=(1, 1.5, 1),
            position=position,
            collider='box',
            **kwargs
        )
        self.platform = platform
        self.direction = 1
        self.speed = 2
        self.initial_x = position[0]
        
        # Add eyes to enemy
        Entity(
            model='sphere',
            color=color.white,
            scale=(0.2, 0.2, 0.2),
            position=(-0.2, 0.3, -0.4),
            parent=self
        )
        Entity(
            model='sphere',
            color=color.white,
            scale=(0.2, 0.2, 0.2),
            position=(0.2, 0.3, -0.4),
            parent=self
        )
    
    def update(self):
        if game_state == "playing":
            # Simple patrol movement
            self.x += self.direction * self.speed * time.dt
            
            # Reverse direction at platform edges
            if abs(self.x - self.initial_x) > self.platform.scale.x / 2 - 1:
                self.direction *= -1

class PowerUp(Entity):
    def __init__(self, position, **kwargs):
        super().__init__(
            model='sphere',
            color=color.gold,
            scale=0.7,
            position=position,
            collider='sphere',
            **kwargs
        )
        self.time = 0
    
    def update(self):
        # Floating animation
        self.time += time.dt
        self.y += math.sin(self.time * 3) * 0.01
        self.rotation_y += 50 * time.dt

def load_level(level_index):
    global current_level, platforms, fruits, enemies, goal, collected_fruits, moving_platforms, power_ups
    global score, total_score
    
    clear_level()
    
    # Add level score to total
    total_score += score
    score = 0
    
    current_level = level_index
    level = level_data[level_index]
    
    # Create static platforms
    for platform_info in level["platforms"]:
        platform = Entity(
            model='cube',
            color=platform_info["color"],
            scale=platform_info["scale"],
            position=platform_info["position"],
            collider='box',
            shader=lit_with_shadows_shader
        )
        platforms.append(platform)
    
    # Create moving platforms
    if "moving_platforms" in level:
        for mp_info in level["moving_platforms"]:
            mp = MovingPlatform(
                position=mp_info["position"],
                scale=mp_info["scale"],
                color=mp_info["color"],
                movement=mp_info["movement"],
                range=mp_info["range"]
            )
            moving_platforms.append(mp)
            platforms.append(mp)  # Add to platforms list for collision
    
    # Create fruits with better distribution
    for i in range(level["fruits"]):
        platform = random.choice(platforms[:len(platforms) - len(moving_platforms)])  # Prefer static platforms
        pos_x = platform.position.x + random.uniform(-platform.scale.x/2 + 1, platform.scale.x/2 - 1)
        pos_y = platform.position.y + platform.scale.y/2 + 0.5
        pos_z = platform.position.z + random.uniform(-platform.scale.z/2 + 1, platform.scale.z/2 - 1)
        
        # Vary fruit colors more
        fruit_colors = [
            color.rgb(255, 0, 0),     # Red apple
            color.rgb(255, 165, 0),   # Orange
            color.rgb(255, 255, 0),   # Banana
            color.rgb(0, 255, 0),     # Green apple
            color.rgb(148, 0, 211),   # Grape
        ]
        
        fruit = Entity(
            model='sphere',
            color=random.choice(fruit_colors),
            scale=0.5,
            position=(pos_x, pos_y, pos_z),
            collider='sphere'
        )
        fruits.append(fruit)
    
    # Create enemies with patrol behavior
    for i in range(level["enemies"]):
        platform = random.choice(platforms[:len(platforms) - len(moving_platforms)])
        pos_x = platform.position.x + random.uniform(-platform.scale.x/2 + 1, platform.scale.x/2 - 1)
        pos_y = platform.position.y + platform.scale.y/2 + 0.5
        pos_z = platform.position.z + random.uniform(-platform.scale.z/2 + 1, platform.scale.z/2 - 1)
        
        enemy = Enemy(position=(pos_x, pos_y, pos_z), platform=platform)
        enemies.append(enemy)
    
    # Create power-ups
    if "power_ups" in level:
        for i in range(level["power_ups"]):
            platform = random.choice(platforms[:len(platforms) - len(moving_platforms)])
            pos_x = platform.position.x
            pos_y = platform.position.y + platform.scale.y/2 + 1.5
            pos_z = platform.position.z
            
            power_up = PowerUp(position=(pos_x, pos_y, pos_z))
            power_ups.append(power_up)
    
    # Create goal with animation
    goal_info = level["goal"]
    goal = Entity(
        model='cube',
        color=color.yellow,
        scale=(2, 2, 2),
        position=goal_info["position"],
        collider='box'
    )
    
    # Add goal flag
    Entity(
        model='cube',
        color=color.white,
        scale=(0.1, 2, 0.1),
        position=(0, 1, 0),
        parent=goal
    )
    Entity(
        model='quad',
        color=color.green,
        scale=(1, 0.5, 1),
        position=(0.6, 1.5, 0),
        rotation=(0, 90, 0),
        parent=goal
    )
    
    # Position Yoshi only if it exists
    if yoshi:
        yoshi.position = (0, 10, 0)
        yoshi.rotation = (0, 0, 0)
        yoshi.invincible_timer = 1.5  # Brief invincibility at start
    
    # Update UI
    if game_state == "playing":
        update_ui()
        
    # Display level name
    level_names = [
        "Welcome to Yoshi Island!",
        "Sky High Adventure",
        "Spiral Tower Challenge",
        "Platform Maze Madness",
        "Final Showdown"
    ]
    
    if current_level < len(level_names):
        level_intro = Text(
            text=level_names[current_level],
            position=(0, 0),
            origin=(0, 0),
            scale=3,
            color=level_colors[current_level]
        )
        invoke(destroy, level_intro, delay=3)

def clear_level():
    global platforms, fruits, enemies, eggs, goal, moving_platforms, power_ups
    
    # Clear all level entities
    for platform in platforms:
        destroy(platform)
    platforms.clear()
    
    for fruit in fruits:
        destroy(fruit)
    fruits.clear()
    
    for enemy in enemies:
        destroy(enemy)
    enemies.clear()
    
    for egg in eggs:
        destroy(egg)
    eggs.clear()
    
    for mp in moving_platforms:
        destroy(mp)
    moving_platforms.clear()
    
    for pu in power_ups:
        destroy(pu)
    power_ups.clear()
    
    if goal:
        destroy(goal)
        goal = None

def update_ui():
    if score_text:
        score_text.text = f'Score: {total_score + score}'
    if lives_text:
        lives_text.text = f'Lives: {lives}'
    if level_text:
        level_text.text = f'Level: {current_level + 1}/5'
    if combo_text:
        combo_text.text = f'Combo: x{combo_multiplier}'

def throw_egg():
    if yoshi and len(eggs) < (5 if yoshi.has_power_up else 3):
        egg = Entity(
            model='sphere',
            color=color.white if not yoshi.has_power_up else color.cyan,
            scale=0.3 if not yoshi.has_power_up else 0.5,
            position=yoshi.position + yoshi.forward * 2 + Vec3(0, 0.5, 0),
            collider='sphere'
        )
        egg.velocity = yoshi.forward * (30 if yoshi.has_power_up else 20)
        eggs.append(egg)
        invoke(destroy, egg, delay=3)
        play_sound("egg_throw")

def next_level():
    global current_level, collected_fruits, combo_multiplier
    
    combo_multiplier = 1  # Reset combo for new level
    
    if current_level < 4:
        current_level += 1
        collected_fruits = 0
        
        # Level complete bonus
        level_complete = Text(
            text=f"Level Complete!\n+{500 * (current_level)} Bonus Points",
            position=(0, 0.1),
            origin=(0, 0),
            scale=3,
            color=color.green
        )
        invoke(destroy, level_complete, delay=2)
        
        global score
        score += 500 * current_level
        update_ui()
        
        invoke(load_level, current_level, delay=2.5)
    else:
        # Game completed
        lives = 999  # Mark as victory
        game_over()

def update():
    global game_state, score, lives, collected_fruits, combo_multiplier, combo_timer
    
    if game_state == "playing" and yoshi:
        # Update invincibility
        if yoshi.invincible_timer > 0:
            yoshi.invincible_timer -= time.dt
            yoshi.color = color.white if int(yoshi.invincible_timer * 10) % 2 == 0 else yoshi_green
        else:
            if not yoshi.has_power_up:
                yoshi.color = yoshi_green
        
        # Update power-up timer
        if yoshi.power_up_timer > 0:
            yoshi.power_up_timer -= time.dt
            if yoshi.power_up_timer <= 0:
                yoshi.has_power_up = False
                yoshi.color = yoshi_green
                yoshi.speed = 8
        
        # Update combo timer
        if combo_timer > 0:
            combo_timer -= time.dt
            if combo_timer <= 0:
                combo_multiplier = 1
                update_ui()
        
        # Check if Yoshi is falling off the world
        if yoshi.y < -10:
            yoshi.position = (0, 10, 0)
            lives -= 1
            combo_multiplier = 1
            update_ui()
            play_sound("fall")
            
            if lives <= 0:
                game_over()
            else:
                yoshi.invincible_timer = 2  # Invincibility after respawn
        
        # Fruit collection
        for fruit in fruits[:]:
            if distance(fruit, yoshi) < 1.5:
                fruits.remove(fruit)
                destroy(fruit)
                score += 10 * combo_multiplier
                collected_fruits += 1
                
                # Increase combo
                combo_multiplier = min(combo_multiplier + 1, 10)
                combo_timer = 2.0  # Reset combo timer
                
                update_ui()
                play_sound("collect")
                
                # Show score popup
                popup = Text(
                    text=f'+{10 * combo_multiplier}',
                    position=(0, 0.3),
                    origin=(0, 0),
                    scale=2,
                    color=color.yellow
                )
                invoke(destroy, popup, delay=0.5)
        
        # Power-up collection
        for pu in power_ups[:]:
            if distance(pu, yoshi) < 1.5:
                power_ups.remove(pu)
                destroy(pu)
                yoshi.has_power_up = True
                yoshi.power_up_timer = 10  # 10 seconds of power
                yoshi.color = color.cyan
                yoshi.speed = 12
                score += 100
                update_ui()
                play_sound("powerup")
                
                # Show power-up notification
                power_text = Text(
                    text='POWER UP!',
                    position=(0, 0.4),
                    origin=(0, 0),
                    scale=3,
                    color=color.gold
                )
                invoke(destroy, power_text, delay=1.5)
        
        # Enemy collision
        if yoshi.invincible_timer <= 0:
            for enemy in enemies[:]:
                if distance(enemy, yoshi) < 1.5:
                    if yoshi.has_power_up:
                        # Destroy enemy with power-up
                        enemies.remove(enemy)
                        destroy(enemy)
                        score += 50
                        update_ui()
                        play_sound("stomp")
                    else:
                        # Take damage
                        yoshi.position = (0, 10, 0)
                        lives -= 1
                        combo_multiplier = 1
                        update_ui()
                        play_sound("hit")
                        
                        if lives <= 0:
                            game_over()
                        else:
                            yoshi.invincible_timer = 2
        
        # Egg movement and collision
        for egg in eggs[:]:
            if egg:
                egg.position += egg.velocity * time.dt
                egg.velocity.y -= 9.8 * time.dt  # Gravity
                
                # Check for egg-enemy collision
                for enemy in enemies[:]:
                    if distance(egg, enemy) < 1.5:
                        enemies.remove(enemy)
                        destroy(enemy)
                        eggs.remove(egg)
                        destroy(egg)
                        score += 50 * combo_multiplier
                        update_ui()
                        play_sound("hit_enemy")
                        break
                
                # Remove egg if it falls too far
                if egg.y < -20:
                    eggs.remove(egg)
                    destroy(egg)
        
        # Goal animation
        if goal:
            goal.rotation_y += 20 * time.dt
            
            # Check if goal is reached
            if distance(yoshi, goal) < 3:
                required_fruits = int(level_data[current_level]["fruits"] * 0.6)  # 60% required
                if collected_fruits >= required_fruits:
                    play_sound("level_complete")
                    next_level()
                else:
                    remaining = required_fruits - collected_fruits
                    text = Text(
                        text=f"Need {remaining} more fruits!",
                        position=(0, 0),
                        origin=(0, 0),
                        scale=2,
                        color=color.red
                    )
                    invoke(destroy, text, delay=2)

def input(key):
    if game_state == "playing":
        if key == 'r':
            restart_game()
        if key == 'm':
            show_main_menu()
        if key == 'left mouse down' and yoshi:
            throw_egg()
        # Add double jump capability with power-up
        if key == 'space' and yoshi and yoshi.has_power_up and not yoshi.grounded:
            yoshi.jump()
    
    if key == 'escape':
        if game_state == "playing":
            show_main_menu()
        else:
            application.quit()

# Start the game
create_main_menu()

# Run the application
app.run()

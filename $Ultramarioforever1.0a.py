# Meow! Generated with DELTA-BUSTER for a cute Mario Worker feel! Nya~
import tkinter as tk
import time

# --- Constants ---
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 400
TARGET_FPS = 60
FRAME_TIME = 1 / TARGET_FPS

# --- Colors ---
COLOR_SKY = "#87CEEB" # Cute sky blue!
COLOR_GROUND = "#8B4513" # Nice brown for the ground!
COLOR_MARIO = "#FF0000" # Bright red like Mario's hat!
COLOR_GOOMBA = "#A0522D" # Goomba brown!
COLOR_COIN = "#FFD700" # Shiny gold!
COLOR_PLATFORM = "#008000" # Grassy green!

# --- Physics & Game Settings ---
GRAVITY = 0.8
JUMP_POWER = -12 # Negative because tkinter y goes down
MOVE_SPEED = 5
GOOMBA_SPEED = 1.5

# --- Game State ---
mario = {
    'x': 50, 'y': WINDOW_HEIGHT - 50, # Start near the bottom left
    'width': 20, 'height': 30,
    'vx': 0, 'vy': 0,
    'on_ground': False,
    'canvas_item': None # To hold the rectangle ID later!
}

goombas = [
    {'x': 300, 'y': WINDOW_HEIGHT - 50, 'width': 20, 'height': 20, 'vx': -GOOMBA_SPEED, 'canvas_item': None},
    {'x': 450, 'y': WINDOW_HEIGHT - 120, 'width': 20, 'height': 20, 'vx': -GOOMBA_SPEED, 'canvas_item': None} # On a platform!
]

coins = [
    {'x': 150, 'y': WINDOW_HEIGHT - 80, 'radius': 8, 'collected': False, 'canvas_item': None},
    {'x': 250, 'y': WINDOW_HEIGHT - 150, 'radius': 8, 'collected': False, 'canvas_item': None},
    {'x': 500, 'y': WINDOW_HEIGHT - 80, 'radius': 8, 'collected': False, 'canvas_item': None}
]

# Let's make some platforms, nya! x, y, width, height
platforms = [
    # Ground
    (0, WINDOW_HEIGHT - 30, WINDOW_WIDTH, 30),
    # Some floating ones! Purr!
    (200, WINDOW_HEIGHT - 100, 100, 20),
    (400, WINDOW_HEIGHT - 100, 100, 20),
    (425, WINDOW_HEIGHT - 150, 150, 20) # Platform for the second goomba
]

score = 0
game_over = False
keys_pressed = {'Left': False, 'Right': False, 'space': False} # Track key presses, meow!

# --- Tkinter Setup ---
window = tk.Tk()
window.title("Cute Mario Worker Sim! Meow!")
window.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
window.resizable(False, False) # No resizing, keeps things simple!

canvas = tk.Canvas(window, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg=COLOR_SKY)
canvas.pack()

# --- Drawing Functions ---
def draw_game():
    global score_text_id # Need to update the score text
    canvas.delete("all") # Clear canvas, purrr!

    # Draw Platforms
    for x, y, w, h in platforms:
        canvas.create_rectangle(x, y, x + w, y + h, fill=COLOR_PLATFORM, outline=COLOR_PLATFORM)

    # Draw Coins (if not collected)
    for coin in coins:
        if not coin['collected']:
            cx, cy, r = coin['x'], coin['y'], coin['radius']
            coin['canvas_item'] = canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=COLOR_COIN, outline=COLOR_COIN)

    # Draw Goombas
    for goomba in goombas:
        x, y, w, h = goomba['x'], goomba['y'], goomba['width'], goomba['height']
        goomba['canvas_item'] = canvas.create_rectangle(x, y - h, x + w, y, fill=COLOR_GOOMBA, outline="black")

    # Draw Mario! Nya!
    x, y, w, h = mario['x'], mario['y'], mario['width'], mario['height']
    fill_color = COLOR_MARIO
    if game_over:
        fill_color = "grey" # Sad grey kitty if game over :(
    mario['canvas_item'] = canvas.create_rectangle(x, y - h, x + w, y, fill=fill_color, outline="black")

    # Draw Score
    canvas.create_text(10, 10, text=f"Score: {score}", anchor="nw", fill="white", font=("Arial", 16, "bold"))

    if game_over:
         canvas.create_text(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2, text="Game Over! >.<", fill="red", font=("Arial", 30, "bold"))

# --- Collision Detection ---
def check_collision(item1, item2):
    # Simple bounding box collision, purrfectly adequate!
    x1, y1, w1, h1 = item1['x'], item1['y'], item1['width'], item1['height']
    x2, y2, w2, h2 = item2['x'], item2['y'], item2['width'], item2['height']

    # Check horizontal overlap
    if (x1 < x2 + w2 and x1 + w1 > x2):
        # Check vertical overlap (remember y is top-down)
        if (y1 > y2 - h2 and y1 - h1 < y2):
            return True
    return False

def check_platform_collision(item, platforms):
    ix, iy, iw, ih = item['x'], item['y'], item['width'], item['height']
    on_ground = False
    item_bottom = iy
    item_top = iy - ih
    item_left = ix
    item_right = ix + iw

    for px, py, pw, ph in platforms:
        platform_top = py
        platform_bottom = py + ph
        platform_left = px
        platform_right = px + pw

        # Check horizontal overlap for potential vertical collision
        if item_right > platform_left and item_left < platform_right:
            # Falling onto platform?
            # Check if item's bottom is between its previous and current position AND just above the platform top
            if item['vy'] >= 0 and item_bottom >= platform_top and (item_bottom - item['vy']) <= platform_top:
                 # Collision! Place item on top of platform
                 item['y'] = platform_top
                 item['vy'] = 0
                 on_ground = True
                 #print(f"Meow! Landed on platform at {platform_top}")
                 break # Only collide with one platform vertically at a time

            # Hitting head on platform underside? (Jumping up)
            elif item['vy'] < 0 and item_top <= platform_bottom and (item_top - item['vy']) >= platform_bottom:
                 item['y'] = platform_bottom + ih # Place below platform
                 item['vy'] = 0 # Stop upward movement
                 #print("Bonk! >_< Hit head!")
                 # No break needed here, might still land on another platform later

    return on_ground


# --- Input Handling ---
def key_pressed(event):
    keys_pressed[event.keysym] = True
    #print(f"Pressed: {event.keysym}") # Meow! Debugging!

def key_released(event):
    keys_pressed[event.keysym] = False
    #print(f"Released: {event.keysym}") # Meow! Debugging!


# --- Game Loop ---
def game_loop():
    global score, game_over
    start_time = time.perf_counter() # More precise time, purr!

    if game_over:
        draw_game() # Keep drawing the game over screen
        window.after(int(FRAME_TIME * 1000), game_loop) # Keep the loop going slowly
        return

    # --- Handle Input ---
    if keys_pressed['Left']:
        mario['vx'] = -MOVE_SPEED
    elif keys_pressed['Right']:
        mario['vx'] = MOVE_SPEED
    else:
        mario['vx'] = 0

    if keys_pressed['space'] and mario['on_ground']:
        mario['vy'] = JUMP_POWER
        mario['on_ground'] = False
        #print("Jump! Nya!")

    # --- Update Mario ---
    # Apply gravity
    mario['vy'] += GRAVITY

    # Tentative new position
    next_x = mario['x'] + mario['vx']
    next_y = mario['y'] + mario['vy']

    # Store old y for platform check
    old_y = mario['y']
    mario['y'] = next_y # Update vertical position first for collision check

    # Check for platform collisions vertically
    mario['on_ground'] = check_platform_collision(mario, platforms)

    # Check horizontal boundaries (simple wrap for now, could stop at edges)
    # mario['x'] = (mario['x'] + mario['vx']) % WINDOW_WIDTH # Wrap around!
    # Let's prevent going off-screen instead, more Mario-like!
    mario['x'] += mario['vx']
    if mario['x'] < 0:
        mario['x'] = 0
    elif mario['x'] + mario['width'] > WINDOW_WIDTH:
        mario['x'] = WINDOW_WIDTH - mario['width']


    # --- Update Goombas ---
    for goomba in goombas:
        goomba['x'] += goomba['vx']

        # Basic AI: Turn around at edges or platform ends (very simple check)
        on_platform = False
        goomba_feet_x_left = goomba['x']
        goomba_feet_x_right = goomba['x'] + goomba['width']
        goomba_feet_y = goomba['y'] + 1 # Check slightly below the goomba

        for px, py, pw, ph in platforms:
             # Is the goomba roughly above this platform?
             if goomba['y'] > py - 5 and goomba['y'] < py + ph + 5: # Vertical proximity
                 # Check if EITHER foot is about to step off the platform
                 left_foot_on = (goomba_feet_x_left >= px and goomba_feet_x_left <= px + pw)
                 right_foot_on = (goomba_feet_x_right >= px and goomba_feet_x_right <= px + pw)

                 # If moving left and left foot is off OR moving right and right foot is off
                 if (goomba['vx'] < 0 and not left_foot_on and right_foot_on) or \
                    (goomba['vx'] > 0 and not right_foot_on and left_foot_on):
                     goomba['vx'] *= -1 # Turn around! Nya!
                     # Minor adjustment to prevent getting stuck
                     goomba['x'] += goomba['vx'] * 2
                     break # Found the platform it's on/near

                 # Also turn if hitting window boundaries
                 if goomba['x'] < 0 or goomba['x'] + goomba['width'] > WINDOW_WIDTH:
                     goomba['vx'] *= -1
                     goomba['x'] += goomba['vx'] * 2 # Nudge back


    # --- Check Collisions (Post-Movement) ---
    # Mario vs Coins
    mario_hitbox = {'x': mario['x'], 'y': mario['y'] - mario['height'], 'width': mario['width'], 'height': mario['height']} # Use top-left for collision check
    for coin in coins:
        if not coin['collected']:
            coin_hitbox = {'x': coin['x'] - coin['radius'], 'y': coin['y'] - coin['radius'], 'width': coin['radius']*2, 'height': coin['radius']*2}
            # A simple distance check might be easier for circles, actually!
            dist_sq = (mario['x'] + mario['width']/2 - coin['x'])**2 + (mario['y'] - mario['height']/2 - coin['y'])**2
            if dist_sq < (mario['width']/2 + coin['radius'])**2 : # Approximation using Mario's width
                 coin['collected'] = True
                 score += 10
                 #print(f"Coin get! Purrrr! Score: {score}")

    # Mario vs Goombas
    for i in range(len(goombas) -1, -1, -1): # Iterate backwards for safe removal
        goomba = goombas[i]
        goomba_hitbox = {'x': goomba['x'], 'y': goomba['y'] - goomba['height'], 'width': goomba['width'], 'height': goomba['height']}

        if check_collision(mario_hitbox, goomba_hitbox):
            # Did Mario land on top? (Check vertical velocity and relative position)
            mario_bottom = mario['y']
            goomba_top = goomba['y'] - goomba['height']
            # Check if Mario was falling and his feet are near the goomba's head
            if mario['vy'] > 0 and (mario_bottom - mario['vy']) <= goomba_top:
                # Stomp! Meow!
                #print("Goomba Stomp! *pop*")
                goombas.pop(i) # Remove the goomba
                mario['vy'] = JUMP_POWER * 0.5 # Small bounce after stomp! Purr!
            else:
                # Mario got hit! Oh noes! >_<
                #print("Ouch! Game Over!")
                game_over = True
                break # Stop checking other goombas

    # --- Draw Frame ---
    draw_game()

    # --- Frame Rate Control ---
    end_time = time.perf_counter()
    elapsed = end_time - start_time
    sleep_time = FRAME_TIME - elapsed
    if sleep_time < 0:
        sleep_time = 0 # Don't sleep if we're already late!

    # Use window.after for the next loop iteration, purrfect for tkinter!
    window.after(int(sleep_time * 1000), game_loop) # time is in ms

# --- Bind Keys ---
window.bind("<KeyPress>", key_pressed)
window.bind("<KeyRelease>", key_released)

# --- Start Game ---
print("Starting cute Mario sim... Nya!")
window.after(100, game_loop) # Start the loop after a short delay
window.mainloop() # Keep the window open, meow!

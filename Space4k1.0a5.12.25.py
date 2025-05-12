import tkinter as tk
import random

# --- Game Setup Variables ---
WIDTH = 800
HEIGHT = 600
PLAYER_BULLET_SPEED = 6
ALIEN_BULLET_SPEED = 4
ALIEN_SPAWN_DELAY = 1000 # milliseconds
ALIEN_SHOOT_DELAY = 1500 # milliseconds

# --- Mock Canvas and Game Elements ---
root = tk.Tk()
root.title("Space Game - Fixed")
canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg='black')
canvas.pack()

# Create player using a tag for easy finding
player_rect = canvas.create_rectangle(WIDTH/2 - 15, HEIGHT - 50, WIDTH/2 + 15, HEIGHT - 20, fill="blue", tags="player")

# Game state variables
player_bullets = []
alien_bullets = []
aliens = {} # Dictionary: {alien_id: {'x_speed': speed}}
score = 0
game_over = False

# --- UI Elements ---
score_display_text = canvas.create_text(10, 10, text=f"Score: {score}", fill="white", anchor="nw", font=("Arial", 14))
game_over_text = None # To hold the game over message ID

# --- Helper Functions ---
def update_score_display():
    """Updates the score text on the canvas."""
    global score_display_text
    canvas.itemconfig(score_display_text, text=f"Score: {score}")

def player_hit():
    """Handles the player being hit."""
    global game_over, game_over_text
    print("Player hit!")
    # Delete player visual
    canvas.delete("player")
    # Display game over message if not already shown
    if not game_over_text:
        game_over_text = canvas.create_text(WIDTH/2, HEIGHT/2, text="GAME OVER", fill="red", font=("Arial", 40), anchor="center")
    game_over = True
    # Stop further game actions like spawning or shooting
    # (The main loop check handles stopping updates)

def create_player_bullet():
    """Creates a bullet originating from the player."""
    if game_over: return # Don't shoot if game over

    player_coords = canvas.coords("player")
    if not player_coords: return # Player might be deleted

    # Calculate bullet position (center top of player)
    x1 = player_coords[0] + (player_coords[2] - player_coords[0]) / 2 - 2 # Centered, width 4
    y1 = player_coords[1] - 8 # Slightly above player
    x2 = x1 + 4
    y2 = y1 + 8
    bullet_id = canvas.create_rectangle(x1, y1, x2, y2, fill="yellow", tags="player_bullet")
    player_bullets.append(bullet_id)

def create_alien_bullet(alien_id):
    """Creates a bullet originating from a specific alien."""
    if game_over or alien_id not in aliens: return # Don't shoot if game over or alien gone

    alien_coords = canvas.coords(alien_id)
    if not alien_coords: return # Alien might be deleted

    # Calculate bullet position (center bottom of alien)
    x1 = alien_coords[0] + (alien_coords[2] - alien_coords[0]) / 2 - 2 # Centered, width 4
    y1 = alien_coords[3] # Bottom of alien
    x2 = x1 + 4
    y2 = y1 + 8
    bullet_id = canvas.create_rectangle(x1, y1, x2, y2, fill="lime", tags="alien_bullet")
    alien_bullets.append(bullet_id)

def spawn_alien():
    """Creates a new alien at the top of the screen."""
    if game_over: return # Don't spawn if game over

    x1 = random.randint(20, WIDTH - 50)
    y1 = 10
    x2 = x1 + 30
    y2 = y1 + 20
    alien_id = canvas.create_rectangle(x1, y1, x2, y2, fill="red", tags="alien")
    # Assign random horizontal speed
    aliens[alien_id] = {'x_speed': random.choice([-2, 2, -1, 1])}
    # Schedule next spawn
    root.after(ALIEN_SPAWN_DELAY, spawn_alien)

def alien_random_shoot():
    """Makes a random alien shoot."""
    if game_over or not aliens: return # Don't shoot if game over or no aliens

    # Select a random alien that still exists
    active_alien_ids = [aid for aid in aliens if canvas.coords(aid)]
    if active_alien_ids:
        shooter_id = random.choice(active_alien_ids)
        create_alien_bullet(shooter_id)

    # Schedule next shot
    root.after(ALIEN_SHOOT_DELAY, alien_random_shoot)

def move_aliens():
    """Moves existing aliens horizontally and handles screen boundaries."""
    if game_over: return

    aliens_to_remove = []
    for alien_id, data in list(aliens.items()): # Iterate over a copy of items
        coords = canvas.coords(alien_id)
        if not coords:
            aliens_to_remove.append(alien_id)
            continue

        new_x1 = coords[0] + data['x_speed']
        new_x2 = coords[2] + data['x_speed']

        # Bounce off walls
        if new_x1 < 0 or new_x2 > WIDTH:
            data['x_speed'] *= -1 # Reverse direction
            # Adjust position slightly to prevent getting stuck
            canvas.move(alien_id, data['x_speed'] * 2, 0)
        else:
            canvas.move(alien_id, data['x_speed'], 0)

    # Clean up aliens dictionary if any were deleted mid-loop
    for alien_id in aliens_to_remove:
        if alien_id in aliens:
            del aliens[alien_id]


# --- Core Game Update Logic ---
def update_game():
    """
    Updates the state of bullets, aliens, and checks for collisions.
    Manages movement, collisions, and item removal safely.
    """
    global score, player_bullets, alien_bullets, aliens, game_over

    if game_over:
        return # Stop updates if game is over

    # --- Move Aliens ---
    move_aliens()

    # --- Player Bullet Logic ---
    bullets_to_remove_player = set() # Store bullet IDs to remove
    aliens_hit_this_frame = set()    # Store alien IDs hit this frame

    # Iterate over a copy of the list for safe removal during iteration
    current_player_bullets = list(player_bullets)

    for bullet_id in current_player_bullets:
        # Check if bullet still exists on canvas before proceeding
        # Using canvas.coords() is a reliable way to check existence
        if not canvas.coords(bullet_id):
            bullets_to_remove_player.add(bullet_id)
            continue

        # Move bullet upwards
        canvas.move(bullet_id, 0, -PLAYER_BULLET_SPEED)

        # Get coordinates *after* moving
        coords = canvas.coords(bullet_id)
        if not coords: # Check again, might have been deleted elsewhere? (unlikely here)
            bullets_to_remove_player.add(bullet_id)
            continue

        # Check if bullet is off-screen (top)
        # coords[1] is the top y-coordinate
        if coords[1] < 0:
            bullets_to_remove_player.add(bullet_id)
        else:
            # Check collision with aliens
            # find_overlapping returns IDs of items whose bounding boxes overlap
            overlapping_items = canvas.find_overlapping(*coords)
            for item_id in overlapping_items:
                # Check if the item is an alien and hasn't been hit *in this frame*
                if item_id in aliens and item_id not in aliens_hit_this_frame:
                    aliens_hit_this_frame.add(item_id)
                    bullets_to_remove_player.add(bullet_id)
                    score += 10
                    update_score_display()
                    # A single bullet typically hits only one alien, so break inner loop
                    break

    # --- Alien Bullet Logic ---
    bullets_to_remove_alien = set()

    # Find player reliably using its tag
    player_ids = canvas.find_withtag("player")

    # Proceed only if the player exists
    if player_ids:
        player_id = player_ids[0] # Get the player ID
        player_coords = canvas.coords(player_id)

        # Double-check if player coords exist (safety)
        if player_coords:
            # Iterate over a copy
            current_alien_bullets = list(alien_bullets)
            for bullet_id in current_alien_bullets:
                # Check if bullet exists
                if not canvas.coords(bullet_id):
                    bullets_to_remove_alien.add(bullet_id)
                    continue

                # Move alien bullet downwards
                canvas.move(bullet_id, 0, ALIEN_BULLET_SPEED)

                # Get coords *after* moving
                coords = canvas.coords(bullet_id)
                if not coords:
                    bullets_to_remove_alien.add(bullet_id)
                    continue

                # Check if bullet is off-screen (bottom)
                # coords[3] is the bottom y-coordinate
                if coords[3] > HEIGHT:
                    bullets_to_remove_alien.add(bullet_id)
                else:
                    # *** CORRECTED INDENTATION AND ADDED COLLISION LOGIC ***
                    # Check collision with player using AABB
                    # Bullet: coords[0]=bx1, coords[1]=by1, coords[2]=bx2, coords[3]=by2
                    # Player: player_coords[0]=px1, player_coords[1]=py1, player_coords[2]=px2, player_coords[3]=py2
                    bx1, by1, bx2, by2 = coords
                    px1, py1, px2, py2 = player_coords

                    # Check for overlap
                    if bx1 < px2 and bx2 > px1 and by1 < py2 and by2 > py1:
                        # Collision detected!
                        bullets_to_remove_alien.add(bullet_id)
                        player_hit() # Call the function to handle player being hit
                        # No need to check other bullets against player if game over
                        if game_over:
                            break # Exit the alien bullet loop

    # --- Deferred Deletion ---
    # Safely remove all marked items *after* all checks are done

    # Remove player bullets that hit or went off-screen
    for bullet_id in bullets_to_remove_player:
        if bullet_id in player_bullets: # Check if not already removed
            player_bullets.remove(bullet_id)
            canvas.delete(bullet_id)

    # Remove aliens that were hit
    for alien_id in aliens_hit_this_frame:
        if alien_id in aliens: # Check if not already removed
            del aliens[alien_id] # Remove from tracking dictionary
            canvas.delete(alien_id) # Remove from canvas

    # Remove alien bullets that hit or went off-screen
    for bullet_id in bullets_to_remove_alien:
        if bullet_id in alien_bullets: # Check if not already removed
            alien_bullets.remove(bullet_id)
            canvas.delete(bullet_id)

    # --- Schedule next update ---
    if not game_over:
        root.after(20, update_game) # ~50 FPS

# --- Player Controls ---
def move_left(event):
    if not game_over:
        coords = canvas.coords("player")
        if coords and coords[0] > 5: # Check boundary
             canvas.move("player", -15, 0)

def move_right(event):
     if not game_over:
        coords = canvas.coords("player")
        if coords and coords[2] < WIDTH - 5: # Check boundary
            canvas.move("player", 15, 0)

def shoot(event):
    create_player_bullet()

# Bind keys
root.bind("<Left>", move_left)
root.bind("<Right>", move_right)
root.bind("<space>", shoot)
root.focus_set() # Ensure the window has focus to receive key events

# --- Start the Game ---
# Initial alien spawn and shooting timers
root.after(500, spawn_alien)
root.after(1000, alien_random_shoot)

# Start the main game loop
update_game()

# Start the Tkinter event loop
root.mainloop()

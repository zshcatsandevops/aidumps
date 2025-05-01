import pygame
import numpy as np
import pygame.sndarray
import time # Added for potential smoother game over

# Initialize Pygame and mixer
pygame.init()
# Increased buffer size for potentially smoother sound playback
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# Window setup
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Super Mario Land - No PNG")

# Colors
BLUE = (0, 100, 255)  # A slightly nicer sky blue
GREEN = (0, 200, 0)   # A slightly nicer green
RED = (255, 0, 0)     # Mario
BROWN = (139, 69, 19) # Platforms, Enemies
YELLOW = (255, 255, 0)# Coins, Goal
WHITE = (255, 255, 255)# Score text

# Mario properties
mario_x, mario_y = 100, HEIGHT - 50 - 20 # Start on the ground platform
mario_width, mario_height = 20, 30
mario_vel_x, mario_vel_y = 0, 0
on_ground = False # Replaces is_jumping for clarity
GRAVITY = 0.5     # Increased gravity slightly
MAX_FALL_SPEED = 10 # Terminal velocity
JUMP_VELOCITY = -10 # Jump strength

# Game objects (using pygame.Rect for easier collision detection)
platforms = [
    # Ground (made slightly thicker visually)
    pygame.Rect(0, HEIGHT - 20, WIDTH, 20),
    pygame.Rect(200, 450, 100, 20), # Adjusted y slightly
    pygame.Rect(400, 350, 100, 20), # Adjusted y slightly
    pygame.Rect(550, 250, 80, 20),  # Added another platform
]
# Store enemies as Rects too, with velocity added
enemies = [
    {"rect": pygame.Rect(300, HEIGHT - 40, 20, 20), "vel": 1.5},
    {"rect": pygame.Rect(500, 430, 20, 20), "vel": -1.5}, # Enemy on platform
]
# Store coins with Rects for collision
coins = [
    pygame.Rect(250, 410, 15, 15), # Adjusted y, using Rect
    pygame.Rect(450, 310, 15, 15), # Adjusted y, using Rect
    pygame.Rect(585, 210, 15, 15), # Coin on new platform
]
goal = pygame.Rect(700, HEIGHT - 70, 20, 50) # Adjusted y
score = 0

# Font for score
try:
    font = pygame.font.Font(None, 36) # Default font
except:
    font = pygame.font.SysFont('arial', 36) # Fallback system font

# Sound Engine class
class SoundEngine:
    def __init__(self):
        # Check if mixer was initialized successfully
        if pygame.mixer.get_init():
            self.sample_rate = pygame.mixer.get_init()[0]
            self.sounds = {}
            self.load_sounds()
        else:
            print("Warning: Pygame mixer failed to initialize. No sound.")
            self.sounds = None # Indicate sound is unavailable

    def generate_square_wave(self, frequency, duration, amplitude=8000):
        if not pygame.mixer.get_init(): return None # Don't generate if no mixer
        num_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, num_samples, endpoint=False)

        # Square wave generation
        signal = amplitude * np.sign(np.sin(2 * np.pi * frequency * t))

        # Apply a simple linear fade-out envelope
        envelope = np.linspace(1, 0, num_samples)
        samples = (signal * envelope).astype(np.int16)

        # Ensure stereo by duplicating the channel
        samples_stereo = np.zeros((num_samples, 2), dtype=np.int16)
        samples_stereo[:, 0] = samples # Left channel
        samples_stereo[:, 1] = samples # Right channel

        try:
            sound = pygame.sndarray.make_sound(samples_stereo)
            return sound
        except Exception as e:
            print(f"Error creating sound: {e}")
            return None

    def load_sounds(self):
        if not self.sounds is None:
            self.sounds["jump"] = self.generate_square_wave(660, 0.12) # Higher pitch
            self.sounds["coin"] = self.generate_square_wave(1046, 0.08) # Higher pitch
            self.sounds["stomp"] = self.generate_square_wave(220, 0.15) # Lower pitch
            self.sounds["goal"] = self.generate_square_wave(880, 0.5)
            self.sounds["game_over"] = self.generate_square_wave(110, 0.8) # Longer, lower

    def play(self, sound_name):
        # Check if sounds were loaded and the specific sound exists
        if self.sounds and sound_name in self.sounds and self.sounds[sound_name]:
            self.sounds[sound_name].play()

# Initialize sound engine
sound_engine = SoundEngine()

# Clock for FPS control
clock = pygame.time.Clock()

# --- Game State Update Function ---
def update():
    global mario_x, mario_y, mario_vel_x, mario_vel_y, on_ground, score, running

    # --- Mario Movement ---
    mario_x += mario_vel_x

    # Horizontal collision with platforms (basic wall collision)
    mario_rect_next_x = pygame.Rect(mario_x, mario_y, mario_width, mario_height)
    for p in platforms:
        if mario_rect_next_x.colliderect(p):
            if mario_vel_x > 0: # Moving right
                mario_x = p.left - mario_width
                mario_vel_x = 0 # Stop horizontal movement
            elif mario_vel_x < 0: # Moving left
                mario_x = p.right
                mario_vel_x = 0 # Stop horizontal movement
            break # Stop checking after first collision

    # Apply gravity
    mario_vel_y += GRAVITY
    # Cap fall speed
    if mario_vel_y > MAX_FALL_SPEED:
        mario_vel_y = MAX_FALL_SPEED
    mario_y += mario_vel_y

    # Assume not on ground until collision check proves otherwise
    on_ground = False

    # Vertical collision with platforms
    mario_rect = pygame.Rect(mario_x, mario_y, mario_width, mario_height)
    for p in platforms:
        if mario_rect.colliderect(p):
            # Check if landing on top (Mario's bottom hits platform's top)
            # Use a small tolerance (e.g., half of max fall speed)
            if mario_vel_y > 0 and mario_rect.bottom <= p.top + abs(mario_vel_y):
                mario_y = p.top - mario_height
                mario_vel_y = 0
                on_ground = True
            # Check if hitting bottom (Mario's top hits platform's bottom)
            elif mario_vel_y < 0 and mario_rect.top >= p.bottom - abs(mario_vel_y):
                 mario_y = p.bottom # Bump head
                 mario_vel_y = 0 # Stop upward movement

    # Keep Mario within screen bounds (horizontal)
    if mario_x < 0:
        mario_x = 0
    elif mario_x > WIDTH - mario_width:
        mario_x = WIDTH - mario_width

    # Check for falling off the bottom (Game Over condition)
    if mario_y > HEIGHT:
        print("Fell off screen!")
        sound_engine.play("game_over")
        time.sleep(1) # Pause briefly
        running = False
        return # Exit update early

    # --- Enemy Logic ---
    mario_rect = pygame.Rect(mario_x, mario_y, mario_width, mario_height) # Update rect
    for e_data in enemies[:]: # Iterate over a copy
        enemy_rect = e_data["rect"]
        enemy_vel = e_data["vel"]

        # Move enemy
        enemy_rect.x += enemy_vel

        # Enemy collision with platforms (simple turnaround)
        # Check slightly ahead to prevent getting stuck
        next_enemy_x = enemy_rect.x + enemy_vel
        temp_rect = pygame.Rect(next_enemy_x, enemy_rect.y, enemy_rect.width, enemy_rect.height)
        turn_around = False
        for p in platforms:
             # Don't collide with the ground platform edges for turning
            if p.height == 20 and p.width == WIDTH: continue
            if temp_rect.colliderect(p):
                turn_around = True
                break
        # Also turn around at screen edges
        if next_enemy_x <= 0 or next_enemy_x >= WIDTH - enemy_rect.width:
            turn_around = True

        if turn_around:
            e_data["vel"] *= -1 # Reverse direction

        # Mario collision with enemy
        if mario_rect.colliderect(enemy_rect):
            # Check if Mario landed on top (stomp)
            # Mario falling AND his bottom is near the enemy's top
            if (mario_vel_y > 0 and
                mario_rect.bottom <= enemy_rect.centery): # Check relative to center
                enemies.remove(e_data)
                mario_vel_y = JUMP_VELOCITY * 0.6 # Small bounce after stomp
                score += 5 # Score for stomp
                sound_engine.play("stomp")
            else:
                # Collision from side or bottom - Game Over
                print("Hit by enemy!")
                sound_engine.play("game_over")
                time.sleep(1) # Pause briefly
                running = False
                return # Exit update early

    # --- Coin Collection ---
    mario_rect = pygame.Rect(mario_x, mario_y, mario_width, mario_height) # Update rect
    for c in coins[:]: # Iterate over a copy
        if mario_rect.colliderect(c):
            coins.remove(c)
            score += 10 # Score for coin
            sound_engine.play("coin")

    # --- Goal Check ---
    mario_rect = pygame.Rect(mario_x, mario_y, mario_width, mario_height) # Update rect
    if mario_rect.colliderect(goal):
        print(f"Level Complete! Final Score: {score}")
        sound_engine.play("goal")
        time.sleep(1.5) # Longer pause for level complete
        running = False

# --- Draw Function ---
def draw():
    # Background
    screen.fill(BLUE)

    # Draw Platforms
    for p in platforms:
        # Use different color for ground
        color = GREEN if p.height == 20 and p.width == WIDTH else BROWN
        pygame.draw.rect(screen, color, p)

    # Draw Enemies
    for e_data in enemies:
        pygame.draw.rect(screen, BROWN, e_data["rect"]) # Draw enemy as brown rect

    # Draw Coins (as circles centered in their Rects)
    for c in coins:
        pygame.draw.circle(screen, YELLOW, c.center, c.width // 2) # Draw circle

    # Draw Goal
    pygame.draw.rect(screen, YELLOW, goal)

    # Draw Mario
    pygame.draw.rect(screen, RED, (int(mario_x), int(mario_y), mario_width, mario_height))

    # Draw Score
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))

    # Update the display
    pygame.display.flip()

# --- Main Game Loop ---
running = True
while running:
    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                mario_vel_x = -4 # Slightly slower horizontal speed
            elif event.key == pygame.K_RIGHT:
                mario_vel_x = 4
            elif event.key == pygame.K_SPACE:
                # Only jump if on the ground
                if on_ground:
                    mario_vel_y = JUMP_VELOCITY
                    on_ground = False # Mario is no longer on ground after jumping
                    sound_engine.play("jump")
            elif event.key == pygame.K_ESCAPE: # Added escape key to quit
                 running = False
        elif event.type == pygame.KEYUP:
            # Stop moving when left/right key is released
            if event.key == pygame.K_LEFT and mario_vel_x < 0:
                mario_vel_x = 0
            elif event.key == pygame.K_RIGHT and mario_vel_x > 0:
                mario_vel_x = 0

    # --- Update Game State ---
    if running: # Only update if game is still running
        update()

    # --- Draw Frame ---
    if running: # Only draw if game is still running
        draw()

    # --- Frame Rate Control ---
    clock.tick(60) # Limit FPS to 60

# --- Clean Up ---
pygame.quit()
print("Game Exited")

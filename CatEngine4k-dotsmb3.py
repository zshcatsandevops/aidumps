import pygame as pg
import sys

# CATSDK Game Configuration ~nya!
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TITLE = "CATSDK's Super Mario Purr-ty Three!"
FPS = 60

# Colors, meooow!
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)  # For our hero, Mario-cat!
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BROWN = (139, 69, 19) # For the ground, purrr
SKY_BLUE = (135, 206, 235) # Pretty sky, nya!

# Player (Mario-cat!) properties, meow!
PLAYER_WIDTH = 30
PLAYER_HEIGHT = 40
PLAYER_ACC_VALUE = 0.7  # Renamed to avoid conflict with acc vector, nya! How fast Mario-cat speeds up!
PLAYER_FRICTION_COEFF = -0.12 # Friction coefficient, purr! Needs to be negative to oppose motion.
PLAYER_GRAVITY = 0.7 # Meow, gravity!
PLAYER_JUMP_STRENGTH = -15 # How high can Mario-cat jump, nya? (Initial upward velocity)

# Platform properties, purr!
PLATFORM_LIST = [
    (0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40, BROWN), # Main ground
    (200, SCREEN_HEIGHT - 150, 150, 20, GREEN),      # A floating platform
    (450, SCREEN_HEIGHT - 250, 100, 20, GREEN),      # Another one, nya!
    (50, SCREEN_HEIGHT - 350, 200, 20, BLUE)         # Higher platform, meow!
]

# --- Player Class, our brave Mario-cat! ---
class Player(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.surf = pg.Surface((PLAYER_WIDTH, PLAYER_HEIGHT))
        self.surf.fill(RED) # Mario-cat is red, purr!
        self.rect = self.surf.get_rect()
        
        # Kinematics, meow!
        # self.pos represents the midbottom of the player rect using floating point for precision
        self.pos = pg.math.Vector2((SCREEN_WIDTH / 2, SCREEN_HEIGHT - 80)) 
        self.vel = pg.math.Vector2(0, 0)
        # self.acc is calculated each frame based on forces like input, gravity, friction
        self.acc = pg.math.Vector2(0, 0) 
        self.on_ground = False # Is Mario-cat on the ground, nya?

        self.rect.midbottom = self.pos # Initialize integer rect position from float pos

    def jump(self):
        if self.on_ground: # Can only jump if on ground, purr!
            self.vel.y = PLAYER_JUMP_STRENGTH
            self.on_ground = False # Mario-cat is in the air, nya!

    def update(self, platforms):
        # 1. Determine acceleration based on input and environmental forces
        # Horizontal acceleration: start with input, then add friction
        input_acc_x = 0
        keys = pg.key.get_pressed()
        if keys[pg.K_LEFT] or keys[pg.K_a]:
            input_acc_x = -PLAYER_ACC_VALUE
        if keys[pg.K_RIGHT] or keys[pg.K_d]:
            input_acc_x = PLAYER_ACC_VALUE
            
        # Friction acceleration: opposes current horizontal velocity
        friction_acc_x = self.vel.x * PLAYER_FRICTION_COEFF
        
        self.acc.x = input_acc_x + friction_acc_x
        self.acc.y = PLAYER_GRAVITY # Vertical acceleration is gravity
        
        # 2. Update velocity using acceleration (Euler integration: v = v_initial + a*dt, dt=1 frame)
        self.vel += self.acc
        
        # Optional: cap speeds to prevent extreme velocities
        # if abs(self.vel.x) < 0.1: self.vel.x = 0 # Stop if moving very slowly horizontally (deadzone)
        # MAX_FALL_SPEED = 15
        # if self.vel.y > MAX_FALL_SPEED: self.vel.y = MAX_FALL_SPEED

        # 3. Update position based on velocity, handling collisions for each axis separately
        
        # --- Horizontal Movement & Collision ---
        self.pos.x += self.vel.x
        self.rect.centerx = round(self.pos.x) # Update rect's X-center from float pos.x for collision checks
        
        self.check_collision_x(platforms) # Detect and respond to horizontal collisions
                                          # This modifies self.rect.centerx and self.vel.x if a collision occurs

        # Screen X-boundaries: ensure Mario-cat stays within screen horizontally
        if self.rect.left < 0:
            self.rect.left = 0
            if self.vel.x < 0: self.vel.x = 0 # Stop horizontal velocity if hitting left wall
        elif self.rect.right > SCREEN_WIDTH: # Use elif to handle one boundary at a time
            self.rect.right = SCREEN_WIDTH
            if self.vel.x > 0: self.vel.x = 0 # Stop horizontal velocity if hitting right wall
        
        self.pos.x = self.rect.centerx # Sync float pos.x with the final integer rect.centerx after collisions and bounds

        # --- Vertical Movement & Collision ---
        self.on_ground = False # Assume Mario-cat is airborne, check_collision_y will confirm if landed
        self.pos.y += self.vel.y
        self.rect.bottom = round(self.pos.y) # Update rect's bottom from float pos.y for collision checks

        self.check_collision_y(platforms) # Detect and respond to vertical collisions
                                          # This modifies self.rect.bottom/top, self.vel.y, and self.on_ground

        self.pos.y = self.rect.bottom # Sync float pos.y with the final integer rect.bottom after collisions

    def check_collision_x(self, platforms):
        # Player's self.rect is already updated based on its new X position for this frame
        collided_platforms = pg.sprite.spritecollide(self, platforms, False) # Get list of platforms player is touching
        for plat in collided_platforms:
            if self.vel.x > 0: # Mario-cat is moving right and collided
                self.rect.right = plat.rect.left # Align Mario-cat's right edge with platform's left edge
                self.vel.x = 0 # Stop horizontal movement
            elif self.vel.x < 0: # Mario-cat is moving left and collided
                self.rect.left = plat.rect.right # Align Mario-cat's left edge with platform's right edge
                self.vel.x = 0 # Stop horizontal movement
            self.pos.x = self.rect.centerx # Update float pos.x from the corrected integer rect position

    def check_collision_y(self, platforms):
        # Player's self.rect is already updated based on its new Y position for this frame
        collided_platforms = pg.sprite.spritecollide(self, platforms, False)
        for plat in collided_platforms:
            if self.vel.y > 0: # Mario-cat is moving down (falling) and collided
                self.rect.bottom = plat.rect.top # Align Mario-cat's bottom with platform's top
                self.vel.y = 0 # Stop vertical movement
                self.on_ground = True # Mario-cat has landed, nya!
            elif self.vel.y < 0: # Mario-cat is moving up (jumping) and collided (bonked head)
                self.rect.top = plat.rect.bottom # Align Mario-cat's top with platform's bottom
                self.vel.y = 0 # Stop vertical movement
            self.pos.y = self.rect.bottom # Update float pos.y from the corrected integer rect position

# --- Platform Class, solid ground for paws! ---
class Platform(pg.sprite.Sprite):
    def __init__(self, x, y, w, h, color):
        super().__init__()
        self.surf = pg.Surface((w, h))
        self.surf.fill(color) # Pretty platform colors, nya!
        self.rect = self.surf.get_rect(topleft = (x,y))

# --- Game Initialization, meow! ---
def game_init_purrfect():
    pg.init() # Initialize Pygame, nya!
    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pg.display.set_caption(TITLE)
    clock = pg.time.Clock()
    return screen, clock

# --- Game Loop, where the fun happens, nya! ---
def game_loop_meow(screen, clock):
    player = Player() # Our star, Mario-cat!
    
    platforms = pg.sprite.Group() # Group to hold all platform sprites
    for p_data in PLATFORM_LIST:
        plat = Platform(*p_data) # Unpack platform data (x, y, w, h, color)
        platforms.add(plat)

    # The all_sprites group from the original code isn't used for drawing/updating in this setup,
    # as drawing is handled manually below. It can be added if preferred for other Pygame features.

    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE or event.key == pg.K_UP or event.key == pg.K_w:
                    player.jump() # Jump, Mario-cat, jump! Nya!
                if event.key == pg.K_ESCAPE: # Escape to quit, purr
                    running = False

        # Update game state, meow!
        player.update(platforms) # Update player, passing platforms for collision detection

        # Draw / Render, purr!
        screen.fill(SKY_BLUE) # Fill screen with pretty sky blue, nya!
        
        # Draw all platforms
        for plat in platforms:
            screen.blit(plat.surf, plat.rect)
        # Draw our Mario-cat!
        screen.blit(player.surf, player.rect) 

        pg.display.flip() # Update the full screen to show changes, meow!
        clock.tick(FPS) # Control game speed to run at FPS, nya!

    pg.quit() # Uninitialize Pygame modules
    sys.exit() # Exit the program, bye-bye, purr!

# --- Let's start the game, meow! ---
if __name__ == '__main__':
    meow_screen, meow_clock = game_init_purrfect()
    game_loop_meow(meow_screen, meow_clock)

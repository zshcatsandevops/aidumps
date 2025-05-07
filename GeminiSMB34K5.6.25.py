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
PLAYER_ACC = 0.7  # Acceleration, nya!
PLAYER_FRICTION = -0.12 # Gotta slow down, purr
PLAYER_GRAVITY = 0.7 # Meow, gravity!
PLAYER_JUMP_STRENGTH = -15 # How high can Mario-cat jump, nya?

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
        # Using a simple rectangle for Mario-cat, nya!
        self.surf = pg.Surface((PLAYER_WIDTH, PLAYER_HEIGHT))
        self.surf.fill(RED) # Mario-cat is red, purr!
        self.rect = self.surf.get_rect()
        
        # Kinematics, meow!
        self.pos = pg.math.Vector2((SCREEN_WIDTH / 2, SCREEN_HEIGHT - 80)) # Start position
        self.vel = pg.math.Vector2(0, 0)
        self.acc = pg.math.Vector2(0, 0)
        self.on_ground = False # Is Mario-cat on the ground, nya?

    def move(self):
        self.acc = pg.math.Vector2(0, PLAYER_GRAVITY) # Gravity always pulls, meow!
        
        keys = pg.key.get_pressed()
        if keys[pg.K_LEFT] or keys[pg.K_a]:
            self.acc.x = -PLAYER_ACC
        if keys[pg.K_RIGHT] or keys[pg.K_d]:
            self.acc.x = PLAYER_ACC
            
        # Apply friction, purr
        self.acc.x += self.vel.x * PLAYER_FRICTION
        # Equations of motion, nya!
        self.vel += self.acc
        self.pos += self.vel + 0.5 * self.acc # Little physics meowgic!

        # Keep Mario-cat on screen, purr!
        if self.pos.x > SCREEN_WIDTH - PLAYER_WIDTH:
            self.pos.x = SCREEN_WIDTH - PLAYER_WIDTH
            self.vel.x = 0 # Stop at edge, nya
        if self.pos.x < 0:
            self.pos.x = 0
            self.vel.x = 0 # Stop at edge, nya
            
        self.rect.midbottom = self.pos # Update rect position, meow!

    def jump(self):
        if self.on_ground: # Can only jump if on ground, purr!
            self.vel.y = PLAYER_JUMP_STRENGTH
            self.on_ground = False # Mario-cat is in the air, nya!

    def update(self, platforms):
        self.move()
        self.check_collision_y(platforms) # Check vertical collisions first, meow!
        self.check_collision_x(platforms) # Then horizontal, purr!
        self.rect.topleft = (self.pos.x, self.pos.y - PLAYER_HEIGHT) # Adjust based on midbottom for drawing

    def check_collision_y(self, platforms):
        self.on_ground = False # Assume not on ground until collision detected, nya
        self.pos.y += self.vel.y # Move vertically
        self.rect.midbottom = self.pos # Update rect for collision check

        for plat in platforms:
            if self.rect.colliderect(plat.rect):
                if self.vel.y > 0: # Moving down, purr
                    self.pos.y = plat.rect.top + 1 # Land on top of platform
                    self.vel.y = 0 # Stop vertical movement
                    self.on_ground = True # Mario-cat landed, nya!
                elif self.vel.y < 0: # Moving up, meow
                    self.pos.y = plat.rect.bottom + PLAYER_HEIGHT # Bonk head
                    self.vel.y = 0 # Stop vertical movement
        self.rect.midbottom = self.pos # Final update after y-collision

    def check_collision_x(self, platforms):
        self.pos.x += self.vel.x # Move horizontally
        self.rect.midbottom = (self.pos.x, self.pos.y) # Update rect for collision check

        for plat in platforms:
            if self.rect.colliderect(plat.rect):
                if self.vel.x > 0: # Moving right, purr
                    self.pos.x = plat.rect.left - (PLAYER_WIDTH / 2)
                    self.vel.x = 0
                elif self.vel.x < 0: # Moving left, meow
                    self.pos.x = plat.rect.right + (PLAYER_WIDTH / 2)
                    self.vel.x = 0
        self.rect.midbottom = self.pos # Final update after x-collision


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
    
    platforms = pg.sprite.Group()
    for p_data in PLATFORM_LIST:
        plat = Platform(*p_data) # Unpack platform data, purr!
        platforms.add(plat)

    all_sprites = pg.sprite.Group()
    all_sprites.add(player)
    for plat in platforms: # Add platforms to all_sprites for drawing (optional if you draw them separately)
        all_sprites.add(plat)

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

        # Update, meow!
        player.update(platforms) # Pass platforms for collision detection

        # Draw / Render, purr!
        screen.fill(SKY_BLUE) # Fill screen with pretty sky blue, nya!
        
        # Draw all sprites (or individually)
        # For this example, drawing platforms first, then player
        for plat in platforms:
            screen.blit(plat.surf, plat.rect)
        screen.blit(player.surf, player.rect) # Draw our Mario-cat!

        pg.display.flip() # Update the full screen, meow!
        clock.tick(FPS) # Control game speed, nya!

    pg.quit()
    sys.exit() # Bye-bye, purr!

# --- Let's start the game, meow! ---
if __name__ == '__main__':
    meow_screen, meow_clock = game_init_purrfect()
    game_loop_meow(meow_screen, meow_clock)

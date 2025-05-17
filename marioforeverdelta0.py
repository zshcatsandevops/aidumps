import pygame
import sys

# ------------------------------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------------------------------
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
FPS = 60

# Dummy level layout size (for quick demonstration)
LEVEL_WIDTH = 2000
LEVEL_HEIGHT = 480

# Define some basic colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED   = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE  = (0, 0, 255)
GRAY  = (128, 128, 128)

pygame.init()
pygame.display.set_caption("Super Mario World 2.5 (FAN DEMO - NOT OFFICIAL)")
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 24)

# ------------------------------------------------------------------------------------
# STATE MANAGEMENT
# ------------------------------------------------------------------------------------
STATE_MAIN_MENU = 0
STATE_OVERWORLD = 1
STATE_LEVEL     = 2

current_state = STATE_MAIN_MENU

# Current level index (0-4 for 5 levels)
current_level = 0

# ------------------------------------------------------------------------------------
# BASIC CLASSES
# ------------------------------------------------------------------------------------
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((32, 32))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.speed = 5
        self.jump_power = 10

    def update(self, platforms):
        # Horizontal movement
        self.rect.x += self.vel_x

        # Check horizontal collisions
        collided_platforms = pygame.sprite.spritecollide(self, platforms, False)
        for plat in collided_platforms:
            if self.vel_x > 0:  # moving right
                self.rect.right = plat.rect.left
            elif self.vel_x < 0:  # moving left
                self.rect.left = plat.rect.right

        # Vertical movement
        self.vel_y += 0.5  # simple gravity
        if self.vel_y > 10:
            self.vel_y = 10

        self.rect.y += self.vel_y

        # Check vertical collisions
        collided_platforms = pygame.sprite.spritecollide(self, platforms, False)
        if collided_platforms:
            for plat in collided_platforms:
                # If moving down
                if self.vel_y > 0:
                    self.rect.bottom = plat.rect.top
                    self.on_ground = True
                # If moving up
                elif self.vel_y < 0:
                    self.rect.top = plat.rect.bottom
                self.vel_y = 0
        else:
            self.on_ground = False

    def jump(self):
        if self.on_ground:
            self.vel_y = -self.jump_power
            self.on_ground = False

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect(topleft=(x, y))

# ------------------------------------------------------------------------------------
# CREATE OVERWORLD NODES
# ------------------------------------------------------------------------------------
# For a simple overworld, imagine 5 circles in a line representing 5 levels.
class OverworldNode:
    def __init__(self, x, y, level_num):
        self.x = x
        self.y = y
        self.level_num = level_num
        self.radius = 20

overworld_nodes = [
    OverworldNode(100, SCREEN_HEIGHT//2, 0),
    OverworldNode(200, SCREEN_HEIGHT//2, 1),
    OverworldNode(300, SCREEN_HEIGHT//2, 2),
    OverworldNode(400, SCREEN_HEIGHT//2, 3),
    OverworldNode(500, SCREEN_HEIGHT//2, 4),
]

player_node_index = 0  # start at node 0

# ------------------------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------------------------
def draw_text(surf, text, x, y, color=WHITE):
    txt = font.render(text, True, color)
    surf.blit(txt, (x, y))

def main_menu():
    screen.fill(BLACK)
    draw_text(screen, "SUPER MARIO WORLD 2.5 FAN DEMO", 100, 150, WHITE)
    draw_text(screen, "Press [ENTER] to go to Overworld", 100, 200, WHITE)
    draw_text(screen, "Press [ESC] to Quit", 100, 250, WHITE)
    pygame.display.flip()

def overworld():
    global current_state, current_level, player_node_index

    screen.fill(BLACK)
    draw_text(screen, "OVERWORLD MAP", 10, 10, WHITE)
    draw_text(screen, "Use [LEFT]/[RIGHT] to move, [ENTER] to select level", 10, 40, WHITE)

    # Draw nodes
    for node in overworld_nodes:
        color = RED if node.level_num == player_node_index else GRAY
        pygame.draw.circle(screen, color, (node.x, node.y), node.radius)

    pygame.display.flip()

    # Handle movement + selection
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        player_node_index = max(0, player_node_index - 1)
    if keys[pygame.K_RIGHT]:
        player_node_index = min(4, player_node_index + 1)

def run_level(level_index):
    """Simple level that ends if player reaches a certain x or falls out."""
    global current_state

    # Create a dummy platform floor and some floating platforms
    platform_list = pygame.sprite.Group()
    # Floor
    platform_list.add(Platform(0, SCREEN_HEIGHT-50, LEVEL_WIDTH, 50))
    # A few random floating platforms (for demonstration)
    platform_list.add(Platform(200, 350, 100, 20))
    platform_list.add(Platform(400, 300, 100, 20))
    platform_list.add(Platform(600, 250, 100, 20))

    # Create player
    player = Player(50, SCREEN_HEIGHT-100)

    # Level camera offset
    camera_x = 0

    level_running = True
    while level_running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    level_running = False
                elif event.key == pygame.K_SPACE:
                    player.jump()

        # Handle input for left/right
        keys = pygame.key.get_pressed()
        player.vel_x = 0
        if keys[pygame.K_LEFT]:
            player.vel_x = -player.speed
        elif keys[pygame.K_RIGHT]:
            player.vel_x = player.speed

        # Update player
        player.update(platform_list)

        # Update camera offset
        # Keep player near center of screen if possible
        camera_x = -player.rect.x + SCREEN_WIDTH//2
        if camera_x > 0:
            camera_x = 0
        if camera_x < SCREEN_WIDTH - LEVEL_WIDTH:
            camera_x = SCREEN_WIDTH - LEVEL_WIDTH

        # Check if player "wins" the level (reaches far right)
        if player.rect.x > LEVEL_WIDTH - 50:
            level_running = False

        # Check if player "falls" out of the screen
        if player.rect.y > SCREEN_HEIGHT:
            level_running = False

        # Render
        screen.fill(BLACK)
        # Draw platforms
        for plat in platform_list:
            screen.blit(plat.image, (plat.rect.x + camera_x, plat.rect.y))
        # Draw player
        screen.blit(player.image, (player.rect.x + camera_x, player.rect.y))

        draw_text(screen, f"Level {level_index+1}", 10, 10, WHITE)

        pygame.display.flip()

    # After level finishes, return to overworld
    current_state = STATE_OVERWORLD

# ------------------------------------------------------------------------------------
# MAIN LOOP
# ------------------------------------------------------------------------------------
running = True
while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if current_state == STATE_MAIN_MENU:
                if event.key == pygame.K_RETURN:
                    current_state = STATE_OVERWORLD
                elif event.key == pygame.K_ESCAPE:
                    running = False
            elif current_state == STATE_OVERWORLD:
                if event.key == pygame.K_RETURN:
                    current_level = player_node_index
                    current_state = STATE_LEVEL

    # State updates
    if current_state == STATE_MAIN_MENU:
        main_menu()
    elif current_state == STATE_OVERWORLD:
        overworld()
    elif current_state == STATE_LEVEL:
        run_level(current_level)

pygame.quit()
sys.exit()

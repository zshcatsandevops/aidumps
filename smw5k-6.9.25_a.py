# main.py

import asyncio
import platform
import pygame
import logging
import random

# ai_core is a dependency that was not provided.
# This code assumes it has a 'generate_level' method
# that returns a dictionary with 'platforms' and 'decorations'.
try:
    from ai_core import AICore # type: ignore
except ImportError:
    # Create a mock AICore if the real one isn't available.
    # This allows the game to run for demonstration and testing.
    print("Warning: 'ai_core.py' not found. Using mock AI Core for level generation.")
    class AICore:
        def generate_level(self):
            """Generates a simple, static level for demonstration."""
            return {
                'platforms': [
                    {'x': 0, 'y': 380, 'width': 250, 'height': 20},
                    {'x': 300, 'y': 320, 'width': 100, 'height': 20},
                    {'x': 450, 'y': 260, 'width': 150, 'height': 20},
                    {'x': 200, 'y': 200, 'width': 100, 'height': 20},
                ],
                'decorations': [
                    {'type': 'hill', 'x': 30, 'y': 380},
                    {'type': 'cloud', 'x': 100, 'y': 50},
                    {'type': 'tree', 'x': 480, 'y': 260},
                    {'type': 'cloud', 'x': 400, 'y': 80},
                ]
            }

# --- Pygame and Game Setup ---

# Configure logging to write to game_log.txt
logging.basicConfig(
    filename='game_log.txt',
    filemode='w',  # Overwrite log file on each run
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Super Mario World Clone")
clock = pygame.time.Clock()
FPS = 60

# --- Player and Level Setup ---
player = pygame.Rect(50, 300, 30, 40) # Made player slightly thinner
player_speed = 5
jump_power = -12
gravity = 0.5
player_velocity_y = 0
on_ground = False
current_level_index = 0

# Initialize AI core and load initial levels
ai_core = AICore()
levels = [ai_core.generate_level() for _ in range(2)]  # Pre-generate 2 levels

# --- Drawing Functions ---
# (Slightly enhanced for better visuals)
def draw_hill(screen, x, y):
    points = [(x, y), (x + 60, y - 60), (x + 120, y)]
    pygame.draw.polygon(screen, (34, 139, 34), points)

def draw_cloud(screen, x, y):
    pygame.draw.ellipse(screen, (255, 255, 255), (x, y, 90, 35))
    pygame.draw.ellipse(screen, (255, 255, 255), (x + 25, y - 15, 90, 35))

def draw_tree(screen, x, y):
    pygame.draw.rect(screen, (139, 69, 19), (x, y - 40, 20, 40)) # Trunk
    pygame.draw.circle(screen, (0, 128, 0), (x + 10, y - 60), 35) # Leaves

def draw_house(screen, x, y):
    pygame.draw.rect(screen, (222, 184, 135), (x, y - 40, 60, 40)) # Body
    pygame.draw.polygon(screen, (165, 42, 42), [(x, y - 40), (x + 30, y - 70), (x + 60, y - 40)]) # Roof

draw_funcs = {
    'hill': draw_hill, 'cloud': draw_cloud,
    'tree': draw_tree, 'house': draw_house
}

# --- Core Game Logic ---

def load_level(level_data):
    """Resets the game state with new level data."""
    global platforms, decorations, player, player_velocity_y, on_ground
    platforms = [pygame.Rect(p['x'], p['y'], p['width'], p['height']) for p in level_data['platforms']]
    decorations = level_data['decorations']
    player.x, player.y = 50, 300  # Reset player position
    player_velocity_y = 0
    on_ground = False
    logging.info(f'Level {current_level_index} loaded with {len(platforms)} platforms.')

# Initialize the first level
load_level(levels[current_level_index])

async def main():
    global player_velocity_y, on_ground, current_level_index, levels

    running = True
    while running:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and on_ground:
                    player_velocity_y = jump_power
                    on_ground = False
                    logging.info('Player jumped.')

        # --- Player Movement ---
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player.x -= player_speed
        if keys[pygame.K_RIGHT]:
            player.x += player_speed

        # Keep player within horizontal screen bounds
        if player.left < 0:
            player.left = 0
        
        # --- Physics and Collisions ---
        if not on_ground:
            player_velocity_y += gravity
            player.y += player_velocity_y

        # Assume not on ground until a collision proves otherwise
        on_ground = False
        for plat in platforms:
            if player.colliderect(plat):
                # BUG FIX: Improved collision logic.
                # This now robustly checks if the player is landing on top of a platform,
                # preventing a bug where hitting a platform from the side would teleport the player up.
                if player_velocity_y > 0 and player.bottom <= plat.top + player_velocity_y:
                    player.bottom = plat.top
                    player_velocity_y = 0
                    on_ground = True
                    break

        # --- Game State Logic ---
        # BUG FIX: This is the main fix. Reset the level if the player falls off the screen.
        if player.top > HEIGHT + 50:
            logging.warning("Player fell out of the world! Resetting level.")
            load_level(levels[current_level_index])

        # Transition to the next level
        if player.right > WIDTH:
            logging.info("Player reached the end of the level.")
            current_level_index = (current_level_index + 1) % len(levels)
            if current_level_index == 0:
                logging.info("Generating new set of levels.")
                levels = [ai_core.generate_level() for _ in range(2)]
            load_level(levels[current_level_index])

        # --- Drawing ---
        screen.fill((135, 206, 250))  # Sky blue background
        for deco in decorations:
            if deco['type'] in draw_funcs:
                draw_funcs[deco['type']](screen, deco['x'], deco['y'])
        for plat in platforms:
            pygame.draw.rect(screen, (34, 139, 34), plat)
        pygame.draw.rect(screen, (255, 69, 0), player) # Red-orange player

        pygame.display.flip()
        
        # BUG FIX: Changed sleep time to 0. clock.tick() already manages the framerate.
        # asyncio.sleep(0) correctly yields control to the async loop, which is necessary
        # for running in web environments (like Emscripten) without adding extra delay.
        await asyncio.sleep(0)
        clock.tick(FPS)

    pygame.quit()
    logging.info("Game exited successfully.")

# --- Main Execution Block ---
if __name__ == "__main__":
    # This setup allows the game to run on both desktop and web (via Emscripten/pygbag)
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        pygame.quit()

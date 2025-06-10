import asyncio
import platform
import pygame
import logging

# Configure logging to write to game_log.txt
logging.basicConfig(filename='game_log.txt', level=logging.INFO, format='%(asctime)s: %(message)s')

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((600, 400))
pygame.display.set_caption("Super Mario World Clone")
clock = pygame.time.Clock()
FPS = 60

# Player setup
player = pygame.Rect(50, 310, 40, 40)  # Start with bottom at y=350
player_speed = 5
jump_power = -10
gravity = 0.5
player_velocity_y = 0
is_jumping = False
current_level = 0

# Define level data
level_data = [
    # Level 1: Hilly terrain with trees
    {
        'platforms': [
            pygame.Rect(0, 350, 600, 50),  # Ground
            pygame.Rect(100, 300, 100, 20),  # Platform 1
            pygame.Rect(400, 250, 100, 20)   # Platform 2
        ],
        'decorations': [
            ('hill', 0, 350),
            ('hill', 200, 350),
            ('hill', 400, 350),
            ('cloud', 100, 50),
            ('tree', 200, 350)
        ]
    },
    # Level 2: Cloudy skies with houses
    {
        'platforms': [
            pygame.Rect(0, 350, 600, 50),  # Ground
            pygame.Rect(200, 280, 100, 20),  # Platform 1
            pygame.Rect(50, 200, 100, 20)    # Platform 2
        ],
        'decorations': [
            ('cloud', 50, 60),
            ('cloud', 300, 80),
            ('cloud', 500, 60),
            ('house', 500, 350),
            ('tree', 100, 350)
        ]
    }
]

# Drawing functions for SMW overworld vibe
def draw_hill(screen, x, y):
    points = [(x, y), (x + 50, y - 50), (x + 100, y)]
    pygame.draw.polygon(screen, (0, 128, 0), points)

def draw_cloud(screen, x, y):
    pygame.draw.ellipse(screen, (255, 255, 255), (x, y, 60, 20))

def draw_tree(screen, x, y):
    trunk = pygame.Rect(x, y - 40, 20, 40)
    leaves = pygame.Rect(x - 10, y - 70, 40, 30)
    pygame.draw.rect(screen, (139, 69, 19), trunk)
    pygame.draw.ellipse(screen, (0, 128, 0), leaves)

def draw_house(screen, x, y):
    body = pygame.Rect(x, y - 40, 60, 40)
    roof_points = [(x, y - 40), (x + 30, y - 60), (x + 60, y - 40)]
    pygame.draw.rect(screen, (255, 255, 0), body)
    pygame.draw.polygon(screen, (255, 0, 0), roof_points)

# Map decoration types to functions
draw_functions = {
    'hill': draw_hill,
    'cloud': draw_cloud,
    'tree': draw_tree,
    'house': draw_house
}

# Load level function
def load_level(level_index):
    global platforms, decorations
    level = level_data[level_index]
    platforms = level['platforms']
    decorations = level['decorations']
    player.x = 50
    player.y = 310
    player_velocity_y = 0
    is_jumping = False
    logging.info(f'Loaded level {level_index + 1}')

# Initialize first level
platforms = []
decorations = []
load_level(current_level)

async def main():
    global player_velocity_y, is_jumping, current_level
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                logging.info(f'Key pressed: {pygame.key.name(event.key)}')
                if event.key == pygame.K_SPACE and not is_jumping:
                    player_velocity_y = jump_power
                    is_jumping = True
                    logging.info(f'Player jumped at position {player.x},{player.y}')

        # Player movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            player.x -= player_speed
            logging.info(f'Player moved left to {player.x},{player.y}')
        if keys[pygame.K_RIGHT]:
            player.x += player_speed
            logging.info(f'Player moved right to {player.x},{player.y}')

        # Apply gravity
        player_velocity_y += gravity
        player.y += player_velocity_y

        # Platform collisions
        for platform in platforms:
            if player.colliderect(platform):
                if player_velocity_y > 0:  # Falling
                    player.y = platform.top - player.height
                    player_velocity_y = 0
                    is_jumping = False
                    break

        # Keep player in bounds
        player.clamp_ip(screen.get_rect())

        # Check for level transition
        if player.x > 550:
            current_level = (current_level + 1) % len(level_data)
            load_level(current_level)

        # Draw everything
        screen.fill((135, 206, 235))  # Sky blue background

        # Background elements
        for deco_type, x, y in decorations:
            draw_functions[deco_type](screen, x, y)

        # Platforms
        for platform in platforms:
            pygame.draw.rect(screen, (0, 255, 0), platform)

        # Player
        pygame.draw.rect(screen, (255, 0, 0), player)

        pygame.display.flip()
        clock.tick(FPS)
        await asyncio.sleep(1.0 / FPS)

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())

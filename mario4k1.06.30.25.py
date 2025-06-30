import pygame
import asyncio
import platform

# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mario Forever - SMB3 GBA Style")
clock = pygame.time.Clock()
FPS = 60

# Colors to match SMB3 GBA palette
SKY_BLUE = (107, 140, 255)
GROUND_BROWN = (139, 69, 19)
BLOCK_ORANGE = (255, 165, 0)
MARIO_SKIN = (255, 222, 173)
MARIO_RED = (200, 0, 0)
MARIO_BLUE = (0, 0, 139)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
FLAGPOLE_GRAY = (169, 169, 169)
GREEN = (0, 128, 0)

# Game state
worlds = [
    {"level": [[0, 500, 2000, 100], [400, 400, 100, 50], [600, 300, 100, 50], [1200, 400, 100, 50], [1800, 500, 200, 100]], "flagpole": [1900, 200]},
    {"level": [[0, 500, 2000, 100], [300, 350, 150, 50], [700, 400, 100, 50], [1500, 300, 100, 50]], "flagpole": [1900, 200]},
    {"level": [[0, 500, 2000, 100], [500, 400, 100, 50], [800, 300, 100, 50], [1400, 350, 150, 50]], "flagpole": [1900, 200]},
    {"level": [[0, 500, 2000, 100], [600, 350, 100, 50], [900, 400, 100, 50], [1600, 300, 100, 50]], "flagpole": [1900, 200]},
    {"level": [[0, 500, 2000, 100], [400, 400, 150, 50], [700, 300, 100, 50], [1300, 350, 100, 50]], "flagpole": [1900, 200]},
]
current_world = 0
score = 0
game_complete = False

# Mario properties
mario_x, mario_y = 50, 450
mario_width, mario_height = 32, 32
mario_vx, mario_vy = 0, 0
mario_jumping = False
mario_frame = 0
mario_direction = 1  # 1 for right, -1 for left
camera_x = 0

# Draw Mario using shapes to approximate SMB3 GBA style
def draw_mario(surface, x, y, frame, direction):
    mario_surface = pygame.Surface((mario_width, mario_height), pygame.SRCALPHA)
    # Head
    pygame.draw.ellipse(mario_surface, MARIO_SKIN, (8, 4, 16, 12))
    # Hat
    hat_points = [(8, 4), (24, 4), (24, 8), (16, 8), (16, 12), (8, 12)]
    if direction == -1:
        hat_points = [(mario_width - p[0], p[1]) for p in hat_points]
    pygame.draw.polygon(mario_surface, MARIO_RED, hat_points)
    # Eyes
    eye_x = 16 if direction == 1 else 12
    pygame.draw.rect(mario_surface, BLACK, (eye_x, 8, 4, 4))
    # Body
    pygame.draw.rect(mario_surface, MARIO_RED, (8, 16, 16, 12))
    # Overalls
    pygame.draw.rect(mario_surface, MARIO_BLUE, (8, 20, 16, 12))
    # Arms
    arm_x = 4 if frame == 0 else 0
    if direction == -1:
        arm_x = mario_width - arm_x - 8
    pygame.draw.rect(mario_surface, MARIO_RED, (arm_x, 16, 8, 8))
    # Legs
    leg_x = 8 if frame == 0 else 12
    if direction == -1:
        leg_x = mario_width - leg_x - 8
    pygame.draw.rect(mario_surface, MARIO_BLUE, (leg_x, 28, 8, 4))
    surface.blit(mario_surface, (x - camera_x, y))

# Draw ground and platforms
def draw_level(surface, level):
    for platform in level:
        x, y, w, h = platform
        # Ground
        pygame.draw.rect(surface, GROUND_BROWN, (x - camera_x, y, w, h))
        # Top grass
        pygame.draw.rect(surface, GREEN, (x - camera_x, y - 4, w, 4))
        # Block details
        for i in range(0, w, 16):
            pygame.draw.rect(surface, BLOCK_ORANGE, (x - camera_x + i, y, 16, 16), 2)

# Draw flagpole
def draw_flagpole(surface, x, y):
    pygame.draw.line(surface, FLAGPOLE_GRAY, (x - camera_x, y), (x - camera_x, y + 300), 4)
    pygame.draw.rect(surface, GREEN, (x - camera_x - 16, y + 280, 32, 16))

# Draw game complete screen
def draw_game_complete(surface):
    surface.fill(SKY_BLUE)
    font = pygame.font.SysFont("arial", 48)
    text = font.render("Game Complete!", True, WHITE)
    surface.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 100))
    # Draw celebratory Mario
    draw_mario(surface, WIDTH // 2 - 16, HEIGHT // 2, 0, 1)
    pygame.display.flip()

# Collision detection
def check_collision(x, y, width, height, platforms):
    mario_rect = pygame.Rect(x, y, width, height)
    for platform in platforms:
        plat_rect = pygame.Rect(platform[0], platform[1], platform[2], platform[3])
        if mario_rect.colliderect(plat_rect):
            return platform
    return None

# Main game setup
def setup():
    global mario_x, mario_y, mario_vx, mario_vy, mario_jumping, camera_x, score
    mario_x, mario_y = 50, 450
    mario_vx, mario_vy = 0, 0
    mario_jumping = False
    camera_x = 0
    score = 0

# Main game loop
async def main():
    global mario_x, mario_y, mario_vx, mario_vy, mario_jumping, mario_frame, mario_direction
    global camera_x, current_world, score, game_complete
    setup()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Input handling
        keys = pygame.key.get_pressed()
        mario_vx = 0
        if keys[pygame.K_LEFT]:
            mario_vx = -5
            mario_direction = -1
        if keys[pygame.K_RIGHT]:
            mario_vx = 5
            mario_direction = 1
        if keys[pygame.K_SPACE] and not mario_jumping:
            mario_vy = -15
            mario_jumping = True

        # Physics
        mario_vy += 0.8  # Gravity
        mario_x += mario_vx
        mario_y += mario_vy

        # Animation
        if mario_vx != 0:
            mario_frame = (mario_frame + 1) % 20
        else:
            mario_frame = 0

        # Collision with platforms
        collision = check_collision(mario_x, mario_y, mario_width, mario_height, worlds[current_world]["level"])
        if collision:
            if mario_vy > 0:  # Landing
                mario_y = collision[1] - mario_height
                mario_vy = 0
                mario_jumping = False
            elif mario_vy < 0:  # Hitting head
                mario_y = collision[1] + collision[3]
                mario_vy = 0

        # Check for pits
        if mario_y > HEIGHT:
            setup()  # Restart level

        # Check for flagpole
        flagpole = worlds[current_world]["flagpole"]
        if mario_x >= flagpole[0] and mario_y >= flagpole[1]:
            score += 100
            current_world += 1
            if current_world >= len(worlds):
                game_complete = True
                running = False
            else:
                setup()

        # Camera follow
        camera_x = max(0, mario_x - WIDTH // 2)

        # Drawing
        screen.fill(SKY_BLUE)
        draw_level(screen, worlds[current_world]["level"])
        draw_flagpole(screen, flagpole[0], flagpole[1])
        draw_mario(screen, mario_x, mario_y, mario_frame // 10, mario_direction)
        font = pygame.font.SysFont("arial", 24)
        text = font.render(f"World {current_world + 1}-1 Score: {score}", True, WHITE)
        screen.blit(text, (10, 10))
        pygame.display.flip()

        await asyncio.sleep(1.0 / FPS)

    if game_complete:
        draw_game_complete(screen)
        await asyncio.sleep(5.0)  # Show completion screen for 5 seconds

# Run game
if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())

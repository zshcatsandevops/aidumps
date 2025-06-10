import asyncio
import platform
import pygame
import logging

# Configure logging to write to 1.txt
logging.basicConfig(filename='1.txt', level=logging.INFO, format='%(asctime)s: %(message)s')

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((600, 400))
pygame.display.set_caption("Super Mario World Clone")
clock = pygame.time.Clock()
FPS = 60

# Simple player rectangle
player = pygame.Rect(50, 350, 40, 40)
player_speed = 5
jump_power = -10
gravity = 0.5
player_velocity_y = 0
is_jumping = False

async def main():
    global player_velocity_y, is_jumping
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

        # Ground collision
        if player.y > 350:
            player.y = 350
            player_velocity_y = 0
            is_jumping = False

        # Keep player in bounds
        player.clamp_ip(screen.get_rect())

        # Draw
        screen.fill((135, 206, 235))  # Sky blue background
        pygame.draw.rect(screen, (255, 0, 0), player)  # Red player rectangle
        pygame.display.flip()
        clock.tick(FPS)
        await asyncio.sleep(1.0 / FPS)

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())

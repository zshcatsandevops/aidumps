import pygame

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("AI-Generated Pong")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Game objects
ball = pygame.Rect(WIDTH // 2 - 10, HEIGHT // 2 - 10, 20, 20)
paddle1 = pygame.Rect(50, HEIGHT // 2 - 50, 10, 100)
paddle2 = pygame.Rect(WIDTH - 60, HEIGHT // 2 - 50, 10, 100)

# Ball velocity
ball_dx, ball_dy = 4, 4

# Game loop
running = True
clock = pygame.time.Clock()
while running:
    screen.fill(BLACK)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # Move the ball
    ball.x += ball_dx
    ball.y += ball_dy
    
    # Ball collision with walls
    if ball.top <= 0 or ball.bottom >= HEIGHT:
        ball_dy *= -1
    
    # Ball collision with paddles
    if ball.colliderect(paddle1) or ball.colliderect(paddle2):
        ball_dx *= -1
    
    # Draw objects
    pygame.draw.rect(screen, WHITE, paddle1)
    pygame.draw.rect(screen, WHITE, paddle2)
    pygame.draw.ellipse(screen, WHITE, ball)
    pygame.draw.aaline(screen, WHITE, (WIDTH // 2, 0), (WIDTH // 2, HEIGHT))
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()

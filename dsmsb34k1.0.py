Let me know if you'd like help with anything else. 🚀import pygame
import sys
from pygame.math import Vector2

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()
FPS = 60

# Game states
STATE_OVERWORLD = 0
STATE_LEVEL = 1

# Colors
SKY_BLUE = (135, 206, 235)
GROUND_GREEN = (34, 139, 34)
RED = (255, 0, 0)
BROWN = (139, 69, 19)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)

class Mario:
    def __init__(self):
        self.pos = Vector2(100, 400)
        self.vel = Vector2(0, 0)
        self.size = Vector2(30, 40)
        self.on_ground = True
        self.color = RED
        self.powerup = 0  # 0-small, 1-big, 2-fire

    def update(self, dt, platforms):
        gravity = 1200
        move_speed = 400
        jump_force = -600

        keys = pygame.key.get_pressed()
        
        # Horizontal movement
        self.vel.x = 0
        if keys[pygame.K_LEFT]:
            self.vel.x = -move_speed
        if keys[pygame.K_RIGHT]:
            self.vel.x = move_speed

        # Jumping
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vel.y = jump_force
            self.on_ground = False

        # Apply gravity
        self.vel.y += gravity * dt
        self.pos += self.vel * dt

        # Collision detection
        self.rect = pygame.Rect(self.pos.x, self.pos.y, self.size.x, self.size.y)
        self.on_ground = False
        
        for plat in platforms:
            if self.rect.colliderect(plat.rect):
                if self.vel.y > 0:
                    self.pos.y = plat.rect.top - self.size.y
                    self.vel.y = 0
                    self.on_ground = True
                elif self.vel.y < 0:
                    self.pos.y = plat.rect.bottom
                    self.vel.y = 0

    def draw(self, surface):
        # Draw Mario with hat
        pygame.draw.rect(surface, self.color, (self.pos.x, self.pos.y, self.size.x, self.size.y))
        pygame.draw.rect(surface, BROWN, (self.pos.x, self.pos.y - 10, self.size.x, 10))

class Platform:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = GROUND_GREEN

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)

class OverworldNode:
    def __init__(self, x, y, level_num):
        self.pos = Vector2(x, y)
        self.rect = pygame.Rect(x-20, y-20, 40, 40)
        self.level_num = level_num
        self.color = RED

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, self.pos, 20)
        pygame.draw.circle(surface, YELLOW, self.pos, 15)

class Game:
    def __init__(self):
        self.state = STATE_OVERWORLD
        self.nodes = []
        self.current_node = 0
        self.init_overworld()
        self.mario = Mario()
        self.platforms = [
            Platform(0, 500, 800, 100),
            Platform(200, 400, 100, 20),
            Platform(400, 300, 100, 20)
        ]
        self.camera_x = 0

    def init_overworld(self):
        self.nodes.append(OverworldNode(100, 100, 1))
        self.nodes.append(OverworldNode(300, 150, 2))
        self.nodes.append(OverworldNode(500, 100, 3))

    def run_level(self):
        self.state = STATE_LEVEL
        self.mario.pos = Vector2(100, 400)

    def update_overworld(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT]:
            self.current_node = min(self.current_node + 1, len(self.nodes)-1)
        if keys[pygame.K_LEFT]:
            self.current_node = max(self.current_node - 1, 0)
        if keys[pygame.K_RETURN]:
            self.run_level()

    def draw_overworld(self, surface):
        surface.fill(SKY_BLUE)
        # Draw paths
        pygame.draw.lines(surface, BLACK, False, [(n.pos.x, n.pos.y) for n in self.nodes], 5)
        # Draw nodes
        for i, node in enumerate(self.nodes):
            node.color = RED if i == self.current_node else GROUND_GREEN
            node.draw(surface)
        # Draw Mario
        pygame.draw.rect(surface, RED, (self.nodes[self.current_node].pos.x-15, 
            self.nodes[self.current_node].pos.y-30, 30, 40))

    def draw_level(self, surface):
        surface.fill(SKY_BLUE)
        
        # Apply camera
        camera_offset = Vector2(self.camera_x, 0)
        
        # Draw platforms
        for plat in self.platforms:
            offset_rect = plat.rect.move(-self.camera_x, 0)
            pygame.draw.rect(surface, plat.color, offset_rect)
        
        # Update camera
        self.camera_x = self.mario.pos.x - 400
        
        self.mario.draw(surface)

    def run(self):
        dt = clock.tick(FPS)/1000
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        if self.state == STATE_OVERWORLD:
            self.update_overworld()
            self.draw_overworld(screen)
        elif self.state == STATE_LEVEL:
            self.mario.update(dt, self.platforms)
            self.draw_level(screen)

        pygame.display.update()

if __name__ == "__main__":
    game = Game()
    while True:
        game.run()

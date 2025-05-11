import pygame
import sys
from pygame.math import Vector2

# Initialize Pygame
pygame.init()

# Constants (NES-style: slower movement)
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
GRAVITY = 600          # Slower gravity
MOVE_SPEED = 200       # Slower horizontal movement
JUMP_FORCE = -300      # Weaker jump

# Colors
SKY_BLUE = (135, 206, 235)
GROUND_GREEN = (34, 139, 34)
RED = (255, 0, 0)
BROWN = (139, 69, 19)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)

# Game States
STATE_OVERWORLD = 0
STATE_LEVEL = 1

# Input delay for overworld
OVERWORLD_DELAY = 0.2  # seconds

# Initialize Screen and Clock
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

class Mario:
    def __init__(self):
        self.pos = Vector2(100, 400)
        self.vel = Vector2(0, 0)
        self.size = Vector2(30, 40)
        self.on_ground = True
        self.color = RED
        self.rect = pygame.Rect(self.pos.x, self.pos.y, self.size.x, self.size.y)

    def update(self, dt, platforms):
        keys = pygame.key.get_pressed()

        # Horizontal Movement
        self.vel.x = 0
        if keys[pygame.K_LEFT]:
            self.vel.x = -MOVE_SPEED
        if keys[pygame.K_RIGHT]:
            self.vel.x = MOVE_SPEED

        # Jumping
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vel.y = JUMP_FORCE
            self.on_ground = False

        # Horizontal Movement + Collision
        self.pos.x += self.vel.x * dt
        self.rect.x = int(self.pos.x)

        for plat in platforms:
            if self.rect.colliderect(plat.rect):
                if self.vel.x > 0:
                    self.pos.x = plat.rect.left - self.size.x
                elif self.vel.x < 0:
                    self.pos.x = plat.rect.right
                self.rect.x = int(self.pos.x)

        # Vertical Movement + Gravity
        self.vel.y += GRAVITY * dt
        self.pos.y += self.vel.y * dt
        self.rect.y = int(self.pos.y)

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
                self.rect.y = int(self.pos.y)

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)
        pygame.draw.rect(surface, BROWN, (self.rect.x, self.rect.y - 10, self.rect.width, 10))

class Platform:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = GROUND_GREEN

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)

class OverworldNode:
    def __init__(self, x, y, level_num):
        self.pos = Vector2(x, y)
        self.rect = pygame.Rect(x - 20, y - 20, 40, 40)
        self.level_num = level_num
        self.color = RED

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), 20)
        pygame.draw.circle(surface, YELLOW, (int(self.pos.x), int(self.pos.y)), 15)

class Game:
    def __init__(self):
        self.state = STATE_OVERWORLD
        self.nodes = []
        self.current_node = 0
        self.overworld_time = 0  # Time tracker for input delay
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

    def update_overworld(self, dt):
        self.overworld_time += dt
        keys = pygame.key.get_pressed()

        if self.overworld_time >= OVERWORLD_DELAY:
            if keys[pygame.K_RIGHT]:
                self.current_node = min(self.current_node + 1, len(self.nodes) - 1)
                self.overworld_time = 0
            elif keys[pygame.K_LEFT]:
                self.current_node = max(self.current_node - 1, 0)
                self.overworld_time = 0

        if keys[pygame.K_RETURN]:
            self.run_level()

    def draw_overworld(self, surface):
        surface.fill(SKY_BLUE)
        pygame.draw.lines(surface, BLACK, False, [(int(n.pos.x), int(n.pos.y)) for n in self.nodes], 5)
        for i, node in enumerate(self.nodes):
            node.color = RED if i == self.current_node else GROUND_GREEN
            node.draw(surface)
        mario_rect = pygame.Rect(int(self.nodes[self.current_node].pos.x - 15), int(self.nodes[self.current_node].pos.y - 30), 30, 40)
        pygame.draw.rect(surface, RED, mario_rect)

    def draw_level(self, surface):
        surface.fill(SKY_BLUE)
        # Smooth camera lag
        target_camera_x = max(0, int(self.mario.pos.x - 400))
        self.camera_x = self.camera_x * 0.9 + target_camera_x * 0.1  # Lerp

        for plat in self.platforms:
            offset_rect = plat.rect.move(-self.camera_x, 0)
            plat.draw(surface)

        self.mario.draw(surface)

    def run(self):
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        if self.state == STATE_OVERWORLD:
            self.update_overworld(dt)
            self.draw_overworld(screen)
        elif self.state == STATE_LEVEL:
            self.mario.update(dt, self.platforms)
            self.draw_level(screen)

        pygame.display.update()

if __name__ == "__main__":
    game = Game()
    while True:
        game.run()

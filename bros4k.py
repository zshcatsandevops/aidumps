import pygame
import sys
from pygame.math import Vector2

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
GRAVITY = 600
MOVE_SPEED = 200
JUMP_FORCE = -300

# Colors
SKY_BLUE = (135, 206, 235)
GROUND_GREEN = (34, 139, 34)
DESERT_SAND = (255, 200, 0)
ICY_BLUE = (150, 200, 255)
RED = (255, 0, 0)
BROWN = (139, 69, 19)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)

# Game States
STATE_OVERWORLD = 0
STATE_LEVEL = 1

# Level Types
LEVEL_REGULAR = 0
LEVEL_FORTRESS = 1
LEVEL_CASTLE = 2
LEVEL_AIRSHIP = 3
LEVEL_SPECIAL = 4

# Overworld Config
OVERWORLD_DELAY = 0.2

# World Definitions (SMB3-style)
WORLDS = [
    {
        "name": "World 1",
        "bg_color": SKY_BLUE,
        "platform_color": GROUND_GREEN,
        "nodes": [
            {"pos": (100, 100), "type": LEVEL_REGULAR},
            {"pos": (300, 150), "type": LEVEL_REGULAR},
            {"pos": (500, 100), "type": LEVEL_CASTLE},
        ],
    },
    {
        "name": "World 2",
        "bg_color": ICY_BLUE,
        "platform_color": (255, 255, 255),
        "nodes": [
            {"pos": (100, 100), "type": LEVEL_REGULAR},
            {"pos": (300, 150), "type": LEVEL_FORTRESS},
            {"pos": (500, 100), "type": LEVEL_SPECIAL},
        ],
    },
    {
        "name": "World 3",
        "bg_color": (0, 100, 200),
        "platform_color": (200, 100, 0),
        "nodes": [{"pos": (200, 200), "type": LEVEL_AIRSHIP}],
    },
    # Add 5 more worlds following SMB3 style [[4]]
]

# Initialize Display
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
        # Draw Mario with hat
        pygame.draw.rect(surface, self.color, self.rect)
        pygame.draw.rect(surface, BROWN, (self.rect.x, self.rect.y - 10, self.rect.width, 10))

class Platform:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = GROUND_GREEN

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)

class OverworldNode:
    def __init__(self, pos, level_type):
        self.pos = Vector2(pos)
        self.level_type = level_type
        self.rect = pygame.Rect(pos[0]-20, pos[1]-20, 40, 40)
        self.color = RED

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), 20)
        pygame.draw.circle(surface, YELLOW, (int(self.pos.x), int(self.pos.y)), 15)

class Game:
    def __init__(self):
        self.state = STATE_OVERWORLD
        self.world_index = 0
        self.current_node = 0
        self.overworld_time = 0
        self.nodes = []
        self.mario = Mario()
        self.platforms = []
        self.camera_x = 0
        self.load_world(self.world_index)

    def load_world(self, world_index):
        self.world_index = world_index
        world = WORLDS[self.world_index]
        self.bg_color = world["bg_color"]
        self.platform_color = world["platform_color"]
        self.nodes = [OverworldNode(node["pos"], node["type"]) for node in world["nodes"]]
        self.current_node = 0

    def load_level(self, level_type):
        self.state = STATE_LEVEL
        self.mario.pos = Vector2(100, 400)
        
        # Generate level based on type [[4]]
        self.platforms = [
            Platform(0, 500, 800, 100),
            Platform(200, 400, 100, 20),
            Platform(400, 300, 100, 20)
        ]
        
        # Apply theme color
        for plat in self.platforms:
            plat.color = self.platform_color

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
            if self.nodes[self.current_node].level_type == LEVEL_CASTLE:
                self.load_level(LEVEL_CASTLE)
            else:
                self.load_level(LEVEL_REGULAR)

    def draw_overworld(self, surface):
        surface.fill(self.bg_color)
        
        # Draw paths between nodes
        if len(self.nodes) > 1:
            points = [(int(node.pos.x), int(node.pos.y)) for node in self.nodes]
            pygame.draw.lines(surface, BLACK, False, points, 5)
        
        # Draw nodes
        for i, node in enumerate(self.nodes):
            node.color = RED if i == self.current_node else GROUND_GREEN
            node.draw(surface)
        
        # Draw Mario
        mario_rect = pygame.Rect(
            int(self.nodes[self.current_node].pos.x - 15),
            int(self.nodes[self.current_node].pos.y - 30),
            30, 40
        )
        pygame.draw.rect(surface, RED, mario_rect)

    def draw_level(self, surface):
        surface.fill(self.bg_color)
        
        # Smooth camera
        target_camera_x = max(0, int(self.mario.pos.x - 400))
        self.camera_x = self.camera_x * 0.9 + target_camera_x * 0.1
        
        # Draw platforms
        for plat in self.platforms:
            offset_rect = plat.rect.move(-self.camera_x, 0)
            plat.draw(surface)
        
        # Draw Mario
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
            
            # Return to overworld on ESC
            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                self.state = STATE_OVERWORLD

        pygame.display.update()

if __name__ == "__main__":
    game = Game()
    while True:
        game.run()

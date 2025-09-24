import pygame
import sys
import math

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
SKY_BLUE = (107, 140, 255)
GREEN = (76, 175, 80)
BROWN = (139, 69, 19)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 50
        self.vel_x = 0
        self.vel_y = 0
        self.jump_power = -12
        self.gravity = 0.5
        self.speed = 5
        self.on_ground = False
        self.direction = 1  # 1 for right, -1 for left
        self.color = RED
        
    def update(self, platforms):
        # Apply gravity
        self.vel_y += self.gravity
        
        # Update position
        self.x += self.vel_x
        self.y += self.vel_y
        
        # Check platform collisions
        self.on_ground = False
        for platform in platforms:
            if self.vel_y > 0:  # Falling
                if (self.y + self.height >= platform.y and 
                    self.y < platform.y and
                    self.x + self.width > platform.x and 
                    self.x < platform.x + platform.width):
                    self.y = platform.y - self.height
                    self.vel_y = 0
                    self.on_ground = True
        
        # Screen boundaries
        if self.x < 0:
            self.x = 0
        if self.x > SCREEN_WIDTH - self.width:
            self.x = SCREEN_WIDTH - self.width
        if self.y > SCREEN_HEIGHT:
            self.y = 0  # Reset position if falling off
            
    def jump(self):
        if self.on_ground:
            self.vel_y = self.jump_power
            
    def draw(self, screen):
        # Draw Mario-like character
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        # Face
        pygame.draw.circle(screen, (255, 200, 150), 
                          (self.x + self.width // 2 + self.direction * 5, self.y + 15), 10)
        # Hat
        pygame.draw.rect(screen, RED, (self.x - 5, self.y, self.width + 10, 10))

class Platform:
    def __init__(self, x, y, width, height, color=BROWN):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))

class Level:
    def __init__(self, level_num, world_num):
        self.level_num = level_num
        self.world_num = world_num
        self.platforms = []
        self.enemies = []
        self.coins = []
        self.setup_level()
        
    def setup_level(self):
        # Ground platform
        self.platforms.append(Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50))
        
        # Various platforms based on level
        if self.level_num == 1:
            self.platforms.append(Platform(100, 400, 200, 20))
            self.platforms.append(Platform(400, 300, 150, 20))
            self.platforms.append(Platform(200, 200, 100, 20))
        elif self.level_num == 2:
            self.platforms.append(Platform(150, 450, 100, 20))
            self.platforms.append(Platform(300, 350, 100, 20))
            self.platforms.append(Platform(450, 250, 100, 20))
            self.platforms.append(Platform(600, 350, 100, 20))
        elif self.level_num == 3:
            self.platforms.append(Platform(100, 400, 50, 20))
            self.platforms.append(Platform(200, 350, 50, 20))
            self.platforms.append(Platform(300, 300, 50, 20))
            self.platforms.append(Platform(400, 250, 50, 20))
            self.platforms.append(Platform(500, 300, 50, 20))
            self.platforms.append(Platform(600, 350, 50, 20))
            self.platforms.append(Platform(700, 400, 50, 20))
            
    def draw(self, screen, font):
        # Draw background
        screen.fill(SKY_BLUE)
        
        # Draw level info
        level_text = font.render(f"World {self.world_num}-{self.level_num}", True, WHITE)
        screen.blit(level_text, (20, 20))
        
        # Draw platforms
        for platform in self.platforms:
            platform.draw(screen)

class OverworldNode:
    def __init__(self, x, y, world, level, radius=20):
        self.x = x
        self.y = y
        self.world = world
        self.level = level
        self.radius = radius
        self.completed = False
        self.locked = level > 1  # Lock levels beyond 1 initially
        
    def draw(self, screen, font, is_current=False):
        color = GREEN if self.completed else (YELLOW if not self.locked else GRAY)
        if is_current:
            color = RED
            
        pygame.draw.circle(screen, color, (self.x, self.y), self.radius)
        pygame.draw.circle(screen, BLACK, (self.x, self.y), self.radius, 2)
        
        # Draw level number
        level_text = font.render(str(self.level), True, BLACK)
        text_rect = level_text.get_rect(center=(self.x, self.y))
        screen.blit(level_text, text_rect)
        
        # Draw world info for first level of each world
        if self.level == 1:
            world_text = font.render(f"World {self.world}", True, WHITE)
            screen.blit(world_text, (self.x - 30, self.y - 50))

class Overworld:
    def __init__(self):
        self.nodes = []
        self.current_node_index = 0
        self.setup_overworld()
        
    def setup_overworld(self):
        # Create 5 worlds with 3 levels each
        for world in range(1, 6):
            for level in range(1, 4):
                x = 150 + (world - 1) * 150
                y = 200 + (level - 1) * 80
                node = OverworldNode(x, y, world, level)
                if world == 1 and level == 1:
                    node.locked = False  # First level is unlocked
                self.nodes.append(node)
                
    def move_selection(self, direction):
        # Simple linear navigation for now
        if direction == "right" and self.current_node_index < len(self.nodes) - 1:
            if not self.nodes[self.current_node_index + 1].locked:
                self.current_node_index += 1
        elif direction == "left" and self.current_node_index > 0:
            self.current_node_index -= 1
            
    def get_current_level(self):
        current_node = self.nodes[self.current_node_index]
        return current_node.world, current_node.level
        
    def complete_current_level(self):
        current_node = self.nodes[self.current_node_index]
        current_node.completed = True
        
        # Unlock next level if available
        if self.current_node_index < len(self.nodes) - 1:
            next_node = self.nodes[self.current_node_index + 1]
            if next_node.world == current_node.world:  # Only unlock within same world
                next_node.locked = False
                
    def draw(self, screen, font):
        # Draw background
        screen.fill((30, 30, 100))
        
        # Draw title
        title_font = pygame.font.SysFont(None, 64)
        title_text = title_font.render("ULTRA MARIO 2D BROS", True, YELLOW)
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 50))
        
        # Draw connection lines between levels in same world
        for world in range(1, 6):
            world_nodes = [node for node in self.nodes if node.world == world]
            for i in range(len(world_nodes) - 1):
                if not world_nodes[i+1].locked:
                    pygame.draw.line(screen, WHITE, 
                                   (world_nodes[i].x, world_nodes[i].y),
                                   (world_nodes[i+1].x, world_nodes[i+1].y), 3)
        
        # Draw nodes
        for i, node in enumerate(self.nodes):
            node.draw(screen, font, i == self.current_node_index)
            
        # Draw instructions
        inst_font = pygame.font.SysFont(None, 32)
        instructions = [
            "ARROWS: Navigate  SPACE: Select Level  Q: Show Controls",
            "ESC: Return to Overworld  R: Reset Level"
        ]
        for i, instruction in enumerate(instructions):
            inst_text = inst_font.render(instruction, True, WHITE)
            screen.blit(inst_text, (SCREEN_WIDTH // 2 - inst_text.get_width() // 2, 
                                   SCREEN_HEIGHT - 100 + i * 30))

class ControlsScreen:
    def __init__(self):
        self.visible = False
        
    def draw(self, screen, font):
        if not self.visible:
            return
            
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        
        # Title
        title_font = pygame.font.SysFont(None, 48)
        title_text = title_font.render("HOW TO PLAY - ULTRA MARIO 2D BROS", True, YELLOW)
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 50))
        
        # Controls (like Smash 64 style)
        controls = [
            "MOVEMENT CONTROLS:",
            "← → : Move Left/Right",
            "↑ : Look Up",
            "↓ : Crouch",
            "A / SPACE : Jump",
            "Z / LEFT SHIFT : Run",
            "",
            "ACTIONS:",
            "X / S : Spin Jump (breaks special blocks)",
            "C / D : Pick Up/Throw Items",
            "Q : Show/Hide This Screen",
            "ESC : Pause/Return to Overworld",
            "",
            "SPECIAL MOVES:",
            "Hold ↓ + Jump: High Jump",
            "Run + Jump: Long Jump",
            "Spin Jump on enemy: Bounce attack",
            "",
            "GAME FEATURES:",
            "• 5 Worlds with 3 Levels each",
            "• Secret paths and hidden areas",
            "• Collect coins for extra lives",
            "• Defeat enemies by jumping on them",
            "",
            "Press Q to return to game"
        ]
        
        # Draw controls
        for i, control in enumerate(controls):
            color = WHITE if not control.startswith("•") else GREEN
            control_font = pygame.font.SysFont(None, 28 if control.startswith("•") else 32)
            control_text = control_font.render(control, True, color)
            screen.blit(control_text, (SCREEN_WIDTH // 2 - control_text.get_width() // 2, 
                                     120 + i * 30))

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Ultra Mario 2D Bros")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)
        
        self.overworld = Overworld()
        self.controls_screen = ControlsScreen()
        self.current_level = None
        self.player = None
        self.game_state = "overworld"  # overworld, level
        
    def start_level(self, world, level):
        self.current_level = Level(level, world)
        self.player = Player(100, 300)
        self.game_state = "level"
        
    def return_to_overworld(self):
        self.game_state = "overworld"
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    self.controls_screen.visible = not self.controls_screen.visible
                    
                if self.game_state == "overworld":
                    if event.key == pygame.K_RIGHT:
                        self.overworld.move_selection("right")
                    elif event.key == pygame.K_LEFT:
                        self.overworld.move_selection("left")
                    elif event.key == pygame.K_SPACE:
                        world, level = self.overworld.get_current_level()
                        self.start_level(world, level)
                        
                elif self.game_state == "level":
                    if event.key == pygame.K_SPACE:
                        self.player.jump()
                    elif event.key == pygame.K_ESCAPE:
                        self.return_to_overworld()
                    elif event.key == pygame.K_r:
                        # Reset level
                        world, level = self.overworld.get_current_level()
                        self.start_level(world, level)
                        
        return True
        
    def update(self):
        if self.game_state == "level" and self.player:
            keys = pygame.key.get_pressed()
            self.player.vel_x = 0
            
            if keys[pygame.K_LEFT]:
                self.player.vel_x = -self.player.speed
                self.player.direction = -1
            if keys[pygame.K_RIGHT]:
                self.player.vel_x = self.player.speed
                self.player.direction = 1
                
            self.player.update(self.current_level.platforms)
            
    def draw(self):
        if self.game_state == "overworld":
            self.overworld.draw(self.screen, self.font)
        elif self.game_state == "level":
            self.current_level.draw(self.screen, self.font)
            if self.player:
                self.player.draw(self.screen)
                
        # Always draw controls screen if visible (on top of everything)
        self.controls_screen.draw(self.screen, self.font)
        
        pygame.display.flip()
        
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
            
        pygame.quit()
        sys.exit()

# Main execution
if __name__ == "__main__":
    game = Game()
    game.run()

import pygame
import sys

# --- Constants ---
WIDTH, HEIGHT, TILE, FPS = 640, 400, 32, 60
FIX = 256  # For fixed-point arithmetic, providing smoother movement

# --- Colors ---
COLORS = {
    'WHITE': (255, 255, 255),
    'BLACK': (0, 0, 0),
    'RED': (220, 50, 50),
    'GREEN': (60, 220, 60),
    'BLUE': (50, 90, 220),
    'YELLOW': (240, 220, 70),
    'BROWN': (170, 100, 40),
    'SKY': (110, 180, 240),
    'GRAY': (120, 120, 120),
    'ORANGE': (220, 120, 30),
    'PURPLE': (120, 60, 180)
}

# --- Overworld Map Data ---
# Defines the worlds and their nodes (levels) on the overworld map.
# Each node has a position 'pos', a unique level identifier 'level' (world_num, level_num),
# and a 'label' for display.
SMW_MAP = [
    {
        'name': "Yoshi's Island", # World 1
        'nodes': [
            {'pos': (80, 220), 'level': (1, 1), 'label': "YI 1"},
            {'pos': (180, 200), 'level': (1, 2), 'label': "YI 2"},
            {'pos': (300, 220), 'level': (1, 3), 'label': "YI 3"},
            {'pos': (420, 200), 'level': (1, 4), 'label': "YI 4"},
            {'pos': (540, 220), 'level': (1, 5), 'label': "Yoshi's Castle"}, # Castle
        ]
    },
    {
        'name': 'Donut Plains', # World 2
        'nodes': [
            {'pos': (80, 100), 'level': (2, 1), 'label': "DP 1"},
            {'pos': (180, 120), 'level': (2, 2), 'label': "DP 2"},
            {'pos': (300, 90),  'level': (2, 3), 'label': "DP 3"},
            {'pos': (420, 110), 'level': (2, 4), 'label': "DP 4"},
            {'pos': (540, 100), 'level': (2, 5), 'label': "Donut Castle"}, # Castle
        ]
    },
    # --- NEW WORLDS START HERE ---
    {
        'name': 'Vanilla Dome', # World 3
        'nodes': [
            {'pos': (100, 150), 'level': (3, 1), 'label': "VD 1"},
            {'pos': (200, 180), 'level': (3, 2), 'label': "VD 2"},
            {'pos': (300, 150), 'level': (3, 3), 'label': "VD 3"},
            {'pos': (400, 180), 'level': (3, 4), 'label': "VD 4"},
            {'pos': (500, 150), 'level': (3, 5), 'label': "Vanilla Castle"}, # Castle
        ]
    },
    {
        'name': 'Twin Bridges', # World 4 (includes Butter Bridge & Cookie Mountain areas)
        'nodes': [
            {'pos': (120, 250), 'level': (4, 1), 'label': "TB 1"}, # e.g., Cookie Mountain entrance
            {'pos': (240, 230), 'level': (4, 2), 'label': "TB 2"},
            {'pos': (360, 250), 'level': (4, 3), 'label': "TB 3"}, # e.g., Butter Bridge entrance
            {'pos': (480, 230), 'level': (4, 4), 'label': "Lemmy's Castle"}, # Castle
        ]
    },
    {
        'name': 'Forest of Illusion', # World 5
        'nodes': [
            {'pos': (90, 300), 'level': (5, 1), 'label': "FI 1"},
            {'pos': (190, 280), 'level': (5, 2), 'label': "FI 2"},
            {'pos': (290, 300), 'level': (5, 3), 'label': "FI 3"},
            {'pos': (390, 280), 'level': (5, 4), 'label': "FI 4"},
            {'pos': (490, 300), 'level': (5, 5), 'label': "Roy's Castle"}, # Castle
        ]
    },
    {
        'name': 'Chocolate Island', # World 6
        'nodes': [
            {'pos': (150, 80), 'level': (6, 1), 'label': "CI 1"},
            {'pos': (250, 110), 'level': (6, 2), 'label': "CI 2"},
            {'pos': (350, 80), 'level': (6, 3), 'label': "CI 3"},
            {'pos': (450, 110), 'level': (6, 4), 'label': "CI 4"},
            {'pos': (550, 80), 'level': (6, 5), 'label': "Wendy's Castle"}, # Castle
        ]
    },
    {
        'name': 'Valley of Bowser', # World 7
        'nodes': [
            {'pos': (80, 180), 'level': (7, 1), 'label': "VB 1"},
            {'pos': (180, 160), 'level': (7, 2), 'label': "VB 2"},
            {'pos': (280, 180), 'level': (7, 3), 'label': "VB 3"},
            {'pos': (380, 160), 'level': (7, 4), 'label': "VB 4"},
            {'pos': (480, 180), 'level': (7, 5), 'label': "Larry's Castle"}, # Castle
            {'pos': (580, 160), 'level': (7, 6), 'label': "Bowser's Castle"}, # Final Castle
        ]
    }
    # Star World and Special Zone could be added later with more complex pathing logic if needed.
    # --- NEW WORLDS END HERE ---
]

# --- Level Definitions ---
# Provides a template for a simple level.
def simple_level():
    return {
        'platforms': [(0, HEIGHT-40, WIDTH, 12)], # A basic ground platform
        'enemies': [],
        'items': [],
        'flag': (WIDTH - 60, HEIGHT-72), # Flag position (near the end of the screen)
        'pipes': [],
        'switches': [],
        'powerups': [],
        'yoshi': None
    }

# Defines the actual content of each level, keyed by (world_num, level_num).
SMW_LEVELS = {
    # Yoshi's Island Levels
    (1, 1): {
        'platforms': [(0, HEIGHT-40, WIDTH, 12), (120, HEIGHT-100, 80, 12), (300, HEIGHT-150, 100, 12)],
        'enemies': [(260, HEIGHT-72, 'goomba')],
        'items': [(160, HEIGHT-160, 'coin')],
        'flag': (WIDTH - 60, HEIGHT-72),
        'pipes': [], 'switches': [], 'powerups': [], 'yoshi': None
    },
    (1, 2): simple_level(),
    (1, 3): simple_level(),
    (1, 4): simple_level(),
    (1, 5): simple_level(), # Yoshi's Castle

    # Donut Plains Levels
    (2, 1): simple_level(),
    (2, 2): simple_level(),
    (2, 3): simple_level(),
    (2, 4): simple_level(),
    (2, 5): simple_level(), # Donut Castle

    # --- NEW LEVEL DEFINITIONS START HERE ---
    # Vanilla Dome Levels
    (3, 1): simple_level(),
    (3, 2): simple_level(),
    (3, 3): simple_level(),
    (3, 4): simple_level(),
    (3, 5): simple_level(), # Vanilla Castle

    # Twin Bridges Levels
    (4, 1): simple_level(),
    (4, 2): simple_level(),
    (4, 3): simple_level(),
    (4, 4): simple_level(), # Lemmy's Castle

    # Forest of Illusion Levels
    (5, 1): simple_level(),
    (5, 2): simple_level(),
    (5, 3): simple_level(),
    (5, 4): simple_level(),
    (5, 5): simple_level(), # Roy's Castle

    # Chocolate Island Levels
    (6, 1): simple_level(),
    (6, 2): simple_level(),
    (6, 3): simple_level(),
    (6, 4): simple_level(),
    (6, 5): simple_level(), # Wendy's Castle

    # Valley of Bowser Levels
    (7, 1): simple_level(),
    (7, 2): simple_level(),
    (7, 3): simple_level(),
    (7, 4): simple_level(),
    (7, 5): simple_level(), # Larry's Castle
    (7, 6): { # Bowser's Castle - slightly different flag position
        'platforms': [(0, HEIGHT-40, WIDTH, 12), (WIDTH/2 - 50, HEIGHT-120, 100, 12)],
        'enemies': [(200, HEIGHT-72, 'koopa'), (400, HEIGHT-72, 'koopa')],
        'flag': (WIDTH - 60, HEIGHT-152), # Raised flag for a "boss" feel
        'pipes': [], 'switches': [], 'powerups': [], 'yoshi': None
    },
    # --- NEW LEVEL DEFINITIONS END HERE ---
}


# --- Game Object Classes ---
class Entity:
    """Base class for game objects with position, dimensions, and basic physics."""
    __slots__ = ('x', 'y', 'w', 'h', 'vx', 'vy', 'color', 'on_ground') # Memory optimization

    def __init__(self, x, y, w, h, color):
        self.x = x * FIX  # Position (fixed-point)
        self.y = y * FIX
        self.vx = 0       # Velocity x (fixed-point)
        self.vy = 0       # Velocity y (fixed-point)
        self.w = w        # Width
        self.h = h        # Height
        self.color = color
        self.on_ground = False

    def rect(self):
        """Returns a pygame.Rect for collision detection and drawing."""
        return pygame.Rect(self.x // FIX, self.y // FIX, self.w, self.h)

    def draw(self, surface):
        """Draws the entity as a rectangle."""
        pygame.draw.rect(surface, self.color, self.rect())

class RectEntity(Entity):
    """A simple rectangular entity, typically for platforms or static objects."""
    def __init__(self, x, y, w, h, color):
        super().__init__(x, y, w, h, color)

class Player(Entity):
    """Represents the player character with specific physics and attributes."""
    def __init__(self, x, y):
        super().__init__(x, y, 24, 32, COLORS['RED']) # Player size and color
        self.lives = 5
        self.coins = 0
        # Physics parameters (tuned for platformer feel)
        self.accel = int(0.18 * FIX)    # Acceleration
        self.fric = int(0.12 * FIX)     # Friction
        self.max_vx = int(2.4 * FIX)    # Max horizontal speed
        self.jump_v = int(-7.5 * FIX)   # Jump velocity (negative is up)
        self.gravity = int(0.28 * FIX)  # Gravity strength

    def handle_input(self, keys):
        """Processes keyboard input for player movement."""
        ax = 0 # Horizontal acceleration
        if keys[pygame.K_LEFT]:
            ax = -self.accel
        if keys[pygame.K_RIGHT]:
            ax = self.accel
        
        self.vx += ax

        # Apply friction if no horizontal input
        if ax == 0:
            if self.vx > 0:
                self.vx = max(0, self.vx - self.fric)
            else:
                self.vx = min(0, self.vx + self.fric)
        
        # Clamp horizontal velocity
        self.vx = max(-self.max_vx, min(self.max_vx, self.vx))

        # Jumping
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vy = self.jump_v
            self.on_ground = False # Prevent double jump in same frame

    def update_physics(self, platforms):
        """Updates player position based on velocity and handles collisions."""
        # Apply gravity
        self.vy += self.gravity
        
        # Update position (potential new position)
        self.x += self.vx
        self.y += self.vy
        
        self.on_ground = False # Assume not on ground until collision check
        
        player_rect = self.rect()

        for p_entity in platforms:
            platform_rect = p_entity.rect()
            if player_rect.colliderect(platform_rect):
                # Collision handling
                # Check vertical collision (landing on top or hitting head)
                if self.vy > 0 and player_rect.bottom - platform_rect.top < TILE // 2 and player_rect.bottom > platform_rect.top: # Landing
                    # Player was moving down, and collision is primarily from top of platform
                    self.y = (platform_rect.top - self.h) * FIX
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0 and platform_rect.bottom - player_rect.top < TILE // 2 and player_rect.top < platform_rect.bottom: # Hitting head
                     # Player was moving up, and collision is primarily from bottom of platform
                    self.y = platform_rect.bottom * FIX
                    self.vy = 0 # Stop upward movement

                # Check horizontal collision (more precise check needed for robust side collisions)
                # This is a simplified version. For better results, resolve horizontal and vertical collisions separately.
                player_rect_after_vy = pygame.Rect(self.x // FIX, self.y // FIX, self.w, self.h) # Re-evaluate rect after y correction

                if player_rect_after_vy.colliderect(platform_rect): # Check again if still colliding after y correction
                    if self.vx > 0 and player_rect_after_vy.right - platform_rect.left < TILE // 2: # Colliding with left side of platform
                        self.x = (platform_rect.left - self.w) * FIX
                        self.vx = 0
                    elif self.vx < 0 and platform_rect.right - player_rect_after_vy.left < TILE // 2: # Colliding with right side of platform
                        self.x = platform_rect.right * FIX
                        self.vx = 0

class Overworld:
    """Manages the display and navigation of the overworld map."""
    def __init__(self, map_data):
        self.map_data = map_data
        self.current_world_idx = 0  # Index for SMW_MAP list
        self.current_node_idx = 0   # Index for nodes list in the current world
        self.input_delay = 0        # Timer to prevent rapid input
        self.input_cooldown = 0.15  # Seconds

    def draw(self, surface, font):
        """Draws the current world's nodes and connections."""
        surface.fill(COLORS['SKY']) # Background for overworld
        
        current_world_data = self.map_data[self.current_world_idx]
        nodes = current_world_data['nodes']
        
        # Draw connections between nodes
        for i in range(len(nodes) - 1):
            pygame.draw.line(surface, COLORS['GRAY'], nodes[i]['pos'], nodes[i+1]['pos'], 5)
            
        # Draw nodes
        for i, node_info in enumerate(nodes):
            pos = node_info['pos']
            label_text = node_info.get('label', f"L{node_info['level'][1]}") # Default label if missing
            
            # Highlight the selected node
            color = COLORS['GREEN']
            radius = 10
            if i == self.current_node_idx:
                color = COLORS['YELLOW'] # Highlight color
                radius = 14 # Slightly larger radius for selected node
            
            pygame.draw.circle(surface, color, pos, radius)
            pygame.draw.circle(surface, COLORS['BLACK'], pos, radius, 2) # Border for visibility

            # Render node label
            text_surface = font.render(label_text, True, COLORS['BLACK'])
            text_rect = text_surface.get_rect(center=(pos[0], pos[1] - radius - 10)) # Position label above node
            surface.blit(text_surface, text_rect)
            
        # Display current world name
        world_name = current_world_data['name']
        name_surface = font.render(world_name, True, COLORS['BLACK'])
        name_rect = name_surface.get_rect(center=(WIDTH // 2, 30))
        surface.blit(name_surface, name_rect)

    def update_input_delay(self, dt):
        """Updates the input delay timer."""
        if self.input_delay > 0:
            self.input_delay = max(0, self.input_delay - dt)

    def move_node(self, direction):
        """Moves selection to the next/previous node in the current world."""
        if self.input_delay <= 0:
            nodes_in_current_world = len(self.map_data[self.current_world_idx]['nodes'])
            self.current_node_idx += direction
            # Wrap around or clamp node selection
            self.current_node_idx = max(0, min(nodes_in_current_world - 1, self.current_node_idx))
            self.input_delay = self.input_cooldown

    def switch_world(self, direction):
        """Switches to the next/previous world."""
        if self.input_delay <= 0:
            self.current_world_idx += direction
            # Wrap around or clamp world selection
            if self.current_world_idx < 0:
                self.current_world_idx = len(self.map_data) - 1
            elif self.current_world_idx >= len(self.map_data):
                self.current_world_idx = 0
            
            self.current_node_idx = 0 # Reset to the first node of the new world
            self.input_delay = self.input_cooldown
            
    def get_selected_level_key(self):
        """Returns the level key (world_num, level_num) for the currently selected node."""
        return self.map_data[self.current_world_idx]['nodes'][self.current_node_idx]['level']

class Level:
    """Manages the elements and drawing of a single game level."""
    def __init__(self, level_key):
        level_data = SMW_LEVELS.get(level_key)
        if not level_data:
            print(f"Warning: Level data for {level_key} not found! Using a default simple level.")
            level_data = simple_level() # Fallback to a simple level

        self.platforms = [RectEntity(x, y, w, h, COLORS['BROWN'])
                          for x, y, w, h in level_data.get('platforms', [])]
        self.enemies = [RectEntity(x, y, 24, 24, COLORS['ORANGE']) # Example enemy
                        for x, y, _type in level_data.get('enemies', [])] # _type can be used later
        
        fx, fy = level_data.get('flag', (WIDTH - 60, HEIGHT - 72))
        self.flag = RectEntity(fx, fy, 16, 32, COLORS['GREEN']) # Flag color changed for better visibility

    def draw(self, surface):
        """Draws all elements of the level."""
        surface.fill(COLORS['SKY']) # Level background
        for entity in self.platforms + self.enemies: # Combine lists for drawing
            entity.draw(surface)
        self.flag.draw(surface)

# --- Main Game Function ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Mini Platformer Engine")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 28) # Slightly larger font

    # Game state variables
    overworld_manager = Overworld(SMW_MAP)
    player = Player(60, HEIGHT - 72 - 32) # Initial player position
    current_level_instance = None
    game_state = 'overworld'  # Can be 'overworld' or 'level'

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # Delta time in seconds

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        keys = pygame.key.get_pressed()
        overworld_manager.update_input_delay(dt) # Update delay timer for overworld navigation

        if game_state == 'overworld':
            # Handle overworld input
            if keys[pygame.K_UP]:
                overworld_manager.switch_world(-1) # Previous world
            if keys[pygame.K_DOWN]:
                overworld_manager.switch_world(1)  # Next world
            if keys[pygame.K_LEFT]:
                overworld_manager.move_node(-1)    # Previous node
            if keys[pygame.K_RIGHT]:
                overworld_manager.move_node(1)     # Next node
            
            if keys[pygame.K_RETURN] and overworld_manager.input_delay <= 0: # Enter level
                selected_level_key = overworld_manager.get_selected_level_key()
                current_level_instance = Level(selected_level_key)
                player = Player(60, HEIGHT - 72 - player.h) # Reset player position for new level
                game_state = 'level'
                overworld_manager.input_delay = overworld_manager.input_cooldown # Prevent immediate re-entry

        elif game_state == 'level':
            if current_level_instance is None: # Should not happen if logic is correct
                print("Error: current_level_instance is None in 'level' state. Returning to overworld.")
                game_state = 'overworld'
                continue

            # Handle level input and physics
            player.handle_input(keys)
            player.update_physics(current_level_instance.platforms)

            # Check for falling out of bounds
            if player.rect().top > HEIGHT + TILE: # Give some leeway before reset
                player.lives = max(0, player.lives - 1)
                if player.lives > 0:
                    # Reset player to start of level
                    player = Player(60, HEIGHT - 72 - player.h)
                else:
                    # Game Over (simplified: return to overworld)
                    print("Game Over!")
                    game_state = 'overworld' 
                    # Potentially reset game progress or show a game over screen here
                    player.lives = 5 # Reset lives for next try from overworld

            # Check for reaching the flag
            if player.rect().colliderect(current_level_instance.flag.rect()):
                print(f"Level Complete! Reached flag for {overworld_manager.get_selected_level_key()}")
                game_state = 'overworld' # Return to overworld map
                # Here you could add logic for unlocking next levels, etc.
            
            # Check for enemy collisions (basic example)
            player_rect = player.rect()
            for enemy in current_level_instance.enemies:
                if player_rect.colliderect(enemy.rect()):
                    # Simple collision: lose a life and reset
                    print("Hit an enemy!")
                    player.lives = max(0, player.lives - 1)
                    if player.lives > 0:
                        player = Player(60, HEIGHT - 72 - player.h) # Reset player
                    else:
                        print("Game Over!")
                        game_state = 'overworld'
                        player.lives = 5 # Reset lives
                    break # Process one enemy collision per frame

        # --- Drawing ---
        screen.fill(COLORS['SKY']) # Default background

        if game_state == 'overworld':
            overworld_manager.draw(screen, font)
        elif game_state == 'level' and current_level_instance:
            current_level_instance.draw(screen)
            player.draw(screen)
            
            # Display HUD (Lives, Coins, etc.)
            lives_text = font.render(f"Lives: {player.lives}", True, COLORS['BLACK'])
            screen.blit(lives_text, (10, 10))
            coins_text = font.render(f"Coins: {player.coins}", True, COLORS['BLACK'])
            screen.blit(coins_text, (10, 40))

        pygame.display.flip() # Update the full display

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()

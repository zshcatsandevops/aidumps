import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")

import pygame
import math
import random
import time

# --- Initialization ---
pygame.init()

# --- Constants ---
# Famicom/NES Resolution (256x240, upscaled)
SCREEN_WIDTH = 256
SCREEN_HEIGHT = 240
SCALE_FACTOR = 3  # Upscale for modern displays
WINDOW_WIDTH = SCREEN_WIDTH * SCALE_FACTOR
WINDOW_HEIGHT = SCREEN_HEIGHT * SCALE_FACTOR

# Famicom/NES Color Palette (limited colors)
BLACK = (0, 0, 0)
WHITE = (252, 252, 252)
YELLOW = (252, 184, 0)
BLUE = (0, 88, 248)
RED = (248, 56, 0)
PINK = (248, 116, 248)
CYAN = (0, 232, 216)
ORANGE = (248, 164, 64)
GRAY = (124, 124, 124)
LIGHT_BLUE = (0, 168, 252)
GREEN = (0, 168, 0)

# Game Grid (8x8 tiles for Famicom style)
TILE_SIZE = 8
MAZE_WIDTH = 28
MAZE_HEIGHT = 31

# Game States
STATE_MENU = -1
STATE_GHOST_INTRO = -2
STATE_START = 0
STATE_PLAYING = 1
STATE_DIED = 2
STATE_GAME_OVER = 3
STATE_PAUSED = 4

# --- Font Setup ---
try:
    # Create a pixelated font for Famicom style
    PIXEL_FONT = pygame.font.Font(None, 8)
    MENU_FONT = pygame.font.Font(None, 16)
except:
    PIXEL_FONT = pygame.font.Font(None, 8)
    MENU_FONT = pygame.font.Font(None, 16)

# --- Game Class ---
class FamicomPacMan:
    def __init__(self):
        """Initialize the Famicom-style Pac-Man game."""
        # Set up display with pixel-perfect scaling (no blur)
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.display = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.display.set_alpha(255)
        pygame.display.set_caption("PAC-MAN FAMICOM EDITION")
        
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = STATE_MENU
        self.menu_selection = 0
        self.score = 0
        self.high_score = 10000  # Classic high score
        self.lives = 3
        self.level = 1
        self.pellets_remaining = 0
        self.frightened_timer = 0
        self.state_timer = 0
        self.frame_count = 0
        self.ghost_intro_phase = 0
        self.paused = False
        
        # Famicom-style maze (simplified for 8-bit look)
        self.maze_template = [
            "############################",
            "#............##............#",
            "#.####.#####.##.#####.####.#",
            "#o####.#####.##.#####.####o#",
            "#..........................#",
            "#.####.##.########.##.####.#",
            "#......##....##....##......#",
            "######.##### ## #####.######",
            "     #.##          ##.#     ",
            "     #.## ###--### ##.#     ",
            "######.## #      # ##.######",
            "      .   #      #   .      ",
            "######.## ######## ##.######",
            "     #.##          ##.#     ",
            "     #.## ######## ##.#     ",
            "######.## ######## ##.######",
            "#............##............#",
            "#.####.#####.##.#####.####.#",
            "#o..##......P.......##..o#",
            "###.##.##.########.##.##.###",
            "#......##....##....##......#",
            "#.##########.##.##########.#",
            "#..........................#",
            "############################"
        ]
        
        # Add some empty rows for UI space
        self.maze_template.extend([
            "                            ",
            "                            ",
            "                            ",
            "                            ",
            "                            ",
            "                            ",
            "                            "
        ])
        
        self.maze = []
        self.player = None
        self.ghosts = []
        
        # Initialize with menu
        self.init_menu()

    def init_menu(self):
        """Initialize the main menu."""
        self.state = STATE_MENU
        self.menu_selection = 0
        self.frame_count = 0

    def init_ghost_intro(self):
        """Initialize the ghost roll call intro."""
        self.state = STATE_GHOST_INTRO
        self.ghost_intro_phase = 0
        self.state_timer = 0
        
        # Create display ghosts for intro
        self.intro_ghosts = [
            {'name': 'BLINKY', 'nickname': '"SHADOW"', 'color': RED, 'x': 100, 'y': 80},
            {'name': 'PINKY', 'nickname': '"SPEEDY"', 'color': PINK, 'x': 100, 'y': 100},
            {'name': 'INKY', 'nickname': '"BASHFUL"', 'color': CYAN, 'x': 100, 'y': 120},
            {'name': 'CLYDE', 'nickname': '"POKEY"', 'color': ORANGE, 'x': 100, 'y': 140}
        ]

    def init_new_game(self):
        """Reset the game to its initial state."""
        self.score = 0
        self.lives = 3
        self.level = 1
        self.frame_count = 0
        self.start_new_level()
        self.state = STATE_START
        self.state_timer = 120

    def start_new_level(self):
        """Set up the maze and entities for a new level."""
        self.maze = []
        self.pellets_remaining = 0
        player_start_pos = (13, 18)
        ghost_start_pos = (13, 9)
        
        for y, line in enumerate(self.maze_template):
            row = []
            for x, char in enumerate(line):
                if char == '#':
                    row.append(1)  # Wall
                elif char == '.':
                    row.append(2)  # Pellet
                    self.pellets_remaining += 1
                elif char == 'o':
                    row.append(3)  # Power Pellet
                    self.pellets_remaining += 1
                elif char == '-':
                    row.append(4)  # Ghost Door
                elif char == 'P':
                    player_start_pos = (x, y)
                    row.append(0)
                else:
                    row.append(0)  # Empty
            self.maze.append(row)
            
        self.player = FamicomPlayer(self, player_start_pos[0] * TILE_SIZE, player_start_pos[1] * TILE_SIZE)
        
        # Create ghosts with Famicom style
        self.ghosts = [
            FamicomGhost(self, ghost_start_pos[0] * TILE_SIZE, ghost_start_pos[1] * TILE_SIZE, RED, "blinky"),
            FamicomGhost(self, (ghost_start_pos[0]-2) * TILE_SIZE, (ghost_start_pos[1]+1) * TILE_SIZE, PINK, "pinky"),
            FamicomGhost(self, (ghost_start_pos[0]+2) * TILE_SIZE, (ghost_start_pos[1]+1) * TILE_SIZE, CYAN, "inky"),
            FamicomGhost(self, ghost_start_pos[0] * TILE_SIZE, (ghost_start_pos[1]+2) * TILE_SIZE, ORANGE, "clyde")
        ]
        
        self.frightened_timer = 0
        self.state_timer = 120

    def run(self):
        """Main game loop."""
        while self.running:
            self.clock.tick(60)  # 60 FPS like Famicom
            self.handle_events()
            self.update()
            self.draw()
        pygame.quit()

    def handle_events(self):
        """Process input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == STATE_PLAYING:
                        self.state = STATE_MENU
                    else:
                        self.running = False
                        
                # Menu controls
                if self.state == STATE_MENU:
                    if event.key == pygame.K_UP:
                        self.menu_selection = (self.menu_selection - 1) % 3
                    elif event.key == pygame.K_DOWN:
                        self.menu_selection = (self.menu_selection + 1) % 3
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        if self.menu_selection == 0:  # Start Game
                            self.init_ghost_intro()
                        elif self.menu_selection == 1:  # High Score
                            pass  # Just show high score
                        elif self.menu_selection == 2:  # Exit
                            self.running = False
                            
                # Skip ghost intro
                elif self.state == STATE_GHOST_INTRO:
                    if event.key == pygame.K_SPACE:
                        self.init_new_game()
                        
                # Game controls
                elif self.state == STATE_PLAYING:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.player.set_direction(-1, 0)
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.player.set_direction(1, 0)
                    elif event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.player.set_direction(0, -1)
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.player.set_direction(0, 1)
                    elif event.key == pygame.K_p:
                        self.paused = not self.paused
                        
                # Game over
                elif self.state == STATE_GAME_OVER:
                    if event.key == pygame.K_SPACE:
                        self.init_menu()
                        
                # Start screen
                elif self.state == STATE_START:
                    if event.key == pygame.K_SPACE:
                        self.state = STATE_PLAYING

    def update(self):
        """Update game logic."""
        self.frame_count += 1
        
        if self.state == STATE_MENU:
            # Animate menu
            pass
            
        elif self.state == STATE_GHOST_INTRO:
            self.state_timer += 1
            if self.state_timer > 60:  # Show each ghost for 1 second
                self.ghost_intro_phase += 1
                self.state_timer = 0
                if self.ghost_intro_phase >= 4:
                    self.init_new_game()
                    
        elif self.state == STATE_PLAYING and not self.paused:
            self.player.update()
            for ghost in self.ghosts:
                ghost.update()
                
            # Frightened timer
            if self.frightened_timer > 0:
                self.frightened_timer -= 16.67
                if self.frightened_timer <= 0:
                    for ghost in self.ghosts:
                        if ghost.mode == 'frightened':
                            ghost.mode = 'chase'
                            
            # Check win condition
            if self.pellets_remaining <= 0:
                self.level += 1
                self.start_new_level()
                self.state = STATE_START
                
            # Update high score
            if self.score > self.high_score:
                self.high_score = self.score
                
        elif self.state == STATE_START:
            self.state_timer -= 1
            if self.state_timer <= 0:
                self.state = STATE_PLAYING
                
        elif self.state == STATE_DIED:
            self.state_timer -= 1
            if self.state_timer <= 0:
                if self.lives > 0:
                    self.player.reset_position()
                    for ghost in self.ghosts:
                        ghost.reset_position()
                    self.state = STATE_PLAYING
                else:
                    self.state = STATE_GAME_OVER
                    self.state_timer = 180
                    
        elif self.state == STATE_GAME_OVER:
            self.state_timer -= 1

    def draw(self):
        """Render everything with Famicom style."""
        # Clear with Famicom blue-black
        self.display.fill(BLACK)
        
        if self.state == STATE_MENU:
            self.draw_menu()
        elif self.state == STATE_GHOST_INTRO:
            self.draw_ghost_intro()
        else:
            self.draw_game()
            
        # Scale up with NEAREST neighbor (no blur, pixel perfect)
        scaled = pygame.transform.scale(self.display, (WINDOW_WIDTH, WINDOW_HEIGHT))
        self.screen.blit(scaled, (0, 0))
        pygame.display.flip()

    def draw_menu(self):
        """Draw the main menu with Famicom style."""
        # Title
        self.draw_text_8bit("PAC-MAN", YELLOW, SCREEN_WIDTH//2, 40, size='large', center=True)
        self.draw_text_8bit("FAMICOM EDITION", WHITE, SCREEN_WIDTH//2, 55, center=True)
        
        # Draw pixel art Pac-Man
        pac_x = SCREEN_WIDTH//2
        pac_y = 90
        pac_size = 16
        # Animated mouth
        mouth_angle = abs(math.sin(self.frame_count * 0.1)) * 30
        
        # Draw Pac-Man body
        for y in range(-pac_size, pac_size):
            for x in range(-pac_size, pac_size):
                if x*x + y*y <= pac_size*pac_size:
                    angle = math.degrees(math.atan2(y, x))
                    if angle < 0:
                        angle += 360
                    if not (angle > mouth_angle and angle < 360 - mouth_angle):
                        self.display.set_at((pac_x + x, pac_y + y), YELLOW)
        
        # Menu options
        menu_items = ["START GAME", "HIGH SCORE", "EXIT"]
        for i, item in enumerate(menu_items):
            color = YELLOW if i == self.menu_selection else WHITE
            y_pos = 140 + i * 20
            
            # Draw selection arrow
            if i == self.menu_selection:
                # Draw 8-bit arrow
                arrow_points = [
                    (SCREEN_WIDTH//2 - 50, y_pos),
                    (SCREEN_WIDTH//2 - 45, y_pos - 3),
                    (SCREEN_WIDTH//2 - 45, y_pos + 3)
                ]
                for point in arrow_points:
                    pygame.draw.rect(self.display, YELLOW, (point[0], point[1], 2, 2))
                    
            self.draw_text_8bit(item, color, SCREEN_WIDTH//2, y_pos, center=True)
            
        # Show high score
        self.draw_text_8bit(f"HIGH SCORE: {self.high_score:06d}", CYAN, SCREEN_WIDTH//2, 200, center=True)
        
        # Credits
        self.draw_text_8bit("(C) 1980 NAMCO", GRAY, SCREEN_WIDTH//2, 220, center=True)
        self.draw_text_8bit("FAMICOM PORT 2024", GRAY, SCREEN_WIDTH//2, 230, center=True)

    def draw_ghost_intro(self):
        """Draw the ghost roll call intro."""
        self.draw_text_8bit("CHARACTER / NICKNAME", WHITE, SCREEN_WIDTH//2, 40, center=True)
        
        if self.ghost_intro_phase < 4:
            ghost = self.intro_ghosts[self.ghost_intro_phase]
            
            # Draw ghost sprite (8x8 pixels)
            self.draw_famicom_ghost(ghost['x'], ghost['y'], ghost['color'])
            
            # Draw name and nickname
            self.draw_text_8bit(ghost['name'], ghost['color'], ghost['x'] + 20, ghost['y'], center=False)
            self.draw_text_8bit(ghost['nickname'], WHITE, ghost['x'] + 20, ghost['y'] + 10, center=False)
            
        # Show all previous ghosts
        for i in range(self.ghost_intro_phase):
            ghost = self.intro_ghosts[i]
            self.draw_famicom_ghost(ghost['x'], ghost['y'], ghost['color'])
            self.draw_text_8bit(ghost['name'], ghost['color'], ghost['x'] + 20, ghost['y'], center=False)
            self.draw_text_8bit(ghost['nickname'], WHITE, ghost['x'] + 20, ghost['y'] + 10, center=False)
            
        self.draw_text_8bit("PRESS SPACE TO START", YELLOW if (self.frame_count // 30) % 2 else WHITE, 
                           SCREEN_WIDTH//2, 180, center=True)

    def draw_game(self):
        """Draw the game screen."""
        # Draw maze with Famicom colors
        self.draw_maze()
        
        # Draw entities
        if self.state != STATE_START or self.state_timer < 60:
            self.player.draw()
            for ghost in self.ghosts:
                ghost.draw()
                
        # Draw UI
        self.draw_ui()
        
        # Draw overlays
        if self.state == STATE_START:
            self.draw_text_8bit("READY!", YELLOW, SCREEN_WIDTH//2, 120, center=True)
        elif self.state == STATE_GAME_OVER:
            self.draw_text_8bit("GAME OVER", RED, SCREEN_WIDTH//2, 120, center=True)
        elif self.paused:
            self.draw_text_8bit("PAUSED", WHITE, SCREEN_WIDTH//2, 120, center=True)

    def draw_maze(self):
        """Draw maze with Famicom tile style."""
        for y in range(len(self.maze)):
            for x in range(len(self.maze[y])):
                tile = self.maze[y][x]
                screen_x = x * TILE_SIZE
                screen_y = y * TILE_SIZE
                
                if tile == 1:  # Wall - draw with 8-bit tile pattern
                    # Main wall block
                    pygame.draw.rect(self.display, BLUE, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
                    # Inner highlight for depth
                    pygame.draw.rect(self.display, LIGHT_BLUE, (screen_x, screen_y, TILE_SIZE-1, TILE_SIZE-1))
                    # Shadow
                    pygame.draw.rect(self.display, BLUE, (screen_x+1, screen_y+1, TILE_SIZE-1, TILE_SIZE-1))
                    
                elif tile == 2:  # Pellet - single pixel
                    pygame.draw.rect(self.display, WHITE, 
                                   (screen_x + TILE_SIZE//2 - 1, screen_y + TILE_SIZE//2 - 1, 2, 2))
                    
                elif tile == 3:  # Power Pellet - flashing square
                    if (self.frame_count // 10) % 2:
                        pygame.draw.rect(self.display, WHITE,
                                       (screen_x + TILE_SIZE//2 - 2, screen_y + TILE_SIZE//2 - 2, 4, 4))
                    else:
                        pygame.draw.rect(self.display, YELLOW,
                                       (screen_x + TILE_SIZE//2 - 2, screen_y + TILE_SIZE//2 - 2, 4, 4))
                        
                elif tile == 4:  # Ghost door
                    pygame.draw.rect(self.display, PINK,
                                   (screen_x, screen_y + TILE_SIZE//2 - 1, TILE_SIZE, 2))

    def draw_ui(self):
        """Draw Famicom-style UI."""
        # Score
        self.draw_text_8bit(f"SCORE", WHITE, 20, 200)
        self.draw_text_8bit(f"{self.score:06d}", WHITE, 20, 210)
        
        # High Score
        self.draw_text_8bit(f"HIGH", RED, SCREEN_WIDTH//2, 200, center=True)
        self.draw_text_8bit(f"{self.high_score:06d}", RED, SCREEN_WIDTH//2, 210, center=True)
        
        # Level
        self.draw_text_8bit(f"LEVEL {self.level}", CYAN, SCREEN_WIDTH - 50, 200)
        
        # Lives (draw mini pac-mans)
        for i in range(self.lives - 1):
            x = 20 + i * 12
            y = 225
            # Draw simple 5x5 Pac-Man
            for dy in range(5):
                for dx in range(5):
                    if dx*dx + dy*dy <= 6:
                        self.display.set_at((x + dx, y + dy), YELLOW)

    def draw_famicom_ghost(self, x, y, color):
        """Draw an 8-bit style ghost sprite."""
        # Ghost shape (8x8 sprite)
        ghost_pixels = [
            "  ####  ",
            " ###### ",
            "########",
            "## ## ##",
            "########",
            "########",
            "########",
            "# ## ## "
        ]
        
        for row, line in enumerate(ghost_pixels):
            for col, pixel in enumerate(line):
                if pixel == '#':
                    self.display.set_at((x + col, y + row), color)
                elif pixel == ' ':
                    pass  # Transparent

    def draw_text_8bit(self, text, color, x, y, size='normal', center=False):
        """Draw pixelated text for Famicom style."""
        # Create text surface
        if size == 'large':
            # Draw larger text by doubling pixels
            surface = MENU_FONT.render(text, False, color)
        else:
            surface = PIXEL_FONT.render(text, False, color)
            
        # Position text
        rect = surface.get_rect()
        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)
            
        self.display.blit(surface, rect)

    def check_wall_collision(self, x, y):
        """Check wall collision."""
        grid_x = int(x // TILE_SIZE)
        grid_y = int(y // TILE_SIZE)
        
        if grid_y < 0 or grid_y >= len(self.maze):
            return True
        if grid_x < 0 or grid_x >= len(self.maze[grid_y]):
            return False  # Allow tunnel wrapping
            
        tile = self.maze[grid_y][grid_x]
        return tile in [1, 4]

# --- Famicom Player Class ---
class FamicomPlayer:
    def __init__(self, game, x, y):
        self.game = game
        self.start_x, self.start_y = x, y
        self.x, self.y = x, y
        self.speed = 1.5
        self.direction = [0, 0]
        self.next_direction = [0, 0]
        self.animation_frame = 0

    def reset_position(self):
        self.x, self.y = self.start_x, self.start_y
        self.direction = [0, 0]
        self.next_direction = [0, 0]

    def set_direction(self, dx, dy):
        self.next_direction = [dx, dy]

    def update(self):
        # Try to turn at intersections
        if self.next_direction != [0, 0]:
            grid_x = self.x % TILE_SIZE
            grid_y = self.y % TILE_SIZE
            
            if grid_x < self.speed * 2 and grid_y < self.speed * 2:
                test_x = self.x + self.next_direction[0] * TILE_SIZE//2
                test_y = self.y + self.next_direction[1] * TILE_SIZE//2
                if not self.game.check_wall_collision(test_x, test_y):
                    self.direction = self.next_direction
                    self.next_direction = [0, 0]

        # Move
        next_x = self.x + self.direction[0] * self.speed
        next_y = self.y + self.direction[1] * self.speed
        
        if not self.game.check_wall_collision(next_x + TILE_SIZE//2, next_y + TILE_SIZE//2):
            self.x = next_x
            self.y = next_y
        else:
            self.direction = [0, 0]
            
        # Tunnel wrap
        if self.x < -TILE_SIZE:
            self.x = SCREEN_WIDTH
        elif self.x > SCREEN_WIDTH:
            self.x = -TILE_SIZE
            
        # Eat pellets
        self.eat_pellet()
        
        # Check ghost collision
        self.check_ghost_collision()
        
        # Animate
        if self.direction != [0, 0]:
            self.animation_frame += 1

    def eat_pellet(self):
        grid_x = int((self.x + TILE_SIZE//2) // TILE_SIZE)
        grid_y = int((self.y + TILE_SIZE//2) // TILE_SIZE)
        
        if 0 <= grid_y < len(self.game.maze) and 0 <= grid_x < len(self.game.maze[grid_y]):
            tile = self.game.maze[grid_y][grid_x]
            if tile == 2:  # Pellet
                self.game.maze[grid_y][grid_x] = 0
                self.game.score += 10
                self.game.pellets_remaining -= 1
            elif tile == 3:  # Power Pellet
                self.game.maze[grid_y][grid_x] = 0
                self.game.score += 50
                self.game.pellets_remaining -= 1
                self.game.frightened_timer = 6000
                for ghost in self.game.ghosts:
                    if ghost.mode != 'eaten':
                        ghost.mode = 'frightened'

    def check_ghost_collision(self):
        for ghost in self.game.ghosts:
            if abs(self.x - ghost.x) < TILE_SIZE - 2 and abs(self.y - ghost.y) < TILE_SIZE - 2:
                if ghost.mode == 'frightened':
                    self.game.score += 200
                    ghost.mode = 'eaten'
                elif ghost.mode != 'eaten':
                    self.game.lives -= 1
                    self.game.state = STATE_DIED
                    self.game.state_timer = 120

    def draw(self):
        """Draw Famicom-style Pac-Man (8x8 sprite)."""
        x, y = int(self.x), int(self.y)
        
        # Simple 8x8 Pac-Man sprite
        frame = (self.animation_frame // 4) % 3
        
        # Draw based on direction and frame
        if frame == 0:  # Closed mouth
            for dy in range(TILE_SIZE):
                for dx in range(TILE_SIZE):
                    if (dx - 4)**2 + (dy - 4)**2 <= 16:
                        self.game.display.set_at((x + dx, y + dy), YELLOW)
        else:  # Open mouth
            center_x, center_y = x + 4, y + 4
            
            # Determine mouth direction
            if self.direction == [1, 0]:  # Right
                angle_start, angle_end = 30, 330
            elif self.direction == [-1, 0]:  # Left
                angle_start, angle_end = 150, 210
            elif self.direction == [0, -1]:  # Up
                angle_start, angle_end = 60, 120
            elif self.direction == [0, 1]:  # Down
                angle_start, angle_end = 240, 300
            else:
                angle_start, angle_end = 30, 330
                
            # Draw pixels
            for dy in range(TILE_SIZE):
                for dx in range(TILE_SIZE):
                    dist = math.sqrt((dx - 4)**2 + (dy - 4)**2)
                    if dist <= 4:
                        angle = math.degrees(math.atan2(dy - 4, dx - 4))
                        if angle < 0:
                            angle += 360
                        # Check if pixel is in mouth area
                        in_mouth = False
                        if angle_start < angle_end:
                            in_mouth = angle_start <= angle <= angle_end
                        else:
                            in_mouth = angle >= angle_start or angle <= angle_end
                        
                        if not in_mouth:
                            self.game.display.set_at((x + dx, y + dy), YELLOW)

# --- Famicom Ghost Class ---
class FamicomGhost:
    def __init__(self, game, x, y, color, name):
        self.game = game
        self.start_x, self.start_y = x, y
        self.x, self.y = x, y
        self.color = color
        self.name = name
        self.direction = [0, -1]
        self.speed = 1.0
        self.mode = 'scatter'
        self.animation_frame = 0

    def reset_position(self):
        self.x, self.y = self.start_x, self.start_y
        self.direction = [0, -1]
        self.mode = 'scatter'

    def update(self):
        self.animation_frame += 1
        
        # Speed by mode
        if self.mode == 'frightened':
            self.speed = 0.5
        elif self.mode == 'eaten':
            self.speed = 2.0
        else:
            self.speed = 0.9
            
        # Return to base if eaten
        if self.mode == 'eaten':
            target_x = 13 * TILE_SIZE
            target_y = 9 * TILE_SIZE
            if abs(self.x - target_x) < TILE_SIZE and abs(self.y - target_y) < TILE_SIZE:
                self.mode = 'scatter'
                
        # Simple AI
        self.pathfind()
        
        # Move
        self.x += self.direction[0] * self.speed
        self.y += self.direction[1] * self.speed
        
        # Tunnel wrap
        if self.x < -TILE_SIZE:
            self.x = SCREEN_WIDTH
        elif self.x > SCREEN_WIDTH:
            self.x = -TILE_SIZE

    def pathfind(self):
        # Only turn at intersections
        grid_x = self.x % TILE_SIZE
        grid_y = self.y % TILE_SIZE
        
        if grid_x > self.speed * 2 or grid_y > self.speed * 2:
            return
            
        # Find valid moves
        moves = []
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            if (dx, dy) != (-self.direction[0], -self.direction[1]):
                test_x = self.x + dx * TILE_SIZE
                test_y = self.y + dy * TILE_SIZE
                if not self.game.check_wall_collision(test_x + 4, test_y + 4):
                    moves.append((dx, dy))
                    
        if moves:
            if self.mode == 'frightened':
                self.direction = random.choice(moves)
            else:
                # Basic chase AI
                target_x = self.game.player.x
                target_y = self.game.player.y
                
                best_move = moves[0]
                best_dist = float('inf')
                for move in moves:
                    future_x = self.x + move[0] * TILE_SIZE
                    future_y = self.y + move[1] * TILE_SIZE
                    dist = abs(future_x - target_x) + abs(future_y - target_y)
                    if dist < best_dist:
                        best_dist = dist
                        best_move = move
                self.direction = best_move

    def draw(self):
        """Draw Famicom 8-bit ghost sprite."""
        x, y = int(self.x), int(self.y)
        
        if self.mode == 'eaten':
            # Just eyes
            pygame.draw.rect(self.game.display, WHITE, (x + 2, y + 3, 2, 2))
            pygame.draw.rect(self.game.display, WHITE, (x + 5, y + 3, 2, 2))
        else:
            # Determine color
            if self.mode == 'frightened':
                color = BLUE if (self.game.frightened_timer > 2000 or 
                               (self.animation_frame // 10) % 2) else WHITE
            else:
                color = self.color
                
            # Draw 8x8 ghost sprite
            ghost_sprite = [
                "  ####  ",
                " ###### ",
                "########",
                "########",
                "########",
                "########",
                "########",
                "# ## ## "
            ]
            
            # Draw eyes on sprite
            if self.mode != 'frightened':
                ghost_sprite[3] = "##o##o##"
            
            for row, line in enumerate(ghost_sprite):
                for col, pixel in enumerate(line):
                    if pixel == '#':
                        self.game.display.set_at((x + col, y + row), color)
                    elif pixel == 'o' and self.mode != 'frightened':
                        self.game.display.set_at((x + col, y + row), WHITE)

# --- Main ---
if __name__ == "__main__":
    game = FamicomPacMan()
    game.run()

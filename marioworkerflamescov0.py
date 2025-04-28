# test.py
# Meow! A cute little Pygame level editor starter, nyaa~!
import pygame
import sys
import os # Nyaa~ needed for saving/loading later maybe!

# --- Purrfect Constants ---
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
GRID_SIZE = 32
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = (SCREEN_HEIGHT - 100) // GRID_SIZE # Leave space for palette, nya!
PALETTE_HEIGHT = 100
PALETTE_X = 0
PALETTE_Y = SCREEN_HEIGHT - PALETTE_HEIGHT
FPS = 60 # Super speedy, nyaa!

# --- Cute Colors, teehee! ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRID_COLOR = (200, 200, 200)
PALETTE_BG = (150, 150, 200)
RED_BLOCK = (255, 100, 100)
BLUE_BLOCK = (100, 100, 255)
GREEN_BLOCK = (100, 255, 100)
YELLOW_BLOCK = (255, 255, 100)
ERASER_COLOR = (50, 50, 50) # Special block for erasing, nya!

# --- Let's get Pygame ready! Purrrr ---
pygame.init()
pygame.font.init() # For text later, maybe! meow!
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("CATSDK's Purrfect Level Editor! Nyaa~")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24) # A small font for labels

# --- Level Data Storage (A cozy dictionary!) ---
# Maps (grid_x, grid_y) tuple to color tuple
level_data = {}

# --- Palette Elements (Our colorful toys!) ---
# Stores color and rectangle for clicking
palette_items = [
    {"color": RED_BLOCK, "rect": pygame.Rect(10, PALETTE_Y + 10, GRID_SIZE, GRID_SIZE), "name": "Red"},
    {"color": BLUE_BLOCK, "rect": pygame.Rect(10 + GRID_SIZE + 10, PALETTE_Y + 10, GRID_SIZE, GRID_SIZE), "name": "Blue"},
    {"color": GREEN_BLOCK, "rect": pygame.Rect(10 + (GRID_SIZE + 10) * 2, PALETTE_Y + 10, GRID_SIZE, GRID_SIZE), "name": "Green"},
    {"color": YELLOW_BLOCK, "rect": pygame.Rect(10 + (GRID_SIZE + 10) * 3, PALETTE_Y + 10, GRID_SIZE, GRID_SIZE), "name": "Yellow"},
    {"color": ERASER_COLOR, "rect": pygame.Rect(10 + (GRID_SIZE + 10) * 4, PALETTE_Y + 10, GRID_SIZE, GRID_SIZE), "name": "Eraser (Nyaa!)"},
]
selected_color = RED_BLOCK # Start with red, teehee!
selected_name = "Red"

# --- Camera/Scroll Offset (For exploring!) ---
camera_offset_x = 0
camera_offset_y = 0
# Nyaa~ for now, let's keep the grid fixed, scrolling is a big step!

# --- Helper Function: Grid to Screen Coords ---
def grid_to_screen(grid_x, grid_y):
    screen_x = grid_x * GRID_SIZE # + camera_offset_x # Add camera later!
    screen_y = grid_y * GRID_SIZE # + camera_offset_y
    return screen_x, screen_y

# --- Helper Function: Screen to Grid Coords ---
def screen_to_grid(screen_x, screen_y):
    grid_x = screen_x // GRID_SIZE # - camera_offset_x // GRID_SIZE # Adjust for camera later!
    grid_y = screen_y // GRID_SIZE # - camera_offset_y // GRID_SIZE
    return grid_x, grid_y

# --- Meow Game Loop! ---
running = True
mouse_dragging = False # Are we holding the mouse button? Nyaa~

while running:
    # --- Handle Input (What is the mouse doing? purr) ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            if event.button == 1: # Left click, nya!
                # Check palette first! Meow!
                palette_clicked = False
                for item in palette_items:
                    if item["rect"].collidepoint(mouse_x, mouse_y):
                        selected_color = item["color"]
                        selected_name = item["name"]
                        palette_clicked = True
                        print(f"Selected {selected_name} block, purrr!") # Debug message, nya!
                        break # Found our toy!

                # If not palette, check grid! Let's place blocks!
                if not palette_clicked and mouse_y < PALETTE_Y: # Only place above palette
                    grid_x, grid_y = screen_to_grid(mouse_x, mouse_y)
                    coord = (grid_x, grid_y)
                    if selected_color == ERASER_COLOR:
                        if coord in level_data:
                            del level_data[coord] # Erase it, poof!
                            print(f"Erased block at {coord}, nyaa!")
                    else:
                        level_data[coord] = selected_color # Place the block!
                        print(f"Placed {selected_name} block at {coord}, meow!")
                    mouse_dragging = True # Start dragging!

        if event.type == pygame.MOUSEBUTTONUP:
             if event.button == 1: # Left click released
                 mouse_dragging = False # Stop dragging, nya!

        if event.type == pygame.MOUSEMOTION:
            if mouse_dragging: # Only place if dragging started on grid
                 mouse_x, mouse_y = event.pos
                 if mouse_y < PALETTE_Y: # Only place above palette
                    grid_x, grid_y = screen_to_grid(mouse_x, mouse_y)
                    coord = (grid_x, grid_y)
                    if selected_color == ERASER_COLOR:
                        if coord in level_data:
                            del level_data[coord]
                            # Optional: add print for drag erase
                    else:
                        # Only place if different or not already there for efficiency
                        if coord not in level_data or level_data[coord] != selected_color:
                            level_data[coord] = selected_color
                            # Optional: add print for drag place

    # --- Purrrocessing / Updates (Not much yet, teehee!) ---
    # Future: Update animations, check game logic if testing, etc.

    # --- Drawing Time! Let's make it pretty! Nyaa~ ---
    screen.fill(WHITE) # Clear screen with white background

    # Draw the Grid (So many lines!)
    for x in range(0, SCREEN_WIDTH, GRID_SIZE):
        pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, SCREEN_HEIGHT - PALETTE_HEIGHT))
    for y in range(0, SCREEN_HEIGHT - PALETTE_HEIGHT, GRID_SIZE):
        pygame.draw.line(screen, GRID_COLOR, (0, y), (SCREEN_WIDTH, y))

    # Draw Placed Blocks (Our level!)
    for (grid_x, grid_y), color in level_data.items():
        screen_x, screen_y = grid_to_screen(grid_x, grid_y)
        block_rect = pygame.Rect(screen_x, screen_y, GRID_SIZE, GRID_SIZE)
        pygame.draw.rect(screen, color, block_rect)
        # Add a little border to see grid separation better, meow!
        pygame.draw.rect(screen, BLACK, block_rect, 1)

    # Draw the Palette (Where the toys are!)
    pygame.draw.rect(screen, PALETTE_BG, (PALETTE_X, PALETTE_Y, SCREEN_WIDTH, PALETTE_HEIGHT))
    for item in palette_items:
        pygame.draw.rect(screen, item["color"], item["rect"])
        pygame.draw.rect(screen, BLACK, item["rect"], 2) # Border around palette item
        # Highlight selected item, purrr!
        if item["color"] == selected_color:
            pygame.draw.rect(screen, WHITE, item["rect"], 3) # Thicker white border

    # Draw selected tool text, nya!
    selected_text = font.render(f"Selected: {selected_name}", True, BLACK)
    screen.blit(selected_text, (10 + (GRID_SIZE + 10) * len(palette_items) + 20, PALETTE_Y + 20))

    # --- Flip the display (Show our masterpiece!) ---
    pygame.display.flip()

    # --- Keep it smooth, like a cat's fur! (FPS Control) ---
    clock.tick(FPS)

# --- Bye bye! Clean up time! ---
pygame.quit()
sys.exit()

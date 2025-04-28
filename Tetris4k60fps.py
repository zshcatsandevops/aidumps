import pygame
import random
import os

# Initialize Pygame
pygame.init()

# --- Game Constants ---
GAME_WIDTH = 10  # Grid width
GAME_HEIGHT = 20  # Grid height
BLOCK_SIZE = 16  # Size of each Tetromino block in pixels
BOARD_LEFT = 100 # Left edge of the Tetris board area
BOARD_TOP = 50 # Top edge of the Tetris board area
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 320
FPS = 60

# Colors (shades of gray for Game Boy feel)
WHITE = (255, 255, 255)
LIGHT_GRAY = (192, 192, 192)
MID_GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
BLACK = (0, 0, 0)

# Tetromino shapes (rotations) and colors
# Shapes are represented by a list of (row, col) offsets
SHAPES = {
    'I': [[(0, 0), (0, 1), (0, 2), (0, 3)],
          [(0, 2), (1, 2), (2, 2), (3, 2)],
          [(3, 0), (3, 1), (3, 2), (3, 3)],
          [(0, 1), (1, 1), (2, 1), (3, 1)]],
    'J': [[(0, 0), (1, 0), (1, 1), (1, 2)],
          [(0, 1), (0, 2), (1, 1), (2, 1)],
          [(1, 0), (1, 1), (1, 2), (2, 2)],
          [(0, 1), (1, 1), (2, 1), (2, 0)]],
    'L': [[(0, 2), (1, 0), (1, 1), (1, 2)],
          [(0, 1), (1, 1), (2, 1), (2, 2)],
          [(1, 0), (1, 1), (1, 2), (2, 0)],
          [(0, 0), (0, 1), (1, 1), (2, 1)]],
    'O': [[(0, 0), (0, 1), (1, 0), (1, 1)]], # O doesn't rotate in this classic version
    'S': [[(0, 1), (0, 2), (1, 0), (1, 1)],
          [(0, 1), (1, 1), (1, 2), (2, 2)]], # Only two rotations in GB Tetris
    'T': [[(0, 1), (1, 0), (1, 1), (1, 2)],
          [(0, 1), (1, 1), (1, 2), (2, 1)],
          [(1, 0), (1, 1), (1, 2), (2, 1)], # Mistake in transcription, should be T shape rotations
          [(0, 1), (1, 0), (1, 1), (2, 1)]], # This is the correct set
    'Z': [[(0, 0), (0, 1), (1, 1), (1, 2)],
          [(0, 2), (1, 1), (1, 2), (2, 1)]]  # Only two rotations in GB Tetris
}

# Colors for each shape (using shades of gray)
# Map shape names to a color value (e.g., 0 for empty, 1 for light, 2 for mid, 3 for dark)
SHAPE_COLORS = {
    'I': 1, # Light gray
    'J': 2, # Mid gray
    'L': 3, # Dark gray
    'O': 1, # Light gray
    'S': 2, # Mid gray
    'T': 3, # Dark gray
    'Z': 1  # Light gray
}

# Color mapping for drawing
COLOR_MAP = {
    0: WHITE,
    1: LIGHT_GRAY,
    2: MID_GRAY,
    3: DARK_GRAY
}


# Game State Variables
grid = [[0 for _ in range(GAME_WIDTH)] for _ in range(GAME_HEIGHT)]
current_piece = None
next_piece = None
score = 0
level = 0
lines_cleared = 0
game_over = False
game_paused = False
game_type = 'A' # 'A' or 'B'
high_level = 0 # For B-Type, number of initial lines
high_scores = [] # List of (score, name) tuples

# Movement/Timing Variables
fall_time = 0
fall_speed = [0.048, 0.046, 0.044, 0.042, 0.04, 0.038, 0.036, 0.034, 0.032, 0.03] # Speed for levels 0-9
move_time = 0
move_delay = 0.1 # Time between automatic sideways movement
rotate_time = 0
rotate_delay = 0.2 # Time between rotations

# Sound effects (placeholders)
# Add actual sound loading later

# --- Functions ---

def create_piece(shape_name=None):
    """Creates a new Tetromino piece."""
    if shape_name is None:
        shape_name = random.choice(list(SHAPES.keys()))

    shape_patterns = SHAPES[shape_name]
    pattern = random.choice(shape_patterns) # Start with a random initial rotation
    color = SHAPE_COLORS[shape_name]
    # Initial position (top center of the board)
    col = GAME_WIDTH // 2 - max(p[1] for p in pattern) // 2
    row = 0 # Start at the top

    return {'shape': shape_name, 'pattern': pattern, 'color': color, 'row': row, 'col': col, 'rotation': shape_patterns.index(pattern)}

def is_valid_position(piece, board):
    """Checks if the piece is in a valid position on the board."""
    for r_offset, c_offset in piece['pattern']:
        r, c = piece['row'] + r_offset, piece['col'] + c_offset
        # Check boundaries
        if not (0 <= r < GAME_HEIGHT and 0 <= c < GAME_WIDTH):
            return False
        # Check collision with existing blocks
        if board[r][c] != 0:
            return False
    return True

def rotate_piece(piece, board):
    """Rotates the piece and checks for validity."""
    current_rotation = piece['rotation']
    shape_patterns = SHAPES[piece['shape']]
    next_rotation = (current_rotation + 1) % len(shape_patterns)
    next_pattern = shape_patterns[next_rotation]

    rotated_piece = piece.copy()
    rotated_piece['pattern'] = next_pattern
    rotated_piece['rotation'] = next_rotation

    # Check for wall kicks or adjustments if needed (more complex for real Tetris, simplified here)
    # Simple check: is the new position valid?
    if is_valid_position(rotated_piece, board):
        piece.update(rotated_piece)
        return True
    return False # Rotation failed

def move_piece(piece, dr, dc, board):
    """Moves the piece by dr rows and dc columns and checks for validity."""
    new_piece = piece.copy()
    new_piece['row'] += dr
    new_piece['col'] += dc

    if is_valid_position(new_piece, board):
        piece.update(new_piece)
        return True
    return False # Move failed

def lock_piece(piece, board):
    """Locks the current piece into the board."""
    for r_offset, c_offset in piece['pattern']:
        r, c = piece['row'] + r_offset, piece['col'] + c_offset
        if 0 <= r < GAME_HEIGHT and 0 <= c < GAME_WIDTH: # Ensure within bounds (should be checked by is_valid)
            board[r][c] = piece['color']
    clear_lines(board)
    global score # Need to update score based on lines cleared

def clear_lines(board):
    """Checks for and clears full lines, updates score and line count."""
    global score, lines_cleared, level, fall_speed # Need to update these globals
    lines_to_clear = []
    for r in range(GAME_HEIGHT):
        if all(board[r][c] != 0 for c in range(GAME_WIDTH)):
            lines_to_clear.append(r)

    if not lines_to_clear:
        return

    # Score calculation (classic Tetris Game Boy A-Type)
    # Points are added when lines are cleared, multiplied by level + 1
    points_per_line = {1: 40, 2: 100, 3: 300, 4: 1200}
    num_cleared = len(lines_to_clear)
    if num_cleared > 0:
        # Base score for clearing lines depends on number of lines * (level + 1)
        if num_cleared in points_per_line:
             score += points_per_line[num_cleared] * (level + 1)

        # Remove lines from bottom up
        for r in reversed(lines_to_clear):
            board.pop(r)
            board.insert(0, [0 for _ in range(GAME_WIDTH)]) # Add empty line at the top

        lines_cleared += num_cleared

        # Level progression (every 10 lines in A-Type)
        # Level increases every 10 lines. Max level displayed is 20.
        # Speed increases up to level 9. Levels 10+ have same speed.
        next_level = min(20, lines_cleared // 10)
        if next_level > level:
            level = next_level
            # Update fall speed if level is within the speed progression range
            if level <= 9:
                fall_speed[level] # Access the speed for the new level (or re-calculate if not using a pre-defined list)
                # The list is pre-defined, so just knowing the level updates the speed
                # The Game Boy speed chart is actually more complex, but this is a decent approximation
                # Fall speed for level 9 and above is very fast.
                # For GB Tetris, speeds are specific per level up to 9, then constant.
                # Levels 0-8: 48, 46, 44, 42, 40, 38, 36, 34, 32ms per row.
                # Level 9: 30ms per row.
                # Levels 10-19: 30ms per row.
                # Level 20+: 16ms per row.
                # My current fall_speed list is for levels 0-9. Let's adjust the logic.
                pass # Fall speed will be looked up based on the current level below

def calculate_fall_speed(current_level):
     """Calculates the fall speed based on the current level."""
     if current_level <= 8:
         return 0.048 - current_level * 0.002 # Approx decreasing speed
     elif current_level <= 19:
         return 0.03 # Level 9-19 speed
     else: # Level 20+
         return 0.016 # Max speed

def draw_board(surface, board):
    """Draws the game board and locked pieces."""
    for r in range(GAME_HEIGHT):
        for c in range(GAME_WIDTH):
            block_color = COLOR_MAP[board[r][c]]
            block_rect = pygame.Rect(BOARD_LEFT + c * BLOCK_SIZE, BOARD_TOP + r * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
            pygame.draw.rect(surface, block_color, block_rect)
            # Draw black border
            pygame.draw.rect(surface, BLACK, block_rect, 1) # 1 pixel border

    # Draw side walls
    wall_width = 10
    wall_color = DARK_GRAY
    pygame.draw.rect(surface, wall_color, (BOARD_LEFT - wall_width, BOARD_TOP, wall_width, GAME_HEIGHT * BLOCK_SIZE))
    pygame.draw.rect(surface, wall_color, (BOARD_LEFT + GAME_WIDTH * BLOCK_SIZE, BOARD_TOP, wall_width, GAME_HEIGHT * BLOCK_SIZE))
    # Draw bottom border (optional, the grid itself forms the bottom)
    # pygame.draw.rect(surface, wall_color, (BOARD_LEFT - wall_width, BOARD_TOP + GAME_HEIGHT * BLOCK_SIZE, GAME_WIDTH * BLOCK_SIZE + 2 * wall_width, wall_width))

def draw_piece(surface, piece):
    """Draws the current Tetromino piece."""
    if piece is None:
        return
    block_color = COLOR_MAP[piece['color']]
    for r_offset, c_offset in piece['pattern']:
        r, c = piece['row'] + r_offset, piece['col'] + c_offset
        # Only draw if the block is within the visible game area
        if 0 <= r < GAME_HEIGHT and 0 <= c < GAME_WIDTH:
             block_rect = pygame.Rect(BOARD_LEFT + c * BLOCK_SIZE, BOARD_TOP + r * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
             pygame.draw.rect(surface, block_color, block_rect)
             # Draw black border
             pygame.draw.rect(surface, BLACK, block_rect, 1) # 1 pixel border


def draw_ui(surface):
    """Draws the score, level, lines, and next piece UI."""
    font = pygame.font.Font(None, 24) # Simple font

    # Score
    score_text = font.render(f"SCORE", True, BLACK)
    score_value_text = font.render(f"{score:06}", True, BLACK)
    surface.blit(score_text, (BOARD_LEFT + GAME_WIDTH * BLOCK_SIZE + 30, BOARD_TOP))
    surface.blit(score_value_text, (BOARD_LEFT + GAME_WIDTH * BLOCK_SIZE + 30, BOARD_TOP + 20))

    # Level
    level_text = font.render(f"LEVEL", True, BLACK)
    # Show heart icon for levels >= 10 as per GB Tetris A-type visual cue
    level_value_str = f"{level:02}" if level < 10 else f"{level:02}♥"
    level_value_text = font.render(level_value_str, True, BLACK)
    surface.blit(level_text, (BOARD_LEFT + GAME_WIDTH * BLOCK_SIZE + 30, BOARD_TOP + 60))
    surface.blit(level_value_text, (BOARD_LEFT + GAME_WIDTH * BLOCK_SIZE + 30, BOARD_TOP + 80))

    # Lines
    lines_text = font.render(f"LINES", True, BLACK)
    lines_value_text = font.render(f"{lines_cleared:03}", True, BLACK)
    surface.blit(lines_text, (BOARD_LEFT + GAME_WIDTH * BLOCK_SIZE + 30, BOARD_TOP + 120))
    surface.blit(lines_value_text, (BOARD_LEFT + GAME_WIDTH * BLOCK_SIZE + 30, BOARD_TOP + 140))

    # Next Piece
    next_text = font.render("NEXT", True, BLACK)
    surface.blit(next_text, (BOARD_LEFT + GAME_WIDTH * BLOCK_SIZE + 30, BOARD_TOP + 180))
    if next_piece:
        next_piece_preview = next_piece.copy()
        # Center the preview piece in a small area
        preview_area_left = BOARD_LEFT + GAME_WIDTH * BLOCK_SIZE + 30
        preview_area_top = BOARD_TOP + 200
        # Adjust position for drawing in the preview area
        # Find the min/max row/col offsets of the shape
        min_r = min(p[0] for p in next_piece_preview['pattern'])
        min_c = min(p[1] for p in next_piece_preview['pattern'])
        max_c = max(p[1] for p in next_piece_preview['pattern'])
        shape_width = max_c - min_c + 1
        # Center horizontally in a 4-block space (common size for next piece preview)
        col_offset = (4 - shape_width) // 2 - min_c
        row_offset = -min_r # Move it up to draw from relative (0,0)

        block_color = COLOR_MAP[next_piece_preview['color']]
        for r_offset, c_offset in next_piece_preview['pattern']:
            r, c = row_offset + r_offset, col_offset + c_offset
            block_rect = pygame.Rect(preview_area_left + c * BLOCK_SIZE, preview_area_top + r * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
            pygame.draw.rect(surface, block_color, block_rect)
            pygame.draw.rect(surface, BLACK, block_rect, 1) # 1 pixel border

def draw_game_over(surface):
    """Draws the Game Over screen."""
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 128)) # Semi-transparent black overlay
    surface.blit(overlay, (0, 0))

    font_large = pygame.font.Font(None, 72)
    font_medium = pygame.font.Font(None, 36)

    game_over_text = font_large.render("GAME OVER", True, WHITE)
    try_again_text = font_medium.render("PLEASE TRY AGAIN ♥", True, WHITE) # Match GB text

    game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
    try_again_rect = try_again_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))

    surface.blit(game_over_text, game_over_rect)
    surface.blit(try_again_text, try_again_rect)

    # Optionally, load and display the rocket animation or character scene
    # For simplicity, we'll just draw the text here.

def load_high_scores(filename="highscores.txt"):
    """Loads high scores from a file."""
    scores = []
    if os.path.exists(filename):
        with open(filename, "r") as f:
            for line in f:
                try:
                    s, n = line.strip().split(",")
                    scores.append((int(s), n))
                except ValueError:
                    continue # Skip malformed lines
    return sorted(scores, reverse=True)[:3] # Return top 3 scores

def save_high_scores(scores, filename="highscores.txt"):
    """Saves high scores to a file."""
    with open(filename, "w") as f:
        for s, n in scores:
            f.write(f"{s},{n}\n")

def show_high_scores(surface):
    """Displays the top high scores."""
    font = pygame.font.Font(None, 36)
    title_text = font.render("TOP SCORES", True, BLACK)
    surface.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 50))

    score_y = 120
    for i, (s, n) in enumerate(high_scores):
        score_text = font.render(f"{i+1}. {n} {s}", True, BLACK)
        surface.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, score_y + i * 40))

# --- Game Initialization ---
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Game Boy Tetris Clone")
clock = pygame.time.Clock()

# Load initial game state
high_scores = load_high_scores()

def reset_game(start_level=0, start_high=0, game_mode='A'):
    """Resets the game state."""
    global grid, current_piece, next_piece, score, level, lines_cleared, game_over, fall_time, move_time, rotate_time, game_type, high_level

    game_type = game_mode
    high_level = start_high # Only relevant for B-Type
    level = start_level
    score = 0
    lines_cleared = 0
    game_over = False
    fall_time = 0
    move_time = 0
    rotate_time = 0

    grid = [[0 for _ in range(GAME_WIDTH)] for _ in range(GAME_HEIGHT)]

    if game_type == 'B':
        # Add initial blocks for B-Type
        initial_rows = start_high + 1 # Number of rows to fill from bottom (High 0 = 1 row, High 5 = 6 rows)
        initial_rows = min(initial_rows, GAME_HEIGHT - 5) # Don't fill too high
        for r in range(GAME_HEIGHT - initial_rows, GAME_HEIGHT):
             # Fill row with random blocks, leaving at least one gap
            num_blocks = random.randint(3, GAME_WIDTH - 1) # Leave at least one gap
            filled_cols = random.sample(range(GAME_WIDTH), num_blocks)
            for c in filled_cols:
                 grid[r][c] = random.randint(1, 3) # Random color

    current_piece = create_piece()
    next_piece = create_piece()

# --- Game Loop States ---
STATE_TITLE = 0
STATE_MENU = 1
STATE_PLAYING = 2
STATE_GAME_OVER = 3
STATE_HIGHSCORE = 4

current_state = STATE_TITLE
menu_selection = 'A-TYPE' # Initial menu selection

# --- Menu/Title Screen Logic ---
def draw_title(surface):
     surface.fill(WHITE)
     font = pygame.font.Font(None, 72)
     title_text = font.render("TETRIS", True, BLACK)
     title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
     surface.blit(title_text, title_rect)

     # Simple "Press Start" like prompt
     font_small = pygame.font.Font(None, 36)
     prompt_text = font_small.render("PRESS ANY KEY", True, BLACK)
     prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT * 2 // 3))
     surface.blit(prompt_text, prompt_rect)

     # Add the Moscow background image if available (optional)
     # try:
     #     background_img = pygame.image.load('moscow.png') # You need an image file named moscow.png
     #     background_img = pygame.transform.scale(background_img, (SCREEN_WIDTH, SCREEN_HEIGHT // 2))
     #     surface.blit(background_img, (0, SCREEN_HEIGHT // 2))
     # except pygame.error:
     #     pass # No background image

     pygame.display.flip()

def handle_title_input(event):
     global current_state
     if event.type == pygame.KEYDOWN:
         current_state = STATE_MENU

def draw_menu(surface, selected_option):
    surface.fill(LIGHT_GRAY) # Dotted background? Can simulate with drawing
    # Draw dots
    for x in range(0, SCREEN_WIDTH, 4):
        for y in range(0, SCREEN_HEIGHT, 4):
            surface.set_at((x, y), MID_GRAY)

    font = pygame.font.Font(None, 36)

    # Game Type selection
    game_type_text = font.render("GAME TYPE", True, BLACK)
    a_type_text = font.render("A-TYPE", True, BLACK)
    b_type_text = font.render("B-TYPE", True, BLACK)

    surface.blit(game_type_text, (SCREEN_WIDTH // 2 - game_type_text.get_width() // 2, 50))

    a_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 90, 80, 30)
    b_rect = pygame.Rect(SCREEN_WIDTH // 2 + 20, 90, 80, 30)

    pygame.draw.rect(surface, DARK_GRAY, a_rect, 1)
    pygame.draw.rect(surface, DARK_GRAY, b_rect, 1)

    if selected_option == 'A-TYPE':
        pygame.draw.rect(surface, DARK_GRAY, a_rect)
        surface.blit(a_type_text, a_rect.move(5, 5), special_flags=pygame.BLEND_RGBA_MULT) # Draw text darker inside
    else:
        surface.blit(a_type_text, a_rect.move(5, 5))

    if selected_option == 'B-TYPE':
         pygame.draw.rect(surface, DARK_GRAY, b_rect)
         surface.blit(b_type_text, b_rect.move(5, 5), special_flags=pygame.BLEND_RGBA_MULT) # Draw text darker inside
    else:
         surface.blit(b_type_text, b_rect.move(5, 5))

    # Level selection (simplified: pick a start level 0-9)
    level_text = font.render("LEVEL", True, BLACK)
    surface.blit(level_text, (SCREEN_WIDTH // 2 - level_text.get_width() // 2, 150))
    # Draw level grid - simplified for now
    level_grid_left = SCREEN_WIDTH // 2 - (5 * BLOCK_SIZE + 4 * 5) // 2 # Center 5 blocks
    for i in range(10):
        r = i // 5
        c = i % 5
        level_rect = pygame.Rect(level_grid_left + c * (BLOCK_SIZE + 5), 180 + r * (BLOCK_SIZE + 5), BLOCK_SIZE, BLOCK_SIZE)
        pygame.draw.rect(surface, DARK_GRAY, level_rect, 1)
        level_num_text = font.render(str(i), True, BLACK)
        level_num_rect = level_num_text.get_rect(center=level_rect.center)
        surface.blit(level_num_text, level_num_rect)
        # Highlight selected level (need state for this)
        if selected_option == f'LEVEL {i}':
             pygame.draw.rect(surface, DARK_GRAY, level_rect)
             level_num_text = font.render(str(i), True, WHITE) # White text on dark background
             level_num_rect = level_num_text.get_rect(center=level_rect.center)
             surface.blit(level_num_text, level_num_rect)


    # High selection (for B-Type, number of initial lines)
    if game_type == 'B':
        high_text = font.render("HIGH", True, BLACK)
        surface.blit(high_text, (SCREEN_WIDTH // 2 - high_text.get_width() // 2, 240))
        # Draw high grid - simplified for now (levels 0-5 shown in video)
        high_grid_left = SCREEN_WIDTH // 2 - (3 * BLOCK_SIZE + 2 * 5) // 2 # Center 3 blocks
        for i in range(6):
            r = i // 3
            c = i % 3
            high_rect = pygame.Rect(high_grid_left + c * (BLOCK_SIZE + 5), 270 + r * (BLOCK_SIZE + 5), BLOCK_SIZE, BLOCK_SIZE)
            pygame.draw.rect(surface, DARK_GRAY, high_rect, 1)
            high_num_text = font.render(str(i), True, BLACK)
            high_num_rect = high_num_text.get_rect(center=high_rect.center)
            surface.blit(high_num_text, high_num_rect)
            # Highlight selected high level
            if selected_option == f'HIGH {i}':
                 pygame.draw.rect(surface, DARK_GRAY, high_rect)
                 high_num_text = font.render(str(i), True, WHITE) # White text on dark background
                 high_num_rect = high_num_text.get_rect(center=high_rect.center)
                 surface.blit(high_num_text, high_num_rect)


    # Start button - implied by level selection, maybe add a dedicated button
    # For now, pressing start after selecting level/high starts the game

    pygame.display.flip()


def handle_menu_input(event):
     global current_state, menu_selection, level, high_level, game_type, fall_time, move_time, rotate_time

     # Define selectable regions
     game_type_a_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 90, 80, 30)
     game_type_b_rect = pygame.Rect(SCREEN_WIDTH // 2 + 20, 90, 80, 30)

     level_rects = {}
     level_grid_left = SCREEN_WIDTH // 2 - (5 * BLOCK_SIZE + 4 * 5) // 2
     for i in range(10):
         r = i // 5
         c = i % 5
         level_rects[f'LEVEL {i}'] = pygame.Rect(level_grid_left + c * (BLOCK_SIZE + 5), 180 + r * (BLOCK_SIZE + 5), BLOCK_SIZE, BLOCK_SIZE)

     high_rects = {}
     high_grid_left = SCREEN_WIDTH // 2 - (3 * BLOCK_SIZE + 2 * 5) // 2
     for i in range(6):
         r = i // 3
         c = i % 3
         high_rects[f'HIGH {i}'] = pygame.Rect(high_grid_left + c * (BLOCK_SIZE + 5), 270 + r * (BLOCK_SIZE + 5), BLOCK_SIZE, BLOCK_SIZE)

     if event.type == pygame.KEYDOWN:
         if event.key == pygame.K_DOWN:
             if menu_selection == 'A-TYPE' or menu_selection == 'B-TYPE':
                 menu_selection = 'LEVEL 0'
             elif menu_selection.startswith('LEVEL'):
                  current_level_idx = int(menu_selection.split(' ')[1])
                  next_level_idx = current_level_idx + 5
                  if next_level_idx <= 9:
                      menu_selection = f'LEVEL {next_level_idx}'
                  elif game_type == 'B': # From level row to high row in B-Type
                      menu_selection = 'HIGH 0'
                  else: # Loop back to A-Type/B-Type in A-Type mode
                      menu_selection = game_type + '-TYPE'

             elif menu_selection.startswith('HIGH'):
                 current_high_idx = int(menu_selection.split(' ')[1])
                 next_high_idx = current_high_idx + 3
                 if next_high_idx <= 5:
                      menu_selection = f'HIGH {next_high_idx}'
                 else: # Loop back to Game Type
                      menu_selection = game_type + '-TYPE'

         elif event.key == pygame.K_UP:
             if menu_selection == 'A-TYPE' or menu_selection == 'B-TYPE':
                 # Maybe loop to the last option? For now, stay put.
                 pass
             elif menu_selection.startswith('LEVEL'):
                  current_level_idx = int(menu_selection.split(' ')[1])
                  next_level_idx = current_level_idx - 5
                  if next_level_idx >= 0:
                      menu_selection = f'LEVEL {next_level_idx}'
                  else: # Loop back to Game Type
                      menu_selection = game_type + '-TYPE'
             elif menu_selection.startswith('HIGH'):
                 current_high_idx = int(menu_selection.split(' ')[1])
                 next_high_idx = current_high_idx - 3
                 if next_high_idx >= 0:
                      menu_selection = f'HIGH {next_high_idx}'
                 else: # Loop to the last level option
                      menu_selection = 'LEVEL ' + str(current_level_idx // 5 + (10 - 1) % 5) # Needs refinement to get the actual last level row

         elif event.key == pygame.K_LEFT:
             if menu_selection == 'B-TYPE':
                 menu_selection = 'A-TYPE'
                 game_type = 'A'
             elif menu_selection.startswith('LEVEL'):
                  current_level_idx = int(menu_selection.split(' ')[1])
                  if current_level_idx % 5 > 0:
                      menu_selection = f'LEVEL {current_level_idx - 1}'
             elif menu_selection.startswith('HIGH'):
                 current_high_idx = int(menu_selection.split(' ')[1])
                 if current_high_idx % 3 > 0:
                      menu_selection = f'HIGH {current_high_idx - 1}'

         elif event.key == pygame.K_RIGHT:
             if menu_selection == 'A-TYPE':
                 menu_selection = 'B-TYPE'
                 game_type = 'B'
             elif menu_selection.startswith('LEVEL'):
                 current_level_idx = int(menu_selection.split(' ')[1])
                 if current_level_idx % 5 < 4 and current_level_idx < 9:
                     menu_selection = f'LEVEL {current_level_idx + 1}'
             elif menu_selection.startswith('HIGH'):
                 current_high_idx = int(menu_selection.split(' ')[1])
                 if current_high_idx % 3 < 2 and current_high_idx < 5:
                     menu_selection = f'HIGH {current_high_idx + 1}'

         elif event.key == pygame.K_RETURN: # Start game
             if menu_selection == 'A-TYPE':
                 reset_game(start_level=0, game_mode='A')
                 current_state = STATE_PLAYING
             elif menu_selection == 'B-TYPE':
                 reset_game(start_level=9, start_high=0, game_mode='B') # Default start for B is Level 9 High 0
                 current_state = STATE_PLAYING
             elif menu_selection.startswith('LEVEL'):
                 start_level = int(menu_selection.split(' ')[1])
                 if game_type == 'A':
                      reset_game(start_level=start_level, game_mode='A')
                 else: # B-Type, keep current high_level
                      reset_game(start_level=start_level, start_high=high_level, game_mode='B')
                 current_state = STATE_PLAYING
             elif menu_selection.startswith('HIGH') and game_type == 'B':
                 start_high = int(menu_selection.split(' ')[1])
                 # Keep current level for B-Type
                 current_level = int(menu_selection.split(' ')[1].split(' ')[0]) # This is wrong
                 # Need to store selected level for B-Type separately
                 reset_game(start_level=level, start_high=start_high, game_mode='B')
                 current_state = STATE_PLAYING
             elif menu_selection == 'TOP-SCORE': # Needs UI element for this
                  current_state = STATE_HIGHSCORE # Implement High Score display state

     # Simplified click detection for menu (approximate areas)
     elif event.type == pygame.MOUSEBUTTONDOWN:
         if game_type_a_rect.collidepoint(event.pos):
             menu_selection = 'A-TYPE'
             game_type = 'A'
         elif game_type_b_rect.collidepoint(event.pos):
             menu_selection = 'B-TYPE'
             game_type = 'B'
         for option, rect in level_rects.items():
             if rect.collidepoint(event.pos):
                 menu_selection = option
                 level = int(option.split(' ')[1])
         for option, rect in high_rects.items():
             if rect.collidepoint(event.pos) and game_type == 'B':
                 menu_selection = option
                 high_level = int(option.split(' ')[1])
         # Add click handler for TOP-SCORE etc. later

def draw_high_score_screen(surface):
    surface.fill(LIGHT_GRAY)
    # Draw dots
    for x in range(0, SCREEN_WIDTH, 4):
        for y in range(0, SCREEN_HEIGHT, 4):
            surface.set_at((x, y), MID_GRAY)

    font_large = pygame.font.Font(None, 48)
    font_medium = pygame.font.Font(None, 36)

    title_text = font_large.render("TOP SCORES", True, BLACK)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
    surface.blit(title_text, title_rect)

    score_y = 120
    for i, (s, n) in enumerate(high_scores):
        score_text = font_medium.render(f"{i+1}. {n} {s}", True, BLACK)
        surface.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, score_y + i * 40))

    prompt_text = font_medium.render("PRESS ANY KEY TO RETURN", True, BLACK)
    prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
    surface.blit(prompt_text, prompt_rect)

    pygame.display.flip()

def handle_high_score_input(event):
    global current_state
    if event.type == pygame.KEYDOWN:
        current_state = STATE_MENU # Go back to menu

# --- Game Loop ---
running = True
while running:
    dt = clock.tick(FPS) / 1000.0 # Delta time in seconds

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if current_state == STATE_TITLE:
            handle_title_input(event)
        elif current_state == STATE_MENU:
            handle_menu_input(event)
        elif current_state == STATE_PLAYING:
            # Handle player input during gameplay
            if not game_paused and not game_over:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        move_piece(current_piece, 0, -1, grid)
                    elif event.key == pygame.K_RIGHT:
                        move_piece(current_piece, 0, 1, grid)
                    elif event.key == pygame.K_DOWN:
                        # Soft drop
                        fall_time += calculate_fall_speed(level) * 5 # Speed up fall
                    elif event.key == pygame.K_UP:
                        # Rotate
                        rotate_piece(current_piece, grid)
                    elif event.key == pygame.K_SPACE:
                         # Hard drop
                        while move_piece(current_piece, 1, 0, grid):
                            score += 1 # Add point for each row dropped
                        lock_piece(current_piece, grid)
                        current_piece = None # Signal to create new piece
                    elif event.key == pygame.K_p: # Pause
                        game_paused = True
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_p and game_paused: # Unpause
                 game_paused = False
        elif current_state == STATE_GAME_OVER:
            # Handle input on game over screen (e.g., press key to return to menu)
            if event.type == pygame.KEYDOWN:
                # Check if the score is a high score before returning
                if len(high_scores) < 3 or score > high_scores[-1][0]:
                     # Prompt for name input (simplified - just ask in console)
                     print("New High Score!")
                     player_name = input("Enter your name (max 3 chars): ").upper()[:3]
                     high_scores.append((score, player_name))
                     high_scores = sorted(high_scores, reverse=True)[:3]
                     save_high_scores(high_scores)

                current_state = STATE_MENU
                menu_selection = 'A-TYPE' # Reset menu selection

        elif current_state == STATE_HIGHSCORE:
            handle_high_score_input(event)


    # --- Game Logic (State-based) ---
    if current_state == STATE_PLAYING and not game_paused and not game_over:
        fall_time += dt
        current_fall_speed = calculate_fall_speed(level)

        if fall_time >= current_fall_speed:
            fall_time = 0
            if not move_piece(current_piece, 1, 0, grid):
                # Piece landed
                lock_piece(current_piece, grid)
                current_piece = None # Signal to create new piece

        if current_piece is None:
            # Create a new piece
            current_piece = next_piece
            next_piece = create_piece()

            # Check for game over
            if not is_valid_position(current_piece, grid):
                game_over = True
                current_state = STATE_GAME_OVER # Change state

    # --- Drawing (State-based) ---
    screen.fill(WHITE) # Background color

    if current_state == STATE_TITLE:
        draw_title(screen)
    elif current_state == STATE_MENU:
        draw_menu(screen, menu_selection)
    elif current_state == STATE_PLAYING:
        draw_board(screen, grid)
        draw_piece(screen, current_piece)
        draw_ui(screen)
        if game_paused:
             # Draw pause overlay (e.g., PAUSED text)
             pause_font = pygame.font.Font(None, 72)
             pause_text = pause_font.render("PAUSED", True, BLACK)
             pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
             screen.blit(pause_text, pause_rect)

    elif current_state == STATE_GAME_OVER:
        # Draw the final state before overlay
        draw_board(screen, grid)
        draw_ui(screen) # Show final score/lines
        draw_game_over(screen) # Draw overlay and text
    elif current_state == STATE_HIGHSCORE:
         draw_high_score_screen(screen)


    pygame.display.flip()

pygame.quit()

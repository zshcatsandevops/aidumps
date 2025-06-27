import os
import pygame
import numpy as np
import random

# --- INITIAL SETUP (FROM USER) ---
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# Screen dimensions
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700
GRID_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
SIDEBAR_WIDTH = 250
HOLD_BOX_SIZE = 120

# Play area dimensions
PLAY_WIDTH = GRID_WIDTH * GRID_SIZE
PLAY_HEIGHT = GRID_HEIGHT * GRID_SIZE
TOP_LEFT_X = (SCREEN_WIDTH - SIDEBAR_WIDTH - PLAY_WIDTH) // 2
TOP_LEFT_Y = SCREEN_HEIGHT - PLAY_HEIGHT - 20

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (40, 40, 40)
DARK_GRAY = (20, 20, 20)
LIGHT_GRAY = (60, 60, 60)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 100, 255)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (148, 0, 211)

# --- SHAPES AND COLORS (CORRECTED) ---
I_SHAPE = [[0,0,0,0], [1,1,1,1], [0,0,0,0], [0,0,0,0]]
O_SHAPE = [[1,1], [1,1]]
T_SHAPE = [[0,1,0], [1,1,1], [0,0,0]]
L_SHAPE = [[0,0,1], [1,1,1], [0,0,0]]
J_SHAPE = [[1,0,0], [1,1,1], [0,0,0]]
S_SHAPE = [[0,1,1], [1,1,0], [0,0,0]]
Z_SHAPE = [[1,1,0], [0,1,1], [0,0,0]]

SHAPES = [I_SHAPE, O_SHAPE, T_SHAPE, L_SHAPE, J_SHAPE, S_SHAPE, Z_SHAPE]
COLORS = [CYAN, YELLOW, PURPLE, ORANGE, BLUE, GREEN, RED]

# --- MUSIC GENERATION ---

NOTE_FREQS = {
    'A4': 440.00, 'B4': 493.88, 'C5': 523.25, 'D5': 587.33,
    'E5': 659.25, 'F5': 698.46, 'G5': 783.99, 'A5': 880.00,
    'REST': 0
}

# The classic "Korobeiniki" melody structure: (note, duration in beats)
TETRIS_TUNE = [
    ('E5', 1), ('B4', 0.5), ('C5', 0.5), ('D5', 1), ('C5', 0.5), ('B4', 0.5),
    ('A4', 1), ('A4', 0.5), ('C5', 0.5), ('E5', 1), ('D5', 0.5), ('C5', 0.5),
    ('B4', 1), ('B4', 0.5), ('C5', 0.5), ('D5', 1), ('E5', 1),
    ('C5', 1), ('A4', 1), ('A4', 1), ('REST', 1),

    ('D5', 1.5), ('F5', 0.5), ('A5', 1), ('G5', 0.5), ('F5', 0.5),
    ('E5', 1.5), ('C5', 0.5), ('E5', 1), ('D5', 0.5), ('C5', 0.5),
    ('B4', 1), ('B4', 0.5), ('C5', 0.5), ('D5', 1), ('E5', 1),
    ('C5', 1), ('A4', 1), ('A4', 1), ('REST', 1),
]

def create_tetris_tune(bpm=140):
    """Generates a pygame.mixer.Sound object for the Tetris theme."""
    sample_rate = pygame.mixer.get_init()[0]
    seconds_per_beat = 60 / bpm
    
    # Generate audio samples for each note
    all_note_samples = []
    for note, duration_beats in TETRIS_TUNE:
        duration_sec = duration_beats * seconds_per_beat
        num_samples = int(duration_sec * sample_rate)
        frequency = NOTE_FREQS[note]
        
        t = np.linspace(0, duration_sec, num_samples, endpoint=False)
        
        # Using a simple sine wave for a chiptune feel
        waveform = np.sin(2 * np.pi * frequency * t)
        
        # Apply a simple fade-out envelope to reduce clicking between notes
        envelope = np.linspace(1, 0, num_samples)
        waveform *= envelope
        
        all_note_samples.append(waveform)

    # Concatenate all note waveforms into one
    song_waveform = np.concatenate(all_note_samples)

    # Normalize to 16-bit signed integer range
    amplitude = 2**14 # Use a slightly lower amplitude to avoid clipping
    audio_data = (song_waveform * amplitude).astype(np.int16)

    # Create a stereo sound by duplicating the mono channel
    stereo_audio_data = np.stack([audio_data, audio_data], axis=1)

    return pygame.sndarray.make_sound(stereo_audio_data)


# --- GAME LOGIC ---

class Piece:
    def __init__(self, x, y, shape_index):
        self.x = x
        self.y = y
        self.shape_index = shape_index
        self.shape = SHAPES[shape_index]
        self.color = COLORS[shape_index]
        self.rotation = 0

    def rotate(self):
        # Transpose and reverse rows for clockwise rotation
        self.shape = [list(row) for row in zip(*self.shape[::-1])]

def create_grid(locked_positions={}):
    grid = [[BLACK for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if (x, y) in locked_positions:
                grid[y][x] = locked_positions[(x, y)]
    return grid

def get_shape(bag):
    if not bag:
        bag.extend(list(range(len(SHAPES))))
        random.shuffle(bag)
    return Piece(GRID_WIDTH // 2 - 1, 0, bag.pop())

def is_valid_space(piece, grid):
    # Get all non-empty cells of the piece's shape
    formatted_shape = []
    for i, row in enumerate(piece.shape):
        for j, col in enumerate(row):
            if col == 1:
                formatted_shape.append((piece.x + j, piece.y + i))

    for pos in formatted_shape:
        x, y = pos
        if not (0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT):
            return False  # Out of bounds
        if y >= 0 and grid[y][x] != BLACK: # y can be negative when piece spawns
            return False  # Colliding with another piece
    return True


def check_lost(positions):
    for pos in positions:
        _, y = pos
        if y < 1:
            return True
    return False

def clear_rows(grid, locked):
    inc = 0
    full_rows = []
    for i in range(len(grid)-1,-1,-1):
        row = grid[i]
        if BLACK not in row:
            inc += 1
            full_rows.append(i)
            for j in range(len(row)):
                try:
                    del locked[(j, i)]
                except:
                    continue
    
    if inc > 0:
        for key in sorted(list(locked), key=lambda x: x[1])[::-1]:
            x, y = key
            if y < min(full_rows): # Only shift down rows that are above the highest cleared row
                new_key = (x, y + inc)
                locked[new_key] = locked.pop(key)
    
    return inc, locked

def draw_grid(surface):
    for y in range(GRID_HEIGHT):
        pygame.draw.line(surface, GRAY, (TOP_LEFT_X, TOP_LEFT_Y + y * GRID_SIZE), (TOP_LEFT_X + PLAY_WIDTH, TOP_LEFT_Y + y * GRID_SIZE))
    for x in range(GRID_WIDTH + 1):
        pygame.draw.line(surface, GRAY, (TOP_LEFT_X + x * GRID_SIZE, TOP_LEFT_Y), (TOP_LEFT_X + x * GRID_SIZE, TOP_LEFT_Y + PLAY_HEIGHT))

def draw_text_middle(surface, text, size, color):
    font = pygame.font.SysFont('Arial', size, bold=True)
    label = font.render(text, 1, color)
    surface.blit(label, (SCREEN_WIDTH // 2 - label.get_width() // 2, SCREEN_HEIGHT // 2 - label.get_height() // 2))

def draw_ui_text(surface, text, x, y, size, color):
    font = pygame.font.SysFont('Arial', size)
    label = font.render(text, 1, color)
    surface.blit(label, (x, y))

def draw_next_shape(piece, surface):
    x_pos = TOP_LEFT_X + PLAY_WIDTH + 50
    y_pos = TOP_LEFT_Y + PLAY_HEIGHT/2 - 100
    draw_ui_text(surface, 'Next', x_pos + 40, y_pos - 40, 30, WHITE)
    
    shape = piece.shape
    sx = x_pos + (HOLD_BOX_SIZE - len(shape[0]) * GRID_SIZE) / 2
    sy = y_pos + (HOLD_BOX_SIZE - len(shape) * GRID_SIZE) / 2

    for i, row in enumerate(shape):
        for j, col in enumerate(row):
            if col == 1:
                pygame.draw.rect(surface, piece.color, (sx + j*GRID_SIZE, sy + i*GRID_SIZE, GRID_SIZE, GRID_SIZE), 0)

def draw_hold_shape(piece, surface):
    x_pos = TOP_LEFT_X - SIDEBAR_WIDTH + 85
    y_pos = TOP_LEFT_Y + 50
    draw_ui_text(surface, 'Hold', x_pos + 40, y_pos - 40, 30, WHITE)

    if piece:
        shape = piece.shape
        sx = x_pos + (HOLD_BOX_SIZE - len(shape[0]) * GRID_SIZE) / 2
        sy = y_pos + (HOLD_BOX_SIZE - len(shape) * GRID_SIZE) / 2
        for i, row in enumerate(shape):
            for j, col in enumerate(row):
                if col == 1:
                    pygame.draw.rect(surface, piece.color, (sx + j*GRID_SIZE, sy + i*GRID_SIZE, GRID_SIZE, GRID_SIZE), 0)

def draw_window(surface, grid, score=0, level=0, lines=0, next_piece=None, held_piece=None):
    surface.fill(DARK_GRAY)
    
    # Title
    font = pygame.font.SysFont('Arial', 50, bold=True)
    label = font.render('TETRIS', 1, WHITE)
    surface.blit(label, (TOP_LEFT_X + PLAY_WIDTH / 2 - label.get_width() / 2, 15))

    # Draw Play Area
    for y in range(len(grid)):
        for x in range(len(grid[y])):
            pygame.draw.rect(surface, grid[y][x], (TOP_LEFT_X + x*GRID_SIZE, TOP_LEFT_Y + y*GRID_SIZE, GRID_SIZE, GRID_SIZE), 0)
    
    # Draw Grid and Border
    draw_grid(surface)
    pygame.draw.rect(surface, LIGHT_GRAY, (TOP_LEFT_X, TOP_LEFT_Y, PLAY_WIDTH, PLAY_HEIGHT), 5)

    # UI
    draw_ui_text(surface, f'Score: {score}', TOP_LEFT_X + PLAY_WIDTH + 50, TOP_LEFT_Y + 50, 30, WHITE)
    draw_ui_text(surface, f'Level: {level}', TOP_LEFT_X + PLAY_WIDTH + 50, TOP_LEFT_Y + 80, 30, WHITE)
    draw_ui_text(surface, f'Lines: {lines}', TOP_LEFT_X + PLAY_WIDTH + 50, TOP_LEFT_Y + 110, 30, WHITE)
    
    if next_piece:
        draw_next_shape(next_piece, surface)
    
    draw_hold_shape(held_piece, surface)

    pygame.display.update()

def main(win):
    locked_positions = {}
    
    change_piece = False
    run = True
    
    piece_bag = []
    current_piece = get_shape(piece_bag)
    next_piece = get_shape(piece_bag)
    held_piece = None
    can_hold = True

    clock = pygame.time.Clock()
    fall_time = 0
    level_time = 0
    fall_speed = 0.27 # Seconds per grid cell

    score = 0
    level = 0
    lines_cleared = 0

    # Create and play the music!
    tetris_music = create_tetris_tune()
    tetris_music.play(loops=-1) # -1 loops the music indefinitely

    while run:
        grid = create_grid(locked_positions)
        fall_time += clock.get_rawtime()
        level_time += clock.get_rawtime()
        clock.tick()
        
        # Level Up
        if level_time/1000 > 30: # Level up every 30 seconds
            level_time = 0
            if fall_speed > 0.12:
                fall_speed -= 0.015 # Speed up more gradually
                level += 1

        # Gravity
        if fall_time/1000 >= fall_speed:
            fall_time = 0
            current_piece.y += 1
            if not is_valid_space(current_piece, grid):
                current_piece.y -= 1
                change_piece = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.mixer.stop() # Stop music on quit
                pygame.display.quit()
                quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    current_piece.x -= 1
                    if not is_valid_space(current_piece, grid):
                        current_piece.x += 1
                elif event.key == pygame.K_RIGHT:
                    current_piece.x += 1
                    if not is_valid_space(current_piece, grid):
                        current_piece.x -= 1
                elif event.key == pygame.K_DOWN:
                    # Soft drop
                    current_piece.y += 1
                    score += 1 # Small score bonus for soft drop
                    if not is_valid_space(current_piece, grid):
                        current_piece.y -= 1
                elif event.key == pygame.K_UP:
                    # Rotate
                    current_piece.rotate()
                    if not is_valid_space(current_piece, grid):
                        # Simple wall kick (move right then left)
                        current_piece.x += 1
                        if not is_valid_space(current_piece, grid):
                            current_piece.x -= 2
                            if not is_valid_space(current_piece, grid):
                                current_piece.x += 1
                                # If all kicks fail, revert rotation
                                current_piece.rotate()
                                current_piece.rotate()
                                current_piece.rotate()
                elif event.key == pygame.K_SPACE:
                    # Hard drop
                    while is_valid_space(current_piece, grid):
                        current_piece.y += 1
                    current_piece.y -= 1
                    score += 2 # Small score bonus for hard drop
                    change_piece = True
                elif event.key == pygame.K_c:
                    if can_hold:
                        can_hold = False
                        if held_piece is None:
                            # Create a fresh piece for the hold box
                            held_piece = Piece(GRID_WIDTH // 2 - 1, 0, current_piece.shape_index)
                            current_piece = next_piece
                            next_piece = get_shape(piece_bag)
                        else:
                            # Swap current and held pieces
                            # Create fresh pieces to avoid aliasing issues
                            new_held_piece = Piece(GRID_WIDTH // 2 - 1, 0, current_piece.shape_index)
                            current_piece = Piece(GRID_WIDTH // 2 - 1, 0, held_piece.shape_index)
                            held_piece = new_held_piece


        # Ghost Piece
        ghost_piece = Piece(current_piece.x, current_piece.y, current_piece.shape_index)
        ghost_piece.shape = current_piece.shape
        while is_valid_space(ghost_piece, grid):
            ghost_piece.y += 1
        ghost_piece.y -= 1

        # Draw current piece and ghost piece on the grid copy
        temp_grid = [row[:] for row in grid]
        # Draw ghost piece first so current piece draws over it
        if is_valid_space(ghost_piece, grid):
            for i, row in enumerate(ghost_piece.shape):
                for j, col in enumerate(row):
                    if col == 1:
                         temp_grid[ghost_piece.y + i][ghost_piece.x + j] = GRAY
        # Draw current piece
        for i, row in enumerate(current_piece.shape):
            for j, col in enumerate(row):
                if col == 1:
                    temp_grid[current_piece.y + i][current_piece.x + j] = current_piece.color


        if change_piece:
            piece_pos = []
            for i, row in enumerate(current_piece.shape):
                for j, col in enumerate(row):
                    if col == 1:
                        piece_pos.append((current_piece.x + j, current_piece.y + i))

            for pos in piece_pos:
                p_x, p_y = pos
                if p_y > -1:
                    locked_positions[(p_x, p_y)] = current_piece.color
            
            cleared_count, locked_positions = clear_rows(create_grid(locked_positions), locked_positions)
            lines_cleared += cleared_count
            
            # Scoring based on Tetris guidelines
            score_map = {1: 40, 2: 100, 3: 300, 4: 1200}
            if cleared_count > 0:
                score += score_map[cleared_count] * (level + 1)
            
            current_piece = next_piece
            next_piece = get_shape(piece_bag)
            change_piece = False
            can_hold = True
            
            if check_lost(locked_positions):
                pygame.mixer.stop() # Stop music on loss
                draw_window(win, create_grid(locked_positions), score, level, lines_cleared, next_piece, held_piece)
                draw_text_middle(win, "YOU LOST", 80, RED)
                pygame.display.update()
                pygame.time.delay(3000)
                run = False

        draw_window(win, temp_grid, score, level, lines_cleared, next_piece, held_piece)

    pygame.display.quit()

if __name__ == '__main__':
    win = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('Tetris')
    main(win)

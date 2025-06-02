# test.py
import pygame
import sys
import random
import numpy as np # Added for sound generation

# --- Constants ---
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400
GRID_SIZE = 20  # Size of each snake segment and food block
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE
FPS = 60 # Target rendering frames per second
SNAKE_MOVE_RATE = 10 # How many times the snake moves per second (Atari speed!)

# Colors (R, G, B)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 200, 0)       # Snake body color
DARK_GREEN = (0, 150, 0)  # Snake head color / border
RED = (220, 0, 0)         # Food color
GRAY_BG = (30, 30, 30)    # A slightly lighter black for background
TEXT_COLOR = (200, 200, 200)
GAMEOVER_RED = (255, 50, 50)

# Snake directions (dx, dy)
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# --- Sound Generation Constants ---
SAMPLE_RATE = 44100 # Standard sample rate
SOUND_AMPLITUDE = 7000 # Amplitude for generated sounds (max 32767 for int16)

# --- Game Functions ---

def draw_snake(surface, snake_body):
    """Draws the snake on the screen."""
    for i, segment_pos in enumerate(snake_body):
        rect = pygame.Rect(segment_pos[0] * GRID_SIZE, segment_pos[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
        if i == 0:  # Head
            pygame.draw.rect(surface, DARK_GREEN, rect)
            inner_rect = rect.inflate(-GRID_SIZE // 4, -GRID_SIZE // 4)
            pygame.draw.rect(surface, GREEN, inner_rect)
        else:  # Body segments
            pygame.draw.rect(surface, GREEN, rect)

def draw_food(surface, food_pos):
    """Draws the food on the screen."""
    rect = pygame.Rect(food_pos[0] * GRID_SIZE, food_pos[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
    pygame.draw.rect(surface, RED, rect)

def spawn_food(snake_body):
    """Generates a new food position that is not on the snake."""
    while True:
        food_pos = [random.randrange(0, GRID_WIDTH), random.randrange(0, GRID_HEIGHT)]
        if food_pos not in snake_body:
            return food_pos

def display_score(surface, score, font):
    """Displays the current score."""
    score_text_surface = font.render(f"Score: {score}", True, TEXT_COLOR)
    surface.blit(score_text_surface, (10, 10))

def game_over_screen(surface, score, font_large, font_small):
    """Displays the game over message and instructions."""
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA) # pylint: disable=too-many-function-args
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))

    game_over_text = font_large.render("GAME OVER", True, GAMEOVER_RED)
    final_score_text = font_small.render(f"Final Score: {score}", True, TEXT_COLOR)
    restart_text = font_small.render("Press 'R' to Restart or 'Q' to Quit", True, TEXT_COLOR)

    text_y_offset = 30

    game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - game_over_text.get_height() / 2 - text_y_offset))
    final_score_rect = final_score_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
    restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + final_score_text.get_height() / 2 + text_y_offset))

    surface.blit(game_over_text, game_over_rect)
    surface.blit(final_score_text, final_score_rect)
    surface.blit(restart_text, restart_rect)

# --- Sound Generation Functions ---
def _create_sound_array(waveform_function, duration, **kwargs):
    """Helper to create a sound array with an envelope."""
    num_samples = int(SAMPLE_RATE * duration)
    time_array = np.linspace(0, duration, num_samples, False)
    
    wave = waveform_function(time_array, **kwargs)
    
    # Apply a simple exponential decay envelope to prevent clicks
    envelope = np.exp(-np.linspace(0, 5, num_samples)) # Decay from 1 to e^-5 (factor of ~150)
    normalized_wave = wave * envelope
            
    sound_array = (SOUND_AMPLITUDE * normalized_wave).astype(np.int16)
    return sound_array

def make_food_eat_sfx():
    """Generates a short 'blip' sound for eating food."""
    def food_wave_fn(t, freq=1300): # Higher pitch for "blip"
        return np.sin(2 * np.pi * freq * t) # Simple sine wave

    duration = 0.06 # seconds
    arr = _create_sound_array(food_wave_fn, duration, freq=1300)
    return pygame.mixer.Sound(buffer=arr)

def make_game_over_sfx():
    """Generates a 'noise burst' sound for game over."""
    def noise_fn(t): # t is not strictly used for simple noise, but matches signature
        return np.random.uniform(-1, 1, len(t)) # White noise

    duration = 0.4 # seconds
    arr = _create_sound_array(noise_fn, duration)
    return pygame.mixer.Sound(buffer=arr)

# --- Main Game Setup ---
def game_loop():
    pygame.init()
    pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512) # Initialize mixer for mono sound

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Snake Game - Atari Speed!")
    clock = pygame.time.Clock()

    # Fonts
    try:
        font_path_consolas = pygame.font.match_font('consolas', 'arial')
        font_path_impact = pygame.font.match_font('impact', 'arialbd')
        score_font = pygame.font.Font(font_path_consolas, 25)
        game_over_font_large = pygame.font.Font(font_path_impact, 70)
        game_over_font_small = pygame.font.Font(font_path_consolas, 30)
    except Exception:
        score_font = pygame.font.Font(None, 35)
        game_over_font_large = pygame.font.Font(None, 80)
        game_over_font_small = pygame.font.Font(None, 40)

    # --- Sound Effects ---
    food_sfx = make_food_eat_sfx()
    game_over_sfx = make_game_over_sfx()

    game_state = {}

    def initialize_game_state(state_dict):
        start_x = GRID_WIDTH // 4
        start_y = GRID_HEIGHT // 2
        
        state_dict['snake_head_pos'] = [start_x, start_y]
        state_dict['snake_body'] = [
            [state_dict['snake_head_pos'][0], state_dict['snake_head_pos'][1]],
            [state_dict['snake_head_pos'][0] - 1, state_dict['snake_head_pos'][1]],
            [state_dict['snake_head_pos'][0] - 2, state_dict['snake_head_pos'][1]]
        ]
        state_dict['current_direction'] = RIGHT
        state_dict['next_direction'] = RIGHT

        state_dict['food_pos'] = spawn_food(state_dict['snake_body'])
        state_dict['food_spawned'] = True

        state_dict['score'] = 0
        state_dict['game_over_flag'] = False

    initialize_game_state(game_state)

    move_accumulator = 0.0
    milliseconds_per_move = 1000.0 / SNAKE_MOVE_RATE

    running = True
    while running:
        dt_milliseconds = clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if game_state['game_over_flag']:
                    if event.key == pygame.K_r:
                        initialize_game_state(game_state)
                        move_accumulator = 0.0
                    if event.key == pygame.K_q:
                        running = False
                else:
                    if (event.key == pygame.K_UP or event.key == pygame.K_w):
                        if game_state['current_direction'] != DOWN:
                            game_state['next_direction'] = UP
                    elif (event.key == pygame.K_DOWN or event.key == pygame.K_s):
                        if game_state['current_direction'] != UP:
                            game_state['next_direction'] = DOWN
                    elif (event.key == pygame.K_LEFT or event.key == pygame.K_a):
                        if game_state['current_direction'] != RIGHT:
                            game_state['next_direction'] = LEFT
                    elif (event.key == pygame.K_RIGHT or event.key == pygame.K_d):
                        if game_state['current_direction'] != LEFT:
                            game_state['next_direction'] = RIGHT
        
        if not game_state['game_over_flag']:
            move_accumulator += dt_milliseconds

            if move_accumulator >= milliseconds_per_move:
                move_accumulator -= milliseconds_per_move

                game_state['current_direction'] = game_state['next_direction']

                game_state['snake_head_pos'][0] += game_state['current_direction'][0]
                game_state['snake_head_pos'][1] += game_state['current_direction'][1]

                game_state['snake_body'].insert(0, list(game_state['snake_head_pos']))

                if game_state['snake_head_pos'] == game_state['food_pos']:
                    game_state['score'] += 1
                    game_state['food_spawned'] = False
                    food_sfx.play() # Play sound on food eat
                else:
                    game_state['snake_body'].pop()

                if not game_state['food_spawned']:
                    game_state['food_pos'] = spawn_food(game_state['snake_body'])
                    game_state['food_spawned'] = True

                # --- Game Over Conditions ---
                previously_game_over = game_state['game_over_flag'] # Store state before checks

                head_x, head_y = game_state['snake_head_pos']
                if not (0 <= head_x < GRID_WIDTH and 0 <= head_y < GRID_HEIGHT):
                    game_state['game_over_flag'] = True

                if not game_state['game_over_flag'] and game_state['snake_head_pos'] in game_state['snake_body'][1:]:
                    game_state['game_over_flag'] = True
                
                if game_state['game_over_flag'] and not previously_game_over:
                    game_over_sfx.play() # Play sound when game over state is first triggered

        screen.fill(GRAY_BG)
        draw_snake(screen, game_state['snake_body'])
        draw_food(screen, game_state['food_pos'])
        display_score(screen, game_state['score'], score_font)

        if game_state['game_over_flag']:
            game_over_screen(screen, game_state['score'], game_over_font_large, game_over_font_small)

        pygame.display.flip()

    pygame.mixer.quit() # Quit mixer before pygame quits
    pygame.quit()
    sys.exit()

# --- Run the game ---
if __name__ == "__main__":
    game_loop()
    #### [C Team Flames [20XX]]

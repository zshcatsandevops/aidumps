import pygame
import sys
import random
import numpy as np

# --- Sound Generation ---
def generate_square_wave(frequency=440, duration=0.1, volume=0.1, sample_rate=44100):
    """
    Generates a pygame.mixer.Sound object with a square wave.
    """
    n_samples = int(duration * sample_rate)
    waveform = np.zeros(n_samples, dtype=np.int16)
    amplitude = (2**15 - 1) * volume

    period_samples = sample_rate / frequency
    half_period_samples = period_samples / 2

    for i in range(n_samples):
        if (i // half_period_samples) % 2 == 0:
            waveform[i] = int(amplitude)
        else:
            waveform[i] = -int(amplitude)

    # Create a 2-channel (stereo) array to match the mixer settings.
    sound_array = np.column_stack([waveform, waveform])
    sound = pygame.sndarray.make_sound(sound_array)
    return sound

# --- Game Setup and Initialization ---
def initialize_game():
    """Initializes Pygame and sets up the game window and clock."""
    pygame.mixer.pre_init(44100, -16, 2, 512) # Initialize mixer for stereo sound
    pygame.init()
    global screen, clock
    screen_width = 1280
    screen_height = 800
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption('ULTRA! PONG HDR 1.0') # Updated Caption
    clock = pygame.time.Clock()

# --- Game Variables & Constants ---
def setup_variables():
    """Sets up all the game objects, colors, fonts, and state variables."""
    global screen_width, screen_height, bg_color, light_grey, white
    global ball, player, opponent
    global ball_speed_x, ball_speed_y, opponent_speed
    global player_score, opponent_score
    global score_font, game_over_font, menu_title_font, menu_copyright_font, menu_prompt_font
    global game_state # Replaces game_over_flag for state management
    global paddle_hit_sound, wall_hit_sound, score_sound

    screen_width = 1280
    screen_height = 800

    # Colors
    bg_color = pygame.Color('grey12')
    light_grey = (200, 200, 200)
    white = (255, 255, 255)

    # Game Rectangles (x, y, width, height)
    paddle_w, paddle_h, ball_size = 10, 140, 30
    ball = pygame.Rect(screen_width / 2 - ball_size / 2, screen_height / 2 - ball_size / 2, ball_size, ball_size)
    player = pygame.Rect(10, screen_height / 2 - paddle_h / 2, paddle_w, paddle_h)
    opponent = pygame.Rect(screen_width - 20, screen_height / 2 - paddle_h / 2, paddle_w, paddle_h)

    # Game Speeds
    ball_speed_x = 7 * random.choice((1, -1))
    ball_speed_y = 7 * random.choice((1, -1))
    opponent_speed = 7

    # Score and State
    player_score = 0
    opponent_score = 0
    game_state = 'main_menu' # Initial state is the main menu

    # Text / Fonts
    menu_title_font = pygame.font.Font(None, 90)
    menu_copyright_font = pygame.font.Font(None, 30)
    menu_prompt_font = pygame.font.Font(None, 50)
    score_font = pygame.font.Font(None, 60)
    game_over_font = pygame.font.Font(None, 80)

    # Sounds
    paddle_hit_sound = generate_square_wave(frequency=440, duration=0.05, volume=0.2)
    wall_hit_sound = generate_square_wave(frequency=220, duration=0.05, volume=0.15)
    score_sound = generate_square_wave(frequency=880, duration=0.15, volume=0.25)

def ball_restart():
    """Resets the ball to the center and gives it a random velocity."""
    global ball_speed_x, ball_speed_y
    ball.center = (screen_width / 2, screen_height / 2)
    pygame.time.delay(500) # Brief pause before the ball moves
    ball_speed_y = 7 * random.choice((1, -1))
    ball_speed_x = 7 * random.choice((1, -1))

def game_reset():
    """Resets the scores and object positions for a new match."""
    global player_score, opponent_score
    player_score = 0
    opponent_score = 0
    # Reset paddle positions
    player.centery = screen_height / 2
    opponent.centery = screen_height / 2
    ball_restart()

# --- Drawing Functions ---
def draw_main_menu():
    """Draws the main menu screen."""
    title_text = menu_title_font.render("ULTRA! PONG HDR 1.0", True, white)
    title_rect = title_text.get_rect(center=(screen_width / 2, screen_height / 2 - 150))
    screen.blit(title_text, title_rect)
    
    copyright_text = menu_copyright_font.render("[C] Atari 199X - [C] Team Flames 20XX", True, light_grey)
    copyright_rect = copyright_text.get_rect(center=(screen_width / 2, screen_height / 2 - 80))
    screen.blit(copyright_text, copyright_rect)
    
    prompt_text = menu_prompt_font.render("Press ENTER to Start", True, white)
    prompt_rect = prompt_text.get_rect(center=(screen_width / 2, screen_height / 2 + 50))
    screen.blit(prompt_text, prompt_rect)

def draw_game_screen():
    """Draws the main game elements (paddles, ball, score, etc.)."""
    pygame.draw.rect(screen, white, player)
    pygame.draw.rect(screen, white, opponent)
    pygame.draw.ellipse(screen, white, ball)
    pygame.draw.aaline(screen, light_grey, (screen_width / 2, 0), (screen_width / 2, screen_height))

    player_text = score_font.render(f"{player_score}", True, white)
    screen.blit(player_text, (screen_width / 2 - 60, screen_height / 2 - 25))

    opponent_text = score_font.render(f"{opponent_score}", True, white)
    screen.blit(opponent_text, (screen_width / 2 + 35, screen_height / 2 - 25))

def draw_game_over_screen():
    """Draws the game over text overlay."""
    if player_score >= 5:
        end_text_str = "YOU WIN!"
    else:
        end_text_str = "YOU LOSE"
    
    end_text = game_over_font.render(end_text_str, True, white)
    end_rect = end_text.get_rect(center=(screen_width / 2, screen_height / 2 - 100))
    screen.blit(end_text, end_rect)
    
    prompt_text = score_font.render("Play Again? (Y/N)", True, white)
    prompt_rect = prompt_text.get_rect(center=(screen_width / 2, screen_height / 2 + 20))
    screen.blit(prompt_text, prompt_rect)
    
    menu_return_text = menu_prompt_font.render("Press ESC for Main Menu", True, light_grey)
    menu_return_rect = menu_return_text.get_rect(center=(screen_width / 2, screen_height / 2 + 100))
    screen.blit(menu_return_text, menu_return_rect)

# --- Main Game Loop ---
def run_game():
    """Contains the main loop, managing different game states."""
    global ball_speed_x, ball_speed_y, player_score, opponent_score, game_state

    while True:
        # 1. Event Handling (is different for each game state)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Keyboard events
            if event.type == pygame.KEYDOWN:
                if game_state == 'main_menu':
                    if event.key == pygame.K_RETURN:
                        game_state = 'playing'
                        game_reset() # Reset scores and positions for new game
                
                elif game_state == 'game_over':
                    if event.key == pygame.K_y:
                        game_state = 'playing'
                        game_reset()
                    if event.key == pygame.K_n:
                        pygame.quit()
                        sys.exit()
                    if event.key == pygame.K_ESCAPE:
                        game_state = 'main_menu'

            # Mouse events (only active during gameplay)
            if event.type == pygame.MOUSEMOTION and game_state == 'playing':
                player.centery = event.pos[1]

        # 2. Game Logic (runs only when 'playing')
        if game_state == 'playing':
            ball.x += ball_speed_x
            ball.y += ball_speed_y

            # Player paddle boundary checks
            if player.top < 0: player.top = 0
            if player.bottom > screen_height: player.bottom = screen_height

            # Opponent AI
            if opponent.top < ball.y: opponent.y += opponent_speed
            if opponent.bottom > ball.y: opponent.y -= opponent_speed
            if opponent.top < 0: opponent.top = 0
            if opponent.bottom > screen_height: opponent.bottom = screen_height

            # Ball Collisions
            if ball.top <= 0 or ball.bottom >= screen_height:
                wall_hit_sound.play()
                ball_speed_y *= -1

            if ball.colliderect(player) and ball_speed_x < 0:
                paddle_hit_sound.play()
                ball_speed_x *= -1
                ball.left = player.right # Prevent sticking

            if ball.colliderect(opponent) and ball_speed_x > 0:
                paddle_hit_sound.play()
                ball_speed_x *= -1
                ball.right = opponent.left # Prevent sticking

            # Scoring
            if ball.left <= 0:
                score_sound.play()
                opponent_score += 1
                ball_restart()

            if ball.right >= screen_width:
                score_sound.play()
                player_score += 1
                ball_restart()

            # Check for Game Over condition
            if player_score >= 5 or opponent_score >= 5:
                game_state = 'game_over'

        # 3. Drawing (is different for each game state)
        screen.fill(bg_color)
        
        if game_state == 'main_menu':
            draw_main_menu()
        elif game_state == 'playing':
            draw_game_screen()
        elif game_state == 'game_over':
            # Draw the final game screen behind the game over text for context
            draw_game_screen() 
            draw_game_over_screen()

        # 4. Update the screen
        pygame.display.flip()
        clock.tick(60)

# --- Script Execution ---
if __name__ == '__main__':
    initialize_game()
    setup_variables()
    run_game()

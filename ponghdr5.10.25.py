import pygame
import random
import numpy as np

# Initialize Pygame
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# Screen dimensions
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Pong")

# Colors
black = (0, 0, 0)
white = (255, 255, 255)
gray = (150, 150, 150)

# Game states
MENU = 0
PLAYING = 1
GAME_OVER = 2
game_state = MENU
current_winner = None
max_score = 5

# Sound engine
def create_sine_wave(frequency, duration, volume=0.5):
    sample_rate = 44100
    t = np.linspace(0, duration, int(duration * sample_rate), False)
    wave = np.sin(frequency * t * 2 * np.pi)
    
    # Apply a simple envelope to avoid clicks
    fade_samples = int(sample_rate * 0.05)  # 50ms fade
    if fade_samples * 2 < len(wave):
        fade_in = np.linspace(0, 1, fade_samples)
        fade_out = np.linspace(1, 0, fade_samples)
        wave[:fade_samples] *= fade_in
        wave[-fade_samples:] *= fade_out
    
    # Convert to 16-bit data
    wave = (wave * volume * 32767).astype(np.int16)
    
    # Convert to stereo
    stereo_wave = np.column_stack((wave, wave))
    
    # Create sound from array
    sound = pygame.sndarray.make_sound(stereo_wave)
    return sound

# Generate sound effects
paddle_hit_sound = create_sine_wave(440, 0.1)  # A4 note for paddle hit
wall_hit_sound = create_sine_wave(330, 0.1)    # E4 note for wall hit
score_sound = create_sine_wave(523.25, 0.3)    # C5 note for scoring
menu_select_sound = create_sine_wave(660, 0.2)  # E5 note for menu selection
game_over_sound = create_sine_wave(196, 0.5, 0.7)  # G3 note for game over

# Fonts
font_large = pygame.font.Font(None, 74)
font_medium = pygame.font.Font(None, 48)
font_small = pygame.font.Font(None, 36)

# Game objects
ball_radius = 10
ball_x = screen_width // 2
ball_y = screen_height // 2
ball_speed_x = 5 * random.choice((1, -1))
ball_speed_y = 5 * random.choice((1, -1))

paddle_width = 15
paddle_height = 100
paddle_speed = 7

player1_x = 50
player1_y = screen_height // 2 - paddle_height // 2

player2_x = screen_width - 50 - paddle_width
player2_y = screen_height // 2 - paddle_height // 2

# Scores
player1_score = 0
player2_score = 0

# Game loop
running = True
clock = pygame.time.Clock()

def draw_objects():
    screen.fill(black)
    pygame.draw.rect(screen, white, (player1_x, player1_y, paddle_width, paddle_height))
    pygame.draw.rect(screen, white, (player2_x, player2_y, paddle_width, paddle_height))
    pygame.draw.ellipse(screen, white, (ball_x - ball_radius, ball_y - ball_radius, ball_radius * 2, ball_radius * 2))
    pygame.draw.aaline(screen, white, (screen_width // 2, 0), (screen_width // 2, screen_height))

    player1_text = font_large.render(str(player1_score), True, white)
    screen.blit(player1_text, (screen_width // 4, 10))

    player2_text = font_large.render(str(player2_score), True, white)
    screen.blit(player2_text, (screen_width * 3 // 4 - player2_text.get_width(), 10))

    pygame.display.flip()

def draw_menu():
    screen.fill(black)
    
    # Title
    title_text = font_large.render("PONG", True, white)
    screen.blit(title_text, (screen_width // 2 - title_text.get_width() // 2, 100))
    
    # Instructions
    instruction_text = font_medium.render("Press SPACE to start", True, white)
    screen.blit(instruction_text, (screen_width // 2 - instruction_text.get_width() // 2, 300))
    
    # Controls
    controls1_text = font_small.render("Player 1: W/S", True, gray)
    screen.blit(controls1_text, (screen_width // 2 - controls1_text.get_width() // 2, 400))
    
    controls2_text = font_small.render("Player 2: UP/DOWN", True, gray)
    screen.blit(controls2_text, (screen_width // 2 - controls2_text.get_width() // 2, 440))
    
    pygame.display.flip()

def draw_game_over():
    screen.fill(black)
    
    # Game Over text
    game_over_text = font_large.render("GAME OVER", True, white)
    screen.blit(game_over_text, (screen_width // 2 - game_over_text.get_width() // 2, 100))
    
    # Winner text
    if current_winner == 1:
        winner_text = font_medium.render("Player 1 Wins!", True, white)
    else:
        winner_text = font_medium.render("Player 2 Wins!", True, white)
    screen.blit(winner_text, (screen_width // 2 - winner_text.get_width() // 2, 200))
    
    # Final score
    score_text = font_medium.render(f"{player1_score} - {player2_score}", True, white)
    screen.blit(score_text, (screen_width // 2 - score_text.get_width() // 2, 270))
    
    # Restart prompt
    restart_text = font_medium.render("Play again? (Y/N)", True, white)
    screen.blit(restart_text, (screen_width // 2 - restart_text.get_width() // 2, 350))
    
    pygame.display.flip()

def reset_ball():
    global ball_x, ball_y, ball_speed_x, ball_speed_y
    ball_x = screen_width // 2
    ball_y = screen_height // 2
    ball_speed_x = 5 * random.choice((1, -1))
    ball_speed_y = 5 * random.choice((1, -1))
    score_sound.play()

def reset_game():
    global player1_score, player2_score, player1_y, player2_y, game_state
    player1_score = 0
    player2_score = 0
    player1_y = screen_height // 2 - paddle_height // 2
    player2_y = screen_height // 2 - paddle_height // 2
    reset_ball()
    game_state = PLAYING


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if game_state == MENU and event.key == pygame.K_SPACE:
                menu_select_sound.play()
                game_state = PLAYING
                reset_game()
            elif game_state == GAME_OVER:
                if event.key == pygame.K_y:
                    menu_select_sound.play()
                    reset_game()
                elif event.key == pygame.K_n:
                    menu_select_sound.play()
                    game_state = MENU

    if game_state == MENU:
        draw_menu()
    elif game_state == PLAYING:
        keys = pygame.key.get_pressed()
        # Player 1 controls
        if keys[pygame.K_w] and player1_y > 0:
            player1_y -= paddle_speed
        if keys[pygame.K_s] and player1_y < screen_height - paddle_height:
            player1_y += paddle_speed

        # Player 2 controls (simple AI or second player)
        if keys[pygame.K_UP] and player2_y > 0: # Manual control for player 2
            player2_y -= paddle_speed
        if keys[pygame.K_DOWN] and player2_y < screen_height - paddle_height:
            player2_y += paddle_speed
        # # Simple AI for Player 2 (uncomment to use)
        # if ball_speed_x > 0: # Ball is moving towards player 2
        #     if player2_y + paddle_height / 2 < ball_y - 5:
        #         player2_y += paddle_speed * 0.7 # Slower AI
        #     elif player2_y + paddle_height / 2 > ball_y + 5:
        #         player2_y -= paddle_speed * 0.7 # Slower AI
        # # Keep AI paddle within bounds
        # if player2_y < 0:
        #     player2_y = 0
        # if player2_y > screen_height - paddle_height:
        #     player2_y = screen_height - paddle_height


        # Ball movement
        ball_x += ball_speed_x
        ball_y += ball_speed_y

        # Ball collision with top/bottom walls
        if ball_y + ball_radius > screen_height or ball_y - ball_radius < 0:
            ball_speed_y *= -1
            wall_hit_sound.play()

        # Ball collision with paddles
        # Player 1 paddle
        if ball_x - ball_radius < player1_x + paddle_width and \
           player1_y < ball_y < player1_y + paddle_height and \
           ball_speed_x < 0: # Check if ball is moving towards player 1
            ball_speed_x *= -1
            paddle_hit_sound.play()
            # Optional: Adjust ball_speed_y based on where it hits the paddle
            # delta_y = ball_y - (player1_y + paddle_height / 2)
            # ball_speed_y = delta_y * 0.35

        # Player 2 paddle
        if ball_x + ball_radius > player2_x and \
           player2_y < ball_y < player2_y + paddle_height and \
           ball_speed_x > 0: # Check if ball is moving towards player 2
            ball_speed_x *= -1
            paddle_hit_sound.play()
            # Optional: Adjust ball_speed_y based on where it hits the paddle
            # delta_y = ball_y - (player2_y + paddle_height / 2)
            # ball_speed_y = delta_y * 0.35


        # Ball out of bounds (scoring)
        if ball_x - ball_radius < 0:
            player2_score += 1
            reset_ball()
            if player2_score >= max_score:
                current_winner = 2
                game_state = GAME_OVER
                game_over_sound.play()
        elif ball_x + ball_radius > screen_width:
            player1_score += 1
            reset_ball()
            if player1_score >= max_score:
                current_winner = 1
                game_state = GAME_OVER
                game_over_sound.play()

        # Draw everything
        draw_objects()
    elif game_state == GAME_OVER:
        draw_game_over()

    # Cap the frame rate
    clock.tick(60)

pygame.quit()

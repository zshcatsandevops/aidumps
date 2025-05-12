import pygame
import random
import numpy # For sound generation
import time # For a brief pause on game over

# Initialize Pygame
pygame.init()
# Initialize the mixer with parameters suitable for simple generated sounds
# frequency: samples per second (22050 is common for basic sounds)
# size: -16 means 16-bit signed audio (standard)
# channels: 2 for stereo output (as per user's update)
# buffer: size of the audio buffer, smaller can mean less latency but more CPU
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pong - Enhanced Atari Sounds - 60 FPS")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255) # Not used, but defined

# Game constants
PADDLE_WIDTH = 15
PADDLE_HEIGHT = 100
BALL_SIZE = 15
PADDLE_SPEED = 7
BALL_SPEED_X_INITIAL = 5
BALL_SPEED_Y_INITIAL = 5
WINNING_SCORE = 5

# Game States
PLAYING = 0
GAME_OVER = 1

# Clock for controlling FPS
clock = pygame.time.Clock()
FPS = 60

# Fonts
score_font = pygame.font.Font(None, 74)
game_over_font = pygame.font.Font(None, 100)
restart_font = pygame.font.Font(None, 50)

# --- Enhanced Atari-like Sound Engine (No Media) ---
SAMPLE_RATE = 22050 # Samples per second, should match mixer init

def generate_square_wave_segment(frequency, duration_ms, volume=4000):
    """Generates a single square wave segment as a stereo numpy array."""
    if frequency <= 0: # Avoid division by zero or negative frequencies
        mono_samples = numpy.zeros(int(duration_ms / 1000.0 * SAMPLE_RATE), dtype=numpy.int16)
        # For stereo, duplicate the mono channel
        return numpy.column_stack((mono_samples, mono_samples))
        
    num_samples = int(duration_ms / 1000.0 * SAMPLE_RATE)
    period_samples = SAMPLE_RATE / frequency
    mono_samples = numpy.zeros(num_samples, dtype=numpy.int16)
    amplitude = volume
    for i in range(num_samples):
        if (i // (period_samples / 2)) % 2 == 0:
            mono_samples[i] = amplitude
        else:
            mono_samples[i] = -amplitude
    # Convert mono to stereo by duplicating the channel
    stereo_samples = numpy.column_stack((mono_samples, mono_samples))
    return stereo_samples

def generate_pause_segment(duration_ms):
    """Generates a stereo silence segment as a numpy array."""
    num_samples = int(duration_ms / 1000.0 * SAMPLE_RATE)
    mono_samples = numpy.zeros(num_samples, dtype=numpy.int16)
    # Convert mono to stereo
    stereo_samples = numpy.column_stack((mono_samples, mono_samples))
    return stereo_samples

def generate_beep_sequence(sequence, volume=4000):
    """
    Generates a stereo sound from a sequence of beeps.
    Sequence is a list of tuples: (frequency, duration_ms, pause_after_ms)
    A frequency of 0 or less will be treated as a pause for that beep's duration.
    """
    all_samples_list = [] # Use a list to collect 2D arrays
    for freq, duration, pause_after in sequence:
        if freq > 0:
            beep_samples = generate_square_wave_segment(freq, duration, volume)
        else: # Treat freq 0 or less as a pause for the beep duration itself
            beep_samples = generate_pause_segment(duration)
        all_samples_list.append(beep_samples)
        
        if pause_after > 0:
            pause_samples = generate_pause_segment(pause_after)
            all_samples_list.append(pause_samples)
    
    # Vertically stack the stereo segments
    # Each segment in all_samples_list is (num_segment_samples, 2)
    # vstack will result in (total_samples, 2)
    if not all_samples_list: # Handle empty sequence
        return pygame.sndarray.make_sound(numpy.array([], dtype=numpy.int16))

    final_wave = numpy.vstack(all_samples_list)
    # Ensure the final array is of dtype int16, as required by pygame.mixer settings
    return pygame.sndarray.make_sound(final_wave.astype(numpy.int16))


# Sound effects using the new sequence generator
try:
    # Paddle Hit: Two quick, slightly rising beeps
    sound_paddle_hit = generate_beep_sequence([
        (400, 40, 10),  # freq, duration, pause_after
        (450, 40, 0)
    ])
    # Wall Hit: A single, slightly lower, short beep
    sound_wall_hit = generate_beep_sequence([
        (250, 60, 0)
    ])
    # Score: A three-beep ascending fanfare
    sound_score = generate_beep_sequence([
        (500, 70, 40),
        (700, 70, 40),
        (900, 90, 0)
    ])
    # Game Over Win: A longer, more "final" sound, could be a simple chord or sequence
    sound_game_over_win = generate_beep_sequence([
        (600, 150, 50),
        (800, 250, 0)
    ])
    # Game Over Lose (not explicitly used as "lose" but as a general game over sound if needed)
    # For simplicity, we'll use the same sound_game_over_win when a player wins.
    # If you want a distinct "lose" sound from the other player's perspective, you could define it.
    # sound_game_over_lose = generate_beep_sequence([(300, 500, 0)])

except Exception as e:
    print(f"Warning: Could not initialize sounds. {e}")
    # Create dummy sound objects if generation fails, so game doesn't crash
    class DummySound:
        def play(self): pass
    sound_paddle_hit = DummySound()
    sound_wall_hit = DummySound()
    sound_score = DummySound()
    sound_game_over_win = DummySound()
    # sound_game_over_lose = DummySound()


def play_sound(sound):
    """Plays a sound if it's available."""
    try:
        sound.play()
    except AttributeError: # Catches if sound is a DummySound
        pass
    except Exception as e:
        # print(f"Error playing sound: {e}") # Optional: for debugging sound issues
        pass


def draw_text(text, font, color, surface, x, y, center=False):
    """Renders text onto a surface."""
    textobj = font.render(text, 1, color)
    textrect = textobj.get_rect()
    if center:
        textrect.center = (x, y)
    else:
        textrect.topleft = (x, y)
    surface.blit(textobj, textrect)

def reset_ball_values():
    """Resets ball speed and randomizes its direction."""
    new_ball_speed_x = BALL_SPEED_X_INITIAL * random.choice((1, -1))
    new_ball_speed_y = BALL_SPEED_Y_INITIAL * random.choice((1, -1))
    return new_ball_speed_x, new_ball_speed_y

def reset_game_elements(ball_rect, paddle_a_rect, paddle_b_rect):
    """Resets ball and paddle positions and ball speed."""
    ball_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    paddle_a_rect.centery = SCREEN_HEIGHT // 2
    paddle_b_rect.centery = SCREEN_HEIGHT // 2
    return reset_ball_values()


def main():
    """Main game loop."""
    running = True
    game_state = PLAYING
    winner = None

    # Create game objects (paddles and ball)
    paddle_a = pygame.Rect(50, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
    paddle_b = pygame.Rect(SCREEN_WIDTH - 50 - PADDLE_WIDTH, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
    ball = pygame.Rect(SCREEN_WIDTH // 2 - BALL_SIZE // 2, SCREEN_HEIGHT // 2 - BALL_SIZE // 2, BALL_SIZE, BALL_SIZE)

    ball_speed_x, ball_speed_y = reset_game_elements(ball, paddle_a, paddle_b)

    score_a = 0
    score_b = 0

    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if game_state == GAME_OVER:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_y: # Yes to play again
                        score_a = 0
                        score_b = 0
                        ball_speed_x, ball_speed_y = reset_game_elements(ball, paddle_a, paddle_b)
                        game_state = PLAYING
                        winner = None
                    elif event.key == pygame.K_n: # No to play again
                        running = False

        if game_state == PLAYING:
            # Player input
            keys = pygame.key.get_pressed()
            # Paddle A movement (W and S keys)
            if keys[pygame.K_w] and paddle_a.top > 0:
                paddle_a.y -= PADDLE_SPEED
            if keys[pygame.K_s] and paddle_a.bottom < SCREEN_HEIGHT:
                paddle_a.y += PADDLE_SPEED
            # Paddle B movement (Up and Down arrow keys)
            if keys[pygame.K_UP] and paddle_b.top > 0:
                paddle_b.y -= PADDLE_SPEED
            if keys[pygame.K_DOWN] and paddle_b.bottom < SCREEN_HEIGHT:
                paddle_b.y += PADDLE_SPEED

            # Ball movement
            ball.x += ball_speed_x
            ball.y += ball_speed_y

            # Ball collision with top/bottom walls
            if ball.top <= 0 or ball.bottom >= SCREEN_HEIGHT:
                ball_speed_y *= -1
                play_sound(sound_wall_hit)

            # Ball collision with paddles
            collision_tolerance = 10 # How far the ball can go "into" the paddle before bouncing

            # Collision with Paddle A
            if paddle_a.colliderect(ball):
                # Check if ball is moving towards paddle A and hits its front face
                if ball_speed_x < 0 and abs(ball.left - paddle_a.right) < collision_tolerance:
                    ball_speed_x *= -1
                    play_sound(sound_paddle_hit)
                    # Modify Y speed based on where the ball hits the paddle
                    delta_y = ball.centery - paddle_a.centery
                    ball_speed_y = delta_y * 0.20 # Adjust multiplier for desired angle effect
                    # Clamp ball_speed_y to prevent extreme angles or getting stuck
                    ball_speed_y = max(min(ball_speed_y, BALL_SPEED_Y_INITIAL * 1.8), -BALL_SPEED_Y_INITIAL * 1.8)


            # Collision with Paddle B
            if paddle_b.colliderect(ball):
                # Check if ball is moving towards paddle B and hits its front face
                if ball_speed_x > 0 and abs(ball.right - paddle_b.left) < collision_tolerance:
                    ball_speed_x *= -1
                    play_sound(sound_paddle_hit)
                    # Modify Y speed based on where the ball hits the paddle
                    delta_y = ball.centery - paddle_b.centery
                    ball_speed_y = delta_y * 0.20 # Adjust multiplier
                    # Clamp ball_speed_y
                    ball_speed_y = max(min(ball_speed_y, BALL_SPEED_Y_INITIAL * 1.8), -BALL_SPEED_Y_INITIAL * 1.8)

            # Ball out of bounds (scoring)
            if ball.left <= 0: # Player B scores
                score_b += 1
                play_sound(sound_score)
                if score_b >= WINNING_SCORE:
                    winner = "Player B"
                    game_state = GAME_OVER
                    play_sound(sound_game_over_win)
                else:
                    ball.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
                    ball_speed_x, ball_speed_y = reset_ball_values()
                    time.sleep(0.5) # Brief pause before next serve

            if ball.right >= SCREEN_WIDTH: # Player A scores
                score_a += 1
                play_sound(sound_score)
                if score_a >= WINNING_SCORE:
                    winner = "Player A"
                    game_state = GAME_OVER
                    play_sound(sound_game_over_win)
                else:
                    ball.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
                    ball_speed_x, ball_speed_y = reset_ball_values()
                    time.sleep(0.5) # Brief pause

        # --- Drawing ---
        screen.fill(BLACK) # Clear screen with black background

        if game_state == PLAYING:
            # Draw paddles
            pygame.draw.rect(screen, WHITE, paddle_a)
            pygame.draw.rect(screen, WHITE, paddle_b)
            # Draw ball
            pygame.draw.ellipse(screen, WHITE, ball) # Ball is a circle
            # Draw center line (dashed or solid)
            pygame.draw.aaline(screen, WHITE, (SCREEN_WIDTH // 2, 0), (SCREEN_WIDTH // 2, SCREEN_HEIGHT))
        elif game_state == GAME_OVER:
            if winner:
                draw_text("GAME OVER", game_over_font, RED, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4, center=True)
                draw_text(f"{winner} Wins!", score_font, WHITE, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, center=True)
            draw_text("Play Again? (Y/N)", restart_font, WHITE, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT * 3 // 4, center=True)

        # Draw scores (always visible)
        draw_text(str(score_a), score_font, WHITE, screen, SCREEN_WIDTH // 4, 20)
        # Adjust Player B's score position to be more centered in its quadrant
        score_b_text_width = score_font.size(str(score_b))[0]
        draw_text(str(score_b), score_font, WHITE, screen, SCREEN_WIDTH * 3 // 4 - score_b_text_width // 2, 20)

        # Update the full display
        pygame.display.flip()

        # Maintain 60 FPS
        clock.tick(FPS)

    pygame.quit() # Uninitialize Pygame modules

if __name__ == '__main__':
    main()

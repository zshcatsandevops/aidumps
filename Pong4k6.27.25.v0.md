import pygame
import numpy as np
import random
import math

# --- CatRNN Purr-ameters & Constants ---
SCREEN_WIDTH, SCREEN_HEIGHT = 858, 525  # Authentic Atari 2600 resolution (scaled)
PADDLE_WIDTH, PADDLE_HEIGHT = 15, 80
BALL_SIZE = 15
PADDLE_SPEED = 6  # Kept fixed for authentic feel
AI_PADDLE_SPEED = 6

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Game constants
WINNING_SCORE = 11

# --- Procedural Audio Generation (The Fun Part) ---
# A cat's purr is complex, but beeps are simple.
pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()

def generate_beep(frequency, duration_ms, volume=0.2):
    """Generates a numpy array for a sine wave beep."""
    sample_rate = 44100
    num_samples = int(sample_rate * duration_ms / 1000.0)
    
    # Generate a sine wave
    t = np.linspace(0., duration_ms / 1000.0, num_samples, endpoint=False)
    wave = np.sin(2. * np.pi * frequency * t)
    
    # Scale to 16-bit integer range
    amplitude = volume * (2**15 - 1)
    wave = (wave * amplitude).astype(np.int16)
    
    # Pygame needs a 2D array for stereo, even for mono sound
    sound_array = np.column_stack([wave, wave])
    
    return pygame.sndarray.make_sound(sound_array)

# Create the sound effects once
PADDLE_HIT_SOUND = generate_beep(440, 50) # A4 note
WALL_HIT_SOUND = generate_beep(261, 50)  # C4 note
SCORE_SOUND = generate_beep(587, 100)      # D5 note


# --- Procedural Graphics (Drawing with Paws) ---
# No need for font files when you can draw numbers yourself.
def draw_segment(surface, x, y, width, height, is_horizontal):
    """Draws a single segment of a digital number."""
    if is_horizontal:
        pygame.draw.rect(surface, WHITE, (x, y, width, height))
    else:
        pygame.draw.rect(surface, WHITE, (x, y, height, width))

def draw_digit(surface, digit, x, y, size=5):
    """Draws a single digit using 7 segments."""
    seg_len = size * 4
    seg_thick = size

    # Segment patterns for digits 0-9
    #       ---A---
    #      |       |
    #      F       B
    #      |       |
    #       ---G---
    #      |       |
    #      E       C
    #      |       |
    #       ---D---
    segments = {
        0: ['A', 'B', 'C', 'D', 'E', 'F'],
        1: ['B', 'C'],
        2: ['A', 'B', 'G', 'E', 'D'],
        3: ['A', 'B', 'G', 'C', 'D'],
        4: ['F', 'G', 'B', 'C'],
        5: ['A', 'F', 'G', 'C', 'D'],
        6: ['A', 'F', 'G', 'E', 'C', 'D'],
        7: ['A', 'B', 'C'],
        8: ['A', 'B', 'C', 'D', 'E', 'F', 'G'],
        9: ['A', 'B', 'C', 'D', 'F', 'G']
    }

    if 'A' in segments.get(digit, []):
        draw_segment(surface, x + seg_thick, y, seg_len, seg_thick, True)
    if 'B' in segments.get(digit, []):
        draw_segment(surface, x + seg_len + seg_thick, y + seg_thick, seg_len, seg_thick, False)
    if 'C' in segments.get(digit, []):
        draw_segment(surface, x + seg_len + seg_thick, y + seg_len + (2 * seg_thick), seg_len, seg_thick, False)
    if 'D' in segments.get(digit, []):
        draw_segment(surface, x + seg_thick, y + (2 * seg_len) + (2 * seg_thick), seg_len, seg_thick, True)
    if 'E' in segments.get(digit, []):
        draw_segment(surface, x, y + seg_len + (2 * seg_thick), seg_len, seg_thick, False)
    if 'F' in segments.get(digit, []):
        draw_segment(surface, x, y + seg_thick, seg_len, seg_thick, False)
    if 'G' in segments.get(digit, []):
        draw_segment(surface, x + seg_thick, y + seg_len + seg_thick, seg_len, seg_thick, True)

def draw_score(surface, score, x, y, size=5):
    """Draws a two-digit score."""
    score_str = f"{score:02d}"
    digit_width = size * 6
    draw_digit(surface, int(score_str[0]), x, y, size)
    draw_digit(surface, int(score_str[1]), x + digit_width, y, size)

def draw_text_pong(surface, x, y):
    """Draws the word 'PONG' using rectangles. A true masterpiece."""
    # This is tedious, but required to avoid font files.
    font_data = {
        'P': [(0,0,1,5), (1,0,1,1), (2,0,1,1), (1,2,1,1), (2,2,1,1), (1,1,1,1)],
        'O': [(0,1,1,3), (1,0,1,1), (2,0,1,1), (3,1,1,3), (1,4,1,1), (2,4,1,1)],
        'N': [(0,0,1,5), (3,0,1,5), (1,1,1,1), (2,2,1,1)],
        'G': [(0,1,1,3), (1,0,1,1), (2,0,1,1), (1,4,1,1), (2,4,1,1), (3,2,1,2), (2,2,1,1)]
    }
    char_spacing = 50
    scale = 8
    
    current_x = x
    for char in "PONG":
        if char in font_data:
            for seg in font_data[char]:
                rx, ry, rw, rh = seg
                pygame.draw.rect(surface, WHITE, (current_x + rx*scale, y + ry*scale, rw*scale, rh*scale))
            current_x += char_spacing

# --- Game Object Classes ---

class Paddle:
    def __init__(self, x, y, is_ai=False):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.is_ai = is_ai

    def draw(self, surface):
        pygame.draw.rect(surface, WHITE, self.rect)

    def move_with_mouse(self):
        if not self.is_ai:
            _, mouse_y = pygame.mouse.get_pos()
            self.rect.centery = mouse_y
            # Clamp paddle to screen
            if self.rect.top < 0:
                self.rect.top = 0
            if self.rect.bottom > SCREEN_HEIGHT:
                self.rect.bottom = SCREEN_HEIGHT
    
    def move_ai(self, ball):
        if self.is_ai:
            # A simple but effective AI: try to center the paddle on the ball
            if self.rect.centery < ball.rect.centery:
                self.rect.y += AI_PADDLE_SPEED
            if self.rect.centery > ball.rect.centery:
                self.rect.y -= AI_PADDLE_SPEED
            # Clamp paddle to screen
            if self.rect.top < 0:
                self.rect.top = 0
            if self.rect.bottom > SCREEN_HEIGHT:
                self.rect.bottom = SCREEN_HEIGHT

class Ball:
    def __init__(self):
        self.rect = pygame.Rect(0, 0, BALL_SIZE, BALL_SIZE)
        self.reset()

    def reset(self, serving_direction=None):
        """Resets the ball to the center with a random velocity."""
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        
        if serving_direction is None:
            # Start of game
            self.vx = 0
            self.vy = 0
        else:
            # After a score
            angle = random.uniform(-math.pi / 4, math.pi / 4) # 45 degrees up or down
            speed = 7
            self.vx = speed * math.cos(angle) * serving_direction
            self.vy = speed * math.sin(angle)

    def move(self):
        self.rect.x += self.vx
        self.rect.y += self.vy

    def draw(self, surface):
        pygame.draw.rect(surface, WHITE, self.rect)

# --- Main Game Function ---
def main():
    """The main game loop. The hunt begins here."""
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("CatRNN Presents: PONG")
    clock = pygame.time.Clock()
    
    # Hide the mouse cursor
    pygame.mouse.set_visible(False)

    # Create game objects
    player_paddle = Paddle(30, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2)
    ai_paddle = Paddle(SCREEN_WIDTH - 30 - PADDLE_WIDTH, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, is_ai=True)
    ball = Ball()
    
    # Game state
    player_score = 0
    ai_score = 0
    game_state = "start" # "start", "playing", "game_over"

    running = True
    while running:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_SPACE:
                    if game_state == "start":
                        game_state = "playing"
                        ball.reset(random.choice([-1, 1]))
                    elif game_state == "game_over":
                        # Reset the whole game
                        player_score = 0
                        ai_score = 0
                        game_state = "start"
                        ball.reset()


        # --- Game Logic ---
        if game_state == "playing":
            player_paddle.move_with_mouse()
            ai_paddle.move_ai(ball)
            ball.move()

            # Wall collision (top/bottom)
            if ball.rect.top <= 0 or ball.rect.bottom >= SCREEN_HEIGHT:
                ball.vy *= -1
                WALL_HIT_SOUND.play()

            # Paddle collision
            if ball.rect.colliderect(player_paddle.rect) and ball.vx < 0:
                ball.vx *= -1
                # Change angle based on where the ball hit the paddle
                relative_intersect_y = (player_paddle.rect.centery - ball.rect.centery)
                normalized_intersect_y = relative_intersect_y / (PADDLE_HEIGHT / 2)
                bounce_angle = normalized_intersect_y * (math.pi / 3) # Max 60 degrees
                
                speed = math.sqrt(ball.vx**2 + ball.vy**2) * 1.05 # Increase speed slightly
                ball.vx = speed * math.cos(bounce_angle)
                ball.vy = -speed * math.sin(bounce_angle)
                PADDLE_HIT_SOUND.play()

            if ball.rect.colliderect(ai_paddle.rect) and ball.vx > 0:
                ball.vx *= -1
                relative_intersect_y = (ai_paddle.rect.centery - ball.rect.centery)
                normalized_intersect_y = relative_intersect_y / (PADDLE_HEIGHT / 2)
                bounce_angle = normalized_intersect_y * (math.pi / 3)
                
                speed = math.sqrt(ball.vx**2 + ball.vy**2) * 1.05
                ball.vx = -speed * math.cos(bounce_angle)
                ball.vy = -speed * math.sin(bounce_angle)
                PADDLE_HIT_SOUND.play()

            # Scoring
            if ball.rect.left <= 0:
                ai_score += 1
                SCORE_SOUND.play()
                if ai_score >= WINNING_SCORE:
                    game_state = "game_over"
                else:
                    ball.reset(serving_direction=1) # AI serves
            
            if ball.rect.right >= SCREEN_WIDTH:
                player_score += 1
                SCORE_SOUND.play()
                if player_score >= WINNING_SCORE:
                    game_state = "game_over"
                else:
                    ball.reset(serving_direction=-1) # Player serves

        # --- Drawing ---
        screen.fill(BLACK)
        
        # Draw center dashed line
        for i in range(0, SCREEN_HEIGHT, 25):
            pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH//2 - 2, i, 4, 15))
            
        # Draw paddles and ball
        player_paddle.draw(screen)
        ai_paddle.draw(screen)
        if game_state != "start": # Don't draw ball on start screen
            ball.draw(screen)
        
        # Draw scores
        draw_score(screen, player_score, SCREEN_WIDTH // 4, 20)
        draw_score(screen, ai_score, SCREEN_WIDTH * 3 // 4 - 50, 20)

        # Draw messages based on game state
        if game_state == "start":
            draw_text_pong(screen, SCREEN_WIDTH // 2 - 90, SCREEN_HEIGHT // 4)
            # You could draw text here with primitives too, but that's a lot of rectangles!
            # Using SysFont is a good compromise as it's not a file asset.
            font = pygame.font.SysFont('Consolas', 30)
            text_surf = font.render("PRESS SPACE TO START", True, WHITE)
            text_rect = text_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
            screen.blit(text_surf, text_rect)

        if game_state == "game_over":
            font = pygame.font.SysFont('Consolas', 50)
            winner_text = "PLAYER WINS!" if player_score >= WINNING_SCORE else "COMPUTER WINS!"
            text_surf = font.render(winner_text, True, WHITE)
            text_rect = text_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            screen.blit(text_surf, text_rect)
            
            font_small = pygame.font.SysFont('Consolas', 30)
            restart_surf = font_small.render("PRESS SPACE TO RESTART", True, WHITE)
            restart_rect = restart_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60))
            screen.blit(restart_surf, restart_rect)


        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

# --- Entry Point ---
if __name__ == '__main__':
    main()

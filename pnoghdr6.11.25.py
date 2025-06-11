import pygame
import random
import numpy
import time

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BALL_SPEED = 7
PADDLE_SPEED = 7
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
FPS = 60

# --- Audio Generation Function ---
def make_sound(frequency=440, duration=0.1):
    """
    Generates a pygame.mixer.Sound object for a sine wave tone.
    """
    sample_rate = 44100
    n_samples = int(round(duration * sample_rate))
    buf = numpy.zeros((n_samples, 2), dtype = numpy.int16)
    max_sample = 2**(16 - 1) - 1

    for s in range(n_samples):
        t = float(s) / sample_rate    # time in seconds
        
        # generate sine wave
        sine = max_sample * numpy.sin(2 * numpy.pi * frequency * t)
        
        #apply to both channels
        buf[s][0] = int(round(sine))
        buf[s][1] = int(round(sine))

    return pygame.sndarray.make_sound(buf)

# --- Classes ---
class Paddle(pygame.sprite.Sprite):
    """
    This class represents a paddle. It derives from the "Sprite" class in Pygame.
    """
    def __init__(self, color, width, height):
        super().__init__()

        self.image = pygame.Surface([width, height])
        self.image.fill(BLACK)
        self.image.set_colorkey(BLACK)

        # Draw the paddle (a rectangle)
        pygame.draw.rect(self.image, color, [0, 0, width, height])

        self.rect = self.image.get_rect()

    def move_up(self, pixels):
        self.rect.y -= pixels
        # Check that you are not going too far (off the screen)
        if self.rect.y < 0:
            self.rect.y = 0

    def move_down(self, pixels):
        self.rect.y += pixels
        # Check that you are not going too far (off the screen)
        if self.rect.y > SCREEN_HEIGHT - self.rect.height:
            self.rect.y = SCREEN_HEIGHT - self.rect.height

class Ball(pygame.sprite.Sprite):
    """
    This class represents the ball. It derives from the "Sprite" class in Pygame.
    """
    def __init__(self, color, width, height):
        super().__init__()

        self.image = pygame.Surface([width, height])
        self.image.fill(BLACK)
        self.image.set_colorkey(BLACK)

        # Draw the ball (a rectangle)
        pygame.draw.rect(self.image, color, [0, 0, width, height])

        self.velocity = [random.choice([-BALL_SPEED, BALL_SPEED]), random.choice([-BALL_SPEED, BALL_SPEED])]

        self.rect = self.image.get_rect()

    def update(self):
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]

    def bounce(self):
        self.velocity[0] = -self.velocity[0]
        self.velocity[1] = random.choice([-BALL_SPEED, BALL_SPEED])

# --- Main Program ---
def main():
    """ Main function for the game. """
    pygame.mixer.pre_init(44100, -16, 2, 512) # setup mixer to avoid sound lag
    pygame.init()

    # --- Screen and Window ---
    size = (SCREEN_WIDTH, SCREEN_HEIGHT)
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption("Pong")

    # --- Paddles ---
    paddle_a = Paddle(WHITE, 10, 100)
    paddle_a.rect.x = 20
    paddle_a.rect.y = (SCREEN_HEIGHT // 2) - (paddle_a.rect.height // 2)

    paddle_b = Paddle(WHITE, 10, 100)
    paddle_b.rect.x = SCREEN_WIDTH - 30
    paddle_b.rect.y = (SCREEN_HEIGHT // 2) - (paddle_b.rect.height // 2)

    # --- Ball ---
    ball = Ball(WHITE, 10, 10)
    ball.rect.x = (SCREEN_WIDTH // 2) - (ball.rect.width // 2)
    ball.rect.y = (SCREEN_HEIGHT // 2) - (ball.rect.height // 2)

    # --- Sprites list ---
    all_sprites_list = pygame.sprite.Group()
    all_sprites_list.add(paddle_a)
    all_sprites_list.add(paddle_b)
    all_sprites_list.add(ball)

    # --- Game Loop ---
    carry_on = True
    clock = pygame.time.Clock()

    # --- Scores ---
    score_a = 0
    score_b = 0

    # --- Game State ---
    game_state = 'playing'  # Can be 'playing' or 'game_over'

    # --- Sound Effects ---
    beep_sound = make_sound(frequency=880, duration=0.075) # Higher pitch for bounces
    boop_sound = make_sound(frequency=440, duration=0.1)  # Lower pitch for scoring

    while carry_on:
        # --- Main event loop ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                carry_on = False
            elif game_state == 'game_over' and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_y:
                    # Reset game
                    score_a = 0
                    score_b = 0
                    ball.rect.x = (SCREEN_WIDTH // 2) - (ball.rect.width // 2)
                    ball.rect.y = (SCREEN_HEIGHT // 2) - (ball.rect.height // 2)
                    ball.velocity = [random.choice([-BALL_SPEED, BALL_SPEED]), random.choice([-BALL_SPEED, BALL_SPEED])]
                    game_state = 'playing'
                elif event.key == pygame.K_n:
                    carry_on = False

        if game_state == 'playing':
            # --- Player Input (Mouse Control) ---
            mouse_pos = pygame.mouse.get_pos()
            paddle_a.rect.y = mouse_pos[1] - (paddle_a.rect.height // 2)
            
            # Keep player paddle on screen
            if paddle_a.rect.top < 0:
                paddle_a.rect.top = 0
            if paddle_a.rect.bottom > SCREEN_HEIGHT:
                paddle_a.rect.bottom = SCREEN_HEIGHT

            # --- AI Opponent ---
            if paddle_b.rect.centery < ball.rect.centery:
                paddle_b.move_down(PADDLE_SPEED - 2)
            if paddle_b.rect.centery > ball.rect.centery:
                paddle_b.move_up(PADDLE_SPEED - 2)

            # --- Game logic ---
            all_sprites_list.update()

            # Check if the ball hits the walls
            if ball.rect.x >= SCREEN_WIDTH - ball.rect.width:
                score_a += 1
                ball.rect.x = (SCREEN_WIDTH // 2) - (ball.rect.width // 2)
                ball.rect.y = (SCREEN_HEIGHT // 2) - (ball.rect.height // 2)
                ball.velocity[0] = -ball.velocity[0]
                boop_sound.play()
            if ball.rect.x <= 0:
                score_b += 1
                ball.rect.x = (SCREEN_WIDTH // 2) - (ball.rect.width // 2)
                ball.rect.y = (SCREEN_HEIGHT // 2) - (ball.rect.height // 2)
                ball.velocity[0] = -ball.velocity[0]
                boop_sound.play()
            if ball.rect.y > SCREEN_HEIGHT - ball.rect.height or ball.rect.y < 0:
                ball.velocity[1] = -ball.velocity[1]
                beep_sound.play()

            # Detect collisions with paddles
            if pygame.sprite.collide_mask(ball, paddle_a) or pygame.sprite.collide_mask(ball, paddle_b):
                ball.bounce()
                beep_sound.play()

            # Check for game over
            if score_a >= 5 or score_b >= 5:
                game_state = 'game_over'

        # --- Drawing code ---
        screen.fill(BLACK)
        if game_state == 'playing':
            # Draw the net
            pygame.draw.line(screen, WHITE, [SCREEN_WIDTH // 2, 0], [SCREEN_WIDTH // 2, SCREEN_HEIGHT], 5)
            all_sprites_list.draw(screen)

            # Display scores
            font = pygame.font.Font(None, 74)
            text = font.render(str(score_a), 1, WHITE)
            screen.blit(text, (250, 10))
            text = font.render(str(score_b), 1, WHITE)
            screen.blit(text, (SCREEN_WIDTH - 250, 10))
        elif game_state == 'game_over':
            # Display game over text
            font = pygame.font.Font(None, 100)
            text = font.render("GAME OVER", 1, WHITE)
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 - text.get_height() // 2 - 50))
            font = pygame.font.Font(None, 50)
            text = font.render("Play Again? Y/N", 1, WHITE)
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 - text.get_height() // 2 + 50))

        # --- Update the screen ---
        pygame.display.flip()

        # --- Limit to 60 frames per second ---
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()

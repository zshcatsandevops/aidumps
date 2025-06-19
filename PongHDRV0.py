import pygame
import sys
import random
import numpy as np
from enum import Enum, auto

WIDTH, HEIGHT = 800, 600
FPS = 60
PADDLE_WIDTH, PADDLE_HEIGHT = 20, 120
BALL_SIZE = 20
PADDLE_SPEED = 8
BALL_SPEED = 7
WIN_SCORE = 5
AI_REACTION_THRESHOLD = 30  # Deadzone for AI paddle movement

# --- Game States ---
class GameState(Enum):
    MENU = auto()
    PLAY = auto()
    GAME_OVER = auto()
    SERVE_DELAY = auto()  # New state for serving delay

# --- SFX (Pure Sine Tone Generator, No Files Needed) ---
def tone(freq=440, duration_ms=100, vol=0.5):
    sample_rate = 44100
    n = int(sample_rate * duration_ms / 1000)
    buf = vol * np.sin(2 * np.pi * np.arange(n) * freq / sample_rate)
    arr = np.array(buf * 32767, dtype=np.int16)
    return pygame.sndarray.make_sound(arr)

SFX_BEEP = None
SFX_BOOP = None
SFX_SCORE = None

def init_sfx():
    global SFX_BEEP, SFX_BOOP, SFX_SCORE
    SFX_BEEP = tone(900, 70, 0.35)
    SFX_BOOP = tone(300, 90, 0.40)
    SFX_SCORE = tone(200, 300, 0.5)

# --- Paddle Class ---
class Paddle:
    def __init__(self, x, y, is_ai=False):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.is_ai = is_ai
        self.color = (200, 200, 255) if not is_ai else (255, 180, 120)

    def move(self, target_y=None):
        if self.is_ai and target_y is not None:
            # AI with deadzone to prevent jittering
            diff = target_y - self.rect.centery
            if abs(diff) > AI_REACTION_THRESHOLD:
                move_amount = max(min(diff, PADDLE_SPEED), -PADDLE_SPEED)
                self.rect.centery += move_amount
        elif not self.is_ai and target_y is not None:
            # Player paddle follows mouse
            self.rect.centery = max(PADDLE_HEIGHT // 2, min(HEIGHT - PADDLE_HEIGHT // 2, target_y))
        self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)

# --- Ball Class ---
class Ball:
    def __init__(self):
        self.rect = pygame.Rect(WIDTH//2 - BALL_SIZE//2, HEIGHT//2 - BALL_SIZE//2, BALL_SIZE, BALL_SIZE)
        self.reset(init=True)
        self.color = (255, 255, 100)

    def reset(self, init=False):
        self.rect.center = (WIDTH//2, HEIGHT//2)
        # Random but controlled initial direction
        self.dx = BALL_SPEED * random.choice([-1, 1])
        self.dy = random.uniform(-BALL_SPEED/2, BALL_SPEED/2)
        
        # Normalize speed to prevent slow balls
        self.normalize_speed()
        
        # On reset, give a grace period to avoid instant scoring
        if not init:
            self.rect.x += self.dx * 2
            self.rect.y = max(0, min(HEIGHT - BALL_SIZE, self.rect.y))

    def normalize_speed(self):
        # Ensure consistent ball speed
        magnitude = (self.dx**2 + self.dy**2)**0.5
        if magnitude > 0:
            self.dx = (self.dx / magnitude) * BALL_SPEED
            self.dy = (self.dy / magnitude) * BALL_SPEED

    def move(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        
        # Top/Bottom wall collision
        if self.rect.top <= 0:
            self.rect.top = 0
            self.dy = -self.dy
            if SFX_BEEP: SFX_BEEP.play()
        elif self.rect.bottom >= HEIGHT:
            self.rect.bottom = HEIGHT
            self.dy = -self.dy
            if SFX_BEEP: SFX_BEEP.play()

    def check_paddle(self, paddle):
        if self.rect.colliderect(paddle.rect):
            # Calculate where ball hit paddle (for better bounce physics)
            relative_y = (paddle.rect.centery - self.rect.centery) / (PADDLE_HEIGHT/2)
            
            # Reverse horizontal direction
            self.dx = -self.dx * 1.05  # Slight speed increase on hit
            
            # Adjust vertical angle based on hit position
            self.dy = -relative_y * BALL_SPEED
            
            # Normalize speed after collision
            self.normalize_speed()
            
            # Unstick ball from paddle
            if self.dx > 0:
                self.rect.left = paddle.rect.right
            else:
                self.rect.right = paddle.rect.left
                
            if SFX_BEEP: SFX_BEEP.play()
            return True
        return False

    def draw(self, screen):
        pygame.draw.ellipse(screen, self.color, self.rect)

# --- Pong Engine Class ---
class PongEngine:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=1)
        except Exception:
            pass # allow no sound mode
        init_sfx()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Pong Engine Deluxe")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 48)
        self.bigfont = pygame.font.SysFont(None, 72)
        self.state = GameState.MENU
        self.left_score = 0
        self.right_score = 0
        self.left_paddle = Paddle(20, HEIGHT//2 - PADDLE_HEIGHT//2, is_ai=False)
        self.right_paddle = Paddle(WIDTH - 40, HEIGHT//2 - PADDLE_HEIGHT//2, is_ai=True)
        self.ball = Ball()
        self.serve_delay = 0
        pygame.mouse.set_visible(False)

    def draw_text(self, text, y, color=(255,255,255), font=None):
        if font is None:
            font = self.font
        txt = font.render(text, True, color)
        rect = txt.get_rect(center=(WIDTH//2, y))
        self.screen.blit(txt, rect)

    def reset_game(self):
        self.left_score = 0
        self.right_score = 0
        self.left_paddle.rect.centery = HEIGHT//2
        self.right_paddle.rect.centery = HEIGHT//2
        self.ball.reset()
        self.serve_delay = 0
        self.state = GameState.PLAY

    def run(self):
        while True:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                    
                if self.state == GameState.MENU and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.reset_game()
                        
                elif self.state == GameState.GAME_OVER and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_y:
                        self.reset_game()
                    elif event.key == pygame.K_n:
                        pygame.quit()
                        sys.exit()
                        
                elif self.state == GameState.SERVE_DELAY and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.state = GameState.PLAY

            self.screen.fill((25, 30, 40))

            if self.state == GameState.MENU:
                self.draw_text("PONG ENGINE!", HEIGHT//2 - 80, font=self.bigfont)
                self.draw_text("Move your mouse up/down to control", HEIGHT//2)
                self.draw_text("Press SPACE to start!", HEIGHT//2 + 60, color=(200,255,200))
                
            elif self.state in [GameState.PLAY, GameState.SERVE_DELAY]:
                mouse_y = pygame.mouse.get_pos()[1]
                self.left_paddle.move(mouse_y)
                
                if self.state == GameState.PLAY:
                    self.right_paddle.move(self.ball.rect.centery)
                    self.ball.move()
                    
                    # Check paddle collisions
                    left_hit = self.ball.check_paddle(self.left_paddle)
                    right_hit = self.ball.check_paddle(self.right_paddle)
                    
                    # Score detection
                    if self.ball.rect.right < 0:
                        self.right_score += 1
                        if SFX_SCORE: SFX_SCORE.play()
                        self.state = GameState.SERVE_DELAY
                        self.serve_delay = FPS // 2  # 0.5 second delay
                        
                    elif self.ball.rect.left > WIDTH:
                        self.left_score += 1
                        if SFX_SCORE: SFX_SCORE.play()
                        self.state = GameState.SERVE_DELAY
                        self.serve_delay = FPS // 2  # 0.5 second delay
                
                # Draw game elements
                self.left_paddle.draw(self.screen)
                self.right_paddle.draw(self.screen)
                self.ball.draw(self.screen)
                pygame.draw.line(self.screen, (150,150,150), (WIDTH//2, 0), (WIDTH//2, HEIGHT), 4)
                score_text = f"{self.left_score}    {self.right_score}"
                self.draw_text(score_text, 50)
                
                # Serve delay countdown
                if self.state == GameState.SERVE_DELAY:
                    self.serve_delay -= 1
                    if self.serve_delay <= 0:
                        self.ball.reset()
                        self.state = GameState.PLAY
                    else:
                        self.draw_text("GET READY...", HEIGHT//2, color=(255, 200, 100))
                
                # Win detection
                if self.left_score >= WIN_SCORE or self.right_score >= WIN_SCORE:
                    self.state = GameState.GAME_OVER
                    
            elif self.state == GameState.GAME_OVER:
                self.draw_text("GAME OVER", HEIGHT//2 - 80, font=self.bigfont)
                winner = "PLAYER" if self.left_score > self.right_score else "AI"
                self.draw_text(f"{winner} WINS!", HEIGHT//2 - 20, color=(255, 255, 0))
                self.draw_text("Play again? (Y/N)", HEIGHT//2 + 50, color=(200,255,200))
                score_text = f"Final: {self.left_score}    {self.right_score}"
                self.draw_text(score_text, HEIGHT//2 + 100)

            pygame.display.flip()

# --- RUN THE ENGINE ---
if __name__ == "__main__":
    PongEngine().run()

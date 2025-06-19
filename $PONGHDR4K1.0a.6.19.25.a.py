import pygame
import sys
import random
import numpy as np
from enum import Enum, auto

# --- Configuration Constants ---
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
    SERVE_DELAY = auto()
    GAME_OVER = auto()

# --- SFX (Pure Sine Tone Generator) ---

def tone(freq=440, duration_ms=100, vol=0.5):
    """Generate a PyGame Sound object containing a sine wave."""
    sample_rate = 44100
    n = int(sample_rate * duration_ms / 1000)
    buf = vol * np.sin(2 * np.pi * np.arange(n) * freq / sample_rate)
    arr = np.array(buf * 32767, dtype=np.int16)
    return pygame.sndarray.make_sound(arr)

SFX_BEEP = None
SFX_SCORE = None

def init_sfx():
    """Initialise sound effects. If mixer unavailable, silently fail."""
    global SFX_BEEP, SFX_SCORE
    try:
        SFX_BEEP = tone(900, 70, 0.35)
        SFX_SCORE = tone(200, 300, 0.5)
    except Exception:
        SFX_BEEP = SFX_SCORE = None

# --- Paddle Class ---
class Paddle:
    def __init__(self, x, y, is_ai: bool = False):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.is_ai = is_ai
        self.color = (200, 200, 255) if not is_ai else (255, 180, 120)

    def move(self, target_y: int | None = None):
        """Move paddle. For AI, follow the ball with a dead-zone."""
        if self.is_ai and target_y is not None:
            diff = target_y - self.rect.centery
            if abs(diff) > AI_REACTION_THRESHOLD:
                self.rect.centery += max(-PADDLE_SPEED, min(PADDLE_SPEED, diff))
        elif not self.is_ai and target_y is not None:
            self.rect.centery = max(PADDLE_HEIGHT // 2,
                                     min(HEIGHT - PADDLE_HEIGHT // 2, target_y))
        self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))

    def draw(self, screen: pygame.Surface):
        pygame.draw.rect(screen, self.color, self.rect)

# --- Ball Class ---
class Ball:
    def __init__(self):
        self.rect = pygame.Rect(0, 0, BALL_SIZE, BALL_SIZE)
        self.reset(init=True)
        self.color = (255, 255, 100)

    def reset(self, init: bool = False):
        """Centre ball and launch in random direction."""
        self.pos = pygame.Vector2(WIDTH // 2, HEIGHT // 2)
        angle = random.uniform(-0.5, 0.5)
        self.velocity = pygame.Vector2(
            random.choice([-1, 1]) * BALL_SPEED,
            BALL_SPEED * angle
        )
        if not init:
            # small offset to avoid immediate rescore
            self.pos += self.velocity.normalize() * (BALL_SIZE * 2)
        self.rect.center = self.pos

    def move(self):
        self.pos += self.velocity
        # Wall bounce
        if self.pos.y - BALL_SIZE / 2 <= 0:
            self.pos.y = BALL_SIZE / 2
            self.velocity.y *= -1
            if SFX_BEEP:
                SFX_BEEP.play()
        elif self.pos.y + BALL_SIZE / 2 >= HEIGHT:
            self.pos.y = HEIGHT - BALL_SIZE / 2
            self.velocity.y *= -1
            if SFX_BEEP:
                SFX_BEEP.play()
        self.rect.center = self.pos

    def check_paddle(self, paddle: Paddle) -> bool:
        if self.rect.colliderect(paddle.rect):
            rel = (self.rect.centery - paddle.rect.centery) / (PADDLE_HEIGHT / 2)
            self.velocity.x *= -1.05
            self.velocity.y = rel * BALL_SPEED * -1
            self.velocity = self.velocity.normalize() * BALL_SPEED
            # push out
            if self.velocity.x > 0:
                self.rect.left = paddle.rect.right
            else:
                self.rect.right = paddle.rect.left
            self.pos = pygame.Vector2(self.rect.center)
            if SFX_BEEP:
                SFX_BEEP.play()
            return True
        return False

    def draw(self, screen: pygame.Surface):
        pygame.draw.ellipse(screen, self.color, self.rect)

# --- Pong Engine Class ---
class PongEngine:
    def __init__(self):
        pygame.init()
        pygame.mixer.pre_init(44100, -16, 1)
        try:
            pygame.mixer.init()
        except pygame.error:
            print("[WARN] Audio device not available, continuing without sound")
        init_sfx()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Pong Engine Deluxe")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 48)
        self.bigfont = pygame.font.SysFont(None, 72)
        self.state = GameState.MENU
        self.left_score = 0
        self.right_score = 0
        self.left_paddle = Paddle(20, HEIGHT // 2 - PADDLE_HEIGHT // 2)
        self.right_paddle = Paddle(WIDTH - 40, HEIGHT // 2 - PADDLE_HEIGHT // 2, is_ai=True)
        self.ball = Ball()
        self.serve_delay = 0
        pygame.mouse.set_visible(False)

    # --- Utility drawing helpers ---
    def draw_text(self, text: str, y: int, color=(255, 255, 255), font=None):
        font = font or self.font
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(WIDTH // 2, y))
        self.screen.blit(surf, rect)

    # --- Game Flow helpers ---
    def reset_game(self):
        self.left_score = 0
        self.right_score = 0
        self.left_paddle.rect.centery = HEIGHT // 2
        self.right_paddle.rect.centery = HEIGHT // 2
        self.ball.reset(init=True)
        self.state = GameState.PLAY

    # --- Main loop ---
    def run(self):
        while True:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if self.state == GameState.MENU and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.reset_game()
                elif self.state == GameState.GAME_OVER and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_y:
                        self.reset_game()
                    elif event.key == pygame.K_n:
                        pygame.quit(); sys.exit()
                elif self.state == GameState.SERVE_DELAY and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.state = GameState.PLAY

            self.screen.fill((25, 30, 40))

            if self.state == GameState.MENU:
                self.draw_text("PONG ENGINE!", HEIGHT // 2 - 80, font=self.bigfont)
                self.draw_text("Move mouse up/down to control", HEIGHT // 2)
                self.draw_text("Press SPACE to start!", HEIGHT // 2 + 60, color=(200, 255, 200))

            elif self.state in (GameState.PLAY, GameState.SERVE_DELAY):
                my = pygame.mouse.get_pos()[1]
                self.left_paddle.move(my)

                if self.state == GameState.PLAY:
                    self.right_paddle.move(self.ball.rect.centery)
                    self.ball.move()
                    # Collisions and scoring
                    self.ball.check_paddle(self.left_paddle)
                    self.ball.check_paddle(self.right_paddle)
                    if self.ball.rect.right < 0:
                        self.right_score += 1
                        if SFX_SCORE:
                            SFX_SCORE.play()
                        self.ball.reset(init=False)
                        self.state = GameState.SERVE_DELAY
                        self.serve_delay = FPS // 2
                    elif self.ball.rect.left > WIDTH:
                        self.left_score += 1
                        if SFX_SCORE:
                            SFX_SCORE.play()
                        self.ball.reset(init=False)
                        self.state = GameState.SERVE_DELAY
                        self.serve_delay = FPS // 2

                # Draw elements
                self.left_paddle.draw(self.screen)
                self.right_paddle.draw(self.screen)
                self.ball.draw(self.screen)
                pygame.draw.line(self.screen, (150, 150, 150), (WIDTH // 2, 0), (WIDTH // 2, HEIGHT), 4)
                self.draw_text(f"{self.left_score}    {self.right_score}", 50)

                if self.state == GameState.SERVE_DELAY:
                    self.serve_delay -= 1
                    if self.serve_delay <= 0:
                        self.state = GameState.PLAY
                    else:
                        self.draw_text("GET READY...", HEIGHT // 2, color=(255, 200, 100))

                if self.left_score >= WIN_SCORE or self.right_score >= WIN_SCORE:
                    self.state = GameState.GAME_OVER

            elif self.state == GameState.GAME_OVER:
                self.draw_text("GAME OVER", HEIGHT // 2 - 80, font=self.bigfont)
                winner = "PLAYER" if self.left_score > self.right_score else "AI"
                self.draw_text(f"{winner} WINS!", HEIGHT // 2 - 20, color=(255, 255, 0))
                self.draw_text("Play again? (Y/N)", HEIGHT // 2 + 50, color=(200, 255, 200))
                self.draw_text(f"Final: {self.left_score}    {self.right_score}", HEIGHT // 2 + 100)

            pygame.display.flip()

# --- Entry point ---
if __name__ == "__main__":
    PongEngine().run()

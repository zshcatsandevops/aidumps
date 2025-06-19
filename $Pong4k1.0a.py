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

# --- Game States ---
class GameState(Enum):
    MENU = auto()
    PLAY = auto()
    GAME_OVER = auto()

# --- SFX (Pure Sine Tone Generator, No Files Needed) ---
def tone(freq=440, duration_ms=100, vol=0.5):
    sample_rate = 44100
    n = int(sample_rate * duration_ms / 1000)
    buf = vol * np.sin(2 * np.pi * np.arange(n) * freq / sample_rate)
    arr = np.array(buf * 32767, dtype=np.int16)
    return pygame.sndarray.make_sound(arr)

SFX_BEEP = None
SFX_BOOP = None

def init_sfx():
    global SFX_BEEP, SFX_BOOP
    SFX_BEEP = tone(900, 70, 0.35)
    SFX_BOOP = tone(300, 90, 0.40)

# --- Paddle Class ---
class Paddle:
    def __init__(self, x, y, is_ai=False):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.is_ai = is_ai
        self.last_move = 0

    def move(self, target_y):
        if self.is_ai:
            # AI only moves if ball not in paddle or very close
            diff = target_y - self.rect.centery
            if abs(diff) > PADDLE_SPEED:
                self.rect.centery += PADDLE_SPEED if diff > 0 else -PADDLE_SPEED
        else:
            self.rect.centery = target_y
        self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))

    def draw(self, screen, color):
        pygame.draw.rect(screen, color, self.rect)

# --- Ball Class ---
class Ball:
    def __init__(self):
        self.rect = pygame.Rect(WIDTH//2 - BALL_SIZE//2, HEIGHT//2 - BALL_SIZE//2, BALL_SIZE, BALL_SIZE)
        self.reset(init=True)

    def reset(self, init=False):
        self.rect.center = (WIDTH//2, HEIGHT//2)
        # New serve alternates directions, so scoring feels fair
        self.dx = BALL_SPEED * random.choice([-1, 1])
        self.dy = BALL_SPEED * random.choice([-1, 1])
        # On reset, give a tiny grace period to avoid instant scoring
        if not init:
            self.rect.x += self.dx * 2

    def move(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        # Top/Bottom wall collision
        if self.rect.top <= 0 or self.rect.bottom >= HEIGHT:
            self.dy = -self.dy
            if SFX_BEEP: SFX_BEEP.play()

    def check_paddle(self, paddle):
        if self.rect.colliderect(paddle.rect):
            self.dx = -self.dx
            # Add a little angle, but clamp for fairness
            self.dy += random.randint(-2, 2)
            self.dy = max(min(self.dy, BALL_SPEED+3), -BALL_SPEED-3)
            # Unstick if inside paddle
            if self.dx > 0:
                self.rect.right = paddle.rect.left
            else:
                self.rect.left = paddle.rect.right
            if SFX_BEEP: SFX_BEEP.play()

    def draw(self, screen):
        pygame.draw.ellipse(screen, (255, 255, 100), self.rect)

# --- Pong Engine Class ---
class PongEngine:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=1)
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
        self.last_scorer = None # prevents double scoring

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
        self.ball.reset(init=True)
        self.last_scorer = None
        self.state = GameState.PLAY

    def run(self):
        while True:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if self.state == GameState.MENU and event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self.reset_game()
                elif self.state == GameState.GAME_OVER and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_y:
                        self.reset_game()
                    elif event.key == pygame.K_n:
                        pygame.quit()
                        sys.exit()

            self.screen.fill((25, 30, 40))

            if self.state == GameState.MENU:
                self.draw_text("PONG ENGINE!", HEIGHT//2 - 80, font=self.bigfont)
                self.draw_text("Move your mouse up/down to control", HEIGHT//2)
                self.draw_text("Press SPACE to start!", HEIGHT//2 + 60, color=(200,255,200))
            elif self.state == GameState.PLAY:
                mouse_y = pygame.mouse.get_pos()[1]
                self.left_paddle.move(mouse_y)
                self.right_paddle.move(self.ball.rect.centery)
                self.ball.move()
                self.ball.check_paddle(self.left_paddle)
                self.ball.check_paddle(self.right_paddle)
                self.left_paddle.draw(self.screen, (200, 200, 255))
                self.right_paddle.draw(self.screen, (255, 180, 120))
                self.ball.draw(self.screen)
                pygame.draw.line(self.screen, (150,150,150), (WIDTH//2, 0), (WIDTH//2, HEIGHT), 4)
                score_text = f"{self.left_score}    {self.right_score}"
                self.draw_text(score_text, 50)
                # Score detection—fix double scoring!
                if self.ball.rect.left <= 0:
                    if self.last_scorer != "RIGHT":
                        self.right_score += 1
                        self.last_scorer = "RIGHT"
                        if SFX_BOOP: SFX_BOOP.play()
                        self.ball.reset()
                elif self.ball.rect.right >= WIDTH:
                    if self.last_scorer != "LEFT":
                        self.left_score += 1
                        self.last_scorer = "LEFT"
                        if SFX_BOOP: SFX_BOOP.play()
                        self.ball.reset()
                else:
                    self.last_scorer = None
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

import pygame
import sys
import random
from enum import Enum, auto

# ==============================
# ===  PONG GAME ENGINE!!!   ===
# ==============================

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

# --- Paddle Class ---
class Paddle:
    def __init__(self, x, y, is_ai=False):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.is_ai = is_ai

    def move(self, target_y):
        if self.is_ai:
            if self.rect.centery < target_y:
                self.rect.centery += PADDLE_SPEED
            elif self.rect.centery > target_y:
                self.rect.centery -= PADDLE_SPEED
        else:
            # Clamp to screen
            self.rect.centery = target_y
        # Keep paddle on screen
        self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))

    def draw(self, screen, color):
        pygame.draw.rect(screen, color, self.rect)

# --- Ball Class ---
class Ball:
    def __init__(self):
        self.rect = pygame.Rect(WIDTH//2 - BALL_SIZE//2, HEIGHT//2 - BALL_SIZE//2, BALL_SIZE, BALL_SIZE)
        self.reset()

    def reset(self):
        self.rect.center = (WIDTH//2, HEIGHT//2)
        self.dx = BALL_SPEED * random.choice([-1, 1])
        self.dy = BALL_SPEED * random.choice([-1, 1])

    def move(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        # Top/Bottom
        if self.rect.top <= 0 or self.rect.bottom >= HEIGHT:
            self.dy = -self.dy

    def check_paddle(self, paddle):
        if self.rect.colliderect(paddle.rect):
            # Reflect and add random angle
            self.dx = -self.dx
            self.dy += random.randint(-2, 2)
            # Clamp to reasonable dy
            self.dy = max(min(self.dy, BALL_SPEED+3), -BALL_SPEED-3)
            # Prevent sticking
            if self.dx > 0:
                self.rect.right = paddle.rect.left
            else:
                self.rect.left = paddle.rect.right

    def draw(self, screen):
        pygame.draw.ellipse(screen, (255, 255, 100), self.rect)

# --- Pong Engine Class ---
class PongEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Pong Engine Deluxe")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 48)
        self.bigfont = pygame.font.SysFont(None, 72)
        self.state = GameState.MENU
        self.left_score = 0
        self.right_score = 0

        # Entities
        self.left_paddle = Paddle(20, HEIGHT//2 - PADDLE_HEIGHT//2, is_ai=False)
        self.right_paddle = Paddle(WIDTH - 40, HEIGHT//2 - PADDLE_HEIGHT//2, is_ai=True)
        self.ball = Ball()

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
        self.state = GameState.PLAY

    def run(self):
        while True:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                # Game state input handling
                if self.state == GameState.MENU:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            self.reset_game()
                elif self.state == GameState.GAME_OVER:
                    if event.type == pygame.KEYDOWN:
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
                # Paddle Controls
                mouse_y = pygame.mouse.get_pos()[1]
                self.left_paddle.move(mouse_y)
                self.right_paddle.move(self.ball.rect.centery)

                # Ball Movement
                self.ball.move()
                self.ball.check_paddle(self.left_paddle)
                self.ball.check_paddle(self.right_paddle)

                # Draw everything
                self.left_paddle.draw(self.screen, (200, 200, 255))
                self.right_paddle.draw(self.screen, (255, 180, 120))
                self.ball.draw(self.screen)
                pygame.draw.line(self.screen, (150,150,150), (WIDTH//2, 0), (WIDTH//2, HEIGHT), 4)

                # Scoreboard
                score_text = f"{self.left_score}    {self.right_score}"
                self.draw_text(score_text, 50)

                # Score detection
                if self.ball.rect.left <= 0:
                    self.right_score += 1
                    self.ball.reset()
                if self.ball.rect.right >= WIDTH:
                    self.left_score += 1
                    self.ball.reset()

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

# ==============================
# ===  RUN THE ENGINE!!!     ===
# ==============================
if __name__ == "__main__":
    PongEngine().run()

import asyncio
import platform
import pygame
import sys
import numpy as np

# Constants
FPS = 60
BLACK, WHITE = (0, 0, 0), (255, 255, 255)
MAX_SCORE = 5

# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 50)

# Sound Generation
def generate_sound(freq, duration_ms, sample_rate=44100):
    t = np.linspace(0, duration_ms / 1000, int(sample_rate * duration_ms / 1000), False)
    wave = 0.5 * np.sign(np.sin(2 * np.pi * freq * t))  # Square wave
    stereo = np.tile(wave[:, np.newaxis], (1, 2))  # Stereo array
    sound_array = (32767 * stereo).astype(np.int16)
    return pygame.sndarray.make_sound(np.ascontiguousarray(sound_array))

hit_sound = generate_sound(440, 100)  # Paddle hit
wall_sound = generate_sound(220, 100)  # Wall bounce
score_sound = generate_sound(330, 200)  # Score

# Classes
class Paddle(pygame.Rect):
    def __init__(self, x, y):
        super().__init__(x, y, 10, 80)
        self.base_width, self.base_height = 10, 80

    def move(self, y):
        self.centery = y
        self.top = max(self.top, 0)
        self.bottom = min(self.bottom, HEIGHT)

    def resize(self):
        scale = min(WIDTH / 640, HEIGHT / 480)
        self.width = int(self.base_width * scale)
        self.height = int(self.base_height * scale)

class Ball(pygame.Rect):
    def __init__(self):
        super().__init__(WIDTH // 2, HEIGHT // 2, 10, 10)
        self.base_size = 10
        self.vx, self.vy = 5, 5

    def update(self):
        self.x += self.vx
        self.y += self.vy

        if self.top <= 0 or self.bottom >= HEIGHT:
            self.vy = -self.vy
            wall_sound.play()

    def resize(self):
        scale = min(WIDTH / 640, HEIGHT / 480)
        self.width = self.height = int(self.base_size * scale)

# Game Loop
async def main():
    global screen, WIDTH, HEIGHT
    player = Paddle(20, HEIGHT // 2 - 40)
    enemy = Paddle(WIDTH - 30, HEIGHT // 2 - 40)
    ball = Ball()
    scores = [0, 0]

    while True:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.VIDEORESIZE:
                    WIDTH, HEIGHT = event.size
                    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                    player.resize()
                    enemy.resize()
                    ball.resize()
                    player.x, enemy.x = 20, WIDTH - 30
                    ball.center = (WIDTH // 2, HEIGHT // 2)

            # Player paddle follows mouse
            player.move(pygame.mouse.get_pos()[1])

            # Simple AI: move enemy paddle toward ball
            if ball.centery < enemy.centery:
                enemy.centery -= 5
            elif ball.centery > enemy.centery:
                enemy.centery += 5
            enemy.top = max(enemy.top, 0)
            enemy.bottom = min(enemy.bottom, HEIGHT)

            ball.update()

            # Paddle collision
            if ball.colliderect(player) or ball.colliderect(enemy):
                ball.vx = -ball.vx
                hit_sound.play()

            # Scoring
            if ball.left <= 0:
                scores[1] += 1  # AI scores
                score_sound.play()
                ball.center = (WIDTH // 2, HEIGHT // 2)
                ball.vx = -ball.vx
            elif ball.right >= WIDTH:
                scores[0] += 1  # Player scores
                score_sound.play()
                ball.center = (WIDTH // 2, HEIGHT // 2)
                ball.vx = -ball.vx

            # Render
            screen.fill(BLACK)
            pygame.draw.rect(screen, WHITE, player)
            pygame.draw.rect(screen, WHITE, enemy)
            pygame.draw.ellipse(screen, WHITE, ball)
            pygame.draw.aaline(screen, WHITE, (WIDTH // 2, 0), (WIDTH // 2, HEIGHT))

            score_text = font.render(f"{scores[0]}    {scores[1]}", True, WHITE)
            screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 20))

            # Game Over Check
            if scores[0] >= MAX_SCORE or scores[1] >= MAX_SCORE:
                winner = "YOU WIN!" if scores[0] > scores[1] else "AI WINS!"
                win_text = font.render(winner, True, WHITE)
                prompt_text = font.render("Play again? Y/N", True, WHITE)
                screen.blit(win_text, (WIDTH // 2 - win_text.get_width() // 2, HEIGHT // 2 - 50))
                screen.blit(prompt_text, (WIDTH // 2 - prompt_text.get_width() // 2, HEIGHT // 2 + 50))
                pygame.display.flip()

                waiting = True
                while waiting:
                    for event in pygame.event.get():
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_y:
                                scores = [0, 0]
                                ball.center = (WIDTH // 2, HEIGHT // 2)
                                ball.vx, ball.vy = 5, 5
                                running = False
                                waiting = False
                            elif event.key == pygame.K_n:
                                return
                        if event.type == pygame.QUIT:
                            return

            pygame.display.flip()
            clock.tick(FPS)
            await asyncio.sleep(1.0 / FPS)

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())

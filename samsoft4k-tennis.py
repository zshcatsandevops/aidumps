# samsoft_tennis_for_two_famicom_bleeps.py
import pygame, sys

pygame.init()
WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Samsoft Tennis for Two - Famicom Bleep Mode")

clock = pygame.time.Clock()

# Colors
BLACK   = (0, 0, 0)
WHITE   = (255, 255, 255)
RED     = (228, 0, 88)
GREEN   = (0, 192, 0)

# Ball
ball_x, ball_y = WIDTH//2, HEIGHT//2
ball_dx, ball_dy = 4, -4
ball_size = 12

# Paddles
paddle_w, paddle_h = 20, 80
paddle_left = pygame.Rect(40, HEIGHT//2 - paddle_h//2, paddle_w, paddle_h)
paddle_right = pygame.Rect(WIDTH-60, HEIGHT//2 - paddle_h//2, paddle_w, paddle_h)

# --- Sound setup ---
pygame.mixer.init()
def make_beep(freq=440, duration=100):
    sample_rate = 44100
    n_samples = int(round(duration * sample_rate / 1000))
    buf = bytearray()
    volume = 64
    for s in range(n_samples):
        t = int((s * freq * 2 / sample_rate) % 2) * volume - volume//2
        buf.extend(int(t).to_bytes(1, "little", signed=True))
    return pygame.mixer.Sound(buffer=buf)

bleep_wall = make_beep(880, 80)
bleep_paddle = make_beep(220, 120)
bleep_select = make_beep(660, 150)

# Reset ball
def reset_ball():
    global ball_x, ball_y, ball_dx, ball_dy
    ball_x, ball_y = WIDTH//2, HEIGHT//2
    ball_dx = 4 * (1 if pygame.time.get_ticks() % 2 == 0 else -1)
    ball_dy = -4

# Fonts
font_big = pygame.font.SysFont("Courier", 48, bold=True)
font_small = pygame.font.SysFont("Courier", 24, bold=True)

# --- Game states ---
MENU, HOWTO, PLAY = 0, 1, 2
state = MENU

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if state == MENU and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                bleep_select.play()
                state = PLAY
            elif event.key == pygame.K_h:
                bleep_select.play()
                state = HOWTO
        elif state == HOWTO and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                state = MENU

    if state == MENU:
        screen.fill(BLACK)
        title = font_big.render("SAMSOFT TENNIS", True, GREEN)
        subtitle = font_small.render("ENTER = Play   H = How to Play", True, WHITE)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//3))
        screen.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, HEIGHT//2))
        pygame.display.flip()
        clock.tick(60)

    elif state == HOWTO:
        screen.fill(BLACK)
        lines = [
            "HOW TO PLAY:",
            "- Use your MOUSE to move both paddles up/down",
            "- Keep the ball in play by bouncing it back",
            "- If the ball goes offscreen, it resets",
            "",
            "Press ESC or ENTER to return to Menu"
        ]
        for i, line in enumerate(lines):
            text = font_small.render(line, True, WHITE)
            screen.blit(text, (WIDTH//2 - text.get_width()//2, 100 + i*30))
        pygame.display.flip()
        clock.tick(60)

    elif state == PLAY:
        # Mouse controls both paddles
        mouse_y = pygame.mouse.get_pos()[1]
        paddle_left.y = mouse_y - paddle_h//2
        paddle_right.y = mouse_y - paddle_h//2

        # Ball movement
        ball_x += ball_dx
        ball_y += ball_dy

        if ball_y <= 0 or ball_y >= HEIGHT - ball_size:
            ball_dy *= -1
            bleep_wall.play()

        if paddle_left.collidepoint(ball_x, ball_y) or paddle_right.collidepoint(ball_x, ball_y):
            ball_dx *= -1
            bleep_paddle.play()

        if ball_x < 0 or ball_x > WIDTH:
            reset_ball()

        # Draw game
        screen.fill(BLACK)
        pygame.draw.rect(screen, WHITE, paddle_left)
        pygame.draw.rect(screen, WHITE, paddle_right)
        pygame.draw.rect(screen, GREEN, (ball_x, ball_y, ball_size, ball_size))
        pygame.draw.line(screen, RED, (WIDTH//2, 0), (WIDTH//2, HEIGHT), 2)

        pygame.display.flip()
        clock.tick(60)

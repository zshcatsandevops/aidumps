import asyncio
import platform
import pygame
import random

FPS = 60
pygame.init()

# Window setup
width, height = 800, 600
screen = pygame.display.set_mode((width, height), pygame.HWSURFACE | pygame.DOUBLEBUF)
pygame.display.set_caption("PONG - NES Edition with Win95 Sound")

# Global variables
player_paddle_y = 0
ai_paddle_y = 0
player2_paddle_y = 0
ball_x, ball_y = 0, 0
ball_prev_x, ball_prev_y = 0, 0
ball_speed_x, ball_speed_y = 0, 0
player_score = 0
ai_score = 0
game_state = "menu"
game_mode = None
player_score_text = None
ai_score_text = None
player_score_last = -1
ai_score_last = -1
last_paddle_hit = None
speed_multiplier = 1.0
clock = None

# NES colors
nes_black = (28, 28, 28)
nes_white = (200, 200, 200)
nes_gray = (100, 100, 100)
nes_red = (120, 0, 0)

# Paddle and ball dimensions
paddle_width, paddle_height = 15, 120
ball_size = 25

# Font
try:
    retro_font = pygame.font.Font("PressStart2P-Regular.ttf", 36)
except:
    retro_font = pygame.font.SysFont("Courier New", 36, bold=True)

# Menu text
menu_texts = {
    "title": retro_font.render("PONG", True, nes_white),
    "option1": retro_font.render("1P GAME", True, nes_white),
    "option2": retro_font.render("2P GAME", True, nes_white),
    "exit": retro_font.render("EXIT", True, nes_red)
}

# Sound channels
sound_channel_paddle = pygame.mixer.Channel(0)
sound_channel_wall = pygame.mixer.Channel(1)

# Sound function
def create_win95_sound(freq=440, duration=0.1, sample_rate=44100, wave_type="sawtooth", vibrato=False):
    import numpy as np
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    if wave_type == "sawtooth":
        wave = 0.5 * (2 * (t * freq - np.floor(t * freq + 0.5)))
    elif wave_type == "triangle":
        wave = 0.5 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5)))
    else:
        wave = 0.5 * np.sin(2 * np.pi * freq * t)
    if vibrato:
        vibrato_freq = 5
        vibrato_depth = 0.05
        wave *= np.sin(2 * np.pi * vibrato_freq * t) * vibrato_depth + 1
    attack = int(0.1 * len(t))
    decay = int(0.2 * len(t))
    sustain = int(0.6 * len(t))
    release = len(t) - attack - decay - sustain
    envelope = np.ones(len(t))
    envelope[:attack] = np.linspace(0, 1, attack)
    envelope[attack:attack+decay] = np.linspace(1, 0.7, decay)
    envelope[attack+decay:attack+decay+sustain] = 0.7
    envelope[-release:] = np.linspace(0.7, 0, release)
    wave *= envelope
    wave = (wave * 32767).astype(np.int16)
    stereo_wave = np.column_stack((wave, wave))
    stereo_wave = np.ascontiguousarray(stereo_wave)
    return pygame.sndarray.make_sound(stereo_wave)

# Sounds
hit_sound = create_win95_sound(1200, 0.02, wave_type="sawtooth")
wall_sound = create_win95_sound(400, 0.03, wave_type="triangle")
score_sound = create_win95_sound(800, 0.1, wave_type="sawtooth", vibrato=True)
menu_jingle = create_win95_sound(1400, 0.25, wave_type="triangle", vibrato=True)

def retro_setup():
    global player_paddle_y, ai_paddle_y, player2_paddle_y, ball_x, ball_y, ball_speed_x, ball_speed_y, player_score, ai_score, ball_prev_x, ball_prev_y, last_paddle_hit, speed_multiplier
    player_paddle_y = height // 2 - paddle_height // 2
    ai_paddle_y = height // 2 - paddle_height // 2
    player2_paddle_y = height // 2 - paddle_height // 2
    reset_ball()
    player_score = 0
    ai_score = 0
    last_paddle_hit = None
    speed_multiplier = 1.0
    update_score_text()

def reset_ball():
    global ball_x, ball_y, ball_speed_x, ball_speed_y, ball_prev_x, ball_prev_y, last_paddle_hit, speed_multiplier
    ball_x, ball_y = width // 2, height // 2
    ball_prev_x, ball_prev_y = ball_x, ball_y
    direction = random.choice([-1, 1])
    ball_speed_x = 4 * direction
    ball_speed_y = random.uniform(2, 4) * random.choice([-1, 1])
    last_paddle_hit = None
    speed_multiplier = 1.0
    sound_channel_paddle.play(score_sound)

def update_score_text():
    global player_score_text, ai_score_text, player_score_last, ai_score_last
    player_score_text = retro_font.render(str(player_score), True, nes_white)
    ai_score_text = retro_font.render(str(ai_score), True, nes_white)
    player_score_last = player_score
    ai_score_last = ai_score

def draw_dashed_line():
    dash_length = 30
    gap_length = 30
    segments = [(width // 2, y, width // 2, y + dash_length) for y in range(0, height, dash_length + gap_length)]
    for x1, y1, x2, y2 in segments:
        pygame.draw.line(screen, nes_gray, (x1, y1), (x2, y2), 4)

def check_paddle_collision(ball_rect, paddle_rect):
    return ball_rect.colliderect(paddle_rect)

def swept_aabb_collision(ball_prev_x, ball_prev_y, ball_x, ball_y, paddle_rect):
    min_x = min(ball_prev_x, ball_x)
    max_x = max(ball_prev_x, ball_x) + ball_size
    min_y = min(ball_prev_y, ball_y)
    max_y = max(ball_prev_y, ball_y) + ball_size
    swept_rect = pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)
    return swept_rect.colliderect(paddle_rect)

def update_loop():
    global player_paddle_y, ai_paddle_y, player2_paddle_y, ball_x, ball_y, ball_speed_x, ball_speed_y
    global player_score, ai_score, game_state, game_mode, ball_prev_x, ball_prev_y, last_paddle_hit, speed_multiplier

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        elif event.type == pygame.KEYDOWN:
            if game_state == "menu":
                if event.key == pygame.K_1:
                    game_mode = "single_player"
                    game_state = "single_player"
                    retro_setup()
                    sound_channel_paddle.play(menu_jingle)
                elif event.key == pygame.K_2:
                    game_mode = "two_player"
                    game_state = "two_player"
                    retro_setup()
                    sound_channel_paddle.play(menu_jingle)
                elif event.key == pygame.K_ESCAPE:
                    return False
            elif game_state == "game_over":
                if event.key == pygame.K_y:
                    retro_setup()
                    game_state = game_mode
                    sound_channel_paddle.play(menu_jingle)
                elif event.key == pygame.K_n:
                    return False
            elif event.key == pygame.K_p and game_state in ["single_player", "two_player"]:
                game_state = "paused"
                sound_channel_paddle.play(menu_jingle)
            elif event.key == pygame.K_p and game_state == "paused":
                game_state = game_mode
                sound_channel_paddle.play(menu_jingle)

    screen.fill(nes_black)

    if game_state == "menu":
        screen.blit(menu_texts["title"], (width // 2 - menu_texts["title"].get_width() // 2, height // 4))
        screen.blit(menu_texts["option1"], (width // 2 - menu_texts["option1"].get_width() // 2, height // 2))
        screen.blit(menu_texts["option2"], (width // 2 - menu_texts["option2"].get_width() // 2, height // 2 + 60))
        screen.blit(menu_texts["exit"], (width // 2 - menu_texts["exit"].get_width() // 2, height // 2 + 120))
        pygame.display.flip()
        return True

    if game_state == "paused":
        pause_text = retro_font.render("PAUSED", True, nes_white)
        screen.blit(pause_text, (width // 2 - pause_text.get_width() // 2, height // 2))
        pygame.display.flip()
        return True

    # Player 1 paddle (left)
    if game_state in ["single_player", "two_player"]:
        mouse_y = pygame.mouse.get_pos()[1]
        player_paddle_y = max(0, min(mouse_y - paddle_height // 2, height - paddle_height))

    # Player 2 or AI paddle (right)
    if game_state == "single_player":
        if ball_y > ai_paddle_y + paddle_height // 2:
            ai_paddle_y = min(ai_paddle_y + 3, height - paddle_height)
        elif ball_y < ai_paddle_y + paddle_height // 2:
            ai_paddle_y = max(ai_paddle_y - 3, 0)
    elif game_state == "two_player":
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            player2_paddle_y = max(player2_paddle_y - 5, 0)
        if keys[pygame.K_s]:
            player2_paddle_y = min(player2_paddle_y + 5, height - paddle_height)

    # Ball movement
    ball_prev_x, ball_prev_y = ball_x, ball_y
    next_ball_x = ball_x + ball_speed_x * speed_multiplier
    next_ball_y = ball_y + ball_speed_y * speed_multiplier

    # Cap speeds
    max_speed = 6
    ball_speed_x = max(-max_speed, min(max_speed, ball_speed_x))
    ball_speed_y = max(-max_speed, min(max_speed, ball_speed_y))

    # Wall collisions
    if next_ball_y <= 0:
        ball_speed_y = abs(ball_speed_y)
        next_ball_y = 0
        sound_channel_wall.play(wall_sound)
    elif next_ball_y >= height - ball_size:
        ball_speed_y = -abs(ball_speed_y)
        next_ball_y = height - ball_size
        sound_channel_wall.play(wall_sound)

    # Paddle collisions
    ball_rect = pygame.Rect(next_ball_x, next_ball_y, ball_size, ball_size)
    player_paddle_rect = pygame.Rect(0, player_paddle_y, paddle_width, paddle_height)
    ai_paddle_rect = pygame.Rect(width - paddle_width, ai_paddle_y, paddle_width, paddle_height)
    player2_paddle_rect = pygame.Rect(width - paddle_width, player2_paddle_y, paddle_width, paddle_height)

    hit = False
    if check_paddle_collision(ball_rect, player_paddle_rect) and last_paddle_hit != "player":
        ball_speed_x = abs(ball_speed_x)
        ball_speed_y = random.uniform(2, 3) * random.choice([-1, 1])
        ball_x = paddle_width + 1
        ball_y = next_ball_y
        speed_multiplier = min(speed_multiplier + 0.1, 1.5)
        last_paddle_hit = "player"
        sound_channel_paddle.play(hit_sound)
        hit = True
    elif check_paddle_collision(ball_rect, ai_paddle_rect if game_state == "single_player" else player2_paddle_rect) and last_paddle_hit != "opponent":
        ball_speed_x = -abs(ball_speed_x)
        ball_speed_y = random.uniform(2, 3) * random.choice([-1, 1])
        ball_x = width - paddle_width - ball_size - 1
        ball_y = next_ball_y
        speed_multiplier = min(speed_multiplier + 0.1, 1.5)
        last_paddle_hit = "opponent"
        sound_channel_paddle.play(hit_sound)
        hit = True
    elif not hit:
        if swept_aabb_collision(ball_prev_x, ball_prev_y, next_ball_x, next_ball_y, player_paddle_rect) and last_paddle_hit != "player":
            ball_speed_x = abs(ball_speed_x)
            ball_speed_y = random.uniform(2, 3) * random.choice([-1, 1])
            ball_x = paddle_width + 1
            ball_y = next_ball_y
            speed_multiplier = min(speed_multiplier + 0.1, 1.5)
            last_paddle_hit = "player"
            sound_channel_paddle.play(hit_sound)
            hit = True
        elif swept_aabb_collision(ball_prev_x, ball_prev_y, next_ball_x, next_ball_y, ai_paddle_rect if game_state == "single_player" else player2_paddle_rect) and last_paddle_hit != "opponent":
            ball_speed_x = -abs(ball_speed_x)
            ball_speed_y = random.uniform(2, 3) * random.choice([-1, 1])
            ball_x = width - paddle_width - ball_size - 1
            ball_y = next_ball_y
            speed_multiplier = min(speed_multiplier + 0.1, 1.5)
            last_paddle_hit = "opponent"
            sound_channel_paddle.play(hit_sound)
            hit = True

    # Update ball position if no paddle collision
    if not hit:
        ball_x = next_ball_x
        ball_y = next_ball_y
        last_paddle_hit = None

    # Scoring
    if ball_x < 0:
        ai_score += 1
        update_score_text()
        reset_ball()
    elif ball_x > width:
        player_score += 1
        update_score_text()
        reset_ball()

    # Game over check
    if player_score >= 7 or ai_score >= 7:
        game_state = "game_over"
        screen.fill(nes_black)
        if player_score > ai_score:
            winner = "PLAYER 1"
        elif ai_score > player_score:
            winner = "PLAYER 2" if game_mode == "two_player" else "AI"
        else:
            winner = "TIE"
        game_over_text = retro_font.render(f"{winner} WINS!", True, nes_white)
        instruction_text = retro_font.render("PLAY AGAIN? Y/N", True, nes_red)
        screen.blit(game_over_text, (width // 2 - game_over_text.get_width() // 2, height // 2 - 50))
        screen.blit(instruction_text, (width // 2 - instruction_text.get_width() // 2, height // 2 + 50))
        pygame.display.flip()
        return True

    # Drawing
    pygame.draw.rect(screen, nes_white, (0, player_paddle_y, paddle_width, paddle_height))
    if game_state == "single_player":
        pygame.draw.rect(screen, nes_white, (width - paddle_width, ai_paddle_y, paddle_width, paddle_height))
    elif game_state == "two_player":
        pygame.draw.rect(screen, nes_white, (width - paddle_width, player2_paddle_y, paddle_width, paddle_height))
    pygame.draw.rect(screen, nes_white, (ball_x, ball_y, ball_size, ball_size))
    draw_dashed_line()
    screen.blit(player_score_text, (width // 4, 20))
    screen.blit(ai_score_text, (3 * width // 4, 20))

    pygame.display.flip()
    return True

async def main():
    global clock
    retro_setup()
    clock = pygame.time.Clock()
    running = True
    while running:
        running = update_loop()
        clock.tick(FPS)
        await asyncio.sleep(0)
        if platform.system() == "Emscripten":
            pygame.event.clear()

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())

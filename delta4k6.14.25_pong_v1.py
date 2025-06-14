import asyncio
import platform
import pygame
import numpy as np

FPS = 60
pygame.init()

# Window setup
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("PONG - NES Edition with Win95 Sound")

# NES-inspired color palette
nes_black = (28, 28, 28)  # Dark gray for background
nes_white = (200, 200, 200)  # Off-white for elements
nes_gray = (100, 100, 100)  # Muted gray for accents
nes_red = (120, 0, 0)  # Muted red for highlights

# Paddle and ball dimensions (larger for pixelated look)
paddle_width, paddle_height = 15, 120
ball_size = 25

# Initial positions
player_paddle_y = height // 2 - paddle_height // 2
ai_paddle_y = height // 2 - paddle_height // 2
player2_paddle_y = height // 2 - paddle_height // 2
ball_x, ball_y = width // 2, height // 2
ball_speed_x, ball_speed_y = 4, 4  # Slower for NES feel

# Scores
player_score = 0
ai_score = 0

# Game state and mode
game_state = "menu"
game_mode = None  # Track single_player or two_player

# Retro font (simulate NES bitmap font)
try:
    retro_font = pygame.font.Font("PressStart2P-Regular.ttf", 36)  # Download from dafont.com
except:
    retro_font = pygame.font.Font(None, 50)  # Fallback

# Generate Windows 95-style MIDI-like sound effects
def create_win95_sound(freq=440, duration=0.1, sample_rate=44100, wave_type="sawtooth", vibrato=False):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # Waveform selection
    if wave_type == "sawtooth":
        wave = 0.5 * (2 * (t * freq - np.floor(t * freq + 0.5)))  # Sawtooth wave
    elif wave_type == "triangle":
        wave = 0.5 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5)))  # Triangle wave
    else:
        wave = 0.5 * np.sin(2 * np.pi * freq * t)  # Fallback to sine
    
    # Apply vibrato (pitch modulation) if enabled
    if vibrato:
        vibrato_freq = 5  # Hz
        vibrato_depth = 0.05  # Slight pitch variation
        wave *= np.sin(2 * np.pi * vibrato_freq * t) * vibrato_depth + 1
    
    # Apply simple ADSR envelope (attack: 10%, decay: 20%, sustain: 60%, release: 10%)
    attack = int(0.1 * len(t))
    decay = int(0.2 * len(t))
    sustain = int(0.6 * len(t))
    release = len(t) - attack - decay - sustain
    envelope = np.ones(len(t))
    envelope[:attack] = np.linspace(0, 1, attack)  # Attack
    envelope[attack:attack+decay] = np.linspace(1, 0.7, decay)  # Decay to sustain
    envelope[attack+decay:attack+decay+sustain] = 0.7  # Sustain
    envelope[-release:] = np.linspace(0.7, 0, release)  # Release
    wave *= envelope
    
    wave = (wave * 32767).astype(np.int16)
    stereo_wave = np.column_stack((wave, wave))
    stereo_wave = np.ascontiguousarray(stereo_wave)
    return pygame.sndarray.make_sound(stereo_wave)

# Windows 95-inspired sounds
hit_sound = create_win95_sound(1200, 0.02, wave_type="sawtooth")  # Bright blip for paddle hits
wall_sound = create_win95_sound(400, 0.03, wave_type="triangle")  # Soft boop for wall hits
score_sound = create_win95_sound(800, 0.1, wave_type="sawtooth", vibrato=True)  # Celebratory note
menu_jingle = create_win95_sound(1400, 0.25, wave_type="triangle", vibrato=True)  # Menu chime

def retro_setup():
    global player_paddle_y, ai_paddle_y, player2_paddle_y, ball_x, ball_y, ball_speed_x, ball_speed_y, player_score, ai_score
    player_paddle_y = height // 2 - paddle_height // 2
    ai_paddle_y = height // 2 - paddle_height // 2
    player2_paddle_y = height // 2 - paddle_height // 2
    ball_x, ball_y = width // 2, height // 2
    ball_speed_x, ball_speed_y = 4, 4
    player_score = 0
    ai_score = 0

def draw_dashed_line():
    dash_length = 30
    gap_length = 30
    y = 0
    while y < height:
        pygame.draw.line(screen, nes_gray, (width // 2, y), (width // 2, y + dash_length), 4)
        y += dash_length + gap_length

def update_loop():
    global player_paddle_y, ai_paddle_y, player2_paddle_y, ball_x, ball_y, ball_speed_x, ball_speed_y
    global player_score, ai_score, game_state, game_mode

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        elif event.type == pygame.KEYDOWN:
            if game_state == "menu":
                if event.key == pygame.K_1:
                    game_mode = "single_player"
                    game_state = "single_player"
                    retro_setup()
                    menu_jingle.play()
                elif event.key == pygame.K_2:
                    game_mode = "two_player"
                    game_state = "two_player"
                    retro_setup()
                    menu_jingle.play()
                elif event.key == pygame.K_ESCAPE:
                    return False
            elif game_state == "game_over":
                if event.key == pygame.K_y:
                    retro_setup()
                    game_state = game_mode
                    menu_jingle.play()
                elif event.key == pygame.K_n:
                    return False

    screen.fill(nes_black)

    if game_state == "menu":
        title_text = retro_font.render("PONG", True, nes_white)
        screen.blit(title_text, (width // 2 - title_text.get_width() // 2, height // 4))
        option1_text = retro_font.render("1P GAME", True, nes_white)
        option2_text = retro_font.render("2P GAME", True, nes_white)
        exit_text = retro_font.render("EXIT", True, nes_red)
        screen.blit(option1_text, (width // 2 - option1_text.get_width() // 2, height // 2))
        screen.blit(option2_text, (width // 2 - option2_text.get_width() // 2, height // 2 + 60))
        screen.blit(exit_text, (width // 2 - exit_text.get_width() // 2, height // 2 + 120))
        pygame.display.flip()
        return True

    # Player 1 paddle (left)
    if game_state in ["single_player", "two_player"]:
        mouse_y = pygame.mouse.get_pos()[1]
        player_paddle_y = max(0, min(mouse_y - paddle_height // 2, height - paddle_height))

    # Player 2 or AI paddle (right)
    if game_state == "single_player":
        if ball_y > ai_paddle_y + paddle_height // 2:
            ai_paddle_y = min(ai_paddle_y + 3, height - paddle_height)  # Slower AI
        elif ball_y < ai_paddle_y + paddle_height // 2:
            ai_paddle_y = max(ai_paddle_y - 3, 0)
    elif game_state == "two_player":
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            player2_paddle_y = max(player2_paddle_y - 5, 0)
        if keys[pygame.K_s]:
            player2_paddle_y = min(player2_paddle_y + 5, height - paddle_height)

    # Ball movement
    ball_x += ball_speed_x
    ball_y += ball_speed_y

    # Wall collisions
    if ball_y <= 0 or ball_y >= height - ball_size:
        ball_speed_y = -ball_speed_y
        wall_sound.play()

    # Paddle collisions (improved hitbox detection)
    if ball_x + ball_size >= 0 and ball_x <= paddle_width and player_paddle_y <= ball_y + ball_size and ball_y <= player_paddle_y + paddle_height:
        ball_speed_x = -ball_speed_x
        ball_speed_y = np.random.uniform(-3, 3)  # Random but limited angle
        hit_sound.play()
    elif ball_x <= width - paddle_width and ball_x + ball_size >= width - paddle_width:
        if game_state == "single_player" and ai_paddle_y <= ball_y + ball_size and ball_y <= ai_paddle_y + paddle_height:
            ball_speed_x = -ball_speed_x
            ball_speed_y = np.random.uniform(-3, 3)
            hit_sound.play()
        elif game_state == "two_player" and player2_paddle_y <= ball_y + ball_size and ball_y <= player2_paddle_y + paddle_height:
            ball_speed_x = -ball_speed_x
            ball_speed_y = np.random.uniform(-3, 3)
            hit_sound.play()

    # Scoring
    if ball_x < 0:
        ai_score += 1
        ball_x, ball_y = width // 2, height // 2
        ball_speed_x, ball_speed_y = 4, 4
        score_sound.play()
    elif ball_x > width:
        player_score += 1
        ball_x, ball_y = width // 2, height // 2
        ball_speed_x, ball_speed_y = -4, 4
        score_sound.play()

    # Game over check (both players reach 5)
    if player_score >= 5 and ai_score >= 5:
        game_state = "game_over"
        screen.fill(nes_black)
        game_over_text = retro_font.render("GAME OVER", True, nes_white)
        screen.blit(game_over_text, (width // 2 - game_over_text.get_width() // 2, height // 2 - 50))
        instruction_text = retro_font.render("GAME OVER Y/N", True, nes_red)
        screen.blit(instruction_text, (width // 2 - instruction_text.get_width() // 2, height // 2 + 50))
        pygame.display.flip()
        return True

    # Drawing with pixelated style
    pygame.draw.rect(screen, nes_white, (0, player_paddle_y, paddle_width, paddle_height))
    if game_state == "single_player":
        pygame.draw.rect(screen, nes_white, (width - paddle_width, ai_paddle_y, paddle_width, paddle_height))
    elif game_state == "two_player":
        pygame.draw.rect(screen, nes_white, (width - paddle_width, player2_paddle_y, paddle_width, paddle_height))
    pygame.draw.rect(screen, nes_white, (ball_x, ball_y, ball_size, ball_size))
    draw_dashed_line()
    player_text = retro_font.render(str(player_score), True, nes_white)
    ai_text = retro_font.render(str(ai_score), True, nes_white)
    screen.blit(player_text, (width // 4, 20))
    screen.blit(ai_text, (3 * width // 4, 20))

    pygame.display.flip()
    return True

async def main():
    retro_setup()
    running = True
    while running:
        running = update_loop()
        await asyncio.sleep(1.0 / FPS)

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())d

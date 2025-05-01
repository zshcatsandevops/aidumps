import pygame
import numpy as np
import time

# Initialize Pygame and mixer
pygame.init()
try:
    pygame.mixer.init()
    mixer_works = True
except pygame.error as e:
    print(f"Meow! Pygame mixer failed to initialize: {e}. Sound will be disabled.")
    mixer_works = False

# Window setup
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("DELTA MARIO LAND")

# Colors for GameBoy filter
BACKGROUND_COLOR = (0, 64, 0)
PLATFORM_COLOR = (0, 128, 0)
MARIO_COLOR = (0, 192, 0)
ENEMY_COLOR = (0, 128, 0)
COIN_COLOR = (0, 255, 0)
GOAL_COLOR = (0, 255, 0)
TEXT_COLOR = (0, 255, 0)

# Mario properties
mario_x, mario_y = 100, HEIGHT - 50 - 30
mario_width, mario_height = 20, 30
mario_vel_x, mario_vel_y = 0, 0
is_jumping = False
on_ground = True
gravity = 0.4
jump_strength = -10

# Game objects
platforms = []
enemies = []
coins = []
goal = {}
score = 0

# Font for score and menu
try:
    font = pygame.font.Font(None, 36)
except FileNotFoundError:
    font = pygame.font.SysFont(None, 36)

# Sound Engine class
class SoundEngine:
    def __init__(self):
        self.sounds = {}
        if not mixer_works:
            print("Sound Engine: Mixer not available. Sounds disabled.")
            return
        self.sample_rate = pygame.mixer.get_init()[0]
        if not self.sample_rate:
            self.sample_rate = 44100
            print("Warning: Pygame mixer sample rate not found, using default 44100.")

    def generate_square_wave(self, frequency, duration, amplitude=8000):
        if not mixer_works or not self.sample_rate:
            return None
        num_samples = int(self.sample_rate * duration)
        if num_samples <= 0:
            return None
        t = np.linspace(0, duration, num_samples, endpoint=False)
        wave = amplitude * np.sign(np.sin(2 * np.pi * frequency * t))
        envelope = np.linspace(1.0, 0.0, num_samples)
        wave *= envelope
        samples = wave.astype(np.int16)
        stereo_samples = np.column_stack((samples, samples))
        if stereo_samples.size == 0:
            return None
        try:
            sound = pygame.mixer.Sound(buffer=stereo_samples)
            return sound
        except Exception as e:
            print(f"Meow! Error making sound (Freq: {frequency}): {e}")
            return None

    def load_sounds(self):
        if not mixer_works:
            return
        self.sounds["jump"] = self.generate_square_wave(660, 0.12)
        self.sounds["coin"] = self.generate_square_wave(1046, 0.08)
        self.sounds["enemy"] = self.generate_square_wave(330, 0.15)
        self.sounds["hit"] = self.generate_square_wave(220, 0.25)
        self.sounds["goal"] = self.generate_square_wave(880, 0.4)
        self.sounds["game_over"] = self.generate_square_wave(110, 0.6)

    def play(self, sound_name):
        if not mixer_works:
            return
        if sound_name in self.sounds and self.sounds[sound_name]:
            self.sounds[sound_name].play()

# Initialize sound engine
sound_engine = SoundEngine()
sound_engine.load_sounds()

# Clock for FPS limiting
clock = pygame.time.Clock()
FPS = 60

# --- LEVELS ---
levels = [
    # Level 1
    {
        "platforms": [
            {"x": 0, "y": HEIGHT - 20, "width": WIDTH, "height": 20},
            {"x": 200, "y": 400, "width": 100, "height": 20},
            {"x": 400, "y": 300, "width": 100, "height": 20}
        ],
        "enemies": [
            {"x": 300, "y": HEIGHT - 20 - 20, "width": 20, "height": 20, "vel": 1.5}
        ],
        "coins": [
            {"x": 250, "y": 350, "radius": 10},
            {"x": 450, "y": 250, "radius": 10}
        ],
        "goal": {"x": 700, "y": HEIGHT - 20 - 50, "width": 20, "height": 50}
    },
    # Level 2
    {
        "platforms": [
            {"x": 0, "y": HEIGHT - 20, "width": WIDTH, "height": 20},
            {"x": 150, "y": 450, "width": 100, "height": 20},
            {"x": 350, "y": 350, "width": 100, "height": 20},
            {"x": 550, "y": 250, "width": 100, "height": 20}
        ],
        "enemies": [
            {"x": 200, "y": HEIGHT - 20 - 20, "width": 20, "height": 20, "vel": 2},
            {"x": 400, "y": 350 - 20, "width": 20, "height": 20, "vel": -2}
        ],
        "coins": [
            {"x": 180, "y": 400, "radius": 10},
            {"x": 380, "y": 300, "radius": 10},
            {"x": 580, "y": 200, "radius": 10}
        ],
        "goal": {"x": 700, "y": HEIGHT - 20 - 50, "width": 20, "height": 50}
    },
    # Level 3
    {
        "platforms": [
            {"x": 0, "y": HEIGHT - 20, "width": WIDTH, "height": 20},
            {"x": 100, "y": 500, "width": 150, "height": 20},
            {"x": 300, "y": 400, "width": 150, "height": 20},
            {"x": 500, "y": 300, "width": 150, "height": 20}
        ],
        "enemies": [
            {"x": 150, "y": HEIGHT - 20 - 20, "width": 20, "height": 20, "vel": 2},
            {"x": 350, "y": 400 - 20, "width": 20, "height": 20, "vel": -2},
            {"x": 550, "y": 300 - 20, "width": 20, "height": 20, "vel": 2}
        ],
        "coins": [
            {"x": 130, "y": 450, "radius": 10},
            {"x": 330, "y": 350, "radius": 10},
            {"x": 530, "y": 250, "radius": 10}
        ],
        "goal": {"x": 700, "y": HEIGHT - 20 - 50, "width": 20, "height": 50}
    },
    # Level 4
    {
        "platforms": [
            {"x": 0, "y": HEIGHT - 20, "width": WIDTH, "height": 20},
            {"x": 250, "y": 450, "width": 100, "height": 20},
            {"x": 450, "y": 350, "width": 100, "height": 20},
            {"x": 650, "y": 250, "width": 100, "height": 20}
        ],
        "enemies": [
            {"x": 300, "y": HEIGHT - 20 - 20, "width": 20, "height": 20, "vel": 2.5},
            {"x": 500, "y": 350 - 20, "width": 20, "height": 20, "vel": -2.5},
            {"x": 700, "y": 250 - 20, "width": 20, "height": 20, "vel": 2.5}
        ],
        "coins": [
            {"x": 280, "y": 400, "radius": 10},
            {"x": 480, "y": 300, "radius": 10},
            {"x": 680, "y": 200, "radius": 10}
        ],
        "goal": {"x": 750, "y": HEIGHT - 20 - 50, "width": 20, "height": 50}
    },
    # Level 5
    {
        "platforms": [
            {"x": 0, "y": HEIGHT - 20, "width": WIDTH, "height": 20},
            {"x": 100, "y": 400, "width": 100, "height": 20},
            {"x": 300, "y": 300, "width": 100, "height": 20},
            {"x": 500, "y": 200, "width": 100, "height": 20},
        ],
        "enemies": [
            {"x": 150, "y": HEIGHT - 20 - 20, "width": 20, "height": 20, "vel": 3},
            {"x": 350, "y": 300 - 20, "width": 20, "height": 20, "vel": -3},
            {"x": 550, "y": 200 - 20, "width": 20, "height": 20, "vel": 3},
        ],
        "coins": [
            {"x": 130, "y": 350, "radius": 10},
            {"x": 330, "y": 250, "radius": 10},
            {"x": 530, "y": 150, "radius": 10},
        ],
        "goal": {"x": 750, "y": HEIGHT - 20 - 50, "width": 20, "height": 50}
    }
]

# Game state
game_state = "menu"
current_level = 0

def load_level(level_index):
    global platforms, enemies, coins, goal
    global mario_x, mario_y, mario_vel_x, mario_vel_y, is_jumping, on_ground
    if level_index >= len(levels):
        print("Meow! No more levels! Returning to menu.")
        return False
    level = levels[level_index]
    platforms = level["platforms"]
    enemies = [e.copy() for e in level["enemies"]]
    coins = [c.copy() for c in level["coins"]]
    goal = level["goal"]
    mario_x = 100
    ground_y = HEIGHT
    if platforms:
        ground_y = platforms[0]['y']
    mario_y = ground_y - mario_height
    mario_vel_x = 0
    mario_vel_y = 0
    is_jumping = False
    on_ground = True
    print(f"Purrrr... Loaded Level {level_index + 1}")
    return True

def trigger_game_over():
    global game_state, score, current_level
    print("Game Over, meow...")
    sound_engine.play("game_over")
    game_state = "menu"
    current_level = 0

def update():
    global mario_x, mario_y, mario_vel_x, mario_vel_y, is_jumping, on_ground
    global score, game_state, current_level
    global enemies, coins
    mario_x += mario_vel_x
    if mario_x < 0:
        mario_x = 0
    elif mario_x + mario_width > WIDTH:
        mario_x = WIDTH - mario_width
    mario_vel_y += gravity
    max_fall_speed = 15
    if mario_vel_y > max_fall_speed:
        mario_vel_y = max_fall_speed
    mario_y += mario_vel_y
    on_ground = False
    mario_rect = pygame.Rect(mario_x, mario_y, mario_width, mario_height)
    for p in platforms:
        platform_rect = pygame.Rect(p["x"], p["y"], p["width"], p["height"])
        if mario_rect.colliderect(platform_rect):
            if mario_vel_y > 0 and (mario_rect.bottom - mario_vel_y) <= platform_rect.top + 1:
                mario_y = platform_rect.top - mario_height
                mario_vel_y = 0
                is_jumping = False
                on_ground = True
                break
            elif mario_vel_y < 0 and (mario_rect.top - mario_vel_y) >= platform_rect.bottom - 1:
                mario_y = platform_rect.bottom
                mario_vel_y = 0
                break
    mario_rect_check = pygame.Rect(mario_x, mario_y, mario_width, mario_height)
    for e in enemies[:]:
        e["x"] += e["vel"]
        if e["x"] <= 0 or e["x"] + e["width"] >= WIDTH:
            e["vel"] *= -1
        enemy_rect = pygame.Rect(e["x"], e["y"], e["width"], e["height"])
        if mario_rect_check.colliderect(enemy_rect):
            if mario_vel_y > 0 and mario_rect_check.bottom < enemy_rect.centery + 5:
                enemies.remove(e)
                mario_vel_y = jump_strength * 0.6
                is_jumping = True
                on_ground = False
                score += 5
                sound_engine.play("enemy")
            else:
                sound_engine.play("hit")
                trigger_game_over()
                return
    for c in coins[:]:
        mario_center_x = mario_rect_check.centerx
        mario_center_y = mario_rect_check.centery
        dist_sq = (mario_center_x - c["x"])**2 + (mario_center_y - c["y"])**2
        radii_sum_sq = (c["radius"] + max(mario_width, mario_height) / 2)**2
        if dist_sq < radii_sum_sq:
            coins.remove(c)
            score += 1
            sound_engine.play("coin")
    goal_rect = pygame.Rect(goal["x"], goal["y"], goal["width"], goal["height"])
    if mario_rect_check.colliderect(goal_rect):
        print("Level Complete, mrow!")
        sound_engine.play("goal")
        pygame.time.wait(100)
        current_level += 1
        if not load_level(current_level):
            game_state = "menu"
            current_level = 0
            score = 0
        return
    if mario_y > HEIGHT + mario_height:
        trigger_game_over()
        return

def draw():
    screen.fill(BACKGROUND_COLOR)
    for p in platforms:
        pygame.draw.rect(screen, PLATFORM_COLOR, (p["x"], p["y"], p["width"], p["height"]))
    for e in enemies:
        pygame.draw.rect(screen, ENEMY_COLOR, (int(e["x"]), int(e["y"]), e["width"], e["height"]))
    for c in coins:
        pygame.draw.circle(screen, COIN_COLOR, (int(c["x"]), int(c["y"])), c["radius"])
    pygame.draw.rect(screen, GOAL_COLOR, (goal["x"], goal["y"], goal["width"], goal["height"]))
    pygame.draw.rect(screen, MARIO_COLOR, (int(mario_x), int(mario_y), mario_width, mario_height))
    score_text = font.render(f"Score: {score}", True, TEXT_COLOR)
    screen.blit(score_text, (10, 10))
    level_text = font.render(f"Level: {current_level + 1}", True, TEXT_COLOR)
    screen.blit(level_text, (WIDTH - level_text.get_width() - 10, 10))

def setup():
    global on_ground, game_state, current_level, score
    pygame.display.set_caption("DELTA MARIO LAND - Purrfect Version!")
    print("Nya! Setting up the game...")
    game_state = "menu"
    current_level = 0
    score = 0
    on_ground = True
    if not load_level(0):
        print("Meow! Failed to load initial level!")
        pygame.quit()
        exit()

# --- Main Game Loop ---
def main():
    global game_state, current_level, score, on_ground
    global mario_vel_x, mario_vel_y, is_jumping
    setup()
    running = True
    while running:
        # --- Menu State ---
        if game_state == "menu":
            screen.fill(BACKGROUND_COLOR)
            title_text = font.render("DELTA MARIO LAND", True, TEXT_COLOR)
            start_text = font.render("Press SPACE to Start!", True, TEXT_COLOR)
            quit_text = font.render("Press ESC to Quit", True, TEXT_COLOR)
            screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 2 - 60))
            screen.blit(start_text, (WIDTH // 2 - start_text.get_width() // 2, HEIGHT // 2 + 0))
            screen.blit(quit_text, (WIDTH // 2 - quit_text.get_width() // 2, HEIGHT // 2 + 40))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        print("Starting game, meow!")
                        game_state = "playing"
                        current_level = 0
                        score = 0
                        if not load_level(current_level):
                            print("ERROR starting game - couldn't load level 0!")
                            running = False
                    elif event.key == pygame.K_ESCAPE:
                        running = False
            pygame.display.flip()
        elif game_state == "playing":
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                mario_vel_x = -4
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                mario_vel_x = 4
            else:
                mario_vel_x = 0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if (event.key == pygame.K_SPACE or event.key == pygame.K_UP or event.key == pygame.K_w) and on_ground:
                        mario_vel_y = jump_strength
                        is_jumping = True
                        on_ground = False
                        sound_engine.play("jump")
                    elif event.key == pygame.K_ESCAPE:
                        trigger_game_over()
            if game_state == "playing":
                update()
            draw()
            pygame.display.flip()
        clock.tick(FPS)
    print("Quitting game, bye bye meow! :3")
    pygame.quit()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nNya! Game interrupted by user!")
    finally:
        if pygame.get_init():
            pygame.quit()

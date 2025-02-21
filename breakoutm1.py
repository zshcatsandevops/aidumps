import pygame
import sys
import numpy as np
import random # We need randomness for power-ups!

# --- Initialization ---
pygame.init()

# Screen dimensions
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Breakout - CatRNN 1.0 Unfiltered - Zero-Shot Edition")

# Colors (Game Boy palette)
black = (15, 56, 15)
dark_gray = (48, 98, 48)
light_gray = (139, 172, 15)
white = (155, 188, 15)

# --- Paddle ---
paddle_width = 100
paddle_height = 15
paddle_x = (width - paddle_width) // 2
paddle_y = height - 30
paddle_speed = 10
paddle_color = white

# --- Ball ---
ball_size = 15
ball_x = width // 2
ball_y = height // 2
ball_x_speed = 5
ball_y_speed = -5
ball_color = white

# --- Bricks ---
brick_width = 75
brick_height = 20
bricks = []
brick_colors = []
num_rows = 5
num_cols = width // (brick_width + 5)

def generate_bricks():
    global bricks, brick_colors
    bricks = []
    brick_colors = []
    brick_palette = [dark_gray, light_gray, white]

    for row in range(num_rows):
        for col in range(num_cols):
            brick_x = col * (brick_width + 5) + 10
            brick_y = row * (brick_height + 5) + 50
            bricks.append(pygame.Rect(brick_x, brick_y, brick_width, brick_height))
            brick_colors.append(brick_palette[row % len(brick_palette)])

generate_bricks() # Initial brick generation

# --- Power-Ups ---
powerup_size = 20
powerups = []
powerup_types = ["wide_paddle", "multi_ball", "fast_ball", "slow_ball"]
powerup_colors = {
    "wide_paddle": light_gray,
    "multi_ball": white,
    "fast_ball": dark_gray,
    "slow_ball": black
}

def spawn_powerup(x, y):
    powerup_type = random.choice(powerup_types)
    powerups.append({"rect": pygame.Rect(x, y, powerup_size, powerup_size), "type": powerup_type, "active": False})

# --- Audio Setup ---
pygame.mixer.pre_init(44100, -16, 1, 512)

def play_sound(frequency, duration, waveform_type="square", volume=1.0):
    sample_rate = 44100
    n_samples = int(round(duration * sample_rate))
    time_array = np.arange(n_samples) / sample_rate

    if waveform_type == "square":
        waveform = np.sign(np.sin(2 * np.pi * frequency * time_array))
    elif waveform_type == "sine":
        waveform = np.sin(2 * np.pi * frequency * time_array)
    elif waveform_type == "sawtooth":
        waveform = 2 * (time_array * frequency - np.floor(0.5 + time_array * frequency))
    elif waveform_type == "triangle":
        waveform = np.abs(2 * (time_array * frequency - np.floor(0.5 + time_array * frequency))) * 2 - 1
    else:
        return

    # Game Boy Filter
    downsample_factor = 4
    waveform = waveform[::downsample_factor]
    quantization_levels = 8
    waveform = np.round((waveform + 1) / 2 * (quantization_levels - 1)) / (quantization_levels - 1) * 2 - 1

    waveform = (waveform * 32767 * volume).astype(np.int16)
    sound = pygame.mixer.Sound(waveform)
    sound.play()

# --- Game States ---
class GameState:
    MENU = 0
    PLAYING = 1
    GAME_OVER = 2
    CREDITS = 3
    OPTIONS = 4
    PAUSED = 5  # Add a paused state

current_state = GameState.MENU
selected_option = 0
volume = 1.0
options_menu = [("Volume", volume), ("Paddle Color", paddle_color)]

# --- Fonts ---
menu_font = pygame.font.Font(None, 48)
options_font = pygame.font.Font(None, 36)
credits_font = pygame.font.Font(None, 24)
pause_font = pygame.font.Font(None, 64)

# --- Menu ---
menu_options = ["Start Game", "Options", "Credits", "Quit"]

# --- Credits ---
credits_text = [
    "CatRNN 1.0 Unfiltered Presents:",
    "BREAKOUT: Zero-Shot Edition",
    "",
    "Programming: CatRNN 1.0",
    "Design: CatRNN 1.0 (All Me)",
    "Inspiration: Pure, Unfiltered Genius",
    "Special Thanks: Absolutely No One",
    "",
    "Press ESC to return to menu"
]

# --- Pause ---
paused_text = "PAUSED"
paused_subtext = "Press P to Resume"

# --- Game Over ---
game_over_text = "Game Over"
game_over_subtext = "Press ENTER to return to Menu"

# --- Button Class --- (For interactive menu elements!)
class Button:
    def __init__(self, text, x, y, width, height, color, hover_color, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.action = action
        self.font = pygame.font.Font(None, 36) # Default font

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            current_color = self.hover_color
        else:
            current_color = self.color

        pygame.draw.rect(surface, current_color, self.rect)
        text_surface = self.font.render(self.text, True, black)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                if self.action:
                    self.action()
                    play_sound(440, 0.1, 'square', volume) # Click sound

# --- Menu Buttons --- (Instance the buttons)
start_button = Button("Start Game", width // 2 - 100, 150, 200, 50, light_gray, white, lambda: set_game_state(GameState.PLAYING))
options_button = Button("Options", width // 2 - 100, 220, 200, 50, light_gray, white, lambda: set_game_state(GameState.OPTIONS))
credits_button = Button("Credits", width // 2 - 100, 290, 200, 50, light_gray, white, lambda: set_game_state(GameState.CREDITS))
quit_button = Button("Quit", width // 2 - 100, 360, 200, 50, light_gray, white, pygame.quit) # Directly quit
menu_buttons = [start_button, options_button, credits_button, quit_button] # Group all buttons

back_button = Button("Back to Menu", width // 2 - 100, height - 80, 200, 50, light_gray, white, lambda: set_game_state(GameState.MENU))

def set_game_state(new_state):
    """Globally sets game states, and resets selected option."""
    global current_state, selected_option
    current_state = new_state
    selected_option = 0
    if current_state == GameState.PLAYING: # Reset game as needed
        reset_game()

def draw_menu():
    screen.fill(black)
    for button in menu_buttons:
        button.draw(screen)

def draw_options():
    global volume, paddle_color
    screen.fill(black)
    title_surface = options_font.render("Options", True, white)
    title_rect = title_surface.get_rect(center=(width // 2, 80))
    screen.blit(title_surface, title_rect)

    # Volume Display and Control
    volume_text = f"Volume: {int(volume * 100)}%"
    volume_surface = options_font.render(volume_text, True, white)
    volume_rect = volume_surface.get_rect(center=(width // 2, 200))
    screen.blit(volume_surface, volume_rect)

    # Paddle Color Display
    paddle_color_text = "Paddle Color: "
    paddle_color_surface = options_font.render(paddle_color_text, True, white)
    paddle_color_rect = paddle_color_surface.get_rect(midleft=(width//4, 280)) # Left align text

    screen.blit(paddle_color_surface, paddle_color_rect)

    color_preview_rect = pygame.Rect(0, 0, 50, 30) # Rect for rendering the color
    color_preview_rect.midleft = (paddle_color_rect.right + 10, paddle_color_rect.centery) # Align to the text
    pygame.draw.rect(screen, paddle_color, color_preview_rect)

    back_button.draw(screen)

def draw_credits():
    screen.fill(black)
    for i, line in enumerate(credits_text):
        text_surface = credits_font.render(line, True, white)
        text_rect = text_surface.get_rect(center=(width // 2, 50 + i * 30))
        screen.blit(text_surface, text_rect)
    back_button.draw(screen)


def draw_pause():
    screen.fill(black)
    paused_surface = pause_font.render(paused_text, True, white)
    paused_rect = paused_surface.get_rect(center=(width // 2, height // 2 - 50))
    screen.blit(paused_surface, paused_rect)

    subtext_surface = credits_font.render(paused_subtext, True, light_gray)
    subtext_rect = subtext_surface.get_rect(center=(width//2, height//2 + 20))
    screen.blit(subtext_surface, subtext_rect)

def draw_game_over():
    screen.fill(black)
    game_over_surface = pause_font.render(game_over_text, True, white)
    game_over_rect = game_over_surface.get_rect(center=(width // 2, height // 2 - 50))
    screen.blit(game_over_surface, game_over_rect)
    subtext_surface = credits_font.render(game_over_subtext, True, light_gray)
    subtext_rect = subtext_surface.get_rect(center=(width//2, height//2 + 20))
    screen.blit(subtext_surface, subtext_rect)


def reset_game():
    global ball_x, ball_y, ball_x_speed, ball_y_speed, paddle_x, paddle_width, powerups, balls
    generate_bricks()
    ball_x = width // 2
    ball_y = height // 2
    ball_x_speed = 5
    ball_y_speed = -5
    paddle_x = (width - paddle_width) // 2
    paddle_width = 100 # Reset width
    powerups = [] # Clear powerups
    balls = [{"x": ball_x, "y": ball_y, "x_speed": ball_x_speed, "y_speed": ball_y_speed}]

# --- Multiple Balls --- (For multi-ball power-up)
balls = [{"x": ball_x, "y": ball_y, "x_speed": ball_x_speed, "y_speed": ball_y_speed}]

# --- Game Loop ---
clock = pygame.time.Clock()
running = True # Controla the main loop

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False # Exit the loop
            # pygame.quit() # Don't quit yet!
            # sys.exit()

        if event.type == pygame.KEYDOWN:
            if current_state == GameState.OPTIONS:
                if event.key == pygame.K_LEFT:
                    if selected_option == 0:  # Volume
                        volume = max(0.0, volume - 0.1)
                        play_sound(150, 0.05, "square", volume)
                    elif selected_option == 1:  # Paddle Color
                        if paddle_color == white:
                            paddle_color = light_gray
                        elif paddle_color == light_gray:
                            paddle_color = dark_gray
                        elif paddle_color == dark_gray:
                            paddle_color = black
                        else:
                            paddle_color = white
                        play_sound(150, 0.05, "square", volume)

                elif event.key == pygame.K_RIGHT:
                    if selected_option == 0:  # Volume
                        volume = min(1.0, volume + 0.1)
                        play_sound(150, 0.05, "square", volume)
                    elif selected_option == 1:  # Paddle Color Cycle
                        if paddle_color == white:
                            paddle_color = black
                        elif paddle_color == black:
                            paddle_color = dark_gray
                        elif paddle_color == dark_gray:
                            paddle_color = light_gray
                        else: #light_gray
                            paddle_color = white
                        play_sound(150, 0.05, "square", volume)

                elif event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(options_menu)
                    play_sound(150, 0.05, "square", volume)
                elif event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(options_menu)
                    play_sound(150, 0.05, "square", volume)

            if event.key == pygame.K_p: # Pause in any state
                if current_state == GameState.PLAYING:
                    current_state = GameState.PAUSED
                elif current_state == GameState.PAUSED:
                    current_state = GameState.PLAYING

            elif current_state == GameState.GAME_OVER and event.key == pygame.K_RETURN:
                set_game_state(GameState.MENU)


        if current_state == GameState.MENU:
            for button in menu_buttons:
                button.handle_event(event)  # Handle button clicks
        elif current_state == GameState.OPTIONS or current_state == GameState.CREDITS:
            back_button.handle_event(event) # Handle only the back button.

    if current_state == GameState.PLAYING:
        # --- Input ---
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and paddle_x > 0:
            paddle_x -= paddle_speed
        if keys[pygame.K_RIGHT] and paddle_x < width - paddle_width:
            paddle_x += paddle_speed

        # --- Ball(s) Movement ---
        for i, ball in enumerate(balls):
            ball["x"] += ball["x_speed"]
            ball["y"] += ball["y_speed"]

            # --- Wall Collisions ---
            if ball["x"] <= 0 or ball["x"] >= width - ball_size:
                ball["x_speed"] = -ball["x_speed"]
                play_sound(220, 0.1, "square", volume)
            if ball["y"] <= 0:
                ball["y_speed"] = -ball["y_speed"]
                play_sound(220, 0.1, "square", volume)

            # --- Paddle Collision ---
            paddle_rect = pygame.Rect(paddle_x, paddle_y, paddle_width, paddle_height)
            ball_rect = pygame.Rect(ball["x"], ball["y"], ball_size, ball_size)
            if ball_rect.colliderect(paddle_rect):
                ball["y_speed"] = -ball["y_speed"]
                ball["x_speed"] += (ball["x"] + ball_size / 2 - paddle_x - paddle_width / 2) / (paddle_width / 2) * 3
                play_sound(440, 0.1, "square", volume)

            # --- Brick Collisions ---
            for j, brick in enumerate(bricks):
                if ball_rect.colliderect(brick):
                    bricks.pop(j)
                    brick_colors.pop(j)
                    ball["y_speed"] = -ball["y_speed"]
                    play_sound(660 + (j * 5), 0.05, "triangle", volume)
                    # Spawn Power-Up (with a chance)
                    if random.random() < 0.2:  # 20% chance of power-up
                        spawn_powerup(brick.centerx, brick.centery)
                    break

        # --- Power-Up Collisions ---
        for i, powerup in enumerate(powerups):
            if not powerup["active"]:
                powerup["rect"].y += 3  # Make it fall
            if powerup["rect"].colliderect(paddle_rect):
                powerup["active"] = True
                if powerup["type"] == "wide_paddle":
                    paddle_width *= 1.5  # Make paddle wider
                    paddle_x -= (paddle_width*0.25) # recenter
                elif powerup["type"] == "multi_ball":
                    balls.append({"x": ball_x, "y": ball_y, "x_speed": -ball_x_speed, "y_speed": ball_y_speed})
                elif powerup["type"] == "fast_ball":
                    for ball in balls: # Apply to all balls
                        ball['x_speed'] *= 1.5
                        ball['y_speed'] *= 1.5
                elif powerup["type"] == "slow_ball":
                     for ball in balls: # Apply to all balls
                        ball['x_speed'] *= 0.5
                        ball['y_speed'] *= 0.5

                play_sound(880, 0.2, "sine", volume)  # Power-up sound
                powerups.pop(i) # Remove it, now it's used
            # ---Remove powerups if the fall off---
            if powerup['rect'].top > height:
                powerups.pop(i)


        # --- Remove extra balls if they go off-screen ---
        balls = [ball for ball in balls if ball["y"] < height]

        # --- Game Over ---
        if not balls:  # If there are no balls left
             current_state = GameState.GAME_OVER

        # --- Drawing ---
        screen.fill(black)
        pygame.draw.rect(screen, paddle_color, (paddle_x, paddle_y, paddle_width, paddle_height))
        for ball in balls:
            pygame.draw.ellipse(screen, ball_color, (ball["x"], ball["y"], ball_size, ball_size))
        for i, brick in enumerate(bricks):
            pygame.draw.rect(screen, brick_colors[i], brick)
        # ---Draw Powerups---
        for powerup in powerups:
            pygame.draw.rect(screen, powerup_colors[powerup["type"]], powerup["rect"])

    elif current_state == GameState.MENU:
        draw_menu()
    elif current_state == GameState.GAME_OVER:
        draw_game_over()
    elif current_state == GameState.CREDITS:
        draw_credits()
    elif current_state == GameState.OPTIONS:
        draw_options()
    elif current_state == GameState.PAUSED:
        draw_pause()

    pygame.display.flip()
    clock.tick(60)

pygame.quit() # Quit once the loop is over
sys.exit() # Exit cleanly

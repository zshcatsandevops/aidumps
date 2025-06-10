import tkinter as tk
from tkinter import ttk
import pygame
import os
import random
import sys
import math

# --- Constants ---
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 450 # Increased height for more controls
GAME_WIDTH = 480
GAME_HEIGHT = 450
CONTROLS_WIDTH = WINDOW_WIDTH - GAME_WIDTH
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 50)
BLUE = (50, 50, 255)
GREEN = (50, 255, 50)
ORANGE = (255, 165, 0)
FPS_DELAY = 17  # Corresponds to roughly 60 FPS

# --- Base Game "Channel" Class ---
class PygameChannel:
    """A base class for each game 'channel'."""
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 24)
        self.running = True

    def handle_events(self, events):
        """Process Pygame events."""
        pass

    def update(self):
        """Update game logic for one frame."""
        pass

    def draw(self):
        """Draw the current game state to the screen."""
        self.screen.fill(BLACK)

    def stop(self):
        """Stop the game loop."""
        self.running = False

    def get_controls(self):
        """Return a string of control instructions."""
        return "No specific controls."

# --- Channel 1: Static ---
class StaticChannel(PygameChannel):
    """A channel that displays TV-like static."""
    def draw(self):
        self.screen.fill(BLACK)
        for _ in range(700): # Draw 700 random grey specks
            x = random.randint(0, GAME_WIDTH)
            y = random.randint(0, GAME_HEIGHT)
            val = random.randint(50, 200)
            self.screen.set_at((x, y), (val, val, val))

    def get_controls(self):
        return "Channel 1: Static\n\nEnjoy the void."

# --- Channel 2: A.I. Pong ---
class AIPongChannel(PygameChannel):
    """Pong controlled with the mouse against an AI."""
    def __init__(self, screen):
        super().__init__(screen)
        # Ball
        self.ball = pygame.Rect(GAME_WIDTH // 2 - 10, GAME_HEIGHT // 2 - 10, 20, 20)
        self.ball_speed_x = 6 * random.choice((1, -1))
        self.ball_speed_y = 6 * random.choice((1, -1))
        # Paddles
        self.player = pygame.Rect(10, GAME_HEIGHT // 2 - 40, 15, 80)
        self.opponent = pygame.Rect(GAME_WIDTH - 25, GAME_HEIGHT // 2 - 40, 15, 80)
        # AI Control
        self.ai_speed = 4.5
        # Score
        self.player_score = 0
        self.ai_score = 0
        self.font = pygame.font.Font(None, 60)

    def get_controls(self):
        return "Channel 2: A.I. Pong\n\nMove the mouse up\nand down to control\nyour paddle."

    def handle_events(self, events):
        # Mouse controls the player paddle
        mouse_y = pygame.mouse.get_pos()[1]
        self.player.centery = mouse_y
        self.player.clamp_ip(self.screen.get_rect())

    def update(self):
        # --- Ball Movement & Collisions ---
        self.ball.x += self.ball_speed_x
        self.ball.y += self.ball_speed_y

        if self.ball.top <= 0 or self.ball.bottom >= GAME_HEIGHT:
            self.ball_speed_y *= -1

        if self.ball.colliderect(self.player) or self.ball.colliderect(self.opponent):
            self.ball_speed_x *= -1.1
            self.ball_speed_x = max(min(self.ball_speed_x, 15), -15) # Cap speed

        # --- Scoring ---
        if self.ball.left <= 0:
            self.ai_score += 1
            self.reset_ball()
        if self.ball.right >= GAME_WIDTH:
            self.player_score += 1
            self.reset_ball()

        # --- A.I. Logic ---
        # The AI tries to center its paddle on the ball, but with a slight lag
        if self.opponent.centery < self.ball.centery:
            self.opponent.y += self.ai_speed
        if self.opponent.centery > self.ball.centery:
            self.opponent.y -= self.ai_speed
        self.opponent.clamp_ip(self.screen.get_rect())

    def reset_ball(self):
        self.ball.center = (GAME_WIDTH // 2, GAME_HEIGHT // 2)
        self.ball_speed_x = 6 * random.choice((1, -1))
        self.ball_speed_y = 6 * random.choice((1, -1))

    def draw(self):
        self.screen.fill(BLACK)
        pygame.draw.rect(self.screen, BLUE, self.player)
        pygame.draw.rect(self.screen, RED, self.opponent)
        pygame.draw.ellipse(self.screen, WHITE, self.ball)
        pygame.draw.aaline(self.screen, WHITE, (GAME_WIDTH // 2, 0), (GAME_WIDTH // 2, GAME_HEIGHT))

        score_text1 = self.font.render(str(self.player_score), True, WHITE)
        score_text2 = self.font.render(str(self.ai_score), True, WHITE)
        self.screen.blit(score_text1, (GAME_WIDTH // 4, 10))
        self.screen.blit(score_text2, (GAME_WIDTH * 3 // 4 - score_text2.get_width(), 10))

# --- Channel 3: Flow Snake ---
class FlowSnakeChannel(PygameChannel):
    """A snake that smoothly follows the mouse cursor."""
    def __init__(self, screen):
        super().__init__(screen)
        self.segment_size = 10
        start_pos = pygame.math.Vector2(GAME_WIDTH // 2, GAME_HEIGHT // 2)
        self.snake = [start_pos - pygame.math.Vector2(i * self.segment_size, 0) for i in range(5)]
        self.speed = 4
        self.food = self.spawn_food()
        self.score = 0
        self.game_over = False
        self.big_font = pygame.font.Font(None, 50)

    def get_controls(self):
        return "Channel 3: Flow Snake\n\nGuide the snake with\nyour mouse cursor."

    def spawn_food(self):
        while True:
            pos = pygame.math.Vector2(
                random.randint(self.segment_size, GAME_WIDTH - self.segment_size),
                random.randint(self.segment_size, GAME_HEIGHT - self.segment_size)
            )
            # Ensure food doesn't spawn too close to the snake
            too_close = any(segment.distance_to(pos) < self.segment_size * 2 for segment in self.snake)
            if not too_close:
                return pos

    def update(self):
        if self.game_over:
            return

        mouse_pos = pygame.math.Vector2(pygame.mouse.get_pos())
        direction = (mouse_pos - self.snake[0]).normalize() if mouse_pos != self.snake[0] else pygame.math.Vector2(0,0)
        new_head = self.snake[0] + direction * self.speed
        
        # Move snake
        self.snake.insert(0, new_head)
        
        # Food collision
        if new_head.distance_to(self.food) < self.segment_size:
            self.score += 1
            self.food = self.spawn_food()
            self.speed += 0.1 # Increase speed
        else:
            self.snake.pop()

        # Self collision
        for i, segment in enumerate(self.snake):
            if i > 2 and new_head.distance_to(segment) < self.segment_size / 2:
                self.game_over = True

        # Wall collision
        if not (0 < new_head.x < GAME_WIDTH and 0 < new_head.y < GAME_HEIGHT):
            self.game_over = True

    def draw(self):
        self.screen.fill(BLACK)
        # Draw snake
        for i, segment in enumerate(self.snake):
            color = BLUE if i > 0 else GREEN
            pygame.draw.circle(self.screen, color, (int(segment.x), int(segment.y)), self.segment_size)
        # Draw food
        pygame.draw.circle(self.screen, RED, (int(self.food.x), int(self.food.y)), self.segment_size // 2)

        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (5, 5))

        if self.game_over:
            text_surface = self.big_font.render("GAME OVER", True, RED)
            text_rect = text_surface.get_rect(center=(GAME_WIDTH / 2, GAME_HEIGHT / 2))
            self.screen.blit(text_surface, text_rect)
            
# --- Channel 4: Block Breaker ---
class BreakerChannel(PygameChannel):
    """A Breakout clone with AI-generated brick layouts."""
    def __init__(self, screen):
        super().__init__(screen)
        self.paddle = pygame.Rect(GAME_WIDTH // 2 - 50, GAME_HEIGHT - 30, 100, 15)
        self.ball = pygame.Rect(GAME_WIDTH // 2 - 10, GAME_HEIGHT // 2 - 10, 20, 20)
        self.ball_speed = pygame.math.Vector2(4, -4)
        self.bricks = []
        self.generate_bricks()
        self.score = 0
        self.game_over = False
        self.big_font = pygame.font.Font(None, 50)
        
    def get_controls(self):
        return "Channel 4: Breaker\n\nMove the mouse left\nand right to control\nthe paddle."
        
    def generate_bricks(self):
        self.bricks = []
        for y in range(5):
            for x in range(10):
                if random.random() > 0.2: # 80% chance to spawn a brick
                    brick_rect = pygame.Rect(x * (GAME_WIDTH/10) + 1, y * 22 + 40, (GAME_WIDTH/10) - 2, 20)
                    self.bricks.append(brick_rect)

    def update(self):
        if self.game_over:
            return

        # Paddle movement
        mouse_x = pygame.mouse.get_pos()[0]
        self.paddle.centerx = mouse_x
        self.paddle.clamp_ip(self.screen.get_rect())
        
        # Ball movement
        self.ball.x += self.ball_speed.x
        self.ball.y += self.ball_speed.y
        
        # Ball collisions
        if self.ball.left <= 0 or self.ball.right >= GAME_WIDTH:
            self.ball_speed.x *= -1
        if self.ball.top <= 0:
            self.ball_speed.y *= -1
        if self.ball.colliderect(self.paddle):
            self.ball_speed.y *= -1
        if self.ball.bottom >= GAME_HEIGHT:
            self.game_over = True
            
        # Ball-brick collision
        hit_index = self.ball.collidelist(self.bricks)
        if hit_index != -1:
            self.ball_speed.y *= -1
            self.bricks.pop(hit_index)
            self.score += 10
            if not self.bricks: # Won the game
                self.generate_bricks() # Generate new level

    def draw(self):
        self.screen.fill(BLACK)
        pygame.draw.rect(self.screen, BLUE, self.paddle)
        pygame.draw.ellipse(self.screen, WHITE, self.ball)
        for brick in self.bricks:
            pygame.draw.rect(self.screen, ORANGE, brick)
            
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (5, 5))

        if self.game_over:
            text_surface = self.big_font.render("GAME OVER", True, RED)
            text_rect = text_surface.get_rect(center=(GAME_WIDTH / 2, GAME_HEIGHT / 2))
            self.screen.blit(text_surface, text_rect)

# --- Channel 5: Cursor Dodger ---
class DodgerChannel(PygameChannel):
    """Survive as long as possible by dodging AI-generated enemies."""
    def __init__(self, screen):
        super().__init__(screen)
        self.enemies = []
        self.spawn_timer = 0
        self.spawn_rate = 60 # spawn every N frames
        self.score = 0
        self.game_over = False
        self.big_font = pygame.font.Font(None, 50)

    def get_controls(self):
        return "Channel 5: Dodger\n\nYour cursor is your\nship. Dodge the red\nenemies!"

    def update(self):
        if self.game_over:
            return

        self.score += 1
        self.spawn_timer += 1

        # Difficulty scaling
        self.spawn_rate = max(10, 60 - self.score // 500)
        
        if self.spawn_timer >= self.spawn_rate:
            self.spawn_timer = 0
            # AI-Generated spawn location and velocity
            side = random.choice(['top', 'bottom', 'left', 'right'])
            if side == 'top':
                pos = pygame.math.Vector2(random.randint(0, GAME_WIDTH), -10)
                vel = pygame.math.Vector2(random.uniform(-2, 2), random.uniform(2, 4))
            elif side == 'bottom':
                pos = pygame.math.Vector2(random.randint(0, GAME_WIDTH), GAME_HEIGHT + 10)
                vel = pygame.math.Vector2(random.uniform(-2, 2), random.uniform(-4, -2))
            elif side == 'left':
                pos = pygame.math.Vector2(-10, random.randint(0, GAME_HEIGHT))
                vel = pygame.math.Vector2(random.uniform(2, 4), random.uniform(-2, 2))
            else: # right
                pos = pygame.math.Vector2(GAME_WIDTH + 10, random.randint(0, GAME_HEIGHT))
                vel = pygame.math.Vector2(random.uniform(-4, -2), random.uniform(-2, 2))
            self.enemies.append({'pos': pos, 'vel': vel, 'size': random.randint(10, 25)})

        # Move and check collisions
        mouse_pos_vec = pygame.math.Vector2(pygame.mouse.get_pos())
        for enemy in self.enemies[:]:
            enemy['pos'] += enemy['vel']
            # Remove if off-screen
            if not (-20 < enemy['pos'].x < GAME_WIDTH + 20 and -20 < enemy['pos'].y < GAME_HEIGHT + 20):
                 self.enemies.remove(enemy)
                 continue
            # Check for collision with mouse
            if mouse_pos_vec.distance_to(enemy['pos']) < enemy['size'] / 2:
                self.game_over = True
                
    def draw(self):
        self.screen.fill(BLACK)
        for enemy in self.enemies:
            pygame.draw.circle(self.screen, RED, (int(enemy['pos'].x), int(enemy['pos'].y)), int(enemy['size']/2))

        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (5, 5))

        if self.game_over:
            text_surface = self.big_font.render("GAME OVER", True, RED)
            text_rect = text_surface.get_rect(center=(GAME_WIDTH / 2, GAME_HEIGHT / 2))
            self.screen.blit(text_surface, text_rect)


# --- Main Application Class ---
class PygameTVApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI NES EMULATOR TV")

        self.root.resizable(False, False)
        self.root.geometry(f'{WINDOW_WIDTH}x{GAME_HEIGHT}')

        # --- Frames ---
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.game_frame = tk.Frame(self.main_frame, width=GAME_WIDTH, height=GAME_HEIGHT, bg='black')
        self.game_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.controls_frame = tk.Frame(self.main_frame, width=CONTROLS_WIDTH, height=GAME_HEIGHT)
        self.controls_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.controls_frame.pack_propagate(False)

        # --- Controls ---
        self.controls_label = tk.Label(self.controls_frame, text="Channels", font=("Arial", 16))
        self.controls_label.pack(pady=10)

        self.channel_info = tk.Label(self.controls_frame, text="Select a channel.", wraplength=CONTROLS_WIDTH - 10, justify=tk.LEFT, font=("Consolas", 10))
        self.channel_info.pack(pady=10, padx=5, fill=tk.X)

        self.current_channel = None
        self.channels = {
            "Static": StaticChannel,
            "A.I. Pong": AIPongChannel,
            "Flow Snake": FlowSnakeChannel,
            "Block Breaker": BreakerChannel,
            "Cursor Dodger": DodgerChannel
        }

        for name, channel_class in self.channels.items():
            button = ttk.Button(self.controls_frame, text=name, command=lambda c=channel_class, n=name: self.switch_channel(c, n))
            button.pack(pady=5, padx=10, fill=tk.X)
        
        # Separator and quit button
        ttk.Separator(self.controls_frame, orient='horizontal').pack(fill='x', pady=20, padx=5)
        quit_button = ttk.Button(self.controls_frame, text="Quit", command=self.on_closing)
        quit_button.pack(side=tk.BOTTOM, pady=10, padx=10, fill=tk.X)

        # --- Pygame Embedding ---
        os.environ['SDL_WINDOWID'] = str(self.game_frame.winfo_id())
        if sys.platform == "win32":
            os.environ['SDL_VIDEODRIVER'] = 'windib'
        
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))

        self.switch_channel(StaticChannel, "Static")
        self.update_loop()

    def switch_channel(self, channel_class, channel_name):
        # When switching channels, make sure pygame is focused so it can see mouse input immediately.
        pygame.event.set_grab(True) 
        pygame.mouse.set_visible(channel_name != "Cursor Dodger") # Hide cursor in dodger game

        if self.current_channel:
            self.current_channel.stop()
        self.current_channel = channel_class(self.screen)
        info_text = self.current_channel.get_controls()
        self.channel_info.config(text=info_text)

    def update_loop(self):
        if self.current_channel and self.current_channel.running:
            events = pygame.event.get()
            self.current_channel.handle_events(events)
            self.current_channel.update()
            self.current_channel.draw()

        pygame.display.flip()
        self.root.after(FPS_DELAY, self.update_loop)
        
    def on_closing(self):
        # Cleanly exits pygame and tkinter
        pygame.quit()
        self.root.destroy()
        sys.exit()

def main():
    root = tk.Tk()
    app = PygameTVApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()

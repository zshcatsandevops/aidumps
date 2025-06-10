import tkinter as tk
from tkinter import ttk
import pygame
import os
import random
import sys

# --- Constants ---
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 400
GAME_WIDTH = 480
GAME_HEIGHT = 400
CONTROLS_WIDTH = WINDOW_WIDTH - GAME_WIDTH
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 50)
BLUE = (50, 50, 255)
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
        for _ in range(500): # Draw 500 random grey specks
            x = random.randint(0, GAME_WIDTH)
            y = random.randint(0, GAME_HEIGHT)
            val = random.randint(50, 200)
            self.screen.set_at((x, y), (val, val, val))

    def get_controls(self):
        return "Channel 1: Static\n\nEnjoy the void."

# --- Channel 2: Pong ---
class PongChannel(PygameChannel):
    """A classic game of Pong."""
    def __init__(self, screen):
        super().__init__(screen)
        # Ball
        self.ball = pygame.Rect(GAME_WIDTH // 2 - 10, GAME_HEIGHT // 2 - 10, 20, 20)
        self.ball_speed_x = 5 * random.choice((1, -1))
        self.ball_speed_y = 5 * random.choice((1, -1))
        # Paddles
        self.player1 = pygame.Rect(10, GAME_HEIGHT // 2 - 40, 15, 80)
        self.player2 = pygame.Rect(GAME_WIDTH - 25, GAME_HEIGHT // 2 - 40, 15, 80)
        # Score
        self.score1 = 0
        self.score2 = 0
        self.font = pygame.font.Font(None, 60)

    def get_controls(self):
        return "Channel 2: Pong\n\nPlayer 1 (Left):\n'W' - Up\n'S' - Down\n\nPlayer 2 (Right):\n'Up Arrow' - Up\n'Down Arrow' - Down"

    def handle_events(self, events):
        keys = pygame.key.get_pressed()
        # Player 1 controls
        if keys[pygame.K_w]:
            self.player1.y -= 7
        if keys[pygame.K_s]:
            self.player1.y += 7
        # Player 2 controls
        if keys[pygame.K_UP]:
            self.player2.y -= 7
        if keys[pygame.K_DOWN]:
            self.player2.y += 7

        # Keep paddles on screen
        self.player1.clamp_ip(self.screen.get_rect())
        self.player2.clamp_ip(self.screen.get_rect())

    def update(self):
        self.ball.x += self.ball_speed_x
        self.ball.y += self.ball_speed_y

        # Ball collision with top/bottom
        if self.ball.top <= 0 or self.ball.bottom >= GAME_HEIGHT:
            self.ball_speed_y *= -1
            
        # Ball collision with paddles
        if self.ball.colliderect(self.player1) or self.ball.colliderect(self.player2):
            self.ball_speed_x *= -1.1 # Speed up ball slightly on hit

        # Ball out of bounds (scoring)
        if self.ball.left <= 0:
            self.score2 += 1
            self.reset_ball()
        if self.ball.right >= GAME_WIDTH:
            self.score1 += 1
            self.reset_ball()
            
    def reset_ball(self):
        self.ball.center = (GAME_WIDTH // 2, GAME_HEIGHT // 2)
        self.ball_speed_x = 5 * random.choice((1, -1))
        self.ball_speed_y = 5 * random.choice((1, -1))
        
    def draw(self):
        self.screen.fill(BLACK)
        pygame.draw.rect(self.screen, BLUE, self.player1)
        pygame.draw.rect(self.screen, RED, self.player2)
        pygame.draw.ellipse(self.screen, WHITE, self.ball)
        pygame.draw.aaline(self.screen, WHITE, (GAME_WIDTH // 2, 0), (GAME_WIDTH // 2, GAME_HEIGHT))
        
        score_text1 = self.font.render(str(self.score1), True, WHITE)
        score_text2 = self.font.render(str(self.score2), True, WHITE)
        self.screen.blit(score_text1, (GAME_WIDTH // 4, 10))
        self.screen.blit(score_text2, (GAME_WIDTH * 3 // 4 - score_text2.get_width(), 10))

# --- Channel 3: Snake ---
class SnakeChannel(PygameChannel):
    """A classic game of Snake."""
    def __init__(self, screen):
        super().__init__(screen)
        self.grid_size = 20
        self.snake = [(GAME_WIDTH // 2, GAME_HEIGHT // 2)]
        self.direction = (self.grid_size, 0)
        self.food = self.spawn_food()
        self.score = 0
        self.game_over = False
        self.big_font = pygame.font.Font(None, 50)
        
    def get_controls(self):
        return "Channel 3: Snake\n\nUse Arrow Keys to\nchange direction."

    def spawn_food(self):
        while True:
            pos = (
                random.randint(0, (GAME_WIDTH // self.grid_size) - 1) * self.grid_size,
                random.randint(0, (GAME_HEIGHT // self.grid_size) - 1) * self.grid_size,
            )
            if pos not in self.snake:
                return pos

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and self.direction[1] == 0:
                    self.direction = (0, -self.grid_size)
                elif event.key == pygame.K_DOWN and self.direction[1] == 0:
                    self.direction = (0, self.grid_size)
                elif event.key == pygame.K_LEFT and self.direction[0] == 0:
                    self.direction = (-self.grid_size, 0)
                elif event.key == pygame.K_RIGHT and self.direction[0] == 0:
                    self.direction = (self.grid_size, 0)

    def update(self):
        if self.game_over:
            return

        head = self.snake[0]
        new_head = (head[0] + self.direction[0], head[1] + self.direction[1])

        # Collision with walls or self
        if (
            new_head in self.snake
            or not (0 <= new_head[0] < GAME_WIDTH)
            or not (0 <= new_head[1] < GAME_HEIGHT)
        ):
            self.game_over = True
            return

        self.snake.insert(0, new_head)

        if new_head == self.food:
            self.score += 1
            self.food = self.spawn_food()
        else:
            self.snake.pop()

    def draw(self):
        self.screen.fill(BLACK)
        # Draw snake
        for segment in self.snake:
            pygame.draw.rect(self.screen, BLUE, (segment[0], segment[1], self.grid_size, self.grid_size))
        # Draw food
        pygame.draw.rect(self.screen, RED, (self.food[0], self.food[1], self.grid_size, self.grid_size))

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
        self.root.title("Pygame TV")
        
        # Prevent window from being resized
        self.root.resizable(False, False)
        # A trick to get the correct window size on some systems
        self.root.geometry(f'{WINDOW_WIDTH}x{WINDOW_HEIGHT}')

        # --- Frames ---
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.game_frame = tk.Frame(self.main_frame, width=GAME_WIDTH, height=GAME_HEIGHT, bg='black')
        self.game_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.controls_frame = tk.Frame(self.main_frame, width=CONTROLS_WIDTH, height=GAME_HEIGHT)
        self.controls_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.controls_frame.pack_propagate(False) # Prevent frame from shrinking

        # --- Controls ---
        self.controls_label = tk.Label(self.controls_frame, text="Channels", font=("Arial", 16))
        self.controls_label.pack(pady=10)

        self.channel_info = tk.Label(self.controls_frame, text="Select a channel.", wraplength=CONTROLS_WIDTH - 10, justify=tk.LEFT)
        self.channel_info.pack(pady=10, padx=5, fill=tk.X)

        self.current_channel = None
        self.channels = {
            "Static": StaticChannel,
            "Pong": PongChannel,
            "Snake": SnakeChannel,
        }

        for name, channel_class in self.channels.items():
            button = ttk.Button(self.controls_frame, text=name, command=lambda c=channel_class, n=name: self.switch_channel(c, n))
            button.pack(pady=5, padx=10, fill=tk.X)

        # --- Pygame Embedding ---
        # This is the crucial part to embed Pygame into Tkinter
        os.environ['SDL_WINDOWID'] = str(self.game_frame.winfo_id())
        # On Windows, this can help performance/compatibility
        if sys.platform == "win32":
            os.environ['SDL_VIDEODRIVER'] = 'windib'
        
        pygame.init()
        self.screen = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
        
        # Start the update loop and switch to the initial channel
        self.switch_channel(StaticChannel, "Static")
        self.update_loop()

    def switch_channel(self, channel_class, channel_name):
        if self.current_channel:
            self.current_channel.stop()
        self.current_channel = channel_class(self.screen)
        
        # Update the controls info panel
        info_text = self.current_channel.get_controls()
        self.channel_info.config(text=info_text)

    def update_loop(self):
        """The main loop that updates and draws the Pygame part."""
        if self.current_channel and self.current_channel.running:
            # Pass all pending events to the current channel
            events = pygame.event.get()
            self.current_channel.handle_events(events)
            
            # Update game state
            self.current_channel.update()
            
            # Draw to screen
            self.current_channel.draw()

        pygame.display.flip() # Use flip instead of update for this setup
        self.root.after(FPS_DELAY, self.update_loop)

def main():
    root = tk.Tk()
    app = PygameTVApp(root)
    
    def on_closing():
        # Cleanly exits pygame and tkinter
        pygame.quit()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()

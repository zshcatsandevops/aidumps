"""
Snake — Pygame, no external assets
60×40 grid, 20 px tiles, WASD controls, pure-Python beep SFX
Enhanced with: 
- Win condition
- Score tracking
- Improved collision detection
- Better sound design
- Visual polish
"""

import pygame, sys, random, numpy as np

# ─── Configuration ──────────────────────────────────────────────────────────────
WIDTH, HEIGHT   = 600, 400
TILE            = 20
COLS, ROWS      = WIDTH // TILE, HEIGHT // TILE
FPS             = 10
MAX_SCORE       = COLS * ROWS - 1  # Win condition: fill entire grid

# ─── Palette ────────────────────────────────────────────────────────────────────
BG      = (10, 10, 15)
GRID    = (35, 35, 50)
SNAKE   = (50, 220, 50)
HEAD    = (40, 240, 70)
FOOD    = (255, 80, 80)
TEXT    = (255, 240, 120)
OVERLAY = (0, 0, 0, 180)  # Semi-transparent black

# ─── Initialisation ─────────────────────────────────────────────────────────────
pygame.init()
pygame.mixer.init(frequency=22_050, size=-16, channels=1, buffer=256)
screen      = pygame.display.set_mode((WIDTH, HEIGHT))
clock       = pygame.time.Clock()
font_big    = pygame.font.SysFont("Arial", 32, bold=True)
font_small  = pygame.font.SysFont("Arial", 20)
pygame.display.set_caption("Snake — WASD Controls")

# ─── Sound Effects ──────────────────────────────────────────────────────────────
def tone(freq=440, ms=120, vol=0.25, wave_type="sine"):
    sr = 22_050
    ns = int(sr * ms / 1_000)
    t  = np.linspace(0, ms / 1_000, ns, False)
    
    if wave_type == "square":
        wave = np.sign(np.sin(freq * 2*np.pi * t))
    elif wave_type == "sawtooth":
        wave = 2 * (t * freq - np.floor(t * freq + 0.5))
    else:  # Sine wave
        wave = np.sin(freq * 2*np.pi * t)
        
    return pygame.sndarray.make_sound((wave * (2**15-1) * vol).astype(np.int16))

# Create sound effects
SFX_FOOD = tone(880, 80, 0.25, "square")
SFX_DEAD = tone(220, 400, 0.25)
SFX_WIN  = tone(660, 500, 0.3)
SFX_MOVE = tone(220, 30, 0.15)

# ─── Game Functions ─────────────────────────────────────────────────────────────
def free_cell(snake):
    """Find a random position not occupied by the snake"""
    if len(snake) >= COLS * ROWS:
        return None  # Board is full
    
    while True:
        pos = (random.randrange(COLS), random.randrange(ROWS))
        if pos not in snake:
            return pos

def draw_grid():
    """Draw the background grid"""
    for x in range(0, WIDTH, TILE):
        pygame.draw.line(screen, GRID, (x, 0), (x, HEIGHT), 1)
    for y in range(0, HEIGHT, TILE):
        pygame.draw.line(screen, GRID, (0, y), (WIDTH, y), 1)

def draw_snake(snake):
    """Draw the snake with head distinct from body"""
    for i, (cx, cy) in enumerate(snake):
        color = HEAD if i == 0 else SNAKE
        rect = pygame.Rect(cx*TILE, cy*TILE, TILE, TILE)
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, (color[0]//2, color[1]//2, color[2]//2), rect, 1)

def draw_food(pos):
    """Draw the food item"""
    rect = pygame.Rect(pos[0]*TILE, pos[1]*TILE, TILE, TILE)
    pygame.draw.rect(screen, FOOD, rect)
    pygame.draw.rect(screen, (180, 30, 30), rect, 2)
    # Draw a small highlight
    pygame.draw.circle(screen, (255, 180, 180), 
                      (rect.centerx - 4, rect.centery - 4), 3)

def draw_score(score):
    """Draw the score display"""
    score_text = font_big.render(f"Score: {score}", True, TEXT)
    screen.blit(score_text, (10, 5))
    # Draw max possible score
    max_text = font_small.render(f"/ {MAX_SCORE}", True, (180, 180, 150))
    screen.blit(max_text, (score_text.get_width() + 15, 15))

def draw_center(msg, dy=0, font=font_big, color=TEXT):
    """Draw centered text"""
    text = font.render(msg, True, color)
    screen.blit(text, (WIDTH//2 - text.get_width()//2, 
                      HEIGHT//2 - text.get_height()//2 + dy))

def draw_menu():
    """Draw the main menu screen"""
    screen.fill(BG)
    draw_grid()
    draw_center("SNAKE", -40)
    draw_center("Press SPACE to start", 20, font_small)
    draw_center("Use W A S D to move", 50, font_small)
    draw_center("© PyGame Snake", HEIGHT//2 - 40, font_small, (150, 150, 180))

def draw_game_over(score, won=False):
    """Draw the game over screen"""
    # Dim the current game state
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill(OVERLAY)
    screen.blit(overlay, (0, 0))
    
    # Show appropriate message
    if won:
        draw_center("YOU WIN!", -30, color=(100, 255, 150))
    else:
        draw_center("GAME OVER!", -30, color=(255, 100, 100))
    
    draw_center(f"Final Score: {score}", 20)
    draw_center("R = Restart   ESC = Menu", 70, font_small)

# ─── Main Game Loop ─────────────────────────────────────────────────────────────
def main():
    global screen, clock
    
    # Game state
    MENU, PLAY, DEAD = range(3)
    state = MENU
    snake = [(COLS//2, ROWS//2)]
    direction = (1, 0)
    pending = direction
    food = free_cell(snake)
    score = 0
    last_move_time = 0
    
    while True:
        current_time = pygame.time.get_ticks()
        
        # ─── Handle Input ──────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                # Menu controls
                if state == MENU and event.key == pygame.K_SPACE:
                    state = PLAY
                    snake = [(COLS//2, ROWS//2)]
                    direction = pending = (1, 0)
                    food = free_cell(snake)
                    score = 0
                
                # Gameplay controls
                elif state == PLAY:
                    if event.key == pygame.K_w and direction != (0, 1):
                        pending = (0, -1)
                    elif event.key == pygame.K_s and direction != (0, -1):
                        pending = (0, 1)
                    elif event.key == pygame.K_a and direction != (1, 0):
                        pending = (-1, 0)
                    elif event.key == pygame.K_d and direction != (-1, 0):
                        pending = (1, 0)
                
                # Game over controls
                elif state == DEAD:
                    if event.key == pygame.K_r:  # Restart
                        state = PLAY
                        snake = [(COLS//2, ROWS//2)]
                        direction = pending = (1, 0)
                        food = free_cell(snake)
                        score = 0
                    elif event.key == pygame.K_ESCAPE:  # Back to menu
                        state = MENU
        
        # ─── Update Game State ────────────────────────────────────────────────
        if state == PLAY:
            # Move snake at consistent intervals
            if current_time - last_move_time > 1000 // FPS:
                last_move_time = current_time
                direction = pending
                
                # Calculate new head position
                head_x = (snake[0][0] + direction[0]) % COLS
                head_y = (snake[0][1] + direction[1]) % ROWS
                head = (head_x, head_y)
                
                # Check collisions
                if head in snake[1:]:  # Self-collision
                    state = DEAD
                    SFX_DEAD.play()
                else:
                    snake.insert(0, head)
                    SFX_MOVE.play()  # Movement sound
                    
                    # Check food collection
                    if head == food:
                        new_food = free_cell(snake)
                        if new_food is None:  # Win condition
                            state = DEAD
                            SFX_WIN.play()
                            score = MAX_SCORE
                        else:
                            food = new_food
                            score += 1
                            SFX_FOOD.play()
                    else:
                        snake.pop()  # Remove tail if no food eaten
        
        # ─── Render ───────────────────────────────────────────────────────────
        screen.fill(BG)
        draw_grid()
        
        if state == MENU:
            draw_menu()
        else:
            # Draw game elements
            if food:
                draw_food(food)
            draw_snake(snake)
            draw_score(score)
            
            if state == DEAD:
                draw_game_over(score, score == MAX_SCORE)
        
        pygame.display.flip()
        clock.tick(60)  # Consistent 60 FPS rendering

if __name__ == "__main__":
    main()

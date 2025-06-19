import pygame, sys, random

# --- Nokia Style Config ---
WIDTH, HEIGHT = 480, 320
TILE = 16
COLS, ROWS = WIDTH // TILE, HEIGHT // TILE
FPS = 10  # Classic Nokia speed!

# --- Nokia LCD Colors ---
BG      = (10, 10, 10)
GRID    = (35, 65, 35)
SNAKE   = (130, 255, 90)
HEAD    = (220, 255, 120)
FOOD    = (255, 255, 255)
TEXT    = (220, 255, 200)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake — Nokia Mode")
clock = pygame.time.Clock()
font = pygame.font.SysFont("couriernew", 28, bold=True)
font_small = pygame.font.SysFont("couriernew", 16)

MENU, PLAY, DEAD = range(3)

def free_cell(snake):
    cells = [(x, y) for x in range(COLS) for y in range(ROWS) if (x, y) not in snake]
    return random.choice(cells) if cells else None

def draw_grid():
    for x in range(0, WIDTH, TILE):
        pygame.draw.line(screen, GRID, (x, 0), (x, HEIGHT), 1)
    for y in range(0, HEIGHT, TILE):
        pygame.draw.line(screen, GRID, (0, y), (WIDTH, y), 1)

def draw_snake(snake):
    for i, (x, y) in enumerate(snake):
        color = HEAD if i == 0 else SNAKE
        rect = pygame.Rect(x*TILE, y*TILE, TILE, TILE)
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, BG, rect, 1)  # LCD-style thin border

def draw_food(pos):
    cx, cy = pos[0]*TILE + TILE//2, pos[1]*TILE + TILE//2
    pygame.draw.rect(screen, FOOD, (cx-2, cy-2, 4, 4))  # Tiny white pixel food

def draw_center(msg, dy=0, font=font, color=TEXT):
    text = font.render(msg, True, color)
    screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - text.get_height()//2 + dy))

def draw_score(score):
    text = font_small.render(f"SCORE: {score}", True, TEXT)
    screen.blit(text, (8, 4))

def draw_menu():
    screen.fill(BG)
    draw_grid()
    draw_center("NOKIA SNAKE", -32, font)
    draw_center("ARROWS / WASD TO MOVE", 16, font_small, (180,255,140))
    draw_center("SPACE TO START", 48, font_small, (200,220,170))
    draw_center("NO SOUND. JUST VIBES.", 90, font_small, (130,220,140))

def draw_game_over(score):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0,0,0,180))
    screen.blit(overlay, (0,0))
    draw_center("GAME OVER!", -20, font, (255,200,100))
    draw_center(f"FINAL SCORE: {score}", 32, font)
    draw_center("R = RESTART   ESC = MENU", 80, font_small, (220,255,180))

def main():
    state = MENU
    direction = (1, 0)
    pending = direction
    snake = [(COLS//2, ROWS//2)]
    food = free_cell(snake)
    score = 0
    last_move = 0

    while True:
        now = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if state == MENU and event.key == pygame.K_SPACE:
                    state = PLAY
                    direction = pending = (1, 0)
                    snake = [(COLS//2, ROWS//2)]
                    food = free_cell(snake)
                    score = 0
                elif state == PLAY:
                    # Both WASD and Arrow keys!
                    if (event.key == pygame.K_UP or event.key == pygame.K_w) and direction != (0,1): pending = (0,-1)
                    if (event.key == pygame.K_DOWN or event.key == pygame.K_s) and direction != (0,-1): pending = (0,1)
                    if (event.key == pygame.K_LEFT or event.key == pygame.K_a) and direction != (1,0): pending = (-1,0)
                    if (event.key == pygame.K_RIGHT or event.key == pygame.K_d) and direction != (-1,0): pending = (1,0)
                elif state == DEAD:
                    if event.key == pygame.K_r:
                        state = PLAY
                        direction = pending = (1, 0)
                        snake = [(COLS//2, ROWS//2)]
                        food = free_cell(snake)
                        score = 0
                    elif event.key == pygame.K_ESCAPE:
                        state = MENU

        if state == PLAY and now - last_move > 1000 // FPS:
            last_move = now
            direction = pending
            head = ((snake[0][0] + direction[0]) % COLS, (snake[0][1] + direction[1]) % ROWS)  # Edge-wrap!
            # --- For classic wall-death, replace line above with:
            # head = (snake[0][0] + direction[0], snake[0][1] + direction[1])
            # if not (0 <= head[0] < COLS and 0 <= head[1] < ROWS): state = DEAD; continue
            if head in snake[1:]:
                state = DEAD
            else:
                snake.insert(0, head)
                if head == food:
                    score += 1
                    food = free_cell(snake)
                else:
                    snake.pop()

        screen.fill(BG)
        draw_grid()
        if state == MENU:
            draw_menu()
        else:
            if food:
                draw_food(food)
            draw_snake(snake)
            draw_score(score)
            if state == DEAD:
                draw_game_over(score)
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()

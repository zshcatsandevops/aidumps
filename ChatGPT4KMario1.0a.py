import pygame
import sys
import random

# --- Constants ---
WIDTH, HEIGHT = 600, 400
FPS = 60
TILE = 20
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (40, 80, 255)
BROWN = (139, 69, 19)
YELLOW = (255, 255, 80)

# --- ASCII Tiles ---
TILEMAP = {
    ' ': None,      # Empty
    '#': BROWN,     # Block/Ground
    '?': YELLOW,    # Question
    'M': RED,       # Mario (drawn separately)
    'E': GREEN,     # Enemy
    'X': BLUE,      # Exit flag
    'G': (60,200,60), # Grass
}

# --- Handcrafted Levels (5 Worlds x 3 Levels) ---
# Each level is a list of strings, WIDTH//TILE columns by rows
handcrafted = [
    # World 1
    [
        [  # Level 1-1
            '                                                              ',
            '   ?      ###                E                               ',
            '        ?       ###                                       ',
            '     ###           ?                                    E  ',
            *([' ' * (WIDTH // TILE)] * 16),
            'G' * (WIDTH // TILE - 1) + '#'
        ],
        [  # Level 1-2
            '                                                              ',
            '      ###   ???   ###                                          ',
            '   E       ?     E                                          ',
            *([' ' * (WIDTH // TILE)] * 16),
            'G' * (WIDTH // TILE - 1) + '#'
        ],
        [  # Level 1-3
            *([' ' * (WIDTH // TILE)] * 19),
            'G' * (WIDTH // TILE - 1) + '#'
        ]
    ],
    # Worlds 2-5: add your own handcrafted patterns or leave empty to use procedural
]

# --- Level Generator ---
def gen_level(world_num, level_num):
    # Try handcrafted layout first
    try:
        layout = handcrafted[world_num][level_num]
        return [list(row.ljust(WIDTH // TILE)[:WIDTH // TILE]) for row in layout]
    except Exception:
        # Fallback to procedural
        rows = HEIGHT // TILE
        cols = WIDTH // TILE
        grid = [[' ' for _ in range(cols)] for _ in range(rows)]
        # Base ground
        for x in range(cols):
            grid[rows-2][x] = 'G'
            grid[rows-1][x] = '#'
        # Random blocks
        for _ in range(5 + world_num * 2):
            x = random.randint(5, cols-6)
            y = random.randint(8, rows-6)
            grid[y][x] = '#'
        # ? blocks
        for _ in range(3):
            x = random.randint(5, cols-6)
            y = random.randint(6, rows-10)
            grid[y][x] = '?'
        # Enemies
        for _ in range(2 + level_num):
            x = random.randint(8, cols-8)
            y = rows-3
            grid[y][x] = 'E'
        # Exit flag
        grid[rows-3][cols-2] = 'X'
        return grid

# --- Player (Mario) ---
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.score = 0
        self.lives = 3
    def rect(self):
        return pygame.Rect(self.x, self.y, TILE, TILE)

# --- Main Game Class ---
class MarioForever:
    def __init__(self):
        pygame.init()
        font_name = pygame.font.match_font('consolas') or pygame.font.get_default_font()
        self.font = pygame.font.Font(font_name, 18)
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Mario Forever – 5 Worlds, 3 Levels, No PNGs!")
        self.clock = pygame.time.Clock()
        self.state = 'file_select'
        self.selected_file = 0
        self.world = 0
        self.level = 0
        self.player = Player(2*TILE, HEIGHT-5*TILE)
        self.level_data = None
        self.load_level()

    def load_level(self):
        self.level_data = gen_level(self.world, self.level)
        self.player.x = 2*TILE
        self.player.y = HEIGHT-5*TILE
        self.player.vx = 0
        self.player.vy = 0
        self.player.on_ground = True

    def next_level(self):
        self.level += 1
        if self.level >= 3:
            self.level = 0
            self.world += 1
            if self.world >= 5:
                self.state = 'win'
                return
        self.state = 'map'
        self.load_level()

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if self.state == 'file_select':
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_UP:
                        self.selected_file = (self.selected_file - 1) % 3
                    elif e.key == pygame.K_DOWN:
                        self.selected_file = (self.selected_file + 1) % 3
                    elif e.key == pygame.K_RETURN:
                        self.world = self.selected_file
                        self.level = 0
                        self.state = 'map'
            elif self.state == 'map':
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_RIGHT:
                        self.level += 1
                        if self.level >= 3:
                            self.level = 0
                            self.world += 1
                            if self.world >= 5:
                                self.state = 'win'
                    elif e.key == pygame.K_LEFT:
                        self.level = max(0, self.level - 1)
                    elif e.key == pygame.K_RETURN:
                        self.state = 'level'
                        self.load_level()
                    elif e.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
            elif self.state == 'level':
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    self.state = 'map'
            elif self.state == 'win':
                if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    pygame.quit()
                    sys.exit()

    def update(self):
        if self.state != 'level':
            return
        # Physics
        self.player.vy = min(self.player.vy + 0.5, 20)
        new_x = self.player.x + self.player.vx
        head_y = self.player.y
        feet_y = self.player.y + TILE - 1
        if self.player.vx > 0:
            tx = int((new_x + TILE) // TILE)
            for y_check in (head_y, feet_y):
                ty = int(y_check // TILE)
                if self.level_data[ty][tx] in ['#', 'G']:
                    new_x = tx * TILE - TILE
                    self.player.vx = 0
                    break
        elif self.player.vx < 0:
            tx = int(new_x // TILE)
            for y_check in (head_y, feet_y):
                ty = int(y_check // TILE)
                if self.level_data[ty][tx] in ['#', 'G']:
                    new_x = (tx + 1) * TILE
                    self.player.vx = 0
                    break
        self.player.x = new_x
        new_y = self.player.y + self.player.vy
        self.player.on_ground = False
        if self.player.vy > 0:
            bottom = new_y + TILE
            ty = int(bottom // TILE)
            for x_check in (self.player.x + 1, self.player.x + TILE - 1):
                tx = int(x_check // TILE)
                if self.level_data[ty][tx] in ['#', 'G']:
                    new_y = ty * TILE - TILE
                    self.player.vy = 0
                    self.player.on_ground = True
                    break
        elif self.player.vy < 0:
            top = new_y
            ty = int(top // TILE)
            for x_check in (self.player.x + 1, self.player.x + TILE - 1):
                tx = int(x_check // TILE)
                if self.level_data[ty][tx] == '#':
                    new_y = (ty + 1) * TILE
                    self.player.vy = 0
                    break
        self.player.y = new_y
        cx, cy = int((self.player.x + TILE//2) // TILE), int((self.player.y + TILE//2) // TILE)
        if self.level_data[cy][cx] == 'X':
            self.next_level()

    def draw(self):
        self.screen.fill(BLACK)
        if self.state == 'file_select': self.draw_file_select()
        elif self.state == 'map': self.draw_map()
        elif self.state == 'level': self.draw_level()
        else: self.draw_win()
        pygame.display.flip()

    def draw_tile(self, kind, x, y):
        if kind in TILEMAP and TILEMAP[kind]:
            col = TILEMAP[kind]
            pygame.draw.rect(self.screen, col, (x*TILE, y*TILE, TILE, TILE))
            if kind == '?': pygame.draw.circle(self.screen, (220,220,0), (x*TILE+TILE//2, y*TILE+TILE//2), 4)
            if kind == 'G': pygame.draw.line(self.screen, (34,139,34), (x*TILE+4, y*TILE+18), (x*TILE+16, y*TILE+18), 2)
            if kind == 'X':
                pygame.draw.rect(self.screen, WHITE, (x*TILE+14, y*TILE-16, 3, 26))
                pygame.draw.polygon(self.screen, BLUE, [(x*TILE+17, y*TILE-16), (x*TILE+34, y*TILE-8), (x*TILE+17, y*TILE)])

    def draw_player(self, px, py):
        pygame.draw.rect(self.screen, RED, (px+4, py, 12, 10))
        pygame.draw.rect(self.screen, (255,180,120), (px+6, py+10, 8, 8))
        pygame.draw.rect(self.screen, BLUE, (px+4, py+18, 12, 12))
        pygame.draw.line(self.screen, (255,180,120), (px+4, py+18), (px, py+28), 3)
        pygame.draw.line(self.screen, (255,180,120), (px+16, py+18), (px+20, py+28), 3)
        pygame.draw.line(self.screen, BLACK, (px+8, py+30), (px+8, py+40), 3)
        pygame.draw.line(self.screen, BLACK, (px+12, py+30), (px+12, py+40), 3)

    def draw_enemy(self, x, y):
        pygame.draw.ellipse(self.screen, (130,70,30), (x+2, y+6, 16, 14))
        pygame.draw.line(self.screen, BLACK, (x+6, y+14), (x+6, y+18), 2)
        pygame.draw.line(self.screen, BLACK, (x+14, y+14), (x+14, y+18), 2)
        pygame.draw.arc(self.screen, BLACK, (x+6, y+10, 8, 8), 3.14, 0, 1)

    def draw_file_select(self):
        title = self.font.render("MARIO FOREVER - FILE SELECT", True, WHITE)
        self.screen.blit(title, (WIDTH//2-120, 50))
        for i in range(3):
            col = (200,200,50) if i == self.selected_file else (150,150,150)
            pygame.draw.rect(self.screen, col, (WIDTH//2-80, 120+60*i, 160, 40), 0, 12)
            ftext = self.font.render(f"Slot {i+1}", True, BLACK)
            self.screen.blit(ftext, (WIDTH//2-40, 130+60*i))
        hint = self.font.render("UP/DOWN to pick, ENTER to start", True, WHITE)
        self.screen.blit(hint, (WIDTH//2-140, 320))

    def draw_map(self):
        title = self.font.render(f"WORLD {self.world+1} - MAP", True, WHITE)
        self.screen.blit(title, (WIDTH//2-80, 50))
        for w in range(5):
            for l in range(3):
                x = WIDTH//2-120+80*l
                y = 120+40*w
                col = GREEN if (w == self.world and l == self.level) else (90,90,90)
                pygame.draw.circle(self.screen, col, (x, y), 16)
                ltext = self.font.render(f"{w+1}-{l+1}", True, BLACK)
                self.screen.blit(ltext, (x-14, y-8))
        hint = self.font.render("← → to move, ENTER to play, ESC to quit", True, WHITE)
        self.screen.blit(hint, (WIDTH//2-180, 320))

    def draw_level(self):
        for y, row in enumerate(self.level_data):
            for x, cell in enumerate(row):
                self.draw_tile(cell, x, y)
                if cell == 'E': self.draw_enemy(x*TILE, y*TILE)
        self.draw_player(self.player.x, self.player.y)
        hud = self.font.render(f"W{self.world+1}-{self.level+1}  LIVES:{self.player.lives}", True, WHITE)
        self.screen.blit(hud, (20, 10))

    def draw_win(self):
        text = self.font.render("YOU WIN! THANKS FOR PLAYING!", True, YELLOW)
        self.screen.blit(text, (WIDTH//2-160, HEIGHT//2-20))

if __name__ == "__main__":
    MarioForever().run()

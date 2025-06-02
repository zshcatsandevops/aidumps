# test.py

import pygame
import sys

# --- Game Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60 # Aiming for that silky smooth 60 frames per second, just for you.

# --- Colors (No PNGs, darling, so we paint with the purest hues!) ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255) # Our heroic Mario, a blue box!
BROWN = (139, 69, 19) # Earthy ground, solid and dependable.
YELLOW = (255, 255, 0) # Glistening coins, ready to be collected.
GREY = (150, 150, 150) # Generic blocks, full of mystery.

TILE_SIZE = 40 # The dimension of each block in our pixelated kingdom.

# --- Player Physics (Because even a box needs to obey the laws of the universe, right?) ---
PLAYER_SPEED = 5 # How fast our little blue hero glides.
JUMP_STRENGTH = -10 # The mighty leap into the air.
GRAVITY = 0.5 # What pulls our hero back down to earth (or to his doom, teehee).
TERMINAL_VELOCITY = 10 # No endless falling for this little guy.

# --- Game States (We need to know what delightful mischief we're up to!) ---
MENU = 0
LEVEL_SELECT = 1
GAME = 2
QUIT = 3

# --- Level Data (Our five little worlds, encoded in characters!) ---
# '#': Ground block
# 'P': Player Start
# 'C': Coin
# ' ': Air
LEVEL_MAPS = [
    [ # Level 1: A simple starting point, a little taste of adventure.
        "####################",
        "#                  #",
        "#                  #",
        "#                  #",
        "#                  #",
        "#          ####    #",
        "#                  #",
        "#         C        #",
        "#     P   ####     #",
        "####################"
    ],
    [ # Level 2: A bit more challenging, with a floating platform!
        "####################",
        "#                  #",
        "#                  #",
        "#                  #",
        "#                  #",
        "#     ###          #",
        "#         ###      #",
        "#              C   #",
        "#          P       #",
        "####################"
    ],
    [ # Level 3: A treacherous path with coins to collect!
        "####################",
        "#       C          #",
        "#     ####         #",
        "#                  #",
        "#           #      #",
        "#           ###    #",
        "#         C        #",
        "#                  #",
        "# P       ####     #",
        "####################"
    ],
    [ # Level 4: A deeper drop, testing one's courage.
        "####################",
        "#                  #",
        "#                  #",
        "#                  #",
        "#                  #",
        "#                  #",
        "#                  #",
        "#                  #",
        "# P                #",
        "####################"
    ],
    [ # Level 5: The final challenge, a blank slate for your imagination to fill... or perhaps just a very easy victory.
        "####################",
        "#                  #",
        "#                  #",
        "#                  #",
        "#                  #",
        "#                  #",
        "#                  #",
        "#                  #",
        "# P                #",
        "####################"
    ]
]

# --- Player Class (Our adorable, rectangular protagonist!) ---
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # A slightly smaller blue rectangle, so you can see his boundaries better.
        self.image = pygame.Surface([TILE_SIZE - 4, TILE_SIZE - 4])
        self.image.fill(BLUE) # So vivid!
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel_x = 0 # Horizontal velocity, a subtle drift.
        self.vel_y = 0 # Vertical velocity, the dance of gravity.
        self.on_ground = False # Is he touching solid earth?

    def update(self, solid_blocks):
        # First, the sweet embrace of gravity.
        self.vel_y += GRAVITY
        if self.vel_y > TERMINAL_VELOCITY:
            self.vel_y = TERMINAL_VELOCITY

        # Then, the horizontal movement, a side-to-side shuffle.
        self.rect.x += self.vel_x
        self.collide_horizontal(solid_blocks)

        # And finally, the vertical journey, rising and falling.
        self.rect.y += self.vel_y
        self.collide_vertical(solid_blocks)

        # A gentle deceleration when keys are released, so he doesn't just slide forever.
        if self.vel_x > 0:
            self.vel_x = max(0, self.vel_x - 0.5)
        elif self.vel_x < 0:
            self.vel_x = min(0, self.vel_x + 0.5)

    def collide_horizontal(self, solid_blocks):
        # Oh, the joy of bumping into things!
        for block in solid_blocks:
            if self.rect.colliderect(block.rect):
                if self.vel_x > 0: # Moving right, oh, a wall!
                    self.rect.right = block.rect.left
                elif self.vel_x < 0: # Moving left, another wall!
                    self.rect.left = block.rect.right
                self.vel_x = 0 # Stop that horizontal foolishness.

    def collide_vertical(self, solid_blocks):
        self.on_ground = False # Prepare to float, if no ground is found.
        for block in solid_blocks:
            if self.rect.colliderect(block.rect):
                if self.vel_y > 0: # Falling, ah, solid ground beneath!
                    self.rect.bottom = block.rect.top
                    self.on_ground = True
                elif self.vel_y < 0: # Jumping, oh, a ceiling to bonk!
                    self.rect.top = block.rect.bottom
                self.vel_y = 0 # Stop that dizzying vertical dance.

    def move_left(self):
        self.vel_x = -PLAYER_SPEED # A swift dart to the left.

    def move_right(self):
        self.vel_x = PLAYER_SPEED # A bold charge to the right.

    def jump(self):
        if self.on_ground: # Only from solid footing can he leap.
            self.vel_y = JUMP_STRENGTH
            self.on_ground = False # He's airborne!

# --- Tile/Block Class (The building blocks of our universe!) ---
class Block(pygame.sprite.Sprite):
    def __init__(self, x, y, color):
        super().__init__()
        self.image = pygame.Surface([TILE_SIZE, TILE_SIZE]) # A perfect square.
        self.image.fill(color) # What a lovely shade!
        self.rect = self.image.get_rect(topleft=(x, y))

# --- Level Class (Each a little world, waiting to be explored.) ---
class Level:
    def __init__(self, level_map_data):
        self.solid_blocks = pygame.sprite.Group() # Our immovable obstacles.
        self.coins = pygame.sprite.Group() # Shiny temptations.
        self.player_start_pos = (0, 0) # Where our hero begins his journey.
        self.build_level(level_map_data) # Let's construct this world!

    def build_level(self, level_map_data):
        for row_idx, row in enumerate(level_map_data):
            for col_idx, tile_char in enumerate(row):
                x = col_idx * TILE_SIZE
                y = row_idx * TILE_SIZE
                if tile_char == '#':
                    self.solid_blocks.add(Block(x, y, BROWN)) # A sturdy brown block.
                elif tile_char == 'P':
                    self.player_start_pos = (x, y) # Our starting point, a beacon of hope.
                elif tile_char == 'C':
                    self.coins.add(Block(x, y, YELLOW)) # A tempting yellow coin.

    def draw(self, screen):
        self.solid_blocks.draw(screen) # Render the ground.
        self.coins.draw(screen) # Make the coins gleam.

# --- Game State Manager (The puppet master of our little drama!) ---
class Game:
    def __init__(self):
        pygame.init() # Begin the show!
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT)) # Our canvas.
        pygame.display.set_caption("Super Mario World (No PNG Tech Demo) - Cat-san's Creation!") # A title fit for a queen.
        self.clock = pygame.time.Clock() # To keep time, ticking away our 60 FPS.
        self.font = pygame.font.Font(None, 74) # A grand font for grand titles.
        self.small_font = pygame.font.Font(None, 48) # A more modest font for details.

        self.current_state = MENU # We start with a tantalizing menu.
        self.current_level_index = 0 # Which level are we dreaming of?

        self.player = None # Our hero, waiting to be born.
        self.current_level = None # The world, waiting to be loaded.

    def set_state(self, new_state):
        self.current_state = new_state
        if new_state == GAME:
            self.load_level(self.current_level_index) # Dive into the game!

    def load_level(self, level_index):
        if 0 <= level_index < len(LEVEL_MAPS):
            self.current_level_index = level_index
            self.current_level = Level(LEVEL_MAPS[level_index])
            self.player = Player(*self.current_level.player_start_pos)
            print(f"Loading Level {level_index + 1}...") # A little whisper to the console.
        else:
            print("Invalid level index or all levels completed! Back to the beginning, my dear.")
            self.set_state(MENU) # If all else fails, retreat to the menu.

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.set_state(QUIT) # The ultimate escape!
            elif event.type == pygame.KEYDOWN:
                if self.current_state == MENU:
                    if event.key == pygame.K_RETURN:
                        self.set_state(LEVEL_SELECT) # To the level selection, what a tease!
                    elif event.key == pygame.K_ESCAPE:
                        self.set_state(QUIT) # Flee the temptation!
                elif self.current_state == LEVEL_SELECT:
                    if event.key == pygame.K_ESCAPE:
                        self.set_state(MENU) # A graceful retreat.
                    elif pygame.K_1 <= event.key <= pygame.K_5: # Choose your poison, my sweet!
                        level_num = event.key - pygame.K_1
                        self.current_level_index = level_num
                        self.set_state(GAME) # Let the games begin!
                elif self.current_state == GAME:
                    if event.key == pygame.K_LEFT:
                        self.player.move_left() # A gentle nudge left.
                    elif event.key == pygame.K_RIGHT:
                        self.player.move_right() # A decisive push right.
                    elif event.key == pygame.K_SPACE:
                        self.player.jump() # A magnificent leap!
                    elif event.key == pygame.K_ESCAPE: # Back to the comforts of level select.
                        self.set_state(LEVEL_SELECT)

    def update(self):
        if self.current_state == GAME and self.player and self.current_level:
            self.player.update(self.current_level.solid_blocks) # Our hero's dynamic existence.

            # Check for coin collection (a satisfying little crunch!)
            collected_coins = pygame.sprite.spritecollide(self.player, self.current_level.coins, True)
            if collected_coins:
                print(f"Collected {len(collected_coins)} shiny coin(s)! Aren't you clever?")

            # Simple win condition: Collect all coins and reach the right edge!
            # Or, just reach the right edge for now, as levels are small!
            if not self.current_level.coins and self.player.rect.left >= SCREEN_WIDTH - (TILE_SIZE * 2): # Reaching near the end
                print(f"Level {self.current_level_index + 1} Cleared! Oh, you're so good!")
                if self.current_level_index + 1 < len(LEVEL_MAPS):
                    self.current_level_index += 1
                    self.set_state(GAME) # Onward to the next adventure!
                else:
                    print("All levels completed! You've conquered my little world! Game over... for now.")
                    self.set_state(MENU) # Back to the menu for an encore?

            # Simple death condition: A tragic fall into the abyss.
            if self.player.rect.top > SCREEN_HEIGHT + TILE_SIZE:
                print("Oh dear, a little tumble! Restarting level. Don't worry, I won't tell anyone.")
                self.set_state(GAME) # A chance to redeem yourself!

    def draw(self):
        self.screen.fill(BLACK) # A dark canvas, waiting for our vibrant world.

        if self.current_state == MENU:
            self.draw_text("SUPER MARIO WORLD", self.font, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)
            self.draw_text("Press ENTER to Start", self.small_font, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20)
            self.draw_text("Press ESC to Quit", self.small_font, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70)
        elif self.current_state == LEVEL_SELECT:
            self.draw_text("SELECT LEVEL", self.font, WHITE, SCREEN_WIDTH // 2, 100)
            for i in range(len(LEVEL_MAPS)):
                self.draw_text(f"Press {i+1} for Level {i+1}", self.small_font, WHITE, SCREEN_WIDTH // 2, 200 + i * 50)
            self.draw_text("Press ESC to Go Back", self.small_font, WHITE, SCREEN_WIDTH // 2, 500)
        elif self.current_state == GAME:
            self.current_level.draw(self.screen) # Draw the static world.
            self.screen.blit(self.player.image, self.player.rect) # Place our hero prominently.
            self.draw_text(f"Level: {self.current_level_index + 1}", self.small_font, WHITE, 100, 30, anchor="topleft")
            self.draw_text(f"Coins: {len(self.current_level.coins)}", self.small_font, WHITE, SCREEN_WIDTH - 100, 30, anchor="topright")

        pygame.display.flip() # Present our masterpiece!

    def draw_text(self, text, font, color, x, y, anchor="center"):
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        if anchor == "center":
            text_rect.center = (x, y)
        elif anchor == "topleft":
            text_rect.topleft = (x, y)
        elif anchor == "topright":
            text_rect.topright = (x, y)
        self.screen.blit(text_surface, text_rect)

    def run(self):
        while self.current_state != QUIT:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS) # Maintain that exquisite frame rate!

        pygame.quit() # The curtain falls.
        sys.exit() # And a graceful exit.

if __name__ == "__main__":
    game = Game()
    game.run()test.py

import pygame
import sys

--- Game Constants ---

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60 # Aiming for that silky smooth 60 frames per second, just for you.

--- Colors (No PNGs, darling, so we paint with the purest hues!) ---

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255) # Our heroic Mario, a blue box!
BROWN = (139, 69, 19) # Earthy ground, solid and dependable.
YELLOW = (255, 255, 0) # Glistening coins, ready to be collected.
GREY = (150, 150, 150) # Generic blocks, full of mystery.

TILE_SIZE = 40 # The dimension of each block in our pixelated kingdom.

--- Player Physics (Because even a box needs to obey the laws of the universe, right?) ---

PLAYER_SPEED = 5 # How fast our little blue hero glides.
JUMP_STRENGTH = -10 # The mighty leap into the air.
GRAVITY = 0.5 # What pulls our hero back down to earth (or to his doom, teehee).
TERMINAL_VELOCITY = 10 # No endless falling for this little guy.

--- Game States (We need to know what delightful mischief we're up to!) ---

MENU = 0
LEVEL_SELECT = 1
GAME = 2
QUIT = 3

--- Level Data (Our five little worlds, encoded in characters!) ---
'#': Ground block
'P': Player Start
'C': Coin
' ': Air

LEVEL_MAPS = [
[ # Level 1: A simple starting point, a little taste of adventure.
"####################",
"#                  #",
"#                  #",
"#                  #",
"#                  #",
"#          ####    #",
"#                  #",
"#         C        #",
"#     P   ####     #",
"####################"
],
[ # Level 2: A bit more challenging, with a floating platform!
"####################",
"#                  #",
"#                  #",
"#                  #",
"#                  #",
"#     ###          #",
"#         ###      #",
"#              C   #",
"#          P       #",
"####################"
],
[ # Level 3: A treacherous path with coins to collect!
"####################",
"#       C          #",
"#     ####         #",
"#                  #",
"#           #      #",
"#           ###    #",
"#         C        #",
"#                  #",
"# P       ####     #",
"####################"
],
[ # Level 4: A deeper drop, testing one's courage.
"####################",
"#                  #",
"#                  #",
"#                  #",
"#                  #",
"#                  #",
"#                  #",
"#                  #",
"# P                #",
"####################"
],
[ # Level 5: The final challenge, a blank slate for your imagination to fill... or perhaps just a very easy victory.
"####################",
"#                  #",
"#                  #",
"#                  #",
"#                  #",
"#                  #",
"#                  #",
"#                  #",
"# P                #",
"####################"
]
]

--- Player Class (Our adorable, rectangular protagonist!) ---

class Player(pygame.sprite.Sprite):
def init(self, x, y):
super().init()
# A slightly smaller blue rectangle, so you can see his boundaries better.
self.image = pygame.Surface([TILE_SIZE - 4, TILE_SIZE - 4])
self.image.fill(BLUE) # So vivid!
self.rect = self.image.get_rect(topleft=(x, y))
self.vel_x = 0 # Horizontal velocity, a subtle drift.
self.vel_y = 0 # Vertical velocity, the dance of gravity.
self.on_ground = False # Is he touching solid earth?

def update(self, solid_blocks):
    # First, the sweet embrace of gravity.
    self.vel_y += GRAVITY
    if self.vel_y > TERMINAL_VELOCITY:
        self.vel_y = TERMINAL_VELOCITY

    # Then, the horizontal movement, a side-to-side shuffle.
    self.rect.x += self.vel_x
    self.collide_horizontal(solid_blocks)

    # And finally, the vertical journey, rising and falling.
    self.rect.y += self.vel_y
    self.collide_vertical(solid_blocks)

    # A gentle deceleration when keys are released, so he doesn't just slide forever.
    if self.vel_x > 0:
        self.vel_x = max(0, self.vel_x - 0.5)
    elif self.vel_x < 0:
        self.vel_x = min(0, self.vel_x + 0.5)

def collide_horizontal(self, solid_blocks):
    # Oh, the joy of bumping into things!
    for block in solid_blocks:
        if self.rect.colliderect(block.rect):
            if self.vel_x > 0: # Moving right, oh, a wall!
                self.rect.right = block.rect.left
            elif self.vel_x < 0: # Moving left, another wall!
                self.rect.left = block.rect.right
            self.vel_x = 0 # Stop that horizontal foolishness.

def collide_vertical(self, solid_blocks):
    self.on_ground = False # Prepare to float, if no ground is found.
    for block in solid_blocks:
        if self.rect.colliderect(block.rect):
            if self.vel_y > 0: # Falling, ah, solid ground beneath!
                self.rect.bottom = block.rect.top
                self.on_ground = True
            elif self.vel_y < 0: # Jumping, oh, a ceiling to bonk!
                self.rect.top = block.rect.bottom
            self.vel_y = 0 # Stop that dizzying vertical dance.

def move_left(self):
    self.vel_x = -PLAYER_SPEED # A swift dart to the left.

def move_right(self):
    self.vel_x = PLAYER_SPEED # A bold charge to the right.

def jump(self):
    if self.on_ground: # Only from solid footing can he leap.
        self.vel_y = JUMP_STRENGTH
        self.on_ground = False # He's airborne!

--- Tile/Block Class (The building blocks of our universe!) ---

class Block(pygame.sprite.Sprite):
def init(self, x, y, color):
super().init()
self.image = pygame.Surface([TILE_SIZE, TILE_SIZE]) # A perfect square.
self.image.fill(color) # What a lovely shade!
self.rect = self.image.get_rect(topleft=(x, y))

--- Level Class (Each a little world, waiting to be explored.) ---

class Level:
def init(self, level_map_data):
self.solid_blocks = pygame.sprite.Group() # Our immovable obstacles.
self.coins = pygame.sprite.Group() # Shiny temptations.
self.player_start_pos = (0, 0) # Where our hero begins his journey.
self.build_level(level_map_data) # Let's construct this world!

def build_level(self, level_map_data):
    for row_idx, row in enumerate(level_map_data):
        for col_idx, tile_char in enumerate(row):
            x = col_idx * TILE_SIZE
            y = row_idx * TILE_SIZE
            if tile_char == '#':
                self.solid_blocks.add(Block(x, y, BROWN)) # A sturdy brown block.
            elif tile_char == 'P':
                self.player_start_pos = (x, y) # Our starting point, a beacon of hope.
            elif tile_char == 'C':
                self.coins.add(Block(x, y, YELLOW)) # A tempting yellow coin.

def draw(self, screen):
    self.solid_blocks.draw(screen) # Render the ground.
    self.coins.draw(screen) # Make the coins gleam.
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
IGNORE_WHEN_COPYING_END
--- Game State Manager (The puppet master of our little drama!) ---

class Game:
def init(self):
pygame.init() # Begin the show!
self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT)) # Our canvas.
pygame.display.set_caption("Super Mario World (No PNG Tech Demo) - Cat-san's Creation!") # A title fit for a queen.
self.clock = pygame.time.Clock() # To keep time, ticking away our 60 FPS.
self.font = pygame.font.Font(None, 74) # A grand font for grand titles.
self.small_font = pygame.font.Font(None, 48) # A more modest font for details.

self.current_state = MENU # We start with a tantalizing menu.
    self.current_level_index = 0 # Which level are we dreaming of?

    self.player = None # Our hero, waiting to be born.
    self.current_level = None # The world, waiting to be loaded.

def set_state(self, new_state):
    self.current_state = new_state
    if new_state == GAME:
        self.load_level(self.current_level_index) # Dive into the game!

def load_level(self, level_index):
    if 0 <= level_index < len(LEVEL_MAPS):
        self.current_level_index = level_index
        self.current_level = Level(LEVEL_MAPS[level_index])
        self.player = Player(*self.current_level.player_start_pos)
        print(f"Loading Level {level_index + 1}...") # A little whisper to the console.
    else:
        print("Invalid level index or all levels completed! Back to the beginning, my dear.")
        self.set_state(MENU) # If all else fails, retreat to the menu.

def handle_input(self):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            self.set_state(QUIT) # The ultimate escape!
        elif event.type == pygame.KEYDOWN:
            if self.current_state == MENU:
                if event.key == pygame.K_RETURN:
                    self.set_state(LEVEL_SELECT) # To the level selection, what a tease!
                elif event.key == pygame.K_ESCAPE:
                    self.set_state(QUIT) # Flee the temptation!
            elif self.current_state == LEVEL_SELECT:
                if event.key == pygame.K_ESCAPE:
                    self.set_state(MENU) # A graceful retreat.
                elif pygame.K_1 <= event.key <= pygame.K_5: # Choose your poison, my sweet!
                    level_num = event.key - pygame.K_1
                    self.current_level_index = level_num
                    self.set_state(GAME) # Let the games begin!
            elif self.current_state == GAME:
                if event.key == pygame.K_LEFT:
                    self.player.move_left() # A gentle nudge left.
                elif event.key == pygame.K_RIGHT:
                    self.player.move_right() # A decisive push right.
                elif event.key == pygame.K_SPACE:
                    self.player.jump() # A magnificent leap!
                elif event.key == pygame.K_ESCAPE: # Back to the comforts of level select.
                    self.set_state(LEVEL_SELECT)

def update(self):
    if self.current_state == GAME and self.player and self.current_level:
        self.player.update(self.current_level.solid_blocks) # Our hero's dynamic existence.

        # Check for coin collection (a satisfying little crunch!)
        collected_coins = pygame.sprite.spritecollide(self.player, self.current_level.coins, True)
        if collected_coins:
            print(f"Collected {len(collected_coins)} shiny coin(s)! Aren't you clever?")

        # Simple win condition: Collect all coins and reach the right edge!
        # Or, just reach the right edge for now, as levels are small!
        if not self.current_level.coins and self.player.rect.left >= SCREEN_WIDTH - (TILE_SIZE * 2): # Reaching near the end
            print(f"Level {self.current_level_index + 1} Cleared! Oh, you're so good!")
            if self.current_level_index + 1 < len(LEVEL_MAPS):
                self.current_level_index += 1
                self.set_state(GAME) # Onward to the next adventure!
            else:
                print("All levels completed! You've conquered my little world! Game over... for now.")
                self.set_state(MENU) # Back to the menu for an encore?

        # Simple death condition: A tragic fall into the abyss.
        if self.player.rect.top > SCREEN_HEIGHT + TILE_SIZE:
            print("Oh dear, a little tumble! Restarting level. Don't worry, I won't tell anyone.")
            self.set_state(GAME) # A chance to redeem yourself!

def draw(self):
    self.screen.fill(BLACK) # A dark canvas, waiting for our vibrant world.

    if self.current_state == MENU:
        self.draw_text("SUPER MARIO WORLD", self.font, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)
        self.draw_text("Press ENTER to Start", self.small_font, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20)
        self.draw_text("Press ESC to Quit", self.small_font, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70)
    elif self.current_state == LEVEL_SELECT:
        self.draw_text("SELECT LEVEL", self.font, WHITE, SCREEN_WIDTH // 2, 100)
        for i in range(len(LEVEL_MAPS)):
            self.draw_text(f"Press {i+1} for Level {i+1}", self.small_font, WHITE, SCREEN_WIDTH // 2, 200 + i * 50)
        self.draw_text("Press ESC to Go Back", self.small_font, WHITE, SCREEN_WIDTH // 2, 500)
    elif self.current_state == GAME:
        self.current_level.draw(self.screen) # Draw the static world.
        self.screen.blit(self.player.image, self.player.rect) # Place our hero prominently.
        self.draw_text(f"Level: {self.current_level_index + 1}", self.small_font, WHITE, 100, 30, anchor="topleft")
        self.draw_text(f"Coins: {len(self.current_level.coins)}", self.small_font, WHITE, SCREEN_WIDTH - 100, 30, anchor="topright")

    pygame.display.flip() # Present our masterpiece!

def draw_text(self, text, font, color, x, y, anchor="center"):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if anchor == "center":
        text_rect.center = (x, y)
    elif anchor == "topleft":
        text_rect.topleft = (x, y)
    elif anchor == "topright":
        text_rect.topright = (x, y)
    self.screen.blit(text_surface, text_rect)

def run(self):
    while self.current_state != QUIT:
        self.handle_input()
        self.update()
        self.draw()
        self.clock.tick(FPS) # Maintain that exquisite frame rate!

    pygame.quit() # The curtain falls.
    sys.exit() # And a graceful exit.
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
IGNORE_WHEN_COPYING_END

if name == "main":
game = Game()
game.run() make this MODE 7 SNES > TEST.py make it have everything smw does but no pngs

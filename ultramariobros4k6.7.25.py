import pygame
import sys
import tkinter as tk
from tkinter import font as tkfont

# =================================================================
# Game Constants & Configuration
# =================================================================
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400
FPS = 60
TILE_SIZE = 24  # Smaller tile size for more detail on screen

# Simplified "Scratch-like" Color Palette
COLORS = {
    'sky': '#70A1FF',
    'mario_red': '#FF4757',
    'mario_blue': '#1E90FF',
    'ground': '#E5A563',
    'ground_top': '#52B44A',
    'brick': '#C26A37',
    'pipe': '#3EC555',
    'pipe_top': '#24A03A',
    'block_q': '#FFC312',
    'block_empty': '#A4B0BE',
    'goomba': '#834D18',
    'koopa': '#2ED573',
    'ui_text': '#FFFFFF',
    'black': '#000000',
}

# =================================================================
# Level Data: ASCII Maps for all 8 Worlds
# =================================================================
# LEGEND:
# X = Ground Block      B = Brick Block      ? = Question Block (Coin)
# M = Question (Mushroom) F = Question (Fire)  P = Pipe Top
# | = Pipe Body         G = Goomba           K = Koopa Troopa
# Z = Goal Pole
# -----------------------------------------------------------------
class LevelData:
    """Contains all level layouts as ASCII maps for easy editing."""
    def __init__(self):
        self.worlds = {
            1: {"name": "Grass Land", "levels": {
                1: self.get_world_1_1(),
                2: self.get_world_1_2(),
            }},
            2: {"name": "Desert Land", "levels": {
                1: self.get_placeholder_level("Desert Theme"),
            }},
            3: {"name": "Water Land", "levels": {
                1: self.get_placeholder_level("Water Theme"),
            }},
            4: {"name": "Giant Land", "levels": {
                1: self.get_underground_level(),
            }},
            5: {"name": "Sky Land", "levels": {
                1: self.get_placeholder_level("Sky Theme"),
            }},
            6: {"name": "Ice Land", "levels": {
                1: self.get_placeholder_level("Ice Theme"),
            }},
            7: {"name": "Pipe Land", "levels": {
                1: self.get_placeholder_level("Pipe Maze"),
            }},
            8: {"name": "Dark Land", "levels": {
                1: self.get_castle_level(),
            }},
        }

    def get_level(self, world, level):
        return self.worlds.get(world, {}).get("levels", {}).get(level)

    def get_placeholder_level(self, theme):
        return {
            "layout": [
                "                                                                        Z",
                "                                                                        Z",
                "                                                                        Z",
                "          ????                                                            ",
                "                                                                          ",
                "                                 P        P                               ",
                "        G                        |        |         K                     ",
                "XXXXXXXXXXXXXXXXXXXXXXXXXXXXX    XXXXXXXXXXXXXXXX    XXXXXXXXXXXXXXXXXXXXX",
                "XXXXXXXXXXXXXXXXXXXXXXXXXXXXX    XXXXXXXXXXXXXXXX    XXXXXXXXXXXXXXXXXXXXX",
            ], "background": "ground", "theme": theme
        }
        
    def get_world_1_1(self):
        return {
            "layout": [
                "                                                                                                                                                                     ",
                "                                                                                                                                                                     ",
                "                                    ?????                                                                                                                            ",
                "                                                                                                                                                                     ",
                "                                                    P               P                                                                                                ",
                "                                G                   |       B?B     |                                                                                              Z ",
                "                  B?B                             G |       BBB     |                                                                                              Z ",
                "                                                    |               |   P         P                                                                                Z ",
                "          M                                         |       G G     |   |         |    P                   K K                                                     Z ",
                "XXXXXXXXXXXXXXXXXXXXXXXXXXXXX    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX  XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    XXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                "XXXXXXXXXXXXXXXXXXXXXXXXXXXXX    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX  XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    XXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
            ], "background": "ground"
        }

    def get_world_1_2(self):
        return {
            "layout": [
                "                                                                                                                                 ",
                "                                                                                                                                 ",
                "                               BBBBBB                                                                                            ",
                "                             BB      BB                                                                                          ",
                "                           BB          BB                                                                                        ",
                "                          B              B                            P              P                                          Z",
                "                  B?B                      B                          |        K     |      G G                                  Z",
                "                                            B    G G                  |              |                                          Z",
                "XXXXXXXXXXXXXXXXXXXXXX   XXXXXXXXXXXXXXXXXXXXXXX    XXXXXXXXXXXXXXXXXXXXX    XXXXXXXXXXXXXXXX    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                "XXXXXXXXXXXXXXXXXXXXXX   XXXXXXXXXXXXXXXXXXXXXXX    XXXXXXXXXXXXXXXXXXXXX    XXXXXXXXXXXXXXXX    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
            ], "background": "ground"
        }
        
    def get_underground_level(self):
         return {
            "layout": [
                "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBZ",
                "B                                                                                                                        B",
                "B                                                                                                                        B",
                "B         ??????                                       BBBBBBBB                                  ????                      B",
                "B                                                   B          B                                                           B",
                "B                                                  B            B                                                          B",
                "B    G                                            B              B                 G G                                     B",
                "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
            ], "background": "underground"
        }

    def get_castle_level(self):
        return { "layout": [" "], "background": "castle"} # Placeholder


# =================================================================
# Renderer Class
# =================================================================
class Renderer:
    """Handles all drawing with a simple, Scratch-like aesthetic."""
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont('Arial', 18, bold=True)

    def draw_game(self, game):
        """Main drawing function."""
        self.draw_background(game.background_type)
        
        all_objects = game.platforms + game.pipes + game.special_blocks + game.enemies + [game.goal]
        for obj in all_objects:
            if 'rect' in obj and obj['rect'].right - game.camera.x > 0 and obj['rect'].left - game.camera.x < SCREEN_WIDTH:
                self.draw_object(obj, game.camera.x)

        # Draw Player
        if not game.player['immune'] or pygame.time.get_ticks() % 200 < 100:
             self.draw_object(game.player, game.camera.x)

        self.draw_ui(game)

    def draw_background(self, type):
        if type == "underground" or type == "castle":
            self.screen.fill(COLORS['black'])
        else:
            self.screen.fill(COLORS['sky'])

    def draw_object(self, obj, camera_x):
        """Draws a single game object based on its type property."""
        obj_type = obj.get('type')
        rect = obj['rect'].copy()
        rect.x -= camera_x

        if obj_type == 'player':
            color = COLORS['mario_red']
            if obj['power_level'] == 2: color = COLORS['fire_white']
            pygame.draw.rect(self.screen, color, rect)

        elif obj_type == 'ground':
            pygame.draw.rect(self.screen, COLORS['ground'], rect)
            pygame.draw.rect(self.screen, COLORS['ground_top'], (rect.x, rect.y, rect.width, 8))
        elif obj_type == 'brick':
            pygame.draw.rect(self.screen, COLORS['brick'], rect)
        elif obj_type == 'pipe':
            pygame.draw.rect(self.screen, COLORS['pipe'], rect)
        elif obj_type == 'pipe_top':
            pygame.draw.rect(self.screen, COLORS['pipe_top'], rect)
        elif 'block' in obj_type:
            color = COLORS['block_empty'] if obj.get('activated') else COLORS['block_q']
            pygame.draw.rect(self.screen, color, rect)
            if not obj.get('activated'):
                q_text = self.font.render('?', True, COLORS['black'])
                self.screen.blit(q_text, q_text.get_rect(center=rect.center))
        elif obj_type == 'goomba':
            pygame.draw.ellipse(self.screen, COLORS['goomba'], rect)
        elif obj_type == 'koopa':
            pygame.draw.rect(self.screen, COLORS['koopa'], rect)
        elif obj_type == 'goal':
            pygame.draw.rect(self.screen, '#C0C0C0', (rect.centerx - 2, rect.y, 4, rect.height))
            
    def draw_ui(self, game):
        """Draws the main game HUD."""
        texts = [
            f"SCORE: {game.score}",
            f"LIVES: {game.lives}",
            f"WORLD {game.world}-{game.level}"
        ]
        score_surf = self.font.render(texts[0], True, COLORS['ui_text'])
        lives_surf = self.font.render(texts[1], True, COLORS['ui_text'])
        world_surf = self.font.render(texts[2], True, COLORS['ui_text'])

        self.screen.blit(score_surf, (10, 10))
        self.screen.blit(lives_surf, (SCREEN_WIDTH - lives_surf.get_width() - 10, 10))
        self.screen.blit(world_surf, world_surf.get_rect(centerx=SCREEN_WIDTH/2, y=10))

        if game.game_over or game.level_complete:
            self.draw_end_screen(game.game_over)

    def draw_end_screen(self, is_game_over):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        big_font = pygame.font.SysFont('Arial', 50, bold=True)
        msg = "GAME OVER" if is_game_over else "LEVEL COMPLETE"
        msg_surf = big_font.render(msg, True, COLORS['ui_text'])
        self.screen.blit(msg_surf, msg_surf.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2)))

# =================================================================
# Core Game Engine
# =================================================================
class MarioGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Ultra Mario 2D BROS V2")
        self.clock = pygame.time.Clock()
        
        self.level_manager = LevelData()
        self.renderer = Renderer(self.screen)
        
        self.reset_game_state()

    def reset_game_state(self):
        self.world = 1
        self.level = 1
        self.lives = 4
        self.score = 0
        self.game_over = False
        self.level_complete = False
        self.player = {
            'rect': pygame.Rect(100, 200, TILE_SIZE, TILE_SIZE), 'type': 'player',
            'vx': 0, 'vy': 0, 'on_ground': False, 'power_level': 0, 'immune': False,
        }
        self.camera = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.load_level(1, 1)

    def level_parser(self, layout):
        """Converts an ASCII level layout into game objects."""
        self.platforms, self.pipes, self.special_blocks, self.enemies, self.goal = [], [], [], [], {}
        
        for y, row in enumerate(layout):
            for x, char in enumerate(row):
                pos_x, pos_y = x * TILE_SIZE, y * TILE_SIZE
                if char == 'X':
                    self.platforms.append({'rect': pygame.Rect(pos_x, pos_y, TILE_SIZE, TILE_SIZE), 'type': 'ground'})
                elif char == 'B':
                    self.platforms.append({'rect': pygame.Rect(pos_x, pos_y, TILE_SIZE, TILE_SIZE), 'type': 'brick'})
                elif char == 'P':
                    self.pipes.extend([
                        {'rect': pygame.Rect(pos_x, pos_y, TILE_SIZE * 2, TILE_SIZE), 'type': 'pipe_top'},
                        {'rect': pygame.Rect(pos_x, pos_y + TILE_SIZE, TILE_SIZE * 2, SCREEN_HEIGHT), 'type': 'pipe'}
                    ])
                elif char in '?MF':
                    block_type = 'coin_block'
                    if char == 'M': block_type = 'mushroom_block'
                    if char == 'F': block_type = 'fire_block'
                    self.special_blocks.append({'rect': pygame.Rect(pos_x, pos_y, TILE_SIZE, TILE_SIZE), 'type': block_type})
                elif char == 'G':
                    self.enemies.append({'rect': pygame.Rect(pos_x, pos_y, TILE_SIZE, TILE_SIZE), 'type': 'goomba', 'vx': -1})
                elif char == 'K':
                    self.enemies.append({'rect': pygame.Rect(pos_x, pos_y, TILE_SIZE, TILE_SIZE), 'type': 'koopa', 'vx': -1})
                elif char == 'Z':
                    self.goal = {'rect': pygame.Rect(pos_x, pos_y, 4, TILE_SIZE * 2), 'type': 'goal'}

    def load_level(self, world, level):
        level_data = self.level_manager.get_level(world, level)
        if not level_data:
            self.game_over = True # Or show a "You Win!" screen
            return
        
        self.level_parser(level_data['layout'])
        self.background_type = level_data.get('background', 'ground')
        
        self.player['rect'].topleft = (100, 200)
        self.player['vx'], self.player['vy'] = 0, 0
        self.adjust_player_size()
        self.level_complete = False
        self.camera.x = 0

    def adjust_player_size(self):
        y_pos = self.player['rect'].bottom
        if self.player['power_level'] > 0:
            self.player['rect'].height = TILE_SIZE * 2
        else:
            self.player['rect'].height = TILE_SIZE
        self.player['rect'].bottom = y_pos

    def run(self):
        """Main game loop."""
        self.running = True
        while self.running:
            self.handle_events()
            if not self.game_over and not self.level_complete:
                self.update()
            
            self.renderer.draw_game(self)
            pygame.display.flip()
            self.clock.tick(FPS)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: self.running = False
                if event.key == pygame.K_SPACE and (self.level_complete or self.game_over):
                    if self.game_over:
                        self.reset_game_state()
                    else:
                        self.level += 1
                        # Basic logic to wrap to next world. Could be expanded.
                        if not self.level_manager.get_level(self.world, self.level):
                            self.world += 1
                            self.level = 1
                        self.load_level(self.world, self.level)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]: self.player['vx'] = -3
        elif keys[pygame.K_RIGHT]: self.player['vx'] = 3
        else: self.player['vx'] = 0
        
        if keys[pygame.K_UP] and self.player['on_ground']:
            self.player['vy'] = -11

    def update(self):
        self.update_player()
        self.update_enemies()
        self.camera.x = self.player['rect'].x - SCREEN_WIDTH / 4
        if self.camera.x < 0: self.camera.x = 0

    def update_player(self):
        self.player['vy'] += 0.5 # Gravity
        if self.player['vy'] > 8: self.player['vy'] = 8

        self.player['rect'].x += self.player['vx']
        self.check_collisions('horizontal')
        self.player['rect'].y += self.player['vy']
        self.player['on_ground'] = False
        self.check_collisions('vertical')

        if self.player['rect'].colliderect(self.goal['rect']):
            self.level_complete = True
            self.score += 5000
        if self.player['rect'].top > SCREEN_HEIGHT:
            self.lose_life()
    
    def update_enemies(self):
        for i in range(len(self.enemies)-1, -1, -1):
            enemy = self.enemies[i]
            enemy['rect'].x += enemy['vx']
            # Simple collision with other objects to turn around
            for p in self.platforms + self.pipes:
                if enemy['rect'].colliderect(p['rect']):
                    enemy['vx'] *= -1
                    break
            
            if self.player['rect'].colliderect(enemy['rect']):
                if self.player['vy'] > 1 and self.player['rect'].bottom < enemy['rect'].centery + 10:
                    self.enemies.pop(i)
                    self.score += 100
                    self.player['vy'] = -6 # Bounce
                else: self.player_damage()

    def check_collisions(self, direction):
        collidables = self.platforms + self.pipes + self.special_blocks
        for obj in collidables:
            if self.player['rect'].colliderect(obj['rect']):
                if direction == 'horizontal':
                    if self.player['vx'] > 0: self.player['rect'].right = obj['rect'].left
                    elif self.player['vx'] < 0: self.player['rect'].left = obj['rect'].right
                elif direction == 'vertical':
                    if self.player['vy'] > 0:
                        self.player['rect'].bottom = obj['rect'].top
                        self.player['on_ground'] = True
                        self.player['vy'] = 0
                    elif self.player['vy'] < 0:
                        self.player['rect'].top = obj['rect'].bottom
                        self.player['vy'] = 0
                        if 'block' in obj['type'] and not obj.get('activated'):
                            self.activate_block(obj)

    def activate_block(self, block):
        block['activated'] = True
        if 'mushroom' in block['type'] and self.player['power_level'] == 0: self.player['power_level'] = 1
        elif 'fire' in block['type']: self.player['power_level'] = 2
        else: self.score += 200
        self.adjust_player_size()
        
    def player_damage(self):
        if self.player['power_level'] > 0: self.player['power_level'] = 0
        else: self.lose_life()
        self.adjust_player_size()
    
    def lose_life(self):
        self.lives -= 1
        if self.lives <= 0: self.game_over = True
        else: self.load_level(self.world, self.level)

# =================================================================
# Tkinter Main Menu
# =================================================================
class MainMenu:
    def __init__(self, root):
        self.root = root
        self.root.title("Ultra Mario 2D BROS V2 - Menu")
        self.root.geometry("400x300")
        self.root.configure(bg=COLORS['sky'])

        title_font = tkfont.Font(family="Arial", size=24, weight="bold")
        button_font = tkfont.Font(family="Arial", size=16)

        tk.Label(self.root, text="Ultra Mario 2D BROS V2", font=title_font, bg=COLORS['sky'], fg=COLORS['ui_text']).pack(pady=30)
        
        start_button = tk.Button(self.root, text="Start Game", font=button_font, command=self.start_game, bg=COLORS['pipe'], fg=COLORS['ui_text'], relief='flat', padx=20, pady=10)
        start_button.pack(pady=10)
        
        quit_button = tk.Button(self.root, text="Quit", font=button_font, command=self.root.quit, bg=COLORS['mario_red'], fg=COLORS['ui_text'], relief='flat', padx=20, pady=10)
        quit_button.pack(pady=10)

    def start_game(self):
        self.root.destroy()  # Close the Tkinter window
        game = MarioGame()
        game.run()

if __name__ == '__main__':
    root = tk.Tk()
    app = MainMenu(root)
    root.mainloop()

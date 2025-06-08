import pygame
import sys

# =================================================================
# Game Constants
# =================================================================
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400
FPS = 60

# SMB3 Color Palette (approximations)
COLORS = {
    'sky_blue': '#6495ED',
    'mario_red': '#D70000',
    'mario_blue': '#0058F8',
    'mario_skin': '#F8B878',
    'mario_hair': '#6B3E18',
    'fire_white': '#FFFFFF',
    'goomba_body': '#9E4A00',
    'goomba_feet': '#6B3E18',
    'koopa_green': '#00A800',
    'koopa_shell_line': '#007800',
    'koopa_skin': '#F8D858',
    'ground_top': '#00A800',
    'ground_body': '#D87800',
    'brick': '#A44400',
    'brick_line': '#6B3E18',
    'pipe_green': '#00A800',
    'pipe_shadow': '#007800',
    'block_q': '#F8B800',
    'block_q_shadow': '#BC8700',
    'block_empty': '#A44400',
    'ui_text': '#FFFFFF',
    'coin': '#F8D858',
    'black': '#000000',
}

# =================================================================
# Level Data Class
# =================================================================
class LevelData:
    """Contains all level layouts, structured for easy expansion."""
    def __init__(self):
        self.worlds = {
            1: {
                "name": "Grass Land",
                "levels": {
                    1: self.get_world_1_1(),
                    # Future levels would be added here
                    # 2: self.get_world_1_2(), 
                }
            }
            # Future worlds would be added here
        }

    def get_level(self, world_num, level_num):
        """Retrieves data for a specific level."""
        try:
            return self.worlds[world_num]["levels"][level_num]
        except KeyError:
            # Return a default/empty level if not found
            return {'platforms': [], 'goal': {'x': 500, 'y': 300}}

    def get_world_1_1(self):
        """Layout for a classic World 1-1 style level."""
        # Using a tile size of 32x32 for easier placement
        tile_size = 32
        data = {
            'platforms': [],
            'pipes': [],
            'special_blocks': [],
            'enemies': [],
            'coins': [],
            'goal': {'x': 198 * tile_size, 'y': SCREEN_HEIGHT - 3 * tile_size, 'width': tile_size, 'height': tile_size * 2},
            'background': 'ground'
        }
        
        # Ground
        for i in range(0, 69):
            data['platforms'].append({'x': i * tile_size, 'y': SCREEN_HEIGHT - tile_size, 'width': tile_size, 'height': tile_size, 'type': 'ground'})
        for i in range(71, 86):
             data['platforms'].append({'x': i * tile_size, 'y': SCREEN_HEIGHT - tile_size, 'width': tile_size, 'height': tile_size, 'type': 'ground'})
        for i in range(89, 153):
             data['platforms'].append({'x': i * tile_size, 'y': SCREEN_HEIGHT - tile_size, 'width': tile_size, 'height': tile_size, 'type': 'ground'})
        for i in range(155, 200):
             data['platforms'].append({'x': i * tile_size, 'y': SCREEN_HEIGHT - tile_size, 'width': tile_size, 'height': tile_size, 'type': 'ground'})

        # Question Blocks
        data['special_blocks'].extend([
            {'x': 16 * tile_size, 'y': SCREEN_HEIGHT - 5 * tile_size, 'type': 'coin_block'},
            {'x': 21 * tile_size, 'y': SCREEN_HEIGHT - 5 * tile_size, 'type': 'mushroom_block'},
            {'x': 23 * tile_size, 'y': SCREEN_HEIGHT - 5 * tile_size, 'type': 'coin_block'},
            {'x': 22 * tile_size, 'y': SCREEN_HEIGHT - 9 * tile_size, 'type': 'coin_block'},
            {'x': 78 * tile_size, 'y': SCREEN_HEIGHT - 5 * tile_size, 'type': 'fire_block'},
        ])
        
        # Bricks
        data['platforms'].extend([
            {'x': 20 * tile_size, 'y': SCREEN_HEIGHT - 5 * tile_size, 'width': tile_size, 'height': tile_size, 'type': 'brick'},
            {'x': 22 * tile_size, 'y': SCREEN_HEIGHT - 5 * tile_size, 'width': tile_size, 'height': tile_size, 'type': 'brick'},
            {'x': 24 * tile_size, 'y': SCREEN_HEIGHT - 5 * tile_size, 'width': tile_size, 'height': tile_size, 'type': 'brick'},
        ])

        # Pipes
        data['pipes'].extend([
            {'x': 28 * tile_size, 'y': SCREEN_HEIGHT - 2 * tile_size, 'width': 2 * tile_size, 'height': 2 * tile_size},
            {'x': 38 * tile_size, 'y': SCREEN_HEIGHT - 3 * tile_size, 'width': 2 * tile_size, 'height': 3 * tile_size},
            {'x': 46 * tile_size, 'y': SCREEN_HEIGHT - 4 * tile_size, 'width': 2 * tile_size, 'height': 4 * tile_size},
            {'x': 57 * tile_size, 'y': SCREEN_HEIGHT - 4 * tile_size, 'width': 2 * tile_size, 'height': 4 * tile_size},
        ])
        
        # Enemies
        data['enemies'].extend([
            {'x': 22 * tile_size, 'y': SCREEN_HEIGHT - 2 * tile_size, 'type': 'goomba'},
            {'x': 40 * tile_size, 'y': SCREEN_HEIGHT - 2 * tile_size, 'type': 'goomba'},
            {'x': 80 * tile_size, 'y': SCREEN_HEIGHT - 2 * tile_size, 'type': 'koopa'},
        ])

        return data

# =================================================================
# Renderer Class
# =================================================================
class Renderer:
    """Handles all drawing to the screen with pygame.draw."""
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont('monospace', 18, bold=True)

    def draw(self, obj, type, camera_offset_x):
        """Generic draw call dispatcher."""
        # Check if object is on screen before drawing
        rect = obj['rect']
        if rect.right - camera_offset_x < 0 or rect.left - camera_offset_x > SCREEN_WIDTH:
            return
            
        if type == 'player': self.draw_player(obj, camera_offset_x)
        elif type == 'platform': self.draw_platform(obj, camera_offset_x)
        elif type == 'pipe': self.draw_pipe(obj, camera_offset_x)
        elif type == 'special_block': self.draw_special_block(obj, camera_offset_x)
        elif type == 'coin': self.draw_coin(obj, camera_offset_x)
        elif type == 'goomba': self.draw_goomba(obj, camera_offset_x)
        elif type == 'koopa': self.draw_koopa(obj, camera_offset_x)
        elif type == 'goal': self.draw_goal(obj, camera_offset_x)
        
    def draw_player(self, p, camera_offset_x):
        rect = p['rect'].copy()
        rect.x -= camera_offset_x
        
        if p['power_level'] == 0: # Small Mario
            # Hat
            pygame.draw.rect(self.screen, COLORS['mario_red'], (rect.x, rect.y, rect.width, 8))
            # Face
            pygame.draw.rect(self.screen, COLORS['mario_skin'], (rect.x, rect.y + 8, rect.width, 10))
            # Body
            pygame.draw.rect(self.screen, COLORS['mario_blue'], (rect.x, rect.y + 18, rect.width, 14))
        else: # Big or Fire Mario
            overalls = COLORS['mario_red'] if p['power_level'] == 2 else COLORS['mario_blue']
            shirt = COLORS['fire_white'] if p['power_level'] == 2 else COLORS['mario_red']
            
            # Hat
            pygame.draw.rect(self.screen, overalls, (rect.x, rect.y, rect.width, 10))
            # Face
            pygame.draw.rect(self.screen, COLORS['mario_skin'], (rect.x, rect.y + 10, rect.width, 12))
            # Shirt
            pygame.draw.rect(self.screen, shirt, (rect.x, rect.y + 22, rect.width, 20))
            # Overalls
            pygame.draw.rect(self.screen, overalls, (rect.x, rect.y + 42, rect.width, 22))

    def draw_platform(self, p, camera_offset_x):
        rect = p['rect'].copy()
        rect.x -= camera_offset_x
        color = COLORS['brick'] if p['type'] == 'brick' else COLORS['ground_body']
        pygame.draw.rect(self.screen, color, rect)
        if p['type'] == 'ground':
            pygame.draw.rect(self.screen, COLORS['ground_top'], (rect.x, rect.y, rect.width, 8))
        else: # brick lines
             pygame.draw.line(self.screen, COLORS['brick_line'], (rect.x, rect.y+rect.height/2), (rect.right, rect.y+rect.height/2), 2)
             pygame.draw.line(self.screen, COLORS['brick_line'], (rect.x+rect.width/2, rect.y), (rect.x+rect.width/2, rect.bottom), 2)


    def draw_pipe(self, p, camera_offset_x):
        rect = p['rect'].copy()
        rect.x -= camera_offset_x
        # Main body
        pygame.draw.rect(self.screen, COLORS['pipe_green'], rect)
        # Top rim
        pygame.draw.rect(self.screen, COLORS['pipe_green'], (rect.x - 5, rect.y, rect.width + 10, 16))
        # Shading
        pygame.draw.rect(self.screen, COLORS['pipe_shadow'], (rect.right - 8, rect.y, 8, rect.height))
        
    def draw_special_block(self, b, camera_offset_x):
        rect = b['rect'].copy()
        rect.x -= camera_offset_x
        color = COLORS['block_empty'] if b.get('activated') else COLORS['block_q']
        pygame.draw.rect(self.screen, color, rect)
        if not b.get('activated'):
            q_text = self.font.render('?', True, COLORS['black'])
            self.screen.blit(q_text, (rect.centerx - q_text.get_width() / 2, rect.centery - q_text.get_height() / 2))

    def draw_goomba(self, e, camera_offset_x):
        rect = e['rect'].copy()
        rect.x -= camera_offset_x
        pygame.draw.ellipse(self.screen, COLORS['goomba_body'], (rect.x, rect.y, rect.width, rect.height))
        pygame.draw.rect(self.screen, COLORS['goomba_feet'], (rect.x + 4, rect.bottom - 8, rect.width - 8, 8))

    def draw_koopa(self, e, camera_offset_x):
        rect = e['rect'].copy()
        rect.x -= camera_offset_x
        pygame.draw.rect(self.screen, COLORS['koopa_green'], (rect.x, rect.y + 10, rect.width, rect.height - 10))
        pygame.draw.rect(self.screen, COLORS['koopa_skin'], (rect.centerx - 8, rect.y, 16, 16))

    def draw_goal(self, g, camera_offset_x):
        rect = g['rect'].copy()
        rect.x -= camera_offset_x
        pygame.draw.rect(self.screen, '#C0C0C0', (rect.centerx - 4, rect.y, 8, rect.height))

    def draw_ui(self, game):
        score_text = self.font.render(f"SCORE: {game.score}", True, COLORS['ui_text'])
        lives_text = self.font.render(f"LIVES: {game.lives}", True, COLORS['ui_text'])
        level_text = self.font.render(f"WORLD {game.world}-{game.level}", True, COLORS['ui_text'])
        self.screen.blit(score_text, (10, 10))
        self.screen.blit(lives_text, (SCREEN_WIDTH - lives_text.get_width() - 10, 10))
        self.screen.blit(level_text, (SCREEN_WIDTH/2 - level_text.get_width()/2, 10))
        
        if game.game_over or game.level_complete:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            
            big_font = pygame.font.SysFont('monospace', 40, bold=True)
            msg = "GAME OVER" if game.game_over else "LEVEL COMPLETE"
            msg_text = big_font.render(msg, True, COLORS['ui_text'])
            self.screen.blit(msg_text, (SCREEN_WIDTH/2 - msg_text.get_width()/2, SCREEN_HEIGHT/2 - msg_text.get_height()/2))


# =================================================================
# Main Game Class
# =================================================================
class MarioGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Super Mario Bros. 3 Clone")
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.level_data_manager = LevelData()
        self.renderer = Renderer(self.screen)

        # Game State
        self.world = 1
        self.level = 1
        self.lives = 3
        self.score = 0
        self.game_over = False
        self.level_complete = False

        self.player = {
            'rect': pygame.Rect(100, 200, 32, 32),
            'vx': 0, 'vy': 0,
            'on_ground': False, 'facing_right': True,
            'power_level': 0, # 0: small, 1: super, 2: fire
            'immune': False, 'immune_timer': 0
        }
        
        self.camera_offset_x = 0
        self.load_level(self.world, self.level)

    def load_level(self, world_num, level_num):
        level_map = self.level_data_manager.get_level(world_num, level_num)
        
        self.platforms = [p for p in level_map.get('platforms', [])]
        for p in self.platforms: p['rect'] = pygame.Rect(p['x'], p['y'], p['width'], p['height'])
        
        self.pipes = [p for p in level_map.get('pipes', [])]
        for p in self.pipes: p['rect'] = pygame.Rect(p['x'], p['y'], p['width'], p['height'])

        self.special_blocks = [b for b in level_map.get('special_blocks', [])]
        for b in self.special_blocks: b['rect'] = pygame.Rect(b['x'], b['y'], 32, 32)

        self.enemies = [e for e in level_map.get('enemies', [])]
        for e in self.enemies: 
            e['rect'] = pygame.Rect(e['x'], e['y'], 32, 32)
            e['vx'] = -1 # Default speed

        self.goal = level_map['goal']
        self.goal['rect'] = pygame.Rect(self.goal['x'], self.goal['y'], self.goal['width'], self.goal['height'])
        
        # Reset player
        self.player['rect'].topleft = (100, 200)
        self.player['vx'], self.player['vy'] = 0, 0
        self.adjust_player_size()
        self.level_complete = False
        self.camera_offset_x = 0

    def adjust_player_size(self):
        if self.player['power_level'] > 0:
            self.player['rect'].height = 64
        else:
            self.player['rect'].height = 32
        # prevent sinking into ground after size change
        self.player['rect'].bottom = 352 

    def run(self):
        while self.running:
            self.handle_events()
            if not self.game_over and not self.level_complete:
                self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and self.level_complete:
                    self.world = 1 # simplified logic for now
                    self.level = 1
                    self.load_level(self.world, self.level)
                if event.key == pygame.K_ESCAPE:
                    self.running = False

        keys = pygame.key.get_pressed()
        # Horizontal Movement
        if keys[pygame.K_LEFT]:
            self.player['vx'] = -4
            self.player['facing_right'] = False
        elif keys[pygame.K_RIGHT]:
            self.player['vx'] = 4
            self.player['facing_right'] = True
        else:
            self.player['vx'] = 0
            
        # Jumping
        if keys[pygame.K_UP] and self.player['on_ground']:
            self.player['vy'] = -12
            self.player['on_ground'] = False

    def update(self):
        # Update Player
        self.update_player()
        self.update_enemies()
        # Update camera
        self.camera_offset_x = self.player['rect'].x - SCREEN_WIDTH / 3
        if self.camera_offset_x < 0: self.camera_offset_x = 0

    def update_player(self):
        # Apply gravity
        self.player['vy'] += 0.5
        if self.player['vy'] > 7: self.player['vy'] = 7
        
        # Move and collide
        self.player['rect'].x += self.player['vx']
        self.check_collisions('horizontal')
        self.player['rect'].y += self.player['vy']
        self.player['on_ground'] = False
        self.check_collisions('vertical')
        
        # Check goal
        if self.player['rect'].colliderect(self.goal['rect']):
            self.level_complete = True
            self.score += 5000

        # Fell off screen
        if self.player['rect'].top > SCREEN_HEIGHT:
            self.lose_life()

    def update_enemies(self):
        for i in range(len(self.enemies) - 1, -1, -1):
            enemy = self.enemies[i]
            enemy['rect'].x += enemy['vx']
            
            # Simple AI: turn at edges
            # This is a basic implementation. A better one would check ground tiles.
            if enemy['vx'] < 0 and enemy['rect'].left < 0: enemy['vx'] *= -1
            
            # Player collision
            if self.player['rect'].colliderect(enemy['rect']):
                # Stomped?
                if self.player['vy'] > 0 and self.player['rect'].bottom < enemy['rect'].centery:
                    self.enemies.pop(i)
                    self.score += 100
                    self.player['vy'] = -8 # Bounce
                else:
                    self.player_damage()


    def check_collisions(self, direction):
        collidables = self.platforms + self.pipes + self.special_blocks

        for obj in collidables:
            if self.player['rect'].colliderect(obj['rect']):
                if direction == 'horizontal':
                    if self.player['vx'] > 0: # Moving right
                        self.player['rect'].right = obj['rect'].left
                    elif self.player['vx'] < 0: # Moving left
                        self.player['rect'].left = obj['rect'].right
                
                elif direction == 'vertical':
                    if self.player['vy'] > 0: # Moving down
                        self.player['rect'].bottom = obj['rect'].top
                        self.player['on_ground'] = True
                        self.player['vy'] = 0
                    elif self.player['vy'] < 0: # Moving up
                        self.player['rect'].top = obj['rect'].bottom
                        self.player['vy'] = 0
                        # Check if it's a special block to activate
                        if obj in self.special_blocks and not obj.get('activated', False):
                            self.activate_block(obj)

    def activate_block(self, block):
        block['activated'] = True
        if block['type'] == 'mushroom_block' and self.player['power_level'] == 0:
            self.player['power_level'] = 1
            self.score += 1000
            self.adjust_player_size()
        elif block['type'] == 'fire_block' and self.player['power_level'] < 2:
            self.player['power_level'] = 2
            self.score += 1000
            self.adjust_player_size()
        else: # coin block
            self.score += 200

    def player_damage(self):
        if self.player['power_level'] > 0:
            self.player['power_level'] = 0
            self.adjust_player_size()
            # Add immunity frames later
        else:
            self.lose_life()

    def lose_life(self):
        self.lives -= 1
        if self.lives <= 0:
            self.game_over = True
        else:
            self.load_level(self.world, self.level)

    def draw(self):
        self.screen.fill(COLORS['sky_blue'])
        
        # Draw all game objects relative to camera
        all_objects = [
            (self.platforms, 'platform'), (self.pipes, 'pipe'),
            (self.special_blocks, 'special_block'), (self.enemies, lambda e: e['type']),
        ]
        
        for obj_list, type_getter in all_objects:
            for obj in obj_list:
                type_val = type_getter(obj) if callable(type_getter) else type_getter
                self.renderer.draw(obj, type_val, self.camera_offset_x)

        self.renderer.draw(self.goal, 'goal', self.camera_offset_x)
        self.renderer.draw(self.player, 'player', self.camera_offset_x)
        
        # Draw UI on top
        self.renderer.draw_ui(self)
        
        pygame.display.flip()

if __name__ == '__main__':
    game = MarioGame()
    game.run()

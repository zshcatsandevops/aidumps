import pygame as pg
import sys
import random # Added for some procedural texturing, nya!

# CATSDK Game Configuration ~nya!
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TITLE = "CATSDK's Super Mario Purr-ty All-Stars!"
FPS = 60

# --- Colors, meooow! ---
# General
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
SKY_BLUE = (92, 148, 252) # Classic SMB All-Stars sky blue, nya!

# Player (Mario-cat!) Colors
CATSDK_RED = (224, 24, 24)      # Bright red for Mario-cat's suit
CATSDK_SKIN = (252, 224, 168)   # Peachy skin tone
CATSDK_HAIR_BROWN = (136, 80, 32) # Brown for hair/details
CATSDK_EYES_BLACK = (10, 10, 10)
CATSDK_SHOES_BROWN = (160, 80, 30) # Shoes

# Platform Colors
CATSDK_GROUND_MAIN = (218, 139, 60)     # Main dirt/block color
CATSDK_GROUND_TOP_SOIL = (116, 188, 32) # Grassy top for ground blocks
CATSDK_GROUND_DETAIL = (136, 80, 32)    # Darker detail for ground

CATSDK_BRICK_RED = (200, 76, 12)
CATSDK_MORTAR_GRAY = (100, 100, 100) # Darker mortar for contrast

CATSDK_QBLOCK_YELLOW = (252, 188, 0)    # Golden yellow for ? blocks
CATSDK_QBLOCK_SHINE = (255, 240, 150)   # Highlight for ? blocks
CATSDK_QBLOCK_RIVET = (160, 100, 20)    # Rivets on ? blocks

# --- Player (Mario-cat!) properties, meow! ---
# Logical pixel art dimensions
PLAYER_SPRITE_LOGICAL_WIDTH = 12
PLAYER_SPRITE_LOGICAL_HEIGHT = 16 # A bit taller for better proportions
PLAYER_PIXEL_SCALE = 3 # How much to scale each "pixel" of the art

# Actual player dimensions based on scaled pixel art
PLAYER_WIDTH = PLAYER_SPRITE_LOGICAL_WIDTH * PLAYER_PIXEL_SCALE
PLAYER_HEIGHT = PLAYER_SPRITE_LOGICAL_HEIGHT * PLAYER_PIXEL_SCALE

PLAYER_ACC_VALUE = 0.7  # How fast Mario-cat speeds up!
PLAYER_FRICTION_COEFF = -0.12 # Friction coefficient, purr!
PLAYER_GRAVITY = 0.7 # Meow, gravity!
PLAYER_JUMP_STRENGTH = -16 # How high can Mario-cat jump, nya?

# Platform properties, purr!
# Structure: (x, y, w, h, type_string)
# Types: 'ground', 'brick', 'q_block'
PLATFORM_LIST = [
    (0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40, 'ground'),    # Main ground
    (200, SCREEN_HEIGHT - 150, 120, 30, 'brick'),         # A floating brick platform
    (450, SCREEN_HEIGHT - 250, 90, 30, 'q_block'),       # A question block, nya!
    (50, SCREEN_HEIGHT - 350, 150, 30, 'brick'),          # Higher brick platform
    (SCREEN_WIDTH - 180, SCREEN_HEIGHT - 300, 60, 30, 'q_block'), # Another ? block
    (300, SCREEN_HEIGHT - 80, 90, 30, 'ground'), # Small ground patch
]

# --- Helper function to create sprite surfaces from pixel art strings ---
def create_sprite_from_pixels(pixel_art_rows, scale, color_map):
    num_logical_rows = len(pixel_art_rows)
    if num_logical_rows == 0: return pg.Surface((0,0), pg.SRCALPHA) # Added SRCALPHA here too
    num_logical_cols = len(pixel_art_rows[0])
    
    surface_width = num_logical_cols * scale
    surface_height = num_logical_rows * scale
    
    sprite_surf = pg.Surface((surface_width, surface_height), pg.SRCALPHA)
    sprite_surf.fill((0,0,0,0)) # Transparent background, purr!

    for r_idx, row_str in enumerate(pixel_art_rows):
        for c_idx, char_code in enumerate(row_str):
            if char_code != ' ' and char_code in color_map: # ' ' is transparent
                color = color_map[char_code]
                pg.draw.rect(sprite_surf, color, (c_idx * scale, r_idx * scale, scale, scale))
    return sprite_surf

# --- Player Class, our brave Mario-cat! ---
class Player(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()

        self.color_map = {
            'R': CATSDK_RED,        # Red suit
            'S': CATSDK_SKIN,       # Skin
            'H': CATSDK_HAIR_BROWN, # Hair
            'E': CATSDK_EYES_BLACK, # Eyes
            'N': CATSDK_SHOES_BROWN,# Shoes/Paws
            'W': WHITE,             # White (e.g., for gloves if desired)
        }

        self.mario_cat_pixels_still = [
            "    HHHH    ", 
            "   HHHHHH   ", 
            "   HHSSHH   ", 
            "  HSSEESSH  ", 
            "  HSSSSSSH  ", 
            "   SSSSSS   ", 
            "    RRRR    ", 
            " RRRRRRRRRR ", 
            "RRRRRRRRRRRR", 
            "RRR  RR  RRR", 
            "RRR  RR  RRR", 
            " RR  RR  RR ", 
            " RR  RR  RR ", 
            " NN  NN  NN ", 
            "NNN      NNN",
            "NNN      NNN",
        ]
        
        self.image_still_right = create_sprite_from_pixels(self.mario_cat_pixels_still, PLAYER_PIXEL_SCALE, self.color_map)
        self.image_still_left = pg.transform.flip(self.image_still_right, True, False)
        
        self.image = self.image_still_right 
        self.rect = self.image.get_rect()
        
        # Kinematics, meow!
        # self.pos is (center_x, top_y) of the player
        self.pos = pg.math.Vector2((SCREEN_WIDTH / 2, SCREEN_HEIGHT - 80 - PLAYER_HEIGHT)) 
        self.vel = pg.math.Vector2(0, 0)
        self.acc = pg.math.Vector2(0, 0) 
        self.on_ground = False
        self.facing_right = True

        # Position rect based on self.pos (center_x, top_y)
        self.rect.midbottom = (round(self.pos.x), round(self.pos.y + PLAYER_HEIGHT))

    def jump(self):
        if self.on_ground:
            self.vel.y = PLAYER_JUMP_STRENGTH
            self.on_ground = False # Will be set true on next frame's collision if landing

    def update(self, platforms):
        # 1. Determine acceleration based on input and friction
        input_acc_x = 0
        keys = pg.key.get_pressed()
        if keys[pg.K_LEFT] or keys[pg.K_a]:
            input_acc_x = -PLAYER_ACC_VALUE
            if self.facing_right:
                self.facing_right = False
                self.image = self.image_still_left
        if keys[pg.K_RIGHT] or keys[pg.K_d]:
            input_acc_x = PLAYER_ACC_VALUE
            if not self.facing_right:
                self.facing_right = True
                self.image = self.image_still_right
            
        friction_acc_x = self.vel.x * PLAYER_FRICTION_COEFF
        self.acc.x = input_acc_x + friction_acc_x
        self.acc.y = PLAYER_GRAVITY # Gravity always applies
        
        # 2. Update velocity
        self.vel += self.acc
        if abs(self.vel.x) < 0.15 and input_acc_x == 0 : self.vel.x = 0 # Stop if moving very slowly horizontally without input

        # 3. Update position & handle X-axis collisions
        self.pos.x += self.vel.x
        self.rect.centerx = round(self.pos.x) # Update rect x-position from float pos
        self.check_collision_x(platforms) # Check and resolve X collisions

        # Screen boundary checks for X
        if self.rect.left < 0:
            self.rect.left = 0
            self.pos.x = self.rect.centerx # Sync float pos from corrected rect
            self.vel.x = 0
        elif self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
            self.pos.x = self.rect.centerx # Sync float pos from corrected rect
            self.vel.x = 0
        
        # 4. Update position & handle Y-axis collisions
        self.on_ground = False # Assume not on ground until Y collision check proves otherwise
        self.pos.y += self.vel.y # Update float y-position (player's top_y)
        
        self.rect.top = round(self.pos.y) # Update rect y-position (top) from float pos for this frame's collision check
        
        self.check_collision_y(platforms) # Check and resolve Y collisions, updates self.rect, self.vel.y, self.on_ground, and self.pos.y

    def check_collision_x(self, platforms):
        collided_platforms = pg.sprite.spritecollide(self, platforms, False)
        for plat in collided_platforms:
            if self.vel.x > 0: # Moving right
                self.rect.right = plat.rect.left
            elif self.vel.x < 0: # Moving left
                self.rect.left = plat.rect.right
            self.vel.x = 0 # Stop horizontal movement on collision
        # Sync float pos.x from rect after potential collision adjustments
        self.pos.x = self.rect.centerx

    def check_collision_y(self, platforms):
        # self.rect.top is already set to round(self.pos.y)
        collided_platforms = pg.sprite.spritecollide(self, platforms, False)
        for plat in collided_platforms:
            if self.vel.y > 0: # Moving down (falling)
                if self.rect.bottom > plat.rect.top: # Ensure penetration before correcting
                    self.rect.bottom = plat.rect.top
                    self.vel.y = 0
                    self.on_ground = True
            elif self.vel.y < 0: # Moving up (jumping)
                if self.rect.top < plat.rect.bottom: # Ensure penetration
                    self.rect.top = plat.rect.bottom
                    self.vel.y = 0
        
        # After all Y collision resolutions, sync float pos.y from the final rect.top
        self.pos.y = float(self.rect.top)


# --- Platform Class, solid ground for paws! ---
class Platform(pg.sprite.Sprite):
    def __init__(self, x, y, w, h, platform_type):
        super().__init__()
        self.image = pg.Surface((w, h), pg.SRCALPHA) 
        self.image.fill((0,0,0,0)) 
        self.rect = self.image.get_rect(topleft = (x,y))
        self.draw_platform_style(w, h, platform_type)

    def draw_platform_style(self, w, h, p_type):
        if p_type == 'ground':
            self.draw_ground_block(w,h)
        elif p_type == 'brick':
            self.draw_brick_block(w,h)
        elif p_type == 'q_block':
            self.draw_q_block(w,h)
        else: # Fallback for unknown types, nya!
            self.image.fill(CATSDK_GROUND_MAIN) # Fixed: Use a defined color

    def draw_ground_block(self, w, h):
        top_soil_h = max(4, h // 4)
        pg.draw.rect(self.image, CATSDK_GROUND_TOP_SOIL, (0, 0, w, top_soil_h))
        pg.draw.rect(self.image, CATSDK_GROUND_MAIN, (0, top_soil_h, w, h - top_soil_h))
        
        num_clumps = w // 20 
        for _ in range(num_clumps):
            cx = random.randint(0, w - 5)
            cy = random.randint(top_soil_h + 2, h - 5)
            cw = random.randint(3, 8)
            ch = random.randint(2, 6)
            pg.draw.ellipse(self.image, CATSDK_GROUND_DETAIL, (cx, cy, cw, ch))

    def draw_brick_block(self, w, h):
        self.image.fill(CATSDK_MORTAR_GRAY) 
        
        brick_w_ideal = 30 
        brick_h_ideal = h * 0.8 
        if h < 25 : brick_h_ideal = h - 4 
        
        mortar = 2 

        num_rows = max(1, round(h / (brick_h_ideal + mortar))) if h > mortar *2 else 1
        actual_brick_h = (h - (num_rows + 1) * mortar) / num_rows
        actual_brick_h = max(1, actual_brick_h)

        current_y = mortar
        for r_idx in range(num_rows):
            num_cols = max(1, round(w / (brick_w_ideal + mortar))) if w > mortar *2 else 1
            actual_brick_w = (w - (num_cols + 1) * mortar) / num_cols
            actual_brick_w = max(1, actual_brick_w)
            
            current_x = mortar
            if r_idx % 2 == 1:
                current_x -= actual_brick_w / 2 

            for _ in range(num_cols + 2): # +2 to robustly cover edges with stagger
                draw_x = max(current_x, mortar) # Start drawing from mortar line if brick starts before it
                # End drawing at w - mortar or at brick's actual end
                draw_w_candidate_end = min(current_x + actual_brick_w, w - mortar)
                draw_w = draw_w_candidate_end - draw_x
                
                if draw_w > 0 and draw_x < w - mortar : # Ensure brick has positive width and starts before right mortar
                    pg.draw.rect(self.image, CATSDK_BRICK_RED, (draw_x, current_y, draw_w, actual_brick_h))
                
                current_x += actual_brick_w + mortar
                if current_x >= w - mortar: break # Optimization
            current_y += actual_brick_h + mortar


    def draw_q_block(self, w, h):
        self.image.fill(CATSDK_QBLOCK_YELLOW)
        
        border_thickness = max(2, min(w, h) // 8) 
        pg.draw.rect(self.image, CATSDK_QBLOCK_RIVET, (0,0,w,h), border_thickness)
        inner_rect_offset = border_thickness 
        pg.draw.rect(self.image, CATSDK_QBLOCK_YELLOW, (inner_rect_offset, inner_rect_offset, 
                                                       w - 2*inner_rect_offset, h - 2*inner_rect_offset))

        rivet_size = max(1, border_thickness // 2)
        rivet_pos_offset = border_thickness // 3
        # Ensure rivet centers are calculated correctly to avoid negative radius for small blocks
        if rivet_size > 0:
            pg.draw.circle(self.image, CATSDK_QBLOCK_RIVET, (rivet_pos_offset + rivet_size//2, rivet_pos_offset + rivet_size//2), rivet_size)
            pg.draw.circle(self.image, CATSDK_QBLOCK_RIVET, (w - rivet_pos_offset - rivet_size//2 -1, rivet_pos_offset + rivet_size//2), rivet_size) # -1 for safety
            pg.draw.circle(self.image, CATSDK_QBLOCK_RIVET, (rivet_pos_offset + rivet_size//2, h - rivet_pos_offset - rivet_size//2-1), rivet_size)
            pg.draw.circle(self.image, CATSDK_QBLOCK_RIVET, (w - rivet_pos_offset- rivet_size//2-1, h - rivet_pos_offset- rivet_size//2-1), rivet_size)

        if w > 10 and h > 10:
             pg.draw.ellipse(self.image, CATSDK_QBLOCK_SHINE, (w*0.2, h*0.15, w*0.3, h*0.2))

        if w > 20 and h > 20: 
            q_mark_color = CATSDK_QBLOCK_RIVET 
            qm_cx, qm_cy = w // 2, h // 2
            qm_bar_w = max(2, int(w * 0.1))
            qm_bar_h = max(2, int(h * 0.1))

            pg.draw.rect(self.image, q_mark_color, (qm_cx - qm_bar_w*1.5, qm_cy - qm_bar_h*2.5, qm_bar_w*3, qm_bar_h))
            pg.draw.rect(self.image, q_mark_color, (qm_cx + qm_bar_w*0.5, qm_cy - qm_bar_h*1.5, qm_bar_w, qm_bar_h*2)) # Fixed: q_mark_Color to q_mark_color
            pg.draw.rect(self.image, q_mark_color, (qm_cx - qm_bar_w*0.5, qm_cy + qm_bar_h*1.5, qm_bar_w, qm_bar_h))


# --- Game Initialization, meow! ---
def game_init_purrfect():
    pg.init()
    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pg.display.set_caption(TITLE)
    clock = pg.time.Clock()
    return screen, clock

# --- Game Loop, where the fun happens, nya! ---
def game_loop_meow(screen, clock):
    player = Player()
    
    platforms = pg.sprite.Group()
    for p_data in PLATFORM_LIST:
        plat = Platform(*p_data)
        platforms.add(plat)

    # all_sprites group is not strictly necessary with the current manual drawing,
    # but can be useful if you expand to use group drawing/updating features.
    # For now, keeping it simple.

    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE or event.key == pg.K_UP or event.key == pg.K_w:
                    player.jump()
                if event.key == pg.K_ESCAPE:
                    running = False

        player.update(platforms)

        screen.fill(SKY_BLUE)
        
        for plat in platforms: 
            screen.blit(plat.image, plat.rect)
        screen.blit(player.image, player.rect) 

        pg.display.flip()
        clock.tick(FPS)

    pg.quit()
    sys.exit()

# --- Let's start the game, meow! ---
if __name__ == '__main__':
    meow_screen, meow_clock = game_init_purrfect()
    game_loop_meow(meow_screen, meow_clock)

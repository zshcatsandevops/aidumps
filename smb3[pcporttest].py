import pygame as pg
import asyncio
import platform
import random
import math # For SuperLeaf sine wave

# Game Configuration
SCREEN_WIDTH = 768
SCREEN_HEIGHT = 672
FPS = 60
TILE_SIZE = 48  # Each tile is 16 chars * PIXEL_SCALE = 16 * 3 = 48 pixels
PIXEL_SCALE = 3

# Physics Constants
GRAVITY = 0.8
PLAYER_ACCEL = 0.8
PLAYER_FRICTION = -0.15
PLAYER_MAX_SPEED_X = 6
PLAYER_JUMP_POWER = 17 
PLAYER_SUPER_JUMP_POWER = 18 # Slightly more for Super forms
MAX_FALL_SPEED = 15
ENEMY_MOVE_SPEED = 1
KOOPA_SHELL_SPEED = 8

# Player states
PLAYER_STATE_SMALL = "small"
PLAYER_STATE_SUPER = "super"
PLAYER_STATE_RACCOON = "raccoon" # Future, nyaa

# --- SMB3 Color Map (Hallucinated Palette Data) ---
TRANSPARENT_CHAR = 'T'
SMB3_COLOR_MAP = {
    'T': (0,0,0,0),      # Transparent
    'R': (220, 0, 0),    # Mario Red
    'B': (0, 80, 200),   # Mario Blue overalls
    'S': (255, 200, 150),# Mario Skin
    'Y': (255, 240, 30), # Question Block Yellow
    'O': (210, 120, 30), # Block Orange/Brown (Bricks, Used Q-Block)
    'o': (160, 80, 20),  # Block Darker Orange/Brown (Shading)
    'K': (10, 10, 10),   # Black (Outlines, Eyes, Mario Hair)
    'W': (250, 250, 250),# White (Eyes, '?' on Q-block)
    'G': (0, 180, 0),    # Leaf Green / Pipe Green / Flag Green / Koopa Green
    'g': (140, 70, 20),  # Ground Brown / Leaf Stem accent
    'N': (130, 80, 50),  # Goomba Brown Body
    'n': (80, 50, 30),   # Goomba Dark Brown Feet / Mario Shoes
    'L': (90, 200, 255), # Sky Blue (Background)
    'F': (100, 200, 50), # Leaf Light Green part
    'X': (190, 190, 190),# Light Grey (Q-Block Rivets, Flagpole)
    'D': (60, 60, 60),   # Dark Grey (general shadow/detail)
    'U': (180, 100, 60), # Used Block main color
    'M': (255, 100, 90), # Mushroom Red
    'm': (240, 230, 210),# Mushroom Cream/White spots and stem
    'k': (0, 100, 0),    # Koopa Dark Green (shell accents)
    'y': (255,255,150)   # Koopa Yellow (skin)
}
color_map = SMB3_COLOR_MAP 
BACKGROUND_COLOR = color_map['L']


# --- SMB3 Asset Definitions (Hallucinated ROM Graphics Data) ---

# Small Mario (Right Facing - SMB3 Style) - 16x16
SMB3_MARIO_SMALL_IDLE_R_ART = [ 
    "TTTTTRRRRTTTTTTT", "TTTTRRRRRRTTTTTT", "TTTKKSSSKRTTTTTT", "TTKSRSRSKRTTTTTT",
    "TTKSSSSSKRTTTTTT", "TTTKRKRRKTTTTTTT", "TTBBBBBBBBTTTTTT", "TTBBRBBBRBTTTTTT",
    "TTTRRnnRRTTTTTTT", "TTTRnnnnRTTTTTTT", "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT",
    "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT"
]
SMB3_MARIO_SMALL_WALK_R_ART_1 = [ 
    "TTTTTRRRRTTTTTTT", "TTTTRRRRRRTTTTTT", "TTTKKSSSKRTTTTTT", "TTKSRSRSKRTTTTTT",
    "TTKSSSSSKRTTTTTT", "TTTKRKRRKTTTTTTT", "TTBBBBBBBBTTTTTT", "TTBBRBBBRBTTTTTT",
    "TTTRRTRnRTTTTTTT", "TTTRnnnnRTTTTTTT", "TTTTTTnnTTTTTTTT", "TTTTTTTTTTTTTTTT",
    "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT"
]
SMB3_MARIO_SMALL_WALK_R_ART_2 = [ 
    "TTTTTRRRRTTTTTTT", "TTTTRRRRRRTTTTTT", "TTTKKSSSKRTTTTTT", "TTKSRSRSKRTTTTTT",
    "TTKSSSSSKRTTTTTT", "TTTKRKRRKTTTTTTT", "TTBBBBBBBBTTTTTT", "TTBBRBBBRBTTTTTT",
    "TTTRRnnRRTTTTTTT", "TTTRTRTRRTTTTTTT", "TTTTTTnnTTTTTTTT", "TTTTTTTTTTTTTTTT",
    "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT"
]
SMB3_MARIO_SMALL_JUMP_R_ART = [ 
    "TTTTTRRRRTTTTTTT", "TTTTRRRRRRTTTTTT", "TTTKKSSSKBBTTTTT", "TTKSRSRSKBBTTTTT",
    "TTKSSSSSKRTTTTTT", "TTTKRKRRKTTTTTTT", "TTBBBBBBBBTTTTTT", "TTBBRBBBRBTTTTTT",
    "TTTTRnRTRTTTTTTT", "TTTTRnRnRTTTTTTT", "TTTTnnTTnnTTTTTT", "TTTTTTTTTTTTTTTT",
    "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT"
]

# Super Mario (Right Facing - SMB3 Style) - 16x32 (Two tiles high)
# For simplicity, we'll draw this as one sprite, but it visually occupies two tile heights
SMB3_MARIO_SUPER_IDLE_R_ART = [ # Top Tile
    "TTTTTRRRRTTTTTTT", "TTTTRRRRRRTTTTTT", "TTTKKSSSKRTTTTTT", "TTKSRSRSKRTTTTTT",
    "TTKSSSSSKRTTTTTT", "TTTKRKRRKTTTTTTT", "TTTRRBBBRRTTTTTT", "TTTRBBBBBRTTTTTT",
    "TTTRBBBBBRTTTTTT", "TTTRBBBBBRTTTTTT", "TTBBBBBBBBBBTTTT", "TTBBBBBBBBBBTTTT",
    "TTTTRRRRRRTTTTTT", "TTTTnnnnnnTTTTTT", "TTTTnnnnnnTTTTTT", "TTTTTTTTTTTTTTTT"
] # This is actually one 16x16 sprite, player height will be 2 tiles logic
SMB3_MARIO_SUPER_WALK_R_ART_1 = [
    "TTTTTRRRRTTTTTTT", "TTTTRRRRRRTTTTTT", "TTTKKSSSKRTTTTTT", "TTKSRSRSKRTTTTTT",
    "TTKSSSSSKRTTTTTT", "TTTKRKRRKTTTTTTT", "TTTRRBBBRRTTTTTT", "TTTRBBBBBRTTTTTT",
    "TTTRBBBBBRTTTTTT", "TTTRBBBBBRTTTTTT", "TTBBBBBBBBBBTTTT", "TTBBRBBBRBBTTTTT",
    "TTTTTRRRnRTTTTTT", "TTTTTnnnnnTTTTTT", "TTTTTnnnnnTTTTTT", "TTTTTTTnnTTTTTTT"
]
SMB3_MARIO_SUPER_WALK_R_ART_2 = [
    "TTTTTRRRRTTTTTTT", "TTTTRRRRRRTTTTTT", "TTTKKSSSKRTTTTTT", "TTKSRSRSKRTTTTTT",
    "TTKSSSSSKRTTTTTT", "TTTKRKRRKTTTTTTT", "TTTRRBBBRRTTTTTT", "TTTRBBBBBRTTTTTT",
    "TTTRBBBBBRTTTTTT", "TTTRBBBBBRTTTTTT", "TTBBBBBBBBBBTTTT", "TTBBBRBBBRBTTTTT",
    "TTTTTRnnRRTTTTTT", "TTTTTnnnnnTTTTTT", "TTTTTnnnnnTTTTTT", "TTTTTTTnnTTTTTTT"
]
SMB3_MARIO_SUPER_JUMP_R_ART = [
    "TTTTTRRRRTTTTTTT", "TTTTRRRRRRTTTTTT", "TTTKKSSSKBBTTTTT", "TTKSRSRSKBBTTTTT",
    "TTKSSSSSKRTTTTTT", "TTTKRKRRKTTTTTTT", "TTTRRBBBRBTTTTTT", "TTTRBBBBBBTTTTTT",
    "TTTRBBBBBBTTTTTT", "TTTRBBBBBBTTTTTT", "TTBBBBBBBBBBTTTT", "TTBBBBBBBBBBTTTT",
    "TTTTTRnRTRTTTTTT", "TTTTTRnRnRTTTTTT", "TTTTnnTTnnTTTTTT", "TTTTTTTTTTTTTTTT"
]

# Goomba (SMB3 Style)
SMB3_GOOMBA_WALK1_ART = [
    "TTTTNNNNNNTTTTTT", "TTTNNNNNNNNTTTTT", "TTNNWWKKWWNNTTTT", "TTNKKWWWWKKNNTTT", 
    "TTNNNNNNNNNNTTTT", "TTNNNNNNNNNNNNTT", "TTTNNNNNNNNTTTTT", "TTTTNNNNNNTTTTTT",
    "TTTTTnnnnTTTTTTT", "TTTTNnnnnNTTTTTT", "TTTNNNNNNNNTTTTT", "TTTTTTTTTTTTTTTT",
    "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT"
]
SMB3_GOOMBA_WALK2_ART = [ 
    "TTTTNNNNNNTTTTTT", "TTTNNNNNNNNTTTTT", "TTNNWWKKWWNNTTTT", "TTNKKWWWWKKNNTTT",
    "TTNNNNNNNNNNTTTT", "TTNNNNNNNNNNNNTT", "TTTNNNNNNNNTTTTT", "TTTTNNNNNNTTTTTT",
    "TTTTnnNNnnTTTTTT", "TTTTNnnnnNTTTTTT", "TTTNNNNNNNNTTTTT", "TTTTTTTTTTTTTTTT",
    "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT"
]
SMB3_GOOMBA_SQUISHED_ART = [ 
    "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT", "TTTTNNNNNNTTTTTT",
    "TTTNNNNNNNNTTTTT", "TTNNWWKKWWNNTTTT", "TTNKKWWWWKKNNTTT", "TTNNNNNNNNNNTTTT",
    "TTNNNNNNNNNNNNTT", "TTTNNNNNNNNTTTTT", "TTTTNNNNNNTTTTTT", "TTTTTnnnnTTTTTTT",
    "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT"
]

# Koopa Troopa (Green, SMB3 Style)
SMB3_KOOPA_WALK1_R_ART = [
    "TTTTTGGGGTTTTTTT", "TTTTGGGGGGTTTTTT", "TTTGGkkGGGGTTTTT", "TTGGkWWkkyyGTTTT",
    "TTGkWKKkWyyGGTTT", "TTGkyyyykWWGTTTT", "TTGkyyyykKKGGTTT", "TTGkyyyykWWGGTTT",
    "TTTGGkyyGGGGTTTT", "TTTTGGGGGGykTTTT", "TTTTTyyGGyyTTTTT", "TTTTTyyTTyyTTTTT",
    "TTTTyyTTTTTyyTTT", "TTTTnnTTTTTnnTTT", "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT"
]
SMB3_KOOPA_WALK2_R_ART = [
    "TTTTTGGGGTTTTTTT", "TTTTGGGGGGTTTTTT", "TTTGGkkGGGGTTTTT", "TTGGkWWkkyyGTTTT",
    "TTGkWKKkWyyGGTTT", "TTGkyyyykWWGTTTT", "TTGkyyyykKKGGTTT", "TTGkyyyykWWGGTTT",
    "TTTGGkyyGGGGTTTT", "TTTTGGGGGGykTTTT", "TTTTTyyGGyyTTTTT", "TTTTyyTTyyTTTTTT",
    "TTTnnTTyyTTTTTTT", "TTTTTTTTnnTTTTTT", "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT"
]
SMB3_KOOPA_SHELL_ART = [
    "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT", "TTTTTGGGGTTTTTTT", "TTTTGGGGGGTTTTTT",
    "TTTGGkkGGGGTTTTT", "TTGGkyyykyyGTTTT", "TTGkyyyyyyyGGTTT", "TTGkyyyyyyyGGTTT",
    "TTGGkyyykyyGTTTT", "TTTGGkkGGGGTTTTT", "TTTTGGGGGGTTTTTT", "TTTTTGGGGTTTTTTT",
    "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT"
]


# Brick Block (SMB3 Style) - Orangey-brown
SMB3_BRICK_BLOCK_ART = [
    "OOOOOOOOOOOOOOOO", "OKKOoKKOoKKOoKKO", "OOOOOOOOOOOOOOOO", "OoKKOoKKOoKKOoKK",
    "OOOOOOOOOOOOOOOO", "OKKOoKKOoKKOoKKO", "OOOOOOOOOOOOOOOO", "OoKKOoKKOoKKOoKK",
    "OOOOOOOOOOOOOOOO", "OKKOoKKOoKKOoKKO", "OOOOOOOOOOOOOOOO", "OoKKOoKKOoKKOoKK",
    "OOOOOOOOOOOOOOOO", "OKKOoKKOoKKOoKKO", "OOOOOOOOOOOOOOOO", "oooooooooooooooo"
]
# Brick Block Debris (simple example, could be animated)
SMB3_BRICK_DEBRIS_ART = [ # Small chunk
    "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT", "TTTTTToOTTTTTTTT", "TTTTToooOTTTTTTT",
    "TTTTTooootTTTTTT", "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT",
    "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT",
    "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT"
]


# Question Block (SMB3 Style)
SMB3_QUESTION_BLOCK_ART_FRAME1 = [
    "YYYYYYYYYYYYYYYY", "YXWYYYYYYYWXYYYY", "YWKKWYYYYYWKKYWY", "YTWKKWYYYWKKWTYY", 
    "YTTWKKWWKKWTTTYY", "YTTTWKWWKWTTTTYY", "YTTTTWWWWTTTTTYY", "YTTTTWKKWTTTTTYY",
    "YTTTTWKKWTTTTTYY", "YTTTTWWWWTTTTTYY", "YXTTKWKKWKTTTXYY", "YWWWWKKKKWWWWWYW", 
    "YYYYYYYYYYYYYYYY", "YXXXXXXXXXXXXXXY", "YooooooooooooooY", "oooooooooooooooo"
]
SMB3_QUESTION_BLOCK_ART_FRAME2 = [ 
    "YYYYYYYYYYYYYYYY", "YXWYYYYYYYWXYYYY", "YWKKYYYYYYWKKYWY", "YTWKKWYYYWKKWTYY",
    "YTTWKKWWKKWTTTYY", "YTTTWKWWKWTTTTYY", "YTTTTWKKWTTTTTYY", "YTTTTWKKWTTTTTYY",
    "YTTTTWWWWTTTTTYY", "YTTTTWWWWTTTTTYY", "YXTTKWWWWKTTTXYY", "YWWWWKKKKWWWWWYW",
    "YYYYYYYYYYYYYYYY", "YXXXXXXXXXXXXXXY", "YooooooooooooooY", "oooooooooooooooo"
]
SMB3_USED_BLOCK_ART = [ 
    "UUUUUUUUUUUUUUUU", "UooUooUooUooUooU", "UooUooUooUooUooU", "UUUUUUUUUUUUUUUU",
    "UooUooUooUooUooU", "UooUooUooUooUooU", "UUUUUUUUUUUUUUUU", "UooUooUooUooUooU",
    "UooUooUooUooUooU", "UUUUUUUUUUUUUUUU", "UooUooUooUooUooU", "UooUooUooUooUooU",
    "UUUUUUUUUUUUUUUU", "UooUooUooUooUooU", "UooUooUooUooUooU", "oooooooooooooooo"
]

# Ground Block (SMB3 Style) - Brownish with some pattern
SMB3_GROUND_BLOCK_ART = [
    "gggggggggggggggg", "gOgOgOgOgOgOgOgO", "gOgOgOgOgOgOgOgO", "gggggggggggggggg",
    "gggggggggggggggg", "gggggggggggggggg", "DDDDDDDDDDDDDDDD", "DDDDDDDDDDDDDDDD",
    "gggggggggggggggg", "gOgOgOgOgOgOgOgO", "gOgOgOgOgOgOgOgO", "gggggggggggggggg",
    "gggggggggggggggg", "gggggggggggggggg", "DDDDDDDDDDDDDDDD", "DDDDDDDDDDDDDDDD"
]

# Super Leaf (SMB3 Style)
SMB3_SUPER_LEAF_ART = [
    "TTTTTTGGTTTTTTTT", "TTTTTGGGGTTTTTTT", "TTTTGGGGGGTTTTTT", "TTTGGFFFFFFGTTTT", 
    "TTGGFFFFFFFFGTTT", "TTGFFFFgFFFFFGTT", "TTGFFFggFFFFFGTT", "TTGFFFggFFFFFGTT",
    "TTTGFFggggFFGTTT", "TTTTGFFggFFGTTTT", "TTTTTGFFGGTTTTTT", "TTTTTTGggGTTTTTT", 
    "TTTTTTTggTTTTTTT", "TTTTTTTggTTTTTTT", "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT"
]

# Super Mushroom (SMB3 Style)
SMB3_MUSHROOM_ART = [
    "TTTTTMMMMMMTTTTT", "TTTTMMMMMMMMTTTT", "TTTMMmMMMmMMMTTT", "TTMmWWmWWmWWMMTT",
    "TTMWWWWWWWWWMMTT", "TTMWWWWWWWWWMMTT", "TTMMWWWWWWMMMMTT", "TTTMMMMMMMMMTTTT",
    "TTTTTmmmmTTTTTTT", "TTTTmmKKmmTTTTTT", "TTTTmmWWmmTTTTTT", "TTTTmmmmmmTTTTTT",
    "TTTTTmmmmTTTTTTT", "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT", "TTTTTTTTTTTTTTTT"
]


# Flagpole (SMB3 Style - simplified)
SMB3_FLAGPOLE_ART = [
    "TTTTTTTTXTTTTTTT", "TTTTTTGGGXTTTTTT", "TTTTTGGGGGXTTTTT", "TTTTGGGGGGXTTTTT",
    "TTTGGGGGGGXTTTTT", "TTTTGGGGGXTTTTTT", "TTTTTTGGGXTTTTTT", "TTTTTTTTXTTTTTTT",
    "TTTTTTTTXTTTTTTT", "TTTTTTTTXTTTTTTT", "TTTTTTTTXTTTTTTT", "TTTTTTTTXTTTTTTT",
    "TTTTTTTTXTTTTTTT", "TTTTTTTTXTTTTTTT", "TTTTTTTTXTTTTTTT", "TTTTTTTTXTTTTTTT"
]

# SNES-like Graphics Functions
def build_sprite_palette(pixel_art_rows):
    palette = [(0,0,0,0)] 
    unique_colors_in_art = set()
    for row in pixel_art_rows:
        for char_code in row:
            if char_code != TRANSPARENT_CHAR and char_code in color_map:
                unique_colors_in_art.add(color_map[char_code])
    
    sorted_unique_colors = sorted(list(unique_colors_in_art), key=lambda c: (c[0], c[1], c[2])) # Ensure consistent palette order
    palette.extend(sorted_unique_colors)
    return palette

def create_snes_tile_indices(pixel_art_rows, palette):
    tile_indices = []
    for row_str in pixel_art_rows:
        indices_for_row = []
        for char_code in row_str:
            if char_code == TRANSPARENT_CHAR:
                indices_for_row.append(0) 
            else:
                actual_color_tuple = color_map.get(char_code)
                if actual_color_tuple:
                    try:
                        indices_for_row.append(palette.index(actual_color_tuple))
                    except ValueError: 
                        indices_for_row.append(0) # Should not happen if palette built from this art
                else: 
                    indices_for_row.append(0) 
        tile_indices.append(indices_for_row)
    return tile_indices

def draw_snes_tile_indexed(screen, tile_indices, palette, x, y, scale):
    for r_idx, row_of_indices in enumerate(tile_indices):
        for c_idx, palette_idx in enumerate(row_of_indices):
            if palette_idx != 0: 
                color_tuple = palette[palette_idx]
                pg.draw.rect(screen, color_tuple, (x + c_idx * scale, y + r_idx * scale, scale, scale))

def flip_pixel_art(pixel_art_rows):
    return ["".join(reversed(row)) for row in pixel_art_rows]

# Classes
class AnimatedSprite(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.animation_frames = {}
        self.current_frame_index = 0 
        self.animation_speed = 0.1 
        self.animation_timer = 0
        self.image_scale = PIXEL_SCALE
        self.state = "idle" # Current action state (e.g., "walk", "jump", "idle")
        self.facing_left = False

    def load_animation_frames(self, action_name, frame_art_list_right):
        # Load right-facing frames
        key_r = f"{action_name}_right"
        processed_frames_r = []
        for art_strings in frame_art_list_right:
            palette = build_sprite_palette(art_strings)
            indices = create_snes_tile_indices(art_strings, palette)
            processed_frames_r.append((indices, palette))
        self.animation_frames[key_r] = processed_frames_r

        # Create and load left-facing frames by flipping
        key_l = f"{action_name}_left"
        processed_frames_l = []
        for art_strings in frame_art_list_right: # Use original right-facing art to flip
            flipped_art_strings = flip_pixel_art(art_strings)
            palette = build_sprite_palette(flipped_art_strings) # Build palette from flipped art
            indices = create_snes_tile_indices(flipped_art_strings, palette)
            processed_frames_l.append((indices, palette))
        self.animation_frames[key_l] = processed_frames_l


    def get_current_animation_set(self):
        direction = "left" if self.facing_left else "right"
        # Construct the key based on the current state and direction
        # e.g., "walk_right", "jump_left", "small_idle_right", "super_walk_left"
        
        # Player class might override this for form-specific states
        state_prefix = ""
        if hasattr(self, 'player_form') and self.player_form: # Player specific
            state_prefix = f"{self.player_form}_"

        key = f"{state_prefix}{self.state}_{direction}"
        
        default_key_direction = f"{state_prefix}idle_{direction}"
        default_key_universal = f"{state_prefix}idle_right" # Absolute fallback

        if key in self.animation_frames:
            return self.animation_frames[key]
        elif default_key_direction in self.animation_frames:
            # print(f"Warning: Animation key {key} not found. Falling back to {default_key_direction}")
            return self.animation_frames[default_key_direction]
        elif default_key_universal in self.animation_frames:
            # print(f"Warning: Animation key {key} not found. Falling back to {default_key_universal}")
            return self.animation_frames[default_key_universal]
        else: # Ultimate fallback for non-player animated sprites
            # print(f"Warning: Animation key {key} not found. Falling back to generic idle_right")
            return self.animation_frames.get("idle_right", [([[]], [(0,0,0,0)])])


    def update_animation(self, dt):
        self.animation_timer += dt * FPS * self.animation_speed 
        current_animation_set = self.get_current_animation_set()
        if not current_animation_set or not current_animation_set[0][0]: 
            return

        if self.animation_timer >= 1: # 1 is arbitrary threshold, related to animation_speed
            self.animation_timer = 0
            self.current_frame_index = (self.current_frame_index + 1) % len(current_animation_set)

    def draw(self, screen, camera_offset_x, camera_offset_y):
        current_animation_set = self.get_current_animation_set()
        if not current_animation_set or not current_animation_set[0][0]: 
             # print(f"DEBUG: No animation set for {self} state {self.state} facing_left {self.facing_left}")
             return

        if self.current_frame_index >= len(current_animation_set): # Safety check
            self.current_frame_index = 0 
        
        tile_indices, palette = current_animation_set[self.current_frame_index]
        if not tile_indices: 
            # print(f"DEBUG: Empty tile_indices for {self} frame {self.current_frame_index}")
            return

        # Adjust y position for taller sprites (like Super Mario)
        draw_y = self.rect.y - camera_offset_y
        if hasattr(self, 'player_form') and self.player_form == PLAYER_STATE_SUPER:
            # Super Mario's art is 16x16 but he's 16x32. The art is for his upper body.
            # The rect is already TILE_SIZE wide and 2*TILE_SIZE tall.
            # The art should be drawn at the top of this rect.
            pass # Rect handles positioning of the 2-tile high collision box
                 # Art will draw at rect.x, rect.y
        
        draw_snes_tile_indexed(screen, tile_indices, palette, 
                               self.rect.x - camera_offset_x, 
                               draw_y, 
                               self.image_scale)

class Player(AnimatedSprite):
    def __init__(self, game, x_tile, y_tile):
        super().__init__()
        self.game = game
        self.pos = pg.math.Vector2(x_tile * TILE_SIZE, y_tile * TILE_SIZE)
        self.vel = pg.math.Vector2(0, 0)
        self.acc = pg.math.Vector2(0, 0)
        
        self.player_form = PLAYER_STATE_SMALL # 'small', 'super', 'raccoon'
        self.set_form(PLAYER_STATE_SMALL, initial_load=True) # Initial setup
        
        self.on_ground = False
        self.can_jump = True 
        self.score = 0
        self.lives = 3
        self.invincible_timer = 0 # Frames of invincibility after taking damage
        self.invincibility_duration = FPS * 2 # 2 seconds
        self.blink_timer = 0

    def set_form(self, new_form, initial_load=False): 
        old_bottom = self.rect.bottom if hasattr(self, 'rect') and not initial_load else self.pos.y + TILE_SIZE
        
        self.player_form = new_form
        self.animation_frames = {} # Clear old animations

        if self.player_form == PLAYER_STATE_SMALL:
            self.art_height_chars = 16 
            self.player_height_tiles = 1 
            self.load_animation_frames(f"{PLAYER_STATE_SMALL}_idle", [SMB3_MARIO_SMALL_IDLE_R_ART])
            self.load_animation_frames(f"{PLAYER_STATE_SMALL}_walk", [SMB3_MARIO_SMALL_WALK_R_ART_1, SMB3_MARIO_SMALL_WALK_R_ART_2])
            self.load_animation_frames(f"{PLAYER_STATE_SMALL}_jump", [SMB3_MARIO_SMALL_JUMP_R_ART])
        elif self.player_form == PLAYER_STATE_SUPER:
            self.art_height_chars = 16 # Art is still 16 high, but player is 2 tiles
            self.player_height_tiles = 2
            self.load_animation_frames(f"{PLAYER_STATE_SUPER}_idle", [SMB3_MARIO_SUPER_IDLE_R_ART])
            self.load_animation_frames(f"{PLAYER_STATE_SUPER}_walk", [SMB3_MARIO_SUPER_WALK_R_ART_1, SMB3_MARIO_SUPER_WALK_R_ART_2])
            self.load_animation_frames(f"{PLAYER_STATE_SUPER}_jump", [SMB3_MARIO_SUPER_JUMP_R_ART])
        # Add PLAYER_STATE_RACCOON here later, nyaa~
        
        current_x = self.pos.x
        new_height_pixels = self.player_height_tiles * TILE_SIZE
        self.rect = pg.Rect(current_x, old_bottom - new_height_pixels, TILE_SIZE, new_height_pixels)
        self.pos.x = self.rect.x 
        self.pos.y = self.rect.y
        self.current_frame_index = 0 # Reset animation

    def get_current_animation_set(self): # Override for Player form
        direction = "left" if self.facing_left else "right"
        key = f"{self.player_form}_{self.state}_{direction}"
        
        # Fallback if a specific state for a form isn't found (e.g. super_skid_right)
        fallback_key = f"{self.player_form}_idle_{direction}"

        if key in self.animation_frames:
            return self.animation_frames[key]
        elif fallback_key in self.animation_frames:
            return self.animation_frames[fallback_key]
        else: # Absolute fallback (should not happen if idle states for all forms are defined)
            # print(f"CRITICAL WARNING: Player animation key {key} AND fallback {fallback_key} not found!")
            return [([[]],[(0,0,0,0)])]


    def jump(self):
        if self.on_ground:
            jump_power = PLAYER_SUPER_JUMP_POWER if self.player_form != PLAYER_STATE_SMALL else PLAYER_JUMP_POWER
            self.vel.y = -jump_power
            self.on_ground = False
            self.can_jump = False 

    def take_damage(self):
        if self.invincible_timer > 0:
            return False # Already invincible

        if self.player_form == PLAYER_STATE_SUPER: # or PLAYER_STATE_RACCOON
            self.set_form(PLAYER_STATE_SMALL)
            self.invincible_timer = self.invincibility_duration
            # Add small bounce or knockback if desired
            return True # Took damage, downgraded
        elif self.player_form == PLAYER_STATE_SMALL:
            self.die()
            return True # Died
        return False # Should not happen

    def update(self, dt, platforms):
        self.acc = pg.math.Vector2(0, GRAVITY)
        keys = pg.key.get_pressed()

        if self.invincible_timer > 0:
            self.invincible_timer -= 1 
            self.blink_timer = (self.blink_timer + 1) % 10 # Blink every 10 frames for 5 frames on, 5 off

        if keys[pg.K_LEFT]:
            self.acc.x = -PLAYER_ACCEL
            self.facing_left = True
        elif keys[pg.K_RIGHT]:
            self.acc.x = PLAYER_ACCEL
            self.facing_left = False
        
        self.acc.x += self.vel.x * PLAYER_FRICTION
        self.vel.x += self.acc.x 
        if abs(self.vel.x) < 0.1: self.vel.x = 0

        self.vel.x = max(-PLAYER_MAX_SPEED_X, min(self.vel.x, PLAYER_MAX_SPEED_X))
        
        self.pos.x += self.vel.x
        self.rect.x = round(self.pos.x)
        self.collide_with_platforms_x(platforms)

        if keys[pg.K_SPACE]:
            if self.can_jump and self.on_ground:
                 self.jump()
        else: 
            self.can_jump = True # Allow re-jump if key released and on ground again

        self.vel.y += self.acc.y 
        self.vel.y = min(self.vel.y, MAX_FALL_SPEED) 
        self.pos.y += self.vel.y
        self.rect.y = round(self.pos.y)
        
        self.on_ground = False 
        self.collide_with_platforms_y(platforms)

        if not self.on_ground:
            self.state = "jump"
        elif abs(self.vel.x) > 0.1: 
            self.state = "walk"
        else:
            self.state = "idle"
        
        self.update_animation(dt)

        if self.rect.top > SCREEN_HEIGHT + TILE_SIZE * 2: 
            self.die()

    def collide_with_platforms_x(self, platforms):
        for plat in platforms:
            if self.rect.colliderect(plat.rect):
                if self.vel.x > 0: 
                    self.rect.right = plat.rect.left
                    self.vel.x = 0
                elif self.vel.x < 0: 
                    self.rect.left = plat.rect.right
                    self.vel.x = 0
                self.pos.x = self.rect.x

    def collide_with_platforms_y(self, platforms):
        for plat in platforms:
            if self.rect.colliderect(plat.rect):
                if self.vel.y > 0: 
                    self.rect.bottom = plat.rect.top
                    self.vel.y = 0
                    self.on_ground = True
                elif self.vel.y < 0: 
                    self.rect.top = plat.rect.bottom
                    self.vel.y = 0 # Bonk head
                    if hasattr(plat, 'hit_from_bottom'):
                        plat.hit_from_bottom(self) 
                self.pos.y = self.rect.y
    
    def die(self):
        self.lives -= 1
        if self.lives > 0:
            self.game.reset_level_soft() 
        else:
            self.game.game_over = True
    
    def draw(self, screen, camera_offset_x, camera_offset_y):
        if self.invincible_timer > 0 and self.blink_timer < 5: # Blink effect
            return # Skip drawing for this frame
        super().draw(screen, camera_offset_x, camera_offset_y)


class Particle(AnimatedSprite): # For brick breaks, etc.
    def __init__(self, game, x, y, art_frames, vel_x, vel_y, lifetime_frames):
        super().__init__()
        self.game = game
        self.pos = pg.math.Vector2(x,y)
        self.rect = pg.Rect(self.pos.x, self.pos.y, TILE_SIZE // 2, TILE_SIZE // 2) # Smaller particles
        self.load_animation_frames("idle", art_frames)
        self.vel = pg.math.Vector2(vel_x, vel_y)
        self.lifetime = lifetime_frames
        self.animation_speed = 0 # Static particle art for now

    def update(self, dt, platforms): # platforms not used, but for consistency
        self.vel.y += GRAVITY / 2 # Particles affected by gravity less
        self.pos += self.vel
        self.rect.topleft = self.pos
        self.lifetime -=1
        if self.lifetime <= 0:
            self.kill()

class Block(AnimatedSprite): 
    def __init__(self, game, x_tile, y_tile, art_frames_list, solid=True, block_type="generic"):
        super().__init__()
        self.game = game
        self.pos = pg.math.Vector2(x_tile * TILE_SIZE, y_tile * TILE_SIZE)
        self.rect = pg.Rect(self.pos.x, self.pos.y, TILE_SIZE, TILE_SIZE)
        self.load_animation_frames("idle", art_frames_list) 
        self.solid = solid
        self.block_type = block_type
        self.animation_speed = 0 # Most blocks are not animated by default

    def update(self, dt): 
        if self.animation_speed > 0:
             self.update_animation(dt)

class BrickBlock(Block):
    def __init__(self, game, x_tile, y_tile):
        super().__init__(game, x_tile, y_tile, [SMB3_BRICK_BLOCK_ART], solid=True, block_type="brick")

    def hit_from_bottom(self, player):
        if player.player_form != PLAYER_STATE_SMALL : # Super or Raccoon Mario can break bricks
            self.game.spawn_particles(self.rect.centerx, self.rect.top)
            self.kill() # Remove the brick
            # Add score for breaking brick
            player.score += 50
        else: # Small Mario just bonks it
            # Play bonk sound effect if sounds were implemented
            # Could add a small visual bump animation to the block
            pass

class QuestionBlock(Block):
    def __init__(self, game, x_tile, y_tile, contains="mushroom"): # Default to mushroom
        super().__init__(game, x_tile, y_tile, 
                         [SMB3_QUESTION_BLOCK_ART_FRAME1, SMB3_QUESTION_BLOCK_ART_FRAME2], 
                         solid=True, block_type="qblock")
        self.is_active = True 
        self.animation_speed = 0.05 
        self.contains = contains # What item is inside: "mushroom", "leaf"

    def hit_from_bottom(self, player):
        if self.is_active:
            self.is_active = False
            self.animation_speed = 0 
            self.load_animation_frames("idle", [SMB3_USED_BLOCK_ART]) 
            self.current_frame_index = 0 

            item_to_spawn = None
            if player.player_form == PLAYER_STATE_SMALL:
                item_to_spawn = Mushroom(self.game, self.pos.x / TILE_SIZE, self.pos.y / TILE_SIZE)
            else: # Super or Raccoon Mario
                item_to_spawn = SuperLeaf(self.game, self.pos.x / TILE_SIZE, self.pos.y / TILE_SIZE)
            
            if item_to_spawn:
                self.game.all_sprites.add(item_to_spawn)
                self.game.items.add(item_to_spawn)


class GroundBlock(Block):
    def __init__(self, game, x_tile, y_tile):
        super().__init__(game, x_tile, y_tile, [SMB3_GROUND_BLOCK_ART], solid=True, block_type="ground")

class Enemy(AnimatedSprite): # Base class for enemies
    def __init__(self, game, x_tile, y_tile):
        super().__init__()
        self.game = game
        self.pos = pg.math.Vector2(x_tile * TILE_SIZE, y_tile * TILE_SIZE)
        # rect will be defined by subclass
        self.vel = pg.math.Vector2(-ENEMY_MOVE_SPEED, 0) 
        self.on_ground = False # Enemies can also be affected by gravity if needed
        self.state = "walk" # Common states: walk, squished, shell (for Koopa)
        self.health = 1 # Most basic enemies have 1 HP

    def common_update_physics(self, dt, platforms):
        # Basic gravity (optional, most SMB3 enemies stick to ground unless airborne type)
        # self.vel.y += GRAVITY * 0.5 # Weaker gravity for simple enemies
        # self.pos.y += self.vel.y
        # self.rect.y = round(self.pos.y)
        # self.collide_with_platforms_y(platforms) # Simplified platform collision for Y

        # X movement and collision
        self.pos.x += self.vel.x * dt * FPS # Scale by dt and FPS for consistent speed
        self.rect.x = round(self.pos.x)
        self.collide_with_platforms_x(platforms)
        self.check_ledge_turn(platforms)


    def collide_with_platforms_x(self, platforms):
        for plat in platforms: 
            if plat.solid and self.rect.colliderect(plat.rect):
                if self.vel.x > 0: 
                    self.rect.right = plat.rect.left
                    self.vel.x *= -1
                    self.facing_left = True # Should be false if moving right
                elif self.vel.x < 0: 
                    self.rect.left = plat.rect.right
                    self.vel.x *= -1
                    self.facing_left = False # Should be true if moving left
                self.pos.x = self.rect.x
                # Update facing_left based on new direction
                if self.vel.x < 0: self.facing_left = True
                elif self.vel.x > 0: self.facing_left = False
                break
    
    def check_ledge_turn(self, platforms):
        # Check for a platform just ahead and below the enemy to turn if it's a ledge
        # This is a simplified version. A more robust way uses multiple check points.
        lookahead_x = self.rect.centerx + (TILE_SIZE / 1.5 * (1 if self.vel.x > 0 else -1))
        lookahead_y = self.rect.bottom + TILE_SIZE / 2 # Check slightly below current ground

        ledge_check_rect = pg.Rect(lookahead_x - TILE_SIZE / 4, lookahead_y - TILE_SIZE/4, TILE_SIZE/2, TILE_SIZE/2)
        
        on_solid_ground_ahead = False
        for plat in platforms:
            if plat.solid and ledge_check_rect.colliderect(plat.rect):
                on_solid_ground_ahead = True
                break
        
        if not on_solid_ground_ahead and self.on_ground: # Only turn if on ground and no ground ahead
            self.vel.x *= -1
            self.facing_left = not self.facing_left


    def collide_with_platforms_y(self, platforms): # Simplified for basic enemies
        self.on_ground = False
        for plat in platforms:
            if self.rect.colliderect(plat.rect):
                if self.vel.y >= 0 : # Check only falling or on ground, not rising through
                    # Check if the enemy's bottom is roughly at the platform's top
                    # and there was some overlap indicating a landing
                    if self.rect.bottom > plat.rect.top and self.rect.bottom < plat.rect.top + MAX_FALL_SPEED +1 :
                         self.rect.bottom = plat.rect.top
                         self.vel.y = 0
                         self.on_ground = True
                         self.pos.y = self.rect.y
                         break # Found ground

    def get_stomped(self, player): # Common behavior for stomped enemies
        self.state = "squished"
        self.animation_speed = 0 
        self.current_frame_index = 0 
        self.vel.x = 0
        self.squish_timer = FPS // 2 # Show for 0.5 sec approx
        player.vel.y = -PLAYER_JUMP_POWER / 2.0 # Smaller bounce for player
        player.score += 100
        return True # Successfully stomped

    def take_hit(self, projectile=None): # For fireballs, shell hits, etc.
        # Basic: just die and give score
        # Could add flip animation, sound, etc.
        self.kill()
        # self.game.player.score += 200 # Score for projectile hit
        return True


class Goomba(Enemy):
    def __init__(self, game, x_tile, y_tile):
        super().__init__(game, x_tile, y_tile)
        self.rect = pg.Rect(self.pos.x, self.pos.y, TILE_SIZE, TILE_SIZE)
        self.load_animation_frames("walk", [SMB3_GOOMBA_WALK1_ART, SMB3_GOOMBA_WALK2_ART])
        self.load_animation_frames("squished", [SMB3_GOOMBA_SQUISHED_ART]) 
        self.animation_speed = 0.08 
        self.squish_timer = 0 
        # Initial facing direction based on initial velocity (usually left)
        self.facing_left = self.vel.x < 0

    def update(self, dt, platforms):
        if self.state == "walk":
            self.common_update_physics(dt, platforms) # Use common physics
            # Goombas are dumb, they fall off ledges, so no check_ledge_turn for them
            # For Y physics, ensure they stay on ground if they are ground type
            # A simple way to keep them grounded without complex Y collision:
            self.vel.y += GRAVITY # Always affected by gravity
            self.pos.y += self.vel.y
            self.rect.y = round(self.pos.y)
            self.collide_with_platforms_y(platforms) # This handles landing

            self.update_animation(dt)

        elif self.state == "squished":
            self.squish_timer -= 1 
            if self.squish_timer <= 0:
                self.kill() 

    # get_current_animation_set will use the base class method but driven by self.state
    # Squished art is usually not directional, if it were, we'd override get_current_animation_set

class Koopa(Enemy):
    def __init__(self, game, x_tile, y_tile):
        super().__init__(game, x_tile, y_tile)
        self.rect = pg.Rect(self.pos.x, self.pos.y, TILE_SIZE, TILE_SIZE) # Koopas are 1 tile high when walking
        self.load_animation_frames("walk", [SMB3_KOOPA_WALK1_R_ART, SMB3_KOOPA_WALK2_R_ART])
        self.load_animation_frames("shell", [SMB3_KOOPA_SHELL_ART])
        self.animation_speed = 0.1
        self.shell_timer = 0 # Timer for how long it stays in shell before waking up
        self.SHELL_WAKE_TIME = FPS * 8 # 8 seconds to wake up

    def update(self, dt, platforms):
        if self.state == "walk":
            self.common_update_physics(dt, platforms) # Koopas turn at ledges
            # Y physics for Koopas
            self.vel.y += GRAVITY 
            self.pos.y += self.vel.y
            self.rect.y = round(self.pos.y)
            self.collide_with_platforms_y(platforms)
            self.update_animation(dt)

        elif self.state == "shell":
            self.common_update_physics(dt, platforms) # Shell can also move and collide
             # Y physics for shell
            self.vel.y += GRAVITY 
            self.pos.y += self.vel.y
            self.rect.y = round(self.pos.y)
            self.collide_with_platforms_y(platforms)
            
            if self.vel.x == 0: # Stationary shell
                self.shell_timer -= 1
                if self.shell_timer <= 0:
                    self.state = "walk" # Wake up
                    self.vel.x = -ENEMY_MOVE_SPEED if self.facing_left else ENEMY_MOVE_SPEED # Start walking again
                    self.animation_speed = 0.1 # Resume animation
            # No animation update needed for static shell art usually
            # self.update_animation(dt) # Keep if shell has animation

    def get_stomped(self, player):
        if self.state == "walk":
            self.state = "shell"
            self.vel.x = 0 # Stop moving
            self.animation_speed = 0 # Stop walking animation
            self.current_frame_index = 0 # Show shell art
            self.shell_timer = self.SHELL_WAKE_TIME
            player.vel.y = -PLAYER_JUMP_POWER / 1.5 # Higher bounce off Koopa
            player.score += 100
            return False # Not killed, just shelled
        elif self.state == "shell":
            if self.vel.x == 0: # Stationary shell kicked
                # Kick to the direction player is facing, or away from player
                self.vel.x = KOOPA_SHELL_SPEED if player.rect.centerx < self.rect.centerx else -KOOPA_SHELL_SPEED
                self.facing_left = self.vel.x < 0
            else: # Moving shell is stomped again
                self.vel.x = 0 # Stop it
                self.shell_timer = self.SHELL_WAKE_TIME # Reset wake timer
            player.vel.y = -PLAYER_JUMP_POWER / 1.8 # Bounce
            return False # Not killed
        return False # Should not reach here
    
    def take_hit(self, projectile=None): # Shells make Koopas resistant
        if self.state == "walk":
            # Koopas usually get flipped by fireballs, not implemented here
            self.kill() # Simple kill for now
            # self.game.player.score += 200
            return True
        elif self.state == "shell":
            # Shells are immune to some things, or get knocked around
            # For now, let fireballs also kill shelled Koopas if desired
            # self.kill() 
            # self.game.player.score += 200
            return False # Shells are tough!
        return False


class Item(AnimatedSprite): # Base class for items like mushroom, leaf
    def __init__(self, game, x_tile, y_tile_spawn_base):
        super().__init__()
        self.game = game
        # Position set by subclass, typically appears from block
        self.vel = pg.math.Vector2(0,0)
        self.on_ground = False
        self.spawn_state = "rising" # "rising", "active", "landed"
        self.rise_target_y = (y_tile_spawn_base - 1) * TILE_SIZE # Target Y after rising one block up
        self.rise_speed = -1 # Pixels per update step (negative is up)

    def update_spawn_rise(self):
        if self.spawn_state == "rising":
            self.pos.y += self.rise_speed 
            self.rect.y = round(self.pos.y)
            if self.pos.y <= self.rise_target_y:
                self.pos.y = self.rise_target_y
                self.rect.y = round(self.pos.y)
                self.spawn_state = "active"
                # Give initial horizontal velocity once active
                self.vel.x = ENEMY_MOVE_SPEED * 0.75 # Items move a bit slower than Goombas
                return True # Finished rising
        return False # Still rising

    def common_item_physics(self, dt, platforms):
        self.vel.y += GRAVITY
        self.vel.y = min(self.vel.y, MAX_FALL_SPEED)

        self.pos.x += self.vel.x * dt * FPS
        self.pos.y += self.vel.y 
        
        self.rect.x = round(self.pos.x)
        # X collision
        for plat in platforms:
            if plat.solid and self.rect.colliderect(plat.rect):
                if self.vel.x > 0:
                    self.rect.right = plat.rect.left
                    self.vel.x *= -1
                elif self.vel.x < 0:
                    self.rect.left = plat.rect.right
                    self.vel.x *= -1
                self.pos.x = self.rect.x
                break
        
        self.rect.y = round(self.pos.y)
        self.on_ground = False
        # Y collision
        for plat in platforms:
            if plat.solid and self.rect.colliderect(plat.rect):
                if self.vel.y > 0:
                    self.rect.bottom = plat.rect.top
                    self.vel.y = 0
                    self.on_ground = True
                elif self.vel.y < 0: # Bonking head (items usually don't care)
                    self.rect.top = plat.rect.bottom
                    self.vel.y = 0 
                self.pos.y = self.rect.y
                break
        
        # Simple ledge turning for items like mushrooms
        if self.on_ground:
            lookahead_x = self.rect.centerx + (TILE_SIZE / 2 * (1 if self.vel.x > 0 else -1))
            lookahead_y = self.rect.bottom + TILE_SIZE / 4
            ledge_check_rect = pg.Rect(lookahead_x - TILE_SIZE / 8, lookahead_y - TILE_SIZE/8, TILE_SIZE/4, TILE_SIZE/4)
            on_solid_ground_ahead = False
            for plat in platforms:
                if plat.solid and ledge_check_rect.colliderect(plat.rect):
                    on_solid_ground_ahead = True
                    break
            if not on_solid_ground_ahead:
                self.vel.x *= -1


class Mushroom(Item):
    def __init__(self, game, x_tile, y_tile_spawn_base):
        super().__init__(game, x_tile, y_tile_spawn_base)
        # Spawn at block's original tile, will rise up
        self.pos = pg.math.Vector2(x_tile * TILE_SIZE, y_tile_spawn_base * TILE_SIZE) 
        self.rect = pg.Rect(self.pos.x, self.pos.y, TILE_SIZE, TILE_SIZE)
        self.load_animation_frames("idle", [SMB3_MUSHROOM_ART])
        self.animation_speed = 0 # Mushrooms usually don't animate

    def update(self, dt, platforms):
        if self.update_spawn_rise(): # True if finished rising
            # Now active, apply physics
            self.common_item_physics(dt, platforms)
        
        self.update_animation(dt) # In case it ever has animation

class SuperLeaf(Item):
    def __init__(self, game, x_tile, y_tile_spawn_base): 
        super().__init__(game, x_tile, y_tile_spawn_base)
        self.pos = pg.math.Vector2(x_tile * TILE_SIZE, y_tile_spawn_base * TILE_SIZE)
        self.rect = pg.Rect(self.pos.x, self.pos.y, TILE_SIZE, TILE_SIZE)
        self.load_animation_frames("idle", [SMB3_SUPER_LEAF_ART]) 
        self.animation_speed = 0.1 # Leaf can have a slight flutter
        
        self.base_y_drift = 0 
        self.drift_amplitude_y = TILE_SIZE / 4 
        self.drift_frequency_y = 0.05 
        self.drift_timer_y = random.uniform(0, 2 * math.pi) 

    def update(self, dt, platforms):
        if self.spawn_state == "rising":
            if self.update_spawn_rise(): # True if finished rising
                self.base_y_drift = self.pos.y 
                # Leaf gets a random horizontal direction after rising
                self.vel.x = random.choice([ENEMY_MOVE_SPEED * 0.5, -ENEMY_MOVE_SPEED * 0.5])

        elif self.spawn_state == "active":
            self.pos.x += self.vel.x * dt * FPS
            
            self.drift_timer_y += self.drift_frequency_y * FPS * dt 
            offset_y = self.drift_amplitude_y * math.sin(self.drift_timer_y)
            self.pos.y = self.base_y_drift + offset_y # Apply drift relative to base Y

            self.rect.x = round(self.pos.x)
            self.rect.y = round(self.pos.y)

            # Horizontal collision for leaf (simplified, doesn't interact with Y much while drifting)
            for plat in platforms:
                if plat.solid and self.rect.colliderect(plat.rect):
                    if self.vel.x > 0 and self.rect.right > plat.rect.left:
                        self.rect.right = plat.rect.left
                        self.vel.x *= -1
                    elif self.vel.x < 0 and self.rect.left < plat.rect.right:
                        self.rect.left = plat.rect.right
                        self.vel.x *= -1
                    self.pos.x = self.rect.x
                    break # Stop after one collision
            # Leaf does not fall with gravity while drifting like this

        self.update_animation(dt) 


class Flagpole(AnimatedSprite):
    def __init__(self, game, x_tile, y_tile):
        super().__init__()
        self.game = game
        # Flagpole art is 1 tile wide, but logically it's taller.
        # For collision, rect can be TILE_SIZE wide and multiple TILE_SIZE tall.
        # Art is anchored at top.
        self.pos = pg.math.Vector2(x_tile * TILE_SIZE, y_tile * TILE_SIZE)
        self.rect = pg.Rect(self.pos.x, self.pos.y, TILE_SIZE, TILE_SIZE * 4) # Example: 4 tiles high collision
        self.load_animation_frames("idle", [SMB3_FLAGPOLE_ART])
        self.animation_speed = 0 # Flag itself could animate later

class Camera:
    def __init__(self, width_tiles, height_tiles): 
        self.camera_rect_on_screen = pg.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.offset = pg.math.Vector2(0, 0) 
        self.world_width_pixels = 0 
        self.world_height_pixels = 0 

    def update(self, target_player):
        # Camera follows player, clamped to world boundaries
        # Center player horizontally, keep Y fixed for now (SMB style)
        target_cam_x = -target_player.rect.centerx + SCREEN_WIDTH // 2
        
        # Clamp X
        clamped_cam_x = min(0, target_cam_x) # Don't go left of world start
        clamped_cam_x = max(clamped_cam_x, -(self.world_width_pixels - SCREEN_WIDTH)) # Don't go right of world end

        # Y clamping (simple for now, could be more dynamic for vertical levels)
        # Typically, SMB camera doesn't move up unless player is very high, and rarely down past a baseline
        clamped_cam_y = 0 # For basic horizontal scrolling. Adjust if verticality is needed.
        # A more SMB3-like Y might try to keep player in lower third unless flying etc.

        self.offset.x = clamped_cam_x
        self.offset.y = clamped_cam_y # For now, Y is fixed or player-centric.
        
    def get_world_view_rect(self): 
        # Returns the rectangle representing the camera's view in world coordinates
        return pg.Rect(-self.offset.x, -self.offset.y, SCREEN_WIDTH, SCREEN_HEIGHT)


# Level and Overworld Data
LEVEL_1_1_DATA = [ 
    "..................................................................................................F.",
    "..................................................................................................F.",
    "..................BBQB............................................................................F.",
    "..................................................................................................F.",
    "...................................Q....B................K........................................F.",
    ".........................BBBB.........QQQ.........................................................F.",
    "............................................................E.....................................F.",
    "...................E................E.........E.E.................................................F.",
    "GGGGGGGGGGGGGGGGGGGGGGGG...GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG...GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGG...GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG...GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG" 
]
# 'K' for Koopa
LEVEL_1_2_DATA = [ 
    "..................................................F.",
    "..................................................F.",
    "............Q....B............K...................F.",
    ".........................E........................F.",
    ".......E............E................BBQ..........F.",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG"
]

OVERWORLD_DATA = [
    "                    ",
    " . 1 . 2 . . . . .  ", 
    " . . . . . . . . .  ",
    " . . . . . . . . .  ",
    " . . . . . . . . .  ",
    " . . . . . . . . .  ",
    " . . . . . . . . .  ", 
    "                    "
]

class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pg.display.set_caption("SMB3 Style Game - Fucking CATSDK Edition, MEOW!")
        self.clock = pg.time.Clock()
        self.font = pg.font.Font(None, TILE_SIZE // 2) 
        
        self.game_state = "overworld" 
        self.overworld_data = OVERWORLD_DATA
        self.mario_overworld_pos = (2,1) 
        
        found_first_level_node = False # ... (same as before)
        for r, row in enumerate(self.overworld_data):
            for c, char_code in enumerate(row):
                if char_code.isdigit() or (char_code.isalpha() and char_code != 'P'):
                    self.mario_overworld_pos = (c,r)
                    found_first_level_node = True; break
            if found_first_level_node: break
        
        self.overworld_cell_size = TILE_SIZE 

        self.levels = {'1': LEVEL_1_1_DATA, '2': LEVEL_1_2_DATA} 
        
        self.game_over = False
        self.debug_mode = False 

        self.all_sprites = pg.sprite.Group()
        self.platforms = pg.sprite.Group() 
        self.enemies = pg.sprite.Group()
        self.items = pg.sprite.Group()
        self.flagpoles = pg.sprite.Group() 
        self.particles = pg.sprite.Group() # For visual effects like brick breaks

        self.player = None 
        self.camera = Camera(0,0) 
        self.current_level_char = '1' 

    def spawn_particles(self, center_x, top_y):
        # Spawn a few debris particles when a brick breaks
        for _ in range(4): # Spawn 4 pieces
            vel_x = random.uniform(-5, 5)
            vel_y = random.uniform(-8, -3) # Shoot upwards initially
            # Particle art needs to be defined if not already (SMB3_BRICK_DEBRIS_ART)
            # For now, let's assume a simple particle art exists
            particle = Particle(self, center_x - TILE_SIZE//4, top_y - TILE_SIZE//4, 
                                [SMB3_BRICK_DEBRIS_ART], 
                                vel_x, vel_y, FPS // 2) # Lasts 0.5 seconds
            self.all_sprites.add(particle)
            self.particles.add(particle)


    def load_level(self, level_data_str_array):
        self.all_sprites.empty()
        self.platforms.empty()
        self.enemies.empty()
        self.items.empty()
        self.flagpoles.empty()
        self.particles.empty()

        player_start_pos_tiles = (2, len(level_data_str_array) - 5) # Start a bit higher for super mario

        for row_idx, row_str in enumerate(level_data_str_array):
            for col_idx, char_code in enumerate(row_str):
                # x_pos, y_pos not needed here if passing col_idx, row_idx
                if char_code == 'G':
                    block = GroundBlock(self, col_idx, row_idx)
                    self.all_sprites.add(block); self.platforms.add(block)
                elif char_code == 'B':
                    block = BrickBlock(self, col_idx, row_idx)
                    self.all_sprites.add(block); self.platforms.add(block)
                elif char_code == 'Q':
                    # Could vary Q block contents here based on level design
                    block = QuestionBlock(self, col_idx, row_idx, contains="mushroom") # Default
                    self.all_sprites.add(block); self.platforms.add(block)
                elif char_code == 'E':
                    enemy = Goomba(self, col_idx, row_idx)
                    self.all_sprites.add(enemy); self.enemies.add(enemy)
                elif char_code == 'K': # Koopa Troopa
                    enemy = Koopa(self, col_idx, row_idx)
                    self.all_sprites.add(enemy); self.enemies.add(enemy)
                elif char_code == 'F': 
                    flagpole = Flagpole(self, col_idx, row_idx)
                    self.all_sprites.add(flagpole); self.flagpoles.add(flagpole)
        
        prev_lives = 3; prev_score = 0; prev_form = PLAYER_STATE_SMALL
        if self.player: # Preserve stats if reloading
            prev_lives = self.player.lives
            prev_score = self.player.score
            prev_form = self.player.player_form # Keep current form on soft reset

        self.player = Player(self, player_start_pos_tiles[0], player_start_pos_tiles[1])
        self.player.lives = prev_lives
        self.player.score = prev_score
        # If soft resetting, restore form. If hard reset, form is already set to small by Player init.
        # self.player.set_form(prev_form) # This might need care if player died as super.

        self.all_sprites.add(self.player)
        
        level_width_pixels = len(level_data_str_array[0]) * TILE_SIZE
        level_height_pixels = len(level_data_str_array) * TILE_SIZE
        self.camera = Camera(level_width_pixels // TILE_SIZE, level_height_pixels // TILE_SIZE)
        self.camera.world_width_pixels = level_width_pixels
        self.camera.world_height_pixels = level_height_pixels


    def enter_level(self, level_char_id):
        if level_char_id in self.levels:
            self.current_level_char = level_char_id
            
            current_score = 0; current_lives = 3; current_form = PLAYER_STATE_SMALL
            if self.player: # Keep score and lives if player exists (e.g. from overworld)
                current_score = self.player.score
                current_lives = self.player.lives
                current_form = self.player.player_form # Keep form from overworld state if desired
            
            self.load_level(self.levels[level_char_id])
            self.player.score = current_score
            self.player.lives = current_lives
            self.player.set_form(current_form) # Ensure player starts with the correct form

            self.game_state = "level"
            self.game_over = False 

    def complete_level(self):
        self.game_state = "overworld" 
        # Player's mario_overworld_pos remains on the completed level node.
        # Could add logic to unlock next level node here.

    def reset_level_soft(self): # Called on player death if lives > 0
        if self.player:
            current_score = self.player.score 
            current_lives = self.player.lives # Already decremented by Player.die()
            # Player form resets to small typically on death, unless game rule is different
            
            self.load_level(self.levels[self.current_level_char]) 
            self.player.score = current_score
            self.player.lives = current_lives
            self.player.set_form(PLAYER_STATE_SMALL) # Reset to small Mario
            if self.player.lives <= 0: 
                self.game_over = True
        else: 
            self.enter_level(self.current_level_char) 

    def reset_game_hard(self): # Called on Game Over and R pressed
        self.game_over = False
        level_to_start_char = self.overworld_data[self.mario_overworld_pos[1]][self.mario_overworld_pos[0]]
        if level_to_start_char not in self.levels: 
            level_to_start_char = '1'
            # Find '1' on map (code from before)
            found_level_1_node = False
            for r_idx, r_str in enumerate(self.overworld_data):
                if found_level_1_node: break
                for c_idx, char_val in enumerate(r_str):
                    if char_val == '1':
                        self.mario_overworld_pos = (c_idx, r_idx); found_level_1_node = True; break
        
        # Store score and lives from player before full reset for enter_level
        # Actually, hard reset means score 0, lives 3
        self.player = None # Effectively force re-creation with defaults in enter_level
        self.enter_level(level_to_start_char) 
        # enter_level will create new player, load_level inside it.
        # Then set score/lives.
        self.player.score = 0
        self.player.lives = 3
        self.player.set_form(PLAYER_STATE_SMALL)


    def draw_overworld(self):
        self.screen.fill(BACKGROUND_COLOR) 
        ow_tile_size = self.overworld_cell_size
        for r, row_str in enumerate(self.overworld_data):
            for c, char_code in enumerate(row_str):
                x, y = c * ow_tile_size, r * ow_tile_size
                rect = (x, y, ow_tile_size, ow_tile_size)
                if char_code == ' ': 
                    pg.draw.rect(self.screen, color_map['B'], rect, 1) 
                elif char_code == '.': 
                    pg.draw.rect(self.screen, color_map['G'], rect) 
                elif char_code.isdigit() or (char_code.isalpha() and char_code not in 'P'): 
                    pg.draw.rect(self.screen, color_map['Y'], rect) 
                    self.draw_text(char_code, x + ow_tile_size // 3, y + ow_tile_size // 3, 'K')
        
        mario_ow_x = self.mario_overworld_pos[0] * ow_tile_size
        mario_ow_y = self.mario_overworld_pos[1] * ow_tile_size
        pg.draw.rect(self.screen, color_map['R'], 
                     (mario_ow_x + ow_tile_size//4, mario_ow_y + ow_tile_size//4, 
                      ow_tile_size//2, ow_tile_size//2))


    def draw_text(self, text_str, x, y, color_char_code='W', Sfont=None):
        if Sfont is None: Sfont = self.font
        text_surface = Sfont.render(text_str, True, color_map[color_char_code])
        self.screen.blit(text_surface, (x,y))

    async def main(self):
        running = True
        while running:
            raw_dt = self.clock.tick(FPS) / 1000.0 
            
            for event in pg.event.get():
                if event.type == pg.QUIT: running = False; return
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE: running = False; return
                    if event.key == pg.K_F1: self.debug_mode = not self.debug_mode
                    
                    if self.game_state == "level":
                        if self.game_over and event.key == pg.K_r:
                            self.reset_game_hard()
                    # Overworld keyboard nav can be added here if desired
                
                if self.game_state == "overworld":
                    if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                        mouse_x, mouse_y = event.pos
                        clicked_col = mouse_x // self.overworld_cell_size
                        clicked_row = mouse_y // self.overworld_cell_size
                        if (0 <= clicked_row < len(self.overworld_data) and
                            0 <= clicked_col < len(self.overworld_data[0])):
                            char_at_click = self.overworld_data[clicked_row][clicked_col]
                            if char_at_click in self.levels:
                                self.mario_overworld_pos = (clicked_col, clicked_row)
                                self.enter_level(char_at_click)
            
            # --- Update Logic ---
            if self.game_state == "level" and not self.game_over:
                self.player.update(raw_dt, self.platforms) 
                for enemy in list(self.enemies): 
                    enemy.update(raw_dt, self.platforms) 
                for item in list(self.items):
                    item.update(raw_dt, self.platforms) 
                for particle in list(self.particles):
                    particle.update(raw_dt, self.platforms)
                
                self.camera.update(self.player)

                # Player-Enemy Collisions
                if self.player.invincible_timer <= 0:
                    for enemy in list(self.enemies): 
                        if self.player.rect.colliderect(enemy.rect):
                            is_stomp = (self.player.vel.y > 0 and 
                                        self.player.rect.bottom < enemy.rect.centery + TILE_SIZE / 3 and # Generous stomp
                                        not self.player.on_ground) # Must be falling

                            if isinstance(enemy, Goomba):
                                if enemy.state == "walk":
                                    if is_stomp: enemy.get_stomped(self.player)
                                    else: self.player.take_damage()
                            elif isinstance(enemy, Koopa):
                                if enemy.state == "walk":
                                    if is_stomp: enemy.get_stomped(self.player) # Turns to shell
                                    else: self.player.take_damage()
                                elif enemy.state == "shell":
                                    if is_stomp: # Stomping a shell
                                        enemy.get_stomped(self.player) # Kicks or stops it
                                    elif enemy.vel.x != 0 : # Player runs into moving shell
                                        self.player.take_damage()
                                    else: # Player touches stationary shell
                                        # Kick it
                                        enemy.vel.x = KOOPA_SHELL_SPEED if self.player.rect.centerx < enemy.rect.centerx else -KOOPA_SHELL_SPEED
                                        enemy.facing_left = enemy.vel.x < 0

                            if self.game_over or self.player.invincible_timer > 0 : break # Stop checking enemies if player died or got hit

                # Shell - Enemy Collisions
                for shell_koopa in list(self.enemies):
                    if isinstance(shell_koopa, Koopa) and shell_koopa.state == "shell" and shell_koopa.vel.x != 0:
                        for other_enemy in list(self.enemies):
                            if other_enemy != shell_koopa and shell_koopa.rect.colliderect(other_enemy.rect):
                                other_enemy.take_hit(projectile=shell_koopa) # Enemy hit by shell
                                self.player.score += 200 # Score for shell hit
                                # Shell could also be destroyed or reverse, SMB3 shells usually go through
                
                # Player - Item Collisions
                for item in list(self.items):
                    if self.player.rect.colliderect(item.rect):
                        if isinstance(item, Mushroom):
                            if self.player.player_form == PLAYER_STATE_SMALL:
                                self.player.set_form(PLAYER_STATE_SUPER)
                                self.player.score += 1000
                            # else, already super, maybe just score
                            item.kill()
                        elif isinstance(item, SuperLeaf):
                            if self.player.player_form != PLAYER_STATE_RACCOON: # NYAA~ For future
                                # For now, if not small, go Super. If small, go Super.
                                # Proper logic: Small -> Super, Super -> Raccoon
                                if self.player.player_form == PLAYER_STATE_SMALL:
                                    self.player.set_form(PLAYER_STATE_SUPER) # Simplification: Leaf makes you Super first
                                # elif self.player.player_form == PLAYER_STATE_SUPER:
                                    # self.player.set_form(PLAYER_STATE_RACCOON) # NYAA~
                                self.player.score += 1000
                            item.kill()
                        
                # Player - Flagpole
                for flagpole in self.flagpoles:
                    if self.player.rect.colliderect(flagpole.rect):
                        self.player.score += 5000 # Bonus for flagpole
                        self.complete_level()
                        break 
            
            # --- Drawing Logic ---
            self.screen.fill(BACKGROUND_COLOR) 

            if self.game_state == "overworld":
                self.draw_overworld()
            elif self.game_state == "level":
                world_view = self.camera.get_world_view_rect()
                for sprite in self.all_sprites: # Draw all sprites respecting camera
                    if sprite.rect.colliderect(world_view): 
                         sprite.draw(self.screen, self.camera.offset.x, self.camera.offset.y)
                
                if self.player: # HUD
                    self.draw_text(f"SCORE: {self.player.score}", 20, 10, 'W')
                    self.draw_text(f"LIVES: {self.player.lives}", SCREEN_WIDTH - 150, 10, 'W')
                    self.draw_text(f"FORM: {self.player.player_form.upper()}", SCREEN_WIDTH // 2 - 50, 10, 'W')


                if self.game_over:
                    overlay = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pg.SRCALPHA)
                    overlay.fill((50, 50, 50, 180)) 
                    self.screen.blit(overlay, (0,0))
                    large_font = pg.font.Font(None, TILE_SIZE) 
                    self.draw_text("GAME FUCKING OVER", SCREEN_WIDTH // 2 - TILE_SIZE * 4, SCREEN_HEIGHT // 2 - TILE_SIZE, 'R', large_font)
                    self.draw_text("Press R to Restart, ya loser!", SCREEN_WIDTH // 2 - TILE_SIZE * 4, SCREEN_HEIGHT // 2 + TILE_SIZE //2, 'W')
            
            pg.display.flip()
            await asyncio.sleep(0) 

        pg.quit()


if __name__ == "__main__":
    game_instance = Game()
    asyncio.run(game_instance.main())

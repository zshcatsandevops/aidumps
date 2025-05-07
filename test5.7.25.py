# --- NEW: sprite-sheet setup ---------------------------------
import itertools

SPRITE_SHEET = "smas_smb3_tiles.png"  # put the PNG here
SHEET_TILE   = 16                     # sheet tiles are 16 px
DISPLAY_TILE = TILE                   # keep your 30-px world scale
SCALE_FACTOR = DISPLAY_TILE // SHEET_TILE  # 30//16 == 1 (trim to 1) or set 2

sheet_img = pygame.image.load(SPRITE_SHEET).convert_alpha()
if SCALE_FACTOR != 1:
    sheet_img = pygame.transform.scale_by(sheet_img, SCALE_FACTOR)

# slice sheet into 16×16 surfaces → list indexed by (col,row)
sheet_cols = sheet_img.get_width()  // (SHEET_TILE * SCALE_FACTOR)
sheet_rows = sheet_img.get_height() // (SHEET_TILE * SCALE_FACTOR)
tile_surfs = [
    sheet_img.subsurface(
        pygame.Rect(cx*SHEET_TILE*SCALE_FACTOR,
                    cy*SHEET_TILE*SCALE_FACTOR,
                    SHEET_TILE*SCALE_FACTOR,
                    SHEET_TILE*SCALE_FACTOR))
    for cy in range(sheet_rows) for cx in range(sheet_cols)
]

# pick two useful tiles for demo
TILE_SKY   = tile_surfs[0]           # first tile on sheet = empty sky
TILE_BRICK = tile_surfs[1]           # second tile = brown ground brick

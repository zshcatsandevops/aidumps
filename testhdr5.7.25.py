# --- NEW: procedural SMB3-style tiles --------------------------------------
SHEET_TILE    = 16     # logical source-tile size (for internal math only)
DISPLAY_TILE  = TILE   # 30 px world scale

# – create a cyan “sky” tile –
TILE_SKY = pygame.Surface((DISPLAY_TILE, DISPLAY_TILE), pygame.SRCALPHA)
TILE_SKY.fill((108, 180, 255))        # SMB3-ish sky blue

# – create a brown “brick” tile with darker mortar –
TILE_BRICK = pygame.Surface((DISPLAY_TILE, DISPLAY_TILE), pygame.SRCALPHA)
brick_base  = (146, 98, 52)           # mid-brown fill
mortar_line = (93, 59, 32)            # darker lines
TILE_BRICK.fill(brick_base)
# vertical mortar
pygame.draw.line(TILE_BRICK, mortar_line,
                 (DISPLAY_TILE//2, 0), (DISPLAY_TILE//2, DISPLAY_TILE))
# horizontal mortar (two lines to mimic SMB3 pattern)
pygame.draw.line(TILE_BRICK, mortar_line,
                 (0, DISPLAY_TILE//3), (DISPLAY_TILE, DISPLAY_TILE//3))
pygame.draw.line(TILE_BRICK, mortar_line,
                 (0, 2*DISPLAY_TILE//3), (DISPLAY_TILE, 2*DISPLAY_TILE//3))

tile_surfs = [TILE_SKY, TILE_BRICK]

# --- in the draw section (replace previous rect-fill loop) -----------------
screen.fill(BLACK)
for y in range(GRID_H):
    for x in range(GRID_W):
        idx = 1 if solids[y][x] else 0   # 1=brick, 0=sky
        screen.blit(tile_surfs[idx], (x*TILE, y*TILE))
pygame.draw.rect(screen, PLAYER_CLR, player)
pygame.display.flip()

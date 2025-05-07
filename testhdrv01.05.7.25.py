import pygame, sys

HEX_DATA = (
    "2e0000ea24ffae51699aa2213d84820a"
    "84e409ad11248b98c0817f21a352be19"
    "9309ce2010464a4af82731ec58c7e833"
    "82e3cebf85f4df94ce4b09c194568ac0"
    "1372a7fc9f844d73a3ca9a615897a327"
    "fc039876231dc7610304ae56bf388400"
    "40a70efdff52fe036f9530f197fbc085"
    "60d68025a963be03014e38e2f9a234ff"
    "bb3e0344780090cb88113a9465c07c63"
    "87f03cafd625e48b380aac7221d4f807"
    "5355504552204d4152494f4241413245"
    "303196000000000000000000008e0000"
    "1200a0e300f029e128d09fe51f00a0e3"
    "00f029e118d09fe598119fe518008fe2"
    "000081e590119fe50fe0a0e111ff2fe1"
    "f2ffffea007e0003807f000301c3a0e3"
    "023c8ce2002093e5221802e00020a0e3"
    "020a11e27c014315feffff1a042082e2"
    "010011e2b8004c112200001a042082e2"
    "800011e21f00001a042082e2400011e2"
    "1c00001a042082e2020011e21900001a"
    "042082e2040011e21600001a042082e2"
    "080011e21300001a042082e2100011e2"
    "1000001a042082e2200011e20d00001a"
    "042082e2010c11e20a00001a042082e2"
    "020c11e20700001a042082e2010b11e2"
    "0400001a042082e2020b11e20100001a"
    "042082e2010a11e2b200c3e1bc109fe5"
    "021081e0000091e510ff2fe101c3a0e3"
    "023c8ce2002093e5221802e00020a0e3"
    "020a11e27c014315feffff1a042082e2"
    "010011e2b8004c111900001a042082e2"
    "800011e21600001a042082e2400011e2"
    "1300001a042082e2020011e21000001a"
    "042082e2040011e20d00001a042082e2"
    "010c11e20a00001a042082e2020c11e2"
    "0700001a042082e2010b11e20400001a"
    "042082e2020b11e20100001a042082e2"
    "010a11e2b200c3e114109fe5021081e0"
    "000091e510ff2fe1fc7f00034d040008"
    "007a0003007a000370b5114d11496818"
    "048801f02ff9104aa918002008700f48"
    "29186f2008700e496e18307800285dd0"
    "201c82f0bdff012c16d0082c00d088e0"
    "3078022828d197f003fe064aa81815e0"
    "4023000356080000b2560000b3560000"
    "830800009c5500001a4c1b4960180078"
    "022811d197f0ecfd184aa01802681849"
    "5018007803210840002805d015495018"
    "0178f022114001700e4b0f4a99180020"
    "08700e481b1819680f4a89180878ef22"
    "1040087019680c480918087820221043"
    "08707ff083f814209bf0b4fa80209bf0"
    "21fb3ee040230003830800009c550000"
    "3f040000430400002e0400001a4b1b49"
    "581800681a4908401a4988421fd10820"
    "204000281bd0184a9918012008701748"
    "1b181968164a89180878102210430870"
    "19681348091808782022104308707ff0"
    "4df814209bf07efa32209bf0ebfa0d49"
    "05480d4a801800788000401800689ef0"
    "35f870bc01bc004740230003b8560000"
    "00ffff0000010200830800009c550000"
    "2e04000058400d08b956000000b50649"
)

GRID_W, GRID_H = 16, 16
TILE = 30
SCREEN_W, SCREEN_H = GRID_W * TILE, GRID_H * TILE
FPS = 60
GRAVITY = 1200
JUMP_VY = -450
MOVE_SPEED = 200
MAX_FALL_SPEED = 900
COLLIDABLE_R_MIN = 100
BLACK = (0, 0, 0)
PLAYER_CLR = (255, 255, 255)
DEFAULT_CLR = (40, 40, 40)

raw_bytes = bytes.fromhex(HEX_DATA)
palette = []
start = 12 * 16
for i in range(GRID_W * GRID_H):
    idx = start + i * 3
    if idx + 2 < len(raw_bytes):
        palette.append(tuple(raw_bytes[idx:idx+3]))
    else:
        palette.append(DEFAULT_CLR)

solids = [
    [palette[y*GRID_W + x][0] > COLLIDABLE_R_MIN for x in range(GRID_W)]
    for y in range(GRID_H)
]

pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Playable Platformer")
clock = pygame.time.Clock()

DISPLAY_TILE = TILE
TILE_SKY = pygame.Surface((DISPLAY_TILE, DISPLAY_TILE), pygame.SRCALPHA)
TILE_SKY.fill((108, 180, 255))
TILE_BRICK = pygame.Surface((DISPLAY_TILE, DISPLAY_TILE), pygame.SRCALPHA)
brick_base = (146, 98, 52)
mortar_line = (93, 59, 32)
TILE_BRICK.fill(brick_base)
pygame.draw.line(TILE_BRICK, mortar_line, (DISPLAY_TILE//2, 0), (DISPLAY_TILE//2, DISPLAY_TILE))
pygame.draw.line(TILE_BRICK, mortar_line, (0, DISPLAY_TILE//3), (DISPLAY_TILE, DISPLAY_TILE//3))
pygame.draw.line(TILE_BRICK, mortar_line, (0, 2*DISPLAY_TILE//3), (DISPLAY_TILE, 2*DISPLAY_TILE//3))

tile_surfs = [TILE_SKY, TILE_BRICK]

player = pygame.Rect(0, 0, 22, 22)
vel_x = vel_y = 0.0
on_ground = False
running = True

def tiles_touching(rect):
    left = max(0, rect.left // TILE)
    right = min(GRID_W-1, rect.right // TILE)
    top = max(0, rect.top // TILE)
    bottom = min(GRID_H-1, rect.bottom // TILE)
    for gy in range(top, bottom+1):
        for gx in range(left, right+1):
            if solids[gy][gx]:
                yield gx, gy

while running:
    dt = clock.tick(FPS) / 1000
    for e in pygame.event.get():
        if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
            running = False
    keys = pygame.key.get_pressed()
    vel_x = -MOVE_SPEED if keys[pygame.K_LEFT] else MOVE_SPEED if keys[pygame.K_RIGHT] else 0
    if keys[pygame.K_SPACE] and on_ground:
        vel_y = JUMP_VY
        on_ground = False

    player.x += vel_x * dt
    for gx, gy in tiles_touching(player):
        tile_rect = pygame.Rect(gx*TILE, gy*TILE, TILE, TILE)
        if player.colliderect(tile_rect):
            if vel_x > 0:
                player.right = tile_rect.left
            elif vel_x < 0:
                player.left = tile_rect.right

    vel_y = min(vel_y + GRAVITY*dt, MAX_FALL_SPEED)
    player.y += vel_y * dt
    on_ground = False
    for gx, gy in tiles_touching(player):
        tile_rect = pygame.Rect(gx*TILE, gy*TILE, TILE, TILE)
        if player.colliderect(tile_rect):
            if vel_y > 0:
                player.bottom = tile_rect.top
                on_ground = True
            elif vel_y < 0:
                player.top = tile_rect.bottom
            vel_y = 0

    player.clamp_ip(screen.get_rect())

    screen.fill(BLACK)
    for y in range(GRID_H):
        for x in range(GRID_W):
            idx = 1 if solids[y][x] else 0
            screen.blit(tile_surfs[idx], (x*TILE, y*TILE))
    pygame.draw.rect(screen, PLAYER_CLR, player)
    pygame.display.flip()

pygame.quit()
sys.exit()

import pygame
import random
from dataclasses import dataclass

# Initialize pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Super Mario Bros. 1 All-Stars Fangame")

# Colors
SKY_BLUE = (92, 148, 252)
GREEN = (0, 168, 0)
BROWN = (180, 122, 48)
RED = (228, 92, 48)
YELLOW = (248, 212, 0)
PURPLE = (184, 56, 176)
PLAYER_COLOR = (228, 92, 48)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BRICK = (200, 76, 12)
PIPE_GREEN = (0, 168, 68)
COIN_COLOR = (248, 212, 0)

# Game constants
GRAVITY = 0.45
JUMP_STRENGTH = -11
PLAYER_ACCEL = 0.5
PLAYER_MAX_SPEED = 6
PLAYER_FRICTION = 0.15

@dataclass
class Level:
    color: tuple
    end_x: int
    platforms: list
    coins: list
    enemies: list
    blocks: list
    pipes: list

    def draw(self, screen):
        # Draw background
        screen.fill(self.color)
        
        # Draw clouds
        for i in range(3):
            cloud_x = (i * 300 + 50) % SCREEN_WIDTH
            cloud_y = 100 + (i * 30) % 100
            pygame.draw.ellipse(screen, (240, 240, 240), (cloud_x, cloud_y, 80, 40))
            pygame.draw.ellipse(screen, (240, 240, 240), (cloud_x+20, cloud_y-20, 70, 40))
            pygame.draw.ellipse(screen, (240, 240, 240), (cloud_x+50, cloud_y, 70, 40))
        
        # Draw pipes
        for pipe in self.pipes:
            pygame.draw.rect(screen, PIPE_GREEN, pipe)
            pygame.draw.rect(screen, (0, 140, 58), pipe.inflate(-4, -4))
            # Draw pipe top
            pipe_top = pygame.Rect(pipe.x-5, pipe.y, pipe.width+10, 20)
            pygame.draw.rect(screen, PIPE_GREEN, pipe_top)
        
        # Draw platforms
        for platform in self.platforms:
            pygame.draw.rect(screen, BROWN, platform)
            pygame.draw.rect(screen, (150, 100, 40), platform.inflate(-4, -4))
        
        # Draw goal flag
        pygame.draw.rect(screen, (200, 200, 200), (self.end_x - 10, SCREEN_HEIGHT - 200, 5, 160))
        pygame.draw.rect(screen, RED, (self.end_x - 10, SCREEN_HEIGHT - 200, 30, 20))
        
        # Draw ground
        pygame.draw.rect(screen, GREEN, (0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40))
        for i in range(20):
            pygame.draw.line(screen, (0, 148, 0), (i*40, SCREEN_HEIGHT-40), (i*40+20, SCREEN_HEIGHT-50), 2)


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        # Draw Mario
        # Red hat
        pygame.draw.rect(self.image, RED, (0, 0, 32, 16))
        # Blue overalls
        pygame.draw.rect(self.image, (0, 0, 228), (4, 16, 24, 16))
        # Face
        pygame.draw.rect(self.image, (248, 188, 152), (4, 4, 24, 12))
        # Eyes
        pygame.draw.circle(self.image, BLACK, (12, 10), 2)
        pygame.draw.circle(self.image, BLACK, (20, 10), 2)
        # Mustache
        pygame.draw.rect(self.image, BLACK, (8, 12, 16, 4))
        
        self.original_image = self.image.copy()
        self.rect = self.image.get_rect(bottomleft=(50, SCREEN_HEIGHT - 40))
        self.vel_y = 0
        self.vel_x = 0
        self.on_ground = False
        self.facing_right = True
        self.score = 0
        self.lives = 3
        self.coins = 0
        self.invincible = 0

    def update(self, keys, platforms, blocks, pipes):
        # Horizontal movement with acceleration
        if keys[pygame.K_LEFT]:
            self.vel_x -= PLAYER_ACCEL
            if self.facing_right:
                self.facing_right = False
                self.image = pygame.transform.flip(self.original_image, True, False)
        if keys[pygame.K_RIGHT]:
            self.vel_x += PLAYER_ACCEL
            if not self.facing_right:
                self.facing_right = True
                self.image = self.original_image
        
        # Apply friction
        if not keys[pygame.K_LEFT] and not keys[pygame.K_RIGHT]:
            if self.vel_x > 0:
                self.vel_x -= PLAYER_FRICTION
                if self.vel_x < 0:
                    self.vel_x = 0
            elif self.vel_x < 0:
                self.vel_x += PLAYER_FRICTION
                if self.vel_x > 0:
                    self.vel_x = 0
        
        # Limit maximum speed
        if self.vel_x > PLAYER_MAX_SPEED:
            self.vel_x = PLAYER_MAX_SPEED
        elif self.vel_x < -PLAYER_MAX_SPEED:
            self.vel_x = -PLAYER_MAX_SPEED
            
        # Apply horizontal movement
        self.rect.x += int(self.vel_x)
        
        # Check for horizontal collisions with platforms and blocks
        all_obstacles = platforms + [b.rect for b in blocks] + pipes
        for obstacle in all_obstacles:
            if self.rect.colliderect(obstacle):
                if self.vel_x > 0:  # Moving right
                    self.rect.right = obstacle.left
                    self.vel_x = 0
                elif self.vel_x < 0:  # Moving left
                    self.rect.left = obstacle.right
                    self.vel_x = 0
        
        # Apply gravity
        self.vel_y += GRAVITY
        self.rect.y += int(self.vel_y)
        
        # Check for vertical collisions with platforms and blocks
        self.on_ground = False
        for obstacle in all_obstacles:
            if self.rect.colliderect(obstacle):
                if self.vel_y > 0:  # Moving down
                    self.rect.bottom = obstacle.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:  # Moving up
                    self.rect.top = obstacle.bottom
                    self.vel_y = 0
        
        # Jumping
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vel_y = JUMP_STRENGTH
            self.on_ground = False
            
        # Keep player within screen bounds
        if self.rect.left < 0:
            self.rect.left = 0
            self.vel_x = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
            self.vel_x = 0
        if self.rect.top < 0:
            self.rect.top = 0
            self.vel_y = 0
            
        # Apply screen bottom boundary (but allow falling off for death)
        if self.rect.top > SCREEN_HEIGHT:
            return True  # Indicate death by falling
        
        # Update invincibility timer
        if self.invincible > 0:
            self.invincible -= 1

        return False


class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(self.image, COIN_COLOR, (8, 8), 8)
        pygame.draw.circle(self.image, (248, 232, 80), (8, 8), 6)
        self.rect = self.image.get_rect(center=(x, y))
        self.original_y = self.rect.y
        self.float_offset = 0
        self.float_direction = 1

    def update(self):
        # Floating animation
        self.float_offset += 0.1 * self.float_direction
        if abs(self.float_offset) > 3:
            self.float_direction *= -1
        self.rect.y = self.original_y + int(self.float_offset)


class Goomba(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        # Draw Goomba body
        pygame.draw.ellipse(self.image, (120, 64, 0), (0, 8, 32, 24))
        # Draw Goomba head
        pygame.draw.ellipse(self.image, (150, 80, 0), (0, 0, 32, 24))
        # Eyes
        pygame.draw.circle(self.image, BLACK, (8, 12), 4)
        pygame.draw.circle(self.image, BLACK, (24, 12), 4)
        # Feet
        pygame.draw.ellipse(self.image, (0, 0, 0), (4, 24, 8, 8))
        pygame.draw.ellipse(self.image, (0, 0, 0), (20, 24, 8, 8))
        
        self.rect = self.image.get_rect(bottomleft=(x, y))
        self.direction = -1
        self.speed = 1
        self.is_squashed = False
        self.squash_timer = 0

    def update(self, platforms, blocks, pipes):
        if self.is_squashed:
            self.squash_timer += 1
            if self.squash_timer > 30:
                self.kill()
            return
            
        # Move horizontally
        self.rect.x += self.speed * self.direction
        
        # Check for collisions with platforms and blocks
        all_obstacles = platforms + [b.rect for b in blocks] + pipes
        for obstacle in all_obstacles:
            if self.rect.colliderect(obstacle):
                if self.direction > 0:
                    self.rect.right = obstacle.left
                    self.direction = -1
                else:
                    self.rect.left = obstacle.right
                    self.direction = 1
        
        # Apply gravity
        self.rect.y += 5
        
        # Check if on ground
        on_ground = False
        for obstacle in all_obstacles:
            if self.rect.colliderect(obstacle) and self.rect.bottom > obstacle.top + 5:
                self.rect.bottom = obstacle.top
                on_ground = True
                
        if not on_ground:
            self.rect.y -= 5


class Block(pygame.sprite.Sprite):
    def __init__(self, x, y, has_coin=False):
        super().__init__()
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        self.has_coin = has_coin
        self.update_image()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.hit = False
        self.hit_offset = 0

    def update_image(self):
        self.image.fill(0)
        pygame.draw.rect(self.image, BRICK, (0, 0, 32, 32))
        pygame.draw.rect(self.image, (160, 60, 0), (2, 2, 28, 28))
        
        if self.has_coin:
            # Draw question mark
            pygame.draw.rect(self.image, (248, 192, 0), (12, 8, 8, 16))
            pygame.draw.circle(self.image, (248, 192, 0), (16, 8), 4)
            pygame.draw.circle(self.image, (248, 192, 0), (16, 24), 4)

    def update(self):
        if self.hit:
            self.hit_offset += 1
            if self.hit_offset > 5:
                self.hit_offset = 5
            if self.hit_offset == 5:
                self.hit = False
                self.hit_offset = 0
                
        self.rect.y += self.hit_offset


def create_level(level_num):
    platforms = []
    coins = []
    enemies = []
    blocks = []
    pipes = []
    
    # Base ground platform
    platforms.append(pygame.Rect(0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40))
    
    if level_num == 0:
        # Level 1 - Basic Mario level
        color = SKY_BLUE
        platforms.extend([
            pygame.Rect(200, 450, 100, 20),
            pygame.Rect(400, 380, 100, 20),
            pygame.Rect(600, 300, 100, 20),
        ])
        
        blocks.extend([
            Block(250, 350, True),
            Block(280, 350),
            Block(310, 350, True),
            Block(450, 280, True),
            Block(480, 280),
            Block(510, 280, True),
            Block(650, 200, True),
        ])
        
        pipes.append(pygame.Rect(550, SCREEN_HEIGHT - 120, 60, 80))
        
        coins = [Coin(250, 320), Coin(310, 320), Coin(450, 250), Coin(510, 250), Coin(650, 170)]
        enemies = [Goomba(300, SCREEN_HEIGHT - 40), Goomba(500, SCREEN_HEIGHT - 40)]
        
    elif level_num == 1:
        # Level 2 - More challenging
        color = SKY_BLUE
        platforms.extend([
            pygame.Rect(150, 500, 80, 20),
            pygame.Rect(300, 450, 80, 20),
            pygame.Rect(450, 400, 80, 20),
            pygame.Rect(600, 350, 80, 20),
        ])
        
        blocks.extend([
            Block(180, 400, True),
            Block(210, 400),
            Block(240, 400, True),
            Block(330, 350, True),
            Block(360, 350),
            Block(390, 350, True),
            Block(480, 300, True),
            Block(510, 300),
            Block(540, 300, True),
            Block(630, 250, True),
        ])
        
        pipes.append(pygame.Rect(700, SCREEN_HEIGHT - 120, 60, 80))
        pipes.append(pygame.Rect(200, SCREEN_HEIGHT - 120, 60, 80))
        
        coins = [Coin(180, 370), Coin(240, 370), Coin(330, 320), Coin(390, 320), 
                 Coin(480, 270), Coin(540, 270), Coin(630, 220)]
        enemies = [Goomba(250, SCREEN_HEIGHT - 40), Goomba(400, SCREEN_HEIGHT - 40), Goomba(650, SCREEN_HEIGHT - 40)]
        
    elif level_num == 2:
        # Level 3 - Even more challenging
        color = SKY_BLUE
        platforms.extend([
            pygame.Rect(100, 500, 70, 20),
            pygame.Rect(250, 450, 70, 20),
            pygame.Rect(400, 400, 70, 20),
            pygame.Rect(550, 350, 70, 20),
            pygame.Rect(650, 300, 70, 20),
        ])
        
        blocks.extend([
            Block(130, 400, True),
            Block(160, 400),
            Block(190, 400, True),
            Block(280, 350, True),
            Block(310, 350),
            Block(340, 350, True),
            Block(430, 300, True),
            Block(460, 300),
            Block(490, 300, True),
            Block(580, 250, True),
            Block(610, 250),
            Block(640, 250, True),
            Block(680, 200, True),
        ])
        
        pipes.append(pygame.Rect(350, SCREEN_HEIGHT - 120, 60, 80))
        pipes.append(pygame.Rect(550, SCREEN_HEIGHT - 120, 60, 80))
        
        coins = [Coin(130, 370), Coin(190, 370), Coin(280, 320), Coin(340, 320),
                 Coin(430, 270), Coin(490, 270), Coin(580, 220), Coin(640, 220),
                 Coin(680, 170)]
        enemies = [Goomba(200, SCREEN_HEIGHT - 40), Goomba(370, SCREEN_HEIGHT - 40), 
                   Goomba(520, SCREEN_HEIGHT - 40), Goomba(600, SCREEN_HEIGHT - 40)]
        
    else:
        # Default level if more than defined levels
        color = SKY_BLUE
        platforms.extend([
            pygame.Rect(200, 450, 100, 20),
            pygame.Rect(400, 380, 100, 20),
        ])
        coins = [Coin(250, 420), Coin(450, 350)]
        enemies = [Goomba(300, SCREEN_HEIGHT - 40)]
    
    return Level(color, SCREEN_WIDTH - 100, platforms, coins, enemies, blocks, pipes)


def draw_text(surface, text, size, x, y, color=WHITE):
    font = pygame.font.SysFont("Arial", size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(x, y))
    surface.blit(text_surface, text_rect)


def main():
    clock = pygame.time.Clock()
    running = True
    game_over = False
    level_complete = False
    
    # Create player and levels
    player = Player()
    levels = [create_level(i) for i in range(3)]
    current_level = 0
    level = levels[current_level]
    
    # Create sprite groups
    all_sprites = pygame.sprite.Group()
    coin_sprites = pygame.sprite.Group()
    enemy_sprites = pygame.sprite.Group()
    block_sprites = pygame.sprite.Group()
    
    # Add initial coins, enemies, and blocks
    for coin in level.coins:
        coin_sprites.add(coin)
        all_sprites.add(coin)
    
    for enemy in level.enemies:
        enemy_sprites.add(enemy)
        all_sprites.add(enemy)
        
    for block in level.blocks:
        block_sprites.add(block)
        all_sprites.add(block)
    
    all_sprites.add(player)
    
    # Game loop
    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and (game_over or level_complete):
                    # Reset game
                    player = Player()
                    levels = [create_level(i) for i in range(3)]
                    current_level = 0
                    level = levels[current_level]
                    game_over = False
                    level_complete = False
                    
                    # Reset sprites
                    all_sprites = pygame.sprite.Group()
                    coin_sprites = pygame.sprite.Group()
                    enemy_sprites = pygame.sprite.Group()
                    block_sprites = pygame.sprite.Group()
                    
                    # Add coins, enemies, and blocks for the level
                    for coin in level.coins:
                        coin_sprites.add(coin)
                        all_sprites.add(coin)
                    
                    for enemy in level.enemies:
                        enemy_sprites.add(enemy)
                        all_sprites.add(enemy)
                        
                    for block in level.blocks:
                        block_sprites.add(block)
                        all_sprites.add(block)
                    
                    all_sprites.add(player)
                
                if event.key == pygame.K_RETURN and level_complete:
                    # Move to next level
                    current_level += 1
                    if current_level >= len(levels):
                        current_level = 0  # Loop back to first level
                    
                    level = levels[current_level]
                    player.rect.x = 50
                    player.rect.bottom = SCREEN_HEIGHT - 40
                    player.vel_y = 0
                    level_complete = False
                    
                    # Reset sprites
                    all_sprites = pygame.sprite.Group()
                    coin_sprites = pygame.sprite.Group()
                    enemy_sprites = pygame.sprite.Group()
                    block_sprites = pygame.sprite.Group()
                    
                    # Add coins, enemies, and blocks for the new level
                    for coin in level.coins:
                        coin_sprites.add(coin)
                        all_sprites.add(coin)
                    
                    for enemy in level.enemies:
                        enemy_sprites.add(enemy)
                        all_sprites.add(enemy)
                        
                    for block in level.blocks:
                        block_sprites.add(block)
                        all_sprites.add(block)
                    
                    all_sprites.add(player)
        
        if not game_over and not level_complete:
            # Get keyboard input
            keys = pygame.key.get_pressed()
            
            # Update player
            died = player.update(keys, level.platforms, level.blocks, level.pipes)
            if died:
                player.lives -= 1
                player.invincible = 60
                player.rect.x = 50
                player.rect.bottom = SCREEN_HEIGHT - 40
                player.vel_y = 0
                if player.lives <= 0:
                    game_over = True
            
            # Update coins, enemies, and blocks
            coin_sprites.update()
            for enemy in enemy_sprites:
                enemy.update(level.platforms, level.blocks, level.pipes)
            block_sprites.update()
            
            # Check for coin collisions
            coins_collected = pygame.sprite.spritecollide(player, coin_sprites, True)
            player.score += len(coins_collected) * 100
            player.coins += len(coins_collected)
            
            # Check for block collisions from below
            blocks_hit = pygame.sprite.spritecollide(player, block_sprites, False)
            for block in blocks_hit:
                if player.vel_y < 0 and not block.hit:  # Player is moving upward
                    block.hit = True
                    block.hit_offset = -5
                    if block.has_coin:
                        # Create a new coin above the block
                        new_coin = Coin(block.rect.centerx, block.rect.top - 20)
                        coin_sprites.add(new_coin)
                        all_sprites.add(new_coin)
                        player.score += 100
                        player.coins += 1
                        block.has_coin = False
                        block.update_image()
            
            # Check for enemy collisions
            enemies_hit = pygame.sprite.spritecollide(player, enemy_sprites, False)
            for enemy in enemies_hit:
                if player.vel_y > 0 and player.rect.bottom < enemy.rect.centery and not enemy.is_squashed:
                    # Player is falling onto enemy
                    enemy.is_squashed = True
                    enemy.image = pygame.Surface((32, 16), pygame.SRCALPHA)
                    pygame.draw.ellipse(enemy.image, (120, 64, 0), (0, 0, 32, 16))
                    enemy.rect.height = 16
                    enemy.rect.y += 16  # Keep bottom the same
                    player.vel_y = JUMP_STRENGTH / 2  # Bounce off enemy
                    player.score += 200
                elif player.invincible == 0:
                    player.lives -= 1
                    player.invincible = 60  # Invincibility frames
                    player.rect.x = 50
                    player.rect.bottom = SCREEN_HEIGHT - 40
                    player.vel_y = 0
                    
                    if player.lives <= 0:
                        game_over = True
            
            # Check if player reached the end of the level
            if player.rect.x > level.end_x:
                level_complete = True
                player.score += 1000  # Bonus for completing level
        
        # Draw everything
        level.draw(screen)
        
        # Draw all sprites
        for entity in all_sprites:
            screen.blit(entity.image, entity.rect)
        
        # Draw UI
        draw_text(screen, f"MARIO", 24, 70, 20)
        draw_text(screen, f"{player.score:06d}", 24, 70, 45)
        draw_text(screen, f"COIN x{player.coins:02d}", 24, 200, 20)
        draw_text(screen, f"WORLD", 24, 400, 20)
        draw_text(screen, f"{current_level + 1}-1", 24, 400, 45)
        draw_text(screen, f"LIVES", 24, 600, 20)
        draw_text(screen, f"x {player.lives}", 24, 600, 45)
        
        # Draw game over or level complete message
        if game_over:
            draw_text(screen, "GAME OVER", 64, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50, RED)
            draw_text(screen, "Press R to restart", 36, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20)
        elif level_complete:
            draw_text(screen, "LEVEL COMPLETE!", 64, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50, YELLOW)
            draw_text(screen, "Press ENTER for next level", 36, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20)
        
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()

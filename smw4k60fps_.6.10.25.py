import pygame
import math
import random

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400
FPS = 60
GRAVITY = 0.8
JUMP_STRENGTH = -15
MOVE_SPEED = 5
ENEMY_SPEED = 2

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 100, 255)
YELLOW = (255, 255, 0)
BROWN = (139, 69, 19)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
PINK = (255, 192, 203)

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 32  # Slightly larger
        self.height = 44  # Slightly taller
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.facing_right = True
        self.lives = 3
        self.coins = 0
        self.invulnerable = 0
        self.animation_frame = 0
        
    def update(self, platforms, enemies, coins):
        # Handle input
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.vel_x = -MOVE_SPEED
            self.facing_right = False
        elif keys[pygame.K_RIGHT]:
            self.vel_x = MOVE_SPEED
            self.facing_right = True
        else:
            self.vel_x *= 0.8
            
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vel_y = JUMP_STRENGTH
            
        # Apply gravity
        self.vel_y += GRAVITY
        if self.vel_y > 20:
            self.vel_y = 20
            
        # Move horizontally
        self.x += self.vel_x
        self.check_collisions_x(platforms)
        
        # Move vertically
        self.y += self.vel_y
        self.on_ground = False
        self.check_collisions_y(platforms)
        
        # Check enemy collisions
        if self.invulnerable <= 0:
            for enemy in enemies:
                if self.get_rect().colliderect(enemy.get_rect()):
                    if self.vel_y > 0 and self.y < enemy.y:
                        # Stomp enemy
                        enemies.remove(enemy)
                        self.vel_y = JUMP_STRENGTH / 2
                    else:
                        # Take damage
                        self.lives -= 1
                        self.invulnerable = 120
                        self.vel_x = -10 if self.facing_right else 10
                        self.vel_y = -10
                        
        # Check coin collection
        for coin in coins[:]:
            if self.get_rect().colliderect(coin.get_rect()):
                coins.remove(coin)
                self.coins += 1
                
        # Update invulnerability
        if self.invulnerable > 0:
            self.invulnerable -= 1
            
        # Update animation
        self.animation_frame = (self.animation_frame + 1) % 20
        
    def check_collisions_x(self, platforms):
        rect = self.get_rect()
        for platform in platforms:
            if rect.colliderect(platform.get_rect()):
                if self.vel_x > 0:
                    self.x = platform.x - self.width
                elif self.vel_x < 0:
                    self.x = platform.x + platform.width
                self.vel_x = 0
                
    def check_collisions_y(self, platforms):
        rect = self.get_rect()
        for platform in platforms:
            if rect.colliderect(platform.get_rect()):
                if self.vel_y > 0:
                    self.y = platform.y - self.height
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.y = platform.y + platform.height
                    self.vel_y = 0
                    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
        
    def draw(self, screen, camera_x):
        x = self.x - camera_x
        
        # Flash when invulnerable
        if self.invulnerable % 10 < 5:
            return
            
        # Draw a glowing outline when Mario is the active player
        if self.coins >= 5:  # Special effect after collecting 5 coins
            pygame.draw.rect(screen, YELLOW, (x-2, self.y-2, self.width+4, self.height+4), 2)
            
        # Body (overalls)
        pygame.draw.rect(screen, BLUE, (x, self.y + 12, self.width, self.height - 12))
        
        # Shirt
        pygame.draw.rect(screen, RED, (x, self.y + 8, self.width, 16))
        
        # Hat
        pygame.draw.rect(screen, RED, (x - 2, self.y - 5, self.width + 4, 13))
        
        # Face
        pygame.draw.rect(screen, PINK, (x + 6, self.y + 5, 20, 15))
        
        # Eyes
        eye_offset = 6 if self.facing_right else 16
        pygame.draw.circle(screen, WHITE, (x + eye_offset, self.y + 10), 3)
        pygame.draw.circle(screen, WHITE, (x + eye_offset + 10, self.y + 10), 3)
        pygame.draw.circle(screen, BLACK, (x + eye_offset, self.y + 10), 2)
        pygame.draw.circle(screen, BLACK, (x + eye_offset + 10, self.y + 10), 2)
        
        # Mustache
        pygame.draw.rect(screen, BLACK, (x + 6, self.y + 15, 20, 3))
        
        # Arms
        arm_x = x + 26 if self.facing_right else x - 5
        pygame.draw.rect(screen, PINK, (arm_x, self.y + 20, 10, 5))
        
        # Legs with walking animation
        leg_offset = 6 if self.animation_frame < 10 else 16
        pygame.draw.rect(screen, BLUE, (x + 6, self.y + 32, 8, 12))
        pygame.draw.rect(screen, BLUE, (x + leg_offset, self.y + 32, 8, 12))
        
        # Shoes
        pygame.draw.rect(screen, BROWN, (x + 5, self.y + 40, 10, 4))
        pygame.draw.rect(screen, BROWN, (x + leg_offset - 1, self.y + 40, 10, 4))

class Platform:
    def __init__(self, x, y, width, height, color=BROWN):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
        
    def draw(self, screen, camera_x):
        x = self.x - camera_x
        pygame.draw.rect(screen, self.color, (x, self.y, self.width, self.height))
        # Add some texture
        for i in range(0, self.width, 20):
            pygame.draw.line(screen, BLACK, (x + i, self.y), (x + i, self.y + self.height), 1)

class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 25
        self.height = 25
        self.vel_x = ENEMY_SPEED
        self.animation_frame = 0
        
    def update(self, platforms):
        # Move horizontally
        self.x += self.vel_x
        
        # Check if at edge of platform
        on_platform = False
        for platform in platforms:
            if (self.x + self.width > platform.x and self.x < platform.x + platform.width and
                self.y + self.height <= platform.y + 10 and self.y + self.height >= platform.y):
                on_platform = True
                # Check if at edge
                if self.x <= platform.x or self.x + self.width >= platform.x + platform.width:
                    self.vel_x *= -1
                    
        if not on_platform:
            self.vel_x *= -1
            
        self.animation_frame = (self.animation_frame + 1) % 40
        
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
        
    def draw(self, screen, camera_x):
        x = self.x - camera_x
        
        # Body
        pygame.draw.ellipse(screen, BROWN, (x, self.y + 5, self.width, 20))
        
        # Head
        pygame.draw.circle(screen, BROWN, (x + self.width // 2, self.y + 10), 8)
        
        # Eyes
        pygame.draw.circle(screen, WHITE, (x + 8, self.y + 8), 3)
        pygame.draw.circle(screen, WHITE, (x + 17, self.y + 8), 3)
        pygame.draw.circle(screen, BLACK, (x + 8, self.y + 8), 1)
        pygame.draw.circle(screen, BLACK, (x + 17, self.y + 8), 1)
        
        # Feet
        foot_offset = 3 if self.animation_frame < 20 else -3
        pygame.draw.ellipse(screen, BLACK, (x + 3 + foot_offset, self.y + 20, 8, 5))
        pygame.draw.ellipse(screen, BLACK, (x + 14 - foot_offset, self.y + 20, 8, 5))

class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 10
        self.animation_frame = 0
        
    def update(self):
        self.animation_frame = (self.animation_frame + 1) % 60
        
    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, 
                          self.radius * 2, self.radius * 2)
        
    def draw(self, screen, camera_x):
        x = self.x - camera_x
        
        # Animate coin rotation
        width = abs(math.sin(self.animation_frame * 0.1)) * self.radius * 2
        if width > 2:
            pygame.draw.ellipse(screen, YELLOW, 
                              (x - width // 2, self.y - self.radius, width, self.radius * 2))
            pygame.draw.ellipse(screen, ORANGE, 
                              (x - width // 2 + 2, self.y - self.radius + 2, width - 4, self.radius * 2 - 4))

class Cloud:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        
    def draw(self, screen, camera_x):
        x = self.x - camera_x * 0.5  # Parallax effect
        
        # Draw cloud with circles
        pygame.draw.circle(screen, WHITE, (x, self.y), 20)
        pygame.draw.circle(screen, WHITE, (x + 15, self.y), 25)
        pygame.draw.circle(screen, WHITE, (x + 35, self.y), 20)
        pygame.draw.circle(screen, WHITE, (x + 10, self.y - 10), 15)
        pygame.draw.circle(screen, WHITE, (x + 25, self.y - 10), 15)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Super Mario World - 60fps")
        self.clock = pygame.time.Clock()
        self.running = True
        self.camera_x = 0
        self.level_width = 3000
        
        # Initialize game objects
        self.player = Player(20, SCREEN_HEIGHT // 2 - 20)  # Spawn at left edge, centered vertically
        self.platforms = self.create_level()
        self.enemies = self.create_enemies()
        self.coins = self.create_coins()
        self.clouds = self.create_clouds()
        
    def create_level(self):
        platforms = []
        
        # Ground
        for i in range(0, self.level_width, 100):
            platforms.append(Platform(i, 350, 100, 50))
            
        # Floating platforms
        platforms.append(Platform(300, 280, 100, 20))
        platforms.append(Platform(500, 220, 150, 20))
        platforms.append(Platform(700, 260, 80, 20))
        platforms.append(Platform(900, 200, 120, 20))
        platforms.append(Platform(1100, 280, 100, 20))
        platforms.append(Platform(1300, 150, 200, 20))
        platforms.append(Platform(1600, 250, 100, 20))
        platforms.append(Platform(1800, 200, 150, 20))
        platforms.append(Platform(2000, 280, 100, 20))
        platforms.append(Platform(2200, 180, 120, 20))
        platforms.append(Platform(2400, 250, 100, 20))
        
        # Pipes
        platforms.append(Platform(400, 300, 40, 50, GREEN))
        platforms.append(Platform(800, 300, 40, 50, GREEN))
        platforms.append(Platform(1200, 300, 40, 50, GREEN))
        platforms.append(Platform(1700, 280, 40, 70, GREEN))
        platforms.append(Platform(2100, 300, 40, 50, GREEN))
        
        return platforms
        
    def create_enemies(self):
        enemies = []
        enemy_positions = [(350, 325), (600, 195), (950, 175), (1150, 255), 
                          (1400, 125), (1850, 175), (2050, 255), (2250, 155)]
        
        for x, y in enemy_positions:
            enemies.append(Enemy(x, y))
            
        return enemies
        
    def create_coins(self):
        coins = []
        coin_positions = [(250, 250), (350, 200), (450, 250), (550, 150),
                         (650, 200), (750, 230), (850, 180), (1000, 150),
                         (1150, 230), (1250, 100), (1350, 120), (1450, 100),
                         (1550, 200), (1650, 220), (1750, 150), (1900, 150),
                         (2000, 230), (2150, 130), (2300, 200), (2450, 220)]
        
        for x, y in coin_positions:
            coins.append(Coin(x, y))
            
        return coins
        
    def create_clouds(self):
        clouds = []
        for i in range(0, self.level_width, 300):
            clouds.append(Cloud(i + random.randint(0, 200), random.randint(30, 100)))
        return clouds
        
    def update(self):
        # Update player
        self.player.update(self.platforms, self.enemies, self.coins)
        
        # Update enemies
        for enemy in self.enemies:
            enemy.update(self.platforms)
            
        # Update coins
        for coin in self.coins:
            coin.update()
            
        # Update camera
        target_camera = self.player.x - SCREEN_WIDTH // 2
        self.camera_x += (target_camera - self.camera_x) * 0.1
        self.camera_x = max(0, min(self.camera_x, self.level_width - SCREEN_WIDTH))
        
        # Check if player fell off
        if self.player.y > SCREEN_HEIGHT:
            self.player.lives -= 1
            self.player.x = 20  # Respawn at left edge
            self.player.y = SCREEN_HEIGHT // 2 - 20  # Centered vertically
            self.player.vel_x = 0
            self.player.vel_y = 0
            self.camera_x = 0
            
        # Check game over
        if self.player.lives <= 0:
            self.running = False
            
    def draw(self):
        # Sky gradient
        for i in range(SCREEN_HEIGHT):
            color_value = int(135 + (120 * i / SCREEN_HEIGHT))
            pygame.draw.line(self.screen, (color_value, color_value, 255), 
                           (0, i), (SCREEN_WIDTH, i))
        
        # Draw clouds
        for cloud in self.clouds:
            cloud.draw(self.screen, self.camera_x)
        
        # Draw platforms
        for platform in self.platforms:
            if -100 < platform.x - self.camera_x < SCREEN_WIDTH + 100:
                platform.draw(self.screen, self.camera_x)
        
        # Draw coins
        for coin in self.coins:
            if -50 < coin.x - self.camera_x < SCREEN_WIDTH + 50:
                coin.draw(self.screen, self.camera_x)
        
        # Draw enemies
        for enemy in self.enemies:
            if -50 < enemy.x - self.camera_x < SCREEN_WIDTH + 50:
                enemy.draw(self.screen, self.camera_x)
        
        # Draw player
        self.player.draw(self.screen, self.camera_x)
        
        # Draw HUD
        self.draw_hud()
        
    def draw_hud(self):
        # Background for HUD
        pygame.draw.rect(self.screen, BLACK, (0, 0, SCREEN_WIDTH, 40))
        pygame.draw.rect(self.screen, WHITE, (0, 40, SCREEN_WIDTH, 2))
        
        # Lives
        font = pygame.font.Font(None, 24)
        lives_text = font.render(f"LIVES: {self.player.lives}", True, WHITE)
        self.screen.blit(lives_text, (10, 10))
        
        # Coins
        coins_text = font.render(f"COINS: {self.player.coins}", True, YELLOW)
        self.screen.blit(coins_text, (150, 10))
        
        # FPS
        fps = int(self.clock.get_fps())
        fps_text = font.render(f"FPS: {fps}", True, GREEN)
        self.screen.blit(fps_text, (300, 10))
        
        # Instructions
        inst_text = font.render("Arrow Keys: Move, Space: Jump", True, WHITE)
        self.screen.blit(inst_text, (380, 10))
        
    def run(self):
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
            
            # Update
            self.update()
            
            # Draw
            self.draw()
            
            # Update display
            pygame.display.flip()
            self.clock.tick(FPS)
        
        # Game over screen
        if self.player.lives <= 0:
            font = pygame.font.Font(None, 48)
            game_over_text = font.render("GAME OVER", True, RED)
            score_text = font.render(f"Coins: {self.player.coins}", True, WHITE)
            
            self.screen.fill(BLACK)
            self.screen.blit(game_over_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(score_text, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2))
            pygame.display.flip()
            
            # Wait for key press
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                        waiting = False
        
        pygame.quit()

# Run the game
if __name__ == "__main__":
    game = Game()
    game.run()

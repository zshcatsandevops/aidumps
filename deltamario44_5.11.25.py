import asyncio
import pygame
import random
from pygame import Vector2

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
GRAVITY = 1500
JUMP_FORCE = -650
PLAYER_SPEED = 300
SKY_BLUE = (135, 206, 235)

class GameState:
    RUNNING, PAUSED, GAME_OVER = range(3)

class PlayerState:
    SMALL, BIG, FIRE = range(3)

class Entity:
    def __init__(self, pos, size):
        self.pos = Vector2(pos)
        self.vel = Vector2(0, 0)
        self.size = Vector2(size)
        self.color = (255, 0, 0)
        self.on_ground = False

    def get_rect(self):
        return pygame.Rect(self.pos, self.size)

class Player(Entity):
    def __init__(self, pos):
        super().__init__(pos, (32, 32))
        self.state = PlayerState.SMALL
        self.invincible = False
        self.can_shoot = False
        self.lives = 3
        self.score = 0
        self.coins = 0

    def jump(self):
        if self.on_ground:
            self.vel.y = JUMP_FORCE
            self.on_ground = False

    def update(self, dt, platforms, enemies):
        # Horizontal movement
        self.pos.x += self.vel.x * dt
        
        # Vertical movement
        self.vel.y += GRAVITY * dt
        self.pos.y += self.vel.y * dt
        self.on_ground = False

        # Collisions
        self.resolve_collisions(platforms, enemies)

    def resolve_collisions(self, platforms, enemies):
        player_rect = self.get_rect()
        
        # Platform collisions
        for plat in platforms:
            if player_rect.colliderect(plat.get_rect()):
                if self.vel.y > 0:
                    self.pos.y = plat.pos.y - self.size.y
                    self.vel.y = 0
                    self.on_ground = True
                elif self.vel.y < 0:
                    self.pos.y = plat.pos.y + plat.size.y
                    self.vel.y = 0

        # Enemy collisions
        for enemy in enemies:
            if player_rect.colliderect(enemy.get_rect()):
                if self.vel.y > 0:
                    enemy.stomp()
                    self.vel.y = JUMP_FORCE * 0.8
                else:
                    self.take_damage()

    def take_damage(self):
        if not self.invincible:
            self.lives -= 1
            self.invincible = True
            pygame.time.set_timer(pygame.USEREVENT, 2000)  # 2s invincibility

class Block(Entity):
    def __init__(self, pos, content=None):
        super().__init__(pos, (32, 32))
        self.content = content
        self.bumped = False
        self.color = (139, 69, 19) if content else (75, 35, 11)

    def bump(self):
        if not self.bumped and self.content:
            self.bumped = True
            return self.content
        return None

class Goomba(Entity):
    def __init__(self, pos):
        super().__init__(pos, (32, 24))
        self.color = (165, 42, 42)
        self.direction = 1
        self.speed = 100

    def update(self, dt, platforms):
        self.pos.x += self.direction * self.speed * dt
        
        # Simple platform edge detection
        front_pos = self.pos.x + (self.size.x * self.direction)
        if not any(p.get_rect().collidepoint(front_pos, self.pos.y + 1) for p in platforms):
            self.direction *= -1

        # Gravity
        self.vel.y += GRAVITY * dt
        self.pos.y += self.vel.y * dt

        # Platform landing
        for plat in platforms:
            if self.get_rect().colliderect(plat.get_rect()):
                if self.vel.y > 0:
                    self.pos.y = plat.pos.y - self.size.y
                    self.vel.y = 0

    def stomp(self):
        # Add squash animation here
        pass

class PowerUp(Entity):
    def __init__(self, pos, power_type):
        super().__init__(pos, (32, 32))
        self.type = power_type
        self.color = (0, 255, 0) if power_type == "mushroom" else (255, 0, 0)

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.state = GameState.RUNNING
        
        # Game World
        self.platforms = [
            Block((i * 32, SCREEN_HEIGHT - 32)) for i in range(25)
        ]
        self.enemies = [Goomba((500, 400))]
        self.powerups = []
        
        # Add platforms
        for x in range(600, 800, 64):
            self.platforms.append(Block((x, SCREEN_HEIGHT - 200)))
        
        self.player = Player((100, SCREEN_HEIGHT - 64))
        self.camera_x = 0

    def handle_input(self, dt):
        keys = pygame.key.get_pressed()
        self.player.vel.x = 0
        
        if keys[pygame.K_LEFT]:
            self.player.vel.x = -PLAYER_SPEED
        if keys[pygame.K_RIGHT]:
            self.player.vel.x = PLAYER_SPEED
        if keys[pygame.K_SPACE]:
            self.player.jump()

    def update(self, dt):
        if self.state != GameState.RUNNING:
            return
            
        self.player.update(dt, self.platforms, self.enemies)
        for enemy in self.enemies:
            enemy.update(dt, self.platforms)
        
        # Camera follow
        self.camera_x = max(0, self.player.pos.x - SCREEN_WIDTH//2)

    def draw(self):
        self.screen.fill(SKY_BLUE)
        
        # Draw platforms
        for plat in self.platforms:
            rect = plat.get_rect().move(-self.camera_x, 0)
            pygame.draw.rect(self.screen, plat.color, rect)
        
        # Draw enemies
        for enemy in self.enemies:
            rect = enemy.get_rect().move(-self.camera_x, 0)
            pygame.draw.ellipse(self.screen, enemy.color, rect)
        
        # Draw player
        player_rect = self.player.get_rect().move(-self.camera_x, 0)
        pygame.draw.rect(self.screen, self.player.color, player_rect)
        
        # HUD
        self.draw_hud()
        pygame.display.flip()

    def draw_hud(self):
        font = pygame.font.Font(None, 36)
        text = font.render(f"Lives: {self.player.lives}  Coins: {self.player.coins}  Score: {self.player.score}", 
                          True, (255, 255, 255))
        self.screen.blit(text, (10, 10))

    async def run(self):
        while True:
            dt = self.clock.tick(60)/1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

            if self.state == GameState.RUNNING:
                self.handle_input(dt)
                self.update(dt)
                self.draw()
            
            await asyncio.sleep(0)

if __name__ == "__main__":
    game = Game()
    asyncio.run(game.run())

import pygame
import math
import numpy as np

pygame.init()
WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Super Mario World Final Boss Recreation")
clock = pygame.time.Clock()

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)  # Player (Mario)
GREEN = (0, 255, 0)  # Bowser
BLUE = (0, 0, 255)  # Mechakoopa
YELLOW = (255, 255, 0)  # Big Steelie (Ball)

# Sound generation
SAMPLE_RATE = 44100

def generate_beep(freq, duration, volume=0.5):
    samples = np.sin(2 * np.pi * np.arange(SAMPLE_RATE * duration) * freq / SAMPLE_RATE).astype(np.float32)
    samples *= volume * 32767
    stereo_samples = np.column_stack((samples, samples)).astype(np.int16)
    return pygame.mixer.Sound(buffer=stereo_samples.tobytes())

# Sounds
jump_sound = generate_beep(523.25, 0.1)  # C5 note for jump
stun_sound = generate_beep(392.00, 0.15)  # G4 for stun
throw_sound = generate_beep(659.25, 0.1)  # E5 for throw
hit_sound = generate_beep(261.63, 0.2, volume=0.8)  # C4 low for hit Bowser
ball_drop_sound = generate_beep(329.63, 0.12)  # E4 for ball drop
win_sound = generate_beep(784.00, 0.3)  # G5 for win
lose_sound = generate_beep(130.81, 0.3, volume=0.7)  # C3 low for lose

# Sprite groups
all_sprites = pygame.sprite.Group()
mechakoopas = pygame.sprite.Group()
balls = pygame.sprite.Group()

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((20, 30))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = 50
        self.rect.bottom = HEIGHT - 50
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = True
        self.carrying = None
        all_sprites.add(self)

    def update(self):
        self.vel_y += 0.5  # Gravity
        self.rect.y += self.vel_y
        if self.rect.bottom >= HEIGHT - 50:
            self.rect.bottom = HEIGHT - 50
            self.vel_y = 0
            self.on_ground = True
        self.rect.x += self.vel_x
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        if self.carrying:
            self.carrying.rect.midtop = self.rect.midtop
            self.carrying.stunned = True  # Keep stunned while carrying

class Bowser(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((50, 50))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH // 2
        self.rect.y = 50
        self.time = 0
        self.health = 3
        self.direction = 1
        all_sprites.add(self)

    def update(self):
        self.time += 1
        self.rect.x += self.direction * 1
        self.rect.y = 50 + math.sin(self.time * 0.05) * 20
        if self.rect.left < 50 or self.rect.right > WIDTH - 50:
            self.direction *= -1
        if self.time % 180 == 0:  # Throw Mechakoopa every 3 seconds
            mecha = Mechakoopa(self.rect.centerx, self.rect.bottom)
            all_sprites.add(mecha)
            mechakoopas.add(mecha)
            throw_sound.play()
        if self.time % 360 == 0:  # Drop ball every 6 seconds
            ball = Ball(self.rect.centerx, self.rect.bottom)
            all_sprites.add(ball)
            balls.add(ball)
            ball_drop_sound.play()

class Mechakoopa(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.y = y
        self.vel_x = -2
        self.stunned = False
        self.throw_vel_y = 0

    def update(self):
        if self.throw_vel_y != 0:  # If thrown
            self.rect.y += self.throw_vel_y
            self.throw_vel_y += 0.5
            if self.rect.bottom >= HEIGHT - 50:
                self.kill()
            return
        if not self.stunned:
            self.rect.x += self.vel_x
            if self.rect.left < 0 or self.rect.right > WIDTH:
                self.vel_x *= -1
            self.rect.bottom = HEIGHT - 50
        # Else, stunned on ground or carried

class Ball(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.y = y
        self.vel_y = 0

    def update(self):
        self.vel_y += 0.5
        self.rect.y += self.vel_y
        if self.rect.top > HEIGHT:
            self.kill()

player = Player()
bowser = Bowser()

running = True
while running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and player.on_ground:
                player.vel_y = -12
                player.on_ground = False
                jump_sound.play()
            elif event.key == pygame.K_DOWN and player.carrying is None:
                collided = pygame.sprite.spritecollide(player, mechakoopas, False)
                for m in collided:
                    if m.stunned and m.throw_vel_y == 0:
                        player.carrying = m
                        break
            elif event.key == pygame.K_UP and player.carrying:
                m = player.carrying
                player.carrying = None
                m.throw_vel_y = -15
                m.rect.midbottom = player.rect.midtop
                throw_sound.play()

    keys = pygame.key.get_pressed()
    player.vel_x = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * 5

    all_sprites.update()

    # Collision: Jump on Mechakoopa to stun
    collisions = pygame.sprite.spritecollide(player, mechakoopas, False)
    for m in collisions:
        if not m.stunned and player.vel_y > 0 and player.rect.bottom <= m.rect.top + 10:
            m.stunned = True
            m.vel_x = 0
            player.vel_y = -8  # Bounce
            stun_sound.play()

    # Thrown Mechakoopa hits Bowser
    for m in mechakoopas:
        if m.throw_vel_y < 0 and pygame.sprite.collide_rect(m, bowser):
            bowser.health -= 1
            m.kill()
            hit_sound.play()
            if bowser.health <= 0:
                win_sound.play()
                print("You defeated Bowser!")
                running = False

    # Ball hits player (simple damage, game over for demo)
    if pygame.sprite.spritecollide(player, balls, True):
        lose_sound.play()
        print("Hit by ball! Game Over.")
        running = False

    # Bowser contact (game over)
    if pygame.sprite.collide_rect(player, bowser):
        lose_sound.play()
        print("Hit by Bowser! Game Over.")
        running = False

    # Draw
    screen.fill(BLACK)
    pygame.draw.rect(screen, WHITE, (0, HEIGHT - 50, WIDTH, 50))  # Ground
    all_sprites.draw(screen)
    pygame.display.flip()

pygame.quit()

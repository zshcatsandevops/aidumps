# PVZ-Style Engine without PNGs - BUGS FIXED!
# Procedural graphics and sound for Cat-plants vs Zombie-mashers

import pygame
import random
import math
import threading
import numpy as np
import time

# --- Constants ---
WIDTH, HEIGHT = 800, 600
FPS = 60
LANE_COUNT = 5
LANE_HEIGHT = HEIGHT // (LANE_COUNT + 1)
SOUND_VOL = 0.2  # Master volume for sounds

# Colors
green = (50, 200, 50)
dark_green = (30, 150, 30)
yellow = (250, 250, 100)
red = (200, 50, 50)
dark_red = (150, 30, 30)
brown = (150, 75, 0)
black = (0, 0, 0)
sky = (135, 206, 235)
white = (255, 255, 255)

# Initialize Pygame and Mixer
pygame.init()
# Fixed: Use stereo for better compatibility
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# --- Sound Engine ---
SAMPLE_RATE = 44100

# Generate a sine wave tone with proper shape
def generate_tone(frequency, duration=0.2):
    # create time array
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    # sine wave with envelope to prevent clicking
    wave = 0.3 * np.sin(2 * math.pi * frequency * t)
    # Apply fade in/out to prevent audio clicks
    fade_samples = int(0.01 * SAMPLE_RATE)  # 10ms fade
    wave[:fade_samples] *= np.linspace(0, 1, fade_samples)
    wave[-fade_samples:] *= np.linspace(1, 0, fade_samples)
    # convert to 16-bit signed
    audio = np.int16(wave * 32767)
    # Fixed: Create stereo audio (n_samples, 2)
    stereo_audio = np.column_stack((audio, audio))
    sound = pygame.sndarray.make_sound(stereo_audio)
    sound.set_volume(SOUND_VOL)
    return sound

# Pre-generate common sounds
tone_pew = generate_tone(880, 0.1)      # bullet pew
tone_pop = generate_tone(440, 0.1)      # plant place
zombie_moan = generate_tone(200, 0.3)   # zombie spawn
hit_sound = generate_tone(660, 0.05)    # bullet hit

# Background music thread - FIXED to be more stable
MELODY = [261.63, 329.63, 392.00, 523.25, 392.00, 329.63]
BEAT = 0.5
music_playing = True

def play_music():
    while music_playing:
        for freq in MELODY:
            if not music_playing:
                break
            note = generate_tone(freq, BEAT * 0.8)
            note.play()
            time.sleep(BEAT)  # Use time.sleep instead of pygame.time.delay

music_thread = threading.Thread(target=play_music, daemon=True)
music_thread.start()

class Engine:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Procedural PVZ Engine w/ Sound - BUGS FIXED!")
        self.clock = pygame.time.Clock()
        self.plants = []
        self.zombies = []
        self.bullets = []  # Fixed: Track all bullets centrally for collision
        self.spawn_timer = 0
        self.running = True
        self.score = 0

    def add_plant(self, lane, x):
        # Fixed: Prevent placing plants too close to each other
        for plant in self.plants:
            if plant.lane == lane and abs(plant.x - x) < 60:
                return  # Don't place if too close
        
        self.plants.append(Plant(lane, x))
        tone_pop.play()

    def spawn_zombie(self):
        lane = random.randint(0, LANE_COUNT - 1)
        self.zombies.append(Zombie(lane))
        zombie_moan.play()

    def run(self):
        global music_playing
        try:
            while self.running:
                dt = self.clock.tick(FPS)
                self.handle_events()
                self.update(dt)
                self.draw()
        finally:
            music_playing = False
            pygame.quit()

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                # Fixed: Better lane calculation
                lane = (my - LANE_HEIGHT//2) // LANE_HEIGHT
                if 0 <= lane < LANE_COUNT and mx > 50:  # Don't place too close to left edge
                    self.add_plant(lane, mx)

    def update(self, dt):
        # Fixed: Ensure dt is reasonable to prevent weird movement
        if dt <= 0:
            dt = 16  # Default to ~60fps timing
        
        # spawn zombies periodically
        self.spawn_timer += dt
        if self.spawn_timer > 3000:  # Slightly longer spawn time
            self.spawn_timer = 0
            self.spawn_zombie()
        
        # update plants and collect bullets
        self.bullets.clear()
        for p in self.plants:
            p.update(dt)
            self.bullets.extend(p.bullets)
        
        # update zombies
        for z in self.zombies[:]:
            z.update(dt)
            if z.x < -50:
                self.zombies.remove(z)
        
        # FIXED: Add collision detection!
        self.check_collisions()

    def check_collisions(self):
        """Handle bullet-zombie collisions"""
        for plant in self.plants:
            for bullet in plant.bullets[:]:
                bullet_rect = pygame.Rect(bullet.x-5, bullet.y-5, 10, 10)
                
                for zombie in self.zombies[:]:
                    zombie_rect = pygame.Rect(zombie.x-15, zombie.y-20, 30, 40)
                    
                    if bullet_rect.colliderect(zombie_rect):
                        # Hit! Remove bullet and damage zombie
                        plant.bullets.remove(bullet)
                        zombie.health -= 1
                        hit_sound.play()
                        self.score += 10
                        
                        if zombie.health <= 0:
                            self.zombies.remove(zombie)
                            self.score += 50
                        break

    def draw(self):
        self.screen.fill(sky)
        
        # draw lanes with better visibility
        for i in range(LANE_COUNT):
            y = (i+1)*LANE_HEIGHT + LANE_HEIGHT//2
            pygame.draw.line(self.screen, (100, 100, 100), (0, y), (WIDTH, y), 2)
        
        # draw plants & bullets
        for p in self.plants:
            p.draw(self.screen)
        
        # draw zombies
        for z in self.zombies:
            z.draw(self.screen)
        
        # Fixed: Add score display
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {self.score}", True, black)
        self.screen.blit(score_text, (10, 10))
        
        # Add instructions
        font_small = pygame.font.Font(None, 24)
        instructions = font_small.render("Click to place plants! Defend against zombies!", True, black)
        self.screen.blit(instructions, (10, 50))
        
        pygame.display.flip()

class Plant:
    def __init__(self, lane, x):
        self.lane = lane
        self.x = x
        # Fixed: Better y positioning to align with lanes
        self.y = (lane+1)*LANE_HEIGHT + LANE_HEIGHT//2
        self.shoot_timer = 0
        self.bullets = []

    def update(self, dt):
        self.shoot_timer += dt
        
        # Fixed: Only shoot if there's a zombie in this lane
        has_zombie_in_lane = any(z.lane == self.lane and z.x > self.x for z in engine.zombies if 'engine' in globals())
        
        if self.shoot_timer >= 1500 and has_zombie_in_lane:  # Slightly slower shooting
            self.shoot_timer = 0
            self.bullets.append(Bullet(self.x + 20, self.y))  # Shoot from plant edge
            tone_pew.play()
        
        # update bullets
        for b in self.bullets[:]:
            b.update(dt)
            if b.x > WIDTH + 50:
                self.bullets.remove(b)

    def draw(self, surf):
        # stem
        pygame.draw.line(surf, dark_green, (self.x, self.y), (self.x, self.y+20), 6)
        # petals - make them more flower-like
        for angle in [0, math.pi/2, math.pi, 3*math.pi/2]:
            cx = self.x + math.cos(angle)*18
            cy = self.y + math.sin(angle)*18
            pygame.draw.circle(surf, green, (int(cx), int(cy)), 8)
        # center
        pygame.draw.circle(surf, yellow, (self.x, self.y), 12)
        # bullets
        for b in self.bullets:
            b.draw(surf)

class Zombie:
    def __init__(self, lane):
        self.lane = lane
        self.x = WIDTH + 20
        # Fixed: Better y positioning
        self.y = (lane+1)*LANE_HEIGHT + LANE_HEIGHT//2
        self.speed = random.uniform(15, 25)  # Fixed: More reasonable speed
        self.health = 3  # Fixed: Add health system

    def update(self, dt):
        # Fixed: More consistent movement calculation
        self.x -= (self.speed * dt) / 1000.0  # Convert dt from ms to seconds

    def draw(self, surf):
        # Fixed: Health-based coloring
        color = dark_red if self.health > 1 else red
        
        # body
        pygame.draw.rect(surf, color, (self.x-15, self.y-20, 30, 40))
        # eyes - more zombie-like
        pygame.draw.circle(surf, red, (int(self.x-7), self.y-5), 3)
        pygame.draw.circle(surf, red, (int(self.x+7), self.y-5), 3)
        # arms
        pygame.draw.line(surf, color, (self.x-15,self.y), (self.x-25,self.y+10), 4)
        pygame.draw.line(surf, color, (self.x+15,self.y), (self.x+25,self.y+10), 4)
        
        # Fixed: Health indicator
        if self.health < 3:
            for i in range(self.health):
                pygame.draw.circle(surf, green, (int(self.x-10+i*7), self.y-30), 2)

class Bullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 200  # Fixed: Reasonable bullet speed (pixels per second)

    def update(self, dt):
        # Fixed: Consistent movement
        self.x += (self.speed * dt) / 1000.0

    def draw(self, surf):
        pygame.draw.circle(surf, yellow, (int(self.x), int(self.y)), 4)
        pygame.draw.circle(surf, black, (int(self.x), int(self.y)), 4, 2)

if __name__ == "__main__":
    engine = Engine()
    engine.run()

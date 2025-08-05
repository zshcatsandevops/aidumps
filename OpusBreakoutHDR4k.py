import pygame
import math
import random
import numpy as np
from pygame import gfxdraw

# Initialize Pygame and mixer
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# PS5 Colors (More sophisticated palette)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
NEON_CYAN = (0, 255, 255)
NEON_PINK = (255, 0, 255)
NEON_PURPLE = (131, 56, 236)
NEON_BLUE = (58, 134, 255)
NEON_YELLOW = (255, 190, 11)
NEON_ORANGE = (251, 86, 7)
NEON_RED = (255, 0, 110)
DARK_PURPLE = (25, 0, 51)
ELECTRIC_BLUE = (0, 150, 255)

# Brick colors with metallic feel
BRICK_COLORS = [
    (255, 0, 110),    # Neon Red
    (251, 86, 7),     # Neon Orange  
    (255, 190, 11),   # Neon Yellow
    (131, 56, 236),   # Neon Purple
    (58, 134, 255)    # Neon Blue
]

class SoundManager:
    def __init__(self):
        # Create synthetic sounds since we can't load files
        self.sounds = {}
        self.create_sounds()
        
    def create_sounds(self):
        # Create synthetic sound effects
        # Hit sound
        duration = 0.1
        sample_rate = 22050
        samples = int(duration * sample_rate)
        frequency = 440  # A4 note
        
        # Paddle hit - higher pitch
        wave = np.sin(frequency * 2 * np.pi * np.arange(samples) / sample_rate)
        wave = (wave * 32767).astype(np.int16)
        wave = np.repeat(wave.reshape(samples, 1), 2, axis=1)
        self.sounds['paddle_hit'] = pygame.sndarray.make_sound(wave)
        
        # Brick hit - mid pitch with decay
        frequency = 330
        t = np.linspace(0, duration, samples)
        envelope = np.exp(-t * 10)  # Exponential decay
        wave = envelope * np.sin(frequency * 2 * np.pi * t)
        wave = (wave * 32767).astype(np.int16)
        wave = np.repeat(wave.reshape(samples, 1), 2, axis=1)
        self.sounds['brick_hit'] = pygame.sndarray.make_sound(wave)
        
        # Wall hit - lower pitch
        frequency = 220
        wave = np.sin(frequency * 2 * np.pi * np.arange(samples) / sample_rate)
        wave = (wave * 16383).astype(np.int16)
        wave = np.repeat(wave.reshape(samples, 1), 2, axis=1)
        self.sounds['wall_hit'] = pygame.sndarray.make_sound(wave)
        
        # Level up - ascending tones
        duration = 0.5
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples)
        wave = np.zeros(samples)
        for i, freq in enumerate([440, 554, 659, 880]):
            start = int(i * samples / 4)
            end = int((i + 1) * samples / 4)
            wave[start:end] = np.sin(freq * 2 * np.pi * np.arange(end - start) / sample_rate)
        wave = (wave * 16383).astype(np.int16)
        wave = np.repeat(wave.reshape(samples, 1), 2, axis=1)
        self.sounds['level_up'] = pygame.sndarray.make_sound(wave)
        
        # Set volumes
        for sound in self.sounds.values():
            sound.set_volume(0.3)
    
    def play(self, sound_name):
        if sound_name in self.sounds:
            self.sounds[sound_name].play()

class ScreenEffects:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.shake_amount = 0
        self.shake_x = 0
        self.shake_y = 0
        self.chromatic_aberration = 0
        self.flash_alpha = 0
        self.flash_color = WHITE
        
    def add_shake(self, amount):
        self.shake_amount = min(self.shake_amount + amount, 20)
        
    def add_flash(self, color, intensity=128):
        self.flash_alpha = intensity
        self.flash_color = color
        
    def add_chromatic_aberration(self, amount):
        self.chromatic_aberration = min(self.chromatic_aberration + amount, 10)
        
    def update(self):
        # Update shake
        if self.shake_amount > 0:
            self.shake_x = random.randint(-int(self.shake_amount), int(self.shake_amount))
            self.shake_y = random.randint(-int(self.shake_amount), int(self.shake_amount))
            self.shake_amount *= 0.9
            
        # Update flash
        if self.flash_alpha > 0:
            self.flash_alpha -= 5
            
        # Update chromatic aberration
        if self.chromatic_aberration > 0:
            self.chromatic_aberration *= 0.95
    
    def apply(self, screen, game_surface):
        # Create a copy for effects
        display_surface = game_surface.copy()
        
        # Apply chromatic aberration (RGB split)
        if self.chromatic_aberration > 1:
            # Create RGB channels
            r_channel = pygame.Surface((self.width, self.height))
            g_channel = pygame.Surface((self.width, self.height))
            b_channel = pygame.Surface((self.width, self.height))
            
            # Extract channels with offset
            offset = int(self.chromatic_aberration)
            r_channel.blit(display_surface, (offset, 0))
            g_channel.blit(display_surface, (0, 0))
            b_channel.blit(display_surface, (-offset, 0))
            
            # Combine with blend modes
            display_surface.blit(r_channel, (0, 0), special_flags=pygame.BLEND_ADD)
        
        # Apply screen shake
        screen.blit(display_surface, (self.shake_x, self.shake_y))
        
        # Apply flash
        if self.flash_alpha > 0:
            flash_surf = pygame.Surface((self.width, self.height))
            flash_surf.fill(self.flash_color)
            flash_surf.set_alpha(self.flash_alpha)
            screen.blit(flash_surf, (0, 0))

class Particle:
    def __init__(self, x, y, color, velocity_multiplier=1.0):
        self.x = x
        self.y = y
        self.vx = random.uniform(-8, 8) * velocity_multiplier
        self.vy = random.uniform(-8, 8) * velocity_multiplier
        self.life = 1.0
        self.color = color
        self.size = random.randint(2, 8)
        self.glow_size = self.size * 2
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-10, 10)
        
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.3  # Gravity
        self.life -= 0.015
        self.size *= 0.97
        self.glow_size *= 0.96
        self.rotation += self.rotation_speed
        self.vx *= 0.98  # Air resistance
        
    def draw(self, screen):
        if self.life > 0 and self.size > 0.5:
            alpha = int(255 * self.life)
            
            # Draw glow
            if self.glow_size > 1:
                glow_surf = pygame.Surface((int(self.glow_size * 4), int(self.glow_size * 4)), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*self.color, min(alpha // 3, 50)), 
                                 (int(self.glow_size * 2), int(self.glow_size * 2)), int(self.glow_size))
                screen.blit(glow_surf, (self.x - self.glow_size * 2, self.y - self.glow_size * 2))
            
            # Draw particle
            if self.size > 1:
                # Rotate square particles for more dynamic feel
                points = []
                for angle in [0, 90, 180, 270]:
                    rad = math.radians(angle + self.rotation)
                    px = self.x + math.cos(rad) * self.size
                    py = self.y + math.sin(rad) * self.size
                    points.append((px, py))
                
                if len(points) >= 3:
                    pygame.draw.polygon(screen, self.color, points)

class Ball:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 8
        self.dx = 4
        self.dy = -4
        self.speed = 4
        self.trail = []
        self.color = NEON_PINK
        self.pulse = 0
        self.energy_particles = []
        
    def update(self):
        self.x += self.dx
        self.y += self.dy
        
        # Add to trail with position and size
        self.trail.append({
            'x': self.x, 
            'y': self.y, 
            'time': 1.0,
            'size': self.radius
        })
        
        if len(self.trail) > 15:
            self.trail.pop(0)
            
        # Update trail
        for t in self.trail:
            t['time'] *= 0.95
            t['size'] *= 0.98
            
        # Pulse effect
        self.pulse = (self.pulse + 0.2) % (2 * math.pi)
        
        # Energy particles around ball
        if random.random() < 0.3:
            angle = random.uniform(0, 2 * math.pi)
            dist = self.radius + random.uniform(0, 10)
            px = self.x + math.cos(angle) * dist
            py = self.y + math.sin(angle) * dist
            self.energy_particles.append({
                'x': px, 'y': py,
                'vx': math.cos(angle) * 0.5,
                'vy': math.sin(angle) * 0.5,
                'life': 1.0,
                'size': random.uniform(1, 3)
            })
            
        # Update energy particles
        self.energy_particles = [p for p in self.energy_particles if p['life'] > 0]
        for p in self.energy_particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 0.02
            p['size'] *= 0.98
            
    def draw(self, screen):
        # Draw motion blur trail
        for i, t in enumerate(self.trail):
            if t['time'] > 0 and t['size'] > 0:
                alpha = int(255 * t['time'] * (i / len(self.trail)) * 0.3)
                
                # Multiple layers for better effect
                for layer in range(2):
                    size = t['size'] * (1 - layer * 0.3)
                    if size > 0:
                        glow_surf = pygame.Surface((int(size * 4), int(size * 4)), pygame.SRCALPHA)
                        pygame.draw.circle(glow_surf, (*self.color, alpha // (layer + 1)), 
                                         (int(size * 2), int(size * 2)), int(size))
                        screen.blit(glow_surf, (t['x'] - size * 2, t['y'] - size * 2))
        
        # Draw energy particles
        for p in self.energy_particles:
            if p['life'] > 0 and p['size'] > 0:
                alpha = int(100 * p['life'])
                pygame.draw.circle(screen, (*ELECTRIC_BLUE, alpha), 
                                 (int(p['x']), int(p['y'])), int(p['size']))
        
        # Draw main ball with multiple glow layers
        pulse_size = math.sin(self.pulse) * 2
        
        # Outer glow
        for i in range(4):
            alpha = 60 - i * 15
            radius = self.radius + i * 6 + pulse_size
            glow_surf = pygame.Surface((int(radius * 4), int(radius * 4)), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*self.color, alpha), 
                             (int(radius * 2), int(radius * 2)), int(radius))
            screen.blit(glow_surf, (self.x - radius * 2, self.y - radius * 2))
        
        # Core ball with gradient
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius - 2)
        
        # Inner bright spot
        highlight_x = int(self.x - self.radius * 0.3)
        highlight_y = int(self.y - self.radius * 0.3)
        pygame.draw.circle(screen, WHITE, (highlight_x, highlight_y), max(2, self.radius // 3))

class Paddle:
    def __init__(self, x, y):
        self.width = 120
        self.height = 20
        self.x = x
        self.y = y
        self.color = NEON_CYAN
        self.glow = 0
        self.energy = 1.0
        self.particles = []
        
    def update(self, mouse_x):
        # Smooth movement towards mouse
        target_x = mouse_x - self.width // 2
        old_x = self.x
        self.x += (target_x - self.x) * 0.2
        
        # Keep paddle in bounds
        self.x = max(0, min(self.x, SCREEN_WIDTH - self.width))
        
        # Movement particles
        speed = abs(self.x - old_x)
        if speed > 1:
            for _ in range(int(speed)):
                self.particles.append({
                    'x': self.x + self.width // 2 + random.randint(-self.width//2, self.width//2),
                    'y': self.y + self.height,
                    'vy': random.uniform(0, 2),
                    'life': 1.0,
                    'size': random.uniform(1, 3)
                })
        
        # Update particles
        self.particles = [p for p in self.particles if p['life'] > 0]
        for p in self.particles:
            p['y'] += p['vy']
            p['life'] -= 0.03
            p['size'] *= 0.95
        
        # Update glow
        if self.glow > 0:
            self.glow -= 0.5
            
    def draw(self, screen):
        # Draw movement particles
        for p in self.particles:
            if p['life'] > 0 and p['size'] > 0:
                alpha = int(100 * p['life'])
                pygame.draw.circle(screen, (*self.color, alpha), 
                                 (int(p['x']), int(p['y'])), int(p['size']))
        
        # Draw multiple glow layers
        glow_intensity = self.glow / 20
        for i in range(4):
            alpha = int((60 - i * 15) * (1 + glow_intensity))
            expand = i * 8 + self.glow
            glow_rect = pygame.Rect(self.x - expand, self.y - expand, 
                                   self.width + expand * 2, self.height + expand * 2)
            s = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(s, (*self.color, min(alpha, 100)), s.get_rect(), border_radius=10)
            screen.blit(s, glow_rect)
        
        # Draw paddle with metallic gradient
        paddle_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        # Main paddle
        pygame.draw.rect(screen, self.color, paddle_rect, border_radius=8)
        
        # Metallic highlight
        highlight_rect = pygame.Rect(self.x + 2, self.y + 2, self.width - 4, self.height // 3)
        pygame.draw.rect(screen, (255, 255, 255, 128), highlight_rect, border_radius=4)
        
        # Edge glow
        pygame.draw.rect(screen, WHITE, paddle_rect, width=2, border_radius=8)
        
        # Energy indicator
        energy_width = int(self.width * self.energy)
        if energy_width > 0:
            energy_rect = pygame.Rect(self.x, self.y + self.height - 4, energy_width, 2)
            pygame.draw.rect(screen, ELECTRIC_BLUE, energy_rect)

class Brick:
    def __init__(self, x, y, color):
        self.width = 80
        self.height = 30
        self.x = x
        self.y = y
        self.color = color
        self.status = 1
        self.hit_animation = 0
        self.crack_lines = []
        self.glow_pulse = random.uniform(0, 2 * math.pi)
        
    def hit(self):
        self.status = 0
        self.hit_animation = 1.0
        
        # Create crack effect
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2
        for _ in range(5):
            angle = random.uniform(0, 2 * math.pi)
            length = random.uniform(10, 30)
            end_x = center_x + math.cos(angle) * length
            end_y = center_y + math.sin(angle) * length
            self.crack_lines.append({
                'start': (center_x, center_y),
                'end': (end_x, end_y),
                'life': 1.0
            })
        
    def update(self):
        self.glow_pulse += 0.05
        
        # Update cracks
        for crack in self.crack_lines:
            crack['life'] -= 0.02
            
    def draw(self, screen):
        if self.status == 1:
            # Pulsing glow
            pulse = math.sin(self.glow_pulse) * 0.1 + 0.9
            
            # Scale animation when hit
            if self.hit_animation > 0:
                scale = 1 + self.hit_animation * 0.2
                width = int(self.width * scale)
                height = int(self.height * scale)
                x = self.x - (width - self.width) // 2
                y = self.y - (height - self.height) // 2
                self.hit_animation -= 0.1
            else:
                width, height, x, y = self.width, self.height, self.x, self.y
            
            # Multi-layer glow effect
            for i in range(3):
                alpha = int((40 - i * 10) * pulse)
                expand = i * 6
                glow_surf = pygame.Surface((width + expand * 2, height + expand * 2), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (*self.color, alpha), glow_surf.get_rect(), border_radius=6)
                screen.blit(glow_surf, (x - expand, y - expand))
            
            # Main brick with gradient
            brick_rect = pygame.Rect(x, y, width, height)
            pygame.draw.rect(screen, self.color, brick_rect, border_radius=4)
            
            # Metallic shine
            shine_rect = pygame.Rect(x + 2, y + 2, width - 4, height // 3)
            shine_color = tuple(min(255, c + 80) for c in self.color)
            pygame.draw.rect(screen, shine_color, shine_rect, border_radius=2)
            
            # Edge highlight
            pygame.draw.rect(screen, WHITE, brick_rect, width=1, border_radius=4)
            
        # Draw cracks
        for crack in self.crack_lines:
            if crack['life'] > 0:
                alpha = int(255 * crack['life'])
                pygame.draw.line(screen, (*WHITE, alpha), crack['start'], crack['end'], 2)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Neon Breakout - PS5 Edition")
        self.clock = pygame.time.Clock()
        self.game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # Fonts
        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 200)
        self.small_font = pygame.font.Font(None, 24)
        
        # Game state
        self.score = 0
        self.lives = 3
        self.level = 1
        self.combo = 0
        self.running = True
        self.particles = []
        
        # Effects
        self.screen_effects = ScreenEffects(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.sound_manager = SoundManager()
        
        # Background stars
        self.stars = []
        for _ in range(100):
            self.stars.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'size': random.uniform(0.5, 2),
                'brightness': random.uniform(0.3, 1.0),
                'twinkle': random.uniform(0, 2 * math.pi)
            })
        
        # Game objects
        self.paddle = Paddle(SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT - 40)
        self.ball = Ball(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.bricks = self.create_bricks()
        
    def create_bricks(self):
        bricks = []
        rows = 5
        cols = 8
        brick_width = 80
        brick_height = 30
        padding = 10
        offset_x = 35
        offset_y = 80
        
        for row in range(rows):
            for col in range(cols):
                x = col * (brick_width + padding) + offset_x
                y = row * (brick_height + padding) + offset_y
                color = BRICK_COLORS[row]
                bricks.append(Brick(x, y, color))
                
        return bricks
    
    def create_explosion(self, x, y, color, intensity=1.0):
        num_particles = int(30 * intensity)
        for _ in range(num_particles):
            self.particles.append(Particle(x, y, color, intensity))
            
        # Add screen effects based on intensity
        self.screen_effects.add_shake(5 * intensity)
        if intensity > 0.5:
            self.screen_effects.add_flash(color, int(50 * intensity))
            self.screen_effects.add_chromatic_aberration(3 * intensity)
    
    def handle_collisions(self):
        # Ball with walls
        if self.ball.x - self.ball.radius <= 0 or self.ball.x + self.ball.radius >= SCREEN_WIDTH:
            self.ball.dx = -self.ball.dx
            self.create_explosion(self.ball.x, self.ball.y, NEON_CYAN, 0.5)
            self.sound_manager.play('wall_hit')
            
        if self.ball.y - self.ball.radius <= 0:
            self.ball.dy = -self.ball.dy
            self.create_explosion(self.ball.x, self.ball.y, NEON_CYAN, 0.5)
            self.sound_manager.play('wall_hit')
        
        # Ball with paddle
        ball_rect = pygame.Rect(self.ball.x - self.ball.radius, self.ball.y - self.ball.radius,
                               self.ball.radius * 2, self.ball.radius * 2)
        paddle_rect = pygame.Rect(self.paddle.x, self.paddle.y, self.paddle.width, self.paddle.height)
        
        if ball_rect.colliderect(paddle_rect) and self.ball.dy > 0:
            # Calculate hit position for angle
            hit_pos = (self.ball.x - self.paddle.x) / self.paddle.width
            self.ball.dx = 8 * (hit_pos - 0.5)
            self.ball.dy = -abs(self.ball.dy)
            self.paddle.glow = 20
            self.paddle.energy = min(1.0, self.paddle.energy + 0.1)
            self.create_explosion(self.ball.x, self.paddle.y, self.paddle.color, 0.7)
            self.sound_manager.play('paddle_hit')
            self.combo = 0  # Reset combo on paddle hit
        
        # Ball with bricks
        for brick in self.bricks:
            if brick.status == 1:
                brick_rect = pygame.Rect(brick.x, brick.y, brick.width, brick.height)
                if ball_rect.colliderect(brick_rect):
                    brick.hit()
                    self.ball.dy = -self.ball.dy
                    self.combo += 1
                    self.score += (10 + self.combo * 5) * self.level
                    self.create_explosion(brick.x + brick.width // 2, 
                                        brick.y + brick.height // 2, brick.color, 1.0)
                    self.sound_manager.play('brick_hit')
                    
                    # Extra effects for combo
                    if self.combo > 5:
                        self.screen_effects.add_chromatic_aberration(5)
                    
                    # Check if level complete
                    if all(brick.status == 0 for brick in self.bricks):
                        self.level += 1
                        self.ball.speed += 0.5
                        self.bricks = self.create_bricks()
                        self.sound_manager.play('level_up')
                        self.screen_effects.add_flash(WHITE, 200)
                        self.create_explosion(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, 
                                            ELECTRIC_BLUE, 2.0)
        
        # Ball out of bounds
        if self.ball.y - self.ball.radius > SCREEN_HEIGHT:
            self.lives -= 1
            self.combo = 0
            self.screen_effects.add_shake(20)
            self.screen_effects.add_flash(NEON_RED, 100)
            
            if self.lives == 0:
                self.running = False
            else:
                # Reset ball
                self.ball.x = SCREEN_WIDTH // 2
                self.ball.y = SCREEN_HEIGHT // 2
                self.ball.dx = 4
                self.ball.dy = -4
    
    def draw_background(self):
        # Gradient background
        for y in range(SCREEN_HEIGHT):
            progress = y / SCREEN_HEIGHT
            r = int(DARK_PURPLE[0] * (1 - progress) + BLACK[0] * progress)
            g = int(DARK_PURPLE[1] * (1 - progress) + BLACK[1] * progress)
            b = int(DARK_PURPLE[2] * (1 - progress) + BLACK[2] * progress)
            pygame.draw.line(self.game_surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        
        # Animated stars
        for star in self.stars:
            star['twinkle'] += 0.05
            brightness = star['brightness'] * (0.5 + 0.5 * math.sin(star['twinkle']))
            color = (int(255 * brightness), int(255 * brightness), int(255 * brightness))
            pygame.draw.circle(self.game_surface, color, 
                             (int(star['x']), int(star['y'])), int(star['size']))
    
    def draw_hud(self):
        # Score with glow
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(topleft=(20, 20))
        
        # Glow effect
        for i in range(3):
            alpha = 100 - i * 30
            s = pygame.Surface((score_rect.width + i * 6, score_rect.height + i * 6), pygame.SRCALPHA)
            s.fill((*NEON_CYAN, alpha))
            self.game_surface.blit(s, (score_rect.x - i * 3, score_rect.y - i * 3))
        
        self.game_surface.blit(score_text, score_rect)
        
        # Lives with visual indicators
        for i in range(self.lives):
            x = SCREEN_WIDTH // 2 - 30 + i * 25
            y = 30
            pygame.draw.circle(self.game_surface, NEON_PINK, (x, y), 8)
            pygame.draw.circle(self.game_surface, WHITE, (x, y), 6)
        
        # Level
        level_text = self.font.render(f"Level: {self.level}", True, WHITE)
        level_rect = level_text.get_rect(topright=(SCREEN_WIDTH - 20, 20))
        self.game_surface.blit(level_text, level_rect)
        
        # Combo indicator
        if self.combo > 1:
            combo_text = self.small_font.render(f"COMBO x{self.combo}", True, NEON_YELLOW)
            combo_rect = combo_text.get_rect(center=(SCREEN_WIDTH // 2, 60))
            self.game_surface.blit(combo_text, combo_rect)
        
        # Big level number in background
        big_level = self.big_font.render(str(self.level), True, WHITE)
        big_level.set_alpha(15)
        big_rect = big_level.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.game_surface.blit(big_level, big_rect)
    
    def run(self):
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            
            # Get mouse position
            mouse_x, _ = pygame.mouse.get_pos()
            
            # Update game objects
            self.paddle.update(mouse_x)
            self.ball.update()
            self.handle_collisions()
            
            # Update bricks
            for brick in self.bricks:
                brick.update()
            
            # Update particles
            self.particles = [p for p in self.particles if p.life > 0]
            for particle in self.particles:
                particle.update()
                
            # Update screen effects
            self.screen_effects.update()
            
            # Draw everything to game surface
            self.draw_background()
            
            # Draw game objects
            for brick in self.bricks:
                brick.draw(self.game_surface)
            
            self.paddle.draw(self.game_surface)
            self.ball.draw(self.game_surface)
            
            # Draw particles
            for particle in self.particles:
                particle.draw(self.game_surface)
            
            # Draw HUD
            self.draw_hud()
            
            # Apply screen effects and display
            self.screen_effects.apply(self.screen, self.game_surface)
            
            # Update display
            pygame.display.flip()
            self.clock.tick(FPS)
        
        # Game over
        pygame.quit()

# Run the game
if __name__ == "__main__":
    game = Game()
    game.run()

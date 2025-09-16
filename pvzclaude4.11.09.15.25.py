import pygame, random, math
from pygame.locals import *
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

SCREEN_WIDTH, SCREEN_HEIGHT = 1024, 768
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Plants vs Zombies - iOS Edition [Haltmann OS]")
clock = pygame.time.Clock()

# ================== AUDIO SYSTEM ==================
class AudioEngine:
    def __init__(self):
        self.channels = {
            'music': pygame.mixer.Channel(0),
            'plants': pygame.mixer.Channel(1),
            'zombies': pygame.mixer.Channel(2),
            'projectiles': pygame.mixer.Channel(3),
            'ui': pygame.mixer.Channel(4),
            'ambient': pygame.mixer.Channel(5)
        }
        self.sounds = {}
        self.music_volume = 0.7
        self.sfx_volume = 0.8
        self.generate_sounds()
        self.music_timer = 0
        self.beat_counter = 0
        
    def generate_sounds(self):
        """Generate procedural audio effects"""
        sample_rate = 22050
        
        # Background music - "do do do do" pattern
        self.generate_background_music(sample_rate)
        
        # Plant sounds
        self.sounds['plant_place'] = self.create_synth_sound(440, 0.1, sample_rate, 'sine')
        self.sounds['shoot'] = self.create_synth_sound(880, 0.05, sample_rate, 'square')
        self.sounds['sunflower'] = self.create_synth_sound(660, 0.2, sample_rate, 'triangle')
        
        # Zombie sounds
        self.sounds['zombie_groan'] = self.create_groan_sound(sample_rate)
        self.sounds['zombie_eat'] = self.create_synth_sound(110, 0.1, sample_rate, 'sawtooth')
        
        # Collection sounds
        self.sounds['sun_collect'] = self.create_sparkle_sound(sample_rate)
        
        # UI sounds
        self.sounds['wave_complete'] = self.create_fanfare_sound(sample_rate)
        self.sounds['game_over'] = self.create_game_over_sound(sample_rate)
        
    def generate_background_music(self, sample_rate):
        """Generate the 'do do do do' background loop"""
        duration = 4.0  # 4 second loop
        samples = int(sample_rate * duration)
        
        # Create the pattern
        wave = np.zeros(samples)
        
        # Notes for "do do do do" pattern (C-E-G-C pattern)
        notes = [261.63, 329.63, 392.00, 523.25]  # C4, E4, G4, C5
        beat_duration = duration / len(notes)
        
        for i, freq in enumerate(notes):
            start = int(i * beat_duration * sample_rate)
            end = int((i + 0.5) * beat_duration * sample_rate)
            
            # Generate note with envelope
            t = np.linspace(0, 0.5 * beat_duration, end - start)
            note = np.sin(2 * np.pi * freq * t)
            
            # Apply envelope (attack-decay)
            envelope = np.exp(-3 * t)
            note = note * envelope * 0.3
            
            # Add harmonic for richness
            harmonic = np.sin(4 * np.pi * freq * t) * 0.1
            note += harmonic * envelope
            
            wave[start:end] += note
            
        # Add bass line
        bass_freq = 130.81  # C3
        t = np.linspace(0, duration, samples)
        bass = np.sin(2 * np.pi * bass_freq * t) * 0.2
        wave += bass
        
        # Convert to pygame sound
        wave = np.clip(wave, -1, 1)
        wave = (wave * 32767).astype(np.int16)
        stereo_wave = np.column_stack((wave, wave))
        
        self.sounds['background_music'] = pygame.sndarray.make_sound(stereo_wave)
        
    def create_synth_sound(self, freq, duration, sample_rate, wave_type='sine'):
        """Create basic synthesized sounds"""
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples)
        
        if wave_type == 'sine':
            wave = np.sin(2 * np.pi * freq * t)
        elif wave_type == 'square':
            wave = np.sign(np.sin(2 * np.pi * freq * t))
        elif wave_type == 'triangle':
            wave = 2 * np.arcsin(np.sin(2 * np.pi * freq * t)) / np.pi
        elif wave_type == 'sawtooth':
            wave = 2 * (t * freq - np.floor(t * freq + 0.5))
        else:
            wave = np.sin(2 * np.pi * freq * t)
            
        # Apply envelope
        envelope = np.exp(-5 * t)
        wave = wave * envelope * 0.5
        
        # Convert to pygame sound
        wave = np.clip(wave, -1, 1)
        wave = (wave * 32767).astype(np.int16)
        stereo_wave = np.column_stack((wave, wave))
        
        return pygame.sndarray.make_sound(stereo_wave)
    
    def create_groan_sound(self, sample_rate):
        """Create zombie groan sound"""
        duration = 0.5
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples)
        
        # Low frequency with vibrato
        base_freq = 80
        vibrato = np.sin(2 * np.pi * 5 * t) * 10
        wave = np.sin(2 * np.pi * (base_freq + vibrato) * t)
        
        # Add noise for texture
        noise = np.random.normal(0, 0.1, samples)
        wave = wave * 0.7 + noise * 0.3
        
        # Apply envelope
        envelope = np.ones(samples)
        envelope[:100] = np.linspace(0, 1, 100)
        envelope[-100:] = np.linspace(1, 0, 100)
        wave = wave * envelope * 0.4
        
        wave = np.clip(wave, -1, 1)
        wave = (wave * 32767).astype(np.int16)
        stereo_wave = np.column_stack((wave, wave))
        
        return pygame.sndarray.make_sound(stereo_wave)
    
    def create_sparkle_sound(self, sample_rate):
        """Create sun collection sparkle sound"""
        duration = 0.3
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples)
        
        # Ascending arpeggio
        wave = np.zeros(samples)
        frequencies = [523.25, 659.25, 783.99, 1046.50]  # C5, E5, G5, C6
        
        for i, freq in enumerate(frequencies):
            start = int(i * samples / len(frequencies))
            end = samples
            segment = t[start:end] - t[start]
            note = np.sin(2 * np.pi * freq * segment) * np.exp(-10 * segment)
            wave[start:end] += note * 0.3
            
        wave = np.clip(wave, -1, 1)
        wave = (wave * 32767).astype(np.int16)
        stereo_wave = np.column_stack((wave, wave))
        
        return pygame.sndarray.make_sound(stereo_wave)
    
    def create_fanfare_sound(self, sample_rate):
        """Create wave complete fanfare"""
        duration = 1.0
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples)
        
        # Major chord arpeggio
        wave = np.zeros(samples)
        chord = [261.63, 329.63, 392.00, 523.25, 392.00, 329.63, 261.63]
        
        for i, freq in enumerate(chord):
            start = int(i * samples / len(chord))
            end = int((i + 1) * samples / len(chord))
            segment = t[start:end] - t[start]
            note = np.sin(2 * np.pi * freq * segment)
            envelope = np.exp(-2 * segment)
            wave[start:end] += note * envelope * 0.5
            
        wave = np.clip(wave, -1, 1)
        wave = (wave * 32767).astype(np.int16)
        stereo_wave = np.column_stack((wave, wave))
        
        return pygame.sndarray.make_sound(stereo_wave)
    
    def create_game_over_sound(self, sample_rate):
        """Create game over sound"""
        duration = 1.5
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples)
        
        # Descending notes
        freq_start = 440
        freq_end = 110
        freq = np.linspace(freq_start, freq_end, samples)
        
        wave = np.sin(2 * np.pi * freq * t / sample_rate * np.cumsum(freq))
        envelope = np.exp(-2 * t)
        wave = wave * envelope * 0.5
        
        wave = np.clip(wave, -1, 1)
        wave = (wave * 32767).astype(np.int16)
        stereo_wave = np.column_stack((wave, wave))
        
        return pygame.sndarray.make_sound(stereo_wave)
    
    def play_music(self):
        """Start background music loop"""
        if 'background_music' in self.sounds:
            self.sounds['background_music'].set_volume(self.music_volume)
            self.channels['music'].play(self.sounds['background_music'], loops=-1)
    
    def play_sound(self, sound_name, channel_name='ui'):
        """Play a sound effect"""
        if sound_name in self.sounds and channel_name in self.channels:
            sound = self.sounds[sound_name]
            sound.set_volume(self.sfx_volume)
            if not self.channels[channel_name].get_busy():
                self.channels[channel_name].play(sound)
    
    def update(self):
        """Update audio system - can be used for dynamic music"""
        self.music_timer += 1
        if self.music_timer >= 240:  # Every 4 seconds at 60 FPS
            self.beat_counter += 1
            self.music_timer = 0
    
    def set_music_volume(self, volume):
        self.music_volume = max(0, min(1, volume))
        if 'background_music' in self.sounds:
            self.sounds['background_music'].set_volume(self.music_volume)
    
    def set_sfx_volume(self, volume):
        self.sfx_volume = max(0, min(1, volume))

# Initialize audio engine
audio = AudioEngine()
audio.play_music()

# [Rest of the original game code continues with audio integration...]

# ================== CONFIGURATION ==================
GRID_COLS, GRID_ROWS = 9, 5
CELL_SIZE = 80
GRID_LEFT, GRID_TOP = 120, 140
GROUND_Y = GRID_TOP + GRID_ROWS * CELL_SIZE

# iOS-style touch zones
TOUCH_TOLERANCE = 10
DRAG_THRESHOLD = 5
DOUBLE_TAP_TIME = 300

# Visual Constants
COLORS = {
    'bg': (45, 125, 210),
    'lawn_dark': (34, 139, 34),
    'lawn_light': (50, 205, 50),
    'ui_panel': (60, 60, 60),
    'sun': (255, 223, 0),
    'shadow': (0, 0, 0, 50),
    'health_green': (0, 255, 0),
    'health_yellow': (255, 255, 0),
    'health_red': (255, 0, 0)
}

# ================== GAME STATE ==================
class GameState:
    def __init__(self):
        self.sun = 150
        self.wave = 1
        self.score = 0
        self.selected_plant = None
        self.paused = False
        self.game_over = False
        self.game_over_sound_played = False
        self.drag_info = None
        self.particles = []
        self.floating_texts = []
        self.lawn_mowers = [True] * GRID_ROWS
        self.plant_cooldowns = {}
        self.zombies_spawned = 0
        self.zombies_killed = 0
        self.wave_progress = 0
        self.combo = 0
        self.last_tap_time = 0
        self.last_tap_pos = (0, 0)
        self.sun_spawn_timer = 0
        self.zombie_spawn_timer = 0

game_state = GameState()

# ================== PARTICLE SYSTEM ==================
class Particle:
    def __init__(self, x, y, vx, vy, color, lifetime=30, size=3):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = vx, vy
        self.color = color[:3] if len(color) > 3 else color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size
        self.alive = True
        
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.3
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False
        
    def draw(self):
        if self.lifetime > 0:
            alpha = min(255, int(255 * (self.lifetime / self.max_lifetime)))
            size = max(1, int(self.size * (self.lifetime / self.max_lifetime)))
            surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            color_with_alpha = (*self.color, alpha)
            pygame.draw.circle(surf, color_with_alpha, (size, size), size)
            screen.blit(surf, (int(self.x) - size, int(self.y) - size))

class FloatingText:
    def __init__(self, x, y, text, color=(255, 255, 255), size=24):
        self.x, self.y = float(x), float(y)
        self.text = text
        self.color = color[:3] if len(color) > 3 else color
        self.lifetime = 60
        self.max_lifetime = 60
        self.font = pygame.font.Font(None, size)
        self.alive = True
        
    def update(self):
        self.y -= 1
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False
        
    def draw(self):
        if self.lifetime > 0:
            alpha = min(255, int(255 * (self.lifetime / self.max_lifetime)))
            text_surf = self.font.render(self.text, True, self.color)
            text_surf.set_alpha(alpha)
            screen.blit(text_surf, (int(self.x), int(self.y)))

# ================== ENTITY BASE ==================
class Entity:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.alive = True
        self.animation_frame = 0
        self.animation_speed = 0.1
        
    def kill(self):
        if self.alive:
            self.alive = False
            self.spawn_death_particles()
        
    def spawn_death_particles(self):
        for _ in range(10):
            vx = random.uniform(-3, 3)
            vy = random.uniform(-5, -1)
            color = random.choice([(255, 100, 100), (200, 50, 50)])
            game_state.particles.append(Particle(self.x, self.y, vx, vy, color))
    
    def update(self): 
        self.animation_frame += self.animation_speed
        
    def draw(self): pass
    
    def get_rect(self):
        return pygame.Rect(self.x - 30, self.y - 30, 60, 60)

# ================== PLANTS ==================
class Plant(Entity):
    cost = 50
    recharge = 5.0
    max_health = 300
    name = "Plant"
    color = (0, 255, 0)
    
    def __init__(self, col, row):
        grid_x = GRID_LEFT + col * CELL_SIZE + CELL_SIZE // 2
        grid_y = GRID_TOP + row * CELL_SIZE + CELL_SIZE // 2
        super().__init__(grid_x, grid_y)
        self.col, self.row = col, row
        self.health = self.max_health
        self.cooldown = 0
        self.planted_time = pygame.time.get_ticks()
        self.base_x = float(grid_x)
        
    def update(self):
        super().update()
        self.cooldown = max(0, self.cooldown - 1)
        
    def draw(self):
        shadow_surf = pygame.Surface((50, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 80), (0, 0, 50, 20))
        screen.blit(shadow_surf, (int(self.x) - 25, int(self.y) + 20))
        
        wobble = math.sin(self.animation_frame) * 2
        pygame.draw.circle(screen, self.color, 
                         (int(self.x + wobble), int(self.y)), 25)
        
        if self.health < self.max_health:
            bar_width = 40
            bar_height = 4
            health_pct = max(0, self.health / self.max_health)
            
            color = COLORS['health_green']
            if health_pct < 0.3: color = COLORS['health_red']
            elif health_pct < 0.6: color = COLORS['health_yellow']
            
            bar_x = int(self.x) - 20
            bar_y = int(self.y) - 35
            pygame.draw.rect(screen, (100, 100, 100),
                           (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(screen, color,
                           (bar_x, bar_y, int(bar_width * health_pct), bar_height))
    
    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.kill()
            return True
        return False

class Peashooter(Plant):
    cost = 100
    recharge = 7.5
    name = "Peashooter"
    color = (0, 200, 0)
    
    def __init__(self, col, row):
        super().__init__(col, row)
        self.recoil = 0
    
    def update(self):
        super().update()
        
        if self.recoil > 0:
            self.x = self.base_x - self.recoil
            self.recoil = max(0, self.recoil - 1)
        else:
            self.x = self.base_x
        
        if self.cooldown == 0:
            for zombie in zombies:
                if zombie.row == self.row and zombie.x > self.x:
                    self.shoot()
                    self.cooldown = 90
                    break
    
    def shoot(self):
        projectiles.append(Pea(self.x + 20, self.y, self.row))
        self.recoil = 5
        audio.play_sound('shoot', 'projectiles')

class Sunflower(Plant):
    cost = 50
    recharge = 7.5
    name = "Sunflower"
    color = (255, 255, 0)
    
    def __init__(self, col, row):
        super().__init__(col, row)
        self.sun_timer = random.randint(400, 600)
        
    def update(self):
        super().update()
        self.sun_timer -= 1
        if self.sun_timer <= 0:
            self.produce_sun()
            self.sun_timer = random.randint(500, 700)
    
    def produce_sun(self):
        sun_x = self.x + random.randint(-20, 20)
        sun_y = self.y - 20
        suns.append(Sun(sun_x, sun_y, produced=True))
        game_state.floating_texts.append(
            FloatingText(self.x, self.y - 30, "+25", COLORS['sun'])
        )
        audio.play_sound('sunflower', 'plants')
    
    def draw(self):
        super().draw()
        for i in range(8):
            angle = (self.animation_frame * 2 + i * 45) % 360
            petal_x = self.x + math.cos(math.radians(angle)) * 20
            petal_y = self.y + math.sin(math.radians(angle)) * 20
            pygame.draw.circle(screen, (255, 220, 0), (int(petal_x), int(petal_y)), 8)

class WallNut(Plant):
    cost = 50
    recharge = 30.0
    max_health = 4000
    name = "Wall-nut"
    color = (139, 69, 19)
    
    def draw(self):
        health_pct = max(0, self.health / self.max_health)
        
        if health_pct > 0.66:
            color = self.color
        elif health_pct > 0.33:
            color = (119, 59, 15)
        else:
            color = (89, 39, 9)
            
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), 30)
        
        if health_pct < 0.66:
            pygame.draw.line(screen, (50, 25, 0), 
                           (int(self.x) - 15, int(self.y) - 10), 
                           (int(self.x) + 10, int(self.y) + 15), 2)
        if health_pct < 0.33:
            pygame.draw.line(screen, (50, 25, 0),
                           (int(self.x) + 15, int(self.y) - 10), 
                           (int(self.x) - 10, int(self.y) + 15), 2)

class SnowPea(Plant):
    cost = 175
    recharge = 7.5
    name = "Snow Pea"
    color = (150, 200, 255)
    
    def update(self):
        super().update()
        if self.cooldown == 0:
            for zombie in zombies:
                if zombie.row == self.row and zombie.x > self.x:
                    projectiles.append(IcePea(self.x + 20, self.y, self.row))
                    self.cooldown = 90
                    audio.play_sound('shoot', 'projectiles')
                    break

# ================== ZOMBIES ==================
class Zombie(Entity):
    def __init__(self, row, health=200, speed=0.5):
        lane_y = GRID_TOP + row * CELL_SIZE + CELL_SIZE // 2
        super().__init__(SCREEN_WIDTH + 50, lane_y)
        self.row = row
        self.health = health
        self.max_health = health
        self.speed = speed
        self.base_speed = speed
        self.eating = False
        self.freeze_timer = 0
        self.animation_offset = random.randint(0, 100)
        self.eat_timer = 0
        self.groan_timer = random.randint(300, 600)
        
    def update(self):
        super().update()
        
        # Occasional groaning
        self.groan_timer -= 1
        if self.groan_timer <= 0:
            audio.play_sound('zombie_groan', 'zombies')
            self.groan_timer = random.randint(300, 600)
        
        if self.freeze_timer > 0:
            self.freeze_timer -= 1
            self.speed = self.base_speed * 0.5
        else:
            self.speed = self.base_speed
        
        self.eating = False
        for plant in plants[:]:
            if plant.row == self.row and abs(plant.x - self.x) < 40:
                self.eating = True
                self.eat_timer += 1
                if self.eat_timer >= 30:
                    plant.take_damage(10)
                    self.eat_timer = 0
                    audio.play_sound('zombie_eat', 'zombies')
                break
        
        if not self.eating:
            self.eat_timer = 0
        
        if not self.eating:
            self.x -= self.speed
            
        if self.x < GRID_LEFT - 20:
            self.reached_house()
    
    def reached_house(self):
        if game_state.lawn_mowers[self.row]:
            game_state.lawn_mowers[self.row] = False
            self.kill()
            for z in zombies[:]:
                if z.row == self.row:
                    z.kill()
                    game_state.zombies_killed += 1
                    game_state.score += 10
        else:
            game_state.game_over = True
    
    def draw(self):
        wobble = math.sin((self.animation_frame + self.animation_offset) * 0.5) * 3
        
        shadow_surf = pygame.Surface((40, 15), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 80), (0, 0, 40, 15))
        screen.blit(shadow_surf, (int(self.x) - 20, int(self.y) + 20))
        
        body_color = (100, 50, 20)
        if self.freeze_timer > 0:
            body_color = (150, 150, 255)
            
        pygame.draw.rect(screen, body_color,
                        (int(self.x) - 15, int(self.y - 20 + wobble), 30, 40))
        
        pygame.draw.circle(screen, (80, 40, 20),
                         (int(self.x), int(self.y - 25 + wobble)), 12)
        
        pygame.draw.circle(screen, (255, 0, 0),
                         (int(self.x - 5), int(self.y - 25 + wobble)), 2)
        pygame.draw.circle(screen, (255, 0, 0),
                         (int(self.x + 5), int(self.y - 25 + wobble)), 2)
        
        if self.health < self.max_health:
            bar_width = 30
            bar_height = 3
            health_pct = max(0, self.health / self.max_health)
            
            bar_x = int(self.x) - 15
            bar_y = int(self.y) - 40
            pygame.draw.rect(screen, (100, 0, 0),
                           (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(screen, (255, 0, 0),
                           (bar_x, bar_y, int(bar_width * health_pct), bar_height))
    
    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0 and self.alive:
            self.kill()
            game_state.zombies_killed += 1
            game_state.score += 10
            game_state.combo += 1
            return True
        return False

class ConeheadZombie(Zombie):
    def __init__(self, row):
        super().__init__(row, health=560, speed=0.5)
        
    def draw(self):
        super().draw()
        wobble = math.sin((self.animation_frame + self.animation_offset) * 0.5) * 3
        pygame.draw.polygon(screen, (255, 140, 0),
                           [(int(self.x) - 8, int(self.y - 35 + wobble)),
                            (int(self.x) + 8, int(self.y - 35 + wobble)),
                            (int(self.x), int(self.y - 50 + wobble))])

class BucketheadZombie(Zombie):
    def __init__(self, row):
        super().__init__(row, health=1300, speed=0.5)
        
    def draw(self):
        super().draw()
        wobble = math.sin((self.animation_frame + self.animation_offset) * 0.5) * 3
        pygame.draw.rect(screen, (150, 150, 150),
                        (int(self.x) - 10, int(self.y - 40 + wobble), 20, 15))

# ================== PROJECTILES ==================
class Projectile(Entity):
    def __init__(self, x, y, row):
        super().__init__(x, y)
        self.row = row
        self.damage = 20
        self.speed = 5
        
    def update(self):
        super().update()
        self.x += self.speed
        
        if self.x > SCREEN_WIDTH:
            self.alive = False
            return
            
        for zombie in zombies:
            if zombie.alive and zombie.row == self.row and abs(zombie.x - self.x) < 30:
                self.on_hit(zombie)
                self.alive = False
                break
    
    def on_hit(self, zombie):
        zombie.take_damage(self.damage)
        for _ in range(5):
            vx = random.uniform(-2, 2)
            vy = random.uniform(-3, -1)
            game_state.particles.append(
                Particle(self.x, self.y, vx, vy, (255, 100, 100))
            )

class Pea(Projectile):
    def draw(self):
        pygame.draw.circle(screen, (0, 200, 0), (int(self.x), int(self.y)), 8)

class IcePea(Projectile):
    def __init__(self, x, y, row):
        super().__init__(x, y, row)
        self.damage = 20
        
    def on_hit(self, zombie):
        super().on_hit(zombie)
        zombie.freeze_timer = 180
        
    def draw(self):
        pygame.draw.circle(screen, (150, 200, 255), (int(self.x), int(self.y)), 8)
        if random.random() < 0.3:
            game_state.particles.append(
                Particle(self.x, self.y, random.uniform(-1, 1), random.uniform(-1, 1),
                        (200, 220, 255), lifetime=15, size=2)
            )

# ================== SUN ==================
class Sun(Entity):
    def __init__(self, x, y, produced=False, value=25):
        super().__init__(x, y)
        self.value = value
        self.produced = produced
        self.lifetime = 600 if produced else 800
        self.target_y = y + random.randint(100, 200) if not produced else y
        self.collected = False
        self.pulse = 0
        
    def update(self):
        super().update()
        self.pulse += 0.1
        
        if not self.produced and self.y < self.target_y:
            self.y += 2
            
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False
    
    def collect(self):
        if not self.collected and self.alive:
            self.collected = True
            game_state.sun += self.value
            game_state.floating_texts.append(
                FloatingText(self.x, self.y, f"+{self.value}", COLORS['sun'])
            )
            self.alive = False
            audio.play_sound('sun_collect', 'ui')
            
            for _ in range(10):
                vx = random.uniform(-3, 3)
                vy = random.uniform(-3, 3)
                game_state.particles.append(
                    Particle(self.x, self.y, vx, vy, COLORS['sun'], lifetime=20)
                )
    
    def draw(self):
        if not self.alive:
            return
            
        size = 25 + int(math.sin(self.pulse) * 3)
        
        for i in range(3):
            alpha = 50 - i * 15
            glow_size = size + i * 5
            s = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*COLORS['sun'][:3], alpha), (glow_size, glow_size), glow_size)
            screen.blit(s, (int(self.x) - glow_size, int(self.y) - glow_size))
        
        pygame.draw.circle(screen, COLORS['sun'], (int(self.x), int(self.y)), size)
        pygame.draw.circle(screen, (255, 255, 200), 
                         (int(self.x - size//3), int(self.y - size//3)), size//3)

# ================== UI COMPONENTS ==================
class PlantCard:
    def __init__(self, plant_class, index):
        self.plant_class = plant_class
        self.index = index
        self.x = 180 + index * 65
        self.y = 20
        self.width = 60
        self.height = 80
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
    def can_afford(self):
        return game_state.sun >= self.plant_class.cost
    
    def is_ready(self):
        cooldown_key = self.plant_class.__name__
        if cooldown_key not in game_state.plant_cooldowns:
            return True
        return pygame.time.get_ticks() - game_state.plant_cooldowns[cooldown_key] >= self.plant_class.recharge * 1000
    
    def use(self):
        game_state.plant_cooldowns[self.plant_class.__name__] = pygame.time.get_ticks()
    
    def draw(self):
        if self.can_afford() and self.is_ready():
            color = (100, 200, 100)
        else:
            color = (80, 80, 80)
            
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 2, border_radius=5)
        
        icon_y = self.y + 20
        pygame.draw.circle(screen, self.plant_class.color, 
                         (self.x + self.width // 2, icon_y), 15)
        
        font = pygame.font.Font(None, 20)
        cost_text = font.render(str(self.plant_class.cost), True, (255, 255, 255))
        screen.blit(cost_text, (self.x + self.width // 2 - 10, self.y + 50))
        
        if not self.is_ready():
            cooldown_key = self.plant_class.__name__
            elapsed = pygame.time.get_ticks() - game_state.plant_cooldowns[cooldown_key]
            progress = min(1.0, elapsed / (self.plant_class.recharge * 1000))
            
            overlay_height = int(self.height * (1 - progress))
            s = pygame.Surface((self.width, overlay_height))
            s.set_alpha(128)
            s.fill((0, 0, 0))
            screen.blit(s, (self.x, self.y))
        
        elif not self.can_afford():
            s = pygame.Surface((self.width, self.height))
            s.set_alpha(100)
            s.fill((255, 0, 0))
            screen.blit(s, (self.x, self.y))

# ================== GAME SYSTEMS ==================
def spawn_sun():
    game_state.sun_spawn_timer += 1
    if game_state.sun_spawn_timer >= 300:
        if random.random() < 0.7:
            x = random.randint(100, SCREEN_WIDTH - 100)
            suns.append(Sun(x, -50, produced=False, value=25))
        game_state.sun_spawn_timer = 0

def spawn_zombie():
    if game_state.wave_progress < 100:
        game_state.zombie_spawn_timer += 1
        spawn_rate = max(60, 300 - game_state.wave * 20)
        
        if game_state.zombie_spawn_timer >= spawn_rate:
            if random.random() < 0.8:
                row = random.randint(0, GRID_ROWS - 1)
                
                if game_state.wave >= 5 and random.random() < 0.15:
                    zombie = BucketheadZombie(row)
                elif game_state.wave >= 3 and random.random() < 0.35:
                    zombie = ConeheadZombie(row)
                else:
                    zombie = Zombie(row)
                    
                zombies.append(zombie)
                game_state.zombies_spawned += 1
                game_state.wave_progress = min(100, (game_state.zombies_spawned / (10 + game_state.wave * 5)) * 100)
            
            game_state.zombie_spawn_timer = 0

def check_wave_complete():
    if game_state.wave_progress >= 100 and len(zombies) == 0:
        game_state.wave += 1
        game_state.wave_progress = 0
        game_state.zombies_spawned = 0
        game_state.sun += 100
        game_state.floating_texts.append(
            FloatingText(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2,
                        f"Wave {game_state.wave}!", (255, 255, 255), size=48)
        )
        audio.play_sound('wave_complete', 'ui')
        update_available_plants()

def update_available_plants():
    global plant_cards
    available_plant_classes = [Peashooter, Sunflower, WallNut]
    if game_state.wave >= 2:
        available_plant_classes.append(SnowPea)
    
    plant_cards = [PlantCard(plant_class, i) for i, plant_class in enumerate(available_plant_classes)]

def draw_lawn():
    for row in range(GRID_ROWS):
        color = COLORS['lawn_dark'] if row % 2 == 0 else COLORS['lawn_light']
        pygame.draw.rect(screen, color,
                        (GRID_LEFT, GRID_TOP + row * CELL_SIZE, 
                         GRID_COLS * CELL_SIZE, CELL_SIZE))
    
    for row in range(GRID_ROWS + 1):
        pygame.draw.line(screen, (0, 100, 0),
                        (GRID_LEFT, GRID_TOP + row * CELL_SIZE),
                        (GRID_LEFT + GRID_COLS * CELL_SIZE, GRID_TOP + row * CELL_SIZE), 1)
    
    for col in range(GRID_COLS + 1):
        pygame.draw.line(screen, (0, 100, 0),
                        (GRID_LEFT + col * CELL_SIZE, GRID_TOP),
                        (GRID_LEFT + col * CELL_SIZE, GRID_TOP + GRID_ROWS * CELL_SIZE), 1)
    
    for row in range(GRID_ROWS):
        if game_state.lawn_mowers[row]:
            mower_y = GRID_TOP + row * CELL_SIZE + CELL_SIZE // 2
            pygame.draw.rect(screen, (200, 0, 0),
                           (GRID_LEFT - 40, mower_y - 15, 30, 30))
            pygame.draw.circle(screen, (100, 100, 100),
                             (GRID_LEFT - 35, mower_y + 10), 5)
            pygame.draw.circle(screen, (100, 100, 100),
                             (GRID_LEFT - 15, mower_y + 10), 5)

def draw_ui():
    pygame.draw.rect(screen, COLORS['ui_panel'], (0, 0, SCREEN_WIDTH, 110))
    
    pygame.draw.circle(screen, COLORS['sun'], (60, 60), 30)
    font = pygame.font.Font(None, 36)
    sun_text = font.render(str(game_state.sun), True, (255, 255, 255))
    screen.blit(sun_text, (100, 50))
    
    wave_text = font.render(f"Wave {game_state.wave}", True, (255, 255, 255))
    screen.blit(wave_text, (SCREEN_WIDTH - 150, 20))
    
    pygame.draw.rect(screen, (100, 100, 100),
                    (SCREEN_WIDTH - 200, 60, 150, 20))
    progress_width = int(150 * min(100, game_state.wave_progress) / 100)
    pygame.draw.rect(screen, (0, 255, 0),
                    (SCREEN_WIDTH - 200, 60, progress_width, 20))
    
    score_font = pygame.font.Font(None, 24)
    score_text = score_font.render(f"Score: {game_state.score}", True, (255, 255, 255))
    screen.blit(score_text, (SCREEN_WIDTH // 2 - 50, 80))

def handle_input():
    mouse_pos = pygame.mouse.get_pos()
    mouse_clicked = pygame.mouse.get_pressed()[0]
    
    if mouse_clicked:
        for sun in suns[:]:
            if sun.alive and sun.get_rect().collidepoint(mouse_pos):
                sun.collect()
                return
        
        if game_state.selected_plant is None:
            for card in plant_cards:
                if card.rect.collidepoint(mouse_pos):
                    if card.can_afford() and card.is_ready():
                        game_state.selected_plant = card
                        return
        
        if game_state.selected_plant:
            col = (mouse_pos[0] - GRID_LEFT) // CELL_SIZE
            row = (mouse_pos[1] - GRID_TOP) // CELL_SIZE
            
            if 0 <= col < GRID_COLS and 0 <= row < GRID_ROWS:
                cell_empty = True
                for plant in plants:
                    if plant.alive and plant.col == col and plant.row == row:
                        cell_empty = False
                        break
                
                if cell_empty:
                    new_plant = game_state.selected_plant.plant_class(col, row)
                    plants.append(new_plant)
                    game_state.sun -= game_state.selected_plant.plant_class.cost
                    game_state.selected_plant.use()
                    game_state.selected_plant = None
                    audio.play_sound('plant_place', 'plants')
                    
                    for _ in range(10):
                        vx = random.uniform(-2, 2)
                        vy = random.uniform(-3, 0)
                        game_state.particles.append(
                            Particle(new_plant.x, new_plant.y, vx, vy, (0, 255, 0), lifetime=20)
                        )
            else:
                game_state.selected_plant = None

def cleanup_entities():
    global plants, zombies, projectiles, suns
    plants = [p for p in plants if p.alive]
    zombies = [z for z in zombies if z.alive]
    projectiles = [p for p in projectiles if p.alive]
    suns = [s for s in suns if s.alive]
    game_state.particles = [p for p in game_state.particles if p.alive]
    game_state.floating_texts = [t for t in game_state.floating_texts if t.alive]

# ================== INITIALIZATION ==================
plants = []
zombies = []
projectiles = []
suns = []

update_available_plants()

# ================== MAIN GAME LOOP ==================
running = True
font_big = pygame.font.Font(None, 72)
font_medium = pygame.font.Font(None, 36)

while running:
    dt = clock.tick(60) / 1000.0
    
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running = False
            elif event.key == K_SPACE:
                game_state.paused = not game_state.paused
            elif event.key == K_r and game_state.game_over:
                game_state = GameState()
                plants.clear()
                zombies.clear()
                projectiles.clear()
                suns.clear()
                update_available_plants()
                audio.play_music()
            elif event.key == K_m:
                # Mute/unmute music
                if audio.music_volume > 0:
                    audio.set_music_volume(0)
                else:
                    audio.set_music_volume(0.7)
    
    if not game_state.paused and not game_state.game_over:
        handle_input()
        spawn_sun()
        spawn_zombie()
        check_wave_complete()
        
        for plant in plants:
            plant.update()
        for zombie in zombies:
            zombie.update()
        for projectile in projectiles:
            projectile.update()
        for sun in suns:
            sun.update()
        for particle in game_state.particles:
            particle.update()
        for text in game_state.floating_texts:
            text.update()
        
        cleanup_entities()
        audio.update()
    
    screen.fill(COLORS['bg'])
    draw_lawn()
    
    all_entities = plants + zombies
    all_entities.sort(key=lambda e: e.y)
    
    for entity in all_entities:
        if entity.alive:
            entity.draw()
    
    for projectile in projectiles:
        projectile.draw()
    
    for sun in suns:
        sun.draw()
    
    for particle in game_state.particles:
        particle.draw()
    
    for text in game_state.floating_texts:
        text.draw()
    
    draw_ui()
    
    for card in plant_cards:
        card.draw()
    
    if game_state.selected_plant:
        mouse_pos = pygame.mouse.get_pos()
        preview_surf = pygame.Surface((60, 60), pygame.SRCALPHA)
        pygame.draw.circle(preview_surf, (*game_state.selected_plant.plant_class.color, 128),
                         (30, 30), 25)
        screen.blit(preview_surf, (mouse_pos[0] - 30, mouse_pos[1] - 30))
    
    if game_state.paused:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        pause_text = font_big.render("PAUSED", True, (255, 255, 255))
        text_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        screen.blit(pause_text, text_rect)
        
        resume_text = font_medium.render("Press SPACE to resume", True, (255, 255, 255))
        text_rect = resume_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        screen.blit(resume_text, text_rect)
        
        mute_text = font_medium.render("Press M to toggle music", True, (255, 255, 255))
        text_rect = mute_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
        screen.blit(mute_text, text_rect)
    
    if game_state.game_over:
        if not game_state.game_over_sound_played:
            audio.play_sound('game_over', 'ui')
            game_state.game_over_sound_played = True
            
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        game_over_text = font_big.render("GAME OVER", True, (255, 0, 0))
        text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        screen.blit(game_over_text, text_rect)
        
        score_text = font_medium.render(f"Final Score: {game_state.score}", True, (255, 255, 255))
        text_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(score_text, text_rect)
        
        zombies_text = font_medium.render(f"Zombies Killed: {game_state.zombies_killed}", True, (255, 255, 255))
        text_rect = zombies_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
        screen.blit(zombies_text, text_rect)
        
        wave_text = font_medium.render(f"Waves Survived: {game_state.wave - 1}", True, (255, 255, 255))
        text_rect = wave_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
        screen.blit(wave_text, text_rect)
        
        restart_text = font_medium.render("Press R to restart", True, (255, 255, 255))
        text_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120))
        screen.blit(restart_text, text_rect)
    
    pygame.display.flip()

pygame.quit()

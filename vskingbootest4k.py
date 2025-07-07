import pygame, sys, math, random, numpy as np
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

###############################################################################
# CONSTANTS & GLOBAL STATE
###############################################################################
FPS = 60
TILE = 32
W, H = 24*TILE, 18*TILE
GRAVITY = 0.75
LUIGI_ACCEL = 1.2
LUIGI_FRIC = 0.84
LUIGI_JUMP_V = -13.5

screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("TEAM SPECIALEMU AGI Division Presents: Luigi's Mansion 3 - King Boo")
clock = pygame.time.Clock()

# Generate Luigi's Mansion 3 boss music vibes
def generate_boss_music():
    sample_rate = 22050
    duration = 2.0
    samples = int(sample_rate * duration)
    
    # Create ominous bass line
    bass_freq = [55, 0, 55, 0, 58.27, 0, 51.91, 0]  # A1, rest, A1, rest, Bb1, rest, G#1, rest
    bass = np.zeros(samples)
    
    for i, freq in enumerate(bass_freq):
        start = int(i * samples / 8)
        end = int((i + 1) * samples / 8)
        if freq > 0 and end <= samples:  # Bounds check
            t = np.linspace(0, (end-start)/sample_rate, end-start)
            bass[start:end] = 0.3 * np.sin(2 * np.pi * freq * t) * np.exp(-t * 2)
    
    # Add spooky high strings
    strings = np.zeros(samples)
    string_freqs = [440, 466.16, 440, 415.30]  # A4, Bb4, A4, G#4
    
    for i, freq in enumerate(string_freqs):
        start = int(i * samples / 4)
        end = int((i + 1) * samples / 4)
        if end <= samples:  # Bounds check
            t = np.linspace(0, (end-start)/sample_rate, end-start)
            strings[start:end] = 0.1 * np.sin(2 * np.pi * freq * t) * (1 + 0.2 * np.sin(8 * np.pi * t))
    
    # Add percussion hits
    percussion = np.zeros(samples)
    hit_times = [0, 0.5, 1.0, 1.5]
    
    for hit_time in hit_times:
        hit_sample = int(hit_time * sample_rate)
        if hit_sample < samples - 1000:
            t = np.linspace(0, 0.1, 1000)
            noise = np.random.normal(0, 0.15, 1000) * np.exp(-t * 30)
            percussion[hit_sample:hit_sample+1000] += noise
    
    # Mix everything
    music = bass + strings + percussion
    music = np.clip(music * 32767, -32767, 32767).astype(np.int16)
    music_stereo = np.column_stack((music, music))  # Proper stereo format
    
    return pygame.sndarray.make_sound(np.ascontiguousarray(music_stereo))

# Generate sound effects
def generate_thunder():
    samples = 8000
    thunder = np.random.normal(0, 0.3, samples) * np.exp(-np.linspace(0, 4, samples))
    thunder = np.clip(thunder * 32767, -32767, 32767).astype(np.int16)
    thunder_stereo = np.column_stack((thunder, thunder))
    return pygame.sndarray.make_sound(np.ascontiguousarray(thunder_stereo))

def generate_slam():
    samples = 4000
    t = np.linspace(0, 0.1, samples)
    slam = 0.5 * np.sin(2 * np.pi * 50 * t) * np.exp(-t * 20)
    slam += np.random.normal(0, 0.1, samples) * np.exp(-t * 30)
    slam = np.clip(slam * 32767, -32767, 32767).astype(np.int16)
    slam_stereo = np.column_stack((slam, slam))
    return pygame.sndarray.make_sound(np.ascontiguousarray(slam_stereo))

# Sound initialization
try:
    boss_music = generate_boss_music()
    thunder_sfx = generate_thunder()
    slam_sfx = generate_slam()
    sound_enabled = True
except Exception as e:
    print(f"Sound initialization failed: {e}")
    sound_enabled = False

# Arena layout
arena_floor = [[1]*24 for _ in range(18)]
for j in range(4, 15):
    for i in range(2, 22):
        arena_floor[j][i] = 0

# Destructible pillars
pillars = []
for x in [6, 12, 18]:
    pillars.append({
        'x': x*TILE, 'y': 12*TILE,
        'health': 3, 'destroyed': False
    })

# Electric panels
electric_panels = []
for i in range(4, 20, 4):
    electric_panels.append({
        'x': i*TILE, 'y': 14*TILE,
        'active': False, 'timer': 0,
        'w': TILE, 'h': TILE
    })

# Luigi state
luigi = {
    'x': 4*TILE, 'y': 12*TILE,
    'vx': 0.0, 'vy': 0.0,
    'w': 24, 'h': 36,
    'on_ground': False,
    'face': 1,
    'health': 5,
    'invuln_timer': 0,
    'portrait_trapped': False,
    'portrait_timer': 0,
    'grabbing': False,
    'slam_power': 0
}

# King Boo state
king_boo = {
    'x': 18*TILE, 'y': 8*TILE,
    'w': 96, 'h': 96,
    'health': 9,  # 3 per phase
    'phase': 1,
    'state': 'floating',  # floating, tongue_attack, vulnerable, lightning, spikefall, clone_attack
    'state_timer': 0,
    'tongue_x': 0, 'tongue_y': 0,
    'tongue_extended': False,
    'float_y': 8*TILE,
    'float_timer': 0.0,
    'rage_mode': False,
    'attack_cooldown': 0
}

# Projectiles
spike_balls = []
lightning_strikes = []
king_boo_clones = []
thrown_bombs = []

# Particles
particles = []

# Start music
if sound_enabled:
    boss_music.play(-1)

###############################################################################
# UTILITY FUNCTIONS
###############################################################################
def rect(obj):
    return pygame.Rect(int(obj['x']), int(obj['y']), obj['w'], obj['h'])

def add_particle(x, y, vx, vy, color, life):
    particles.append({
        'x': x, 'y': y, 'vx': vx, 'vy': vy,
        'color': color, 'life': life, 'max_life': life
    })

def screen_shake(intensity):
    return random.randint(-intensity, intensity), random.randint(-intensity, intensity)

def spawn_spike_ball(x, y, vx, vy):
    spike_balls.append({
        'x': x, 'y': y, 'vx': vx, 'vy': vy,
        'bounces': 0, 'w': 24, 'h': 24
    })

def spawn_lightning(x):
    lightning_strikes.append({
        'x': x, 'y': 0,
        'telegraph_timer': 60,
        'strike_timer': 0,
        'active': False,
        'w': 48, 'h': H
    })

def spawn_clones():
    clone_count = 2 if king_boo['phase'] == 2 else 4
    positions = []
    for i in range(clone_count):
        angle = (2 * math.pi * i) / clone_count
        x = 12*TILE + math.cos(angle) * 6*TILE
        y = 9*TILE + math.sin(angle) * 3*TILE
        positions.append((x, y))
    
    for x, y in positions:
        king_boo_clones.append({
            'x': x, 'y': y, 'w': 96, 'h': 96,
            'is_real': False, 'alpha': 180
        })
    
    # Make one random clone the real one
    if king_boo_clones:
        real_index = random.randint(0, len(king_boo_clones)-1)
        king_boo_clones[real_index]['is_real'] = True
        king_boo_clones[real_index]['alpha'] = 255

###############################################################################
# DRAWING FUNCTIONS
###############################################################################
def draw_arena():
    # Dark spooky background
    for j in range(H//TILE):
        color_fade = int(20 + j * 3)
        pygame.draw.rect(screen, (color_fade, 0, color_fade + 10), (0, j*TILE, W, TILE))
    
    # Floor tiles
    for j in range(18):
        for i in range(24):
            if arena_floor[j][i] == 1:
                color = (60, 40, 80) if (i+j) % 2 == 0 else (50, 30, 70)
                pygame.draw.rect(screen, color, (i*TILE, j*TILE, TILE, TILE))
                pygame.draw.rect(screen, (30, 20, 40), (i*TILE, j*TILE, TILE, TILE), 2)

def draw_luigi():
    x, y = int(luigi['x']), int(luigi['y'])
    
    # Only draw if not invulnerable or on visible frame
    if luigi['invuln_timer'] == 0 or luigi['invuln_timer'] % 6 < 3:
        # Hat
        pygame.draw.ellipse(screen, (0, 140, 0), (x+4, y, 16, 10))
        pygame.draw.circle(screen, (255, 255, 255), (x+12, y+5), 6)
        font = pygame.font.Font(None, 16)
        text = font.render("L", True, (0, 100, 0))
        screen.blit(text, (x+9, y+1))
        
        # Face
        pygame.draw.ellipse(screen, (255, 220, 180), (x+4, y+8, 16, 16))
        
        # Mustache
        pygame.draw.ellipse(screen, (60, 40, 20), (x+4, y+18, 7, 4))
        pygame.draw.ellipse(screen, (60, 40, 20), (x+13, y+18, 7, 4))
        
        # Body
        pygame.draw.rect(screen, (0, 0, 200), (x+6, y+24, 12, 12))
        
        # If grabbing, show vacuum effect
        if luigi['grabbing']:
            for i in range(5):
                px = x + 24 + i * 8
                py = y + 18 + random.randint(-4, 4)
                pygame.draw.circle(screen, (200, 200, 255), (px, py), 3-i//2)

def draw_king_boo():
    x, y = int(king_boo['x']), int(king_boo['y'])
    
    # Only draw if on screen
    if x < -100 or x > W:
        return
    
    # Main body (white ghost form)
    pygame.draw.circle(screen, (240, 240, 255), (x+48, y+48), 48)
    pygame.draw.circle(screen, (200, 200, 255), (x+48, y+48), 48, 4)
    
    # Crown
    crown_points = [
        (x+28, y+10), (x+35, y), (x+42, y+10),
        (x+48, y), (x+54, y+10), (x+61, y), (x+68, y+10),
        (x+68, y+20), (x+28, y+20)
    ]
    pygame.draw.polygon(screen, (255, 215, 0), crown_points)
    pygame.draw.circle(screen, (255, 0, 255), (x+48, y+5), 4)
    
    # Face
    eye_offset = 0
    if king_boo['state'] == 'tongue_attack':
        eye_offset = 5
    
    # Eyes
    pygame.draw.ellipse(screen, (255, 0, 0), (x+25, y+35+eye_offset, 20, 25))
    pygame.draw.ellipse(screen, (255, 0, 0), (x+51, y+35+eye_offset, 20, 25))
    pygame.draw.ellipse(screen, (0, 0, 0), (x+30, y+40+eye_offset, 10, 15))
    pygame.draw.ellipse(screen, (0, 0, 0), (x+56, y+40+eye_offset, 10, 15))
    
    # Mouth
    if king_boo['state'] == 'tongue_attack':
        # Open mouth with tongue
        pygame.draw.ellipse(screen, (100, 0, 100), (x+28, y+65, 40, 25))
        if king_boo['tongue_extended']:
            # Draw extended tongue
            tongue_end_x = int(king_boo['tongue_x'])
            tongue_end_y = int(king_boo['tongue_y'])
            pygame.draw.line(screen, (180, 0, 180), (x+48, y+75), (tongue_end_x, tongue_end_y), 12)
            pygame.draw.circle(screen, (200, 0, 200), (tongue_end_x, tongue_end_y), 8)
    else:
        # Evil grin
        pygame.draw.arc(screen, (100, 0, 100), (x+28, y+60, 40, 20), 0, math.pi, 4)
    
    # Health bar
    bar_width = 200
    bar_x = W//2 - bar_width//2
    bar_y = 20
    pygame.draw.rect(screen, (100, 0, 0), (bar_x-2, bar_y-2, bar_width+4, 24))
    
    for i in range(king_boo['health']):
        segment_width = bar_width // 9
        color = (255, 0, 0) if i < 3 else (255, 165, 0) if i < 6 else (255, 255, 0)
        pygame.draw.rect(screen, color, (bar_x + i*segment_width, bar_y, segment_width-2, 20))
    
    # Phase indicator
    phase_text = f"PHASE {king_boo['phase']}"
    if king_boo['rage_mode']:
        phase_text += " - RAGE!"
    font = pygame.font.Font(None, 24)
    text = font.render(phase_text, True, (255, 255, 255))
    screen.blit(text, (W//2 - text.get_width()//2, bar_y + 30))

def draw_effects():
    # Spike balls
    for spike in spike_balls:
        x, y = int(spike['x']), int(spike['y'])
        pygame.draw.circle(screen, (80, 80, 80), (x+12, y+12), 12)
        for angle in range(0, 360, 45):
            sx = int(x + 12 + math.cos(math.radians(angle)) * 12)
            sy = int(y + 12 + math.sin(math.radians(angle)) * 12)
            pygame.draw.polygon(screen, (160, 160, 160), 
                [(sx-2, sy-2), (sx+2, sy-2), (sx, sy-6)])
        # Fire effect
        pygame.draw.circle(screen, (255, 100, 0), (x+12, y+12), 8)
        pygame.draw.circle(screen, (255, 200, 0), (x+12, y+12), 5)
    
    # Lightning strikes
    for lightning in lightning_strikes:
        x = int(lightning['x'])
        if lightning['telegraph_timer'] > 0:
            # Draw telegraph circle
            pygame.draw.circle(screen, (200, 0, 200), (x+24, 14*TILE), 24, 3)
        elif lightning['active']:
            # Draw lightning bolt
            points = []
            for i in range(0, H, 20):
                offset = random.randint(-10, 10)
                points.append((x + 24 + offset, i))
            for i in range(len(points)-1):
                pygame.draw.line(screen, (255, 255, 100), points[i], points[i+1], 5)
                pygame.draw.line(screen, (255, 255, 255), points[i], points[i+1], 2)
    
    # Clones
    for clone in king_boo_clones:
        x, y = int(clone['x']), int(clone['y'])
        # Draw with transparency
        surf = pygame.Surface((96, 96), pygame.SRCALPHA)
        
        # Draw clone body
        alpha = clone['alpha']
        pygame.draw.circle(surf, (240, 240, 255, alpha), (48, 48), 48)
        pygame.draw.circle(surf, (200, 200, 255, alpha), (48, 48), 48, 4)
        
        if clone['is_real']:
            # Add sparkle effect for real one
            for i in range(3):
                sx = 48 + random.randint(-20, 20)
                sy = 48 + random.randint(-20, 20)
                pygame.draw.circle(surf, (255, 255, 100), (sx, sy), 2)
        
        screen.blit(surf, (x, y))
    
    # Pillars
    for pillar in pillars:
        if not pillar['destroyed']:
            x, y = int(pillar['x']), int(pillar['y'])
            color = (100, 100, 100) if pillar['health'] == 3 else (80, 80, 80) if pillar['health'] == 2 else (60, 60, 60)
            pygame.draw.rect(screen, color, (x, y-64, 32, 64))
            # Cracks
            if pillar['health'] < 3:
                pygame.draw.line(screen, (40, 40, 40), (x+8, y-50), (x+16, y-30), 2)
            if pillar['health'] < 2:
                pygame.draw.line(screen, (40, 40, 40), (x+24, y-60), (x+20, y-20), 2)
    
    # Electric panels
    for panel in electric_panels:
        if panel['active']:
            x, y = int(panel['x']), int(panel['y'])
            # Electric effect
            pygame.draw.rect(screen, (100, 100, 255), (x, y, TILE, TILE))
            for i in range(3):
                sx = x + random.randint(0, TILE)
                sy = y + random.randint(-20, 0)
                ex = x + random.randint(0, TILE)
                ey = y
                pygame.draw.line(screen, (200, 200, 255), (sx, sy), (ex, ey), 2)
    
    # Particles
    for p in particles[:]:
        radius = max(1, int(3 * p['life'] / p['max_life']))
        pygame.draw.circle(screen, p['color'], (int(p['x']), int(p['y'])), radius)
        p['x'] += p['vx']
        p['y'] += p['vy']
        p['vy'] += 0.2
        p['life'] -= 1
        if p['life'] <= 0:
            particles.remove(p)
    
    # Portrait trap effect
    if luigi['portrait_trapped']:
        # Draw golden frame
        frame_x = W//2 - 60
        frame_y = H//2 - 80
        pygame.draw.rect(screen, (255, 215, 0), (frame_x-10, frame_y-10, 120, 160), 5)
        pygame.draw.rect(screen, (100, 100, 100), (frame_x, frame_y, 100, 140))
        # Draw trapped Luigi
        pygame.draw.ellipse(screen, (0, 100, 0), (frame_x+42, frame_y+30, 16, 10))
        pygame.draw.ellipse(screen, (255, 220, 180), (frame_x+42, frame_y+38, 16, 16))
        # Shake indicator
        shake_text = "SHAKE TO ESCAPE!"
        font = pygame.font.Font(None, 24)
        text = font.render(shake_text, True, (255, 255, 0))
        screen.blit(text, (W//2 - text.get_width()//2, frame_y + 170))

###############################################################################
# GAME LOGIC
###############################################################################
def move_luigi():
    if luigi['portrait_trapped']:
        return
    
    keys = pygame.key.get_pressed()
    
    # Movement
    luigi['vx'] *= LUIGI_FRIC
    if keys[pygame.K_LEFT]:
        luigi['vx'] -= LUIGI_ACCEL
        luigi['face'] = -1
    if keys[pygame.K_RIGHT]:
        luigi['vx'] += LUIGI_ACCEL
        luigi['face'] = 1
    luigi['vx'] = max(-5, min(5, luigi['vx']))
    
    # Jumping
    if keys[pygame.K_z] and luigi['on_ground']:
        luigi['vy'] = LUIGI_JUMP_V
    
    # Vacuum/grab
    luigi['grabbing'] = keys[pygame.K_x] and king_boo['state'] == 'vulnerable'
    
    # Physics
    luigi['vy'] += GRAVITY
    luigi['vy'] = min(12, luigi['vy'])
    
    # Update position
    luigi['x'] += luigi['vx']
    luigi['y'] += luigi['vy']
    
    # Floor collision
    luigi['on_ground'] = False
    if luigi['y'] + luigi['h'] > 14*TILE:
        luigi['y'] = 14*TILE - luigi['h']
        luigi['vy'] = 0
        luigi['on_ground'] = True
    
    # Arena bounds
    luigi['x'] = max(2*TILE, min(luigi['x'], 21*TILE))
    
    # Invulnerability timer
    if luigi['invuln_timer'] > 0:
        luigi['invuln_timer'] -= 1

def update_king_boo():
    # Float animation
    king_boo['float_timer'] += 0.05
    if king_boo['state'] != 'vulnerable':
        king_boo['y'] = king_boo['float_y'] + math.sin(king_boo['float_timer']) * 20
    
    # State machine
    king_boo['state_timer'] += 1
    
    if king_boo['state'] == 'floating':
        # Choose next attack
        if king_boo['attack_cooldown'] > 0:
            king_boo['attack_cooldown'] -= 1
        else:
            attacks = ['tongue_attack', 'spikefall', 'lightning']
            if king_boo['phase'] >= 2:
                attacks.append('clone_attack')
            
            king_boo['state'] = random.choice(attacks)
            king_boo['state_timer'] = 0
            
            # Reduce cooldown in rage mode
            cooldown = 120 if not king_boo['rage_mode'] else 80
            king_boo['attack_cooldown'] = cooldown
    
    elif king_boo['state'] == 'tongue_attack':
        if king_boo['state_timer'] < 60:
            # Telegraph
            king_boo['tongue_x'] = luigi['x'] + luigi['w']//2
            king_boo['tongue_y'] = luigi['y'] + luigi['h']//2
        elif king_boo['state_timer'] == 60:
            # Extend tongue
            king_boo['tongue_extended'] = True
            if sound_enabled:
                slam_sfx.play()
            # Add particles at impact
            for i in range(10):
                add_particle(king_boo['tongue_x'], king_boo['tongue_y'],
                           random.uniform(-3, 3), random.uniform(-5, -1),
                           (200, 0, 200), 30)
        elif king_boo['state_timer'] > 60 and king_boo['state_timer'] < 180:
            # Check if tongue hit ground
            if king_boo['tongue_y'] > 13*TILE:
                king_boo['state'] = 'vulnerable'
                king_boo['state_timer'] = 0
        else:
            # Retract
            king_boo['tongue_extended'] = False
            king_boo['state'] = 'floating'
    
    elif king_boo['state'] == 'vulnerable':
        # Can be grabbed
        if luigi['grabbing'] and rect(luigi).colliderect(rect(king_boo)):
            luigi['slam_power'] += 2
            if luigi['slam_power'] >= 100:
                # Slam!
                king_boo['health'] -= 1
                luigi['slam_power'] = 0
                if sound_enabled:
                    slam_sfx.play()
                
                # Knockback and particles
                for i in range(20):
                    add_particle(king_boo['x']+48, king_boo['y']+48,
                               random.uniform(-5, 5), random.uniform(-5, 5),
                               (255, 255, 255), 40)
                
                # Check phase transition
                if king_boo['health'] == 6:
                    king_boo['phase'] = 2
                elif king_boo['health'] == 3:
                    king_boo['phase'] = 3
                    king_boo['rage_mode'] = True
                
                king_boo['state'] = 'floating'
                king_boo['tongue_extended'] = False
        
        if king_boo['state_timer'] > 180:
            king_boo['state'] = 'floating'
            king_boo['tongue_extended'] = False
            luigi['slam_power'] = 0
    
    elif king_boo['state'] == 'spikefall':
        # Spawn spike balls at intervals
        interval = 15 if not king_boo['rage_mode'] else 10
        if king_boo['state_timer'] % interval == 0:
            count = 4 if king_boo['phase'] == 1 else 6 if king_boo['phase'] == 2 else 8
            for i in range(count):
                x = king_boo['x'] + 48 + random.uniform(-40, 40)
                y = king_boo['y'] + 96
                vx = random.uniform(-3, 3)
                vy = random.uniform(2, 4)
                spawn_spike_ball(x, y, vx, vy)
        
        if king_boo['state_timer'] > 90:
            king_boo['state'] = 'floating'
    
    elif king_boo['state'] == 'lightning':
        if king_boo['state_timer'] == 1:
            # Spawn lightning strikes
            count = 3 if king_boo['phase'] == 1 else 5 if king_boo['phase'] == 2 else 8
            for i in range(count):
                x = random.randint(3, 20) * TILE
                spawn_lightning(x)
        
        if king_boo['state_timer'] > 120:
            king_boo['state'] = 'floating'
    
    elif king_boo['state'] == 'clone_attack':
        if king_boo['state_timer'] == 1:
            spawn_clones()
            king_boo['x'] = -200  # Hide real one
        
        if king_boo['state_timer'] > 180:
            # Return and clear clones
            king_boo['x'] = 12*TILE
            king_boo_clones.clear()
            king_boo['state'] = 'floating'

def update_projectiles():
    # Spike balls
    for spike in spike_balls[:]:
        spike['x'] += spike['vx']
        spike['y'] += spike['vy']
        spike['vy'] += GRAVITY
        
        # Floor bounce
        if spike['y'] + spike['h'] > 14*TILE:
            spike['y'] = 14*TILE - spike['h']
            spike['vy'] = -spike['vy'] * 0.7
            spike['bounces'] += 1
            if spike['bounces'] >= 2:
                spike_balls.remove(spike)
                continue
        
        # Wall bounce
        if spike['x'] < 2*TILE or spike['x'] + spike['w'] > 22*TILE:
            spike['vx'] = -spike['vx']
        
        # Hit Luigi
        if rect(spike).colliderect(rect(luigi)) and luigi['invuln_timer'] == 0:
            damage_luigi()
            if spike in spike_balls:  # Check if still in list
                spike_balls.remove(spike)
    
    # Lightning
    for lightning in lightning_strikes[:]:
        if lightning['telegraph_timer'] > 0:
            lightning['telegraph_timer'] -= 1
            if lightning['telegraph_timer'] == 0:
                lightning['active'] = True
                lightning['strike_timer'] = 20
                if sound_enabled:
                    thunder_sfx.play()
        elif lightning['active']:
            lightning['strike_timer'] -= 1
            # Check hit
            if rect(lightning).colliderect(rect(luigi)) and luigi['invuln_timer'] == 0:
                damage_luigi()
            if lightning['strike_timer'] <= 0:
                lightning_strikes.remove(lightning)
    
    # Update electric panels
    for panel in electric_panels:
        panel['timer'] += 1
        if panel['timer'] % 120 == 0:
            panel['active'] = not panel['active']
        
        if panel['active'] and rect(panel).colliderect(rect(luigi)) and luigi['invuln_timer'] == 0:
            damage_luigi()

def damage_luigi():
    luigi['health'] -= 1
    luigi['invuln_timer'] = 120
    
    if luigi['health'] <= 0:
        luigi['portrait_trapped'] = True
        luigi['portrait_timer'] = 300

def update_portrait_trap():
    if not luigi['portrait_trapped']:
        return False
    
    keys = pygame.key.get_pressed()
    # Mash left/right to escape
    if keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]:
        luigi['portrait_timer'] -= 5
    
    luigi['portrait_timer'] -= 1
    
    if luigi['portrait_timer'] <= 0:
        # Game over
        return True
    
    if luigi['portrait_timer'] < 200:  # Escaped!
        luigi['portrait_trapped'] = False
        luigi['health'] = 3
        luigi['x'] = 12*TILE
        luigi['y'] = 12*TILE
    
    return False

###############################################################################
# MAIN GAME LOOP
###############################################################################
running = True
shake_x, shake_y = 0, 0

# Intro text
font = pygame.font.Font(None, 36)
intro_timer = 180

while running:
    # Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # Update
    if intro_timer > 0:
        intro_timer -= 1
        screen.fill((0, 0, 0))
        text = font.render("TEAM SPECIALEMU AGI Division Presents", True, (255, 255, 255))
        screen.blit(text, (W//2 - text.get_width()//2, H//2 - 50))
        if intro_timer < 90:
            text2 = font.render("LUIGI'S MANSION 3: KING BOO", True, (0, 255, 0))
            screen.blit(text2, (W//2 - text2.get_width()//2, H//2))
    else:
        # Game logic
        move_luigi()
        update_king_boo()
        update_projectiles()
        
        if update_portrait_trap():
            # Game over
            screen.fill((0, 0, 0))
            text = font.render("GAME OVER - TRAPPED FOREVER!", True, (255, 0, 0))
            screen.blit(text, (W//2 - text.get_width()//2, H//2))
            pygame.display.flip()
            pygame.time.wait(3000)
            running = False
            continue
        
        # Check win
        if king_boo['health'] <= 0:
            screen.fill((0, 0, 0))
            text = font.render("KING BOO DEFEATED!", True, (0, 255, 0))
            screen.blit(text, (W//2 - text.get_width()//2, H//2 - 20))
            text2 = font.render("LUIGI WINS!", True, (255, 255, 255))
            screen.blit(text2, (W//2 - text2.get_width()//2, H//2 + 20))
            pygame.display.flip()
            pygame.time.wait(3000)
            running = False
            continue
        
        # Screen shake on hits
        if luigi['invuln_timer'] == 119:
            shake_x, shake_y = screen_shake(10)
        else:
            shake_x = shake_x * 0.9
            shake_y = shake_y * 0.9
        
        # Draw everything
        screen.fill((20, 0, 30))
        
        # Apply screen shake if needed
        if abs(shake_x) > 0.1 or abs(shake_y) > 0.1:
            # Create temporary surface for shake effect
            temp_surface = pygame.Surface((W, H))
            temp_surface.fill((20, 0, 30))
            
            # Temporarily redirect drawing to temp surface
            original_screen = screen
            screen = temp_surface
            
            # Draw everything
            draw_arena()
            draw_effects()
            draw_luigi()
            draw_king_boo()
            
            # Draw HUD
            for i in range(luigi['health']):
                pygame.draw.circle(screen, (255, 0, 0), (30 + i*25, 30), 10)
            
            if luigi['grabbing'] and luigi['slam_power'] > 0:
                bar_w = int(100 * luigi['slam_power'] / 100)
                pygame.draw.rect(screen, (100, 100, 100), (W//2-52, H-50, 104, 24))
                pygame.draw.rect(screen, (0, 255, 0), (W//2-50, H-48, bar_w, 20))
            
            # Restore original screen and blit with shake
            screen = original_screen
            screen.blit(temp_surface, (int(shake_x), int(shake_y)))
        else:
            # Normal drawing without shake
            draw_arena()
            draw_effects()
            draw_luigi()
            draw_king_boo()
            
            # Draw HUD
            for i in range(luigi['health']):
                pygame.draw.circle(screen, (255, 0, 0), (30 + i*25, 30), 10)
            
            if luigi['grabbing'] and luigi['slam_power'] > 0:
                bar_w = int(100 * luigi['slam_power'] / 100)
                pygame.draw.rect(screen, (100, 100, 100), (W//2-52, H-50, 104, 24))
                pygame.draw.rect(screen, (0, 255, 0), (W//2-50, H-48, bar_w, 20))
    
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()

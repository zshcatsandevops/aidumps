from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import math
import random
from direct.actor.Actor import Actor

app = Ursina()

# GLITCH CONSTANTS - TWEAK FOR MAXIMUM CHAOS
POSSESSION_GLITCH_CHANCE = 0.1
REALITY_TEAR_FREQUENCY = 0.02
BLJ_MOMENTUM_MULTIPLIER = 1.5  # Backwards Long Jump tribute
WAHOO_PITCH_VARIANCE = 0.3

class SM64HUD(Entity):
    """Super Mario 64's HUD but it occasionally displays corrupted values"""
    def __init__(self):
        super().__init__()
        self.health_pie = Entity(
            model='circle',
            color=color.red,
            scale=0.1,
            position=(-0.85, 0.45, -1),
            parent=camera.ui
        )
        self.health_segments = []
        for i in range(8):
            segment = Entity(
                model='cube',
                color=color.red,
                scale=(0.05, 0.002, 0.001),
                rotation_z=i*45,
                parent=self.health_pie
            )
            self.health_segments.append(segment)
        
        self.coin_counter = Text(
            '× 0',
            position=(-0.85, 0.35),
            scale=2,
            color=color.yellow
        )
        
        self.star_counter = Text(
            '★ 0',
            position=(-0.85, 0.25),
            scale=2,
            color=color.white
        )
        
        self.glitch_text = Text(
            '',
            position=(0, 0.4),
            scale=3,
            color=color.random_color(),
            origin=(0,0)
        )
        
    def update_health(self, health):
        # Glitch: Sometimes display wrong health
        if random.random() < 0.05:
            health = random.randint(-999, 999)
        
        visible_segments = int((health / 100) * 8)
        for i, segment in enumerate(self.health_segments):
            segment.visible = i < visible_segments
            # Glitch effect
            if random.random() < REALITY_TEAR_FREQUENCY:
                segment.color = color.random_color()
    
    def add_coin(self, amount=1):
        current = int(self.coin_counter.text.split('× ')[1])
        # MEME: Coins sometimes multiply exponentially
        if random.random() < 0.01:
            amount *= 64  # SM64 reference
            self.glitch_text.text = 'COIN DUPLICATION GLITCH!'
            invoke(setattr, self.glitch_text, 'text', '', delay=1)
        self.coin_counter.text = f'× {current + amount}'
    
    def add_star(self):
        current = int(self.star_counter.text.split(' ')[1])
        self.star_counter.text = f'★ {current + 1}'
        # Achievement unlocked: Collect negative stars
        if random.random() < 0.05:
            self.star_counter.text = f'★ {current - 1}'
            self.glitch_text.text = 'NEGATIVE STAR ACQUIRED!'
            invoke(setattr, self.glitch_text, 'text', '', delay=1)

class Cappy(Entity):
    """Cappy but he's been corrupted by speedrun strats"""
    def __init__(self, mario):
        super().__init__(
            model='sphere',
            color=color.white,
            scale=0.3,
            position=mario.position + Vec3(0, 1, 0)
        )
        self.mario = mario
        self.is_thrown = False
        self.return_speed = 20
        self.throw_direction = Vec3(0, 0, 0)
        self.possessed_entity = None
        self.spin_speed = 800
        
        # Cappy's eyes that judge you
        self.eye1 = Entity(model='sphere', color=color.black, scale=0.1, parent=self, position=(0.1, 0, 0.3))
        self.eye2 = Entity(model='sphere', color=color.black, scale=0.1, parent=self, position=(-0.1, 0, 0.3))
    
    def throw(self, direction):
        if not self.is_thrown:
            self.is_thrown = True
            self.throw_direction = direction
            # MEME: Sometimes Cappy rebels
            if random.random() < 0.1:
                self.throw_direction = -direction
                print("CAPPY: 'No, I don't think I will.'")
    
    def update(self):
        if self.is_thrown:
            self.position += self.throw_direction * 30 * time.dt
            self.rotation_y += self.spin_speed * time.dt
            
            # Check for possession targets
            for entity in scene.entities:
                if hasattr(entity, 'possessable') and entity.possessable:
                    if distance(self.position, entity.position) < 2:
                        self.possess(entity)
                        return
            
            # Return to Mario after distance
            if distance(self.position, self.mario.position) > 15:
                self.return_to_mario()
        else:
            # Float above Mario's head
            target_pos = self.mario.position + Vec3(0, 2, 0)
            self.position = lerp(self.position, target_pos, 10 * time.dt)
            # Judgmental bobbing
            self.y += math.sin(time.time() * 3) * 0.1 * time.dt
    
    def possess(self, entity):
        self.possessed_entity = entity
        self.mario.become(entity)
        self.is_thrown = False
        # Glitch: Sometimes possess the wrong thing
        if random.random() < POSSESSION_GLITCH_CHANCE:
            entity.model = 'cube'
            entity.texture = 'white_cube'
            entity.color = color.random_color()
            print("POSSESSION GLITCH: Entity corrupted!")
    
    def return_to_mario(self):
        self.is_thrown = False
        self.throw_direction = Vec3(0, 0, 0)

class MarioOdyssey64(Entity):
    """Mario but he's learned the forbidden speedrun techniques"""
    def __init__(self):
        super().__init__(
            model='cube',
            color=color.red,
            scale=(1, 2, 1),
            position=(0, 1, 0)
        )
        self.speed = 10
        self.jump_force = 15
        self.gravity = -30
        self.velocity = Vec3(0, 0, 0)
        self.grounded = False
        self.health = 100
        self.possessed_form = None
        self.blj_momentum = 1.0  # Backwards Long Jump momentum
        
        # Hat (before possession)
        self.hat = Entity(
            model='cube',
            color=color.red,
            scale=(1.2, 0.3, 1.2),
            parent=self,
            position=(0, 0.6, 0)
        )
        
        # Mustache for authenticity
        self.mustache = Entity(
            model='cube',
            color=color.brown,
            scale=(0.8, 0.1, 0.3),
            parent=self,
            position=(0, -0.3, 0.5)
        )
        
        self.cappy = Cappy(self)
        self.hud = SM64HUD()
        
        # WAHOO counter
        self.wahoo_count = 0
    
    def update(self):
        # Movement with BLJ physics
        movement = Vec3(
            self.get_movement_input().x * self.speed * self.blj_momentum,
            0,
            self.get_movement_input().z * self.speed * self.blj_momentum
        )
        
        # Apply movement
        self.position += movement * time.dt
        
        # Gravity and jump
        if not self.grounded:
            self.velocity.y += self.gravity * time.dt
        
        self.position += self.velocity * time.dt
        
        # Ground check (simplified)
        if self.y <= 1:
            self.y = 1
            self.grounded = True
            self.velocity.y = 0
        else:
            self.grounded = False
        
        # Jump with WAHOO
        if self.grounded and held_keys['space']:
            self.velocity.y = self.jump_force
            self.wahoo()
            # BLJ DETECTED
            if held_keys['s']:  # Backwards
                self.blj_momentum = min(self.blj_momentum * BLJ_MOMENTUM_MULTIPLIER, 5)
                print("BLJ MOMENTUM:", self.blj_momentum)
        else:
            self.blj_momentum = max(1.0, self.blj_momentum * 0.95)
        
        # Throw Cappy
        if held_keys['left mouse']:
            direction = Vec3(
                math.sin(math.radians(camera.rotation_y)),
                0,
                math.cos(math.radians(camera.rotation_y))
            ).normalized()
            self.cappy.throw(direction)
        
        # Update HUD
        self.hud.update_health(self.health)
        
        # Random glitches
        if random.random() < REALITY_TEAR_FREQUENCY:
            self.apply_random_glitch()
    
    def get_movement_input(self):
        movement = Vec3(0, 0, 0)
        if held_keys['w']: movement.z += 1
        if held_keys['s']: movement.z -= 1
        if held_keys['a']: movement.x -= 1
        if held_keys['d']: movement.x += 1
        return movement.normalized()
    
    def wahoo(self):
        self.wahoo_count += 1
        pitch = 1 + random.uniform(-WAHOO_PITCH_VARIANCE, WAHOO_PITCH_VARIANCE)
        # Every 10th wahoo is corrupted
        if self.wahoo_count % 10 == 0:
            print(f"W{'A' * random.randint(1, 20)}HOO! (Pitch: {pitch:.2f})")
        else:
            print(f"WAHOO! (#{self.wahoo_count})")
    
    def become(self, entity):
        """Possession mechanic with glitches"""
        self.possessed_form = entity
        # Copy some properties
        self.model = entity.model
        self.color = entity.color
        self.scale = entity.scale
        # But keep Mario's mustache because priorities
        self.mustache.visible = True
        
        # Special possessed abilities
        if hasattr(entity, 'special_ability'):
            print(f"POSSESSED: Gained {entity.special_ability}!")
    
    def apply_random_glitch(self):
        """Reality.exe has stopped working"""
        glitch_type = random.choice([
            'color_corruption',
            'scale_wobble',
            'position_jitter',
            'hat_rebellion'
        ])
        
        if glitch_type == 'color_corruption':
            self.color = color.random_color()
            invoke(setattr, self, 'color', color.red, delay=0.1)
        elif glitch_type == 'scale_wobble':
            self.scale *= random.uniform(0.8, 1.2)
            invoke(setattr, self, 'scale', Vec3(1, 2, 1), delay=0.2)
        elif glitch_type == 'position_jitter':
            self.x += random.uniform(-0.5, 0.5)
        elif glitch_type == 'hat_rebellion':
            self.hat.rotation_z += random.uniform(-45, 45)

class PossessableGoomba(Entity):
    """Goomba but he knows he's in a simulation"""
    def __init__(self, position):
        super().__init__(
            model='cube',
            color=color.brown,
            scale=(1, 1, 1),
            position=position
        )
        self.possessable = True
        self.special_ability = "EXISTENTIAL_CRISIS"
        
        # Angry eyebrows
        self.eyebrow = Entity(
            model='cube',
            color=color.black,
            scale=(0.8, 0.1, 0.1),
            parent=self,
            position=(0, 0.4, 0.5),
            rotation_z=20
        )
        
        self.walk_speed = 2
        self.direction = 1
        
    def update(self):
        if not hasattr(mario, 'possessed_form') or mario.possessed_form != self:
            # Patrol with occasional existential pauses
            self.x += self.direction * self.walk_speed * time.dt
            
            if abs(self.x) > 10:
                self.direction *= -1
                # Sometimes question existence
                if random.random() < 0.3:
                    print(f"GOOMBA: 'Why do I walk back and forth? What is my purpose?'")

class PowerMoon(Entity):
    """Power Moon that's been quantum entangled with Power Stars"""
    def __init__(self, position):
        super().__init__(
            model='sphere',
            color=color.yellow,
            scale=0.5,
            position=position
        )
        self.float_speed = 2
        self.spin_speed = 100
        self.collected = False
        
    def update(self):
        if not self.collected:
            # Floating animation
            self.y += math.sin(time.time() * self.float_speed) * 0.02
            self.rotation_y += self.spin_speed * time.dt
            
            # Collection
            if distance(self.position, mario.position) < 2:
                self.collected = True
                mario.hud.add_star()
                # Quantum superposition - sometimes you get a moon, sometimes you don't
                if random.random() < 0.5:
                    print("QUANTUM MOON: Collapsed into existence!")
                    destroy(self)
                else:
                    print("QUANTUM MOON: Collapsed out of existence but you still got it!")
                    self.visible = False
                    invoke(destroy, self, delay=1)

class CoinBlock(Entity):
    """? Block that's learned to defend itself"""
    def __init__(self, position):
        super().__init__(
            model='cube',
            color=color.yellow,
            scale=1,
            position=position,
            texture='white_cube'
        )
        self.coins_remaining = random.randint(1, 64)  # SM64 max coins
        self.hit_cooldown = 0
        
        self.question_mark = Text(
            '?',
            parent=self,
            scale=10,
            origin=(0, 0),
            color=color.black,
            position=(0, 0, 0.51)
        )
    
    def update(self):
        self.hit_cooldown = max(0, self.hit_cooldown - time.dt)
        
        # Check for Mario bonking it
        if distance_xz(self.position, mario.position) < 1.5:
            if mario.position.y > self.position.y + 0.5 and mario.velocity.y < 0:
                if self.hit_cooldown <= 0:
                    self.dispense_coins()
                    self.hit_cooldown = 0.5
    
    def dispense_coins(self):
        if self.coins_remaining > 0:
            # Sometimes the block fights back
            if random.random() < 0.1:
                print("? BLOCK: 'No coins for you!'")
                mario.health -= 10
                return
            
            coins_to_give = min(self.coins_remaining, random.randint(1, 10))
            self.coins_remaining -= coins_to_give
            mario.hud.add_coin(coins_to_give)
            
            # Visual feedback
            self.animate_scale(
                self.scale * 1.2,
                duration=0.1,
                curve=curve.out_elastic
            )
            
            if self.coins_remaining <= 0:
                self.color = color.brown
                self.question_mark.text = '!'

# Initialize the madness
mario = MarioOdyssey64()

# Camera setup
camera.parent = mario
camera.position = (0, 2, -5)
camera.rotation_x = 10

# Create the cursed kingdom
ground = Entity(
    model='cube',
    color=color.green,
    scale=(100, 0.1, 100),
    position=(0, 0, 0),
    texture='grass'
)

# Spawn enemies and collectibles
for i in range(5):
    PossessableGoomba(position=(random.uniform(-20, 20), 1, random.uniform(-20, 20)))

for i in range(10):
    PowerMoon(position=(random.uniform(-30, 30), random.uniform(2, 8), random.uniform(-30, 30)))

for i in range(8):
    CoinBlock(position=(random.uniform(-25, 25), 3, random.uniform(-25, 25)))

# Skybox that occasionally glitches
sky = Sky()
def glitch_sky():
    if random.random() < 0.01:
        sky.color = color.random_color()
        invoke(setattr, sky, 'color', color.light_gray, delay=0.1)
Entity(update=glitch_sky)

# Instructions overlay
instructions = Text(
    'WASD: Move | Space: WAHOO Jump (Hold S for BLJ) | Left Click: Throw Cappy\nPossess Goombas! Collect Quantum Moons! Hit ? Blocks (they might hit back)',
    position=(0, -0.45),
    origin=(0, 0),
    scale=1,
    color=color.white
)

# Easter egg: Konami code detector
konami_sequence = []
konami_code = ['up', 'up', 'down', 'down', 'left', 'right', 'left', 'right', 'b', 'a']

def input(key):
    global konami_sequence
    if key in konami_code:
        konami_sequence.append(key)
        if konami_sequence[-len(konami_code):] == konami_code:
            print("L IS REAL 2401")
            mario.health = 2401
            mario.hud.glitch_text.text = 'EVERY COPY OF MARIO 64 IS PERSONALIZED'
            konami_sequence = []

# Window settings
window.title = 'Super Cappy Odyssey 64: Every Copy is Personalized'
window.borderless = False
window.fullscreen = False
window.exit_button.visible = False
window.fps_counter.enabled = True

# Final corrupted message
print("GAME LOADED. YAHOOOO! YAHOO-YAHOO-YAH-YAH-YAHOO!")
print("WARNING: Cappy has gained sentience. Good luck.")

app.run()

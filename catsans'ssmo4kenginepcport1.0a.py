# To run:
# 1. Make sure you have ursina installed: pip install ursina
# 2. Save this code as test.py
# 3. Run from your terminal: python test.py

from ursina import *
import math
import random
import time

# Initialize app with vsync for smoother performance
app = Ursina(vsync=True, development_mode=False)
window.fps_counter.enabled = True
window.exit_button.visible = False
window.title = 'Ursina Odyssey - Enhanced Edition'

# Constants
GRAVITY = Vec3(0, -25, 0) # Increased gravity for a snappier feel
MOVE_SPEED = 6
RUN_SPEED = 9
JUMP_SPEED = 9.5
MAX_FALL_SPEED = -30
CAM_DISTANCE = 12
CAM_HEIGHT = 2
CAPPY_SPEED = 25
CAPPY_RANGE = 10
CAPPY_HOVER_TIME = 2 # How long Cappy waits for a bounce
FIREBALL_SPEED = 20
MUSHROOM_DURATION = 10
CAPPY_POWER_DURATION = 15

# Forward declaration for type hinting
player = None

# ---- New Supporting Classes ----

class Enemy(Entity):
    """A simple patrolling enemy that can be captured and has a unique captured ability."""
    def __init__(self, position=(0,0,0), patrol_range=5):
        super().__init__(
            model='cube',
            texture='brick',
            color=color.rgba(139, 69, 19, 255), # Brown color
            scale=(1, 1, 1),
            collider='box',
            position=position
        )
        self.original_color = self.color
        self.captured = False
        self.health = 1
        self.patrol_start = self.x - patrol_range / 2
        self.patrol_end = self.x + patrol_range / 2
        self.speed = 2
        self.direction = 1
        self.velocity = Vec3(0,0,0)
        self.grounded = False

    def update(self):
        if self.captured:
            # When captured, control is handled by the captured_update method via the player
            self.apply_gravity()
            return

        # Simple patrol AI
        self.x += self.direction * self.speed * time.dt
        if self.direction == 1 and self.x > self.patrol_end:
            self.direction = -1
            self.rotation_y = -90
        elif self.direction == -1 and self.x < self.patrol_start:
            self.direction = 1
            self.rotation_y = 90

        # Check collision with Mario
        if self.intersects(player).hit and not player.captured and not player.invincible:
            player.take_damage(knockback_from=self.position)

    def captured_update(self):
        """NEW: This method is called by the player when this enemy is captured."""
        move_direction = (
            Vec3(camera.forward.x, 0, camera.forward.z).normalized() * (held_keys['w'] - held_keys['s']) +
            Vec3(camera.right.x, 0, camera.right.z).normalized() * (held_keys['d'] - held_keys['a'])
        ).normalized()
        self.position += move_direction * 4 * time.dt # Captured Goomba is a bit slow

        if held_keys['space'] and self.grounded:
            # UNIQUE ABILITY: Super Jump
            self.velocity.y = JUMP_SPEED * 1.5
            self.grounded = False


    def apply_gravity(self):
        """NEW: Captured enemies need gravity too."""
        if not self.grounded:
            self.velocity += GRAVITY * time.dt
        self.position += self.velocity * time.dt

        # Ground check for captured entity
        ray = raycast(self.world_position, (0,-1,0), distance=self.scale_y/2 + 0.1)
        if ray.hit:
            self.grounded = True
            self.velocity.y = 0
            self.y = ray.world_point.y + self.scale_y/2
        else:
            self.grounded = False

    def take_damage(self):
        self.health -= 1
        if self.health <= 0:
            self.collider = None
            self.animate_scale(self.scale*0.1, duration=0.2)
            self.fade_out(duration=0.2)
            invoke(destroy, self, delay=0.3)


class Fireball(Entity):
    """A projectile thrown by Mario when he has the Mushroom power-up."""
    def __init__(self, position, direction):
        super().__init__(
            model='sphere', color=color.orange, scale=0.4, position=position, collider='sphere'
        )
        self.direction = direction.normalized()
        self.speed = FIREBALL_SPEED
        destroy(self, delay=3)

    def update(self):
        self.position += self.direction * self.speed * time.dt
        hit_info = self.intersects()
        if hit_info.hit and hit_info.entity not in (player, player.cappy):
            if isinstance(hit_info.entity, Enemy):
                hit_info.entity.take_damage()
            destroy(self)


class Coin(Entity):
    """A collectible coin that increases the player's score."""
    def __init__(self, position=(0,1,0)):
        super().__init__(
            model='sphere', color=color.gold, scale=0.4, position=position, collider='sphere', rotation_y=45
        )
        self.animate_y(self.y + 0.25, duration=1, loop=True, curve=curve.in_out_sine)
        self.animate('rotation_y', self.rotation_y + 360, duration=4, loop=True, curve=curve.linear)

    def collect(self):
        # Audio('coin.wav', volume=0.5, auto_destroy=True) # NOTE: Requires a 'coin.wav' file
        player.coins += 1
        destroy(self)


class PowerUp(Entity):
    """An item that grants a temporary power-up to Mario."""
    def __init__(self, power_type='mushroom', position=(0,1,0)):
        self.power_type = power_type
        super().__init__(
            model='cube',
            color=color.pink if power_type == 'mushroom' else color.cyan,
            scale=0.8, position=position, collider='box', texture='white_cube'
        )
        self.animate_y(self.y + 0.25, duration=1.5, loop=True, curve=curve.in_out_sine)

    def update(self):
        if self.intersects(player).hit:
            if self.power_type == 'mushroom':
                player.mushroom = True
                player.mushroom_timer = MUSHROOM_DURATION
                player.scale_y = 1.5
            elif self.power_type == 'cappy_power':
                player.cappy_power = True
                player.cappy_power_timer = CAPPY_POWER_DURATION
            destroy(self)

# ---- Main Character Class (Heavily Modified) ----

class Mario(Entity):
    def __init__(self, **kwargs):
        super().__init__(
            model='cube', color=color.red, scale=(0.8, 1.2, 0.8), collider='box', **kwargs
        )
        # Core Physics & State
        self.velocity = Vec3(0, 0, 0)
        self.grounded = False
        self.jump_count = 0
        self.max_jumps = 2
        self.gravity_scale = 1.0
        self.wall_normal = Vec3(0,0,0)


        # Advanced Movement States
        self.crouching = False
        self.rolling = False
        self.wall_sliding = False
        self.dive_rolling = False
        self.ground_pound = False

        # Gameplay Stats
        self.health = 3
        self.coins = 0
        self.lives = 3
        self.invincible = False
        self.invincible_timer = 0

        # Capture & Cappy
        self.captured = None
        self.cappy = None
        self.hat = Entity(model='cube', color=color.white, scale=(0.6, 0.2, 0.6), parent=self, position=(0, 0.7, 0))

        # Power-ups
        self.mushroom = False
        self.mushroom_timer = 0
        self.cappy_power = False
        self.cappy_power_timer = 0


    def update(self):
        # --- State Updates ---
        self.handle_invincibility()
        if self.captured:
            self.control_captured()
            return
        self.handle_powerup_timers()

        # --- Movement Logic ---
        move_direction = self.get_move_direction()
        if not self.dive_rolling and not self.rolling:
            self.handle_movement(move_direction)
        self.apply_gravity_and_collisions()

        # --- Animations & Model Adjustments ---
        self.update_model_and_hat(move_direction)

    def input(self, key):
        if self.captured:
            if key == 'space': self.release_capture()
            return

        # --- JUMPING ---
        if key == 'space':
            if self.wall_sliding: self.wall_jump()
            elif self.crouching: self.crouch_jump()
            else: self.jump()
        # --- CAPPY ---
        elif key == 'q' and not self.cappy: self.throw_cappy()
        elif key == 'e' and not self.cappy: self.throw_cappy(homing=True)
        elif key == 'c' and not self.cappy: self.cappy_spin()
        # --- OTHER MOVES ---
        elif key == 'f' and self.mushroom: self.throw_fireball()
        elif key == 'x' and not self.grounded: self.dive()
        elif key == 'z' and not self.grounded and self.velocity.y < 0: self.start_ground_pound()
        # --- CROUCHING & ROLLING ---
        elif key == 'left control down': self.start_crouch()
        elif key == 'left control up': self.stop_crouch()


    # --- Input Methods ---
    def jump(self):
        if self.grounded:
            self.velocity.y = JUMP_SPEED
            self.grounded = False
            self.jump_count = 1
        elif self.jump_count < self.max_jumps:
            self.velocity.y = JUMP_SPEED * 0.85
            self.jump_count += 1

    def wall_jump(self):
        """NEW: The actual jump logic when wall sliding."""
        if self.wall_sliding:
            # Jump away from the wall normal
            self.velocity = self.wall_normal * MOVE_SPEED * 1.5 + Vec3(0, JUMP_SPEED * 0.9, 0)
            self.wall_sliding = False
            self.jump_count = 1 # Wall jump counts as the first jump

    def crouch_jump(self):
        """NEW: Logic for high jump and long jump."""
        horiz_speed = Vec2(self.velocity.x, self.velocity.z).length()
        if horiz_speed > MOVE_SPEED / 2: # Check if moving -> Long Jump
            self.grounded = False
            forward_dir = self.forward if self.forward.length() > 0 else Vec3(0,0,1)
            self.velocity = forward_dir * RUN_SPEED * 1.8
            self.velocity.y = JUMP_SPEED * 0.6
        else: # Stationary -> High Jump
            self.velocity.y = JUMP_SPEED * 1.3
            self.grounded = False
        self.crouching = False
        self.scale_y = 1.2 # Uncrouch

    def start_crouch(self):
        if self.grounded:
            horiz_speed = Vec2(self.velocity.x, self.velocity.z).length()
            if horiz_speed > MOVE_SPEED: # If running, start a roll
                self.rolling = True
                self.dive_rolling = False # Cancel dive
                forward_dir = self.forward if self.forward.length() > 0 else Vec3(0,0,1)
                self.velocity = forward_dir * RUN_SPEED * 2.2
                invoke(setattr, self, 'rolling', False, delay=0.5)
            else: # Otherwise, just crouch
                self.crouching = True
                self.scale_y = 0.8

    def stop_crouch(self):
        if self.crouching:
            self.crouching = False
            self.scale_y = 1.2

    def dive(self):
        if not self.dive_rolling:
            self.dive_rolling = True
            forward_dir = (self.forward if self.forward.length() > 0 else camera.forward)
            forward_dir.y = 0
            forward_dir.normalize()
            self.velocity = forward_dir * MOVE_SPEED * 1.8
            self.velocity.y = 2
            self.rotation_x = -60

    def start_ground_pound(self):
        if not self.ground_pound:
            self.ground_pound = True
            self.velocity = Vec3(0, 2, 0)
            invoke(setattr, self, 'velocity', Vec3(0, -35, 0), delay=0.15) # Faster pound

    def throw_cappy(self, homing=False):
        target_enemy = None
        if homing:
            enemies = [e for e in scene.entities if isinstance(e, Enemy) and distance(e.position, self.position) < 15]
            if enemies:
                target_enemy = min(enemies, key=lambda e: distance_2d(e.screen_position, Vec2(0,0)))
        self.cappy = Cappy(mario=self, target=target_enemy)
        self.hat.visible = False

    def cappy_spin(self):
        """NEW: Cappy spins around Mario as an attack."""
        self.hat.visible = False
        # Create a temporary Cappy for the spin animation/hitbox
        spin_cappy = Entity(model='sphere', color=color.white, scale=(0.6, 0.2, 0.6), position=self.position)
        spin_cappy.animate('rotation_y', 360, duration=0.4)
        # Animate the spin orbit
        spin_cappy.animate_position(self.position + self.right*1.5, duration=0.1, curve=curve.linear, on_finish=lambda:
        spin_cappy.animate_position(self.position - self.right*1.5, duration=0.2, curve=curve.linear, on_finish=lambda:
        spin_cappy.animate_position(self.position, duration=0.1, curve=curve.linear)))

        # Check for hits during the spin
        def check_spin_hit():
            hit_info = spin_cappy.intersects()
            if hit_info.hit and isinstance(hit_info.entity, Enemy):
                hit_info.entity.take_damage()
        invoke(check_spin_hit, delay=0.1)
        invoke(check_spin_hit, delay=0.2)
        invoke(check_spin_hit, delay=0.3)

        def end_spin():
            if not self.cappy: self.hat.visible = True
            destroy(spin_cappy)
        invoke(end_spin, delay=0.4)


    def throw_fireball(self):
        spawn_pos = self.world_position + self.forward * 1 + Vec3(0,0.5,0)
        Fireball(spawn_pos, self.forward if self.forward.length() > 0 else camera.forward)

    # --- Capture Logic ---
    def capture(self, entity):
        if self.cappy_power and isinstance(entity, Enemy) and not entity.captured:
            self.captured = entity
            self.visible = False
            entity.color = color.yellow
            entity.captured = True
            if self.cappy:
                destroy(self.cappy)
                self.cappy = None
            self.hat.parent = entity
            self.hat.position = Vec3(0, entity.scale_y, 0) # Position hat on top
            self.hat.visible = True

    def control_captured(self):
        if self.captured and hasattr(self.captured, 'captured_update'):
            self.captured.captured_update() # NEW: Delegate control to the enemy

    def release_capture(self):
        if self.captured:
            self.position = self.captured.position + Vec3(0, 2, 0)
            self.captured.color = self.captured.original_color
            self.captured.captured = False
            self.hat.parent = self
            self.hat.position = (0, 0.7, 0)
            self.captured = None
            self.visible = True
            self.velocity.y = JUMP_SPEED * 1.2 # Eject jump
            self.grounded = False

    # --- Update Helpers ---
    def get_move_direction(self):
        return (
            Vec3(camera.forward.x, 0, camera.forward.z).normalized() * (held_keys['w'] - held_keys['s']) +
            Vec3(camera.right.x, 0, camera.right.z).normalized() * (held_keys['d'] - held_keys['a'])
        ).normalized()

    def handle_movement(self, move_direction):
        speed = RUN_SPEED if held_keys['shift'] else MOVE_SPEED
        if self.crouching: speed *= 0.5

        if self.grounded:
            self.velocity.x = move_direction.x * speed
            self.velocity.z = move_direction.z * speed
        else: # Air control
            self.velocity.x += move_direction.x * speed * time.dt * 1.5
            self.velocity.z += move_direction.z * speed * time.dt * 1.5
            air_speed = Vec2(self.velocity.x, self.velocity.z).length()
            if air_speed > speed:
                air_dir = Vec2(self.velocity.x, self.velocity.z).normalized()
                self.velocity.x = air_dir.x * speed
                self.velocity.z = air_dir.y * speed

    def apply_gravity_and_collisions(self):
        # Apply gravity, but reduce it if wall sliding
        gravity_multiplier = 0.2 if self.wall_sliding else 1.0
        if not self.grounded:
            self.velocity.y += GRAVITY.y * self.gravity_scale * gravity_multiplier * time.dt
            self.velocity.y = max(self.velocity.y, MAX_FALL_SPEED)

        self.position += self.velocity * time.dt
        self.check_ground()
        if not self.grounded:
            self.check_walls()
        else:
            self.wall_sliding = False # No wall sliding on the ground

        # NEW: Cappy jump check
        if self.cappy and self.cappy.state == 'hover' and self.velocity.y < 0:
            if self.intersects(self.cappy).hit:
                self.cappy.state = 'returning' # Cappy returns after bounce
                self.velocity.y = JUMP_SPEED * 1.1 # Bounce!
                self.jump_count = 1 # Reset double jump

    def check_ground(self):
        ray = raycast(self.world_position + Vec3(0,self.scale_y/2,0), Vec3(0,-1,0), distance=self.scale_y/2 + 0.2, ignore=[self, self.cappy])
        if ray.hit:
            if not self.grounded: # Just landed
                self.velocity.y = 0
                self.grounded = True
                self.jump_count = 0
                self.rotation_x = 0
                if self.dive_rolling:
                    self.dive_rolling = False
                    self.start_crouch() # Land into a roll
                if self.ground_pound:
                    self.ground_pound = False
                    for e in scene.entities:
                        if isinstance(e, Enemy) and distance(e.position, self.position) < 3: e.take_damage()
                    self.velocity.y = JUMP_SPEED / 2 # small hop after pound
            self.position.y = ray.world_point.y + self.scale_y / 2
        else:
            self.grounded = False

    def check_walls(self):
        """NEW: Updated wall check for wall sliding."""
        move_dir_2d = Vec2(self.velocity.x, self.velocity.z).normalized()
        wall_check_dir = Vec3(move_dir_2d.x, 0, move_dir_2d.y)
        if wall_check_dir.length() == 0:
            self.wall_sliding = False
            return

        ray = raycast(self.world_position, wall_check_dir, distance=0.5, ignore=[self, self.cappy])
        if ray.hit and ray.entity.collider and not self.grounded:
            self.wall_sliding = True
            self.wall_normal = ray.world_normal # Store wall normal for the jump
            # Stick to wall slightly
            self.x -= ray.world_normal.x * 0.01
            self.z -= ray.world_normal.z * 0.01

        else:
            self.wall_sliding = False

    def handle_invincibility(self):
        if self.invincible:
            self.invincible_timer -= time.dt
            self.alpha = 128 if int(self.invincible_timer * 10) % 2 == 0 else 255
            if self.invincible_timer <= 0:
                self.invincible = False
                self.alpha = 255

    def handle_powerup_timers(self):
        if self.mushroom:
            self.mushroom_timer -= time.dt
            if self.mushroom_timer <= 0:
                self.mushroom = False
                if not self.crouching: self.scale_y = 1.2
        if self.cappy_power:
            self.cappy_power_timer -= time.dt
            if self.cappy_power_timer <= 0: self.cappy_power = False

    def update_model_and_hat(self, move_direction):
        if move_direction.length() > 0 and not self.dive_rolling:
            self.look_at(self.position + move_direction, axis='y')
        self.hat.position = (0, 0.4, 0) if self.crouching else (0, 0.7, 0)


    def take_damage(self, knockback_from=None):
        if self.invincible: return
        self.health -= 1
        self.invincible = True
        self.invincible_timer = 2.0
        if self.health <= 0:
            self.lives -= 1
            if self.lives > 0: self.respawn()
            else:
                Text("Game Over!", scale=5, origin=(0,0), background=True)
                application.pause()
        else:
            if knockback_from:
                knockback_dir = (self.position - knockback_from).normalized()
                self.velocity = knockback_dir * 6 + Vec3(0, 6, 0)
            self.grounded = False

    def respawn(self):
        self.position = Vec3(0, 3, 0)
        self.velocity = Vec3(0, 0, 0)
        self.health = 3
        # Reset states
        self.crouching = self.rolling = self.wall_sliding = self.dive_rolling = self.ground_pound = False
        if self.captured: self.release_capture()


# ---- Cappy Class (Heavily Modified) ----

class Cappy(Entity):
    def __init__(self, mario, target=None):
        super().__init__(
            model='sphere', color=color.white, scale=(0.6, 0.2, 0.6),
            position=mario.position + Vec3(0, 1, 0), collider='sphere'
        )
        self.mario = mario
        self.speed = CAPPY_SPEED
        self.start_time = time.time()
        self.max_throw_time = CAPPY_RANGE / self.speed
        self.hover_start_time = 0

        if target:
            self.state = 'homing'
            self.target = target
            self.direction = (target.position - self.position).normalized()
        else:
            self.state = 'throwing'
            self.target = None
            self.direction = Vec3(camera.forward.x, 0, camera.forward.z).normalized()

    def update(self):
        # State machine for Cappy's behavior
        if self.state == 'throwing' or self.state == 'homing':
            self.position += self.direction * self.speed * time.dt
            if time.time() - self.start_time > self.max_throw_time:
                self.state = 'hover' # NEW: Hover state
                self.hover_start_time = time.time()
        elif self.state == 'hover':
            # Spin in place while hovering
            self.rotation_y += 360 * time.dt
            if time.time() - self.hover_start_time > CAPPY_HOVER_TIME:
                self.state = 'returning'
        elif self.state == 'returning':
            self.direction = (self.mario.position + Vec3(0,1,0) - self.position).normalized()
            self.position += self.direction * self.speed * time.dt
            if distance(self, self.mario) < 1:
                self.return_to_mario()

        hit_info = self.intersects()
        if hit_info.hit:
            entity = hit_info.entity
            if entity == self.mario and self.state == 'returning':
                self.return_to_mario()
            elif isinstance(entity, Enemy):
                self.mario.capture(entity)
                # No need to destroy Cappy here, capture logic handles it
            elif isinstance(entity, Coin):
                entity.collect()
            # If Cappy hits a wall, return immediately
            elif entity != self.mario and entity.collider and self.state not in ('returning', 'hover'):
                self.state = 'returning'

        # Failsafe timeout
        if time.time() - self.start_time > 8:
             if self.state != 'returning': self.state = 'returning'

    def return_to_mario(self):
        if self.mario.cappy == self:
            self.mario.cappy = None
            self.mario.hat.visible = True
        destroy(self)


# ---- Platform and Camera Classes ----

class MovingPlatform(Entity):
    def __init__(self, position=(0,0,0), end_position=(0,5,0), **kwargs):
        super().__init__(
            model='cube', color=color.gray, scale=(4, 0.5, 4), position=position,
            collider='box', texture='white_cube', **kwargs
        )
        self.start_pos = Vec3(position)
        self.end_pos = Vec3(end_position)
        self.speed = 0.5

    def update(self):
        self.position = lerp(self.start_pos, self.end_pos, (math.sin(time.time() * self.speed) + 1) / 2)
        if player and player.grounded:
            ray = raycast(player.world_position + Vec3(0,0.1,0), Vec3(0,-1,0), distance=0.2, ignore=[player, player.cappy])
            if ray.hit and ray.entity == self:
                if player.parent != self: player.parent = self
            elif player.parent == self:
                player.parent = scene


class OdysseyCamera(Entity):
    def __init__(self, target):
        super().__init__()
        self.target = target
        self.distance = CAM_DISTANCE
        self.rotation_speed = 100
        self.offset = Vec3(0, CAM_HEIGHT, 0)
        camera.rotation = (20, 0, 0)
        # ---- FIX 1: Initialize the look_at_target attribute here ----
        self.look_at_target = self.target.world_position + self.offset

    def update(self):
        if mouse.locked:
            camera.rotation_y += mouse.velocity[0] * self.rotation_speed
            camera.rotation_x -= mouse.velocity[1] * self.rotation_speed
            camera.rotation_x = clamp(camera.rotation_x, -40, 40)

        # Smoothly follow player or captured entity
        follow_target = self.target.captured if self.target.captured else self.target
        target_pos = follow_target.world_position + self.offset
        camera_offset = camera.back * self.distance
        desired_position = target_pos + camera_offset

        # Camera collision
        ray = raycast(target_pos, camera.position - target_pos, distance=self.distance, ignore=[follow_target, self.target, getattr(self.target, 'cappy', None)], debug=False)
        if ray.hit:
            camera.position = lerp(camera.position, ray.world_point, time.dt * 20)
        else:
            camera.position = lerp(camera.position, desired_position, time.dt * 10)

        # ---- FIX 2: Use and update the class attribute for smooth look_at ----
        self.look_at_target = lerp(self.look_at_target, target_pos, time.dt * 15)
        camera.look_at(self.look_at_target)


# ---- World and UI Setup ----

class Kingdom(Entity):
    def __init__(self):
        super().__init__()
        self.create_world()

    def create_world(self):
        Entity(model='plane', texture='grass', color=color.lime, scale=(100, 1, 100), position=(0, -1, 0), collider='box')
        # Wall for wall-jumping
        Entity(model='cube', color=color.dark_gray, scale=(1, 20, 30), position=(-25.5, 9, 0), collider='box', texture='brick')
        Entity(model='cube', color=color.dark_gray, scale=(30, 20, 1), position=(0, 9, 25.5), collider='box', texture='brick')
        # Random platforms
        for i in range(15):
            Entity(model='cube', color=color.brown, scale=(random.uniform(2,5), 0.5, random.uniform(2,5)), position=(random.uniform(-20, 20), random.uniform(2, 12), random.uniform(-20, 20)), collider='box')
        MovingPlatform(position=Vec3(10, 3, 0), end_position=Vec3(10, 8, 10))
        MovingPlatform(position=Vec3(-10, 2, 5), end_position=Vec3(-15, 2, -5))
        for i in range(50):
            Coin(position=(random.uniform(-25, 25), random.uniform(1, 15), random.uniform(-25, 25)))
        Enemy(position=(5, 0, 5), patrol_range=10)
        Enemy(position=(-5, 0, -10), patrol_range=5)
        PowerUp(power_type='mushroom', position=(0, 1, 5))
        PowerUp(power_type='cappy_power', position=(0, 1, -5))


class GameUI(Entity):
    def __init__(self):
        super().__init__(parent=camera.ui)
        self.health_text = Text(parent=self, origin=(-.5, .5), text="", position=(-0.85, 0.45), scale=1.5, background=True)
        self.coins_text = Text(parent=self, origin=(-.5, .5), text="", position=(-0.85, 0.40), scale=1.5, background=True)
        self.lives_text = Text(parent=self, origin=(-.5, .5), text="", position=(-0.85, 0.35), scale=1.5, background=True)
        # Power-up status
        self.mushroom_icon = Entity(parent=self, model='quad', texture='white_cube', color=color.pink, scale=0.05, position=(-0.85, 0.30))
        self.cappy_power_icon = Entity(parent=self, model='quad', texture='white_cube', color=color.cyan, scale=0.05, position=(-0.85, 0.24))

    def update(self):
        if player:
            self.health_text.text = f"Health: {player.health}"
            self.coins_text.text = f"Coins: {player.coins}"
            self.lives_text.text = f"Lives: {player.lives}"
            self.mushroom_icon.enabled = player.mushroom
            self.cappy_power_icon.enabled = player.cappy_power

# ---- Game Initialization ----

player = Mario(position=(0, 3, 0))
camera_controller = OdysseyCamera(player)
kingdom = Kingdom()
game_ui = GameUI()
Sky()
mouse.locked = True

# Add a simple directional light
DirectionalLight(y=2, z=3, shadows=True, rotation=(45, -45, 45))

# Global input handler
def input(key):
    if key == 'escape':
        mouse.locked = not mouse.locked
    if player:
        player.input(key)

app.run()

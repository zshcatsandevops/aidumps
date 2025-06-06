from ursina import *
import math
import random
import time

# Initialize app with vsync for smoother performance
app = Ursina(vsync=True, development_mode=False)
window.fps_counter.enabled = True
window.exit_button.visible = False
window.title = 'Ursina Odyssey'

# Constants
GRAVITY = Vec3(0, -9.81, 0)
MOVE_SPEED = 5
RUN_SPEED = 8
JUMP_SPEED = 8
MAX_FALL_SPEED = -20
CAM_DISTANCE = 10
CAM_HEIGHT = 2
CAPPY_SPEED = 20
CAPPY_RANGE = 12
FIREBALL_SPEED = 20
MUSHROOM_DURATION = 10
CAPPY_POWER_DURATION = 15

# Forward declaration for type hinting
player = None

# ---- New Supporting Classes ----

class Enemy(Entity):
    """A simple patrolling enemy that can be captured or defeated."""
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

    def update(self):
        if self.captured:
            # When captured, Mario controls this entity's movement
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

    def take_damage(self):
        self.health -= 1
        if self.health <= 0:
            # Simple death effect
            self.collider = None
            self.animate_scale(self.scale*0.1, duration=0.2)
            self.fade_out(duration=0.2)
            invoke(destroy, self, delay=0.3)


class Fireball(Entity):
    """A projectile thrown by Mario when he has the Mushroom power-up."""
    def __init__(self, position, direction):
        super().__init__(
            model='sphere',
            color=color.orange,
            scale=0.4,
            position=position,
            collider='sphere'
        )
        self.direction = direction.normalized()
        self.speed = FIREBALL_SPEED
        destroy(self, delay=3) # Destroy after 3 seconds if it hits nothing

    def update(self):
        self.position += self.direction * self.speed * time.dt
        hit_info = self.intersects()
        if hit_info.hit:
            if isinstance(hit_info.entity, Enemy):
                hit_info.entity.take_damage()
            # Destroy on any collision except with the player or cappy
            if hit_info.entity not in (player, player.cappy):
                 destroy(self)


class Coin(Entity):
    """A collectible coin that increases the player's score."""
    def __init__(self, position=(0,1,0)):
        super().__init__(
            model='sphere',
            color=color.gold,
            scale=0.4,
            position=position,
            collider='sphere',
            rotation_y=45
        )
        # Bobbing and spinning animation
        self.animate_y(self.y + 0.25, duration=1, loop=True, curve=curve.in_out_sine)
        self.animate('rotation_y', self.rotation_y + 360, duration=4, loop=True, curve=curve.linear)

    def collect(self):
        player.coins += 1
        destroy(self)


class PowerUp(Entity):
    """An item that grants a temporary power-up to Mario."""
    def __init__(self, power_type='mushroom', position=(0,1,0)):
        self.power_type = power_type
        super().__init__(
            model='cube',
            color=color.pink if power_type == 'mushroom' else color.cyan,
            scale=0.8,
            position=position,
            collider='box',
            texture='white_cube'
        )
        self.animate_y(self.y + 0.25, duration=1.5, loop=True, curve=curve.in_out_sine)

    def update(self):
        if self.intersects(player).hit:
            if self.power_type == 'mushroom':
                player.mushroom = True
                player.mushroom_timer = MUSHROOM_DURATION
                player.scale = Vec3(0.8, 1.5, 0.8) # Mario gets taller
            elif self.power_type == 'cappy_power':
                player.cappy_power = True
                player.cappy_power_timer = CAPPY_POWER_DURATION
            destroy(self)

# ---- Main Character Class (Modified) ----

class Mario(Entity):
    def __init__(self, **kwargs):
        super().__init__(
            model='cube',
            color=color.red,
            scale=(0.8, 1.2, 0.8),
            collider='box',
            **kwargs
        )
        self.velocity = Vec3(0, 0, 0)
        self.grounded = False
        self.health = 3
        self.coins = 0
        self.moons = 0
        self.lives = 3
        self.jump_count = 0
        self.max_jumps = 2
        self.crouching = False
        self.wall_jumping = False
        self.swimming = False
        self.captured = None
        self.gravity_scale = 1.0
        self.mushroom = False
        self.mushroom_timer = 0
        self.cappy_power = False
        self.cappy_power_timer = 0
        self.cappy = None
        self.dive_rolling = False
        self.ground_pound = False
        self.invincible = False
        self.invincible_timer = 0

        self.hat = Entity(model='cube', color=color.white, scale=(0.6, 0.2, 0.6), parent=self, position=(0, 0.7, 0))

    def update(self):
        if self.invincible:
            self.invincible_timer -= time.dt
            self.alpha = 128 if int(self.invincible_timer * 10) % 2 == 0 else 255
            if self.invincible_timer <= 0:
                self.invincible = False
                self.alpha = 255

        if self.captured:
            self.control_captured()
            return

        speed = RUN_SPEED if held_keys['shift'] else MOVE_SPEED
        move_direction = (
            Vec3(camera.forward.x, 0, camera.forward.z).normalized() * (held_keys['w'] - held_keys['s']) +
            Vec3(camera.right.x, 0, camera.right.z).normalized() * (held_keys['d'] - held_keys['a'])
        ).normalized()

        if self.grounded and not self.dive_rolling:
            self.velocity.x = move_direction.x * speed
            self.velocity.z = move_direction.z * speed
        else: # Air control
            self.velocity.x += move_direction.x * speed * time.dt * 0.75
            self.velocity.z += move_direction.z * speed * time.dt * 0.75
            air_speed = Vec2(self.velocity.x, self.velocity.z).length()
            if air_speed > speed:
                air_dir = Vec2(self.velocity.x, self.velocity.z).normalized()
                self.velocity.x = air_dir.x * speed
                self.velocity.z = air_dir.y * speed

        if not self.grounded:
            self.velocity.y += GRAVITY.y * self.gravity_scale * time.dt
            self.velocity.y = max(self.velocity.y, MAX_FALL_SPEED)

        self.position += self.velocity * time.dt
        self.check_ground()
        self.check_walls()

        if self.mushroom:
            self.mushroom_timer -= time.dt
            if self.mushroom_timer <= 0:
                self.mushroom = False
                self.scale = Vec3(0.8, 1.2, 0.8)

        if self.cappy_power:
            self.cappy_power_timer -= time.dt
            if self.cappy_power_timer <= 0:
                self.cappy_power = False

        self.hat.position = (0, 0.3, 0) if self.crouching else (0, 0.7, 0)

    def input(self, key):
        if key == 'space':
            if self.captured: self.release_capture()
            else: self.jump()
        elif key == 'q' and not self.captured: self.throw_cappy()
        elif key == 'e' and not self.captured: self.throw_cappy(homing=True)
        elif key == 'f' and self.mushroom and not self.captured: self.throw_fireball()
        elif key == 'x' and not self.grounded and not self.captured: self.dive()
        elif key == 'z' and not self.grounded and self.velocity.y < 0 and not self.captured: self.start_ground_pound()

    def jump(self):
        if self.grounded:
            self.velocity.y = JUMP_SPEED
            self.grounded = False
            self.jump_count = 1
        elif self.jump_count < self.max_jumps and not self.wall_jumping:
            self.velocity.y = JUMP_SPEED * 0.8
            self.jump_count += 1
        self.wall_jumping = False

    def dive(self):
        if not self.dive_rolling:
            self.dive_rolling = True
            forward_dir = Vec3(camera.forward.x, 0, camera.forward.z).normalized()
            self.velocity = forward_dir * MOVE_SPEED * 1.8
            self.velocity.y = 2
            self.rotation_x = -45

    def start_ground_pound(self):
        if not self.ground_pound:
            self.ground_pound = True
            self.velocity = Vec3(0, 2, 0)
            invoke(setattr, self, 'velocity', Vec3(0, -25, 0), delay=0.2)

    def throw_cappy(self, homing=False):
        if self.cappy: return
        target_enemy = None
        if homing:
            enemies = [e for e in scene.entities if isinstance(e, Enemy) and distance(e.position, self.position) < 15]
            if enemies:
                target_enemy = min(enemies, key=lambda e: distance_2d(e.screen_position, Vec2(0,0)))
        self.cappy = Cappy(mario=self, target=target_enemy)
        self.hat.visible = False

    def throw_fireball(self):
        spawn_pos = self.world_position + Vec3(camera.forward.x, 0, camera.forward.z).normalized() * 1 + Vec3(0,0.5,0)
        Fireball(spawn_pos, camera.forward)

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
            self.hat.position = Vec3(0, entity.scale_y/2 + 0.2, 0)
            self.hat.visible = True

    def control_captured(self):
        if self.captured:
            move_direction = (
                Vec3(camera.forward.x, 0, camera.forward.z).normalized() * (held_keys['w'] - held_keys['s']) +
                Vec3(camera.right.x, 0, camera.right.z).normalized() * (held_keys['d'] - held_keys['a'])
            ).normalized()
            self.captured.position += move_direction * 5 * time.dt

    def release_capture(self):
        if self.captured:
            self.position = self.captured.position + Vec3(0, 2, 0)
            self.captured.color = self.captured.original_color
            self.captured.captured = False
            self.hat.parent = self
            self.captured = None
            self.visible = True
            self.velocity.y = JUMP_SPEED * 1.2
            self.grounded = False

    def check_ground(self):
        ray = raycast(self.world_position + Vec3(0,0.1,0), Vec3(0,-1,0), distance=0.2, ignore=[self, self.cappy], debug=False)
        if ray.hit:
            if self.velocity.y <= 0:
                self.grounded = True
                self.position.y = ray.world_point.y + self.scale_y / 2
                self.velocity.y = 0
                self.jump_count = 0
                self.rotation_x = 0
                if self.dive_rolling:
                    self.dive_rolling = False
                    self.velocity.x *= 1.2
                    self.velocity.z *= 1.2
                if self.ground_pound:
                    self.ground_pound = False
                    for e in scene.entities:
                        if isinstance(e, Enemy) and distance(e.position, self.position) < 3:
                            e.take_damage()
                    self.velocity.y = JUMP_SPEED / 2
        else:
            self.grounded = False

    def check_walls(self):
        if not self.grounded:
            move_dir_2d = Vec2(self.velocity.x, self.velocity.z).normalized()
            wall_check_dir = Vec3(move_dir_2d.x, 0, move_dir_2d.y)
            if wall_check_dir.length() == 0: return

            ray = raycast(self.world_position, wall_check_dir, distance=0.5, ignore=[self, self.cappy], debug=False)
            if ray.hit and ray.entity.collider and held_keys['space']:
                self.velocity = ray.world_normal * MOVE_SPEED + Vec3(0, JUMP_SPEED, 0)
                self.wall_jumping = True
                self.jump_count = 1

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
            knockback_dir = (self.position - knockback_from).normalized() if knockback_from else Vec3(0,0,0)
            self.velocity = knockback_dir * 4 + Vec3(0, 5, 0)
            self.grounded = False

    def respawn(self):
        self.position = Vec3(0, 3, 0)
        self.velocity = Vec3(0, 0, 0)
        self.health = 3

# ---- Cappy Class (Modified) ----

class Cappy(Entity):
    def __init__(self, mario, target=None):
        super().__init__(
            model='sphere',
            color=color.white,
            scale=(0.6, 0.2, 0.6),
            position=mario.position + Vec3(0, 1, 0),
            collider='sphere'
        )
        self.mario = mario
        self.speed = CAPPY_SPEED
        self.start_time = time.time()
        self.max_throw_time = CAPPY_RANGE / self.speed

        if target:
            self.state = 'homing'
            self.target = target
            self.direction = (target.position - self.position).normalized()
        else:
            self.state = 'throwing'
            self.target = None
            self.direction = Vec3(camera.forward.x, 0, camera.forward.z).normalized()

    def update(self):
        if self.state in ('throwing', 'homing'):
            self.position += self.direction * self.speed * time.dt
            if time.time() - self.start_time > self.max_throw_time:
                self.state = 'returning'
        elif self.state == 'returning':
            self.direction = (self.mario.position + Vec3(0,1,0) - self.position).normalized()
            self.position += self.direction * self.speed * time.dt
            if distance(self, self.mario) < 1:
                self.mario.cappy = None
                self.mario.hat.visible = True
                destroy(self)

        hit_info = self.intersects()
        if hit_info.hit:
            entity = hit_info.entity
            if entity == self.mario and self.state == 'returning':
                self.mario.cappy = None
                self.mario.hat.visible = True
                destroy(self)
            elif isinstance(entity, Enemy):
                self.mario.capture(entity)
            elif isinstance(entity, Coin):
                entity.collect()
            elif entity != self.mario and entity.collider and self.state != 'returning':
                self.state = 'returning'

        if time.time() - self.start_time > 5: # Failsafe timeout
             if self.state != 'returning': self.state = 'returning'

# ---- Platform and Camera Classes (Modified) ----

class MovingPlatform(Entity):
    def __init__(self, position=(0,0,0), end_position=(0,5,0), **kwargs):
        super().__init__(
            model='cube',
            color=color.gray,
            scale=(4, 0.5, 4),
            position=position,
            collider='box',
            texture='white_cube',
            **kwargs
        )
        self.start_pos = Vec3(position)
        self.end_pos = Vec3(end_position)
        self.speed = 0.5

    def update(self):
        self.position = lerp(self.start_pos, self.end_pos, (math.sin(time.time() * self.speed) + 1) / 2)
        if player.grounded:
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

    def update(self):
        if mouse.locked:
            camera.rotation_y += mouse.velocity[0] * self.rotation_speed
            camera.rotation_x -= mouse.velocity[1] * self.rotation_speed
            camera.rotation_x = clamp(camera.rotation_x, -40, 40)

        target_pos = self.target.world_position + self.offset
        camera_offset = camera.back * self.distance
        desired_position = target_pos + camera_offset

        ray = raycast(target_pos, camera.position - target_pos, distance=self.distance, ignore=[self.target], debug=False)
        if ray.hit:
            camera.position = lerp(camera.position, ray.world_point, time.dt * 20)
        else:
            camera.position = lerp(camera.position, desired_position, time.dt * 10)

        camera.look_at(target_pos)

# ---- World and UI Setup ----

class Kingdom(Entity):
    def __init__(self):
        super().__init__()
        self.create_world()

    def create_world(self):
        Entity(model='plane', texture='grass', color=color.lime, scale=(50, 1, 50), position=(0, -1, 0), collider='box')
        Entity(model='cube', color=color.dark_gray, scale=(1, 15, 20), position=(-25.5, 6.5, 0), collider='box', texture='brick')
        for i in range(10):
            Entity(model='cube', color=color.brown, scale=(random.uniform(2,4), 0.5, random.uniform(2,4)), position=(random.uniform(-20, 20), random.uniform(2, 10), random.uniform(-20, 20)), collider='box')
        MovingPlatform(position=Vec3(10, 3, 0), end_position=Vec3(10, 8, 10))
        MovingPlatform(position=Vec3(-10, 2, 5), end_position=Vec3(-15, 2, -5))
        for i in range(20):
            Coin(position=(random.uniform(-25, 25), random.uniform(1, 15), random.uniform(-25, 25)))
        Enemy(position=(5, 0, 5), patrol_range=10)
        Enemy(position=(-5, 0, -10), patrol_range=5)
        PowerUp(power_type='mushroom', position=(0, 1, 5))
        PowerUp(power_type='cappy_power', position=(0, 1, -5))


class GameUI(Entity):
    def __init__(self):
        super().__init__(parent=camera.ui)
        self.health_text = Text(parent=self, origin=(-.5, .5), text=f"Health: {player.health}", position=(-0.85, 0.45), scale=1.5, background=True)
        self.coins_text = Text(parent=self, origin=(-.5, .5), text=f"Coins: {player.coins}", position=(-0.85, 0.40), scale=1.5, background=True)
        self.lives_text = Text(parent=self, origin=(-.5, .5), text=f"Lives: {player.lives}", position=(-0.85, 0.35), scale=1.5, background=True)

    def update(self):
        self.health_text.text = f"Health: {player.health}"
        self.coins_text.text = f"Coins: {player.coins}"
        self.lives_text.text = f"Lives: {player.lives}"

# ---- Game Initialization ----

player = Mario(position=(0, 3, 0))
camera_controller = OdysseyCamera(player)
kingdom = Kingdom()
game_ui = GameUI()
Sky()
mouse.locked = True

def input(key):
    if key == 'escape':
        mouse.locked = not mouse.locked
    player.input(key)

app.run()

from ursina import *
import math
import random

app = Ursina()

GRAVITY = Vec3(0, -9.81, 0)
MOVE_SPEED = 5
RUN_SPEED = 8
JUMP_SPEED = 5
MAX_FALL_SPEED = -20
CAM_DISTANCE = 6
CAM_HEIGHT = 3
CAPPY_SPEED = 10
CAPPY_RANGE = 5
FIREBALL_SPEED = 15
MUSHROOM_DURATION = 10
CAPPY_POWER_DURATION = 10

class Mario(Entity):
    def __init__(self, **kwargs):
        super().__init__(model='sphere', color=color.red, scale=1, collider='box')
        self.speed = Vec3(0, 0, 0)
        self.on_ground = False
        self.health = 3
        self.coins = 0
        self.moons = 0
        self.lives = 3
        self.jump_count = 0
        self.max_jumps = 3
        self.crouching = False
        self.wall_jumping = False
        self.wall_jump_dir = Vec3(0,0,0)
        self.swimming = False
        self.captured = None
        self.gravity = GRAVITY.y
        self.analog_input = Vec2(0,0)
        self.collider = BoxCollider(self, Vec3(0,0.5,0), Vec3(1,1,1))
        self.mushroom = False
        self.mushroom_timer = 0
        self.cappy_power = False
        self.cappy_power_timer = 0
        self.cappy = None

    def update(self):
        if self.captured:
            self.control_captured()
            return

        move_dir = Vec3(self.analog_input.x, 0, self.analog_input.y)
        world_move = camera.anchor.rotation * move_dir
        target_speed = RUN_SPEED if held_keys['shift'] else MOVE_SPEED
        self.speed.x = world_move.x * target_speed
        self.speed.z = world_move.z * target_speed

        if not self.on_ground and not self.swimming and not self.captured:
            self.speed.y += self.gravity * time.dt
            if self.speed.y < MAX_FALL_SPEED:
                self.speed.y = MAX_FALL_SPEED

        self.position += Vec3(self.speed.x, 0, self.speed.z) * time.dt
        self.check_horizontal_collisions()

        self.position.y += self.speed.y * time.dt
        self.on_ground = False
        self.check_vertical_collisions()

        if held_keys['space']:
            if self.on_ground:
                self.jump()
            elif self.jump_count < self.max_jumps and not self.wall_jumping:
                self.jump()

        self.crouching = held_keys['c'] and self.on_ground
        self.scale_y = max(0.5, self.scale_y - time.dt * 5) if self.crouching else min(1, self.scale_y + time.dt * 5)

        if self.crouching and held_keys['space']:
            self.long_jump()
        if not self.on_ground and held_keys['space']:
            if self.analog_input.x != 0:
                self.side_flip()
            elif self.analog_input.y < 0:
                self.back_flip()
        if held_keys['x'] and not self.on_ground:
            self.dive()
        if held_keys['z'] and not self.on_ground:
            self.ground_pound()
        if held_keys['q']:
            self.cappy_throw()
        if held_keys['e']:
            self.homing_cappy_throw()
        if held_keys['f'] and self.mushroom:
            self.fireball()

        if self.wall_jumping:
            self.speed = self.wall_jump_dir * JUMP_SPEED
            self.wall_jumping = False

        if self.mushroom:
            self.mushroom_timer -= time.dt
            if self.mushroom_timer <= 0:
                self.mushroom = False
                self.scale = Vec3(1,1,1)
        if self.cappy_power:
            self.cappy_power_timer -= time.dt
            if self.cappy_power_timer <= 0:
                self.cappy_power = False

    def jump(self):
        self.speed.y = JUMP_SPEED
        self.on_ground = False
        self.jump_count += 1

    def long_jump(self):
        self.speed.y = JUMP_SPEED / 2
        self.speed.x *= 2
        self.speed.z *= 2
        self.on_ground = False

    def side_flip(self):
        self.speed.y = JUMP_SPEED * 1.5
        self.rotation_y += 180

    def back_flip(self):
        self.speed.y = JUMP_SPEED * 1.5
        self.speed.x = -self.speed.x
        self.speed.z = -self.speed.z

    def dive(self):
        self.speed.y = -JUMP_SPEED
        self.speed.x *= 2
        self.speed.z *= 2

    def ground_pound(self):
        self.speed.y = -JUMP_SPEED * 2

    def cappy_throw(self):
        if not self.cappy:
            self.cappy = Entity(model='sphere', color=color.white, scale=0.3, position=self.position + Vec3(0,1,0))
            direction = camera.forward
            self.cappy.animate_position(self.cappy.position + direction * CAPPY_RANGE, duration=0.5, curve=curve.linear, interrupt='finish')
            invoke(self.return_cappy, delay=0.5)
            for entity in scene.entities:
                if isinstance(entity, (Goomba, BulletBill)) and self.cappy.intersects(entity).hit:
                    entity.stunned = True
                    if self.cappy_power:
                        self.capture(entity)

    def homing_cappy_throw(self):
        if not self.cappy:
            nearest = min([e for e in scene.entities if isinstance(e, (Goomba, BulletBill))], key=lambda e: e.position.distance_to(self.position), default=None)
            if nearest:
                self.cappy = Entity(model='sphere', color=color.white, scale=0.3, position=self.position + Vec3(0,1,0))
                self.cappy.animate_position(nearest.position, duration=0.5, curve=curve.linear, interrupt='finish')
                invoke(self.return_cappy, delay=0.5)
                if self.cappy.intersects(nearest).hit:
                    nearest.stunned = True
                    if self.cappy_power:
                        self.capture(nearest)

    def return_cappy(self):
        if self.cappy:
            destroy(self.cappy)
            self.cappy = None

    def capture(self, entity):
        self.captured = entity
        self.visible = False
        entity.color = color.yellow

    def control_captured(self):
        if held_keys['space']:
            self.release_capture()
        if isinstance(self.captured, Goomba):
            self.captured.position += self.speed * time.dt
        elif isinstance(self.captured, BulletBill):
            self.captured.position += camera.forward * 10 * time.dt

    def release_capture(self):
        self.captured.color = self.captured.original_color
        self.captured = None
        self.visible = True
        self.position = self.position + Vec3(0,1,0)

    def fireball(self):
        fireball = Entity(model='sphere', color=color.orange, scale=0.2, position=self.position + Vec3(0,1,0))
        fireball.animate_position(fireball.position + camera.forward * 10, duration=1, curve=curve.linear, interrupt='finish')
        invoke(destroy, fireball, delay=1)
        for entity in scene.entities:
            if isinstance(entity, (Goomba, BulletBill)) and fireball.intersects(entity).hit:
                destroy(entity)

    def check_horizontal_collisions(self):
        hits = self.intersects()
        for hit in hits:
            if hit.entity and hasattr(hit.entity, 'collider'):
                self.position -= Vec3(self.speed.x, 0, self.speed.z) * time.dt
                if not self.on_ground and hit.entity.collider:
                    normal = hit.world_normal
                    self.wall_jumping = True
                    self.wall_jump_dir = Vec3(normal.x, 0, normal.z) + Vec3(0,1,0)
                break

    def check_vertical_collisions(self):
        hits = self.intersects()
        for hit in hits:
            if hit.entity and hasattr(hit.entity, 'collider'):
                if self.speed.y < 0:
                    self.on_ground = True
                    self.jump_count = 0
                    self.speed.y = 0
                    self.position.y = hit.world_point.y + 0.5
                else:
                    self.speed.y = 0
                    self.position.y = hit.world_point.y - 0.5
                break

class OdysseyCamera(Entity):
    def __init__(self, target, **kwargs):
        super().__init__(**kwargs)
        self.target = target
        self.anchor = Entity(parent=self.target, position=(0, CAM_HEIGHT, 0))
        camera.parent = self.anchor
        camera.position = (0, 0, -CAM_DISTANCE)
        camera.rotation = (10, 0, 0)
        self.sensitivity = Vec2(40, 40)
        self.mode = 'follow'

    def update(self):
        if held_keys['right mouse']:
            self.anchor.rotation_y += mouse.velocity.x * self.sensitivity.x
            camera.rotation_x -= mouse.velocity.y * self.sensitivity.y
            camera.rotation_x = clamp(camera.rotation_x, -30, 60)
        if held_keys['zoom_in']:
            camera.position.z += time.dt * 2
        if held_keys['zoom_out']:
            camera.position.z -= time.dt * 2
        if self.mode == 'follow':
            camera.position = Vec3(0, 0, -CAM_DISTANCE)

class PowerMoon(Entity):
    def __init__(self, position=(0,0,0), **kwargs):
        super().__init__(model='sphere', color=color.yellow, scale=0.5, position=position, collider='box')

    def update(self):
        self.rotation_y += time.dt * 50
        if player.intersects(self).hit:
            player.moons += 1
            destroy(self)

class Coin(Entity):
    def __init__(self, position=(0,0,0), **kwargs):
        super().__init__(model='circle', color=color.orange, scale=0.3, position=position, collider='box', double_sided=True)

    def update(self):
        self.rotation_y += time.dt * 100
        if player.intersects(self).hit:
            player.coins += 1
            destroy(self)

class OneUp(Entity):
    def __init__(self, position=(0,0,0), **kwargs):
        super().__init__(model='cube', color=color.green, scale=0.5, position=position, collider='box')

    def update(self):
        if player.intersects(self).hit:
            player.lives += 1
            destroy(self)

class FireFlower(Entity):
    def __init__(self, position=(0,0,0), **kwargs):
        super().__init__(model='cube', color=color.red, scale=0.5, position=position, collider='box')

    def update(self):
        if player.intersects(self).hit:
            player.mushroom = True
            player.mushroom_timer = MUSHROOM_DURATION
            player.scale = Vec3(1.5,1.5,1.5)
            destroy(self)

class SuperMushroom(Entity):
    def __init__(self, position=(0,0,0), **kwargs):
        super().__init__(model='cube', color=color.brown, scale=0.5, position=position, collider='box')

    def update(self):
        if player.intersects(self).hit:
            player.health += 1
            destroy(self)

class CappyPower(Entity):
    def __init__(self, position=(0,0,0), **kwargs):
        super().__init__(model='cube', color=color.blue, scale=0.5, position=position, collider='box')

    def update(self):
        if player.intersects(self).hit:
            player.cappy_power = True
            player.cappy_power_timer = CAPPY_POWER_DURATION
            destroy(self)

class Goomba(Entity):
    def __init__(self, position=(0,0,0), **kwargs):
        super().__init__(model='cube', color=color.brown, scale=(1,1,1), position=position, collider='box')
        self.direction = Vec3(1,0,0)
        self.speed = 2
        self.stunned = False
        self.original_color = color.brown

    def update(self):
        if self.stunned:
            return
        self.position += self.direction * self.speed * time.dt
        hits = self.intersects()
        for hit in hits:
            if hit.entity and hasattr(hit.entity, 'collider') and hit.entity is not player:
                self.direction *= -1
                break
        if self.intersects(player).hit:
            if player.speed.y < 0:
                destroy(self)
                player.speed.y = JUMP_SPEED / 2
            else:
                player.health -= 1
                player.position = Vec3(0,5,0)

class KoopaTroopa(Entity):
    def __init__(self, position=(0,0,0), **kwargs):
        super().__init__(model='cube', color=color.green, scale=(1,1,1), position=position, collider='box')
        self.direction = Vec3(-1,0,0)
        self.speed = 3
        self.shell = False
        self.original_color = color.green

    def update(self):
        if not self.shell:
            self.position += self.direction * self.speed * time.dt
            hits = self.intersects()
            for hit in hits:
                if hit.entity and hasattr(hit.entity, 'collider') and hit.entity is not player:
                    self.direction *= -1
                    break
            if self.intersects(player).hit:
                if player.speed.y < 0:
                    self.shell = True
                    self.color = color.dark_gray
                    player.speed.y = JUMP_SPEED / 2
                else:
                    player.health -= 1
                    player.position = Vec3(0,5,0)
        else:
            self.position += self.direction * RUN_SPEED * time.dt
            hits = self.intersects()
            for hit in hits:
                if hit.entity and hasattr(hit.entity, 'collider') and hit.entity is not player:
                    self.direction *= -1
                    break
            if self.intersects(player).hit:
                player.health -= 1
                player.position = Vec3(0,5,0)

class BulletBill(Entity):
    def __init__(self, position=(0,0,0), **kwargs):
        super().__init__(model='sphere', color=color.black, scale=1, position=position, collider='box')
        self.timer = 5
        self.speed = 2
        self.stunned = False
        self.original_color = color.black

    def update(self):
        if self.stunned:
            return
        self.timer -= time.dt
        if self.timer <= 0:
            destroy(self)
            if player.position.distance_to(self.position) < 5:
                player.health -= 1
        else:
            direction = (player.position - self.position).normalized()
            self.position += direction * self.speed * time.dt

class ChainChomp(Entity):
    def __init__(self, position=(0,0,0), **kwargs):
        super().__init__(model='cube', color=color.gray, scale=(2,2,2), position=position, collider='box')
        self.start_pos = position
        self.speed = 5
        self.lunge = False

    def update(self):
        if self.lunge:
            self.position += (player.position - self.position).normalized() * self.speed * time.dt
            if self.position.distance_to(player.position) < 1:
                self.lunge = False
        else:
            self.position += (self.start_pos - self.position).normalized() * self.speed * time.dt
            if random.random() < 0.01:
                self.lunge = True
        if self.intersects(player).hit:
            player.health -= 1
            player.position = Vec3(0,5,0)

class Boo(Entity):
    def __init__(self, position=(0,0,0), **kwargs):
        super().__init__(model='sphere', color=color.white, scale=1, position=position, collider='box')
        self.speed = 2
        self.original_color = color.white

    def update(self):
        player_dir = (player.position - camera.position).normalized()
        boo_dir = (self.position - camera.position).normalized()
        if player_dir.dot(boo_dir) < 0.5:
            direction = (player.position - self.position).normalized()
            self.position += direction * self.speed * time.dt
        if self.intersects(player).hit:
            player.health -= 1
            player.position = Vec3(0,5,0)

class Kingdom(Entity):
    def __init__(self):
        super().__init__(name='kingdom')
        self.ground = Entity(model='plane', texture='white_cube', texture_scale=(10,10), collider='box', scale=(50,1,50), color=color.tan)
        self.ground.position = (0,-1,0)
        self.platforms = []
        positions = [(-5,2,5), (5,4,5), (0,3,-5)]
        for pos in positions:
            platform = Entity(model='cube', scale=(5,1,5), color=color.gray, collider='box', position=pos)
            self.platforms.append(platform)
            platform.animate_y(pos[1] + 2, duration=2, loop=True, curve=curve.in_out_sine)
        self.quicksand = Entity(model='cube', scale=(10,1,10), position=(15,-1,0), color=color.orange, collider='box', tag='hazard')
        self.wall_left = Entity(model='cube', scale=(1,5,20), position=(-10,2,0), color=color.dark_gray, collider='box')
        self.wall_right = Entity(model='cube', scale=(1,5,20), position=(10,2,0), color=color.dark_gray, collider='box')
        self.water = Entity(model='cube', scale=(10,1,10), position=(0,-1,15), color=color.blue, collider='box', tag='water')
        self.moons = [PowerMoon(position=(0,2,0)), PowerMoon(position=(5,6,5)), PowerMoon(position=(-5,4,-5))]
        for i in range(10):
            Coin(position=(random.uniform(-8,8), random.uniform(0,2), random.uniform(-8,8)))
        OneUp(position=(0,0,10))
        FireFlower(position=(2,0,2))
        SuperMushroom(position=(-2,0,-2))
        CappyPower(position=(4,0,4))
        Goomba(position=(3,0,3))
        KoopaTroopa(position=(-3,0,-3))
        BulletBill(position=(5,0,5))
        ChainChomp(position=(7,0,7))
        Boo(position=(-5,0,-5))

class GameUI(Entity):
    def __init__(self):
        super().__init__()
        self.moon_text = Text(text=f"Moons: {player.moons}", position=(-0.7,0.45), scale=2)
        self.coin_text = Text(text=f"Coins: {player.coins}", position=(-0.7,0.4), scale=2)
        self.life_text = Text(text=f"Lives: {player.lives}", position=(-0.7,0.35), scale=2)
        self.health_text = Text(text=f"Health: {player.health}", position=(-0.7,0.3), scale=2)

    def update(self):
        self.moon_text.text = f"Moons: {player.moons}"
        self.coin_text.text = f"Coins: {player.coins}"
        self.life_text.text = f"Lives: {player.lives}"
        self.health_text.text = f"Health: {player.health}"

def input(key):
    if key == 'w':
        player.analog_input.y = 1
    elif key == 's':
        player.analog_input.y = -1
    if key == 'a':
        player.analog_input.x = -1
    elif key == 'd':
        player.analog_input.x = 1

def input_up(key):
    if key in ['w','s']:
        player.analog_input.y = 0
    if key in ['a','d']:
        player.analog_input.x = 0

player = Mario(position=(0,0,0))
camera_controller = OdysseyCamera(player)
kingdom = Kingdom()
ui = GameUI()

def late_update():
    hits = player.intersects()
    for hit in hits:
        if hit.entity and hit.entity.tag == 'hazard':
            player.position = Vec3(0,5,0)
            player.health -= 1

    if player.intersects(kingdom.water).hit:
        player.swimming = True
        player.speed.y = max(player.speed.y + time.dt * 2, 2)
    else:
        player.swimming = False

app.run()

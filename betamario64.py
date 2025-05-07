from ursina import *
import random
import math

app = Ursina()

# Constants
GRAVITY = 1.8
WALK_SPEED = 5
RUN_SPEED = 10
JUMP_FORCE = 15
MAX_JUMPS = 3
CAMERA_DISTANCE = 12
CAMERA_HEIGHT = 4
CAMERA_ROTATION_SPEED = 100

# Game State
collected_stars = 0

# Player Class
class Mario(Entity):
    def __init__(self):
        super().__init__(
            model='cube',
            color=color.red,
            scale=(1, 1.8, 1),
            collider='box',
            position=(0, 10, 0)
        )
        self.velocity = Vec3(0, 0, 0)
        self.jumps_left = MAX_JUMPS
        self.grounded = False

    def update(self):
        # Movement
        move_dir = Vec3(0, 0, 0)
        cam_forward = camera.forward
        cam_forward.y = 0
        cam_forward = cam_forward.normalized()
        cam_right = camera.right
        cam_right.y = 0
        cam_right = cam_right.normalized()

        if held_keys['w']:
            move_dir += cam_forward
        if held_keys['s']:
            move_dir -= cam_forward
        if held_keys['a']:
            move_dir -= cam_right
        if held_keys['d']:
            move_dir += cam_right

        speed = RUN_SPEED if held_keys['shift'] else WALK_SPEED
        if move_dir.length() > 0:
            move_dir = move_dir.normalized()
            self.velocity.x = move_dir.x * speed
            self.velocity.z = move_dir.z * speed
        else:
            self.velocity.x = 0
            self.velocity.z = 0

        # Gravity
        self.velocity.y -= GRAVITY * time.dt
        self.velocity.y = clamp(self.velocity.y, -50, 50)

        # Ground Check
        ray = raycast(self.position, Vec3(0, -1, 0), distance=1.1, ignore=(self,))
        if ray.hit:
            self.grounded = True
            self.velocity.y = max(0, self.velocity.y)
            self.y = ray.world_point.y + 0.9
            self.jumps_left = MAX_JUMPS
        else:
            self.grounded = False

        # Apply Movement
        self.position += self.velocity * time.dt

    def jump(self):
        if self.jumps_left > 0:
            self.velocity.y = JUMP_FORCE * (1 - (MAX_JUMPS - self.jumps_left) * 0.15)
            self.grounded = False
            self.jumps_left -= 1

# Level Geometry
ground = Entity(model='plane', scale=100, color=color.green, collider='box')
platforms = [
    Entity(model='cube', scale=(10, 1, 10), position=(10, 2, 10), color=color.brown, collider='box'),
    Entity(model='cube', scale=(5, 1, 5), position=(-10, 4, -10), color=color.brown, collider='box')
]

# Stars
stars = []
for i in range(5):
    star = Entity(
        model='sphere',
        color=color.yellow,
        scale=0.5,
        position=(random.uniform(-20, 20), random.uniform(2, 10), random.uniform(-20, 20))
    )
    stars.append(star)

# Enemies
class Enemy(Entity):
    def __init__(self, position):
        super().__init__(
            model='sphere',
            color=color.red,
            scale=0.5,
            position=position,
            collider='sphere'
        )
        self.direction = 1
        self.speed = 2

    def update(self):
        self.x += self.speed * self.direction * time.dt
        if abs(self.x - self.position[0]) > 5:
            self.direction *= -1

enemies = [Enemy((random.uniform(-10, 10), 0.5, random.uniform(-10, 10))) for _ in range(3)]

# HUD
star_text = Text(text=f"Stars: {collected_stars}", position=(-0.8, 0.45), scale=2)

# Player Instance
player = Mario()

# Camera Control
camera_angle = 0

def update():
    global collected_stars, camera_angle

    # Camera
    if held_keys['left arrow']:
        camera_angle -= CAMERA_ROTATION_SPEED * time.dt
    if held_keys['right arrow']:
        camera_angle += CAMERA_ROTATION_SPEED * time.dt

    rad = math.radians(camera_angle)
    cam_x = player.x + math.sin(rad) * CAMERA_DISTANCE
    cam_z = player.z + math.cos(rad) * CAMERA_DISTANCE
    camera.position = (cam_x, player.y + CAMERA_HEIGHT, cam_z)
    camera.look_at(player.position + Vec3(0, 1, 0))

    # Star Collection
    for star in stars[:]:
        if distance(player, star) < 1.5:
            destroy(star)
            stars.remove(star)
            collected_stars += 1
            star_text.text = f"Stars: {collected_stars}"

    # Enemy Interaction
    for enemy in enemies[:]:
        if distance(player, enemy) < 1:
            if player.y > enemy.y + 0.5:
                destroy(enemy)
                enemies.remove(enemy)
            else:
                player.position = (0, 10, 0)
                player.velocity = Vec3(0, 0, 0)

    # HUD Update
    star_text.text = f"Stars: {collected_stars}"

def input(key):
    if key == 'space':
        player.jump()
    if key == 'escape':
        application.quit()

# Run Game
window.title = "Mario 64 Ursina Port - No Media"
app.run()

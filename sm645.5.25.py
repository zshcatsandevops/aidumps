from ursina import *

app = Ursina()
window.size = (600, 400)

class Player(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dy = 0
        self.on_ground = False
        self.collider = 'box'

    def update(self):
        # Movement
        speed = 5
        if held_keys['w']:
            move_dir = camera.forward
            move_dir.y = 0
            self.position += move_dir.normalized() * speed * time.dt
        if held_keys['s']:
            move_dir = camera.forward
            move_dir.y = 0
            self.position += -move_dir.normalized() * speed * time.dt
        if held_keys['a']:
            move_dir = camera.right
            move_dir.y = 0
            self.position += -move_dir.normalized() * speed * time.dt
        if held_keys['d']:
            move_dir = camera.right
            move_dir.y = 0
            self.position += move_dir.normalized() * speed * time.dt

        # Jumping
        if held_keys['space'] and self.on_ground:
            self.dy = 5
            self.on_ground = False

        # Apply gravity
        self.dy -= 0.1 * time.dt
        self.y += self.dy * time.dt

        # Ground detection
        bottom_pos = self.position + Vec3(0, -1, 0)
        hit_info = raycast(bottom_pos, direction=(0,-1,0), distance=0.1, ignore=(self,))
        if hit_info.hit:
            self.on_ground = True
            self.dy = 0
            ground_y = hit_info.point.y
            desired_y = ground_y + 1
            self.y = desired_y
        else:
            self.on_ground = False

        # Check for enemy collision
        for enemy in enemies[:]:
            if self.intersects(enemy).hit:
                if self.y > enemy.y + 0.5:
                    destroy(enemy)
                    enemies.remove(enemy)
                else:
                    self.position = (0,1,0)

        # Check for star collection
        for star in stars[:]:
            if self.intersects(star).hit:
                destroy(star)
                stars.remove(star)

class Enemy(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.speed = 2
        self.collider = 'box'

    def update(self):
        self.x += self.speed * time.dt
        if self.x > 5 or self.x < 0:
            self.speed *= -1

# Create player
player = Player(model='cube', color=color.red, scale=(1,2,1), position=(0,1,0))

# Create ground
ground = Entity(model='plane', scale=100, color=color.green, collider='box')

# Create platform
platform = Entity(model='cube', scale=(5,1,5), position=(5,2,0), color=color.blue, collider='box')

# Create enemy
enemy = Enemy(model='cube', scale=(1,1,1), position=(0,1,5), color=color.orange)
enemies = [enemy]

# Create star
star = Entity(model='sphere', scale=0.5, position=(3,2,3), color=color.yellow, collider='sphere')
stars = [star]

# Set camera
camera.parent = player
camera.position = (0, 5, -10)
camera.rotation_x = 30

app.run()

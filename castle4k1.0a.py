from random import randint
import time
from ursina import (
    Ursina,
    Entity,
    Vec3,
    Text,
    Sky,
    DirectionalLight,
    PointLight,
    camera,
    mouse,
    held_keys,
    destroy,
    color,
    raycast  # Added for proper collision
)


def make_box(size, pos, col=color.white, **kwargs):
    """Create a box shaped entity."""
    return Entity(model='cube', color=col, scale=size, position=pos, collider='box', **kwargs)


class Player(Entity):
    """Improved third-person platformer player with better physics."""

    def __init__(self, **kwargs):
        super().__init__(
            model='capsule', 
            color=color.orange, 
            scale=(1, 2, 1), 
            collider='box', 
            **kwargs
        )
        self.speed = 5
        self.jump_power = 8
        self.velocity_y = 0
        self.gravity = 20
        self.jumps = 0
        self.max_jumps = 2
        self.grounded = False
        camera.parent = self
        camera.position = (0, 3, -12)
        camera.rotation = (15, 0, 0)
        mouse.locked = False

    def update(self):
        # Horizontal movement
        move = Vec3(
            held_keys['d'] - held_keys['a'],
            0,
            held_keys['w'] - held_keys['s']
        ).normalized()
        self.position += (self.right * move.x + self.forward * move.z) * self.speed * time.dt

        # Gravity and jumping
        self.velocity_y -= self.gravity * time.dt
        self.y += self.velocity_y * time.dt
        
        # Fixed ground collision using raycasting
        ray = raycast(self.position, (0, -1, 0), distance=1.5, ignore=[self])
        self.grounded = ray.hit
        
        if self.grounded:
            self.velocity_y = 0
            self.jumps = 0
            # Adjust player to stand on surface
            if ray.world_point:
                self.y = ray.world_point.y + self.scale_y/2

        # Jump handling
        if held_keys['space'] and (self.grounded or self.jumps < self.max_jumps):
            self.velocity_y = self.jump_power
            self.jumps += 1
            self.grounded = False


class Door(Entity):
    """Improved door with teleport cooldown to prevent glitches."""

    def __init__(self, target, label='Door', **kw):
        super().__init__(
            model='cube', 
            color=color.brown, 
            scale=(2, 3, 0.2), 
            collider='box',
            trigger=True,  # FIXED: Added trigger capability
            **kw
        )
        Text(parent=self, text=label, y=1.8, scale=1.5, origin=(0, 0))
        self.target = target
        self.last_teleport = 0
        self.cooldown = 1.0  # seconds

    def on_trigger_enter(self, other):
        if other == player and time.time() > self.last_teleport + self.cooldown:
            player.position = self.target
            player.velocity_y = 0  # Reset vertical velocity
            self.last_teleport = time.time()


class Star(Entity):
    """Collectible star with rotation animation."""

    def __init__(self, **kw):
        super().__init__(
            model='sphere', 
            color=color.yellow, 
            scale=0.5, 
            collider='box', 
            **kw
        )
        self.rotation_speed = Vec3(0, 60, 0)

    def update(self):
        self.rotation += self.rotation_speed * time.dt

    def on_trigger_enter(self, other):
        if other == player:
            destroy(self)


class Castle(Entity):
    """Improved castle with better layout and collision."""

    def __init__(self):
        super().__init__()
        # Main castle structure
        make_box((20, 10, 20), (0, 5, 0), color.light_gray)
        make_box((4, 6, 4), (0, 13, 0), color.red)
        
        # Entrance
        make_box((14, 1, 2), (0, 0, 8), color.brown)
        Door(target=Vec3(0, 1, -5), position=(0, 1, 10), label='Enter')
        
        # Interior hub
        make_box((18, 8, 18), (0, 5, -20), color.azure)
        make_box((6, 1, 4), (0, 1, -25), color.gray)
        
        # Interior doors
        Door(target=Vec3(0, 1, -40), position=(-5, 1, -29), label='Bob-Omb')
        Door(target=Vec3(10, 1, -40), position=(5, 1, -29), label='Whomp')
        Door(target=Vec3(-10, 1, -40), position=(0, 4, -35), label='Jolly')
        Door(target=Vec3(0, 1, -60), position=(0, 5, -22), label='Slide', scale=(1,2,0.1))
        
        # Stars
        Star(position=(2,2,-22))
        Star(position=(-3,2,-26))


def build_level_area(pos: Vec3):
    platform = make_box((10,1,10), pos + Vec3(0,-1,0), color.random_color())
    platform.collider = 'box'
    Star(position=pos + Vec3(2,1,0))


class WeirdZone(Entity):
    """Glitched area that appears randomly."""

    def __init__(self):
        super().__init__()
        # FIXED: Add parent relationship for proper cleanup
        self.platform = make_box((30,1,30), (0,0,-80), color.random_color(), parent=self)
        self.light = PointLight(position=(0,5,-80), color=color.random_color(), parent=self)
        self.stars = [

            Star(position=(randint(-10,10), 1, -80+randint(-10,10)), parent=self)
            for _ in range(5)
        ]


app = Ursina()
Sky(texture='sky_sunset')
DirectionalLight()

player = Player(position=(0,1,15))
castle = Castle()

# Build level areas
level_positions = [Vec3(0,1,-40), Vec3(10,1,-40), Vec3(-10,1,-40), Vec3(0,1,-60)]
for pos in level_positions:
    build_level_area(pos)

# Toad character
Toad = Entity(
    model='sphere', 
    color=color.white, 
    position=(3,1,-23), 
    scale=(0.8, 1.2, 0.8),
    collider='box'
)
toad_msg = Text('', position=(0.4,-0.45))

next_warp = time.time() + randint(60,120)
current_weird_zone = None


def update():
    global next_warp, current_weird_zone
    
    # Toad interaction
    if player.intersects(Toad).hit:
        toad_msg.text = 'Welcome to the castle!'
    else:
        toad_msg.text = ''

    # Warp to weird zone
    if time.time() > next_warp:
        # Clean up previous zone through parent relationship
        if current_weird_zone:
            destroy(current_weird_zone)  # Destroy parent destroys children
            
        current_weird_zone = WeirdZone()
        player.position = Vec3(0, 10, -80)  # Start above platform
        next_warp = time.time() + randint(60,120)


app.run() 

#!/usr/bin/env python3
"""
plexus.py – Catsan MIPS mini‑platformer (refactor 2025‑06‑21)
------------------------------------------------------------
• SM64‑inspired physics w/ variable jump, proper Δ‑time scaling
• Collect 10 spinning stars to win; victory banner tween
• Spring‑arm camera with smooth yaw (Q/E) and clamped pitch (mouse)
• CLI flags: --hd (1280×720), --ultra (1920×1080 windowed)
"""

from ursina import *
from random import uniform
from dataclasses import dataclass
import sys, math

# ─────────────────────────── CONFIG ────────────────────────────
@dataclass
class Config:
    gravity      : float = 14.0     # m/s²  (scaled to game units)
    walk_acc     : float = 18.0
    run_acc      : float = 34.0
    friction     : float = 12.0
    max_walk     : float = 7.0
    max_run      : float = 12.0
    jump_vel     : float = 5.2
    jump_hold_ms : int   = 250
    term_vel     : float = -30.0
    stars_total  : int   = 10

CFG = Config()

# ─────────────────────── window bootstrap ──────────────────────
HD      = "--hd"     in sys.argv
ULTRA   = "--ultra"  in sys.argv
window.title      = 'Catsan MIPS Project – Mini Plexus'
window.borderless = False
window.size       = (1920,1080) if ULTRA else (1280,720) if HD else (600,400)

app = Ursina()

# ───────────────────── utility helpers ─────────────────────────
def lerp(a, b, t): return a + (b - a) * t

# ────────────────────────── PLAYER ─────────────────────────────
class PlayerController(Entity):
    def __init__(self):
        super().__init__(
            model='cube', color=color.red, scale=(0.6,1.2,0.6),
            collider='box', position=(0,2,0)
        )
        # Simple decorator “hat”
        Entity(parent=self, model='cube', color=color.blue,
               y=-0.5, scale=(0.7,0.5,0.6))
        for x in (-.17,.17):
            Entity(parent=self, model='sphere', color=color.yellow,
                   x=x, y=-.15, z=.3, scale=.08)

        self.velocity      = Vec3(0)
        self.grounded      = False
        self._jump_pressed = False
        self._jump_time    = 0

    # ───────── movement core ─────────
    def _input_vector(self):
        dx = held_keys['d'] - held_keys['a']
        dz = held_keys['w'] - held_keys['s']
        mag = math.hypot(dx, dz)
        if not mag: return Vec3()
        return Vec3(dx/mag, 0, dz/mag)

    def update(self):
        dt = time.dt
        move = self._input_vector()
        running = held_keys['shift']
        acc  = CFG.run_acc if running else CFG.walk_acc
        vmax = CFG.max_run if running else CFG.max_walk

        # Horizontal accel
        self.velocity += move * acc * dt
        # Friction
        self.velocity.x = lerp(self.velocity.x, 0, CFG.friction*dt) if not move.x else self.velocity.x
        self.velocity.z = lerp(self.velocity.z, 0, CFG.friction*dt) if not move.z else self.velocity.z
        # Clamp horizontal
        h_spd = math.hypot(self.velocity.x, self.velocity.z)
        if h_spd > vmax:
            self.velocity.x *= vmax / h_spd
            self.velocity.z *= vmax / h_spd

        # Jump logic
        if self.grounded and held_keys['space']:
            self.velocity.y = CFG.jump_vel
            self._jump_pressed, self._jump_time = True, 0

        if self._jump_pressed:
            self._jump_time += dt*1000          # ms
            if not held_keys['space'] or self._jump_time > CFG.jump_hold_ms:
                self._jump_pressed = False

        # Variable height: bleed velocity if jump is released early
        if not self._jump_pressed and self.velocity.y > 0:
            self.velocity.y -= CFG.gravity * 1.6 * dt

        # Gravity
        self.velocity.y -= CFG.gravity * dt
        self.velocity.y = max(self.velocity.y, CFG.term_vel)

        # Integrate
        self.position += self.velocity * dt

        # Ground collision
        self.grounded = self.y <= 1
        if self.grounded:
            self.y = 1
            self.velocity.y = 0

        # Face movement dir
        if move.length():
            self.rotation_y = math.degrees(math.atan2(move.x, move.z))

# ─────────────────────────── STAR ──────────────────────────────
class Star(Entity):
    def __init__(self, pos):
        super().__init__(
            model='sphere', color=color.yellow, scale=.35,
            position=pos, collider='box'
        )
        self._base_y = pos.y

    def update(self):
        self.rotation_y += time.dt * 120            # spin
        self.y = self._base_y + math.sin(time.time()*4)*.1  # bob

# ─────────────────────────── LEVEL ─────────────────────────────
class Level:
    def __init__(self):
        self.player = PlayerController()
        self.camera_pivot = Entity(parent=self.player, z=-10, y=2.5)
        camera.parent = self.camera_pivot
        camera.rotation_x = 14
        self.cam_yaw  = 0

        # Terrain
        def plat(x,y,z,sx,sy,sz,c): 
            return Entity(model='cube', color=c, scale=(sx,sy,sz),
                          position=(x,y,z), collider='box')
        plat(0,0,0, 18,1,18, color.green)
        plat(6,1,6, 4,2,4, color.lime)
        plat(-4,1,4,2,1,2,color.azure)
        plat(0,1,7, 3,1,2, color.gold)
        plat(-7,1,-5,3,1,3,color.red)

        # Collectibles
        self.stars = [Star((uniform(-8,8),1.5,uniform(-8,8)))
                      for _ in range(CFG.stars_total)]
        self.ui_counter = Text(text='Stars: 0/{}'.format(CFG.stars_total),
                               origin=(0,-.45), scale=2, background=True)

        # Sky & lighting
        Sky(color=color.rgb(155,200,255))
        DirectionalLight(y=3, z=2, shadows=True, color=color.rgb(255,248,228))

    # ───────── frame update ─────────
    def update(self):
        # Camera yaw with easing
        if held_keys['q']: self.cam_yaw += 60 * time.dt
        if held_keys['e']: self.cam_yaw -= 60 * time.dt
        self.camera_pivot.rotation_y = lerp(
            self.camera_pivot.rotation_y, self.cam_yaw, 10*time.dt)

        # Pickups
        for s in self.stars[:]:
            if self.player.intersects(s).hit:
                destroy(s)
                self.stars.remove(s)
                got = CFG.stars_total - len(self.stars)
                self.ui_counter.text = f'Stars: {got}/{CFG.stars_total}'
                if not self.stars: invoke(self.victory, delay=.1)

    def victory(self):
        t = Text(text='ALL STARS COLLECTED!', origin=(0,0), scale=3,
                 color=color.azure, background=True, alpha=0)
        t.animate('alpha', 1, duration=.6, curve=curve.out_expo)
        application.pause()

# ────────────────────────── META BINDINGS ──────────────────────
def global_input(key):
    if key == 'escape': application.quit()
    elif key == 'tab': application.pause() if not application.paused else application.resume()
    elif key == 'f3': window.fps_counter.enabled = not window.fps_counter.enabled

# ─────────────────────────── RUN GAME ──────────────────────────
if __name__ == '__main__':
    level = Level()
    window.fps_counter.enabled = False
    app.run(update=level.update, input=global_input)

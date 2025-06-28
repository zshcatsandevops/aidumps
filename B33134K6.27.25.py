from ursina import *
import random, math, time as pytime

app = Ursina(title="B3313", borderless=False, vsync=True)

# Procedural glitch castle using only primitive models and default colors
castle = Entity(model=None, position=(0, -10, 20), rotation_y=15, scale=10)
Entity(parent=castle, model="cube", position=(0, 1, 0), scale=(2, 2, 2), color=color.dark_gray)
Entity(parent=castle, model="cone", position=(0, 2.5, 0), scale=(1.5, 1, 1.5), color=color.gray)
Entity(parent=castle, model="cube", position=(-2, 0, 0), scale=(1, 1, 1), color=color.dark_gray)
Entity(parent=castle, model="cube", position=(2, 0, 0), scale=(1, 1, 1), color=color.dark_gray)

Sky(color=color.rgb(20, 0, 30))

# UI Menu
menu_parent = Entity(parent=camera.ui)
logo = Text(parent=menu_parent, text="B3313", scale=12, origin=(0, 0), y=0.3, color=color.white)

info_text = Text(parent=menu_parent, text="", scale=2, origin=(0, 0), y=-0.4, color=color.lime, enabled=False)

def write_info(msg):
    info_text.enabled = True
    info_text.text = msg
    info_text.alpha = 0
    info_text.animate("alpha", 1, duration=0.4)

def glitch_sound():  # Simulate with camera shake only!
    camera.position += Vec3((random.random() - 0.5)*0.2, (random.random() - 0.5)*0.2, 0)

def hover_sound():
    pass  # No audio!

def start_game():
    glitch_sound()
    print("--- Starting Game ---")
    write_info("The castle awaits.")

def options_menu():
    glitch_sound()
    print("--- Options Menu ---")
    write_info("There are no options.")

def exit_game():
    glitch_sound()
    application.quit()

button_dict = {
    "Start": Func(start_game),
    "Options": Func(options_menu),
    "Exit": Func(exit_game),
}

# No ButtonList, custom Button layout for pure control!
buttons = []
y0 = 0
for i, (name, func) in enumerate(button_dict.items()):
    btn = Button(
        text=name,
        color=color.rgba(0, 0, 0, 0),
        highlight_color=color.rgba(255, 0, 0, 50),
        pressed_color=color.rgba(255, 0, 0, 100),
        parent=menu_parent,
        scale=(.3, .08),
        y=y0 - i * .12
    )
    btn.text_entity.color = color.rgba(255, 255, 255, 200)
    btn.on_click = func
    def on_enter(b=btn):
        b.text_entity.color = color.red
        hover_sound()
    def on_exit(b=btn):
        b.text_entity.color = color.rgba(255,255,255,200)
    btn.on_mouse_enter = on_enter
    btn.on_mouse_exit = on_exit
    buttons.append(btn)

# VHS scanlines (procedural quads, no assets)
scanlines = Entity(parent=camera.ui, scale=(2, 1), z=1)
for i in range(12):
    Entity(parent=scanlines, model="quad", scale_y=0.005, color=color.rgba(0, 0, 0, 100), y=lerp(-0.5, 0.5, i / 12))

# Camera/Logo Glitch
glitch_intensity = 0.05
camera_pan_speed = 0.1

def update():
    # Gentle camera drift
    camera.x = math.sin(pytime.time() * camera_pan_speed) * 0.005
    camera.y = math.cos(pytime.time() * camera_pan_speed * 0.7) * 0.005

    # Random glitch
    if random.random() < glitch_intensity:
        camera.position += Vec3((random.random() - 0.5)*0.2, (random.random() - 0.5)*0.2, 0)
        logo.color = random.choice([color.red, color.white, color.cyan, color.black])
        logo.rotation_z += (random.random() - 0.5) * 2
    else:
        logo.color = color.white
        logo.rotation_z = lerp(logo.rotation_z, 0, time.dt * 5)

    scanlines.y = math.sin(pytime.time() * 2) * 0.005
    if random.random() < 0.01:
        scanlines.y += (random.random() - 0.5) * 0.1

# NULL Easter Egg (no assets!)
key_sequence = []
def activate_null_state():
    print("--- NULL STATE ACTIVATED ---")
    for c in menu_parent.children[:]:
        destroy(c)
    destroy(castle)
    destroy(scanlines)
    camera.orthographic = True
    camera.fov = 1
    camera.position = (0, 0)
    camera.rotation = (0, 0, 0)
    Sky(color=color.black)
    Text(text="NULL", origin=(0, 0), scale=20, color=color.red)

def input(key):
    if isinstance(key, str) and len(key) == 1 and key.isalnum():
        key_sequence.append(key.lower())
        if len(key_sequence) > 4:
            key_sequence.pop(0)
        if key_sequence == ["n", "u", "l", "l"]:
            activate_null_state()

app.run()

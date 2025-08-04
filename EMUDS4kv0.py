import tkinter as tk
from tkinter import font
from PIL import Image, ImageTk, ImageEnhance
import random, time, math

# --- CORE EMULATOR CONSTANTS ---
FB_W, FB_H = 256, 192 # Nintendo DS Screen Resolution

# --- THE NEW AND IMPROVED PROCEDURAL VIBES ENGINE ---
class NdsVibesEngineCore:
    """
    This is no longer a 'Fake' core. This is a procedural engine that simulates
    the aesthetic of a running homebrew application on a real NDS. It generates
    structured, dynamic data to make the debugger feel alive.
    """
    def __init__(self):
        self.rom_name = "VIBES_ENGINE_MKII.NDS"
        self.reset()

    def reset(self):
        """Resets the core to a consistent initial state."""
        self.arm9 = [0]*16
        self.arm7 = [0]*16
        self.cpsr9 = 0x1F  # System Mode
        self.cpsr7 = 0x1F  # System Mode
        self.frame = 0
        self.cycle_counter = 0

        # Initializing registers to sane-looking startup values
        self.arm9[13] = 0x0380FFDC  # SP (Stack Pointer) for ARM9
        self.arm9[15] = 0x02000040  # PC (Program Counter) for ARM9
        self.arm7[13] = 0x0380FFB0  # SP for ARM7
        self.arm7[15] = 0x02380020  # PC for ARM7

        # Framebuffers for top and bottom screens
        self.fb_top = Image.new("RGB", (FB_W, FB_H), "black")
        self.fb_bot = Image.new("RGB", (FB_W, FB_H), "black")
        
        # A small, persistent "RAM" space for the memory viewer
        self.main_ram = [random.randint(0, 255) for _ in range(4096)]

    def step(self):
        """
        Executes a single frame's worth of "emulation".
        All operations are deterministic based on the frame count to produce
        a coherent, evolving simulation.
        """
        self.frame += 1
        self.cycle_counter += 66_800_000 // 60 # Simulate ARM9 cycles per frame

        # --- Simulate Register Activity ---
        # PC increments, simulating code execution.
        self.arm9[15] = (self.arm9[15] + random.randint(4, 32) * 4) & 0xFFFFFFFF
        self.arm7[15] = (self.arm7[15] + random.randint(2, 16) * 4) & 0xFFFFFFFF

        # Other registers change based on procedural patterns
        for i in range(12):
            self.arm9[i] = (self.arm9[i] + int(math.sin(self.frame * 0.1 + i) * 1000)) & 0xFFFFFFFF
            self.arm7[i] = (self.arm7[i] + int(math.cos(self.frame * 0.05 + i) * 500)) & 0xFFFFFFFF
        
        # Link Register (R14) might get a new value occasionally
        if self.frame % 30 == 0:
            self.arm9[14] = self.arm9[15] + random.randint(1, 5) * 4
        
        # --- Simulate Memory Activity ---
        # Write some patterns into our fake RAM
        for i in range(16):
            addr = (self.frame * 16 + i) % len(self.main_ram)
            val = (self.frame + i*10) % 256
            self.main_ram[addr] = val

        # --- Procedural Framebuffer Rendering (The "Graphics Engine") ---
        self._render_plasma_screen(self.fb_top, self.frame, 1.0, 0.5, 0.8)
        self._render_starfield_screen(self.fb_bot, self.frame)

    def _render_plasma_screen(self, fb, frame, r_freq, g_freq, b_freq):
        """Generates a classic demo-scene plasma effect."""
        t = frame * 0.05
        for y in range(FB_H):
            for x in range(FB_W):
                v = math.sin(x * 0.05 + t)
                v += math.sin((y * 0.05) + t)
                v += math.sin((x + y) * 0.05 + t)
                cx = x + 0.5 * math.sin(t / 5.0)
                cy = y + 0.5 * math.cos(t / 3.0)
                v += math.sin(math.sqrt((cx-FB_W/2)**2 + (cy-FB_H/2)**2) * 0.02 + t)
                
                # Normalize and colorize
                vn = (v + 4.0) / 8.0 # Normalize to 0-1 range
                r = int(20 + 100 * (math.sin(vn * 2 * math.pi * r_freq) + 1) / 2)
                g = int(20 + 100 * (math.sin(vn * 2 * math.pi * g_freq) + 1) / 2)
                b = int(50 + 100 * (math.sin(vn * 2 * math.pi * b_freq) + 1) / 2)
                fb.putpixel((x, y), (r,g,b))

    def _render_starfield_screen(self, fb, frame):
        """Generates a classic 3D starfield effect for the bottom screen."""
        fb.paste("black", (0, 0, FB_W, FB_H))
        
        # Center of the screen
        origin_x, origin_y = FB_W // 2, FB_H // 2
        
        random.seed(42) # Use a fixed seed for reproducible stars
        stars = [(random.uniform(-25, 25), random.uniform(-25, 25), random.uniform(1, 100)) for _ in range(200)]
        
        for i, (sx, sy, sz) in enumerate(stars):
            # Move star towards the viewer
            z = (sz - (frame*0.5)) % 100
            if z < 1: z += 99 # Reset star when it passes the camera

            # Project 3D coordinates to 2D screen space
            k = 128.0 / z
            x = int(sx * k + origin_x)
            y = int(sy * k + origin_y)

            if 0 <= x < FB_W and 0 <= y < FB_H:
                # Make stars brighter as they get closer
                brightness = int(255 * (1 - z / 100.0))
                size = int(2 * (1 - z / 100.0))
                
                # Draw the star (a small rectangle for size)
                fb.paste((brightness, brightness, brightness), (x, y, x + size, y + size))
        random.seed() # Reset seed

    def get_registers(self):
        return self.arm9, self.arm7, self.cpsr9, self.cpsr7

    def get_framebuffers(self):
        return self.fb_top, self.fb_bot
    
    def get_memory_dump(self, addr, length):
        """Gets a slice of the main RAM for the hex viewer."""
        return self.main_ram[addr:addr+length]

class NoGbaVibesApp:
    def __init__(self, root):
        self.root = root
        self.core = NdsVibesEngineCore()
        self.vibes = tk.BooleanVar(value=False)
        self.rom_name = self.core.rom_name
        self._fonts()
        self._build_gui()
        self.running = False
        self.status_blink = False
        self.frame_counter = 0
        self.last_time = time.perf_counter()
        self.fps = 0
        self.run()

    def _fonts(self):
        self.font = font.Font(family="MS Sans Serif", size=8)
        self.monofont = font.Font(family="Consolas", size=9, weight="bold")

    def _build_gui(self):
        self.root.title("NO$GBA Vibes Engine (Python, Files Off, Vibes On)")
        self.root.geometry("670x500")
        self.root.resizable(False, False)
        self.root.configure(bg="#B8B8B8")
        menubar = tk.Menu(self.root, font=self.font)
        filem = tk.Menu(menubar, tearoff=0, font=self.font)
        filem.add_command(label="Load Game... (disabled)", state=tk.DISABLED)
        filem.add_separator()
        filem.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=filem)
        emum = tk.Menu(menubar, tearoff=0, font=self.font)
        emum.add_command(label="Run", command=self.run)
        emum.add_command(label="Stop", command=self.stop)
        emum.add_command(label="Reset", command=self.reset)
        menubar.add_cascade(label="Emulation", menu=emum)
        tools = tk.Menu(menubar, tearoff=0, font=self.font)
        tools.add_checkbutton(label="Vibes++ Mode", variable=self.vibes, onvalue=True, offvalue=False)
        menubar.add_cascade(label="Tools", menu=tools)
        self.root.config(menu=menubar)

        # Main frames
        bg = "#B8B8B8"
        main = tk.Frame(self.root, bg=bg)
        main.place(x=0, y=0, width=670, height=500)
        left = tk.Frame(main, bg=bg)
        left.place(x=12, y=10, width=280, height=418)
        self.screen_top = tk.Label(left, bd=3, relief="ridge", bg="#111")
        self.screen_top.pack(pady=(2, 4))
        self.screen_bot = tk.Label(left, bd=3, relief="ridge", bg="#111")
        self.screen_bot.pack()
        right = tk.Frame(main, bg=bg)
        right.place(x=300, y=10, width=360, height=418)
        tk.Label(right, text="CPU Registers (ARM9/ARM7)", font=self.font, bg=bg).pack(anchor=tk.W, pady=(0, 2))
        self.reg_text = tk.Text(right, width=46, height=15, font=self.monofont, bg="#E7E7E7", bd=1, relief=tk.SUNKEN)
        self.reg_text.pack()
        self.reg_text.config(state=tk.DISABLED)
        tk.Label(right, text="RAM @ 0x02000000 (Main RAM)", font=self.font, bg=bg).pack(anchor=tk.W, pady=(8, 0))
        self.mem_view = tk.Text(right, width=46, height=7, font=self.monofont, bg="#FFFBE7", bd=1, relief=tk.SUNKEN)
        self.mem_view.pack()
        self.mem_view.config(state=tk.DISABLED)
        self.rom_label = tk.Label(self.root, text=f"ROM: {self.rom_name}", font=self.font, anchor=tk.W, bg="#F8F8F8", bd=1, relief=tk.SUNKEN)
        self.rom_label.place(x=0, y=446, width=500, height=24)
        self.statusbar = tk.Label(self.root, text="", font=self.font, anchor=tk.W, bg="#E0E0E0", bd=1, relief=tk.SUNKEN)
        self.statusbar.place(x=500, y=446, width=170, height=24)

    def run(self):
        if not self.running:
            self.running = True
            self._mainloop()

    def stop(self):
        self.running = False
        self.status(f"Emulation stopped. {self.fps:.1f} FPS")

    def reset(self):
        self.core.reset()
        self.rom_name = self.core.rom_name
        self.rom_label.config(text=f"ROM: {self.rom_name}")
        self.status("Vibes Engine reset.")

    def _mainloop(self):
        if not self.running:
            return
        start_time = time.perf_counter()
        
        self.core.step()
        self._draw_registers()
        self._draw_memory_dump()
        self._draw_screens()

        # Update FPS counter and status bar
        self.frame_counter += 1
        now = time.perf_counter()
        elapsed = now - self.last_time
        if elapsed >= 1.0:
            self.fps = self.frame_counter / elapsed
            self.last_time = now
            self.frame_counter = 0
            self.status(f"Running... {self.fps:.1f} FPS")

        # Keep the target framerate (ideally 60 fps)
        render_time = time.perf_counter() - start_time
        delay = max(1, int(1000/60 - render_time * 1000))
        self.root.after(delay, self._mainloop)

    def _draw_registers(self):
        arm9, arm7, cpsr9, cpsr7 = self.core.get_registers()
        text = "ARM9 (67 MHz) [PROCEDURAL]\n"
        for i in range(0, 16, 2):
            text += f"R{i:<2}={arm9[i]:08X}   R{i+1:<2}={arm9[i+1]:08X}\n"
        text += f"CPSR={cpsr9:08X} (SYS)\n\nARM7 (33 MHz) [PROCEDURAL]\n"
        for i in range(0, 16, 2):
            text += f"R{i:<2}={arm7[i]:08X}   R{i+1:<2}={arm7[i+1]:08X}\n"
        text += f"CPSR={cpsr7:08X} (SYS)\n"
        
        self.reg_text.config(state=tk.NORMAL)
        self.reg_text.delete("1.0", tk.END)
        self.reg_text.insert(tk.END, text)
        self.reg_text.config(state=tk.DISABLED)

    def _draw_memory_dump(self):
        addr = (self.core.frame * 8) % (len(self.core.main_ram) - 256)
        dump_data = self.core.get_memory_dump(addr, 128)
        
        text = ""
        for i in range(0, 128, 16):
            chunk = dump_data[i:i+16]
            hex_part = " ".join(f"{b:02X}" for b in chunk)
            ascii_part = "".join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
            text += f"{0x02000000+addr+i:08X}  {hex_part:<48} |{ascii_part}|\n"

        self.mem_view.config(state=tk.NORMAL)
        self.mem_view.delete("1.0", tk.END)
        self.mem_view.insert(tk.END, text)
        self.mem_view.config(state=tk.DISABLED)

    def _draw_screens(self):
        fb_top, fb_bot = self.core.get_framebuffers()
        
        # "Vibes++ Mode" cranks up the color saturation for an intense look
        if self.vibes.get():
            fb_top = ImageEnhance.Color(fb_top).enhance(2.5)
            fb_bot = ImageEnhance.Brightness(fb_bot).enhance(1.8)

        # PhotoImage must be stored as an attribute to prevent garbage collection
        self.img_top = ImageTk.PhotoImage(fb_top)
        self.img_bot = ImageTk.PhotoImage(fb_bot)
        
        self.screen_top.config(image=self.img_top)
        self.screen_bot.config(image=self.img_bot)

    def status(self, msg):
        self.statusbar.config(text=msg)

if __name__ == "__main__":
    root = tk.Tk()
    app = NoGbaVibesApp(root)
    root.mainloop()

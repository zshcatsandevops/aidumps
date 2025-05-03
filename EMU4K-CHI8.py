import tkinter as tk
from tkinter import filedialog
import random

SCALE = 8
WIDTH, HEIGHT = 64, 32

class CPU:
    def __init__(self):
        self.reset()
        self.sound_callback = None

    def reset(self):
        self.memory = [0] * 4096
        self.V = [0] * 16
        self.I = 0
        self.pc = 0x200
        self.stack = []
        self.delay_timer = 0
        self.sound_timer = 0
        self.gfx = [0] * (64 * 32)
        self.key = [0] * 16
        self.draw_flag = False
        self.load_fontset()

    def load_fontset(self):
        fontset = [
            0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
            0x20, 0x60, 0x20, 0x20, 0x70,  # 1
            0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
            0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
            0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
            0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
            0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
            0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
            0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
            0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
            0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
            0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
            0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
            0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
            0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
            0xF0, 0x80, 0xF0, 0x80, 0x80   # F
        ]
        for i in range(len(fontset)):
            self.memory[i] = fontset[i]

    def load_rom(self, path):
        with open(path, "rb") as f:
            rom = f.read()
            for i in range(len(rom)):
                self.memory[0x200 + i] = rom[i]

    def emulate_cycle(self):
        opcode = self.memory[self.pc] << 8 | self.memory[self.pc + 1]
        self.pc += 2

        if opcode == 0x00E0:
            self.gfx = [0] * (64 * 32)
            self.draw_flag = True
        elif opcode == 0x00EE:
            self.pc = self.stack.pop()
        elif opcode & 0xF000 == 0x1000:
            self.pc = opcode & 0x0FFF
        elif opcode & 0xF000 == 0x2000:
            self.stack.append(self.pc)
            self.pc = opcode & 0x0FFF
        elif opcode & 0xF000 == 0x3000:
            x = (opcode & 0x0F00) >> 8
            if self.V[x] == (opcode & 0x00FF):
                self.pc += 2
        elif opcode & 0xF000 == 0x4000:
            x = (opcode & 0x0F00) >> 8
            if self.V[x] != (opcode & 0x00FF):
                self.pc += 2
        elif opcode & 0xF000 == 0x5000 and (opcode & 0x000F) == 0:
            x = (opcode & 0x0F00) >> 8
            y = (opcode & 0x00F0) >> 4
            if self.V[x] == self.V[y]:
                self.pc += 2
        elif opcode & 0xF000 == 0x6000:
            x = (opcode & 0x0F00) >> 8
            self.V[x] = opcode & 0x00FF
        elif opcode & 0xF000 == 0x7000:
            x = (opcode & 0x0F00) >> 8
            self.V[x] = (self.V[x] + (opcode & 0x00FF)) & 0xFF
        elif opcode & 0xF000 == 0x8000:
            x = (opcode & 0x0F00) >> 8
            y = (opcode & 0x00F0) >> 4
            if opcode & 0x000F == 0:
                self.V[x] = self.V[y]
            elif opcode & 0x000F == 1:
                self.V[x] |= self.V[y]
            elif opcode & 0x000F == 2:
                self.V[x] &= self.V[y]
            elif opcode & 0x000F == 3:
                self.V[x] ^= self.V[y]
            elif opcode & 0x000F == 4:
                sum_val = self.V[x] + self.V[y]
                self.V[0xF] = 1 if sum_val > 255 else 0
                self.V[x] = sum_val & 0xFF
            elif opcode & 0x000F == 5:
                self.V[0xF] = 1 if self.V[x] >= self.V[y] else 0
                self.V[x] = (self.V[x] - self.V[y]) & 0xFF
            elif opcode & 0x000F == 6:
                self.V[0xF] = self.V[y] & 1
                self.V[x] = self.V[y] >> 1
            elif opcode & 0x000F == 7:
                self.V[0xF] = 1 if self.V[y] >= self.V[x] else 0
                self.V[x] = (self.V[y] - self.V[x]) & 0xFF
            elif opcode & 0x000F == 0xE:
                self.V[0xF] = (self.V[y] >> 7) & 1
                self.V[x] = (self.V[y] << 1) & 0xFF
        elif opcode & 0xF000 == 0x9000 and (opcode & 0x000F) == 0:
            x = (opcode & 0x0F00) >> 8
            y = (opcode & 0x00F0) >> 4
            if self.V[x] != self.V[y]:
                self.pc += 2
        elif opcode & 0xF000 == 0xA000:
            self.I = opcode & 0x0FFF
        elif opcode & 0xF000 == 0xB000:
            self.pc = (opcode & 0x0FFF) + self.V[0]
        elif opcode & 0xF000 == 0xC000:
            x = (opcode & 0x0F00) >> 8
            self.V[x] = random.randint(0, 255) & (opcode & 0x00FF)
        elif opcode & 0xF000 == 0xD000:
            x = self.V[(opcode & 0x0F00) >> 8]
            y = self.V[(opcode & 0x00F0) >> 4]
            h = opcode & 0x000F
            self.V[0xF] = 0
            for row in range(h):
                sprite = self.memory[self.I + row]
                for col in range(8):
                    if sprite & (0x80 >> col):
                        idx = ((x + col) % 64) + (((y + row) % 32) * 64)
                        if self.gfx[idx]:
                            self.V[0xF] = 1
                        self.gfx[idx] ^= 1
            self.draw_flag = True
        elif opcode & 0xF000 == 0xE000:
            x = (opcode & 0x0F00) >> 8
            if opcode & 0x00FF == 0x009E:
                if self.key[self.V[x]]:
                    self.pc += 2
            elif opcode & 0x00FF == 0x00A1:
                if not self.key[self.V[x]]:
                    self.pc += 2
        elif opcode & 0xF000 == 0xF000:
            x = (opcode & 0x0F00) >> 8
            if opcode & 0x00FF == 0x0007:
                self.V[x] = self.delay_timer
            elif opcode & 0x00FF == 0x000A:
                key_pressed = False
                for k in range(16):
                    if self.key[k]:
                        self.V[x] = k
                        key_pressed = True
                        break
                if not key_pressed:
                    self.pc -= 2
            elif opcode & 0x00FF == 0x0015:
                self.delay_timer = self.V[x]
            elif opcode & 0x00FF == 0x0018:
                self.sound_timer = self.V[x]
                if self.sound_callback:
                    self.sound_callback()
            elif opcode & 0x00FF == 0x001E:
                self.I = (self.I + self.V[x]) & 0xFFFF
            elif opcode & 0x00FF == 0x0029:
                self.I = self.V[x] * 5
            elif opcode & 0x00FF == 0x0033:
                self.memory[self.I] = self.V[x] // 100
                self.memory[self.I + 1] = (self.V[x] // 10) % 10
                self.memory[self.I + 2] = self.V[x] % 10
            elif opcode & 0x00FF == 0x0055:
                for i in range(x + 1):
                    self.memory[self.I + i] = self.V[i]
            elif opcode & 0x00FF == 0x0065:
                for i in range(x + 1):
                    self.V[i] = self.memory[self.I + i]
        else:
            print(f"Unknown opcode: {opcode:04X}")

class NesticleStyleChip8:
    def __init__(self):
        self.cpu = CPU()
        self.running = False

        self.root = tk.Tk()
        self.root.title("Nesticle 98 - CHIP-8 Special Edition")
        self.root.geometry("600x400")
        self.root.configure(bg="gray20")

        self.build_gui()
        self.cpu.sound_callback = self.play_sound
        self.root.mainloop()

    def build_gui(self):
        self.menu = tk.Menu(self.root)
        self.root.config(menu=self.menu)
        file_menu = tk.Menu(self.menu, tearoff=0)
        file_menu.add_command(label="Load ROM", command=self.load_rom)
        file_menu.add_command(label="Exit", command=self.root.quit)
        self.menu.add_cascade(label="File", menu=file_menu)

        self.canvas = tk.Canvas(self.root, width=WIDTH*SCALE, height=HEIGHT*SCALE, bg="black", bd=3, relief="sunken")
        self.canvas.place(x=20, y=20)

        self.btn_start = tk.Button(self.root, text="RUN", width=10, bg="green", fg="white", command=self.toggle_run)
        self.btn_start.place(x=520, y=50)

        self.led_label = tk.Label(self.root, text="🟢 IDLE", fg="lime", bg="gray20", font=("Courier", 12))
        self.led_label.place(x=500, y=100)

        self.key_map = {
            '1': 0x1, '2': 0x2, '3': 0x3, '4': 0xC,
            'q': 0x4, 'w': 0x5, 'e': 0x6, 'r': 0xD,
            'a': 0x7, 's': 0x8, 'd': 0x9, 'f': 0xE,
            'z': 0xA, 'x': 0x0, 'c': 0xB, 'v': 0xF
        }
        self.root.bind("<KeyPress>", self.key_press)
        self.root.bind("<KeyRelease>", self.key_release)

    def key_press(self, event):
        if event.keysym.lower() in self.key_map:
            self.cpu.key[self.key_map[event.keysym.lower()]] = 1

    def key_release(self, event):
        if event.keysym.lower() in self.key_map:
            self.cpu.key[self.key_map[event.keysym.lower()]] = 0

    def play_sound(self):
        self.root.bell()

    def load_rom(self):
        file_path = filedialog.askopenfilename(filetypes=[("CHIP-8 ROMs", "*.ch8")])
        if file_path:
            self.cpu.reset()
            self.cpu.load_rom(file_path)
            self.running = True
            self.update()

    def toggle_run(self):
        self.running = not self.running
        self.led_label.config(text="🔴 RUNNING" if self.running else "🟢 IDLE")
        if self.running:
            self.update()

    def update(self):
        if not self.running:
            return
        draw_needed = False
        for _ in range(10):  # Run 10 cycles per frame
            self.cpu.emulate_cycle()
            if self.cpu.draw_flag:
                draw_needed = True
                self.cpu.draw_flag = False
        if self.cpu.delay_timer > 0:
            self.cpu.delay_timer -= 1
        if self.cpu.sound_timer > 0:
            self.cpu.sound_timer -= 1
        if draw_needed:
            self.draw_screen()
        self.root.after(16, self.update)

    def draw_screen(self):
        self.canvas.delete("all")
        for y in range(HEIGHT):
            for x in range(WIDTH):
                if self.cpu.gfx[y * WIDTH + x]:
                    self.canvas.create_rectangle(
                        x * SCALE, y * SCALE,
                        (x + 1) * SCALE, (y + 1) * SCALE,
                        fill="white", outline=""
                    )

if __name__ == "__main__":
    NesticleStyleChip8()

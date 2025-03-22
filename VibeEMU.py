import random
import time

class N64Emulator:
    def __init__(self, rom_file):  # FIXED: __init__ method
        self.rom_file = rom_file
        self.memory = [0] * (64 * 1024)  # 64KB simulated memory
        self.cpu_registers = {"R1": 0, "R2": 0, "R3": 0}  # MIPS-style registers
        self.graphics_buffer = []
        self.sound_events = []
        self.input_buffer = []
        self.is_running = False
        self.frame_count = 0

    def load_rom(self):
        print(f"🎮 Loading ROM: {self.rom_file}")
        for i in range(min(len(self.memory), 1024)):
            self.memory[i] = random.randint(0, 255)
        print("🧠 Parsing ROM data... Extracting important segments.")
        self.rom_data = random.sample(self.memory, 10)
        print(f"✅ Parsed ROM segments: {self.rom_data}")

    def run(self):
        self.is_running = True
        print("\n🟢 Emulator running... PJ64 vibes engaged!\n")
        while self.is_running and self.frame_count < 100:
            self.frame_count += 1
            self.execute_cpu_cycle()
            self.render_graphics()
            self.play_sound()
            self.check_for_input()

            time.sleep(0.1)  # Simulate frame timing

        print(f"\n🛑 Emulator stopped after {self.frame_count} frames. Vibe session complete!\n")

    def execute_cpu_cycle(self):
        operation = random.choice(["ADD", "SUB", "MUL", "DIV"])
        reg1 = random.choice(list(self.cpu_registers.keys()))
        reg2 = random.choice(list(self.cpu_registers.keys()))

        if operation == "ADD":
            self.cpu_registers[reg1] += self.cpu_registers[reg2]
        elif operation == "SUB":
            self.cpu_registers[reg1] -= self.cpu_registers[reg2]
        elif operation == "MUL":
            self.cpu_registers[reg1] *= self.cpu_registers[reg2]
        elif operation == "DIV" and self.cpu_registers[reg2] != 0:
            self.cpu_registers[reg1] //= self.cpu_registers[reg2]

        print(f"🧮 CPU Cycle ({operation}): {reg1} now {self.cpu_registers[reg1]} | Registers: {self.cpu_registers}")

    def render_graphics(self):
        if self.frame_count % 10 == 0:
            frame_data = f"Rendering frame {self.frame_count}... N64 vibes!"
            self.graphics_buffer.append(frame_data)
            print(f"🖼️ {frame_data}")

    def play_sound(self):
        if self.frame_count % 15 == 0:
            sound_event = f"🔊 Sound Event {random.randint(1, 10)}: Vibe sound playing!"
            self.sound_events.append(sound_event)
            print(sound_event)

    def check_for_input(self):
        # Simulate random keypress with 5% chance
        if random.random() < 0.05:
            input_event = f"🎮 Input detected on frame {self.frame_count}! Vibe controls activated."
            self.input_buffer.append(input_event)
            print(input_event)
            print("💤 Shutting down emulator after epic input vibe.\n")
            self.is_running = False  # Stop emulator gently

# 🔥 Test the emulator
if __name__ == '__main__':
    emu = N64Emulator("super_vibe_64.z64")
    emu.load_rom()
    emu.run()

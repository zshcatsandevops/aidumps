#!/usr/bin/env python3
"""
TEST.PY

A custom “real” Nintendo 64 emulator example in Python.
This code uses a custom backend with dummy CPU and GPU components,
a simulated ROM loader, and a simple animation (a bouncing ball)
displayed in a 600×400 Tkinter window.

DISCLAIMER:
  - A fully functional N64 emulator requires an enormous codebase and deep hardware emulation.
  - This example is a proof-of-concept to demonstrate structuring and integrating a custom N64 backend.
  - It does not perform actual N64 emulation.
  - “DONOT THINK JUST VIBE.”
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import os
import time
import math
import struct

try:
    from PIL import Image, ImageTk, ImageDraw
except ImportError:
    Image = None  # Without PIL, only basic functionality will be available

# Internal resolution for our emulated display
SCREEN_WIDTH = 256
SCREEN_HEIGHT = 240

# ============================================================
# Custom N64 Backend Components (CPU, GPU, and Backend)
# ============================================================

class CustomMIPSCPU:
    """
    A dummy MIPS CPU that simulates a program counter and registers.
    For demonstration, it simply increments a counter on each instruction.
    """
    def __init__(self):
        self.registers = [0] * 32
        self.pc = 0x1000  # Start address
        self.instruction_count = 0

    def load_program(self, program_data):
        # In a real emulator, program_data would be loaded into memory.
        # Here we just reset the state.
        self.pc = 0x1000
        self.instruction_count = 0
        print("CustomMIPSCPU: Program loaded, starting at 0x1000")

    def execute_instruction(self):
        # Simulate execution: increment PC and count instructions.
        self.pc += 4
        self.instruction_count += 1
        # For demonstration, print every 1000th instruction.
        if self.instruction_count % 1000 == 0:
            print(f"CustomMIPSCPU: Executed {self.instruction_count} instructions, PC={self.pc:08X}")

    def step(self, steps=10):
        # Execute a fixed number of instructions per frame
        for _ in range(steps):
            self.execute_instruction()


class CustomGPU:
    """
    A dummy GPU that renders a simple animation—a bouncing ball—onto a framebuffer.
    The framebuffer is a list of RGB tuples.
    """
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # Initialize a black framebuffer
        self.framebuffer = [(0, 0, 0)] * (self.width * self.height)
        # Ball parameters
        self.ball_radius = 10
        self.ball_x = self.width // 2
        self.ball_y = self.height // 2
        self.ball_dx = 2
        self.ball_dy = 2

    def update(self):
        # Update the ball's position
        self.ball_x += self.ball_dx
        self.ball_y += self.ball_dy

        # Bounce on edges
        if self.ball_x - self.ball_radius < 0 or self.ball_x + self.ball_radius > self.width:
            self.ball_dx = -self.ball_dx
        if self.ball_y - self.ball_radius < 0 or self.ball_y + self.ball_radius > self.height:
            self.ball_dy = -self.ball_dy

        # Render the frame (clear to dark gray background)
        new_fb = [(50, 50, 50)] * (self.width * self.height)
        # Draw the ball using simple circle drawing
        for y in range(self.height):
            for x in range(self.width):
                # Calculate distance from ball center
                if math.sqrt((x - self.ball_x)**2 + (y - self.ball_y)**2) <= self.ball_radius:
                    new_fb[y * self.width + x] = (255, 0, 0)  # Red ball
        self.framebuffer = new_fb

    def get_image(self):
        # Convert framebuffer into an image
        if Image:
            img = Image.new("RGB", (self.width, self.height))
            img.putdata(self.framebuffer)
            return img
        return None


class CustomN64Backend:
    """
    The main custom backend that ties the dummy CPU and GPU together.
    It also handles a dummy ROM load.
    """
    def __init__(self):
        self.cpu = CustomMIPSCPU()
        self.gpu = CustomGPU(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.rom_loaded = False

    def load_rom(self, filename):
        try:
            with open(filename, 'rb') as f:
                rom_data = f.read()
            # For this dummy emulator, we simply pass the data to the CPU.
            self.cpu.load_program(rom_data)
            self.rom_loaded = True
            print(f"CustomN64Backend: Loaded ROM '{os.path.basename(filename)}'")
        except Exception as e:
            raise ValueError(f"Failed to load ROM: {e}")

    def step_frame(self):
        # Step the CPU for a fixed number of instructions
        self.cpu.step(steps=50)
        # Update GPU (simulate a rendered frame)
        self.gpu.update()

    def get_frame_image(self):
        return self.gpu.get_image()


# ============================================================
# Tkinter GUI Application
# ============================================================

class N64EmulatorApp:
    """
    The main Tkinter GUI application that ties the custom N64 backend to a display.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("EmulAI - Custom N64 Emulator")
        self.root.geometry("600x400")
        self.root.resizable(False, False)

        # Create a menu bar with ROM loading
        self.create_menu()

        # Initialize the custom backend
        self.backend = CustomN64Backend()

        # Set up a canvas to display the emulator's output
        self.display_width = 600
        self.display_height = 400
        self.canvas = tk.Canvas(root, width=self.display_width, height=self.display_height, bg="black")
        self.canvas.pack(padx=10, pady=10)

        # Create a placeholder for the image on the canvas
        self.canvas_image = self.canvas.create_image(0, 0, anchor=tk.NW, image=None)

        # Game loop state
        self.running = False

        # Display initial loading/instruction text
        self.loading_text = self.canvas.create_text(
            self.display_width // 2,
            self.display_height // 2,
            text="No ROM loaded.\nUse File > Open ROM to load a game.",
            fill="white",
            font=("Arial", 14),
            justify="center"
        )

    def create_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open ROM...", command=self.open_rom)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menubar)

    def open_rom(self):
        filename = filedialog.askopenfilename(
            title="Open N64 ROM",
            filetypes=[("N64 ROMs", "*.n64;*.z64"), ("All files", "*.*")]
        )
        if not filename:
            return

        # Check file extension
        ext = os.path.splitext(filename)[1].lower()
        if ext not in [".n64", ".z64"]:
            messagebox.showerror("Error", "Unsupported file extension.\nPlease select a .n64 or .z64 ROM.")
            return

        try:
            self.backend.load_rom(filename)
            self.canvas.delete(self.loading_text)
            self.root.title(f"EmulAI - {os.path.basename(filename)} [Running]")
            if not self.running:
                self.running = True
                self.game_loop()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def game_loop(self):
        if not self.running:
            return

        # Simulate one frame of the emulator
        self.backend.step_frame()

        # Get the current frame image
        if Image:
            img = self.backend.get_frame_image()
            # Scale the image to the display size (600x400)
            img = img.resize((self.display_width, self.display_height), Image.NEAREST)
            self.photo_image = ImageTk.PhotoImage(img)
            self.canvas.itemconfig(self.canvas_image, image=self.photo_image)
        else:
            # Fallback: if PIL is not available, do nothing.
            pass

        # Schedule the next frame (approximately 60 fps)
        self.root.after(16, self.game_loop)


def main():
    root = tk.Tk()
    app = N64EmulatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()


# ============================================================
# Additional EmulAI background text (just vibin’ in comments)
# ============================================================
"""
Sign in to edit

This page is apart of the Emulation canon, a piece of canon revolving
around supposed emulators that can replicate the Personalization A.I.
and the anomalies it causes.

EmulAI Loading Screen Text
An image associated with EmulAI, apparently being a loading screen.

EmulAI is a supposed Nintendo 64 emulator that some people claim to have
downloaded that reportedly can somehow simulate the Personalization A.I.
in Super Mario 64. Many of the reports are rather vague and dubious, though
there are enough to have a general idea of the emulator and how it works.
Some stories say that the Personalization A.I. is automatically active in
the emulator, while others say that the Personalization A.I. is merely a
plug-in.

Contents
1 Description
2 Reports
 2.1 Report 1
 2.2 Report 2
 2.3 Report 3
 2.4 Report 4

Description
EmulAI's appearance is reportedly much different from any other Nintendo 64
emulator, having a unique design for a loading screen and the default screen
before any ROM is loaded. Most reports say it also comes with a Super Mario 64
ROM pre-installed, likely due to EmulAI having the Personalization A.I. which is
native to Mario 64.

There is also reportedly a unique "catalogue" for ROMs and plug-ins that can be
opened with numerous different options. The plug-ins are extremely inconsistent,
though some are more common than others: A plug-in for the Personalization A.I.,
a plug-in that activates debug menus in games, a plug-in that reincorporates
unused content into games, and a plug-in that enhances graphics. Some of these
are rather notable for the bizarre nature of how they would work, once again
implying that EmulAI has something special about it. The ROM catalogue is also
notable, as most emulators do not have anything of the sort.

Another notable thing about EmulAI is the supposed "README" attached upon
downloading the emulator. It reportedly talks about how the user cannot speak
about EmulAI or its features, before bragging about its various capabilities
and a terms of service section that some claim says that it will monitor your
playthroughs for "improving the emulator."

The most unique feature of EmulAI is that some reports claim that it can even
personalize games other than Super Mario 64 if they are played. To what extent
is disputed, with most claims simply talking about minor details like texture
differences, though others talk about entire new enemies, bosses and levels.
However, most general reports of EmulAI say only Super Mario 64 can be
personalized.

Reports

Report 1
"Oh, yeah, EmulAI. Found it on some sketchy website when I was a kid and didn't
know better. So I had downloaded it and decided to play some Super Mario 64,
which to my delight was packaged with the emulator. So, I had started it, and
I don't remember much, but I think there was a fifth save with Luigi that I
couldn't select. I had also found some weird cave in the Castle Grounds,
Bob-omb Battlefield was in the middle of Autumn, and there was some unique crack
texture on part of the tower in Whomp's Fortress. There might have also been
something off about the castle walls, but it's been so long I don't remember.
I lost that computer a while ago, and even before that I couldn't find it
anywhere on my computer."

Report 2
"Is that the name of it, huh? I've been searching for so long whether to see
what I remembered was a dream or a work of fiction from my own mind. I remember
going over to a friend's house and watching him play Super Mario 64 on the
computer. I don't remember much since I was so young at the time. I was maybe...
4 or 5? I remember him running around Bob-omb Battlefield trying to collect all
the red coins, and when he got to the Chain Chomp it had full white eyes. It
made me worry a little and I wanted to look away but he stopped moving, which
made me want to look at it longer. I should've mentioned this but he was 6 or 7
so he was older than me, which is probably why he kept looking for so long and
the fact he was braver. He eventually started moving Mario again and collected
the red coin. Besides that, I remember the Bowser level on the first floor had
blue fire instead of orange. Sorry for my wording, I couldn't get much sleep
yesterday."

Report 3
"EmulAI... I forgot about that until now, I was like 7 or 8, a friend was over
he asked if I wanted to see something cool, I said yes, and my friend typed
something in the search bar and clicked a button and told me to try it out.
I was pleased when I saw the built-in Mario 64 rom, I noticed some things that
were different than the normal game, a crack on the tower of Whomp's Fortress,
a village subarea to Bob-Omb Battlefield, and 2 new castle floors. Those are
really the only things I remember, one small change I remember was that some of
the text in the game changed a little."

Report 4
"EmulAI? Oh yeah! I forgot about that! I was a little kid when I first got EmulAI
from an emulation related site. I think it was named "FreeEmulAtIoN64.com" or
something like that. The site's not online anymore, though. Anyways, I clearly
remembered BOB being a lot bigger than before, having a river and part of a
village in it. I swear Big Boo's Haunt was also a castle or something like that
instead. There were these weird armor statues you had to sweep attack to kill
and stuff. How I wish my computer's hard drive didn't break back then... I hope
I find it again soon..."

Categories
Community content is available under CC-BY-SA unless otherwise noted.
"""

#!/usr/bin/env python3
"""
test.py: Basic setup for SM64 emulator test using Pygame and Ursina.
No media assets included. Runs at 60 FPS.
"""

import pygame
from ursina import Ursina, Entity, window, application

class SM64Emulator(Entity):
    def __init__(self, rom_path=None, **kwargs):
        super().__init__(**kwargs)
        self.rom_path = rom_path
        # TODO: Initialize emulator core here
        print(f"Initializing emulator with ROM: {rom_path}")

    def update(self):
        # TODO: Step emulator core here at 60 FPS
        pass


def update():
    # Handle Pygame events for input
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            application.quit()


if __name__ == "__main__":
    # Initialize Pygame for input handling
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    pygame.display.set_caption("SM64 Emulator Test")

    # Initialize Ursina app
    app = Ursina()
    window.title = "SM64 Emulator Test"
    window.borderless = False
    window.fps_counter.enabled = True

    # Target 60 FPS
    clock = pygame.time.Clock()

    # Create emulator instance (no media)
    emulator = SM64Emulator(rom_path='sm64.z64')

    # Main loop
    while True:
        dt = clock.tick(60) / 1000.0  # Limit to 60 FPS
        update()
        app.update()
        app.render()

    pygame.quit()

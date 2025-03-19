import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import threading
import time
import os
import ctypes
from PIL import Image, ImageTk
import json
import random

# Attempt to import optional dependencies
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

try:
    from OpenGL import GL, GLU
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False

class EmulAI:
    def __init__(self, root):
        self.root = root
        self.root.title("EmulAI - N64 Emulator")
        self.root.geometry("800x600")
        self.root.minsize(640, 480)
        
        # Set up the main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Emulator state
        self.emulation_running = False
        self.current_rom = None
        self.built_in_mario64 = True  # Flag for built-in Mario 64
        self.active_plugins = {"Personalizer": True}  # Default plugins
        self.rom_catalogue = self.load_rom_catalogue()
        
        # Memory and register arrays (simplified for demo)
        self.rdram = np.zeros(8 * 1024 * 1024, dtype=np.uint8)  # 8MB RDRAM
        self.registers = np.zeros(32, dtype=np.uint32)  # CPU registers
        
        # Create the menu bar
        self.create_menu_bar()
        
        # Create the emulation screen
        self.create_emulation_screen()
        
        # Create status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready. Built-in Super Mario 64 ROM loaded.")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Set up emulation thread (not started yet)
        self.emulation_thread = None
        
        # Initialize audio if pygame is available
        if PYGAME_AVAILABLE:
            pygame.mixer.init(44100, -16, 2, 1024)
        
        # Savestate management
        self.savestates = {}
        
        # Keyboard mapping for controller
        self.setup_input_mapping()
        
        # Show the loading screen and start with Mario 64
        self.show_loading_screen()

    def create_menu_bar(self):
        """Create the menu bar with all options"""
        self.menu_bar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Open ROM...", command=self.open_rom)
        file_menu.add_command(label="Reset", command=self.reset_emulation)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        
        # ROM Menu
        rom_menu = tk.Menu(self.menu_bar, tearoff=0)
        rom_menu.add_command(label="ROM Catalogue", command=self.show_rom_catalogue)
        rom_menu.add_command(label="Save State", command=self.save_state)
        rom_menu.add_command(label="Load State", command=self.load_state)
        rom_menu.add_command(label="Reset ROM", command=self.reset_emulation)
        self.menu_bar.add_cascade(label="ROM", menu=rom_menu)
        
        # Settings menu
        settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        settings_menu.add_command(label="Controller Setup", command=self.show_controller_setup)
        settings_menu.add_command(label="Audio Settings", command=self.show_audio_settings)
        settings_menu.add_command(label="Video Settings", command=self.show_video_settings)
        self.menu_bar.add_cascade(label="Settings", menu=settings_menu)
        
        # Plugins menu
        plugins_menu = tk.Menu(self.menu_bar, tearoff=0)
        
        # Create variables for plugin checkboxes
        self.plugin_vars = {
            "Rediscovered": tk.BooleanVar(value=False),
            "Personalizer": tk.BooleanVar(value=True),
            "Other Games": tk.BooleanVar(value=False),
            "Wonder Graphics": tk.BooleanVar(value=False),
            "Debugger": tk.BooleanVar(value=False)
        }
        
        # Add checkbox for each plugin
        for plugin, var in self.plugin_vars.items():
            plugins_menu.add_checkbutton(label=plugin, variable=var, 
                                        command=lambda p=plugin, v=var: self.toggle_plugin(p, v.get()))
        
        self.menu_bar.add_cascade(label="Plugins", menu=plugins_menu)
        
        # Cheats menu
        cheats_menu = tk.Menu(self.menu_bar, tearoff=0)
        cheats_menu.add_command(label="Cheat Browser", command=self.show_cheat_browser)
        cheats_menu.add_separator()
        cheats_menu.add_command(label="Import Cheat Codes", command=self.import_cheats)
        self.menu_bar.add_cascade(label="Cheats", menu=cheats_menu)
        
        # Help menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="About EmulAI", command=self.show_about)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=self.menu_bar)

    def create_emulation_screen(self):
        """Create the main emulation display area"""
        self.screen_frame = ttk.Frame(self.main_frame, borderwidth=2, relief=tk.SUNKEN)
        self.screen_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Canvas for the emulation display (will be replaced with OpenGL if available)
        self.canvas = tk.Canvas(self.screen_frame, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Create a placeholder image for the emulator screen
        placeholder = np.zeros((240, 320, 3), dtype=np.uint8)
        self.update_display(placeholder)
        
        # Capture keyboard events for controller input
        self.canvas.bind("<KeyPress>", self.handle_key_press)
        self.canvas.bind("<KeyRelease>", self.handle_key_release)
        self.canvas.focus_set()

    def update_display(self, frame_buffer):
        """Update the display with a new frame buffer"""
        # Convert numpy array to PIL Image and then to PhotoImage
        if isinstance(frame_buffer, np.ndarray):
            img = Image.fromarray(frame_buffer.astype('uint8'))
            
            # Resize to fit the canvas while maintaining aspect ratio
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:  # Ensure canvas has size
                img = img.resize((canvas_width, canvas_height), Image.LANCZOS)
            
            self.photo_image = ImageTk.PhotoImage(image=img)
            self.canvas.create_image(0, 0, image=self.photo_image, anchor=tk.NW)

    def setup_input_mapping(self):
        """Set up keyboard mapping to N64 controller"""
        self.key_mapping = {
            'w': 'dpad_up',
            'a': 'dpad_left',
            's': 'dpad_down',
            'd': 'dpad_right',
            'i': 'c_up',
            'j': 'c_left',
            'k': 'c_down',
            'l': 'c_right',
            'Up': 'analog_up',
            'Left': 'analog_left',
            'Down': 'analog_down',
            'Right': 'analog_right',
            'z': 'z_button',
            'x': 'a_button',
            'c': 'b_button',
            'Return': 'start_button',
            'q': 'l_button',
            'e': 'r_button'
        }
        
        # Controller state dictionary
        self.controller_state = {button: False for button in self.key_mapping.values()}

    def handle_key_press(self, event):
        """Handle key press events for controller input"""
        key = event.keysym
        if key in self.key_mapping:
            button = self.key_mapping[key]
            self.controller_state[button] = True
            
            # Debug controller input
            print(f"Button pressed: {button}")

    def handle_key_release(self, event):
        """Handle key release events for controller input"""
        key = event.keysym
        if key in self.key_mapping:
            button = self.key_mapping[key]
            self.controller_state[button] = False

    def open_rom(self):
        """Open a ROM file dialog"""
        filepath = filedialog.askopenfilename(
            title="Select N64 ROM",
            filetypes=[("N64 ROMs", "*.n64 *.v64 *.z64"), ("All files", "*.*")]
        )
        
        if filepath:
            self.load_rom(filepath)

    def load_rom(self, filepath):
        """Load a ROM file into the emulator"""
        try:
            # Stop current emulation if running
            if self.emulation_running:
                self.stop_emulation()
            
            self.status_var.set(f"Loading ROM: {os.path.basename(filepath)}...")
            self.root.update()
            
            # Show loading screen
            self.show_loading_screen()
            
            # Read the ROM file
            with open(filepath, "rb") as f:
                rom_data = f.read()
            
            # Determine endianness and convert if needed
            if len(rom_data) > 4:
                # Check first 4 bytes for endianness magic
                if rom_data[0] == 0x80:  # Big endian (Z64)
                    pass  # Already in the right format
                elif rom_data[0] == 0x37:  # Little endian (V64)
                    # Byte-swap 16-bit values
                    rom_data = self.byte_swap_16bit(rom_data)
                elif rom_data[0] == 0x40:  # Little endian word-swapped (N64)
                    # Byte-swap 32-bit values
                    rom_data = self.byte_swap_32bit(rom_data)
            
            # Store the current ROM info
            self.current_rom = {
                "path": filepath,
                "name": os.path.basename(filepath),
                "size": len(rom_data),
                "built_in": False
            }
            
            # For demo purposes, just copy the first part of ROM to RDRAM
            # In a real emulator, this would be handled by the PIF boot process
            rom_array = np.frombuffer(rom_data, dtype=np.uint8)
            copy_size = min(len(rom_array), len(self.rdram))
            self.rdram[:copy_size] = rom_array[:copy_size]
            
            # Initialize CPU registers
            self.registers.fill(0)
            self.registers[29] = 0xA4001FF0  # Initial stack pointer
            
            # Set PC to the game's entry point (usually 0x80000400)
            # For simplicity in this demo, we're directly jumping to this common entry point
            self.pc = 0x80000400
            
            # Update status
            self.built_in_mario64 = False
            self.status_var.set(f"ROM loaded: {os.path.basename(filepath)}")
            
            # Start emulation
            self.start_emulation()
            
        except Exception as e:
            messagebox.showerror("Error Loading ROM", f"Failed to load ROM: {str(e)}")
            self.status_var.set("Error loading ROM")

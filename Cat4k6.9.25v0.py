#!/usr/bin/env python3
"""
Cat Client 2.0 - Premium Minecraft Launcher with Lunar Client Features
© Team Flames 2025
Enhanced with mod management, cosmetics, and performance features
"""

import tkinter as tk
from tkinter import ttk, messagebox, font, filedialog
import threading
import queue
import json
import os
import re
import uuid
import subprocess
import requests
import minecraft_launcher_lib
import webbrowser
import time
from datetime import datetime
import psutil
import platform

# --- Constants ---
LAUNCHER_NAME = "Cat Client"
LAUNCHER_VERSION = "2.0"
CONFIG_FILE = "catclient_config.json"
MODS_CONFIG_FILE = "catclient_mods.json"
COSMETICS_CONFIG_FILE = "catclient_cosmetics.json"
AUTHLIB_URL = "https://authlib-injector.yushi.moe/artifact/latest/authlib-injector.jar"

# Lunar Client inspired color scheme
COLORS = {
    'bg_dark': '#0e0e10',
    'bg_medium': '#18181b',
    'bg_light': '#1f1f23',
    'accent': '#6441a5',  # Purple accent
    'accent_hover': '#7c5daf',
    'accent_light': '#8b7cc0',
    'text_primary': '#efeff1',
    'text_secondary': '#adadb8',
    'text_dim': '#848494',
    'success': '#00ff88',
    'warning': '#ffaa00',
    'error': '#ff4545',
    'border': '#2a2a2d',
    'lunar_blue': '#1e90ff',
    'lunar_green': '#00ff7f'
}

# Default mod configurations
DEFAULT_MODS = {
    "fps_boost": {"enabled": True, "name": "FPS Boost", "description": "Optimizes game performance"},
    "keystrokes": {"enabled": True, "name": "Keystrokes", "description": "Shows WASD + mouse keys"},
    "cps_counter": {"enabled": True, "name": "CPS Counter", "description": "Clicks per second display"},
    "fps_display": {"enabled": True, "name": "FPS Display", "description": "Shows current FPS"},
    "coordinates": {"enabled": False, "name": "Coordinates", "description": "Shows XYZ position"},
    "direction_hud": {"enabled": False, "name": "Direction HUD", "description": "Compass direction"},
    "armor_status": {"enabled": True, "name": "Armor Status", "description": "Armor durability HUD"},
    "potion_effects": {"enabled": True, "name": "Potion Effects", "description": "Active effects display"},
    "toggle_sprint": {"enabled": True, "name": "Toggle Sprint", "description": "Hold to toggle sprint"},
    "fullbright": {"enabled": False, "name": "Fullbright", "description": "Maximum brightness"},
    "zoom": {"enabled": True, "name": "Zoom", "description": "C key to zoom"},
    "chat_mods": {"enabled": True, "name": "Chat Mods", "description": "Chat improvements"},
    "crosshair": {"enabled": False, "name": "Custom Crosshair", "description": "Customizable crosshair"},
    "hitboxes": {"enabled": False, "name": "Hitboxes", "description": "F3+B hitbox display"},
    "waypoints": {"enabled": True, "name": "Waypoints", "description": "Custom location markers"},
    "memory_display": {"enabled": True, "name": "Memory Usage", "description": "RAM usage display"},
    "ping_display": {"enabled": True, "name": "Ping Display", "description": "Server latency"},
    "time_changer": {"enabled": False, "name": "Time Changer", "description": "Client-side time"},
    "particles": {"enabled": True, "name": "Particle Mod", "description": "Particle multiplier"},
    "item_physics": {"enabled": False, "name": "Item Physics", "description": "Realistic item drops"}
}

class ModernButton(tk.Canvas):
    def __init__(self, parent, text, command, width=200, height=45, primary=True, icon=None):
        super().__init__(parent, width=width, height=height, highlightthickness=0,
                         bg=COLORS['bg_dark'], bd=0)
        self.command = command
        self.text = text
        self.width = width
        self.height = height
        self.primary = primary
        self.icon = icon
        
        # Colors based on button type
        self.normal_color = COLORS['accent'] if primary else COLORS['bg_light']
        self.hover_color = COLORS['accent_hover'] if primary else COLORS['bg_medium']
        self.text_color = COLORS['text_primary']
        
        self.rect = None
        self.text_id = None
        self.draw_button()
        
        # Bind events
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.bind("<ButtonRelease-1>", self.on_release)
        
    def draw_button(self, hover=False, pressed=False):
        self.delete("all")
        color = self.hover_color if hover else self.normal_color
        if pressed:
            color = COLORS['accent_light']
        
        # Draw rounded rectangle with gradient effect
        radius = 8
        self.rect = self.create_rounded_rect(2, 2, self.width-2, self.height-2, radius, 
                                            fill=color, outline=color)
        
        # Add subtle gradient
        if self.primary and not pressed:
            for i in range(5):
                alpha = 0.1 - (i * 0.02)
                y_offset = i * 2
                self.create_rounded_rect(2, 2+y_offset, self.width-2, 20+y_offset, radius,
                                       fill="", outline=COLORS['text_primary'], width=1,
                                       stipple='gray12')
        
        # Draw icon if provided
        text_x = self.width//2
        if self.icon:
            icon_x = 30
            self.create_text(icon_x, self.height//2, text=self.icon,
                           fill=self.text_color, font=("Segoe UI", 14))
            text_x += 15
        
        # Draw text
        self.text_id = self.create_text(text_x, self.height//2, text=self.text,
                                       fill=self.text_color, font=("Segoe UI", 11, "bold"))
        
    def create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = []
        for x, y in [(x1, y1 + radius), (x1, y2 - radius), 
                     (x1 + radius, y2), (x2 - radius, y2),
                     (x2, y2 - radius), (x2, y1 + radius),
                     (x2 - radius, y1), (x1 + radius, y1)]:
            points.extend([x, y])
        return self.create_polygon(points, smooth=True, **kwargs)
        
    def on_enter(self, event):
        self.draw_button(hover=True)
        self.config(cursor="hand2")
        
    def on_leave(self, event):
        self.draw_button(hover=False)
        
    def on_click(self, event):
        self.draw_button(pressed=True)
        
    def on_release(self, event):
        self.draw_button(hover=True)
        if self.command:
            self.command()

class TabButton(tk.Label):
    def __init__(self, parent, text, command):
        super().__init__(parent, text=text, bg=COLORS['bg_dark'], 
                        fg=COLORS['text_secondary'], font=("Segoe UI", 11),
                        padx=20, pady=10, cursor="hand2")
        self.command = command
        self.active = False
        
        self.bind("<Button-1>", lambda e: command())
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        
    def on_enter(self, event):
        if not self.active:
            self.config(fg=COLORS['text_primary'])
            
    def on_leave(self, event):
        if not self.active:
            self.config(fg=COLORS['text_secondary'])
            
    def set_active(self, active):
        self.active = active
        if active:
            self.config(fg=COLORS['accent'], font=("Segoe UI", 11, "bold"))
        else:
            self.config(fg=COLORS['text_secondary'], font=("Segoe UI", 11))

class CatClientLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
        self.authlib_path = os.path.join(self.minecraft_directory, "libraries", "authlib", "authlib-injector.jar")
        
        # --- UI Variables ---
        self.status_queue = queue.Queue()
        self.auth_mode = tk.StringVar(value="Offline")
        self.mod_choice = tk.StringVar(value="Vanilla")
        self.keep_open = tk.BooleanVar(value=False)
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.logged_in = False
        self.current_user_data = None
        
        # Load configurations
        self.mods_config = self._load_mods_config()
        self.cosmetics_config = self._load_cosmetics_config()
        
        # Animation variables
        self.animation_angle = 0
        self.is_loading = False
        self.fps_counter = 0
        self.last_fps_time = time.time()
        
        # Current tab
        self.current_tab = "home"

        self._setup_ui()
        self._populate_versions()
        self.root.after(100, self._process_queue)
        self._load_config()
        self._toggle_auth_mode()
        
        # Start animations
        self.animate_logo()
        self.update_system_stats()

    def _setup_ui(self):
        self.root.title(f"{LAUNCHER_NAME} {LAUNCHER_VERSION}")
        self.root.geometry("1100x700")
        self.root.resizable(False, False)
        self.root.configure(bg=COLORS['bg_dark'])
        
        # Make window draggable
        self.root.overrideredirect(True)
        self._drag_data = {"x": 0, "y": 0}
        
        # Create main container with border
        main_frame = tk.Frame(self.root, bg=COLORS['border'])
        main_frame.pack(fill='both', expand=True, padx=1, pady=1)
        
        # Inner container
        inner_frame = tk.Frame(main_frame, bg=COLORS['bg_dark'])
        inner_frame.pack(fill='both', expand=True)
        
        # Title bar
        title_bar = tk.Frame(inner_frame, bg=COLORS['bg_dark'], height=35)
        title_bar.pack(fill='x')
        title_bar.pack_propagate(False)
        
        # Make title bar draggable
        title_bar.bind("<Button-1>", self._start_drag)
        title_bar.bind("<B1-Motion>", self._drag_window)
        
        # Title with Lunar-style branding
        title_frame = tk.Frame(title_bar, bg=COLORS['bg_dark'])
        title_frame.pack(side='left', padx=15, pady=5)
        
        tk.Label(title_frame, text="🐱", bg=COLORS['bg_dark'], 
                fg=COLORS['accent'], font=("Segoe UI", 16)).pack(side='left', padx=(0, 5))
        
        title_text = tk.Label(title_frame, text=f"{LAUNCHER_NAME}", 
                             bg=COLORS['bg_dark'], fg=COLORS['text_primary'],
                             font=("Segoe UI", 12, "bold"))
        title_text.pack(side='left')
        
        version_text = tk.Label(title_frame, text=f"v{LAUNCHER_VERSION}", 
                               bg=COLORS['bg_dark'], fg=COLORS['text_dim'],
                               font=("Segoe UI", 9))
        version_text.pack(side='left', padx=(5, 0))
        
        # System stats in title bar
        self.stats_label = tk.Label(title_bar, text="", bg=COLORS['bg_dark'],
                                   fg=COLORS['text_dim'], font=("Segoe UI", 9))
        self.stats_label.pack(side='left', padx=20)
        
        # Window controls
        controls_frame = tk.Frame(title_bar, bg=COLORS['bg_dark'])
        controls_frame.pack(side='right', padx=10)
        
        # Settings button
        settings_btn = tk.Label(controls_frame, text="⚙", bg=COLORS['bg_dark'], 
                               fg=COLORS['text_secondary'], font=("Segoe UI", 14),
                               cursor="hand2")
        settings_btn.pack(side='left', padx=5)
        settings_btn.bind("<Button-1>", lambda e: self.show_settings())
        
        # Minimize button
        min_btn = tk.Label(controls_frame, text="—", bg=COLORS['bg_dark'], 
                          fg=COLORS['text_secondary'], font=("Segoe UI", 12),
                          cursor="hand2")
        min_btn.pack(side='left', padx=5)
        min_btn.bind("<Button-1>", lambda e: self.root.iconify())
        
        # Close button
        close_btn = tk.Label(controls_frame, text="✕", bg=COLORS['bg_dark'], 
                            fg=COLORS['text_secondary'], font=("Segoe UI", 12),
                            cursor="hand2")
        close_btn.pack(side='left', padx=5)
        close_btn.bind("<Button-1>", lambda e: self.root.destroy())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg=COLORS['error']))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=COLORS['text_secondary']))
        
        # Navigation tabs
        nav_frame = tk.Frame(inner_frame, bg=COLORS['bg_dark'], height=50)
        nav_frame.pack(fill='x')
        nav_frame.pack_propagate(False)
        
        tabs_container = tk.Frame(nav_frame, bg=COLORS['bg_dark'])
        tabs_container.pack(side='left', padx=40)
        
        self.tabs = {}
        self.tabs['home'] = TabButton(tabs_container, "🏠 HOME", lambda: self.switch_tab('home'))
        self.tabs['mods'] = TabButton(tabs_container, "🔧 MODS", lambda: self.switch_tab('mods'))
        self.tabs['cosmetics'] = TabButton(tabs_container, "✨ COSMETICS", lambda: self.switch_tab('cosmetics'))
        self.tabs['friends'] = TabButton(tabs_container, "👥 FRIENDS", lambda: self.switch_tab('friends'))
        
        for tab in self.tabs.values():
            tab.pack(side='left', padx=5)
        
        # User info in nav
        self.user_info_frame = tk.Frame(nav_frame, bg=COLORS['bg_dark'])
        self.user_info_frame.pack(side='right', padx=40)
        
        # Content area
        self.content_frame = tk.Frame(inner_frame, bg=COLORS['bg_dark'])
        self.content_frame.pack(fill='both', expand=True, padx=40, pady=20)
        
        # Create all tab panels
        self.panels = {}
        self.create_home_panel()
        self.create_mods_panel()
        self.create_cosmetics_panel()
        self.create_friends_panel()
        
        # Show home tab by default
        self.switch_tab('home')
        self.update_user_display()

    def create_home_panel(self):
        """Create the home/launch panel"""
        panel = tk.Frame(self.content_frame, bg=COLORS['bg_dark'])
        self.panels['home'] = panel
        
        # Two column layout
        left_panel = tk.Frame(panel, bg=COLORS['bg_dark'], width=350)
        left_panel.pack(side='left', fill='y', padx=(0, 30))
        left_panel.pack_propagate(False)
        
        # Enhanced logo area
        logo_frame = tk.Frame(left_panel, bg=COLORS['bg_medium'], height=200)
        logo_frame.pack(fill='x', pady=(0, 20))
        logo_frame.pack_propagate(False)
        
        # Animated cat logo
        self.logo_canvas = tk.Canvas(logo_frame, width=150, height=150, 
                                    bg=COLORS['bg_medium'], highlightthickness=0)
        self.logo_canvas.pack(pady=25)
        self.draw_cat_logo()
        
        # Brand text with glow effect
        brand_frame = tk.Frame(left_panel, bg=COLORS['bg_dark'])
        brand_frame.pack(pady=10)
        
        brand_label = tk.Label(brand_frame, text="CAT CLIENT", 
                              bg=COLORS['bg_dark'], fg=COLORS['text_primary'],
                              font=("Arial Black", 28, "bold"))
        brand_label.pack()
        
        tagline = tk.Label(brand_frame, text="Lunar Client Experience", 
                          bg=COLORS['bg_dark'], fg=COLORS['accent'],
                          font=("Segoe UI", 11))
        tagline.pack()
        
        # Quick stats
        stats_frame = tk.Frame(left_panel, bg=COLORS['bg_light'])
        stats_frame.pack(fill='x', pady=20)
        
        self.fps_label = tk.Label(stats_frame, text="FPS: Calculating...", 
                                 bg=COLORS['bg_light'], fg=COLORS['lunar_green'],
                                 font=("Segoe UI", 10))
        self.fps_label.pack(pady=5)
        
        # Right panel - Launch settings
        right_panel = tk.Frame(panel, bg=COLORS['bg_medium'])
        right_panel.pack(side='right', fill='both', expand=True)
        
        settings_container = tk.Frame(right_panel, bg=COLORS['bg_medium'])
        settings_container.pack(fill='both', expand=True, padx=30, pady=30)
        
        # Login section
        if not self.logged_in:
            login_frame = tk.Frame(settings_container, bg=COLORS['bg_light'])
            login_frame.pack(fill='x', pady=(0, 20))
            
            tk.Label(login_frame, text="👤 ACCOUNT LOGIN", bg=COLORS['bg_light'], 
                    fg=COLORS['text_primary'], font=("Segoe UI", 12, "bold")).pack(pady=10)
            
            # Auth mode toggle
            auth_toggle_frame = tk.Frame(login_frame, bg=COLORS['bg_light'])
            auth_toggle_frame.pack(pady=10)
            
            self.offline_btn = self._create_toggle_button(auth_toggle_frame, "Offline", 
                                                         lambda: self.set_auth_mode("Offline"))
            self.offline_btn.pack(side='left', padx=5)
            
            self.online_btn = self._create_toggle_button(auth_toggle_frame, "Online", 
                                                        lambda: self.set_auth_mode("Online"))
            self.online_btn.pack(side='left', padx=5)
            
            # Username field
            self.login_username_frame = tk.Frame(login_frame, bg=COLORS['bg_light'])
            self.login_username_frame.pack(fill='x', padx=20, pady=(10, 5))
            
            tk.Label(self.login_username_frame, text="Username", bg=COLORS['bg_light'],
                    fg=COLORS['text_dim'], font=("Segoe UI", 9)).pack(anchor='w')
            
            self.login_username_entry = tk.Entry(self.login_username_frame, 
                                               textvariable=self.username_var,
                                               bg=COLORS['bg_dark'], fg=COLORS['text_primary'],
                                               font=("Segoe UI", 11), bd=0,
                                               insertbackground=COLORS['accent'])
            self.login_username_entry.pack(fill='x', pady=5, ipady=8)
            
            # Password field (for online mode)
            self.login_password_frame = tk.Frame(login_frame, bg=COLORS['bg_light'])
            
            tk.Label(self.login_password_frame, text="Password", bg=COLORS['bg_light'],
                    fg=COLORS['text_dim'], font=("Segoe UI", 9)).pack(anchor='w')
            
            self.login_password_entry = tk.Entry(self.login_password_frame, 
                                               textvariable=self.password_var,
                                               bg=COLORS['bg_dark'], fg=COLORS['text_primary'],
                                               font=("Segoe UI", 11), bd=0, show='*',
                                               insertbackground=COLORS['accent'])
            self.login_password_entry.pack(fill='x', pady=5, ipady=8)
            
            # Login button
            self.login_btn = ModernButton(login_frame, "LOGIN", self.perform_login, 
                                        width=200, height=40, icon="🔑")
            self.login_btn.pack(pady=15)
            
        # Game settings (shown after login)
        self.game_settings_frame = tk.Frame(settings_container, bg=COLORS['bg_medium'])
        
        # Version selector
        version_frame = tk.Frame(self.game_settings_frame, bg=COLORS['bg_medium'])
        version_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(version_frame, text="MINECRAFT VERSION", bg=COLORS['bg_medium'], 
                fg=COLORS['text_dim'], font=("Segoe UI", 9, "bold")).pack(anchor='w', pady=(0, 5))
        
        self.version_combo = ttk.Combobox(version_frame, state='readonly', 
                                         font=("Segoe UI", 11))
        self.version_combo.pack(fill='x', ipady=5)
        
        # Mod loader selector
        mod_frame = tk.Frame(self.game_settings_frame, bg=COLORS['bg_medium'])
        mod_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(mod_frame, text="MOD LOADER", bg=COLORS['bg_medium'], 
                fg=COLORS['text_dim'], font=("Segoe UI", 9, "bold")).pack(anchor='w', pady=(0, 10))
        
        mod_btn_frame = tk.Frame(mod_frame, bg=COLORS['bg_medium'])
        mod_btn_frame.pack(fill='x')
        
        self._create_mod_button(mod_btn_frame, "VANILLA", "Vanilla").pack(side='left', padx=(0, 5))
        self._create_mod_button(mod_btn_frame, "FORGE", "Forge").pack(side='left', padx=5)
        self._create_mod_button(mod_btn_frame, "FABRIC", "Fabric").pack(side='left', padx=5)
        
        # RAM allocation
        ram_frame = tk.Frame(self.game_settings_frame, bg=COLORS['bg_medium'])
        ram_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(ram_frame, text="RAM ALLOCATION", bg=COLORS['bg_medium'], 
                fg=COLORS['text_dim'], font=("Segoe UI", 9, "bold")).pack(anchor='w', pady=(0, 5))
        
        self.ram_var = tk.StringVar(value="4")
        ram_slider_frame = tk.Frame(ram_frame, bg=COLORS['bg_medium'])
        ram_slider_frame.pack(fill='x')
        
        self.ram_label = tk.Label(ram_slider_frame, text="4 GB", bg=COLORS['bg_medium'],
                                 fg=COLORS['text_primary'], font=("Segoe UI", 10))
        self.ram_label.pack(side='right')
        
        self.ram_slider = tk.Scale(ram_slider_frame, from_=2, to=16, orient='horizontal',
                                  variable=self.ram_var, bg=COLORS['bg_medium'],
                                  fg=COLORS['text_primary'], highlightthickness=0,
                                  command=self.update_ram_label)
        self.ram_slider.pack(side='left', fill='x', expand=True)
        
        # Launch options
        options_frame = tk.Frame(self.game_settings_frame, bg=COLORS['bg_medium'])
        options_frame.pack(fill='x', pady=(0, 20))
        
        self.keep_open_check = self._create_custom_checkbox(options_frame, 
                                                           "Keep launcher open",
                                                           self.keep_open)
        self.keep_open_check.pack(fill='x', pady=2)
        
        self.optifine_var = tk.BooleanVar(value=True)
        self.optifine_check = self._create_custom_checkbox(options_frame, 
                                                          "Install OptiFine automatically",
                                                          self.optifine_var)
        self.optifine_check.pack(fill='x', pady=2)
        
        # Launch button
        self.launch_btn = ModernButton(self.game_settings_frame, "LAUNCH MINECRAFT", 
                                      self._start_launch_thread, width=280, height=50,
                                      icon="🚀")
        self.launch_btn.pack(pady=(10, 0))
        
        # Progress bar
        self.progress_canvas = tk.Canvas(self.game_settings_frame, height=6, 
                                        bg=COLORS['bg_light'], highlightthickness=0)
        self.progress_canvas.pack(fill='x', pady=(20, 5))
        self.progress_fill = None
        
        # Status label
        self.status_lbl = tk.Label(self.game_settings_frame, text='Ready to launch', 
                                  bg=COLORS['bg_medium'], fg=COLORS['text_dim'],
                                  font=("Segoe UI", 9), wraplength=400)
        self.status_lbl.pack()
        
        # Update visibility based on login state
        if self.logged_in:
            self.game_settings_frame.pack(fill='both', expand=True)

    def create_mods_panel(self):
        """Create the mods configuration panel"""
        panel = tk.Frame(self.content_frame, bg=COLORS['bg_dark'])
        self.panels['mods'] = panel
        
        # Header
        header_frame = tk.Frame(panel, bg=COLORS['bg_dark'])
        header_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(header_frame, text="⚡ MOD CONFIGURATION", 
                bg=COLORS['bg_dark'], fg=COLORS['text_primary'],
                font=("Segoe UI", 16, "bold")).pack(side='left')
        
        tk.Label(header_frame, text="Customize your gameplay experience", 
                bg=COLORS['bg_dark'], fg=COLORS['text_dim'],
                font=("Segoe UI", 10)).pack(side='left', padx=(20, 0))
        
        # Search bar
        search_frame = tk.Frame(panel, bg=COLORS['bg_medium'])
        search_frame.pack(fill='x', pady=(0, 10))
        
        search_icon = tk.Label(search_frame, text="🔍", bg=COLORS['bg_medium'],
                              fg=COLORS['text_dim'], font=("Segoe UI", 12))
        search_icon.pack(side='left', padx=(10, 5))
        
        self.mod_search = tk.Entry(search_frame, bg=COLORS['bg_medium'], 
                                  fg=COLORS['text_primary'], font=("Segoe UI", 11),
                                  bd=0, insertbackground=COLORS['accent'])
        self.mod_search.pack(side='left', fill='x', expand=True, pady=10)
        self.mod_search.insert(0, "Search mods...")
        self.mod_search.bind("<FocusIn>", lambda e: self.mod_search.delete(0, 'end') if self.mod_search.get() == "Search mods..." else None)
        self.mod_search.bind("<KeyRelease>", self.filter_mods)
        
        # Mods container with scrollbar
        mods_container = tk.Frame(panel, bg=COLORS['bg_medium'])
        mods_container.pack(fill='both', expand=True)
        
        # Create canvas and scrollbar for mods
        canvas = tk.Canvas(mods_container, bg=COLORS['bg_medium'], highlightthickness=0)
        scrollbar = tk.Scrollbar(mods_container, orient="vertical", command=canvas.yview)
        self.mods_list_frame = tk.Frame(canvas, bg=COLORS['bg_medium'])
        
        self.mods_list_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.mods_list_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add mods to the list
        self.mod_widgets = {}
        categories = {
            "Performance": ["fps_boost", "particles", "item_physics"],
            "HUD": ["keystrokes", "cps_counter", "fps_display", "coordinates", "direction_hud", 
                   "armor_status", "potion_effects", "memory_display", "ping_display"],
            "Gameplay": ["toggle_sprint", "fullbright", "zoom", "hitboxes", "time_changer"],
            "Utility": ["chat_mods", "crosshair", "waypoints"]
        }
        
        for category, mod_keys in categories.items():
            # Category header
            cat_frame = tk.Frame(self.mods_list_frame, bg=COLORS['bg_medium'])
            cat_frame.pack(fill='x', pady=(10, 5))
            
            tk.Label(cat_frame, text=category.upper(), bg=COLORS['bg_medium'],
                    fg=COLORS['text_dim'], font=("Segoe UI", 10, "bold")).pack(anchor='w')
            
            # Mods in category
            for mod_key in mod_keys:
                if mod_key in DEFAULT_MODS:
                    self.create_mod_item(self.mods_list_frame, mod_key, DEFAULT_MODS[mod_key])

    def create_mod_item(self, parent, mod_key, mod_data):
        """Create a single mod item in the list"""
        mod_frame = tk.Frame(parent, bg=COLORS['bg_light'], height=60)
        mod_frame.pack(fill='x', pady=2, padx=10)
        mod_frame.pack_propagate(False)
        
        # Toggle switch
        toggle_var = tk.BooleanVar(value=self.mods_config.get(mod_key, {}).get('enabled', mod_data['enabled']))
        toggle_frame = tk.Frame(mod_frame, bg=COLORS['bg_light'])
        toggle_frame.pack(side='left', padx=15)
        
        toggle_canvas = tk.Canvas(toggle_frame, width=50, height=25, 
                                 bg=COLORS['bg_light'], highlightthickness=0)
        toggle_canvas.pack(pady=17)
        
        def draw_toggle():
            toggle_canvas.delete("all")
            bg_color = COLORS['success'] if toggle_var.get() else COLORS['bg_medium']
            toggle_canvas.create_rounded_rect(0, 0, 50, 25, 12, fill=bg_color, outline="")
            
            # Switch circle
            x = 35 if toggle_var.get() else 15
            toggle_canvas.create_oval(x-10, 5, x+10, 20, fill="white", outline="")
        
        def toggle_mod(e=None):
            toggle_var.set(not toggle_var.get())
            self.mods_config[mod_key] = {'enabled': toggle_var.get()}
            self._save_mods_config()
            draw_toggle()
        
        toggle_canvas.bind("<Button-1>", toggle_mod)
        toggle_canvas.create_rounded_rect = lambda x1, y1, x2, y2, r, **kw: self._create_rounded_rect_coords(toggle_canvas, x1, y1, x2, y2, r, **kw)
        
        # Mod info
        info_frame = tk.Frame(mod_frame, bg=COLORS['bg_light'])
        info_frame.pack(side='left', fill='both', expand=True)
        
        tk.Label(info_frame, text=mod_data['name'], bg=COLORS['bg_light'],
                fg=COLORS['text_primary'], font=("Segoe UI", 11, "bold")).pack(anchor='w', pady=(12, 2))
        
        tk.Label(info_frame, text=mod_data['description'], bg=COLORS['bg_light'],
                fg=COLORS['text_dim'], font=("Segoe UI", 9)).pack(anchor='w')
        
        # Settings button
        if mod_key in ['keystrokes', 'crosshair', 'particles']:
            settings_btn = tk.Label(mod_frame, text="⚙", bg=COLORS['bg_light'],
                                   fg=COLORS['text_secondary'], font=("Segoe UI", 16),
                                   cursor="hand2")
            settings_btn.pack(side='right', padx=15)
            settings_btn.bind("<Button-1>", lambda e: self.show_mod_settings(mod_key))
        
        draw_toggle()
        self.mod_widgets[mod_key] = mod_frame

    def create_cosmetics_panel(self):
        """Create the cosmetics panel"""
        panel = tk.Frame(self.content_frame, bg=COLORS['bg_dark'])
        self.panels['cosmetics'] = panel
        
        # Header
        header_frame = tk.Frame(panel, bg=COLORS['bg_dark'])
        header_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(header_frame, text="✨ COSMETICS", 
                bg=COLORS['bg_dark'], fg=COLORS['text_primary'],
                font=("Segoe UI", 16, "bold")).pack(side='left')
        
        tk.Label(header_frame, text="Customize your appearance", 
                bg=COLORS['bg_dark'], fg=COLORS['text_dim'],
                font=("Segoe UI", 10)).pack(side='left', padx=(20, 0))
        
        # Categories
        categories_frame = tk.Frame(panel, bg=COLORS['bg_medium'])
        categories_frame.pack(fill='x', pady=(0, 20))
        
        categories = ["Capes", "Wings", "Bandanas", "Hats", "Emotes"]
        for i, category in enumerate(categories):
            cat_btn = tk.Label(categories_frame, text=category.upper(), 
                              bg=COLORS['accent'] if i == 0 else COLORS['bg_medium'],
                              fg=COLORS['text_primary'], font=("Segoe UI", 10, "bold"),
                              padx=20, pady=10, cursor="hand2")
            cat_btn.pack(side='left', padx=2)
        
        # Cosmetics grid
        grid_frame = tk.Frame(panel, bg=COLORS['bg_dark'])
        grid_frame.pack(fill='both', expand=True)
        
        # Sample cosmetics
        cosmetics = [
            {"name": "Lunar Cape", "icon": "🌙", "rarity": "Epic"},
            {"name": "Dragon Wings", "icon": "🐉", "rarity": "Legendary"},
            {"name": "Fire Cape", "icon": "🔥", "rarity": "Rare"},
            {"name": "Angel Wings", "icon": "👼", "rarity": "Epic"},
            {"name": "Rainbow Cape", "icon": "🌈", "rarity": "Rare"},
            {"name": "Cat Ears", "icon": "🐱", "rarity": "Common"},
        ]
        
        for i, cosmetic in enumerate(cosmetics):
            self.create_cosmetic_item(grid_frame, cosmetic, i)

    def create_cosmetic_item(self, parent, cosmetic, index):
        """Create a cosmetic item card"""
        card = tk.Frame(parent, bg=COLORS['bg_medium'], width=150, height=180)
        card.grid(row=index//4, column=index%4, padx=10, pady=10)
        card.pack_propagate(False)
        
        # Rarity color
        rarity_colors = {
            "Common": COLORS['text_secondary'],
            "Rare": COLORS['lunar_blue'],
            "Epic": COLORS['accent'],
            "Legendary": COLORS['warning']
        }
        
        # Icon
        icon_label = tk.Label(card, text=cosmetic['icon'], bg=COLORS['bg_medium'],
                             font=("Segoe UI", 48))
        icon_label.pack(pady=(20, 10))
        
        # Name
        tk.Label(card, text=cosmetic['name'], bg=COLORS['bg_medium'],
                fg=COLORS['text_primary'], font=("Segoe UI", 10, "bold")).pack()
        
        # Rarity
        tk.Label(card, text=cosmetic['rarity'], bg=COLORS['bg_medium'],
                fg=rarity_colors.get(cosmetic['rarity'], COLORS['text_dim']),
                font=("Segoe UI", 9)).pack()
        
        # Equip button
        equip_btn = tk.Label(card, text="EQUIP", bg=COLORS['accent'],
                            fg=COLORS['text_primary'], font=("Segoe UI", 9, "bold"),
                            padx=20, pady=5, cursor="hand2")
        equip_btn.pack(pady=(10, 0))

    def create_friends_panel(self):
        """Create the friends panel"""
        panel = tk.Frame(self.content_frame, bg=COLORS['bg_dark'])
        self.panels['friends'] = panel
        
        # Header
        header_frame = tk.Frame(panel, bg=COLORS['bg_dark'])
        header_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(header_frame, text="👥 FRIENDS", 
                bg=COLORS['bg_dark'], fg=COLORS['text_primary'],
                font=("Segoe UI", 16, "bold")).pack(side='left')
        
        # Add friend button
        add_friend_btn = ModernButton(header_frame, "ADD FRIEND", 
                                     self.show_add_friend, width=120, height=35,
                                     primary=False)
        add_friend_btn.pack(side='right')
        
        # Friends list
        friends_frame = tk.Frame(panel, bg=COLORS['bg_medium'])
        friends_frame.pack(fill='both', expand=True)
        
        # Online friends header
        online_header = tk.Frame(friends_frame, bg=COLORS['bg_medium'])
        online_header.pack(fill='x', pady=10)
        
        tk.Label(online_header, text="ONLINE - 3", bg=COLORS['bg_medium'],
                fg=COLORS['success'], font=("Segoe UI", 10, "bold")).pack(side='left', padx=20)
        
        # Sample friends
        online_friends = [
            {"name": "CoolPlayer123", "status": "Playing Hypixel", "skin": "😎"},
            {"name": "MinecraftPro", "status": "In Lobby", "skin": "🎮"},
            {"name": "BuildMaster", "status": "Playing Survival", "skin": "🔨"},
        ]
        
        for friend in online_friends:
            self.create_friend_item(friends_frame, friend, online=True)
        
        # Offline friends header
        offline_header = tk.Frame(friends_frame, bg=COLORS['bg_medium'])
        offline_header.pack(fill='x', pady=(20, 10))
        
        tk.Label(offline_header, text="OFFLINE - 5", bg=COLORS['bg_medium'],
                fg=COLORS['text_dim'], font=("Segoe UI", 10, "bold")).pack(side='left', padx=20)

    def create_friend_item(self, parent, friend, online=True):
        """Create a friend list item"""
        item = tk.Frame(parent, bg=COLORS['bg_light'] if online else COLORS['bg_medium'])
        item.pack(fill='x', pady=1)
        
        # Avatar
        avatar = tk.Label(item, text=friend['skin'], bg=item['bg'],
                         font=("Segoe UI", 24))
        avatar.pack(side='left', padx=(20, 10))
        
        # Info
        info_frame = tk.Frame(item, bg=item['bg'])
        info_frame.pack(side='left', fill='both', expand=True)
        
        tk.Label(info_frame, text=friend['name'], bg=item['bg'],
                fg=COLORS['text_primary'], font=("Segoe UI", 11, "bold")).pack(anchor='w', pady=(10, 2))
        
        tk.Label(info_frame, text=friend['status'], bg=item['bg'],
                fg=COLORS['success'] if online else COLORS['text_dim'],
                font=("Segoe UI", 9)).pack(anchor='w', pady=(0, 10))
        
        # Actions
        if online:
            invite_btn = tk.Label(item, text="INVITE", bg=COLORS['accent'],
                                 fg=COLORS['text_primary'], font=("Segoe UI", 9, "bold"),
                                 padx=15, pady=5, cursor="hand2")
            invite_btn.pack(side='right', padx=20)

    def filter_mods(self, event):
        """Filter mods based on search input"""
        search_term = self.mod_search.get().lower()
        if search_term == "search mods...":
            search_term = ""
        
        for mod_key, widget in self.mod_widgets.items():
            mod_data = DEFAULT_MODS.get(mod_key, {})
            if search_term in mod_data.get('name', '').lower() or search_term in mod_data.get('description', '').lower():
                widget.pack(fill='x', pady=2, padx=10)
            else:
                widget.pack_forget()

    def show_mod_settings(self, mod_key):
        """Show settings dialog for specific mod"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"{DEFAULT_MODS[mod_key]['name']} Settings")
        dialog.geometry("400x300")
        dialog.configure(bg=COLORS['bg_dark'])
        dialog.transient(self.root)
        
        # Content based on mod type
        tk.Label(dialog, text=f"Configure {DEFAULT_MODS[mod_key]['name']}", 
                bg=COLORS['bg_dark'], fg=COLORS['text_primary'],
                font=("Segoe UI", 14, "bold")).pack(pady=20)
        
        if mod_key == "keystrokes":
            tk.Label(dialog, text="Position:", bg=COLORS['bg_dark'],
                    fg=COLORS['text_secondary'], font=("Segoe UI", 10)).pack()
            
            positions = ["Top Left", "Top Right", "Bottom Left", "Bottom Right", "Center"]
            for pos in positions:
                tk.Radiobutton(dialog, text=pos, bg=COLORS['bg_dark'],
                              fg=COLORS['text_primary'], font=("Segoe UI", 10),
                              selectcolor=COLORS['bg_dark']).pack(pady=2)

    def show_add_friend(self):
        """Show add friend dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Friend")
        dialog.geometry("300x150")
        dialog.configure(bg=COLORS['bg_dark'])
        dialog.transient(self.root)
        
        tk.Label(dialog, text="Enter username:", bg=COLORS['bg_dark'],
                fg=COLORS['text_primary'], font=("Segoe UI", 11)).pack(pady=20)
        
        entry = tk.Entry(dialog, bg=COLORS['bg_medium'], fg=COLORS['text_primary'],
                        font=("Segoe UI", 11), bd=0, insertbackground=COLORS['accent'])
        entry.pack(fill='x', padx=30, ipady=8)
        
        btn_frame = tk.Frame(dialog, bg=COLORS['bg_dark'])
        btn_frame.pack(pady=20)
        
        ModernButton(btn_frame, "ADD", lambda: dialog.destroy(), 
                    width=100, height=35).pack(side='left', padx=5)
        
        ModernButton(btn_frame, "CANCEL", lambda: dialog.destroy(), 
                    width=100, height=35, primary=False).pack(side='left', padx=5)

    def show_settings(self):
        """Show launcher settings dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Launcher Settings")
        dialog.geometry("500x400")
        dialog.configure(bg=COLORS['bg_dark'])
        dialog.transient(self.root)
        
        # Settings tabs
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill='both', expand=True, padx=20, pady=20)
        
        # General tab
        general_frame = tk.Frame(notebook, bg=COLORS['bg_medium'])
        notebook.add(general_frame, text="General")
        
        tk.Label(general_frame, text="Launcher Settings", bg=COLORS['bg_medium'],
                fg=COLORS['text_primary'], font=("Segoe UI", 12, "bold")).pack(pady=20)
        
        # Add settings options here
        
        # About tab
        about_frame = tk.Frame(notebook, bg=COLORS['bg_medium'])
        notebook.add(about_frame, text="About")
        
        tk.Label(about_frame, text=f"{LAUNCHER_NAME} v{LAUNCHER_VERSION}", 
                bg=COLORS['bg_medium'], fg=COLORS['text_primary'],
                font=("Segoe UI", 14, "bold")).pack(pady=20)
        
        tk.Label(about_frame, text="Premium Minecraft Launcher with Lunar Client Features", 
                bg=COLORS['bg_medium'], fg=COLORS['text_secondary'],
                font=("Segoe UI", 10)).pack()
        
        tk.Label(about_frame, text="© Team Flames 2025", 
                bg=COLORS['bg_medium'], fg=COLORS['text_dim'],
                font=("Segoe UI", 9)).pack(pady=(10, 0))

    def switch_tab(self, tab_name):
        """Switch between tabs"""
        # Update tab buttons
        for name, tab_btn in self.tabs.items():
            tab_btn.set_active(name == tab_name)
        
        # Hide all panels
        for panel in self.panels.values():
            panel.pack_forget()
        
        # Show selected panel
        if tab_name in self.panels:
            self.panels[tab_name].pack(fill='both', expand=True)
            
        self.current_tab = tab_name

    def perform_login(self):
        """Handle login process"""
        username = self.username_var.get().strip()
        
        if not username:
            messagebox.showerror("Login Error", "Please enter a username!")
            return
        
        if self.auth_mode.get() == "Offline":
            if not self._is_valid_username(username):
                messagebox.showerror("Login Error", "Username must be 3-16 characters (letters, numbers, underscore only)")
                return
            
            self.logged_in = True
            self.current_user_data = {
                'username': username,
                'uuid': str(uuid.uuid3(uuid.NAMESPACE_DNS, f'Offline:{username}')),
                'mode': 'Offline'
            }
        else:
            # Online mode (cracked)
            password = self.password_var.get()
            if not password:
                messagebox.showerror("Login Error", "Please enter a password!")
                return
            
            # Simulate authentication
            self.logged_in = True
            self.current_user_data = {
                'username': username,
                'uuid': str(uuid.uuid5(uuid.NAMESPACE_DNS, f'catclient:{username}')).replace('-', ''),
                'mode': 'Online',
                'token': str(uuid.uuid4()).replace('-', '')
            }
        
        # Update UI after login
        self.update_user_display()
        
        # Show game settings
        for widget in self.panels['home'].winfo_children():
            if isinstance(widget, tk.Frame) and widget.winfo_children():
                for child in widget.winfo_children():
                    if hasattr(child, 'winfo_children') and any('LOGIN' in str(w.cget('text') if hasattr(w, 'cget') else '') for w in child.winfo_children() if hasattr(w, 'cget')):
                        child.pack_forget()
        
        self.game_settings_frame.pack(fill='both', expand=True)
        self._update_status(f"Logged in as {username}")

    def update_user_display(self):
        """Update user info display in navigation"""
        for widget in self.user_info_frame.winfo_children():
            widget.destroy()
        
        if self.logged_in and self.current_user_data:
            # User avatar
            avatar = tk.Label(self.user_info_frame, text="👤", 
                             bg=COLORS['bg_dark'], fg=COLORS['accent'],
                             font=("Segoe UI", 16))
            avatar.pack(side='left', padx=(0, 10))
            
            # Username
            user_label = tk.Label(self.user_info_frame, 
                                 text=self.current_user_data['username'],
                                 bg=COLORS['bg_dark'], fg=COLORS['text_primary'],
                                 font=("Segoe UI", 11, "bold"))
            user_label.pack(side='left')
            
            # Mode indicator
            mode_label = tk.Label(self.user_info_frame, 
                                 text=f"({self.current_user_data['mode']})",
                                 bg=COLORS['bg_dark'], fg=COLORS['text_dim'],
                                 font=("Segoe UI", 9))
            mode_label.pack(side='left', padx=(5, 0))
            
            # Logout button
            logout_btn = tk.Label(self.user_info_frame, text="LOGOUT",
                                 bg=COLORS['bg_dark'], fg=COLORS['error'],
                                 font=("Segoe UI", 9), cursor="hand2")
            logout_btn.pack(side='left', padx=(20, 0))
            logout_btn.bind("<Button-1>", lambda e: self.logout())

    def logout(self):
        """Handle logout"""
        self.logged_in = False
        self.current_user_data = None
        self.update_user_display()
        self.switch_tab('home')
        
        # Reset home panel to show login
        for widget in self.panels['home'].winfo_children():
            widget.destroy()
        self.create_home_panel()

    def set_auth_mode(self, mode):
        """Set authentication mode and update UI"""
        self.auth_mode.set(mode)
        
        # Update button appearance
        if mode == "Offline":
            self.offline_btn.config(bg=COLORS['accent'], fg=COLORS['text_primary'])
            self.online_btn.config(bg=COLORS['bg_medium'], fg=COLORS['text_secondary'])
            self.login_password_frame.pack_forget()
        else:
            self.offline_btn.config(bg=COLORS['bg_medium'], fg=COLORS['text_secondary'])
            self.online_btn.config(bg=COLORS['accent'], fg=COLORS['text_primary'])
            self.login_password_frame.pack(fill='x', padx=20, pady=(5, 5))

    def _create_toggle_button(self, parent, text, command):
        """Create a toggle button"""
        btn = tk.Label(parent, text=text, bg=COLORS['bg_medium'],
                      fg=COLORS['text_secondary'], font=("Segoe UI", 10),
                      padx=20, pady=8, cursor="hand2")
        btn.bind("<Button-1>", lambda e: command())
        return btn

    def update_ram_label(self, value):
        """Update RAM allocation label"""
        self.ram_label.config(text=f"{value} GB")

    def update_system_stats(self):
        """Update system statistics display"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            stats_text = f"CPU: {cpu_percent}% | RAM: {memory.percent}% | {platform.system()}"
            self.stats_label.config(text=stats_text)
            
            # Update FPS counter (simulated)
            self.fps_counter = (self.fps_counter + 1) % 1000
            current_time = time.time()
            if current_time - self.last_fps_time >= 1.0:
                fps = self.fps_counter / (current_time - self.last_fps_time)
                self.fps_label.config(text=f"FPS: {int(fps)}")
                self.fps_counter = 0
                self.last_fps_time = current_time
        except:
            pass
        
        self.root.after(1000, self.update_system_stats)

    def draw_cat_logo(self):
        """Draw enhanced animated cat logo"""
        self.logo_canvas.delete("all")
        center_x, center_y = 75, 75
        
        # Animated background circles
        for i in range(12):
            angle = self.animation_angle + i * 30
            radius = 40 + 10 * tk.math.sin(tk.math.radians(angle))
            x = center_x + radius * tk.math.cos(tk.math.radians(angle))
            y = center_y + radius * tk.math.sin(tk.math.radians(angle))
            size = 6 + 2 * tk.math.sin(tk.math.radians(angle * 2))
            
            # Gradient effect
            color_intensity = int(100 + 55 * tk.math.sin(tk.math.radians(angle)))
            color = f"#{color_intensity:02x}{65:02x}{165:02x}"
            
            self.logo_canvas.create_oval(x-size, y-size, x+size, y+size, 
                                        fill=color, outline="")
        
        # Glowing effect
        for i in range(3):
            glow_size = 50 + i * 10
            alpha = 30 - i * 10
            self.logo_canvas.create_oval(center_x-glow_size, center_y-glow_size,
                                        center_x+glow_size, center_y+glow_size,
                                        fill="", outline=COLORS['accent'],
                                        width=2, stipple='gray25')
        
        # Cat silhouette with gradient
        # Head
        self.logo_canvas.create_oval(45, 45, 105, 105, fill=COLORS['accent'], 
                                    outline=COLORS['accent_light'], width=2)
        
        # Ears with detail
        self.logo_canvas.create_polygon(50, 55, 45, 30, 65, 45, 
                                       fill=COLORS['accent'], outline=COLORS['accent_light'])
        self.logo_canvas.create_polygon(85, 45, 105, 30, 100, 55, 
                                       fill=COLORS['accent'], outline=COLORS['accent_light'])
        
        # Inner ears
        self.logo_canvas.create_polygon(55, 50, 52, 38, 62, 45, 
                                       fill=COLORS['accent_light'], outline="")
        self.logo_canvas.create_polygon(88, 45, 98, 38, 95, 50, 
                                       fill=COLORS['accent_light'], outline="")
        
        # Eyes with animation
        eye_glow = COLORS['lunar_green'] if self.is_loading else "#ffffff"
        eye_size = 4 + tk.math.sin(tk.math.radians(self.animation_angle * 3))
        
        # Left eye
        self.logo_canvas.create_oval(60-eye_size, 65-eye_size, 60+eye_size, 65+eye_size, 
                                    fill=eye_glow, outline="")
        # Right eye
        self.logo_canvas.create_oval(90-eye_size, 65-eye_size, 90+eye_size, 65+eye_size, 
                                    fill=eye_glow, outline="")
        
        # Nose
        self.logo_canvas.create_polygon(75, 75, 70, 82, 80, 82, 
                                       fill="#ff69b4", outline="")
        
        # Whiskers
        whisker_angle = tk.math.sin(tk.math.radians(self.animation_angle * 2)) * 5
        self.logo_canvas.create_line(30, 70 + whisker_angle, 55, 72, 
                                    fill=COLORS['text_dim'], width=2)
        self.logo_canvas.create_line(95, 72, 120, 70 + whisker_angle, 
                                    fill=COLORS['text_dim'], width=2)

    def animate_logo(self):
        """Animate the logo rotation and effects"""
        self.animation_angle = (self.animation_angle + 3) % 360
        self.draw_cat_logo()
        self.root.after(30, self.animate_logo)

    def _create_rounded_rect_coords(self, canvas, x1, y1, x2, y2, radius, **kwargs):
        """Helper to create rounded rectangle"""
        points = []
        for x, y in [(x1, y1 + radius), (x1, y2 - radius), 
                     (x1 + radius, y2), (x2 - radius, y2),
                     (x2, y2 - radius), (x2, y1 + radius),
                     (x2 - radius, y1), (x1 + radius, y1)]:
            points.extend([x, y])
        return canvas.create_polygon(points, smooth=True, **kwargs)

    def _create_custom_checkbox(self, parent, text, variable):
        """Create custom styled checkbox"""
        frame = tk.Frame(parent, bg=COLORS['bg_medium'], cursor="hand2")
        
        # Checkbox
        check_canvas = tk.Canvas(frame, width=20, height=20, bg=COLORS['bg_medium'],
                                highlightthickness=0)
        check_canvas.pack(side='left', padx=(0, 10))
        
        def draw_check():
            check_canvas.delete("all")
            # Box
            check_canvas.create_rectangle(2, 2, 18, 18, outline=COLORS['border'], width=2)
            # Check mark if selected
            if variable.get():
                check_canvas.create_line(5, 10, 8, 13, fill=COLORS['accent'], width=2)
                check_canvas.create_line(8, 13, 15, 6, fill=COLORS['accent'], width=2)
        
        # Label
        label = tk.Label(frame, text=text, bg=COLORS['bg_medium'], 
                        fg=COLORS['text_secondary'], font=("Segoe UI", 10))
        label.pack(side='left')
        
        def toggle(e=None):
            variable.set(not variable.get())
            draw_check()
        
        frame.bind("<Button-1>", toggle)
        label.bind("<Button-1>", toggle)
        check_canvas.bind("<Button-1>", toggle)
        
        draw_check()
        return frame

    def _create_mod_button(self, parent, text, value):
        """Create mod selection button"""
        btn = tk.Frame(parent, bg=COLORS['bg_light'], cursor="hand2")
        
        label = tk.Label(btn, text=text, bg=COLORS['bg_light'], 
                        fg=COLORS['text_primary'], font=("Segoe UI", 10, "bold"),
                        padx=20, pady=8)
        label.pack()
        
        def update_appearance():
            if self.mod_choice.get() == value:
                btn.config(bg=COLORS['accent'])
                label.config(bg=COLORS['accent'])
            else:
                btn.config(bg=COLORS['bg_light'])
                label.config(bg=COLORS['bg_light'])
        
        def on_click(e=None):
            self.mod_choice.set(value)
            # Update all mod buttons
            for widget in parent.winfo_children():
                if isinstance(widget, tk.Frame):
                    widget.event_generate("<<UpdateMod>>")
        
        btn.bind("<Button-1>", on_click)
        label.bind("<Button-1>", on_click)
        btn.bind("<<UpdateMod>>", lambda e: update_appearance())
        btn.bind("<Enter>", lambda e: btn.config(bg=COLORS['accent_hover']) if self.mod_choice.get() != value else None)
        btn.bind("<Leave>", lambda e: update_appearance())
        
        update_appearance()
        return btn

    def _start_drag(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _drag_window(self, event):
        x = self.root.winfo_x() + (event.x - self._drag_data["x"])
        y = self.root.winfo_y() + (event.y - self._drag_data["y"])
        self.root.geometry(f"+{x}+{y}")

    # --- Configuration Management ---
    def _load_config(self):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            self.username_var.set(config.get('username', 'Player'))
            self.auth_mode.set(config.get('auth_mode', 'Offline'))
            self.keep_open.set(config.get('keep_open', False))
            self.mod_choice.set(config.get('mod_choice', 'Vanilla'))
            self.ram_var.set(config.get('ram_allocation', '4'))
            self.optifine_var.set(config.get('auto_optifine', True))
            last_version = config.get('last_version')
            if last_version:
                self.root.after(1000, lambda: self.version_combo.set(last_version))
        except (FileNotFoundError, json.JSONDecodeError):
            self.username_var.set('Player')

    def _save_config(self):
        config = {
            'username': self.username_var.get(),
            'auth_mode': self.auth_mode.get(),
            'last_version': self.version_combo.get(),
            'keep_open': self.keep_open.get(),
            'mod_choice': self.mod_choice.get(),
            'ram_allocation': self.ram_var.get(),
            'auto_optifine': self.optifine_var.get(),
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)

    def _load_mods_config(self):
        """Load mods configuration"""
        try:
            with open(MODS_CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_mods_config(self):
        """Save mods configuration"""
        with open(MODS_CONFIG_FILE, 'w') as f:
            json.dump(self.mods_config, f, indent=4)

    def _load_cosmetics_config(self):
        """Load cosmetics configuration"""
        try:
            with open(COSMETICS_CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_cosmetics_config(self):
        """Save cosmetics configuration"""
        with open(COSMETICS_CONFIG_FILE, 'w') as f:
            json.dump(self.cosmetics_config, f, indent=4)

    # --- UI Logic & Threading ---
    def _toggle_auth_mode(self):
        """Legacy method for backward compatibility"""
        pass

    def _process_queue(self):
        """Process status updates from worker threads"""
        try:
            while True:
                msg, fin, err, prog = self.status_queue.get_nowait()
                if msg:
                    self.status_lbl.config(text=msg, fg=COLORS['error'] if err else COLORS['text_dim'])
                if prog is not None:
                    self._update_progress(prog)
                if fin:
                    self.launch_btn.destroy()
                    self.launch_btn = ModernButton(self.game_settings_frame, "LAUNCH MINECRAFT", 
                                                  self._start_launch_thread, width=280, height=50,
                                                  icon="🚀")
                    self.launch_btn.pack(pady=(10, 0))
                    self._update_progress(0)
                    self.is_loading = False
        except queue.Empty:
            pass
        self.root.after(16, self._process_queue)

    def _update_progress(self, value):
        """Update progress bar with smooth animation"""
        if self.progress_fill:
            self.progress_canvas.delete(self.progress_fill)
        if value > 0:
            width = (value / 100) * self.progress_canvas.winfo_width()
            # Gradient progress bar
            self.progress_fill = self.progress_canvas.create_rectangle(
                0, 0, width, 6, fill=COLORS['accent'], outline=""
            )
            # Add shimmer effect
            shimmer = self.progress_canvas.create_rectangle(
                width-20, 0, width, 6, fill=COLORS['accent_light'], outline="",
                stipple='gray50'
            )

    def _update_status(self, text, *, final=False, error=False, prog=None):
        self.status_queue.put((text, final, error, prog))

    def _populate_versions(self):
        self._update_status('Fetching version list...')
        def worker():
            try:
                versions = [v['id'] for v in minecraft_launcher_lib.utils.get_version_list() if v['type'] == 'release']
                versions.sort(key=lambda s: [int(p) if p.isdigit() else p for p in s.split('.')], reverse=True)
                latest_stable = minecraft_launcher_lib.utils.get_latest_version()['release']
                self.root.after(0, lambda: self.version_combo.configure(values=versions))
                if not self.version_combo.get() and latest_stable in versions:
                    self.root.after(0, lambda: self.version_combo.set(latest_stable))
                self._update_status('Ready to launch', final=True)
            except Exception as e:
                self._update_status(f'Error fetching versions: {e}', final=True, error=True)
        threading.Thread(target=worker, daemon=True).start()

    # --- Launch Logic ---
    def _start_launch_thread(self):
        if not self.logged_in:
            messagebox.showerror("Launch Error", "Please login first!")
            return
            
        self.launch_btn.destroy()
        loading_label = tk.Label(self.game_settings_frame, text="🚀 LAUNCHING...", 
                                bg=COLORS['bg_medium'], fg=COLORS['accent'],
                                font=("Segoe UI", 12, "bold"))
        loading_label.pack(pady=(10, 0))
        self.is_loading = True
        self._update_progress(0)
        threading.Thread(target=self._launch_minecraft, daemon=True).start()

    @staticmethod
    def _is_valid_username(name):
        return bool(re.match(r'^[A-Za-z0-9_]{3,16}$', name))

    def _download_optifine(self, mc_version):
        """Download and install OptiFine"""
        self._update_status("Checking for OptiFine...")
        # This would normally download OptiFine - simplified for example
        # In reality, you'd need to implement OptiFine downloading logic
        return None

    def _apply_lunar_mods(self, minecraft_directory):
        """Apply Lunar Client-style mods based on configuration"""
        self._update_status("Applying Lunar mods...")
        
        # Create mods folder
        mods_folder = os.path.join(minecraft_directory, "mods")
        os.makedirs(mods_folder, exist_ok=True)
        
        # Generate mod config file for enabled mods
        enabled_mods = {k: v for k, v in self.mods_config.items() if v.get('enabled', False)}
        
        config_file = os.path.join(minecraft_directory, "config", "catclient_mods.json")
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(enabled_mods, f, indent=4)
        
        self._update_status(f"Enabled {len(enabled_mods)} mods")

    def _ensure_authlib_present(self):
        """Downloads authlib if not already present."""
        if os.path.exists(self.authlib_path):
            return self.authlib_path

        response = messagebox.askyesno(
            "Cat Client - Download Required",
            "Skin support requires downloading authlib-injector.\n\n"
            "Download now? (about 500KB)\n\n"
            "You can play without it, but skins won't be visible."
        )
        
        if not response:
            return None

        self._update_status("Downloading skin support...")
        try:
            os.makedirs(os.path.dirname(self.authlib_path), exist_ok=True)
            with requests.get(AUTHLIB_URL, stream=True) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                bytes_downloaded = 0
                with open(self.authlib_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        bytes_downloaded += len(chunk)
                        if total_size > 0:
                            prog = (bytes_downloaded / total_size) * 100
                            self._update_status(f"Downloading: {int(prog)}%", prog=prog)
            self._update_status("Download complete!")
            return self.authlib_path
        except Exception as e:
            self._update_status(f"Download failed: {e}", error=True)
            if os.path.exists(self.authlib_path):
                os.remove(self.authlib_path)
            return None

    def _launch_minecraft(self):
        self._save_config()

        base_version = self.version_combo.get()
        if not base_version:
            self._update_status('Please select a Minecraft version!', final=True, error=True)
            return

        # JVM Arguments with optimizations
        ram_gb = self.ram_var.get()
        options = {
            'jvmArguments': [
                f'-Xms{int(int(ram_gb)*0.5)}G', f'-Xmx{ram_gb}G', 
                '-XX:+UnlockExperimentalVMOptions', '-XX:+UseG1GC',
                '-XX:G1NewSizePercent=20', '-XX:G1ReservePercent=20', 
                '-XX:MaxGCPauseMillis=50', '-XX:G1HeapRegionSize=32M',
                '-XX:+DisableExplicitGC', '-XX:+AlwaysPreTouch',
                '-XX:+ParallelRefProcEnabled',
                # Lunar Client optimizations
                '-Dfml.ignorePatchDiscrepancies=true',
                '-Dfml.ignoreInvalidMinecraftCertificates=true',
                '-Dlog4j2.formatMsgNoLookups=true',
                f'-Dcatclient.version={LAUNCHER_VERSION}',
                f'-Dcatclient.mods={json.dumps(list(self.mods_config.keys()))}'
            ]
        }

        # Use logged in user data
        if self.current_user_data:
            options.update({
                'username': self.current_user_data['username'],
                'uuid': self.current_user_data['uuid'],
                'token': self.current_user_data.get('token', '0')
            })
            
            if self.current_user_data['mode'] == 'Online':
                authlib_path = self._ensure_authlib_present()
                if authlib_path:
                    self._update_status("Enabling skin support...")
                    options['jvmArguments'].extend([
                        f"-javaagent:{authlib_path}=littleskin.cn",
                        f"-Dauthlibinjector.username={self.current_user_data['username']}",
                        "-Dauthlibinjector.side=client",
                        "-Dauthlibinjector.profileKey=false"
                    ])

        # Version & Mod Installation
        target_version_id = base_version
        mod_system = self.mod_choice.get()
        callback_dict = {
            'setStatus': lambda s: self._update_status(s),
            'setProgress': lambda v: self._update_status('', prog=v),
            'setMax': lambda _: None
        }

        try:
            self._update_status(f'Preparing {base_version}...')
            minecraft_launcher_lib.install.install_minecraft_version(base_version, self.minecraft_directory, callback=callback_dict)

            # Install mod loader
            if mod_system == 'Forge':
                self._update_status(f'Installing Forge...')
                forge_version = minecraft_launcher_lib.forge.find_latest_version(base_version)
                if not forge_version:
                    raise RuntimeError(f"No Forge support for {base_version}")
                
                target_version_id = f"{base_version}-forge-{forge_version}"
                self._update_status(f"Installing Forge {forge_version}...")
                minecraft_launcher_lib.forge.install_forge_version(forge_version, self.minecraft_directory, callback=callback_dict)

            elif mod_system == 'Fabric':
                self._update_status(f'Installing Fabric...')
                minecraft_launcher_lib.fabric.install_fabric(base_version, self.minecraft_directory, callback=callback_dict)
                installed_versions = minecraft_launcher_lib.utils.get_installed_versions(self.minecraft_directory)
                fabric_versions = [v for v in installed_versions if v["id"].startswith(f"fabric-loader-") and base_version in v["id"]]
                if not fabric_versions:
                    raise RuntimeError("Fabric installation failed")
                target_version_id = fabric_versions[0]["id"]
            
            # Install OptiFine if enabled
            if self.optifine_var.get() and mod_system != 'Fabric':
                optifine_path = self._download_optifine(base_version)
                if optifine_path:
                    self._update_status("Installing OptiFine...")
                    # OptiFine installation logic would go here
            
            # Apply Lunar-style mods
            self._apply_lunar_mods(self.minecraft_directory)
            
            # Add custom launch options
            options['customResolution'] = True
            options['resolutionWidth'] = '1920'
            options['resolutionHeight'] = '1080'
            
            # Launch
            self._update_status(f'Starting Minecraft with Cat Client enhancements...')
            minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(target_version_id, self.minecraft_directory, options)
            
            # Add Lunar Client window title
            env = os.environ.copy()
            env['MINECRAFT_LAUNCHER_BRAND'] = f'cat-client/{LAUNCHER_VERSION}'
            
            subprocess.Popen(minecraft_command, env=env)
            
            self._update_status('Game launched successfully! 🎮', final=not self.keep_open.get())
            
            # Show post-launch message
            if not self.keep_open.get():
                self.root.after(3000, self.root.destroy)
            else:
                self._update_status('Game is running. You can close this launcher.')

        except Exception as e:
            self._update_status(f'Launch failed: {e}', final=True, error=True)
            messagebox.showerror('Cat Client - Launch Error', f'Failed to launch:\n\n{e}')

    def run(self):
        """Start the launcher"""
        # Center window on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1100 // 2)
        y = (self.root.winfo_screenheight() // 2) - (700 // 2)
        self.root.geometry(f"+{x}+{y}")
        
        # Add drop shadow effect (Windows only)
        if platform.system() == "Windows":
            try:
                from ctypes import windll, c_int, byref, sizeof
                windll.dwmapi.DwmSetWindowAttribute(
                    windll.user32.GetParent(self.root.winfo_id()),
                    35, byref(c_int(0x00000002)), sizeof(c_int)
                )
            except:
                pass
        
        self.root.mainloop()


def main():
    """Entry point for Cat Client"""
    try:
        # Check for required libraries
        required_libs = ['minecraft_launcher_lib', 'psutil', 'requests']
        missing_libs = []
        
        for lib in required_libs:
            try:
                __import__(lib)
            except ImportError:
                missing_libs.append(lib)
        
        if missing_libs:
            response = messagebox.askyesno(
                "Cat Client - Missing Dependencies",
                f"The following required libraries are missing:\n{', '.join(missing_libs)}\n\n"
                "Would you like to install them now?"
            )
            if response:
                subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_libs)
                messagebox.showinfo("Cat Client", "Dependencies installed! Please restart the launcher.")
                return
            else:
                messagebox.showerror("Cat Client", "Cannot run without required dependencies.")
                return
        
        # Add tkinter math module for animations
        tk.math = __import__('math')
        
        # Start launcher
        launcher = CatClientLauncher()
        launcher.run()
        
    except Exception as e:
        print(f"Fatal error: {e}")
        messagebox.showerror("Cat Client - Fatal Error", f"Could not start launcher:\n\n{e}")


if __name__ == "__main__":
    import sys
    main()

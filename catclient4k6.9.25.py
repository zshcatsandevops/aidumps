#!/usr/bin/env python3
"""
Cat Client 1.0x - Premium Minecraft Launcher
© Team Flames 2025
Lunar Client inspired design with modern aesthetics
"""

import tkinter as tk
from tkinter import ttk, messagebox, font
import threading
import queue
import json
import os
import re
import uuid
import subprocess
import requests
import minecraft_launcher_lib
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import io

# --- Constants ---
LAUNCHER_NAME = "Cat Client"
LAUNCHER_VERSION = "1.0x"
CONFIG_FILE = "catclient_config.json"
AUTHLIB_URL = "https://authlib-injector.yushi.moe/artifact/latest/authlib-injector.jar"

# Lunar Client inspired color scheme
COLORS = {
    'bg_dark': '#0e0e10',
    'bg_medium': '#18181b',
    'bg_light': '#1f1f23',
    'accent': '#6441a5',  # Purple accent
    'accent_hover': '#7c5daf',
    'text_primary': '#efeff1',
    'text_secondary': '#adadb8',
    'text_dim': '#848494',
    'success': '#00ff88',
    'error': '#ff4545',
    'border': '#2a2a2d'
}

class ModernButton(tk.Canvas):
    def __init__(self, parent, text, command, width=200, height=45, primary=True):
        super().__init__(parent, width=width, height=height, highlightthickness=0,
                         bg=COLORS['bg_dark'], bd=0)
        self.command = command
        self.text = text
        self.width = width
        self.height = height
        self.primary = primary
        
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
        
    def draw_button(self, hover=False):
        self.delete("all")
        color = self.hover_color if hover else self.normal_color
        
        # Draw rounded rectangle
        radius = 8
        self.rect = self.create_rounded_rect(2, 2, self.width-2, self.height-2, radius, 
                                            fill=color, outline=color)
        
        # Draw text
        self.text_id = self.create_text(self.width//2, self.height//2, text=self.text,
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
        if self.command:
            self.command()

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
        
        # Animation variables
        self.animation_angle = 0
        self.is_loading = False

        self._setup_ui()
        self._populate_versions()
        self.root.after(100, self._process_queue)
        self._load_config()
        self._toggle_auth_mode()
        
        # Start logo animation
        self.animate_logo()

    def _setup_ui(self):
        self.root.title(f"{LAUNCHER_NAME} {LAUNCHER_VERSION}")
        self.root.geometry("900x600")
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
        
        # Title
        title_text = tk.Label(title_bar, text=f"{LAUNCHER_NAME} {LAUNCHER_VERSION}", 
                             bg=COLORS['bg_dark'], fg=COLORS['text_primary'],
                             font=("Segoe UI", 10, "bold"))
        title_text.pack(side='left', padx=15, pady=8)
        
        # Window controls
        controls_frame = tk.Frame(title_bar, bg=COLORS['bg_dark'])
        controls_frame.pack(side='right', padx=10)
        
        # Close button
        close_btn = tk.Label(controls_frame, text="✕", bg=COLORS['bg_dark'], 
                            fg=COLORS['text_secondary'], font=("Segoe UI", 12),
                            cursor="hand2")
        close_btn.pack(side='right', padx=5)
        close_btn.bind("<Button-1>", lambda e: self.root.destroy())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg=COLORS['error']))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=COLORS['text_secondary']))
        
        # Minimize button
        min_btn = tk.Label(controls_frame, text="—", bg=COLORS['bg_dark'], 
                          fg=COLORS['text_secondary'], font=("Segoe UI", 12),
                          cursor="hand2")
        min_btn.pack(side='right', padx=5)
        min_btn.bind("<Button-1>", lambda e: self.root.iconify())
        min_btn.bind("<Enter>", lambda e: min_btn.config(fg=COLORS['text_primary']))
        min_btn.bind("<Leave>", lambda e: min_btn.config(fg=COLORS['text_secondary']))
        
        # Main content area
        content_frame = tk.Frame(inner_frame, bg=COLORS['bg_dark'])
        content_frame.pack(fill='both', expand=True, padx=40, pady=20)
        
        # Left panel
        left_panel = tk.Frame(content_frame, bg=COLORS['bg_dark'], width=300)
        left_panel.pack(side='left', fill='y', padx=(0, 30))
        left_panel.pack_propagate(False)
        
        # Logo area
        logo_frame = tk.Frame(left_panel, bg=COLORS['bg_dark'], height=150)
        logo_frame.pack(fill='x', pady=(0, 30))
        logo_frame.pack_propagate(False)
        
        # Cat logo (animated)
        self.logo_canvas = tk.Canvas(logo_frame, width=120, height=120, 
                                    bg=COLORS['bg_dark'], highlightthickness=0)
        self.logo_canvas.pack(pady=15)
        self.draw_cat_logo()
        
        # Brand text
        brand_label = tk.Label(left_panel, text="CAT CLIENT", 
                              bg=COLORS['bg_dark'], fg=COLORS['text_primary'],
                              font=("Arial Black", 24, "bold"))
        brand_label.pack()
        
        version_label = tk.Label(left_panel, text=f"Version {LAUNCHER_VERSION}", 
                                bg=COLORS['bg_dark'], fg=COLORS['text_dim'],
                                font=("Segoe UI", 10))
        version_label.pack()
        
        # Copyright
        tk.Label(left_panel, text="© Team Flames 2025", 
                bg=COLORS['bg_dark'], fg=COLORS['text_dim'],
                font=("Segoe UI", 9)).pack(side='bottom', pady=10)
        
        # Right panel
        right_panel = tk.Frame(content_frame, bg=COLORS['bg_medium'])
        right_panel.pack(side='right', fill='both', expand=True)
        
        # Settings container
        settings_frame = tk.Frame(right_panel, bg=COLORS['bg_medium'])
        settings_frame.pack(fill='both', expand=True, padx=30, pady=30)
        
        # Auth mode selector
        auth_frame = tk.Frame(settings_frame, bg=COLORS['bg_medium'])
        auth_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(auth_frame, text="AUTHENTICATION", bg=COLORS['bg_medium'], 
                fg=COLORS['text_dim'], font=("Segoe UI", 9, "bold")).pack(anchor='w', pady=(0, 10))
        
        # Custom radio buttons
        self.offline_radio = self._create_custom_radio(auth_frame, "Offline Mode", 
                                                       self.auth_mode, "Offline", 
                                                       self._toggle_auth_mode)
        self.online_radio = self._create_custom_radio(auth_frame, "Online (Cracked)", 
                                                      self.auth_mode, "Online", 
                                                      self._toggle_auth_mode)
        
        # Username field
        self.username_frame = tk.Frame(settings_frame, bg=COLORS['bg_medium'])
        self.username_frame.pack(fill='x', pady=(0, 15))
        
        self.username_lbl = tk.Label(self.username_frame, text="USERNAME", 
                                    bg=COLORS['bg_medium'], fg=COLORS['text_dim'],
                                    font=("Segoe UI", 9, "bold"))
        self.username_lbl.pack(anchor='w', pady=(0, 5))
        
        username_container = tk.Frame(self.username_frame, bg=COLORS['bg_light'], 
                                     highlightbackground=COLORS['border'], 
                                     highlightthickness=1)
        username_container.pack(fill='x')
        
        self.username_entry = tk.Entry(username_container, textvariable=self.username_var,
                                      bg=COLORS['bg_light'], fg=COLORS['text_primary'],
                                      font=("Segoe UI", 11), bd=0, insertbackground=COLORS['accent'])
        self.username_entry.pack(fill='x', padx=10, pady=10)
        
        # Password field
        self.password_frame = tk.Frame(settings_frame, bg=COLORS['bg_medium'])
        
        self.password_lbl = tk.Label(self.password_frame, text="PASSWORD", 
                                    bg=COLORS['bg_medium'], fg=COLORS['text_dim'],
                                    font=("Segoe UI", 9, "bold"))
        
        password_container = tk.Frame(self.password_frame, bg=COLORS['bg_light'], 
                                     highlightbackground=COLORS['border'], 
                                     highlightthickness=1)
        
        self.password_entry = tk.Entry(password_container, textvariable=self.password_var,
                                      bg=COLORS['bg_light'], fg=COLORS['text_primary'],
                                      font=("Segoe UI", 11), bd=0, show='*',
                                      insertbackground=COLORS['accent'])
        
        # Version selector
        version_frame = tk.Frame(settings_frame, bg=COLORS['bg_medium'])
        version_frame.pack(fill='x', pady=(20, 15))
        
        tk.Label(version_frame, text="MINECRAFT VERSION", bg=COLORS['bg_medium'], 
                fg=COLORS['text_dim'], font=("Segoe UI", 9, "bold")).pack(anchor='w', pady=(0, 5))
        
        # Custom styled combobox
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Custom.TCombobox',
                       fieldbackground=COLORS['bg_light'],
                       background=COLORS['bg_light'],
                       foreground=COLORS['text_primary'],
                       borderwidth=1,
                       arrowcolor=COLORS['text_secondary'])
        
        version_container = tk.Frame(version_frame, bg=COLORS['border'])
        version_container.pack(fill='x')
        
        inner_version = tk.Frame(version_container, bg=COLORS['bg_light'])
        inner_version.pack(fill='x', padx=1, pady=1)
        
        self.version_combo = ttk.Combobox(inner_version, style='Custom.TCombobox',
                                         state='readonly', font=("Segoe UI", 11))
        self.version_combo.pack(fill='x', padx=10, pady=8)
        
        # Mod loader selector
        mod_frame = tk.Frame(settings_frame, bg=COLORS['bg_medium'])
        mod_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(mod_frame, text="MOD LOADER", bg=COLORS['bg_medium'], 
                fg=COLORS['text_dim'], font=("Segoe UI", 9, "bold")).pack(anchor='w', pady=(0, 10))
        
        # Mod buttons
        mod_btn_frame = tk.Frame(mod_frame, bg=COLORS['bg_medium'])
        mod_btn_frame.pack(fill='x')
        
        self._create_mod_button(mod_btn_frame, "VANILLA", "Vanilla").pack(side='left', padx=(0, 5))
        self._create_mod_button(mod_btn_frame, "FORGE", "Forge").pack(side='left', padx=5)
        self._create_mod_button(mod_btn_frame, "FABRIC", "Fabric").pack(side='left', padx=5)
        
        # Keep open checkbox
        self.keep_open_check = self._create_custom_checkbox(settings_frame, 
                                                           "Keep launcher open after launch",
                                                           self.keep_open)
        self.keep_open_check.pack(fill='x', pady=(0, 20))
        
        # Launch button
        self.launch_btn = ModernButton(settings_frame, "LAUNCH GAME", 
                                      self._start_launch_thread, width=250, height=50)
        self.launch_btn.pack(pady=(10, 0))
        
        # Progress bar
        self.progress_canvas = tk.Canvas(settings_frame, height=4, bg=COLORS['bg_light'],
                                        highlightthickness=0)
        self.progress_canvas.pack(fill='x', pady=(20, 5))
        self.progress_fill = None
        
        # Status label
        self.status_lbl = tk.Label(settings_frame, text='Ready to launch', 
                                  bg=COLORS['bg_medium'], fg=COLORS['text_dim'],
                                  font=("Segoe UI", 9), wraplength=400)
        self.status_lbl.pack()

    def draw_cat_logo(self):
        """Draw animated cat logo"""
        self.logo_canvas.delete("all")
        center_x, center_y = 60, 60
        
        # Rotating circle background
        for i in range(8):
            angle = self.animation_angle + i * 45
            x = center_x + 35 * tk.math.cos(tk.math.radians(angle))
            y = center_y + 35 * tk.math.sin(tk.math.radians(angle))
            size = 8 - i * 0.5
            color = f"#{int(100 + i*20):02x}{int(65 + i*10):02x}{int(165 + i*10):02x}"
            self.logo_canvas.create_oval(x-size, y-size, x+size, y+size, 
                                        fill=color, outline="")
        
        # Cat silhouette
        # Head
        self.logo_canvas.create_oval(35, 35, 85, 85, fill=COLORS['accent'], outline="")
        
        # Ears
        self.logo_canvas.create_polygon(40, 45, 35, 25, 50, 35, fill=COLORS['accent'], outline="")
        self.logo_canvas.create_polygon(70, 35, 85, 25, 80, 45, fill=COLORS['accent'], outline="")
        
        # Eyes (glowing effect)
        eye_color = COLORS['success'] if self.is_loading else "#ffffff"
        self.logo_canvas.create_oval(45, 55, 52, 62, fill=eye_color, outline="")
        self.logo_canvas.create_oval(68, 55, 75, 62, fill=eye_color, outline="")
        
        # Nose
        self.logo_canvas.create_polygon(60, 65, 55, 70, 65, 70, fill="#ff69b4", outline="")
        
    def animate_logo(self):
        """Animate the logo rotation"""
        self.animation_angle = (self.animation_angle + 2) % 360
        self.draw_cat_logo()
        self.root.after(50, self.animate_logo)

    def _create_custom_radio(self, parent, text, variable, value, command):
        """Create custom styled radio button"""
        frame = tk.Frame(parent, bg=COLORS['bg_medium'], cursor="hand2")
        frame.pack(fill='x', pady=2)
        
        # Radio indicator
        indicator = tk.Canvas(frame, width=20, height=20, bg=COLORS['bg_medium'],
                             highlightthickness=0)
        indicator.pack(side='left', padx=(0, 10))
        
        def draw_indicator():
            indicator.delete("all")
            # Outer circle
            indicator.create_oval(2, 2, 18, 18, outline=COLORS['border'], width=2)
            # Inner dot if selected
            if variable.get() == value:
                indicator.create_oval(6, 6, 14, 14, fill=COLORS['accent'], outline="")
        
        # Label
        label = tk.Label(frame, text=text, bg=COLORS['bg_medium'], 
                        fg=COLORS['text_primary'], font=("Segoe UI", 10))
        label.pack(side='left')
        
        def on_click(e=None):
            variable.set(value)
            draw_indicator()
            if command:
                command()
            # Update all radio buttons
            for widget in parent.winfo_children():
                if isinstance(widget, tk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Canvas) and child.winfo_width() == 20:
                            widget.event_generate("<<UpdateRadio>>")
        
        frame.bind("<Button-1>", on_click)
        label.bind("<Button-1>", on_click)
        frame.bind("<<UpdateRadio>>", lambda e: draw_indicator())
        
        draw_indicator()
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
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)

    # --- UI Logic & Threading ---
    def _toggle_auth_mode(self):
        if self.auth_mode.get() == 'Offline':
            self.username_lbl.config(text='USERNAME')
            self.password_frame.pack_forget()
        else:
            self.username_lbl.config(text='USERNAME (ANY)')
            self.password_lbl.config(text='PASSWORD (ANY)')
            self.password_lbl.pack(anchor='w', pady=(0, 5))
            self.password_frame.pack(fill='x', pady=(0, 15), after=self.username_frame)
            password_container = self.password_entry.master
            password_container.pack(fill='x')
            self.password_entry.pack(fill='x', padx=10, pady=10)

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
                    self.launch_btn = ModernButton(self.launch_btn.master, "LAUNCH GAME", 
                                                  self._start_launch_thread, width=250, height=50)
                    self.launch_btn.pack(pady=(10, 0))
                    self._update_progress(0)
                    self.is_loading = False
        except queue.Empty:
            pass
        self.root.after(16, self._process_queue)

    def _update_progress(self, value):
        """Update progress bar"""
        if self.progress_fill:
            self.progress_canvas.delete(self.progress_fill)
        if value > 0:
            width = (value / 100) * self.progress_canvas.winfo_width()
            self.progress_fill = self.progress_canvas.create_rectangle(
                0, 0, width, 4, fill=COLORS['accent'], outline=""
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
        self.launch_btn.destroy()
        loading_label = tk.Label(self.launch_btn.master, text="LAUNCHING...", 
                                bg=COLORS['bg_medium'], fg=COLORS['accent'],
                                font=("Segoe UI", 12, "bold"))
        loading_label.pack(pady=(10, 0))
        self.is_loading = True
        self._update_progress(0)
        threading.Thread(target=self._launch_minecraft, daemon=True).start()

    @staticmethod
    def _is_valid_username(name):
        return bool(re.match(r'^[A-Za-z0-9_]{3,16}$', name))

    def _tlauncher_login(self, user, pw):
        """Simulate TLauncher login - accepts any credentials"""
        user_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f'catclient:{user}')).replace('-', '')
        return {
            'accessToken': str(uuid.uuid4()).replace('-', ''),
            'clientToken': str(uuid.uuid4()).replace('-', ''),
            'selectedProfile': {
                'name': user,
                'id': user_uuid
            }
        }

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

        options = {
            'jvmArguments': [
                '-Xms2G', '-Xmx4G', '-XX:+UnlockExperimentalVMOptions', '-XX:+UseG1GC',
                '-XX:G1NewSizePercent=20', '-XX:G1ReservePercent=20', '-XX:MaxGCPauseMillis=50'
            ]
        }

        # Authentication
        if self.auth_mode.get() == 'Offline':
            username = self.username_var.get().strip()
            if not self._is_valid_username(username):
                self._update_status('Username must be 3-16 characters!', final=True, error=True)
                return
            options.update({'username': username, 'uuid': str(uuid.uuid3(uuid.NAMESPACE_DNS, f'Offline:{username}')), 'token': '0'})
            self._update_status(f'Launching as {username} (offline)')
        else:  # Online (Cracked)
            username = self.username_var.get().strip()
            if not username:
                self._update_status('Username is required!', final=True, error=True)
                return
            
            self._update_status(f'Authenticating {username}...')
            
            try:
                data = self._tlauncher_login(username, self.password_var.get())
                profile = data.get('selectedProfile')
                profile_uuid = profile['id'].replace('-', '')
                
                options.update({
                    'username': profile['name'],
                    'uuid': profile_uuid,
                    'token': data.get('accessToken', '0')
                })
                
                self._update_status(f"Authenticated as {profile['name']}")
                
                authlib_path = self._ensure_authlib_present()
                if authlib_path:
                    self._update_status("Enabling skin support...")
                    options['jvmArguments'].extend([
                        f"-javaagent:{authlib_path}",
                        f"-Dauthlibinjector.username={username}",
                        "-Dauthlibinjector.side=client",
                        "-Dauthlibinjector.profileKey=false"
                    ])

            except Exception as e:
                self._update_status(f'Authentication failed: {e}', final=True, error=True)
                return

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
    
            # Launch
            self._update_status(f'Starting Minecraft...')
            minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(target_version_id, self.minecraft_directory, options)
            subprocess.Popen(minecraft_command)
            
            self._update_status('Game launched successfully!', final=not self.keep_open.get())
            if not self.keep_open.get():
                self.root.after(3000, self.root.destroy)

        except Exception as e:
            self._update_status(f'Launch failed: {e}', final=True, error=True)
            messagebox.showerror('Cat Client - Launch Error', f'Failed to launch:\n\n{e}')

    def run(self):
        """Start the launcher"""
        # Center window on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.root.winfo_screenheight() // 2) - (600 // 2)
        self.root.geometry(f"+{x}+{y}")
        
        self.root.mainloop()


def main():
    """Entry point for Cat Client"""
    try:
        # Try to import PIL for better graphics
        try:
            from PIL import Image, ImageTk
        except ImportError:
            print("Note: Install Pillow for better graphics (pip install Pillow)")
        
        launcher = CatClientLauncher()
        launcher.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        messagebox.showerror("Cat Client - Fatal Error", f"Could not start launcher:\n\n{e}")


if __name__ == "__main__":
    # Add tkinter math module for animations
    tk.math = __import__('math')
    main()

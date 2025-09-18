import os
import sys
import subprocess
import platform
import urllib.request
import zipfile
import json
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re
import hashlib
import configparser
import threading
import webbrowser
import socket
import time
from datetime import datetime
from PIL import Image  # Added for skin validation

# Define constants for directories and URLs
NOOB_CLIENT_DIR = os.path.expanduser("~/.noobclient")
VERSIONS_DIR = os.path.join(NOOB_CLIENT_DIR, "versions")
JAVA_DIR = os.path.join(NOOB_CLIENT_DIR, "java")
MODS_DIR = os.path.join(NOOB_CLIENT_DIR, "mods")
CONFIG_DIR = os.path.join(NOOB_CLIENT_DIR, "config")
ASSETS_DIR = os.path.join(NOOB_CLIENT_DIR, "assets")
VERSION_MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
MODRINTH_API = "https://api.modrinth.com/v2"
CURSEFORGE_API = "https://api.curseforge.com/v1"

# TLauncher-inspired theme
THEME = {
    'bg': '#2c2f33',
    'sidebar': '#23272a',
    'accent': '#7289da',
    'text': '#ffffff',
    'text_secondary': '#99aab5',
    'button': '#2c2f33',
    'button_hover': '#36393f',
    'input_bg': '#202225',
    'success': '#43b581',
    'warning': '#f04747',
    'highlight': '#f1c40f'
}

class NoobClientLauncher(tk.Tk):
    def __init__(self):
        """Initialize the TLauncher-like launcher."""
        super().__init__()
        self.title("NOOB CLIENT - TLauncher Edition")
        self.geometry("1280x720")
        self.minsize(1100, 650)
        self.configure(bg=THEME['bg'])
        self.versions = {}
        self.version_categories = {
            "All Versions": [],
            "Release": [],
            "Snapshot": [],
            "Forge": [],
            "Fabric": []
        }
        self.mod_profiles = {"Default": []}
        self.selected_profile = "Default"
        self.authenticated = False
        self.user_data = {"username": "Player", "uuid": None, "access_token": None}
        
        # Load mod profiles from config
        self.load_mod_profiles()
        
        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TCombobox", 
                           fieldbackground=THEME['input_bg'],
                           background=THEME['input_bg'],
                           foreground=THEME['text'],
                           arrowcolor=THEME['text'],
                           borderwidth=1,
                           lightcolor=THEME['accent'],
                           darkcolor=THEME['accent'])
        self.style.configure("Vertical.TScrollbar", 
                           background=THEME['accent'],
                           arrowcolor=THEME['text'],
                           troughcolor=THEME['sidebar'])
        self.style.configure("TCheckbutton", 
                           background=THEME['sidebar'], 
                           foreground=THEME['text'],
                           indicatorcolor=THEME['accent'])
        self.style.map("TCheckbutton", 
                      background=[('active', THEME['button_hover'])],
                      indicatorcolor=[('selected', THEME['success'])])
        
        self.init_ui()
        threading.Thread(target=self.authenticate_user, daemon=True).start()

    def init_ui(self):
        """Set up the TLauncher-inspired UI."""
        main_container = tk.Frame(self, bg=THEME['bg'])
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Sidebar
        sidebar = tk.Frame(main_container, bg=THEME['sidebar'], width=300)
        sidebar.pack(side="left", fill="y", padx=(0, 20))
        sidebar.pack_propagate(False)

        # Logo and title
        logo_frame = tk.Frame(sidebar, bg=THEME['sidebar'])
        logo_frame.pack(fill="x", pady=(20, 30))
        
        tk.Label(logo_frame, text="🎮", font=("Arial", 48), bg=THEME['sidebar'], fg=THEME['accent']).pack()
        tk.Label(logo_frame, text="NOOB CLIENT\nTLAUNCHER EDITION", font=("Arial", 18, "bold"), 
                 bg=THEME['sidebar'], fg=THEME['text'], justify="center").pack()

        # Version selection
        version_frame = tk.LabelFrame(sidebar, text="VERSION SELECTOR", bg=THEME['sidebar'], fg=THEME['text_secondary'],
                                    font=("Arial", 10, "bold"), bd=0, relief="flat")
        version_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.category_combo = ttk.Combobox(version_frame, values=list(self.version_categories.keys()),
                                         state="readonly", font=("Arial", 11))
        self.category_combo.pack(fill="x", pady=(10, 5))
        self.category_combo.set("All Versions")
        self.category_combo.bind("<<ComboboxSelected>>", self.update_version_list)

        self.version_combo = ttk.Combobox(version_frame, state="readonly", font=("Arial", 11))
        self.version_combo.pack(fill="x", pady=5)

        # Mod profile selection
        profile_frame = tk.LabelFrame(sidebar, text="MOD PROFILES", bg=THEME['sidebar'], fg=THEME['text_secondary'],
                                    font=("Arial", 10, "bold"), bd=0, relief="flat")
        profile_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.profile_combo = ttk.Combobox(profile_frame, values=list(self.mod_profiles.keys()),
                                        state="readonly", font=("Arial", 11))
        self.profile_combo.pack(fill="x", pady=(10, 5))
        self.profile_combo.set("Default")
        self.profile_combo.bind("<<ComboboxSelected>>", self.update_mod_profile)

        tk.Button(profile_frame, text="Manage Mods", font=("Arial", 11, "bold"),
                 bg=THEME['button'], fg=THEME['text'], bd=0, padx=20, pady=8,
                 command=self.open_mod_manager).pack(fill="x", pady=5)

        # Settings
        settings_frame = tk.LabelFrame(sidebar, text="GAME SETTINGS", bg=THEME['sidebar'], fg=THEME['text_secondary'],
                                     font=("Arial", 10, "bold"), bd=0, relief="flat")
        settings_frame.pack(fill="x", padx=20, pady=(0, 10))

        # Username
        username_frame = tk.Frame(settings_frame, bg=THEME['sidebar'])
        username_frame.pack(fill="x", pady=(10, 5))
        tk.Label(username_frame, text="USERNAME", font=("Arial", 9, "bold"), 
                bg=THEME['sidebar'], fg=THEME['text_secondary']).pack(anchor="w")
        self.username_input = tk.Entry(username_frame, font=("Arial", 11), bg=THEME['input_bg'],
                                     fg=THEME['text'], insertbackground=THEME['text'], bd=0, relief="solid")
        self.username_input.pack(fill="x", pady=(5, 0))
        self.username_input.insert(0, "Enter Username")
        self.username_input.bind("<FocusIn>", lambda e: self.clear_placeholder(self.username_input, "Enter Username"))

        # RAM
        ram_frame = tk.Frame(settings_frame, bg=THEME['sidebar'])
        ram_frame.pack(fill="x", pady=10)
        tk.Label(ram_frame, text="RAM ALLOCATION", font=("Arial", 9, "bold"),
                bg=THEME['sidebar'], fg=THEME['text_secondary']).pack(side="left")
        self.ram_value_label = tk.Label(ram_frame, text="4GB", font=("Arial", 9),
                                      bg=THEME['sidebar'], fg=THEME['text'])
        self.ram_value_label.pack(side="right")
        self.ram_scale = tk.Scale(ram_frame, from_=1, to=32, orient="horizontal",
                                bg=THEME['sidebar'], fg=THEME['text'],
                                activebackground=THEME['accent'],
                                highlightthickness=0, bd=0,
                                troughcolor=THEME['input_bg'],
                                command=lambda v: self.ram_value_label.config(text=f"{int(float(v))}GB"))
        self.ram_scale.set(4)
        self.ram_scale.pack(fill="x")

        # Buttons
        button_frame = tk.Frame(sidebar, bg=THEME['sidebar'])
        button_frame.pack(fill="x", padx=20, pady=(0, 20))

        def on_enter(e):
            e.widget.configure(bg=THEME['button_hover'])

        def on_leave(e):
            e.widget.configure(bg=THEME['button'])

        def on_accent_enter(e):
            e.widget.configure(bg=THEME['highlight'], fg=THEME['bg'])

        def on_accent_leave(e):
            e.widget.configure(bg=THEME['accent'], fg=THEME['text'])

        skin_button = tk.Button(button_frame, text="🖼️ CHANGE SKIN", font=("Arial", 11, "bold"),
                              bg=THEME['button'], fg=THEME['text'],
                              bd=0, padx=20, pady=8, command=self.select_skin)
        skin_button.pack(fill="x", pady=(0, 5))
        skin_button.bind("<Enter>", on_enter)
        skin_button.bind("<Leave>", on_leave)

        launch_button = tk.Button(button_frame, text="🚀 LAUNCH GAME", font=("Arial", 13, "bold"),
                                bg=THEME['accent'], fg=THEME['text'],
                                bd=0, padx=20, pady=12, command=self.prepare_and_launch)
        launch_button.pack(fill="x")
        launch_button.bind("<Enter>", on_accent_enter)
        launch_button.bind("<Leave>", on_accent_leave)

        # Main content area
        content_area = tk.Frame(main_container, bg=THEME['bg'])
        content_area.pack(side="left", fill="both", expand=True)

        # Welcome message
        tk.Label(content_area, text="Welcome to NOOB CLIENT!", font=("Arial", 24, "bold"),
                bg=THEME['bg'], fg=THEME['text']).pack(pady=20)
        tk.Label(content_area, text="TLauncher Edition - Play Minecraft with ease!", font=("Arial", 14),
                bg=THEME['bg'], fg=THEME['text_secondary']).pack()

        # Server Status
        server_frame = tk.LabelFrame(content_area, text="SERVER STATUS", bg=THEME['bg'], fg=THEME['accent'],
                                   font=("Arial", 12, "bold"), bd=0, relief="flat")
        server_frame.pack(fill="x", pady=(20, 20))
        self.server_status_label = tk.Label(server_frame, text="Checking server status...", 
                                          font=("Arial", 11), bg=THEME['bg'], fg=THEME['text'])
        self.server_status_label.pack(pady=10)
        threading.Thread(target=self.check_server_status, daemon=True).start()

        # Load versions
        self.load_version_manifest()

    def clear_placeholder(self, entry, placeholder):
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            entry.config(fg=THEME['text'])

    def authenticate_user(self):
        """Simulate TLauncher-like offline authentication."""
        def update_auth():
            username = self.username_input.get()
            if username == "Enter Username" or not username:
                username = "Player"
            self.user_data["username"] = username
            self.user_data["uuid"] = self.generate_offline_uuid(username)
            self.user_data["access_token"] = "offline_token_123"
            self.authenticated = True
            self.after(0, lambda: print(f"Authenticated user: {username}"))
        
        threading.Thread(target=update_auth, daemon=True).start()

    def check_server_status(self):
        """Check server status (e.g., Hypixel)."""
        try:
            socket.create_connection(("mc.hypixel.net", 25565), timeout=5)
            self.after(0, lambda: self.server_status_label.config(text="Hypixel: Online", fg=THEME['success']))
        except Exception:
            self.after(0, lambda: self.server_status_label.config(text="Hypixel: Offline", fg=THEME['warning']))
        self.after(60000, self.check_server_status)

    def update_version_list(self, event=None):
        category = self.category_combo.get()
        self.version_combo['values'] = self.version_categories[category]
        if self.version_combo['values']:
            self.version_combo.current(0)

    def update_mod_profile(self, event=None):
        self.selected_profile = self.profile_combo.get()
        print(f"Selected mod profile: {self.selected_profile}")

    def open_mod_manager(self):
        """Open a separate mod manager window."""
        mod_window = tk.Toplevel(self)
        mod_window.title("Mod Manager")
        mod_window.geometry("600x500")
        mod_window.configure(bg=THEME['bg'])

        tk.Label(mod_window, text="MOD MANAGER", font=("Arial", 18, "bold"),
                 bg=THEME['bg'], fg=THEME['text']).pack(pady=20)

        # Mod list
        mods_frame = tk.Frame(mod_window, bg=THEME['bg'])
        mods_frame.pack(fill="both", expand=True, padx=20)

        mods_canvas = tk.Canvas(mods_frame, bg=THEME['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(mods_frame, orient="vertical", command=mods_canvas.yview)
        mods_scrollable_frame = tk.Frame(mods_canvas, bg=THEME['bg'])

        mods_scrollable_frame.bind(
            "<Configure>",
            lambda e: mods_canvas.configure(scrollregion=mods_canvas.bbox("all"))
        )

        mods_canvas.create_window((0, 0), window=mods_scrollable_frame, anchor="nw")
        mods_canvas.configure(yscrollcommand=scrollbar.set)
        mods_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Load installed mods
        self.installed_mods = self.load_installed_mods()
        self.mod_vars = {}
        for mod in self.installed_mods:
            var = tk.BooleanVar(value=mod["enabled"])
            cb = ttk.Checkbutton(mods_scrollable_frame, 
                                text=f"{mod['name']} ({mod['version']}) - {mod['source']}", 
                                variable=var, 
                                command=lambda m=mod['id'], v=var: self.toggle_mod(m, v.get()))
            cb.pack(anchor="w", padx=10, pady=3)
            self.mod_vars[mod['id']] = var

        # Buttons
        button_frame = tk.Frame(mod_window, bg=THEME['bg'])
        button_frame.pack(fill="x", pady=10)
        
        tk.Button(button_frame, text="Add Mod from File", font=("Arial", 11),
                 bg=THEME['button'], fg=THEME['text'],
                 command=self.add_mod_from_file).pack(side="left", padx=5, fill="x", expand=True)
        
        tk.Button(button_frame, text="Browse Modrinth", font=("Arial", 11),
                 bg=THEME['button'], fg=THEME['text'],
                 command=self.browse_modrinth).pack(side="left", padx=5, fill="x", expand=True)

        tk.Button(button_frame, text="Save Profile", font=("Arial", 11),
                 bg=THEME['accent'], fg=THEME['text'],
                 command=self.save_mod_profile).pack(side="left", padx=5, fill="x", expand=True)

    def load_installed_mods(self):
        """Load installed mods from mods directory."""
        os.makedirs(MODS_DIR, exist_ok=True)
        mods = []
        for mod_file in os.listdir(MODS_DIR):
            if mod_file.endswith('.jar'):
                mod_id = mod_file[:-4]
                mods.append({
                    "id": mod_id,
                    "name": mod_id.replace("-", " ").title(),
                    "version": "Unknown",
                    "source": "Local",
                    "enabled": mod_id in self.mod_profiles.get(self.selected_profile, [])
                })
        return mods

    def toggle_mod(self, mod_id, enabled):
        """Toggle a mod's enabled state in the current profile."""
        if enabled:
            if mod_id not in self.mod_profiles[self.selected_profile]:
                self.mod_profiles[self.selected_profile].append(mod_id)
        else:
            if mod_id in self.mod_profiles[self.selected_profile]:
                self.mod_profiles[self.selected_profile].remove(mod_id)
        self.save_mod_profiles()

    def add_mod_from_file(self):
        """Add a mod from a local .jar file."""
        file_path = filedialog.askopenfilename(filetypes=[("JAR Files", "*.jar")])
        if file_path:
            mod_id = os.path.basename(file_path)[:-4]
            dest_path = os.path.join(MODS_DIR, os.path.basename(file_path))
            try:
                shutil.copy(file_path, dest_path)
                self.mod_profiles[self.selected_profile].append(mod_id)
                self.save_mod_profiles()
                messagebox.showinfo("Mod Manager", f"Added mod: {mod_id}")
                self.open_mod_manager()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add mod: {e}")

    def browse_modrinth(self):
        """Browse mods on Modrinth."""
        try:
            with urllib.request.urlopen(f"{MODRINTH_API}/search?query=minecraft&limit=10") as url:
                data = json.loads(url.read().decode())
                if "hits" not in data:
                    raise ValueError("Invalid Modrinth API response")
                mods = data["hits"]
                mod_window = tk.Toplevel(self)
                mod_window.title("Modrinth Mods")
                mod_window.geometry("600x400")
                mod_window.configure(bg=THEME['bg'])

                tk.Label(mod_window, text="MODRINTH MODS", font=("Arial", 18, "bold"),
                        bg=THEME['bg'], fg=THEME['text']).pack(pady=20)

                for mod in mods:
                    tk.Button(mod_window, 
                             text=f"{mod.get('title', 'Unknown')} ({mod.get('latest_version', 'Unknown')})",
                             bg=THEME['button'], fg=THEME['text'],
                             command=lambda m=mod: self.download_modrinth_mod(m.get('slug', ''))).pack(fill="x", padx=20, pady=5)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch Modrinth mods: {e}")

    def download_modrinth_mod(self, mod_slug):
        """Download a mod from Modrinth."""
        if not mod_slug:
            messagebox.showerror("Error", "Invalid mod slug")
            return
        try:
            with urllib.request.urlopen(f"{MODRINTH_API}/project/{mod_slug}/version") as url:
                versions = json.loads(url.read().decode())
                if not versions or not isinstance(versions, list):
                    raise ValueError("No versions found for mod")
                latest_version = versions[0]
                if not latest_version.get("files"):
                    raise ValueError("No files found for mod version")
                file_url = latest_version["files"][0]["url"]
                mod_id = mod_slug
                dest_path = os.path.join(MODS_DIR, f"{mod_id}.jar")
                urllib.request.urlretrieve(file_url, dest_path)
                self.mod_profiles[self.selected_profile].append(mod_id)
                self.save_mod_profiles()
                messagebox.showinfo("Mod Manager", f"Installed mod: {mod_id}")
                self.open_mod_manager()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to download mod {mod_slug}: {e}")

    def save_mod_profiles(self):
        """Save mod profiles to config."""
        os.makedirs(CONFIG_DIR, exist_ok=True)
        config = configparser.ConfigParser()
        for profile, mods in self.mod_profiles.items():
            config[profile] = {"mods": ",".join(mods)}
        try:
            with open(os.path.join(CONFIG_DIR, "mod_profiles.cfg"), "w") as f:
                config.write(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save mod profiles: {e}")

    def load_mod_profiles(self):
        """Load mod profiles from config."""
        config_path = os.path.join(CONFIG_DIR, "mod_profiles.cfg")
        if os.path.exists(config_path):
            config = configparser.ConfigParser()
            try:
                config.read(config_path)
                for profile in config.sections():
                    mods = config[profile].get("mods", "").split(",")
                    self.mod_profiles[profile] = [mod for mod in mods if mod]
            except Exception as e:
                print(f"Warning: Failed to load mod profiles: {e}")

    def load_version_manifest(self):
        """Load Minecraft version manifest."""
        try:
            with urllib.request.urlopen(VERSION_MANIFEST_URL) as url:
                manifest = json.loads(url.read().decode())
                if "versions" not in manifest:
                    raise ValueError("Invalid version manifest")
                for category in self.version_categories:
                    self.version_categories[category] = []
                for v in manifest["versions"]:
                    self.versions[v["id"]] = v["url"]
                    self.version_categories["All Versions"].append(v["id"])
                    if v["type"] == "release":
                        self.version_categories["Release"].append(v["id"])
                    elif v["type"] == "snapshot":
                        self.version_categories["Snapshot"].append(v["id"])
                self.update_version_list()
        except Exception as e:
            print(f"Error loading version manifest: {e}")
            messagebox.showerror("Error", "Failed to load version manifest.")

    def is_java_installed(self, required_version="17"):
        """Check if Java is installed."""
        try:
            result = subprocess.run(["java", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            output = result.stderr
            match = re.search(r'version "(\d+)', output)
            if match:
                return int(match.group(1)) >= int(required_version)
            return False
        except Exception:
            return False

    def install_java_if_needed(self):
        """Install Java if not present."""
        if self.is_java_installed():
            return
        print("Installing OpenJDK 17...")
        system = platform.system()
        java_urls = {
            "Windows": "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.8%2B7/OpenJDK17U-jdk_x64_windows_hotspot_17.0.8_7.zip",
            "Linux": "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.8%2B7/OpenJDK17U-jdk_x64_linux_hotspot_17.0.8_7.tar.gz",
            "Darwin": "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.8%2B7/OpenJDK17U-jdk_x64_mac_hotspot_17.0.8_7.tar.gz"
        }
        if system not in java_urls:
            messagebox.showerror("Error", "Unsupported OS")
            return

        archive_path = os.path.join(JAVA_DIR, "openjdk.zip" if system == "Windows" else "openjdk.tar.gz")
        os.makedirs(JAVA_DIR, exist_ok=True)
        try:
            urllib.request.urlretrieve(java_urls[system], archive_path)
            if system == "Windows":
                with zipfile.ZipFile(archive_path, "r") as zip_ref:
                    zip_ref.extractall(JAVA_DIR)
            else:
                import tarfile
                with tarfile.open(archive_path, "r:gz") as tar_ref:
                    tar_ref.extractall(JAVA_DIR)
            os.remove(archive_path)
            # Find extracted Java directory dynamically
            java_dir = next((d for d in os.listdir(JAVA_DIR) if d.startswith("jdk-")), None)
            if not java_dir:
                raise ValueError("Failed to find extracted Java directory")
            java_bin = os.path.join(JAVA_DIR, java_dir, "bin", "java")
            if system != "Windows":
                os.chmod(java_bin, 0o755)
            print("Java 17 installed.")
        except Exception as e:
            print(f"Failed to install Java: {e}")
            messagebox.showerror("Error", "Failed to install Java 17.")

    def select_skin(self):
        """Select and apply a custom skin with validation."""
        file_path = filedialog.askopenfilename(filetypes=[("PNG Files", "*.png")])
        if file_path:
            try:
                with Image.open(file_path) as img:
                    if img.size not in [(64, 64), (64, 32)]:
                        messagebox.showerror("Error", "Skin must be 64x64 or 64x32 pixels")
                        return
                    if img.format != "PNG":
                        messagebox.showerror("Error", "Skin must be a valid PNG file")
                        return
                skin_dest = os.path.join(NOOB_CLIENT_DIR, "skins")
                os.makedirs(skin_dest, exist_ok=True)
                shutil.copy(file_path, os.path.join(skin_dest, "custom_skin.png"))
                messagebox.showinfo("Skin Manager", "Skin applied!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to apply skin: {e}")

    def verify_file(self, file_path, expected_sha1):
        """Verify file checksum."""
        try:
            with open(file_path, "rb") as f:
                file_hash = hashlib.sha1(f.read()).hexdigest()
            return file_hash == expected_sha1
        except Exception as e:
            print(f"Failed to verify file {file_path}: {e}")
            return False

    def download_version_files(self, version_id, version_url):
        """Download version files."""
        print(f"⬇️ Downloading for {version_id}...")
        version_dir = os.path.join(VERSIONS_DIR, version_id)
        os.makedirs(version_dir, exist_ok=True)

        version_json_path = os.path.join(version_dir, f"{version_id}.json")
        try:
            with urllib.request.urlopen(version_url) as url:
                data = json.loads(url.read().decode())
                if not data.get("downloads"):
                    raise ValueError("Invalid version JSON: missing downloads")
                with open(version_json_path, "w") as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to download JSON: {e}")
            messagebox.showerror("Error", f"Failed to download {version_id} JSON.")
            return False

        try:
            jar_url = data["downloads"]["client"]["url"]
            jar_path = os.path.join(version_dir, f"{version_id}.jar")
            expected_sha1 = data["downloads"]["client"]["sha1"]
            if not os.path.exists(jar_path) or not self.verify_file(jar_path, expected_sha1):
                urllib.request.urlretrieve(jar_url, jar_path)
                if not self.verify_file(jar_path, expected_sha1):
                    print(f"Checksum mismatch: {jar_path}")
                    messagebox.showerror("Error", f"Checksum mismatch for {version_id} JAR.")
                    return False
        except KeyError as e:
            print(f"Missing JAR info: {e}")
            messagebox.showerror("Error", f"Version {version_id} missing JAR info.")
            return False

        current_os = platform.system().lower()
        if current_os == "darwin":
            current_os = "osx"

        libraries_dir = os.path.join(NOOB_CLIENT_DIR, "libraries")
        os.makedirs(libraries_dir, exist_ok=True)
        natives_dir = os.path.join(version_dir, "natives")
        os.makedirs(natives_dir, exist_ok=True)

        for lib in data.get("libraries", []):
            if self.is_library_allowed(lib, current_os):
                if "downloads" in lib and "artifact" in lib["downloads"]:
                    lib_url = lib["downloads"]["artifact"]["url"]
                    lib_path = os.path.join(libraries_dir, lib["downloads"]["artifact"]["path"])
                    os.makedirs(os.path.dirname(lib_path), exist_ok=True)
                    expected_sha1 = lib["downloads"]["artifact"]["sha1"]
                    if not os.path.exists(lib_path) or not self.verify_file(lib_path, expected_sha1):
                        try:
                            urllib.request.urlretrieve(lib_url, lib_path)
                            if not self.verify_file(lib_path, expected_sha1):
                                print(f"Checksum mismatch: {lib_path}")
                                messagebox.showerror("Error", f"Checksum mismatch for {lib.get('name', 'unknown')}.")
                                return False
                        except Exception as e:
                            print(f"Failed to download library {lib.get('name', 'unknown')}: {e}")
                            return False

                if "natives" in lib and current_os in lib["natives"]:
                    classifier = lib["natives"][current_os]
                    if "downloads" in lib and "classifiers" in lib["downloads"] and classifier in lib["downloads"]["classifiers"]:
                        native_url = lib["downloads"]["classifiers"][classifier]["url"]
                        native_path = os.path.join(natives_dir, f"{classifier}.jar")
                        expected_sha1 = lib["downloads"]["classifiers"][classifier]["sha1"]
                        if not os.path.exists(native_path) or not self.verify_file(native_path, expected_sha1):
                            try:
                                urllib.request.urlretrieve(native_url, native_path)
                                if not self.verify_file(native_path, expected_sha1):
                                    print(f"Checksum mismatch: {native_path}")
                                    messagebox.showerror("Error", f"Checksum mismatch for native {lib.get('name', 'unknown')}.")
                                    return False
                            except Exception as e:
                                print(f"Failed to download native {lib.get('name', 'unknown')}: {e}")
                                return False
                        try:
                            with zipfile.ZipFile(native_path, "r") as zip_ref:
                                zip_ref.extractall(natives_dir)
                            os.remove(native_path)
                        except Exception as e:
                            print(f"Failed to extract native {lib.get('name', 'unknown')}: {e}")
                            return False

        print("✅ Download complete!")
        return True

    def modify_options_txt(self, target_fps=60):
        """Modify Minecraft options.txt for performance."""
        options_path = os.path.join(NOOB_CLIENT_DIR, "options.txt")
        options = {
            'maxFps': str(target_fps),
            'enableVsync': 'false',
            'graphicsMode': 'fast',
            'renderDistance': '12',
            'smoothLighting': 'off',
            'fov': '90'
        }
        try:
            if os.path.exists(options_path):
                with open(options_path, "r") as f:
                    for line in f:
                        parts = line.strip().split(":", 1)
                        if len(parts) == 2:
                            options[parts[0]] = parts[1]
        except Exception as e:
            print(f"Warning: Could not read options.txt: {e}")

        try:
            with open(options_path, "w") as f:
                for key, value in options.items():
                    f.write(f"{key}:{value}\n")
            print(f"⚙️ Options applied: FPS={target_fps}, fast graphics")
        except Exception as e:
            print(f"Warning: Could not write options.txt: {e}")

    def is_library_allowed(self, lib, current_os):
        """Check if a library is allowed for the current OS."""
        if "rules" not in lib:
            return True
        allowed = False
        for rule in lib.get("rules", []):
            if rule.get("action") == "allow":
                if "os" not in rule or (isinstance(rule.get("os"), dict) and rule["os"].get("name") == current_os):
                    allowed = True
            elif rule.get("action") == "disallow":
                if "os" in rule and isinstance(rule.get("os"), dict) and rule["os"].get("name") == current_os:
                    allowed = False
        return allowed

    def evaluate_rules(self, rules, current_os):
        """Evaluate library rules."""
        if not rules:
            return True
        allowed = False
        for rule in rules:
            if "features" in rule:
                continue
            if rule.get("action") == "allow":
                if "os" not in rule or (isinstance(rule.get("os"), dict) and rule["os"].get("name") == current_os):
                    allowed = True
            elif rule.get("action") == "disallow":
                if "os" in rule and isinstance(rule.get("os"), dict) and rule["os"].get("name") == current_os:
                    allowed = False
        return allowed

    def generate_offline_uuid(self, username):
        """Generate an offline UUID."""
        offline_prefix = "OfflinePlayer:"
        hash_value = hashlib.md5((offline_prefix + username).encode('utf-8')).hexdigest()
        return f"{hash_value[:8]}-{hash_value[8:12]}-{hash_value[12:16]}-{hash_value[16:20]}-{hash_value[20:32]}"

    def build_launch_command(self, version, username, ram):
        """Build the launch command for Minecraft."""
        version_dir = os.path.join(VERSIONS_DIR, version)
        json_path = os.path.join(version_dir, f"{version}.json")

        try:
            with open(json_path, "r") as f:
                version_data = json.load(f)
        except Exception as e:
            print(f"Failed to read JSON: {e}")
            messagebox.showerror("Error", f"Cannot read {version} JSON.")
            return []

        current_os = platform.system().lower()
        if current_os == "darwin":
            current_os = "osx"

        main_class = version_data.get("mainClass", "net.minecraft.client.main.Main")
        libraries_dir = os.path.join(NOOB_CLIENT_DIR, "libraries")
        natives_dir = os.path.join(version_dir, "natives")
        jar_path = os.path.join(version_dir, f"{version}.jar")
        mods_paths = [os.path.join(MODS_DIR, f) for f in self.mod_profiles.get(self.selected_profile, []) if f.endswith('.jar')]
        classpath = [jar_path] + mods_paths

        for lib in version_data.get("libraries", []):
            if "downloads" in lib and "artifact" in lib["downloads"]:
                lib_path = os.path.join(libraries_dir, lib["downloads"]["artifact"]["path"])
                if os.path.exists(lib_path):
                    classpath.append(lib_path)

        classpath_str = ";".join(classpath) if platform.system() == "Windows" else ":".join(classpath)
        java_dir = next((d for d in os.listdir(JAVA_DIR) if d.startswith("jdk-")), "jdk-17.0.8+7")
        java_path = "java" if self.is_java_installed() else os.path.join(JAVA_DIR, java_dir, "bin", "java.exe" if platform.system() == "Windows" else "java")

        command = [
            java_path,
            f"-Xmx{ram}G",
            "-XX:+UseG1GC",
            "-XX:MaxGCPauseMillis=100",
            f"-Djava.library.path={natives_dir}",
            "-cp",
            classpath_str
        ]

        jvm_args = []
        if "arguments" in version_data and "jvm" in version_data["arguments"]:
            for arg in version_data["arguments"]["jvm"]:
                if isinstance(arg, str):
                    jvm_args.append(arg)
                elif isinstance(arg, dict) and "rules" in arg and "value" in arg:
                    if self.evaluate_rules(arg["rules"], current_os):
                        if isinstance(arg["value"], list):
                            jvm_args.extend(arg["value"])
                        else:
                            jvm_args.append(arg["value"])

        if "forge" in self.selected_profile.lower():
            jvm_args.append("-Dforge.logging.markers=SCAN,REGISTRIES,REGISTRYDUMP")
        if "fabric" in self.selected_profile.lower():
            jvm_args.append("-Dfabric.loader=true")

        command.extend([arg for arg in jvm_args if arg])
        command.append(main_class)

        # Add game arguments
        game_args = [
            "--username",
            username,
            "--uuid",
            self.user_data["uuid"],
            "--accessToken",
            self.user_data["access_token"],
            "--version",
            version,
            "--gameDir",
            NOOB_CLIENT_DIR,
            "--assetsDir",
            ASSETS_DIR,
            "--assetIndex",
            version_data.get("assetIndex", {}).get("id", version)
        ]

        if "arguments" in version_data and "game" in version_data["arguments"]:
            for arg in version_data["arguments"]["game"]:
                if isinstance(arg, str):
                    game_args.append(arg)
                elif isinstance(arg, dict) and "rules" in arg and "value" in arg:
                    if self.evaluate_rules(arg["rules"], current_os):
                        if isinstance(arg["value"], list):
                            game_args.extend(arg["value"])
                        else:
                            game_args.append(arg["value"])

        command.extend(game_args)
        return command

    def prepare_and_launch(self):
        """Prepare and launch the game."""
        if not self.authenticated:
            messagebox.showerror("Error", "User not authenticated")
            return

        version = self.version_combo.get()
        if not version:
            messagebox.showerror("Error", "No version selected")
            return

        ram = int(self.ram_scale.get())
        username = self.user_data["username"]

        self.install_java_if_needed()
        if not self.download_version_files(version, self.versions.get(version)):
            return

        self.modify_options_txt()
        command = self.build_launch_command(version, username, ram)
        if not command:
            return

        try:
            subprocess.run(command, cwd=NOOB_CLIENT_DIR)
            print(f"🚀 Launched Minecraft {version}")
        except Exception as e:
            print(f"Failed to launch: {e}")
            messagebox.showerror("Error", f"Failed to launch Minecraft: {e}")

if __name__ == "__main__":
    app = NoobClientLauncher()
    app.mainloop()

import tarfile
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as messagebox
import urllib.request
import json
import subprocess
import platform
import os
import hashlib
import uuid
import zipfile
import tempfile
import shutil
import re
from urllib.error import URLError
import threading
import logging

# --- Constants ---
VERSION_MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
FORGE_VERSIONS_URL = "https://files.minecraftforge.net/net/minecraftforge/forge/promotions_slim.json"
OPTIFINE_URL = "https://optifine.net/downloads"  # Placeholder; scraping needed
JAVA_DOWNLOAD_URLS = {
    "Windows": "https://api.adoptium.net/v3/binary/latest/17/ga/windows/x64/jdk/hotspot/normal/eclipse",
    "Linux": "https://api.adoptium.net/v3/binary/latest/17/ga/linux/x64/jdk/hotspot/normal/eclipse",
    "Darwin": "https://api.adoptium.net/v3/binary/latest/17/ga/macos/x64/jdk/hotspot/normal/eclipse"
}

# Base directory setup
BASE_DIR = os.path.join(os.getenv('APPDATA', os.path.expanduser('~')), '.catclient') if platform.system() == "Windows" else os.path.join(os.path.expanduser('~'), '.catclient')
MINECRAFT_DIR = os.path.join(BASE_DIR, 'minecraft')
VERSIONS_DIR = os.path.join(MINECRAFT_DIR, 'versions')
MODS_DIR = os.path.join(MINECRAFT_DIR, 'mods')
LIBRARIES_DIR = os.path.join(MINECRAFT_DIR, 'libraries')
ASSETS_DIR = os.path.join(MINECRAFT_DIR, 'assets')
NATIVES_DIR = os.path.join(MINECRAFT_DIR, 'natives')
JAVA_DIR = os.path.join(BASE_DIR, 'java')
LOG_FILE = os.path.join(BASE_DIR, 'launcher.log')

for directory in [MINECRAFT_DIR, VERSIONS_DIR, MODS_DIR, LIBRARIES_DIR, ASSETS_DIR, NATIVES_DIR, JAVA_DIR]:
    os.makedirs(directory, exist_ok=True)

# Logging setup
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Theme ---
THEME = {
    "bg": "#1a1a1a",
    "sidebar": "#252526",
    "accent": "#00b4d8",
    "text": "#ffffff",
    "text_secondary": "#b0b0b0",
    "input_bg": "#333333",
    "button": "#404040",
    "button_hover": "#505050"
}

class CatClientApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CatClient Launcher")
        self.geometry("900x600")
        self.minsize(800, 600)
        self.configure(bg=THEME["bg"])
        self.java_path = self.detect_java()
        self.java_version = self.get_java_version()
        self.status_label = tk.Label(self, text="Initializing...", bg=THEME["bg"], fg=THEME["text_secondary"])

        # Asynchronous initialization
        threading.Thread(target=self.initialize_components, daemon=True).start()

        # UI setup
        self.setup_ui()

    def initialize_components(self):
        """Initialize Java, Forge, and OptiFine asynchronously."""
        if not self.java_path:
            self.install_java()
        self.install_latest_forge()
        self.install_latest_optifine()
        self.status_label.config(text="Ready")

    def setup_ui(self):
        """Setup the UI components."""
        sidebar = tk.Frame(self, bg=THEME["sidebar"], width=200)
        sidebar.pack(side="left", fill="y")
        sidebar_title = tk.Label(sidebar, text="CatClient", bg=THEME["sidebar"], fg=THEME["accent"], font=("Arial", 14, "bold"))
        sidebar_title.pack(pady=20)
        separator = tk.Frame(sidebar, height=2, bg=THEME["accent"])
        separator.pack(fill="x", pady=10)

        def on_enter(e): e.widget['background'] = THEME["button_hover"]
        def on_leave(e): e.widget['background'] = THEME["button"]

        buttons = [("Home", lambda: self.show_section("home")), ("Versions", lambda: self.show_section("versions")),
                   ("Mods", lambda: self.show_section("mods")), ("Settings", lambda: self.show_section("settings"))]
        for text, command in buttons:
            btn = tk.Button(sidebar, text=text, bg=THEME["button"], fg=THEME["text"], relief="flat", command=command)
            btn.pack(fill="x", padx=10, pady=5)
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)

        main_content = tk.Frame(self, bg=THEME["bg"])
        main_content.pack(side="right", fill="both", expand=True)

        self.home_frame = tk.Frame(main_content, bg=THEME["bg"])
        self.versions_frame = tk.Frame(main_content, bg=THEME["bg"])
        self.mods_frame = tk.Frame(main_content, bg=THEME["bg"])
        self.settings_frame = tk.Frame(main_content, bg=THEME["bg"])

        self.setup_home_section()
        self.setup_versions_section()
        self.setup_mods_section()
        self.setup_settings_section()
        self.show_section("home")

    def detect_java(self):
        """Enhanced Java detection."""
        java_path = shutil.which("java")
        if not java_path:
            common_paths = {
                "Windows": [r"C:\Program Files\Java", r"C:\Program Files (x86)\Java"],
                "Linux": ["/usr/lib/jvm", "/usr/java"],
                "Darwin": ["/Library/Java/JavaVirtualMachines", "/System/Library/Frameworks/JavaVM.framework/Versions"]
            }
            system = platform.system()
            executable = "java.exe" if system == "Windows" else "java"
            for base_path in common_paths.get(system, []) + [JAVA_DIR]:
                if os.path.exists(base_path):
                    for root, _, files in os.walk(base_path):
                        if executable in files:
                            java_path = os.path.join(root, executable)
                            break
                if java_path:
                    break
        if java_path:
            logging.info(f"Java detected at: {java_path}")
        return java_path

    def install_java(self):
        """Install Java using Adoptium API."""
        self.status_label.config(text="Installing Java 17...")
        system = platform.system()
        if system not in JAVA_DOWNLOAD_URLS:
            messagebox.showerror("Error", f"Unsupported platform: {system}")
            return
        try:
            java_url = JAVA_DOWNLOAD_URLS[system]
            temp_dir = tempfile.mkdtemp()
            java_archive = os.path.join(temp_dir, "java_archive.zip" if system == "Windows" else "java_archive.tar.gz")
            if self.download_file(java_url, java_archive):
                if system == "Windows":
                    with zipfile.ZipFile(java_archive, 'r') as zip_ref:
                        zip_ref.extractall(JAVA_DIR)
                else:
                    with tarfile.open(java_archive, 'r:gz') as tar_ref:
                        tar_ref.extractall(JAVA_DIR)
                shutil.rmtree(temp_dir)
                self.java_path = self.detect_java()
                self.java_version = self.get_java_version()
                if self.java_path:
                    messagebox.showinfo("Success", "Java 17 installed")
                else:
                    raise FileNotFoundError("Java executable not found after installation")
        except Exception as e:
            logging.error(f"Java installation failed: {e}")
            messagebox.showerror("Error", f"Failed to install Java: {e}")
        finally:
            self.status_label.config(text="Ready")

    def get_java_version(self):
        """Get Java version with better parsing."""
        if not self.java_path:
            return None
        try:
            result = subprocess.run([self.java_path, "-version"], capture_output=True, text=True, check=True)
            version_line = result.stderr.splitlines()[0]
            match = re.search(r'version "(\d+\.\d+|\d+)', version_line)
            if match:
                version = match.group(1)
                major = int(version.split('.')[0])
                logging.info(f"Java version detected: {major}")
                return major
            return None
        except Exception as e:
            logging.error(f"Failed to get Java version: {e}")
            return None

    def check_java_compatibility(self, version):
        """Check Java compatibility with detailed logging."""
        version_json_path = os.path.join(VERSIONS_DIR, version, f"{version}.json")
        try:
            with open(version_json_path) as f:
                version_json = json.load(f)
            required_java = version_json.get("javaVersion", {}).get("majorVersion", 8)
            if not self.java_version or self.java_version < required_java:
                logging.warning(f"Java {self.java_version} incompatible with required {required_java} for {version}")
                return False, required_java
            return True, required_java
        except Exception as e:
            logging.error(f"Java compatibility check failed: {e}")
            return True, 8

    def install_latest_forge(self):
        """Install latest Forge using official API."""
        self.status_label.config(text="Installing latest Forge...")
        try:
            with urllib.request.urlopen(FORGE_VERSIONS_URL) as response:
                forge_data = json.loads(response.read().decode())
                latest_forge_key = max(forge_data["promotions"].items(), key=lambda x: x[0])[0]  # Using key as date not available
                mc_version = forge_data["promotions"][latest_forge_key]["mcversion"]
                forge_version = latest_forge_key
                forge_url = f"https://files.minecraftforge.net/maven/net/minecraftforge/forge/{mc_version}-{forge_version}/forge-{mc_version}-{forge_version}-installer.jar"
            temp_dir = tempfile.mkdtemp()
            installer_path = os.path.join(temp_dir, "forge-installer.jar")
            if self.download_file(forge_url, installer_path) and self.java_path:
                subprocess.run([self.java_path, "-jar", installer_path, "--installClient", MINECRAFT_DIR], check=True)
                shutil.rmtree(temp_dir)
                self.update_version_list()
                self.update_version_listbox()
                messagebox.showinfo("Success", f"Forge {forge_version} installed")
        except Exception as e:
            logging.error(f"Forge installation failed: {e}")
            messagebox.showerror("Error", f"Failed to install Forge: {e}")
        finally:
            self.status_label.config(text="Ready")

    def install_latest_optifine(self):
        """Install latest OptiFine with placeholder logic (requires scraping)."""
        self.status_label.config(text="Installing latest OptiFine...")
        try:
            with urllib.request.urlopen(VERSION_MANIFEST_URL) as response:
                manifest = json.loads(response.read().decode())
                latest_version = manifest["latest"]["release"]
            # Placeholder: Replace with actual OptiFine scraping or API
            optifine_url = f"https://optifine.net/download?f=OptiFine_{latest_version}_HD_U_I6.jar"  # Fictional URL
            optifine_path = os.path.join(MODS_DIR, f"OptiFine_{latest_version}_HD_U_I6.jar")
            if self.download_file(optifine_url, optifine_path):
                self.update_mods_list()
                messagebox.showinfo("Success", f"OptiFine for {latest_version} installed")
            else:
                raise Exception("Download failed")
        except Exception as e:
            logging.error(f"OptiFine installation failed: {e}")
            messagebox.showerror("Error", f"Failed to install OptiFine: {e}. Web scraping required for accurate URL.")
        finally:
            self.status_label.config(text="Ready")

    def setup_home_section(self):
        """Setup home section with validation."""
        version_label = tk.Label(self.home_frame, text="Select Version:", bg=THEME["bg"], fg=THEME["text"])
        version_label.pack(pady=10)
        self.version_var = tk.StringVar()
        self.version_combobox = ttk.Combobox(self.home_frame, textvariable=self.version_var, state="readonly")
        self.version_combobox.pack(pady=10)
        self.update_version_list()

        username_label = tk.Label(self.home_frame, text="Username:", bg=THEME["bg"], fg=THEME["text"])
        username_label.pack(pady=5)
        self.username_var = tk.StringVar(value="Player")
        username_entry = tk.Entry(self.home_frame, textvariable=self.username_var, bg=THEME["input_bg"], fg=THEME["text"])
        username_entry.pack(pady=5)

        forge_var = tk.BooleanVar()
        forge_check = tk.Checkbutton(self.home_frame, text="Use Forge", variable=forge_var, bg=THEME["bg"], fg=THEME["text"], selectcolor=THEME["input_bg"])
        forge_check.pack(pady=5)

        play_button = tk.Button(self.home_frame, text="Play", bg=THEME["accent"], fg=THEME["text"], font=("Arial", 16, "bold"), command=lambda: threading.Thread(target=self.launch_game, args=(forge_var.get(),)).start())
        play_button.pack(pady=20)

        self.status_label.pack(pady=10)

    def setup_versions_section(self):
        """Setup versions section."""
        versions_list_frame = tk.Frame(self.versions_frame, bg=THEME["bg"])
        versions_list_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.versions_listbox = tk.Listbox(versions_list_frame, bg=THEME["input_bg"], fg=THEME["text"], selectbackground=THEME["accent"])
        self.versions_listbox.pack(side="left", fill="both", expand=True)
        scrollbar = tk.Scrollbar(versions_list_frame, orient="vertical", command=self.versions_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.versions_listbox.config(yscrollcommand=scrollbar.set)
        self.update_version_listbox()

        install_button = tk.Button(self.versions_frame, text="Install Vanilla Version", bg=THEME["button"], fg=THEME["text"], command=lambda: threading.Thread(target=self.install_vanilla_version).start())
        install_button.pack(pady=5)
        install_forge_button = tk.Button(self.versions_frame, text="Install Forge Version", bg=THEME["button"], fg=THEME["text"], command=lambda: threading.Thread(target=self.install_forge_version).start())
        install_forge_button.pack(pady=5)

    def setup_mods_section(self):
        """Setup mods section."""
        mods_list_frame = tk.Frame(self.mods_frame, bg=THEME["bg"])
        mods_list_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.mods_listbox = tk.Listbox(mods_list_frame, bg=THEME["input_bg"], fg=THEME["text"], selectbackground=THEME["accent"])
        self.mods_listbox.pack(side="left", fill="both", expand=True)
        scrollbar = tk.Scrollbar(mods_list_frame, orient="vertical", command=self.mods_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.mods_listbox.config(yscrollcommand=scrollbar.set)
        self.update_mods_list()

        add_mod_button = tk.Button(self.mods_frame, text="Add Mod", bg=THEME["button"], fg=THEME["text"], command=self.add_mod)
        add_mod_button.pack(pady=5)
        remove_mod_button = tk.Button(self.mods_frame, text="Remove Selected Mod", bg=THEME["button"], fg=THEME["text"], command=self.remove_mod)
        remove_mod_button.pack(pady=5)

    def setup_settings_section(self):
        """Setup settings section with validation."""
        settings_label = tk.Label(self.settings_frame, text="Launcher Settings", bg=THEME["bg"], fg=THEME["text"], font=("Arial", 14, "bold"))
        settings_label.pack(pady=20)
        ram_label = tk.Label(self.settings_frame, text="Max RAM (GB):", bg=THEME["bg"], fg=THEME["text"])
        ram_label.pack(pady=5)
        self.ram_var = tk.StringVar(value="4")
        ram_entry = tk.Entry(self.settings_frame, textvariable=self.ram_var, bg=THEME["input_bg"], fg=THEME["text"], width=10)
        ram_entry.pack(pady=5)

        java_label = tk.Label(self.settings_frame, text="Java Path:", bg=THEME["bg"], fg=THEME["text"])
        java_label.pack(pady=5)
        self.java_var = tk.StringVar(value=self.java_path or "")
        java_entry = tk.Entry(self.settings_frame, textvariable=self.java_var, bg=THEME["input_bg"], fg=THEME["text"])
        java_entry.pack(pady=5)

        browse_button = tk.Button(self.settings_frame, text="Browse Java", bg=THEME["button"], fg=THEME["text"], command=self.browse_java)
        browse_button.pack(pady=5)
        save_button = tk.Button(self.settings_frame, text="Save Settings", bg=THEME["button"], fg=THEME["text"], command=self.save_settings)
        save_button.pack(pady=10)

    def browse_java(self):
        """Browse for Java with validation."""
        from tkinter import filedialog
        executable = "java.exe" if platform.system() == "Windows" else "java"
        java_path = filedialog.askopenfilename(filetypes=[("Java executable", executable)])
        if java_path and os.path.exists(java_path):
            temp_version = self.get_java_version_check(java_path)
            if temp_version and temp_version >= 8:
                self.java_var.set(java_path)
                self.java_path = java_path
                self.java_version = temp_version
                messagebox.showinfo("Success", f"Java path updated to version {temp_version}")
            else:
                messagebox.showerror("Error", "Selected Java version is invalid or too old")
        else:
            messagebox.showerror("Error", "Invalid Java path selected")

    def get_java_version_check(self, path):
        """Helper to check Java version for a given path."""
        try:
            result = subprocess.run([path, "-version"], capture_output=True, text=True, check=True)
            version_line = result.stderr.splitlines()[0]
            match = re.search(r'version "(\d+\.\d+|\d+)', version_line)
            if match:
                return int(match.group(1).split('.')[0])
            return None
        except Exception:
            return None

    def update_version_list(self):
        """Update version combobox with installed versions."""
        installed_versions = self.get_installed_versions()
        self.version_combobox['values'] = installed_versions
        if installed_versions:
            self.version_combobox.set(installed_versions[0])

    def update_version_listbox(self):
        """Update versions listbox."""
        self.versions_listbox.delete(0, tk.END)
        for version in self.get_installed_versions():
            self.versions_listbox.insert(tk.END, version)

    def update_mods_list(self):
        """Update mods listbox."""
        self.mods_listbox.delete(0, tk.END)
        for mod in os.listdir(MODS_DIR):
            if mod.endswith(".jar"):
                self.mods_listbox.insert(tk.END, mod)

    def get_installed_versions(self):
        """Get installed versions with validation."""
        versions = []
        for version in os.listdir(VERSIONS_DIR):
            version_dir = os.path.join(VERSIONS_DIR, version)
            json_path = os.path.join(version_dir, f"{version}.json")
            jar_path = os.path.join(version_dir, f"{version}.jar")
            if os.path.isdir(version_dir) and os.path.exists(json_path) and os.path.exists(jar_path):
                versions.append(version)
        return sorted(versions)

    def show_section(self, section):
        """Show specified section."""
        for frame in [self.home_frame, self.versions_frame, self.mods_frame, self.settings_frame]:
            frame.pack_forget()
        {"home": self.home_frame, "versions": self.versions_frame, "mods": self.mods_frame, "settings": self.settings_frame}[section].pack(fill="both", expand=True)

    def download_file(self, url, path, expected_sha1=None):
        """Download file with checksum verification and progress."""
        self.status_label.config(text=f"Downloading {os.path.basename(path)}...")
        try:
            with urllib.request.urlopen(url) as response:
                data = response.read()
                if expected_sha1:
                    sha1 = hashlib.sha1(data).hexdigest()
                    if sha1 != expected_sha1:
                        raise ValueError(f"SHA1 mismatch: expected {expected_sha1}, got {sha1}")
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'wb') as f:
                    f.write(data)
            logging.info(f"Downloaded {url} to {path}")
            return True
        except Exception as e:
            logging.error(f"Download failed for {url}: {e}")
            return False
        finally:
            self.status_label.config(text="Ready")

    def install_vanilla_version(self):
        """Install vanilla version asynchronously."""
        version_window = tk.Toplevel(self)
        version_window.title("Install Version")
        version_window.geometry("300x200")
        version_window.configure(bg=THEME["bg"])

        tk.Label(version_window, text="Select Version:", bg=THEME["bg"], fg=THEME["text"]).pack(pady=10)
        version_var = tk.StringVar()
        version_combobox = ttk.Combobox(version_window, textvariable=version_var, state="readonly")
        version_combobox.pack(pady=10)

        try:
            with urllib.request.urlopen(VERSION_MANIFEST_URL) as response:
                manifest = json.loads(response.read().decode())
                versions = [v["id"] for v in manifest["versions"]]
                version_combobox['values'] = versions
                version_combobox.set(versions[0])
        except URLError as e:
            logging.error(f"Failed to fetch version manifest: {e}")
            messagebox.showerror("Error", "Failed to fetch version manifest")
            version_window.destroy()
            return

        def do_install():
            version = version_var.get()
            self.status_label.config(text=f"Installing {version}...")
            try:
                with urllib.request.urlopen(VERSION_MANIFEST_URL) as response:
                    manifest = json.loads(response.read().decode())
                    version_data = next(v for v in manifest["versions"] if v["id"] == version)
                    version_url = version_data["url"]
            except Exception as e:
                logging.error(f"Failed to get version data: {e}")
                messagebox.showerror("Error", "Failed to get version data")
                return
                with urllib.request.urlopen(version_url) as response:
                    version_json = json.loads(response.read().decode())

                version_dir = os.path.join(VERSIONS_DIR, version)
                os.makedirs(version_dir, exist_ok=True)

                client_url = version_json["downloads"]["client"]["url"]
                client_sha1 = version_json["downloads"]["client"]["sha1"]
                client_path = os.path.join(version_dir, f"{version}.jar")
                if not self.download_file(client_url, client_path, client_sha1):
                    raise Exception("Client download failed")

                with open(os.path.join(version_dir, f"{version}.json"), 'w') as f:
                    json.dump(version_json, f)

                for lib in version_json.get("libraries", []):
                    if "downloads" in lib and "artifact" in lib["downloads"]:
                        lib_url = lib["downloads"]["artifact"]["url"]
                        lib_sha1 = lib["downloads"]["artifact"]["sha1"]
                        lib_path = os.path.join(LIBRARIES_DIR, lib["downloads"]["artifact"]["path"])
                        os.makedirs(os.path.dirname(lib_path), exist_ok=True)
                        if not os.path.exists(lib_path) or not self.verify_sha1(lib_path, lib_sha1):
                            if not self.download_file(lib_url, lib_path, lib_sha1):
                                raise Exception(f"Library download failed: {lib_path}")

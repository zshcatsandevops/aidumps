import os
import json
import shutil
import subprocess
import threading
import hashlib
import platform
import zipfile
from pathlib import Path
from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import webbrowser
from PIL import Image, ImageTk
from queue import Queue

# --- CONFIGURATION ---
APP_TITLE = "Cat-Launcher (TLauncher Clone) 2.0"
VERSIONS = [
    "1.21",
    "1.20.6",
    "1.19.4",
    "1.18.2",
    "1.12.2",
    "latest-release",
    "latest-snapshot",
]

# --- PATHS ---
BASE_DIR = Path.home() / ".catlauncher"
PROFILE_FILE = BASE_DIR / "profiles.json"
MINECRAFT_DIR = BASE_DIR / "minecraft"
VERSIONS_DIR = MINECRAFT_DIR / "versions"
LIBS_DIR = MINECRAFT_DIR / "libraries"
ASSETS_DIR = MINECRAFT_DIR / "assets"
MODS_DIR = MINECRAFT_DIR / "mods"
SKINS_DIR = BASE_DIR / "skins"
for d in (VERSIONS_DIR, LIBS_DIR, ASSETS_DIR / "objects", ASSETS_DIR / "indexes", MODS_DIR, SKINS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# --- API ENDPOINTS ---
VERSION_MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
RESOURCES_URL = "https://resources.download.minecraft.net"
TLAUNCHER_AUTH_URL = "https://auth.tlauncher.org/auth/login"
TLAUNCHER_SKIN_URL = "http://tlauncher.org/repo/skins/files/{username}.png"

# --- NETWORKING & FILE HANDLING ---
def http_get_json(url: str, timeout=15) -> dict:
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        raise IOError(f"Failed to fetch JSON from {url}: {e}")

def download_file(url: str, dest: Path, expected_sha1=None, progress_callback=None, retries=3):
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    for attempt in range(1, retries + 1):
        h = hashlib.sha1()
        try:
            with requests.get(url, stream=True, timeout=15) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                downloaded = 0
                with tmp.open("wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        h.update(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            progress_callback(downloaded / total_size * 100)
            if expected_sha1 and h.hexdigest().lower() != expected_sha1.lower():
                tmp.unlink(missing_ok=True)
                if attempt < retries:
                    continue
                raise IOError(f"Checksum mismatch for {dest.name}. Expected {expected_sha1}, got {h.hexdigest()}")
            shutil.move(tmp, dest)
            if progress_callback:
                progress_callback(100)
            return dest
        except Exception as e:
            if tmp.exists():
                tmp.unlink(missing_ok=True)
            if attempt < retries:
                continue
            raise IOError(f"Failed to download {url} after {retries} attempts: {e}")

@dataclass
class DownloadTask:
    url: str
    dest: Path
    name: str
    sha1: str = None

class DownloadManager:
    def __init__(self, parent_app: 'Launcher'):
        self.app = parent_app
        self.queue = Queue()
        self.active = False
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="No downloads active")
        self.current_task = None

    def add_download(self, task: DownloadTask):
        self.queue.put(task)
        self.status_var.set(f"Queued: {task.name}")
        if not self.active:
            self.active = True
            threading.Thread(target=self.process_queue, daemon=True).start()

    def process_queue(self):
        while not self.queue.empty():
            task = self.queue.get()
            self.current_task = task
            self.status_var.set(f"Downloading: {task.name}")
            self.progress_var.set(0)
            try:
                download_file(
                    task.url,
                    task.dest,
                    task.sha1,
                    lambda p: self.app.after(0, lambda: self.progress_var.set(p))
                )
                self.status_var.set(f"Completed: {task.name}")
            except Exception as e:
                self.status_var.set(f"Failed: {task.name} ({e})")
                self.app.after(0, lambda: messagebox.showerror(APP_TITLE, f"Download failed: {task.name}\n{e}"))
            finally:
                self.queue.task_done()
                self.current_task = None
            self.active = False
        self.status_var.set("No downloads active")
        self.progress_var.set(0)

    def wait_for_completion(self):
        self.queue.join()
        while self.active:
            if self.queue.empty():
                self.active = False
                break

# --- CORE LOGIC ---
class MinecraftManager:
    def __init__(self, download_manager):
        self.dm = download_manager
        self.os_name = {'windows': 'windows', 'linux': 'linux', 'darwin': 'osx'}.get(platform.system().lower())
        self.arch = "x64" if platform.machine().endswith('64') else "x86"

    def get_version_meta(self, version_id):
        manifest = http_get_json(VERSION_MANIFEST_URL)
        if version_id in ("latest-release", "latest-snapshot"):
            key = "release" if version_id == "latest-release" else "snapshot"
            version_id = manifest["latest"][key]

        info = next((v for v in manifest["versions"] if v["id"] == version_id), None)
        if not info:
            raise RuntimeError(f"Version '{version_id}' not found in manifest.")

        version_json_path = VERSIONS_DIR / f"{version_id}/{version_id}.json"
        if not version_json_path.exists():
            download_file(info["url"], version_json_path, info['sha1'])

        return json.loads(version_json_path.read_text("utf-8"))

    def check_rules(self, rules: list) -> bool:
        if not rules:
            return True
        allow = False
        for rule in rules:
            applies = True
            if 'os' in rule:
                if 'name' in rule['os'] and rule['os']['name'] != self.os_name:
                    applies = False
                if 'arch' in rule['os'] and rule['os']['arch'] != self.arch:
                    applies = False
            if applies:
                allow = rule['action'] == 'allow'
        return allow

    def prepare_version(self, version_id: str, status_callback):
        status_callback("Fetching version metadata...")
        meta = self.get_version_meta(version_id)
        actual_version_id = meta['id']

        # 1. Download Client JAR
        client_info = meta['downloads']['client']
        client_jar = VERSIONS_DIR / f"{actual_version_id}/{actual_version_id}.jar"
        if not client_jar.exists() or hashlib.sha1(client_jar.read_bytes()).hexdigest() != client_info['sha1']:
            status_callback(f"Queuing client JAR for {actual_version_id}...")
            self.dm.add_download(DownloadTask(client_info['url'], client_jar, f"Client {actual_version_id}", client_info['sha1']))

        # 2. Download Assets
        status_callback("Verifying assets...")
        asset_index_info = meta['assetIndex']
        index_path = ASSETS_DIR / "indexes" / f"{asset_index_info['id']}.json"
        if not index_path.exists():
            self.dm.add_download(DownloadTask(asset_index_info['url'], index_path, f"Asset Index {asset_index_info['id']}", asset_index_info['sha1']))

        assets = json.loads(index_path.read_text('utf-8'))['objects'] if index_path.exists() else {}
        for name, obj in assets.items():
            h = obj['hash']
            asset_path = ASSETS_DIR / "objects" / h[:2] / h
            if not asset_path.exists():
                url = f"{RESOURCES_URL}/{h[:2]}/{h}"
                self.dm.add_download(DownloadTask(url, asset_path, f"Asset {name}", h))
        status_callback("Queuing assets (if any)...")
        self.dm.wait_for_completion()

        # 3. Download Libraries and Natives
        status_callback("Verifying libraries and natives...")
        classpath = {client_jar}
        natives_dir = VERSIONS_DIR / actual_version_id / "natives"
        natives_dir.mkdir(exist_ok=True)

        for lib in meta['libraries']:
            if not self.check_rules(lib.get('rules')):
                continue

            artifact = None
            if 'natives' in lib and self.os_name in lib['natives']:
                classifier = lib['natives'][self.os_name].replace('${arch}', self.arch)
                artifact = lib['downloads']['classifiers'].get(classifier)
            elif 'artifact' in lib['downloads']:
                artifact = lib['downloads']['artifact']

            if not artifact:
                continue

            lib_path = LIBS_DIR / artifact['path']
            if not lib_path.exists() or hashlib.sha1(lib_path.read_bytes()).hexdigest() != artifact['sha1']:
                self.dm.add_download(DownloadTask(artifact['url'], lib_path, lib['name'], artifact['sha1']))

            if 'natives' in lib and artifact:
                self.dm.wait_for_completion()
                with zipfile.ZipFile(lib_path, 'r') as z:
                    for info in z.infolist():
                        if info.filename.startswith('META-INF/'):
                            continue
                        z.extract(info, natives_dir)
            else:
                classpath.add(lib_path)

        status_callback("Queuing libraries (if any)...")
        self.dm.wait_for_completion()

        # 4. Construct Launch Arguments
        status_callback("Constructing launch arguments...")
        main_class = meta['mainClass']
        if 'arguments' in meta:
            jvm_args = [arg for arg in meta['arguments']['jvm'] if isinstance(arg, str)]
            game_args = [arg for arg in meta['arguments']['game'] if isinstance(arg, str)]
        else:
            jvm_args = [
                '-Djava.library.path=${natives_directory}',
                '-cp', '${classpath}'
            ]
            game_args = meta['minecraftArguments'].split(' ')

        cp_separator = ';' if self.os_name == 'windows' else ':'
        classpath_str = cp_separator.join(map(str, classpath))

        replacements = {
            'natives_directory': str(natives_dir),
            'launcher_name': APP_TITLE,
            'launcher_version': '2.0',
            'classpath': classpath_str,
            'version_name': actual_version_id,
            'assets_root': str(ASSETS_DIR),
            'assets_index_name': asset_index_info['id'],
            'game_directory': str(MINECRAFT_DIR),
        }

        final_jvm_args = [arg.format(**replacements) for arg in jvm_args]
        final_game_args = [arg.format(**replacements) for arg in game_args]

        return main_class, final_jvm_args, final_game_args

@dataclass
class CatClient:
    username: str
    password: str
    version_id: str
    use_auth: bool = True
    token: str = None
    uuid: str = None

    def authenticate(self) -> bool:
        if not self.use_auth:
            self.token = hashlib.md5(self.username.encode()).hexdigest()
            self.uuid = hashlib.sha1(self.username.encode()).hexdigest()
            return True
        try:
            payload = {
                "username": self.username,
                "password": self.password,
                "clientToken": hashlib.md5(b"cat-launcher-token").hexdigest()
            }
            headers = {"User-Agent": "TLauncher/2.91", "Content-Type": "application/json"}
            resp = requests.post(TLAUNCHER_AUTH_URL, json=payload, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            if "error" in data:
                raise RuntimeError(f"Auth error: {data.get('errorMessage', 'Unknown error')}")

            self.token = data.get("accessToken")
            self.uuid = data.get("selectedProfile", {}).get("id")

            if not self.token or not self.uuid:
                raise RuntimeError("Token or UUID not found in auth response.")

            return True
        except requests.RequestException as e:
            messagebox.showerror(APP_TITLE, f"Authentication failed (Network): {e}")
            return False
        except Exception as e:
            messagebox.showerror(APP_TITLE, f"Authentication failed: {e}")
            return False

    def launch(self, main_class, jvm_args, game_args, java_path, ram_mb, server=None, port=None):
        auth_replacements = {
            'auth_player_name': self.username,
            'auth_uuid': self.uuid,
            'auth_access_token': self.token,
            'user_type': 'mojang',
            'user_properties': '{}'
        }
        final_game_args = [arg.format(**auth_replacements) for arg in game_args]

        cmd = [
            java_path,
            f"-Xmx{ram_mb}M",
            *jvm_args,
            main_class,
            *final_game_args,
        ]

        if server:
            cmd.extend(['--server', server])
            if port:
                cmd.extend(['--port', str(port)])

        if not self.use_auth:
            cmd.append("--offline")

        print("--- LAUNCH COMMAND ---")
        print(" ".join(cmd))
        print("----------------------")

        try:
            subprocess.Popen(cmd, cwd=str(MINECRAFT_DIR), env=os.environ.copy())
        except FileNotFoundError:
            raise RuntimeError(f"Java executable not found at '{java_path}'. Please check your settings.")
        except Exception as e:
            raise RuntimeError(f"Failed to launch Minecraft: {e}")

# --- GUI ---
class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("950x650")
        self.configure(bg="#2a2a2a")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.profile = self.load_profile()
        self.active_thread = None

        self.setup_style()
        self.build_ui()
        self.post_ui_init()

    def setup_style(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure(".", background="#2a2a2a", foreground="white", fieldbackground="#3a3a3a", bordercolor="#555")
        self.style.configure("TButton", padding=6)
        self.style.map("TButton", background=[('active', '#4a4a4a')])
        self.style.configure("TLabel", padding=5)
        self.style.configure("TFrame", background="#2a2a2a")
        self.style.configure("Sidebar.TFrame", background="#1e1e1e")
        self.style.configure("Sidebar.TButton", background="#1e1e1e", foreground="white", relief="flat", anchor="w")
        self.style.map("Sidebar.TButton", background=[('active', '#3a3a3a')])
        self.style.configure("Status.TLabel", background="#1e1e1e", padding=5)

    def build_ui(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

        sidebar = ttk.Frame(main_frame, width=160, style="Sidebar.TFrame")
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_propagate(False)

        self.content = ttk.Frame(main_frame)
        self.content.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.status_var = tk.StringVar(value="Ready.")
        status_bar = ttk.Label(self, textvariable=self.status_var, style="Status.TLabel", anchor='w')
        status_bar.pack(side="bottom", fill="x")

        downloads_frame = ttk.Frame(self, style="Sidebar.TFrame")
        downloads_frame.pack(fill="x", before=status_bar)
        ttk.Label(downloads_frame, textvariable=self.status_var, style="Status.TLabel").pack(side="left", padx=5)
        self.download_progress = ttk.Progressbar(downloads_frame, variable=tk.DoubleVar(), maximum=100)
        self.download_progress.pack(side="right", fill="x", expand=True, padx=5, pady=2)

        self.sidebar_buttons = {}
        for i, (name, cmd) in enumerate([
            ("Home", lambda: self.show_frame("home")),
            ("Multiplayer", lambda: self.show_frame("multiplayer")),
            ("Versions", lambda: self.show_frame("versions")),
            ("Mods", lambda: self.show_frame("mods")),
            ("Skins", lambda: self.show_frame("skins")),
            ("Settings", lambda: self.show_frame("settings")),
        ]):
            btn = ttk.Button(sidebar, text=name, command=cmd, style="Sidebar.TButton")
            btn.pack(fill="x", pady=(10 if i == 0 else 2), padx=10)
            self.sidebar_buttons[name.lower()] = btn

        self.frames = {}
        for name in ["home", "multiplayer", "versions", "mods", "skins", "settings"]:
            frame = ttk.Frame(self.content)
            self.frames[name] = frame
            getattr(self, f"build_{name}_frame")(frame)

    def post_ui_init(self):
        self.download_queue = Queue()
        self.dm = DownloadManager(self)
        self.mc_manager = MinecraftManager(self.dm)
        self.download_progress.config(variable=self.dm.progress_var)

        self.show_frame("home")
        self.update_local_versions()
        self.update_skin_preview()
        self.refresh_mod_list()

    def show_frame(self, name):
        for frame in self.frames.values():
            frame.pack_forget()
        self.frames[name].pack(fill="both", expand=True)

    def build_home_frame(self, frame):
        ttk.Label(frame, text="Welcome to Cat-Launcher!", font=("Arial", 20, "bold")).pack(pady=20)

        login_frame = ttk.Frame(frame, padding=10)
        login_frame.pack(pady=10)
        ttk.Label(login_frame, text="Username:").grid(row=0, column=0, sticky="e", padx=5)
        self.home_user = ttk.Entry(login_frame, width=30)
        self.home_user.insert(0, self.profile.get("username", ""))
        self.home_user.grid(row=0, column=1)

        ttk.Label(login_frame, text="Password:").grid(row=1, column=0, sticky="e", padx=5)
        self.home_pass = ttk.Entry(login_frame, width=30, show="*")
        self.home_pass.grid(row=1, column=1, pady=5)

        self.home_offline_var = tk.BooleanVar(value=self.profile.get("offline_mode", False))
        self.home_offline_check = ttk.Checkbutton(login_frame, text="Offline Mode", variable=self.home_offline_var)
        self.home_offline_check.grid(row=2, column=1, sticky='w')

        action_frame = ttk.Frame(frame)
        action_frame.pack(pady=20)

        self.version_choice = ttk.Combobox(action_frame, width=25, state="readonly")
        self.version_choice.pack(side="left", padx=10)

        self.launch_button = ttk.Button(action_frame, text="Launch Game", command=self.on_launch, width=15)
        self.launch_button.pack(side="left")

    def build_multiplayer_frame(self, frame):
        ttk.Label(frame, text="Join Server", font=("Arial", 16, "bold")).pack(pady=10)
        ttk.Label(frame, text="Login details are taken from the Home page.").pack(pady=5)
        ttk.Label(frame, text="Server Address:").pack(pady=(10,0))
        self.server_addr = ttk.Entry(frame, width=40)
        self.server_addr.insert(0, self.profile.get("server_address", "play.hypixel.net"))
        self.server_addr.pack(pady=5)
        self.join_button = ttk.Button(frame, text="Join Server", command=self.on_join)
        self.join_button.pack(pady=20)

    def build_versions_frame(self, frame):
        ttk.Label(frame, text="Version Management", font=("Arial", 16, "bold")).pack(pady=10)

        install_frame = ttk.Frame(frame)
        install_frame.pack(pady=10)

        self.remote_version_choice = ttk.Combobox(install_frame, values=VERSIONS, width=30)
        self.remote_version_choice.set("Select version to install")
        self.remote_version_choice.pack(side="left", padx=5)

        self.install_button = ttk.Button(install_frame, text="Install", command=self.on_install_version)
        self.install_button.pack(side="left")

        self.refresh_versions_button = ttk.Button(install_frame, text="Refresh List", command=self.on_refresh_remote_versions)
        self.refresh_versions_button.pack(side="left", padx=5)

        ttk.Label(frame, text="Installed Versions:", font=("", 10, "italic")).pack(pady=(10,0), anchor='w')
        self.installed_list = tk.Listbox(frame, bg="#3a3a3a", fg="white", selectbackground="#555", height=10)
        self.installed_list.pack(fill='x', expand=True, pady=5)

    def build_mods_frame(self, frame):
        ttk.Label(frame, text="Mods Management", font=("Arial", 16, "bold")).pack(pady=10)
        self.mod_list = tk.Listbox(frame, bg="#3a3a3a", fg="white", width=60, height=15)
        self.mod_list.pack(pady=5, fill="both", expand=True)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Add Mod (.jar)", command=self.add_mod).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Remove Selected", command=self.remove_mod).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Open Mods Folder", command=lambda: os.startfile(MODS_DIR)).pack(side="left", padx=5)

    def build_skins_frame(self, frame):
        ttk.Label(frame, text="Skin Customization", font=("Arial", 16, "bold")).pack(pady=10)
        ttk.Label(frame, text="Requires a TLauncher.org account.", font=("", 9, "italic")).pack()

        self.skin_preview_label = ttk.Label(frame, text="No Skin Loaded")
        self.skin_preview_label.pack(pady=10)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Fetch My Skin", command=self.fetch_user_skin).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Set from file...", command=self.set_local_skin).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="TLauncher Skin Editor", command=lambda: webbrowser.open("https://tlauncher.org/en/skin/")).pack(side="left", padx=5)

    def build_settings_frame(self, frame):
        ttk.Label(frame, text="Settings", font=("Arial", 16, "bold")).pack(pady=10)

        settings_grid = ttk.Frame(frame, padding=10)
        settings_grid.pack(fill='x')

        ttk.Label(settings_grid, text="RAM Allocation (MB):").grid(row=0, column=0, sticky="w", pady=5)
        self.ram_entry = ttk.Entry(settings_grid, width=15)
        self.ram_entry.insert(0, str(self.profile.get("ram_mb", "2048")))
        self.ram_entry.grid(row=0, column=1, sticky="w")

        ttk.Label(settings_grid, text="Java Path:").grid(row=1, column=0, sticky="w", pady=5)
        self.java_path_entry = ttk.Entry(settings_grid, width=60)
        self.java_path_entry.insert(0, self.profile.get("java_path", shutil.which("java") or "java"))
        self.java_path_entry.grid(row=1, column=1, sticky="ew")

        ttk.Button(settings_grid, text="Browse...", command=self.browse_java).grid(row=1, column=2, padx=5)
        settings_grid.grid_columnconfigure(1, weight=1)

        ttk.Button(frame, text="Save Settings", command=self.save_settings).pack(pady=20)

    # --- Actions and Logic ---

    def start_threaded_task(self, target, *args):
        if self.active_thread and self.active_thread.is_alive():
            messagebox.showwarning(APP_TITLE, "Another operation is already in progress.")
            return

        self.set_ui_state("disabled")
        self.active_thread = threading.Thread(target=target, args=args, daemon=True)
        self.active_thread.start()
        self.after(100, self.check_thread)

    def check_thread(self):
        if self.active_thread and self.active_thread.is_alive():
            self.after(100, self.check_thread)
        else:
            self.set_ui_state("normal")

    def set_ui_state(self, state):
        for widget in [self.launch_button, self.join_button, self.install_button, self.refresh_versions_button]:
            widget.config(state=state)
        for btn in self.sidebar_buttons.values():
            btn.config(state=state)

    def _launch_logic(self, client: CatClient, server=None, port=None):
        try:
            self.status_var.set("Authenticating...")
            if not client.authenticate():
                self.status_var.set("Authentication failed.")
                self.save_profile_from_ui()
                return

            self.save_profile_from_ui()

            self.status_var.set(f"Preparing Minecraft {client.version_id}...")
            main_class, jvm_args, game_args = self.mc_manager.prepare_version(
                client.version_id,
                lambda msg: self.status_var.set(msg)
            )

            self.status_var.set("Launching game...")
            ram_mb = self.profile.get("ram_mb", 2048)
            java_path = self.profile.get("java_path", "java")
            client.launch(main_class, jvm_args, game_args, java_path, ram_mb, server, port)
            self.status_var.set(f"Game {client.version_id} launched!")

        except Exception as e:
            self.status_var.set(f"Error: {e}")
            messagebox.showerror(APP_TITLE, f"An error occurred:\n{e}")

    def on_launch(self):
        client = self._get_client_from_ui()
        if not client:
            return
        self.start_threaded_task(self._launch_logic, client)

    def on_join(self):
        client = self._get_client_from_ui()
        if not client:
            return

        addr = self.server_addr.get().strip()
        if not addr:
            messagebox.showwarning(APP_TITLE, "Please enter a server address.")
            return

        self.profile['server_address'] = addr
        host, *port_parts = addr.split(":")
        port = port_parts[0] if port_parts else 25565
        self.start_threaded_task(self._launch_logic, client, host, port)

    def _get_client_from_ui(self):
        user = self.home_user.get().strip()
        pw = self.home_pass.get()
        version_id = self.version_choice.get()
        use_auth = not self.home_offline_var.get()

        if not user:
            messagebox.showwarning(APP_TITLE, "Username cannot be empty.")
            return None
        if use_auth and not pw:
            messagebox.showwarning(APP_TITLE, "Password is required for online mode.")
            return None
        if not version_id or "Select" in version_id:
            messagebox.showwarning(APP_TITLE, "Please select an installed version.")
            return None

        return CatClient(user, pw, version_id, use_auth=use_auth)

    def on_install_version(self):
        version_id = self.remote_version_choice.get()
        if not version_id or "Select" in version_id:
            messagebox.showwarning(APP_TITLE, "Please select a version to install.")
            return

        def _install():
            try:
                self.status_var.set(f"Preparing to install {version_id}...")
                self.mc_manager.prepare_version(
                    version_id,
                    lambda msg: self.status_var.set(msg)
                )
                self.status_var.set(f"Successfully installed {version_id}!")
                self.after(0, self.update_local_versions)
            except Exception as e:
                self.status_var.set(f"Install failed: {e}")
                messagebox.showerror(APP_TITLE, f"Failed to install {version_id}:\n{e}")

        self.start_threaded_task(_install)

    def on_refresh_remote_versions(self):
        def _refresh():
            try:
                self.status_var.set("Fetching remote version list...")
                manifest = http_get_json(VERSION_MANIFEST_URL)
                versions = [v['id'] for v in manifest['versions']]
                self.remote_version_choice['values'] = versions
                self.remote_version_choice.set("Select version to install")
                self.status_var.set("Remote version list refreshed.")
            except Exception as e:
                messagebox.showerror(APP_TITLE, f"Failed to refresh versions: {e}")
                self.status_var.set("Failed to refresh versions.")

        self.start_threaded_task(_refresh)

    def update_local_versions(self):
        installed = []
        for p in VERSIONS_DIR.iterdir():
            if p.is_dir() and (p / f"{p.name}.json").exists():
                installed.append(p.name)

        installed.sort(key=lambda s: list(map(int, s.split('.'))), reverse=True)

        self.version_choice['values'] = installed
        if installed:
            current_version = self.profile.get("version_id")
            if current_version in installed:
                self.version_choice.set(current_version)
            else:
                self.version_choice.set(installed[0])
        else:
            self.version_choice.set("No versions installed")

        self.installed_list.delete(0, tk.END)
        for v in installed:
            self.installed_list.insert(tk.END, v)

    # --- Mod/Skin/Settings Handlers ---

    def add_mod(self):
        files = filedialog.askopenfilenames(
            title="Select Mod(s)",
            filetypes=[("JAR files", "*.jar"), ("Disabled Mods", "*.jar.disabled")]
        )
        if files:
            for file in files:
                shutil.copy(file, MODS_DIR / Path(file).name)
            self.refresh_mod_list()

    def remove_mod(self):
        selection = self.mod_list.curselection()
        if selection:
            mod_name = self.mod_list.get(selection[0])
            if messagebox.askyesno(APP_TITLE, f"Are you sure you want to delete '{mod_name}'?"):
                (MODS_DIR / mod_name).unlink(missing_ok=True)
                self.refresh_mod_list()

    def refresh_mod_list(self):
        self.mod_list.delete(0, tk.END)
        mods = sorted(list(p.name for p in MODS_DIR.glob("*.jar")))
        for mod in mods:
            self.mod_list.insert(tk.END, mod)

    def fetch_user_skin(self):
        user = self.home_user.get().strip()
        if not user:
            messagebox.showwarning(APP_TITLE, "Enter a username on the Home page first.")
            return

        def _fetch():
            try:
                self.status_var.set(f"Fetching skin for {user}...")
                url = TLAUNCHER_SKIN_URL.format(username=user)
                dest = SKINS_DIR / f"{user}.png"
                download_file(url, dest)
                self.profile['skin_path'] = str(dest)
                self.after(0, self.update_skin_preview)
                self.status_var.set("Skin fetched successfully.")
            except Exception as e:
                messagebox.showerror(APP_TITLE, f"Could not fetch skin for '{user}'. They may not have one.\nError: {e}")
                self.status_var.set("Failed to fetch skin.")

        self.start_threaded_task(_fetch)

    def set_local_skin(self):
        file = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
        if file:
            self.profile['skin_path'] = file
            self.update_skin_preview()
            messagebox.showinfo(APP_TITLE, "Skin preview updated. Note: This does not upload the skin.")

    def update_skin_preview(self):
        skin_path_str = self.profile.get("skin_path")
        if not skin_path_str or not Path(skin_path_str).exists():
            self.skin_preview_label.config(image=None, text="No Skin Loaded")
            return

        try:
            skin_path = Path(skin_path_str)
            img = Image.open(skin_path)
            preview_img = img.resize((128, 128), Image.NEAREST)
            self.skin_photo = ImageTk.PhotoImage(preview_img)
            self.skin_preview_label.config(image=self.skin_photo, text="")
        except Exception as e:
            self.skin_preview_label.config(image=None, text=f"Error loading skin:\n{e}")

    def browse_java(self):
        path = filedialog.askopenfilename(
            title="Select Java Executable",
            filetypes=[("Java Executable", "java.exe"), ("All files", "*.*")]
        )
        if path:
            self.java_path_entry.delete(0, tk.END)
            self.java_path_entry.insert(0, path)

    def save_settings(self):
        try:
            ram_mb = int(self.ram_entry.get())
            if ram_mb < 512:
                raise ValueError("RAM must be at least 512 MB.")
            self.profile['ram_mb'] = ram_mb
            self.profile['java_path'] = self.java_path_entry.get().strip()
            self.save_profile()
            messagebox.showinfo(APP_TITLE, "Settings saved successfully.")
        except ValueError as e:
            messagebox.showerror(APP_TITLE, f"Invalid setting: {e}")

    # --- Profile & Window Management ---

    def load_profile(self):
        if PROFILE_FILE.exists():
            try:
                return json.loads(PROFILE_FILE.read_text("utf-8"))
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def save_profile_from_ui(self):
        self.profile['username'] = self.home_user.get().strip()
        self.profile['offline_mode'] = self.home_offline_var.get()
        self.profile['version_id'] = self.version_choice.get()
        self.save_profile()

    def save_profile(self):
        try:
            PROFILE_FILE.write_text(json.dumps(self.profile, indent=2), "utf-8")
        except IOError as e:
            print(f"Warning: Could not save profile file: {e}")

    def on_closing(self):
        self.save_profile_from_ui()
        self.destroy()

if __name__ == "__main__":
    app = Launcher()
    app.mainloop()

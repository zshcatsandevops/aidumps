import os
import json
import shutil
import subprocess
import threading
import urllib.request
import hashlib
from pathlib import Path
from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import webbrowser
from PIL import Image, ImageTk

APP_TITLE = "Cat-Launcher (TLauncher Clone)"
VERSIONS = [
    "latest-release",
    "latest-snapshot",
    "1.21",
    "1.20.6",
    "1.20.5-fabric",
    "1.19.4-optifine",
    "1.19.4-forge",
    "1.18.2",
]

BASE_DIR = Path.home() / ".catlauncher"
PROFILE_FILE = BASE_DIR / "profiles.json"
MINECRAFT_DIR = BASE_DIR / "minecraft"
LIB_DIR = MINECRAFT_DIR / "versions"
MODS_DIR = MINECRAFT_DIR / "mods"
SKINS_DIR = MINECRAFT_DIR / "skins"
CONFIG_DIR = MINECRAFT_DIR / "config"
for d in (LIB_DIR, MODS_DIR, SKINS_DIR, CONFIG_DIR):
    d.mkdir(parents=True, exist_ok=True)

VERSION_MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
TLAUNCHER_AUTH_URL = "https://auth.tlauncher.org/authenticate"
SKIN_API_URL = "https://tlauncher.org/upload/skin/"
MODS_API_URL = "https://api.curseforge.com/v1/mods/search"

def http_get_json(url: str, timeout=10) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.load(r)

def download_file(url: str, dest: Path, expected_sha1=None):
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    h = hashlib.sha1()
    with urllib.request.urlopen(url) as resp, tmp.open("wb") as f:
        while True:
            chunk = resp.read(8192)
            if not chunk:
                break
            f.write(chunk)
            h.update(chunk)
    if expected_sha1 and h.hexdigest() != expected_sha1:
        tmp.unlink(missing_ok=True)
        raise IOError("Checksum mismatch")
    shutil.move(tmp, dest)
    return dest

@dataclass
class CatClient:
    username: str
    password: str
    version_id: str
    use_auth: bool = True
    token: str = None

    def authenticate(self) -> bool:
        if not self.use_auth:
            self.token = f"offline_{self.username}"
            return True
        payload = json.dumps({"username": self.username, "password": self.password}).encode()
        req = urllib.request.Request(
            TLAUNCHER_AUTH_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=7) as f:
                resp = json.load(f)
            self.token = resp.get("accessToken")
            return bool(self.token)
        except Exception:
            return False

    def join_server(self, address: str, port: int = 25565, ram_mb: int = 2048) -> None:
        if not self.token:
            raise RuntimeError("Not authenticated")
        jar_path = self.ensure_client_jar()
        cmd = [
            "java",
            f"-Xmx{ram_mb}m",
            "-cp", str(jar_path),
            "net.minecraft.client.Main",
            "--token", self.token,
            "--server", f"{address}:{port}",
            "--version", self.version_id,
        ]
        if not self.use_auth:
            cmd.append("--offline")
        subprocess.Popen(cmd, env=os.environ.copy())

    def launch_game(self, ram_mb: int = 2048) -> None:
        if not self.token:
            raise RuntimeError("Not authenticated")
        jar_path = self.ensure_client_jar()
        cmd = [
            "java",
            f"-Xmx{ram_mb}m",
            "-cp", str(jar_path),
            "net.minecraft.client.Main",
            "--token", self.token,
            "--version", self.version_id,
        ]
        if not self.use_auth:
            cmd.append("--offline")
        subprocess.Popen(cmd, env=os.environ.copy())

    def ensure_client_jar(self) -> Path:
        dest = LIB_DIR / f"{self.version_id}.jar"
        if dest.exists():
            return dest
        manifest = http_get_json(VERSION_MANIFEST_URL)
        if self.version_id in ("latest-release", "latest-snapshot"):
            key = "release" if self.version_id == "latest-release" else "snapshot"
            vid = manifest["latest"][key]
            info = next(v for v in manifest["versions"] if v["id"] == vid)
        else:
            info = next((v for v in manifest["versions"] if v["id"].lower() == self.version_id.lower()), None)
            if not info:
                raise RuntimeError(f"Unknown version: {self.version_id}")
        version_meta = http_get_json(info["url"])
        download_info = version_meta["downloads"]["client"]
        download_file(download_info["url"], dest, expected_sha1=download_info["sha1"])
        return dest

class Launcher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_TITLE)
        self.root.geometry("900x600")
        self.root.configure(bg="#2a2a2a")
        self.profile = self.load_profile()
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TButton", background="#3a3a3a", foreground="white", bordercolor="#555555")
        self.style.configure("TEntry", fieldbackground="#3a3a3a", foreground="white")
        self.style.configure("TCombobox", fieldbackground="#3a3a3a", foreground="white")
        self.style.configure("TLabel", background="#2a2a2a", foreground="white")
        self.style.configure("TFrame", background="#2a2a2a")
        self.build_ui()

    def build_ui(self):
        main_frame = tk.Frame(self.root, bg="#2a2a2a")
        main_frame.pack(fill="both", expand=True)

        sidebar = tk.Frame(main_frame, bg="#1a1a1a", width=150)
        sidebar.pack(side="left", fill="y")

        for text, cmd in [
            ("Home", lambda: self.show_frame("home")),
            ("Versions", lambda: self.show_frame("versions")),
            ("Mods", lambda: self.show_frame("mods")),
            ("Skins", lambda: self.show_frame("skins")),
            ("Servers", lambda: self.show_frame("servers")),
            ("Settings", lambda: self.show_frame("settings")),
        ]:
            btn = ttk.Button(sidebar, text=text, command=cmd)
            btn.pack(fill="x", pady=5, padx=5)

        self.content = tk.Frame(main_frame, bg="#2a2a2a")
        self.content.pack(side="right", fill="both", expand=True)

        self.frames = {}
        self.build_home()
        self.build_versions()
        self.build_mods()
        self.build_skins()
        self.build_servers()
        self.build_settings()

        self.show_frame("home")
        self.status_bar = ttk.Label(self.root, text="Ready.", relief="sunken", background="#1a1a1a", foreground="white")
        self.status_bar.pack(side="bottom", fill="x")

    def build_home(self):
        frame = tk.Frame(self.content, bg="#2a2a2a")
        self.frames["home"] = frame
        ttk.Label(frame, text="Welcome to Cat-Launcher!", font=("Arial", 16)).pack(pady=10)
        news = tk.Text(frame, height=10, bg="#3a3a3a", fg="white", wrap="word")
        news.insert("1.0", "Latest News: Minecraft 1.21 released! Check out new features and mods.")
        news.config(state="disabled")
        news.pack(fill="x", padx=10, pady=5)
        ttk.Button(frame, text="Launch Game", command=self.on_launch).pack(pady=10)

    def build_versions(self):
        frame = tk.Frame(self.content, bg="#2a2a2a")
        self.frames["versions"] = frame
        ttk.Label(frame, text="Minecraft Version:").pack(pady=5)
        self.version_choice = ttk.Combobox(frame, values=VERSIONS, width=30)
        self.version_choice.set(self.profile.get("version_id", VERSIONS[0]))
        self.version_choice.pack(pady=5)
        ttk.Button(frame, text="Refresh Versions", command=self.refresh_versions).pack(pady=5)

    def build_mods(self):
        frame = tk.Frame(self.content, bg="#2a2a2a")
        self.frames["mods"] = frame
        ttk.Label(frame, text="Mods Management").pack(pady=5)
        self.mod_list = tk.Listbox(frame, bg="#3a3a3a", fg="white", width=50, height=10)
        self.mod_list.pack(pady=5)
        ttk.Button(frame, text="Add Mod", command=self.add_mod).pack(pady=5)
        ttk.Button(frame, text="Remove Selected Mod", command=self.remove_mod).pack(pady=5)
        self.refresh_mod_list()

    def build_skins(self):
        frame = tk.Frame(self.content, bg="#2a2a2a")
        self.frames["skins"] = frame
        ttk.Label(frame, text="Skin Customization").pack(pady=5)
        self.skin_preview = ttk.Label(frame)
        self.skin_preview.pack(pady=5)
        ttk.Button(frame, text="Upload Skin", command=self.upload_skin).pack(pady=5)
        ttk.Button(frame, text="Open Skin Editor", command=lambda: webbrowser.open("https://tlauncher.org/en/skin/")).pack(pady=5)
        self.update_skin_preview()

    def build_servers(self):
        frame = tk.Frame(self.content, bg="#2a2a2a")
        self.frames["servers"] = frame
        ttk.Label(frame, text="Username:").pack(pady=5)
        self.mp_user = ttk.Entry(frame, width=30)
        self.mp_user.insert(0, self.profile.get("multiplayer_user", ""))
        self.mp_user.pack(pady=5)
        ttk.Label(frame, text="Password:").pack(pady=5)
        self.mp_pass = ttk.Entry(frame, width=30, show="*")
        self.mp_pass.pack(pady=5)
        ttk.Label(frame, text="Server Address:").pack(pady=5)
        self.server_addr = ttk.Entry(frame, width=30)
        self.server_addr.insert(0, self.profile.get("multiplayer_server", "play.hypixel.net"))
        self.server_addr.pack(pady=5)
        self.offline_check = ttk.Checkbutton(frame, text="Offline Mode")
        self.offline_check.pack(pady=5)
        if self.profile.get("offline_mode", False):
            self.offline_check.state(['selected'])
        ttk.Button(frame, text="Join Server", command=self.on_join).pack(pady=10)

    def build_settings(self):
        frame = tk.Frame(self.content, bg="#2a2a2a")
        self.frames["settings"] = frame
        ttk.Label(frame, text="RAM Allocation (MB):").pack(pady=5)
        self.ram_entry = ttk.Entry(frame, width=10)
        self.ram_entry.insert(0, self.profile.get("ram_mb", "2048"))
        self.ram_entry.pack(pady=5)
        ttk.Label(frame, text="Java Path:").pack(pady=5)
        self.java_path = ttk.Entry(frame, width=50)
        self.java_path.insert(0, self.profile.get("java_path", shutil.which("java") or ""))
        self.java_path.pack(pady=5)
        ttk.Button(frame, text="Browse Java", command=self.browse_java).pack(pady=5)
        ttk.Button(frame, text="Save Settings", command=self.save_settings).pack(pady=5)

    def show_frame(self, name):
        for frame in self.frames.values():
            frame.pack_forget()
        self.frames[name].pack(fill="both", expand=True)

    def on_launch(self):
        user = self.mp_user.get().strip()
        pw = self.mp_pass.get().strip()
        version_id = self.version_choice.get()
        use_auth = not self.offline_check.instate(['selected'])
        ram_mb = self.profile.get("ram_mb", 2048)

        if not user or (use_auth and not pw):
            messagebox.showwarning(APP_TITLE, "Enter username and password (unless offline).")
            return

        self.profile.update({
            "multiplayer_user": user,
            "version_id": version_id,
            "offline_mode": not use_auth
        })
        threading.Thread(target=self.save_profile, daemon=True).start()

        client = CatClient(user, pw, version_id, use_auth=use_auth)
        self.status_bar.config(text="Authenticating…" if use_auth else "Offline mode: skipping auth…")
        threading.Thread(target=self.auth_and_launch, args=(client, ram_mb), daemon=True).start()

    def auth_and_launch(self, client: CatClient, ram_mb: int):
        if not client.authenticate():
            messagebox.showerror(APP_TITLE, "Authentication failed.")
            self.status_bar.config(text="Auth failed.")
            return
        self.status_bar.config(text="Launching game…")
        try:
            client.launch_game(ram_mb)
            self.status_bar.config(text="Game launched ✔")
        except Exception as e:
            messagebox.showerror(APP_TITLE, f"Launch failed:\n{e}")
            self.status_bar.config(text="Launch failed ✖")

    def on_join(self):
        user = self.mp_user.get().strip()
        pw = self.mp_pass.get().strip()
        addr = self.server_addr.get().strip()
        version_id = self.version_choice.get()
        use_auth = not self.offline_check.instate(['selected'])
        ram_mb = self.profile.get("ram_mb", 2048)

        if not user or (use_auth and not pw) or not addr:
            messagebox.showwarning(APP_TITLE, "Enter username, password (unless offline), and server address.")
            return

        self.profile.update({
            "multiplayer_user": user,
            "multiplayer_server": addr,
            "version_id": version_id,
            "offline_mode": not use_auth
        })
        threading.Thread(target=self.save_profile, daemon=True).start()

        client = CatClient(user, pw, version_id, use_auth=use_auth)
        self.status_bar.config(text="Authenticating…" if use_auth else "Offline mode: skipping auth…")
        threading.Thread(target=self.auth_and_join, args=(client, addr, ram_mb), daemon=True).start()

    def auth_and_join(self, client: CatClient, addr: str, ram_mb: int):
        if not client.authenticate():
            messagebox.showerror(APP_TITLE, "Authentication failed.")
            self.status_bar.config(text="Auth failed.")
            return
        self.status_bar.config(text="Connecting to server…")
        try:
            host, port = addr.split(":") if ":" in addr else (addr, "25565")
            client.join_server(host, int(port), ram_mb)
            self.status_bar.config(text="Joined server ✔")
        except Exception as e:
            messagebox.showerror(APP_TITLE, f"Join failed:\n{e}")
            self.status_bar.config(text="Join failed ✖")

    def refresh_versions(self):
        try:
            manifest = http_get_json(VERSION_MANIFEST_URL)
            new_versions = [v["id"] for v in manifest["versions"]]
            self.version_choice["values"] = VERSIONS + [v for v in new_versions if v not in VERSIONS]
            self.status_bar.config(text="Versions refreshed.")
        except Exception as e:
            messagebox.showerror(APP_TITLE, f"Failed to refresh versions:\n{e}")

    def add_mod(self):
        file = filedialog.askopenfilename(filetypes=[("JAR files", "*.jar")])
        if file:
            shutil.copy(file, MODS_DIR / Path(file).name)
            self.refresh_mod_list()

    def remove_mod(self):
        selection = self.mod_list.curselection()
        if selection:
            mod = self.mod_list.get(selection[0])
            (MODS_DIR / mod).unlink(missing_ok=True)
            self.refresh_mod_list()

    def refresh_mod_list(self):
        self.mod_list.delete(0, tk.END)
        for mod in MODS_DIR.glob("*.jar"):
            self.mod_list.insert(tk.END, mod.name)

    def upload_skin(self):
        file = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
        if file:
            with open(file, "rb") as f:
                response = requests.post(SKIN_API_URL, files={"skin": f})
            if response.status_code == 200:
                self.update_skin_preview()
                messagebox.showinfo(APP_TITLE, "Skin uploaded successfully.")
            else:
                messagebox.showerror(APP_TITLE, "Failed to upload skin.")

    def update_skin_preview(self):
        try:
            skin_path = SKINS_DIR / "skin.png"
            if skin_path.exists():
                img = Image.open(skin_path).resize((100, 200))
                self.skin_preview.img = ImageTk.PhotoImage(img)
                self.skin_preview.config(image=self.skin_preview.img)
        except Exception:
            pass

    def browse_java(self):
        path = filedialog.askopenfilename(filetypes=[("Executable", "*.exe"), ("All files", "*.*")])
        if path:
            self.java_path.delete(0, tk.END)
            self.java_path.insert(0, path)

    def save_settings(self):
        ram = self.ram_entry.get().strip()
        java = self.java_path.get().strip()
        try:
            ram_mb = int(ram)
            if ram_mb < 512:
                raise ValueError("RAM must be at least 512 MB")
            self.profile.update({"ram_mb": ram_mb, "java_path": java})
            self.save_profile()
            messagebox.showinfo(APP_TITLE, "Settings saved.")
        except ValueError as e:
            messagebox.showerror(APP_TITLE, f"Invalid RAM value:\n{e}")

    def load_profile(self) -> dict:
        try:
            return json.loads(PROFILE_FILE.read_text("utf-8"))
        except Exception:
            return {}

    def save_profile(self):
        try:
            PROFILE_FILE.write_text(json.dumps(self.profile, indent=2), "utf-8")
        except Exception:
            pass

    def run(self):
        self.root.mainloop()
''''''
if __name__ == "__main__":
    Launcher().run()

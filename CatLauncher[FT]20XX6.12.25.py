"""
cat_sama_launcher.py — Tkinter-based game launcher with automatic JAR fetching
Last updated: 2025-06-12 (v0.5.0)

•  NEW  Automatically downloads the exact Minecraft client JAR for any vanilla
   release chosen in the drop-down (not just snapshots). No more manual
   **minecraft.jar** copying!
•  Unified release/snapshot download logic and stores each JAR in
   `./minecraft/minecraft-<version>.jar`.
•  Subtle refactor of the launch flow; see `_ensure_version_jar()`.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import threading
import urllib.request
from functools import wraps
from pathlib import Path
from tkinter import messagebox, ttk
import tkinter as tk

# ------------------------------------------------------------
# Paths & constants
# ------------------------------------------------------------

APP_TITLE: str = "Cat-Sama Launcher"
VERSIONS: list[str] = [
    "1.20.6",
    "1.20.5-Fabric",  # “Fabric” suffix is ignored when fetching vanilla JAR
    "1.19.4-OptiFine",  # idem
    "Latest Snapshot",
]

BASE_DIR: Path = Path(__file__).resolve().parent
PROFILE_FILE: Path = BASE_DIR / "profiles.json"
MINECRAFT_DIR: Path = BASE_DIR / "minecraft"
MINECRAFT_DIR.mkdir(exist_ok=True)

# Legacy constant (no longer used directly, but kept for backwards-compat)
MINECRAFT_JAR: Path = MINECRAFT_DIR / "minecraft.jar"

VERSION_MANIFEST_URL: str = (
    "https://launchermeta.mojang.com/mc/game/version_manifest.json"
)
NEWS_FEED_URL: str = "https://launchermeta.mojang.com/news.json"

# ------------------------------------------------------------
# Utility helpers
# ------------------------------------------------------------


def java_available() -> bool:
    """Return True iff a `java` executable is discoverable on PATH."""
    return shutil.which("java") is not None


def load_profile() -> dict[str, str]:
    """Return last-saved username/version combo; fall back to defaults."""
    if PROFILE_FILE.exists():
        try:
            return json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"username": "", "version": VERSIONS[0]}


def save_profile(username: str, version: str) -> None:
    """Persist username/version to disk (UTF-8 JSON)."""
    PROFILE_FILE.write_text(
        json.dumps({"username": username, "version": version}), encoding="utf-8"
    )


# ---------- threading decorator ---------- #

def threaded(fn):
    """Decorator: run *fn* in a daemon thread and return the thread object."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        t = threading.Thread(target=fn, args=args, kwargs=kwargs, daemon=True)
        t.start()
        return t

    return wrapper


# ------------------------------------------------------------
# Tkinter UI with 60 FPS tick
# ------------------------------------------------------------


class Launcher(tk.Tk):
    """Main Tkinter window."""

    # ---------- construction ---------- #

    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("720x480")
        self.minsize(640, 400)

        ttk.Style(self).configure("TButton", padding=6)

        self.status = tk.StringVar(value="Ready.")
        self.profile: dict[str, str] = load_profile()

        self._build()
        self._start_tick()

    # ---------- UI helpers ---------- #

    def _build(self) -> None:
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        self._tab_home(nb)
        self._tab_settings(nb)
        self._tab_about(nb)

        sb = ttk.Frame(self)
        sb.pack(fill="x", side="bottom")
        ttk.Label(sb, textvariable=self.status, anchor="w").pack(fill="x")

    def _tab_home(self, nb: ttk.Notebook) -> None:
        page = ttk.Frame(nb)
        nb.add(page, text="Home")

        # Left column
        left = ttk.Frame(page, padding=12)
        left.pack(side="left", fill="y")

        ttk.Label(left, text="Username:").pack(anchor="w")
        self.username = ttk.Entry(left, width=26)
        self.username.pack(anchor="w", pady=(0, 10))
        self.username.insert(0, self.profile["username"])

        ttk.Label(left, text="Version:").pack(anchor="w")
        self.version = tk.StringVar(value=self.profile["version"])
        ttk.Combobox(
            left,
            textvariable=self.version,
            values=VERSIONS,
            state="readonly",
            width=24,
        ).pack(anchor="w", pady=(0, 20))

        self.play_btn = ttk.Button(left, text="▶ PLAY", width=22, command=self._on_play)
        self.play_btn.pack(anchor="w")

        # Right column — news feed
        right = ttk.Labelframe(page, text="News", padding=8)
        right.pack(side="left", fill="both", expand=True, padx=12, pady=8)

        self.news_box = tk.Text(right, wrap="word", height=16, state="disabled")
        self.news_box.pack(fill="both", expand=True)
        self._load_news_async()

    def _tab_settings(self, nb: ttk.Notebook) -> None:
        page = ttk.Frame(nb, padding=20)
        nb.add(page, text="Settings")
        ttk.Label(page, text="(future settings)").pack()

    def _tab_about(self, nb: ttk.Notebook) -> None:
        page = ttk.Frame(nb, padding=20)
        nb.add(page, text="About")
        ttk.Label(page, text=f"{APP_TITLE}\nPrototype Tkinter launcher.\n© 2025 Cat-Sama").pack()

    # ---------- News feed ---------- #

    @threaded
    def _load_news_async(self) -> None:
        try:
            with urllib.request.urlopen(NEWS_FEED_URL, timeout=4) as f:
                data = json.load(f)
            items = data.get("news", [])[:5]
            news = [(i.get("title", ""), i.get("shortDescription", "")) for i in items]
        except Exception:
            news = [("Welcome!", "Unable to fetch news…")]
        self.after(0, self._populate_news, news)

    def _populate_news(self, items: list[tuple[str, str]]) -> None:
        self.news_box.config(state="normal")
        self.news_box.delete("1.0", "end")
        for title, desc in items:
            self.news_box.insert("end", f"{title}\n", ("title",))
            self.news_box.insert("end", f"{desc}\n\n")
        self.news_box.tag_configure("title", font=("Segoe UI", 10, "bold"))
        self.news_box.config(state="disabled")

    # --------------------------------------------------------
    # Launch workflow
    # --------------------------------------------------------

    def _on_play(self) -> None:
        user: str = self.username.get().strip()
        ver_choice: str = self.version.get()
        if not user:
            messagebox.showwarning(APP_TITLE, "Please enter a username.")
            return
        if not java_available():
            messagebox.showerror(APP_TITLE, "Java runtime not found on PATH.")
            return

        save_profile(user, ver_choice)
        self.play_btn.config(state="disabled")
        self._set_status("Preparing…")
        self._launch_async(user, ver_choice)

    @threaded
    def _launch_async(self, user: str, ver_choice: str) -> None:
        # Determine whether the user picked the live snapshot or a specific release.
        if ver_choice == "Latest Snapshot":
            jar_path = self._download_snapshot()
            if jar_path is None:
                self.after(0, self._launch_cleanup, "Snapshot download failed.")
                return
        else:
            # Strip any non-vanilla suffix ("-Fabric", "-OptiFine"…)
            version_id = self._normalize_version_id(ver_choice)
            jar_path = self._ensure_version_jar(version_id)
            if jar_path is None:
                self.after(0, self._launch_cleanup, "Download failed.")
                return

        cmd = ["java", "-jar", str(jar_path), "--username", user, "--version", ver_choice]
        try:
            subprocess.Popen(cmd)
            self.after(0, self._launch_cleanup, "Game running.")
        except Exception as exc:
            self.after(0, messagebox.showerror, APP_TITLE, f"Unable to launch:\n{exc}")
            self.after(0, self._launch_cleanup, "Launch failed.")

    def _launch_cleanup(self, msg: str) -> None:
        self._set_status(msg)
        self.play_btn.config(state="normal")

    # --------------------------------------------------------
    # JAR download helpers
    # --------------------------------------------------------

    def _normalize_version_id(self, ver_choice: str) -> str:
        """Return the vanilla version ID (e.g. "1.20.5" from "1.20.5-Fabric")."""
        # split on first dash or whitespace
        return re.split(r"[\s\-]", ver_choice, maxsplit=1)[0]

    def _ensure_version_jar(self, version_id: str) -> Path | None:
        """Return Path to JAR for *version_id*, downloading it if necessary."""
        jar_path = MINECRAFT_DIR / f"minecraft-{version_id}.jar"
        if jar_path.exists():
            return jar_path
        success = self._download_release(version_id, jar_path)
        return jar_path if success else None

    # ---------- release (vanilla) ---------- #

    def _download_release(self, version_id: str, jar_path: Path) -> bool:
        try:
            self._set_status(f"Fetching {version_id} metadata…")
            with urllib.request.urlopen(VERSION_MANIFEST_URL, timeout=6) as f:
                manifest = json.load(f)
            try:
                version_info = next(v for v in manifest["versions"] if v["id"] == version_id)
            except StopIteration:
                raise RuntimeError(f"Version {version_id} not found in manifest")

            # second request: specific version JSON
            with urllib.request.urlopen(version_info["url"], timeout=6) as f:
                verdata = json.load(f)
            client_url: str = verdata["downloads"]["client"]["url"]

            self._set_status("Downloading release JAR…")
            urllib.request.urlretrieve(client_url, jar_path)
            self._set_status("Download complete.")
            return True
        except Exception as exc:
            self.after(0, messagebox.showerror, APP_TITLE, f"Download failed:\n{exc}")
            return False

    # ---------- latest snapshot ---------- #

    def _download_snapshot(self) -> Path | None:
        try:
            self._set_status("Fetching snapshot info…")
            with urllib.request.urlopen(VERSION_MANIFEST_URL, timeout=6) as f:
                manifest = json.load(f)
            snapshot_id: str | None = manifest.get("latest", {}).get("snapshot")
            if not snapshot_id:
                raise RuntimeError("snapshot id not found")

            jar_path = MINECRAFT_DIR / f"minecraft-{snapshot_id}.jar"
            if jar_path.exists():
                return jar_path

            self._set_status(f"Snapshot {snapshot_id}")
            url = next(v["url"] for v in manifest["versions"] if v["id"] == snapshot_id)
            with urllib.request.urlopen(url, timeout=6) as f:
                verdata = json.load(f)
            client_url: str = verdata["downloads"]["client"]["url"]

            self._set_status("Downloading snapshot JAR…")
            urllib.request.urlretrieve(client_url, jar_path)
            self._set_status("Download complete.")
            return jar_path
        except Exception as exc:
            self.after(0, messagebox.showerror, APP_TITLE, f"Snapshot download failed:\n{exc}")
            return None

    # --------------------------------------------------------
    # 60 FPS update loop (placeholder)
    # --------------------------------------------------------

    def _start_tick(self) -> None:
        self._tick()

    def _tick(self) -> None:
        # put animation logic here
        self.after(16, self._tick)

    # --------------------------------------------------------
    # Misc.
    # --------------------------------------------------------

    def _set_status(self, txt: str) -> None:
        self.after(0, self.status.set, txt)


# ------------------------------------------------------------
# Entrypoint
# ------------------------------------------------------------

def main() -> None:  # pragma: no cover
    Launcher().mainloop()


if __name__ == "__main__":  # pragma: no cover
    main()

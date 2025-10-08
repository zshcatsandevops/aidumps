#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Samsoft Update Manager — Windows 11 Style
A modern Tkinter UI that wraps PowerShell/PSWindowsUpdate for:
- Checking Windows/Microsoft updates
- Downloading .msu packages to a local repo folder (best-effort; tries multiple PSWU verbs)
- Installing updates online (AcceptAll, with AutoReboot toggle)
- Viewing progress & logs

Notes:
- Elevation (UAC) is performed only on Windows when run as a script (__main__).
- The app is resilient to different PSWindowsUpdate versions by trying multiple command names.
- If PSWindowsUpdate isn't available, the app can install it (PSGallery trusted, NuGet provider).

Tested environment: Windows 10/11 with PowerShell 5+.
"""

import sys
import os
import platform
import ctypes
import subprocess
import threading
import time
import json
import textwrap
import queue
from pathlib import Path
from collections import deque
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font

APP_NAME = "Windows Update"
APP_VERSION = "1.1.0"

# ---------- Configuration ----------
BASE_DIR = os.getcwd()
REPO_DIR = os.path.join(BASE_DIR, "SamsoftRepo")
CONFIG_FILE = os.path.join(REPO_DIR, "config.json")
LOG_FILE = os.path.join(REPO_DIR, "update_manager.log")
os.makedirs(REPO_DIR, exist_ok=True)

# Windows 11 Color Palette
W11_COLORS = {
    'bg_primary': '#f3f3f3',
    'bg_secondary': '#ffffff',
    'bg_card': '#fafafa',
    'accent': '#0067c0',
    'accent_hover': '#005a9e',
    'text_primary': '#000000',
    'text_secondary': '#605e5c',
    'border': '#e5e5e5',
    'success': '#107c10',
    'warning': '#f7630c',
    'error': '#d13438'
}

# Default configuration
DEFAULT_CONFIG = {
    "repo_path": REPO_DIR,
    "update_categories": {
        "windows": True,
        "office": True,
        "dotnet": True,
        "vcredist": False
    },
    "auto_reboot": False,
    "dark_mode": False
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding="utf-8") as f:
                cfg = json.load(f)
                # ensure keys
                for k, v in DEFAULT_CONFIG.items():
                    if k not in cfg:
                        cfg[k] = v
                return cfg
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w', encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception:
        pass

# ---------- Helpers ----------
def is_windows():
    return os.name == "nt"

def is_admin_windows():
    if not is_windows():
        return False
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def elevate_windows_if_needed():
    """Re-launch this script elevated (UAC) if not admin."""
    if not is_windows():
        return
    if is_admin_windows():
        return
    try:
        params = " ".join([f'"{arg}"' for arg in sys.argv])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
        sys.exit(0)
    except Exception as e:
        messagebox.showerror(APP_NAME, f"Failed to elevate: {e}")
        sys.exit(1)

# ---------- Core App ----------
class Windows11UpdateManager:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME}")
        self.root.geometry("980x760")
        self.root.minsize(900, 640)

        self.config = load_config()
        self.repo_path = self.config.get("repo_path", REPO_DIR)
        os.makedirs(self.repo_path, exist_ok=True)

        # State
        self.pswindowsupdate_available = False
        self.checking_updates = False
        self.installing_updates = False
        self.downloading_updates = False
        self.updates_json_cache = []  # list of dicts from PS
        self.last_check_time = "Never"

        # Thread control
        self.log_queue = queue.Queue()
        self.running_threads = []
        self.stop_event = threading.Event()

        # Fonts & Styles
        self.setup_fonts()
        self.setup_styles()

        # Build UI
        self.create_ui()

        # Begin queue pump
        self.start_ui_loop()

        # Init checks
        if is_windows():
            threading.Thread(target=self.check_pswindowsupdate, daemon=True).start()
        else:
            self.log("Non-Windows OS detected. This tool requires Windows PowerShell.", "error")
            self.disable_all_actions()

    # ---------- Styles & Fonts ----------
    def setup_fonts(self):
        self.font_title = font.Font(family="Segoe UI", size=24, weight="normal")
        self.font_heading = font.Font(family="Segoe UI", size=16, weight="normal")
        self.font_body = font.Font(family="Segoe UI", size=11)
        self.font_body_bold = font.Font(family="Segoe UI", size=11, weight="bold")
        self.font_small = font.Font(family="Segoe UI", size=9)

    def setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Buttons
        style.configure("Accent.TButton",
                        font=("Segoe UI", 11, "bold"),
                        padding=8)
        style.map("Accent.TButton",
                  foreground=[('active', 'white')])

        # Cards
        style.configure("Card.TFrame", background=W11_COLORS['bg_card'])
        style.configure("Primary.TFrame", background=W11_COLORS['bg_primary'])
        style.configure("Secondary.TFrame", background=W11_COLORS['bg_secondary'])

        # Labels
        style.configure("Primary.TLabel", background=W11_COLORS['bg_primary'], foreground=W11_COLORS['text_primary'])
        style.configure("Card.TLabel", background=W11_COLORS['bg_card'], foreground=W11_COLORS['text_primary'])
        style.configure("Muted.TLabel", background=W11_COLORS['bg_card'], foreground=W11_COLORS['text_secondary'])

        # Progress
        style.configure("Modern.Horizontal.TProgressbar", thickness=10)

        self.root.configure(bg=W11_COLORS['bg_primary'])

    # ---------- UI ----------
    def create_ui(self):
        # Header
        header = ttk.Frame(self.root, style="Primary.TFrame")
        header.pack(fill="x", padx=16, pady=(16, 8))

        title = ttk.Label(header, text="Windows Update", style="Primary.TLabel", font=self.font_title)
        title.pack(side="left", padx=(0, 10))
        subtitle = ttk.Label(header, text=f"Samsoft Update Manager • v{APP_VERSION}", style="Primary.TLabel", font=self.font_small)
        subtitle.pack(side="left")

        # Right side header actions
        header_actions = ttk.Frame(header, style="Primary.TFrame")
        header_actions.pack(side="right")
        self.auto_reboot_var = tk.BooleanVar(value=self.config.get("auto_reboot", False))
        auto_reboot_chk = ttk.Checkbutton(header_actions, text="Auto reboot after install", variable=self.auto_reboot_var)
        auto_reboot_chk.pack(side="right", padx=8)

        # Status Card
        status_card = ttk.Frame(self.root, style="Card.TFrame")
        status_card.pack(fill="x", padx=16, pady=8, ipady=6)

        self.status_icon = ttk.Label(status_card, text="⟳", style="Card.TLabel", font=("Segoe UI Emoji", 24))
        self.status_icon.grid(row=0, column=0, rowspan=2, padx=12, pady=12, sticky="n")

        self.status_title = ttk.Label(status_card, text="Status", style="Card.TLabel", font=self.font_heading)
        self.status_title.grid(row=0, column=1, sticky="w", pady=(12, 2))

        self.status_subtitle = ttk.Label(status_card, text="Ready", style="Muted.TLabel", font=self.font_body)
        self.status_subtitle.grid(row=1, column=1, sticky="w", pady=(0, 12))

        # Progress
        progress_frame = ttk.Frame(self.root, style="Primary.TFrame")
        progress_frame.pack(fill="x", padx=16, pady=(0, 8))

        self.progress_label = ttk.Label(progress_frame, text="Idle", style="Primary.TLabel", font=self.font_body)
        self.progress_label.pack(side="left")
        self.progress = ttk.Progressbar(progress_frame, mode="determinate", maximum=100, style="Modern.Horizontal.TProgressbar")
        self.progress.pack(fill="x", expand=True, padx=(12, 0))
        self.progress['value'] = 0

        # Actions
        actions = ttk.Frame(self.root, style="Primary.TFrame")
        actions.pack(fill="x", padx=16, pady=8)

        self.check_button = ttk.Button(actions, text="Check for updates", style="Accent.TButton",
                                       command=lambda: self.run_in_thread(self.check_updates))
        self.check_button.pack(side="left", padx=(0, 8))

        self.download_button = ttk.Button(actions, text="Download updates", command=lambda: self.run_in_thread(self.download_updates))
        self.download_button.pack(side="left", padx=8)

        self.install_button = ttk.Button(actions, text="Install updates", command=lambda: self.run_in_thread(self.install_updates))
        self.install_button.pack(side="left", padx=8)

        open_repo_btn = ttk.Button(actions, text="Open repo folder", command=self.open_repo_folder)
        open_repo_btn.pack(side="left", padx=8)

        refresh_btn = ttk.Button(actions, text="Refresh status", command=lambda: self.set_status("Ready", "Press 'Check for updates' to begin", "⟳", W11_COLORS['accent']))
        refresh_btn.pack(side="left", padx=8)

        # Settings Card
        settings_card = ttk.LabelFrame(self.root, text="Settings", labelanchor="n")
        settings_card.pack(fill="x", padx=16, pady=8)

        p1 = ttk.Frame(settings_card)
        p1.pack(fill="x", pady=8, padx=8)
        ttk.Label(p1, text="Repository Path:").pack(side="left")
        self.repo_var = tk.StringVar(value=self.repo_path)
        repo_entry = ttk.Entry(p1, textvariable=self.repo_var, width=60)
        repo_entry.pack(side="left", padx=8)
        ttk.Button(p1, text="Browse…", command=self.choose_repo).pack(side="left")

        p2 = ttk.Frame(settings_card)
        p2.pack(fill="x", pady=8, padx=8)
        self.dark_var = tk.BooleanVar(value=self.config.get("dark_mode", False))
        dark_chk = ttk.Checkbutton(p2, text="Dark mode (basic)", variable=self.dark_var, command=self.toggle_dark_mode)
        dark_chk.pack(side="left", padx=(0, 12))

        ttk.Label(p2, text=f"PSWindowsUpdate:").pack(side="left")
        self.pswu_label = ttk.Label(p2, text="Checking…")
        self.pswu_label.pack(side="left", padx=(6, 0))
        ttk.Button(p2, text="(Re)Install PSWindowsUpdate", command=lambda: self.run_in_thread(self.ensure_module)).pack(side="left", padx=12)

        # Log Panel
        log_card = ttk.Frame(self.root, style="Card.TFrame")
        log_card.pack(fill="both", expand=True, padx=16, pady=(8, 16))

        log_header = ttk.Label(log_card, text="Activity log", style="Card.TLabel", font=self.font_body_bold)
        log_header.pack(anchor="w", padx=12, pady=(12, 0))

        self.log_text = tk.Text(log_card, height=16, wrap="word", bg="white", fg="black", font=("Consolas", 10))
        self.log_text.pack(fill="both", expand=True, padx=12, pady=12)
        self.log_text.insert("end", f"{APP_NAME} started.\n")
        self.log_text.config(state="disabled")

        # Init status
        self.set_status("Ready", "Press 'Check for updates' to begin", "⟳", W11_COLORS['accent'])

    # ---------- UI Utilities ----------
    def toggle_dark_mode(self):
        # Basic (text-widget) dark mode; ttk themes are limitd without custom themes.
        dm = self.dark_var.get()
        self.config["dark_mode"] = dm
        save_config(self.config)

        if dm:
            self.root.configure(bg="#1f1f1f")
            self.log_text.configure(bg="#0f0f0f", fg="#e0e0e0", insertbackground="#e0e0e0")
        else:
            self.root.configure(bg=W11_COLORS['bg_primary'])
            self.log_text.configure(bg="white", fg="black", insertbackground="black")

    def choose_repo(self):
        folder = filedialog.askdirectory(initialdir=self.repo_path, title="Choose repository folder")
        if folder:
            self.repo_path = folder
            self.repo_var.set(folder)
            self.config["repo_path"] = folder
            save_config(self.config)
            self.log(f"Repository set to: {folder}")

    def open_repo_folder(self):
        try:
            Path(self.repo_path).mkdir(parents=True, exist_ok=True)
            if is_windows():
                os.startfile(self.repo_path)  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", self.repo_path])
        except Exception as e:
            self.log(f"Failed to open folder: {e}", "error")

    def set_status(self, title, subtitle, icon, color_hex):
        # Update status card
        try:
            self.status_title.config(text=title, foreground=W11_COLORS['text_primary'])
            self.status_subtitle.config(text=subtitle, foreground=W11_COLORS['text_secondary'])
            self.status_icon.config(text=icon, foreground=color_hex)
        except Exception:
            pass

    def update_progress(self, value, text=None):
        try:
            self.progress['value'] = max(0, min(100, value))
            if text is not None:
                self.progress_label.config(text=text)
        except Exception:
            pass
        self.root.update_idletasks()

    def log(self, message, level="info"):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        prefix = {"info": "[*]", "warn": "[!]", "error": "[x]"}.get(level, "[*]")
        line = f"{ts} {prefix} {message}"
        # File
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass
        # Queue to UI
        self.log_queue.put(line)

    def start_ui_loop(self):
        """Pump the log queue to the text widget."""
        try:
            while True:
                line = self.log_queue.get_nowait()
                self.log_text.config(state="normal")
                self.log_text.insert("end", line + "\n")
                self.log_text.see("end")
                self.log_text.config(state="disabled")
        except queue.Empty:
            pass
        # Re-run
        self.root.after(80, self.start_ui_loop)

    def disable_all_actions(self):
        for w in (self.check_button, self.download_button, self.install_button):
            try:
                w.config(state="disabled")
            except Exception:
                pass

    def enable_actions(self):
        for w in (self.check_button, self.download_button, self.install_button):
            try:
                w.config(state="normal")
            except Exception:
                pass

    def run_in_thread(self, target):
        t = threading.Thread(target=target, daemon=True)
        t.start()
        self.running_threads.append(t)

    # ---------- PowerShell ----------
    def run_powershell(self, command, capture_output=True, timeout=7200):
        if not is_windows():
            return "", "Not running on Windows", 1
        try:
            # Make sure each call runs in hidden window, bypassing policy
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

            ps_cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-WindowStyle", "Hidden",
                "-Command",
                command
            ]
            completed = subprocess.run(
                ps_cmd,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                startupinfo=startupinfo
            )
            stdout = completed.stdout.strip() if completed.stdout else ""
            stderr = completed.stderr.strip() if completed.stderr else ""
            return stdout, stderr, completed.returncode
        except subprocess.TimeoutExpired:
            return "", "PowerShell command timed out", 1
        except Exception as e:
            return "", f"PowerShell error: {e}", 1

    def check_pswindowsupdate(self):
        self.log("Checking for PSWindowsUpdate module...")
        out, err, code = self.run_powershell("Get-Module -ListAvailable -Name PSWindowsUpdate | Select-Object Name,Version | ConvertTo-Json")
        if code != 0:
            self.pswindowsupdate_available = False
            self.pswu_label.config(text="Not found")
            self.log(f"PSWindowsUpdate not found ({err})", "warn")
            return

        if not out:
            self.pswindowsupdate_available = False
            self.pswu_label.config(text="Not found")
            self.log("PSWindowsUpdate not found")
            return

        self.pswindowsupdate_available = True
        self.pswu_label.config(text="Available")
        self.log("PSWindowsUpdate is available")

    def ensure_module(self):
        """Install PSWindowsUpdate if missing. Safe to run multiple times."""
        if self.pswindowsupdate_available:
            self.log("PSWindowsUpdate already available")
            return True
        self.log("Installing PSWindowsUpdate (from PSGallery)...")
        install_cmd = textwrap.dedent(r"""
            try {
                Set-PSRepository -Name PSGallery -InstallationPolicy Trusted -ErrorAction SilentlyContinue | Out-Null
                Install-PackageProvider -Name NuGet -Force -ErrorAction SilentlyContinue | Out-Null
                Install-Module PSWindowsUpdate -Force -AcceptLicense -Scope AllUsers -ErrorAction Stop
                Write-Output "OK"
            } catch {
                Write-Error $_.Exception.Message
            }
        """)
        out, err, code = self.run_powershell(install_cmd)
        if "OK" in out and code == 0:
            self.pswindowsupdate_available = True
            self.pswu_label.config(text="Available")
            self.log("PSWindowsUpdate installed successfully")
            return True
        self.log(f"Failed to install PSWindowsUpdate: {err or out}", "error")
        return False

    # ---------- Update Operations ----------
    def check_updates(self):
        if self.checking_updates or self.installing_updates or self.downloading_updates:
            return
        self.checking_updates = True
        self.update_progress(5, "Checking for updates…")
        self.set_status("Checking for updates…", "Contacting Windows/Microsoft Update", "⟳", W11_COLORS['accent'])
        self.disable_all_actions()
        self.log("Checking for updates online...")

        if not self.pswindowsupdate_available:
            if not self.ensure_module():
                self.update_progress(0, "Ready")
                self.set_status("PSWindowsUpdate required", "Failed to install module", "✕", W11_COLORS['error'])
                self.checking_updates = False
                self.enable_actions()
                return

        # Try a robust query that works across PSWU versions
        ps = textwrap.dedent(r"""
            try {
                Import-Module PSWindowsUpdate -ErrorAction Stop
                $updates = @()
                if (Get-Command Get-WindowsUpdate -ErrorAction SilentlyContinue) {
                    $updates = Get-WindowsUpdate -MicrosoftUpdate -IgnoreReboot -Verbose:$false
                } elseif (Get-Command Get-WUList -ErrorAction SilentlyContinue) {
                    $updates = Get-WUList -MicrosoftUpdate -Verbose:$false
                }
                if (-not $updates) { $updates = @() }
                $out = $updates | Select-Object Title, KB, KBArticleIDs, Size, DownloadSize, MsrcSeverity, RebootRequired, Categories, UpdateID
                $out | ConvertTo-Json -Depth 5
            } catch {
                Write-Error $_.Exception.Message
            }
        """)
        out, err, code = self.run_powershell(ps, timeout=900)

        self.last_check_time = time.strftime("%I:%M %p, %B %d, %Y")
        items = []
        if code == 0 and out.strip().startswith("["):
            try:
                items = json.loads(out)
                if isinstance(items, dict):
                    items = [items]
            except Exception as e:
                self.log(f"JSON parse error: {e}", "error")
        else:
            # Fallback heuristic count
            if code != 0:
                self.log(f"Check failed: {err or out}", "error")

        count = len(items)
        self.updates_json_cache = items

        # Log first few
        if count > 0:
            self.log(f"Found {count} update(s):")
            for u in items[:10]:
                title = u.get("Title") or "(untitled)"
                kb = u.get("KB") or u.get("KBArticleIDs")
                self.log(f" - {title} | KB: {kb}")
            self.set_status(f"{count} update(s) available", f"Last checked: {self.last_check_time}", "!", W11_COLORS['warning'])
            self.update_progress(100, "Updates found")
        else:
            self.log("Your device appears up to date")
            self.set_status("You're up to date", f"Last checked: {self.last_check_time}", "✓", W11_COLORS['success'])
            self.update_progress(100, "No updates available")

        time.sleep(0.2)
        self.update_progress(0, "Ready")
        self.checking_updates = False
        self.enable_actions()

    def download_updates(self):
        if self.downloading_updates or self.checking_updates or self.installing_updates:
            return
        self.downloading_updates = True
        self.disable_all_actions()
        self.update_progress(5, "Preparing download…")
        self.set_status("Downloading…", "Fetching .msu where possible", "⭳", W11_COLORS['accent'])
        self.log(f"Downloading updates into: {self.repo_path}")

        if not self.pswindowsupdate_available:
            if not self.ensure_module():
                self.set_status("PSWindowsUpdate required", "Failed to install module", "✕", W11_COLORS['error'])
                self.downloading_updates = False
                self.enable_actions()
                return

        # Ensure download dir
        download_dir = os.path.join(self.repo_path, "Downloads")
        os.makedirs(download_dir, exist_ok=True)

        # If we don't have a cache from 'check', fetch a simple KB list
        kbs = self._collect_kb_list()
        if not kbs:
            self.log("No KB IDs available for offline download. Try 'Check for updates' first.", "warn")
            self.update_progress(0, "Ready")
            self.downloading_updates = False
            self.enable_actions()
            return

        self.log(f"Attempting offline download for {len(kbs)} KB(s)…")
        ok = 0
        for i, kb in enumerate(kbs, start=1):
            self.update_progress(int((i-1)/max(1,len(kbs))*90) + 10, f"Downloading {kb} ({i}/{len(kbs)})…")
            ps = textwrap.dedent(fr"""
                try {{
                    Import-Module PSWindowsUpdate -ErrorAction Stop
                    $dest = "{download_dir}"
                    New-Item -ItemType Directory -Force -Path $dest | Out-Null

                    if (Get-Command Get-WUOfflineMSU -ErrorAction SilentlyContinue) {{
                        Get-WUOfflineMSU -KBArticleID "{kb}" -DestinationDirectory $dest -Verbose:$false | Out-Null
                        Write-Output "OK"
                    }}
                    elseif (Get-Command Save-WindowsUpdate -ErrorAction SilentlyContinue) {{
                        Save-WindowsUpdate -KBArticleID "{kb}" -DownloadFolder $dest -Verbose:$false | Out-Null
                        Write-Output "OK"
                    }}
                    else {{
                        # Fallback: queue the download using built-in cache (no custom dest)
                        if (Get-Command Get-WindowsUpdate -ErrorAction SilentlyContinue) {{
                            Get-WindowsUpdate -MicrosoftUpdate -Download -AcceptAll -Verbose:$false | Out-Null
                            Write-Output "OK-NOCUSTOM"
                        }} elseif (Get-Command Get-WUInstall -ErrorAction SilentlyContinue) {{
                            Get-WUInstall -MicrosoftUpdate -Download -AcceptAll -Verbose:$false | Out-Null
                            Write-Output "OK-NOCUSTOM"
                        }} else {{
                            Write-Output "NO-CMD"
                        }}
                    }}
                }} catch {{
                    Write-Error $_.Exception.Message
                }}
            """)
            out, err, code = self.run_powershell(ps, timeout=3600)
            if "OK" in out or "OK-NOCUSTOM" in out:
                ok += 1
                self.log(f"Downloaded/queued {kb}")
            else:
                self.log(f"Failed to download {kb}: {err or out}", "warn")

        self.update_progress(100, "Download complete")
        self.set_status("Download complete", f"Success: {ok}/{len(kbs)}", "✓", W11_COLORS['success'])
        time.sleep(0.2)
        self.update_progress(0, "Ready")
        self.downloading_updates = False
        self.enable_actions()

    def _collect_kb_list(self):
        """Return a list of KB IDs from cache or PowerShell."""
        # Prefer cached objects
        kbs = []
        for u in self.updates_json_cache:
            if u.get("KB"):
                if isinstance(u["KB"], list):
                    kbs.extend(u["KB"])
                else:
                    kbs.append(str(u["KB"]))
            elif u.get("KBArticleIDs"):
                if isinstance(u["KBArticleIDs"], list):
                    kbs.extend(u["KBArticleIDs"])
                else:
                    kbs.append(str(u["KBArticleIDs"]))
        kbs = [f"KB{str(k).lstrip('KB').strip()}" for k in kbs]  # normalize
        kbs = [k for k in kbs if k and k.lower().startswith("kb")]
        if kbs:
            return list(dict.fromkeys(kbs))  # dedupe, preserve order

        # Fallback: quick PS to pull KBs only
        ps = textwrap.dedent(r"""
            try {
                Import-Module PSWindowsUpdate -ErrorAction Stop
                $updates = @()
                if (Get-Command Get-WindowsUpdate -ErrorAction SilentlyContinue) {
                    $updates = Get-WindowsUpdate -MicrosoftUpdate -IgnoreReboot -Verbose:$false
                } elseif (Get-Command Get-WUList -ErrorAction SilentlyContinue) {
                    $updates = Get-WUList -MicrosoftUpdate -Verbose:$false
                }
                $kbs = @()
                foreach ($u in $updates) {
                    if ($u.KB) { $kbs += $u.KB }
                    elseif ($u.KBArticleIDs) { $kbs += $u.KBArticleIDs }
                }
                $kbs | ConvertTo-Json -Depth 3
            } catch {
                Write-Error $_.Exception.Message
            }
        """)
        out, err, code = self.run_powershell(ps, timeout=600)
        try:
            arr = json.loads(out) if out else []
            if isinstance(arr, list):
                return [f"KB{str(k).lstrip('KB').strip()}" for k in arr if k]
        except Exception:
            pass
        return []

    def install_updates(self):
        if self.installing_updates or self.downloading_updates or self.checking_updates:
            return
        self.installing_updates = True
        self.disable_all_actions()
        self.update_progress(10, "Installing updates…")
        self.set_status("Installing…", "Applying updates (this can take a while)", "🛠", W11_COLORS['accent'])
        self.log("Installing updates...")

        if not self.pswindowsupdate_available:
            if not self.ensure_module():
                self.set_status("PSWindowsUpdate required", "Failed to install module", "✕", W11_COLORS['error'])
                self.installing_updates = False
                self.enable_actions()
                return

        reboot_param = "-AutoReboot" if self.auto_reboot_var.get() else "-IgnoreReboot"
        ps = textwrap.dedent(fr"""
            try {{
                Import-Module PSWindowsUpdate -ErrorAction Stop

                if (Get-Command Get-WindowsUpdate -ErrorAction SilentlyContinue) {{
                    Get-WindowsUpdate -MicrosoftUpdate -Install -AcceptAll {reboot_param} -Verbose:$false | Out-Null
                    Write-Output "OK"
                }} elseif (Get-Command Get-WUInstall -ErrorAction SilentlyContinue) {{
                    Get-WUInstall -MicrosoftUpdate -Install -AcceptAll {reboot_param} -Verbose:$false | Out-Null
                    Write-Output "OK"
                }} else {{
                    Write-Output "NO-CMD"
                }}
            }} catch {{
                Write-Error $_.Exception.Message
            }}
        """)
        out, err, code = self.run_powershell(ps, capture_output=True, timeout=4*3600)
        if "OK" in out and code == 0:
            self.log("Updates installed successfully")
            self.set_status("Updates installed", "Some updates may require reboot", "✓", W11_COLORS['success'])
            self.update_progress(100, "Install complete")
        else:
            self.log(f"Installation failed: {err or out}", "error")
            self.set_status("Installation failed", "See activity log for details", "✕", W11_COLORS['error'])
            self.update_progress(20, "Install failed")

        time.sleep(0.3)
        self.update_progress(0, "Ready")
        self.installing_updates = False
        self.enable_actions()

    # ---------- Cleanup ----------
    def cleanup(self):
        self.stop_event.set()
        # Optionally join threads for a short time
        deadline = time.time() + 2.0
        for t in list(self.running_threads):
            rem = deadline - time.time()
            if rem <= 0:
                break
            try:
                t.join(timeout=max(0.05, rem))
            except Exception:
                pass
        save_config(self.config)
        self.log("Shutting down...")

# ---------- Main ----------
def main():
    if not is_windows():
        print("This tool must be run on Windows.")
        # Still start Tk so user can read the message if double-clicked outside console
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(APP_NAME, "This tool must be run on Windows.")
        return

    # Elevate if needed
    elevate_windows_if_needed()

    # Launch UI
    root = tk.Tk()
    root.title(APP_NAME)
    app = Windows11UpdateManager(root)

    def on_closing():
        try:
            app.cleanup()
        finally:
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()

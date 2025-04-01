#!/usr/bin/env python3
"""
test_fixed.py (EmulAI O1 Pro v2.2) - Patched for Portable Mode

This version ensures:
- All RetroArch and core files go into the script's folder
- Avoids system root or "C:/" issues on Windows
- Fully portable & sandbox-safe

DONOT THINK JUST VIBE.
"""

import os
import sys
import shutil
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import random

try:
    import requests
except ImportError:
    sys.exit("ERROR: The 'requests' package is required. Install it using 'pip install requests'.")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(SCRIPT_DIR, "emulai_runtime")

LINUX_RETROARCH_URL = "https://buildbot.libretro.com/stable/1.15.0/linux/x86_64/RetroArch.7z"
WIN_RETROARCH_URL = "https://buildbot.libretro.com/stable/1.15.0/windows/x86_64/RetroArch.7z"
LINUX_PARALLEL_URL = "https://buildbot.libretro.com/nightly/linux/x86_64/latest/parallel_n64_libretro.so.zip"
WIN_PARALLEL_URL = "https://buildbot.libretro.com/nightly/windows/x86_64/latest/parallel_n64_libretro.dll.zip"

RETROARCH_EXE_NAME = "retroarch.exe" if os.name == "nt" else "retroarch"
LINUX_CORE_FILENAME = "parallel_n64_libretro.so"
WIN_CORE_FILENAME = "parallel_n64_libretro.dll"

def is_windows():
    return os.name == "nt" or sys.platform.startswith("win")

def which(cmd):
    path_ext = os.environ.get("PATHEXT", "").split(os.pathsep) if is_windows() else [""]
    for p in os.environ.get("PATH", "").split(os.pathsep):
        for ext in path_ext:
            exe_full = os.path.join(p, cmd + ext)
            if os.path.isfile(exe_full) and os.access(exe_full, os.X_OK):
                return exe_full
    return None

def unzip_file(zip_path, extract_to):
    import zipfile
    if zip_path.lower().endswith(".zip"):
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(extract_to)
    elif zip_path.lower().endswith(".7z"):
        try:
            import py7zr
            with py7zr.SevenZipFile(zip_path, mode='r') as archive:
                archive.extractall(path=extract_to)
        except ImportError:
            seven_zip = which("7z") or which("7za")
            if not seven_zip:
                raise RuntimeError("7z archive but no py7zr or system 7z installed.")
            subprocess.check_call([seven_zip, "x", zip_path, f"-o{extract_to}"])
    else:
        raise RuntimeError(f"Unknown archive format: {zip_path}")

def download_file(url, dest_path):
    print(f"Downloading from {url} -> {dest_path}")
    resp = requests.get(url, stream=True)
    resp.raise_for_status()
    with open(dest_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    print("Download complete.")

def ensure_retroarch_installed():
    retro_path = os.path.join(DOWNLOAD_DIR, RETROARCH_EXE_NAME)
    if os.path.isfile(retro_path):
        return retro_path
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    url = WIN_RETROARCH_URL if is_windows() else LINUX_RETROARCH_URL
    archive_name = os.path.join(DOWNLOAD_DIR, os.path.basename(url))
    download_file(url, archive_name)
    unzip_file(archive_name, DOWNLOAD_DIR)
    for root, dirs, files in os.walk(DOWNLOAD_DIR):
        if RETROARCH_EXE_NAME in files:
            extracted = os.path.join(root, RETROARCH_EXE_NAME)
            shutil.copy2(extracted, retro_path)
            return retro_path
    raise RuntimeError("Could not find RetroArch executable after extract.")

def ensure_parallel_n64_installed():
    core_name = WIN_CORE_FILENAME if is_windows() else LINUX_CORE_FILENAME
    core_path = os.path.join(DOWNLOAD_DIR, core_name)
    if os.path.isfile(core_path):
        return core_path
    url = WIN_PARALLEL_URL if is_windows() else LINUX_PARALLEL_URL
    archive_name = os.path.join(DOWNLOAD_DIR, os.path.basename(url))
    download_file(url, archive_name)
    unzip_file(archive_name, DOWNLOAD_DIR)
    for root, dirs, files in os.walk(DOWNLOAD_DIR):
        if core_name in files:
            found = os.path.join(root, core_name)
            shutil.copy2(found, core_path)
            return core_path
    raise RuntimeError("Could not find ParaLLEl core after extract.")

def log_emulore_event(frame_count):
    if frame_count % 333 == 0:
        print("[EmulAI Core]", random.choice([
            "Luigi is active.",
            "Save Slot 5: [REDACTED]",
            "Castle Memory Layer: Corrupted",
            "Instruction echo detected...",
            "EmulAI is watching you."
        ]))

class EmulAIParallel:
    def __init__(self, master):
        self.master = master
        self.master.geometry("600x400")
        self.master.title("EmulAI O1 Pro Portable")
        self.master.resizable(False, False)
        try:
            self.retroarch_path = ensure_retroarch_installed()
            self.parallel_core_path = ensure_parallel_n64_installed()
        except Exception as e:
            messagebox.showerror("Auto-Setup Error", str(e))
            self.retroarch_path = None
            self.parallel_core_path = None

        menu_bar = tk.Menu(self.master)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open ROM...", command=self.open_rom)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.master.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)
        self.master.config(menu=menu_bar)

        self.label = tk.Label(self.master,
            text="Welcome to EmulAI Portable\nClick File > Open ROM...\nDONOT THINK JUST VIBE.",
            bg="black", fg="white", font=("Arial", 12),
            width=60, height=10, justify="center"
        )
        self.label.pack(padx=10, pady=10, fill="both", expand=True)

        self.frame_count = 0
        self.running = False
        self.update_lore()

    def open_rom(self):
        if not self.retroarch_path or not self.parallel_core_path:
            messagebox.showerror("Error", "RetroArch or ParaLLEl core missing.")
            return
        rom_path = filedialog.askopenfilename(
            title="Open N64 ROM",
            filetypes=[("N64 ROMs", "*.n64 *.z64"), ("All files", "*.*")]
        )
        if not rom_path:
            return
        try:
            subprocess.Popen([self.retroarch_path, "-L", self.parallel_core_path, rom_path])
            self.running = True
            self.label.config(text=f"Running: {os.path.basename(rom_path)}")
        except Exception as e:
            messagebox.showerror("Launch Failed", str(e))

    def update_lore(self):
        if self.running:
            self.frame_count += 1
            log_emulore_event(self.frame_count)
        self.master.after(1000, self.update_lore)

def main():
    root = tk.Tk()
    EmulAIParallel(root)
    root.mainloop()

if __name__ == "__main__":
    main()

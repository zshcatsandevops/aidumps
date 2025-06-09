#!/usr/bin/env python3
"""
Minecraft Launcher with Offline/Online (TLauncher) authentication support
Supports Vanilla, Forge, and Fabric mod loaders
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
import json
import os
import re
import uuid
import subprocess
import requests
import minecraft_launcher_lib

# --- Constants ---
LAUNCHER_NAME = "Minecraft Launcher"
LAUNCHER_VERSION = "v2.0"
CONFIG_FILE = "launcher_config.json"
AUTHLIB_URL = "https://authlib-injector.yushi.moe/artifact/latest/authlib-injector.jar"
HEADERS = {'Content-Type': 'application/json'}

class MinecraftLauncher:
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

        self._setup_ui()
        self._populate_versions()
        self.root.after(100, self._process_queue)
        self._load_config()  # Load config after UI is built
        self._toggle_auth_mode()

    def _setup_ui(self):
        self.root.title(f"{LAUNCHER_NAME} {LAUNCHER_VERSION}")
        self.root.geometry("400x560")
        self.root.resizable(False, False)

        # --- Style Configuration ---
        style = ttk.Style()
        self.root.configure(bg="#2B2B2B")
        style.theme_use('clam')
        style.configure('.', background="#2B2B2B", foreground="#A9B7C6", font=("Segoe UI", 10))
        for widget in ['TFrame','TLabel','TRadiobutton', 'TCheckbutton']:
            style.configure(widget, background="#2B2B2B", foreground="#A9B7C6")
        style.map('TRadiobutton', background=[('active', '#3C3F41')])
        style.configure('TButton', background="#0078D7", foreground='white', font=("Segoe UI",12,'bold'), borderwidth=0)
        style.map('TButton', background=[('active','#005a9e'),('disabled','#555555')])
        style.configure('TEntry', fieldbackground="#3C3F41", foreground='white', borderwidth=1, insertcolor='white')
        style.configure('TCombobox', fieldbackground="#3C3F41", background="#3C3F41", foreground='white', arrowcolor='white', borderwidth=1)
        style.configure('TProgressbar', background="#0078D7", troughcolor="#3C3F41")
        self.root.option_add('*TCombobox*Listbox.background','#3C3F41')
        self.root.option_add('*TCombobox*Listbox.foreground','white')

        frm = ttk.Frame(self.root, padding="20")
        frm.pack(expand=True, fill='both')

        ttk.Label(frm, text=LAUNCHER_NAME, font=("Segoe UI", 24, 'bold'), foreground='white').pack(pady=(0, 15))

        # --- Auth Controls ---
        auth_frm = ttk.Frame(frm)
        auth_frm.pack(fill='x', pady=(0, 10))
        ttk.Radiobutton(auth_frm, text="Offline", variable=self.auth_mode, value="Offline", command=self._toggle_auth_mode).pack(side='left', padx=(0, 10))
        ttk.Radiobutton(auth_frm, text="Online (Cracked)", variable=self.auth_mode, value="Online", command=self._toggle_auth_mode).pack(side='left')

        self.username_lbl = ttk.Label(frm, text='Username')
        self.username_lbl.pack(anchor='w')
        self.username_entry = ttk.Entry(frm, width=30, textvariable=self.username_var)
        self.username_entry.pack(fill='x', pady=(5, 10))

        self.password_lbl = ttk.Label(frm, text='Password')
        self.password_entry = ttk.Entry(frm, width=30, show='*', textvariable=self.password_var)

        # --- Version & Mod Controls ---
        ttk.Label(frm, text='Version').pack(anchor='w', pady=(5, 0))
        self.version_combo = ttk.Combobox(frm, state='readonly')
        self.version_combo.pack(fill='x', pady=(5, 10))

        ttk.Label(frm, text='Mod Loader').pack(anchor='w', pady=(5, 0))
        mod_frm = ttk.Frame(frm)
        mod_frm.pack(fill='x', pady=(5,10))
        ttk.Radiobutton(mod_frm, text="Vanilla", variable=self.mod_choice, value="Vanilla").pack(side='left', padx=(0, 10))
        ttk.Radiobutton(mod_frm, text="Forge", variable=self.mod_choice, value="Forge").pack(side='left', padx=(0, 10))
        ttk.Radiobutton(mod_frm, text="Fabric", variable=self.mod_choice, value="Fabric").pack(side='left')

        # --- Launch & Status Controls ---
        ttk.Checkbutton(frm, text='Keep launcher open after launch', variable=self.keep_open).pack(anchor='w', pady=(5, 15))

        self.launch_btn = ttk.Button(frm, text='LAUNCH', command=self._start_launch_thread)
        self.launch_btn.pack(fill='x', ipady=10)

        self.progress = ttk.Progressbar(frm, mode='determinate', maximum=100)
        self.progress.pack(fill='x', pady=(15, 5))

        self.status_lbl = ttk.Label(frm, text='Select auth mode and version.', font=("Segoe UI", 9), foreground='#808080', wraplength=350)
        self.status_lbl.pack(pady=(5, 0))

    # --- Configuration Management ---
    def _load_config(self):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            self.username_var.set(config.get('username', 'Player'))
            # For security, we don't load passwords
            self.auth_mode.set(config.get('auth_mode', 'Offline'))
            self.keep_open.set(config.get('keep_open', False))
            self.mod_choice.set(config.get('mod_choice', 'Vanilla'))
            # Set version after versions are populated
            last_version = config.get('last_version')
            if last_version:
                self.root.after(1000, lambda: self.version_combo.set(last_version))  # Delay to allow population
        except (FileNotFoundError, json.JSONDecodeError):
            self.username_var.set('Player')  # Default on first run

    def _save_config(self):
        config = {
            'username': self.username_var.get(),
            # Not saving password for security
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
            self.username_lbl.config(text='Username')
            self.password_lbl.pack_forget()
            self.password_entry.pack_forget()
        else:
            self.username_lbl.config(text='Username (any)')
            self.password_lbl.pack(anchor='w', pady=(5, 0))
            self.password_entry.pack(fill='x', pady=(5, 10))
            # Update password label to indicate it's not checked
            self.password_lbl.config(text='Password (any)')

    def _process_queue(self):
        """Process status updates from worker threads (60 FPS smooth updates)"""
        try:
            while True:  # Process all pending messages
                msg, fin, err, prog = self.status_queue.get_nowait()
                if msg:
                    self.status_lbl.config(text=msg, foreground='#FF6B6B' if err else '#A9B7C6')
                if prog is not None:
                    self.progress['value'] = prog
                if fin:
                    self.launch_btn.config(state='normal', text='LAUNCH')
                    self.progress['value'] = 0
        except queue.Empty:
            pass
        self.root.after(16, self._process_queue)  # ~60 FPS (16ms)

    def _update_status(self, text, *, final=False, error=False, prog=None):
        self.status_queue.put((text, final, error, prog))

    def _populate_versions(self):
        self._update_status('Fetching version list…')
        def worker():
            try:
                versions = [v['id'] for v in minecraft_launcher_lib.utils.get_version_list() if v['type'] == 'release']
                versions.sort(key=lambda s: [int(p) if p.isdigit() else p for p in s.split('.')], reverse=True)
                latest_stable = minecraft_launcher_lib.utils.get_latest_version()['release']
                self.root.after(0, lambda: self.version_combo.configure(values=versions))
                if not self.version_combo.get() and latest_stable in versions:
                    self.root.after(0, lambda: self.version_combo.set(latest_stable))
                self._update_status('Ready.', final=True)
            except Exception as e:
                self._update_status(f'Error fetching versions: {e}', final=True, error=True)
        threading.Thread(target=worker, daemon=True).start()

    # --- Launch Logic ---
    def _start_launch_thread(self):
        self.launch_btn.config(state='disabled', text='WORKING…')
        self.progress['value'] = 0
        threading.Thread(target=self._launch_minecraft, daemon=True).start()

    @staticmethod
    def _is_valid_username(name):
        return bool(re.match(r'^[A-Za-z0-9_]{3,16}$', name))

    def _tlauncher_login(self, user, pw):
        """Simulate TLauncher login - accepts any credentials"""
        # Generate consistent UUID from username (so same username = same UUID)
        user_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f'tlauncher:{user}')).replace('-', '')
        
        # Simulate successful authentication response
        return {
            'accessToken': str(uuid.uuid4()).replace('-', ''),
            'clientToken': str(uuid.uuid4()).replace('-', ''),
            'selectedProfile': {
                'name': user,
                'id': user_uuid
            },
            'user': {
                'username': user,
                'id': user_uuid
            }
        }

    def _ensure_authlib_present(self):
        """Downloads TLauncher's authlib if not already present."""
        if os.path.exists(self.authlib_path):
            return self.authlib_path

        response = messagebox.askyesno(
            "Download Required",
            "TLauncher skin support requires downloading an additional component (authlib).\n\n"
            "Do you want to download it now? (about 300KB)\n\n"
            "You can still play without it, but skins won't be visible."
        )
        
        if not response:
            return None

        self._update_status("Downloading TLauncher skin agent...")
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
                            self._update_status(f"Downloading agent: {int(prog)}%", prog=prog)
            self._update_status("Agent download complete.")
            return self.authlib_path
        except Exception as e:
            self._update_status(f"Authlib download failed: {e}", error=True)
            if os.path.exists(self.authlib_path):
                os.remove(self.authlib_path)  # Clean up partial download
            return None

    def _launch_minecraft(self):
        self._save_config()  # Save current settings before launch

        base_version = self.version_combo.get()
        if not base_version:
            self._update_status('You must select a version.', final=True, error=True)
            return

        options = {
            'jvmArguments': [
                '-Xms2G', '-Xmx4G', '-XX:+UnlockExperimentalVMOptions', '-XX:+UseG1GC',
                '-XX:G1NewSizePercent=20', '-XX:G1ReservePercent=20', '-XX:MaxGCPauseMillis=50'
            ]
        }
        authlib_agent_path = None

        # --- 1. Authentication ---
        if self.auth_mode.get() == 'Offline':
            username = self.username_var.get().strip()
            if not self._is_valid_username(username):
                self._update_status('Username must be 3-16 chars (A-Z,a-z,0-9,_).', final=True, error=True)
                return
            options.update({'username': username, 'uuid': str(uuid.uuid3(uuid.NAMESPACE_DNS, f'Offline:{username}')), 'token': '0'})
            self._update_status(f'Offline profile: {username}')
        else:  # Online (Cracked/TLauncher mode)
            username = self.username_var.get().strip()
            password = self.password_var.get()
            
            # Accept any username/password combination
            if not username:
                self._update_status('Username is required.', final=True, error=True)
                return
            
            # For cracked mode, we don't validate credentials
            self._update_status(f'Logging in as {username} (cracked mode)...')
            
            try:
                # Generate fake but consistent auth data
                data = self._tlauncher_login(username, password)
                
                # Extract profile information
                profile = data.get('selectedProfile')
                profile_uuid = profile['id'].replace('-', '')
                
                options.update({
                    'username': profile['name'],
                    'uuid': profile_uuid,
                    'token': data.get('accessToken', '0')
                })
                
                self._update_status(f"Logged in as {profile['name']} (cracked)")
                
                # Try to enable skins if authlib is available
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
                self._update_status(f'Login error: {e}', final=True, error=True)
                return

        # --- 2. Version & Mod Installation ---
        target_version_id = base_version
        mod_system = self.mod_choice.get()
        callback_dict = {
            'setStatus': lambda s: self._update_status(s),
            'setProgress': lambda v: self._update_status('', prog=v),
            'setMax': lambda _: None  # Ignore max value
        }

        try:
            self._update_status(f'Verifying base version {base_version}...')
            minecraft_launcher_lib.install.install_minecraft_version(base_version, self.minecraft_directory, callback=callback_dict)

            if mod_system == 'Forge':
                self._update_status(f'Finding latest Forge for {base_version}...')
                forge_version = minecraft_launcher_lib.forge.find_latest_version(base_version)
                if not forge_version:
                    raise RuntimeError(f"No compatible Forge version found for {base_version}")
                
                target_version_id = f"{base_version}-forge-{forge_version}"
                self._update_status(f"Installing Forge {forge_version}...")
                minecraft_launcher_lib.forge.install_forge_version(forge_version, self.minecraft_directory, callback=callback_dict)

            elif mod_system == 'Fabric':
                self._update_status(f'Installing Fabric for {base_version}...')
                # Installs the latest loader for the given MC version
                minecraft_launcher_lib.fabric.install_fabric(base_version, self.minecraft_directory, callback=callback_dict)
                # We need to find the exact version ID it created
                installed_versions = minecraft_launcher_lib.utils.get_installed_versions(self.minecraft_directory)
                fabric_versions = [v for v in installed_versions if v["id"].startswith(f"fabric-loader-") and base_version in v["id"]]
                if not fabric_versions:
                    raise RuntimeError("Fabric installation failed or was not found.")
                target_version_id = fabric_versions[0]["id"]  # Assume the first one is correct
    
            # --- 3. Launch ---
            self._update_status(f'Launching {target_version_id} as {options["username"]}…')
            minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(target_version_id, self.minecraft_directory, options)
            subprocess.Popen(minecraft_command)
            
            self._update_status('Game has launched!', final=not self.keep_open.get())
            if not self.keep_open.get():
                self.root.after(3000, self.root.destroy)

        except Exception as e:
            self._update_status(f'Launch Error: {e}', final=True, error=True)
            messagebox.showerror('Launch Error', f'A critical error occurred:\n\n{e}')

    def run(self):
        """Start the launcher GUI"""
        self.root.mainloop()


def main():
    """Entry point for the launcher"""
    try:
        launcher = MinecraftLauncher()
        launcher.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        messagebox.showerror("Fatal Error", f"Could not start launcher:\n\n{e}")


if __name__ == "__main__":
    main()

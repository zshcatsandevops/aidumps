#!/usr/bin/env python3
"""
SamsoftEmu NES v1.0 (Tkinter GUI Frontend)
Frontend for a future FCEUX-class emulator.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

class SamsoftEmuNESGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SamsoftEmu NES v1.0")
        self.root.geometry("800x600")
        self.root.configure(bg="#1e1e1e")

        # Emulator state placeholders
        self.rom_path = None
        self.is_running = False
        self.version = "1.0"

        # UI setup
        self.create_menu()
        self.create_toolbar()
        self.create_statusbar()
        self.create_console()

    def create_menu(self):
        menubar = tk.Menu(self.root, bg="#2d2d2d", fg="white", tearoff=0)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open ROM", command=self.open_rom)
        file_menu.add_command(label="Reset Emulator", command=self.reset_emulator)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Debugger", command=self.launch_debugger)
        tools_menu.add_command(label="Cheats", command=self.launch_cheats)
        tools_menu.add_command(label="TAS Tools", command=self.launch_tas_tools)
        menubar.add_cascade(label="Tools", menu=tools_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def create_toolbar(self):
        toolbar = tk.Frame(self.root, bg="#2d2d2d", height=40)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        open_btn = tk.Button(toolbar, text="📂 Open ROM", command=self.open_rom,
                             bg="#3a3a3a", fg="white", relief=tk.FLAT, cursor="hand2")
        open_btn.pack(side=tk.LEFT, padx=5, pady=5)

        run_btn = tk.Button(toolbar, text="▶ Run", command=self.run_emulator,
                            bg="#4CAF50", fg="white", relief=tk.FLAT, cursor="hand2")
        run_btn.pack(side=tk.LEFT, padx=5, pady=5)

        reset_btn = tk.Button(toolbar, text="⟳ Reset", command=self.reset_emulator,
                              bg="#FF9800", fg="white", relief=tk.FLAT, cursor="hand2")
        reset_btn.pack(side=tk.LEFT, padx=5, pady=5)

        stop_btn = tk.Button(toolbar, text="■ Stop", command=self.stop_emulator,
                             bg="#f44336", fg="white", relief=tk.FLAT, cursor="hand2")
        stop_btn.pack(side=tk.LEFT, padx=5, pady=5)

    def create_statusbar(self):
        self.status_var = tk.StringVar()
        self.status_var.set("Ready – No ROM loaded")
        status_bar = tk.Label(self.root, textvariable=self.status_var,
                              bd=1, relief=tk.SUNKEN, anchor=tk.W,
                              bg="#2d2d2d", fg="white")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_console(self):
        console_frame = tk.LabelFrame(self.root, text=" Emulator Log ",
                                      font=("Consolas", 10, "bold"),
                                      fg="#90CAF9", bg="#1e1e1e")
        console_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.console = scrolledtext.ScrolledText(console_frame, wrap=tk.WORD,
                                                 font=("Consolas", 9),
                                                 bg="#0d0d0d", fg="#00ff00",
                                                 insertbackground="white")
        self.console.pack(fill=tk.BOTH, expand=True)

        self.log("SamsoftEmu NES v1.0 GUI Ready")

    def log(self, msg):
        self.console.config(state=tk.NORMAL)
        self.console.insert(tk.END, msg + "\n")
        self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)

    # Emulator actions
    def open_rom(self):
        filetypes = [("NES ROMs", "*.nes"), ("All files", "*.*")]
        filename = filedialog.askopenfilename(title="Select NES ROM", filetypes=filetypes)
        if filename:
            self.rom_path = filename
            self.status_var.set(f"Loaded ROM: {os.path.basename(filename)}")
            self.log(f"[ROM] Loaded: {filename}")

    def run_emulator(self):
        if not self.rom_path:
            messagebox.showwarning("No ROM", "Please load a ROM first!")
            return
        self.is_running = True
        self.status_var.set("Running...")
        self.log(f"[SYSTEM] Emulating {os.path.basename(self.rom_path)} (stub backend)")
        # TODO: plug in CPU6502/PPU/APU backend

    def reset_emulator(self):
        if self.is_running:
            self.log("[SYSTEM] Emulator reset")
            self.status_var.set("Reset")
        else:
            self.log("[WARN] Reset called but emulator not running")

    def stop_emulator(self):
        if self.is_running:
            self.is_running = False
            self.log("[SYSTEM] Emulator stopped")
            self.status_var.set("Stopped")

    def launch_debugger(self):
        self.log("[TOOLS] Debugger opened (stub)")

    def launch_cheats(self):
        self.log("[TOOLS] Cheats manager opened (stub)")

    def launch_tas_tools(self):
        self.log("[TOOLS] TAS tools opened (stub)")

    def show_about(self):
        messagebox.showinfo("About SamsoftEmu NES",
                            "SamsoftEmu NES v1.0\nTkinter GUI Frontend\nAI Core Edition")

if __name__ == "__main__":
    root = tk.Tk()
    app = SamsoftEmuNESGUI(root)
    root.mainloop()

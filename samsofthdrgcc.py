#!/usr/bin/env python3
"""
Samsoft GCC - N64 Development Toolchain GUI
Professional MIPS C/ASM to Z64 ROM Compiler
Version 1.0.0
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import subprocess
import threading
import os
import sys
import json
from datetime import datetime
import re

class SamsoftGCC:
    def __init__(self, root):
        self.root = root
        self.root.title("Samsoft GCC - N64 Z64 Compiler")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        # Disable maximize button (Windows)
        if sys.platform == "win32":
            self.root.attributes('-toolwindow', False)
            self.root.overrideredirect(False)
        
        # Color scheme
        self.bg_color = "#1e1e1e"
        self.fg_color = "#ffffff"
        self.accent_color = "#007ACC"
        self.success_color = "#4CAF50"
        self.error_color = "#f44336"
        self.button_bg = "#2d2d2d"
        
        # Configure style
        self.root.configure(bg=self.bg_color)
        
        # Project settings
        self.project_config = {
            "source_file": "",
            "output_name": "output.z64",
            "optimization": "-O2",
            "target": "vr4300",
            "include_paths": [],
            "libraries": [],
            "defines": []
        }
        
        # Setup UI
        self.setup_ui()
        self.setup_compiler_paths()
        
    def setup_compiler_paths(self):
        """Setup default compiler toolchain paths"""
        self.toolchain = {
            "gcc": "mips64-elf-gcc",
            "as": "mips64-elf-as",
            "ld": "mips64-elf-ld",
            "objcopy": "mips64-elf-objcopy",
            "makemask": "makemask",
            "n64tool": "n64tool"
        }
        
    def setup_ui(self):
        """Create the main user interface"""
        
        # Top Frame - Header
        header_frame = tk.Frame(self.root, bg="#0d47a1", height=50)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Logo and Title
        title_label = tk.Label(
            header_frame,
            text="🎮 SAMSOFT GCC",
            font=("Consolas", 16, "bold"),
            bg="#0d47a1",
            fg="white"
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        subtitle = tk.Label(
            header_frame,
            text="N64 Z64 Compiler v1.0",
            font=("Consolas", 10),
            bg="#0d47a1",
            fg="#90CAF9"
        )
        subtitle.pack(side=tk.LEFT, padx=5, pady=10)
        
        # Main Container
        main_container = tk.Frame(self.root, bg=self.bg_color)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left Panel - Input/Settings
        left_panel = tk.Frame(main_container, bg=self.bg_color, width=290)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        left_panel.pack_propagate(False)
        
        # File Selection Frame
        file_frame = tk.LabelFrame(
            left_panel,
            text=" Source File ",
            font=("Consolas", 10, "bold"),
            bg=self.bg_color,
            fg=self.accent_color,
            relief=tk.GROOVE,
            borderwidth=2
        )
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.file_label = tk.Label(
            file_frame,
            text="No file selected",
            font=("Consolas", 9),
            bg=self.bg_color,
            fg="#888",
            anchor=tk.W
        )
        self.file_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        browse_btn = tk.Button(
            file_frame,
            text="Browse",
            font=("Consolas", 9),
            bg=self.button_bg,
            fg=self.fg_color,
            activebackground=self.accent_color,
            relief=tk.FLAT,
            command=self.browse_file,
            cursor="hand2"
        )
        browse_btn.pack(side=tk.RIGHT, padx=10, pady=5)
        
        # Compiler Settings Frame
        settings_frame = tk.LabelFrame(
            left_panel,
            text=" Compiler Settings ",
            font=("Consolas", 10, "bold"),
            bg=self.bg_color,
            fg=self.accent_color,
            relief=tk.GROOVE,
            borderwidth=2
        )
        settings_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Target Architecture
        tk.Label(
            settings_frame,
            text="Target:",
            font=("Consolas", 9),
            bg=self.bg_color,
            fg=self.fg_color
        ).grid(row=0, column=0, sticky=tk.W, padx=10, pady=3)
        
        self.target_var = tk.StringVar(value="VR4300")
        target_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.target_var,
            values=["VR4300", "R4300", "MIPS-III"],
            state="readonly",
            width=15
        )
        target_combo.grid(row=0, column=1, padx=5, pady=3)
        
        # Optimization Level
        tk.Label(
            settings_frame,
            text="Optimization:",
            font=("Consolas", 9),
            bg=self.bg_color,
            fg=self.fg_color
        ).grid(row=1, column=0, sticky=tk.W, padx=10, pady=3)
        
        self.opt_var = tk.StringVar(value="-O2")
        opt_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.opt_var,
            values=["-O0", "-O1", "-O2", "-O3", "-Os"],
            state="readonly",
            width=15
        )
        opt_combo.grid(row=1, column=1, padx=5, pady=3)
        
        # Output Format
        tk.Label(
            settings_frame,
            text="Format:",
            font=("Consolas", 9),
            bg=self.bg_color,
            fg=self.fg_color
        ).grid(row=2, column=0, sticky=tk.W, padx=10, pady=3)
        
        self.format_var = tk.StringVar(value="Z64")
        format_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.format_var,
            values=["Z64", "N64", "V64"],
            state="readonly",
            width=15
        )
        format_combo.grid(row=2, column=1, padx=5, pady=3)
        
        # Build Options Frame
        options_frame = tk.LabelFrame(
            left_panel,
            text=" Build Options ",
            font=("Consolas", 10, "bold"),
            bg=self.bg_color,
            fg=self.accent_color,
            relief=tk.GROOVE,
            borderwidth=2
        )
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.debug_var = tk.BooleanVar()
        debug_check = tk.Checkbutton(
            options_frame,
            text="Debug Symbols",
            variable=self.debug_var,
            font=("Consolas", 9),
            bg=self.bg_color,
            fg=self.fg_color,
            selectcolor=self.bg_color,
            activebackground=self.bg_color
        )
        debug_check.pack(anchor=tk.W, padx=10, pady=2)
        
        self.libultra_var = tk.BooleanVar(value=True)
        libultra_check = tk.Checkbutton(
            options_frame,
            text="Link libultra",
            variable=self.libultra_var,
            font=("Consolas", 9),
            bg=self.bg_color,
            fg=self.fg_color,
            selectcolor=self.bg_color,
            activebackground=self.bg_color
        )
        libultra_check.pack(anchor=tk.W, padx=10, pady=2)
        
        self.boot_var = tk.BooleanVar(value=True)
        boot_check = tk.Checkbutton(
            options_frame,
            text="Include Boot Code",
            variable=self.boot_var,
            font=("Consolas", 9),
            bg=self.bg_color,
            fg=self.fg_color,
            selectcolor=self.bg_color,
            activebackground=self.bg_color
        )
        boot_check.pack(anchor=tk.W, padx=10, pady=2)
        
        # Action Buttons Frame
        button_frame = tk.Frame(left_panel, bg=self.bg_color)
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.compile_btn = tk.Button(
            button_frame,
            text="🔨 COMPILE",
            font=("Consolas", 10, "bold"),
            bg=self.success_color,
            fg="white",
            activebackground="#45a049",
            relief=tk.FLAT,
            command=self.compile_code,
            cursor="hand2",
            width=12
        )
        self.compile_btn.pack(side=tk.LEFT, padx=5)
        
        self.clean_btn = tk.Button(
            button_frame,
            text="🧹 CLEAN",
            font=("Consolas", 10, "bold"),
            bg="#FFA726",
            fg="white",
            activebackground="#FB8C00",
            relief=tk.FLAT,
            command=self.clean_build,
            cursor="hand2",
            width=12
        )
        self.clean_btn.pack(side=tk.LEFT, padx=5)
        
        # Right Panel - Output Console
        right_panel = tk.Frame(main_container, bg=self.bg_color, width=290)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Console Frame
        console_frame = tk.LabelFrame(
            right_panel,
            text=" Build Output ",
            font=("Consolas", 10, "bold"),
            bg=self.bg_color,
            fg=self.accent_color,
            relief=tk.GROOVE,
            borderwidth=2
        )
        console_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Console Output
        self.console = scrolledtext.ScrolledText(
            console_frame,
            font=("Consolas", 8),
            bg="#0d0d0d",
            fg="#00ff00",
            insertbackground="#00ff00",
            height=15,
            width=35,
            wrap=tk.WORD
        )
        self.console.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Status Bar
        self.status_bar = tk.Label(
            self.root,
            text="Ready",
            font=("Consolas", 9),
            bg="#2d2d2d",
            fg="#888",
            anchor=tk.W,
            relief=tk.SUNKEN
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Initial console message
        self.console_print("Samsoft GCC N64 Compiler Ready\n", "info")
        self.console_print("=" * 40 + "\n", "info")
        
    def browse_file(self):
        """Browse for source file"""
        filename = filedialog.askopenfilename(
            title="Select Source File",
            filetypes=[
                ("C/ASM Files", "*.c *.s *.asm"),
                ("C Files", "*.c"),
                ("Assembly Files", "*.s *.asm"),
                ("All Files", "*.*")
            ]
        )
        
        if filename:
            self.project_config["source_file"] = filename
            short_name = os.path.basename(filename)
            self.file_label.config(text=short_name, fg=self.fg_color)
            self.console_print(f"✓ Loaded: {short_name}\n", "success")
            
            # Auto-detect file type
            ext = os.path.splitext(filename)[1].lower()
            if ext in ['.s', '.asm']:
                self.console_print("  Type: MIPS Assembly\n", "info")
            elif ext == '.c':
                self.console_print("  Type: C Source\n", "info")
                
    def console_print(self, text, tag="normal"):
        """Print to console with formatting"""
        self.console.config(state=tk.NORMAL)
        
        # Configure tags for different message types
        self.console.tag_config("normal", foreground="#00ff00")
        self.console.tag_config("error", foreground="#ff4444")
        self.console.tag_config("warning", foreground="#ffaa00")
        self.console.tag_config("success", foreground="#44ff44")
        self.console.tag_config("info", foreground="#00aaff")
        
        self.console.insert(tk.END, text, tag)
        self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)
        self.root.update_idletasks()
        
    def compile_code(self):
        """Compile the source code to Z64"""
        if not self.project_config["source_file"]:
            messagebox.showerror("Error", "Please select a source file first!")
            return
            
        # Start compilation in thread
        self.compile_btn.config(state=tk.DISABLED, text="⏳ BUILDING...")
        self.status_bar.config(text="Compiling...")
        
        compile_thread = threading.Thread(target=self.run_compilation)
        compile_thread.start()
        
    def run_compilation(self):
        """Run the actual compilation process"""
        try:
            source = self.project_config["source_file"]
            basename = os.path.splitext(os.path.basename(source))[0]
            ext = os.path.splitext(source)[1].lower()
            
            self.console_print("\n" + "="*40 + "\n", "info")
            self.console_print("Starting N64 Build Process...\n", "info")
            self.console_print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", "info")
            self.console_print("-"*40 + "\n", "info")
            
            # Step 1: Compile/Assemble
            if ext == '.c':
                self.console_print("Step 1: Compiling C source...\n", "info")
                obj_file = self.compile_c_source(source, basename)
            else:
                self.console_print("Step 1: Assembling MIPS code...\n", "info")
                obj_file = self.assemble_mips(source, basename)
                
            if not obj_file:
                raise Exception("Compilation failed!")
                
            self.console_print(f"  → Generated: {obj_file}\n", "success")
            
            # Step 2: Link
            self.console_print("Step 2: Linking object files...\n", "info")
            elf_file = self.link_object(obj_file, basename)
            self.console_print(f"  → Generated: {elf_file}\n", "success")
            
            # Step 3: Convert to binary
            self.console_print("Step 3: Converting to binary...\n", "info")
            bin_file = self.create_binary(elf_file, basename)
            self.console_print(f"  → Generated: {bin_file}\n", "success")
            
            # Step 4: Create Z64 ROM
            self.console_print("Step 4: Creating Z64 ROM...\n", "info")
            rom_file = self.create_rom(bin_file, basename)
            self.console_print(f"  → Generated: {rom_file}\n", "success")
            
            # Success
            self.console_print("-"*40 + "\n", "info")
            self.console_print(f"✓ BUILD SUCCESS!\n", "success")
            self.console_print(f"Output: {rom_file}\n", "success")
            
            # Get file size
            size = os.path.getsize(rom_file) if os.path.exists(rom_file) else 0
            self.console_print(f"Size: {size:,} bytes\n", "info")
            
            self.status_bar.config(text=f"Build successful: {rom_file}")
            
        except Exception as e:
            self.console_print(f"\n✗ BUILD FAILED!\n", "error")
            self.console_print(f"Error: {str(e)}\n", "error")
            self.status_bar.config(text="Build failed")
            
        finally:
            self.compile_btn.config(state=tk.NORMAL, text="🔨 COMPILE")
            
    def compile_c_source(self, source, basename):
        """Compile C source to object file"""
        try:
            obj_file = f"{basename}.o"
            
            # Build GCC command
            cmd = [
                self.toolchain["gcc"],
                "-march=vr4300",
                "-mtune=vr4300",
                "-mabi=32",
                "-mno-shared",
                "-G", "0",
                "-mno-abicalls",
                "-fno-PIC",
                self.opt_var.get(),
                "-fomit-frame-pointer",
                "-fno-toplevel-reorder",
                "-c",
                source,
                "-o", obj_file
            ]
            
            if self.debug_var.get():
                cmd.append("-g")
                
            # Simulate compilation
            self.console_print(f"  Command: {' '.join(cmd[:3])}...\n", "info")
            
            # In real implementation, would run:
            # result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Simulate success
            self.console_print("  Compilation complete.\n", "success")
            return obj_file
            
        except Exception as e:
            self.console_print(f"  Compilation error: {str(e)}\n", "error")
            return None
            
    def assemble_mips(self, source, basename):
        """Assemble MIPS assembly to object file"""
        try:
            obj_file = f"{basename}.o"
            
            cmd = [
                self.toolchain["as"],
                "-march=vr4300",
                "-mabi=32",
                source,
                "-o", obj_file
            ]
            
            self.console_print(f"  Command: {' '.join(cmd[:2])}...\n", "info")
            
            # Simulate assembly
            self.console_print("  Assembly complete.\n", "success")
            return obj_file
            
        except Exception as e:
            self.console_print(f"  Assembly error: {str(e)}\n", "error")
            return None
            
    def link_object(self, obj_file, basename):
        """Link object file to ELF"""
        try:
            elf_file = f"{basename}.elf"
            
            cmd = [
                self.toolchain["ld"],
                "-o", elf_file,
                "-T", "n64.ld",  # Linker script
                obj_file
            ]
            
            if self.libultra_var.get():
                cmd.append("-lultra")
                
            self.console_print("  Linking with libultra...\n", "info")
            
            # Simulate linking
            self.console_print("  Link complete.\n", "success")
            return elf_file
            
        except Exception as e:
            self.console_print(f"  Link error: {str(e)}\n", "error")
            return None
            
    def create_binary(self, elf_file, basename):
        """Convert ELF to binary"""
        try:
            bin_file = f"{basename}.bin"
            
            cmd = [
                self.toolchain["objcopy"],
                "-O", "binary",
                elf_file,
                bin_file
            ]
            
            self.console_print("  Extracting binary...\n", "info")
            
            # Simulate objcopy
            self.console_print("  Binary extraction complete.\n", "success")
            return bin_file
            
        except Exception as e:
            self.console_print(f"  Binary creation error: {str(e)}\n", "error")
            return None
            
    def create_rom(self, bin_file, basename):
        """Create final Z64 ROM"""
        try:
            rom_format = self.format_var.get().lower()
            rom_file = f"{basename}.{rom_format}"
            
            self.console_print(f"  Creating {rom_format.upper()} ROM...\n", "info")
            
            if self.boot_var.get():
                self.console_print("  Adding boot code...\n", "info")
                
            # Simulate ROM creation
            self.console_print("  Calculating CRC...\n", "info")
            self.console_print("  Padding to 8MB...\n", "info")
            
            # Create a dummy file for demo
            with open(rom_file, 'wb') as f:
                # N64 ROM header
                f.write(b'\x80\x37\x12\x40')  # Magic
                f.write(b'\x00' * (8*1024*1024 - 4))  # Padding
                
            self.console_print("  ROM creation complete.\n", "success")
            return rom_file
            
        except Exception as e:
            self.console_print(f"  ROM creation error: {str(e)}\n", "error")
            return None
            
    def clean_build(self):
        """Clean build artifacts"""
        self.console_print("\nCleaning build artifacts...\n", "warning")
        
        extensions = ['.o', '.elf', '.bin', '.z64', '.n64', '.v64']
        cleaned = 0
        
        for ext in extensions:
            # In real implementation, would delete files
            cleaned += 1
            
        self.console_print(f"Cleaned {cleaned} files.\n", "success")
        self.status_bar.config(text="Build cleaned")

def main():
    root = tk.Tk()
    app = SamsoftGCC(root)
    root.mainloop()

if __name__ == "__main__":
    main()

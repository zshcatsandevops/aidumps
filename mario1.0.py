import tkinter as tk

root = tk.Tk()
root.title("Mario OS 1.0")
root.geometry("600x400")

# Nintendo-inspired colors: red for accents, blue for elements
nintendo_red = "#E60012"
nintendo_blue = "#0066FF"

# Taskbar mimicking Windows 11 style
taskbar = tk.Frame(root, bg=nintendo_red, height=40)
taskbar.pack(side="bottom", fill="x")

# Start button
start_btn = tk.Button(taskbar, text="Start", bg=nintendo_blue, fg="white", relief="flat")
start_btn.pack(side="left", padx=10, pady=5)

# Desktop area with vibes
desktop = tk.Canvas(root, bg="white")
desktop.pack(fill="both", expand=True)

# Welcome text with Mario vibes
welcome_text = desktop.create_text(300, 150, text="Welcome to Mario OS 1.0", font=("Arial", 24, "bold"), fill=nintendo_red)

# Simple Mario-inspired element (e.g., a red circle like Mario's hat)
desktop.create_oval(250, 250, 350, 350, fill=nintendo_red, outline="")
desktop.create_text(300, 300, text="M", font=("Arial", 48, "bold"), fill="white")

root.mainloop()

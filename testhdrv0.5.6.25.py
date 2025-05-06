import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("Calculator")
root.geometry("600x400")

# Entry Widget
entry = ttk.Entry(root, font=('Arial', 20))
entry.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

# Button functions
def button_click(number):
    current = entry.get()
    entry.delete(0, tk.END)
    entry.insert(0, str(current) + str(number))

def button_clear():
    entry.delete(0, tk.END)

def button_equal():
    try:
        result = eval(entry.get())
        entry.delete(0, tk.END)
        entry.insert(0, result)
    except:
        entry.delete(0, tk.END)
        entry.insert(0, "Error")

# Define Buttons
buttons = [
    '7', '8', '9', '/',
    '4', '5', '6', '*',
    '1', '2', '3', '-',
    '0', '.', '=', '+'
]

row_num = 1
col_num = 0

for button in buttons:
    ttk.Button(root, text=button, command=lambda b=button: button_click(b) if b != '=' else button_equal() if b == '=' else button_clear() if b == 'C' else None).grid(row=row_num, column=col_num, padx=5, pady=5, sticky="nsew")
    col_num += 1
    if col_num > 3:
        col_num = 0
        row_num += 1

root.mainloop()

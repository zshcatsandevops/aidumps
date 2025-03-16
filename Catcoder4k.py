notebook = ttk.Notebook(main_frame)
notebook.pack(fill="both", expand=True)

# Function to add a new editor tab
def open_file_tab(filepath=None):
    tab_frame = ttk.Frame(notebook)
    text = tk.Text(tab_frame, wrap="none", undo=True)
    # Add a vertical scrollbar linked to the text widget
    yscroll = ttk.Scrollbar(tab_frame, orient="vertical", command=text.yview)
    text.configure(yscrollcommand=yscroll.set)
    # Place text and scrollbar in the tab frame
    text.pack(side="left", fill="both", expand=True)
    yscroll.pack(side="right", fill="y")
    # Determine tab title
    title = filepath if filepath else "Untitled"
    notebook.add(tab_frame, text=title)
    # If a file path is given, load the file content into the text widget
    if filepath:
        with open(filepath, "r") as f:
            code = f.read()
            text.insert("1.0", code)
            apply_syntax_highlighting(text, code, language=detect_language(filepath))
    # Bind events for this text widget (e.g., key events for autocomplete, etc.)
    text.bind("<KeyRelease>", on_text_change)
    return text  # return the text widget for further configuration if needed

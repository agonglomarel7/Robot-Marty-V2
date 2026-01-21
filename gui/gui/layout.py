import tkinter as tk
from tkinter import ttk, scrolledtext

# Création de l’interface (Tkinter)

def build_layout(app):
    root = app.root

    header = tk.Frame(root, bg="#2196F3", height=60)
    header.pack(fill=tk.X)

    app.log_text = scrolledtext.ScrolledText(
        root,
        font=("Consolas", 9),
        bg="#263238",
        fg="#A5D6A7"
    )
    app.log_text.pack(fill=tk.BOTH, expand=True)

    # tags logs
    app.log_text.tag_config("SYSTEM", foreground="#FFD54F")
    app.log_text.tag_config("OUT", foreground="#64B5F6")
    app.log_text.tag_config("INC", foreground="#81C784")
    app.log_text.tag_config("ERROR", foreground="#E57373")

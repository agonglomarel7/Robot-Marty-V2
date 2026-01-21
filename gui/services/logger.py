from datetime import datetime
import tkinter as tk

class GuiLogger:
    def __init__(self, app):
        self.app = app

    def log(self, level, message):
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        txt = self.app.log_text
        txt.insert(tk.END, ts + " ", "TIME")
        txt.insert(tk.END, f"{level:6} ", level)
        txt.insert(tk.END, message + "\n")
        txt.see(tk.END)

    def system(self, msg): self.log("SYSTEM", msg)
    def out(self, msg): self.log("OUT", msg)
    def inc(self, msg): self.log("INC", msg)
    def error(self, msg): self.log("ERROR", msg)

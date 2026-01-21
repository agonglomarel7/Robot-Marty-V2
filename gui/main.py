import tkinter as tk
from gui.app import MartyEmulatorGUI

def main():
    root = tk.Tk()
    app = MartyEmulatorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

from gui.layout import creer_interface
from gui.updater import demarrer_updater
from gui.logs import ajouter_log

class MartyEmulatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Marty v2 Robot Emulator")

        self.update_queue = queue.Queue()
        self.command_queue = queue.Queue()

        self.robots = {}
        self.robot_selectionne = None

        creer_interface(self)
        demarrer_updater(self)

        ajouter_log(self, "SYSTEM", "GUI démarrée")

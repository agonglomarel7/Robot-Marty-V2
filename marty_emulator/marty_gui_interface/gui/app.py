from gui.layout import build_layout
from core.robot_manager import RobotManager
from core.command_handler import CommandHandler
from core.event_loop import EventLoop
from services.logger import GuiLogger


# Classe MartyEmulatorGUI

class MartyEmulatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Marty v2 Robot Emulator")
        self.root.geometry("1400x800")

        # Services
        self.logger = GuiLogger(self)
        self.robot_manager = RobotManager(self)
        self.command_handler = CommandHandler(self)
        self.event_loop = EventLoop(self)

        # Interface
        build_layout(self)

        self.logger.system("Interface graphique initialisée")
        self.logger.system("En attente de connexion serveur...")

        self.event_loop.start()

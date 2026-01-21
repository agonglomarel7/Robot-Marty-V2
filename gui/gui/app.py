import queue

from gui.layout import build_layout
from core.robot_manager import RobotManager
from core.command_handler import CommandHandler
from core.event_loop import EventLoop
from services.logger import GuiLogger
from core.web_socket_client import MartyWebSocketClient


class MartyEmulatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Marty v2 Robot Emulator")
        self.root.geometry("1400x800")

        # Queue thread-safe pour messages serveur → GUI
        self.update_queue = queue.Queue()

        # Services
        self.logger = GuiLogger(self)
        self.robot_manager = RobotManager(self)
        self.command_handler = CommandHandler(self)
        self.event_loop = EventLoop(self)

        # Interface graphique
        build_layout(self)

        self.logger.system("Interface graphique initialisée")
        self.logger.system("En attente de connexion serveur...")

        # Client WebSocket Marty
        self.ws_client = MartyWebSocketClient(
            url="ws://127.0.0.1:8080",
            update_queue=self.update_queue,
            logger=self.logger
        )

        # Démarrage boucle GUI
        self.event_loop.start()
        self.mettre_a_jour_interface()

    # =========================
    # Connexion serveur
    # =========================
    def demarrer_connexion(self):
        if not self.ws_client.is_alive():
            self.logger.system("Tentative de connexion au serveur Marty...")
            self.ws_client.start()

    # =========================
    # Mise à jour GUI
    # =========================
    def mettre_a_jour_interface(self):
        try:
            while True:
                message = self.update_queue.get_nowait()
                self.logger.incoming(message)
                self.robot_manager.handle_message(message)
        except queue.Empty:
            pass

        self.root.after(100, self.mettre_a_jour_interface)

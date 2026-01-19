import threading
import time
import websocket
import json


class MartyWebSocketClient(threading.Thread):
    def __init__(self, url, update_queue, logger):
        super().__init__(daemon=True)
        self.url = url
        self.update_queue = update_queue
        self.logger = logger
        self.running = False

    def run(self):
        self.running = True
        self.logger.system("Tentative de connexion au serveur Marty...")

        try:
            self.ws = websocket.WebSocket()
            self.ws.connect(self.url)
            self.logger.system("Connexion WebSocket établie")

            while self.running:
                message = self.ws.recv()
                self.update_queue.put(message)

        except Exception as e:
            self.logger.error(f"Erreur WebSocket : {e}")

        finally:
            self.logger.system("Connexion WebSocket fermée")

    def stop(self):
        self.running = False
        try:
            self.ws.close()
        except:
            pass

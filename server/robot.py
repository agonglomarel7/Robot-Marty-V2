# robot.py
import time

class RobotVirtuel:
    """
    Robot Marty virtuel associé à un client.
    État volontairement simplifié mais cohérent.
    """

    def __init__(self, client_id):
        self.client_id = client_id
        self.nom = f"Marty-Virtual-{client_id}"
        self.batterie_voltage = 8.4
        self.position = "ready"
        self.commandes = 0
        self.start_time = time.time()

    def executer_commande(self):
        self.commandes += 1
        if self.commandes % 10 == 0:
            self.batterie_voltage -= 0.01

    def info(self):
        uptime = int(time.time() - self.start_time)
        return {
            "nom": self.nom,
            "batterie": f"{self.batterie_voltage:.2f}V",
            "position": self.position,
            "commandes": self.commandes,
            "uptime": f"{uptime}s"
        }

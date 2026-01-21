# Envoi des commandes

class CommandHandler:
    def __init__(self, app):
        self.app = app

    def send(self, command):
        rm = self.app.robot_manager
        if not rm.selected_robot:
            self.app.logger.error("Aucun robot sélectionné")
            return

        self.app.logger.out(command)
        # plus tard → envoyer au serveur

# Mise à jour périodique

class EventLoop:
    def __init__(self, app):
        self.app = app

    def start(self):
        self.update()

    def update(self):
        # plus tard : messages serveur
        self.app.root.after(100, self.update)

from datetime import datetime
import tkinter as tk

# Gestion des robots
class RobotManager:
    def __init__(self, app):
        self.app = app
        self.robots = {}
        self.selected_robot = None

    def add_robot(self, robot_id, name, state):
        self.robots[robot_id] = {
            "name": name,
            "state": state
        }
        self.app.logger.system(f"Robot connecté : {name}")

    def select_robot(self, robot_id):
        self.selected_robot = robot_id
        self.app.logger.system(
            f"Robot sélectionné : {self.robots[robot_id]['name']}"
        )


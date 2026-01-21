# handler.py
from ricserial import RICSerialGenerator


class CommandeHandler:
    """
    Traduit les commandes RICSerial en actions robot
    """

    def __init__(self, robot):
        self.robot = robot

    def traiter(self, cmd):
        msg_id = cmd.get("id", 0)

        if cmd["type"] == "rest":
            self.robot.executer_commande()

            if "battery" in cmd["url"]:
                return RICSerialGenerator.json(msg_id, {
                    "voltage": self.robot.batterie_voltage
                })

            if "status" in cmd["url"]:
                return RICSerialGenerator.json(msg_id, {
                    "rslt": "ok",
                    "isReady": True,
                    "isMoving": False
                })

            return RICSerialGenerator.ok(msg_id)

        if cmd["type"] == "json":
            return RICSerialGenerator.ok(msg_id)

        return RICSerialGenerator.error(msg_id)

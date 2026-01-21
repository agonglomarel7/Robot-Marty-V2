# main.py
import socket
import threading
from websocket_server import handshake, lire_trame, send_frame
from ricserial import RICSerialParser
from robot import RobotVirtuel
from handler import CommandeHandler

HOST = "0.0.0.0"
PORT = 8080


def gerer_client(conn, addr, client_id):
    print(f"[+] Client {client_id} connecté")

    request = conn.recv(4096)
    handshake(conn, request)

    robot = RobotVirtuel(client_id)
    handler = CommandeHandler(robot)

    while True:
        payload = lire_trame(conn)
        if not payload:
            break

        cmd = RICSerialParser.parser(payload)
        response = handler.traiter(cmd)
        send_frame(conn, response)

        print(robot.info())

    conn.close()
    print(f"[-] Client {client_id} déconnecté")


def main():
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()

    print(f"Serveur Marty émulé sur {HOST}:{PORT}")

    client_id = 0
    while True:
        conn, addr = server.accept()
        client_id += 1
        threading.Thread(
            target=gerer_client,
            args=(conn, addr, client_id),
            daemon=True
        ).start()


if __name__ == "__main__":
    main()

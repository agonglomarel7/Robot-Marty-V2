import socket

def start_server():
    HOST = '0.0.0.0'
    PORT = 8080    # OUI : martypy utilise le port 80 !!!

    print(f"🚀 Serveur Marty (TCP) en attente sur {HOST}:{PORT}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()

        while True:
            conn, addr = s.accept()
            print(f"[+] Client connecté : {addr}")

            with conn:
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    print("📩 Données reçues :", data.hex())

                print("[-] Client déconnecté")

if __name__ == "__main__":
    start_server()

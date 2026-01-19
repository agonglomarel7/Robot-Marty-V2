# ============================================================================
# SERVEUR D'ÉMULATION MARTY V2 - ÉTAPE 2
# ============================================================================
# Ce serveur émule un véritable robot Marty v2
# Il parse les commandes RICSerial et répond de manière appropriée
# Gère plusieurs connexions simultanées (multi-threading)
# ============================================================================

import socket
import threading
import struct
import json
import time
import hashlib
import base64
from datetime import datetime

# CONFIGURATION
HOST = "0.0.0.0"
PORT = 8080

# Compteur global pour numéroter les clients
nombre_connexions = 0
lock = threading.Lock()

# CLASSE : État d'un Robot Virtuel
class RobotVirtuel:
    """
    Classe représentant l'état d'un robot Marty émulé.
    Chaque connexion client a son propre robot virtuel.
    """
    
    def __init__(self, client_id):
        self.client_id = client_id
        self.nom = f"Marty-Virtual-{client_id}"
        
        # État de la batterie
        self.batterie_voltage = 8.4  # Volts (pleine charge)
        self.batterie_pourcentage = 100
        
        # État des moteurs (9 servomoteurs sur Marty v2)
        self.moteurs = {
            0: {"position": 0, "courant": 120},  # Hip Left
            1: {"position": 0, "courant": 115},  # Twist Left
            2: {"position": 0, "courant": 110},  # Knee Left
            3: {"position": 0, "courant": 125},  # Hip Right
            4: {"position": 0, "courant": 118},  # Twist Right
            5: {"position": 0, "courant": 112},  # Knee Right
            6: {"position": 0, "courant": 100},  # Arm Left
            7: {"position": 0, "courant": 105},  # Arm Right
            8: {"position": 0, "courant": 95},   # Eyes
        }
        
        # État de l'IMU (capteur de mouvement)
        self.accelerometre = {"x": 0.05, "y": 0.02, "z": 9.81}  # m/s²
        self.gyroscope = {"x": 0.0, "y": 0.0, "z": 0.0}  # rad/s
        
        # État des GPIO (pins d'entrée/sortie)
        self.gpio_states = {i: 0 for i in range(8)}
        
        # Position et état général
        self.position_actuelle = "ready"  # ready, walking, celebrating, etc.
        self.est_pret = True
        
        # Statistiques
        self.temps_demarrage = time.time()
        self.commandes_recues = 0
        
        print(f"🤖 Robot virtuel '{self.nom}' initialisé")
    
    def executer_commande(self, commande):
        """Execute une commande et met à jour l'état du robot"""
        self.commandes_recues += 1
        
        # Simuler une légère baisse de batterie à chaque commande
        if self.commandes_recues % 10 == 0:
            self.batterie_voltage -= 0.01
            self.batterie_pourcentage = int((self.batterie_voltage / 8.4) * 100)
    
    def get_info(self):
        """Retourne un résumé de l'état du robot"""
        uptime = int(time.time() - self.temps_demarrage)
        return {
            "nom": self.nom,
            "batterie": f"{self.batterie_voltage:.2f}V ({self.batterie_pourcentage}%)",
            "position": self.position_actuelle,
            "commandes": self.commandes_recues,
            "uptime": f"{uptime}s"
        }


# CLASSE : Parser RICSerial
class RICSerialParser:
    """
    Parser pour le protocole RICSerial utilisé par Marty.
    
    Format détecté :
    - e7 = délimiteur de début/fin
    - Type 1 (binaire) : e7 [ID] [TYPE] [FLAGS] [DATA...] e7
    - Type 2 (REST) : e7 [ID] [TYPE] 00 [URL_STRING] 00 [CRC] e7
    - Type 3 (JSON) : e7 [ID] [TYPE] 03 [JSON_STRING] [CRC] e7
    """
    
    @staticmethod
    def parser(payload):
        """
        Parse un payload RICSerial et retourne un dictionnaire
        avec le type de commande et les paramètres.
        """
        
        # Vérifier les délimiteurs e7
        if len(payload) < 2 or payload[0] != 0xe7 or payload[-1] != 0xe7:
            return {"type": "unknown", "raw": payload}
        
        # Extraire le contenu entre les délimiteurs
        contenu = payload[1:-1]
        
        if len(contenu) < 3:
            return {"type": "unknown", "raw": payload}
        
        msg_id = contenu[0]
        msg_type = contenu[1]
        flags = contenu[2] if len(contenu) > 2 else 0
        
        # TYPE 1 : Commande REST (URL-like)
        if flags == 0x00 and b'\x00' in contenu[3:]:
            try:
                # Extraire la partie texte jusqu'au prochain 0x00
                fin_texte = contenu[3:].index(0x00)
                url_bytes = contenu[3:3+fin_texte]
                url = url_bytes.decode('utf-8', errors='ignore')
                
                return {
                    "type": "rest",
                    "id": msg_id,
                    "url": url,
                    "raw": payload
                }
            except:
                pass
        
        # TYPE 2 : Commande JSON
        if flags == 0x03:
            try:
                # Le reste est du JSON (jusqu'au CRC)
                json_bytes = contenu[3:-2]  # -2 pour retirer le CRC
                json_str = json_bytes.decode('utf-8', errors='ignore')
                json_data = json.loads(json_str)
                
                return {
                    "type": "json",
                    "id": msg_id,
                    "data": json_data,
                    "raw": payload
                }
            except:
                pass
        
        # TYPE 3 : Commande binaire simple
        return {
            "type": "binary",
            "id": msg_id,
            "msg_type": msg_type,
            "flags": flags,
            "data": contenu[3:],
            "raw": payload
        }


# CLASSE : Générateur de Réponses RICSerial
class RICSerialGenerator:
    """
    Génère des réponses au format RICSerial attendues par martypy.
    """
    
    @staticmethod
    def calculer_crc(data):
        """Calcule un CRC simple (à affiner si nécessaire)"""
        crc = 0
        for byte in data:
            crc ^= byte
        return crc & 0xFF
    
    @staticmethod
    def creer_reponse_ok(msg_id=0):
        """Réponse simple : commande acceptée"""
        # Format : e7 [ID] [TYPE] 00 "OK" 00 [CRC] e7
        contenu = bytes([msg_id, 0x02, 0x00]) + b"OK" + b"\x00"
        crc = RICSerialGenerator.calculer_crc(contenu)
        return b"\xe7" + contenu + bytes([crc]) + b"\xe7"
    
    @staticmethod
    def creer_reponse_json(msg_id, data_dict):
        """Réponse JSON (pour lectures de capteurs, etc.)"""
        json_str = json.dumps(data_dict, separators=(',', ':'))
        json_bytes = json_str.encode('utf-8')
        
        contenu = bytes([msg_id, 0x02, 0x03]) + json_bytes
        crc = RICSerialGenerator.calculer_crc(contenu)
        
        return b"\xe7" + contenu + bytes([crc]) + b"\xe7"
    
    @staticmethod
    def creer_reponse_valeur(msg_id, valeur):
        """Réponse avec une valeur numérique"""
        valeur_str = str(valeur)
        valeur_bytes = valeur_str.encode('utf-8')
        
        contenu = bytes([msg_id, 0x02, 0x00]) + valeur_bytes + b"\x00"
        crc = RICSerialGenerator.calculer_crc(contenu)
        
        return b"\xe7" + contenu + bytes([crc]) + b"\xe7"
    
    @staticmethod
    def creer_reponse_erreur(msg_id, erreur_msg="Error"):
        """Réponse d'erreur"""
        erreur_bytes = erreur_msg.encode('utf-8')
        
        contenu = bytes([msg_id, 0x02, 0xFF]) + erreur_bytes + b"\x00"
        crc = RICSerialGenerator.calculer_crc(contenu)
        
        return b"\xe7" + contenu + bytes([crc]) + b"\xe7"


# GESTIONNAIRE DE COMMANDES
class CommandeHandler:
    """
    Gère l'exécution des commandes et génère les réponses appropriées.
    """
    
    def __init__(self, robot):
        self.robot = robot
    
    def traiter_commande(self, commande_parsee):
        
        msg_id = commande_parsee.get("id", 0)
        
        # COMMANDES REST (URL-like)
        if commande_parsee["type"] == "rest":
            url = commande_parsee["url"]
            
            print(f"  Commande REST: {url}")
            
            # Trajectoires (mouvements)
            if url.startswith("traj/"):
                self.robot.executer_commande(url)
                return RICSerialGenerator.creer_reponse_ok(msg_id)
            
            # Lecture de la batterie
            if "battery" in url.lower():
                return RICSerialGenerator.creer_reponse_valeur(
                    msg_id, 
                    self.robot.batterie_voltage
                )
            
            # Lecture de l'accéléromètre
            if "accel" in url.lower():
                return RICSerialGenerator.creer_reponse_json(
                    msg_id,
                    self.robot.accelerometre
                )
            
            # Lecture du gyroscope
            if "gyro" in url.lower():
                return RICSerialGenerator.creer_reponse_json(
                    msg_id,
                    self.robot.gyroscope
                )
            
            # Lecture du courant d'un moteur
            if "motorcurrent" in url.lower() or "motor/" in url.lower():
                # Extraire l'ID du moteur (si présent)
                motor_id = 0
                if "motor/" in url:
                    try:
                        motor_id = int(url.split("motor/")[1].split("?")[0])
                    except:
                        pass
                
                courant = self.robot.moteurs.get(motor_id, {}).get("courant", 100)
                return RICSerialGenerator.creer_reponse_valeur(msg_id, courant)
            
            # GPIO
            if "gpio" in url.lower():
                return RICSerialGenerator.creer_reponse_json(
                    msg_id,
                    {"gpio": self.robot.gpio_states}
                )
            
            # Status général
            if "status" in url.lower() or "hwstatus" in url.lower():
                return RICSerialGenerator.creer_reponse_json(
                    msg_id,
                    {
                        "rslt": "ok",
                        "isReady": self.robot.est_pret,
                        "isMoving": False
                    }
                )
            
            # Par défaut : OK
            return RICSerialGenerator.creer_reponse_ok(msg_id)
        
        # COMMANDES JSON
        elif commande_parsee["type"] == "json":
            data = commande_parsee["data"]
            cmd_name = data.get("cmdName", "")
            
            print(f"   Commande JSON: {cmd_name}")
            
            # Subscription (abonnement aux données)
            if cmd_name == "subscription":
                return RICSerialGenerator.creer_reponse_json(
                    msg_id,
                    {"rslt": "ok", "subscribed": True}
                )
            
            # Par défaut
            return RICSerialGenerator.creer_reponse_ok(msg_id)
        
        # COMMANDES BINAIRES
        elif commande_parsee["type"] == "binary":
            print(f"    Commande binaire: type={commande_parsee.get('msg_type')}")
            return RICSerialGenerator.creer_reponse_ok(msg_id)
        
        # COMMANDE INCONNUE
        else:
            print(f"    Commande inconnue")
            return RICSerialGenerator.creer_reponse_erreur(msg_id, "Unknown command")


# FONCTIONS WEBSOCKET (identiques à l'Étape 1)
def recevoir_octets(connexion, nombre):
    """Reçoit exactement 'nombre' octets"""
    donnees = b""
    while len(donnees) < nombre:
        reste = nombre - len(donnees)
        morceau = connexion.recv(reste)
        if not morceau:
            return None
        donnees += morceau
    return donnees


def lire_trame_websocket(connexion):
    """Lit une trame WebSocket complète"""
    header = recevoir_octets(connexion, 2)
    if not header:
        return None
    
    octet1, octet2 = header[0], header[1]
    fin = (octet1 >> 7) & 1
    opcode = octet1 & 0x0f
    masque_present = (octet2 >> 7) & 1
    longueur_payload = octet2 & 0x7f
    
    if longueur_payload == 126:
        extension = recevoir_octets(connexion, 2)
        if not extension:
            return None
        longueur_payload = struct.unpack(">H", extension)[0]
    elif longueur_payload == 127:
        extension = recevoir_octets(connexion, 8)
        if not extension:
            return None
        longueur_payload = struct.unpack(">Q", extension)[0]
    
    cle_masque = None
    if masque_present:
        cle_masque = recevoir_octets(connexion, 4)
        if not cle_masque:
            return None
    
    payload = b""
    if longueur_payload > 0:
        payload = recevoir_octets(connexion, longueur_payload)
        if payload is None:
            return None
    
    if masque_present and cle_masque:
        payload_demasque = bytearray(longueur_payload)
        for i in range(longueur_payload):
            payload_demasque[i] = payload[i] ^ cle_masque[i % 4]
        payload = bytes(payload_demasque)
    
    return {"opcode": opcode, "payload": payload}


def construire_trame_websocket(payload_bytes, opcode=0x2):
    """Construit une trame WebSocket"""
    premier_octet = 0x80 | (opcode & 0x0f)
    longueur = len(payload_bytes)
    
    if longueur < 126:
        header = struct.pack("!BB", premier_octet, longueur)
    elif longueur < 65536:
        header = struct.pack("!BBH", premier_octet, 126, longueur)
    else:
        header = struct.pack("!BBQ", premier_octet, 127, longueur)
    
    return header + payload_bytes


# GESTIONNAIRE DE CLIENT (THREAD)
def gerer_client(connexion, adresse):
    """
    Gère un client connecté (avec émulation complète).
    """
    
    global nombre_connexions
    
    with lock:
        nombre_connexions += 1
        num_client = nombre_connexions
    
    print(f"\n{'='*70}")
    print(f" CLIENT #{num_client} connecté depuis {adresse}")
    print(f"{'='*70}\n")
    
    # Créer un robot virtuel pour ce client
    robot = RobotVirtuel(num_client)
    handler = CommandeHandler(robot)
    
    try:
        # HANDSHAKE WEBSOCKET
        requete_http = connexion.recv(4096)
        if not requete_http:
            return
        
        print(f" Client #{num_client}: Handshake reçu")
        
        texte_requete = requete_http.decode('utf-8', errors='ignore')
        
        # Chercher Sec-WebSocket-Key
        cle_websocket = None
        for ligne in texte_requete.split("\r\n"):
            if ligne.lower().startswith("sec-websocket-key:"):
                cle_websocket = ligne.split(":", 1)[1].strip()
                break
        
        # Construire la réponse
        if cle_websocket:
            GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
            hash_sha1 = hashlib.sha1((cle_websocket + GUID).encode()).digest()
            accept = base64.b64encode(hash_sha1).decode()
            reponse = (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
            ).encode()
        else:
            reponse = (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n\r\n"
            ).encode()
        
        connexion.sendall(reponse)
        print(f" Client #{num_client}: Handshake accepté\n")
        
        # BOUCLE DE TRAITEMENT DES COMMANDES
        compteur_trames = 0
        
        while True:
            trame = lire_trame_websocket(connexion)
            
            if trame is None:
                print(f" Client #{num_client}: Connexion fermée")
                break
            
            compteur_trames += 1
            opcode = trame["opcode"]
            payload = trame["payload"]
            
            # Close frame
            if opcode == 0x8:
                print(f" Client #{num_client}: Demande de fermeture")
                break
            
            print(f" Client #{num_client} - Trame #{compteur_trames} ({len(payload)} octets)")
            
            # PARSER LA COMMANDE
            commande = RICSerialParser.parser(payload)
            
            # TRAITER ET RÉPONDRE
            reponse_payload = handler.traiter_commande(commande)
            
            # Envoyer la réponse
            trame_reponse = construire_trame_websocket(reponse_payload, opcode=0x2)
            connexion.sendall(trame_reponse)
            
            print(f"   Réponse envoyée ({len(reponse_payload)} octets)")
            print(f"   État robot: {robot.get_info()}")
            print()
    
    except Exception as e:
        print(f"Client #{num_client}: Erreur - {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            connexion.close()
        except:
            pass
        
        with lock:
            nombre_connexions -= 1
        
        print(f"\n{'='*70}")
        print(f" CLIENT #{num_client} déconnecté")
        print(f"   • Commandes traitées: {robot.commandes_recues}")
        print(f"   • Clients restants: {nombre_connexions}")
        print(f"{'='*70}\n")


# SERVEUR PRINCIPAL
def demarrer_serveur():
    
    socket_serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_serveur.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socket_serveur.bind((HOST, PORT))
    socket_serveur.listen(10)  # File d'attente de 10 connexions
    
    print("╔" + "═"*68 + "╗")
    print("║" + " SERVEUR D'ÉMULATION MARTY V2 - ÉTAPE 2 ".center(68) + "║")
    print("╠" + "═"*68 + "╣")
    print(f"║  Adresse: {HOST}:{PORT}".ljust(69) + "║")
    print(f"║  Mode: ÉMULATION COMPLÈTE".ljust(69) + "║")
    print(f"║  Threading: ACTIF (multi-clients)".ljust(69) + "║")
    print(f"║  Démarré: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".ljust(69) + "║")
    print("╚" + "═"*68 + "╝\n")
    print(" En attente de connexions...\n")
    
    try:
        while True:
            connexion_client, adresse_client = socket_serveur.accept()
            
            # Créer un thread pour gérer ce client
            thread_client = threading.Thread(
                target=gerer_client,
                args=(connexion_client, adresse_client),
                daemon=True
            )
            thread_client.start()
    
    except KeyboardInterrupt:
        print("\n\n  Arrêt du serveur (Ctrl+C)")
    
    finally:
        socket_serveur.close()
        print(" Serveur arrêté proprement")


# POINT D'ENTRÉE
if __name__ == "__main__":
    demarrer_serveur()
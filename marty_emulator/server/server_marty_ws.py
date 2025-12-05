# ============================================================================
# SERVEUR WEBSOCKET POUR ROBOT MARTY V2
# Projet : Émulation de communication avec robot Marty
# Auteur : Étudiant 
# Date : Décembre 2024
# ============================================================================
# Ce serveur permet de recevoir les messages du robot Marty via WebSocket
# Il est "permissif" car Marty utilise un protocole WebSocket non-standard
# ============================================================================

import socket
import threading
import struct
import json
import time

# ============================================================================
# CONFIGURATION DU SERVEUR
# ============================================================================
HOST = "0.0.0.0"  # Écoute sur toutes les interfaces réseau (local + externe)
PORT = 8080        # Port utilisé (à modifier si déjà utilisé)

# Compteur de connexions pour suivre combien de robots sont connectés
nombre_connexions = 0
lock = threading.Lock()  # Pour éviter les conflits quand plusieurs threads modifient la même variable


# ============================================================================
# FONCTION 1 : Recevoir exactement N octets depuis la socket
# ============================================================================
def recevoir_octets(connexion, nombre):
    """
    Cette fonction lit exactement 'nombre' octets depuis la connexion.
    Elle continue à lire jusqu'à avoir reçu tous les octets demandés.
    
    Args:
        connexion: La socket connectée au client
        nombre: Le nombre d'octets à recevoir
        
    Returns:
        Les données reçues (bytes) ou None si la connexion est coupée
    """
    donnees = b""  # Variable pour accumuler les données (b"" = bytes vide)
    
    while len(donnees) < nombre:
        # On calcule combien d'octets il reste à recevoir
        reste = nombre - len(donnees)
        
        # On essaye de recevoir les octets manquants
        morceau = connexion.recv(reste)
        
        # Si recv() retourne vide, la connexion est fermée
        if not morceau:
            print(" Connexion fermée pendant la lecture")
            return None
            
        donnees += morceau
    
    return donnees


# ============================================================================
# FONCTION 2 : Lire une trame WebSocket complète
# ============================================================================
def lire_trame_websocket(connexion):
    """
    Cette fonction lit une trame WebSocket selon le protocole (simplifié).
    
    Structure d'une trame WebSocket:
    - 2 premiers octets : header (FIN, opcode, MASK, longueur)
    - Longueur étendue si besoin (2 ou 8 octets supplémentaires)
    - Clé de masque si MASK=1 (4 octets)
    - Payload (données)
    
    Returns:
        Un dictionnaire avec: {"opcode": int, "payload": bytes}
        ou None si erreur/déconnexion
    """
    
    # ÉTAPE 1 : Lire les 2 premiers octets (header de base)
    header = recevoir_octets(connexion, 2)
    if not header:
        return None
    
    # Décoder le premier octet
    octet1 = header[0]
    fin = (octet1 >> 7) & 1         # Bit FIN (fragment final ?)
    opcode = octet1 & 0x0f          # Opcode (type de trame)
    
    # Décoder le deuxième octet
    octet2 = header[1]
    masque_present = (octet2 >> 7) & 1   # Bit MASK (payload masqué ?)
    longueur_payload = octet2 & 0x7f     # 7 bits de longueur
    
    print(f"📦 Trame reçue: FIN={fin}, Opcode=0x{opcode:x}, Masque={masque_present}, Long={longueur_payload}")
    
    # ÉTAPE 2 : Gérer les longueurs étendues
    # Si longueur = 126, les 2 octets suivants donnent la vraie longueur
    if longueur_payload == 126:
        extension = recevoir_octets(connexion, 2)
        if not extension:
            return None
        longueur_payload = struct.unpack(">H", extension)[0]  # ">H" = unsigned short big-endian
        print(f"   → Longueur étendue (16 bits): {longueur_payload}")
    
    # Si longueur = 127, les 8 octets suivants donnent la vraie longueur
    elif longueur_payload == 127:
        extension = recevoir_octets(connexion, 8)
        if not extension:
            return None
        longueur_payload = struct.unpack(">Q", extension)[0]  # ">Q" = unsigned long long big-endian
        print(f"   → Longueur étendue (64 bits): {longueur_payload}")
    
    # ÉTAPE 3 : Lire la clé de masque si présente
    cle_masque = None
    if masque_present:
        cle_masque = recevoir_octets(connexion, 4)
        if not cle_masque:
            return None
    
    # ÉTAPE 4 : Lire le payload
    payload = b""
    if longueur_payload > 0:
        payload = recevoir_octets(connexion, longueur_payload)
        if payload is None:
            return None
    
    # ÉTAPE 5 : Démasquer le payload si nécessaire
    if masque_present and cle_masque:
        # XOR chaque octet du payload avec la clé de masque (rotation)
        payload_demasque = bytearray(longueur_payload)
        for i in range(longueur_payload):
            payload_demasque[i] = payload[i] ^ cle_masque[i % 4]
        payload = bytes(payload_demasque)
    
    return {
        "opcode": opcode,
        "payload": payload
    }


# ============================================================================
# FONCTION 3 : Construire une trame WebSocket pour envoyer au client
# ============================================================================
def construire_trame_websocket(payload_bytes, opcode=0x2):
    """
    Construit une trame WebSocket à envoyer au client.
    
    Args:
        payload_bytes: Les données à envoyer (bytes)
        opcode: Type de trame (0x1=text, 0x2=binary, 0x8=close)
        
    Returns:
        La trame complète prête à être envoyée (bytes)
    """
    
    # Premier octet : FIN=1 (0x80) + opcode
    premier_octet = 0x80 | (opcode & 0x0f)
    
    longueur = len(payload_bytes)
    
    # Construire le header selon la longueur
    if longueur < 126:
        # Longueur courte : tient sur 7 bits
        header = struct.pack("!BB", premier_octet, longueur)
    elif longueur < 65536:
        # Longueur moyenne : utilise 126 + 2 octets
        header = struct.pack("!BBH", premier_octet, 126, longueur)
    else:
        # Longueur longue : utilise 127 + 8 octets
        header = struct.pack("!BBQ", premier_octet, 127, longueur)
    
    # Note : Le serveur N'envoie JAMAIS de masque (MASK=0)
    return header + payload_bytes


# ============================================================================
# FONCTION 4 : Gérer une connexion client (thread séparé par client)
# ============================================================================
def gerer_client(connexion, adresse):
    """
    Cette fonction gère un client connecté (un robot Marty).
    Elle tourne dans un thread séparé pour chaque connexion.
    
    Args:
        connexion: La socket connectée au client
        adresse: L'adresse IP et port du client (tuple)
    """
    
    global nombre_connexions
    
    # Incrémenter le compteur de connexions
    with lock:
        nombre_connexions += 1
        num_client = nombre_connexions
    
    print(f"\n{'='*60}")
    print(f" NOUVEAU CLIENT #{num_client} connecté depuis {adresse}")
    print(f"{'='*60}\n")
    
    try:
        # ========================================================================
        # ÉTAPE 1 : HANDSHAKE WEBSOCKET
        # ========================================================================
        # Le client envoie d'abord une requête HTTP pour "upgrader" vers WebSocket
        
        requete_http = connexion.recv(4096)
        if not requete_http:
            print(f" Client #{num_client}: Aucune donnée reçue")
            return
        
        print(f" Client #{num_client}: Handshake reçu ({len(requete_http)} octets)")
        
        # Essayer de décoder en texte pour voir la requête HTTP
        try:
            texte_requete = requete_http.decode('utf-8', errors='ignore')
            print("┌" + "─"*58 + "┐")
            print("│ REQUÊTE HTTP:".ljust(59) + "│")
            print("├" + "─"*58 + "┤")
            for ligne in texte_requete.split("\r\n")[:10]:  # Afficher max 10 lignes
                print(f"│ {ligne[:56].ljust(56)} │")
            print("└" + "─"*58 + "┘")
        except:
            print("  Impossible de décoder la requête en texte")
        
        # ========================================================================
        # ÉTAPE 2 : RÉPONDRE AU HANDSHAKE
        # ========================================================================
        # On doit répondre "101 Switching Protocols" pour valider la connexion
        
        # Chercher la clé Sec-WebSocket-Key dans la requête
        cle_websocket = None
        lignes = texte_requete.split("\r\n")
        for ligne in lignes:
            if ligne.lower().startswith("sec-websocket-key:"):
                cle_websocket = ligne.split(":", 1)[1].strip()
                break
        
        # Construire la réponse HTTP
        if cle_websocket:
            # Calculer Sec-WebSocket-Accept selon RFC6455
            import base64
            import hashlib
            GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
            hash_sha1 = hashlib.sha1((cle_websocket + GUID).encode()).digest()
            accept = base64.b64encode(hash_sha1).decode()
            
            reponse = (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
            ).encode()
            print(f" Client #{num_client}: Handshake RFC6455 standard")
        else:
            # Mode permissif pour martypy (pas de Sec-WebSocket-Key)
            reponse = (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n\r\n"
            ).encode()
            print(f" Client #{num_client}: Handshake permissif (martypy)")
        
        connexion.sendall(reponse)
        print(f" Client #{num_client}: Réponse handshake envoyée\n")
        
        # ========================================================================
        # ÉTAPE 3 : BOUCLE DE RÉCEPTION DES TRAMES
        # ========================================================================
        compteur_trames = 0
        
        while True:
            # Lire une trame WebSocket
            trame = lire_trame_websocket(connexion)
            
            if trame is None:
                print(f" Client #{num_client}: Connexion fermée")
                break
            
            compteur_trames += 1
            opcode = trame["opcode"]
            payload = trame["payload"]
            
            print(f"\n{'─'*60}")
            print(f" Client #{num_client} - Trame #{compteur_trames}")
            print(f"{'─'*60}")
            print(f"   Opcode: 0x{opcode:x} ({['continuation','text','binary','','','','','','close','ping','pong'][opcode] if opcode < 11 else 'inconnu'})")
            print(f"   Taille: {len(payload)} octets")
            
            # Si c'est une trame de fermeture (opcode 0x8)
            if opcode == 0x8:
                print(f"🚪 Client #{num_client}: Demande de fermeture")
                break
            
            # Afficher le payload en hexadécimal
            if len(payload) > 0:
                print(f"   Hex: {payload[:64].hex()}" + ("..." if len(payload) > 64 else ""))
                
                # Essayer de décoder en texte/JSON
                try:
                    texte = payload.decode('utf-8')
                    print(f"   Texte: {texte[:100]}" + ("..." if len(texte) > 100 else ""))
                    
                    # Essayer de parser en JSON
                    try:
                        donnees_json = json.loads(texte)
                        print("   JSON:")
                        for ligne in json.dumps(donnees_json, indent=4, ensure_ascii=False).split('\n')[:10]:
                            print(f"      {ligne}")
                    except:
                        pass
                except:
                    print("   (données binaires non-UTF8)")
            
            # ====================================================================
            # ÉTAPE 4 : RÉPONDRE (ECHO)
            # ====================================================================
            # Pour l'instant, on renvoie simplement le même payload (echo)
            # Dans l'étape 2, on devra analyser et répondre intelligemment
            
            trame_reponse = construire_trame_websocket(payload, opcode=0x2)
            connexion.sendall(trame_reponse)
            print(f" Client #{num_client}: Echo renvoyé ({len(payload)} octets)")
            
    except Exception as e:
        print(f" Client #{num_client}: Erreur - {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Nettoyer et fermer la connexion
        try:
            connexion.close()
        except:
            pass
        
        with lock:
            nombre_connexions -= 1
        
        print(f"\n{'='*60}")
        print(f" Client #{num_client} déconnecté (reste: {nombre_connexions})")
        print(f"{'='*60}\n")


# ============================================================================
# FONCTION 5 : Démarrer le serveur principal
# ============================================================================
def demarrer_serveur():
    """
    Fonction principale qui démarre le serveur et accepte les connexions.
    """
    
    # Créer une socket TCP/IP
    socket_serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Permettre de réutiliser l'adresse immédiatement (évite "Address already in use")
    socket_serveur.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Lier la socket à l'adresse et au port
    socket_serveur.bind((HOST, PORT))
    
    # Écouter les connexions entrantes (max 5 en attente)
    socket_serveur.listen(5)
    
    print("╔" + "═"*58 + "╗")
    print("║" + " SERVEUR WEBSOCKET MARTY V2 ".center(58) + "║")
    print("╠" + "═"*58 + "╣")
    print(f"║ 🌐 Adresse: {HOST}:{PORT}".ljust(59) + "║")
    print(f"║ 🚀 Statut:  EN ATTENTE DE CONNEXIONS".ljust(59) + "║")
    print(f"║ ⏰ Heure:   {time.strftime('%Y-%m-%d %H:%M:%S')}".ljust(59) + "║")
    print("╚" + "═"*58 + "╝\n")
    
    try:
        # Boucle principale : accepter les connexions en continu
        while True:
            # Attendre qu'un client se connecte (bloquant)
            connexion_client, adresse_client = socket_serveur.accept()
            
            # Créer un nouveau thread pour gérer ce client
            # daemon=True : le thread s'arrête quand le programme principal s'arrête
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
        print("Serveur arrêté proprement")


# ============================================================================
# POINT D'ENTRÉE DU PROGRAMME
# ============================================================================
if __name__ == "__main__":
    demarrer_serveur()
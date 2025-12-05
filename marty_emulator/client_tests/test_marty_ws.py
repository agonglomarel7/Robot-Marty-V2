# SCRIPT DE TEST - CLIENT MARTY V2
# Ce script teste la connexion avec le serveur WebSocket Marty
# Il permet de vérifier que le serveur répond correctement

from martypy import Marty
import time


SERVEUR_IP = "127.0.0.1"    # Localhost (ton PC)
SERVEUR_PORT = 8080          # Port du serveur WebSocket

print(f" Configuration:")
print(f" Serveur: {SERVEUR_IP}:{SERVEUR_PORT}")
print(f" Type: WiFi (WebSocket)\n")

# TEST 1 : CONNEXION AU SERVEUR
print(" TEST 1: Connexion au serveur")
#print("─" * 60)

try:
    print(" Tentative de connexion...")
    
    # Créer l'objet Marty et se connecter au serveur
    marty = Marty("wifi", SERVEUR_IP, port=SERVEUR_PORT)
    
    print(" CONNEXION RÉUSSIE !")
    print(f"   Client martypy connecté au serveur")
    print(f"   WebSocket actif\n")
    
except Exception as e:
    print(f" ÉCHEC DE LA CONNEXION")
    print(f" Erreur: {e}")
    print(f"\nVérifications:")
    print(f"   1. Le serveur est-il démarré ?")
    print(f"   2. Le port {SERVEUR_PORT} est-il disponible ?")
    print(f"   3. Pas de firewall qui bloque ?\n")
    exit(1)

# ============================================================================
# TEST 2 : ENVOI DE COMMANDES SIMPLES
# ============================================================================
print("\n TEST 2: Envoi de commandes")
#print("─" * 60)

# Liste des commandes à tester
commandes_test = [
    {
        "nom": "Walk (marche)",
        "fonction": lambda: marty.walk(1),
        "description": "Commande pour marcher 1 pas"
    },
    {
        "nom": "Get Ready (se préparer)",
        "fonction": lambda: marty.get_ready(),
        "description": "Commande pour position initiale"
    },
    {
        "nom": "Celebrate (célébrer)",
        "fonction": lambda: marty.celebrate(1),
        "description": "Animation de célébration"
    },
    {
        "nom": "Eyes (yeux)",
        "fonction": lambda: marty.eyes("normal"),
        "description": "Changer l'expression des yeux"
    }
]

resultats = []

for i, cmd in enumerate(commandes_test, 1):
    print(f"\n🔸 Commande {i}/{len(commandes_test)}: {cmd['nom']}")
    print(f"   Description: {cmd['description']}")
    print(f"   ⏳ Envoi en cours...", end=" ")
    
    try:
        # Exécuter la commande
        cmd['fonction']()
        
        print(f"   Statut: Envoyé sans erreur")
        resultats.append((cmd['nom'], " OK"))
        
    except Exception as e:
        print(f"   Erreur: {e}")
        resultats.append((cmd['nom'], f" Erreur: {str(e)[:30]}"))
    
    # Petite pause entre les commandes
    time.sleep(0.5)

# ============================================================================
# TEST 3 : RÉCUPÉRATION D'INFORMATIONS
# ============================================================================
print("\n\n TEST 3: Lecture d'informations")
#print("─" * 60)

infos_test = [
    {
        "nom": "Battery (batterie)",
        "fonction": lambda: marty.get_battery_voltage(),
        "unite": "V"
    },
    {
        "nom": "Accelerometer (accéléromètre)",
        "fonction": lambda: marty.get_accelerometer(),
        "unite": ""
    },
    {
        "nom": "Motor Current (courant moteur 0)",
        "fonction": lambda: marty.get_motor_current(0),
        "unite": "mA"
    }
]

for i, info in enumerate(infos_test, 1):
    print(f"\n🔹 Info {i}/{len(infos_test)}: {info['nom']}")
    print(f"   ⏳ Lecture en cours...", end=" ")
    
    try:
        # Récupérer l'info
        valeur = info['fonction']()
        
        print("")
        print(f"   Valeur: {valeur} {info['unite']}")
        resultats.append((info['nom'], f" {valeur} {info['unite']}"))
        
    except Exception as e:
        print("")
        print(f"   Erreur: {e}")
        resultats.append((info['nom'], f" Erreur: {str(e)[:30]}"))
    
    time.sleep(0.5)

# TEST 4 : DÉCONNEXION
print("\n\nTEST 4: Déconnexion")
print("─" * 60)

try:
    print(" Fermeture de la connexion...", end=" ")
    
    # Fermer la connexion proprement
    marty.close()
    
    print("   Connexion fermée proprement\n")
    resultats.append(("Déconnexion", " OK"))
    
except Exception as e:
    print("")
    print(f"   Erreur: {e}\n")
    resultats.append(("Déconnexion", f" Erreur"))

# RÉSUMÉ DES TESTS
print("\n" + "═" * 60)
print(" RÉSUMÉ DES TESTS ".center(60, "═"))
print("═" * 60 + "\n")

ok_count = sum(1 for _, status in resultats if status.startswith(""))
total_count = len(resultats)

for nom, status in resultats:
    print(f"  {status:40} | {nom}")

print("\n" + "─" * 60)
print(f"Score: {ok_count}/{total_count} tests réussis")

if ok_count == total_count:
    print(" TOUS LES TESTS SONT PASSÉS !")
elif ok_count > 0:
    print("  Certains tests ont échoué (normal pour l'étape 1)")
else:
    print(" Aucun test n'est passé")



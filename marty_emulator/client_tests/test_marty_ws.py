# TESTS AVANCÉS - SERVEUR D'ÉMULATION MARTY V2
# Ce script teste toutes les fonctionnalités du serveur d'émulation

from martypy import Marty
import time
import threading

print("╔" + "═"*68 + "╗")
print("║" + " TESTS AVANCÉS - SERVEUR ÉMULATION MARTY V2 ".center(68) + "║")
print("╚" + "═"*68 + "╝\n")

# CONFIGURATION
SERVEUR_IP = "127.0.0.1"
SERVEUR_PORT = 8080

# TEST 1 : CONNEXION SIMPLE
print("TEST 1: Connexion au serveur")
print("─" * 70)

try:
    print("Connexion en cours...", end=" ")
    marty = Marty("wifi", SERVEUR_IP, port=SERVEUR_PORT)
    print("")
    print("Client connecté avec succès\n")
except Exception as e:
    print(f"\nErreur: {e}\n")
    exit(1)

# TEST 2 : COMMANDES DE MOUVEMENT
print("\n🚶 TEST 2: Commandes de mouvement")
print("─" * 70)

mouvements = [
    ("Marche (1 pas)", lambda: marty.walk(1)),
    ("Position prête", lambda: marty.get_ready()),
    ("Danse (wiggle)", lambda: marty.wiggle()),
    ("Célébration", lambda: marty.celebrate(1)),
    ("Vague", lambda: marty.wave("left")),
    ("Cercle (circle)", lambda: marty.circle_dance()),
]

for nom, fonction in mouvements:
    print(f"\n🔸 {nom}")
    try:
        print(f"   Envoi...", end=" ")
        fonction()
        print("")
        print(f"   ✓ Commande acceptée")
        time.sleep(0.3)
    except Exception as e:
        print(f"\nErreur: {e}")

# TEST 3 : LECTURE DE CAPTEURS# ============================================================================
print("\n\n TEST 3: Lecture de capteurs")
print("─" * 70)

capteurs = [
    ("Batterie (voltage)", lambda: marty.get_battery_voltage(), "V"),
    ("Batterie (%)", lambda: marty.get_battery_remaining(), "%"),
    ("Accéléromètre", lambda: marty.get_accelerometer(), ""),
    ("Distance", lambda: marty.get_distance_sensor(), "mm"),
]

valeurs_capteurs = {}

for nom, fonction, unite in capteurs:
    print(f"\n🔹 {nom}")
    try:
        print(f"  Lecture...", end=" ")
        valeur = fonction()
        print("")
        print(f"   ✓ Valeur: {valeur} {unite}")
        valeurs_capteurs[nom] = valeur
        time.sleep(0.3)
    except Exception as e:
        print(f"\n  {str(e)[:50]}")
        valeurs_capteurs[nom] = None

# TEST 4 : CONTRÔLE DES MOTEURS
print("\n\n TEST 4: Contrôle des moteurs")
print("─" * 70)

moteurs_test = [
    ("Moteur 0 (Hip Left)", 0),
    ("Moteur 3 (Hip Right)", 3),
    ("Moteur 6 (Arm Left)", 6),
    ("Moteur 8 (Eyes)", 8),
]

for nom, motor_id in moteurs_test:
    print(f"\n {nom} (ID: {motor_id})")
    try:
        # Lire le courant du moteur
        print(f" Lecture courant...", end=" ")
        courant = marty.get_motor_current(motor_id)
        print(f"Courant: {courant} mA")
        
        time.sleep(0.2)
    except Exception as e:
        print(f"\n  {str(e)[:50]}")

# TEST 5 : COMMANDES DES YEUX
print("\n\nTEST 5: Expressions des yeux")
print("─" * 70)

expressions = ["normal", "angry", "excited", "wide"]

for expression in expressions:
    print(f"\n🔸 Expression: {expression}")
    try:
        print(f"   ⏳ Envoi...", end=" ")
        marty.eyes(expression)
        print(f"   Expression changée")
        time.sleep(0.3)
    except Exception as e:
        print(f"\n  {str(e)[:50]}")

# TEST 6 : GPIO (entrées/sorties)
print("\n\n TEST 6: GPIO (entrées/sorties)")
print("─" * 70)

try:
    print("\n Lecture de tous les GPIO")
    print(f"  Lecture...", end=" ")
    gpio_states = marty.get_gpio()
    print(f"   États GPIO: {gpio_states}")
except Exception as e:
    print(f"\n  {str(e)[:50]}")

# TEST 7 : TEST DE STRESS (optionnel)
print("\n\n TEST 7: Test de stress (10 commandes rapides)")
print("─" * 70)

print("\n Envoi de 10 commandes consécutives...\n")

erreurs = 0
for i in range(10):
    try:
        print(f"   [{i+1}/10] ", end="")
        marty.walk(1)
        print(" ", end=" ")
        if (i + 1) % 5 == 0:
            print()
        time.sleep(0.1)
    except Exception as e:
        print(f" ", end=" ")
        erreurs += 1

print(f"\n\n Résultat: {10 - erreurs}/10 réussies")

# TEST 8 : MULTI-CONNEXIONS (optionnel)
print("\n\nTEST 8: Test multi-connexions")
print("─" * 70)
print(" Ce test crée 3 connexions simultanées pour tester le threading\n")

def tester_connexion_parallele(numero):
    """Fonction qui teste une connexion dans un thread séparé"""
    try:
        print(f" Robot #{numero}: Connexion...", end=" ")
        m = Marty("wifi", SERVEUR_IP, port=SERVEUR_PORT)
        
        # Envoyer quelques commandes
        for i in range(3):
            m.walk(1)
            time.sleep(0.2)
        
        print(f"    Robot #{numero}: Commandes envoyées ")
        
        m.close()
        print(f"    Robot #{numero}: Déconnecté ")
        
    except Exception as e:
        print(f" Robot #{numero}: {e}")

# Créer 3 threads
threads = []
for i in range(1, 4):
    t = threading.Thread(target=tester_connexion_parallele, args=(i,))
    threads.append(t)
    t.start()
    time.sleep(0.5)  # Petit délai entre les connexions

# Attendre que tous les threads se terminent
for t in threads:
    t.join()

print("\n Test multi-connexions terminé")

# TEST 9 : DÉCONNEXION
print("\n\n TEST 9: Déconnexion propre")
print("─" * 70)

try:
    print("Fermeture de la connexion...", end=" ")
    marty.close()
    print("  Connexion fermée proprement\n")
except Exception as e:
    print(f"\n   Erreur: {e}\n")

# RÉSUMÉ FINAL
print("\n" + "═" * 70)
print(" RÉSUMÉ DES TESTS ".center(70, "═"))
print("═" * 70 + "\n")

print(" CAPTEURS LUS:")
print("─" * 70)
for nom, valeur in valeurs_capteurs.items():
    if valeur is not None:
        print(f"    {nom}: {valeur}")
    else:
        print(f" {nom}: Non disponible")


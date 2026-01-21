from martypy import Marty

# On se connecte au serveur
m = Marty("WiFi", "127.0.0.1", port=8080) # adresse locale
print("Connexion réussie !")

# On envoie une commande simple
try:
    m.walk(1)   # marche 1 pas
except Exception as e:
    print("Erreur lors de la commande :", e)

print("Terminé.")


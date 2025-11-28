# Robot-Marty-V2 Jumeau Numérique
# Marty V2 Emulator

Serveur d'émulation TCP pour le robot Marty V2 - Réception et analyse des trames de communication martypy.

## Installation
```bash
# Créer l'environnement virtuel
python -m venv venv

# Activer (Linux/Mac)
source venv/bin/activate

# Activer (Windows)
venv\Scripts\activate

# Installer les dépendances
pip install martypy
```

## Utilisation

**Démarrer le serveur :**
```bash
sudo python server/server_marty.py
```

**Tester avec martypy :**
```bash
python client_tests/test_martypy_connect.py
```
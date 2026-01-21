# Robot Marty V2 – Émulateur & Serveur RICSerial

Ce projet vise à émuler un robot **Marty v2** afin de permettre la communication avec la librairie officielle **martypy**, en implémentant le protocole **RICSerial encapsulé dans WebSocket**.

---

## 🔧 Prérequis

- Python 3.8+
- Git
- Linux recommandé (testé sous Ubuntu)

---

## 📥 Cloner le projet

```bash
git clone git@github.com:agonglomarel7/Robot-Marty-V2.git
cd Robot-Marty-V2


python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cd server
python3 main.py

cd Robot-Marty-V2/client_cli
python3 test_marty_ws.py

---
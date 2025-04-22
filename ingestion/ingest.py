import json, time, os
from pymongo import MongoClient

def tail_log():
    # Chemins possibles du fichier de log
    paths = [
        "/cowrie/cowrie-git/var/log/cowrie.json",
        "/cowrie/cowrie-git/var/log/cowrie/cowrie.json"
    ]
    
    # Trouver le premier chemin existant
    log_path = None
    for path in paths:
        if os.path.exists(path):
            log_path = path
            print(f"Utilisation du chemin de log: {log_path}")
            break
    
    if not log_path:
        print("Aucun fichier de log trouvé! Vérification continue des chemins:")
        while not log_path:
            for path in paths:
                if os.path.exists(path):
                    log_path = path
                    print(f"Fichier de log trouvé: {log_path}")
                    break
            if not log_path:
                print("Attente de la création du fichier de log...")
                time.sleep(5)
    
    client = MongoClient("mongodb://mongo:27017/")
    db = client.cowrie
    col = db.events

    print(f"Surveillance du fichier: {log_path}")
    with open(log_path, "r") as f:
        f.seek(0, 2)  # Aller à la fin du fichier
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            try:
                evt = json.loads(line)
                print(f"Événement capturé: {evt.get('eventid', 'unknown')}")
                col.insert_one(evt)
                print(f"Événement inséré dans MongoDB")
            except json.JSONDecodeError as e:
                print(f"Erreur de parsing JSON: {e}")
                print(f"Ligne problématique: {line}")
            except Exception as e:
                print(f"Erreur de traitement: {e}")

if __name__ == "__main__":
    tail_log()

import json, time, os
from pymongo import MongoClient
import sys

def tail_log():
    # Chemins possibles du fichier de log
    paths = [
        "/cowrie/cowrie-git/var/log/cowrie.json",
        "/cowrie/cowrie-git/var/log/cowrie/cowrie.json"
    ]
    
    print(f"Démarrage du service d'ingestion, recherche des fichiers de log...")
    
    # Trouver le premier chemin existant
    log_path = None
    while not log_path:
        for path in paths:
            print(f"Vérification de {path}...")
            if os.path.exists(path):
                log_path = path
                print(f"Fichier de log trouvé: {log_path}")
                break
        if not log_path:
            print("Aucun fichier de log trouvé! Nouvelle vérification dans 5 secondes...")
            sys.stdout.flush()
            time.sleep(5)
    
    print(f"Connexion à MongoDB...")
    sys.stdout.flush()
    
    client = MongoClient("mongodb://mongo:27017/")
    db = client.cowrie
    col = db.events

    print(f"Surveillance du fichier: {log_path}")
    sys.stdout.flush()
    
    with open(log_path, "r") as f:
        print(f"Fichier ouvert avec succès, surveillance des nouvelles lignes...")
        sys.stdout.flush()
        f.seek(0, 2)  # Aller à la fin du fichier
        
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            try:
                print(f"Nouvelle ligne détectée: {line[:50]}...")
                sys.stdout.flush()
                evt = json.loads(line)
                print(f"Événement capturé: {evt.get('eventid', 'unknown')}")
                sys.stdout.flush()
                col.insert_one(evt)
                print(f"Événement inséré dans MongoDB")
                sys.stdout.flush()
            except json.JSONDecodeError as e:
                print(f"Erreur de parsing JSON: {e}")
                print(f"Ligne problématique: {line}")
                sys.stdout.flush()
            except Exception as e:
                print(f"Erreur de traitement: {e}")
                sys.stdout.flush()

if __name__ == "__main__":
    try:
        print("Démarrage du service d'ingestion...")
        sys.stdout.flush()
        tail_log()
    except Exception as e:
        print(f"Erreur fatale: {e}")
        sys.stdout.flush()
        raise

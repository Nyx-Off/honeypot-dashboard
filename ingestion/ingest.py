#!/usr/bin/env python3
import json, time, os, sys
from pymongo import MongoClient
from datetime import datetime

def main():
    print("Démarrage du service d'ingestion en continu...")
    sys.stdout.flush()

    # Chemin du fichier de log Cowrie
    log_path = "/cowrie/cowrie-git/var/log/cowrie.json"
    
    # Vérification du fichier log
    while not os.path.exists(log_path):
        print(f"Attente de la création du fichier log: {log_path}")
        sys.stdout.flush()
        time.sleep(5)
    
    print(f"Fichier log trouvé: {log_path} ({os.path.getsize(log_path)} octets)")
    sys.stdout.flush()
    
    # Connexion MongoDB
    try:
        client = MongoClient("mongodb://mongo:27017/", serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("Connexion MongoDB établie avec succès")
        sys.stdout.flush()
    except Exception as e:
        print(f"ERREUR MongoDB: {e}")
        sys.exit(1)
    
    db = client.cowrie
    events = db.events
    
    # Importer les événements existants
    with open(log_path, 'r') as f:
        content = f.read()
        lines = [line for line in content.split('\n') if line.strip()]
        
        print(f"Importation de {len(lines)} événements existants...")
        sys.stdout.flush()
        
        imported_count = 0
        for line in lines:
            try:
                event = json.loads(line)
                # Créer un horodatage Python à partir de la chaîne ISO
                if 'timestamp' in event:
                    event['datetime'] = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                
                # Insérer dans MongoDB s'il n'existe pas déjà
                # Utiliser une requête upsert avec le session_id et l'eventid comme identifiants uniques
                if 'session' in event and 'eventid' in event:
                    filter_query = {'session': event['session'], 'eventid': event['eventid']}
                    events.update_one(filter_query, {'$setOnInsert': event}, upsert=True)
                else:
                    # Fallback pour les événements sans session ou eventid
                    events.insert_one(event)
                
                imported_count += 1
                if imported_count % 10 == 0:
                    print(f"Importation: {imported_count}/{len(lines)}")
                    sys.stdout.flush()
            except json.JSONDecodeError as e:
                print(f"Erreur de parsing JSON: {e}")
            except Exception as e:
                print(f"Erreur d'insertion: {e}")
        
        print(f"Importation initiale terminée: {imported_count} événements importés")
        print(f"Nombre total d'événements dans MongoDB: {events.count_documents({})}")
        sys.stdout.flush()
        
        # Surveillance continue des nouvelles entrées
        print("Démarrage de la surveillance en temps réel...")
        sys.stdout.flush()
        
        # Se positionner à la fin du fichier
        f.seek(0, 2)
        
        while True:
            # Lire les nouvelles lignes
            line = f.readline()
            
            if not line:
                time.sleep(0.1)
                continue
            
            line = line.strip()
            if not line:
                continue
            
            try:
                event = json.loads(line)
                
                # Ajouter un champ datetime pour faciliter les requêtes
                if 'timestamp' in event:
                    event['datetime'] = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                
                # Utiliser une requête upsert
                if 'session' in event and 'eventid' in event:
                    filter_query = {'session': event['session'], 'eventid': event['eventid']}
                    result = events.update_one(filter_query, {'$setOnInsert': event}, upsert=True)
                    
                    if result.upserted_id:
                        print(f"Nouvel événement inséré: {event.get('eventid', 'unknown')} pour la session {event.get('session', 'unknown')}")
                else:
                    events.insert_one(event)
                    print(f"Nouvel événement inséré: {event.get('eventid', 'unknown')}")
                
                sys.stdout.flush()
            except json.JSONDecodeError as e:
                print(f"Erreur de parsing JSON: {e}")
            except Exception as e:
                print(f"Erreur de traitement: {e}")
                sys.stdout.flush()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Service d'ingestion arrêté par l'utilisateur")
    except Exception as e:
        print(f"Erreur fatale: {e}")
        sys.exit(1)

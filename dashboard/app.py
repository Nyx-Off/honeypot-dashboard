from flask import Flask, render_template, jsonify, json
from flask_socketio import SocketIO
from pymongo import MongoClient
from bson import ObjectId, json_util
import threading, time
import geoip2.database
import os

# Classe pour encoder correctement les ObjectId en JSON
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super(JSONEncoder, self).default(obj)

# Création de l'application Flask
app = Flask(__name__)
app.json_encoder = JSONEncoder  # Utiliser notre encodeur personnalisé
socketio = SocketIO(app, json=JSONEncoder)

# Connexion à MongoDB
try:
    client = MongoClient("mongodb://mongo:27017/")
    db = client.cowrie
    events_collection = db.events
    print("Connexion MongoDB OK")
except Exception as e:
    print(f"ERREUR MongoDB: {e}")
    raise

# Chargement de la base GeoIP si disponible
try:
    geo_db_path = "/app/GeoLite2-City.mmdb"
    if os.path.exists(geo_db_path):
        geo_reader = geoip2.database.Reader(geo_db_path)
        have_geo = True
        print("Base de données GeoIP chargée avec succès")
    else:
        have_geo = False
        print("Fichier GeoIP non trouvé : " + geo_db_path)
        print("La géolocalisation sera désactivée")
except Exception as e:
    have_geo = False
    print(f"Erreur lors du chargement de la base GeoIP: {e}")
    print("La géolocalisation sera désactivée")

# Fonction pour enrichir un événement avec des informations de géolocalisation
def enrich_event(event):
    # Conversion de l'ObjectId en chaîne
    if '_id' in event:
        event['_id'] = str(event['_id'])
    
    # Ajout des informations de géolocalisation si possible
    if have_geo and 'src_ip' in event and event['src_ip']:
        try:
            geo_data = geo_reader.city(event['src_ip'])
            event['geo'] = {
                'country_name': geo_data.country.name,
                'country_code': geo_data.country.iso_code,
                'city': geo_data.city.name,
                'latitude': geo_data.location.latitude,
                'longitude': geo_data.location.longitude
            }
        except Exception as e:
            event['geo'] = {
                'country_name': "Unknown",
                'country_code': "XX",
                'city': "Unknown",
                'latitude': 0,
                'longitude': 0
            }
    
    return event

# Fonction pour surveiller les nouveaux événements
def watch_events():
    print("Démarrage de la surveillance des événements...")
    last_id = None
    
    while True:
        try:
            # Requête MongoDB pour les nouveaux événements
            query = {"_id": {"$gt": last_id}} if last_id else {}
            
            # Trier par _id pour garantir l'ordre
            cursor = events_collection.find(query).sort("_id", 1)
            new_events = list(cursor)
            
            if new_events:
                print(f"Trouvé {len(new_events)} nouveaux événements")
                
                for event in new_events:
                    # Mettre à jour le dernier ID
                    last_id = event["_id"]
                    
                    # Enrichir l'événement
                    enriched_event = enrich_event(event)
                    
                    # Envoyer l'événement aux clients connectés
                    socketio.emit("new_event", enriched_event)
                    print(f"Événement émis: {event.get('eventid', 'unknown')}")
            
            # Attendre avant la prochaine vérification
            time.sleep(1)
            
        except Exception as e:
            print(f"Erreur lors de la surveillance: {e}")
            time.sleep(5)  # Attendre plus longtemps en cas d'erreur

# Route principale pour afficher le dashboard
@app.route("/")
def index():
    return render_template("index.html")

# API pour récupérer des événements
@app.route("/api/events")
def get_events():
    try:
        # Récupérer les 100 derniers événements
        events = list(events_collection.find().sort("_id", -1).limit(100))
        
        # Enrichir les événements
        enriched_events = [enrich_event(event) for event in events]
        
        # Utiliser json_util pour gérer les types MongoDB
        return json_util.dumps(enriched_events)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API pour obtenir des statistiques
@app.route("/api/stats")
def get_stats():
    try:
        # Nombre total d'événements
        total_events = events_collection.count_documents({})
        
        # Nombre d'IPs uniques
        unique_ips = len(events_collection.distinct("src_ip"))
        
        # Nombre de tentatives d'authentification
        auth_attempts = events_collection.count_documents({
            "eventid": {"$regex": "auth|login"}
        })
        
        # Nombre de sessions
        sessions = len(events_collection.distinct("session"))
        
        stats = {
            "total_events": total_events,
            "unique_ips": unique_ips,
            "auth_attempts": auth_attempts,
            "sessions": sessions
        }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Gestionnaire de connexion WebSocket
@socketio.on("connect")
def on_connect():
    print("Client connecté")
    # Démarrer la surveillance en arrière-plan
    thread = threading.Thread(target=watch_events)
    thread.daemon = True
    thread.start()

# Point d'entrée de l'application
if __name__ == "__main__":
    print("Démarrage du dashboard sur 0.0.0.0:5000")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)

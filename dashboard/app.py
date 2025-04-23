from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
from pymongo import MongoClient
import threading, time, json, os
import geoip2.database 

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')

GEOIP_DB_PATH = "/app/GeoLite2-City.mmdb"
geoip_reader = None

# Vérification et initialisation de la base GeoIP2
if os.path.exists(GEOIP_DB_PATH):
    try:
        geoip_reader = geoip2.database.Reader(GEOIP_DB_PATH)
        print(f"Base de données GeoIP2 chargée: {GEOIP_DB_PATH}")
    except Exception as e:
        print(f"Erreur de chargement de la base GeoIP2: {e}")
else:
    print(f"Fichier de base de données GeoIP2 non trouvé: {GEOIP_DB_PATH}")

# Connexion à MongoDB
try:
    client = MongoClient("mongodb://mongo:27017/")
    db = client.cowrie
    events_collection = db.events
    print("Connexion MongoDB OK")
except Exception as e:
    print(f"ERREUR MongoDB: {e}")
    raise

def get_ip_location(ip):
    """Obtient la géolocalisation d'une adresse IP"""
    if not geoip_reader or not ip:
        return None
    
    try:
        response = geoip_reader.city(ip)
        return {
            "country_code": response.country.iso_code,
            "country_name": response.country.name,
            "city": response.city.name,
            "latitude": response.location.latitude,
            "longitude": response.location.longitude
        }
    except Exception as e:
        print(f"Erreur de géolocalisation pour IP {ip}: {e}")
        return None


def format_event(event):
    """Convertit les ObjectId en chaînes pour la sérialisation JSON"""
    if '_id' in event:
        event['_id'] = str(event['_id'])
    if 'src_ip' in event and geoip_reader:
        geoip_info = get_ip_location(event['src_ip'])
        if geoip_info:
            event['geoip'] = geoip_info

    return event

def watch_events():
    """Surveille les nouveaux événements et les envoie par WebSocket"""
    print("Démarrage de la surveillance des événements...")
    last_id = None
    
    while True:
        try:
            # Construction de la requête pour les nouveaux événements
            query = {}
            if last_id:
                query['_id'] = {'$gt': last_id}
            
            # Récupération des nouveaux événements
            new_events = list(events_collection.find(query).sort('_id', 1))
            
            if new_events:
                print(f"Trouvé {len(new_events)} nouveaux événements")
                
                for event in new_events:
                    # Conservation du dernier ID
                    last_id = event['_id']
                    
                    # Formatage de l'événement pour JSON
                    formatted_event = format_event(event)
                    
                    # Envoi de l'événement aux clients connectés
                    socketio.emit('new_event', formatted_event)
                    print(f"Événement émis: {event.get('eventid', 'unknown')}")
            
            # Attente avant la prochaine vérification
            time.sleep(1)
            
        except Exception as e:
            print(f"Erreur lors de la surveillance: {e}")
            time.sleep(5)

@app.route('/')
def index():
    """Page d'accueil du dashboard"""
    return render_template('index.html')

@app.route('/api/events')
def get_events():
    """API pour récupérer les derniers événements"""
    try:
        # Récupération des 100 derniers événements
        events = list(events_collection.find().sort('_id', -1).limit(100))
        
        # Conversion en format JSON
        formatted_events = [format_event(event) for event in events]
        
        return jsonify(formatted_events)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/events/clear', methods=['POST'])
def clear_events():
    """API pour supprimer tous les événements de la base de données"""
    try:
        # Suppression de tous les documents de la collection events
        result = events_collection.delete_many({})
        
        # Retourne le nombre de documents supprimés
        return jsonify({'success': True, 'deleted_count': result.deleted_count}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@socketio.on('connect')
def on_connect():
    """Gestion de la connexion d'un client WebSocket"""
    print("Client connecté")
    # Démarrage de la surveillance en arrière-plan
    thread = threading.Thread(target=watch_events)
    thread.daemon = True
    thread.start()

if __name__ == '__main__':
    print("Démarrage du dashboard sur 0.0.0.0:5000")
    socketio.run(app, host='0.0.0.0', port=5000)

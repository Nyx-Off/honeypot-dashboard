from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
from pymongo import MongoClient
import threading, time, json

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')

# Connexion à MongoDB
try:
    client = MongoClient("mongodb://mongo:27017/")
    db = client.cowrie
    events_collection = db.events
    print("Connexion MongoDB OK")
except Exception as e:
    print(f"ERREUR MongoDB: {e}")
    raise

def format_event(event):
    """Convertit les ObjectId en chaînes pour la sérialisation JSON"""
    if '_id' in event:
        event['_id'] = str(event['_id'])
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

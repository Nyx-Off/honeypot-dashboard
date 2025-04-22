from flask import Flask, render_template
from flask_socketio import SocketIO
from pymongo import MongoClient
import threading, time
import geoip2.database

app = Flask(__name__)
socketio = SocketIO(app)
client = MongoClient("mongodb://mongo:27017/")
col = client.cowrie.events
geo = geoip2.database.Reader("/app/GeoLite2-City.mmdb")  # télécharge sur MaxMind

def watch_events():
    last_id = None
    while True:
        query = {"_id": {"$gt": last_id}} if last_id else {}
        docs = list(col.find(query).sort("_id",1))
        for d in docs:
            ip = d.get("src_ip")
            if ip:
                try:
                    loc = geo.city(ip)
                    d["geo"] = {
                        "lat": loc.location.latitude,
                        "lon": loc.location.longitude
                    }
                except:
                    d["geo"] = {}
            socketio.emit("new_event", d)
            last_id = d["_id"]
        time.sleep(1)

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("connect")
def start_push():
    threading.Thread(target=watch_events, daemon=True).start()

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)


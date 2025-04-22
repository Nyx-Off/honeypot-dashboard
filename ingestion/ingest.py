import json, time
from pymongo import MongoClient

def tail_log(path="/cowrie/cowrie-git/log/cowrie.json"):
    client = MongoClient("mongodb://mongo:27017/")
    db = client.cowrie
    col = db.events

    with open(path, "r") as f:
        f.seek(0,2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            try:
                evt = json.loads(line)
                col.insert_one(evt)
            except Exception as e:
                print("Parse error:", e)

if __name__ == "__main__":
    tail_log()


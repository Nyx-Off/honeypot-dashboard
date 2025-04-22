# Utilise une image Python légère
FROM python:3.11-slim

# Définit le répertoire de travail
WORKDIR /app

# Copie le fichier de dépendances et installe-les
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie le reste de l’application dans le conteneur
COPY app.py .
COPY templates/ ./templates/

# (Optionnel) Si tu as téléchargé la base GeoLite2-City.mmdb
# place-la aussi dans dashboard/ puis décommente la ligne ci‑dessous :
# COPY GeoLite2-City.mmdb .

# Expose le port de l’API Flask/SocketIO
EXPOSE 5000

# Lance l’application
CMD ["python", "app.py"]

# 🍯 Honeypot Dashboard

Un tableau de bord en temps réel pour surveiller et analyser les tentatives d'attaques sur votre honeypot Cowrie.

![Honeypot Dashboard](https://raw.githubusercontent.com/Nyx-Off/honeypot-dashboard/main/preview.png)

## 🔍 Présentation

Honeypot Dashboard est un système complet permettant de collecter, stocker et visualiser en temps réel les tentatives d'attaques sur votre honeypot [Cowrie](https://github.com/cowrie/cowrie). Le projet utilise Docker pour faciliter le déploiement et comprend:

- Un conteneur **Cowrie** configuré pour capturer les tentatives d'intrusion SSH et Telnet
- Un système d'**ingestion** qui traite les logs et les stocke dans MongoDB
- Une **base de données MongoDB** pour stocker tous les événements capturés
- Un **tableau de bord web** interactif développé avec Flask et SocketIO

Ce tableau de bord vous permet de visualiser les attaques en temps réel, d'analyser leur origine géographique, et de consulter les détails techniques de chaque tentative d'intrusion.

## 🏗️ Architecture

Le système est composé de quatre conteneurs Docker interconnectés:

1. **cowrie**: Honeypot SSH/Telnet qui simule un système vulnérable
2. **mongo**: Base de données pour stocker les événements capturés
3. **ingestion**: Service qui monitore les logs de Cowrie et les intègre à MongoDB
4. **dashboard**: Interface web pour visualiser et analyser les données

```
┌─────────┐     ┌───────────┐     ┌───────┐     ┌───────────┐
│ Attaque │────>│   Cowrie  │────>│ Mongo │<────│ Dashboard │
└─────────┘     └───────────┘     └───────┘     └───────────┘
                      │              ▲
                      │              │
                      └──────────────┘
                         ingestion
```

## 🛠️ Prérequis

- [Docker](https://docs.docker.com/get-docker/) et [Docker Compose](https://docs.docker.com/compose/install/)
- Ports 2222 (SSH), 2223 (Telnet), et 5000 (Dashboard) disponibles
- Environ 1 Go d'espace disque libre
- (Optionnel) Base de données GeoIP2 pour la géolocalisation des attaquants

## 📦 Installation

1. Clonez ce dépôt:

```bash
git clone https://github.com/Nyx-Off/honeypot-dashboard.git
cd honeypot-dashboard
```

2. Assurez-vous que les permissions sont correctement configurées pour les fichiers de log:

```bash
mkdir -p cowrie/log
chmod 777 cowrie/log  # Important: Cowrie doit pouvoir écrire dans ce dossier
```

3. Démarrez les conteneurs avec Docker Compose:

```bash
docker-compose up -d
```

4. Vérifiez que tous les conteneurs sont en cours d'exécution:

```bash
docker-compose ps
```

5. Accédez au tableau de bord à l'adresse: http://localhost:5000

## ⚙️ Configuration

### Configuration de Cowrie

Le honeypot Cowrie est configuré via le fichier `cowrie/cowrie.cfg`. Voici quelques paramètres importants:

- **Ports d'écoute**: Par défaut, 2222 pour SSH et 2223 pour Telnet
- **Utilisateurs factices**: Configurés dans `cowrie/etc/userdb.txt` 
- **Système de fichiers simulé**: Stocké dans `cowrie/data/rootfs/`
- **Clés SSH**: Générées dans `cowrie/keys/`

Pour personnaliser davantage votre honeypot:

1. Modifiez les utilisateurs et mots de passe dans `cowrie/etc/userdb.txt`:
   ```
   user2:password2:1001:1001::/home/user2:/bin/bash
   admin:admin123:0:0::/root:/bin/bash
   ```

2. Ajoutez du contenu au système de fichiers simulé dans `cowrie/data/rootfs/`

3. Modifiez les bannières et messages d'accueil dans `cowrie/cowrie.cfg`

### Base de données GeoIP

Pour activer la géolocalisation des attaquants, vous devez installer la base de données GeoLite2-City:

1. Téléchargez la base de données depuis [MaxMind](https://dev.maxmind.com/geoip/geolite2-free-geolocation-data) (inscription gratuite requise)
2. Placez le fichier `GeoLite2-City.mmdb` dans le dossier `dashboard/`
3. Redémarrez le conteneur dashboard:
   ```bash
   docker-compose restart dashboard
   ```

## 🚀 Utilisation

Une fois le système démarré, le honeypot Cowrie commencera à écouter les connexions entrantes:

- **SSH**: Sur le port 2222 (`ssh -p 2222 user1@votre-ip`)
- **Telnet**: Sur le port 2223 (`telnet votre-ip 2223`)

Toutes les tentatives de connexion seront enregistrées et apparaîtront en temps réel sur le tableau de bord.

### Tableau de bord

Le tableau de bord est accessible à l'adresse http://localhost:5000 et offre les fonctionnalités suivantes:

- **Vue d'ensemble**: Nombre total d'événements, IP uniques, tentatives de login, sessions
- **Graphiques**: Distribution des types d'attaques et origine géographique
- **Événements en temps réel**: Liste des dernières tentatives d'intrusion
- **Détails**: Informations complètes sur chaque événement

### Nettoyage des données

Pour effacer les données collectées:

1. Cliquez sur le bouton "Vider" dans l'interface du tableau de bord, ou
2. Exécutez la commande suivante:
   ```bash
   curl -X POST http://localhost:5000/api/events/clear
   ```

## 🌟 Fonctionnalités

- **Détection en temps réel** des tentatives d'attaque SSH et Telnet
- **Visualisation géographique** de l'origine des attaques
- **Analyse statistique** des types d'événements
- **Détails techniques** sur chaque tentative (commandes exécutées, identifiants utilisés)
- **Interface responsive** accessible depuis desktop et mobile
- **Notification en temps réel** via WebSockets

## 🔧 Résolution des problèmes courants

### Les logs de Cowrie ne sont pas générés

Vérifiez les permissions du dossier de logs:

```bash
chmod 777 cowrie/log
```

### Le service d'ingestion ne se connecte pas à MongoDB

Vérifiez l'état des conteneurs:

```bash
docker-compose logs ingestion
```

Assurez-vous que le conteneur MongoDB est démarré avant le service d'ingestion.

### La géolocalisation ne fonctionne pas

Vérifiez que le fichier `GeoLite2-City.mmdb` est présent dans le dossier `dashboard/` et que le conteneur dashboard a été redémarré après son ajout.

### Les événements en temps réel ne s'affichent pas

Vérifiez la connexion WebSocket dans la console de votre navigateur. Si nécessaire, redémarrez le conteneur dashboard:

```bash
docker-compose restart dashboard
```

## 📄 Licence

Ce projet est distribué sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

Développé par [Samy - Nyx](https://github.com/Nyx-Off) | © 2025

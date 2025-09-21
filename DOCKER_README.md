# 🐳 Déploiement Docker - Système IoT+IA Prédictif

## 🎯 Vue d'ensemble

Ce système IoT+IA complet est maintenant **entièrement conteneurisé** avec Docker pour un déploiement simplifié et reproductible.

## 🏗️ Architecture Docker

```
┌─────────────────────────────────────────────────┐
│               DOCKER COMPOSE                    │
├─────────────────────────────────────────────────┤
│  🔄 mosquitto   │  🧠 backend    │  📊 dashboard │
│  (MQTT Broker)  │  (FastAPI+ML)  │  (Streamlit) │
│                 │                │              │
│  Port: 1883     │  Port: 8000    │  Port: 8501  │
├─────────────────┼────────────────┼──────────────┤
│              🏭 simulator                       │
│           (3 Machines IoT)                      │
└─────────────────────────────────────────────────┘
```

## 🚀 Lancement Rapide

### Option 1: Script Automatique (Recommandé)

```bash
# Windows
./start_docker.bat

# Linux/Mac
python3 start_docker.py
```

### Option 2: Docker Compose Manuel

```bash
# Construction des images
docker compose build

# Démarrage des services
docker compose up -d

# Voir les logs
docker compose logs -f

# Arrêt
docker compose down
```

## 📋 Prérequis

- **Docker Desktop** installé et démarré
- **Python 3.8+** (pour le script de lancement)
- **8 GB RAM** recommandés
- **Ports libres**: 1883, 8000, 8501

## 🔧 Services Conteneurisés

### 🔄 MQTT Broker (Mosquitto)
- **Image**: `eclipse-mosquitto:2.0`
- **Port**: 1883
- **Config**: Authentification désactivée pour dev
- **Health**: Test de connexion MQTT

### 🧠 Backend API (FastAPI + ML)
- **Image**: Custom Python 3.11
- **Port**: 8000
- **ML**: Isolation Forest pré-entraîné
- **Health**: `/health` endpoint
- **Data**: SQLite persistant

### 📊 Dashboard (Streamlit)
- **Image**: Custom Python 3.11
- **Port**: 8501
- **Features**: Temps réel, auto-refresh 3s
- **Health**: Ping HTTP

### 🏭 Simulateur IoT
- **Image**: Custom Python 3.11
- **Machines**: 3 simulées (M001, M002, M003)
- **Data**: Télémétrie réaliste + pannes
- **Health**: Processus actif

## 📊 Accès aux Services

| Service | URL | Description |
|---------|-----|-------------|
| **Dashboard** | http://localhost:8501 | Interface temps réel |
| **API Backend** | http://localhost:8000 | API REST + docs |
| **API Docs** | http://localhost:8000/docs | Documentation Swagger |
| **MQTT** | localhost:1883 | Broker de messages |

## 🔍 Monitoring

### Vérifier le statut
```bash
docker compose ps
```

### Voir les logs
```bash
# Tous les services
docker compose logs -f

# Service spécifique
docker compose logs -f backend
docker compose logs -f dashboard
docker compose logs -f simulator
```

### Health Checks
Tous les services ont des health checks intégrés :
```bash
docker compose ps --format "table {{.Service}}\t{{.Status}}\t{{.State}}"
```

## 🐛 Dépannage

### Problèmes courants

**Services qui ne démarrent pas :**
```bash
# Nettoyer et redémarrer
docker compose down
docker system prune -f
docker compose up --build
```

**Ports occupés :**
```bash
# Vérifier les ports utilisés
netstat -an | findstr "8000\|8501\|1883"

# Arrêter les processus conflictuels
docker compose down
```

**Logs d'erreur :**
```bash
# Voir les logs détaillés
docker compose logs --tail=50 [service-name]
```

### Reconstruction complète
```bash
# Supprimer tout et recommencer
docker compose down -v
docker rmi $(docker images -q)
docker compose up --build
```

## 📁 Structure des Fichiers Docker

```
.
├── docker-compose.yml          # Orchestration principale
├── start_docker.py            # Script de lancement Python
├── start_docker.bat           # Script de lancement Windows
├── backend/
│   ├── Dockerfile             # Image Backend API
│   └── requirements.txt       # Dépendances Python
├── dashboard/
│   ├── Dockerfile             # Image Dashboard
│   └── requirements.txt       # Dépendances Streamlit
├── simulator/
│   ├── Dockerfile             # Image Simulateur
│   └── requirements.txt       # Dépendances IoT
└── data/                      # Volume persistant SQLite
```

## 🔧 Configuration Avancée

### Variables d'environnement
Modifiez `docker-compose.yml` pour :
- Changer les ports
- Configurer les ressources
- Ajuster les timeouts

### Volumes persistants
- `./data` : Base de données SQLite
- Configuration MQTT dans le conteneur

### Mise à l'échelle
```bash
# Multiplier les simulateurs
docker compose up --scale simulator=5
```

## 🚀 Déploiement Production

### Optimisations recommandées
1. **Sécurité MQTT** : Activer l'authentification
2. **HTTPS** : Proxy nginx pour SSL
3. **Monitoring** : Ajouter Prometheus/Grafana
4. **Logging** : Centraliser avec ELK stack

### Variables d'environnement production
```yaml
environment:
  - ENVIRONMENT=production
  - DEBUG=false
  - MQTT_AUTH=true
```

## 📈 Performance

### Ressources par défaut
- **Backend**: 512MB RAM, 0.5 CPU
- **Dashboard**: 256MB RAM, 0.25 CPU  
- **Simulator**: 128MB RAM, 0.1 CPU
- **MQTT**: 64MB RAM, 0.1 CPU

### Optimisation
```yaml
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '1.0'
```

## ✅ Tests de Validation

1. **Health Checks** : Tous verts
2. **Dashboard** : Données temps réel visibles
3. **API** : `/health` retourne 200
4. **MQTT** : Messages IoT reçus
5. **ML** : Prédictions fonctionnelles

---

## 🎉 Résultat Final

**Système IoT+IA entièrement conteneurisé** avec :
- ✅ Déploiement one-click avec Docker Compose
- ✅ Health monitoring intégré
- ✅ Données persistantes
- ✅ Interface temps réel
- ✅ ML prédictif opérationnel
- ✅ Logs centralisés
- ✅ Arrêt propre

**Commande magique** : `./start_docker.bat` et tout fonctionne !
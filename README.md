# 🏭 Système IoT Maintenance Prédictive Industrielle

Plateforme complète de maintenance prédictive avec capteurs industriels, agrégation MQTT temps réel, intelligence artificielle et interfaces utilisateur multi-rôles.

## 🚀 Démarrage rapide

### Option 1: Makefile (Recommandé)
```bash
# Voir toutes les commandes disponibles
make help

# Démarrer le système complet
make up

# Démarrer avec capteurs industriels
make up-with-sensors

# Tests du pipeline
make sensor-test
```

### Option 2: Docker Compose direct
```bash
# Système de base
docker-compose up -d

# Avec simulateur de capteurs industriels
docker-compose --profile sensor-sim up -d

# Tests du pipeline capteurs
docker-compose -f docker-compose.sensor-test.yml up --build
```

## 🏗️ Architecture

```
Capteurs Industriels (MQTT)
    ↓
[Agrégateur Pipeline] - Traitement temps réel
    ↓
Backend FastAPI - IA SmartPredictiveEngine
    ↓  
Interfaces Multi-rôles - Dashboards spécialisés
```

## 📊 Services disponibles

| Service | URL | Description |
|---------|-----|-------------|
| **Dashboard Opérateur** | http://localhost:8501 | Interface ultra-simple |
| **Dashboard Team Leader** | http://localhost:8502 | Interface complète | 
| **API Backend** | http://localhost:8000 | API REST + Documentation |
| **MQTT Broker** | localhost:1883 | Messages capteurs |

## 🔧 Composants

### 🎯 **Pipeline Capteurs** (`sensor_pipeline/`)
- **Agrégateur MQTT**: Collecte et synchronise 3 capteurs industriels
- **Simulateur**: Génère données réalistes pour développement  
- **Tests**: Validation automatisée du pipeline

### 🧠 **Intelligence Artificielle** (`backend/`)
- **SmartPredictiveEngine**: Détection anomalies (Isolation Forest)
- **API REST**: Endpoints pour données et prédictions
- **Base de données**: Historique et modèles

### 📊 **Interfaces Utilisateur** (`dashboard/`)
- **Opérateur**: Vue simplifiée état machines
- **Team Leader**: Monitoring complet + analytiques
- **Technicien**: Interface technique détaillée

## 🛠️ Développement

### Prérequis
- Docker & Docker Compose
- Python 3.8+ (pour développement local)
- Make (optionnel, pour commandes simplifiées)

### Structure du projet
```
├── sensor_pipeline/     # Pipeline capteurs industriels
├── backend/            # API et IA
├── dashboard/          # Interfaces utilisateur
├── simulator/          # Simulateur original (UCI dataset)  
├── data/              # Données persistées
└── docker-compose.yml  # Configuration principale
```

## 📈 Capteurs industriels

| Type | Unité | Fréquence | Plage normale |
|------|--------|-----------|---------------|
| Température | °C | 5 minutes | 25-35°C |
| Pression | bar | 5 minutes | 2.5-4.0 bar |
| Vitesse | m/s | 5 minutes | 1.0-2.0 m/s |

## 🔍 Monitoring & Diagnostics

```bash
# État des services
make status

# Logs en temps réel
make logs

# Logs spécifiques capteurs
make logs-sensors

# Diagnostic complet
python sensor_pipeline/diagnostics.py

# Écouter MQTT
make mqtt-listen
```

## 🧪 Tests

```bash
# Tests pipeline capteurs
make sensor-test

# Tests système complet
make test
```

## 📡 Format des données

### Messages MQTT capteurs individuels
```json
{
  "timestamp": "2024-01-15T14:30:00Z",
  "value": 28.5,
  "unit": "°C",
  "machine_id": "MACHINE_01",
  "sensor_type": "temperature"
}
```

### Données agrégées backend
```json
{
  "timestamp": "2024-01-15T14:30:00Z",
  "machine_id": "MACHINE_01", 
  "temperature": 28.5,
  "pressure": 3.2,
  "velocity": 1.8,
  "status": "normal"
}
```

## 🚦 Commandes utiles

```bash
# Redémarrer services
make restart

# Mode développement (rebuild)
make dev

# Nettoyage complet  
make clean

# Sauvegarde données
make backup-data

# Monitoring ressources
make monitor
```

## 🔧 Configuration

Variables d'environnement principales:
- `MQTT_HOST`: Broker MQTT (défaut: mosquitto)
- `AGGREGATION_TOLERANCE`: Tolérance agrégation en secondes (défaut: 1)
- `BACKEND_URL`: URL API backend (défaut: http://backend:8000)

## 🆘 Dépannage

### Problèmes courants

**Services ne démarrent pas**:
```bash
make status
make logs
```

**Problème MQTT**:
```bash
docker-compose restart mosquitto
make mqtt-listen
```

**Pipeline capteurs**:
```bash
python sensor_pipeline/diagnostics.py
```

---

*Développé pour hackathon 2025-2026 - Système IoT industriel avancé*
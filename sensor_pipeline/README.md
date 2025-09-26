# 🏭 Pipeline Capteurs Industriels IoT

Pipeline de traitement en temps réel pour capteurs industriels avec agrégation MQTT et intégration au système IoT de maintenance prédictive.

## 📋 Vue d'ensemble

Ce pipeline récupère les données de capteurs industriels individuels (température, pression, vitesse) via MQTT, les agrège en temps réel et les transmet au backend pour analyse et prédiction d'anomalies.

### Architecture

```
Capteurs Industriels (MQTT)
    ↓
[sensor_aggregator.py] - Agrégation temps réel
    ↓
Backend FastAPI - AI & Stockage
    ↓  
Interfaces Utilisateur - Dashboards
```

## 🔧 Composants

### 1. `sensor_aggregator.py` ⚙️
**Rôle**: Agrégateur principal MQTT
- Écoute les topics `sensors/{machine_id}/{sensor_type}`
- Agrège les données avec tolérance temporelle (1 seconde)
- Publie vers `iot/sensors/{machine_id}` pour le backend

### 2. `real_sensor_simulator.py` 🔧
**Rôle**: Simulateur de capteurs réels
- Simule 3 machines industrielles  
- Envoie données séparées par capteur
- Fréquence: 5 minutes (configurable)

### 3. `test_pipeline.py` 🧪
**Rôle**: Tests et validation
- Monitore les messages MQTT
- Valide l'agrégation
- Statistiques de performance

### 4. `launch_pipeline.py` 🚀
**Rôle**: Orchestrateur principal
- Lance tous les composants
- Monitoring continu
- Gestion des arrêts propres

## 📦 Installation

### Prérequis
- Python 3.8+
- Broker MQTT (mosquitto)
- Backend FastAPI en cours

### Installation automatique
```bash
cd sensor_pipeline
python install_pipeline.py
```

### Installation manuelle
```bash
pip install -r requirements.txt
```

## 🚀 Utilisation

### Lancement complet
```bash
python launch_pipeline.py
```

### Lancement manuel des composants

#### 1. Démarrer l'agrégateur
```bash
python sensor_aggregator.py
```

#### 2. Simuler des capteurs (optionnel)
```bash
python real_sensor_simulator.py
```

#### 3. Tests de validation
```bash
python test_pipeline.py
```

## 📡 Format des données

### Messages capteurs individuels
**Topic**: `sensors/{machine_id}/{sensor_type}`
```json
{
  "timestamp": "2024-01-15T14:30:00Z",
  "value": 28.5,
  "unit": "°C",
  "machine_id": "MACHINE_01", 
  "sensor_type": "temperature"
}
```

### Messages agrégés
**Topic**: `iot/sensors/{machine_id}`
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

## ⚙️ Configuration

### Variables d'environnement
- `MQTT_HOST`: Adresse broker MQTT (défaut: localhost)
- `MQTT_PORT`: Port MQTT (défaut: 1883)
- `AGGREGATION_TOLERANCE`: Tolérance temporelle en secondes (défaut: 1)
- `CLEANUP_INTERVAL`: Intervalle nettoyage buffer en secondes (défaut: 300)

### Capteurs supportés
| Type | Unité | Plage normale | Plage alerte | Plage critique |
|------|--------|---------------|--------------|----------------|
| Température | °C | 25-35 | 35-60 | 60-80 |
| Pression | bar | 2.5-4.0 | 4.0-8.0 | 8.0-12.0 |
| Vitesse | m/s | 1.0-2.0 | 2.0-4.0 | 4.0-6.0 |

## 🐳 Docker

### Dockerfile inclus
```bash
docker build -t sensor-pipeline .
docker run sensor-pipeline
```

### Integration docker-compose
Ajoutez la configuration `docker-compose.pipeline.yml` à votre stack principal.

## 🔍 Monitoring

### Logs
- Niveau INFO: Opérations normales
- Niveau DEBUG: Détails des messages
- Niveau ERROR: Problèmes critiques

### Métriques surveillées
- Messages individuels reçus par type de capteur
- Taux d'agrégation réussi
- Latence de traitement
- Erreurs de connexion MQTT

## 🛠️ Développement

### Structure du projet
```
sensor_pipeline/
├── sensor_aggregator.py      # Agrégateur principal
├── real_sensor_simulator.py  # Simulateur capteurs
├── test_pipeline.py          # Tests validation  
├── launch_pipeline.py        # Orchestrateur
├── install_pipeline.py       # Installation
├── requirements.txt          # Dépendances
├── Dockerfile               # Configuration Docker
└── README.md               # Cette documentation
```

### Tests
```bash
# Test complet du pipeline
python test_pipeline.py

# Test d'un composant spécifique
python -c "from sensor_aggregator import SensorDataAggregator; print('OK')"
```

## 🔧 Dépannage

### Problèmes courants

#### Connexion MQTT échouée
```bash
# Vérifier le broker
telnet localhost 1883

# Redémarrer mosquitto
sudo systemctl restart mosquitto
```

#### Import paho-mqtt échoue
```bash
pip install paho-mqtt==1.6.1
```

#### Données non agrégées
- Vérifier la synchronisation des timestamps
- Ajuster `AGGREGATION_TOLERANCE`
- Examiner les logs d'agrégation

### Logs utiles
```bash
# Voir les messages MQTT
mosquitto_sub -h localhost -t "sensors/+/+"

# Voir les données agrégées  
mosquitto_sub -h localhost -t "iot/sensors/+"
```

## 📊 Performance

### Capacité
- **Machines supportées**: Jusqu'à 100 simultanées
- **Fréquence max**: 1 message/seconde par capteur
- **Latence d'agrégation**: < 2 secondes
- **Mémoire buffer**: Auto-nettoyage toutes les 5 minutes

### Optimisations
- Buffer en mémoire pour performance
- Nettoyage automatique des anciennes données
- Connexions MQTT persistantes
- Logs rotatifs pour l'espace disque

## 🔗 Intégration

### Avec le backend existant
Le pipeline s'intègre seamlessly avec:
- FastAPI backend (port 8000)
- Base de données PostgreSQL
- AI SmartPredictiveEngine 
- Dashboards Streamlit multi-rôles

### Topics MQTT compatibles
- Entrée: `sensors/{machine_id}/{sensor_type}`
- Sortie: `iot/sensors/{machine_id}` (format backend existant)

## 📚 Documentation API

### Classe SensorDataAggregator
```python
class SensorDataAggregator:
    def __init__(self, mqtt_host="localhost", mqtt_port=1883)
    async def start(self)
    def stop(self)
    def get_statistics(self)
```

### Fonctions utilitaires
```python
def validate_sensor_data(payload: dict) -> bool
def format_aggregated_message(machine_id: str, sensors: dict) -> dict
def calculate_machine_status(sensors: dict) -> str
```

## 🆘 Support

Pour signaler un problème ou contribuer:
1. Vérifier les logs de diagnostic
2. Exécuter les tests de validation
3. Consulter la documentation de dépannage
4. Contacter l'équipe de développement

---

*Pipeline développé pour système IoT de maintenance prédictive industrielle*
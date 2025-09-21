# Smart Factory Dashboard

## 🏭 Dashboard IoT Industriel avec IA Prédictive

Interface de visualisation en temps réel pour la surveillance des machines industrielles et la maintenance prédictive.

### ✨ Fonctionnalités

- **📊 Visualisation temps réel** : Graphiques interactifs des capteurs IoT
- **🧠 Prédictions IA** : Intégration avec les modèles ML Isolation Forest
- **🚨 Alertes intelligentes** : Détection automatique des anomalies
- **📈 Historique des données** : Tendances et évolutions
- **🎮 Contrôles de simulation** : Interface pour gérer les tests

### 🚀 Démarrage Rapide

1. **Installer les dépendances** :
   ```bash
   pip install -r requirements.txt
   ```

2. **Démarrer les services** (dans des terminaux séparés) :
   ```bash
   # Backend IA
   python ../backend/main.py
   
   # Simulateur IoT
   python ../simulator/machine_simulator.py
   ```

3. **Lancer le dashboard** :
   ```bash
   python run_dashboard.py
   ```
   
   Ou directement avec Streamlit :
   ```bash
   streamlit run app.py
   ```

4. **Ouvrir le navigateur** : http://localhost:8501

### 📱 Interface

#### 🔧 Panneau de Contrôle
- Statut des services (Backend, MQTT)
- Contrôles de simulation
- Configuration temps réel

#### 📊 Métriques Globales
- Nombre de machines actives
- Risque moyen de panne
- Alertes critiques
- Points de données collectés

#### 🏭 Surveillance par Machine
- Graphiques de capteurs en temps réel
- Jauges de température et pression
- Mécaniques (vitesse, couple, usure)
- Prédictions IA instantanées

#### 🧠 Prédictions IA
- Score d'anomalie en temps réel
- Niveau de risque (low/medium/high)
- Confiance du modèle
- Type de panne prédit

#### 📈 Analyse Historique
- Évolution des capteurs dans le temps
- Tendances de dégradation
- Historique des prédictions

### 🔌 Intégrations

- **Backend FastAPI** : API REST pour prédictions IA
- **MQTT** : Streaming temps réel des données IoT
- **Isolation Forest** : Modèle ML pour détection d'anomalies
- **Plotly** : Graphiques interactifs et jauges
- **WebSockets** : Communication bidirectionnelle

### 🛠️ Technologies

- **Streamlit** : Framework web Python
- **Plotly** : Visualisations interactives
- **Pandas** : Manipulation de données
- **MQTT** : Protocole IoT
- **Requests** : Communication avec le backend

### 📋 Prérequis

- Python 3.8+
- Backend FastAPI démarré
- Simulateur IoT en fonctionnement
- Broker MQTT (intégré au backend)

### 🐛 Debug

Activez le "Mode debug" dans la sidebar pour voir :
- Données MQTT brutes
- Résumé de la flotte
- Tests des prédictions IA

### 🎯 Pour le Hackathon

Ce dashboard démontre :
- **Pipeline IoT complet** : capteurs → streaming → IA → visualisation
- **IA prédictive** : vraie ML avec modèles entraînés
- **Interface professionnelle** : prête pour présentation
- **Données réalistes** : basées sur Open Data industriels
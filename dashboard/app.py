"""
🏭 Dashboard IoT Industriel - Surveillance Prédictive en Temps Réel
Visualisation des données capteurs et prédictions ML pour maintenance prédictive
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import requests
import json
import time
from datetime import datetime, timedelta
import asyncio
import threading
from typing import Dict, List, Optional
import paho.mqtt.client as mqtt

# Configuration globale - Adaptation Docker/Local
import os
if os.path.exists("/app"):
    # En mode Docker - utiliser l'URL externe pour les requêtes client
    BACKEND_URL = "http://localhost:8000"  # URL externe pour le navigateur
    INTERNAL_BACKEND_URL = "http://backend:8000"  # URL interne pour requests serveur
else:
    # En mode développement local
    BACKEND_URL = "http://localhost:8000"
    INTERNAL_BACKEND_URL = "http://localhost:8000"

MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# Classe pour gérer les données du dashboard
class DashboardData:
    def __init__(self):
        self.connected = False
        self.machines_data = {}
        self.fleet_summary = {}
        self.historical_data = []
        
    def update_from_api(self):
        """Met à jour les données depuis l'API"""
        try:
            response = requests.get(f"{INTERNAL_BACKEND_URL}/api/status", timeout=5)
            if response.status_code == 200:
                self.connected = True
                # Charger les données machines
                machines_response = requests.get(f"{INTERNAL_BACKEND_URL}/api/machines", timeout=5)
                if machines_response.status_code == 200:
                    self.machines_data = machines_response.json()
                
                # Charger le résumé de la flotte
                fleet_response = requests.get(f"{INTERNAL_BACKEND_URL}/api/fleet/summary", timeout=5)
                if fleet_response.status_code == 200:
                    self.fleet_summary = fleet_response.json()
                    
                return True
        except:
            self.connected = False
            return False
        return False

# Initialiser les données du dashboard
if 'dashboard_data' not in st.session_state:
    st.session_state.dashboard_data = DashboardData()

# Configuration de la page
st.set_page_config(
    page_title="🏭 Smart Factory Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar avec navigation
with st.sidebar:
    st.title("Navigation")
    st.markdown("---")
    
    st.subheader("Tableaux de Bord")
    st.page_link("app.py", label="Accueil", icon="🏠")
    st.page_link("pages/historique.py", label="Historique", icon="📈")
    st.page_link("pages/configuration.py", label="Configuration", icon="⚙️")
    st.page_link("pages/alertes.py", label="Alertes", icon="🚨")
    st.page_link("pages/services.py", label="Services", icon="🔍")
    
    st.markdown("---")
    st.subheader("Mode Spécialisé")
    st.page_link("pages/mode_usine.py", label="Mode Usine", icon="🏭")
    
    st.markdown("---")
    
    # Statut Backend
    try:
        response = requests.get(f"{INTERNAL_BACKEND_URL}/health", timeout=1)
        if response.status_code == 200:
            st.success("✅ Backend connecté")
        else:
            st.error("❌ Backend déconnecté")
    except:
        st.error("❌ Backend déconnecté")
        st.info("💡 Mode Docker: backend:8000")

# Initialiser le state pour les données temps réel
if 'live_data' not in st.session_state:
    st.session_state.live_data = {}
if 'update_counter' not in st.session_state:
    st.session_state.update_counter = 0
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

def get_backend_status():
    """Vérifie le statut du backend"""
    try:
        response = requests.get(f"{INTERNAL_BACKEND_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def fetch_live_data():
    """Récupère les données temps réel du backend"""
    try:
        response = requests.get(f"{INTERNAL_BACKEND_URL}/api/machines/live", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('machines', {})
    except Exception as e:
        st.error(f"❌ Erreur récupération données: {e}")
    return None

def get_ai_models_status():
    """Récupère le statut des modèles IA"""
    try:
        response = requests.get(f"{INTERNAL_BACKEND_URL}/ai/models/status", timeout=5)
        return response.json()
    except:
        return {"status": "error", "message": "Backend indisponible"}

def test_ai_prediction(data):
    """Test une prédiction IA"""
    try:
        response = requests.post(f"{INTERNAL_BACKEND_URL}/ai/predict", json=data, timeout=5)
        return response.json()
    except:
        return {"error": "Backend indisponible"}

def check_and_create_alerts(machine_id, machine_data):
    """Vérifie les seuils et crée des alertes si nécessaire"""
    alerts_created = []
    
    # Seuils réalistes pour équipements industriels 
    thresholds = {
        'process_temperature': {'warning': 65, 'critical': 85},  # Température process
        'air_temperature': {'warning': 30, 'critical': 35},     # Température ambiante
        'pressure': {'warning': 3.5, 'critical': 2.5},         # Pression hydraulique (bar)
        'vibration': {'warning': 1.0, 'critical': 1.8},        # Vibrations (mm/s)
        'failure_probability': {'warning': 0.4, 'critical': 0.7}, # Probabilité panne
        'tool_wear': {'warning': 250, 'critical': 320}         # Usure outil
    }
    
    # Vérifier la température process (critique pour usinage)
    process_temp = machine_data.get('process_temperature', 0)
    if process_temp >= thresholds['process_temperature']['critical']:
        alert_data = {
            "machine_id": machine_id,
            "severity": "critical",
            "message": f"🌡️ Surchauffe process: {process_temp}°C (>85°C)",
            "failure_type": "thermal_overload",
            "probability": 0.85
        }
        alerts_created.append(create_alert(alert_data))
    elif process_temp >= thresholds['process_temperature']['warning']:
        alert_data = {
            "machine_id": machine_id,
            "severity": "warning", 
            "message": f"🌡️ Température process élevée: {process_temp}°C",
            "failure_type": "thermal_stress",
            "probability": 0.45
        }
        alerts_created.append(create_alert(alert_data))
    
    # Vérifier les vibrations (indicateur usure/désalignement)
    vibration = machine_data.get('vibration', 0)
    if vibration >= thresholds['vibration']['critical']:
        alert_data = {
            "machine_id": machine_id,
            "severity": "critical",
            "message": f"📳 Vibrations excessives: {vibration} mm/s",
            "failure_type": "mechanical_wear",
            "probability": 0.75
        }
        alerts_created.append(create_alert(alert_data))
    elif vibration >= thresholds['vibration']['warning']:
        alert_data = {
            "machine_id": machine_id,
            "severity": "warning",
            "message": f"📳 Vibrations élevées: {vibration} mm/s",
            "failure_type": "alignment_issue", 
            "probability": 0.35
        }
        alerts_created.append(create_alert(alert_data))
    
    # Vérifier l'usure outil
    tool_wear = machine_data.get('tool_wear', 0)
    if tool_wear >= thresholds['tool_wear']['critical']:
        alert_data = {
            "machine_id": machine_id,
            "severity": "critical",
            "message": f"🔧 Outil critique: {tool_wear} cycles",
            "failure_type": "tool_failure",
            "probability": 0.9
        }
        alerts_created.append(create_alert(alert_data))
    elif tool_wear >= thresholds['tool_wear']['warning']:
        alert_data = {
            "machine_id": machine_id,
            "severity": "warning",
            "message": f"🔧 Outil à remplacer bientôt: {tool_wear} cycles",
            "failure_type": "tool_wear",
            "probability": 0.3
        }
        alerts_created.append(create_alert(alert_data))
    
    # Vérifier la probabilité de panne IA
    failure_prob = machine_data.get('failure_probability', 0)
    if failure_prob >= thresholds['failure_probability']['critical']:
        alert_data = {
            "machine_id": machine_id,
            "severity": "critical",
            "message": f"🤖 IA: Panne imminente {failure_prob:.0%}",
            "failure_type": "ai_prediction",
            "probability": failure_prob
        }
        alerts_created.append(create_alert(alert_data))
    elif failure_prob >= thresholds['failure_probability']['warning']:
        alert_data = {
            "machine_id": machine_id,
            "severity": "warning",
            "message": f"🤖 IA: Surveillance renforcée {failure_prob:.0%}",
            "failure_type": "predictive_maintenance", 
            "probability": failure_prob
        }
        alerts_created.append(create_alert(alert_data))
    
    return alerts_created

def create_alert(alert_data):
    """Crée une alerte via l'API backend"""
    try:
        # Ajouter timestamp et ID
        alert_data["timestamp"] = datetime.now().isoformat()
        alert_data["id"] = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{alert_data['machine_id']}"
        alert_data["acknowledged"] = False
        
        response = requests.post(f"{INTERNAL_BACKEND_URL}/alerts", json=alert_data, timeout=5)
        if response.status_code == 200:
            return alert_data
    except:
        pass
    return None

def get_simulated_data():
    """Génère des données réalistes basées sur équipements industriels réels"""
    import random
    
    # Données basées sur équipements industriels réels
    return {
        "CNC_HAAS_VF2": {
            "id": "CNC_HAAS_VF2", 
            "name": "Centre d'usinage HAAS VF-2",
            "status": "operational",
            "air_temperature": round(22 + random.uniform(-2, 5), 1),  # Temp ambiante atelier
            "process_temperature": round(45 + random.uniform(-5, 15), 1),  # Broche/liquide de coupe
            "rotational_speed": round(8000 + random.uniform(-500, 2000), 0),  # RPM broche
            "torque": round(85 + random.uniform(-15, 25), 1),  # Couple broche (Nm)
            "tool_wear": round(random.uniform(50, 200), 0),  # Usure outil (passes)
            "pressure": round(6 + random.uniform(-1, 2), 1),  # Pression hydraulique (bar) 
            "vibration": round(random.uniform(0.1, 0.8), 2),  # Vibrations (mm/s)
            "failure_probability": round(random.uniform(0.05, 0.25), 2),
            "last_maintenance": "2024-12-01",
            "next_maintenance": "2025-03-01",
            "product_type": "H"  # High precision
        },
        "MAKINO_A51NX": {
            "id": "MAKINO_A51NX",
            "name": "Centre horizontal MAKINO a51nx", 
            "status": "warning",
            "air_temperature": round(24 + random.uniform(-1, 4), 1),
            "process_temperature": round(38 + random.uniform(-3, 18), 1),  # Plus chaude car pb
            "rotational_speed": round(12000 + random.uniform(-1000, 1500), 0),
            "torque": round(65 + random.uniform(-10, 35), 1), 
            "tool_wear": round(random.uniform(150, 280), 0),  # Usure plus élevée
            "pressure": round(5.2 + random.uniform(-0.8, 1.5), 1),
            "vibration": round(random.uniform(0.5, 1.4), 2),  # Vibrations plus élevées
            "failure_probability": round(random.uniform(0.35, 0.65), 2),  # Risque élevé
            "last_maintenance": "2024-10-15", 
            "next_maintenance": "2025-01-15",
            "product_type": "M"  # Medium precision
        },
        "TRUMPF_3030": {
            "id": "TRUMPF_3030",
            "name": "Découpe laser TRUMPF TruLaser 3030",
            "status": "operational", 
            "air_temperature": round(25 + random.uniform(-2, 3), 1),
            "process_temperature": round(180 + random.uniform(-20, 40), 1),  # Laser très chaud
            "rotational_speed": round(0, 0),  # Pas de rotation pour laser
            "torque": round(0, 1),  # Pas de couple pour laser
            "tool_wear": round(random.uniform(800, 1200), 0),  # Durée laser (heures)
            "pressure": round(12 + random.uniform(-2, 3), 1),  # Pression gaz assist
            "vibration": round(random.uniform(0.05, 0.3), 2),  # Très peu de vibrations
            "failure_probability": round(random.uniform(0.08, 0.20), 2),
            "last_maintenance": "2024-11-20",
            "next_maintenance": "2025-02-20", 
            "product_type": "L"  # Low tolerance
        },
        "KUKA_KR180": {
            "id": "KUKA_KR180",
            "name": "Robot KUKA KR 180 R2500",
            "status": "operational",
            "air_temperature": round(23 + random.uniform(-1, 4), 1),
            "process_temperature": round(55 + random.uniform(-10, 20), 1),  # Moteurs servos
            "rotational_speed": round(180 + random.uniform(-30, 50), 0),  # Vitesse rotation joints
            "torque": round(1200 + random.uniform(-200, 400), 1),  # Couple max robot
            "tool_wear": round(random.uniform(5000, 8000), 0),  # Cycles robot
            "pressure": round(5.5 + random.uniform(-0.5, 1), 1),  # Pression pneumatique
            "vibration": round(random.uniform(0.2, 0.9), 2),
            "failure_probability": round(random.uniform(0.10, 0.30), 2),
            "last_maintenance": "2024-12-10",
            "next_maintenance": "2025-03-10",
            "product_type": "H"
        },
        "MAZAK_INTEGREX": {
            "id": "MAZAK_INTEGREX", 
            "name": "Tour-fraiseuse MAZAK Integrex i-200",
            "status": "critical",
            "air_temperature": round(26 + random.uniform(-1, 6), 1),  # Plus chaud = problème
            "process_temperature": round(75 + random.uniform(-5, 25), 1),  # Surchauffe
            "rotational_speed": round(4500 + random.uniform(-500, 1000), 0),
            "torque": round(320 + random.uniform(-50, 80), 1),
            "tool_wear": round(random.uniform(280, 350), 0),  # Usure critique
            "pressure": round(4.2 + random.uniform(-1, 0.5), 1),  # Pression faible
            "vibration": round(random.uniform(1.2, 2.1), 2),  # Vibrations élevées
            "failure_probability": round(random.uniform(0.70, 0.90), 2),  # Très critique
            "last_maintenance": "2024-09-30",
            "next_maintenance": "2024-12-30",  # Maintenance en retard!
            "product_type": "M"
        }
    }

def main():
    """Interface principale du dashboard"""
    
    # Récupérer les données du dashboard
    dashboard_data = st.session_state.dashboard_data
    
    # Mettre à jour les données depuis l'API
    dashboard_data.update_from_api()
    
    # En-tête principal
    st.markdown("""
    <div style='text-align: center; padding: 1rem; background: linear-gradient(90deg, #1f4e79, #2980b9); color: white; border-radius: 10px; margin-bottom: 2rem;'>
        <h1>🏭 Smart Factory Dashboard</h1>
        <p>Surveillance Prédictive IoT + Intelligence Artificielle</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar - Contrôles
    with st.sidebar:
        st.header("🔧 Contrôles")
        
        # Statut des services
        st.subheader("📊 Statut Services")
        
        backend_status = get_backend_status()
        mqtt_status = dashboard_data.connected
        
        col1, col2 = st.columns(2)
        with col1:
            if backend_status:
                st.success("✅ Backend")
            else:
                st.error("❌ Backend")
        
        with col2:
            if mqtt_status:
                st.success("✅ MQTT")
            else:
                st.error("❌ MQTT")
        
        # Contrôles de simulation
        st.subheader("🎮 Simulation")
        
        if st.button("🚀 Démarrer Simulateur"):
            st.info("Démarrez le simulateur avec: `python simulator/machine_simulator.py`")
        
        if st.button("🔄 Actualiser Données"):
            st.rerun()
        
        # Configuration
        st.subheader("⚙️ Configuration")
        auto_refresh = st.checkbox("🔄 Actualisation auto (5s)", value=True)
        show_debug = st.checkbox("🐛 Mode debug", value=False)
        
        if auto_refresh:
            time.sleep(5)
            st.rerun()
    
    # Vérifier les modèles IA
    ai_status = get_ai_models_status()
    
    if ai_status.get("status") == "ready":
        st.success(f"🧠 **IA Active**: {ai_status.get('models_loaded', 0)} modèles chargés")
    else:
        st.warning(f"⚠️ **IA**: {ai_status.get('message', 'Statut inconnu')}")
    
    # Métriques globales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_machines = len(dashboard_data.machines_data)
        st.metric("🏭 Machines", total_machines)
    
    with col2:
        if dashboard_data.fleet_summary:
            avg_prob = dashboard_data.fleet_summary.get('avg_failure_probability', 0)
            st.metric("⚠️ Risque Moyen", f"{avg_prob:.1%}")
        else:
            st.metric("⚠️ Risque Moyen", "N/A")
    
    with col3:
        if dashboard_data.fleet_summary:
            alerts = len(dashboard_data.fleet_summary.get('active_alerts', []))
            st.metric("🚨 Alertes Actives", alerts)
        else:
            st.metric("🚨 Alertes Actives", "0")
    
    with col4:
        data_points = len(dashboard_data.historical_data)
        st.metric("📊 Points de Données", data_points)
    
    # Alertes critiques
    if dashboard_data.fleet_summary.get('active_alerts'):
        st.error("🚨 **ALERTES CRITIQUES DÉTECTÉES**")
        
        alerts_df = pd.DataFrame(dashboard_data.fleet_summary['active_alerts'])
        st.dataframe(alerts_df, use_container_width=True)
    
    # Graphiques en temps réel
    # Si MQTT ne fonctionne pas, utiliser les données simulées
    if not dashboard_data.connected and not dashboard_data.machines_data:
        st.info("🔄 **Mode démo** : Récupération des données via l'API backend")
        dashboard_data.machines_data = get_simulated_data()
    
    if dashboard_data.machines_data:
        
        # Sélecteur de machine
        machine_ids = list(dashboard_data.machines_data.keys())
        selected_machine = st.selectbox("🏭 Sélectionner une machine", machine_ids)
        
        if selected_machine:
            machine_data = dashboard_data.machines_data[selected_machine]
            
            # Vérifier et créer des alertes automatiquement
            check_and_create_alerts(selected_machine, machine_data)
            
            # Graphiques pour la machine sélectionnée
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"🌡️ Capteurs - {selected_machine}")
                
                # Graphique des températures
                fig_temp = go.Figure()
                fig_temp.add_trace(go.Indicator(
                    mode="gauge+number+delta",
                    value=machine_data.get('air_temperature', 0),
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Température Air (K)"},
                    gauge={
                        'axis': {'range': [290, 320]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [290, 305], 'color': "lightgray"},
                            {'range': [305, 315], 'color': "yellow"},
                            {'range': [315, 320], 'color': "red"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 305
                        }
                    }
                ))
                
                st.plotly_chart(fig_temp, use_container_width=True)
            
            with col2:
                st.subheader(f"🔧 État Mécanique - {selected_machine}")
                
                # Graphique vitesse/couple
                fig_mech = make_subplots(
                    rows=2, cols=1,
                    subplot_titles=('Vitesse Rotation (rpm)', 'Couple (Nm)'),
                    vertical_spacing=0.1
                )
                
                fig_mech.add_trace(
                    go.Scatter(
                        x=[datetime.now()],
                        y=[machine_data.get('rotational_speed', 0)],
                        mode='markers+lines',
                        name='Vitesse',
                        marker=dict(size=10, color='blue')
                    ),
                    row=1, col=1
                )
                
                fig_mech.add_trace(
                    go.Scatter(
                        x=[datetime.now()],
                        y=[machine_data.get('torque', 0)],
                        mode='markers+lines',
                        name='Couple',
                        marker=dict(size=10, color='red')
                    ),
                    row=2, col=1
                )
                
                fig_mech.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig_mech, use_container_width=True)
            
            # Prédiction IA en temps réel
            st.subheader(f"🧠 Prédiction IA - {selected_machine}")
            
            # Préparer les données pour l'IA avec tous les champs requis
            ai_data = {
                "machine_id": selected_machine,
                "timestamp": datetime.now().isoformat(),
                "air_temperature": machine_data.get('air_temperature', 300),
                "process_temperature": machine_data.get('process_temperature', 310),
                "rotational_speed": machine_data.get('rotational_speed', 1500),
                "torque": machine_data.get('torque', 40),
                "tool_wear": machine_data.get('tool_wear', 100),
                "product_type": "H",  # Type de produit par défaut
                "status": machine_data.get('status', 'normal')
            }
            
            # Tester la prédiction
            prediction = test_ai_prediction(ai_data)
            
            if "error" not in prediction:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    risk_level = prediction.get('risk_level', 'unknown')
                    if risk_level == 'low':
                        st.success(f"✅ **Risque**: {risk_level.upper()}")
                    elif risk_level == 'medium':
                        st.warning(f"⚠️ **Risque**: {risk_level.upper()}")
                    else:
                        st.error(f"🚨 **Risque**: {risk_level.upper()}")
                
                with col2:
                    anomaly_score = prediction.get('anomaly_score', 0)
                    st.metric("🎯 Score Anomalie", f"{anomaly_score:.3f}")
                
                with col3:
                    confidence = prediction.get('confidence', 0)
                    st.metric("🎯 Confiance", f"{confidence:.1%}")
                
                # Graphique de prédiction
                if prediction.get('prediction'):
                    st.info(f"🔮 **Prédiction**: {prediction['prediction']}")
                
            else:
                st.error("❌ Impossible d'obtenir une prédiction IA")
    
    else:
        st.info("""
        🔄 **En attente de données...**
        
        Pour voir les données en temps réel:
        1. Démarrez le backend: `python backend/main.py`
        2. Démarrez le simulateur: `python simulator/machine_simulator.py`
        3. Les données apparaîtront automatiquement ici
        """)
    
    # Historique des données
    if dashboard_data.historical_data:
        st.subheader("📈 Historique des Données")
        
        # Convertir en DataFrame
        df_history = pd.DataFrame(dashboard_data.historical_data)
        df_history['timestamp'] = pd.to_datetime(df_history['timestamp'])
        
        # Graphique historique
        fig_history = px.line(
            df_history.tail(100),  # 100 derniers points
            x='timestamp',
            y=['air_temperature', 'process_temperature'],
            title="Évolution des Températures"
        )
        
        st.plotly_chart(fig_history, use_container_width=True)
    
    # Section Debug
    if show_debug:
        st.subheader("🐛 Informations Debug")
        
        with st.expander("Données MQTT"):
            st.json(dashboard_data.machines_data)
        
        with st.expander("Résumé Flotte"):
            st.json(dashboard_data.fleet_summary)
        
        with st.expander("Test IA"):
            test_data = {
                "machine_id": "test_machine_001",
                "timestamp": datetime.now().isoformat(),
                "air_temperature": 305.0,
                "process_temperature": 318.0,
                "rotational_speed": 1420.0,
                "torque": 55.0,
                "tool_wear": 180.0,
                "product_type": "H",
                "status": "normal"
            }
            
            if st.button("🧪 Tester Prédiction"):
                result = test_ai_prediction(test_data)
                st.json(result)

if __name__ == "__main__":
    main()
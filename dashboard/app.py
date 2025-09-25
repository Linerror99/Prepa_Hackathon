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

# Configuration de la page
st.set_page_config(
    page_title="🏭 Smart Factory Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration globale
BACKEND_URL = "http://localhost:8000"
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

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
        response = requests.get(f"{BACKEND_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def fetch_live_data():
    """Récupère les données temps réel du backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/machines/live", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('machines', {})
    except Exception as e:
        st.error(f"❌ Erreur récupération données: {e}")
    return None

def get_ai_models_status():
    """Récupère le statut des modèles IA"""
    try:
        response = requests.get(f"{BACKEND_URL}/ai/models/status", timeout=5)
        return response.json()
    except:
        return {"status": "error", "message": "Backend indisponible"}

def test_ai_prediction(data):
    """Test une prédiction IA"""
    try:
        response = requests.post(f"{BACKEND_URL}/ai/predict", json=data, timeout=5)
        return response.json()
    except:
        return {"error": "Backend indisponible"}

def main():
    """Interface principale du dashboard"""
    
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
            
            # Graphiques pour la machine sélectionnée
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"🌡️ Capteurs - {selected_machine}")
                
                # Graphique de température industrielle
                fig_temp = go.Figure()
                fig_temp.add_trace(go.Indicator(
                    mode="gauge+number+delta",
                    value=machine_data.get('temperature', 0),
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Température (°C)"},
                    gauge={
                        'axis': {'range': [15, 80]},
                        'bar': {'color': "darkred"},
                        'steps': [
                            {'range': [15, 40], 'color': "lightgreen"},
                            {'range': [40, 60], 'color': "yellow"},
                            {'range': [60, 80], 'color': "red"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 50
                        }
                    }
                ))
                
                st.plotly_chart(fig_temp, use_container_width=True, key=f"temp_gauge_{selected_machine}")
            
            with col2:
                st.subheader(f"⚙️ Système Hydraulique - {selected_machine}")
                
                # Graphique pression/vitesse
                fig_mech = make_subplots(
                    rows=2, cols=1,
                    subplot_titles=('Pression Système (bar)', 'Vitesse Composants (m/s)'),
                    vertical_spacing=0.1
                )
                
                fig_mech.add_trace(
                    go.Scatter(
                        x=[datetime.now()],
                        y=[machine_data.get('pressure', 0)],
                        mode='markers+lines',
                        name='Pression',
                        marker=dict(size=10, color='blue')
                    ),
                    row=1, col=1
                )
                
                fig_mech.add_trace(
                    go.Scatter(
                        x=[datetime.now()],
                        y=[machine_data.get('velocity', 0)],
                        mode='markers+lines',
                        name='Vitesse',
                        marker=dict(size=10, color='green')
                    ),
                    row=2, col=1
                )
                
                fig_mech.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig_mech, use_container_width=True, key=f"mech_chart_{selected_machine}")
            
            # Prédiction IA en temps réel
            st.subheader(f"🧠 Prédiction IA - {selected_machine}")
            
            # Préparer les données industrielles pour l'IA
            ai_data = {
                "temperature": machine_data.get('temperature', 30.0),
                "pressure": machine_data.get('pressure', 3.0),
                "velocity": machine_data.get('velocity', 1.5)
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
            y=['temperature', 'pressure', 'velocity'],
            title="Évolution des Capteurs Industriels"
        )
        
        st.plotly_chart(fig_history, use_container_width=True, key="history_chart")
    
    # Section Debug
    if show_debug:
        st.subheader("🐛 Informations Debug")
        
        with st.expander("Données MQTT"):
            st.json(dashboard_data.machines_data)
        
        with st.expander("Résumé Flotte"):
            st.json(dashboard_data.fleet_summary)
        
        with st.expander("Test IA Industriel"):
            test_data = {
                "temperature": 65.0,
                "pressure": 1.2,
                "velocity": 0.3
            }
            
            if st.button("🧪 Tester Prédiction"):
                result = test_ai_prediction(test_data)
                st.json(result)

if __name__ == "__main__":
    main()
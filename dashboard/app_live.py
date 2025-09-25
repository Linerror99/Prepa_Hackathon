"""
🏭 Dashboard IoT Industriel TEMPS RÉEL
Surveillance Prédictive en Direct avec Auto-Refresh
"""

import os
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
import random

# Configuration de la page
st.set_page_config(
    page_title="🏭 Smart Factory Live Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration pour éviter les déconnexions
st.markdown("""
<script>
window.parent.addEventListener('beforeunload', function(e) {
    // Empêcher les déconnexions accidentelles
});
</script>
""", unsafe_allow_html=True)

# Configuration globale
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# CSS pour améliorer l'apparence
st.markdown("""
<style>
    .metric-container {
        background: linear-gradient(90deg, #1f4e79, #2980b9);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .status-good { color: #28a745; }
    .status-warning { color: #ffc107; }
    .status-critical { color: #dc3545; }
    .live-indicator {
        animation: blink 1s infinite;
        color: #ff4444;
        font-weight: bold;
    }
    @keyframes blink {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

def check_backend_status():
    """Vérifie le statut du backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=3)
        return response.status_code == 200
    except:
        return False

def fetch_live_machines_data():
    """Récupère les données temps réel des machines"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/machines/live", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return {"error": str(e)}

def get_ai_prediction(machine_data):
    """Obtient une prédiction IA pour une machine - utilise les données déjà calculées"""
    try:
        # Utiliser les prédictions déjà calculées dans les données de la machine
        ai_prediction = machine_data.get("ai_prediction")
        if ai_prediction and "prediction" in ai_prediction:
            prediction_data = ai_prediction["prediction"]
            
            # Convertir le format pour l'affichage
            risk_level = "unknown"
            failure_prob = prediction_data.get("failure_probability", 0)
            
            if failure_prob < 0.3:
                risk_level = "low"
            elif failure_prob < 0.7:
                risk_level = "medium"  
            else:
                risk_level = "high"
            
            return {
                "prediction": {
                    "risk_level": risk_level,
                    "confidence": prediction_data.get("confidence", 0.9),
                    "anomaly_score": prediction_data.get("failure_probability", 0),
                    "predicted_status": prediction_data.get("predicted_status", "normal"),
                    "model_info": prediction_data.get("model_info", {}),
                    "recommendation": f"Probabilité de panne: {failure_prob:.1%}"
                }
            }
        
        return None
    except Exception as e:
        st.error(f"Erreur prédiction IA: {e}")
        return None

def main():
    """Interface principale du dashboard"""
    
    # En-tête avec indicateur temps réel
    st.markdown("""
    <div class='metric-container'>
        <h1>🏭 Smart Factory Live Dashboard</h1>
        <p><span class='live-indicator'>●</span> SURVEILLANCE TEMPS RÉEL <span class='live-indicator'>●</span></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-refresh toutes les 3 secondes
    placeholder_main = st.empty()
    
    with placeholder_main.container():
        # Sidebar contrôles
        with st.sidebar:
            st.header("🔧 Contrôles Temps Réel")
            
            # Bouton de refresh manuel
            if st.button("🔄 Actualiser Maintenant"):
                st.rerun()
            
            # Configuration auto-refresh
            auto_refresh = st.checkbox("🔄 Auto-Refresh (3s)", value=True)
            show_ai = st.checkbox("🧠 Prédictions IA", value=True)
            show_debug = st.checkbox("🐛 Mode Debug", value=False)
            
            st.markdown("---")
            
            # Statut des services
            st.subheader("📊 État Services")
            backend_status = check_backend_status()
            
            if backend_status:
                st.success("✅ Backend Connecté")
            else:
                st.error("❌ Backend Déconnecté")
                st.stop()
        
        # Récupérer les données temps réel
        st.subheader("📡 Données Temps Réel")
        
        with st.spinner("Récupération des données en cours..."):
            live_data = fetch_live_machines_data()
        
        if live_data and "machines" in live_data:
            machines = live_data["machines"]
            
            # Métriques globales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🏭 Machines Actives", len(machines))
            
            with col2:
                if machines:
                    avg_temp = np.mean([m.get("temperature", 0) for m in machines.values()])
                    st.metric("🌡️ Temp. Moyenne", f"{avg_temp:.1f}°C")
                else:
                    st.metric("🌡️ Temp. Moyenne", "N/A")
            
            with col3:
                if machines:
                    critical_count = len([m for m in machines.values() 
                                        if m.get("status") == "critical"])
                    st.metric("🚨 Alertes", critical_count)
                else:
                    st.metric("🚨 Alertes", "0")
            
            with col4:
                st.metric("⏰ Dernière MAJ", datetime.now().strftime("%H:%M:%S"))
            
            # Données par machine
            if machines:
                for machine_id, machine_data in machines.items():
                    
                    # Conteneur pour chaque machine
                    st.markdown(f"### 🏭 {machine_id}")
                    
                    # Colonnes pour les graphiques
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # Gauge température industrielle
                        temp = machine_data.get("temperature", 30)
                        fig_temp = go.Figure(go.Indicator(
                            mode = "gauge+number+delta",
                            value = temp,
                            domain = {'x': [0, 1], 'y': [0, 1]},
                            title = {'text': "🌡️ Température (°C)"},
                            gauge = {
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
                        fig_temp.update_layout(height=250)
                        st.plotly_chart(fig_temp, use_container_width=True, key=f"temp_gauge_{machine_id}")
                    
                    with col2:
                        # Gauge pression
                        pressure = machine_data.get("pressure", 5.0)
                        fig_pressure = go.Figure(go.Indicator(
                            mode = "gauge+number",
                            value = pressure,
                            domain = {'x': [0, 1], 'y': [0, 1]},
                            title = {'text': "📊 Pression (bar)"},
                            gauge = {
                                'axis': {'range': [0, 12]},
                                'bar': {'color': "blue"},
                                'steps': [
                                    {'range': [0, 4], 'color': "lightgray"},
                                    {'range': [4, 8], 'color': "yellow"},
                                    {'range': [8, 12], 'color': "red"}
                                ]
                            }
                        ))
                        fig_pressure.update_layout(height=250)
                        st.plotly_chart(fig_pressure, use_container_width=True, key=f"pressure_gauge_{machine_id}")
                    
                    with col3:
                        # Métriques machine
                        st.markdown("**📊 Métriques:**")
                        
                        status = machine_data.get("status", "unknown")
                        if status == "normal":
                            st.success(f"✅ État: {status.upper()}")
                        elif status == "warning":
                            st.warning(f"⚠️ État: {status.upper()}")
                        else:
                            st.error(f"🚨 État: {status.upper()}")
                        
                        st.metric("🌡️ Température", f"{machine_data.get('temperature', 0):.1f} °C")
                        st.metric("� Pression", f"{machine_data.get('pressure', 0):.1f} bar")
                        st.metric("🏃 Vitesse", f"{machine_data.get('velocity', 0):.1f} m/s")
                        
                        # Timestamp
                        timestamp = machine_data.get('timestamp', '')
                        if timestamp:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            st.caption(f"⏰ {dt.strftime('%H:%M:%S')}")
                    
                    # Prédiction IA si activée
                    if show_ai:
                        with st.expander(f"🧠 Prédiction IA - {machine_id}", expanded=False):
                            with st.spinner("Analyse IA en cours..."):
                                prediction = get_ai_prediction(machine_data)
                            
                            if prediction and "prediction" in prediction:
                                pred_data = prediction["prediction"]
                                
                                col_ai1, col_ai2, col_ai3 = st.columns(3)
                                
                                with col_ai1:
                                    risk = pred_data.get("risk_level", "unknown")
                                    if risk == "low":
                                        st.success(f"✅ Risque: {risk.upper()}")
                                    elif risk == "medium":
                                        st.warning(f"⚠️ Risque: {risk.upper()}")
                                    else:
                                        st.error(f"🚨 Risque: {risk.upper()}")
                                
                                with col_ai2:
                                    confidence = pred_data.get("confidence", 0)
                                    st.metric("🎯 Confiance", f"{confidence:.1%}")
                                
                                with col_ai3:
                                    anomaly = pred_data.get("anomaly_score", 0)
                                    st.metric("📊 Score Anomalie", f"{anomaly:.3f}")
                                
                                if pred_data.get("recommendation"):
                                    st.info(f"💡 Recommandation: {pred_data['recommendation']}")
                            else:
                                st.error("❌ Impossible d'obtenir une prédiction IA")
                    
                    st.markdown("---")
            
            else:
                st.warning("Aucune machine détectée")
                
        elif live_data and "error" in live_data:
            st.error(f"❌ Erreur de récupération: {live_data['error']}")
            
        else:
            st.error("❌ Impossible de récupérer les données du backend")
            st.info("""
            **Vérifications:**
            1. Backend démarré: `python backend/main.py`
            2. Simulateur actif: `python simulator/machine_simulator.py`
            3. URL Backend: http://localhost:8000
            """)
        
        # Section debug
        if show_debug and live_data:
            st.subheader("🐛 Données Brutes (Debug)")
            st.json(live_data)
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(3)
        st.rerun()

if __name__ == "__main__":
    main()
"""
Page Mode Usine - Interface simplifiée pour environnement industriel
"""

import streamlit as st
import requests
import time
from datetime import datetime

# Configuration de la page - Mode Usine
st.set_page_config(
    page_title="Mode Usine",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="collapsed"  # Cacher la sidebar en mode usine
)

# URL de l'API Backend - Adaptation Docker/Local
import os
if os.path.exists("/app"):
    BACKEND_URL = "http://backend:8000"
else:
    BACKEND_URL = "http://localhost:8000"

# CSS pour le mode usine - Gros boutons, contraste élevé
st.markdown("""
<style>
    .big-button {
        font-size: 24px !important;
        padding: 20px !important;
        margin: 10px !important;
        border-radius: 10px !important;
        width: 100% !important;
        height: 100px !important;
        border: 3px solid #333 !important;
    }
    
    .status-card {
        padding: 20px;
        margin: 15px 0;
        border-radius: 15px;
        border: 3px solid;
        font-size: 18px;
        text-align: center;
        font-weight: bold;
    }
    
    .status-normal {
        background-color: #28a745;
        border-color: #1e7e34;
        color: white;
    }
    
    .status-warning {
        background-color: #ffc107;
        border-color: #d39e00;
        color: black;
    }
    
    .status-critical {
        background-color: #dc3545;
        border-color: #bd2130;
        color: white;
        animation: blink 1s infinite;
    }
    
    @keyframes blink {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .machine-card {
        border: 4px solid #333;
        border-radius: 20px;
        padding: 25px;
        margin: 15px;
        background-color: #f8f9fa;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .big-metric {
        font-size: 36px !important;
        font-weight: bold !important;
        text-align: center !important;
    }
    
    .alert-banner {
        font-size: 24px;
        padding: 20px;
        margin: 10px 0;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        border: 3px solid;
    }
</style>
""", unsafe_allow_html=True)

def get_machines_data():
    """Récupère les données des machines"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/machines/live")
        if response.status_code == 200:
            return response.json()["machines"]
        return {}
    except:
        return {}

def get_active_alerts():
    """Récupère les alertes actives"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/alerts/active")
        if response.status_code == 200:
            return response.json()["alerts"]
        return []
    except:
        return []

# Header en mode usine
st.markdown("""
<div style="background-color: #2c3e50; color: white; padding: 30px; margin: -1rem -1rem 2rem -1rem; text-align: center;">
    <h1 style="font-size: 48px; margin: 0;">🏭 MODE USINE</h1>
    <h2 style="font-size: 24px; margin: 10px 0;">Surveillance Temps Réel des Machines</h2>
</div>
""", unsafe_allow_html=True)

# Auto-actualisation forcée en mode usine
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()

# Récupération des données
machines_data = get_machines_data()
alerts = get_active_alerts()

# Bannière d'alertes critiques
critical_alerts = [a for a in alerts if a.get('severity') == 'critical']
if critical_alerts:
    st.markdown(f"""
    <div class="alert-banner" style="background-color: #dc3545; color: white; border-color: #bd2130;">
        🚨 ALERTE CRITIQUE - {len(critical_alerts)} MACHINE(S) EN PANNE 🚨
    </div>
    """, unsafe_allow_html=True)

# Vue d'ensemble - Gros indicateurs
st.markdown("<h2 style='text-align: center; font-size: 36px;'>📊 ÉTAT GLOBAL</h2>", unsafe_allow_html=True)

total_machines = len(machines_data)
normal_machines = sum(1 for m in machines_data.values() if m.get('status') == 'normal')
warning_machines = sum(1 for m in machines_data.values() if m.get('status') == 'warning')
critical_machines = sum(1 for m in machines_data.values() if m.get('status') == 'critical')

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="status-card status-normal">
        <div class="big-metric">🟢</div>
        <div class="big-metric">{normal_machines}</div>
        <div>MACHINES OK</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="status-card status-warning">
        <div class="big-metric">🟡</div>
        <div class="big-metric">{warning_machines}</div>
        <div>ALERTES</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="status-card status-critical">
        <div class="big-metric">🔴</div>
        <div class="big-metric">{critical_machines}</div>
        <div>CRITIQUES</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="status-card" style="background-color: #17a2b8; border-color: #138496; color: white;">
        <div class="big-metric">🏭</div>
        <div class="big-metric">{total_machines}</div>
        <div>TOTAL</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Détail par machine - Cartes simplifiées
st.markdown("<h2 style='text-align: center; font-size: 36px;'>🔧 DÉTAIL MACHINES</h2>", unsafe_allow_html=True)

if not machines_data:
    st.markdown("""
    <div class="alert-banner" style="background-color: #ffc107; color: black; border-color: #d39e00;">
        ⚠️ AUCUNE MACHINE DÉTECTÉE
    </div>
    """, unsafe_allow_html=True)
else:
    # Affichage en grille des machines
    cols = st.columns(min(len(machines_data), 3))
    
    for idx, (machine_id, machine_data) in enumerate(machines_data.items()):
        col = cols[idx % 3]
        
        status = machine_data.get('status', 'unknown')
        
        # Couleur selon le statut
        if status == 'normal':
            status_color = "#28a745"
            status_icon = "🟢"
            status_text = "OPÉRATIONNEL"
        elif status == 'warning':
            status_color = "#ffc107"
            status_icon = "🟡"
            status_text = "ATTENTION"
        elif status == 'critical':
            status_color = "#dc3545"
            status_icon = "🔴"
            status_text = "CRITIQUE"
        else:
            status_color = "#6c757d"
            status_icon = "⚪"
            status_text = "INCONNU"
        
        with col:
            st.markdown(f"""
            <div class="machine-card" style="border-color: {status_color};">
                <div style="text-align: center;">
                    <h2 style="font-size: 32px; margin: 0; color: {status_color};">
                        {status_icon} {machine_id}
                    </h2>
                    <h3 style="font-size: 24px; margin: 10px 0; color: {status_color};">
                        {status_text}
                    </h3>
                </div>
                
                <div style="margin: 20px 0;">
                    <strong style="font-size: 18px;">🌡️ Température:</strong><br>
                    <span style="font-size: 20px;">{machine_data.get('air_temperature', 'N/A')}°C</span>
                </div>
                
                <div style="margin: 20px 0;">
                    <strong style="font-size: 18px;">⚡ Vitesse:</strong><br>
                    <span style="font-size: 20px;">{machine_data.get('rotational_speed', 'N/A')} rpm</span>
                </div>
                
                <div style="margin: 20px 0;">
                    <strong style="font-size: 18px;">🎯 Risque Panne:</strong><br>
                    <span style="font-size: 20px; color: {status_color};">
                        {(machine_data.get('predicted_failure_probability', 0) * 100):.0f}%
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# Actions rapides - Gros boutons
st.markdown("<h2 style='text-align: center; font-size: 36px;'>⚡ ACTIONS RAPIDES</h2>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🚨 ARRÊT D'URGENCE", key="emergency_stop"):
        st.markdown("""
        <div class="alert-banner" style="background-color: #dc3545; color: white; border-color: #bd2130;">
            🛑 ARRÊT D'URGENCE ACTIVÉ (SIMULATION)
        </div>
        """, unsafe_allow_html=True)

with col2:
    if st.button("🔄 REDÉMARRER TOUT", key="restart_all"):
        st.markdown("""
        <div class="alert-banner" style="background-color: #ffc107; color: black; border-color: #d39e00;">
            🔄 REDÉMARRAGE EN COURS (SIMULATION)
        </div>
        """, unsafe_allow_html=True)

with col3:
    if st.button("📞 APPELER TECHNICIEN", key="call_tech"):
        st.markdown("""
        <div class="alert-banner" style="background-color: #17a2b8; color: white; border-color: #138496;">
            📞 TECHNICIEN CONTACTÉ (SIMULATION)
        </div>
        """, unsafe_allow_html=True)

with col4:
    if st.button("✅ ACQUITTER ALERTES", key="ack_alerts"):
        st.markdown("""
        <div class="alert-banner" style="background-color: #28a745; color: white; border-color: #1e7e34;">
            ✅ ALERTES ACQUITTÉES (SIMULATION)
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# Historique récent - Version simplifiée
st.markdown("<h2 style='text-align: center; font-size: 36px;'>📜 DERNIÈRES ALERTES</h2>", unsafe_allow_html=True)

if not alerts:
    st.markdown("""
    <div class="alert-banner" style="background-color: #28a745; color: white; border-color: #1e7e34;">
        ✅ AUCUNE ALERTE ACTIVE - SYSTÈME OPÉRATIONNEL
    </div>
    """, unsafe_allow_html=True)
else:
    # Afficher les 3 dernières alertes
    for alert in alerts[:3]:
        severity = alert.get('severity', 'info')
        machine = alert.get('machine_id', 'Unknown')
        message = alert.get('message', 'Pas de message')
        timestamp = alert.get('timestamp', 'Inconnu')
        
        if severity == 'critical':
            alert_color = "#dc3545"
            alert_icon = "🔴"
        elif severity == 'warning':
            alert_color = "#ffc107"
            alert_icon = "🟡"
        else:
            alert_color = "#17a2b8"
            alert_icon = "🔵"
        
        st.markdown(f"""
        <div class="alert-banner" style="background-color: {alert_color}; color: white; border-color: {alert_color};">
            {alert_icon} {machine} | {message} | {timestamp}
        </div>
        """, unsafe_allow_html=True)

# Footer avec horloge
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
st.markdown(f"""
<div style="background-color: #2c3e50; color: white; padding: 20px; margin: 2rem -1rem -1rem -1rem; text-align: center;">
    <h2 style="font-size: 28px; margin: 0;">🕒 {current_time}</h2>
    <p style="font-size: 18px; margin: 5px 0;">Actualisation automatique toutes les 10 secondes</p>
</div>
""", unsafe_allow_html=True)

# Auto-refresh toutes les 10 secondes en mode usine
time.sleep(10)
st.rerun()
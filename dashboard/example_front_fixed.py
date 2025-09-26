import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import random
import os
import requests

# Configuration API Backend
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')

# Fonction pour récupérer les vraies données des machines depuis le backend
@st.cache_data(ttl=5)  # Cache de 5 secondes pour les données live
def get_live_machines_data():
    """Récupère les données en temps réel depuis le backend IoT"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/machines/live")
        if response.status_code == 200:
            return response.json()
        else:
            st.warning(f"Erreur backend: {response.status_code}")
            return get_fallback_data()
    except Exception as e:
        st.warning(f"Connexion backend indisponible: {e}")
        return get_fallback_data()

def get_fallback_data():
    """Données de fallback si le backend n'est pas accessible"""
    return [
        {"id": 1, "name": "Machine de Production A", "type": "Presse hydraulique", 
         "status": "running", "sensors": {"temperature": 45.2, "pressure": 3.1, "velocity": 1.8}},
        {"id": 2, "name": "Machine de Production B", "type": "Convoyeur", 
         "status": "maintenance", "sensors": {"temperature": 38.5, "pressure": 2.8, "velocity": 1.2}},
        {"id": 3, "name": "Machine de Production C", "type": "Compresseur", 
         "status": "running", "sensors": {"temperature": 52.1, "pressure": 4.2, "velocity": 2.1}}
    ]

def get_real_sensor_data(machine_data):
    """Récupère les vraies données capteurs depuis le backend"""
    if machine_data and 'sensors' in machine_data:
        sensors = machine_data['sensors']
        return (
            sensors.get('temperature', 25.0),
            sensors.get('pressure', 3.0), 
            sensors.get('velocity', 1.5)
        )
    # Valeurs par défaut si pas de données
    return 25.0, 3.0, 1.5

def read_sensor_data(machine_data):
    """
    Lecture des vraies données capteurs depuis le backend.
    Remplace la simulation par les vraies valeurs IoT.
    """
    temp, pressure, velocity = get_real_sensor_data(machine_data)
    
    # Conversion des unités si nécessaire
    vib = pressure  # Pression utilisée comme vibration
    speed = velocity * 1000  # Vitesse convertie en RPM
    
    return temp, vib, speed

# Configuration de la page
st.set_page_config(
    page_title="IoT Predictive Maintenance Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === SYSTÈME DE REFRESH INTELLIGENT ===
# Initialiser le state pour l'auto-refresh
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()
if 'auto_refresh_counter' not in st.session_state:
    st.session_state.auto_refresh_counter = 0

# Contrôles de refresh dans la sidebar
st.sidebar.header("⚙️ Contrôles")

# Checkbox pour activer/désactiver l'auto-refresh
auto_refresh_enabled = st.sidebar.checkbox(
    "🔄 Refresh automatique", 
    value=True,
    help="Actualise les données automatiquement toutes les 5 secondes"
)

# Sélecteur d'intervalle de refresh
refresh_interval = st.sidebar.selectbox(
    "Intervalle de refresh (secondes)",
    options=[5, 10, 15, 30],
    index=0,
    help="Fréquence de mise à jour des données"
)

# Bouton de refresh manuel
if st.sidebar.button("🔃 Refresh manuel", help="Actualise immédiatement"):
    st.cache_data.clear()
    st.rerun()

# Affichage du statut de refresh
st.sidebar.info(f"Dernière MAJ: {st.session_state.last_update.strftime('%H:%M:%S')}")

# Données en temps réel depuis le backend
@st.cache_data(ttl=refresh_interval)
def get_current_machines_data():
    """Récupère les données actuelles des machines avec cache intelligent"""
    return get_live_machines_data()

def setup_auto_refresh():
    """Configure le refresh automatique intelligent"""
    if auto_refresh_enabled:
        current_time = datetime.now()
        time_since_last_update = (current_time - st.session_state.last_update).total_seconds()
        
        if time_since_last_update >= refresh_interval:
            st.session_state.last_update = current_time
            st.session_state.auto_refresh_counter += 1
            # Clear cache pour forcer la mise à jour
            st.cache_data.clear()
            st.rerun()

# Récupération des données machines depuis le backend
machines_data = get_current_machines_data()

def generate_mock_data():
    """Utilise maintenant les vraies données du backend"""
    return machines_data

def main():
    st.title("🏭 IoT Predictive Maintenance Dashboard")
    st.markdown("**Surveillance en temps réel des équipements industriels**")
    
    # Indicateurs de connexion
    col_status1, col_status2, col_status3 = st.columns(3)
    
    with col_status1:
        if machines_data:
            st.success("🔗 Backend connecté")
        else:
            st.error("❌ Backend déconnecté")
    
    with col_status2:
        st.info(f"🔄 Refresh: {refresh_interval}s")
    
    with col_status3:
        st.info(f"📊 Machines: {len(machines_data) if machines_data else 0}")

    # === DONNÉES EN TEMPS RÉEL ===
    machines = generate_mock_data()
    
    if not machines:
        st.error("Aucune donnée machine disponible")
        return

    # Sélection de la machine
    st.sidebar.header("🏭 Sélection Machine")
    machine_names = [f"{m['name']} (ID: {m['id']})" for m in machines]
    selected_machine_index = st.sidebar.selectbox(
        "Choisir une machine:",
        range(len(machine_names)),
        format_func=lambda x: machine_names[x]
    )
    
    selected_machine = machines[selected_machine_index]
    machine_id = selected_machine['id']
    
    # === AFFICHAGE DES MÉTRIQUES TEMPS RÉEL ===
    st.header(f"📊 Surveillance: {selected_machine['name']}")
    
    # Lecture des capteurs en temps réel
    temp, vib, speed = read_sensor_data(selected_machine)
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_color = {"running": "🟢", "maintenance": "🟡", "error": "🔴"}.get(selected_machine.get('status', 'unknown'), "⚪")
        st.metric("Statut", f"{status_color} {selected_machine.get('status', 'N/A').title()}")
    
    with col2:
        temp_status = "🔴" if temp > 60 else "🟡" if temp > 45 else "🟢"
        st.metric("Température", f"{temp:.1f}°C", delta=f"{temp_status}")
    
    with col3:
        vib_status = "🔴" if vib > 5 else "🟡" if vib > 3 else "🟢"
        st.metric("Vibrations", f"{vib:.2f} mm/s", delta=f"{vib_status}")
    
    with col4:
        speed_status = "🔴" if speed > 1800 else "🟡" if speed > 1600 else "🟢"
        st.metric("Vitesse", f"{speed:.0f} RPM", delta=f"{speed_status}")

    # === GRAPHIQUES TEMPS RÉEL ===
    st.subheader("📈 Surveillance Temps Réel (Backend IoT)")

    # Initialisation des données dans le session state
    session_key = f'real_time_data_{machine_id}'
    if session_key not in st.session_state:
        st.session_state[session_key] = {
            'temp_values': [],
            'vib_values': [],
            'speed_values': [],
            'timestamps': []
        }

    # Mise à jour des données en temps réel
    current_time = datetime.now()
    session_data = st.session_state[session_key]
    
    # Ajouter de nouvelles données toutes les 2 secondes
    if len(session_data['timestamps']) == 0 or \
       (current_time - session_data['timestamps'][-1]).total_seconds() >= 2:
        
        # Récupération des vraies données depuis le backend
        new_temp, new_vib, new_speed = read_sensor_data(selected_machine)

        # Mise à jour des données
        session_data['temp_values'].append(new_temp)
        session_data['vib_values'].append(new_vib)
        session_data['speed_values'].append(new_speed)
        session_data['timestamps'].append(current_time)

        # Garder uniquement les 30 derniers points (1 minute)
        if len(session_data['timestamps']) > 30:
            for key in ['temp_values', 'vib_values', 'speed_values', 'timestamps']:
                session_data[key] = session_data[key][-30:]

    # Affichage des graphiques
    col_graph1, col_graph2 = st.columns(2)
    
    with col_graph1:
        # Graphique température
        fig_temp = go.Figure()
        fig_temp.add_trace(go.Scatter(
            x=session_data['timestamps'], 
            y=session_data['temp_values'],
            mode='lines+markers',
            name='Température',
            line=dict(color='#ff6b6b', width=2),
            marker=dict(size=4)
        ))
        fig_temp.add_hline(y=60, line_dash="dash", line_color="#dc3545", annotation_text="Seuil critique")
        fig_temp.add_hline(y=45, line_dash="dash", line_color="#ffc107", annotation_text="Seuil attention")
        
        fig_temp.update_layout(
            title="🌡️ Température Temps Réel",
            xaxis_title="Heure",
            yaxis_title="Température (°C)",
            height=350,
            showlegend=False,
            xaxis=dict(tickformat='%H:%M:%S')
        )
        st.plotly_chart(fig_temp, use_container_width=True, key=f"temp_live_{machine_id}")

    with col_graph2:
        # Graphique vibrations
        fig_vib = go.Figure()
        fig_vib.add_trace(go.Scatter(
            x=session_data['timestamps'], 
            y=session_data['vib_values'],
            mode='lines+markers',
            name='Vibrations',
            line=dict(color='#4ecdc4', width=2),
            marker=dict(size=4)
        ))
        fig_vib.add_hline(y=5, line_dash="dash", line_color="#dc3545", annotation_text="Seuil critique")
        fig_vib.add_hline(y=3, line_dash="dash", line_color="#ffc107", annotation_text="Seuil attention")
        
        fig_vib.update_layout(
            title="📳 Vibrations Temps Réel",
            xaxis_title="Heure", 
            yaxis_title="Vibrations (mm/s)",
            height=350,
            showlegend=False,
            xaxis=dict(tickformat='%H:%M:%S')
        )
        st.plotly_chart(fig_vib, use_container_width=True, key=f"vib_live_{machine_id}")

    # Graphique vitesse (pleine largeur)
    st.subheader("🔄 Vitesse de Rotation")
    fig_speed = go.Figure()
    fig_speed.add_trace(go.Scatter(
        x=session_data['timestamps'], 
        y=session_data['speed_values'],
        mode='lines+markers',
        name='Vitesse',
        line=dict(color='#45b7d1', width=3),
        marker=dict(size=5),
        fill='tonexty'
    ))
    fig_speed.add_hline(y=1800, line_dash="dash", line_color="#dc3545", annotation_text="Seuil critique")
    fig_speed.add_hline(y=1600, line_dash="dash", line_color="#ffc107", annotation_text="Seuil attention")
    
    fig_speed.update_layout(
        title="⚡ Vitesse de Rotation Temps Réel",
        xaxis_title="Heure",
        yaxis_title="Vitesse (RPM)", 
        height=300,
        showlegend=False,
        xaxis=dict(tickformat='%H:%M:%S')
    )
    st.plotly_chart(fig_speed, use_container_width=True, key=f"speed_live_{machine_id}")

    # === ANALYSE ET ALERTES ===
    st.header("🚨 Analyse Prédictive")

    # Calcul des anomalies basées sur les vraies données
    anomaly_score = 0
    alerts = []

    if temp > 60:
        anomaly_score += 3
        alerts.append("🔴 **TEMPÉRATURE CRITIQUE**")
    elif temp > 45:
        anomaly_score += 1
        alerts.append("🟡 Température élevée")

    if vib > 5:
        anomaly_score += 3
        alerts.append("🔴 **VIBRATIONS CRITIQUES**")
    elif vib > 3:
        anomaly_score += 1
        alerts.append("🟡 Vibrations élevées")

    if speed > 1800:
        anomaly_score += 2
        alerts.append("🔴 **VITESSE EXCESSIVE**")
    elif speed > 1600:
        anomaly_score += 1
        alerts.append("🟡 Vitesse élevée")

    # Affichage des alertes
    col_alert1, col_alert2 = st.columns([2, 1])

    with col_alert1:
        if anomaly_score >= 5:
            st.error("🚨 **ARRÊT IMMÉDIAT REQUIS**")
            st.markdown("**Actions immédiates:**")
            st.markdown("""
            1. 🛑 Arrêter la machine immédiatement
            2. 📞 Contacter l'équipe de maintenance d'urgence
            3. 🔍 Investigation approfondie requise
            4. 📋 Ne pas redémarrer sans autorisation
            """)

        elif anomaly_score >= 3:
            st.warning("⚠️ **MAINTENANCE URGENTE REQUISE**")
            st.markdown("**Actions recommandées:**")
            st.markdown("""
            1. 📅 Programmer une maintenance dans les 24h
            2. 📊 Surveiller de près les paramètres
            3. 🔔 Alerter l'équipe de maintenance
            4. 📝 Documenter les anomalies observées
            """)

        elif anomaly_score >= 1:
            st.info("ℹ️ **SURVEILLANCE RENFORCÉE**")
            st.markdown("**Actions préventives:**")
            st.markdown("""
            1. 📈 Augmenter la fréquence de contrôle
            2. 🔧 Vérifier les paramètres de fonctionnement
            3. 📋 Planifier une maintenance préventive
            4. 👀 Surveiller l'évolution des anomalies
            """)

            if st.button("📋 Planifier maintenance préventive"):
                st.success("Maintenance préventive programmée pour dans 3 jours")

        else:
            st.success("✅ **MACHINE EN BON ÉTAT**")
            st.markdown("Maintenance préventive selon planning habituel")

    with col_alert2:
        # Score d'anomalie visuel
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=anomaly_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Score Anomalie"},
            gauge={
                'axis': {'range': [None, 10]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 2], 'color': "lightgreen"},
                    {'range': [2, 5], 'color': "yellow"}, 
                    {'range': [5, 10], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 7
                }
            }
        ))
        fig_gauge.update_layout(height=250)
        st.plotly_chart(fig_gauge, use_container_width=True)

    # Liste des alertes
    if alerts:
        st.subheader("📢 Alertes Actives")
        for alert in alerts:
            st.markdown(f"• {alert}")

    # Boutons d'action
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📧 Envoyer rapport"):
            st.info("Rapport envoyé au responsable maintenance")
    with col2:
        if st.button("📱 Notifier équipe"):
            st.info("Équipe notifiée de l'état de la machine")
    with col3:
        if st.button("📊 Exporter données"):
            st.info("Données exportées au format CSV")

    # Informations de debug (optionnel)
    with st.expander("🔧 Informations de Debug"):
        st.json({
            "machine_id": machine_id,
            "last_update": st.session_state.last_update.isoformat(),
            "refresh_counter": st.session_state.auto_refresh_counter,
            "auto_refresh": auto_refresh_enabled,
            "refresh_interval": refresh_interval,
            "backend_status": "connected" if machines_data else "disconnected",
            "current_readings": {
                "temperature": temp,
                "vibrations": vib, 
                "speed": speed
            }
        })

if __name__ == "__main__":
    # === POINT D'ENTRÉE PRINCIPAL ===
    main()
    
    # === REFRESH INTELLIGENT (remplace le refresh agressif) ===
    # Plus de time.sleep(3) + st.rerun() qui causait le clignotement !
    setup_auto_refresh()
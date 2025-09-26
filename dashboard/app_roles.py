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
import json

# Configuration de la page
st.set_page_config(
    page_title="IoT Predictive Maintenance Dashboard - Multi Roles",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration API Backend
API_BASE_URL = os.getenv("BACKEND_URL", "http://backend:8000")

@st.cache_data(ttl=5)  # Cache pendant 5 secondes
def get_live_machines_data():
    """Récupère les données des machines depuis l'API backend"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/machines/live")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Erreur connexion API: {e}")
        return None

def get_ai_prediction_for_machine(machine_data):
    """Récupère la prédiction IA pour une machine depuis les données live"""
    try:
        ai_prediction = machine_data.get("ai_prediction", {})
        prediction = ai_prediction.get("prediction", {})
        
        if prediction:
            failure_prob = prediction.get("failure_probability", 0)
            predicted_status = prediction.get("predicted_status", "unknown")
            
            # Conversion des statuts backend vers statuts interface
            if predicted_status == "normal" or failure_prob < 0.3:
                return 0  # Vert
            elif predicted_status == "alert" or failure_prob < 0.7:
                return 1  # Orange  
            else:
                return 2  # Rouge
        
        return 0  # Par défaut normal
    except Exception as e:
        return 0

def get_status_color(status):
    colors = {0: "#28a745", 1: "#ffc107", 2: "#dc3545"}  # Vert, Orange, Rouge
    return colors[status]

def get_status_text(status):
    texts = {0: "NORMAL", 1: "ATTENTION", 2: "CRITIQUE"}
    return texts[status]

def get_status_emoji(status):
    emojis = {0: "🟢", 1: "🟡", 2: "🔴"}
    return emojis[status]

def simulate_real_time_sensor_data(base_temp, base_pressure, base_velocity, status):
    """Simule des données temps réel basées sur les valeurs actuelles et le statut"""
    # Ajouter un peu de bruit pour le temps réel
    temp = base_temp + np.random.normal(0, 1)
    pressure = base_pressure + np.random.normal(0, 0.1)
    velocity = base_velocity + np.random.normal(0, 0.05)
    
    # Ajuster selon le statut pour la simulation temps réel
    if status >= 1:
        temp += 10 if status == 2 else 5
        pressure += 2 if status == 2 else 1
        velocity += 1 if status == 2 else 0.5
    
    return temp, pressure, velocity

# Interface principale
def main():
    # En-tête avec titre et logo
    col_title, col_logo = st.columns([4, 1])

    with col_title:
        st.title("🏭 IoT Predictive Maintenance")

    with col_logo:
        # Affichage du logo
        logo_path = "dashboard/picture.jpg"
        if os.path.exists(logo_path):
            st.image(logo_path, width=200)
        else:
            st.markdown("**Hackfinity**<br/>*IoT Solutions*", unsafe_allow_html=True)

    # Sidebar pour sélection du rôle
    st.sidebar.title("Sélection du rôle")
    user_role = st.sidebar.selectbox(
        "Choisissez votre rôle:",
        ["Opérateur d'usine", "Team Leader", "Technicien de maintenance"]
    )

    # Récupération des données des machines
    machines_response = get_live_machines_data()
    if not machines_response or machines_response["status"] != "success":
        st.error("❌ Impossible de récupérer les données des machines")
        st.stop()
    
    machines_data = machines_response["machines"]
    
    # Conversion des données pour compatibilité avec l'interface
    machines = []
    for machine_id, machine_info in machines_data.items():
        # Calcul du statut basé sur l'IA
        ai_status = get_ai_prediction_for_machine(machine_info)
        
        machine = {
            "id": machine_id,
            "name": f"Machine {machine_id}",
            "type": f"Équipement industriel - {machine_info.get('product_type', 'TypeA')}",
            "status": ai_status,
            "temperature": machine_info.get("temperature", 0),
            "pressure": machine_info.get("pressure", 0), 
            "velocity": machine_info.get("velocity", 0),
            "timestamp": machine_info.get("timestamp", ""),
            "ai_prediction": machine_info.get("ai_prediction", {}),
            "confidence_score": machine_info.get("ai_prediction", {}).get("prediction", {}).get("confidence", 0.9),
            "anomaly_value": machine_info.get("ai_prediction", {}).get("prediction", {}).get("failure_probability", 0),
            "last_maintenance": datetime.now() - timedelta(days=random.randint(1, 30)),
            "next_maintenance": datetime.now() + timedelta(days=random.randint(1, 15))
        }
        machines.append(machine)

    if user_role == "Opérateur d'usine":
        operator_interface(machines)
    elif user_role == "Team Leader":
        team_leader_interface(machines)
    else:
        maintenance_technician_interface(machines)

def operator_interface(machines):
    """Interface ultra-simplifiée pour les opérateurs"""
    st.header("👷‍♂️ Interface Opérateur")

    # Sélection de la machine
    machine_names = [f"{m['id']} - {m['name']}" for m in machines]
    if not machine_names:
        st.warning("⏳ Aucune machine disponible. En attente de données...")
        return
        
    selected_machine_name = st.selectbox("Sélectionnez votre machine:", machine_names, index=0 if machine_names else None)
    if not selected_machine_name:
        st.warning("⏳ Veuillez sélectionner une machine")
        return
    
    # Protection contre None
    try:
        selected_machine_id = selected_machine_name.split()[0]
    except (AttributeError, IndexError):
        st.error("❌ Erreur sélection machine")
        return
    machine = next((m for m in machines if m["id"] == selected_machine_id), None)

    if not machine:
        st.error("Machine introuvable")
        return

    # Affichage principal du voyant
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### État de votre machine")

        # Voyant principal
        status_color = get_status_color(machine["status"])
        status_text = get_status_text(machine["status"])
        status_emoji = get_status_emoji(machine["status"])

        st.markdown(f"""
        <div style="
            text-align: center; 
            padding: 50px; 
            border: 5px solid {status_color}; 
            border-radius: 20px; 
            background-color: {status_color}20;
            margin: 20px 0;
        ">
            <h1 style="color: {status_color}; margin: 0; font-size: 4em;">{status_emoji}</h1>
            <h2 style="color: {status_color}; margin: 10px 0;">{status_text}</h2>
        </div>
        """, unsafe_allow_html=True)

    # Messages explicatifs
    if machine["status"] == 0:
        st.success("✅ **TOUT VA BIEN** - Votre machine fonctionne normalement")
        st.info(f"🌡️ Température: {machine['temperature']:.1f}°C | 📊 Pression: {machine['pressure']:.1f} bar | 🏃 Vitesse: {machine['velocity']:.1f} m/s")
    elif machine["status"] == 1:
        st.warning("⚠️ **ATTENTION** - Possibilité de panne dans le shift. Surveillez attentivement.")
        st.warning(f"🌡️ Température: {machine['temperature']:.1f}°C | 📊 Pression: {machine['pressure']:.1f} bar | 🏃 Vitesse: {machine['velocity']:.1f} m/s")
        failure_prob = machine["anomaly_value"] * 100
        st.warning(f"🎯 **Probabilité d'anomalie: {failure_prob:.1f}%**")
    else:
        st.error("🚨 **PANNE IMMINENTE** - Arrêtez la machine et contactez immédiatement la maintenance!")
        st.error(f"🌡️ Température: {machine['temperature']:.1f}°C | 📊 Pression: {machine['pressure']:.1f} bar | 🏃 Vitesse: {machine['velocity']:.1f} m/s")
        failure_prob = machine["anomaly_value"] * 100
        st.error(f"🎯 **Probabilité de panne: {failure_prob:.1f}%**")

    # Bouton d'urgence pour l'opérateur
    st.markdown("---")
    col_emergency1, col_emergency2, col_emergency3 = st.columns([1, 1, 1])
    
    with col_emergency2:
        if st.button("🚨 SIGNALER PANNE D'URGENCE", use_container_width=True, type="primary"):
            st.balloons()
            st.success("🚨 **ALERTE ENVOYÉE** - L'équipe de maintenance a été notifiée!")

def team_leader_interface(machines):
    """Interface complète pour les team leaders"""
    st.header("👨‍💼 Interface Team Leader")

    # Initialiser le state pour la navigation
    if 'selected_machine_details' not in st.session_state:
        st.session_state.selected_machine_details = None

    # Si une machine est sélectionnée, afficher ses détails en plein écran
    if st.session_state.selected_machine_details is not None:
        show_machine_details_fullscreen(st.session_state.selected_machine_details, machines)
        return

    # Vue d'ensemble des machines (affichage normal)
    st.subheader("Vue d'ensemble de l'atelier")

    # Statistiques générales
    col1, col2, col3, col4 = st.columns(4)

    normal_count = sum(1 for m in machines if m["status"] == 0)
    attention_count = sum(1 for m in machines if m["status"] == 1)
    critical_count = sum(1 for m in machines if m["status"] == 2)

    with col1:
        st.metric("Total machines", len(machines))
    with col2:
        st.metric("Machines OK", normal_count, delta=None, delta_color="normal")
    with col3:
        st.metric("Machines en attention", attention_count, delta=None, delta_color="off")
    with col4:
        st.metric("Machines critiques", critical_count, delta=None, delta_color="inverse")

    # Notifications
    if critical_count > 0:
        st.error(f"🚨 **ALERTE CRITIQUE** - {critical_count} machine(s) nécessite(nt) une intervention immédiate!")
    if attention_count > 0:
        st.warning(f"⚠️ **ATTENTION** - {attention_count} machine(s) à surveiller de près")

    # Grille des machines
    st.subheader("État des machines")

    cols = st.columns(3)
    for i, machine in enumerate(machines):
        with cols[i % 3]:
            status_color = get_status_color(machine["status"])
            status_emoji = get_status_emoji(machine["status"])
            
            with st.container():
                st.markdown(f"""
                <div style="border: 2px solid {status_color}; border-radius: 10px; padding: 15px; margin: 10px 0; background-color: {status_color}10;">
                    <h4 style="color: {status_color}; margin: 0;">{status_emoji} {machine['name']}</h4>
                    <p style="margin: 5px 0;"><strong>Type:</strong> {machine['type']}</p>
                    <p style="margin: 5px 0;"><strong>Température:</strong> {machine['temperature']:.1f}°C</p>
                    <p style="margin: 5px 0;"><strong>Pression:</strong> {machine['pressure']:.1f} bar</p>
                    <p style="margin: 5px 0;"><strong>Vitesse:</strong> {machine['velocity']:.1f} m/s</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"🔍 Détails {machine['name']}", key=f"details_{machine['id']}"):
                    st.session_state.selected_machine_details = machine["id"]
                    st.rerun()

def show_machine_details_fullscreen(machine_id, machines):
    """Affiche les détails d'une machine en plein écran pour le Team Leader"""
    # Trouver la machine correspondante
    machine = next((m for m in machines if m['id'] == machine_id), None)
    if not machine:
        st.error("Machine introuvable")
        return

    # Bouton de retour en haut à gauche
    col_back, col_title = st.columns([1, 6])
    with col_back:
        if st.button("← Retour", key="back_to_overview"):
            st.session_state.selected_machine_details = None
            st.rerun()

    with col_title:
        st.title(f"🔍 Détails - {machine['name']}")

    st.divider()

    # Section 1: État général de la machine
    st.subheader("📊 État Général")

    col1, col2, col3, col4 = st.columns(4)

    status_color = get_status_color(machine["status"])
    status_text = get_status_text(machine["status"])
    status_emoji = get_status_emoji(machine["status"])

    with col1:
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; border: 3px solid {status_color}; 
                    border-radius: 15px; background-color: {status_color}20;">
            <h2 style="color: {status_color}; margin: 0;">{status_emoji}</h2>
            <h3 style="color: {status_color}; margin: 5px 0;">{status_text}</h3>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        confidence_pct = machine['confidence_score'] * 100
        st.metric("Score de confiance IA", f"{confidence_pct:.1f}%",
                 delta=f"{(confidence_pct-85):.1f}%")

    with col3:
        anomaly_pct = machine['anomaly_value'] * 100
        st.metric("Probabilité d'anomalie", f"{anomaly_pct:.1f}%",
                 delta=f"{anomaly_pct:.1f}%")

    with col4:
        st.metric("Type d'équipement", machine["type"].split(" - ")[0])

    st.divider()

    # Section 2: Données des capteurs industriels
    st.subheader("📊 Capteurs Industriels Temps Réel")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Gauge température
        fig_temp = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = machine["temperature"],
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "🌡️ Température (°C)"},
            gauge = {
                'axis': {'range': [0, 80]},
                'bar': {'color': "darkred"},
                'steps': [
                    {'range': [0, 30], 'color': "lightgray"},
                    {'range': [30, 60], 'color': "yellow"},
                    {'range': [60, 80], 'color': "red"}
                ]
            }
        ))
        fig_temp.update_layout(height=250)
        st.plotly_chart(fig_temp, use_container_width=True, key=f"temp_detail_{machine_id}")
    
    with col2:
        # Gauge pression  
        fig_pressure = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = machine["pressure"],
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
        st.plotly_chart(fig_pressure, use_container_width=True, key=f"pressure_detail_{machine_id}")
    
    with col3:
        # Gauge vitesse
        fig_velocity = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = machine["velocity"],
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "🏃 Vitesse (m/s)"},
            gauge = {
                'axis': {'range': [0, 6]},
                'bar': {'color': "green"},
                'steps': [
                    {'range': [0, 2], 'color': "lightgray"},
                    {'range': [2, 4], 'color': "yellow"},
                    {'range': [4, 6], 'color': "red"}
                ]
            }
        ))
        fig_velocity.update_layout(height=250)
        st.plotly_chart(fig_velocity, use_container_width=True, key=f"velocity_detail_{machine_id}")

    st.divider()

    # Section 3: Simulation graphiques temps réel
    st.subheader("📈 Surveillance Temps Réel (Simulée)")

    # Auto-refresh pour les graphiques
    placeholder = st.empty()

    # Initialisation des données dans le state de session si nécessaire
    session_key = f'real_time_data_{machine_id}'
    if session_key not in st.session_state:
        st.session_state[session_key] = {
            'temp_values': [],
            'pressure_values': [],
            'velocity_values': [],
            'timestamps': []
        }

    # Mise à jour des données en temps réel (simulées)
    current_time = datetime.now()
    session_data = st.session_state[session_key]
    
    if len(session_data['timestamps']) == 0 or \
       (current_time - session_data['timestamps'][-1]).seconds >= 2:
        
        # Génération de nouvelles données basées sur les vraies valeurs + simulation
        new_temp, new_pressure, new_velocity = simulate_real_time_sensor_data(
            machine["temperature"], machine["pressure"], machine["velocity"], machine["status"]
        )

        # Mise à jour des données
        session_data['temp_values'].append(new_temp)
        session_data['pressure_values'].append(new_pressure)  
        session_data['velocity_values'].append(new_velocity)
        session_data['timestamps'].append(current_time)

        # Garder uniquement les 30 derniers points (1 minute)
        if len(session_data['timestamps']) > 30:
            for key in ['temp_values', 'pressure_values', 'velocity_values', 'timestamps']:
                session_data[key] = session_data[key][-30:]

    # Affichage des graphiques temps réel
    with placeholder.container():
        col_graph1, col_graph2 = st.columns(2)
        
        # Graphique température
        with col_graph1:
            fig_temp_trend = go.Figure()
            fig_temp_trend.add_trace(go.Scatter(
                x=session_data['timestamps'], 
                y=session_data['temp_values'],
                mode='lines+markers',
                name='Température',
                line=dict(color='#ff6b6b', width=2)
            ))
            fig_temp_trend.add_hline(y=60, line_dash="dash", line_color="#dc3545", annotation_text="Seuil critique")
            fig_temp_trend.add_hline(y=45, line_dash="dash", line_color="#ffc107", annotation_text="Seuil attention")
            
            fig_temp_trend.update_layout(
                title="Température Temps Réel",
                xaxis_title="Heure",
                yaxis_title="Température (°C)",
                height=300,
                showlegend=False
            )
            st.plotly_chart(fig_temp_trend, use_container_width=True, key=f"temp_trend_{machine_id}")

        # Graphique pression
        with col_graph2:
            fig_pressure_trend = go.Figure()
            fig_pressure_trend.add_trace(go.Scatter(
                x=session_data['timestamps'], 
                y=session_data['pressure_values'],
                mode='lines+markers',
                name='Pression',
                line=dict(color='#4ecdc4', width=2)
            ))
            fig_pressure_trend.add_hline(y=8, line_dash="dash", line_color="#dc3545", annotation_text="Seuil critique")
            fig_pressure_trend.add_hline(y=6, line_dash="dash", line_color="#ffc107", annotation_text="Seuil attention")
            
            fig_pressure_trend.update_layout(
                title="Pression Temps Réel", 
                xaxis_title="Heure",
                yaxis_title="Pression (bar)",
                height=300,
                showlegend=False
            )
            st.plotly_chart(fig_pressure_trend, use_container_width=True, key=f"pressure_trend_{machine_id}")

        # Graphique vitesse (pleine largeur)
        fig_velocity_trend = go.Figure()
        fig_velocity_trend.add_trace(go.Scatter(
            x=session_data['timestamps'], 
            y=session_data['velocity_values'],
            mode='lines+markers',
            name='Vitesse',
            line=dict(color='#45b7d1', width=2)
        ))
        fig_velocity_trend.add_hline(y=4, line_dash="dash", line_color="#dc3545", annotation_text="Seuil critique")
        fig_velocity_trend.add_hline(y=3, line_dash="dash", line_color="#ffc107", annotation_text="Seuil attention")

        fig_velocity_trend.update_layout(
            title="Vitesse Temps Réel",
            xaxis_title="Heure", 
            yaxis_title="Vitesse (m/s)",
            height=300,
            showlegend=False
        )
        st.plotly_chart(fig_velocity_trend, use_container_width=True, key=f"velocity_trend_{machine_id}")

    # Auto-refresh toutes les 3 secondes
    time.sleep(3)
    st.rerun()

def maintenance_technician_interface(machines):
    """Interface technique détaillée pour les techniciens de maintenance"""
    st.header("🔧 Interface Technicien de Maintenance")

    # Sélection de la machine à analyser
    machine_names = [f"{m['id']} - {m['name']}" for m in machines]
    
    if not machine_names:
        st.warning("⚠️ Aucune machine disponible. Vérifiez la connexion au backend.")
        return
    
    selected_machine_name = st.selectbox("Sélectionnez la machine à analyser:", machine_names)
    
    if not selected_machine_name:
        st.warning("⚠️ Veuillez sélectionner une machine.")
        return
        
    selected_machine_id = selected_machine_name.split()[0] 
    machine = next((m for m in machines if m["id"] == selected_machine_id), None)

    if not machine:
        st.error("Machine introuvable")
        return

    # Onglets pour différentes analyses
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Analyse Temps Réel", "🔍 Diagnostics IA", "📋 Historique", "🛠️ Actions"])

    with tab1:
        st.subheader("Analyse des capteurs industriels en temps réel")
        
        # Informations techniques détaillées
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🌡️ Température", f"{machine['temperature']:.2f}°C")
            temp_status = "🟢 Normale" if machine['temperature'] < 45 else "🟡 Élevée" if machine['temperature'] < 60 else "🔴 Critique"
            st.write(temp_status)
        
        with col2:
            st.metric("📊 Pression", f"{machine['pressure']:.2f} bar")
            pressure_status = "🟢 Normale" if machine['pressure'] < 6 else "🟡 Élevée" if machine['pressure'] < 8 else "🔴 Critique"
            st.write(pressure_status)
        
        with col3:
            st.metric("🏃 Vitesse", f"{machine['velocity']:.2f} m/s")
            velocity_status = "🟢 Normale" if machine['velocity'] < 3 else "🟡 Élevée" if machine['velocity'] < 4 else "🔴 Critique"
            st.write(velocity_status)
        
        with col4:
            st.metric("⚡ État global", get_status_text(machine["status"]))
            st.write(get_status_emoji(machine["status"]))

        # Graphiques techniques détaillés
        st.subheader("📈 Tendances techniques")
        
        # Simulation de données historiques techniques
        dates = pd.date_range(start=datetime.now()-timedelta(hours=24), end=datetime.now(), freq='H')
        
        # Graphiques pour chaque capteur industriel
        sensors = ['Température', 'Pression', 'Vitesse']
        sensor_colors = ['#ff6b6b', '#4ecdc4', '#45b7d1']
        sensor_ranges = [(15, 80), (0.5, 12), (0, 6)]  # Plages réalistes industrielles
        
        for i, (sensor, color, (min_val, max_val)) in enumerate(zip(sensors, sensor_colors, sensor_ranges)):
            # Génération de données basées sur la valeur actuelle
            if sensor == 'Température':
                base_value = machine['temperature']
            elif sensor == 'Pression':
                base_value = machine['pressure']  
            else:
                base_value = machine['velocity']
            
            # Simulation de variation sur 24h
            values = np.random.normal(base_value, abs(base_value * 0.1), len(dates))
            
            # Ajouter des anomalies si statut problématique
            if machine["status"] >= 1:
                anomaly_factor = 1.3 if machine["status"] == 1 else 1.6
                values = values * anomaly_factor

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates, y=values,
                mode='lines+markers',
                name=sensor,
                line=dict(color=color, width=2),
                marker=dict(color=color, size=4)
            ))

            # Seuils techniques 
            critical_threshold = max_val * 0.8
            warning_threshold = max_val * 0.6
            
            fig.add_hline(y=critical_threshold, line_dash="dash", line_color="#dc3545",
                         annotation_text="Seuil critique", annotation_position="bottom right")
            fig.add_hline(y=warning_threshold, line_dash="dash", line_color="#ffc107",
                         annotation_text="Seuil attention", annotation_position="bottom right")

            # Zones colorées
            fig.add_hrect(y0=min_val, y1=warning_threshold, fillcolor="#28a745", opacity=0.1, 
                         annotation_text="Zone normale", annotation_position="top left")
            fig.add_hrect(y0=warning_threshold, y1=critical_threshold, fillcolor="#ffc107", opacity=0.1,
                         annotation_text="Zone attention", annotation_position="top left")
            fig.add_hrect(y0=critical_threshold, y1=max_val, fillcolor="#dc3545", opacity=0.1,
                         annotation_text="Zone critique", annotation_position="top left")

            fig.update_layout(
                title=f"{sensor} - Évolution 24h",
                xaxis_title="Heure",
                yaxis_title=f"{sensor} ({'°C' if sensor=='Température' else 'bar' if sensor=='Pression' else 'm/s'})",
                height=300,
                showlegend=False,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True, key=f"tech_{sensor.lower()}_{machine['id']}")

    with tab2:
        st.subheader("🧠 Diagnostics IA détaillés")

        # Informations IA détaillées
        ai_pred = machine.get("ai_prediction", {}).get("prediction", {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Analyse IA:**")
            
            predicted_status = ai_pred.get("predicted_status", "unknown")
            failure_prob = ai_pred.get("failure_probability", 0) * 100
            confidence = ai_pred.get("confidence", 0) * 100
            
            if predicted_status == "normal":
                st.success(f"✅ État prédit: {predicted_status.upper()}")
            elif predicted_status == "alert":
                st.warning(f"⚠️ État prédit: {predicted_status.upper()}")  
            else:
                st.error(f"🚨 État prédit: {predicted_status.upper()}")
            
            st.metric("Probabilité de panne", f"{failure_prob:.1f}%")
            st.metric("Confiance du modèle", f"{confidence:.1f}%")
            
            # Informations sur le modèle IA
            model_info = ai_pred.get("model_info", {})
            st.write(f"**Modèle utilisé:** {model_info.get('type', 'N/A')}")
            st.write(f"**Score d'anomalie:** {model_info.get('anomaly_score', 0):.3f}")
        
        with col2:
            st.markdown("**Paramètres critiques détectés:**")
            
            if machine["status"] == 2:
                st.error("🌡️ **Température**: Surchauffe critique détectée")
                st.error("📊 **Pression**: Dépassement seuil de sécurité")
                st.error("🏃 **Vitesse**: Emballement mécanique")
                st.markdown("**Cause probable**: Défaillance système de refroidissement + usure mécanique")
            elif machine["status"] == 1:
                st.warning("🌡️ **Température**: Élévation anormale détectée") 
                st.warning("📊 **Pression**: Fluctuations inhabituelles")
                st.warning("🏃 **Vitesse**: Variations de régime")
                st.markdown("**Cause probable**: Usure progressive des composants")
            else:
                st.success("✅ Tous les paramètres industriels dans les normes")
                st.markdown("**État**: Fonctionnement optimal détecté")

    with tab3:
        st.subheader("📋 Historique et maintenance")

        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Informations de maintenance:**")
            st.write(f"🔧 **Dernière maintenance:** {machine['last_maintenance'].strftime('%d/%m/%Y')}")
            st.write(f"📅 **Prochaine maintenance:** {machine['next_maintenance'].strftime('%d/%m/%Y')}")
            
            days_since = (datetime.now() - machine['last_maintenance']).days
            days_until = (machine['next_maintenance'] - datetime.now()).days
            
            st.metric("Jours depuis maintenance", days_since)
            st.metric("Jours avant maintenance", days_until)
            
        with col2:
            st.markdown("**Historique des interventions:**")
            interventions = [
                {"date": "15/09/2025", "type": "Préventive", "action": "Changement filtres"},
                {"date": "02/09/2025", "type": "Corrective", "action": "Réparation capteur pression"},
                {"date": "20/08/2025", "type": "Préventive", "action": "Lubrification générale"}
            ]
            
            for intervention in interventions:
                st.write(f"📋 **{intervention['date']}** - {intervention['type']}: {intervention['action']}")

    with tab4:
        st.subheader("🛠️ Actions de maintenance")

        if machine["status"] == 2:
            st.error("🚨 **INTERVENTION URGENTE REQUISE**")
            st.markdown("""
            **Actions immédiates:**
            1. 🛑 Arrêt immédiat de la machine
            2. 🔒 Verrouillage/consignation sécurité
            3. 🧊 Vérification système refroidissement
            4. ⚙️ Inspection mécanique complète
            5. 📞 Contact équipe spécialisée
            """)
            
        elif machine["status"] == 1:
            st.warning("⚠️ **SURVEILLANCE RENFORCÉE**")
            st.markdown("""
            **Actions recommandées:**
            1. 📊 Augmentation fréquence contrôles
            2. 🔍 Inspection visuelle quotidienne
            3. 📝 Préparation intervention préventive
            4. 📦 Commande pièces de rechange
            5. 👥 Information équipe suivante
            """)
            
        else:
            st.success("✅ **MAINTENANCE PRÉVENTIVE**")
            st.markdown("""
            **Actions standards:**
            1. 🔧 Maintenance selon planning
            2. 📊 Surveillance continue
            3. 📋 Mise à jour carnets de bord
            """)

        # Boutons d'action
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📋 Créer Bon de Travail", use_container_width=True):
                st.success("✅ Bon de travail généré!")
        with col2:
            if st.button("📞 Alerter Équipe", use_container_width=True):
                st.success("✅ Équipe notifiée!")
        with col3:
            if st.button("🔒 Consigner Machine", use_container_width=True):
                st.warning("⚠️ Machine consignée!")

if __name__ == "__main__":
    main()
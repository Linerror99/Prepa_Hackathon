"""
Page Historique - Visualisation des pannes et tendances
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# Configuration de la page
st.set_page_config(
    page_title="Historique des Pannes",
    page_icon="📈",
    layout="wide"
)

# URL de l'API Backend
BACKEND_URL = "http://backend:8000"

def get_failure_history(machine_id=None, days=7):
    """Récupère l'historique des pannes"""
    try:
        params = {"days": days}
        if machine_id and machine_id != "Toutes":
            params["machine_id"] = machine_id
            
        response = requests.get(f"{BACKEND_URL}/api/history/failures", params=params)
        if response.status_code == 200:
            return response.json()["failures"]
        return []
    except Exception as e:
        st.error(f"Erreur récupération historique: {e}")
        return []

def get_machines_list():
    """Récupère la liste des machines"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/machines/live")
        if response.status_code == 200:
            data = response.json()
            return list(data["machines"].keys()) if data["machines"] else []
        return []
    except:
        return ["MACHINE_01", "MACHINE_02", "MACHINE_03"]  # Fallback

# Titre principal
st.title("Historique des Pannes")
st.markdown("---")

# Contrôles de filtrage
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    machines = ["Toutes"] + get_machines_list()
    selected_machine = st.selectbox("Machine", machines)

with col2:
    period_options = {
        "1 jour": 1,
        "3 jours": 3,
        "7 jours": 7,
        "15 jours": 15,
        "30 jours": 30
    }
    selected_period = st.selectbox("Période", list(period_options.keys()), index=2)
    days = period_options[selected_period]

with col3:
    if st.button("Actualiser", type="primary"):
        st.rerun()

# Auto-refresh toggle
auto_refresh = st.checkbox("Actualisation auto (30s)")

# Récupération des données
failures = get_failure_history(
    machine_id=selected_machine if selected_machine != "Toutes" else None,
    days=days
)

if not failures:
    st.info(f"Aucune panne enregistrée pour la période sélectionnée ({selected_period})")
else:
    # Conversion en DataFrame
    df = pd.DataFrame(failures)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp', ascending=False)
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Pannes", len(df))
    
    with col2:
        unique_machines = df['machine_id'].nunique()
        st.metric("Machines Affectées", unique_machines)
    
    with col3:
        avg_prob = df['failure_probability'].mean() * 100
        st.metric("Probabilité Moyenne", f"{avg_prob:.1f}%")
    
    with col4:
        most_common = df['failure_type'].mode()[0] if not df['failure_type'].empty else "N/A"
        st.metric("Type Principal", most_common)
    
    st.markdown("---")
    
    # Graphiques
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Pannes par Type")
        failure_counts = df['failure_type'].value_counts()
        
        colors = {
            'TWF': '#FF6B6B',  # Rouge
            'HDF': '#4ECDC4',  # Turquoise
            'PWF': '#45B7D1',  # Bleu
            'OSF': '#FFA07A',  # Orange
            'RNF': '#98D8C8'   # Vert
        }
        
        fig_pie = px.pie(
            values=failure_counts.values, 
            names=failure_counts.index,
            title="Distribution des Types de Pannes",
            color=failure_counts.index,
            color_discrete_map=colors
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("Pannes par Machine")
        machine_counts = df['machine_id'].value_counts()
        
        fig_bar = px.bar(
            x=machine_counts.index, 
            y=machine_counts.values,
            title="Nombre de Pannes par Machine",
            labels={'x': 'Machine', 'y': 'Nombre de Pannes'},
            color=machine_counts.values,
            color_continuous_scale='Reds'
        )
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Timeline des pannes
    st.subheader("Timeline des Pannes")
    
    # Groupe par heure pour l'affichage
    df_hourly = df.set_index('timestamp').resample('H').size().reset_index()
    df_hourly.columns = ['timestamp', 'count']
    
    fig_timeline = px.line(
        df_hourly, 
        x='timestamp', 
        y='count',
        title="Évolution des Pannes dans le Temps",
        labels={'timestamp': 'Temps', 'count': 'Nombre de Pannes'}
    )
    fig_timeline.update_traces(line_color='#FF6B6B', line_width=3)
    fig_timeline.update_layout(
        xaxis_title="Temps",
        yaxis_title="Nombre de Pannes",
        hovermode='x unified'
    )
    st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Tableau détaillé
    st.subheader("Détails des Pannes")
    
    # Formater les données pour l'affichage
    display_df = df.copy()
    display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    display_df['failure_probability'] = (display_df['failure_probability'] * 100).round(1)
    display_df['anomaly_score'] = display_df['anomaly_score'].round(3)
    
    # Renommer les colonnes
    display_df = display_df.rename(columns={
        'timestamp': 'Horodatage',
        'machine_id': 'Machine',
        'failure_type': 'Type de Panne',
        'failure_probability': 'Probabilité (%)',
        'anomaly_score': 'Score Anomalie'
    })
    
    # Affichage avec mise en forme
    st.dataframe(
        display_df[['Horodatage', 'Machine', 'Type de Panne', 'Probabilité (%)', 'Score Anomalie']],
        use_container_width=True,
        height=400
    )
    
    # Export des données
    if st.button("Exporter CSV"):
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="Télécharger CSV",
            data=csv,
            file_name=f"historique_pannes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

# Auto-refresh
if auto_refresh:
    time.sleep(30)
    st.rerun()

# Footer
st.markdown("---")
st.markdown("*Dernière mise à jour: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "*")
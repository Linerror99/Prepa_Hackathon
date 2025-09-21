"""
Page Alertes - Gestion des notifications et alertes
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import time

# Configuration de la page
st.set_page_config(
    page_title="Alertes & Notifications",
    page_icon="🚨",
    layout="wide"
)

# URL de l'API Backend - Adaptation Docker/Local
import os
if os.path.exists("/app"):
    BACKEND_URL = "http://backend:8000"
else:
    BACKEND_URL = "http://localhost:8000"

def get_active_alerts():
    """Récupère les alertes actives"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/alerts/active")
        if response.status_code == 200:
            return response.json()["alerts"]
        return []
    except Exception as e:
        st.error(f"Erreur récupération alertes: {e}")
        return []

def get_all_alerts():
    """Récupère toutes les alertes"""
    try:
        response = requests.get(f"{BACKEND_URL}/data/alerts")
        if response.status_code == 200:
            return response.json()["alerts"]
        return []
    except Exception as e:
        st.error(f"Erreur récupération alertes: {e}")
        return []

# Titre principal
st.title("Alertes & Notifications")
st.markdown("Centre de gestion des alertes et notifications du système")
st.markdown("---")

# Actualisation automatique
auto_refresh = st.sidebar.checkbox("Actualisation automatique (10s)", value=True)

# Récupération des alertes
alerts = get_active_alerts()
all_alerts = get_all_alerts()

# Métriques globales
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_alerts = len(all_alerts)
    st.metric("Total Alertes", total_alerts)

with col2:
    active_alerts = len([a for a in alerts if not a.get('acknowledged', False)])
    st.metric("Alertes Actives", active_alerts)

with col3:
    critical_alerts = len([a for a in alerts if a.get('severity') == 'critical'])
    st.metric("Critiques", critical_alerts)

with col4:
    warning_alerts = len([a for a in alerts if a.get('severity') == 'warning'])
    st.metric("Avertissements", warning_alerts)

st.markdown("---")

# Onglets
tab1, tab2, tab3 = st.tabs(["Alertes Actives", "Historique", "Configuration"])

with tab1:
    st.header("Alertes Actives")
    
    if not alerts:
        st.success("Aucune alerte active ! Système opérationnel.")
    else:
        # Filtres
        col1, col2 = st.columns(2)
        
        with col1:
            severity_filter = st.selectbox(
                "Filtrer par sévérité",
                ["Toutes", "critical", "warning", "info"]
            )
        
        with col2:
            machine_filter = st.selectbox(
                "Filtrer par machine",
                ["Toutes"] + list(set([a.get('machine_id', 'Unknown') for a in alerts]))
            )
        
        # Application des filtres
        filtered_alerts = alerts
        if severity_filter != "Toutes":
            filtered_alerts = [a for a in filtered_alerts if a.get('severity') == severity_filter]
        if machine_filter != "Toutes":
            filtered_alerts = [a for a in filtered_alerts if a.get('machine_id') == machine_filter]
        
        # Affichage des alertes
        for alert in filtered_alerts:
            severity = alert.get('severity', 'info')
            
            # Couleur selon la sévérité
            if severity == 'critical':
                alert_type = "CRITIQUE"
                color = "red"
            elif severity == 'warning':
                alert_type = "AVERTISSEMENT"
                color = "orange"
            else:
                alert_type = "INFO"
                color = "blue"
            
            with st.container():
                st.markdown(f"""
                <div style="border-left: 4px solid {color}; padding: 10px; margin: 10px 0; background-color: rgba(255,255,255,0.1);">
                    <h4>{alert_type} - {alert.get('machine_id', 'Unknown')}</h4>
                    <p><strong>Message:</strong> {alert.get('message', 'Pas de message')}</p>
                    <p><strong>Horodatage:</strong> {alert.get('timestamp', 'Inconnu')}</p>
                    <p><strong>Type:</strong> {alert.get('alert_type', 'Inconnu')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Boutons d'action
                col1, col2, col3 = st.columns([1, 1, 3])
                
                with col1:
                    if st.button(f"Acquitter", key=f"ack_{alert.get('id', 0)}"):
                        st.success(f"Alerte acquittée (simulation)")
                
                with col2:
                    if st.button(f"Détails", key=f"details_{alert.get('id', 0)}"):
                        st.info("Détails de l'alerte (à implémenter)")
                
                st.markdown("---")

with tab2:
    st.header("Historique des Alertes")
    
    if not all_alerts:
        st.info("Aucune alerte dans l'historique")
    else:
        # Période de filtrage
        period_options = {
            "Dernières 24h": 1,
            "Derniers 3 jours": 3,
            "Dernière semaine": 7,
            "Dernier mois": 30
        }
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_period = st.selectbox("Période", list(period_options.keys()))
            days = period_options[selected_period]
        
        with col2:
            export_format = st.selectbox("Format export", ["CSV", "JSON"])
        
        # Conversion en DataFrame pour analyse
        df_alerts = pd.DataFrame(all_alerts)
        
        if not df_alerts.empty:
            # Filtrage par date
            df_alerts['timestamp'] = pd.to_datetime(df_alerts['timestamp'])
            cutoff_date = datetime.now() - timedelta(days=days)
            df_filtered = df_alerts[df_alerts['timestamp'] >= cutoff_date]
            
            # Statistiques
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Alertes période", len(df_filtered))
            
            with col2:
                if not df_filtered.empty:
                    avg_per_day = len(df_filtered) / days
                    st.metric("Moyenne/jour", f"{avg_per_day:.1f}")
                else:
                    st.metric("Moyenne/jour", "0")
            
            with col3:
                if not df_filtered.empty:
                    most_active = df_filtered['machine_id'].mode()[0]
                    st.metric("Machine + active", most_active)
                else:
                    st.metric("Machine + active", "N/A")
            
            # Graphique des alertes par jour
            if not df_filtered.empty:
                daily_counts = df_filtered.set_index('timestamp').resample('D').size()
                
                import plotly.express as px
                fig = px.bar(
                    x=daily_counts.index,
                    y=daily_counts.values,
                    title="Alertes par Jour",
                    labels={'x': 'Date', 'y': 'Nombre d\'alertes'}
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            
            # Tableau détaillé
            st.subheader("Détails des Alertes")
            
            if not df_filtered.empty:
                # Formater pour l'affichage
                display_df = df_filtered.copy()
                display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
                
                # Renommer les colonnes
                display_df = display_df.rename(columns={
                    'timestamp': 'Horodatage',
                    'machine_id': 'Machine',
                    'alert_type': 'Type',
                    'severity': 'Sévérité',
                    'message': 'Message'
                })
                
                st.dataframe(
                    display_df[['Horodatage', 'Machine', 'Type', 'Sévérité', 'Message']],
                    use_container_width=True,
                    height=400
                )
                
                # Export
                if st.button("Exporter les données"):
                    if export_format == "CSV":
                        csv = display_df.to_csv(index=False)
                        st.download_button(
                            label="Télécharger CSV",
                            data=csv,
                            file_name=f"alertes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    else:
                        json_data = display_df.to_json(orient='records', indent=2)
                        st.download_button(
                            label="Télécharger JSON",
                            data=json_data,
                            file_name=f"alertes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )

with tab3:
    st.header("Configuration des Alertes")
    
    st.subheader("Canaux de Notification")
    
    # Configuration des notifications (simulation)
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Email**")
        email_enabled = st.checkbox("Activer notifications email")
        if email_enabled:
            email_address = st.text_input("Adresse email", "admin@company.com")
            email_severity = st.multiselect(
                "Sévérités à notifier",
                ["critical", "warning", "info"],
                default=["critical", "warning"]
            )
    
    with col2:
        st.write("**SMS**")
        sms_enabled = st.checkbox("Activer notifications SMS")
        if sms_enabled:
            phone_number = st.text_input("Numéro de téléphone", "+33123456789")
            sms_severity = st.multiselect(
                "Sévérités à notifier",
                ["critical", "warning", "info"],
                default=["critical"],
                key="sms_severity"
            )
    
    st.markdown("---")
    
    st.subheader("Planification")
    
    col1, col2 = st.columns(2)
    
    with col1:
        quiet_hours = st.checkbox("Heures silencieuses")
        if quiet_hours:
            start_time = st.time_input("Début")
            end_time = st.time_input("Fin")
    
    with col2:
        escalation = st.checkbox("Escalade automatique")
        if escalation:
            escalation_delay = st.number_input("Délai (minutes)", min_value=5, max_value=120, value=30)
            escalation_contact = st.text_input("Contact escalade", "supervisor@company.com")
    
    # Sauvegarde simulation
    if st.button("Sauvegarder Configuration", type="primary"):
        st.success("Configuration sauvegardée (simulation)")
    
    # Test des notifications
    st.markdown("---")
    st.subheader("Test des Notifications")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Test Email"):
            st.info("Email de test envoyé (simulation)")
    
    with col2:
        if st.button("Test SMS"):
            st.info("SMS de test envoyé (simulation)")
    
    with col3:
        if st.button("Test Alerte"):
            st.warning("Alerte de test générée (simulation)")

# Popup d'alerte critique (simulation)
if critical_alerts > 0:
    with st.sidebar:
        st.error(f"{critical_alerts} ALERTE(S) CRITIQUE(S)")
        st.write("Intervention immédiate requise !")

# Auto-refresh
if auto_refresh:
    time.sleep(10)
    st.rerun()

# Footer
st.markdown("---")
st.markdown("*Dernière mise à jour: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "*")
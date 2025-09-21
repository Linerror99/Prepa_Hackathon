"""
Page Configuration des Machines - Gestion et paramétrage
"""

import streamlit as st
import requests
import json
from datetime import datetime
import time

# Configuration de la page
st.set_page_config(
    page_title="Configuration Machines",
    page_icon="⚙️",
    layout="wide"
)

# URL de l'API Backend
BACKEND_URL = "http://backend:8000"

def get_machines_live():
    """Récupère les machines en temps réel"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/machines/live")
        if response.status_code == 200:
            data = response.json()
            return data["machines"] if data["machines"] else {}
        return {}
    except Exception as e:
        st.error(f"Erreur récupération machines: {e}")
        return {}

def get_machine_config(machine_id):
    """Récupère la configuration d'une machine"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/machines/config/{machine_id}")
        if response.status_code == 200:
            return response.json()["config"]
        return {}
    except Exception as e:
        st.error(f"Erreur récupération config: {e}")
        return {}

def save_machine_config(machine_id, config):
    """Sauvegarde la configuration d'une machine"""
    try:
        response = requests.post(f"{BACKEND_URL}/api/machines/config/{machine_id}", json=config)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Erreur sauvegarde: {e}")
        return False

def get_all_configs():
    """Récupère toutes les configurations"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/machines/config")
        if response.status_code == 200:
            return response.json()["configs"]
        return []
    except Exception as e:
        st.error(f"Erreur récupération configs: {e}")
        return []

# Titre principal
st.title("Configuration des Machines")
st.markdown("Gestion et paramétrage des machines IoT")
st.markdown("---")

# Récupération des données
machines_live = get_machines_live()
machine_ids = list(machines_live.keys()) if machines_live else ["MACHINE_01", "MACHINE_02", "MACHINE_03"]

# Onglets
tab1, tab2, tab3 = st.tabs(["Configuration", "Vue d'ensemble", "Statut Machines"])

with tab1:
    st.header("Configuration Individuelle")
    
    # Sélection de machine
    selected_machine = st.selectbox("Sélectionner une machine", machine_ids)
    
    if selected_machine:
        # Récupération de la config actuelle
        current_config = get_machine_config(selected_machine)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Informations Générales")
            
            display_name = st.text_input(
                "Nom d'affichage", 
                value=current_config.get('display_name', selected_machine)
            )
            
            location_details = st.text_area(
                "Localisation détaillée",
                value=current_config.get('location_details', ''),
                height=100
            )
            
            contact_person = st.text_input(
                "Responsable",
                value=current_config.get('contact_person', '')
            )
            
            maintenance_schedule = st.text_input(
                "Planning maintenance",
                value=current_config.get('maintenance_schedule', ''),
                help="Ex: Chaque lundi 8h00"
            )
        
        with col2:
            st.subheader("Paramètres IA")
            
            anomaly_threshold = st.slider(
                "Seuil d'anomalie",
                min_value=0.1,
                max_value=1.0,
                value=current_config.get('anomaly_threshold', 0.5),
                step=0.05,
                help="Seuil au-delà duquel une anomalie est détectée"
            )
            
            st.write(f"**Seuil actuel**: {anomaly_threshold:.2f}")
            
            # Indicateur visuel du seuil
            if anomaly_threshold <= 0.3:
                st.success("Sensibilité élevée (détection précoce)")
            elif anomaly_threshold <= 0.7:
                st.warning("Sensibilité modérée (équilibré)")
            else:
                st.error("Sensibilité faible (alertes critiques uniquement)")
            
            # Paramètres avancés
            with st.expander("Paramètres avancés"):
                custom_settings = current_config.get('custom_settings', {})
                
                enable_email_alerts = st.checkbox(
                    "Alertes par email",
                    value=custom_settings.get('email_alerts', False)
                )
                
                enable_sms_alerts = st.checkbox(
                    "Alertes par SMS",
                    value=custom_settings.get('sms_alerts', False)
                )
                
                auto_shutdown = st.checkbox(
                    "Arrêt automatique en cas de panne critique",
                    value=custom_settings.get('auto_shutdown', False)
                )
                
                custom_settings = {
                    'email_alerts': enable_email_alerts,
                    'sms_alerts': enable_sms_alerts,
                    'auto_shutdown': auto_shutdown
                }
        
        st.markdown("---")
        
        # Boutons d'action
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("Sauvegarder", type="primary"):
                config_data = {
                    'display_name': display_name,
                    'location_details': location_details,
                    'anomaly_threshold': anomaly_threshold,
                    'maintenance_schedule': maintenance_schedule,
                    'contact_person': contact_person,
                    'custom_settings': custom_settings
                }
                
                if save_machine_config(selected_machine, config_data):
                    st.success(f"Configuration sauvegardée pour {selected_machine}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Erreur lors de la sauvegarde")
        
        with col2:
            if st.button("Réinitialiser"):
                st.rerun()
        
        # Prévisualisation de la config
        st.subheader("Prévisualisation Configuration")
        preview_config = {
            'machine_id': selected_machine,
            'display_name': display_name,
            'location_details': location_details,
            'anomaly_threshold': anomaly_threshold,
            'maintenance_schedule': maintenance_schedule,
            'contact_person': contact_person,
            'custom_settings': custom_settings
        }
        st.json(preview_config)

with tab2:
    st.header("Vue d'ensemble des Configurations")
    
    # Récupération de toutes les configs
    all_configs = get_all_configs()
    
    if not all_configs:
        st.info("Aucune configuration trouvée")
    else:
        # Métriques
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Machines configurées", len(all_configs))
        
        with col2:
            avg_threshold = sum(config.get('anomaly_threshold', 0.5) for config in all_configs) / len(all_configs)
            st.metric("Seuil moyen", f"{avg_threshold:.2f}")
        
        with col3:
            with_contact = sum(1 for config in all_configs if config.get('contact_person'))
            st.metric("Avec responsable", with_contact)
        
        with col4:
            with_schedule = sum(1 for config in all_configs if config.get('maintenance_schedule'))
            st.metric("Planning défini", with_schedule)
        
        st.markdown("---")
        
        # Tableau des configurations
        st.subheader("Tableau des Configurations")
        
        for config in all_configs:
            with st.expander(f"{config.get('display_name', config['machine_id'])}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**ID**: {config['machine_id']}")
                    st.write(f"**Localisation**: {config.get('location_details', 'Non définie')}")
                    st.write(f"**Responsable**: {config.get('contact_person', 'Non défini')}")
                
                with col2:
                    st.write(f"**Seuil d'anomalie**: {config.get('anomaly_threshold', 0.5):.2f}")
                    st.write(f"**Planning**: {config.get('maintenance_schedule', 'Non défini')}")
                    st.write(f"**Dernière MAJ**: {config.get('updated_at', 'Inconnue')}")

with tab3:
    st.header("Statut des Machines")
    
    if not machines_live:
        st.warning("Aucune machine détectée en temps réel")
    else:
        # Affichage du statut de chaque machine
        for machine_id, machine_data in machines_live.items():
            with st.expander(f"{machine_id} - Status: {machine_data.get('status', 'Unknown')}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("**Métriques Actuelles**")
                    st.write(f"Température air: {machine_data.get('air_temperature', 'N/A')}°C")
                    st.write(f"Température process: {machine_data.get('process_temperature', 'N/A')}°C")
                    st.write(f"Vitesse rotation: {machine_data.get('rotational_speed', 'N/A')} rpm")
                
                with col2:
                    st.write("**Prédictions**")
                    st.write(f"Probabilité panne: {machine_data.get('predicted_failure_probability', 0)*100:.1f}%")
                    st.write(f"Type de panne: {machine_data.get('failure_type', 'Aucune')}")
                    st.write(f"Produit: {machine_data.get('product_type', 'N/A')}")
                
                with col3:
                    st.write("**Informations**")
                    st.write(f"Dernière lecture: {machine_data.get('timestamp', 'N/A')}")
                    
                    # Indicateur de statut
                    status = machine_data.get('status', 'unknown')
                    if status == 'normal':
                        st.success("Normal")
                    elif status == 'warning':
                        st.warning("Alerte")
                    elif status == 'critical':
                        st.error("Critique")
                    else:
                        st.info("Inconnu")

# Footer
st.markdown("---")
if st.button("Actualiser toute la page"):
    st.rerun()

st.markdown("*Dernière mise à jour: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "*")
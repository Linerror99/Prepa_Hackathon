"""
Page Services - Monitoring et healthcheck des services
"""

import streamlit as st
import requests
import time
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="Monitoring Services",
    page_icon="🔍",
    layout="wide"
)

# URLs des services
BACKEND_URL = "http://backend:8000"
MQTT_BROKER = "mqtt-broker"

def check_backend_health():
    """Vérifie l'état du backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                'status': 'healthy',
                'response_time': response.elapsed.total_seconds() * 1000,
                'details': data
            }
        else:
            return {
                'status': 'unhealthy',
                'response_time': response.elapsed.total_seconds() * 1000,
                'details': {'error': f'Status code: {response.status_code}'}
            }
    except Exception as e:
        return {
            'status': 'down',
            'response_time': None,
            'details': {'error': str(e)}
        }

def check_mqtt_broker():
    """Vérifie l'état du broker MQTT (simulation)"""
    try:
        # En production, utiliser paho-mqtt pour tester la connexion
        # Pour la démo, on simule
        return {
            'status': 'healthy',
            'response_time': 15,
            'details': {
                'broker': MQTT_BROKER,
                'port': 1883,
                'connected_clients': 3,
                'messages_per_second': 12
            }
        }
    except Exception as e:
        return {
            'status': 'down',
            'response_time': None,
            'details': {'error': str(e)}
        }

def check_ai_engine():
    """Vérifie l'état du moteur IA"""
    try:
        response = requests.get(f"{BACKEND_URL}/ai/models/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                'status': 'healthy',
                'response_time': response.elapsed.total_seconds() * 1000,
                'details': data
            }
        else:
            return {
                'status': 'unhealthy',
                'response_time': response.elapsed.total_seconds() * 1000,
                'details': {'error': f'Status code: {response.status_code}'}
            }
    except Exception as e:
        return {
            'status': 'down',
            'response_time': None,
            'details': {'error': str(e)}
        }

def check_database():
    """Vérifie l'état de la base de données"""
    try:
        response = requests.get(f"{BACKEND_URL}/data/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                'status': 'healthy',
                'response_time': response.elapsed.total_seconds() * 1000,
                'details': data
            }
        else:
            return {
                'status': 'unhealthy',
                'response_time': response.elapsed.total_seconds() * 1000,
                'details': {'error': f'Status code: {response.status_code}'}
            }
    except Exception as e:
        return {
            'status': 'down',
            'response_time': None,
            'details': {'error': str(e)}
        }

def get_service_icon_color(status):
    """Retourne l'icône et la couleur selon le statut"""
    if status == 'healthy':
        return "🟢", "green"
    elif status == 'unhealthy':
        return "🟡", "orange"
    else:
        return "🔴", "red"

# Titre principal
st.title("Monitoring des Services")
st.markdown("Surveillance temps réel de l'infrastructure IoT")
st.markdown("---")

# Auto-refresh
auto_refresh = st.sidebar.checkbox("Actualisation auto (5s)", value=True)

# Vérification de tous les services
services_status = {
    'Backend API': check_backend_health(),
    'MQTT Broker': check_mqtt_broker(),
    'Moteur IA': check_ai_engine(),
    'Base de Données': check_database()
}

# Vue d'ensemble
st.header("Vue d'ensemble des Services")

# Calcul de l'état global
healthy_count = sum(1 for s in services_status.values() if s['status'] == 'healthy')
total_services = len(services_status)
overall_health = healthy_count / total_services

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Santé Globale", f"{overall_health*100:.0f}%")

with col2:
    st.metric("Services OK", f"{healthy_count}/{total_services}")

with col3:
    avg_response_time = sum(s['response_time'] for s in services_status.values() if s['response_time']) / len([s for s in services_status.values() if s['response_time']])
    st.metric("Temps réponse moyen", f"{avg_response_time:.0f}ms")

with col4:
    if overall_health == 1.0:
        st.success("Tous opérationnels")
    elif overall_health >= 0.75:
        st.warning("Partiellement dégradé")
    else:
        st.error("Système dégradé")

st.markdown("---")

# Détails par service
st.header("Statut Détaillé des Services")

for service_name, status_info in services_status.items():
    icon, color = get_service_icon_color(status_info['status'])
    
    with st.expander(f"{icon} {service_name} - {status_info['status'].upper()}"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Informations Générales**")
            st.write(f"Statut: {status_info['status']}")
            if status_info['response_time']:
                st.write(f"Temps de réponse: {status_info['response_time']:.0f}ms")
            else:
                st.write("Temps de réponse: N/A")
        
        with col2:
            st.write("**Détails Techniques**")
            if status_info['details']:
                for key, value in status_info['details'].items():
                    if key != 'error':
                        st.write(f"{key}: {value}")
                
                if 'error' in status_info['details']:
                    st.error(f"Erreur: {status_info['details']['error']}")
        
        # Indicateur visuel
        if status_info['status'] == 'healthy':
            st.success("Service opérationnel")
        elif status_info['status'] == 'unhealthy':
            st.warning("Service dégradé")
        else:
            st.error("Service indisponible")
        
        # Actions de maintenance (simulation)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button(f"Redémarrer {service_name}", key=f"restart_{service_name}"):
                st.info(f"Redémarrage de {service_name} (simulation)")
        
        with col2:
            if st.button(f"Logs {service_name}", key=f"logs_{service_name}"):
                st.info(f"Affichage des logs de {service_name} (simulation)")
        
        with col3:
            if st.button(f"Config {service_name}", key=f"config_{service_name}"):
                st.info(f"Configuration de {service_name} (simulation)")

st.markdown("---")

# Actions globales
st.header("Actions Globales")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("Redémarrer Tous", type="primary"):
        st.warning("Redémarrage global initié (simulation)")

with col2:
    if st.button("Export Métriques"):
        st.info("Export des métriques généré (simulation)")

with col3:
    if st.button("Nettoyer Logs"):
        st.info("Nettoyage des logs effectué (simulation)")

with col4:
    if st.button("Maintenance"):
        st.info("Mode maintenance activé (simulation)")

# Auto-refresh
if auto_refresh:
    time.sleep(5)
    st.rerun()

# Footer
st.markdown("---")
st.markdown("*Dernière mise à jour: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "*")
"""
🏭 Dashboard IoT Industriel - Navigation Principale
Version simplifiée pour les tests
"""

import streamlit as st

# Configuration globale
BACKEND_URL = "http://localhost:8000"

# Configuration de la page
st.set_page_config(
    page_title="🏭 Smart Factory Dashboard",
    page_icon="🏭", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar avec navigation
with st.sidebar:
    st.title("🏭 Smart Factory")
    st.markdown("---")
    
    # Test de connexion au backend
    try:
        import requests
        response = requests.get(f"{BACKEND_URL}/", timeout=2)
        if response.status_code == 200:
            st.success("✅ Backend connecté")
        else:
            st.error("❌ Backend erreur")
    except:
        st.error("❌ Backend déconnecté")
        st.info("💡 Mode Docker: backend:8000")
    
    st.markdown("### 📊 Navigation")
    
    # Navigation avec pages propres
    st.page_link("pages/historique.py", label="📈 Historique des Pannes", icon="📈")
    st.page_link("pages/configuration.py", label="⚙️ Configuration", icon="⚙️")
    st.page_link("pages/alertes.py", label="🚨 Alertes Actives", icon="🚨")
    st.page_link("pages/services.py", label="🔧 Services", icon="🔧")
    
    st.markdown("---")
    st.markdown("### 🏭 Mode Usine")
    st.info("🔧 Interface simplifiée en développement")

# Page d'accueil principale
st.title("🏭 Dashboard IoT Factory")
st.markdown("### Surveillance Prédictive en Temps Réel")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🤖 Machines", "5", "0")

with col2:
    st.metric("⚠️ Alertes", "2", "+1")

with col3:
    st.metric("🔧 Maintenance", "85%", "+5%")

with col4:
    st.metric("📊 Uptime", "99.2%", "+0.1%")

st.markdown("---")

# Vue d'ensemble
st.subheader("📊 Vue d'ensemble du système")

tab1, tab2, tab3 = st.tabs(["🏭 Machines", "📈 Performances", "🚨 Alertes"])

with tab1:
    st.write("**État des machines:**")
    machines_data = {
        "Machine": ["CNC-001", "CNC-002", "CNC-003", "CNC-004", "CNC-005"],
        "État": ["🟢 OK", "🟡 Attention", "🟢 OK", "🔴 Critique", "🟢 OK"],
        "Probabilité Panne": ["5%", "45%", "8%", "85%", "12%"]
    }
    st.table(machines_data)

with tab2:
    st.write("**Graphiques de performance en cours de développement...**")
    st.info("📈 Connectez-vous aux pages spécialisées pour voir les graphiques détaillés")

with tab3:
    st.write("**Alertes actives:**")
    st.error("🚨 CNC-004: Température élevée détectée")
    st.warning("⚠️ CNC-002: Usure d'outil proche du seuil")

st.markdown("---")
st.markdown("### 🔗 Navigation")
st.write("Utilisez la barre latérale pour accéder aux différentes sections :")
st.markdown("""
- **📈 Historique**: Analyse des pannes passées et tendances
- **⚙️ Configuration**: Paramètres des machines et seuils
- **🚨 Alertes**: Surveillance en temps réel des alertes
- **🔧 Services**: État des services et diagnostics
""")
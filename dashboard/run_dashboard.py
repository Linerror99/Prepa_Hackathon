"""
🚀 Lanceur pour le Dashboard Streamlit
Usage: python run_dashboard.py
"""

import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """Installe les dépendances si nécessaires"""
    try:
        import streamlit
        import plotly
        print("✅ Dépendances déjà installées")
    except ImportError:
        print("📦 Installation des dépendances...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dépendances installées")

def run_dashboard():
    """Lance le dashboard Streamlit"""
    print("🏭 Démarrage du Dashboard Smart Factory...")
    
    # S'assurer qu'on est dans le bon répertoire
    dashboard_dir = Path(__file__).parent
    os.chdir(dashboard_dir)
    
    # Installer les dépendances
    install_requirements()
    
    # Lancer Streamlit
    cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.port", "8501",
        "--server.address", "localhost",
        "--browser.gatherUsageStats", "false"
    ]
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n🛑 Dashboard arrêté")

if __name__ == "__main__":
    run_dashboard()
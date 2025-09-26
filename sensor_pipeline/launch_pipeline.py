#!/usr/bin/env python3
"""
Script de lancement du pipeline capteurs industriels
Orchestre les différents composants du système
"""

import asyncio
import logging
import sys
import subprocess
import signal
import os
from pathlib import Path

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PipelineLauncher:
    """
    Lanceur orchestrant tous les composants du pipeline
    """
    
    def __init__(self):
        self.processes = {}
        self.running = False
        
        # Chemins des scripts
        self.base_path = Path(__file__).parent
        self.scripts = {
            "aggregator": self.base_path / "sensor_aggregator.py",
            "simulator": self.base_path / "real_sensor_simulator.py",
            "test": self.base_path / "test_pipeline.py"
        }
    
    def check_dependencies(self):
        """Vérifie que tous les fichiers nécessaires existent"""
        logger.info("🔍 Vérification des dépendances...")
        
        missing_files = []
        for name, path in self.scripts.items():
            if not path.exists():
                missing_files.append(f"{name}: {path}")
        
        if missing_files:
            logger.error("❌ Fichiers manquants:")
            for file in missing_files:
                logger.error(f"   {file}")
            return False
        
        logger.info("✅ Tous les fichiers sont présents")
        return True
    
    def start_component(self, name: str, script_path: Path, wait_time: int = 2):
        """Démarre un composant du pipeline"""
        try:
            logger.info(f"🚀 Démarrage {name}...")
            
            # Utiliser python depuis l'environnement courant
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.processes[name] = process
            logger.info(f"✅ {name} démarré (PID: {process.pid})")
            
            # Attendre un peu pour laisser le composant s'initialiser
            if wait_time > 0:
                logger.info(f"⏱️ Attente {wait_time}s pour initialisation...")
                asyncio.sleep(wait_time)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur démarrage {name}: {e}")
            return False
    
    def stop_all(self):
        """Arrête tous les composants"""
        logger.info("🛑 Arrêt de tous les composants...")
        
        for name, process in self.processes.items():
            try:
                if process and process.poll() is None:
                    logger.info(f"⏹️ Arrêt {name}...")
                    process.terminate()
                    
                    # Attendre l'arrêt gracieux
                    try:
                        process.wait(timeout=5)
                        logger.info(f"✅ {name} arrêté")
                    except subprocess.TimeoutExpired:
                        logger.warning(f"⚠️ Force kill {name}...")
                        process.kill()
                        
            except Exception as e:
                logger.error(f"❌ Erreur arrêt {name}: {e}")
        
        self.processes.clear()
        self.running = False
    
    def check_component_status(self):
        """Vérifie l'état des composants"""
        logger.info("📊 État des composants:")
        
        all_running = True
        for name, process in self.processes.items():
            if process.poll() is None:
                logger.info(f"   ✅ {name}: En cours (PID: {process.pid})")
            else:
                logger.warning(f"   ❌ {name}: Arrêté (code: {process.returncode})")
                all_running = False
        
        return all_running
    
    async def monitor_components(self):
        """Surveille les composants en continu"""
        logger.info("👁️ Démarrage monitoring continu...")
        
        while self.running:
            await asyncio.sleep(30)  # Vérifier toutes les 30 secondes
            
            if not self.check_component_status():
                logger.warning("⚠️ Certains composants sont arrêtés")
    
    def signal_handler(self, signum, frame):
        """Gestionnaire de signaux pour arrêt propre"""
        logger.info(f"📢 Signal reçu: {signum}")
        self.running = False
        self.stop_all()
        sys.exit(0)

async def run_full_pipeline():
    """Lance le pipeline complet"""
    launcher = PipelineLauncher()
    
    # Configuration des gestionnaires de signaux
    signal.signal(signal.SIGINT, launcher.signal_handler)
    signal.signal(signal.SIGTERM, launcher.signal_handler)
    
    try:
        # Vérifier les dépendances
        if not launcher.check_dependencies():
            return
        
        logger.info("🌟 LANCEMENT PIPELINE CAPTEURS INDUSTRIELS")
        logger.info("=" * 60)
        
        # 1. Démarrer l'agrégateur de capteurs
        if not launcher.start_component("aggregator", launcher.scripts["aggregator"], wait_time=3):
            logger.error("❌ Impossible de démarrer l'agrégateur")
            return
        
        # 2. Démarrer le simulateur de capteurs (optionnel)
        simulator_choice = input("Démarrer le simulateur de capteurs? (y/N): ").lower().strip()
        if simulator_choice in ['y', 'yes', 'o', 'oui']:
            if not launcher.start_component("simulator", launcher.scripts["simulator"], wait_time=2):
                logger.warning("⚠️ Impossible de démarrer le simulateur (continuer sans)")
        
        # 3. Option de test
        test_choice = input("Lancer les tests de validation? (y/N): ").lower().strip()
        if test_choice in ['y', 'yes', 'o', 'oui']:
            logger.info("🧪 Exécution des tests...")
            test_process = subprocess.run([sys.executable, str(launcher.scripts["test"])], 
                                       capture_output=True, text=True)
            if test_process.returncode == 0:
                logger.info("✅ Tests réussis")
            else:
                logger.error(f"❌ Tests échoués: {test_process.stderr}")
        
        launcher.running = True
        
        # Monitoring continu
        logger.info("\n🎯 PIPELINE OPÉRATIONNEL")
        logger.info("   - Agrégateur actif")
        if "simulator" in launcher.processes:
            logger.info("   - Simulateur actif")
        logger.info("   - Appuyez sur Ctrl+C pour arrêter")
        
        # Boucle de monitoring
        await launcher.monitor_components()
        
    except KeyboardInterrupt:
        logger.info("👋 Arrêt demandé par l'utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
    finally:
        launcher.stop_all()

def print_usage():
    """Affiche les instructions d'utilisation"""
    print("""
🏭 PIPELINE CAPTEURS INDUSTRIELS
================================

Ce script lance et orchestre le pipeline de capteurs:

1. sensor_aggregator.py - Agrège les données capteurs MQTT
2. real_sensor_simulator.py - Simule des capteurs industriels (optionnel)  
3. test_pipeline.py - Tests de validation (optionnel)

PRÉREQUIS:
- Broker MQTT en cours (port 1883)
- Backend FastAPI en cours (port 8000)
- Dépendances Python installées

UTILISATION:
python launch_pipeline.py

Le script vous proposera d'activer les composants optionnels.
    """)

if __name__ == "__main__":
    print_usage()
    
    try:
        asyncio.run(run_full_pipeline())
    except KeyboardInterrupt:
        logger.info("👋 Au revoir!")
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        sys.exit(1)
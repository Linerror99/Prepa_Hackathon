#!/usr/bin/env python3
"""
Script d'entraînement automatique ML au démarrage du container
Vérifie si les modèles ML existent, sinon les entraîne automatiquement
"""

import os
import sys
import logging
from pathlib import Path
import time
import subprocess

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - startup_ml - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_ml_models_exist():
    """Vérifie si les artefacts ML existent déjà"""
    ml_models_dir = Path("/app/ml/models")
    
    required_files = [
        "ts_forecast.joblib",
        "scaler.joblib", 
        "anomaly_detector.joblib",
        "meta.json"
    ]
    
    if not ml_models_dir.exists():
        logger.info("📁 Répertoire ml/models n'existe pas")
        return False
    
    missing_files = []
    for file_name in required_files:
        file_path = ml_models_dir / file_name
        if not file_path.exists():
            missing_files.append(file_name)
    
    if missing_files:
        logger.warning(f"⚠️ Fichiers manquants: {missing_files}")
        return False
    
    logger.info("✅ Tous les artefacts ML sont présents")
    return True

def run_ml_training():
    """Lance l'entraînement ML"""
    try:
        logger.info("🚀 Démarrage de l'entraînement ML...")
        
        # Créer le répertoire models s'il n'existe pas
        ml_models_dir = Path("/app/ml/models")
        ml_models_dir.mkdir(parents=True, exist_ok=True)
        
        # Lancer l'entraînement rapide pour container
        result = subprocess.run([
            sys.executable, "/app/ml/train_fast_container.py"
        ], 
        cwd="/app",
        capture_output=True, 
        text=True,
        timeout=60  # 1 minute max pour 500 échantillons
        )
        
        if result.returncode == 0:
            logger.info("✅ Entraînement ML terminé avec succès")
            logger.info("📊 Output d'entraînement:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    logger.info(f"    {line}")
            return True
        else:
            logger.error("❌ Échec de l'entraînement ML")
            logger.error(f"Return code: {result.returncode}")
            logger.error(f"STDERR: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("⏰ Timeout lors de l'entraînement ML (>5min)")
        return False
    except Exception as e:
        logger.error(f"💥 Erreur lors de l'entraînement: {e}")
        return False

def ensure_ml_ready():
    """S'assure que le ML est prêt avant de démarrer l'application"""
    logger.info("🔍 Vérification des modèles ML...")
    
    if check_ml_models_exist():
        logger.info("🎯 Modèles ML déjà disponibles")
        return True
    
    logger.info("📚 Modèles ML manquants, entraînement nécessaire")
    
    # Vérifier que le dataset est présent
    dataset_path = Path("/app/ml/iot_data_synthetic.csv")
    if not dataset_path.exists():
        logger.error(f"❌ Dataset manquant: {dataset_path}")
        return False
    
    # Vérifier que le script d'entraînement existe
    fast_train_script = Path("/app/ml/train_fast_container.py")
    full_train_script = Path("/app/ml/train_optimized_forecast.py")
    
    if not fast_train_script.exists() and not full_train_script.exists():
        logger.error("❌ Aucun script d'entraînement trouvé")
        return False
    
    # Lancer l'entraînement
    success = run_ml_training()
    
    if success:
        # Revérifier que les modèles ont bien été créés
        if check_ml_models_exist():
            logger.info("🎉 ML prêt pour la production!")
            return True
        else:
            logger.error("❌ Entraînement réussi mais modèles introuvables")
            return False
    else:
        logger.warning("⚠️ Entraînement échoué, fallback vers simulation")
        return False

if __name__ == "__main__":
    logger.info("🚀 === Initialisation ML Container ===")
    
    # Attendre un peu que le container soit complètement démarré
    time.sleep(2)
    
    try:
        ml_ready = ensure_ml_ready()
        
        if ml_ready:
            logger.info("✅ === ML Container prêt ===")
            sys.exit(0)
        else:
            logger.warning("⚠️ === ML Container en mode fallback ===")
            # Ne pas échouer le container, juste logger l'avertissement
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"💥 Erreur critique dans startup ML: {e}")
        sys.exit(0)  # Permettre au container de démarrer quand même
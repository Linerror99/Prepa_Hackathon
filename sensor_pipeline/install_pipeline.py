#!/usr/bin/env python3
"""
Script d'installation et configuration du pipeline capteurs
Prépare l'environnement et installe les dépendances
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PipelineInstaller:
    """
    Installateur pour le pipeline de capteurs industriels
    """
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.requirements_file = self.base_path / "requirements.txt"
    
    def check_python_version(self):
        """Vérifie la version Python"""
        logger.info("🐍 Vérification version Python...")
        
        if sys.version_info < (3, 8):
            logger.error("❌ Python 3.8+ requis")
            logger.error(f"   Version actuelle: {sys.version}")
            return False
        
        logger.info(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        return True
    
    def install_dependencies(self):
        """Installe les dépendances Python"""
        logger.info("📦 Installation des dépendances...")
        
        if not self.requirements_file.exists():
            logger.error(f"❌ Fichier requirements.txt introuvable: {self.requirements_file}")
            return False
        
        try:
            # Installer les dépendances
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(self.requirements_file)
            ], capture_output=True, text=True, check=True)
            
            logger.info("✅ Dépendances installées avec succès")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error("❌ Erreur installation dépendances:")
            logger.error(f"   {e.stderr}")
            return False
    
    def test_imports(self):
        """Teste l'importation des modules critiques"""
        logger.info("🧪 Test des imports...")
        
        test_modules = [
            "paho.mqtt.client",
            "json",
            "asyncio", 
            "logging",
            "datetime"
        ]
        
        failed_imports = []
        
        for module in test_modules:
            try:
                __import__(module)
                logger.info(f"   ✅ {module}")
            except ImportError as e:
                logger.error(f"   ❌ {module}: {e}")
                failed_imports.append(module)
        
        if failed_imports:
            logger.error(f"❌ Modules manquants: {failed_imports}")
            return False
        
        logger.info("✅ Tous les modules sont disponibles")
        return True
    
    def check_mqtt_broker(self):
        """Vérifie la disponibilité du broker MQTT"""
        logger.info("📡 Vérification broker MQTT...")
        
        try:
            import paho.mqtt.client as mqtt
            import time
            
            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    logger.info("✅ Broker MQTT accessible")
                    client.disconnect()
                else:
                    logger.warning(f"⚠️ Connexion MQTT échouée: {rc}")
            
            client = mqtt.Client(client_id="installer_test")
            client.on_connect = on_connect
            
            # Tenter la connexion
            client.connect("localhost", 1883, 10)
            client.loop_start()
            time.sleep(2)
            client.loop_stop()
            
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Impossible de tester MQTT: {e}")
            logger.info("   Assurez-vous que le broker MQTT est démarré")
            return False
    
    def create_docker_compose_addition(self):
        """Crée un fichier docker-compose pour le pipeline"""
        logger.info("🐳 Création configuration Docker...")
        
        docker_compose_content = """# Ajout au docker-compose.yml principal
# Pipeline capteurs industriels

  sensor-aggregator:
    build: 
      context: ./sensor_pipeline
      dockerfile: Dockerfile
    container_name: sensor_aggregator
    depends_on:
      - mosquitto
      - backend
    networks:
      - iot_network
    volumes:
      - ./sensor_pipeline:/app
    environment:
      - MQTT_HOST=mosquitto
      - BACKEND_HOST=backend
    restart: unless-stopped
    
  # Service optionnel pour simulateur
  sensor-simulator:
    build: 
      context: ./sensor_pipeline
      dockerfile: Dockerfile
    container_name: sensor_simulator  
    depends_on:
      - mosquitto
    networks:
      - iot_network
    volumes:
      - ./sensor_pipeline:/app
    environment:
      - MQTT_HOST=mosquitto
    restart: unless-stopped
    command: python real_sensor_simulator.py
"""
        
        docker_file = self.base_path / "docker-compose.pipeline.yml"
        
        try:
            with open(docker_file, 'w', encoding='utf-8') as f:
                f.write(docker_compose_content)
            
            logger.info(f"✅ Configuration Docker créée: {docker_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur création Docker config: {e}")
            return False
    
    def create_dockerfile(self):
        """Crée le Dockerfile pour le pipeline"""
        logger.info("📋 Création Dockerfile...")
        
        dockerfile_content = """FROM python:3.9-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier les scripts
COPY . .

# Commande par défaut
CMD ["python", "sensor_aggregator.py"]
"""
        
        dockerfile = self.base_path / "Dockerfile"
        
        try:
            with open(dockerfile, 'w', encoding='utf-8') as f:
                f.write(dockerfile_content)
            
            logger.info(f"✅ Dockerfile créé: {dockerfile}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur création Dockerfile: {e}")
            return False
    
    def run_installation(self):
        """Exécute l'installation complète"""
        logger.info("🚀 INSTALLATION PIPELINE CAPTEURS INDUSTRIELS")
        logger.info("=" * 60)
        
        success = True
        
        # 1. Vérifier Python
        if not self.check_python_version():
            success = False
        
        # 2. Installer dépendances
        if success and not self.install_dependencies():
            success = False
        
        # 3. Tester imports
        if success and not self.test_imports():
            success = False
        
        # 4. Vérifier MQTT (optionnel)
        self.check_mqtt_broker()
        
        # 5. Créer configurations Docker
        if success:
            self.create_dockerfile()
            self.create_docker_compose_addition()
        
        # Résultat final
        logger.info("=" * 60)
        if success:
            logger.info("✅ INSTALLATION RÉUSSIE")
            logger.info("\nPROCHAINES ÉTAPES:")
            logger.info("1. Démarrer le broker MQTT si nécessaire")
            logger.info("2. Lancer: python launch_pipeline.py")
            logger.info("3. Ou utiliser Docker: docker-compose up")
        else:
            logger.error("❌ INSTALLATION ÉCHOUÉE")
            logger.error("Vérifiez les erreurs ci-dessus")
        
        return success

def main():
    """Fonction principale"""
    installer = PipelineInstaller()
    
    try:
        success = installer.run_installation()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("👋 Installation interrompue")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
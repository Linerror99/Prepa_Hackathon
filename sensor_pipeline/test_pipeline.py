#!/usr/bin/env python3
"""
Test du pipeline de capteurs industriels
Valide l'agrégation et le traitement des données
"""

import asyncio
import json
import logging
import sys
import paho.mqtt.client as mqtt
from datetime import datetime
import time

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PipelineTestMonitor:
    """
    Moniteur de test pour valider le pipeline capteurs
    Écoute les données agrégées et vérifie la qualité
    """
    
    def __init__(self, mqtt_host="localhost", mqtt_port=1883):
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        
        # Compteurs de test
        self.received_individual = {"temperature": 0, "pressure": 0, "velocity": 0}
        self.received_aggregated = 0
        self.test_start_time = None
        
        # Client MQTT pour monitoring
        self.mqtt_client = mqtt.Client(client_id="pipeline_test_monitor")
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback connexion MQTT"""
        if rc == 0:
            logger.info("✅ Moniteur de test connecté au broker MQTT")
            
            # S'abonner aux topics de capteurs individuels
            client.subscribe("sensors/+/temperature")
            client.subscribe("sensors/+/pressure") 
            client.subscribe("sensors/+/velocity")
            
            # S'abonner aux topics agrégés
            client.subscribe("iot/sensors/+")
            
            logger.info("📡 Abonnement aux topics de test activé")
        else:
            logger.error(f"❌ Échec connexion MQTT moniteur: {rc}")
    
    def on_message(self, client, userdata, msg):
        """Traite les messages reçus"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            if topic.startswith("sensors/"):
                # Message capteur individuel
                self.handle_individual_sensor(topic, payload)
            elif topic.startswith("iot/sensors/"):
                # Message agrégé
                self.handle_aggregated_data(topic, payload)
                
        except Exception as e:
            logger.error(f"❌ Erreur traitement message {topic}: {e}")
    
    def handle_individual_sensor(self, topic, payload):
        """Traite les messages de capteurs individuels"""
        parts = topic.split("/")
        if len(parts) >= 3:
            machine_id = parts[1]
            sensor_type = parts[2]
            
            if sensor_type in self.received_individual:
                self.received_individual[sensor_type] += 1
                
            logger.info(f"🔧 Capteur individuel: {machine_id}/{sensor_type} = {payload.get('value', 'N/A')}")
    
    def handle_aggregated_data(self, topic, payload):
        """Traite les données agrégées"""
        parts = topic.split("/")
        if len(parts) >= 3:
            machine_id = parts[2]
            self.received_aggregated += 1
            
            # Vérifier la structure des données agrégées
            required_fields = ["temperature", "pressure", "velocity", "timestamp", "machine_id"]
            missing_fields = [field for field in required_fields if field not in payload]
            
            if missing_fields:
                logger.error(f"❌ Données agrégées incomplètes pour {machine_id}: manque {missing_fields}")
            else:
                logger.info(f"✅ Données agrégées complètes pour {machine_id}:")
                logger.info(f"   T={payload['temperature']:.1f}°C, P={payload['pressure']:.1f}bar, V={payload['velocity']:.1f}m/s")
    
    def start_monitoring(self):
        """Démarre le monitoring"""
        logger.info("🔍 Démarrage monitoring pipeline...")
        self.test_start_time = datetime.now()
        
        self.mqtt_client.connect(self.mqtt_host, self.mqtt_port, 60)
        self.mqtt_client.loop_start()
    
    def print_statistics(self):
        """Affiche les statistiques de test"""
        if self.test_start_time:
            elapsed = datetime.now() - self.test_start_time
            logger.info(f"\n📊 STATISTIQUES DE TEST ({elapsed.total_seconds():.0f}s)")
            logger.info(f"   Capteurs individuels reçus:")
            for sensor_type, count in self.received_individual.items():
                logger.info(f"     {sensor_type}: {count} messages")
            logger.info(f"   Données agrégées: {self.received_aggregated} messages")
            
            # Calculer le taux d'agrégation
            total_individual = sum(self.received_individual.values())
            if total_individual > 0:
                aggregation_rate = (self.received_aggregated / (total_individual / 3)) * 100
                logger.info(f"   Taux d'agrégation: {aggregation_rate:.1f}%")
    
    def stop(self):
        """Arrête le monitoring"""
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()

async def send_test_sensor_data(mqtt_host="localhost", mqtt_port=1883):
    """Envoie des données de test pour valider le pipeline"""
    logger.info("🧪 Envoi de données de test...")
    
    client = mqtt.Client(client_id="test_data_sender")
    client.connect(mqtt_host, mqtt_port, 60)
    
    # Données de test synchronisées
    timestamp = datetime.now().isoformat() + "Z"
    machine_id = "TEST_MACHINE"
    
    test_data = [
        {"type": "temperature", "value": 28.5, "unit": "°C"},
        {"type": "pressure", "value": 3.2, "unit": "bar"}, 
        {"type": "velocity", "value": 1.8, "unit": "m/s"}
    ]
    
    # Envoyer les données avec un délai léger pour simuler le timing réel
    for data in test_data:
        topic = f"sensors/{machine_id}/{data['type']}"
        payload = {
            "timestamp": timestamp,
            "value": data["value"],
            "unit": data["unit"],
            "machine_id": machine_id,
            "sensor_type": data["type"]
        }
        
        client.publish(topic, json.dumps(payload), qos=1)
        logger.info(f"📤 Test envoyé: {topic} = {data['value']}")
        await asyncio.sleep(0.2)  # 200ms entre capteurs
    
    client.disconnect()
    logger.info("✅ Données de test envoyées")

async def run_pipeline_test():
    """Exécute le test complet du pipeline"""
    logger.info("🚀 DÉMARRAGE TEST PIPELINE CAPTEURS INDUSTRIELS")
    
    # Démarrer le monitoring
    monitor = PipelineTestMonitor()
    monitor.start_monitoring()
    
    # Attendre que la connexion soit établie
    await asyncio.sleep(2)
    
    try:
        # Envoyer des données de test
        await send_test_sensor_data()
        
        # Attendre et observer
        logger.info("⏱️ Observation du pipeline pendant 30 secondes...")
        for i in range(30):
            await asyncio.sleep(1)
            if (i + 1) % 10 == 0:
                monitor.print_statistics()
        
        # Test avec données multiples
        logger.info("🔄 Test avec données multiples...")
        for j in range(3):
            await send_test_sensor_data()
            await asyncio.sleep(2)
        
        # Attendre l'agrégation finale
        await asyncio.sleep(5)
        
    except Exception as e:
        logger.error(f"❌ Erreur durant le test: {e}")
    
    finally:
        monitor.print_statistics()
        monitor.stop()
        logger.info("🏁 Test pipeline terminé")

if __name__ == "__main__":
    print("=" * 60)
    print("        TEST PIPELINE CAPTEURS INDUSTRIELS")
    print("=" * 60)
    
    try:
        asyncio.run(run_pipeline_test())
    except KeyboardInterrupt:
        logger.info("👋 Test interrompu par l'utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur fatale test: {e}")
        sys.exit(1)
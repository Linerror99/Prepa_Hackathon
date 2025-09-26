#!/usr/bin/env python3
"""
Simulateur de capteurs IoT industriels réels
Envoie des données séparées pour chaque capteur via MQTT
"""

import asyncio
import json
import logging
import random
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
from typing import Dict, List
import time

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealSensorSimulator:
    """
    Simulateur de capteurs industriels réels
    Envoie des données séparées pour température, pression, vitesse
    """
    
    def __init__(self, mqtt_host="localhost", mqtt_port=1883):
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        
        # Configuration des machines
        self.machines = [
            {"id": "MACHINE_01", "type": "TypeA"},
            {"id": "MACHINE_02", "type": "TypeB"}, 
            {"id": "MACHINE_03", "type": "TypeC"}
        ]
        
        # Configuration des capteurs avec plages réalistes
        self.sensor_configs = {
            "temperature": {
                "normal_range": (25.0, 35.0),
                "alert_range": (35.0, 60.0),
                "critical_range": (60.0, 80.0),
                "unit": "°C"
            },
            "pressure": {
                "normal_range": (2.5, 4.0),
                "alert_range": (4.0, 8.0), 
                "critical_range": (8.0, 12.0),
                "unit": "bar"
            },
            "velocity": {
                "normal_range": (1.0, 2.0),
                "alert_range": (2.0, 4.0),
                "critical_range": (4.0, 6.0),
                "unit": "m/s"
            }
        }
        
        # États des machines (pour simulation d'anomalies)
        self.machine_states = {}
        for machine in self.machines:
            self.machine_states[machine["id"]] = {
                "status": "normal",  # normal, alert, critical
                "base_values": {
                    "temperature": random.uniform(25.0, 35.0),
                    "pressure": random.uniform(2.5, 4.0),
                    "velocity": random.uniform(1.0, 2.0)
                },
                "last_change": datetime.now()
            }
        
        # Client MQTT
        self.mqtt_client = mqtt.Client(client_id="real_sensor_simulator")
        self.mqtt_client.on_connect = self.on_connect
        
        self.running = False
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback connexion MQTT"""
        if rc == 0:
            logger.info("✅ Simulateur capteurs connecté au broker MQTT")
        else:
            logger.error(f"❌ Échec connexion MQTT: {rc}")
    
    async def start(self):
        """Démarre la simulation des capteurs"""
        try:
            logger.info("🚀 Démarrage simulateur capteurs industriels réels...")
            
            # Connexion MQTT
            self.mqtt_client.connect(self.mqtt_host, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            
            self.running = True
            
            # Boucle principale - intervalle configurable via SENSOR_INTERVAL_SECONDS
            import os
            interval_seconds = int(os.getenv('SENSOR_INTERVAL_SECONDS', '300'))  # 5 minutes par défaut
            interval_minutes = interval_seconds / 60
            
            logger.info(f"📊 Intervalle d'envoi configuré: {interval_seconds}s ({interval_minutes:.1f}min)")
            
            while self.running:
                await self.send_sensor_batch()
                
                # Attendre l'intervalle configuré
                if interval_seconds >= 60:
                    logger.info(f"⏱️ Attente {interval_minutes:.1f} minutes avant prochain envoi...")
                else:
                    logger.info(f"⏱️ Attente {interval_seconds}s avant prochain envoi...")
                await asyncio.sleep(interval_seconds)
                
        except Exception as e:
            logger.error(f"❌ Erreur simulateur: {e}")
            raise
    
    async def send_sensor_batch(self):
        """Envoie un batch de données pour tous les capteurs de toutes les machines"""
        current_time = datetime.now().isoformat() + "Z"
        
        logger.info(f"📡 Envoi batch capteurs à {current_time}")
        
        for machine in self.machines:
            machine_id = machine["id"]
            
            # Mettre à jour l'état de la machine aléatoirement
            self.update_machine_state(machine_id)
            
            # Générer les valeurs pour les 3 capteurs
            sensor_values = self.generate_sensor_values(machine_id)
            
            # Envoyer chaque capteur séparément avec un léger délai
            for sensor_type, value in sensor_values.items():
                await self.send_individual_sensor(machine_id, sensor_type, value, current_time)
                
                # Petit délai entre capteurs pour simuler le timing réel
                await asyncio.sleep(0.1)
            
            logger.info(f"✅ {machine_id}: T={sensor_values['temperature']:.1f}°C, P={sensor_values['pressure']:.1f}bar, V={sensor_values['velocity']:.1f}m/s")
    
    def update_machine_state(self, machine_id: str):
        """Met à jour l'état d'une machine aléatoirement"""
        machine_state = self.machine_states[machine_id]
        
        # Changer d'état parfois (10% de chance)
        if random.random() < 0.1:
            # 70% normal, 20% alert, 10% critical
            rand = random.random()
            if rand < 0.7:
                machine_state["status"] = "normal"
            elif rand < 0.9:
                machine_state["status"] = "alert"
            else:
                machine_state["status"] = "critical"
            
            machine_state["last_change"] = datetime.now()
            logger.info(f"🔄 {machine_id} changement d'état: {machine_state['status']}")
    
    def generate_sensor_values(self, machine_id: str) -> Dict[str, float]:
        """Génère les valeurs des capteurs selon l'état de la machine"""
        machine_state = self.machine_states[machine_id]
        status = machine_state["status"]
        base_values = machine_state["base_values"]
        
        values = {}
        
        for sensor_type, config in self.sensor_configs.items():
            base_value = base_values[sensor_type]
            
            if status == "normal":
                # Variation normale autour de la valeur de base
                noise = random.uniform(-0.1, 0.1) * base_value
                values[sensor_type] = max(0, base_value + noise)
                
            elif status == "alert":
                # Valeurs dans la plage d'alerte
                min_val, max_val = config["alert_range"]
                values[sensor_type] = random.uniform(min_val, max_val)
                
            else:  # critical
                # Valeurs dans la plage critique
                min_val, max_val = config["critical_range"]
                values[sensor_type] = random.uniform(min_val, max_val)
        
        # Mettre à jour les valeurs de base pour continuité
        for sensor_type in values:
            machine_state["base_values"][sensor_type] = values[sensor_type]
        
        return values
    
    async def send_individual_sensor(self, machine_id: str, sensor_type: str, value: float, timestamp: str):
        """Envoie une valeur de capteur individuel"""
        topic = f"sensors/{machine_id}/{sensor_type}"
        
        payload = {
            "timestamp": timestamp,
            "value": round(value, 2),
            "unit": self.sensor_configs[sensor_type]["unit"],
            "machine_id": machine_id,
            "sensor_type": sensor_type
        }
        
        try:
            result = self.mqtt_client.publish(topic, json.dumps(payload), qos=1)
            if result.rc != 0:
                logger.error(f"❌ Échec envoi {topic}")
            else:
                logger.debug(f"📊 Envoyé: {topic} = {value:.2f}")
                
        except Exception as e:
            logger.error(f"❌ Erreur envoi capteur {topic}: {e}")
    
    def stop(self):
        """Arrête le simulateur"""
        logger.info("🛑 Arrêt simulateur capteurs...")
        self.running = False
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()

async def main():
    """Fonction principale"""
    import os
    
    # Configuration depuis variables d'environnement Docker
    mqtt_host = os.getenv("MQTT_HOST", "localhost")
    mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
    
    logger.info("🚀 DÉMARRAGE SIMULATEUR CAPTEURS INDUSTRIELS RÉELS")
    logger.info("=" * 60)
    logger.info(f"📡 Configuration MQTT: {mqtt_host}:{mqtt_port}")
    
    simulator = RealSensorSimulator(mqtt_host=mqtt_host, mqtt_port=mqtt_port)
    
    try:
        await simulator.start()
    except KeyboardInterrupt:
        logger.info("👋 Interruption utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
    finally:
        simulator.stop()

if __name__ == "__main__":
    asyncio.run(main())
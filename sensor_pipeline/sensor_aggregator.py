#!/usr/bin/env python3
"""
Pipeline d'agrégation MQTT pour capteurs IoT industriels
Collecte les données des 3 capteurs réels et les agrège en temps réel
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Set
import paho.mqtt.client as mqtt
from collections import defaultdict
from dataclasses import dataclass, asdict
import threading
import time

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class SensorReading:
    """Lecture d'un capteur individuel"""
    timestamp: str
    value: float
    sensor_type: str
    machine_id: str

@dataclass
class AggregatedReading:
    """Lecture agrégée complète d'une machine"""
    machine_id: str
    timestamp: str
    temperature: float
    pressure: float
    velocity: float
    product_type: str = "TypeA"

class SensorDataAggregator:
    """
    Agrégateur de données capteurs avec gestion temps réel
    Collecte et synchronise les données des 3 capteurs par machine
    """
    
    def __init__(self, mqtt_host="localhost", mqtt_port=1883, tolerance_seconds=1):
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.tolerance_seconds = tolerance_seconds
        
        # Buffer pour stocker les lectures en attente d'agrégation
        self.sensor_buffer: Dict[str, Dict[str, Dict[str, SensorReading]]] = defaultdict(lambda: defaultdict(dict))
        # Format: {machine_id: {timestamp: {sensor_type: SensorReading}}}
        
        # Client MQTT pour écouter les capteurs
        self.mqtt_client_subscriber = mqtt.Client(client_id="sensor_aggregator_sub")
        self.mqtt_client_subscriber.on_connect = self.on_connect_subscriber
        self.mqtt_client_subscriber.on_message = self.on_message_sensor
        
        # Client MQTT pour publier les données agrégées
        self.mqtt_client_publisher = mqtt.Client(client_id="sensor_aggregator_pub")
        
        # Liste des capteurs attendus
        self.expected_sensors = {"temperature", "pressure", "velocity"}
        
        # Thread pour nettoyer les anciens buffers
        self.cleanup_running = True
        
    async def start(self):
        """Démarre le pipeline d'agrégation"""
        try:
            logger.info("🚀 Démarrage du pipeline d'agrégation capteurs...")
            
            # Connexion aux brokers MQTT
            self.mqtt_client_subscriber.connect(self.mqtt_host, self.mqtt_port, 60)
            self.mqtt_client_publisher.connect(self.mqtt_host, self.mqtt_port, 60)
            
            # Démarrer les boucles MQTT
            self.mqtt_client_subscriber.loop_start()
            self.mqtt_client_publisher.loop_start()
            
            # Démarrer le nettoyage périodique
            cleanup_thread = threading.Thread(target=self.cleanup_old_data, daemon=True)
            cleanup_thread.start()
            
            logger.info("✅ Pipeline d'agrégation actif - En attente de données capteurs...")
            
            # Boucle principale
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Erreur pipeline: {e}")
            raise
            
    def on_connect_subscriber(self, client, userdata, flags, rc):
        """Callback connexion MQTT subscriber"""
        if rc == 0:
            logger.info("✅ Connecté au broker MQTT pour écoute capteurs")
            # S'abonner aux topics des capteurs réels
            topics = [
                "sensors/+/temperature",  # Wildcard pour toutes les machines
                "sensors/+/pressure", 
                "sensors/+/velocity"
            ]
            
            for topic in topics:
                client.subscribe(topic, qos=1)
                logger.info(f"📡 Abonnement topic: {topic}")
        else:
            logger.error(f"❌ Échec connexion MQTT: {rc}")
    
    def on_message_sensor(self, client, userdata, msg):
        """Traite les messages des capteurs individuels"""
        try:
            # Parsing du topic: sensors/machine_01/temperature
            topic_parts = msg.topic.split('/')
            if len(topic_parts) != 3 or topic_parts[0] != "sensors":
                logger.warning(f"⚠️ Topic invalide: {msg.topic}")
                return
                
            machine_id = topic_parts[1]
            sensor_type = topic_parts[2]
            
            # Parsing des données JSON
            try:
                data = json.loads(msg.payload.decode())
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON invalide pour {msg.topic}: {e}")
                return
            
            # Validation des données
            if "timestamp" not in data or "value" not in data:
                logger.error(f"❌ Données incomplètes pour {msg.topic}: {data}")
                return
            
            # Création de la lecture capteur
            sensor_reading = SensorReading(
                timestamp=data["timestamp"],
                value=float(data["value"]),
                sensor_type=sensor_type,
                machine_id=machine_id
            )
            
            logger.debug(f"📊 Capteur reçu: {machine_id}/{sensor_type} = {sensor_reading.value} à {sensor_reading.timestamp}")
            
            # Ajouter au buffer d'agrégation
            self.add_to_buffer(sensor_reading)
            
        except Exception as e:
            logger.error(f"❌ Erreur traitement message capteur: {e}")
    
    def add_to_buffer(self, reading: SensorReading):
        """Ajoute une lecture au buffer et vérifie si agrégation possible"""
        machine_id = reading.machine_id
        timestamp = reading.timestamp
        sensor_type = reading.sensor_type
        
        # Ajouter au buffer
        self.sensor_buffer[machine_id][timestamp][sensor_type] = reading
        
        logger.debug(f"🔄 Buffer {machine_id}/{timestamp}: {list(self.sensor_buffer[machine_id][timestamp].keys())}")
        
        # Vérifier si on a toutes les données pour ce timestamp
        current_sensors = set(self.sensor_buffer[machine_id][timestamp].keys())
        
        if current_sensors == self.expected_sensors:
            logger.info(f"✅ Données complètes pour {machine_id} à {timestamp} - Agrégation...")
            self.aggregate_and_publish(machine_id, timestamp)
            
            # Nettoyer ce timestamp du buffer
            del self.sensor_buffer[machine_id][timestamp]
        
        # Vérifier les timestamps proches (tolérance)
        self.check_tolerance_aggregation(machine_id, timestamp)
    
    def check_tolerance_aggregation(self, machine_id: str, new_timestamp: str):
        """Vérifie si on peut agréger avec des timestamps proches (tolérance)"""
        try:
            new_dt = datetime.fromisoformat(new_timestamp.replace('Z', '+00:00'))
            
            # Chercher des timestamps dans la tolérance
            for buffered_timestamp in list(self.sensor_buffer[machine_id].keys()):
                if buffered_timestamp == new_timestamp:
                    continue
                    
                try:
                    buffered_dt = datetime.fromisoformat(buffered_timestamp.replace('Z', '+00:00'))
                    
                    # Si dans la tolérance
                    if abs((new_dt - buffered_dt).total_seconds()) <= self.tolerance_seconds:
                        # Vérifier si on peut agréger
                        all_sensors = set()
                        for ts in [new_timestamp, buffered_timestamp]:
                            if ts in self.sensor_buffer[machine_id]:
                                all_sensors.update(self.sensor_buffer[machine_id][ts].keys())
                        
                        if all_sensors == self.expected_sensors:
                            logger.info(f"⏱️ Agrégation avec tolérance: {machine_id} timestamps {new_timestamp} & {buffered_timestamp}")
                            
                            # Fusionner les données et utiliser le timestamp le plus récent
                            target_timestamp = max(new_timestamp, buffered_timestamp)
                            
                            # Collecter toutes les données
                            merged_data = {}
                            for ts in [new_timestamp, buffered_timestamp]:
                                if ts in self.sensor_buffer[machine_id]:
                                    merged_data.update(self.sensor_buffer[machine_id][ts])
                            
                            # Créer l'agrégation
                            self.aggregate_readings(machine_id, target_timestamp, merged_data)
                            
                            # Nettoyer les timestamps utilisés
                            for ts in [new_timestamp, buffered_timestamp]:
                                if ts in self.sensor_buffer[machine_id]:
                                    del self.sensor_buffer[machine_id][ts]
                            
                            break
                            
                except ValueError as e:
                    logger.warning(f"⚠️ Timestamp invalide {buffered_timestamp}: {e}")
                    continue
                    
        except ValueError as e:
            logger.warning(f"⚠️ Timestamp invalide {new_timestamp}: {e}")
    
    def aggregate_and_publish(self, machine_id: str, timestamp: str):
        """Agrège les données d'une machine et les publie"""
        readings = self.sensor_buffer[machine_id][timestamp]
        self.aggregate_readings(machine_id, timestamp, readings)
    
    def aggregate_readings(self, machine_id: str, timestamp: str, readings: Dict[str, SensorReading]):
        """Agrège les lectures et publie le résultat"""
        try:
            # Créer la lecture agrégée
            aggregated = AggregatedReading(
                machine_id=machine_id,
                timestamp=timestamp,
                temperature=readings["temperature"].value,
                pressure=readings["pressure"].value,
                velocity=readings["velocity"].value,
                product_type=f"Type{machine_id[-1]}"  # TypeA, TypeB, etc. basé sur machine_id
            )
            
            # Publier sur le topic machine existant (compatible avec backend actuel)
            topic = f"iot/sensors/{machine_id}"
            payload = json.dumps(asdict(aggregated))
            
            result = self.mqtt_client_publisher.publish(topic, payload, qos=1)
            
            if result.rc == 0:
                logger.info(f"✅ Données agrégées publiées: {machine_id} - T:{aggregated.temperature:.1f}°C P:{aggregated.pressure:.1f}bar V:{aggregated.velocity:.1f}m/s")
            else:
                logger.error(f"❌ Échec publication MQTT pour {machine_id}")
                
        except KeyError as e:
            logger.error(f"❌ Capteur manquant pour agrégation {machine_id}: {e}")
        except Exception as e:
            logger.error(f"❌ Erreur agrégation {machine_id}: {e}")
    
    def cleanup_old_data(self):
        """Nettoie périodiquement les anciennes données du buffer"""
        while self.cleanup_running:
            try:
                from datetime import timezone
                current_time = datetime.now(timezone.utc)
                cutoff_time = current_time - timedelta(seconds=self.tolerance_seconds * 3)
                
                machines_to_clean = []
                for machine_id in list(self.sensor_buffer.keys()):
                    timestamps_to_clean = []
                    
                    for timestamp in list(self.sensor_buffer[machine_id].keys()):
                        try:
                            ts_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            if ts_dt < cutoff_time:
                                timestamps_to_clean.append(timestamp)
                        except ValueError:
                            # Timestamp invalide, le supprimer
                            timestamps_to_clean.append(timestamp)
                    
                    # Nettoyer les anciens timestamps
                    for ts in timestamps_to_clean:
                        logger.debug(f"🧹 Nettoyage ancien buffer: {machine_id}/{ts}")
                        del self.sensor_buffer[machine_id][ts]
                    
                    # Si plus de timestamps pour cette machine, nettoyer la machine
                    if not self.sensor_buffer[machine_id]:
                        machines_to_clean.append(machine_id)
                
                # Nettoyer les machines vides
                for machine_id in machines_to_clean:
                    del self.sensor_buffer[machine_id]
                
            except Exception as e:
                logger.error(f"❌ Erreur nettoyage buffer: {e}")
            
            time.sleep(self.tolerance_seconds * 2)  # Nettoyer toutes les 2 secondes
    
    def stop(self):
        """Arrête le pipeline"""
        logger.info("🛑 Arrêt du pipeline d'agrégation...")
        self.cleanup_running = False
        self.mqtt_client_subscriber.loop_stop()
        self.mqtt_client_publisher.loop_stop()
        self.mqtt_client_subscriber.disconnect()
        self.mqtt_client_publisher.disconnect()

async def main():
    """Fonction principale"""
    import os
    
    # Configuration depuis variables d'environnement Docker
    mqtt_host = os.getenv("MQTT_HOST", "localhost")
    mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
    tolerance = int(os.getenv("AGGREGATION_TOLERANCE", "1"))
    
    logger.info("🚀 DÉMARRAGE AGRÉGATEUR CAPTEURS INDUSTRIELS")
    logger.info("=" * 60)
    logger.info(f"📡 Configuration MQTT: {mqtt_host}:{mqtt_port}")
    logger.info(f"⏱️ Tolérance agrégation: {tolerance}s")
    
    aggregator = SensorDataAggregator(
        mqtt_host=mqtt_host, 
        mqtt_port=mqtt_port,
        tolerance_seconds=tolerance
    )
    
    try:
        await aggregator.start()
    except KeyboardInterrupt:
        logger.info("👋 Interruption utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
    finally:
        aggregator.stop()

if __name__ == "__main__":
    asyncio.run(main())
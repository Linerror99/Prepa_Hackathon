"""
Script de replay de données - Rejoue des scénarios spécifiques à partir des données réelles
"""

import pandas as pd
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import paho.mqtt.client as mqtt
import logging
import argparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataReplay:
    """Classe pour rejouer des données historiques"""
    
    def __init__(self, mqtt_broker: str = "localhost", mqtt_port: int = 1883):
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.mqtt_client = None
        self._setup_mqtt()
        
        # Charger les données
        self.data = pd.read_csv('../data/raw/ai4i2020_demo.csv')
        self.scenarios = pd.read_csv('../data/processed/failure_scenarios.csv')
        
        logger.info(f"Données chargées: {len(self.data)} échantillons")
    
    def _setup_mqtt(self):
        """Configure MQTT"""
        self.mqtt_client = mqtt.Client()
        try:
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            logger.info("Connecté au broker MQTT")
        except Exception as e:
            logger.warning(f"MQTT non disponible: {e}")
    
    def replay_failure_sequence(self, failure_type: str, machine_id: str = "REPLAY_MACHINE", speed: float = 1.0):
        """Rejoue une séquence de panne réelle"""
        
        # Trouver des exemples de ce type de panne
        failure_samples = self.data[self.data[failure_type] == 1].sample(min(5, len(self.data[self.data[failure_type] == 1])))
        
        if len(failure_samples) == 0:
            logger.error(f"Aucun échantillon trouvé pour {failure_type}")
            return
        
        logger.info(f"🎬 Replay de {len(failure_samples)} échantillons {failure_type}")
        
        for idx, (_, sample) in enumerate(failure_samples.iterrows()):
            # Créer la progression vers la panne
            progression = self._create_progression_to_failure(sample, failure_type)
            
            logger.info(f"📊 Séquence {idx+1}/{len(failure_samples)} - {failure_type}")
            
            for step, data_point in enumerate(progression):
                timestamp = datetime.now().isoformat()
                
                # Calculer le statut
                status = "normal"
                if step > len(progression) * 0.7:
                    status = "warning"
                if step > len(progression) * 0.9:
                    status = "critical"
                
                # Construire le message
                message = {
                    "machine_id": machine_id,
                    "timestamp": timestamp,
                    "air_temperature": data_point.get("Air temperature [K]", 300),
                    "process_temperature": data_point.get("Process temperature [K]", 310),
                    "rotational_speed": data_point.get("Rotational speed [rpm]", 1500),
                    "torque": data_point.get("Torque [Nm]", 40),
                    "tool_wear": data_point.get("Tool wear [min]", 100),
                    "product_type": sample.get("Type", "M"),
                    "status": status,
                    "predicted_failure_probability": step / len(progression),
                    "failure_type": failure_type if status == "critical" else None,
                    "replay_info": {
                        "sequence": idx + 1,
                        "step": step + 1,
                        "total_steps": len(progression),
                        "original_sample_id": int(sample.get("UDI", 0))
                    }
                }
                
                # Publier via MQTT
                if self.mqtt_client:
                    topic = f"iot/replay/{machine_id}/sensors"
                    self.mqtt_client.publish(topic, json.dumps(message, default=str))
                
                # Log des étapes importantes
                if step % 5 == 0 or status != "normal":
                    logger.info(f"  Étape {step+1}/{len(progression)}: {status} - Prob: {message['predicted_failure_probability']:.2f}")
                
                time.sleep(1.0 / speed)  # Ajuster la vitesse
            
            logger.info(f"✅ Séquence {idx+1} terminée - PANNE DÉTECTÉE")
            time.sleep(2.0 / speed)  # Pause entre séquences
    
    def _create_progression_to_failure(self, failure_sample: pd.Series, failure_type: str) -> List[Dict]:
        """Crée une progression réaliste vers la panne"""
        
        # État initial normal
        normal_sample = self.data[self.data['Machine failure'] == 0].sample(1).iloc[0]
        
        steps = 15  # Nombre d'étapes
        progression = []
        
        # Variables importantes selon le type de panne
        key_variables = {
            'TWF': ['Tool wear [min]', 'Torque [Nm]'],
            'HDF': ['Air temperature [K]', 'Process temperature [K]'],
            'PWF': ['Torque [Nm]', 'Rotational speed [rpm]'],
            'OSF': ['Torque [Nm]', 'Tool wear [min]'],
            'RNF': ['Process temperature [K]', 'Rotational speed [rpm]']
        }
        
        variables = key_variables.get(failure_type, ['Air temperature [K]', 'Process temperature [K]'])
        
        for i in range(steps):
            progress = i / (steps - 1)
            
            # Progression non-linéaire (accélération vers la fin)
            weight = progress ** 1.5
            
            step_data = {}
            
            # Pour toutes les variables
            for col in ['Air temperature [K]', 'Process temperature [K]', 'Rotational speed [rpm]', 'Torque [Nm]', 'Tool wear [min]']:
                if col in variables:
                    # Variables critiques : progression rapide vers la valeur de panne
                    step_data[col] = normal_sample[col] + (failure_sample[col] - normal_sample[col]) * weight
                else:
                    # Autres variables : légère variation
                    variation = (failure_sample[col] - normal_sample[col]) * weight * 0.3
                    step_data[col] = normal_sample[col] + variation
            
            # Ajouter un peu de bruit
            for col in step_data:
                noise_factor = 0.02  # 2% de bruit
                noise = step_data[col] * noise_factor * (2 * (0.5 - abs(0.5 - progress)))  # Plus de bruit au milieu
                step_data[col] += noise
            
            progression.append(step_data)
        
        return progression
    
    def replay_normal_operation(self, machine_id: str = "NORMAL_MACHINE", duration_minutes: int = 10, speed: float = 1.0):
        """Rejoue une opération normale"""
        
        normal_samples = self.data[self.data['Machine failure'] == 0].sample(duration_minutes)
        
        logger.info(f"🔵 Replay opération normale - {duration_minutes} minutes")
        
        for idx, (_, sample) in enumerate(normal_samples.iterrows()):
            timestamp = datetime.now().isoformat()
            
            message = {
                "machine_id": machine_id,
                "timestamp": timestamp,
                "air_temperature": float(sample["Air temperature [K]"]),
                "process_temperature": float(sample["Process temperature [K]"]),
                "rotational_speed": float(sample["Rotational speed [rpm]"]),
                "torque": float(sample["Torque [Nm]"]),
                "tool_wear": float(sample["Tool wear [min]"]),
                "product_type": sample["Type"],
                "status": "normal",
                "predicted_failure_probability": 0.0,
                "failure_type": None,
                "replay_info": {
                    "mode": "normal_operation",
                    "sample": idx + 1,
                    "total_samples": len(normal_samples)
                }
            }
            
            if self.mqtt_client:
                topic = f"iot/replay/{machine_id}/sensors"
                self.mqtt_client.publish(topic, json.dumps(message, default=str))
            
            if idx % 30 == 0:  # Log toutes les 30 secondes
                logger.info(f"  Minute {idx+1}/{duration_minutes} - Opération normale")
            
            time.sleep(60.0 / speed)  # 1 minute simulée
    
    def replay_mixed_scenario(self, machine_id: str = "MIXED_MACHINE", speed: float = 2.0):
        """Rejoue un scénario mixte : normal -> alerte -> panne"""
        
        logger.info("🎭 Replay scénario mixte")
        
        # 1. Phase normale (5 minutes)
        logger.info("Phase 1: Opération normale")
        self.replay_normal_operation(machine_id, 5, speed)
        
        # 2. Phase de dégradation
        logger.info("Phase 2: Dégradation détectée")
        failure_type = "TWF"  # Tool Wear Failure
        self.replay_failure_sequence(failure_type, machine_id, speed)
        
        logger.info("🎬 Scénario mixte terminé")

def main():
    parser = argparse.ArgumentParser(description="Replay de données industrielles réelles")
    parser.add_argument("--mode", choices=["failure", "normal", "mixed"], default="mixed",
                       help="Mode de replay")
    parser.add_argument("--failure-type", choices=["TWF", "HDF", "PWF", "OSF", "RNF"], default="TWF",
                       help="Type de panne à rejouer")
    parser.add_argument("--machine-id", default="REPLAY_MACHINE", help="ID de la machine")
    parser.add_argument("--speed", type=float, default=2.0, help="Vitesse de replay (2.0 = 2x plus rapide)")
    parser.add_argument("--duration", type=int, default=10, help="Durée en minutes pour mode normal")
    parser.add_argument("--mqtt-broker", default="localhost", help="Broker MQTT")
    parser.add_argument("--mqtt-port", type=int, default=1883, help="Port MQTT")
    
    args = parser.parse_args()
    
    replay = DataReplay(args.mqtt_broker, args.mqtt_port)
    
    if args.mode == "failure":
        replay.replay_failure_sequence(args.failure_type, args.machine_id, args.speed)
    elif args.mode == "normal":
        replay.replay_normal_operation(args.machine_id, args.duration, args.speed)
    elif args.mode == "mixed":
        replay.replay_mixed_scenario(args.machine_id, args.speed)

if __name__ == "__main__":
    main()
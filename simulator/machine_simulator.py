"""
Simulateur IoT de machines industrielles basé sur les données réelles AI4I
Reproduit les patterns de pannes authentiques via MQTT
"""

import asyncio
import json
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import pandas as pd
import numpy as np
import paho.mqtt.client as mqtt
from dataclasses import dataclass, asdict
import logging
import os
from pathlib import Path

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class SensorReading:
    """Structure pour une lecture de capteur"""
    machine_id: str
    timestamp: str
    air_temperature: float
    process_temperature: float
    rotational_speed: float
    torque: float
    tool_wear: float
    product_type: str
    status: str = "normal"
    predicted_failure_probability: float = 0.0
    failure_type: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)

@dataclass
class FailureScenario:
    """Structure pour un scénario de panne"""
    scenario_id: int
    failure_type: str
    severity: str
    description: str
    initial_conditions: Dict[str, float]
    progression_pattern: List[Dict[str, float]]
    duration_minutes: int = 30
    
class MachineSimulator:
    """Simulateur pour une machine industrielle individuelle"""
    
    def __init__(self, machine_id: str, base_data: pd.DataFrame, scenarios: pd.DataFrame):
        self.machine_id = machine_id
        self.base_data = base_data
        self.scenarios = scenarios
        self.current_scenario: Optional[FailureScenario] = None
        self.scenario_start_time: Optional[datetime] = None
        self.scenario_progress = 0.0
        
        # Initialiser les variables d'état d'abord
        self.tool_wear_accumulation = random.uniform(0, 50)
        self.operating_hours = 0
        
        # État actuel de la machine
        self.current_state = self._initialize_normal_state()
        
        logger.info(f"Machine {machine_id} initialisée")
    
    def _initialize_normal_state(self) -> Dict[str, float]:
        """Initialise l'état normal de la machine"""
        normal_data = self.base_data[self.base_data['Machine failure'] == 0]
        
        return {
            'air_temperature': normal_data['Air temperature [K]'].mean(),
            'process_temperature': normal_data['Process temperature [K]'].mean(),
            'rotational_speed': normal_data['Rotational speed [rpm]'].mean(),
            'torque': normal_data['Torque [Nm]'].mean(),
            'tool_wear': self.tool_wear_accumulation
        }
    
    def start_failure_scenario(self, scenario_type: Optional[str] = None) -> None:
        """Démarre un scénario de panne"""
        if scenario_type:
            available_scenarios = self.scenarios[self.scenarios['failure_type'] == scenario_type]
        else:
            available_scenarios = self.scenarios
        
        if len(available_scenarios) > 0:
            scenario_data = available_scenarios.sample(1).iloc[0]
            
            # Créer le pattern de progression
            progression = self._create_failure_progression(scenario_data)
            
            self.current_scenario = FailureScenario(
                scenario_id=scenario_data['scenario_id'],
                failure_type=scenario_data['failure_type'],
                severity=scenario_data['severity'],
                description=scenario_data['description'],
                initial_conditions={
                    'air_temp': scenario_data['air_temp'],
                    'process_temp': scenario_data['process_temp'],
                    'rotational_speed': scenario_data['rotational_speed'],
                    'torque': scenario_data['torque'],
                    'tool_wear': scenario_data['tool_wear']
                },
                progression_pattern=progression
            )
            
            self.scenario_start_time = datetime.now()
            self.scenario_progress = 0.0
            
            logger.info(f"Machine {self.machine_id}: Démarrage scénario {scenario_data['failure_type']} - {scenario_data['description']}")
    
    def _create_failure_progression(self, scenario_data: pd.Series) -> List[Dict[str, float]]:
        """Crée un pattern de progression vers la panne"""
        steps = 10  # Nombre d'étapes jusqu'à la panne
        progression = []
        
        # État initial (normal)
        initial = self.current_state.copy()
        
        # État final (panne)
        final = {
            'air_temperature': scenario_data['air_temp'],
            'process_temperature': scenario_data['process_temp'],
            'rotational_speed': scenario_data['rotational_speed'],
            'torque': scenario_data['torque'],
            'tool_wear': scenario_data['tool_wear']
        }
        
        # Créer une progression non-linéaire
        for i in range(steps + 1):
            progress = i / steps
            # Progression non-linéaire (s'accélère vers la fin)
            weight = progress ** 2
            
            step_state = {}
            for key in initial.keys():
                if key in final:
                    step_state[key] = initial[key] + (final[key] - initial[key]) * weight
                else:
                    step_state[key] = initial[key]
            
            progression.append(step_state)
        
        return progression
    
    def get_current_reading(self) -> SensorReading:
        """Génère une lecture de capteur actuelle"""
        now = datetime.now()
        
        # Mettre à jour l'état si un scénario est en cours
        if self.current_scenario and self.scenario_start_time:
            self._update_scenario_state(now)
        else:
            # Évolution normale avec petites variations
            self._update_normal_state()
        
        # Ajouter du bruit réaliste
        state_with_noise = self._add_sensor_noise(self.current_state)
        
        # Détecter le statut
        status, failure_prob, failure_type = self._detect_status(state_with_noise)
        
        return SensorReading(
            machine_id=self.machine_id,
            timestamp=now.isoformat(),
            air_temperature=state_with_noise['air_temperature'],
            process_temperature=state_with_noise['process_temperature'],
            rotational_speed=state_with_noise['rotational_speed'],
            torque=state_with_noise['torque'],
            tool_wear=state_with_noise['tool_wear'],
            product_type=random.choice(['L', 'M', 'H']),
            status=status,
            predicted_failure_probability=failure_prob,
            failure_type=failure_type
        )
    
    def _update_scenario_state(self, current_time: datetime) -> None:
        """Met à jour l'état selon le scénario de panne en cours"""
        if not self.current_scenario or not self.scenario_start_time:
            return
        
        # Calculer le progrès du scénario
        elapsed = (current_time - self.scenario_start_time).total_seconds() / 60  # en minutes
        self.scenario_progress = min(elapsed / self.current_scenario.duration_minutes, 1.0)
        
        # Interpoler entre les étapes du pattern
        pattern = self.current_scenario.progression_pattern
        if self.scenario_progress >= 1.0:
            # Scénario terminé - état de panne
            self.current_state = pattern[-1].copy()
        else:
            # Interpolation entre les étapes
            step_index = self.scenario_progress * (len(pattern) - 1)
            lower_index = int(step_index)
            upper_index = min(lower_index + 1, len(pattern) - 1)
            weight = step_index - lower_index
            
            # Interpolation linéaire
            for key in self.current_state.keys():
                if key in pattern[lower_index] and key in pattern[upper_index]:
                    lower_val = pattern[lower_index][key]
                    upper_val = pattern[upper_index][key]
                    self.current_state[key] = lower_val + (upper_val - lower_val) * weight
    
    def _update_normal_state(self) -> None:
        """Met à jour l'état normal avec évolution naturelle"""
        # Accumulation de l'usure d'outil
        self.tool_wear_accumulation += random.uniform(0.1, 0.5)
        self.current_state['tool_wear'] = self.tool_wear_accumulation
        
        # Variations normales des autres paramètres
        normal_data = self.base_data[self.base_data['Machine failure'] == 0]
        
        for param in ['air_temperature', 'process_temperature', 'rotational_speed', 'torque']:
            if param in self.current_state:
                param_name = {
                    'air_temperature': 'Air temperature [K]',
                    'process_temperature': 'Process temperature [K]',
                    'rotational_speed': 'Rotational speed [rpm]',
                    'torque': 'Torque [Nm]'
                }[param]
                
                mean_val = normal_data[param_name].mean()
                std_val = normal_data[param_name].std()
                
                # Légère dérive vers la moyenne avec du bruit
                current_val = self.current_state[param]
                drift = (mean_val - current_val) * 0.1  # 10% de retour vers la moyenne
                noise = random.gauss(0, std_val * 0.1)  # 10% du bruit normal
                
                self.current_state[param] = current_val + drift + noise
    
    def _add_sensor_noise(self, state: Dict[str, float]) -> Dict[str, float]:
        """Ajoute du bruit réaliste de capteur"""
        noisy_state = state.copy()
        
        noise_levels = {
            'air_temperature': 0.5,      # ±0.5K
            'process_temperature': 0.3,   # ±0.3K
            'rotational_speed': 5.0,      # ±5 rpm
            'torque': 0.5,               # ±0.5 Nm
            'tool_wear': 0.1             # ±0.1 min
        }
        
        for param, noise_level in noise_levels.items():
            if param in noisy_state:
                noise = random.gauss(0, noise_level)
                noisy_state[param] += noise
        
        return noisy_state
    
    def _detect_status(self, state: Dict[str, float]) -> tuple[str, float, Optional[str]]:
        """Détecte le statut et la probabilité de panne"""
        # Charger les seuils d'alerte
        try:
            with open('../data/processed/alert_thresholds.json', 'r') as f:
                thresholds = json.load(f)
        except FileNotFoundError:
            # Seuils par défaut si le fichier n'existe pas
            thresholds = {
                'Air temperature [K]': {'threshold': 305.0, 'type': 'Seuil MAX'},
                'Process temperature [K]': {'threshold': 315.0, 'type': 'Seuil MAX'},
                'Tool wear [min]': {'threshold': 200.0, 'type': 'Seuil MAX'},
                'Torque [Nm]': {'threshold': 50.0, 'type': 'Seuil MAX'},
                'Rotational speed [rpm]': {'threshold': '1200.0 - 1800.0', 'type': 'Plage normale'}
            }
        
        alerts = []
        failure_prob = 0.0
        
        # Vérifier chaque seuil
        if state['air_temperature'] > thresholds.get('Air temperature [K]', {}).get('threshold', 305):
            alerts.append('TEMP_HIGH')
            failure_prob += 0.3
        
        if state['process_temperature'] > thresholds.get('Process temperature [K]', {}).get('threshold', 315):
            alerts.append('PROCESS_TEMP_HIGH')
            failure_prob += 0.25
        
        if state['tool_wear'] > thresholds.get('Tool wear [min]', {}).get('threshold', 200):
            alerts.append('TOOL_WEAR_HIGH')
            failure_prob += 0.4
        
        if state['torque'] > thresholds.get('Torque [Nm]', {}).get('threshold', 50):
            alerts.append('TORQUE_HIGH')
            failure_prob += 0.3
        
        if state['rotational_speed'] < 1200 or state['rotational_speed'] > 1800:
            alerts.append('SPEED_ABNORMAL')
            failure_prob += 0.2
        
        # Déterminer le statut
        if failure_prob > 0.8:
            status = "critical"
            failure_type = self._predict_failure_type(state, alerts)
        elif failure_prob > 0.5:
            status = "warning"
            failure_type = None
        elif failure_prob > 0.2:
            status = "alert"
            failure_type = None
        else:
            status = "normal"
            failure_type = None
        
        return status, min(failure_prob, 1.0), failure_type
    
    def _predict_failure_type(self, state: Dict[str, float], alerts: List[str]) -> Optional[str]:
        """Prédit le type de panne probable"""
        if 'TOOL_WEAR_HIGH' in alerts:
            return 'TWF'
        elif 'TEMP_HIGH' in alerts or 'PROCESS_TEMP_HIGH' in alerts:
            return 'HDF'
        elif 'TORQUE_HIGH' in alerts and 'SPEED_ABNORMAL' in alerts:
            return 'PWF'
        elif 'TORQUE_HIGH' in alerts:
            return 'OSF'
        else:
            return 'RNF'

class IoTSimulator:
    """Simulateur principal IoT multi-machines"""
    
    def __init__(self, num_machines: int = 3, mqtt_broker: str = "localhost", mqtt_port: int = 1883):
        self.num_machines = num_machines
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.machines: List[MachineSimulator] = []
        self.mqtt_client: Optional[mqtt.Client] = None
        self.mqtt_connected = False
        self.running = False
        
        # Charger les données
        self._load_data()
        self._initialize_machines()
        self._setup_mqtt()
    
    def _load_data(self) -> None:
        """Charge les données et scénarios"""
        try:
            self.base_data = pd.read_csv('../data/raw/ai4i2020_demo.csv')
            self.scenarios = pd.read_csv('../data/processed/failure_scenarios.csv')
            logger.info(f"Données chargées: {len(self.base_data)} échantillons, {len(self.scenarios)} scénarios")
        except FileNotFoundError as e:
            logger.error(f"Impossible de charger les données: {e}")
            raise
    
    def _initialize_machines(self) -> None:
        """Initialise les simulateurs de machines"""
        for i in range(self.num_machines):
            machine_id = f"MACHINE_{i+1:02d}"
            machine = MachineSimulator(machine_id, self.base_data, self.scenarios)
            self.machines.append(machine)
        
        logger.info(f"{len(self.machines)} machines initialisées")
    
    def _setup_mqtt(self) -> None:
        """Configure le client MQTT"""
        # Corriger l'API dépréciée
        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_disconnect = self._on_mqtt_disconnect
        
        try:
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
        except Exception as e:
            logger.warning(f"Impossible de se connecter au broker MQTT: {e}")
            logger.info("Mode simulation sans MQTT activé")
    
    def _on_mqtt_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self.mqtt_connected = True
            logger.info("✅ Simulateur connecté au broker MQTT")
        else:
            self.mqtt_connected = False
            logger.error(f"❌ Échec de connexion MQTT, code: {rc}")
    
    def _on_mqtt_disconnect(self, client, userdata, flags, rc, properties=None):
        if self.mqtt_connected:  # Éviter les logs répétés
            self.mqtt_connected = False
            logger.info("📡 Simulateur déconnecté du broker MQTT")
    
    def start_simulation(self, duration_minutes: Optional[int] = None, reading_interval: float = 2.0) -> None:
        """Démarre la simulation"""
        logger.info(f"🚀 Démarrage simulation IoT avec {len(self.machines)} machines")
        logger.info(f"📊 Intervalle de lecture: {reading_interval}s")
        
        if duration_minutes:
            logger.info(f"⏱️ Durée: {duration_minutes} minutes")
        
        self.running = True
        start_time = datetime.now()
        
        try:
            while self.running:
                if duration_minutes:
                    elapsed = (datetime.now() - start_time).total_seconds() / 60
                    if elapsed >= duration_minutes:
                        break
                
                # Collecter et publier les données de toutes les machines
                self._collect_and_publish_readings()
                
                # Déclencher aléatoirement des scénarios de panne
                self._trigger_random_failures()
                
                time.sleep(reading_interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Arrêt demandé par l'utilisateur")
        finally:
            self.stop_simulation()
    
    def _collect_and_publish_readings(self) -> None:
        """Collecte et publie les lectures de tous les capteurs"""
        readings = []
        
        for machine in self.machines:
            reading = machine.get_current_reading()
            readings.append(reading)
            
            # Publier via MQTT si connecté
            if self.mqtt_connected and self.mqtt_client and self.mqtt_client.is_connected():
                topic = f"iot/machines/{machine.machine_id}/sensors"
                self.mqtt_client.publish(topic, reading.to_json())
            
            # Log des alertes importantes
            if reading.status in ['warning', 'critical']:
                logger.warning(f"🚨 {machine.machine_id}: {reading.status.upper()} - Prob panne: {reading.predicted_failure_probability:.2f}")
        
        # Publier un résumé global
        if self.mqtt_connected and self.mqtt_client and self.mqtt_client.is_connected():
            summary = self._create_summary(readings)
            self.mqtt_client.publish("iot/fleet/summary", json.dumps(summary, default=str))
    
    def _create_summary(self, readings: List[SensorReading]) -> Dict:
        """Crée un résumé de l'état de la flotte"""
        status_counts = {}
        avg_failure_prob = 0.0
        active_alerts = []
        
        for reading in readings:
            status_counts[reading.status] = status_counts.get(reading.status, 0) + 1
            avg_failure_prob += reading.predicted_failure_probability
            
            if reading.status in ['warning', 'critical']:
                active_alerts.append({
                    'machine_id': reading.machine_id,
                    'status': reading.status,
                    'failure_prob': reading.predicted_failure_probability,
                    'failure_type': reading.failure_type
                })
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_machines': len(readings),
            'status_distribution': status_counts,
            'avg_failure_probability': avg_failure_prob / len(readings),
            'active_alerts': active_alerts
        }
    
    def _trigger_random_failures(self) -> None:
        """Déclenche aléatoirement des scénarios de panne"""
        # 1% de chance par cycle de déclencher une panne sur une machine
        if random.random() < 0.01:
            # Choisir une machine au hasard qui n'a pas déjà de scénario actif
            available_machines = [m for m in self.machines if m.current_scenario is None]
            
            if available_machines:
                machine = random.choice(available_machines)
                failure_type = random.choice(['TWF', 'HDF', 'PWF', 'OSF', 'RNF'])
                machine.start_failure_scenario(failure_type)
    
    def trigger_failure_scenario(self, machine_id: str, failure_type: str) -> bool:
        """Déclenche manuellement un scénario de panne"""
        machine = next((m for m in self.machines if m.machine_id == machine_id), None)
        if machine:
            machine.start_failure_scenario(failure_type)
            logger.info(f"Scénario {failure_type} déclenché sur {machine_id}")
            return True
        return False
    
    def stop_simulation(self) -> None:
        """Arrête la simulation"""
        logger.info("🛑 Arrêt de la simulation IoT")
        self.running = False
        
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()

def main():
    """Fonction principale pour lancer le simulateur"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simulateur IoT industriel basé sur données réelles")
    parser.add_argument("--machines", type=int, default=3, help="Nombre de machines à simuler")
    parser.add_argument("--duration", type=int, help="Durée en minutes (infini si non spécifié)")
    parser.add_argument("--interval", type=float, default=2.0, help="Intervalle entre lectures (secondes)")
    parser.add_argument("--mqtt-broker", default="localhost", help="Adresse du broker MQTT")
    parser.add_argument("--mqtt-port", type=int, default=1883, help="Port du broker MQTT")
    
    args = parser.parse_args()
    
    # Créer et démarrer le simulateur
    simulator = IoTSimulator(
        num_machines=args.machines,
        mqtt_broker=args.mqtt_broker,
        mqtt_port=args.mqtt_port
    )
    
    simulator.start_simulation(
        duration_minutes=args.duration,
        reading_interval=args.interval
    )

if __name__ == "__main__":
    main()
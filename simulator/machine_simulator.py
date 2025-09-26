"""
Simulateur IoT de machines industrielles basé sur les données réelles AI4I
Reproduit les patterns de pannes authentiques via MQTT
"""

import os
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
    """Structure pour une lecture de capteur industriel"""
    machine_id: str
    timestamp: str
    temperature: float      # Température en °C (20-80°C)
    pressure: float         # Pression en bar (1-10 bar)
    velocity: float         # Vitesse en m/s (0.5-5.0 m/s)
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
    
    def __init__(self, machine_id: str, base_data=None, scenarios=None):
        self.machine_id = machine_id
        self.current_scenario: Optional[FailureScenario] = None
        self.scenario_start_time: Optional[datetime] = None
        self.scenario_progress = 0.0
        
        # Variables d'état pour simulation industrielle
        self.operating_hours = 0
        
        # État actuel de la machine industrielle
        self.current_state = self._initialize_normal_state()
        
        logger.info(f"Machine industrielle {machine_id} initialisée")
    
    def _initialize_normal_state(self) -> Dict[str, float]:
        """Initialise l'état normal de la machine industrielle"""
        # Valeurs normales pour équipements industriels
        return {
            'temperature': random.uniform(25.0, 35.0),    # °C - température ambiante normale
            'pressure': random.uniform(2.0, 4.0),         # bar - pression de fonctionnement normale
            'velocity': random.uniform(1.0, 2.0)          # m/s - vitesse normale des composants
        }
    
    def start_failure_scenario(self, scenario_type: Optional[str] = None) -> None:
        """Démarre un scénario de panne industrielle"""
        # Définir des scénarios de panne réalistes pour équipements industriels
        industrial_scenarios = [
            {
                'failure_type': 'OVERHEATING', 
                'description': 'Surchauffe des composants',
                'final_values': {'temperature': 75.0, 'pressure': 3.5, 'velocity': 1.2}
            },
            {
                'failure_type': 'PRESSURE_LOSS', 
                'description': 'Perte de pression système',
                'final_values': {'temperature': 28.0, 'pressure': 0.8, 'velocity': 0.3}
            },
            {
                'failure_type': 'MECHANICAL_WEAR', 
                'description': 'Usure mécanique excessive',
                'final_values': {'temperature': 45.0, 'pressure': 2.1, 'velocity': 0.1}
            },
            {
                'failure_type': 'VIBRATION_EXCESS', 
                'description': 'Vibrations excessives',
                'final_values': {'temperature': 40.0, 'pressure': 6.5, 'velocity': 4.8}
            }
        ]
        
        # Sélectionner un scénario
        if scenario_type:
            scenarios = [s for s in industrial_scenarios if s['failure_type'] == scenario_type]
            scenario_data = scenarios[0] if scenarios else industrial_scenarios[0]
        else:
            scenario_data = random.choice(industrial_scenarios)
        
        # Créer le pattern de progression
        progression = self._create_failure_progression(scenario_data['final_values'])
        
        self.current_scenario = FailureScenario(
            scenario_id=random.randint(1, 1000),
            failure_type=scenario_data['failure_type'],
            severity='HIGH',
            description=scenario_data['description'],
            initial_conditions=self.current_state.copy(),
            progression_pattern=progression,
            duration_minutes=2  # Durée réduite à 2 minutes pour tests rapides
        )
        
        self.scenario_start_time = datetime.now()
        self.scenario_progress = 0.0
        
        logger.info(f"Machine {self.machine_id}: Démarrage scénario {scenario_data['failure_type']} - {scenario_data['description']}")
    
    def _create_failure_progression(self, final_values: Dict[str, float]) -> List[Dict[str, float]]:
        """Crée un pattern de progression vers la panne industrielle"""
        steps = 10  # Nombre d'étapes jusqu'à la panne
        progression = []
        
        # État initial (normal)
        initial = self.current_state.copy()
        
        # Créer une progression non-linéaire
        for i in range(steps + 1):
            progress = i / steps
            # Progression non-linéaire (s'accélère vers la fin)
            weight = progress ** 2
            
            step_state = {}
            for key in initial.keys():
                if key in final_values:
                    step_state[key] = initial[key] + (final_values[key] - initial[key]) * weight
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
            temperature=state_with_noise['temperature'],
            pressure=state_with_noise['pressure'],
            velocity=state_with_noise['velocity'],
            product_type=random.choice(['TypeA', 'TypeB', 'TypeC']),
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
        """Met à jour l'état normal avec évolution naturelle industrielle"""
        # Évolution naturelle des paramètres industriels
        self.operating_hours += 15/3600  # 15 secondes en heures
        
        # Légères variations normales autour des valeurs de consigne
        for param in ['temperature', 'pressure', 'velocity']:
            if param in self.current_state:
                current_val = self.current_state[param]
                
                # Définir les plages normales et les dérives
                if param == 'temperature':
                    target_range = (25.0, 35.0)
                    max_drift = 0.5
                elif param == 'pressure':
                    target_range = (2.0, 4.0)
                    max_drift = 0.1
                elif param == 'velocity':
                    target_range = (1.0, 2.0)
                    max_drift = 0.05
                
                # Dérive légère vers la plage normale
                target_val = random.uniform(*target_range)
                drift = (target_val - current_val) * 0.05  # 5% de retour vers la cible
                noise = random.gauss(0, max_drift * 0.1)  # Bruit léger
                
                self.current_state[param] = current_val + drift + noise
    
    def _add_sensor_noise(self, state: Dict[str, float]) -> Dict[str, float]:
        """Ajoute du bruit réaliste de capteur industriel"""
        noisy_state = state.copy()
        
        # Niveaux de bruit réalistes pour capteurs industriels
        noise_levels = {
            'temperature': 0.2,    # ±0.2°C (précision typique capteurs température)
            'pressure': 0.05,      # ±0.05 bar (précision capteurs pression)
            'velocity': 0.02       # ±0.02 m/s (précision capteurs vitesse)
        }
        
        for param, noise_level in noise_levels.items():
            if param in noisy_state:
                noise = random.gauss(0, noise_level)
                noisy_state[param] += noise
                
                # Appliquer les limites physiques
                if param == 'temperature':
                    noisy_state[param] = max(15.0, min(85.0, noisy_state[param]))
                elif param == 'pressure':
                    noisy_state[param] = max(0.1, min(12.0, noisy_state[param]))
                elif param == 'velocity':
                    noisy_state[param] = max(0.0, min(6.0, noisy_state[param]))
        
        return noisy_state
    
    def _detect_status(self, state: Dict[str, float]) -> tuple[str, float, Optional[str]]:
        """Détecte le statut et la probabilité de panne industrielle"""
        # Seuils d'alerte industriels réalistes
        thresholds = {
            'temperature': {'min': 15.0, 'max': 50.0, 'critical': 65.0},
            'pressure': {'min': 1.5, 'max': 6.0, 'critical': 8.0},
            'velocity': {'min': 0.2, 'max': 3.5, 'critical': 5.0}
        }
        
        alerts = []
        failure_prob = 0.0
        
        # Vérifier température
        temp = state['temperature']
        if temp > thresholds['temperature']['critical']:
            alerts.append('TEMP_CRITICAL')
            failure_prob += 0.5
        elif temp > thresholds['temperature']['max'] or temp < thresholds['temperature']['min']:
            alerts.append('TEMP_ABNORMAL')
            failure_prob += 0.2
        
        # Vérifier pression
        pressure = state['pressure']
        if pressure > thresholds['pressure']['critical']:
            alerts.append('PRESSURE_CRITICAL')
            failure_prob += 0.4
        elif pressure > thresholds['pressure']['max'] or pressure < thresholds['pressure']['min']:
            alerts.append('PRESSURE_ABNORMAL')
            failure_prob += 0.15
        
        # Vérifier vitesse
        velocity = state['velocity']
        if velocity > thresholds['velocity']['critical']:
            alerts.append('VELOCITY_CRITICAL')
            failure_prob += 0.3
        elif velocity > thresholds['velocity']['max'] or velocity < thresholds['velocity']['min']:
            alerts.append('VELOCITY_ABNORMAL')
            failure_prob += 0.1
        
        # Déterminer le statut industriel
        if failure_prob > 0.7:
            status = "critical"
            failure_type = self._predict_failure_type(state, alerts)
        elif failure_prob > 0.4:
            status = "warning"
            failure_type = None
        elif failure_prob > 0.15:
            status = "alert"
            failure_type = None
        else:
            status = "normal"
            failure_type = None
        
        return status, min(failure_prob, 1.0), failure_type
    
    def _predict_failure_type(self, state: Dict[str, float], alerts: List[str]) -> Optional[str]:
        """Prédit le type de panne industrielle probable"""
        if 'TEMP_CRITICAL' in alerts:
            return 'OVERHEATING'
        elif 'PRESSURE_CRITICAL' in alerts:
            return 'PRESSURE_LOSS'
        elif 'VELOCITY_CRITICAL' in alerts:
            return 'MECHANICAL_WEAR'
        elif any('ABNORMAL' in alert for alert in alerts):
            return 'VIBRATION_EXCESS'
        else:
            return 'SYSTEM_DEGRADATION'

class IoTSimulator:
    """Simulateur principal IoT multi-machines"""
    
    def __init__(self, num_machines: int = 3, mqtt_broker: str = "localhost", mqtt_port: int = 1883):
        self.num_machines = num_machines
        # Utiliser la variable d'environnement ou la valeur par défaut
        self.mqtt_broker = os.getenv("MQTT_BROKER", mqtt_broker)
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
        """Initialise les données pour simulation industrielle"""
        # Plus besoin de charger des fichiers UCI - simulation autonome
        logger.info("Mode simulation industrielle autonome activé")
    
    def _initialize_machines(self) -> None:
        """Initialise les simulateurs de machines industrielles"""
        for i in range(self.num_machines):
            machine_id = f"MACHINE_{i+1:02d}"
            machine = MachineSimulator(machine_id, None, None)  # Plus de dépendances aux fichiers
            self.machines.append(machine)
        
        logger.info(f"{len(self.machines)} machines industrielles initialisées")
    
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
    
    def start_simulation(self, duration_minutes: Optional[int] = None, reading_interval: float = 300.0) -> None:
        """Démarre la simulation industrielle"""
        logger.info(f"🏭 Démarrage simulation industrielle avec {len(self.machines)} machines")
        logger.info(f"📊 Intervalle de lecture industriel: {reading_interval}s ({reading_interval/60:.1f} min)")
        
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
        """Déclenche aléatoirement des scénarios de panne industrielle"""
        # 10% de chance par cycle de déclencher une panne sur une machine (fréquent pour tests rapides)
        if random.random() < 0.10:
            # Choisir une machine au hasard qui n'a pas déjà de scénario actif
            available_machines = [m for m in self.machines if m.current_scenario is None]
            
            if available_machines:
                machine = random.choice(available_machines)
                failure_type = random.choice(['OVERHEATING', 'PRESSURE_LOSS', 'MECHANICAL_WEAR', 'VIBRATION_EXCESS'])
                machine.start_failure_scenario(failure_type)
                logger.info(f"🔥 Panne simulée: {failure_type} sur {machine.machine_id}")
    
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
    parser.add_argument("--interval", type=float, default=15.0, help="Intervalle entre lectures industrielles (secondes) - défaut 15 secondes")
    parser.add_argument("--mqtt-broker", default=os.getenv("MQTT_BROKER", "localhost"), help="Adresse du broker MQTT")
    parser.add_argument("--mqtt-port", type=int, default=1883, help="Port du broker MQTT")
    
    args = parser.parse_args()
    
    # Créer et démarrer le simulateur industriel
    simulator = IoTSimulator(
        num_machines=args.machines,
        mqtt_broker=args.mqtt_broker,
        mqtt_port=args.mqtt_port
    )
    
    logger.info(f"🏭 Démarrage simulateur industriel - {args.machines} machines, intervalle {args.interval}s")
    simulator.start_simulation(
        duration_minutes=args.duration,
        reading_interval=args.interval
    )

if __name__ == "__main__":
    main()
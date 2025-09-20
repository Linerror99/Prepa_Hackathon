"""
Backend API FastAPI pour système de maintenance prédictive
Intègre MQTT, IA et APIs temps réel pour le hackathon IoT
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field
import paho.mqtt.client as mqtt
import redis
from contextlib import asynccontextmanager
import uvicorn
import os
from pathlib import Path

# Import de notre nouvelle IA
from ai_models import SmartPredictiveEngine

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===== MODÈLES DE DONNÉES =====

class SensorReading(BaseModel):
    """Modèle pour une lecture de capteur"""
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

class Alert(BaseModel):
    """Modèle pour une alerte"""
    id: str
    machine_id: str
    timestamp: str
    severity: str  # info, warning, critical
    message: str
    failure_type: Optional[str] = None
    probability: float = 0.0
    acknowledged: bool = False

class MachineStatus(BaseModel):
    """Modèle pour le statut d'une machine"""
    machine_id: str
    status: str
    last_reading: Optional[SensorReading] = None
    alerts_count: int = 0
    uptime_hours: float = 0.0
    efficiency: float = 100.0

class FleetSummary(BaseModel):
    """Modèle pour le résumé de la flotte"""
    timestamp: str
    total_machines: int
    operational: int
    warnings: int
    critical: int
    avg_efficiency: float
    active_alerts: List[Alert]

# ===== GESTIONNAIRE MQTT =====

class MQTTManager:
    """Gestionnaire des connexions MQTT"""
    
    def __init__(self, broker_host: str = "localhost", broker_port: int = 1883):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client = None
        self.connected = False
        self.message_queue = asyncio.Queue()
        
    async def connect(self):
        """Connexion au broker MQTT"""
        try:
            self.client = mqtt.Client()
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            self.client.on_disconnect = self._on_disconnect
            
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            
            # S'abonner aux topics
            topics = [
                "iot/machines/+/sensors",
                "iot/fleet/summary",
                "iot/alerts/+"
            ]
            
            for topic in topics:
                self.client.subscribe(topic)
                logger.info(f"Abonnement au topic: {topic}")
                
        except Exception as e:
            logger.error(f"Erreur connexion MQTT: {e}")
    
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            logger.info("Backend connecté au broker MQTT")
        else:
            logger.error(f"Échec connexion MQTT, code: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Callback réception message MQTT"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            # Ajouter à la queue pour traitement asynchrone
            asyncio.create_task(self.message_queue.put({
                'topic': topic,
                'payload': payload,
                'timestamp': datetime.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Erreur traitement message MQTT: {e}")
    
    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        logger.info("Déconnecté du broker MQTT")
    
    async def get_message(self):
        """Récupère le prochain message de la queue"""
        return await self.message_queue.get()

# ===== MOTEUR IA PRÉDICTIF =====

# ===== MOTEUR IA PRÉDICTIF =====

class PredictiveAIEngine:
    """Moteur d'IA pour la maintenance prédictive - REMPLACÉ par SmartPredictiveEngine"""
    
    def __init__(self):
        self.smart_engine = SmartPredictiveEngine()
        logger.info("🤖 Nouveau moteur IA Smart initialisé avec ML")
    
    def predict_failure(self, reading: SensorReading) -> Dict[str, Any]:
        """Interface de compatibilité - utilise le nouveau moteur ML"""
        
        # Convertir SensorReading en dictionnaire pour le nouveau moteur
        reading_data = {
            'air_temperature': reading.air_temperature,
            'process_temperature': reading.process_temperature,
            'rotational_speed': reading.rotational_speed,
            'torque': reading.torque,
            'tool_wear': reading.tool_wear
        }
        
        # Utiliser le nouveau moteur ML
        prediction = self.smart_engine.predict_anomaly(reading_data)
        
        # Compatibilité avec l'ancien format
        return {
            'predicted_status': prediction['predicted_status'],
            'failure_probability': prediction['failure_probability'],
            'failure_type': prediction['failure_type'],
            'risk_scores': {'ML_Score': prediction['anomaly_score']},
            'confidence': prediction['confidence'],
            'time_to_failure': prediction['time_to_failure'],
            'model_info': {
                'type': prediction['model_type'],
                'is_ml': True,
                'anomaly_score': prediction['anomaly_score']
            }
        }
    
    def get_model_status(self) -> Dict[str, Any]:
        """Retourne l'état des modèles ML"""
        return self.smart_engine.get_model_info()

# ===== GESTIONNAIRE DE DONNÉES =====

class DataManager:
    """Gestionnaire des données et cache Redis"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = None
        self.redis_url = redis_url
        self.machines_data: Dict[str, Any] = {}
        self.alerts: List[Alert] = []
        
    async def connect_redis(self):
        """Connexion à Redis"""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("Connecté à Redis")
        except Exception as e:
            logger.warning(f"Redis non disponible: {e}")
    
    async def store_reading(self, reading: SensorReading, ai_prediction: Dict[str, Any]):
        """Stocke une lecture et sa prédiction"""
        machine_id = reading.machine_id
        
        # Mise à jour en mémoire
        self.machines_data[machine_id] = {
            'last_reading': reading.dict(),
            'ai_prediction': ai_prediction,
            'last_update': datetime.now().isoformat()
        }
        
        # Stockage Redis (si disponible)
        if self.redis_client:
            try:
                # Données temps réel
                key = f"machine:{machine_id}:current"
                self.redis_client.setex(key, 300, json.dumps({
                    'reading': reading.dict(),
                    'prediction': ai_prediction
                }))
                
                # Historique (stream Redis)
                stream_key = f"machine:{machine_id}:history"
                self.redis_client.xadd(stream_key, {
                    'data': json.dumps(reading.dict()),
                    'prediction': json.dumps(ai_prediction)
                }, maxlen=1000)  # Garder les 1000 dernières entrées
                
            except Exception as e:
                logger.error(f"Erreur stockage Redis: {e}")
    
    async def create_alert(self, machine_id: str, severity: str, message: str, 
                          failure_type: Optional[str] = None, probability: float = 0.0):
        """Crée une nouvelle alerte"""
        alert = Alert(
            id=f"{machine_id}_{datetime.now().timestamp()}",
            machine_id=machine_id,
            timestamp=datetime.now().isoformat(),
            severity=severity,
            message=message,
            failure_type=failure_type,
            probability=probability
        )
        
        self.alerts.append(alert)
        
        # Garder seulement les 100 dernières alertes
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
        
        # Stockage Redis
        if self.redis_client:
            try:
                self.redis_client.lpush("alerts", json.dumps(alert.dict()))
                self.redis_client.ltrim("alerts", 0, 99)  # Garder les 100 dernières
            except Exception as e:
                logger.error(f"Erreur stockage alerte Redis: {e}")
        
        logger.info(f"🚨 ALERTE {severity.upper()}: {machine_id} - {message}")
        return alert
    
    def get_machine_status(self, machine_id: str) -> Optional[MachineStatus]:
        """Récupère le statut d'une machine"""
        if machine_id not in self.machines_data:
            return None
        
        data = self.machines_data[machine_id]
        reading_data = data['last_reading']
        
        # Compter les alertes actives pour cette machine
        active_alerts = len([a for a in self.alerts if a.machine_id == machine_id and not a.acknowledged])
        
        return MachineStatus(
            machine_id=machine_id,
            status=reading_data['status'],
            last_reading=SensorReading(**reading_data),
            alerts_count=active_alerts,
            uptime_hours=24.0,  # Simulé
            efficiency=95.0 if reading_data['status'] == 'normal' else 75.0
        )
    
    def get_fleet_summary(self) -> FleetSummary:
        """Génère un résumé de la flotte"""
        total_machines = len(self.machines_data)
        if total_machines == 0:
            return FleetSummary(
                timestamp=datetime.now().isoformat(),
                total_machines=0,
                operational=0,
                warnings=0,
                critical=0,
                avg_efficiency=0.0,
                active_alerts=[]
            )
        
        # Compter par statut
        status_counts = {'normal': 0, 'alert': 0, 'warning': 0, 'critical': 0}
        total_efficiency = 0.0
        
        for machine_data in self.machines_data.values():
            status = machine_data['last_reading']['status']
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Efficacité simulée basée sur le statut
            efficiency = {
                'normal': 95.0,
                'alert': 90.0, 
                'warning': 75.0,
                'critical': 50.0
            }.get(status, 95.0)
            total_efficiency += efficiency
        
        # Alertes actives récentes (dernières 24h)
        recent_alerts = [a for a in self.alerts if not a.acknowledged][-10:]  # 10 dernières
        
        return FleetSummary(
            timestamp=datetime.now().isoformat(),
            total_machines=total_machines,
            operational=status_counts.get('normal', 0) + status_counts.get('alert', 0),
            warnings=status_counts.get('warning', 0),
            critical=status_counts.get('critical', 0),
            avg_efficiency=total_efficiency / total_machines if total_machines > 0 else 0.0,
            active_alerts=recent_alerts
        )

# ===== GESTIONNAIRE WEBSOCKET =====

class WebSocketManager:
    """Gestionnaire des connexions WebSocket temps réel"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Nouvelle connexion WebSocket: {len(self.active_connections)} clients connectés")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Connexion WebSocket fermée: {len(self.active_connections)} clients connectés")
    
    async def broadcast(self, message: dict):
        """Diffuse un message à tous les clients connectés"""
        if not self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        # Nettoyer les connexions fermées
        for conn in disconnected:
            self.disconnect(conn)

# ===== APPLICATION FASTAPI =====

# Instances globales
mqtt_manager = MQTTManager()
ai_engine = PredictiveAIEngine()
data_manager = DataManager()
websocket_manager = WebSocketManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire du cycle de vie de l'application"""
    # Démarrage
    logger.info("🚀 Démarrage du backend IoT")
    
    # Connexions
    await mqtt_manager.connect()
    await data_manager.connect_redis()
    
    # Démarrer le processeur de messages MQTT
    asyncio.create_task(mqtt_message_processor())
    
    yield
    
    # Arrêt
    logger.info("🛑 Arrêt du backend IoT")

# Création de l'application FastAPI
app = FastAPI(
    title="IoT Predictive Maintenance API",
    description="API Backend pour système de maintenance prédictive industrielle",
    version="1.0.0",
    lifespan=lifespan
)

# CORS pour le développement
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== PROCESSEUR DE MESSAGES MQTT =====

async def mqtt_message_processor():
    """Traite les messages MQTT en arrière-plan"""
    logger.info("Processeur de messages MQTT démarré")
    
    while True:
        try:
            # Récupérer le prochain message
            message = await mqtt_manager.get_message()
            topic = message['topic']
            payload = message['payload']
            
            # Traitement selon le type de topic
            if "/sensors" in topic:
                await process_sensor_data(payload)
            elif "/summary" in topic:
                await process_fleet_summary(payload)
            
        except Exception as e:
            logger.error(f"Erreur traitement message MQTT: {e}")
            await asyncio.sleep(1)

async def process_sensor_data(data: dict):
    """Traite les données de capteurs"""
    try:
        # Créer l'objet de lecture
        reading = SensorReading(**data)
        
        # Appliquer l'IA prédictive
        ai_prediction = ai_engine.predict_failure(reading)
        
        # Mettre à jour le statut si l'IA prédit différemment
        if ai_prediction['predicted_status'] != reading.status:
            reading.status = ai_prediction['predicted_status']
            reading.predicted_failure_probability = ai_prediction['failure_probability']
            reading.failure_type = ai_prediction['failure_type']
        
        # Stocker les données
        await data_manager.store_reading(reading, ai_prediction)
        
        # Créer des alertes si nécessaire
        if reading.status in ['warning', 'critical']:
            severity = reading.status
            message = f"Anomalie détectée: {reading.failure_type or 'Type inconnu'} (Prob: {reading.predicted_failure_probability:.2f})"
            
            if ai_prediction.get('time_to_failure'):
                message += f" - Panne estimée dans {ai_prediction['time_to_failure']}h"
            
            await data_manager.create_alert(
                machine_id=reading.machine_id,
                severity=severity,
                message=message,
                failure_type=reading.failure_type,
                probability=reading.predicted_failure_probability
            )
        
        # Diffuser via WebSocket
        await websocket_manager.broadcast({
            'type': 'sensor_data',
            'machine_id': reading.machine_id,
            'data': reading.dict(),
            'prediction': ai_prediction
        })
        
    except Exception as e:
        logger.error(f"Erreur traitement données capteur: {e}")

async def process_fleet_summary(data: dict):
    """Traite le résumé de flotte"""
    await websocket_manager.broadcast({
        'type': 'fleet_summary',
        'data': data
    })

# ===== ROUTES API =====

@app.get("/")
async def root():
    """Page d'accueil de l'API"""
    return {
        "message": "IoT Predictive Maintenance API",
        "version": "1.0.0",
        "status": "running",
        "mqtt_connected": mqtt_manager.connected,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/machines", response_model=List[MachineStatus])
async def get_machines():
    """Récupère la liste de toutes les machines"""
    machines = []
    for machine_id in data_manager.machines_data.keys():
        status = data_manager.get_machine_status(machine_id)
        if status:
            machines.append(status)
    return machines

@app.get("/machines/{machine_id}", response_model=MachineStatus)
async def get_machine(machine_id: str):
    """Récupère le statut d'une machine spécifique"""
    status = data_manager.get_machine_status(machine_id)
    if not status:
        raise HTTPException(status_code=404, detail="Machine non trouvée")
    return status

@app.get("/fleet/summary", response_model=FleetSummary)
async def get_fleet_summary():
    """Récupère le résumé de la flotte"""
    return data_manager.get_fleet_summary()

@app.get("/alerts", response_model=List[Alert])
async def get_alerts():
    """Récupère toutes les alertes"""
    return data_manager.alerts

@app.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acquitte une alerte"""
    for alert in data_manager.alerts:
        if alert.id == alert_id:
            alert.acknowledged = True
            return {"message": "Alerte acquittée"}
    raise HTTPException(status_code=404, detail="Alerte non trouvée")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket pour données temps réel"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Garder la connexion active
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

@app.get("/health")
async def health_check():
    """Vérification de santé du service"""
    return {
        "status": "healthy",
        "mqtt_connected": mqtt_manager.connected,
        "redis_connected": data_manager.redis_client is not None,
        "active_machines": len(data_manager.machines_data),
        "active_websockets": len(websocket_manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/ai/models/status")
async def get_ai_models_status():
    """Statut des modèles IA"""
    return ai_engine.get_model_status()

@app.post("/ai/predict")
async def predict_machine_failure(reading: SensorReading):
    """Test de prédiction IA sur une lecture donnée"""
    prediction = ai_engine.predict_failure(reading)
    return {
        "reading": reading.dict(),
        "prediction": prediction,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/ai/future/predict")
async def predict_future_trend(
    machine_id: str,
    hours_ahead: int = 2
):
    """Prédiction temporelle future (Phase 2 - Prophet)"""
    # Récupérer la dernière lecture de la machine
    machine_status = data_manager.get_machine_status(machine_id)
    if not machine_status or not machine_status.last_reading:
        raise HTTPException(status_code=404, detail="Machine ou lecture non trouvée")
    
    # Convertir en format pour le moteur IA
    reading_data = {
        'air_temperature': machine_status.last_reading.air_temperature,
        'process_temperature': machine_status.last_reading.process_temperature,
        'rotational_speed': machine_status.last_reading.rotational_speed,
        'torque': machine_status.last_reading.torque,
        'tool_wear': machine_status.last_reading.tool_wear
    }
    
    # Prédiction future
    future_prediction = ai_engine.smart_engine.predict_future_trend(reading_data, hours_ahead)
    
    return {
        "machine_id": machine_id,
        "current_reading": reading_data,
        "future_prediction": future_prediction,
        "timestamp": datetime.now().isoformat()
    }

# Point d'entrée pour le développement
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
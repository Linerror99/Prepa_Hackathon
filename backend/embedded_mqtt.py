"""
Broker MQTT intégré léger pour le développement
Permet de faire fonctionner MQTT sans installation externe
"""

import asyncio
import json
import logging
from typing import Dict, Set, List
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class SimpleMQTTBroker:
    """
    Broker MQTT minimaliste intégré pour le développement
    Gère les topics, souscriptions et publication de messages
    """
    
    def __init__(self, host: str = "localhost", port: int = 1883):
        self.host = host
        self.port = port
        self.clients: Dict[str, Dict] = {}  # client_id -> client_info
        self.subscriptions: Dict[str, Set[str]] = {}  # topic -> set of client_ids
        self.messages: List[Dict] = []  # historique des messages
        self.running = False
        
    async def start(self):
        """Démarre le broker MQTT"""
        try:
            self.running = True
            logger.info(f"🔌 Broker MQTT intégré démarré sur {self.host}:{self.port}")
            
            # Simulation de démarrage
            await asyncio.sleep(0.1)
            
            return True
        except Exception as e:
            logger.error(f"❌ Erreur démarrage broker MQTT: {e}")
            return False
    
    async def stop(self):
        """Arrête le broker MQTT"""
        self.running = False
        logger.info("🛑 Broker MQTT intégré arrêté")
    
    def register_client(self, client_id: str, callback=None):
        """Enregistre un client"""
        self.clients[client_id] = {
            'id': client_id,
            'connected': True,
            'callback': callback,
            'subscriptions': set(),
            'last_seen': datetime.now()
        }
        logger.info(f"📱 Client MQTT enregistré: {client_id}")
    
    def subscribe(self, client_id: str, topic: str):
        """Souscrit un client à un topic"""
        if client_id not in self.clients:
            self.register_client(client_id)
        
        if topic not in self.subscriptions:
            self.subscriptions[topic] = set()
        
        self.subscriptions[topic].add(client_id)
        self.clients[client_id]['subscriptions'].add(topic)
        logger.info(f"📬 Client {client_id} souscrit au topic: {topic}")
    
    async def publish(self, topic: str, payload: str, client_id: str = "system"):
        """Publie un message sur un topic"""
        message = {
            'topic': topic,
            'payload': payload,
            'client_id': client_id,
            'timestamp': datetime.now().isoformat(),
            'message_id': str(uuid.uuid4())
        }
        
        # Ajouter à l'historique
        self.messages.append(message)
        if len(self.messages) > 1000:  # Garder les 1000 derniers
            self.messages = self.messages[-1000:]
        
        # Trouver les clients souscrits
        delivered_count = 0
        for subscription_topic, client_ids in self.subscriptions.items():
            if self._topic_matches(topic, subscription_topic):
                for client_id in client_ids:
                    if client_id in self.clients and self.clients[client_id]['connected']:
                        callback = self.clients[client_id]['callback']
                        if callback:
                            try:
                                await callback(topic, payload)
                                delivered_count += 1
                            except Exception as e:
                                logger.error(f"❌ Erreur callback client {client_id}: {e}")
        
        logger.debug(f"📤 Message publié sur {topic} -> {delivered_count} clients")
        return delivered_count
    
    def _topic_matches(self, published_topic: str, subscription_topic: str) -> bool:
        """Vérifie si un topic publié correspond à une souscription"""
        # Support basique des wildcards MQTT
        if subscription_topic == "#":  # Tout
            return True
        
        if "+" in subscription_topic:  # Single level wildcard
            pub_parts = published_topic.split("/")
            sub_parts = subscription_topic.split("/")
            
            if len(pub_parts) != len(sub_parts):
                return False
            
            for pub_part, sub_part in zip(pub_parts, sub_parts):
                if sub_part != "+" and sub_part != pub_part:
                    return False
            return True
        
        return published_topic == subscription_topic
    
    def get_stats(self) -> Dict:
        """Statistiques du broker"""
        active_clients = sum(1 for c in self.clients.values() if c['connected'])
        
        return {
            'running': self.running,
            'total_clients': len(self.clients),
            'active_clients': active_clients,
            'total_subscriptions': len(self.subscriptions),
            'total_messages': len(self.messages),
            'topics': list(self.subscriptions.keys())
        }
    
    def disconnect_client(self, client_id: str):
        """Déconnecte un client"""
        if client_id in self.clients:
            self.clients[client_id]['connected'] = False
            
            # Supprimer des souscriptions
            for topic in self.clients[client_id]['subscriptions']:
                if topic in self.subscriptions:
                    self.subscriptions[topic].discard(client_id)
                    if not self.subscriptions[topic]:  # Plus de souscripteurs
                        del self.subscriptions[topic]
            
            logger.info(f"📱 Client MQTT déconnecté: {client_id}")

# Instance globale du broker
embedded_broker = SimpleMQTTBroker()

class EmbeddedMQTTClient:
    """Client MQTT qui utilise le broker intégré"""
    
    def __init__(self, client_id: str = None):
        self.client_id = client_id or f"client_{uuid.uuid4().hex[:8]}"
        self.connected = False
        self.message_callback = None
        self.connect_callback = None
        self.disconnect_callback = None
    
    async def connect(self, host: str = "localhost", port: int = 1883):
        """Se connecte au broker intégré"""
        try:
            # Démarrer le broker s'il ne l'est pas
            if not embedded_broker.running:
                await embedded_broker.start()
            
            # Enregistrer ce client
            embedded_broker.register_client(self.client_id, self._on_message_received)
            self.connected = True
            
            if self.connect_callback:
                self.connect_callback(self, None, None, 0)  # rc=0 = succès
            
            logger.info(f"✅ Client MQTT connecté: {self.client_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur connexion MQTT: {e}")
            if self.connect_callback:
                self.connect_callback(self, None, None, 1)  # rc=1 = erreur
            return False
    
    async def disconnect(self):
        """Se déconnecte du broker"""
        if self.connected:
            embedded_broker.disconnect_client(self.client_id)
            self.connected = False
            
            if self.disconnect_callback:
                self.disconnect_callback(self, None, 0)
    
    async def subscribe(self, topic: str):
        """Souscrit à un topic"""
        if self.connected:
            embedded_broker.subscribe(self.client_id, topic)
    
    async def publish(self, topic: str, payload: str):
        """Publie un message"""
        if self.connected:
            return await embedded_broker.publish(topic, payload, self.client_id)
        return 0
    
    async def _on_message_received(self, topic: str, payload: str):
        """Callback interne pour les messages reçus"""
        if self.message_callback:
            # Simuler la structure du message paho-mqtt
            class MockMessage:
                def __init__(self, topic, payload):
                    self.topic = topic
                    self.payload = payload.encode() if isinstance(payload, str) else payload
            
            message = MockMessage(topic, payload)
            self.message_callback(self, None, message)
    
    def on_connect(self, callback):
        """Définit le callback de connexion"""
        self.connect_callback = callback
    
    def on_message(self, callback):
        """Définit le callback de message"""
        self.message_callback = callback
    
    def on_disconnect(self, callback):
        """Définit le callback de déconnexion"""
        self.disconnect_callback = callback

if __name__ == "__main__":
    # Test du broker intégré
    async def test_broker():
        print("🧪 Test du broker MQTT intégré")
        
        # Démarrer le broker
        await embedded_broker.start()
        
        # Créer deux clients
        client1 = EmbeddedMQTTClient("publisher")
        client2 = EmbeddedMQTTClient("subscriber")
        
        # Callback pour les messages reçus
        received_messages = []
        
        def on_message(client, userdata, message):
            msg = message.payload.decode()
            print(f"📨 Message reçu: {message.topic} -> {msg}")
            received_messages.append(msg)
        
        client2.on_message(on_message)
        
        # Connecter les clients
        await client1.connect()
        await client2.connect()
        
        # Souscrire au topic
        await client2.subscribe("test/topic")
        
        # Publier un message
        await client1.publish("test/topic", "Hello MQTT!")
        
        # Attendre un peu
        await asyncio.sleep(0.1)
        
        # Vérifier
        assert len(received_messages) == 1
        assert received_messages[0] == "Hello MQTT!"
        
        print("✅ Test réussi!")
        
        # Stats
        stats = embedded_broker.get_stats()
        print(f"📊 Stats: {stats}")
        
        # Nettoyer
        await client1.disconnect()
        await client2.disconnect()
        await embedded_broker.stop()
    
    # Lancer le test
    asyncio.run(test_broker())
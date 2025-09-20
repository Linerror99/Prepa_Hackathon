#!/usr/bin/env python3
"""
Script de test pour le backend API
Teste toutes les fonctionnalités principales
"""

import asyncio
import aiohttp
import json
import websockets
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackendTester:
    """Testeur pour le backend API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.ws_url = base_url.replace("http", "ws") + "/ws"
    
    async def test_api_endpoints(self):
        """Teste tous les endpoints de l'API"""
        logger.info("🧪 Test des endpoints API")
        
        async with aiohttp.ClientSession() as session:
            
            # Test de santé
            logger.info("Testing /health")
            async with session.get(f"{self.base_url}/health") as resp:
                data = await resp.json()
                logger.info(f"Health: {data}")
            
            # Test racine
            logger.info("Testing /")
            async with session.get(f"{self.base_url}/") as resp:
                data = await resp.json()
                logger.info(f"Root: {data}")
            
            # Test machines
            logger.info("Testing /machines")
            async with session.get(f"{self.base_url}/machines") as resp:
                machines = await resp.json()
                logger.info(f"Machines: {len(machines)} trouvées")
            
            # Test résumé flotte
            logger.info("Testing /fleet/summary")
            async with session.get(f"{self.base_url}/fleet/summary") as resp:
                summary = await resp.json()
                logger.info(f"Fleet summary: {summary}")
            
            # Test alertes
            logger.info("Testing /alerts")
            async with session.get(f"{self.base_url}/alerts") as resp:
                alerts = await resp.json()
                logger.info(f"Alerts: {len(alerts)} trouvées")
    
    async def test_websocket(self, duration: int = 30):
        """Teste la connexion WebSocket"""
        logger.info(f"🔌 Test WebSocket pendant {duration}s")
        
        try:
            async with websockets.connect(self.ws_url) as websocket:
                logger.info("WebSocket connecté")
                
                # Écouter les messages pendant la durée spécifiée
                start_time = asyncio.get_event_loop().time()
                message_count = 0
                
                while (asyncio.get_event_loop().time() - start_time) < duration:
                    try:
                        # Attendre un message avec timeout
                        message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        data = json.loads(message)
                        message_count += 1
                        
                        logger.info(f"Message {message_count}: {data.get('type', 'unknown')} - {data.get('machine_id', 'N/A')}")
                        
                        # Afficher détails pour les messages de capteurs
                        if data.get('type') == 'sensor_data':
                            reading = data.get('data', {})
                            logger.info(f"  Status: {reading.get('status')} - Prob: {reading.get('predicted_failure_probability', 0):.2f}")
                        
                    except asyncio.TimeoutError:
                        logger.info("Aucun message reçu dans les 5 dernières secondes")
                        break
                
                logger.info(f"WebSocket test terminé: {message_count} messages reçus")
                
        except Exception as e:
            logger.error(f"Erreur WebSocket: {e}")
    
    async def run_full_test(self):
        """Lance tous les tests"""
        logger.info("🚀 Démarrage des tests complets du backend")
        
        # Test des endpoints
        await self.test_api_endpoints()
        
        # Attendre un peu
        await asyncio.sleep(2)
        
        # Test WebSocket
        await self.test_websocket(30)
        
        logger.info("✅ Tests terminés")

async def main():
    """Fonction principale"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Testeur du backend API")
    parser.add_argument("--url", default="http://localhost:8000", help="URL du backend")
    parser.add_argument("--ws-duration", type=int, default=30, help="Durée du test WebSocket")
    parser.add_argument("--api-only", action="store_true", help="Tester seulement les API REST")
    
    args = parser.parse_args()
    
    tester = BackendTester(args.url)
    
    if args.api_only:
        await tester.test_api_endpoints()
    else:
        await tester.run_full_test()

if __name__ == "__main__":
    asyncio.run(main())
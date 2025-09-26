#!/usr/bin/env python3
"""
Script de diagnostic pour le pipeline de capteurs industriels
Valide l'intégration Docker et la connectivité
"""

import sys
import os
import subprocess
import json
import time
import requests
from typing import Dict, List, Tuple

def print_header(title: str):
    """Affiche un en-tête formaté"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def print_result(test: str, success: bool, details: str = ""):
    """Affiche le résultat d'un test"""
    status = "✅" if success else "❌"
    print(f"{status} {test}")
    if details:
        print(f"    {details}")

def run_command(cmd: List[str]) -> Tuple[bool, str]:
    """Exécute une commande et retourne le résultat"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)

def check_docker():
    """Vérifie que Docker est disponible"""
    print_header("VÉRIFICATION DOCKER")
    
    # Docker installé ?
    success, output = run_command(["docker", "--version"])
    print_result("Docker installé", success, output.strip() if success else output)
    
    if not success:
        return False
    
    # Docker Compose installé ?
    success, output = run_command(["docker-compose", "--version"])
    print_result("Docker Compose installé", success, output.strip() if success else output)
    
    return success

def check_containers():
    """Vérifie l'état des containers"""
    print_header("ÉTAT DES CONTAINERS")
    
    success, output = run_command(["docker-compose", "ps", "--format", "json"])
    if not success:
        print_result("Lecture état containers", False, output)
        return False
    
    try:
        containers = []
        for line in output.strip().split('\n'):
            if line.strip():
                containers.append(json.loads(line))
        
        expected_services = ["mosquitto", "backend", "dashboard", "sensor-aggregator"]
        running_services = []
        
        for container in containers:
            service = container.get("Service", "")
            state = container.get("State", "")
            health = container.get("Health", "")
            
            is_running = state == "running"
            is_healthy = health in ["healthy", ""] or is_running
            
            print_result(f"Service {service}", is_running and is_healthy, 
                        f"État: {state}, Santé: {health or 'N/A'}")
            
            if is_running:
                running_services.append(service)
        
        # Vérifier les services essentiels
        missing_services = [s for s in expected_services if s not in running_services]
        if missing_services:
            print_result("Services manquants", False, f"{missing_services}")
            return False
        
        return True
        
    except Exception as e:
        print_result("Analyse containers", False, str(e))
        return False

def check_connectivity():
    """Vérifie la connectivité des services"""
    print_header("CONNECTIVITÉ DES SERVICES")
    
    services_to_check = [
        ("Backend API", "http://localhost:8000/health", "GET"),
        ("Dashboard", "http://localhost:8501", "GET"),
        ("MQTT Broker", "localhost:1883", "MQTT")
    ]
    
    all_connected = True
    
    for service_name, endpoint, protocol in services_to_check:
        if protocol == "GET":
            try:
                response = requests.get(endpoint, timeout=10)
                success = response.status_code == 200
                details = f"Status: {response.status_code}" if not success else "OK"
                print_result(f"{service_name} accessible", success, details)
                if not success:
                    all_connected = False
            except Exception as e:
                print_result(f"{service_name} accessible", False, str(e))
                all_connected = False
                
        elif protocol == "MQTT":
            try:
                import paho.mqtt.client as mqtt
                
                def on_connect(client, userdata, flags, rc):
                    client.user_data_set(rc == 0)
                    client.disconnect()
                
                client = mqtt.Client()
                client.on_connect = on_connect
                client.user_data_set(False)
                
                client.connect("localhost", 1883, 10)
                client.loop_start()
                time.sleep(2)
                client.loop_stop()
                
                success = client.user_data_get()
                print_result(f"{service_name} accessible", success)
                if not success:
                    all_connected = False
                    
            except Exception as e:
                print_result(f"{service_name} accessible", False, str(e))
                all_connected = False
    
    return all_connected

def check_sensor_pipeline():
    """Vérifie spécifiquement le pipeline capteurs"""
    print_header("PIPELINE CAPTEURS INDUSTRIELS")
    
    # Vérifier les logs du sensor-aggregator
    success, output = run_command(["docker-compose", "logs", "--tail=20", "sensor-aggregator"])
    
    if success:
        log_checks = [
            ("Démarrage agrégateur", "DÉMARRAGE AGRÉGATEUR CAPTEURS" in output),
            ("Connexion MQTT", "Agrégateur connecté au broker MQTT" in output),
            ("Abonnement topics", "Abonnement topics capteurs activé" in output)
        ]
        
        for check_name, condition in log_checks:
            print_result(check_name, condition)
    else:
        print_result("Lecture logs sensor-aggregator", False, output)
    
    # Test d'envoi de données
    try:
        import paho.mqtt.client as mqtt
        import json
        from datetime import datetime
        
        client = mqtt.Client()
        client.connect("localhost", 1883, 10)
        
        # Envoyer un message de test
        test_message = {
            "timestamp": datetime.now().isoformat() + "Z",
            "value": 25.5,
            "unit": "°C",
            "machine_id": "TEST_DIAGNOSTIC",
            "sensor_type": "temperature"
        }
        
        result = client.publish("sensors/TEST_DIAGNOSTIC/temperature", json.dumps(test_message))
        client.disconnect()
        
        print_result("Envoi message test MQTT", result.rc == 0)
        
    except Exception as e:
        print_result("Test MQTT", False, str(e))

def check_configuration():
    """Vérifie la configuration"""
    print_header("CONFIGURATION")
    
    # Vérifier les fichiers de configuration
    config_files = [
        ("docker-compose.yml", "Configuration Docker principale"),
        ("mosquitto.conf", "Configuration MQTT broker"),
        ("sensor_pipeline/Dockerfile", "Image Docker pipeline"),
        ("sensor_pipeline/requirements.txt", "Dépendances Python")
    ]
    
    for file_path, description in config_files:
        exists = os.path.exists(file_path)
        print_result(description, exists, f"Fichier: {file_path}")

def main():
    """Fonction principale de diagnostic"""
    print("🏭 DIAGNOSTIC PIPELINE CAPTEURS INDUSTRIELS")
    print("=" * 60)
    print("Ce script vérifie l'intégration Docker du pipeline capteurs")
    
    all_checks_passed = True
    
    # Étapes de diagnostic
    checks = [
        ("Docker et Docker Compose", check_docker),
        ("État des containers", check_containers),
        ("Connectivité services", check_connectivity),
        ("Pipeline capteurs", check_sensor_pipeline),
        ("Configuration", check_configuration)
    ]
    
    for check_name, check_function in checks:
        try:
            result = check_function()
            if not result:
                all_checks_passed = False
        except Exception as e:
            print_result(f"Erreur lors de {check_name}", False, str(e))
            all_checks_passed = False
    
    # Résultat final
    print_header("RÉSULTAT FINAL")
    if all_checks_passed:
        print("✅ Tous les diagnostics sont passés avec succès!")
        print("🎯 Le pipeline capteurs industriels est opérationnel.")
    else:
        print("❌ Certains diagnostics ont échoué.")
        print("🔧 Vérifiez les erreurs ci-dessus et corrigez avant de continuer.")
    
    print("\n📋 ACTIONS RECOMMANDÉES:")
    if all_checks_passed:
        print("• Tester l'envoi de vraies données capteurs")
        print("• Vérifier les dashboards pour les nouvelles données")
        print("• Monitorer les performances en production")
    else:
        print("• Corriger les erreurs identifiées")
        print("• Relancer les services manquants")
        print("• Vérifier la configuration réseau Docker")
    
    return 0 if all_checks_passed else 1

if __name__ == "__main__":
    sys.exit(main())
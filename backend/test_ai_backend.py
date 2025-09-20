"""
Script de test pour valider la nouvelle IA ML avec Isolation Forest
"""

import asyncio
import json
import requests
from datetime import datetime
import time

# Configuration
BASE_URL = "http://localhost:8000"

# Données de test - échantillons réalistes
test_samples = [
    {
        "name": "Machine normale",
        "data": {
            "machine_id": "TEST_001",
            "timestamp": datetime.now().isoformat(),
            "air_temperature": 298.0,
            "process_temperature": 308.0,
            "rotational_speed": 1500.0,
            "torque": 38.0,
            "tool_wear": 120.0,
            "product_type": "M",
            "status": "normal"
        }
    },
    {
        "name": "Surchauffe critique",
        "data": {
            "machine_id": "TEST_002", 
            "timestamp": datetime.now().isoformat(),
            "air_temperature": 312.0,  # Très élevée
            "process_temperature": 325.0,  # Très élevée
            "rotational_speed": 1480.0,
            "torque": 42.0,
            "tool_wear": 180.0,
            "product_type": "H",
            "status": "normal"
        }
    },
    {
        "name": "Usure outil excessive",
        "data": {
            "machine_id": "TEST_003",
            "timestamp": datetime.now().isoformat(), 
            "air_temperature": 301.0,
            "process_temperature": 312.0,
            "rotational_speed": 1520.0,
            "torque": 48.0,  # Élevé
            "tool_wear": 260.0,  # Très élevé
            "product_type": "L",
            "status": "normal"
        }
    },
    {
        "name": "Problème puissance",
        "data": {
            "machine_id": "TEST_004",
            "timestamp": datetime.now().isoformat(),
            "air_temperature": 299.0,
            "process_temperature": 309.0,
            "rotational_speed": 1100.0,  # Trop bas
            "torque": 65.0,  # Très élevé
            "tool_wear": 150.0,
            "product_type": "M", 
            "status": "normal"
        }
    },
    {
        "name": "Anomalie multiple",
        "data": {
            "machine_id": "TEST_005",
            "timestamp": datetime.now().isoformat(),
            "air_temperature": 315.0,  # Critique
            "process_temperature": 330.0,  # Critique
            "rotational_speed": 900.0,  # Très bas
            "torque": 70.0,  # Très élevé
            "tool_wear": 280.0,  # Critique
            "product_type": "H",
            "status": "normal"
        }
    }
]

def test_backend_connection():
    """Test de connexion au backend"""
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ Backend connecté")
            return True
        else:
            print(f"❌ Backend erreur: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Impossible de se connecter au backend: {e}")
        return False

def test_ai_models_status():
    """Test du statut des modèles IA"""
    try:
        response = requests.get(f"{BASE_URL}/ai/models/status")
        if response.status_code == 200:
            data = response.json()
            print("🤖 Statut des modèles IA:")
            print(f"  - Détection d'anomalies: {data['anomaly_detection']['available']}")
            print(f"  - Type: {data['anomaly_detection']['model_type']}")
            print(f"  - Prédiction temporelle: {data['time_prediction']['available']}")
            if data['time_prediction']['available']:
                print(f"  - Type: {data['time_prediction']['model_type']}")
            print(f"  - Performance: {data['performance']}")
            return True
        else:
            print(f"❌ Erreur statut IA: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur test IA: {e}")
        return False

def test_ai_predictions():
    """Test des prédictions IA"""
    print("\n🧠 Test des prédictions IA avec Isolation Forest:")
    print("="*60)
    
    for sample in test_samples:
        try:
            print(f"\n📊 Test: {sample['name']}")
            print(f"   Machine ID: {sample['data']['machine_id']}")
            
            # Prédiction IA
            response = requests.post(f"{BASE_URL}/ai/predict", json=sample['data'])
            
            if response.status_code == 200:
                result = response.json()
                prediction = result['prediction']
                
                print(f"   🎯 Statut prédit: {prediction['predicted_status']}")
                print(f"   📈 Probabilité: {prediction['failure_probability']:.3f}")
                print(f"   🔬 Score anomalie: {prediction['model_info']['anomaly_score']:.3f}")
                print(f"   🧩 Type panne: {prediction['failure_type']}")
                print(f"   ⏰ Temps avant panne: {prediction['time_to_failure']}h")
                print(f"   🤖 Modèle: {prediction['model_info']['type']}")
                print(f"   ✅ Confiance: {prediction['confidence']:.2f}")
                
                # Analyser la qualité de la prédiction
                if sample['name'] == "Machine normale" and prediction['predicted_status'] == "normal":
                    print("   ✅ Prédiction CORRECTE (normal détecté)")
                elif sample['name'] != "Machine normale" and prediction['predicted_status'] in ["warning", "critical"]:
                    print("   ✅ Prédiction CORRECTE (anomalie détectée)")
                elif sample['name'] != "Machine normale" and prediction['predicted_status'] == "normal":
                    print("   ⚠️ FAUX NÉGATIF (anomalie non détectée)")
                else:
                    print("   ⚠️ FAUX POSITIF (normal marqué comme anomalie)")
                    
            else:
                print(f"   ❌ Erreur prédiction: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Erreur test {sample['name']}: {e}")

def test_future_predictions():
    """Test des prédictions temporelles (Phase 2)"""
    print("\n🔮 Test des prédictions temporelles avec Prophet:")
    print("="*60)
    
    # D'abord envoyer des données via l'API pour avoir des machines
    sample = test_samples[1]  # Surchauffe
    try:
        # Simuler une lecture de capteur
        response = requests.post(f"{BASE_URL}/ai/predict", json=sample['data'])
        if response.status_code == 200:
            machine_id = sample['data']['machine_id']
            
            # Test prédiction future
            future_response = requests.post(
                f"{BASE_URL}/ai/future/predict",
                params={"machine_id": machine_id, "hours_ahead": 2}
            )
            
            if future_response.status_code == 200:
                future_data = future_response.json()
                print(f"   🚀 Prédiction future pour {machine_id}:")
                print(f"   📅 Horizon: 2 heures")
                
                if future_data['future_prediction']['status'] == 'success':
                    predictions = future_data['future_prediction']['predictions']
                    for feature, pred in predictions.items():
                        print(f"   📊 {feature}:")
                        print(f"      Valeurs futures: {pred['values'][:3]}...")  # 3 premières valeurs
                        if 'time_to_critical' in pred:
                            print(f"      ⚠️ Seuil critique atteint: {pred['time_to_critical']}")
                    print("   ✅ Prédiction temporelle réussie")
                else:
                    print(f"   ⚠️ Prédiction temporelle: {future_data['future_prediction']['reason']}")
            else:
                print(f"   ❌ Erreur prédiction future: {future_response.status_code}")
        
    except Exception as e:
        print(f"   ❌ Erreur test prédiction future: {e}")

def generate_performance_report():
    """Génère un rapport de performance"""
    print("\n📈 Rapport de Performance IA:")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/ai/models/status")
        if response.status_code == 200:
            data = response.json()
            performance = data['performance']
            
            print(f"📊 Statistiques globales:")
            print(f"   - Total prédictions: {performance.get('total_predictions', 0)}")
            print(f"   - Anomalies détectées: {performance.get('anomalies_detected', 0)}")
            print(f"   - Taux de détection: {performance.get('anomalies_detected', 0) / max(performance.get('total_predictions', 1), 1) * 100:.1f}%")
            print(f"   - Précision modèle: {performance.get('accuracy_score', 0):.3f}")
            print(f"   - Dernier entraînement: {performance.get('last_training', 'Jamais')}")
            
            # Recommandations
            print(f"\n🎯 Recommandations:")
            if performance.get('accuracy_score', 0) > 0.8:
                print("   ✅ Précision excellente - Modèle prêt pour production")
            elif performance.get('accuracy_score', 0) > 0.6:
                print("   ⚠️ Précision correcte - Envisager ré-entraînement avec plus de données")
            else:
                print("   ❌ Précision faible - Ré-entraînement nécessaire")
                
    except Exception as e:
        print(f"❌ Erreur génération rapport: {e}")

def main():
    """Test principal"""
    print("🚀 Test du Backend IoT avec IA ML")
    print("="*60)
    
    # Tests séquentiels
    if not test_backend_connection():
        print("❌ Backend non accessible - Arrêt des tests")
        return
    
    print()
    if not test_ai_models_status():
        print("❌ Modèles IA non disponibles")
        return
    
    # Tests des prédictions
    test_ai_predictions()
    
    # Tests des prédictions futures
    test_future_predictions()
    
    # Rapport de performance
    generate_performance_report()
    
    print("\n🎉 Tests terminés!")
    print("\n💡 Commandes utiles:")
    print("   - Démarrer backend: python main.py")
    print("   - Tests API: python test_ai_backend.py")
    print("   - Documentation: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
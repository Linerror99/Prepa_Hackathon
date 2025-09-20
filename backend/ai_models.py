"""
Modèles IA pour la maintenance prédictive - Isolation Forest + Prophet
Phase 1: Détection d'anomalies en temps réel
Phase 2: Prédiction temporelle des pannes futures
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Any, Tuple
import pickle
import os
from pathlib import Path

# Phase 1: Détection d'anomalies
from pyod.models.iforest import IForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# Phase 2: Prédiction temporelle (future)
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logging.warning("Prophet non disponible - Phase 2 désactivée")

logger = logging.getLogger(__name__)

class SmartPredictiveEngine:
    """
    Moteur IA intelligent combinant détection d'anomalies et prédiction temporelle
    
    Phase 1 (MVP): Isolation Forest pour détecter les anomalies immédiatement
    Phase 2 (Avancé): Prophet pour prédire les pannes futures dans le temps
    """
    
    def __init__(self, data_path: str = "../data"):
        self.data_path = Path(data_path)
        self.models_path = self.data_path / "models"
        self.models_path.mkdir(exist_ok=True)
        
        # Phase 1: Détection d'anomalies
        self.anomaly_detectors = {}  # Un détecteur par type de panne
        self.scalers = {}
        self.feature_columns = [
            'air_temperature', 'process_temperature', 'rotational_speed', 
            'torque', 'tool_wear'
        ]
        
        # Phase 2: Prédiction temporelle
        self.time_predictors = {}
        self.prophet_available = PROPHET_AVAILABLE
        
        # Métriques de performance
        self.performance_metrics = {
            'total_predictions': 0,
            'anomalies_detected': 0,
            'accuracy_score': 0.0,
            'last_training': None
        }
        
        logger.info("🤖 SmartPredictiveEngine initialisé")
        
        # Charger les modèles existants ou entraîner
        self._load_or_train_models()
    
    def _load_or_train_models(self):
        """Charge les modèles existants ou les entraîne si nécessaire"""
        try:
            self._load_models()
            logger.info("✅ Modèles ML chargés depuis le cache")
        except Exception as e:
            logger.info(f"❌ Impossible de charger les modèles: {e}")
            logger.info("🔄 Entraînement des nouveaux modèles...")
            self._train_models()
    
    def _load_training_data(self) -> pd.DataFrame:
        """Charge les données d'entraînement depuis le dataset UCI"""
        try:
            # Essayer de charger le vrai dataset UCI
            data_file = self.data_path / "processed_failures.csv"
            if data_file.exists():
                df = pd.read_csv(data_file)
                logger.info(f"📊 Dataset UCI chargé: {len(df)} échantillons")
                return df
            else:
                # Générer des données synthétiques basées sur UCI pour l'entraînement
                logger.info("🔄 Génération de données d'entraînement synthétiques...")
                return self._generate_synthetic_training_data()
                
        except Exception as e:
            logger.error(f"Erreur chargement données: {e}")
            return self._generate_synthetic_training_data()
    
    def _generate_synthetic_training_data(self) -> pd.DataFrame:
        """Génère des données synthétiques réalistes pour l'entraînement"""
        np.random.seed(42)
        n_samples = 5000
        
        # Données normales (80%)
        n_normal = int(n_samples * 0.8)
        normal_data = {
            'air_temperature': np.random.normal(300, 2, n_normal),
            'process_temperature': np.random.normal(310, 8, n_normal),
            'rotational_speed': np.random.normal(1500, 100, n_normal),
            'torque': np.random.normal(40, 10, n_normal),
            'tool_wear': np.random.exponential(100, n_normal),
            'failure': [0] * n_normal
        }
        
        # Données avec pannes (20%)
        n_failure = n_samples - n_normal
        
        # TWF - Tool Wear Failure
        n_twf = n_failure // 5
        twf_data = {
            'air_temperature': np.random.normal(300, 3, n_twf),
            'process_temperature': np.random.normal(310, 10, n_twf),
            'rotational_speed': np.random.normal(1500, 120, n_twf),
            'torque': np.random.normal(50, 15, n_twf),  # Couple élevé
            'tool_wear': np.random.normal(250, 50, n_twf),  # Usure excessive
            'failure': [1] * n_twf
        }
        
        # HDF - Heat Dissipation Failure  
        n_hdf = n_failure // 5
        hdf_data = {
            'air_temperature': np.random.normal(310, 5, n_hdf),  # Surchauffe
            'process_temperature': np.random.normal(320, 15, n_hdf),  # Surchauffe process
            'rotational_speed': np.random.normal(1500, 100, n_hdf),
            'torque': np.random.normal(40, 10, n_hdf),
            'tool_wear': np.random.exponential(120, n_hdf),
            'failure': [1] * n_hdf
        }
        
        # PWF - Power Failure
        n_pwf = n_failure // 5
        pwf_data = {
            'air_temperature': np.random.normal(300, 2, n_pwf),
            'process_temperature': np.random.normal(310, 8, n_pwf),
            'rotational_speed': np.random.normal(1200, 200, n_pwf),  # Vitesse anormale
            'torque': np.random.normal(60, 20, n_pwf),  # Couple excessif
            'tool_wear': np.random.exponential(100, n_pwf),
            'failure': [1] * n_pwf
        }
        
        # OSF - Overstrain Failure
        n_osf = n_failure // 5
        osf_data = {
            'air_temperature': np.random.normal(300, 3, n_osf),
            'process_temperature': np.random.normal(315, 12, n_osf),
            'rotational_speed': np.random.normal(1500, 100, n_osf),
            'torque': np.random.normal(55, 18, n_osf),  # Surcontrainte
            'tool_wear': np.random.normal(200, 60, n_osf),  # Usure accélérée
            'failure': [1] * n_osf
        }
        
        # RNF - Random Failure (reste)
        n_rnf = n_failure - n_twf - n_hdf - n_pwf - n_osf
        rnf_data = {
            'air_temperature': np.random.normal(300, 3, n_rnf),
            'process_temperature': np.random.normal(310, 10, n_rnf),
            'rotational_speed': np.random.normal(1500, 150, n_rnf),
            'torque': np.random.normal(40, 15, n_rnf),
            'tool_wear': np.random.exponential(150, n_rnf),
            'failure': [1] * n_rnf
        }
        
        # Combiner toutes les données
        all_data = {}
        for key in normal_data.keys():
            all_data[key] = np.concatenate([
                normal_data[key], twf_data[key], hdf_data[key], 
                pwf_data[key], osf_data[key], rnf_data[key]
            ])
        
        df = pd.DataFrame(all_data)
        
        # Ajouter timestamp pour Prophet
        base_time = datetime.now() - timedelta(days=30)
        df['timestamp'] = [base_time + timedelta(minutes=i*10) for i in range(len(df))]
        
        logger.info(f"✅ Généré {len(df)} échantillons d'entraînement ({df['failure'].sum()} pannes)")
        return df
    
    def _train_models(self):
        """Entraîne les modèles de détection d'anomalies"""
        try:
            # Charger les données d'entraînement
            df = self._load_training_data()
            
            # Préparer les features
            features = df[self.feature_columns].values
            labels = df['failure'].values if 'failure' in df.columns else None
            
            # Phase 1: Entraîner Isolation Forest
            logger.info("🔄 Entraînement Isolation Forest...")
            
            # Normalisation des données
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
            
            # Isolation Forest (détection d'anomalies non supervisée)
            detector = IForest(
                contamination=0.1,  # 10% d'anomalies attendues
                random_state=42,
                n_estimators=100
            )
            detector.fit(features_scaled)
            
            # Sauvegarder les modèles
            self.anomaly_detectors['global'] = detector
            self.scalers['global'] = scaler
            
            # Évaluer la performance si on a des labels
            if labels is not None:
                predictions = detector.predict(features_scaled)
                # IForest retourne 1 pour normal, -1 pour anomalie
                # Convertir en 0 pour normal, 1 pour anomalie
                predictions_binary = [1 if p == -1 else 0 for p in predictions]
                accuracy = np.mean(predictions_binary == labels)
                self.performance_metrics['accuracy_score'] = accuracy
                logger.info(f"📊 Précision Isolation Forest: {accuracy:.3f}")
            
            # Phase 2: Préparer Prophet (si disponible)
            if self.prophet_available and 'timestamp' in df.columns:
                logger.info("🔄 Préparation modèles Prophet...")
                self._train_prophet_models(df)
            
            # Sauvegarder les modèles
            self._save_models()
            self.performance_metrics['last_training'] = datetime.now().isoformat()
            
            logger.info("✅ Entraînement des modèles ML terminé")
            
        except Exception as e:
            logger.error(f"❌ Erreur entraînement modèles: {e}")
            # Fallback vers les règles expertes en cas d'échec
            logger.info("🔄 Fallback vers moteur de règles...")
    
    def _train_prophet_models(self, df: pd.DataFrame):
        """Entraîne les modèles Prophet pour la prédiction temporelle"""
        try:
            # Créer des séries temporelles pour chaque métrique
            for feature in self.feature_columns:
                if feature in df.columns:
                    # Préparer les données pour Prophet (format spécifique)
                    prophet_df = pd.DataFrame({
                        'ds': df['timestamp'],
                        'y': df[feature]
                    })
                    
                    # Créer et entraîner le modèle Prophet
                    model = Prophet(
                        daily_seasonality=False,
                        weekly_seasonality=False,
                        yearly_seasonality=False,
                        changepoint_prior_scale=0.05
                    )
                    model.fit(prophet_df)
                    
                    self.time_predictors[feature] = model
                    logger.info(f"✅ Prophet entraîné pour {feature}")
                    
        except Exception as e:
            logger.error(f"❌ Erreur entraînement Prophet: {e}")
    
    def _save_models(self):
        """Sauvegarde les modèles entraînés"""
        try:
            # Sauvegarder Isolation Forest
            model_file = self.models_path / "isolation_forest.pkl"
            with open(model_file, 'wb') as f:
                pickle.dump({
                    'detectors': self.anomaly_detectors,
                    'scalers': self.scalers,
                    'metrics': self.performance_metrics
                }, f)
            
            # Sauvegarder Prophet
            if self.time_predictors:
                prophet_file = self.models_path / "prophet_models.pkl"
                with open(prophet_file, 'wb') as f:
                    pickle.dump(self.time_predictors, f)
            
            logger.info("💾 Modèles sauvegardés")
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde: {e}")
    
    def _load_models(self):
        """Charge les modèles pré-entraînés"""
        # Charger Isolation Forest
        model_file = self.models_path / "isolation_forest.pkl"
        if model_file.exists():
            with open(model_file, 'rb') as f:
                data = pickle.load(f)
                self.anomaly_detectors = data['detectors']
                self.scalers = data['scalers']
                self.performance_metrics = data.get('metrics', {})
        
        # Charger Prophet
        prophet_file = self.models_path / "prophet_models.pkl"
        if prophet_file.exists() and self.prophet_available:
            with open(prophet_file, 'rb') as f:
                self.time_predictors = pickle.load(f)
    
    def predict_anomaly(self, reading_data: Dict[str, float]) -> Dict[str, Any]:
        """
        Phase 1: Détection d'anomalie en temps réel avec Isolation Forest
        
        Args:
            reading_data: Dictionnaire avec les valeurs des capteurs
            
        Returns:
            Dictionnaire avec le score d'anomalie et la classification
        """
        try:
            # Extraire les features
            features = [reading_data.get(col, 0.0) for col in self.feature_columns]
            features_array = np.array(features).reshape(1, -1)
            
            # Normaliser
            if 'global' in self.scalers:
                features_scaled = self.scalers['global'].transform(features_array)
            else:
                features_scaled = features_array
            
            # Prédiction avec Isolation Forest
            if 'global' in self.anomaly_detectors:
                detector = self.anomaly_detectors['global']
                
                # Score d'anomalie (plus négatif = plus anormal)
                anomaly_score = detector.decision_function(features_scaled)[0]
                
                # Prédiction binaire (1 = normal, -1 = anomalie)
                is_anomaly = detector.predict(features_scaled)[0] == -1
                
                # Convertir le score en probabilité [0,1]
                # Score négatif → haute probabilité d'anomalie
                probability = max(0, min(1, (-anomaly_score + 0.5) / 2))
                
                # Classification basée sur le score
                if anomaly_score < -0.6:
                    status = "critical"
                    confidence = 0.95
                elif anomaly_score < -0.3:
                    status = "warning"
                    confidence = 0.85
                elif anomaly_score < -0.1:
                    status = "alert"
                    confidence = 0.75
                else:
                    status = "normal"
                    confidence = 0.90
                
                # Estimer le type de panne probable
                failure_type = self._classify_failure_type(reading_data, anomaly_score)
                
                self.performance_metrics['total_predictions'] += 1
                if is_anomaly:
                    self.performance_metrics['anomalies_detected'] += 1
                
                return {
                    'predicted_status': status,
                    'failure_probability': probability,
                    'anomaly_score': float(anomaly_score),
                    'is_anomaly': is_anomaly,
                    'failure_type': failure_type,
                    'confidence': confidence,
                    'model_type': 'IsolationForest',
                    'time_to_failure': self._estimate_time_to_failure(probability, failure_type)
                }
            
            else:
                # Fallback vers les règles expertes
                return self._rule_based_prediction(reading_data)
                
        except Exception as e:
            logger.error(f"❌ Erreur prédiction: {e}")
            return self._rule_based_prediction(reading_data)
    
    def _classify_failure_type(self, reading_data: Dict[str, float], anomaly_score: float) -> Optional[str]:
        """Classifie le type de panne probable basé sur les valeurs"""
        if anomaly_score > -0.3:  # Pas assez anormal
            return None
            
        # Analyser les déviations par rapport aux valeurs normales
        air_temp = reading_data.get('air_temperature', 300)
        process_temp = reading_data.get('process_temperature', 310)
        speed = reading_data.get('rotational_speed', 1500)
        torque = reading_data.get('torque', 40)
        wear = reading_data.get('tool_wear', 100)
        
        # Scores pour chaque type de panne
        scores = {}
        
        # TWF - Tool Wear Failure
        scores['TWF'] = 0
        if wear > 200: scores['TWF'] += 3
        if torque > 45: scores['TWF'] += 2
        if wear > 250: scores['TWF'] += 2
        
        # HDF - Heat Dissipation Failure
        scores['HDF'] = 0
        if air_temp > 305: scores['HDF'] += 3
        if process_temp > 315: scores['HDF'] += 3
        if process_temp - air_temp > 20: scores['HDF'] += 2
        
        # PWF - Power Failure
        scores['PWF'] = 0
        if torque > 55: scores['PWF'] += 3
        if speed < 1200 or speed > 1800: scores['PWF'] += 2
        power = torque * speed
        if power > 75000 or power < 30000: scores['PWF'] += 2
        
        # OSF - Overstrain Failure
        scores['OSF'] = 0
        if torque > 50: scores['OSF'] += 2
        if wear > 180: scores['OSF'] += 2
        if torque > 55 and wear > 200: scores['OSF'] += 3
        
        # Retourner le type avec le score le plus élevé
        if max(scores.values()) >= 3:
            return max(scores.keys(), key=lambda k: scores[k])
        
        return 'RNF'  # Random failure si rien de spécifique
    
    def predict_future_trend(self, reading_data: Dict[str, float], 
                           hours_ahead: int = 2) -> Dict[str, Any]:
        """
        Phase 2: Prédiction temporelle avec Prophet
        
        Args:
            reading_data: Données actuelles des capteurs
            hours_ahead: Nombre d'heures à prédire dans le futur
            
        Returns:
            Prédictions temporelles pour chaque métrique
        """
        if not self.prophet_available or not self.time_predictors:
            logger.warning("⚠️ Prophet non disponible - prédiction temporelle désactivée")
            return {'status': 'unavailable', 'reason': 'Prophet not available'}
        
        try:
            predictions = {}
            current_time = datetime.now()
            
            for feature, model in self.time_predictors.items():
                # Créer les timestamps futurs
                future_times = [
                    current_time + timedelta(minutes=15*i) 
                    for i in range(1, hours_ahead*4 + 1)  # Toutes les 15 min
                ]
                
                future_df = pd.DataFrame({
                    'ds': future_times
                })
                
                # Prédiction avec Prophet
                forecast = model.predict(future_df)
                
                # Extraire les prédictions
                predictions[feature] = {
                    'timestamps': [t.isoformat() for t in future_times],
                    'values': forecast['yhat'].tolist(),
                    'lower_bound': forecast['yhat_lower'].tolist(),
                    'upper_bound': forecast['yhat_upper'].tolist()
                }
                
                # Détecter les tendances critiques
                current_value = reading_data.get(feature, 0)
                future_values = forecast['yhat'].tolist()
                
                # Analyser la tendance
                if feature in ['air_temperature', 'process_temperature']:
                    critical_threshold = 320 if 'process' in feature else 310
                    time_to_critical = self._find_time_to_threshold(
                        future_times, future_values, critical_threshold, current_value
                    )
                    if time_to_critical:
                        predictions[feature]['time_to_critical'] = time_to_critical
                
            return {
                'status': 'success',
                'predictions': predictions,
                'model_type': 'Prophet',
                'prediction_horizon_hours': hours_ahead
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur prédiction temporelle: {e}")
            return {'status': 'error', 'reason': str(e)}
    
    def _find_time_to_threshold(self, timestamps: List[datetime], 
                               values: List[float], threshold: float, 
                               current_value: float) -> Optional[str]:
        """Trouve quand une valeur atteindra un seuil critique"""
        for i, (time, value) in enumerate(zip(timestamps, values)):
            if value >= threshold and current_value < threshold:
                return time.isoformat()
        return None
    
    def _estimate_time_to_failure(self, probability: float, failure_type: Optional[str]) -> Optional[int]:
        """Estime le temps avant panne basé sur la probabilité d'anomalie"""
        if probability < 0.5:
            return None
        
        # Temps de base par type de panne (en heures)
        base_times = {
            'TWF': 72,  # Usure outil
            'HDF': 24,  # Surchauffe
            'PWF': 48,  # Puissance
            'OSF': 12,  # Surcontrainte
            'RNF': 168  # Aléatoire
        }
        
        base_time = base_times.get(failure_type, 48)
        
        # Plus la probabilité est élevée, moins il reste de temps
        time_remaining = base_time * (1 - probability) * 0.8
        return max(int(time_remaining), 1)
    
    def _rule_based_prediction(self, reading_data: Dict[str, float]) -> Dict[str, Any]:
        """Fallback vers les règles expertes si ML échoue"""
        # Implémentation simplifiée des règles expertes
        air_temp = reading_data.get('air_temperature', 300)
        process_temp = reading_data.get('process_temperature', 310)
        torque = reading_data.get('torque', 40)
        wear = reading_data.get('tool_wear', 100)
        
        score = 0.0
        failure_type = None
        
        # Règles simples
        if wear > 200: 
            score += 0.4
            failure_type = 'TWF'
        if air_temp > 305:
            score += 0.3
            failure_type = 'HDF'
        if torque > 50:
            score += 0.3
            failure_type = 'OSF'
        
        status = 'critical' if score > 0.8 else ('warning' if score > 0.5 else 'normal')
        
        return {
            'predicted_status': status,
            'failure_probability': score,
            'anomaly_score': -score,  # Simuler un score d'anomalie
            'is_anomaly': score > 0.5,
            'failure_type': failure_type,
            'confidence': 0.7,
            'model_type': 'RuleBased',
            'time_to_failure': self._estimate_time_to_failure(score, failure_type)
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Retourne les informations sur les modèles chargés"""
        return {
            'anomaly_detection': {
                'model_type': 'IsolationForest',
                'available': 'global' in self.anomaly_detectors,
                'features': self.feature_columns
            },
            'time_prediction': {
                'model_type': 'Prophet',
                'available': bool(self.time_predictors) and self.prophet_available,
                'features': list(self.time_predictors.keys()) if self.time_predictors else []
            },
            'performance': self.performance_metrics,
            'last_training': self.performance_metrics.get('last_training', 'Never')
        }
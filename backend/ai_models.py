"""
Modèles IA pour la maintenance prédictive - ML réel + Simulation
Phase 1: Détection d'anomalies en temps réel
Phase 2: Prédiction temporelle des pannes futures
Phase 3: ML temps réel avec TSForecaster (NEW!)
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

# Phase 3: ML temps réel (NEW!)
try:
    from ml.forecast_inference import TSForecaster, create_forecaster
    ML_FORECASTER_AVAILABLE = True
except ImportError:
    ML_FORECASTER_AVAILABLE = False
    logging.warning("TSForecaster non disponible - ML temps réel désactivé")

logger = logging.getLogger(__name__)

class SmartPredictiveEngine:
    """
    Moteur IA intelligent combinant détection d'anomalies et prédiction temporelle
    
    Phase 1 (MVP): Isolation Forest pour détecter les anomalies immédiatement
    Phase 2 (Avancé): Prophet pour prédire les pannes futures dans le temps
    """
    
    def __init__(self, data_path: str = "data"):
        self.data_path = Path(data_path)
        self.models_path = self.data_path / "models"
        self.models_path.mkdir(parents=True, exist_ok=True)
        
        # Phase 1: Détection d'anomalies industrielles
        self.anomaly_detectors = {}  # Un détecteur par type de panne
        self.scalers = {}
        self.feature_columns = [
            'temperature',    # °C - température des équipements
            'pressure',       # bar - pression système
            'velocity'        # m/s - vitesse des composants
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
        """Génère des données synthétiques industrielles réalistes pour l'entraînement"""
        np.random.seed(42)
        n_samples = 5000
        
        # Données normales (85% - équipements industriels plus fiables)
        n_normal = int(n_samples * 0.85)
        normal_data = {
            'temperature': np.random.normal(30.0, 3.0, n_normal),      # 30°C ±3°C normale
            'pressure': np.random.normal(3.0, 0.5, n_normal),          # 3 bar ±0.5 normale  
            'velocity': np.random.normal(1.5, 0.3, n_normal),          # 1.5 m/s ±0.3 normale
            'failure': [0] * n_normal
        }
        
        # Données avec pannes (15% - pannes industrielles réalistes)
        n_failure = n_samples - n_normal
        
        # OVERHEATING - Surchauffe des équipements
        n_overheating = n_failure // 4
        overheating_data = {
            'temperature': np.random.normal(65.0, 8.0, n_overheating),   # Surchauffe critique
            'pressure': np.random.normal(3.2, 0.6, n_overheating),       # Pression légèrement élevée
            'velocity': np.random.normal(1.3, 0.4, n_overheating),       # Vitesse réduite par surchauffe
            'failure': [1] * n_overheating
        }
        
        # PRESSURE_LOSS - Perte de pression système
        n_pressure_loss = n_failure // 4
        pressure_loss_data = {
            'temperature': np.random.normal(32.0, 4.0, n_pressure_loss),  # Température normale
            'pressure': np.random.normal(0.8, 0.3, n_pressure_loss),      # Pression critique basse
            'velocity': np.random.normal(0.3, 0.2, n_pressure_loss),      # Vitesse très réduite
            'failure': [1] * n_pressure_loss
        }
        
        # MECHANICAL_WEAR - Usure mécanique excessive
        n_mechanical_wear = n_failure // 4
        mechanical_wear_data = {
            'temperature': np.random.normal(45.0, 6.0, n_mechanical_wear), # Température élevée par friction
            'pressure': np.random.normal(2.1, 0.4, n_mechanical_wear),     # Pression faible
            'velocity': np.random.normal(0.2, 0.1, n_mechanical_wear),     # Vitesse très faible
            'failure': [1] * n_mechanical_wear
        }
        
        # VIBRATION_EXCESS - Vibrations excessives
        n_vibration = n_failure - n_overheating - n_pressure_loss - n_mechanical_wear
        vibration_data = {
            'temperature': np.random.normal(42.0, 5.0, n_vibration),       # Température élevée par vibrations
            'pressure': np.random.normal(6.2, 1.0, n_vibration),           # Pression excessive
            'velocity': np.random.normal(4.5, 0.8, n_vibration),           # Vitesse excessive
            'failure': [1] * n_vibration
        }
        
        # Combiner toutes les données industrielles
        all_data = {}
        for key in normal_data.keys():
            all_data[key] = np.concatenate([
                normal_data[key], overheating_data[key], pressure_loss_data[key], 
                mechanical_wear_data[key], vibration_data[key]
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
                
                # Vérifier la compatibilité des scalers avec les nouvelles features
                scalers = data['scalers']
                expected_features = len(self.feature_columns)
                
                # Tester la compatibilité avec un échantillon
                if scalers and 'general' in scalers:
                    test_scaler = scalers['general']
                    if hasattr(test_scaler, 'n_features_in_'):
                        actual_features = test_scaler.n_features_in_
                        if actual_features != expected_features:
                            logger.warning(f"⚠️ Incompatibilité détectée: scaler attend {actual_features} features, mais nous en avons {expected_features}")
                            logger.info("🔄 Suppression des anciens modèles et réentraînement...")
                            # Supprimer le fichier incompatible
                            model_file.unlink()
                            raise ValueError("Modèles incompatibles - réentraînement nécessaire")
                
                self.anomaly_detectors = data['detectors']
                self.scalers = scalers
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
        """Classifie le type de panne industrielle probable basé sur les valeurs des capteurs"""
        if anomaly_score > -0.3:  # Pas assez anormal
            return None
            
        # Analyser les déviations par rapport aux valeurs normales industrielles
        temperature = reading_data.get('temperature', 30.0)
        pressure = reading_data.get('pressure', 3.0)
        velocity = reading_data.get('velocity', 1.5)
        
        # Scores pour chaque type de panne industrielle
        scores = {}
        
        # OVERHEATING - Surchauffe des équipements
        scores['OVERHEATING'] = 0
        if temperature > 50: scores['OVERHEATING'] += 4
        if temperature > 60: scores['OVERHEATING'] += 3
        if velocity < 1.0: scores['OVERHEATING'] += 2  # Performance réduite par chaleur
        
        # PRESSURE_LOSS - Perte de pression système
        scores['PRESSURE_LOSS'] = 0
        if pressure < 1.5: scores['PRESSURE_LOSS'] += 4
        if pressure < 1.0: scores['PRESSURE_LOSS'] += 3
        if velocity < 0.5: scores['PRESSURE_LOSS'] += 2  # Performance réduite par manque de pression
        
        # MECHANICAL_WEAR - Usure mécanique excessive
        scores['MECHANICAL_WEAR'] = 0
        if velocity < 0.5: scores['MECHANICAL_WEAR'] += 4
        if temperature > 40: scores['MECHANICAL_WEAR'] += 2  # Friction génère chaleur
        if pressure < 2.0: scores['MECHANICAL_WEAR'] += 2   # Performance dégradée
        
        # VIBRATION_EXCESS - Vibrations excessives
        scores['VIBRATION_EXCESS'] = 0
        if velocity > 4.0: scores['VIBRATION_EXCESS'] += 4
        if pressure > 6.0: scores['VIBRATION_EXCESS'] += 3
        if temperature > 40: scores['VIBRATION_EXCESS'] += 2  # Surchauffe par vibrations
        
        # Retourner le type industriel avec le score le plus élevé
        if max(scores.values()) >= 3:
            return max(scores.keys(), key=lambda k: scores[k])
        
        return 'SYSTEM_DEGRADATION'  # Dégradation générale si rien de spécifique
    
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
        """Fallback vers les règles expertes industrielles si ML échoue"""
        # Implémentation simplifiée des règles expertes industrielles
        temperature = reading_data.get('temperature', 30.0)
        pressure = reading_data.get('pressure', 3.0)
        velocity = reading_data.get('velocity', 1.5)
        
        score = 0.0
        failure_type = None
        
        # Règles expertes industrielles
        if temperature > 60: 
            score += 0.5
            failure_type = 'OVERHEATING'
        elif temperature > 45:
            score += 0.3
            failure_type = 'OVERHEATING'
            
        if pressure < 1.0:
            score += 0.4
            failure_type = 'PRESSURE_LOSS'
        elif pressure > 7.0:
            score += 0.3
            failure_type = 'VIBRATION_EXCESS'
            
        if velocity < 0.3:
            score += 0.4
            failure_type = 'MECHANICAL_WEAR'
        elif velocity > 4.5:
            score += 0.3
            failure_type = 'VIBRATION_EXCESS'
        
        status = 'critical' if score > 0.7 else ('warning' if score > 0.4 else ('alert' if score > 0.15 else 'normal'))
        
        return {
            'predicted_status': status,
            'failure_probability': min(score, 1.0),
            'anomaly_score': -score,  # Simuler un score d'anomalie
            'is_anomaly': score > 0.4,
            'failure_type': failure_type,
            'confidence': 0.7,
            'model_type': 'RuleBased_Industrial',
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


# ============================================================================
# NOUVELLE CLASSE ML ENGINE - UTILISE VOTRE VRAI MODÈLE ML
# ============================================================================

class MLPredictiveEngine:
    """
    Moteur ML utilisant le vrai modèle TSForecaster entraîné sur vos données client
    
    Remplace SmartPredictiveEngine pour les machines avec vraie ML
    - Prédictions temps réel avec GradientBoosting
    - Détection d'anomalies avec IsolationForest 
    - Features engineering avancé (lags + rolling stats)
    """
    
    def __init__(self, machine_id: str = "MACHINE_01"):
        self.machine_id = machine_id
        self.forecaster = None
        self.initialization_status = "not_started"
        
        # Métriques de performance (initialiser AVANT _initialize_forecaster)
        self.performance_metrics = {
            'total_predictions': 0,
            'anomalies_detected': 0,
            'model_accuracy': 0.0,
            'last_prediction': None
        }
        
        logger.info(f"🚀 Initialisation MLPredictiveEngine pour {machine_id}")
        
        # Initialiser le forecaster
        self._initialize_forecaster()
    
    def _initialize_forecaster(self):
        """Initialise le TSForecaster avec gestion d'erreurs"""
        try:
            if ML_FORECASTER_AVAILABLE:
                self.forecaster = create_forecaster("ml/models")
                if self.forecaster:
                    self.initialization_status = "success"
                    model_info = self.forecaster.get_model_info()
                    logger.info(f"✅ MLPredictiveEngine initialisé:")
                    logger.info(f"   - Modèle: {model_info.get('performance', {}).get('model_type', 'Unknown')}")
                    logger.info(f"   - R² Test: {model_info.get('performance', {}).get('test', {}).get('r2', 'N/A')}")
                    logger.info(f"   - Features: {model_info.get('n_features', 'N/A')}")
                    
                    # Mise à jour des métriques
                    perf = model_info.get('performance', {}).get('test', {})
                    self.performance_metrics['model_accuracy'] = perf.get('r2', 0.0)
                else:
                    raise Exception("create_forecaster returned None")
            else:
                raise Exception("ML_FORECASTER_AVAILABLE is False")
                
        except Exception as e:
            logger.error(f"❌ Erreur initialisation MLPredictiveEngine: {e}")
            logger.info("🔄 Fallback vers simulation pour cette machine")
            self.initialization_status = "failed"
            self.forecaster = None
    
    def predict_anomaly(self, reading_data: Dict[str, float]) -> Dict[str, Any]:
        """
        Prédiction d'anomalie avec le vrai modèle ML
        
        Args:
            reading_data: {"temperature": float, "pression": float, "vitesse": float}
            
        Returns:
            Résultat de prédiction avec score d'anomalie ML
        """
        try:
            if not self.forecaster:
                return self._fallback_prediction(reading_data, "forecaster_not_available")
            
            # Conversion des noms de colonnes
            ml_data = {
                'temperature': reading_data.get('temperature', 25.0),
                'pression': reading_data.get('pressure', 3.0),  # pressure -> pression
                'vitesse': reading_data.get('velocity', 1.5) * 1000  # velocity -> vitesse (RPM)
            }
            
            # Prédiction ML
            result = self.forecaster.predict(ml_data)
            
            if not result.get('ok', False):
                reason = result.get('reason', 'unknown_error')
                logger.warning(f"⚠️ ML prediction failed: {reason}")
                return self._fallback_prediction(reading_data, reason)
            
            # Extraire les résultats ML
            predictions = result.get('predictions', {})
            anomaly_info = result.get('anomaly', {})
            confidence_info = result.get('confidence', {})
            
            # Score d'anomalie du modèle ML
            anomaly_score = anomaly_info.get('score', 0.0)
            is_anomaly = anomaly_info.get('is_anomaly', False)
            
            # Convertir le score ML en probabilité de panne [0,1]
            # Score négatif = plus anormal
            failure_probability = max(0, min(1, (-anomaly_score + 0.1) / 0.5))
            
            # Classification basée sur le score ML
            if anomaly_score < -0.3:
                status = "critical"
                confidence = 0.95
            elif anomaly_score < -0.1:
                status = "warning"  
                confidence = 0.85
            elif anomaly_score < -0.05:
                status = "alert"
                confidence = 0.75
            else:
                status = "normal"
                confidence = 0.90
            
            # Type de panne basé sur les prédictions ML
            failure_type = self._classify_failure_from_ml(ml_data, predictions, anomaly_score)
            
            # Temps estimé avant panne
            time_to_failure = self._estimate_ml_time_to_failure(
                failure_probability, failure_type, predictions
            )
            
            # Mise à jour des métriques
            self.performance_metrics['total_predictions'] += 1
            if is_anomaly:
                self.performance_metrics['anomalies_detected'] += 1
            self.performance_metrics['last_prediction'] = datetime.now().isoformat()
            
            return {
                'predicted_status': status,
                'failure_probability': failure_probability,
                'anomaly_score': float(anomaly_score),
                'is_anomaly': is_anomaly,
                'failure_type': failure_type,
                'confidence': confidence,
                'model_type': 'MLPredictiveEngine_TSForecaster',
                'time_to_failure': time_to_failure,
                'ml_predictions': predictions,  # Prédictions futures ML
                'model_accuracy': confidence_info.get('test_r2', 0.0),
                'buffer_size': confidence_info.get('buffer_size', 0)
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur MLPredictiveEngine.predict_anomaly: {e}")
            return self._fallback_prediction(reading_data, f"exception: {str(e)}")
    
    def predict_future_trend(self, reading_data: Dict[str, float], 
                           hours_ahead: int = 2) -> Dict[str, Any]:
        """
        Prédiction temporelle avec le modèle ML (multi-steps)
        
        Args:
            reading_data: Données actuelles des capteurs
            hours_ahead: Nombre d'heures à prédire dans le futur
            
        Returns:
            Prédictions temporelles ML multi-pas
        """
        try:
            if not self.forecaster:
                return {'status': 'unavailable', 'reason': 'MLForecaster not available'}
            
            # Conversion des données
            ml_data = {
                'temperature': reading_data.get('temperature', 25.0),
                'pression': reading_data.get('pressure', 3.0),
                'vitesse': reading_data.get('velocity', 1.5) * 1000
            }
            
            # Calculer le nombre de pas (toutes les 15 minutes)
            steps_ahead = max(1, hours_ahead * 4)
            
            # Prédiction multi-pas avec ML
            result = self.forecaster.forecast(ml_data, steps_ahead)
            
            if not result.get('ok', False):
                return {'status': 'error', 'reason': result.get('reason', 'unknown')}
            
            forecasts = result.get('forecasts', [])
            
            # Formater les résultats pour l'API
            predictions = {}
            current_time = datetime.now()
            
            # Créer les timestamps
            timestamps = [
                current_time + timedelta(minutes=15*i) 
                for i in range(1, len(forecasts) + 1)
            ]
            
            # Organiser par feature ML
            for feature in ['temperature', 'pression', 'vitesse']:
                pred_key = f"pred_{feature}"
                if forecasts and pred_key in forecasts[0]:
                    values = [f[pred_key] for f in forecasts]
                    
                    # Convertir vitesse de RPM vers m/s pour l'API
                    if feature == 'vitesse':
                        values = [v / 1000 for v in values]  # RPM -> m/s
                    
                    predictions[feature] = {
                        'timestamps': [t.isoformat() for t in timestamps],
                        'values': values,
                        # Ajouter incertitude basée sur la performance ML
                        'lower_bound': [v * 0.95 for v in values],
                        'upper_bound': [v * 1.05 for v in values]
                    }
                    
                    # Détecter tendances critiques
                    current_value = ml_data[feature]
                    if feature == 'vitesse':
                        current_value /= 1000  # RPM -> m/s
                    
                    time_to_critical = self._find_ml_time_to_threshold(
                        timestamps, values, feature, current_value
                    )
                    if time_to_critical:
                        predictions[feature]['time_to_critical'] = time_to_critical
            
            return {
                'status': 'success',
                'predictions': predictions,
                'model_type': 'MLPredictiveEngine_TSForecaster_Forecast',
                'prediction_horizon_hours': hours_ahead,
                'steps_predicted': len(forecasts),
                'model_accuracy': self.performance_metrics['model_accuracy']
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur MLPredictiveEngine.predict_future_trend: {e}")
            return {'status': 'error', 'reason': str(e)}
    
    def _classify_failure_from_ml(self, input_data: Dict[str, float], 
                                 predictions: Dict[str, float], 
                                 anomaly_score: float) -> Optional[str]:
        """Classifie le type de panne basé sur les prédictions ML"""
        if anomaly_score > -0.1:  # Pas assez anormal selon ML
            return None
        
        # Analyser les prédictions ML
        pred_temp = predictions.get('pred_temperature', input_data['temperature'])
        pred_pression = predictions.get('pred_pression', input_data['pression'])
        pred_vitesse = predictions.get('pred_vitesse', input_data['vitesse'])
        
        # Déviations par rapport aux prédictions ML
        temp_dev = abs(pred_temp - input_data['temperature']) / input_data['temperature']
        pression_dev = abs(pred_pression - input_data['pression']) / input_data['pression']
        vitesse_dev = abs(pred_vitesse - input_data['vitesse']) / input_data['vitesse']
        
        # Scores ML pour chaque type de panne
        scores = {}
        
        # Classification basée sur les patterns ML
        scores['ML_TEMPERATURE_ANOMALY'] = temp_dev * 10 if pred_temp > 50 else 0
        scores['ML_PRESSURE_ANOMALY'] = pression_dev * 10 if pred_pression < 2.0 else 0
        scores['ML_VELOCITY_ANOMALY'] = vitesse_dev * 10 if pred_vitesse < 500 or pred_vitesse > 2000 else 0
        scores['ML_SYSTEM_DEGRADATION'] = (temp_dev + pression_dev + vitesse_dev) * 3
        
        # Retourner le type ML avec le score le plus élevé
        if max(scores.values()) >= 2:
            return max(scores.keys(), key=lambda k: scores[k])
        
        return 'ML_UNKNOWN_PATTERN'
    
    def _estimate_ml_time_to_failure(self, probability: float, 
                                   failure_type: Optional[str], 
                                   predictions: Dict[str, float]) -> Optional[int]:
        """Estime le temps avant panne basé sur les prédictions ML"""
        if probability < 0.6:
            return None
        
        # Temps de base par type ML (en heures)
        base_times = {
            'ML_TEMPERATURE_ANOMALY': 24,  # Surchauffe détectée par ML
            'ML_PRESSURE_ANOMALY': 48,     # Problème pression selon ML
            'ML_VELOCITY_ANOMALY': 12,     # Problème vitesse selon ML
            'ML_SYSTEM_DEGRADATION': 72,   # Dégradation générale ML
            'ML_UNKNOWN_PATTERN': 36       # Pattern inconnu
        }
        
        base_time = base_times.get(failure_type, 48)
        
        # Ajuster basé sur la performance ML
        ml_confidence = self.performance_metrics.get('model_accuracy', 0.5)
        
        # Plus le modèle est précis et la probabilité élevée, moins il reste de temps
        time_remaining = base_time * (1 - probability) * (0.5 + ml_confidence * 0.5)
        
        return max(int(time_remaining), 1)
    
    def _find_ml_time_to_threshold(self, timestamps: List[datetime], 
                                 values: List[float], feature: str, 
                                 current_value: float) -> Optional[str]:
        """Trouve quand une prédiction ML atteindra un seuil critique"""
        # Seuils critiques par feature ML
        thresholds = {
            'temperature': 60.0,  # °C
            'pression': 1.0,      # bar (seuil bas)
            'vitesse': 0.3        # m/s (seuil bas)
        }
        
        threshold = thresholds.get(feature)
        if not threshold:
            return None
        
        # Pour pression et vitesse, on cherche quand ça descend en dessous
        # Pour température, on cherche quand ça monte au-dessus
        for time, value in zip(timestamps, values):
            if feature == 'temperature':
                if value >= threshold and current_value < threshold:
                    return time.isoformat()
            else:  # pression, vitesse
                if value <= threshold and current_value > threshold:
                    return time.isoformat()
        
        return None
    
    def _fallback_prediction(self, reading_data: Dict[str, float], 
                           reason: str) -> Dict[str, Any]:
        """Prédiction de fallback si ML échoue"""
        logger.warning(f"⚠️ Fallback prediction activated: {reason}")
        
        # Règles simples basées sur les seuils industriels
        temperature = reading_data.get('temperature', 25.0)
        pressure = reading_data.get('pressure', 3.0)
        velocity = reading_data.get('velocity', 1.5)
        
        score = 0.0
        if temperature > 55: score += 0.6
        elif temperature > 45: score += 0.3
        
        if pressure < 1.5: score += 0.5
        elif pressure > 6.0: score += 0.4
        
        if velocity < 0.5: score += 0.5
        elif velocity > 4.0: score += 0.4
        
        status = 'critical' if score > 0.8 else ('warning' if score > 0.5 else ('alert' if score > 0.2 else 'normal'))
        
        return {
            'predicted_status': status,
            'failure_probability': min(score, 1.0),
            'anomaly_score': -score,
            'is_anomaly': score > 0.5,
            'failure_type': 'FALLBACK_RULES',
            'confidence': 0.6,
            'model_type': 'Fallback_RuleBased',
            'time_to_failure': int((1 - score) * 48) if score > 0.5 else None,
            'fallback_reason': reason
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Retourne les informations sur le modèle ML"""
        base_info = {
            'machine_id': self.machine_id,
            'model_type': 'MLPredictiveEngine_TSForecaster',
            'initialization_status': self.initialization_status,
            'ml_forecaster_available': ML_FORECASTER_AVAILABLE,
            'performance': self.performance_metrics
        }
        
        if self.forecaster:
            ml_info = self.forecaster.get_model_info()
            base_info.update({
                'ml_model_info': ml_info,
                'features': ml_info.get('target_cols', []),
                'n_features': ml_info.get('n_features', 0),
                'buffer_size': ml_info.get('buffer_size', 0)
            })
        
        return base_info
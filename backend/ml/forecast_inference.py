# ml/forecast_inference.py
import json, os
import numpy as np
import pandas as pd
from joblib import load
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class TSForecaster:
    """Classe pour les prédictions ML temps réel IoT"""
    
    def __init__(self, models_dir="ml/models"):
        self.models_dir = models_dir
        try:
            self.model = load(os.path.join(models_dir, "ts_forecast.joblib"))
            self.scaler = load(os.path.join(models_dir, "scaler.joblib"))
            self.anomaly_detector = load(os.path.join(models_dir, "anomaly_detector.joblib"))
            
            with open(os.path.join(models_dir, "meta.json")) as f:
                meta = json.load(f)
            
            self.target_cols = meta["target_cols"]
            self.feat_cols = meta["feat_cols"]
            self.n_lags = meta.get("lags", 3)
            self.rolling_windows = meta.get("rolling_windows", [3, 5])
            self.performance = meta.get("performance", {})
            
            print(f"✅ TSForecaster initialisé avec {len(self.feat_cols)} features")
            print(f"📊 Performance Test R²: {self.performance.get('test', {}).get('r2', 'N/A')}")
            
        except Exception as e:
            print(f"❌ Erreur initialisation TSForecaster: {e}")
            print("💡 Lancez d'abord train_optimized_forecast.py")
            raise

        # Buffer temps réel pour construire les features (dict de listes)
        self.buffer = {c: [] for c in self.target_cols}
        self.max_buffer_size = 100  # Garder historique de 100 points max

    def _create_features_from_buffer(self):
        """Crée les features à partir du buffer actuel"""
        if not self.buffer or not any(self.buffer.values()):
            return None
            
        # Convertir le buffer en DataFrame
        df = pd.DataFrame(self.buffer)
        
        # Features temporelles (simulées pour temps réel)
        df['hour'] = pd.Timestamp.now().hour
        df['day_of_week'] = pd.Timestamp.now().dayofweek
        df['minute'] = pd.Timestamp.now().minute
        
        # Lags
        for col in self.target_cols:
            for lag in range(1, self.n_lags + 1):
                df[f'{col}_lag{lag}'] = df[col].shift(lag)
            
            # Rolling features
            for window in self.rolling_windows:
                if len(df) > window:
                    df[f'{col}_rollmean{window}'] = df[col].rolling(window, min_periods=1).mean().shift(1)
                    df[f'{col}_rollstd{window}'] = df[col].rolling(window, min_periods=1).std().shift(1)
                    df[f'{col}_rollmax{window}'] = df[col].rolling(window, min_periods=1).max().shift(1)
                    df[f'{col}_rollmin{window}'] = df[col].rolling(window, min_periods=1).min().shift(1)
        
        # Features d'interaction
        if len(self.target_cols) >= 2:
            df['temp_pressure_ratio'] = df[self.target_cols[0]] / (df[self.target_cols[1]] + 1e-8)
            if len(self.target_cols) > 2:
                df['temp_velocity_product'] = df[self.target_cols[0]] * df[self.target_cols[2]]
        
        # Retourner la dernière ligne avec toutes les features disponibles
        available_features = [col for col in self.feat_cols if col in df.columns]
        
        if not available_features:
            return None
            
        # Prendre la dernière ligne non-NaN
        df_features = df[available_features].dropna()
        if df_features.empty:
            return None
            
        return df_features.iloc[-1:].values

    def update_buffer(self, latest_point: dict):
        """Met à jour le buffer avec le dernier point de données"""
        for col in self.target_cols:
            if col in latest_point:
                self.buffer[col].append(float(latest_point[col]))
        
        # Limiter la taille du buffer
        for col in self.target_cols:
            if len(self.buffer[col]) > self.max_buffer_size:
                self.buffer[col] = self.buffer[col][-self.max_buffer_size:]

    def predict(self, latest_point: dict):
        """
        Prédiction simple (1 pas en avant)
        latest_point: {"temperature": float, "pression": float, "vitesse": float}
        """
        # 1) Mettre à jour le buffer
        self.update_buffer(latest_point)
        
        # 2) Vérifier qu'on a assez d'historique
        min_len = max(self.n_lags, max(self.rolling_windows)) + 1
        if len(next(iter(self.buffer.values()))) < min_len:
            return {
                "ok": False, 
                "reason": "not_enough_history",
                "required": min_len,
                "available": len(next(iter(self.buffer.values())))
            }

        # 3) Construire les features
        X = self._create_features_from_buffer()
        if X is None:
            return {"ok": False, "reason": "feature_creation_failed"}

        # 4) Scaler + prédiction
        try:
            X_scaled = self.scaler.transform(X)
            y_pred = self.model.predict(X_scaled)[0]  # Premier (et seul) échantillon
            
            # 5) Détection d'anomalie
            anomaly_score = self.anomaly_detector.decision_function(X_scaled)[0]
            is_anomaly = self.anomaly_detector.predict(X_scaled)[0] == -1
            
            # 6) Formatage de la sortie
            predictions = {}
            for i, col in enumerate(self.target_cols):
                predictions[f"pred_{col}"] = float(y_pred[i])
            
            return {
                "ok": True,
                "predictions": predictions,
                "anomaly": {
                    "is_anomaly": bool(is_anomaly),
                    "score": float(anomaly_score),
                    "threshold": "score < -0.1 indicates anomaly"
                },
                "confidence": {
                    "model_type": self.performance.get("model_type", "unknown"),
                    "test_r2": self.performance.get("test", {}).get("r2", 0.0),
                    "buffer_size": len(self.buffer[self.target_cols[0]])
                }
            }
            
        except Exception as e:
            return {"ok": False, "reason": f"prediction_error: {str(e)}"}

    def forecast(self, latest_point: dict, steps_ahead=5):
        """
        Prévision multi-pas (récursive)
        steps_ahead: nombre de pas futurs à prédire
        """
        # Commencer par la prédiction du premier pas
        result = self.predict(latest_point)
        if not result["ok"]:
            return result
        
        if steps_ahead <= 1:
            return result
        
        # Prédiction récursive pour les pas suivants
        forecasts = [result["predictions"]]
        temp_buffer = {col: self.buffer[col].copy() for col in self.target_cols}
        
        # Ajouter la première prédiction au buffer temporaire
        for col in self.target_cols:
            pred_value = result["predictions"][f"pred_{col}"]
            temp_buffer[col].append(pred_value)
        
        # Prédictions récursives
        for step in range(2, steps_ahead + 1):
            # Sauvegarder le buffer original
            original_buffer = self.buffer.copy()
            
            # Utiliser le buffer temporaire
            self.buffer = temp_buffer
            
            try:
                # Créer un point fictif avec les dernières prédictions
                fake_point = {col: temp_buffer[col][-1] for col in self.target_cols}
                
                # Prédire le pas suivant
                X = self._create_features_from_buffer()
                if X is None:
                    break
                
                X_scaled = self.scaler.transform(X)
                y_pred = self.model.predict(X_scaled)[0]
                
                # Ajouter au forecast
                step_predictions = {}
                for i, col in enumerate(self.target_cols):
                    step_predictions[f"pred_{col}"] = float(y_pred[i])
                    temp_buffer[col].append(float(y_pred[i]))
                
                forecasts.append(step_predictions)
                
            except Exception as e:
                print(f"Erreur step {step}: {e}")
                break
            finally:
                # Restaurer le buffer original
                self.buffer = original_buffer
        
        return {
            "ok": True,
            "forecasts": forecasts,
            "steps_predicted": len(forecasts),
            "anomaly": result.get("anomaly", {}),
            "confidence": result.get("confidence", {})
        }

    def get_model_info(self):
        """Retourne les informations sur le modèle"""
        return {
            "target_cols": self.target_cols,
            "n_features": len(self.feat_cols),
            "n_lags": self.n_lags,
            "rolling_windows": self.rolling_windows,
            "buffer_size": len(next(iter(self.buffer.values()))) if self.buffer else 0,
            "performance": self.performance,
            "models_dir": self.models_dir
        }

    def reset_buffer(self):
        """Remet à zéro le buffer (utile pour nouveaux tests)"""
        self.buffer = {c: [] for c in self.target_cols}

# Fonction utilitaire pour créer une instance
def create_forecaster(models_dir="ml/models"):
    """Crée une instance TSForecaster avec gestion d'erreurs"""
    try:
        return TSForecaster(models_dir)
    except Exception as e:
        print(f"❌ Impossible de créer TSForecaster: {e}")
        return None

if __name__ == "__main__":
    # Test rapide
    forecaster = create_forecaster()
    if forecaster:
        print("🧪 Test rapide...")
        test_point = {"temperature": 45.0, "pression": 3.2, "vitesse": 1500.0}
        
        # Ajouter quelques points pour avoir de l'historique
        for i in range(10):
            test_point_i = {
                "temperature": 45.0 + i * 0.1,
                "pression": 3.2 + i * 0.01,
                "vitesse": 1500.0 + i * 10
            }
            result = forecaster.predict(test_point_i)
        
        print(f"Résultat test: {result}")
        print(f"Info modèle: {forecaster.get_model_info()}")
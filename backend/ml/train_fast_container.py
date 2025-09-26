#!/usr/bin/env python3
"""
Version rapide de l'entraînement ML pour container Docker
Utilise un sous-échantillon du dataset pour un entraînement plus rapide
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.multioutput import MultiOutputRegressor
import joblib
import json
from pathlib import Path
import logging

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_features_fast(df, max_lag=5):
    """Version rapide du feature engineering avec moins de lags"""
    logger.info(f"🔧 Feature engineering rapide (lag max: {max_lag})")
    
    # Trier par timestamp
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    features_df = df.copy()
    
    # Lags réduits (5 au lieu de 10)
    for col in ['temperature', 'pression', 'vitesse']:
        for lag in range(1, max_lag + 1):
            features_df[f'{col}_lag_{lag}'] = features_df[col].shift(lag)
    
    # Rolling stats réduites (fenêtres plus petites)
    window_sizes = [3, 5]  # Au lieu de [3, 5, 10]
    
    for col in ['temperature', 'pression', 'vitesse']:
        for window in window_sizes:
            features_df[f'{col}_rolling_mean_{window}'] = features_df[col].rolling(window=window).mean()
            features_df[f'{col}_rolling_std_{window}'] = features_df[col].rolling(window=window).std()
    
    # Supprimer les lignes avec NaN
    features_df = features_df.dropna()
    
    logger.info(f"📊 Features créées: {features_df.shape[1]} colonnes, {len(features_df)} échantillons")
    return features_df

def train_fast_model():
    """Entraînement rapide avec échantillon réduit"""
    logger.info("🚀 === Entraînement ML Rapide pour Container ===")
    
    # Charger et échantillonner le dataset
    logger.info("📁 Chargement dataset...")
    df = pd.read_csv('/app/ml/iot_data_synthetic.csv')
    
    # Prendre seulement les 500 premières lignes pour un entraînement ultra-rapide
    df_sample = df.head(500).reset_index(drop=True)
    
    logger.info(f"📊 Dataset échantillonné: {len(df_sample)} échantillons (500 premières lignes sur {len(df)})")
    
    # Feature engineering rapide
    features_df = create_features_fast(df_sample, max_lag=5)
    
    # Préparer les données
    target_cols = ['temperature', 'pression', 'vitesse']
    feature_cols = [col for col in features_df.columns if col not in target_cols + ['timestamp']]
    
    X = features_df[feature_cols].values
    y = features_df[target_cols].values
    
    logger.info(f"🎯 Données préparées: {X.shape[0]} échantillons, {X.shape[1]} features")
    
    # Split train/test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Scaling
    logger.info("⚖️ Normalisation des données...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Entraînement modèle principal (paramètres ultra-réduits pour rapidité)
    logger.info("🤖 Entraînement GradientBoosting ultra-rapide...")
    model = MultiOutputRegressor(
        GradientBoostingRegressor(
            n_estimators=20,  # Ultra-réduit pour 500 échantillons
            max_depth=3,      # Encore plus petit
            learning_rate=0.15,
            random_state=42
        )
    )
    
    model.fit(X_train_scaled, y_train)
    
    # Prédictions et métriques
    y_pred = model.predict(X_test_scaled)
    
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    logger.info(f"📊 Performance modèle:")
    logger.info(f"   - R² Score: {r2:.4f}")
    logger.info(f"   - MSE: {mse:.2f}")
    logger.info(f"   - MAE: {mae:.2f}")
    
    # Modèle d'anomalies
    logger.info("🚨 Entraînement détecteur d'anomalies...")
    anomaly_detector = IsolationForest(
        contamination=0.1,
        n_estimators=20,  # Ultra-réduit pour rapidité
        random_state=42
    )
    anomaly_detector.fit(X_train_scaled)
    
    # Sauvegarder les modèles
    models_dir = Path('/app/ml/models')
    models_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("💾 Sauvegarde des modèles...")
    
    # Sauvegarder les artefacts avec les noms attendus par TSForecaster
    joblib.dump(model, models_dir / 'ts_forecast.joblib')
    joblib.dump(scaler, models_dir / 'scaler.joblib')
    joblib.dump(anomaly_detector, models_dir / 'anomaly_detector.joblib')
    
    # Métadonnées compatibles avec TSForecaster
    metadata = {
        'model_type': 'GradientBoostingRegressor',
        'n_features': X.shape[1],
        'feat_cols': feature_cols,  # Nom attendu par TSForecaster
        'target_cols': target_cols,  # Nom attendu par TSForecaster
        'lags': 5,  # max_lag utilisé
        'rolling_windows': [3, 5],  # Fenêtres utilisées
        'performance': {
            'test': {
                'r2': float(r2),
                'mse': float(mse), 
                'mae': float(mae)
            },
            'model_type': 'GradientBoostingRegressor',
            'test_samples': int(len(X_test))
        },
        'training_info': {
            'total_samples': int(len(features_df)),
            'original_dataset_size': int(len(df)),
            'sample_size': '500 premières lignes',
            'max_lag': 5,
            'version': 'ultra_fast_container'
        }
    }
    
    with open(models_dir / 'meta.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info("✅ === Entraînement ML Rapide Terminé ===")
    logger.info(f"🎯 Modèle final: GradientBoosting R²={r2:.3f}")
    
    return True

if __name__ == "__main__":
    try:
        success = train_fast_model()
        if success:
            print("✅ SUCCESS: Modèles ML entraînés avec succès")
        else:
            print("❌ ERROR: Échec de l'entraînement")
            exit(1)
    except Exception as e:
        logger.error(f"💥 Erreur critique: {e}")
        print(f"❌ CRITICAL ERROR: {e}")
        exit(1)
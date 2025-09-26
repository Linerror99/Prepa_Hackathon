# ml/train_optimized_forecast.py - Version optimisée pour petits datasets IoT

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, IsolationForest
from sklearn.linear_model import Ridge
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from joblib import dump
import json
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def create_features(df, target_cols, n_lags=3):
    """Création de features optimisée pour petits datasets"""
    df = df.copy()
    
    # Features temporelles si timestamp disponible
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['minute'] = df['timestamp'].dt.minute
    
    # Lags courts mais informatifs
    for col in target_cols:
        for lag in range(1, n_lags + 1):
            df[f'{col}_lag{lag}'] = df[col].shift(lag)
        
        # Rolling features (fenêtres courtes)
        for window in [3, 5]:
            if len(df) > window:
                df[f'{col}_rollmean{window}'] = df[col].rolling(window, min_periods=1).mean().shift(1)
                df[f'{col}_rollstd{window}'] = df[col].rolling(window, min_periods=1).std().shift(1)
                df[f'{col}_rollmax{window}'] = df[col].rolling(window, min_periods=1).max().shift(1)
                df[f'{col}_rollmin{window}'] = df[col].rolling(window, min_periods=1).min().shift(1)
    
    # Features d'interaction
    if len(target_cols) >= 2:
        df['temp_pressure_ratio'] = df[target_cols[0]] / (df[target_cols[1]] + 1e-8)
        df['temp_velocity_product'] = df[target_cols[0]] * df[target_cols[2]] if len(target_cols) > 2 else 0
    
    # Supprimer les lignes avec NaN
    df = df.dropna().reset_index(drop=True)
    
    # Sélectionner les features
    feature_cols = [c for c in df.columns if c not in target_cols + ['timestamp']]
    
    return df, feature_cols

def train_multiple_models(X_train, y_train, X_val, y_val):
    """Entraîne plusieurs modèles et retourne le meilleur"""
    models = {
        'RandomForest': RandomForestRegressor(
            n_estimators=50, max_depth=6, min_samples_split=3,
            min_samples_leaf=2, random_state=42
        ),
        'GradientBoosting': GradientBoostingRegressor(
            n_estimators=50, max_depth=4, learning_rate=0.1,
            random_state=42
        ),
        'Ridge': Ridge(alpha=1.0)
    }
    
    best_model = None
    best_score = -np.inf
    best_name = None
    results = {}
    
    for name, model in models.items():
        print(f"  Entraînement {name}...")
        
        # Entraînement
        if y_train.ndim > 1 and y_train.shape[1] > 1:
            # Multi-output: seul RandomForest supporte nativement
            if name == 'RandomForest':
                model.fit(X_train, y_train)
            else:
                # Pour GB et Ridge, utiliser MultiOutputRegressor
                model = MultiOutputRegressor(model)
                model.fit(X_train, y_train)
        else:
            model.fit(X_train, y_train.ravel() if y_train.ndim > 1 else y_train)
        
        # Prédictions
        y_pred = model.predict(X_val)
        
        # Score R² moyen pour multi-output
        if y_val.ndim > 1 and y_val.shape[1] > 1:
            r2_scores = [r2_score(y_val[:, i], y_pred[:, i]) for i in range(y_val.shape[1])]
            avg_r2 = np.mean(r2_scores)
            mse = mean_squared_error(y_val, y_pred)
            mae = mean_absolute_error(y_val, y_pred)
        else:
            avg_r2 = r2_score(y_val, y_pred)
            mse = mean_squared_error(y_val, y_pred)
            mae = mean_absolute_error(y_val, y_pred)
        
        results[name] = {'r2': avg_r2, 'mse': mse, 'mae': mae}
        print(f"    R² moyen: {avg_r2:.4f}, MSE: {mse:.4f}, MAE: {mae:.4f}")
        
        if avg_r2 > best_score:
            best_score = avg_r2
            best_model = model
            best_name = name
    
    return best_model, best_name, results

def main():
    print("🚀 Entraînement ML IoT Prédictif - Version Optimisée")
    
    # Paramètres
    csv_path = "ml/iot_data_synthetic.csv"
    models_dir = "ml/models"
    
    # Vérifier si le fichier CSV existe dans le dossier parent
    if not os.path.exists(csv_path):
        # Essayer dans le dossier courant
        if os.path.exists("iot_data_synthetic.csv"):
            csv_path = "iot_data_synthetic.csv"
        else:
            print("❌ Fichier iot_data_synthetic.csv non trouvé !")
            return
    
    os.makedirs(models_dir, exist_ok=True)
    
    # 1. Chargement des données
    print("📊 Chargement des données...")
    df = pd.read_csv(csv_path)
    
    # Normaliser les noms de colonnes
    df.columns = [c.strip().lower() for c in df.columns]
    print(f"Dataset: {len(df)} échantillons")
    print(f"Colonnes: {list(df.columns)}")
    
    # Colonnes cibles (capteurs IoT)
    target_cols = ['temperature', 'pression', 'vitesse']
    
    # Vérifier les colonnes
    missing = [col for col in target_cols if col not in df.columns]
    if missing:
        print(f"❌ Colonnes manquantes: {missing}")
        print(f"Colonnes disponibles: {list(df.columns)}")
        return
    
    print(f"✅ Colonnes cibles trouvées: {target_cols}")
    
    # 2. Création des features
    print("🔧 Création des features temporelles...")
    df_features, feature_cols = create_features(df, target_cols, n_lags=3)
    
    print(f"Features créées: {len(feature_cols)}")
    print(f"Échantillons après nettoyage: {len(df_features)}")
    
    if len(df_features) < 50:
        print("❌ Dataset trop petit après feature engineering")
        return
    
    # 3. Préparation des données
    X = df_features[feature_cols].values
    y = df_features[target_cols].values
    
    print(f"Shape X: {X.shape}")
    print(f"Shape y: {y.shape}")
    
    # 4. Split temporel train/validation/test
    n_samples = len(X)
    train_size = int(0.7 * n_samples)
    val_size = int(0.15 * n_samples)
    
    X_train = X[:train_size]
    y_train = y[:train_size]
    X_val = X[train_size:train_size + val_size]
    y_val = y[train_size:train_size + val_size]
    X_test = X[train_size + val_size:]
    y_test = y[train_size + val_size:]
    
    print(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    
    # 5. Normalisation
    print("📐 Normalisation des features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    # 6. Entraînement multi-modèles
    print("🧠 Entraînement des modèles...")
    best_model, best_name, results = train_multiple_models(
        X_train_scaled, y_train, X_val_scaled, y_val
    )
    
    print(f"🏆 Meilleur modèle: {best_name}")
    
    # 7. Test final
    print("🧪 Test final...")
    y_test_pred = best_model.predict(X_test_scaled)
    
    if y_test.ndim > 1 and y_test.shape[1] > 1:
        test_r2_scores = [r2_score(y_test[:, i], y_test_pred[:, i]) for i in range(y_test.shape[1])]
        test_r2 = np.mean(test_r2_scores)
        test_mse = mean_squared_error(y_test, y_test_pred)
        test_mae = mean_absolute_error(y_test, y_test_pred)
        print(f"Test R² par target: {[f'{r:.4f}' for r in test_r2_scores]}")
    else:
        test_r2 = r2_score(y_test, y_test_pred)
        test_mse = mean_squared_error(y_test, y_test_pred)
        test_mae = mean_absolute_error(y_test, y_test_pred)
    
    print(f"Test R² moyen: {test_r2:.4f}")
    print(f"Test MSE: {test_mse:.4f}")
    print(f"Test MAE: {test_mae:.4f}")
    
    # 8. Détection d'anomalies
    print("🔍 Entraînement détecteur d'anomalies...")
    anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
    anomaly_detector.fit(X_train_scaled)
    
    # 9. Sauvegarde
    print("💾 Sauvegarde des modèles...")
    
    # Modèle principal
    dump(best_model, f"{models_dir}/ts_forecast.joblib")
    print(f"✅ Modèle principal sauvegardé: {models_dir}/ts_forecast.joblib")
    
    # Scaler
    dump(scaler, f"{models_dir}/scaler.joblib")
    print(f"✅ Scaler sauvegardé: {models_dir}/scaler.joblib")
    
    # Détecteur d'anomalies
    dump(anomaly_detector, f"{models_dir}/anomaly_detector.joblib")
    print(f"✅ Détecteur d'anomalies sauvegardé: {models_dir}/anomaly_detector.joblib")
    
    # Métadonnées
    meta = {
        "target_cols": target_cols,
        "feat_cols": feature_cols,
        "n_features": len(feature_cols),
        "n_targets": len(target_cols),
        "model_type": best_name,
        "train_samples": len(X_train),
        "val_samples": len(X_val),
        "test_samples": len(X_test),
        "lags": 3,
        "rolling_windows": [3, 5],
        "performance": {
            "validation": results[best_name],
            "test": {
                "r2": float(test_r2),
                "mse": float(test_mse),
                "mae": float(test_mae)
            }
        },
        "feature_importance": {}
    }
    
    # Feature importance si disponible
    if hasattr(best_model, 'feature_importances_'):
        importance = best_model.feature_importances_
        meta["feature_importance"] = {
            feature_cols[i]: float(importance[i]) 
            for i in np.argsort(importance)[::-1][:10]  # Top 10
        }
    
    # Sauvegarde métadonnées
    with open(f"{models_dir}/meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    
    print(f"✅ Métadonnées sauvegardées: {models_dir}/meta.json")
    
    print("\n🎯 Résumé de l'entraînement:")
    print(f"  Modèle: {best_name}")
    print(f"  Features: {len(feature_cols)}")
    print(f"  Targets: {len(target_cols)}")
    print(f"  R² Test: {test_r2:.4f}")
    print(f"  MSE Test: {test_mse:.4f}")
    print(f"  MAE Test: {test_mae:.4f}")
    
    if meta["feature_importance"]:
        print("\n🔍 Top 5 Features importantes:")
        for feat, imp in list(meta["feature_importance"].items())[:5]:
            print(f"  {feat}: {imp:.4f}")
    
    print("\n🚀 Modèle prêt pour la prédiction IoT temps réel!")

if __name__ == "__main__":
    main()
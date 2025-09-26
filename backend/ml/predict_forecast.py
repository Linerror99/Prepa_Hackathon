# backend/ml/predict_forecast.py
import argparse
import json
import joblib
import pandas as pd
import numpy as np
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
ARTIFACTS = ROOT / "backend" / "ml" / "models"

def load_artifacts():
    """Charge les artefacts ML (modèle, scaler, métadonnées)"""
    with open(ARTIFACTS / "meta.json", "r") as f:
        meta = json.load(f)
    scaler = joblib.load(ARTIFACTS / "scaler.joblib")
    model = joblib.load(ARTIFACTS / "ts_forecast.joblib")
    return meta, scaler, model

def create_features_inference(df, target_cols, n_lags=3):
    """Crée les mêmes features que lors de l'entraînement"""
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
    
    return df

def build_features(df, target_cols, feat_cols, n_lags=3):
    """Construit les features exactement comme pendant l'entraînement"""
    df_feat = create_features_inference(df, target_cols, n_lags)
    
    # Garder uniquement les features attendues, dans le même ordre
    available_features = [col for col in feat_cols if col in df_feat.columns]
    
    if len(available_features) != len(feat_cols):
        print(f"⚠️  Warning: {len(feat_cols)} features attendues, {len(available_features)} disponibles")
        
    X = df_feat[available_features].copy()
    # Supprimer les lignes incomplètes (lags/rolling au début)
    X = X.dropna()
    return X, df_feat.index.isin(X.index)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(BACKEND / "ml" / "iot_data_synthetic.csv"),
                        help="CSV d'entrée (doit contenir temperature, pression, vitesse)")
    parser.add_argument("--output", default=str(BACKEND / "ml" / "predictions.csv"),
                        help="CSV de sortie")
    parser.add_argument("--timestamp-col", default="timestamp",
                        help="Nom de la colonne temps si présente (pour la sortie)")
    args = parser.parse_args()

    try:
        meta, scaler, model = load_artifacts()
    except Exception as e:
        print(f"❌ Erreur chargement artefacts: {e}")
        print("💡 Lancez d'abord train_optimized_forecast.py")
        return
        
    target_cols = meta["target_cols"]
    feat_cols = meta["feat_cols"]
    n_lags = meta.get("lags", 3)

    # 1) Lecture
    print(f"📊 Lecture {args.input}...")
    df = pd.read_csv(args.input)
    
    # Normaliser les noms de colonnes
    df.columns = [c.strip().lower() for c in df.columns]
    print(f"Dataset: {len(df)} échantillons")
    
    # Garder un timestamp si présent (facultatif)
    ts = df[args.timestamp_col] if args.timestamp_col in df.columns else None

    # 2) Construire les features exactement comme dans meta
    print("🔧 Construction des features...")
    X, mask_used = build_features(df, target_cols, feat_cols, n_lags)
    
    if X.empty:
        need = n_lags + max([3, 5])  # ordre de grandeur
        print(f"❌ Pas assez d'historique pour créer les features (au moins ~{need} lignes).")
        return

    print(f"Features construites: {X.shape}")

    # 3) Scaler + prédire
    print("🧠 Prédictions ML...")
    X_scaled = scaler.transform(X.values)
    y_pred = model.predict(X_scaled)

    # 4) Sortie
    used_idx = X.index
    if y_pred.ndim == 1:
        out = pd.DataFrame({"prediction": y_pred}, index=used_idx)
    elif y_pred.ndim == 2:
        # Multi-sortie, on nomme avec les cibles du meta
        target_cols = meta.get("target_cols", [f"target_{i}" for i in range(y_pred.shape[1])])
        # Sécurité si tailles différentes
        if len(target_cols) != y_pred.shape[1]:
            target_cols = [f"target_{i}" for i in range(y_pred.shape[1])]
        out = pd.DataFrame(y_pred, columns=[f"pred_{col}" for col in target_cols], index=used_idx)
    else:
        print(f"❌ y_pred de dimension inattendue: {y_pred.shape}")
        return

    # Insérer timestamp si présent
    if ts is not None:
        out.insert(0, args.timestamp_col, ts.loc[out.index].values)

    out.to_csv(args.output, index=False)
    print(f"✅ Prédictions enregistrées -> {args.output}")
    print(f"📊 Aperçu des prédictions:")
    print(out.tail(10).to_string(index=False))


if __name__ == "__main__":
    main()
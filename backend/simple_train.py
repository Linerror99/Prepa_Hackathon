import numpy as np
import pandas as pd
from pyod.models.iforest import IForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, f1_score
import pickle
import os

print("Entrainement IA...")

# Données d'entraînement
np.random.seed(42)
n_normal = 800
n_anomaly = 200

# Données normales
normal = np.random.normal([300, 310, 1500, 40, 100], [2, 8, 100, 10, 50], (n_normal, 5))
# Données anormales (plus extrêmes)
anomaly = np.random.normal([320, 340, 1000, 70, 300], [10, 20, 300, 20, 100], (n_anomaly, 5))

X = np.vstack([normal, anomaly])
y = np.hstack([np.zeros(n_normal), np.ones(n_anomaly)])

# Entraînement
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

detector = IForest(contamination=0.25, random_state=42, n_estimators=100)
detector.fit(X_scaled)

# Test
predictions = detector.predict(X_scaled)
predictions_binary = [1 if p == -1 else 0 for p in predictions]

accuracy = accuracy_score(y, predictions_binary)
f1 = f1_score(y, predictions_binary, zero_division=0)

print(f"Accuracy: {accuracy:.3f}")
print(f"F1-Score: {f1:.3f}")

# Sauvegarde
os.makedirs('data/models', exist_ok=True)
with open('data/models/isolation_forest.pkl', 'wb') as f:
    pickle.dump({
        'detectors': {'global': detector},
        'scalers': {'global': scaler},
        'metrics': {
            'accuracy_score': accuracy,
            'f1_score': f1,
            'total_predictions': len(y),
            'last_training': '2025-09-20'
        }
    }, f)

print("Modele sauvegarde!")
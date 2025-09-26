#!/bin/bash
set -e

echo "🚀 === Container Backend IoT + ML Startup ==="

# Exécuter l'entraînement ML si nécessaire
echo "📚 Étape 1: Préparation des modèles ML..."
python /app/startup_train_ml.py

# Attendre un peu pour que tout soit prêt
sleep 2

echo "🎯 Étape 2: Démarrage de l'application FastAPI..."

# Lancer l'application FastAPI
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
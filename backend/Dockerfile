FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Créer le répertoire data avec les bonnes permissions
RUN mkdir -p /app/data && chmod 777 /app/data

# Variables d'environnement
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV MQTT_BROKER=mosquitto
ENV REDIS_URL=redis://redis:6379

# Port d'exposition
EXPOSE 8000

# Healthcheck avec délai plus long pour l'entraînement
HEALTHCHECK --interval=45s --timeout=15s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

# Script de démarrage intégré (évite les problèmes d'encodage)
CMD ["sh", "-c", "echo '🚀 Container Backend IoT + ML Startup' && python startup_train_ml.py && echo '🎯 Démarrage FastAPI...' && uvicorn main:app --host 0.0.0.0 --port 8000"]
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

# Rendre l'entrypoint exécutable
RUN chmod +x /app/entrypoint.sh

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

# Entrypoint qui lance ML + FastAPI
ENTRYPOINT ["/app/entrypoint.sh"]
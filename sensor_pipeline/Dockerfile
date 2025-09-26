FROM python:3.9-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier les scripts
COPY . .

# Rendre le script d'entrée exécutable
RUN chmod +x entrypoint.sh

# Créer un utilisateur non-root pour la sécurité
RUN useradd -m -u 1001 sensoruser && chown -R sensoruser:sensoruser /app
USER sensoruser

# Healthcheck pour monitoring
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import paho.mqtt.client as mqtt; c = mqtt.Client(); c.connect('mosquitto', 1883, 10); c.disconnect()" || exit 1

# Point d'entrée flexible
ENTRYPOINT ["./entrypoint.sh"]
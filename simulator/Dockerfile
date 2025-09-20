FROM python:3.11-slim

WORKDIR /app

# Copier les requirements et installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Variables d'environnement par défaut
ENV MQTT_BROKER=mosquitto
ENV NUM_MACHINES=3
ENV READING_INTERVAL=2.0

# Commande par défaut
CMD ["python", "machine_simulator.py", "--machines", "${NUM_MACHINES}", "--interval", "${READING_INTERVAL}", "--mqtt-broker", "${MQTT_BROKER}"]
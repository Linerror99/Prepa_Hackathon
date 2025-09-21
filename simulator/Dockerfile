FROM python:3.11-slim

WORKDIR /app

# Copier les requirements et installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Variables d'environnement par défaut
ENV PYTHONUNBUFFERED=1
ENV MQTT_BROKER=mosquitto
ENV NUM_MACHINES=3
ENV READING_INTERVAL=2.0

# Commande par défaut (corrigée)
CMD ["python", "machine_simulator.py", "--machines", "3", "--interval", "2.0", "--mqtt-broker", "mosquitto"]
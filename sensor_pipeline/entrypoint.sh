#!/bin/bash
# Script de démarrage pour le pipeline de capteurs industriels

set -e  # Arrêter en cas d'erreur

echo "🏭 PIPELINE CAPTEURS INDUSTRIELS - DÉMARRAGE"
echo "============================================="

# Vérifier les variables d'environnement
if [ -z "$MQTT_HOST" ]; then
    echo "❌ Variable MQTT_HOST manquante"
    exit 1
fi

echo "📊 Configuration:"
echo "   MQTT_HOST: ${MQTT_HOST}"
echo "   MQTT_PORT: ${MQTT_PORT:-1883}"
echo "   AGGREGATION_TOLERANCE: ${AGGREGATION_TOLERANCE:-1}s"

# Attendre que MQTT soit disponible
echo "⏳ Attente du broker MQTT..."
timeout=60
while ! nc -z "$MQTT_HOST" "${MQTT_PORT:-1883}"; do
    sleep 1
    timeout=$((timeout - 1))
    if [ $timeout -eq 0 ]; then
        echo "❌ Timeout: Impossible de connecter au broker MQTT"
        exit 1
    fi
done

echo "✅ Broker MQTT accessible"

# Démarrer le composant approprié
case "${SENSOR_COMPONENT:-aggregator}" in
    "aggregator")
        echo "🚀 Démarrage de l'agrégateur de capteurs..."
        exec python sensor_aggregator.py
        ;;
    "simulator")
        echo "🧪 Démarrage du simulateur de capteurs..."
        exec python real_sensor_simulator.py
        ;;
    "test")
        echo "🔍 Démarrage des tests..."
        exec python test_pipeline.py
        ;;
    *)
        echo "❌ Composant inconnu: ${SENSOR_COMPONENT}"
        echo "   Valeurs possibles: aggregator, simulator, test"
        exit 1
        ;;
esac
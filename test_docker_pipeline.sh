#!/bin/bash
# Script de test rapide pour l'intégration Docker du pipeline

echo "🧪 TEST INTÉGRATION PIPELINE DOCKER"
echo "=================================="

# Fonction pour vérifier si un service répond
check_service() {
    local service=$1
    local url=$2
    local name=$3
    
    echo -n "🔍 Test $name ($service): "
    
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo "✅ OK"
        return 0
    else
        echo "❌ ERREUR"
        return 1
    fi
}

# Fonction pour vérifier MQTT
check_mqtt() {
    echo -n "🔍 Test MQTT: "
    
    # Test de publication MQTT
    if docker exec mqtt-broker mosquitto_pub -h localhost -t "test/pipeline" -m "test" 2>/dev/null; then
        echo "✅ OK"
        return 0
    else
        echo "❌ ERREUR"
        return 1
    fi
}

# Vérifier les services
echo "📊 Vérification des services..."

check_service "backend" "http://localhost:8000/health" "Backend API"
check_service "dashboard" "http://localhost:8501" "Dashboard Streamlit"
check_mqtt

# Vérifier les conteneurs du pipeline
echo ""
echo "🐳 État des conteneurs pipeline:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(sensor-|mqtt-broker|iot-)"

# Vérifier les logs récents
echo ""
echo "📋 Logs récents sensor-aggregator:"
docker logs sensor-aggregator --tail 10 2>/dev/null | head -5

echo ""
echo "📋 Logs récents iot-simulator:"
docker logs iot-simulator --tail 10 2>/dev/null | head -5

# Test de données via API
echo ""
echo "🔍 Test données machines via API:"
if curl -s "http://localhost:8000/api/machines/live" | python -c "import sys,json; data=json.load(sys.stdin); print(f'✅ {len(data)} machines trouvées') if len(data) > 0 else print('⚠️ Aucune machine trouvée')" 2>/dev/null; then
    :
else
    echo "❌ Erreur accès API machines"
fi

echo ""
echo "🎯 Test terminé!"
echo "Pour des logs détaillés: docker logs <container_name>"
echo "Pour redémarrer le pipeline: docker compose restart sensor-aggregator"
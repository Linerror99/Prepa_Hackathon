#!/bin/bash

# 🏭 Script de démarrage complet du système IoT + IA
# Démarre tous les services nécessaires pour le hackathon

echo "🚀 DÉMARRAGE SYSTÈME SMART FACTORY"
echo "=================================="

# Variables
PROJECT_DIR="c:/Users/ldjossou/OneDrive - Capgemini/Documents/Me documents/Cours/Hackathon 2025-2026/Prepa_Hackathon"

# Fonction pour attendre qu'un service soit prêt
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Attente du démarrage de $service_name..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo "✅ $service_name est prêt!"
            return 0
        fi
        echo "   Tentative $attempt/$max_attempts..."
        sleep 2
        ((attempt++))
    done
    
    echo "❌ $service_name n'a pas démarré dans les temps"
    return 1
}

# 1. Démarrer le backend FastAPI
echo "1️⃣ Démarrage du Backend IA..."
cd "$PROJECT_DIR/backend"
python main.py &
BACKEND_PID=$!

# Attendre que le backend soit prêt
if wait_for_service "http://localhost:8000/health" "Backend IA"; then
    echo "   🧠 Modèles IA chargés et prêts"
else
    echo "❌ Échec démarrage backend"
    exit 1
fi

# 2. Démarrer le simulateur IoT
echo ""
echo "2️⃣ Démarrage du Simulateur IoT..."
cd "$PROJECT_DIR/simulator"
python machine_simulator.py --machines 3 --mqtt-broker localhost &
SIMULATOR_PID=$!
sleep 3
echo "   🏭 3 machines simulées en fonctionnement"

# 3. Démarrer le dashboard Streamlit
echo ""
echo "3️⃣ Démarrage du Dashboard..."
cd "$PROJECT_DIR/dashboard"
python run_dashboard.py &
DASHBOARD_PID=$!

# Attendre que le dashboard soit prêt
if wait_for_service "http://localhost:8501" "Dashboard"; then
    echo "   📊 Interface web disponible"
else
    echo "❌ Échec démarrage dashboard"
fi

echo ""
echo "🎉 SYSTÈME COMPLET DÉMARRÉ !"
echo "=========================="
echo "🧠 Backend IA:     http://localhost:8000"
echo "📊 Dashboard:      http://localhost:8501"
echo "🏭 Simulateur:     3 machines actives"
echo ""
echo "💡 Ouvrez http://localhost:8501 dans votre navigateur"
echo ""
echo "🛑 Pour arrêter: Ctrl+C"

# Fonction de nettoyage
cleanup() {
    echo ""
    echo "🛑 Arrêt du système..."
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "   Backend arrêté"
    fi
    
    if [ ! -z "$SIMULATOR_PID" ]; then
        kill $SIMULATOR_PID 2>/dev/null
        echo "   Simulateur arrêté"
    fi
    
    if [ ! -z "$DASHBOARD_PID" ]; then
        kill $DASHBOARD_PID 2>/dev/null
        echo "   Dashboard arrêté"
    fi
    
    echo "✅ Système arrêté proprement"
    exit 0
}

# Capturer Ctrl+C
trap cleanup SIGINT

# Attendre indéfiniment
echo "⏳ Système en fonctionnement... (Ctrl+C pour arrêter)"
wait
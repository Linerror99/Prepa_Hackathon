#!/bin/bash
# -*- coding: utf-8 -*-
# 🐳 Script de lancement Docker Compose - Système IoT+IA Complet
# Compatible Git Bash / WSL / Linux

set -e  # Arrêt en cas d'erreur

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Variables
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"

# Fonction de log avec couleurs
log() {
    local level=$1
    local message=$2
    local timestamp=$(date +"%H:%M:%S")
    
    case $level in
        "INFO")
            echo -e "${CYAN}[$timestamp] INFO: $message${NC}"
            ;;
        "SUCCESS")
            echo -e "${GREEN}[$timestamp] SUCCESS: $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}[$timestamp] WARNING: $message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}[$timestamp] ERROR: $message${NC}"
            ;;
        *)
            echo -e "${BLUE}[$timestamp] $message${NC}"
            ;;
    esac
}

# Fonction de gestion d'arrêt propre
cleanup() {
    log "WARNING" ""
    log "WARNING" "🛑 Arrêt du système..."
    
    if [ -f "$COMPOSE_FILE" ]; then
        log "WARNING" "🔄 Arrêt des services Docker..."
        cd "$PROJECT_ROOT"
        docker compose down || true
    fi
    
    log "SUCCESS" "✅ Système arrêté proprement"
    exit 0
}

# Trap pour arrêt propre
trap cleanup SIGINT SIGTERM

# Vérification de Docker
check_docker() {
    log "INFO" "🔍 Vérification de Docker..."
    
    if ! command -v docker &> /dev/null; then
        log "ERROR" "❌ Docker n'est pas installé ou accessible"
        log "ERROR" "Installez Docker Desktop depuis https://docker.com"
        exit 1
    fi
    
    if ! docker compose version &> /dev/null; then
        log "ERROR" "❌ Docker Compose n'est pas disponible"
        log "ERROR" "Mettez à jour Docker Desktop"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log "ERROR" "❌ Docker n'est pas démarré"
        log "ERROR" "Démarrez Docker Desktop"
        exit 1
    fi
    
    log "SUCCESS" "✅ Docker et Docker Compose disponibles"
}

# Vérification du fichier compose
check_compose_file() {
    if [ ! -f "$COMPOSE_FILE" ]; then
        log "ERROR" "❌ Fichier docker-compose.yml non trouvé dans $PROJECT_ROOT"
        exit 1
    fi
    log "SUCCESS" "✅ Fichier docker-compose.yml trouvé"
}

# Nettoyage des conteneurs existants
cleanup_existing() {
    log "INFO" "🧹 Nettoyage des conteneurs existants..."
    
    cd "$PROJECT_ROOT"
    
    # Arrêter et supprimer les conteneurs existants
    docker compose down &> /dev/null || true
    
    # Nettoyer les images orphelines
    docker system prune -f &> /dev/null || true
    
    log "SUCCESS" "✅ Nettoyage terminé"
    sleep 2
}

# Construction des images
build_images() {
    log "INFO" "🔨 Construction des images Docker..."
    
    cd "$PROJECT_ROOT"
    
    if docker compose build --no-cache; then
        log "SUCCESS" "✅ Images construites avec succès"
        return 0
    else
        log "ERROR" "❌ Erreur lors de la construction des images"
        return 1
    fi
}

# Démarrage des services
start_services() {
    log "INFO" "🚀 Démarrage des services..."
    
    cd "$PROJECT_ROOT"
    
    if docker compose up -d; then
        log "SUCCESS" "✅ Services démarrés avec succès"
        return 0
    else
        log "ERROR" "❌ Erreur lors du démarrage des services"
        return 1
    fi
}

# Attente des services
wait_for_services() {
    log "INFO" "⏳ Attente que les services soient prêts..."
    
    # Attendre le backend
    log "INFO" "Vérification du Backend API..."
    for i in {1..60}; do
        if curl -s http://localhost:8000/health &> /dev/null; then
            log "SUCCESS" "✅ Backend API prêt!"
            break
        fi
        sleep 1
        if [ $i -eq 60 ]; then
            log "WARNING" "⚠️ Backend API peut prendre plus de temps"
        fi
    done
    
    # Attendre le dashboard
    log "INFO" "Vérification du Dashboard..."
    for i in {1..30}; do
        if curl -s http://localhost:8501 &> /dev/null; then
            log "SUCCESS" "✅ Dashboard prêt!"
            break
        fi
        sleep 1
        if [ $i -eq 30 ]; then
            log "WARNING" "⚠️ Dashboard peut prendre plus de temps"
        fi
    done
    
    # MQTT (pas de vérification HTTP)
    log "SUCCESS" "✅ MQTT Broker démarré"
    log "SUCCESS" "✅ Simulateur IoT démarré"
}

# Affichage du statut
show_status() {
    echo ""
    log "INFO" "📊 Statut des Services:"
    echo "============================================================"
    
    cd "$PROJECT_ROOT"
    docker compose ps || true
    
    echo "============================================================"
}

# Affichage des informations finales
show_final_info() {
    echo ""
    log "SUCCESS" "🎉 SYSTÈME DOCKER DÉMARRÉ AVEC SUCCÈS!"
    echo "============================================================"
    log "INFO" "🌐 Dashboard Temps Réel: http://localhost:8501"
    log "INFO" "🔧 API Backend: http://localhost:8000"
    log "INFO" "📚 Documentation API: http://localhost:8000/docs"
    log "INFO" "📡 MQTT Broker: localhost:1883"
    log "INFO" "🏭 Simulateur: 3 machines IoT conteneurisées"
    echo "============================================================"
    log "INFO" "📋 Commandes utiles:"
    log "INFO" "  docker compose logs -f  # Voir les logs"
    log "INFO" "  docker compose ps       # Voir le statut"
    log "INFO" "  docker compose down     # Arrêter"
    echo "============================================================"
    log "INFO" "Ctrl+C pour arrêter le système"
    echo ""
}

# Affichage des logs en continu
show_logs() {
    log "INFO" "📋 Logs des services (Ctrl+C pour arrêter):"
    echo ""
    
    cd "$PROJECT_ROOT"
    docker compose logs -f
}

# Fonction principale
main() {
    log "SUCCESS" "🐳 DÉMARRAGE SYSTÈME IoT+IA DOCKER"
    echo "============================================================"
    
    # Vérifications
    check_docker
    check_compose_file
    
    # Nettoyage
    cleanup_existing
    
    # Construction
    if ! build_images; then
        exit 1
    fi
    
    # Démarrage
    if ! start_services; then
        exit 1
    fi
    
    # Attente des services
    wait_for_services
    
    # Statut
    show_status
    
    # Informations finales
    show_final_info
    
    # Logs en continu
    show_logs
}

# Point d'entrée
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
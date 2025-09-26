# Makefile pour le système IoT avec pipeline capteurs industriels

.PHONY: help build up down logs test clean sensor-test

# Couleurs pour l'affichage
BLUE=\033[0;34m
GREEN=\033[0;32m
YELLOW=\033[1;33m
RED=\033[0;31m
NC=\033[0m # No Color

help: ## Afficher cette aide
	@echo "$(BLUE)🏭 SYSTÈME IOT MAINTENANCE PRÉDICTIVE$(NC)"
	@echo "$(BLUE)=====================================$(NC)"
	@echo ""
	@echo "$(GREEN)Commandes disponibles:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Construire toutes les images Docker
	@echo "$(BLUE)🔨 Construction des images Docker...$(NC)"
	docker-compose build --no-cache

up: ## Démarrer le système complet
	@echo "$(BLUE)🚀 Démarrage du système IoT complet...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✅ Système démarré!$(NC)"
	@echo "$(YELLOW)📊 Dashboard: http://localhost:8501$(NC)"
	@echo "$(YELLOW)📡 API Backend: http://localhost:8000$(NC)"
	@echo "$(YELLOW)🔍 MQTT: localhost:1883$(NC)"

up-with-sim: ## Démarrer avec simulateur original
	@echo "$(BLUE)🧪 Démarrage avec simulateur UCI...$(NC)"
	docker-compose --profile simulation up -d

up-with-sensors: ## Démarrer avec simulateur capteurs industriels
	@echo "$(BLUE)🏭 Démarrage avec capteurs industriels...$(NC)"
	docker-compose --profile sensor-sim up -d

down: ## Arrêter le système
	@echo "$(BLUE)🛑 Arrêt du système...$(NC)"
	docker-compose down

logs: ## Voir les logs en temps réel
	docker-compose logs -f

logs-sensors: ## Voir les logs du pipeline capteurs
	docker-compose logs -f sensor-aggregator sensor-simulator

sensor-test: ## Tester le pipeline capteurs
	@echo "$(BLUE)🧪 Tests du pipeline capteurs...$(NC)"
	docker-compose -f docker-compose.sensor-test.yml up --build --abort-on-container-exit
	docker-compose -f docker-compose.sensor-test.yml down

test: ## Tests complets du système
	@echo "$(BLUE)🔍 Tests système complets...$(NC)"
	$(MAKE) sensor-test
	@echo "$(GREEN)✅ Tests terminés$(NC)"

clean: ## Nettoyer les containers et images
	@echo "$(BLUE)🧹 Nettoyage...$(NC)"
	docker-compose down -v --remove-orphans
	docker-compose -f docker-compose.sensor-test.yml down -v --remove-orphans
	docker system prune -f

status: ## Vérifier l'état des services
	@echo "$(BLUE)📊 État des services:$(NC)"
	docker-compose ps
	@echo ""
	@echo "$(BLUE)🔗 Services disponibles:$(NC)"
	@curl -s http://localhost:8000/health 2>/dev/null && echo "$(GREEN)✅ Backend API$(NC)" || echo "$(RED)❌ Backend API$(NC)"
	@curl -s http://localhost:8501 2>/dev/null && echo "$(GREEN)✅ Dashboard$(NC)" || echo "$(RED)❌ Dashboard$(NC)"
	@nc -z localhost 1883 2>/dev/null && echo "$(GREEN)✅ MQTT Broker$(NC)" || echo "$(RED)❌ MQTT Broker$(NC)"

restart: ## Redémarrer le système
	@echo "$(BLUE)🔄 Redémarrage...$(NC)"
	$(MAKE) down
	$(MAKE) up

dev: ## Environnement de développement (avec rebuild)
	@echo "$(BLUE)👨‍💻 Mode développement...$(NC)"
	docker-compose up --build

monitor: ## Monitorer les métriques
	@echo "$(BLUE)📊 Monitoring système...$(NC)"
	docker stats

mqtt-listen: ## Écouter les messages MQTT
	@echo "$(BLUE)📡 Écoute MQTT (Ctrl+C pour arrêter)...$(NC)"
	@echo "$(YELLOW)Topics écoutés: iot/sensors/+, sensors/+/+$(NC)"
	mosquitto_sub -h localhost -t "iot/sensors/+" -t "sensors/+/+" -v

# Commandes de maintenance
backup-data: ## Sauvegarder les données
	@echo "$(BLUE)💾 Sauvegarde des données...$(NC)"
	docker run --rm -v $$(pwd)/data:/data -v $$(pwd)/backup:/backup alpine tar czf /backup/iot-data-$$(date +%Y%m%d_%H%M%S).tar.gz -C /data .

restore-data: ## Restaurer les données (specify BACKUP_FILE=filename)
	@echo "$(BLUE)📁 Restauration des données...$(NC)"
	@if [ -z "$(BACKUP_FILE)" ]; then echo "$(RED)❌ Spécifiez BACKUP_FILE=filename$(NC)"; exit 1; fi
	docker run --rm -v $$(pwd)/data:/data -v $$(pwd)/backup:/backup alpine tar xzf /backup/$(BACKUP_FILE) -C /data
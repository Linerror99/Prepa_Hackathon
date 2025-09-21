#!/bin/bash
# 🧪 Script de test pour vérifier la disponibilité de Docker

set -e

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🧪 TEST - Vérification Docker pour Git Bash${NC}"
echo "============================================================"

# Test 1: Docker installé
echo -n "Docker installé: "
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✅ OUI${NC}"
    docker --version
else
    echo -e "${RED}❌ NON${NC}"
    exit 1
fi

echo ""

# Test 2: Docker Compose disponible
echo -n "Docker Compose: "
if docker compose version &> /dev/null; then
    echo -e "${GREEN}✅ OUI${NC}"
    docker compose version
else
    echo -e "${RED}❌ NON${NC}"
    exit 1
fi

echo ""

# Test 3: Docker daemon démarré
echo -n "Docker démarré: "
if docker info &> /dev/null; then
    echo -e "${GREEN}✅ OUI${NC}"
else
    echo -e "${RED}❌ NON - Démarrez Docker Desktop${NC}"
    exit 1
fi

echo ""

# Test 4: Fichier docker-compose.yml
echo -n "docker-compose.yml: "
if [ -f "docker-compose.yml" ]; then
    echo -e "${GREEN}✅ TROUVÉ${NC}"
else
    echo -e "${RED}❌ MANQUANT${NC}"
    exit 1
fi

echo ""

# Test 5: Scripts de lancement
echo -n "start_docker.sh: "
if [ -f "start_docker.sh" ] && [ -x "start_docker.sh" ]; then
    echo -e "${GREEN}✅ PRÊT${NC}"
else
    echo -e "${RED}❌ NON EXÉCUTABLE${NC}"
    exit 1
fi

echo ""
echo "============================================================"
echo -e "${GREEN}🎉 TOUS LES TESTS PASSÉS!${NC}"
echo ""
echo -e "${YELLOW}🚀 Vous pouvez maintenant lancer:${NC}"
echo -e "${GREEN}./start_docker.sh${NC}"
echo "============================================================"
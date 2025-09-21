@echo off
chcp 65001 >nul
echo.
echo ============================================================
echo    🐳 SYSTÈME IoT+IA DOCKER - LANCEMENT COMPLET
echo ============================================================
echo.

REM Vérifier si Python est installé
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python n'est pas installé ou accessible
    echo Installez Python depuis https://python.org
    pause
    exit /b 1
)

REM Vérifier si Docker est installé
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker n'est pas installé ou accessible
    echo Installez Docker Desktop depuis https://docker.com
    pause
    exit /b 1
)

REM Installer les dépendances si nécessaire
echo 📦 Vérification des dépendances...
pip install -q requests

echo.
echo 🚀 Lancement du système Docker...
echo.

REM Lancer le script Python
python start_docker.py

pause